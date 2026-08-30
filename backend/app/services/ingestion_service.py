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
from app.schemas.chunk import CodeChunk
from app.services.parser_service import get_parser_service
from app.services.chunker_service import get_chunker_service
from app.services.vector_store import get_vector_store_service
from app.services.graph_service import get_graph_service


class LanguageDetector:
    """Detects programming languages and configuration types based on file extensions and basenames."""

    EXTENSION_MAP: Dict[str, str] = {
        # Python
        ".py": "Python", ".pyw": "Python",
        # JavaScript / TypeScript / Web
        ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
        ".ts": "TypeScript", ".tsx": "TypeScript",
        ".html": "HTML", ".htm": "HTML", ".ejs": "HTML/EJS", ".pug": "HTML", ".hbs": "HTML",
        ".css": "CSS", ".scss": "SCSS", ".sass": "SCSS", ".less": "CSS",
        ".vue": "Vue", ".svelte": "Svelte",
        # Systems & Core Languages
        ".java": "Java", ".c": "C", ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".h": "C/C++", ".hpp": "C/C++",
        ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP", ".cs": "C#",
        ".swift": "Swift", ".kt": "Kotlin", ".kts": "Kotlin", ".scala": "Scala",
        # Scripts & Shell
        ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell", ".ps1": "PowerShell", ".bat": "Batch", ".cmd": "Batch",
        ".lua": "Lua", ".pl": "Perl", ".r": "R",
        # Database & Schemas
        ".sql": "SQL", ".prisma": "Prisma", ".graphql": "GraphQL", ".gql": "GraphQL",
        # Config & Documentation
        ".json": "Configuration", ".yaml": "Configuration", ".yml": "Configuration",
        ".toml": "Configuration", ".xml": "Configuration", ".env": "Configuration",
        ".properties": "Configuration", ".conf": "Configuration", ".ini": "Configuration",
        ".md": "Documentation", ".markdown": "Documentation", ".txt": "Documentation",
    }

    SPECIAL_BASENAMES: Dict[str, str] = {
        "DOCKERFILE": "Configuration",
        "MAKEFILE": "Configuration",
        "LICENSE": "Documentation",
        "README": "Documentation",
    }

    @classmethod
    def get_language(cls, file_path: str) -> Optional[str]:
        basename = os.path.basename(file_path).upper()
        if basename.startswith("README") or basename.startswith("LICENSE"):
            return "Documentation"
        if basename in cls.SPECIAL_BASENAMES:
            return cls.SPECIAL_BASENAMES[basename]
        ext = os.path.splitext(file_path)[1].lower()
        return cls.EXTENSION_MAP.get(ext, "Plain Text")


