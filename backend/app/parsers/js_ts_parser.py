import re
from typing import List, Optional, Tuple
from app.parsers.base import BaseLanguageParser
from app.parsers.fallback_parser import FallbackParser
from app.schemas.parser import CodeSymbol
from app.core.logging import logger


class JSTSParser(BaseLanguageParser):
    """JavaScript / TypeScript parser extracting classes, methods, functions, and imports."""

    @staticmethod
    def _find_closing_brace_line(lines: List[str], start_line_idx: int) -> int:
        """Finds line number of matching closing brace starting from start_line_idx (0-indexed)."""
        brace_count = 0
        started = False

        for idx in range(start_line_idx, len(lines)):
            line = lines[idx]
            for char in line:
                if char == '{':
                    brace_count += 1
                    started = True
                elif char == '}':
                    brace_count -= 1

            if started and brace_count == 0:
                return idx + 1  # 1-indexed

        return min(start_line_idx + 30, len(lines))

    def parse(self, repository_id: str, file_path: str, content: str, language: str = "TypeScript") -> List[CodeSymbol]:
        lines = content.splitlines()
        if not lines:
            return []

        symbols: List[CodeSymbol] = []

        # 1. Imports: import { x } from 'y'; OR const x = require('y');
        import_regex = re.compile(r"^\s*(import\s+.*?from\s+['\"].*?['\"]|const\s+.*?\s*=\s*require\(['\"].*?['\"]\));?")
        for idx, line in enumerate(lines):
            match = import_regex.match(line)
            if match:
                symbols.append(CodeSymbol(
                    repository_id=repository_id,
                    file_path=file_path,
                    language=language,
                    symbol_type="import",
                    symbol_name=line.strip()[:60],
                    start_line=idx + 1,
                    end_line=idx + 1,
                    content=line.strip(),
                    parent_symbol=None
                ))

        # 2. Classes & Interfaces: class ClassName [extends Parent] {
        class_regex = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(class|interface)\s+([A-Za-z0-9_]+)")
        class_spans: List[Tuple[str, int, int]] = []  # (class_name, start_line, end_line)

        for idx, line in enumerate(lines):
            match = class_regex.search(line)
            if match:
                kind, class_name = match.group(1), match.group(2)
                start_line = idx + 1
                end_line = self._find_closing_brace_line(lines, idx)
                snippet = "\n".join(lines[start_line - 1 : end_line])

                symbols.append(CodeSymbol(
                    repository_id=repository_id,
                    file_path=file_path,
                    language=language,
                    symbol_type=kind.lower(),
                    symbol_name=class_name,
                    start_line=start_line,
                    end_line=end_line,
                    content=snippet,
                    parent_symbol=None
                ))
                class_spans.append((class_name, start_line, end_line))

        # 3. Functions & Methods:
        func_regex = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_]+)\s*\((.*?)\)")
        arrow_regex = re.compile(r"^\s*(?:export\s+)?const\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s*)?\((.*?)\)\s*=>")
        method_regex = re.compile(r"^\s*(?:public\s+|private\s+|protected\s+|async\s+|static\s+)*([A-Za-z0-9_]+)\s*\((.*?)\)\s*\{")

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("import") or stripped.startswith("class ") or stripped.startswith("interface "):
                continue

            match = func_regex.search(line) or arrow_regex.search(line) or method_regex.search(line)
            if match:
                func_name = match.group(1)
                raw_params = match.group(2) if len(match.groups()) >= 2 else ""

                if func_name in {"if", "for", "while", "switch", "catch", "return"}:
                    continue

                start_line = idx + 1
                end_line = self._find_closing_brace_line(lines, idx)
                snippet = "\n".join(lines[start_line - 1 : end_line])
                params = [p.strip().split(":")[0].strip() for p in raw_params.split(",") if p.strip()]

                # Determine parent class if method falls within a class span
                parent = None
                for cname, cstart, cend in class_spans:
                    if cstart < start_line <= cend:
                        parent = cname
                        break

                decorators = []
                if idx > 0 and lines[idx - 1].strip().startswith("@"):
                    decorators.append(lines[idx - 1].strip())

                symbols.append(CodeSymbol(
                    repository_id=repository_id,
                    file_path=file_path,
                    language=language,
                    symbol_type="method" if parent else "function",
                    symbol_name=func_name,
                    start_line=start_line,
                    end_line=end_line,
                    content=snippet,
                    parent_symbol=parent,
                    parameters=params,
                    decorators=decorators
                ))

        return symbols if symbols else FallbackParser().parse(repository_id, file_path, content, language)
