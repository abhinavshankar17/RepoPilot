from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import QueryService, get_query_service

router = APIRouter(prefix="/repositories", tags=["Query"])


@router.post("/{repository_id}/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def query_repository(
    repository_id: str,
    payload: QueryRequest,
    q_service: QueryService = Depends(get_query_service)
):
    """Executes a natural language query against a specific repository."""
    try:
        return q_service.process_query(repository_id, payload)
    except KeyError as key_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(key_err)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}"
        )
