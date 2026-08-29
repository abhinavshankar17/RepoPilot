from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class RepositoryCreate(BaseModel):
    url: str = Field(..., description="GitHub repository HTTP/HTTPS URL", examples=["https://github.com/octocat/Hello-World"])
    branch: Optional[str] = Field(default=None, description="Optional git branch name", examples=["main"])


class RepositoryResponse(BaseModel):
    id: str = Field(..., description="Unique repository identifier")
    name: str = Field(..., description="Repository name extracted from URL")
    url: str = Field(..., description="Repository git URL")
    branch: Optional[str] = Field(default=None, description="Ingested branch name")
    status: str = Field(..., description="Ingestion status: pending, processing, completed, failed")
    file_count: int = Field(default=0, description="Total source files indexed")
    chunk_count: int = Field(default=0, description="Total code chunks created")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    message: Optional[str] = Field(default=None, description="Status message or error detail")


class RepositoryListResponse(BaseModel):
    total: int
    repositories: List[RepositoryResponse]
