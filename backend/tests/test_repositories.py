from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_repository_success():
    payload = {"url": "https://github.com/octocat/Hello-World", "branch": "main"}
    response = client.post("/repositories", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Hello-World"
    assert data["status"] == "completed"


def test_create_repository_invalid_url():
    payload = {"url": "invalid-url"}
    response = client.post("/repositories", json=payload)
    assert response.status_code == 400
    assert "Invalid GitHub repository URL" in response.json()["detail"]


def test_list_and_get_repository():
    # Create repo
    create_res = client.post("/repositories", json={"url": "https://github.com/fastapi/fastapi"})
    repo_id = create_res.json()["id"]

    # List repos
    list_res = client.get("/repositories")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # Get by ID
    get_res = client.get(f"/repositories/{repo_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == repo_id


def test_get_nonexistent_repository():
    response = client.get("/repositories/nonexistent-id")
    assert response.status_code == 404
