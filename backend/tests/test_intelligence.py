import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_code_flow_analysis_endpoint():
    # 1. Ingest repository
    create_res = client.post("/repositories", json={"url": "https://github.com/octocat/Hello-World"})
    assert create_res.status_code == 201
    repo_id = create_res.json()["id"]

    # 2. Analyze code flow
    flow_payload = {"query": "Explain the request flow for POST /api/orders"}
    flow_res = client.post(f"/repositories/{repo_id}/flow", json=flow_payload)

    assert flow_res.status_code == 200
    data = flow_res.json()

    assert data["repository_id"] == repo_id
    assert "flow_diagram" in data
    assert "Route → Controller" in data["flow_diagram"]
    assert len(data["steps"]) >= 1
    assert data["steps"][0]["layer"] in ["Route", "Controller", "Service", "Repository", "Database"]
    assert len(data["citations"]) >= 1


def test_impact_analysis_endpoint():
    create_res = client.post("/repositories", json={"url": "https://github.com/octocat/Hello-World"})
    repo_id = create_res.json()["id"]

    impact_payload = {"target_file_or_symbol": "auth.js"}
    impact_res = client.post(f"/repositories/{repo_id}/impact", json=impact_payload)

    assert impact_res.status_code == 200
    data = impact_res.json()

    assert data["repository_id"] == repo_id
    assert data["target"] == "auth.js"
    assert "impacts" in data
    assert len(data["impacts"]) >= 1
    assert data["impacts"][0]["category"] in ["Imports", "References", "Function Calls", "Dependent Modules", "API Routes"]


def test_change_planning_endpoint():
    create_res = client.post("/repositories", json={"url": "https://github.com/octocat/Hello-World"})
    repo_id = create_res.json()["id"]

    plan_payload = {"proposed_feature": "I want to add Google OAuth"}
    plan_res = client.post(f"/repositories/{repo_id}/change-plan", json=plan_payload)

    assert plan_res.status_code == 200
    data = plan_res.json()

    assert data["repository_id"] == repo_id
    assert data["proposed_feature"] == "I want to add Google OAuth"

    # Verify clear distinction: Evidence found vs Recommendations
    assert "evidence_found" in data
    assert "Verified repository evidence" in data["evidence_found"] or "matching" in data["evidence_found"]

    assert "recommendations" in data
    assert len(data["recommendations"]) >= 1
    rec = data["recommendations"][0]
    assert "file_path" in rec
    assert "reason" in rec
    assert "confidence" in rec
    assert rec["confidence"] in ["High", "Medium", "Low"]
