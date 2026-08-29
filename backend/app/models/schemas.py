from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class HealthResponse(BaseModel):
    status: str = "ok"
    environment: str
    version: str = "0.1.0"


class IngestRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub Repository HTTP or HTTPS URL")
    branch: Optional[str] = Field(default=None, description="Optional git branch to clone")


class IngestResponse(BaseModel):
    status: str
    repo_name: str
    total_files: int
    total_chunks: int
    message: str


class Citation(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    snippet: str


class QueryRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub Repository HTTP or HTTPS URL previously ingested")
    query: str = Field(..., description="Natural language question about the codebase")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of top context chunks to retrieve")


class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[Citation]
