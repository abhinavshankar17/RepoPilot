from fastapi import APIRouter
from app.schemas.health import HealthResponse
from app.core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Service health check endpoint."""
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        version="0.1.0"
    )
