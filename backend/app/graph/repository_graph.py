import os
import json
from typing import List, Dict, Set, Optional, Any
from pydantic import BaseModel, Field
from app.core.logging import logger


class GraphNode(BaseModel):
    id: str = Field(..., description="Unique node identifier")
    name: str = Field(..., description="Display name of symbol or file")
    node_type: str = Field(..., description="file | function | class | route | module")
    file_path: str = Field(..., description="Relative file path")
    start_line: int = 1
    end_line: int = 1


class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    relation_type: str = Field(..., description="IMPORTS | CALLS | DEFINES | EXTENDS | IMPLEMENTS | USES | ROUTES_TO")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RepositoryGraph:
    """In-memory lightweight directed relationship graph for a repository."""

    def __init__(self, repository_id: str):
        self.repository_id = repository_id
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.outgoing_adj: Dict[str, List[GraphEdge]] = {}
        self.incoming_adj: Dict[str, List[GraphEdge]] = {}

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges.append(edge)
        if edge.source_id not in self.outgoing_adj:
            self.outgoing_adj[edge.source_id] = []
        self.outgoing_adj[edge.source_id].append(edge)

        if edge.target_id not in self.incoming_adj:
            self.incoming_adj[edge.target_id] = []
        self.incoming_adj[edge.target_id].append(edge)

    def find_dependencies(self, node_id: str) -> List[GraphEdge]:
        """Finds outgoing dependency edges from node_id."""
        return self.outgoing_adj.get(node_id, [])

    def find_dependents(self, node_id: str) -> List[GraphEdge]:
        """Finds incoming dependent edges targeting node_id."""
        return self.incoming_adj.get(node_id, [])

    def trace_call_chain(self, start_node_id: str, max_depth: int = 5) -> List[GraphEdge]:
        """Traces CALLS and USES relationships up to max_depth."""
        visited: Set[str] = set()
        chain: List[GraphEdge] = []

        def dfs(curr_id: str, depth: int):
            if depth >= max_depth or curr_id in visited:
                return
            visited.add(curr_id)

            for edge in self.outgoing_adj.get(curr_id, []):
                if edge.relation_type in ("CALLS", "USES", "ROUTES_TO"):
                    chain.append(edge)
                    dfs(edge.target_id, depth + 1)

        dfs(start_node_id, 0)
        return chain

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repository_id": self.repository_id,
            "nodes": [n.model_dump() for n in self.nodes.values()],
            "edges": [e.model_dump() for e in self.edges]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RepositoryGraph":
        graph = cls(repository_id=data["repository_id"])
        for node_data in data.get("nodes", []):
            graph.add_node(GraphNode(**node_data))
        for edge_data in data.get("edges", []):
            graph.add_edge(GraphEdge(**edge_data))
        return graph

    def save(self, storage_dir: str) -> str:
        os.makedirs(storage_dir, exist_ok=True)
        file_path = os.path.join(storage_dir, f"{self.repository_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        return file_path

    @classmethod
    def load(cls, repository_id: str, storage_dir: str) -> Optional["RepositoryGraph"]:
        file_path = os.path.join(storage_dir, f"{self.repository_id}.json")
        if not os.path.isfile(file_path):
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
