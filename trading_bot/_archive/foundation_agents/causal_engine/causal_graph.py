"""
Causal Graph - Visual Causal Relationship Mapping
====================================================

Builds and manages causal graphs for:
1. Visual representation of causal relationships
2. Path analysis
3. Confounder identification
4. DAG (Directed Acyclic Graph) validation

Provides tools for understanding and visualizing causal structures.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)


@dataclass
class CausalNode:
    """A node in the causal graph"""
    node_id: str
    name: str
    node_type: str = "variable"  # variable, latent, intervention, outcome
    
    # Metadata
    description: str = ""
    domain: str = ""  # e.g., "market", "economic", "behavioral"
    
    # Properties
    observed: bool = True
    
    def to_dict(self) -> Dict:
        return {
            'id': self.node_id,
            'name': self.name,
            'type': self.node_type,
            'description': self.description[:100] if self.description else ""
        }


@dataclass
class CausalEdge:
    """An edge in the causal graph"""
    source: str
    target: str
    
    # Edge properties
    strength: float = 1.0
    edge_type: str = "direct"  # direct, indirect, bidirected (confounding)
    
    # Temporal
    lag: int = 0  # 0 for instantaneous
    
    # Evidence
    evidence_type: str = "data"  # data, theory, assumption
    confidence: float = 0.5
    
    def to_dict(self) -> Dict:
        return {
            'source': self.source,
            'target': self.target,
            'strength': self.strength,
            'type': self.edge_type,
            'lag': self.lag,
            'confidence': self.confidence
        }


class CausalGraphBuilder:
    """
    Causal Graph Builder
    
    Constructs and manages causal graphs for visualizing and
    analyzing causal relationships between variables.
    """
    
    def __init__(self, name: str = "causal_graph"):
        self.name = name
        
        # Graph structure
        self.nodes: Dict[str, CausalNode] = {}
        self.edges: Dict[Tuple[str, str], CausalEdge] = {}
        
        # Indexing
        self.parents: Dict[str, Set[str]] = defaultdict(set)
        self.children: Dict[str, Set[str]] = defaultdict(set)
        
        # Paths
        self.paths_cache: Dict[Tuple[str, str], List[List[str]]] = {}
        
        # Statistics
        self.stats = {
            'nodes_added': 0,
            'edges_added': 0,
            'paths_computed': 0
        }
        
        logger.info(f"Causal Graph Builder '{name}' initialized")
    
    def add_node(
        self,
        node_id: str,
        name: str,
        node_type: str = "variable",
        description: str = "",
        domain: str = "",
        observed: bool = True
    ) -> CausalNode:
        """Add a node to the graph"""
        node = CausalNode(
            node_id=node_id,
            name=name,
            node_type=node_type,
            description=description,
            domain=domain,
            observed=observed
        )
        
        self.nodes[node_id] = node
        self.stats['nodes_added'] += 1
        
        return node
    
    def add_edge(
        self,
        source: str,
        target: str,
        strength: float = 1.0,
        edge_type: str = "direct",
        lag: int = 0,
        confidence: float = 0.5
    ) -> CausalEdge:
        """Add an edge to the graph"""
        # Ensure nodes exist
        if source not in self.nodes:
            self.add_node(source, source)
        if target not in self.nodes:
            self.add_node(target, target)
        
        edge = CausalEdge(
            source=source,
            target=target,
            strength=strength,
            edge_type=edge_type,
            lag=lag,
            confidence=confidence
        )
        
        key = (source, target)
        self.edges[key] = edge
        
        # Update indices
        self.children[source].add(target)
        self.parents[target].add(source)
        
        self.stats['edges_added'] += 1
        
        # Clear path cache
        self.paths_cache.clear()
        
        return edge
    
    def remove_edge(self, source: str, target: str) -> bool:
        """Remove an edge from the graph"""
        key = (source, target)
        if key in self.edges:
            del self.edges[key]
            self.children[source].discard(target)
            self.parents[target].discard(source)
            self.paths_cache.clear()
            return True
        return False
    
    def get_parents(self, node_id: str) -> Set[str]:
        """Get parent nodes"""
        return self.parents[node_id].copy()
    
    def get_children(self, node_id: str) -> Set[str]:
        """Get child nodes"""
        return self.children[node_id].copy()
    
    def get_ancestors(self, node_id: str) -> Set[str]:
        """Get all ancestors (recursive parents)"""
        ancestors = set()
        to_visit = [node_id]
        visited = set()
        
        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue
            visited.add(current)
            
            parents = self.get_parents(current)
            ancestors.update(parents)
            to_visit.extend(parents)
        
        return ancestors
    
    def get_descendants(self, node_id: str) -> Set[str]:
        """Get all descendants (recursive children)"""
        descendants = set()
        to_visit = [node_id]
        visited = set()
        
        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue
            visited.add(current)
            
            children = self.get_children(current)
            descendants.update(children)
            to_visit.extend(children)
        
        return descendants
    
    def get_siblings(self, node_id: str) -> Set[str]:
        """Get sibling nodes (share common parents)"""
        parents = self.get_parents(node_id)
        siblings = set()
        
        for parent in parents:
            siblings.update(self.get_children(parent))
        
        siblings.discard(node_id)
        return siblings
    
    def find_all_paths(
        self,
        source: str,
        target: str,
        max_length: int = 10
    ) -> List[List[str]]:
        """Find all paths from source to target"""
        cache_key = (source, target)
        
        if cache_key in self.paths_cache:
            return self.paths_cache[cache_key]
        
        paths = []
        queue = deque([(source, [source])])
        
        while queue:
            current, path = queue.popleft()
            
            if current == target and len(path) > 1:
                paths.append(path)
                continue
            
            if len(path) >= max_length:
                continue
            
            for child in self.get_children(current):
                if child not in path:  # Avoid cycles
                    queue.append((child, path + [child]))
        
        self.paths_cache[cache_key] = paths
        self.stats['paths_computed'] += 1
        
        return paths
    
    def find_backdoor_paths(self, x: str, y: str) -> List[List[str]]:
        """Find all backdoor paths (paths with arrow into X)"""
        backdoor_paths = []
        
        # Find all paths that end with an arrow into X
        for parent in self.get_parents(x):
            paths = self.find_all_paths(parent, y)
            for path in paths:
                if y not in path[:-1]:  # Ensure Y is the endpoint
                    backdoor_paths.append([x] + path)
        
        return backdoor_paths
    
    def identify_confounders(self, x: str, y: str) -> Set[str]:
        """Identify confounders between X and Y"""
        # Confounders are common ancestors
        ancestors_x = self.get_ancestors(x)
        ancestors_y = self.get_ancestors(y)
        
        confounders = ancestors_x.intersection(ancestors_y)
        
        # Remove X and Y themselves
        confounders.discard(x)
        confounders.discard(y)
        
        return confounders
    
    def identify_mediators(self, x: str, y: str) -> Set[str]:
        """Identify mediators between X and Y"""
        # Mediators are on directed paths from X to Y
        mediators = set()
        
        paths = self.find_all_paths(x, y)
        for path in paths:
            if len(path) > 2:
                # Internal nodes are mediators
                mediators.update(path[1:-1])
        
        return mediators
    
    def identify_colliders(self, x: str, y: str) -> Set[str]:
        """Identify colliders between X and Y"""
        # Colliders are nodes with paths from both X and Y
        colliders = set()
        
        descendants_x = self.get_descendants(x)
        descendants_y = self.get_descendants(y)
        
        # Common descendants
        common_descendants = descendants_x.intersection(descendants_y)
        
        for node in common_descendants:
            # Check if it's actually a collider (arrows from both sides)
            parents = self.get_parents(node)
            if x in self.get_ancestors(node) and y in self.get_ancestors(node):
                # Check if paths go through different parents
                if len(parents) >= 2:
                    colliders.add(node)
        
        return colliders
    
    def is_dag(self) -> bool:
        """Check if graph is a Directed Acyclic Graph (DAG)"""
        # Topological sort check
        visited = set()
        recursion_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            recursion_stack.add(node)
            
            for child in self.get_children(node):
                if child not in visited:
                    if has_cycle(child):
                        return True
                elif child in recursion_stack:
                    return True
            
            recursion_stack.remove(node)
            return False
        
        for node in self.nodes:
            if node not in visited:
                if has_cycle(node):
                    return False
        
        return True
    
    def get_topological_order(self) -> Optional[List[str]]:
        """Get topological ordering of nodes (if DAG)"""
        if not self.is_dag():
            return None
        
        # Kahn's algorithm
        in_degree = {node: len(self.get_parents(node)) for node in self.nodes}
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        order = []
        
        while queue:
            node = queue.popleft()
            order.append(node)
            
            for child in self.get_children(node):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)
        
        return order if len(order) == len(self.nodes) else None
    
    def to_networkx(self):
        """Convert to NetworkX graph"""
        try:
            import networkx as nx
            
            G = nx.DiGraph()
            
            # Add nodes
            for node_id, node in self.nodes.items():
                G.add_node(node_id, **node.to_dict())
            
            # Add edges
            for (source, target), edge in self.edges.items():
                G.add_edge(source, target, **edge.to_dict())
            
            return G
        except ImportError:
            logger.warning("NetworkX not available")
            return None
    
    def to_dict(self) -> Dict:
        """Convert graph to dictionary"""
        return {
            'name': self.name,
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges.values()],
            'is_dag': self.is_dag(),
            'node_count': len(self.nodes),
            'edge_count': len(self.edges)
        }
    
    def to_json(self, filepath: Optional[str] = None) -> str:
        """Export graph to JSON"""
        data = self.to_dict()
        json_str = json.dumps(data, indent=2)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
        
        return json_str
    
    def export_for_d3(self) -> Dict:
        """Export graph in D3.js compatible format"""
        return {
            'nodes': [
                {
                    'id': node_id,
                    'name': node.name,
                    'group': node.domain or 'default',
                    'type': node.node_type
                }
                for node_id, node in self.nodes.items()
            ],
            'links': [
                {
                    'source': edge.source,
                    'target': edge.target,
                    'value': edge.strength,
                    'type': edge.edge_type
                }
                for edge in self.edges.values()
            ]
        }
    
    def export_for_cytoscape(self) -> List[Dict]:
        """Export graph in Cytoscape.js compatible format"""
        elements = []
        
        # Nodes
        for node_id, node in self.nodes.items():
            elements.append({
                'data': {
                    'id': node_id,
                    'label': node.name,
                    'type': node.node_type
                }
            })
        
        # Edges
        for i, ((source, target), edge) in enumerate(self.edges.items()):
            elements.append({
                'data': {
                    'id': f'e{i}',
                    'source': source,
                    'target': target,
                    'strength': edge.strength,
                    'type': edge.edge_type
                }
            })
        
        return elements
    
    def get_statistics(self) -> Dict:
        """Get graph statistics"""
        return {
            **self.stats,
            'node_count': len(self.nodes),
            'edge_count': len(self.edges),
            'is_dag': self.is_dag(),
            'avg_out_degree': np.mean([len(self.get_children(n)) for n in self.nodes]) if self.nodes else 0,
            'avg_in_degree': np.mean([len(self.get_parents(n)) for n in self.nodes]) if self.nodes else 0
        }
    
    @classmethod
    def from_edges(
        cls,
        edges: List[Tuple[str, str]],
        name: str = "imported_graph"
    ) -> 'CausalGraphBuilder':
        """Create graph from edge list"""
        graph = cls(name)
        
        for source, target in edges:
            graph.add_edge(source, target)
        
        return graph
    
    @classmethod
    def from_adjacency_matrix(
        cls,
        matrix: np.ndarray,
        node_names: List[str],
        name: str = "matrix_graph"
    ) -> 'CausalGraphBuilder':
        """Create graph from adjacency matrix"""
        graph = cls(name)
        
        n = len(node_names)
        for i in range(n):
            graph.add_node(node_names[i], node_names[i])
            for j in range(n):
                if matrix[i, j] != 0:
                    graph.add_edge(
                        node_names[i],
                        node_names[j],
                        strength=float(matrix[i, j])
                    )
        
        return graph
