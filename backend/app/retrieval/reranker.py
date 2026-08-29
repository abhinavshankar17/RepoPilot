from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
from app.schemas.chunk import CodeChunk
from app.retrieval.tokenizer import CodeTokenizer
from app.core.logging import logger


class BaseReranker(ABC):
    """Abstract interface for candidate rerankers."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: List[Tuple[CodeChunk, Dict[str, float]]],
        top_k: int = 5
    ) -> List[Tuple[CodeChunk, Dict[str, float]]]:
        """Reranks candidate chunks and returns top K with updated score diagnostics."""
        pass


class CrossEncoderReranker(BaseReranker):
    """
    Reranker using cross-encoder feature scoring evaluating exact symbol matches,
    identifier occurrences, file path relevance, and query term coverage.
    """

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[CodeChunk, Dict[str, float]]],
        top_k: int = 5
    ) -> List[Tuple[CodeChunk, Dict[str, float]]]:
        if not candidates:
            return []

        query_terms = set(CodeTokenizer.tokenize(query))
        reranked_candidates = []

        for chunk, diagnostics in candidates:
            score_boost = 0.0
            raw_content_lower = chunk.content.lower()
            symbol_lower = chunk.symbol_name.lower()
            file_lower = chunk.file_path.lower()

            # 1. Exact Symbol / Identifier Match Boost
            for term in query_terms:
                if term == symbol_lower:
                    score_boost += 3.5  # High boost for exact symbol match
                elif term in symbol_lower:
                    score_boost += 1.5
                if term in file_lower:
                    score_boost += 1.0

            # 2. Term Coverage Ratio
            matched_terms = sum(1 for term in query_terms if term in raw_content_lower or term in symbol_lower or term in file_lower)
            coverage_ratio = matched_terms / max(1, len(query_terms))
            score_boost += coverage_ratio * 2.0

            # 3. Base Fusion Score
            fusion_score = diagnostics.get("fusion_score", 0.0)

            # Combined Cross-Encoder Reranker Score
            reranker_score = fusion_score * 1.5 + score_boost

            diag = dict(diagnostics)
            diag["reranker_score"] = round(reranker_score, 4)
            reranked_candidates.append((chunk, diag))

        # Sort descending by reranker_score
        reranked_candidates.sort(key=lambda x: x[1]["reranker_score"], reverse=True)

        # Assign final_rank
        final_results = []
        for rank, (chunk, diag) in enumerate(reranked_candidates[:top_k], start=1):
            diag_copy = dict(diag)
            diag_copy["final_rank"] = rank
            # Store diagnostics in chunk metadata for API/UI transparency
            chunk.metadata.update(diag_copy)
            final_results.append((chunk, diag_copy))

        return final_results
