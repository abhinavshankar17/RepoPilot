from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CodeSymbol(BaseModel):
    repository_id: str = Field(..., description="Target repository ID")
    file_path: str = Field(..., description="Relative file path")
    language: str = Field(..., description="Source code language name")
    symbol_type: str = Field(..., description="Symbol type: class, function, method, import, route, file, block")
    symbol_name: str = Field(..., description="Extracted symbol identifier or scope name")
    start_line: int = Field(..., ge=1, description="1-indexed start line number")
    end_line: int = Field(..., ge=1, description="1-indexed end line number")
    content: str = Field(..., description="Raw code snippet of the symbol")
    parent_symbol: Optional[str] = Field(default=None, description="Enclosing class or parent scope name")
    parameters: List[str] = Field(default_factory=list, description="Extracted parameter names")
    decorators: List[str] = Field(default_factory=list, description="Decorators or annotations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional language metadata (e.g. route method, imports)")
