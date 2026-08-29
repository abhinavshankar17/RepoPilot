from typing import List, Tuple, Dict, Optional, Any
from app.schemas.chunk import CodeChunk
from app.services.vector_store import VectorStoreService, get_vector_store_service
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.reranker import BaseReranker, CrossEncoderReranker
from app.core.logging import logger


class HybridRetriever:
    """Advanced Hybrid Retriever combining Vector Search, BM25 Keyword Search, RRF Fusion, and Reranking."""

    def __init__(
        self,
        vector_store_svc: Optional[VectorStoreService] = None,
        reranker: Optional[BaseReranker] = None,
        rrf_k: int = 60
    ):
        self.vector_store_svc = vector_store_svc or get_vector_store_service()
        self.reranker = reranker or CrossEncoderReranker()
        self.rrf_k = rrf_k
        self._bm25_cache: Dict[str, BM25Retriever] = {}

    def get_bm25_retriever(self, repository_id: str) -> BM25Retriever:
        """Retrieves or builds BM25 retriever for a repository."""
        if repository_id not in self._bm25_cache:
            # Load chunks from vector store metadata
            repo_index = self.vector_store_svc._indices.get(repository_id)
            if not repo_index:
                self.vector_store_svc.load_index(repository_id)
                repo_index = self.vector_store_svc._indices.get(repository_id)

            chunks = []
            if repo_index and repo_index.metadata_store:
                chunks = [CodeChunk(**meta) for meta in repo_index.metadata_store]

            self._bm25_cache[repository_id] = BM25Retriever(chunks)

        return self._bm25_cache[repository_id]

    def retrieve(
        self,
        repository_id: str,
        query: str,
        top_k: int = 5,
        candidate_k: int = 15,
        strategy: str = "hybrid_rerank"
    ) -> List[Tuple[CodeChunk, Dict[str, float]]]:
        """
        Executes multi-stage hybrid retrieval pipeline.
        Strategies:
            - 'vector_only': FAISS vector search only
            - 'hybrid': FAISS vector search + BM25 keyword search with RRF fusion
            - 'hybrid_rerank': Vector + BM25 + RRF + Cross-Encoder Reranker (Default)
        """
        logger.info(f"Retrieving for repo_id='{repository_id}', query='{query}', strategy='{strategy}', top_k={top_k}")

        # Stage 1: Vector Search Candidates
        vector_results = self.vector_store_svc.search(repository_id, query, top_k=candidate_k)
        
        # Stage 2: Keyword BM25 Candidates
        bm25_retriever = self.get_bm25_retriever(repository_id)
        bm25_results = bm25_retriever.search(query, top_k=candidate_k)

        logger.info(f"Retrieved {len(vector_results)} vector candidates and {len(bm25_results)} BM25 keyword candidates.")

        if strategy == "vector_only":
            results = []
            for rank, (chunk, v_score) in enumerate(vector_results[:top_k], start=1):
                diag = {
                    "vector_score": round(v_score, 4),
                    "keyword_score": 0.0,
                    "fusion_score": round(v_score, 4),
                    "reranker_score": round(v_score, 4),
                    "final_rank": rank
                }
                chunk.metadata.update(diag)
                results.append((chunk, diag))
            return results

        # Stage 3: Candidate Fusion via Reciprocal Rank Fusion (RRF)
        candidate_map: Dict[str, Tuple[CodeChunk, Dict[str, float]]] = {}

        # Process vector candidates
        for v_rank, (chunk, v_score) in enumerate(vector_results, start=1):
            rrf_score = 1.0 / (self.rrf_k + v_rank)
            candidate_map[chunk.chunk_id] = (
                chunk,
                {
                    "vector_score": round(v_score, 4),
                    "keyword_score": 0.0,
                    "fusion_score": round(rrf_score, 6),
                    "v_rank": v_rank,
                    "bm25_rank": 999
                }
            )

        # Process BM25 candidates
        for b_rank, (chunk, b_score) in enumerate(bm25_results, start=1):
            rrf_score = 1.0 / (self.rrf_k + b_rank)
            if chunk.chunk_id in candidate_map:
                existing_chunk, diag = candidate_map[chunk.chunk_id]
                diag["keyword_score"] = round(b_score, 4)
                diag["fusion_score"] = round(diag["fusion_score"] + rrf_score, 6)
                diag["bm25_rank"] = b_rank
            else:
                candidate_map[chunk.chunk_id] = (
                    chunk,
                    {
                        "vector_score": 0.0,
                        "keyword_score": round(b_score, 4),
                        "fusion_score": round(rrf_score, 6),
                        "v_rank": 999,
                        "bm25_rank": b_rank
                    }
                )

        fused_candidates = list(candidate_map.values())
        fused_candidates.sort(key=lambda x: x[1]["fusion_score"], reverse=True)

        if strategy == "hybrid":
            results = []
            for rank, (chunk, diag) in enumerate(fused_candidates[:top_k], start=1):
                diag_copy = dict(diag)
                diag_copy["reranker_score"] = diag_copy["fusion_score"]
                diag_copy["final_rank"] = rank
                chunk.metadata.update(diag_copy)
                results.append((chunk, diag_copy))
            return results

        # Stage 4: Cross-Encoder Reranking (hybrid_rerank)
        final_candidates = self.reranker.rerank(query, fused_candidates, top_k=top_k)
        logger.info(f"Reranked {len(fused_candidates)} fused candidates down to top {len(final_candidates)} context chunks.")
        return final_candidates


hybrid_retriever = HybridRetriever()


def get_hybrid_retriever() -> HybridRetriever:
    return hybrid_retriever
