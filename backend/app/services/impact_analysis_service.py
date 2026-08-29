from typing import List, Optional
from app.schemas.chunk import CodeChunk
from app.schemas.query import Citation
from app.schemas.intelligence import ImpactAnalysisRequest, ImpactAnalysisResponse, ImpactDetail
from app.services.repository_service import RepositoryService, get_repository_service
from app.retrieval.hybrid_retriever import HybridRetriever, get_hybrid_retriever
from app.services.rag_service import RAGService
from app.core.logging import logger


class ImpactAnalysisService:
    """Service analyzing structural codebase dependencies and modification impacts."""

    def __init__(
        self,
        repo_service: Optional[RepositoryService] = None,
        hybrid_retriever: Optional[HybridRetriever] = None
    ):
        self.repo_service = repo_service or get_repository_service()
        self.hybrid_retriever = hybrid_retriever or get_hybrid_retriever()

    def analyze_impact(self, repo_id: str, request: ImpactAnalysisRequest) -> ImpactAnalysisResponse:
        repo = self.repo_service.get_repository_by_id(repo_id)
        if not repo:
            raise KeyError(f"Repository with ID '{repo_id}' not found.")

        target = request.target_file_or_symbol.strip()
        logger.info(f"Executing Impact Analysis for repo_id='{repo_id}', target='{target}'")

        # Retrieve candidates referencing the target
        retrieved_tuples = self.hybrid_retriever.retrieve(repo_id, target, top_k=request.top_k, strategy="hybrid_rerank")
        chunks_with_scores = [(c, diag.get("reranker_score", 0.0)) for c, diag in retrieved_tuples]
        citations = RAGService.map_sources(chunks_with_scores)

        impacts: List[ImpactDetail] = []

        for chunk, score in chunks_with_scores:
            content_lower = chunk.content.lower()

            # Identify impact category
            if any(imp.lower() in target.lower() for imp in chunk.imports):
                cat = "Imports"
                desc = f"File '{chunk.file_path}' explicitly imports '{target}'."
            elif "route" in chunk.file_path.lower() or "api" in chunk.file_path.lower():
                cat = "API Routes"
                desc = f"API Route in '{chunk.file_path}' relies on '{target}' functionality."
            elif chunk.symbol_type == "function" or "call" in content_lower:
                cat = "Function Calls"
                desc = f"Symbol '{chunk.symbol_name}' in '{chunk.file_path}' invokes methods from '{target}'."
            else:
                cat = "Dependent Modules"
                desc = f"Module '{chunk.file_path}' references symbols from '{target}'."

            chunk_citation = Citation(
                chunk_id=chunk.chunk_id,
                file_path=chunk.file_path,
                symbol=chunk.symbol_name,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                language=chunk.language,
                score=round(score, 4),
                snippet=chunk.content[:300]
            )

            impacts.append(ImpactDetail(
                category=cat,
                file_path=chunk.file_path,
                description=desc,
                citations=[chunk_citation]
            ))

        summary = (
            f"Modifying '{target}' could impact {len(impacts)} downstream module(s) "
            f"across imports, function calls, dependent services, and API routes."
        )

        return ImpactAnalysisResponse(
            repository_id=repo_id,
            target=target,
            summary=summary,
            impacts=impacts,
            citations=citations
        )


impact_analysis_service = ImpactAnalysisService()


def get_impact_analysis_service() -> ImpactAnalysisService:
    return impact_analysis_service
