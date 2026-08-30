from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.repository import RepositoryCreate, RepositoryResponse, RepositoryListResponse, FileContentResponse
from app.schemas.chunk import ChunkInspectResponse
from app.services.repository_service import RepositoryService, get_repository_service
from app.core.deps import UserToken, get_current_user
from app.core.security import SecurityUtils

router = APIRouter(prefix="/repositories", tags=["Repositories"])


def check_repo_authorization(repo: RepositoryResponse, current_user: UserToken) -> None:
    if current_user.role == "admin":
        return
    if repo.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not authorized to access this repository."
        )


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def create_repository(
    payload: RepositoryCreate,
    repo_service: RepositoryService = Depends(get_repository_service),
    current_user: UserToken = Depends(get_current_user)
):
    """Registers and triggers ingestion for a GitHub repository under the authenticated user."""
    try:
        return repo_service.create_repository(payload, owner_id=current_user.user_id)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=SecurityUtils.sanitize_error_message(str(val_err))
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=SecurityUtils.sanitize_error_message(f"Failed to process repository: {str(e)}")
        )


@router.get("", response_model=RepositoryListResponse, status_code=status.HTTP_200_OK)
async def list_repositories(
    repo_service: RepositoryService = Depends(get_repository_service),
    current_user: UserToken = Depends(get_current_user)
):
    """Lists registered repositories authorized for current user."""
    is_admin = current_user.role == "admin"
    return repo_service.list_repositories(owner_id=current_user.user_id, is_admin=is_admin)


@router.get("/{repository_id}", response_model=RepositoryResponse, status_code=status.HTTP_200_OK)
async def get_repository(
    repository_id: str,
    repo_service: RepositoryService = Depends(get_repository_service),
    current_user: UserToken = Depends(get_current_user)
):
    """Retrieves repository details by repository ID."""
    repo = repo_service.get_repository_by_id(repository_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repository_id}' not found."
        )
    check_repo_authorization(repo, current_user)
    return repo


@router.get("/{repository_id}/chunks", response_model=ChunkInspectResponse, status_code=status.HTTP_200_OK)
async def inspect_repository_chunks(
    repository_id: str,
    repo_service: RepositoryService = Depends(get_repository_service),
    current_user: UserToken = Depends(get_current_user)
):
    """Chunk inspection endpoint allowing debugging of generated code chunks before embedding."""
    repo = repo_service.get_repository_by_id(repository_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repository_id}' not found."
        )
    check_repo_authorization(repo, current_user)

    chunks = repo_service.ingestion_svc.get_repository_chunks(repository_id)
    return ChunkInspectResponse(
        repository_id=repository_id,
        file_path=repo.name,
        total_chunks=len(chunks),
        chunks=chunks
    )


@router.get("/{repository_id}/files/{file_path:path}", response_model=FileContentResponse, status_code=status.HTTP_200_OK)
async def get_repository_file(
    repository_id: str,
    file_path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    repo_service: RepositoryService = Depends(get_repository_service),
    current_user: UserToken = Depends(get_current_user)
):
    """Safely retrieves repository source code content with optional line range slicing."""
    repo = repo_service.get_repository_by_id(repository_id)
    if repo:
        check_repo_authorization(repo, current_user)

    try:
        return repo_service.get_repository_file_content(repository_id, file_path, start_line, end_line)
    except KeyError as k_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=SecurityUtils.sanitize_error_message(str(k_err)))
    except FileNotFoundError as fnf_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=SecurityUtils.sanitize_error_message(str(fnf_err)))
    except PermissionError as perm_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=SecurityUtils.sanitize_error_message(str(perm_err)))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=SecurityUtils.sanitize_error_message(f"Failed to read file: {str(e)}"))
