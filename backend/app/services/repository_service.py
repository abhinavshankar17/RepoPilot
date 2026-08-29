import os
from typing import List, Optional
from app.schemas.repository import RepositoryCreate, RepositoryResponse, RepositoryListResponse, FileContentResponse
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

    def get_repository_file_content(
        self,
        repo_id: str,
        file_path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None
    ) -> FileContentResponse:
        repo = self.get_repository_by_id(repo_id)
        if not repo:
            raise KeyError(f"Repository '{repo_id}' not found.")

        storage_dir = os.path.abspath(repo.storage_path)
        target_path = os.path.abspath(os.path.join(storage_dir, file_path))

        # Strict Path Traversal Prevention
        try:
            if os.path.commonpath([storage_dir, target_path]) != storage_dir:
                raise PermissionError(f"Access denied: Path traversal attempt detected for file '{file_path}'")
        except ValueError:
            raise PermissionError(f"Access denied: Invalid path '{file_path}'")

        if not os.path.isfile(target_path):
            raise FileNotFoundError(f"File '{file_path}' not found in repository '{repo.name}'.")

        with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_content = f.read()

        lines = raw_content.splitlines()
        total_lines = len(lines)

        s_line = max(1, start_line) if start_line else 1
        e_line = min(total_lines, end_line) if end_line else max(1, total_lines)

        if s_line > total_lines:
            sliced_content = ""
        else:
            sliced_content = "\n".join(lines[s_line - 1 : e_line])

        return FileContentResponse(
            repository_id=repo_id,
            file_path=file_path,
            start_line=s_line,
            end_line=e_line,
            total_lines=total_lines,
            content=sliced_content
        )


repository_service = RepositoryService()


def get_repository_service() -> RepositoryService:
    return repository_service
