from typing import List
from app.parsers.base import BaseLanguageParser
from app.schemas.parser import CodeSymbol


class FallbackParser(BaseLanguageParser):
    """Fallback plain text parser used when language AST parser fails or is unavailable."""

    def parse(self, repository_id: str, file_path: str, content: str, language: str) -> List[CodeSymbol]:
        lines = content.splitlines()
        if not lines:
            return []

        symbols: List[CodeSymbol] = []
        chunk_size = 50
        start_line = 1

        for idx in range(0, len(lines), chunk_size):
            chunk_lines = lines[idx : idx + chunk_size]
            end_line = idx + len(chunk_lines)
            chunk_text = "\n".join(chunk_lines)

            symbols.append(CodeSymbol(
                repository_id=repository_id,
                file_path=file_path,
                language=language,
                symbol_type="block",
                symbol_name=f"block:{start_line}-{end_line}",
                start_line=start_line,
                end_line=end_line,
                content=chunk_text,
                parent_symbol=None
            ))
            start_line = end_line + 1

        return symbols
