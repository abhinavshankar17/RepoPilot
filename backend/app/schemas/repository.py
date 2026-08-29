from datetime import datetime, timezone
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
    storage_path: str = Field(..., description="Isolated local storage directory path")
    file_count: int = Field(default=0, description="Total valid source files ingested")
    detected_languages: List[str] = Field(default_factory=list, description="List of detected programming/config languages")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message: Optional[str] = Field(default=None, description="Status message or error detail")


class RepositoryListResponse(BaseModel):
    total: int
    repositories: List[RepositoryResponse]


class FileContentResponse(BaseModel):
    repository_id: str
    file_path: str
    start_line: int
    end_line: int
    total_lines: int
    content: str
