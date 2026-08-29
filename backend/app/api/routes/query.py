from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.query import QueryRequest, QueryResponse
from app.services.rag_service import RAGService, get_rag_service

router = APIRouter(prefix="/repositories", tags=["Query"])


@router.post("/{repository_id}/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def query_repository(
    repository_id: str,
    payload: QueryRequest,
    rag_svc: RAGService = Depends(get_rag_service)
):
    """Executes a grounded RAG query against an ingested repository using query rewriting, session history, and hybrid retrieval."""
    try:
        return rag_svc.answer_question(
            repo_id=repository_id,
            query=payload.query,
            session_id=payload.session_id,
            top_k=payload.top_k
        )
    except KeyError as key_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(key_err)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG query execution failed: {str(e)}"
        )
