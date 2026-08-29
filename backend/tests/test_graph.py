import pytest
from app.schemas.chunk import CodeChunk
from app.graph.graph_extractor import GraphExtractor
from app.services.graph_service import GraphService
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_graph_extraction_and_relations():
    chunks = [
        CodeChunk(
            chunk_id="c1",
            repository_id="repo-graph-test",
            file_path="src/auth.js",
            language="JavaScript",
            symbol_type="function",
            symbol_name="authenticateUser",
            start_line=10,
            end_line=30,
            content="export function authenticateUser(token) { verifyToken(token); }",
            imports=["import { verifyToken } from './jwt';"]
        ),
        CodeChunk(
            chunk_id="c2",
            repository_id="repo-graph-test",
            file_path="src/jwt.js",
            language="JavaScript",
            symbol_type="function",
            symbol_name="verifyToken",
            start_line=1,
            end_line=15,
            content="export function verifyToken(t) { return true; }",
            imports=[]
        )
    ]

    graph = GraphExtractor.extract_graph("repo-graph-test", chunks)

    # 1. Verify Node Creation
    assert "file:src/auth.js" in graph.nodes
    assert "symbol:src/auth.js:authenticateUser" in graph.nodes

    # 2. Verify DEFINES edges
    defines_edges = [e for e in graph.edges if e.relation_type == "DEFINES"]
    assert len(defines_edges) >= 2

    # 3. Verify IMPORTS edges
    imports_edges = [e for e in graph.edges if e.relation_type == "IMPORTS"]
    assert len(imports_edges) >= 1
    assert imports_edges[0].source_id == "file:src/auth.js"

    # 4. Verify CALLS edges
    calls_edges = [e for e in graph.edges if e.relation_type == "CALLS"]
    assert len(calls_edges) >= 1
    assert calls_edges[0].source_id == "symbol:src/auth.js:authenticateUser"
    assert calls_edges[0].target_id == "symbol:src/jwt.js:verifyToken"


def test_graph_service_dependencies_and_call_chain(tmp_path):
    svc = GraphService(base_storage_dir=str(tmp_path))
    chunks = [
        CodeChunk(
            chunk_id="c1",
            repository_id="repo-svc-test",
            file_path="auth.js",
            language="JavaScript",
            symbol_type="function",
            symbol_name="loginUser",
            start_line=1,
            end_line=10,
            content="function loginUser() { checkPassword(); }",
            imports=[]
        ),
        CodeChunk(
            chunk_id="c2",
            repository_id="repo-svc-test",
            file_path="auth.js",
            language="JavaScript",
            symbol_type="function",
            symbol_name="checkPassword",
            start_line=12,
            end_line=20,
            content="function checkPassword() {}",
            imports=[]
        )
    ]

    graph = svc.build_and_store_graph("repo-svc-test", chunks)

    # Find dependencies for loginUser
    deps = svc.find_dependencies("repo-svc-test", "loginUser")
    assert len(deps) >= 1

    # Trace call chain
    chain = svc.trace_call_chain("repo-svc-test", "loginUser")
    assert len(chain) >= 1
    assert chain[0].relation_type == "CALLS"


def test_vector_vs_graph_evidence_demarcation():
    # 1. Ingest repo
    create_res = client.post("/repositories", json={"url": "https://github.com/octocat/Hello-World"})
    repo_id = create_res.json()["id"]

    # 2. Query code flow
    flow_res = client.post(f"/repositories/{repo_id}/flow", json={"query": "Explain authentication flow"})
    assert flow_res.status_code == 200
    data = flow_res.json()

    assert "steps" in data
    assert len(data["steps"]) >= 1
    assert "[Vector & Graph Evidence]" in data["steps"][0]["description"]
