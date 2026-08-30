import pytest
from app.core.security import SecurityUtils
from app.services.ingestion_service import GitIngestionSource
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_jwt_token_generation_and_verification():
    token = SecurityUtils.create_access_token(user_id="user123", username="testuser", role="user")
    assert isinstance(token, str)
    assert len(token.split(".")) == 3

    payload = SecurityUtils.verify_access_token(token)
    assert payload["sub"] == "user123"
    assert payload["username"] == "testuser"
    assert payload["role"] == "user"


def test_malicious_github_url_validation():
    # Insecure HTTP
    assert GitIngestionSource.is_valid_github_url("http://evil.com/repo") is False

    # SSRF / Internal IP targets
    assert GitIngestionSource.is_valid_github_url("https://127.0.0.1/repo") is False
    assert GitIngestionSource.is_valid_github_url("https://localhost/repo") is False
    assert GitIngestionSource.is_valid_github_url("https://169.254.169.254/repo") is False

    # Non-GitHub domain
    assert GitIngestionSource.is_valid_github_url("https://gitlab.com/user/repo") is False

    # Valid HTTPS GitHub URL
    assert GitIngestionSource.is_valid_github_url("https://github.com/octocat/Hello-World") is True


def test_multi_tenant_repository_isolation():
    # User A creates repository
    headers_a = {"X-User-ID": "userA", "X-User-Role": "user"}
    res_a = client.post("/repositories", json={"url": "https://github.com/octocat/Hello-World"}, headers=headers_a)
    assert res_a.status_code == 201
    repo_id_a = res_a.json()["id"]

    # User B attempts to access User A's repository
    headers_b = {"X-User-ID": "userB", "X-User-Role": "user"}
    access_b = client.get(f"/repositories/{repo_id_a}", headers=headers_b)
    assert access_b.status_code == 403
    assert "Access denied" in access_b.json()["detail"]

    # User B list repositories -> User A's repository must not be visible
    list_b = client.get("/repositories", headers=headers_b)
    assert list_b.status_code == 200
    repos_b = list_b.json()["repositories"]
    assert not any(r["id"] == repo_id_a for r in repos_b)

    # Admin access -> Admin can see User A's repository
    headers_admin = {"X-User-ID": "adminUser", "X-User-Role": "admin"}
    access_admin = client.get(f"/repositories/{repo_id_a}", headers=headers_admin)
    assert access_admin.status_code == 200


def test_error_message_sanitization():
    raw_error = "Failed to open C:\\Users\\abhin\\OneDrive\\Desktop\\Projects\\RepoPilot\\storage\\secret.key with key super-secret-jwt-key"
    sanitized = SecurityUtils.sanitize_error_message(raw_error)
    assert "super-secret-jwt-key" not in sanitized or "[REDACTED" in sanitized
    assert "[STORAGE_ROOT]" in sanitized
