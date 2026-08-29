import os
import re
import shutil
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Set, Tuple, Optional

import git
from app.core.config import settings
from app.core.logging import logger
from app.schemas.repository import RepositoryCreate, RepositoryResponse


class LanguageDetector:
    """Detects programming languages and configuration types based on file extensions and basenames."""

    EXTENSION_MAP: Dict[str, str] = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".java": "Java",
        ".c": "C/C++",
        ".cpp": "C/C++",
        ".h": "C/C++",
        ".hpp": "C/C++",
        ".go": "Go",
        ".rs": "Rust",
        ".md": "Documentation",
        ".json": "Configuration",
        ".yaml": "Configuration",
        ".yml": "Configuration",
        ".toml": "Configuration",
    }

    SPECIAL_BASENAMES: Dict[str, str] = {
        "DOCKERFILE": "Configuration",
        "MAKEFILE": "Configuration",
    }

    @classmethod
    def get_language(cls, file_path: str) -> Optional[str]:
        basename = os.path.basename(file_path).upper()
        if basename.startswith("README") or basename.startswith("LICENSE"):
            return "Documentation"
        if basename in cls.SPECIAL_BASENAMES:
            return cls.SPECIAL_BASENAMES[basename]
        ext = os.path.splitext(file_path)[1].lower()
        return cls.EXTENSION_MAP.get(ext)


class FileScanner:
    """Scans and filters files in a repository directory while enforcing security limits."""

    ALLOWED_EXTENSIONS: Set[str] = set(LanguageDetector.EXTENSION_MAP.keys())

    IGNORE_DIRS: Set[str] = {
        ".git", "node_modules", "venv", ".venv", "__pycache__", "dist",
        "build", "coverage", "target", ".next", ".cache"
    }

    IGNORE_FILES: Set[str] = {
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock", "poetry.lock"
    }

    MAX_FILE_SIZE_BYTES: int = 1 * 1024 * 1024  # 1 MB

    @classmethod
    def is_binary_file(cls, file_path: str) -> bool:
        """Checks if a file is binary by scanning for null bytes in initial chunk."""
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                return b"\x00" in chunk
        except Exception:
            return True

    @classmethod
    def is_allowed_file(cls, file_name: str) -> bool:
        upper_name = file_name.upper()
        if upper_name.startswith("README") or upper_name.startswith("LICENSE"):
            return True
        if upper_name in {"DOCKERFILE", "MAKEFILE"}:
            return True
        ext = os.path.splitext(file_name)[1].lower()
        return ext in cls.ALLOWED_EXTENSIONS

    @classmethod
    def scan_directory(cls, repo_dir: str) -> Tuple[List[str], List[str]]:
        """
        Scans a repository directory safely.
        Returns:
            Tuple of (list of valid relative file paths, sorted list of detected language names)
        """
        valid_rel_files: List[str] = []
        detected_languages: Set[str] = set()

        abs_repo_dir = os.path.abspath(repo_dir)

        for root, dirs, files in os.walk(abs_repo_dir):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in cls.IGNORE_DIRS]

            for file in files:
                if file in cls.IGNORE_FILES:
                    continue

                if not cls.is_allowed_file(file):
                    continue

                full_path = os.path.abspath(os.path.join(root, file))

                # Security check: prevent path traversal outside repo root
                if not full_path.startswith(abs_repo_dir):
                    logger.warning(f"Path traversal attempt detected: {full_path}")
                    continue

                # File size limit check
                try:
                    if os.path.getsize(full_path) > cls.MAX_FILE_SIZE_BYTES:
                        logger.info(f"Skipping file exceeding size limit: {full_path}")
                        continue
                except OSError:
                    continue

                # Binary file check
                if cls.is_binary_file(full_path):
                    logger.info(f"Skipping binary file: {full_path}")
                    continue

                rel_path = os.path.relpath(full_path, abs_repo_dir)
                valid_rel_files.append(rel_path)

                lang = LanguageDetector.get_language(full_path)
                if lang:
                    detected_languages.add(lang)

        return valid_rel_files, sorted(list(detected_languages))


class BaseIngestionSource(ABC):
    """Abstract ingestion source to support Git cloning, ZIP uploads, etc."""

    @abstractmethod
    def prepare_repository(self, target_dir: str) -> str:
        pass


