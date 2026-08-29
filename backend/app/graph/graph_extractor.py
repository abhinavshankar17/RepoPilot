import re
from typing import List, Dict, Set
from app.schemas.chunk import CodeChunk
from app.graph.repository_graph import RepositoryGraph, GraphNode, GraphEdge
from app.core.logging import logger


class GraphExtractor:
    """Extracts structural graph nodes and edges from AST parsed codebase chunks."""

    CALL_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
    CLASS_EXTENDS_PATTERN = re.compile(r"class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]+\)|extends\s+([A-Za-z_][A-Za-z0-9_]*)|implements\s+([A-Za-z_][A-Za-z0-9_]*))", re.IGNORECASE)
    ROUTE_PATTERN = re.compile(r"\b(GET|POST|PUT|DELETE|PATCH)\s+([/\w:-]+)", re.IGNORECASE)

    @classmethod
    def extract_graph(cls, repository_id: str, chunks: List[CodeChunk]) -> RepositoryGraph:
        graph = RepositoryGraph(repository_id=repository_id)
        file_nodes: Dict[str, GraphNode] = {}
        symbol_nodes: Dict[str, GraphNode] = {}

        # 1. Create File Nodes and Symbol Nodes + DEFINES edges
        for chunk in chunks:
            # File Node
            file_id = f"file:{chunk.file_path}"
            if file_id not in file_nodes:
                f_node = GraphNode(
                    id=file_id,
                    name=chunk.file_path,
                    node_type="file",
                    file_path=chunk.file_path,
                    start_line=1,
                    end_line=1
                )
                file_nodes[file_id] = f_node
                graph.add_node(f_node)

            # Symbol Node
            symbol_id = f"symbol:{chunk.file_path}:{chunk.symbol_name}"
            s_node = GraphNode(
                id=symbol_id,
                name=chunk.symbol_name,
                node_type=chunk.symbol_type,
                file_path=chunk.file_path,
                start_line=chunk.start_line,
                end_line=chunk.end_line
            )
            symbol_nodes[symbol_id] = s_node
            graph.add_node(s_node)

            # DEFINES Edge (File -> DEFINES -> Symbol)
            graph.add_edge(GraphEdge(
                source_id=file_id,
                target_id=symbol_id,
                relation_type="DEFINES"
            ))

            # IMPORTS Edges (File -> IMPORTS -> Module)
            for imp in chunk.imports:
                imp_clean = imp.replace("import", "").replace("from", "").strip(" ;'\"")
                if imp_clean:
                    target_file_id = f"file:{imp_clean}"
                    if target_file_id not in graph.nodes:
                        imp_node = GraphNode(
                            id=target_file_id,
                            name=imp_clean,
                            node_type="module",
                            file_path=imp_clean,
                            start_line=1,
                            end_line=1
                        )
                        graph.add_node(imp_node)
                    graph.add_edge(GraphEdge(
                        source_id=file_id,
                        target_id=target_file_id,
                        relation_type="IMPORTS"
                    ))

        # 2. Extract CALLS, EXTENDS, IMPLEMENTS, USES, ROUTES_TO edges
        for chunk in chunks:
            source_symbol_id = f"symbol:{chunk.file_path}:{chunk.symbol_name}"
            content = chunk.content

            # CALLS Edges
            called_funcs = set(cls.CALL_PATTERN.findall(content))
            for func_name in called_funcs:
                if func_name != chunk.symbol_name and len(func_name) > 2:
                    # Match against defined symbols
                    for s_id, s_node in symbol_nodes.items():
                        if s_node.name == func_name:
                            graph.add_edge(GraphEdge(
                                source_id=source_symbol_id,
                                target_id=s_id,
                                relation_type="CALLS"
                            ))

            # EXTENDS & IMPLEMENTS Edges
            for match in cls.CLASS_EXTENDS_PATTERN.finditer(content):
                cls_name, extends_parent, implements_iface = match.groups()
                if extends_parent:
                    parent_id = f"symbol:parent:{extends_parent}"
                    if parent_id not in graph.nodes:
                        p_node = GraphNode(id=parent_id, name=extends_parent, node_type="class", file_path=chunk.file_path)
                        graph.add_node(p_node)
                    graph.add_edge(GraphEdge(source_id=source_symbol_id, target_id=parent_id, relation_type="EXTENDS"))
                if implements_iface:
                    iface_id = f"symbol:iface:{implements_iface}"
                    if iface_id not in graph.nodes:
                        i_node = GraphNode(id=iface_id, name=implements_iface, node_type="interface", file_path=chunk.file_path)
                        graph.add_node(i_node)
                    graph.add_edge(GraphEdge(source_id=source_symbol_id, target_id=iface_id, relation_type="IMPLEMENTS"))

            # ROUTES_TO Edges
            route_matches = cls.ROUTE_PATTERN.findall(content)
            for verb, path in route_matches:
                route_id = f"route:{verb}:{path}"
                if route_id not in graph.nodes:
                    r_node = GraphNode(
                        id=route_id,
                        name=f"{verb} {path}",
                        node_type="route",
                        file_path=chunk.file_path,
                        start_line=chunk.start_line,
                        end_line=chunk.end_line
                    )
                    graph.add_node(r_node)

                graph.add_edge(GraphEdge(
                    source_id=route_id,
                    target_id=source_symbol_id,
                    relation_type="ROUTES_TO"
                ))

        logger.info(f"Extracted relationship graph for '{repository_id}': {len(graph.nodes)} nodes, {len(graph.edges)} edges.")
        return graph
