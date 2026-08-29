import os
import shutil
import tempfile
import pytest
from app.services.ingestion_service import (
    GitIngestionSource,
    LanguageDetector,
    FileScanner,
    IngestionService
)
from app.schemas.repository import RepositoryCreate


def test_valid_and_invalid_github_url():
    assert GitIngestionSource.is_valid_github_url("https://github.com/octocat/Hello-World") is True
    assert GitIngestionSource.is_valid_github_url("https://github.com/octocat/Hello-World.git") is True
    assert GitIngestionSource.is_valid_github_url("http://github.com/fastapi/fastapi/") is True
    
    assert GitIngestionSource.is_valid_github_url("https://evil.com/repo") is False
    assert GitIngestionSource.is_valid_github_url("not-a-url") is False
    assert GitIngestionSource.is_valid_github_url("") is False


def test_language_detector():
    assert LanguageDetector.get_language("main.py") == "Python"
    assert LanguageDetector.get_language("App.tsx") == "TypeScript"
    assert LanguageDetector.get_language("index.js") == "JavaScript"
    assert LanguageDetector.get_language("main.go") == "Go"
    assert LanguageDetector.get_language("lib.rs") == "Rust"
    assert LanguageDetector.get_language("Main.java") == "Java"
    assert LanguageDetector.get_language("README.md") == "Documentation"
    assert LanguageDetector.get_language("config.json") == "Configuration"
    assert LanguageDetector.get_language("unknown.xyz") is None


def test_file_scanner_filtering_and_limits():
    temp_dir = tempfile.mkdtemp()
    try:
        # 1. Valid files
        with open(os.path.join(temp_dir, "app.py"), "w", encoding="utf-8") as f:
            f.write("print('hello')\n")

        with open(os.path.join(temp_dir, "index.ts"), "w", encoding="utf-8") as f:
            f.write("console.log('hi');\n")

        # 2. Ignored directory
        venv_dir = os.path.join(temp_dir, "venv")
        os.makedirs(venv_dir, exist_ok=True)
        with open(os.path.join(venv_dir, "ignored.py"), "w", encoding="utf-8") as f:
            f.write("# ignored\n")

        # 3. Lock file (ignored)
        with open(os.path.join(temp_dir, "package-lock.json"), "w", encoding="utf-8") as f:
            f.write("{}\n")

        # 4. Binary file (ignored)
        with open(os.path.join(temp_dir, "image.py"), "wb") as f:
            f.write(b"PNG\x00\x01\x02")

        # 5. Oversized file (ignored > 1MB)
        large_file = os.path.join(temp_dir, "large.py")
        with open(large_file, "wb") as f:
            f.seek(1 * 1024 * 1024 + 100)
            f.write(b"a")

        valid_files, languages = FileScanner.scan_directory(temp_dir)

        # Should only contain app.py and index.ts
        assert len(valid_files) == 2
        assert "app.py" in valid_files or os.path.join("app.py") in valid_files
        assert "index.ts" in valid_files or os.path.join("index.ts") in valid_files
        assert sorted(languages) == ["Python", "TypeScript"]

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_ingestion_service_clone_failure_handling():
    temp_storage = tempfile.mkdtemp()
    try:
        svc = IngestionService(storage_base_dir=temp_storage)
        payload = RepositoryCreate(url="https://github.com/nonexistent-org-12345/nonexistent-repo-99999.git")
        
        with pytest.raises(RuntimeError):
            svc.ingest_github_repository(payload)

        # Verify failed status was recorded in service
        repos = svc.list_repositories()
        assert len(repos) == 1
        assert repos[0].status == "failed"
        assert repos[0].file_count == 0

    finally:
        shutil.rmtree(temp_storage, ignore_errors=True)