class GitIngestionSource(BaseIngestionSource):
    """Git repository ingestion source."""

    def __init__(self, repo_url: str, branch: Optional[str] = None):
        self.repo_url = repo_url
        self.branch = branch

    @staticmethod
    def is_valid_github_url(url: str) -> bool:
        """Validates if the URL is a safe, properly formatted GitHub URL."""
        if not url or not isinstance(url, str):
            return False
        pattern = r"^https?://(www\.)?github\.com/[\w.-]+/[\w.-]+(\.git)?/?$"
        return bool(re.match(pattern, url.strip()))

    def prepare_repository(self, target_dir: str) -> str:
        if not self.is_valid_github_url(self.repo_url):
            raise ValueError(f"Invalid GitHub repository URL: {self.repo_url}")

        os.makedirs(target_dir, exist_ok=True)
        clone_kwargs = {"depth": 1}
        if self.branch:
            clone_kwargs["branch"] = self.branch

        try:
            logger.info(f"Cloning {self.repo_url} (branch: {self.branch or 'default'}) into {target_dir}")
            if self.branch:
                try:
                    git.Repo.clone_from(self.repo_url, target_dir, depth=1, branch=self.branch)
                    return target_dir
                except Exception as branch_err:
                    logger.warning(f"Branch '{self.branch}' not found for {self.repo_url}. Retrying with default branch...")
                    if os.path.exists(target_dir):
                        shutil.rmtree(target_dir, ignore_errors=True)
                    os.makedirs(target_dir, exist_ok=True)
            
            git.Repo.clone_from(self.repo_url, target_dir, depth=1)
            return target_dir
        except Exception as e:
            # Clean up temporary directory on failure
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir, ignore_errors=True)
            logger.error(f"Git clone failed for {self.repo_url}: {str(e)}")
            raise RuntimeError(f"Failed to clone repository: {str(e)}")


class IngestionService:
    """Orchestrates repository ingestion, scanning, and state recording."""

    def __init__(self, storage_base_dir: Optional[str] = None):
        self.storage_base_dir = storage_base_dir or settings.STORAGE_DIR
        self._registry: Dict[str, RepositoryResponse] = {}

    @staticmethod
    def extract_repo_name(url: str) -> str:
        clean_url = url.strip().rstrip("/")
        if clean_url.endswith(".git"):
            clean_url = clean_url[:-4]
        return clean_url.split("/")[-1]

    def ingest_github_repository(self, payload: RepositoryCreate) -> RepositoryResponse:
        git_source = GitIngestionSource(payload.url, payload.branch)
        if not git_source.is_valid_github_url(payload.url):
            raise ValueError(f"Invalid GitHub repository URL format: {payload.url}")

        repo_id = str(uuid.uuid4())[:8]
        repo_name = self.extract_repo_name(payload.url)
        target_storage_dir = os.path.join(self.storage_base_dir, repo_id)
        now = datetime.now(timezone.utc)

        try:
            git_source.prepare_repository(target_storage_dir)
            valid_files, languages = FileScanner.scan_directory(target_storage_dir)

            response = RepositoryResponse(
                id=repo_id,
                name=repo_name,
                url=payload.url,
                branch=payload.branch or "main",
                status="completed",
                storage_path=target_storage_dir,
                file_count=len(valid_files),
                detected_languages=languages,
                created_at=now,
                updated_at=now,
                message=f"Successfully ingested {len(valid_files)} files across {len(languages)} languages."
            )
            self._registry[repo_id] = response
            return response

        except Exception as e:
            # Record failed status if directory setup was attempted
            response = RepositoryResponse(
                id=repo_id,
                name=repo_name,
                url=payload.url,
                branch=payload.branch,
                status="failed",
                storage_path=target_storage_dir,
                file_count=0,
                detected_languages=[],
                created_at=now,
                updated_at=now,
                message=str(e)
            )
            self._registry[repo_id] = response
            raise e

    def list_repositories(self) -> List[RepositoryResponse]:
        return list(self._registry.values())

    def get_repository(self, repo_id: str) -> Optional[RepositoryResponse]:
        return self._registry.get(repo_id)


# Global singleton instance for service dependency injection
ingestion_service = IngestionService()


def get_ingestion_service() -> IngestionService:
    return ingestion_service
