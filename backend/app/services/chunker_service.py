from typing import List, Dict, Any
from app.services.parser_service import CodeUnit
from app.core.logging import logger


class CodeChunk:
    def __init__(self, chunk_id: str, file_path: str, start_line: int, end_line: int, text: str):
        self.chunk_id = chunk_id
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.text = text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "text": self.text,
        }


class ChunkerService:
    """Service to group code units into contextual vector chunks."""

    def create_chunks(self, code_units: List[CodeUnit], max_chunk_tokens: int = 512) -> List[CodeChunk]:
        chunks: List[CodeChunk] = []
        
        for idx, unit in enumerate(code_units):
            # Prepend metadata header to assist embedding semantics
            formatted_text = f"File: {unit.file_path} (Lines {unit.start_line}-{unit.end_line})\n```\n{unit.code}\n```"
            chunk_id = f"{unit.file_path}:{unit.start_line}-{unit.end_line}:{idx}"
            
            chunks.append(CodeChunk(
                chunk_id=chunk_id,
                file_path=unit.file_path,
                start_line=unit.start_line,
                end_line=unit.end_line,
                text=formatted_text
            ))

        logger.info(f"Created {len(chunks)} code chunks from {len(code_units)} code units.")
        return chunks
