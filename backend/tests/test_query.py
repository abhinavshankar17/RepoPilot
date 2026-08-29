from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_query_repository_success():
    # Register repo
    create_res = client.post("/repositories", json={"url": "https://github.com/octocat/Hello-World"})
    repo_id = create_res.json()["id"]

    # Execute query
    query_payload = {"query": "Where is authentication implemented?", "top_k": 3}
    response = client.post(f"/repositories/{repo_id}/query", json=query_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["repository_id"] == repo_id
    assert "answer" in data
    assert len(data["citations"]) > 0


def test_query_nonexistent_repository():
    query_payload = {"query": "Explain the login flow."}
    response = client.post("/repositories/nonexistent-id/query", json=query_payload)
    assert response.status_code == 404
