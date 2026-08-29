from typing import List
from app.parsers.registry import get_parser
from app.parsers.fallback_parser import FallbackParser
from app.schemas.parser import CodeSymbol
from app.core.logging import logger


class ParserService:
    """Orchestrates AST parsing and symbol extraction for ingested files."""

    def parse_file(self, repository_id: str, file_path: str, content: str, language: str = None) -> List[CodeSymbol]:
        if not content or not content.strip():
            return []

        try:
            parser = get_parser(file_path, language)
            symbols = parser.parse(repository_id, file_path, content, language or "Plain Text")
            return symbols
        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}. Falling back to plain text parsing.")
            return FallbackParser().parse(repository_id, file_path, content, language or "Plain Text")


parser_service = ParserService()


def get_parser_service() -> ParserService:
    return parser_service
