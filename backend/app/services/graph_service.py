import os
from typing import List, Dict, Optional, Any
from app.graph.repository_graph import RepositoryGraph, GraphNode, GraphEdge
from app.graph.graph_extractor import GraphExtractor
from app.schemas.chunk import CodeChunk
from app.core.config import settings
from app.core.logging import logger


class GraphService:
    """Service providing graph query capabilities for code relationship analysis."""

    def __init__(self, base_storage_dir: Optional[str] = None):
        self.base_dir = base_storage_dir or os.path.join(settings.STORAGE_DIR, "graphs")
        os.makedirs(self.base_dir, exist_ok=True)
        self._graphs: Dict[str, RepositoryGraph] = {}

    def build_and_store_graph(self, repo_id: str, chunks: List[CodeChunk]) -> RepositoryGraph:
        """Builds and persists repository relationship graph."""
        graph = GraphExtractor.extract_graph(repo_id, chunks)
        graph.save(self.base_dir)
        self._graphs[repo_id] = graph
        return graph

    def get_graph(self, repo_id: str) -> RepositoryGraph:
        """Retrieves or loads graph for repository."""
        if repo_id not in self._graphs:
            loaded = RepositoryGraph.load(repo_id, self.base_dir)
            if loaded:
                self._graphs[repo_id] = loaded
            else:
                self._graphs[repo_id] = RepositoryGraph(repo_id)
        return self._graphs[repo_id]

    def find_node_by_name(self, repo_id: str, name: str) -> Optional[GraphNode]:
        graph = self.get_graph(repo_id)
        name_lower = name.lower()
        for node in graph.nodes.values():
            if node.name.lower() == name_lower or node.file_path.lower() == name_lower:
                return node
        return None

    def find_dependencies(self, repo_id: str, symbol_or_file: str) -> List[GraphEdge]:
        graph = self.get_graph(repo_id)
        node = self.find_node_by_name(repo_id, symbol_or_file)
        if not node:
            return []
        return graph.find_dependencies(node.id)

    def find_dependents(self, repo_id: str, symbol_or_file: str) -> List[GraphEdge]:
        graph = self.get_graph(repo_id)
        node = self.find_node_by_name(repo_id, symbol_or_file)
        if not node:
            return []
        return graph.find_dependents(node.id)

    def trace_call_chain(self, repo_id: str, start_symbol: str, max_depth: int = 5) -> List[GraphEdge]:
        graph = self.get_graph(repo_id)
        node = self.find_node_by_name(repo_id, start_symbol)
        if not node:
            return []
        return graph.trace_call_chain(node.id, max_depth=max_depth)


graph_service = GraphService()


def get_graph_service() -> GraphService:
    return graph_service
