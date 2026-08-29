import os
from typing import Dict, Any, List
from app.core.logging import logger


class CodeUnit:
    def __init__(self, file_path: str, start_line: int, end_line: int, code: str, unit_type: str = "block"):
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.code = code
        self.unit_type = unit_type


class ParserService:
    """Service to parse source files into structural AST / code elements."""

    def parse_file(self, file_path: str, content: str) -> List[CodeUnit]:
        """Parses a file content into logical structural units."""
        lines = content.splitlines()
        if not lines:
            return []

        ext = os.path.splitext(file_path)[1].lower()
        
        # Simple fallback structural parser for foundation (will be enhanced with Tree-Sitter)
        units: List[CodeUnit] = []
        current_block: List[str] = []
        start_line = 1

        for idx, line in enumerate(lines, start=1):
            current_block.append(line)
            # Break every 40 lines or on logical empty line gaps
            if len(current_block) >= 40 or (len(current_block) >= 20 and not line.strip()):
                units.append(CodeUnit(
                    file_path=file_path,
                    start_line=start_line,
                    end_line=idx,
                    code="\n".join(current_block),
                    unit_type="code_block"
                ))
                current_block = []
                start_line = idx + 1

        if current_block:
            units.append(CodeUnit(
                file_path=file_path,
                start_line=start_line,
                end_line=len(lines),
                code="\n".join(current_block),
                unit_type="code_block"
            ))

        return units
