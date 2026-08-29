import os
import shutil
import tempfile
import pytest
from app.schemas.chunk import CodeChunk
from app.retrieval.tokenizer import CodeTokenizer
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.reranker import CrossEncoderReranker
from app.retrieval.hybrid_retriever import HybridRetriever
from app.services.embedding_service import MockEmbeddingProvider
from app.services.vector_store import VectorStoreService


def test_code_tokenizer_identifier_splitting():
    tokens = CodeTokenizer.tokenize("def authenticateUser(user_token: str): pass")
    assert "authenticateuser" in tokens or "authenticate" in tokens
    assert "user" in tokens
    assert "token" in tokens


def test_bm25_retriever_exact_symbol_match():
    chunks = [
        CodeChunk(chunk_id="c1", repository_id="repo1", file_path="auth.py", language="Python", symbol_type="function", symbol_name="authenticateUser", start_line=1, end_line=10, content="def authenticateUser(): pass"),
        CodeChunk(chunk_id="c2", repository_id="repo1", file_path="db.py", language="Python", symbol_type="function", symbol_name="connectDatabase", start_line=1, end_line=10, content="def connectDatabase(): pass")
    ]
    retriever = BM25Retriever(chunks)
    results = retriever.search("Where is authenticateUser defined?", top_k=2)

    assert len(results) >= 1
    matched_chunk, b_score = results[0]
    assert matched_chunk.symbol_name == "authenticateUser"
    assert b_score >= 0.0


def test_hybrid_retriever_pipeline_and_diagnostics():
    temp_dir = tempfile.mkdtemp()
    try:
        vec_svc = VectorStoreService(base_dir=temp_dir, embedding_provider=MockEmbeddingProvider(dim=64))
        chunks = [
            CodeChunk(chunk_id="c1", repository_id="repo-h", file_path="src/auth.js", language="JavaScript", symbol_type="function", symbol_name="authenticateUser", start_line=12, end_line=30, content="function authenticateUser(req, res) {}"),
            CodeChunk(chunk_id="c2", repository_id="repo-h", file_path="src/user.js", language="JavaScript", symbol_type="class", symbol_name="UserController", start_line=1, end_line=20, content="class UserController {}")
        ]
        vec_svc.index_repository("repo-h", chunks)

        retriever = HybridRetriever(vector_store_svc=vec_svc)
        results = retriever.retrieve("repo-h", "Where is authenticateUser defined?", top_k=2, strategy="hybrid_rerank")

        assert len(results) == 2
        top_chunk, diagnostics = results[0]

        # Verify diagnostics metadata preservation
        assert "vector_score" in diagnostics
        assert "keyword_score" in diagnostics
        assert "fusion_score" in diagnostics
        assert "reranker_score" in diagnostics
        assert "final_rank" in diagnostics
        assert diagnostics["final_rank"] == 1
        assert top_chunk.symbol_name == "authenticateUser"

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