class FileScanner:
    """Scans and filters files in a repository directory while enforcing security limits."""

    BINARY_EXTENSIONS: Set[str] = {
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg", ".bmp", ".tiff",
        ".zip", ".tar", ".gz", ".7z", ".rar", ".bz2",
        ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
        ".exe", ".dll", ".so", ".dylib", ".bin", ".dat", ".out", ".app",
        ".woff", ".woff2", ".ttf", ".eot", ".otf",
        ".mp4", ".avi", ".mov", ".mp3", ".wav", ".flac", ".aac",
        ".pyc", ".pyo", ".pyd", ".class", ".o", ".obj",
        ".db", ".sqlite", ".sqlite3",
    }

    IGNORE_DIRS: Set[str] = {
        ".git", "node_modules", "venv", ".venv", "__pycache__", "dist",
        "build", "coverage", "target", ".next", ".cache"
    }

    IGNORE_FILES: Set[str] = {
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock", "poetry.lock"
    }

    MAX_FILE_SIZE_BYTES: int = 2 * 1024 * 1024  # 2 MB

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
        ext = os.path.splitext(file_name)[1].lower()
        if ext in cls.BINARY_EXTENSIONS:
            return False
        return True

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
        clean_url = url.strip()
        pattern = r"^https?://(www\.)?github\.com/[\w.-]+/[\w.-]+.*$"
        return bool(re.match(pattern, clean_url))

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
    """Orchestrates repository ingestion, scanning, parsing, chunking, and state recording."""

    def __init__(self, storage_base_dir: Optional[str] = None):
        self.storage_base_dir = storage_base_dir or settings.STORAGE_DIR
        self._registry: Dict[str, RepositoryResponse] = {}
        self._chunk_registry: Dict[str, List[CodeChunk]] = {}

    @staticmethod
    def extract_repo_name(url: str) -> str:
        clean_url = url.strip().rstrip("/")
        if clean_url.endswith(".git"):
            clean_url = clean_url[:-4]
        return clean_url.split("/")[-1]

    def ingest_github_repository(self, payload: RepositoryCreate, owner_id: str = "default_owner") -> RepositoryResponse:
        git_source = GitIngestionSource(payload.url, payload.branch)
        if not git_source.is_valid_github_url(payload.url):
            raise ValueError(f"Invalid GitHub repository URL format: {payload.url}")

        repo_id = str(uuid.uuid4())[:8]
        repo_name = self.extract_repo_name(payload.url)
        target_storage_dir = os.path.join(self.storage_base_dir, owner_id, repo_id)
        now = datetime.now(timezone.utc)

        try:
            git_source.prepare_repository(target_storage_dir)
            valid_files, languages = FileScanner.scan_directory(target_storage_dir)

            parser_svc = get_parser_service()
            chunker_svc = get_chunker_service()
            all_chunks: List[CodeChunk] = []

            for rel_file in valid_files:
                full_path = os.path.join(target_storage_dir, rel_file)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        raw_content = f.read()

                    lang = LanguageDetector.get_language(full_path) or "Plain Text"
                    symbols = parser_svc.parse_file(repo_id, rel_file, raw_content, lang)
                    file_chunks = chunker_svc.create_chunks(repo_id, rel_file, symbols, raw_content, lang)
                    all_chunks.extend(file_chunks)
                except Exception as file_err:
                    logger.warning(f"Error parsing/chunking file {rel_file}: {file_err}")

            self._chunk_registry[repo_id] = all_chunks

            # Generate embeddings and store in FAISS vector store
            vector_store = get_vector_store_service()
            vector_store.index_repository(repo_id, all_chunks)

            # Build and store relationship graph
            graph_svc = get_graph_service()
            graph_svc.build_and_store_graph(repo_id, all_chunks)

            response = RepositoryResponse(
                id=repo_id,
                owner_id=owner_id,
                name=repo_name,
                url=payload.url,
                branch=payload.branch or "main",
                status="completed",
                storage_path=target_storage_dir,
                file_count=len(valid_files),
                chunk_count=len(all_chunks),
                detected_languages=languages,
                created_at=now,
                updated_at=now,
                message=f"Successfully ingested {len(valid_files)} files, indexed {len(all_chunks)} vectors in FAISS."
            )
            self._registry[repo_id] = response
            return response

        except Exception as e:
            response = RepositoryResponse(
                id=repo_id,
                owner_id=owner_id,
                name=repo_name,
                url=payload.url,
                branch=payload.branch,
                status="failed",
                storage_path=target_storage_dir,
                file_count=0,
                chunk_count=0,
                detected_languages=[],
                created_at=now,
                updated_at=now,
                message=str(e)
            )
            self._registry[repo_id] = response
            self._chunk_registry[repo_id] = []
            raise e

    def list_repositories(self, owner_id: Optional[str] = None, is_admin: bool = False) -> List[RepositoryResponse]:
        if is_admin or not owner_id:
            return list(self._registry.values())
        return [r for r in self._registry.values() if r.owner_id == owner_id]

    def get_repository(self, repo_id: str) -> Optional[RepositoryResponse]:
        return self._registry.get(repo_id)

    def get_repository_chunks(self, repo_id: str) -> List[CodeChunk]:
        return self._chunk_registry.get(repo_id, [])


# Global singleton instance for service dependency injection
ingestion_service = IngestionService()


def get_ingestion_service() -> IngestionService:
    return ingestion_service
