import os
import tempfile
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import IngestRequest, IngestResponse
from app.services.git_service import GitService
from app.services.parser_service import ParserService, CodeUnit
from app.services.chunker_service import ChunkerService
from app.services.embedding_service import get_embedding_provider
from app.services.vector_store import get_vector_store
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_200_OK, tags=["Ingestion"])
async def ingest_repository(request: IngestRequest):
    """Clones, parses, chunks, and indexes a GitHub repository."""
    git_service = GitService()

    if not git_service.is_valid_github_url(request.repo_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL provided."
        )

    repo_name = git_service.extract_repo_name(request.repo_url)
    repo_storage_dir = os.path.join(settings.STORAGE_DIR, repo_name)

    try:
        logger.info(f"Starting ingestion process for {request.repo_url}")
        git_service.clone_repository(request.repo_url, repo_storage_dir, branch=request.branch)
        file_paths = git_service.discover_files(repo_storage_dir)

        parser = ParserService()
        chunker = ChunkerService()
        all_code_units: list[CodeUnit] = []

        for rel_path in file_paths:
            full_path = os.path.join(repo_storage_dir, rel_path)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                units = parser.parse_file(rel_path, content)
                all_code_units.extend(units)
            except Exception as read_err:
                logger.warning(f"Skipping unreadable file {rel_path}: {read_err}")

        chunks = chunker.create_chunks(all_code_units)
        
        # Embed and index
        embedding_provider = get_embedding_provider()
        chunk_texts = [c.text for c in chunks]
        embeddings = embedding_provider.embed_texts(chunk_texts)

        vector_store = get_vector_store(repo_name)
        vector_store.add_chunks(chunks, embeddings)

        return IngestResponse(
            status="success",
            repo_name=repo_name,
            total_files=len(file_paths),
            total_chunks=len(chunks),
            message=f"Successfully ingested and indexed repository '{repo_name}'."
        )

    except Exception as e:
        logger.error(f"Error during repository ingestion: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest repository: {str(e)}"
        )
