import os
import re
import shutil
import tempfile
from typing import List, Tuple
import git
from app.core.logging import logger


class GitService:
    """Service to safely clone GitHub repositories and discover source files."""

    ALLOWED_EXTENSIONS = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cpp", ".h", ".hpp",
        ".cs", ".go", ".rs", ".php", ".rb", ".swift", ".kt", ".scala", ".md",
        ".html", ".css", ".json", ".yaml", ".yml", ".toml", ".sql", ".sh"
    }

    IGNORE_DIRS = {
        ".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build",
        ".next", ".target", "vendor", "coverage", ".pytest_cache"
    }

    @staticmethod
    def is_valid_github_url(url: str) -> bool:
        """Validates if the provided string is a valid GitHub URL."""
        pattern = r"^https?://(www\.)?github\.com/[\w.-]+/[\w.-]+(\.git)?/?$"
        return bool(re.match(pattern, url.strip()))

    @staticmethod
    def extract_repo_name(url: str) -> str:
        """Extracts repo name from GitHub URL."""
        clean_url = url.strip().rstrip("/")
        if clean_url.endswith(".git"):
            clean_url = clean_url[:-4]
        return clean_url.split("/")[-1]

    def clone_repository(self, repo_url: str, target_dir: str, branch: str = None) -> str:
        """Clones a GitHub repository safely into target_dir."""
        if not self.is_valid_github_url(repo_url):
            raise ValueError(f"Invalid GitHub URL format: {repo_url}")

        if os.path.exists(target_dir):
            logger.info(f"Removing existing target directory: {target_dir}")
            shutil.rmtree(target_dir, ignore_errors=True)

        os.makedirs(target_dir, exist_ok=True)
        logger.info(f"Cloning {repo_url} into {target_dir}")

        clone_kwargs = {"depth": 1}
        if branch:
            clone_kwargs["branch"] = branch

        try:
            git.Repo.clone_from(repo_url, target_dir, **clone_kwargs)
            logger.info(f"Successfully cloned {repo_url}")
            return target_dir
        except Exception as e:
            logger.error(f"Failed to clone repository {repo_url}: {str(e)}")
            raise RuntimeError(f"Git clone failed: {str(e)}")

    def discover_files(self, repo_dir: str) -> List[str]:
        """Discovers relevant code and text source files in the repository."""
        discovered_files: List[str] = []

        for root, dirs, files in os.walk(repo_dir):
            # Exclude ignored directories
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in self.ALLOWED_EXTENSIONS:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, repo_dir)
                    discovered_files.append(rel_path)

        logger.info(f"Discovered {len(discovered_files)} source files in {repo_dir}")
        return discovered_files
