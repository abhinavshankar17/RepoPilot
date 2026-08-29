import os
from typing import Dict, Type
from app.parsers.base import BaseLanguageParser
from app.parsers.python_parser import PythonASTParser
from app.parsers.js_ts_parser import JSTSParser
from app.parsers.generic_parser import GenericLanguageParser
from app.parsers.fallback_parser import FallbackParser
from app.core.logging import logger


class ParserRegistry:
    """Registry providing language-specific AST parsers."""

    PARSER_MAP: Dict[str, BaseLanguageParser] = {
        "Python": PythonASTParser(),
        "JavaScript": JSTSParser(),
        "TypeScript": JSTSParser(),
        "Java": GenericLanguageParser(),
        "C/C++": GenericLanguageParser(),
        "Go": GenericLanguageParser(),
        "Rust": GenericLanguageParser(),
    }

    EXTENSION_MAP: Dict[str, str] = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".java": "Java",
        ".c": "C/C++",
        ".cpp": "C/C++",
        ".h": "C/C++",
        ".hpp": "C/C++",
        ".go": "Go",
        ".rs": "Rust",
    }

    @classmethod
    def get_parser(cls, file_path: str, language: str = None) -> BaseLanguageParser:
        if not language:
            ext = os.path.splitext(file_path)[1].lower()
            language = cls.EXTENSION_MAP.get(ext)

        if language in cls.PARSER_MAP:
            return cls.PARSER_MAP[language]

        return FallbackParser()


def get_parser(file_path: str, language: str = None) -> BaseLanguageParser:
    return ParserRegistry.get_parser(file_path, language)
