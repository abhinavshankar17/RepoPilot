from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.repository import RepositoryCreate, RepositoryResponse, RepositoryListResponse
from app.schemas.chunk import ChunkInspectResponse
from app.services.repository_service import RepositoryService, get_repository_service

router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def create_repository(
    payload: RepositoryCreate,
    repo_service: RepositoryService = Depends(get_repository_service)
):
    """Registers and triggers ingestion for a GitHub repository."""
    try:
        return repo_service.create_repository(payload)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process repository: {str(e)}"
        )


@router.get("", response_model=RepositoryListResponse, status_code=status.HTTP_200_OK)
async def list_repositories(
    repo_service: RepositoryService = Depends(get_repository_service)
):
    """Lists all registered repositories."""
    return repo_service.list_repositories()


@router.get("/{repository_id}", response_model=RepositoryResponse, status_code=status.HTTP_200_OK)
async def get_repository(
    repository_id: str,
    repo_service: RepositoryService = Depends(get_repository_service)
):
    """Retrieves repository details by repository ID."""
    repo = repo_service.get_repository_by_id(repository_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repository_id}' not found."
        )
    return repo


@router.get("/{repository_id}/chunks", response_model=ChunkInspectResponse, status_code=status.HTTP_200_OK)
async def inspect_repository_chunks(
    repository_id: str,
    repo_service: RepositoryService = Depends(get_repository_service)
):
    """Chunk inspection endpoint allowing debugging of generated code chunks before embedding."""
    repo = repo_service.get_repository_by_id(repository_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repository_id}' not found."
        )

    chunks = repo_service.ingestion_svc.get_repository_chunks(repository_id)
    return ChunkInspectResponse(
        repository_id=repository_id,
        file_path=repo.name,
        total_chunks=len(chunks),
        chunks=chunks
    )
