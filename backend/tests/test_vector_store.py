import os
import shutil
import tempfile
import pytest
from app.services.embedding_service import MockEmbeddingProvider
from app.services.vector_store import VectorStoreService, FaissRepositoryIndex
from app.schemas.chunk import CodeChunk


def test_embedding_provider_generation():
    provider = MockEmbeddingProvider(dim=128)
    assert provider.dimension == 128

    vecs = provider.embed_texts(["hello world", "foo bar"])
    assert len(vecs) == 2
    assert len(vecs[0]) == 128

    query_vec = provider.embed_query("search query")
    assert len(query_vec) == 128


def test_vector_store_indexing_and_search():
    temp_dir = tempfile.mkdtemp()
    try:
        svc = VectorStoreService(base_dir=temp_dir, embedding_provider=MockEmbeddingProvider(dim=64))

        chunks = [
            CodeChunk(
                chunk_id="chunk-1",
                repository_id="repo-1",
                file_path="src/auth.py",
                language="Python",
                symbol_type="function",
                symbol_name="authenticate_user",
                start_line=10,
                end_line=25,
                content="def authenticate_user(username, password): pass"
            ),
            CodeChunk(
                chunk_id="chunk-2",
                repository_id="repo-1",
                file_path="src/db.py",
                language="Python",
                symbol_type="function",
                symbol_name="connect_database",
                start_line=1,
                end_line=15,
                content="def connect_database(uri): pass"
            )
        ]

        count, dim = svc.index_repository("repo-1", chunks)
        assert count == 2
        assert dim == 64

        # Verify disk persistence files exist
        assert os.path.exists(os.path.join(temp_dir, "repo-1", "index.faiss"))
        assert os.path.exists(os.path.join(temp_dir, "repo-1", "metadata.json"))

        # Execute similarity search
        results = svc.search("repo-1", "authenticate_user", top_k=2)
        assert len(results) == 2
        matched_chunk, score = results[0]
        assert matched_chunk.repository_id == "repo-1"
        assert isinstance(score, float)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_persistence_and_reloading():
    temp_dir = tempfile.mkdtemp()
    try:
        svc_writer = VectorStoreService(base_dir=temp_dir, embedding_provider=MockEmbeddingProvider(dim=64))
        chunks = [
            CodeChunk(
                chunk_id="chunk-1",
                repository_id="repo-persisted",
                file_path="main.go",
                language="Go",
                symbol_type="function",
                symbol_name="main",
                start_line=1,
                end_line=10,
                content="package main\nfunc main() {}"
            )
        ]
        svc_writer.index_repository("repo-persisted", chunks)

        # Create a fresh service instance (simulating app restart)
        svc_reader = VectorStoreService(base_dir=temp_dir, embedding_provider=MockEmbeddingProvider(dim=64))
        loaded = svc_reader.load_index("repo-persisted")
        assert loaded is True

        results = svc_reader.search("repo-persisted", "main function", top_k=1)
        assert len(results) == 1
        assert results[0][0].symbol_name == "main"

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_repository_isolation():
    temp_dir = tempfile.mkdtemp()
    try:
        svc = VectorStoreService(base_dir=temp_dir, embedding_provider=MockEmbeddingProvider(dim=64))

        chunks_a = [CodeChunk(chunk_id="c1", repository_id="repoA", file_path="a.py", language="Python", symbol_type="function", symbol_name="funcA", start_line=1, end_line=5, content="def funcA(): pass")]
        chunks_b = [CodeChunk(chunk_id="c2", repository_id="repoB", file_path="b.py", language="Python", symbol_type="function", symbol_name="funcB", start_line=1, end_line=5, content="def funcB(): pass")]

        svc.index_repository("repoA", chunks_a)
        svc.index_repository("repoB", chunks_b)

        results_a = svc.search("repoA", "funcA", top_k=5)
        assert len(results_a) == 1
        assert results_a[0][0].repository_id == "repoA"

        results_b = svc.search("repoB", "funcA", top_k=5)
        assert len(results_b) == 1
        assert results_b[0][0].repository_id == "repoB"

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_empty_repo_and_deletion():
    temp_dir = tempfile.mkdtemp()
    try:
        svc = VectorStoreService(base_dir=temp_dir, embedding_provider=MockEmbeddingProvider(dim=64))

        # Index empty list
        count, dim = svc.index_repository("repo-empty", [])
        assert count == 0
        assert svc.search("repo-empty", "query", top_k=5) == []

        # Delete index
        deleted = svc.delete_index("repo-empty")
        assert deleted is True
        assert not os.path.exists(os.path.join(temp_dir, "repo-empty"))

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
