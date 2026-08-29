from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.query import Citation


# --- Feature 1: Code Flow ---
class CodeFlowRequest(BaseModel):
    query: str = Field(..., description="Natural language flow request, e.g. 'Explain request flow for POST /api/orders'")
    endpoint_or_symbol: Optional[str] = Field(default=None, description="Optional target route or entrypoint symbol")
    top_k: int = Field(default=5, ge=1, le=20)


class CodeFlowStep(BaseModel):
    step_number: int
    layer: str = Field(..., description="Layer category: Route | Controller | Service | Repository | Database")
    description: str
    file_path: str
    start_line: int
    end_line: int
    symbol: Optional[str] = None


class CodeFlowResponse(BaseModel):
    repository_id: str
    query: str
    flow_diagram: str = Field(..., description="ASCII / Markdown flow representation: Route -> Controller -> Service -> Database")
    steps: List[CodeFlowStep]
    citations: List[Citation]


# --- Feature 2: Impact Analysis ---
class ImpactAnalysisRequest(BaseModel):
    target_file_or_symbol: str = Field(..., description="Target file path or symbol name to analyze impact for, e.g. 'User.js'")
    top_k: int = Field(default=5, ge=1, le=20)


class ImpactDetail(BaseModel):
    category: str = Field(..., description="Imports | References | Function Calls | Dependent Modules | API Routes")
    file_path: str
    description: str
    citations: List[Citation] = Field(default_factory=list)


class ImpactAnalysisResponse(BaseModel):
    repository_id: str
    target: str
    summary: str
    impacts: List[ImpactDetail]
    citations: List[Citation]


# --- Feature 3: Change Planning ---
class ChangePlanRequest(BaseModel):
    proposed_feature: str = Field(..., description="Description of feature to add, e.g. 'Add Google OAuth'")
    top_k: int = Field(default=5, ge=1, le=20)


class FileChangeRecommendation(BaseModel):
    file_path: str
    reason: str
    relevant_existing_code: str
    confidence: str = Field(..., description="High | Medium | Low")
    is_new_file: bool = False


class ChangePlanResponse(BaseModel):
    repository_id: str
    proposed_feature: str
    evidence_found: str = Field(..., description="Repository evidence found strictly in code")
    recommendations: List[FileChangeRecommendation]
    citations: List[Citation]
