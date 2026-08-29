import pytest
from app.services.session_service import SessionService
from app.retrieval.query_rewriter import QueryRewriter
from app.services.llm_service import MockLLMProvider
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_standalone_question_no_rewrite():
    rewriter = QueryRewriter(llm_provider=MockLLMProvider())
    history = []
    query = "Where is authentication implemented?"
    
    assert rewriter.needs_rewriting(query, history) is False
    rewritten = rewriter.rewrite_query(query, history)
    assert rewritten == query


def test_followup_ambiguous_reference_rewriting():
    rewriter = QueryRewriter(llm_provider=MockLLMProvider())
    history = [
        {"role": "user", "content": "How does authentication work in this repo?"},
        {"role": "assistant", "content": "JWT authentication is used in src/middleware/auth.js"}
    ]
    query = "Where is the token generated?"

    assert rewriter.needs_rewriting(query, history) is True
    rewritten = rewriter.rewrite_query(query, history)

    assert rewritten != query
    assert "JWT" in rewritten or "auth" in rewritten or "token" in rewritten


def test_session_history_window_limit():
    svc = SessionService(max_turns_per_session=2)
    session_id = "sess-window-test"

    # Add 4 turns (8 messages)
    svc.add_turn(session_id, "Q1", "A1")
    svc.add_turn(session_id, "Q2", "A2")
    svc.add_turn(session_id, "Q3", "A3")
    svc.add_turn(session_id, "Q4", "A4")

    history = svc.get_recent_history(session_id)
    # Should only keep last 2 turns (4 messages)
    assert len(history) == 4
    assert history[0]["content"] == "Q3"
    assert history[-1]["content"] == "A4"


def test_unrelated_topic_change_context_switch():
    rewriter = QueryRewriter(llm_provider=MockLLMProvider())
    history = [
        {"role": "user", "content": "How does authentication work?"},
        {"role": "assistant", "content": "JWT auth is used."}
    ]
    query = "Where is the database connection initialized?"

    # Completely new topic without ambiguous pronouns
    assert rewriter.needs_rewriting(query, history) is False
    rewritten = rewriter.rewrite_query(query, history)
    assert rewritten == query


def test_end_to_end_conversation_query_endpoint():
    # 1. Ingest repo
    create_res = client.post("/repositories", json={"url": "https://github.com/octocat/Hello-World"})
    repo_id = create_res.json()["id"]

    # Turn 1: Standalone question
    t1_payload = {"query": "How does authentication work?", "session_id": "sess-e2e-123"}
    t1_res = client.post(f"/repositories/{repo_id}/query", json=t1_payload)
    assert t1_res.status_code == 200
    t1_data = t1_res.json()

    assert t1_data["session_id"] == "sess-e2e-123"
    assert t1_data["original_query"] == "How does authentication work?"
    assert t1_data["rewritten_query"] == "How does authentication work?"

    # Turn 2: Follow-up question with ambiguous reference
    t2_payload = {"query": "Where is the token generated?", "session_id": "sess-e2e-123"}
    t2_res = client.post(f"/repositories/{repo_id}/query", json=t2_payload)
    assert t2_res.status_code == 200
    t2_data = t2_res.json()

    assert t2_data["session_id"] == "sess-e2e-123"
    assert t2_data["original_query"] == "Where is the token generated?"
    assert "token" in t2_data["rewritten_query"].lower()
