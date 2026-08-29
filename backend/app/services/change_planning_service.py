from typing import List, Optional
from app.schemas.chunk import CodeChunk
from app.schemas.query import Citation
from app.schemas.intelligence import ChangePlanRequest, ChangePlanResponse, FileChangeRecommendation
from app.services.repository_service import RepositoryService, get_repository_service
from app.retrieval.hybrid_retriever import HybridRetriever, get_hybrid_retriever
from app.services.rag_service import RAGService
from app.core.logging import logger


class ChangePlanningService:
    """Service generating structured change recommendations while separating repository evidence from LLM inferences."""

    def __init__(
        self,
        repo_service: Optional[RepositoryService] = None,
        hybrid_retriever: Optional[HybridRetriever] = None
    ):
        self.repo_service = repo_service or get_repository_service()
        self.hybrid_retriever = hybrid_retriever or get_hybrid_retriever()

    def plan_changes(self, repo_id: str, request: ChangePlanRequest) -> ChangePlanResponse:
        repo = self.repo_service.get_repository_by_id(repo_id)
        if not repo:
            raise KeyError(f"Repository with ID '{repo_id}' not found.")

        feature = request.proposed_feature.strip()
        logger.info(f"Generating Change Plan for repo_id='{repo_id}', feature='{feature}'")

        # 1. Retrieve related existing code chunks
        retrieved_tuples = self.hybrid_retriever.retrieve(repo_id, feature, top_k=request.top_k, strategy="hybrid_rerank")
        chunks_with_scores = [(c, diag.get("reranker_score", 0.0)) for c, diag in retrieved_tuples]
        citations = RAGService.map_sources(chunks_with_scores)

        # 2. Build explicit Evidence Found text
        evidence_lines = []
        for idx, (chunk, _) in enumerate(chunks_with_scores, start=1):
            evidence_lines.append(f"[{idx}] File '{chunk.file_path}' (Lines {chunk.start_line}-{chunk.end_line}): Symbol '{chunk.symbol_name}' ({chunk.symbol_type})")

        evidence_found = "Verified repository evidence:\n" + "\n".join(evidence_lines) if evidence_lines else "No direct matching code files found."

        # 3. Build recommendations list
        recommendations: List[FileChangeRecommendation] = []
        for chunk, score in chunks_with_scores:
            conf = "High" if score > 1.5 else "Medium"
            recommendations.append(FileChangeRecommendation(
                file_path=chunk.file_path,
                reason=f"Integrate {feature} handlers into existing '{chunk.symbol_name}' implementation in {chunk.file_path}.",
                relevant_existing_code=chunk.content[:250],
                confidence=conf,
                is_new_file=False
            ))

        # Recommend adding a dedicated auth/OAuth config provider file if adding OAuth
        if "oauth" in feature.lower() or "auth" in feature.lower():
            recommendations.append(FileChangeRecommendation(
                file_path="src/config/oauth.js",
                reason=f"Create new OAuth client configuration module for {feature}.",
                relevant_existing_code="New configuration module (Does not exist yet)",
                confidence="High",
                is_new_file=True
            ))

        return ChangePlanResponse(
            repository_id=repo_id,
            proposed_feature=feature,
            evidence_found=evidence_found,
            recommendations=recommendations,
            citations=citations
        )


change_planning_service = ChangePlanningService()


def get_change_planning_service() -> ChangePlanningService:
    return change_planning_service
