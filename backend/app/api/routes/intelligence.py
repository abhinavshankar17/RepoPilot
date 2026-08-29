from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.intelligence import (
    CodeFlowRequest, CodeFlowResponse,
    ImpactAnalysisRequest, ImpactAnalysisResponse,
    ChangePlanRequest, ChangePlanResponse
)
from app.services.code_flow_service import CodeFlowService, get_code_flow_service
from app.services.impact_analysis_service import ImpactAnalysisService, get_impact_analysis_service
from app.services.change_planning_service import ChangePlanningService, get_change_planning_service

router = APIRouter(prefix="/repositories", tags=["Repository Intelligence"])


@router.post("/{repository_id}/flow", response_model=CodeFlowResponse, status_code=status.HTTP_200_OK)
async def analyze_code_flow(
    repository_id: str,
    payload: CodeFlowRequest,
    flow_svc: CodeFlowService = Depends(get_code_flow_service)
):
    """Traces architectural execution flows (Route -> Controller -> Service -> Repository -> Database)."""
    try:
        return flow_svc.analyze_code_flow(repository_id, payload)
    except KeyError as k_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(k_err))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Code flow analysis failed: {str(e)}")


@router.post("/{repository_id}/impact", response_model=ImpactAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_impact(
    repository_id: str,
    payload: ImpactAnalysisRequest,
    impact_svc: ImpactAnalysisService = Depends(get_impact_analysis_service)
):
    """Analyzes structural codebase dependencies, imports, function calls, and modification impacts."""
    try:
        return impact_svc.analyze_impact(repository_id, payload)
    except KeyError as k_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(k_err))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Impact analysis failed: {str(e)}")


@router.post("/{repository_id}/change-plan", response_model=ChangePlanResponse, status_code=status.HTTP_200_OK)
async def plan_changes(
    repository_id: str,
    payload: ChangePlanRequest,
    plan_svc: ChangePlanningService = Depends(get_change_planning_service)
):
    """Generates structured feature change recommendations separating code evidence from LLM inferences."""
    try:
        return plan_svc.plan_changes(repository_id, payload)
    except KeyError as k_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(k_err))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Change planning failed: {str(e)}")
