import pytest
from app.services.rag_service import RAGService
from app.services.llm_service import MockLLMProvider
from app.schemas.chunk import CodeChunk
from app.schemas.repository import RepositoryCreate
from app.services.ingestion_service import IngestionService
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_context_construction_and_source_mapping():
    chunks_with_scores = [
        (
            CodeChunk(
                chunk_id="c1",
                repository_id="repo-1",
                file_path="src/middleware/auth.py",
                language="Python",
                symbol_type="function",
                symbol_name="authenticate_user",
                start_line=12,
                end_line=31,
                content="def authenticate_user(token):\n    return token == 'valid'",
                imports=["import jwt"]
            ),
            0.89
        )
    ]

    context_str = RAGService.build_context_string(chunks_with_scores)
    assert "src/middleware/auth.py" in context_str
    assert "L12-L31" in context_str
    assert "authenticate_user" in context_str
    assert "import jwt" in context_str

    user_prompt = RAGService.build_user_prompt("Where is auth implemented?", context_str)
    assert "Where is auth implemented?" in user_prompt
    assert "Retrieved Codebase Context:" in user_prompt

    sources = RAGService.map_sources(chunks_with_scores)
    assert len(sources) == 1
    assert sources[0].file_path == "src/middleware/auth.py"
    assert sources[0].start_line == 12
    assert sources[0].end_line == 31


def test_insufficient_context_handling():
    context_str = RAGService.build_context_string([])
    assert context_str == "NO CONTEXT AVAILABLE."

    llm = MockLLMProvider()
    response = llm.generate("User query with NO CONTEXT AVAILABLE.")
    assert "does not contain sufficient information" in response


def test_llm_failure_fallback():
    class FailingLLMProvider(MockLLMProvider):
        def generate(self, prompt: str, system_prompt: str = None) -> str:
            raise RuntimeError("API Connection Timeout")

    from app.services.llm_service import OpenAILLMProvider
    # OpenAILLMProvider with invalid key falls back gracefully
    provider = OpenAILLMProvider(api_key="invalid-key")
    ans = provider.generate("Test prompt")
    assert isinstance(ans, str)
    assert len(ans) > 0


def test_end_to_end_rag_query():
    # 1. Ingest repository
    create_res = client.post("/repositories", json={"url": "https://github.com/octocat/Hello-World"})
    assert create_res.status_code == 201
    repo_id = create_res.json()["id"]

    # 2. Query repository
    query_payload = {"query": "Where is authentication implemented?", "top_k": 3}
    response = client.post(f"/repositories/{repo_id}/query", json=query_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["repository_id"] == repo_id
    assert "answer" in data
    assert "citations" in data
    assert len(data["citations"]) >= 1
    assert data["citations"][0]["file_path"] == "README"
