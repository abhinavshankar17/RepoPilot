from typing import List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    file_path: str = Field(..., description="Relative path of the source file")
    start_line: int = Field(..., description="Start line number")
    end_line: int = Field(..., description="End line number")
    snippet: str = Field(..., description="Code snippet snippet content")


class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language question about the codebase")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of context chunks to retrieve")


class QueryResponse(BaseModel):
    repository_id: str
    query: str
    answer: str
    citations: List[Citation] = Field(default_factory=list)
