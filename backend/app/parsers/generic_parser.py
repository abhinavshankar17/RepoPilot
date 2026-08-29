import re
from typing import List, Tuple
from app.parsers.base import BaseLanguageParser
from app.parsers.fallback_parser import FallbackParser
from app.schemas.parser import CodeSymbol


class GenericLanguageParser(BaseLanguageParser):
    """Parser for Java, Go, Rust, C/C++, and config files."""

    @staticmethod
    def _find_closing_brace_line(lines: List[str], start_line_idx: int) -> int:
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
                return idx + 1
        return min(start_line_idx + 35, len(lines))

    def parse(self, repository_id: str, file_path: str, content: str, language: str) -> List[CodeSymbol]:
        lines = content.splitlines()
        if not lines:
            return []

        symbols: List[CodeSymbol] = []

        # Classes / Structs / Types
        class_regex = re.compile(r"^\s*(?:public\s+|private\s+|protected\s+)?(?:class|struct|interface|type)\s+([A-Za-z0-9_]+)")
        class_spans: List[Tuple[str, int, int]] = []

        for idx, line in enumerate(lines):
            match = class_regex.search(line)
            if match:
                name = match.group(1)
                start_line = idx + 1
                end_line = self._find_closing_brace_line(lines, idx)
                snippet = "\n".join(lines[start_line - 1 : end_line])

                symbols.append(CodeSymbol(
                    repository_id=repository_id,
                    file_path=file_path,
                    language=language,
                    symbol_type="class",
                    symbol_name=name,
                    start_line=start_line,
                    end_line=end_line,
                    content=snippet,
                    parent_symbol=None
                ))
                class_spans.append((name, start_line, end_line))

        # Functions / Methods
        # e.g., func Foo(bar string) error {}, fn baz() {}, public void myMethod()
        func_regex = re.compile(r"^\s*(?:pub\s+)?(?:fn|func|(?:public\s+|private\s+|protected\s+|static\s+)+[\w<>\[\]]+\s+)+([A-Za-z0-9_]+)\s*\((.*?)\)")

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                continue

            match = func_regex.search(line)
            if match:
                func_name, raw_params = match.group(1), match.group(2)
                if func_name in {"if", "for", "while", "switch"}:
                    continue

                start_line = idx + 1
                end_line = self._find_closing_brace_line(lines, idx)
                snippet = "\n".join(lines[start_line - 1 : end_line])
                params = [p.strip() for p in raw_params.split(",") if p.strip()]

                parent = None
                for cname, cstart, cend in class_spans:
                    if cstart <= start_line <= cend:
                        parent = cname
                        break

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
                    parameters=params
                ))

        return symbols if symbols else FallbackParser().parse(repository_id, file_path, content, language)
