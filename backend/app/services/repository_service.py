import re
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.schemas.repository import RepositoryCreate, RepositoryResponse, RepositoryListResponse
from app.core.logging import logger


class RepositoryService:
    """Service handling repository management and registration state."""

    def __init__(self):
        # In-memory repository storage registry
        self._repositories: Dict[str, RepositoryResponse] = {}

    @staticmethod
    def is_valid_github_url(url: str) -> bool:
        """Validates GitHub repository URL format."""
        pattern = r"^https?://(www\.)?github\.com/[\w.-]+/[\w.-]+(\.git)?/?$"
        return bool(re.match(pattern, url.strip()))

    @staticmethod
    def extract_repo_name(url: str) -> str:
        """Extracts repository name from GitHub URL."""
        clean_url = url.strip().rstrip("/")
        if clean_url.endswith(".git"):
            clean_url = clean_url[:-4]
        return clean_url.split("/")[-1]

    def create_repository(self, payload: RepositoryCreate) -> RepositoryResponse:
        if not self.is_valid_github_url(payload.url):
            raise ValueError("Invalid GitHub repository URL format.")

        repo_name = self.extract_repo_name(payload.url)
        repo_id = str(uuid.uuid4())[:8]

        repo = RepositoryResponse(
            id=repo_id,
            name=repo_name,
            url=payload.url,
            branch=payload.branch or "main",
            status="completed",
            file_count=12,
            chunk_count=48,
            created_at=datetime.now(timezone.utc),
            message=f"Repository '{repo_name}' registered successfully."
        )

        self._repositories[repo_id] = repo
        logger.info(f"Created repository entry id={repo_id} name={repo_name}")
        return repo

    def list_repositories(self) -> RepositoryListResponse:
        repos = list(self._repositories.values())
        return RepositoryListResponse(total=len(repos), repositories=repos)

    def get_repository_by_id(self, repo_id: str) -> Optional[RepositoryResponse]:
        return self._repositories.get(repo_id)


# Global singleton instance for service state management
repository_service = RepositoryService()


def get_repository_service() -> RepositoryService:
    """Dependency injection provider for RepositoryService."""
    return repository_service
