import re
from typing import List, Dict, Optional, Any
from app.schemas.parser import CodeSymbol
from app.schemas.chunk import CodeChunk
from app.core.logging import logger


class MarkdownChunker:
    """Chunks Markdown documents according to headers (#, ##, ###) while preserving line numbers."""

    @staticmethod
    def chunk_markdown(repository_id: str, file_path: str, content: str) -> List[CodeChunk]:
        lines = content.splitlines()
        if not lines:
            return []

        chunks: List[CodeChunk] = []
        header_regex = re.compile(r"^(#{1,6})\s+(.+)$")

        current_heading = "Overview"
        current_lines: List[str] = []
        start_line = 1

        for idx, line in enumerate(lines, start=1):
            match = header_regex.match(line)
            if match:
                # Save previous section if non-empty
                if current_lines and "\n".join(current_lines).strip():
                    end_line = idx - 1
                    chunks.append(CodeChunk(
                        chunk_id=f"{file_path}:{current_heading}:{start_line}-{end_line}",
                        repository_id=repository_id,
                        file_path=file_path,
                        language="Markdown",
                        symbol_type="section",
                        symbol_name=current_heading,
                        parent_symbol=None,
                        start_line=start_line,
                        end_line=end_line,
                        content="\n".join(current_lines)
                    ))
                current_heading = match.group(2).strip()
                current_lines = [line]
                start_line = idx
            else:
                current_lines.append(line)

        if current_lines and "\n".join(current_lines).strip():
            end_line = len(lines)
            chunks.append(CodeChunk(
                chunk_id=f"{file_path}:{current_heading}:{start_line}-{end_line}",
                repository_id=repository_id,
                file_path=file_path,
                language="Markdown",
                symbol_type="section",
                symbol_name=current_heading,
                parent_symbol=None,
                start_line=start_line,
                end_line=end_line,
                content="\n".join(current_lines)
            ))

        return chunks


class LargeSymbolSplitter:
    """Splits oversized code symbols into smaller sub-chunks while maintaining parent context and line numbers."""

    MAX_CHUNK_LINES: int = 40
    OVERLAP_LINES: int = 5

    @classmethod
    def split_symbol(cls, symbol: CodeSymbol, imports: List[str]) -> List[CodeChunk]:
        lines = symbol.content.splitlines()
        if len(lines) <= cls.MAX_CHUNK_LINES:
            return [CodeChunk(
                chunk_id=f"{symbol.file_path}:{symbol.symbol_name}:{symbol.start_line}-{symbol.end_line}",
                repository_id=symbol.repository_id,
                file_path=symbol.file_path,
                language=symbol.language,
                symbol_type=symbol.symbol_type,
                symbol_name=symbol.symbol_name,
                parent_symbol=symbol.parent_symbol,
                start_line=symbol.start_line,
                end_line=symbol.end_line,
                content=symbol.content,
                imports=imports
            )]

        sub_chunks: List[CodeChunk] = []
        step = cls.MAX_CHUNK_LINES - cls.OVERLAP_LINES
        part = 1

        for i in range(0, len(lines), step):
            chunk_slice = lines[i : i + cls.MAX_CHUNK_LINES]
            if not chunk_slice:
                break

            sub_start = symbol.start_line + i
            sub_end = min(symbol.start_line + i + len(chunk_slice) - 1, symbol.end_line)
            sub_content = "\n".join(chunk_slice)

            sub_chunks.append(CodeChunk(
                chunk_id=f"{symbol.file_path}:{symbol.symbol_name}_part{part}:{sub_start}-{sub_end}",
                repository_id=symbol.repository_id,
                file_path=symbol.file_path,
                language=symbol.language,
                symbol_type=symbol.symbol_type,
                symbol_name=f"{symbol.symbol_name} (part {part})",
                parent_symbol=symbol.parent_symbol or symbol.symbol_name,
                start_line=sub_start,
                end_line=sub_end,
                content=sub_content,
                imports=imports
            ))
            part += 1

            if sub_end >= symbol.end_line:
                break

        return sub_chunks


class CodeAwareChunkerService:
    """Code-aware chunker converting symbols and documents into contextual retrieval chunks."""

    def create_chunks(self, repository_id: str, file_path: str, symbols: List[CodeSymbol], raw_content: str, language: str) -> List[CodeChunk]:
        if not raw_content or not raw_content.strip():
            return []

        # 1. Handle Markdown files
        if language == "Markdown" or file_path.lower().endswith(".md"):
            return MarkdownChunker.chunk_markdown(repository_id, file_path, raw_content)

        # 2. Extract import statements for contextual header injection
        imports = [s.content for s in symbols if s.symbol_type == "import"]

        chunks: List[CodeChunk] = []

        # Filter symbols (excluding import statements from being standalone chunks unless necessary)
        code_symbols = [s for s in symbols if s.symbol_type != "import"]

        if not code_symbols:
            # Fallback for plain text or configuration files without explicit AST symbols
            lines = raw_content.splitlines()
            chunk_size = 40
            for idx in range(0, len(lines), chunk_size):
                chunk_lines = lines[idx : idx + chunk_size]
                sub_start = idx + 1
                sub_end = idx + len(chunk_lines)
                chunks.append(CodeChunk(
                    chunk_id=f"{file_path}:block:{sub_start}-{sub_end}",
                    repository_id=repository_id,
                    file_path=file_path,
                    language=language,
                    symbol_type="block",
                    symbol_name=f"block:{sub_start}-{sub_end}",
                    parent_symbol=None,
                    start_line=sub_start,
                    end_line=sub_end,
                    content="\n".join(chunk_lines),
                    imports=imports
                ))
            return chunks

        # 3. Process structural AST symbols (functions, methods, classes, blocks)
        for sym in code_symbols:
            sub_chunks = LargeSymbolSplitter.split_symbol(sym, imports)
            chunks.extend(sub_chunks)

        return chunks


chunker_service = CodeAwareChunkerService()


def get_chunker_service() -> CodeAwareChunkerService:
    return chunker_service
