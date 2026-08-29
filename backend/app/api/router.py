from fastapi import APIRouter
from app.api.routes import health, repositories, query, intelligence

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(repositories.router)
api_router.include_router(query.router)
api_router.include_router(intelligence.router)
