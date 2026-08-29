import ast
from typing import List, Optional
from app.parsers.base import BaseLanguageParser
from app.parsers.fallback_parser import FallbackParser
from app.schemas.parser import CodeSymbol
from app.core.logging import logger


class PythonASTParser(BaseLanguageParser):
    """Python AST parser using Python's built-in ast module."""

    def _get_decorator_names(self, node: ast.AST, lines: List[str]) -> List[str]:
        decorators = []
        if hasattr(node, "decorator_list"):
            for dec in node.decorator_list:
                try:
                    dec_str = ast.unparse(dec)
                    decorators.append(f"@{dec_str}")
                except Exception:
                    if hasattr(dec, "lineno") and 1 <= dec.lineno <= len(lines):
                        decorators.append(lines[dec.lineno - 1].strip())
        return decorators

    def _get_parameters(self, node: ast.AST) -> List[str]:
        params = []
        if hasattr(node, "args") and isinstance(node.args, ast.arguments):
            for arg in node.args.args:
                if arg.arg != "self" and arg.arg != "cls":
                    params.append(arg.arg)
        return params

    def parse(self, repository_id: str, file_path: str, content: str, language: str = "Python") -> List[CodeSymbol]:
        lines = content.splitlines()
        if not lines:
            return []

        try:
            tree = ast.parse(content, filename=file_path)
        except Exception as err:
            logger.warning(f"Python AST parse error in {file_path}: {err}. Falling back to plain text.")
            return FallbackParser().parse(repository_id, file_path, content, language)

        symbols: List[CodeSymbol] = []

        class ASTVisitor(ast.NodeVisitor):
            def __init__(self, parser_obj):
                self.parser = parser_obj
                self.current_class: Optional[str] = None

            def visit_Import(self, node: ast.Import):
                for alias in node.names:
                    start = getattr(node, "lineno", 1)
                    end = getattr(node, "end_lineno", start)
                    snippet = "\n".join(lines[start - 1 : end])
                    symbols.append(CodeSymbol(
                        repository_id=repository_id,
                        file_path=file_path,
                        language="Python",
                        symbol_type="import",
                        symbol_name=alias.name,
                        start_line=start,
                        end_line=end,
                        content=snippet,
                        parent_symbol=None
                    ))
                self.generic_visit(node)

            def visit_ImportFrom(self, node: ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    start = getattr(node, "lineno", 1)
                    end = getattr(node, "end_lineno", start)
                    snippet = "\n".join(lines[start - 1 : end])
                    symbols.append(CodeSymbol(
                        repository_id=repository_id,
                        file_path=file_path,
                        language="Python",
                        symbol_type="import",
                        symbol_name=f"{module}.{alias.name}",
                        start_line=start,
                        end_line=end,
                        content=snippet,
                        parent_symbol=None
                    ))
                self.generic_visit(node)

            def visit_ClassDef(self, node: ast.ClassDef):
                start = getattr(node, "lineno", 1)
                end = getattr(node, "end_lineno", len(lines))
                snippet = "\n".join(lines[start - 1 : end])
                decorators = self.parser._get_decorator_names(node, lines)

                symbols.append(CodeSymbol(
                    repository_id=repository_id,
                    file_path=file_path,
                    language="Python",
                    symbol_type="class",
                    symbol_name=node.name,
                    start_line=start,
                    end_line=end,
                    content=snippet,
                    parent_symbol=self.current_class,
                    decorators=decorators
                ))

                prev_class = self.current_class
                self.current_class = node.name
                self.generic_visit(node)
                self.current_class = prev_class

            def visit_FunctionDef(self, node: ast.FunctionDef):
                self._handle_function(node)
                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
                self._handle_function(node)
                self.generic_visit(node)

            def _handle_function(self, node):
                start = getattr(node, "lineno", 1)
                end = getattr(node, "end_lineno", len(lines))
                snippet = "\n".join(lines[start - 1 : end])
                decorators = self.parser._get_decorator_names(node, lines)
                params = self.parser._get_parameters(node)
                is_method = self.current_class is not None

                metadata = {}
                # Detect API routes (e.g. @app.get("/path"), @router.post("/path"))
                for dec in decorators:
                    if any(verb in dec for verb in [".get(", ".post(", ".put(", ".delete(", ".patch("]):
                        metadata["route"] = dec

                symbols.append(CodeSymbol(
                    repository_id=repository_id,
                    file_path=file_path,
                    language="Python",
                    symbol_type="method" if is_method else "function",
                    symbol_name=node.name,
                    start_line=start,
                    end_line=end,
                    content=snippet,
                    parent_symbol=self.current_class,
                    parameters=params,
                    decorators=decorators,
                    metadata=metadata
                ))

        visitor = ASTVisitor(self)
        visitor.visit(tree)

        return symbols if symbols else FallbackParser().parse(repository_id, file_path, content, language)
