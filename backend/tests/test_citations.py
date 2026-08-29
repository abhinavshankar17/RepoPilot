import pytest
from app.services.rag_service import RAGService
from app.schemas.chunk import CodeChunk
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_precise_citation_mapping_fields():
    chunk = CodeChunk(
        chunk_id="src/auth.js:authenticateUser:12-31",
        repository_id="repo-123",
        file_path="src/auth.js",
        language="JavaScript",
        symbol_type="function",
        symbol_name="authenticateUser",
        start_line=12,
        end_line=31,
        content="function authenticateUser(req, res) { return true; }"
    )
    chunks_with_scores = [(chunk, 0.9123)]

    citations = RAGService.map_sources(chunks_with_scores)
    assert len(citations) == 1
    c = citations[0]

    assert c.chunk_id == "src/auth.js:authenticateUser:12-31"
    assert c.file_path == "src/auth.js"
    assert c.symbol == "authenticateUser"
    assert c.start_line == 12
    assert c.end_line == 31
    assert c.language == "JavaScript"
    assert c.score == 0.9123
    assert "function authenticateUser" in c.snippet


def test_safe_file_retrieval_and_line_range():
    # 1. Ingest repo
    create_res = client.post("/repositories", json={"url": "https://github.com/octocat/Hello-World"})
    assert create_res.status_code == 201
    repo_id = create_res.json()["id"]

    # 2. Retrieve README file content
    file_res = client.get(f"/repositories/{repo_id}/files/README")
    assert file_res.status_code == 200
    data = file_res.json()
    assert data["repository_id"] == repo_id
    assert data["file_path"] == "README"
    assert "Hello World!" in data["content"]
    assert data["start_line"] == 1

    # 3. Retrieve with line range slicing
    sliced_res = client.get(f"/repositories/{repo_id}/files/README?start_line=1&end_line=1")
    assert sliced_res.status_code == 200
    sliced_data = sliced_res.json()
    assert sliced_data["start_line"] == 1
    assert sliced_data["end_line"] == 1


def test_path_traversal_attack_prevention():
    create_res = client.post("/repositories", json={"url": "https://github.com/octocat/Hello-World"})
    repo_id = create_res.json()["id"]

    from app.services.repository_service import get_repository_service
    repo_service = get_repository_service()

    # Test direct service path traversal protection
    with pytest.raises(PermissionError):
        repo_service.get_repository_file_content(repo_id, "../../../../etc/passwd")

    with pytest.raises(PermissionError):
        repo_service.get_repository_file_content(repo_id, "..\\..\\..\\windows\\system32\\hosts")

    # Test URL encoded path traversal request
    res = client.get(f"/repositories/{repo_id}/files/%2E%2E%2F%2E%2E%2Fetc%2Fpasswd")
    assert res.status_code in (403, 404)


def test_invalid_file_path_404():
    create_res = client.post("/repositories", json={"url": "https://github.com/octocat/Hello-World"})
    repo_id = create_res.json()["id"]

    res = client.get(f"/repositories/{repo_id}/files/nonexistent_file.py")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"]
