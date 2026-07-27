"""
Research Graph (Cognitive Memory) Subsystem for Research OS.
Leverages NetworkX to accumulate structured, auditable scientific knowledge.
Supports lineage tracing, dependency resolution, contradiction discovery, and GraphML/JSON export.
"""

from typing import Dict, Any, List, Optional, Tuple
import json
import networkx as nx
from trading_bot.research.core.interfaces import GraphStore

import logging
logger = logging.getLogger(__name__)


class NetworkXGraphStore(GraphStore):
    """
    Core Graph database engine utilizing NetworkX backend.
    Preserves full quantitative R&D provenance and lineage for absolute reproducibility.
    """

    def __init__(self):
        self._graph = nx.DiGraph()

    def add_node(self, node_id: str, node_type: str, properties: Dict[str, Any]) -> None:
        """
        Inserts a research entity into the Graph.
        """
        props = properties.copy()
        props["node_type"] = node_type
        props["id"] = node_id
        self._graph.add_node(node_id, **props)
        logger.debug(f"GraphNode Added: {node_id} ({node_type})")

    def add_edge(self, source_id: str, target_id: str, relationship_type: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """
        Draws a scientific link between two existing nodes in the graph.
        """
        props = properties.copy() if properties else {}
        props["relationship_type"] = relationship_type

        # Ensure nodes exist in the graph (auto-create placeholders if needed to avoid orphans)
        if not self._graph.has_node(source_id):
            self.add_node(source_id, "placeholder", {"created_by": "auto_edge_generation"})
        if not self._graph.has_node(target_id):
            self.add_node(target_id, "placeholder", {"created_by": "auto_edge_generation"})

        self._graph.add_edge(source_id, target_id, **props)
        logger.debug(f"GraphEdge Added: {source_id} --({relationship_type})--> {target_id}")

    def query_semantic(self, query_type: str, *args, **kwargs) -> Any:
        """
        Executes semantic graph queries. Supported query types:
          - lineage_tracing: returns the path of ancestor nodes generating this node.
          - dependency_analysis: returns all features/datasets this node depends on.
          - evidence_lookup: returns statistical tests confirming/validating this node.
          - contradiction_discovery: returns nodes that contradict or refute this node.
          - failed_experiments: returns failed experiment child nodes.
          - genealogy: returns parents, siblings, and children of this node.
        """
        node_id = args[0] if len(args) > 0 else kwargs.get("node_id")
        if not node_id or not self._graph.has_node(node_id):
            return []

        if query_type == "lineage_tracing":
            return self._query_lineage(node_id)
        elif query_type == "dependency_analysis":
            return self._query_dependencies(node_id)
        elif query_type == "evidence_lookup":
            return self._query_evidence(node_id)
        elif query_type == "contradiction_discovery":
            return self._query_contradictions(node_id)
        elif query_type == "failed_experiments":
            return self._query_failed_experiments(node_id)
        elif query_type == "genealogy":
            return self._query_genealogy(node_id)
        else:
            logger.warning(f"Unknown semantic query type: {query_type}")
            return []

    def _query_lineage(self, node_id: str) -> List[Dict[str, Any]]:
        """Trace lineage using simple depth-first search on ancestors."""
        # Finds all nodes that feed into the target node (parents, papers, etc.)
        ancestors = nx.ancestors(self._graph, node_id)
        nodes_list = []
        for anc in ancestors:
            nodes_list.append(dict(self._graph.nodes[anc]))
        return nodes_list

    def _query_dependencies(self, node_id: str) -> List[Dict[str, Any]]:
        """Returns all features and datasets on which the node directly or indirectly depends."""
        ancestors = nx.ancestors(self._graph, node_id)
        deps = []
        for anc in ancestors:
            node_data = self._graph.nodes[anc]
            if node_data.get("node_type") in ["dataset", "feature"]:
                deps.append(node_data)
        return deps

    def _query_evidence(self, node_id: str) -> List[Dict[str, Any]]:
        """Retrieves statistical tests or metrics that 'validate' or provide evidence for this node."""
        evidence = []
        # Look for incoming or outgoing edges with validates relationship
        for src, dst, data in self._graph.edges(data=True):
            if data.get("relationship_type") == "validates":
                if dst == node_id:
                    evidence.append(self._graph.nodes[src])
                elif src == node_id:
                    evidence.append(self._graph.nodes[dst])
        return evidence

    def _query_contradictions(self, node_id: str) -> List[Dict[str, Any]]:
        """Discovers nodes having 'contradicts' relationships with this node."""
        contradictions = []
        for src, dst, data in self._graph.edges(data=True):
            if data.get("relationship_type") == "contradicts":
                if dst == node_id:
                    contradictions.append(self._graph.nodes[src])
                elif src == node_id:
                    contradictions.append(self._graph.nodes[dst])
        return contradictions

    def _query_failed_experiments(self, node_id: str) -> List[Dict[str, Any]]:
        """Retrieves downstream experiments that failed."""
        descendants = nx.descendants(self._graph, node_id)
        failed = []
        for desc in descendants:
            node_data = self._graph.nodes[desc]
            if node_data.get("node_type") == "experiment" and not node_data.get("success", True):
                failed.append(node_data)
        return failed

    def _query_genealogy(self, node_id: str) -> Dict[str, Any]:
        """Provides Parents, Children, and Siblings of the node."""
        parents = [p for p in self._graph.predecessors(node_id)]
        children = [c for c in self._graph.successors(node_id)]

        siblings = []
        for p in parents:
            for s in self._graph.successors(p):
                if s != node_id and s not in siblings:
                    siblings.append(s)

        return {
            "node": dict(self._graph.nodes[node_id]),
            "parents": [dict(self._graph.nodes[p]) for p in parents],
            "children": [dict(self._graph.nodes[c]) for c in children],
            "siblings": [dict(self._graph.nodes[s]) for s in siblings]
        }

    def export_graph(self, format_type: str = "json") -> str:
        """
        Exports the entire graph into a clean representation.
        Supports GraphML and JSON string conversions.
        """
        if format_type.lower() == "graphml":
            # Direct GraphML serialization
            import tempfile
            import os
            # Use temporary file to write graphml then read back to string
            fd, path = tempfile.mkstemp()
            try:
                nx.write_graphml(self._graph, path)
                with open(path, 'r') as f:
                    return f.read()
            finally:
                os.close(fd)
                os.remove(path)
        else:
            # Standard node-link JSON export
            from networkx.readwrite import json_graph
            data = json_graph.node_link_data(self._graph)
            return json.dumps(data, indent=2)

    def load_graph(self, data_str: str, format_type: str = "json") -> None:
        """Loads a previously exported graph store."""
        if format_type.lower() == "graphml":
            import tempfile
            import os
            fd, path = tempfile.mkstemp()
            try:
                with open(path, 'w') as f:
                    f.write(data_str)
                self._graph = nx.read_graphml(path)
            finally:
                os.close(fd)
                os.remove(path)
        else:
            from networkx.readwrite import json_graph
            data = json.loads(data_str)
            self._graph = json_graph.node_link_graph(data)
