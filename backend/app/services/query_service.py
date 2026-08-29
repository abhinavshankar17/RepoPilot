from typing import Optional
from app.schemas.query import QueryRequest, QueryResponse, Citation
from app.services.repository_service import RepositoryService, get_repository_service
from app.core.logging import logger


class QueryService:
    """Service handling natural language query execution over indexed repositories."""

    def __init__(self, repo_service: RepositoryService = None):
        self.repo_service = repo_service or get_repository_service()

    def process_query(self, repo_id: str, request: QueryRequest) -> QueryResponse:
        repo = self.repo_service.get_repository_by_id(repo_id)
        if not repo:
            raise KeyError(f"Repository with id '{repo_id}' not found.")

        logger.info(f"Processing query for repo_id={repo_id}: {request.query}")

        # Placeholder grounded response for Phase 1 skeleton
        citations = [
            Citation(
                file_path=f"src/main.py",
                start_line=1,
                end_line=25,
                snippet="def initialize_app():\n    # Database connection & setup\n    pass"
            ),
            Citation(
                file_path=f"src/auth/jwt.py",
                start_line=10,
                end_line=45,
                snippet="def verify_jwt_token(token: str):\n    # JWT authentication logic\n    pass"
            )
        ]

        answer = (
            f"Based on the repository '{repo.name}', the functionality requested in query "
            f"'{request.query}' is implemented across core modules listed in the citations below."
        )

        return QueryResponse(
            repository_id=repo_id,
            query=request.query,
            answer=answer,
            citations=citations
        )


query_service = QueryService()


def get_query_service() -> QueryService:
    """Dependency injection provider for QueryService."""
    return query_service
