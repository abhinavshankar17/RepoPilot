from typing import List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    chunk_id: str = Field(..., description="Unique chunk identifier")
    file_path: str = Field(..., description="Relative path of the source file")
    symbol: Optional[str] = Field(default=None, description="Extracted symbol name or section heading")
    start_line: int = Field(..., ge=1, description="1-indexed start line number")
    end_line: int = Field(..., ge=1, description="1-indexed end line number")
    language: str = Field(..., description="Source code language name")
    score: float = Field(..., description="Vector search relevance similarity score")
    snippet: str = Field(..., description="Code snippet content")


class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language question about the codebase")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of context chunks to retrieve")


class QueryResponse(BaseModel):
    repository_id: str
    query: str
    answer: str
    citations: List[Citation] = Field(default_factory=list)
