from typing import List, Optional
from app.schemas.repository import RepositoryCreate, RepositoryResponse, RepositoryListResponse
from app.services.ingestion_service import IngestionService, get_ingestion_service


class RepositoryService:
    """Service wrapper for repository operations using IngestionService."""

    def __init__(self, ingestion_svc: IngestionService = None):
        self.ingestion_svc = ingestion_svc or get_ingestion_service()

    def create_repository(self, payload: RepositoryCreate) -> RepositoryResponse:
        return self.ingestion_svc.ingest_github_repository(payload)

    def list_repositories(self) -> RepositoryListResponse:
        repos = self.ingestion_svc.list_repositories()
        return RepositoryListResponse(total=len(repos), repositories=repos)

    def get_repository_by_id(self, repo_id: str) -> Optional[RepositoryResponse]:
        return self.ingestion_svc.get_repository(repo_id)


repository_service = RepositoryService()


def get_repository_service() -> RepositoryService:
    return repository_service
