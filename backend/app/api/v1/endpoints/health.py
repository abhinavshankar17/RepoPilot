from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Returns the operational status of the RepoPilot service."""
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        version="0.1.0"
    )
