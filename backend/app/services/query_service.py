from typing import Optional
from app.schemas.query import QueryRequest, QueryResponse, Citation
from app.services.repository_service import RepositoryService, get_repository_service
from app.services.vector_store import VectorStoreService, get_vector_store_service
from app.core.logging import logger


class QueryService:
    """Service processing natural language query retrieval against FAISS vector indices."""

    def __init__(self, repo_service: RepositoryService = None, vector_store_svc: VectorStoreService = None):
        self.repo_service = repo_service or get_repository_service()
        self.vector_store_svc = vector_store_svc or get_vector_store_service()

    def process_query(self, repo_id: str, request: QueryRequest) -> QueryResponse:
        repo = self.repo_service.get_repository_by_id(repo_id)
        if not repo:
            raise KeyError(f"Repository with id '{repo_id}' not found.")

        logger.info(f"Executing FAISS similarity search for repo_id={repo_id}: query='{request.query}'")

        search_results = self.vector_store_svc.search(repo_id, request.query, top_k=request.top_k)

        citations = []
        context_summaries = []

        for chunk, score in search_results:
            snippet_text = chunk.content[:300] + ("..." if len(chunk.content) > 300 else "")
            citations.append(Citation(
                file_path=chunk.file_path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                snippet=snippet_text
            ))
            context_summaries.append(f"- `{chunk.file_path}` (Lines {chunk.start_line}-{chunk.end_line}, score: {score:.3f})")

        if not citations:
            answer = f"No relevant code chunks found in repository '{repo.name}' for query '{request.query}'."
        else:
            refs = "\n".join(context_summaries[:4])
            answer = (
                f"Retrieved {len(citations)} relevant code chunks from repository '{repo.name}' "
                f"for query **'{request.query}'**:\n\n{refs}\n\n"
                f"Refer to the citations below for exact code snippets."
            )

        return QueryResponse(
            repository_id=repo_id,
            query=request.query,
            answer=answer,
            citations=citations
        )


query_service = QueryService()


def get_query_service() -> QueryService:
    return query_service
