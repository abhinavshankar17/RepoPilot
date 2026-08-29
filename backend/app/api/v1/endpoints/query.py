from fastapi import APIRouter, HTTPException, status
from app.models.schemas import QueryRequest, QueryResponse
from app.services.git_service import GitService
from app.services.embedding_service import get_embedding_provider
from app.services.vector_store import get_vector_store
from app.services.llm_service import get_llm_provider
from app.core.logging import logger

router = APIRouter()


@router.post("/query", response_model=QueryResponse, status_code=status.HTTP_200_OK, tags=["Query"])
async def query_repository(request: QueryRequest):
    """Executes a natural language search and generates a grounded response with citations."""
    git_service = GitService()

    if not git_service.is_valid_github_url(request.repo_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL provided."
        )

    repo_name = git_service.extract_repo_name(request.repo_url)
    vector_store = get_vector_store(repo_name)

    if not vector_store.chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_name}' has not been ingested yet. Please ingest the repo first."
        )

    try:
        embedding_provider = get_embedding_provider()
        query_embedding = embedding_provider.embed_query(request.query)

        search_results = vector_store.search(query_embedding, top_k=request.top_k)
        retrieved_chunks = [chunk for chunk, score in search_results]

        llm_provider = get_llm_provider()
        answer, citations = llm_provider.generate_answer(request.query, retrieved_chunks)

        return QueryResponse(
            query=request.query,
            answer=answer,
            citations=citations
        )

    except Exception as e:
        logger.error(f"Error during query execution: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}"
        )
