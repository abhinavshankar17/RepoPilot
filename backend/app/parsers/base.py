from abc import ABC, abstractmethod
from typing import List
from app.schemas.parser import CodeSymbol
from app.core.logging import logger


class BaseLanguageParser(ABC):
    """Abstract interface for language-specific AST parsers."""

    @abstractmethod
    def parse(self, repository_id: str, file_path: str, content: str, language: str) -> List[CodeSymbol]:
        """Parses source file content into a list of normalized CodeSymbol objects."""
        pass
