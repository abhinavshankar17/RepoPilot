import pytest
from app.services.parser_service import ParserService
from app.services.chunker_service import CodeAwareChunkerService, MarkdownChunker, LargeSymbolSplitter
from app.schemas.parser import CodeSymbol
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_normal_function_and_class_chunking():
    sample_code = '''class DatabaseManager:
    def __init__(self, uri: str):
        self.uri = uri

    def connect(self):
        return True

def standalone_helper(val: int) -> int:
    return val * 2
'''
    parser = ParserService()
    symbols = parser.parse_file("repo-1", "db.py", sample_code, "Python")

    chunker = CodeAwareChunkerService()
    chunks = chunker.create_chunks("repo-1", "db.py", symbols, sample_code, "Python")

    assert len(chunks) >= 3
    
    # Verify class symbol chunk
    class_chunks = [c for c in chunks if c.symbol_type == "class"]
    assert len(class_chunks) == 1
    assert class_chunks[0].symbol_name == "DatabaseManager"
    assert class_chunks[0].start_line == 1

    # Verify nested method chunk & parent symbol preservation
    method_chunks = [c for c in chunks if c.symbol_type == "method"]
    assert len(method_chunks) == 2
    assert method_chunks[0].parent_symbol == "DatabaseManager"

    # Verify standalone function chunk
    func_chunks = [c for c in chunks if c.symbol_type == "function"]
    assert len(func_chunks) == 1
    assert func_chunks[0].symbol_name == "standalone_helper"


def test_large_function_splitting():
    # Generate large function with 100 lines
    lines = ["def large_function():"] + [f"    x_{i} = {i}" for i in range(99)]
    large_code = "\n".join(lines)

    sym = CodeSymbol(
        repository_id="repo-1",
        file_path="large.py",
        language="Python",
        symbol_type="function",
        symbol_name="large_function",
        start_line=1,
        end_line=100,
        content=large_code
    )

    sub_chunks = LargeSymbolSplitter.split_symbol(sym, imports=["import os"])
    assert len(sub_chunks) > 1

    # Verify parent symbol and line range preservation
    for chunk in sub_chunks:
        assert "large_function" in chunk.symbol_name
        assert chunk.parent_symbol == "large_function"
        assert chunk.start_line >= 1
        assert chunk.end_line <= 100
        assert chunk.imports == ["import os"]


def test_markdown_section_chunking():
    md_content = '''# RepoPilot Documentation

Overview of the system architecture.

## Installation

Run `pip install -r requirements.txt`.

## Configuration

Set `.env` variables.
'''
    chunks = MarkdownChunker.chunk_markdown("repo-1", "README.md", md_content)
    assert len(chunks) == 3

    assert chunks[0].symbol_name == "RepoPilot Documentation"
    assert chunks[0].start_line == 1

    assert chunks[1].symbol_name == "Installation"
    assert chunks[1].start_line == 5

    assert chunks[2].symbol_name == "Configuration"
    assert chunks[2].start_line == 9


def test_unsupported_file_fallback_chunking():
    unsupported_content = "\n".join([f"log line {i}" for i in range(100)])
    chunker = CodeAwareChunkerService()
    chunks = chunker.create_chunks("repo-1", "output.log", [], unsupported_content, "Plain Text")

    assert len(chunks) == 3  # 100 lines divided by chunk size 40 -> 3 chunks
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 40
    assert chunks[1].start_line == 41
    assert chunks[1].end_line == 80
    assert chunks[2].start_line == 81
    assert chunks[2].end_line == 100


def test_chunk_inspection_endpoint():
    # 1. Register repo
    create_res = client.post("/repositories", json={"url": "https://github.com/octocat/Hello-World"})
    assert create_res.status_code == 201
    repo_id = create_res.json()["id"]

    # 2. Inspect chunks
    inspect_res = client.get(f"/repositories/{repo_id}/chunks")
    assert inspect_res.status_code == 200
    data = inspect_res.json()
    assert data["repository_id"] == repo_id
    assert "total_chunks" in data
    assert len(data["chunks"]) == data["total_chunks"]
