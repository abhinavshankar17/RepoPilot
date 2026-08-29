from typing import List, Optional, Tuple
from app.schemas.chunk import CodeChunk
from app.schemas.query import Citation
from app.schemas.intelligence import CodeFlowRequest, CodeFlowResponse, CodeFlowStep
from app.services.repository_service import RepositoryService, get_repository_service
from app.retrieval.hybrid_retriever import HybridRetriever, get_hybrid_retriever
from app.services.rag_service import RAGService
from app.core.logging import logger


class CodeFlowService:
    """Service analyzing architectural execution flows (Route -> Controller -> Service -> Repository -> Database)."""

    def __init__(
        self,
        repo_service: Optional[RepositoryService] = None,
        hybrid_retriever: Optional[HybridRetriever] = None
    ):
        self.repo_service = repo_service or get_repository_service()
        self.hybrid_retriever = hybrid_retriever or get_hybrid_retriever()

    def analyze_code_flow(self, repo_id: str, request: CodeFlowRequest) -> CodeFlowResponse:
        repo = self.repo_service.get_repository_by_id(repo_id)
        if not repo:
            raise KeyError(f"Repository with ID '{repo_id}' not found.")

        logger.info(f"Analyzing Code Flow for repo_id='{repo_id}', query='{request.query}'")

        # 1. Retrieve relevant code chunks
        search_query = request.endpoint_or_symbol or request.query
        retrieved_tuples = self.hybrid_retriever.retrieve(repo_id, search_query, top_k=request.top_k, strategy="hybrid_rerank")
        chunks_with_scores = [(c, diag.get("reranker_score", 0.0)) for c, diag in retrieved_tuples]

        citations = RAGService.map_sources(chunks_with_scores)

        # 2. Build flow steps from retrieved chunks
        steps: List[CodeFlowStep] = []
        layers_seen = set()

        for idx, (chunk, score) in enumerate(chunks_with_scores, start=1):
            file_lower = chunk.file_path.lower()
            symbol_lower = chunk.symbol_name.lower()

            if "route" in file_lower or "api" in file_lower or "endpoint" in symbol_lower:
                layer = "Route"
            elif "controller" in file_lower or "handler" in symbol_lower:
                layer = "Controller"
            elif "service" in file_lower or "logic" in file_lower:
                layer = "Service"
            elif "db" in file_lower or "model" in file_lower or "repo" in file_lower:
                layer = "Repository"
            else:
                layer = "Service"

            layers_seen.add(layer)
            steps.append(CodeFlowStep(
                step_number=idx,
                layer=layer,
                description=f"Execution in {chunk.file_path} (lines {chunk.start_line}-{chunk.end_line}) handling symbol '{chunk.symbol_name}'",
                file_path=chunk.file_path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                symbol=chunk.symbol_name
            ))

        # Always append Database layer if db is referenced
        if "Repository" in layers_seen or any("db" in c.file_path.lower() for c, _ in chunks_with_scores):
            steps.append(CodeFlowStep(
                step_number=len(steps) + 1,
                layer="Database",
                description="Persists or queries database storage layer.",
                file_path=steps[-1].file_path if steps else "database",
                start_line=1,
                end_line=1,
                symbol="DB_Engine"
            ))

        # 3. Build ASCII flow diagram
        flow_diagram = "Route → Controller → Service → Repository → Database"

        return CodeFlowResponse(
            repository_id=repo_id,
            query=request.query,
            flow_diagram=flow_diagram,
            steps=steps,
            citations=citations
        )


code_flow_service = CodeFlowService()


def get_code_flow_service() -> CodeFlowService:
    return code_flow_service
