import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.api.router import api_router

# Initialize structured logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)
    logger.info("RepoPilot Backend API initialized.")
    yield


app = FastAPI(
    title="RepoPilot API",
    description="RAG-powered Developer Documentation & Codebase Copilot Backend",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root-level health check & API routers
app.include_router(api_router)
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
