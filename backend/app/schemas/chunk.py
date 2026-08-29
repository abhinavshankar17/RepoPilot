from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CodeChunk(BaseModel):
    chunk_id: str = Field(..., description="Unique chunk identifier")
    repository_id: str = Field(..., description="Repository ID")
    file_path: str = Field(..., description="Relative file path")
    language: str = Field(..., description="Source language")
    symbol_type: str = Field(..., description="Symbol type: function, method, class, section, block, import")
    symbol_name: str = Field(..., description="Symbol name or section heading")
    parent_symbol: Optional[str] = Field(default=None, description="Enclosing class or parent scope name")
    start_line: int = Field(..., ge=1, description="1-indexed start line number")
    end_line: int = Field(..., ge=1, description="1-indexed end line number")
    content: str = Field(..., description="Formatted code or section chunk text")
    imports: List[str] = Field(default_factory=list, description="Extracted import context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional chunk metadata")


class ChunkInspectResponse(BaseModel):
    repository_id: str
    file_path: str
    total_chunks: int
    chunks: List[CodeChunk]
