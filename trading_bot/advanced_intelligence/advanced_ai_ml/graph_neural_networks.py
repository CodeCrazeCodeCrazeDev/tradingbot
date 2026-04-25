"""
Idea #8: Graph Neural Networks for Market Relationships
=========================================================
Model complex inter-asset relationships using dynamic graph neural networks.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    node_id: str
    features: np.ndarray
    node_type: str = "asset"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str
    weight: float
    edge_type: str = "correlation"
    features: Optional[np.ndarray] = None


@dataclass
class DynamicGraph:
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)
    adjacency_matrix: Optional[np.ndarray] = None
    timestamp: Optional[datetime] = None
    
    def add_node(self, node: GraphNode):
        self.nodes[node.node_id] = node
        
    def add_edge(self, edge: GraphEdge):
        self.edges.append(edge)
        
    def get_neighbors(self, node_id: str) -> List[str]:
        neighbors = []
        for edge in self.edges:
            if edge.source == node_id:
                neighbors.append(edge.target)
            elif edge.target == node_id:
                neighbors.append(edge.source)
        return neighbors
    
    def build_adjacency_matrix(self) -> np.ndarray:
        node_ids = list(self.nodes.keys())
        n = len(node_ids)
        adj = np.zeros((n, n))
        
        node_to_idx = {nid: i for i, nid in enumerate(node_ids)}
        
        for edge in self.edges:
            if edge.source in node_to_idx and edge.target in node_to_idx:
                i, j = node_to_idx[edge.source], node_to_idx[edge.target]
                adj[i, j] = edge.weight
                adj[j, i] = edge.weight
        
        self.adjacency_matrix = adj
        return adj


class GraphConvolutionLayer:
    """Graph Convolution Layer for message passing."""
    
    def __init__(self, in_features: int, out_features: int):
        self.in_features = in_features
        self.out_features = out_features
        self.weight = np.random.randn(in_features, out_features) * 0.01
        self.bias = np.zeros(out_features)
        
    def forward(self, node_features: np.ndarray, adjacency: np.ndarray) -> np.ndarray:
        degree = np.sum(adjacency, axis=1, keepdims=True) + 1
        norm_adj = adjacency / np.sqrt(degree @ degree.T + 1e-10)
        np.fill_diagonal(norm_adj, 1.0 / np.sqrt(degree.flatten() + 1))
        
        aggregated = norm_adj @ node_features
        output = aggregated @ self.weight + self.bias
        
        return np.maximum(0, output)


class GraphAttentionLayer:
    """Graph Attention Layer with learnable attention weights."""
    
    def __init__(self, in_features: int, out_features: int, num_heads: int = 4):
        self.in_features = in_features
        self.out_features = out_features
        self.num_heads = num_heads
        self.head_dim = out_features // num_heads
        
        self.W = np.random.randn(in_features, out_features) * 0.01
        self.a = np.random.randn(2 * self.head_dim, 1) * 0.01
        
    def forward(self, node_features: np.ndarray, adjacency: np.ndarray) -> np.ndarray:
        n_nodes = node_features.shape[0]
        
        h = node_features @ self.W
        
        attention_scores = np.zeros((n_nodes, n_nodes))
        
        for i in range(n_nodes):
            for j in range(n_nodes):
                if adjacency[i, j] > 0 or i == j:
                    concat = np.concatenate([h[i, :self.head_dim], h[j, :self.head_dim]])
                    attention_scores[i, j] = np.dot(concat, self.a.flatten())
        
        attention_scores = np.where(adjacency > 0, attention_scores, -1e9)
        np.fill_diagonal(attention_scores, 0)
        
        attention_weights = self._softmax(attention_scores)
        
        output = attention_weights @ h
        
        return np.maximum(0, output)
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / (np.sum(exp_x, axis=-1, keepdims=True) + 1e-10)


class TemporalGraphNetwork:
    """Temporal Graph Network for dynamic graph evolution."""
    
    def __init__(self, node_dim: int, edge_dim: int, time_dim: int):
        self.node_dim = node_dim
        self.edge_dim = edge_dim
        self.time_dim = time_dim
        
        self.memory = {}
        self.message_aggregator = np.random.randn(node_dim * 2 + edge_dim, node_dim) * 0.01
        self.memory_updater = np.random.randn(node_dim * 2, node_dim) * 0.01
        
    def compute_temporal_embedding(self, timestamps: np.ndarray) -> np.ndarray:
        div_term = np.exp(np.arange(0, self.time_dim, 2) * (-np.log(10000.0) / self.time_dim))
        
        pe = np.zeros((len(timestamps), self.time_dim))
        pe[:, 0::2] = np.sin(timestamps.reshape(-1, 1) * div_term)
        pe[:, 1::2] = np.cos(timestamps.reshape(-1, 1) * div_term)
        
        return pe
    
    def update_memory(self, node_id: str, message: np.ndarray):
        if node_id not in self.memory:
            self.memory[node_id] = np.zeros(self.node_dim)
        
        combined = np.concatenate([self.memory[node_id], message])
        self.memory[node_id] = np.tanh(combined @ self.memory_updater)
    
    def get_memory(self, node_id: str) -> np.ndarray:
        return self.memory.get(node_id, np.zeros(self.node_dim))


class GraphNeuralMarketNetwork:
    """
    Graph Neural Network for modeling market relationships.
    Captures complex inter-asset dependencies dynamically.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.node_dim = self.config.get("node_dim", 64)
        self.hidden_dim = self.config.get("hidden_dim", 128)
        self.num_layers = self.config.get("num_layers", 3)
        self.num_heads = self.config.get("num_heads", 4)
        
        self.gcn_layers = [
            GraphConvolutionLayer(self.node_dim if i == 0 else self.hidden_dim, self.hidden_dim)
            for i in range(self.num_layers)
        ]
        
        self.gat_layer = GraphAttentionLayer(self.hidden_dim, self.hidden_dim, self.num_heads)
        self.temporal_gnn = TemporalGraphNetwork(self.node_dim, 16, 32)
        
        self.current_graph: Optional[DynamicGraph] = None
        self.graph_history: List[DynamicGraph] = []
        
        self.initialized = False
        self.metrics = {
            "graphs_processed": 0,
            "nodes_tracked": 0,
            "edges_tracked": 0,
            "avg_clustering": 0.0
        }
        
    async def initialize(self):
        """Initialize the GNN system."""
        logger.info("Initializing Graph Neural Market Network")
        self.current_graph = DynamicGraph(timestamp=datetime.now())
        self.initialized = True
        
    async def build_market_graph(self, assets: List[str], 
                                  price_data: Dict[str, np.ndarray],
                                  correlation_threshold: float = 0.3) -> DynamicGraph:
        """Build market graph from price data."""
        if not self.initialized:
            await self.initialize()
        
        graph = DynamicGraph(timestamp=datetime.now())
        
        for asset in assets:
            if asset in price_data:
                features = self._extract_node_features(price_data[asset])
                node = GraphNode(
                    node_id=asset,
                    features=features,
                    node_type="asset"
                )
                graph.add_node(node)
        
        for i, asset1 in enumerate(assets):
            for asset2 in assets[i+1:]:
                if asset1 in price_data and asset2 in price_data:
                    corr = np.corrcoef(price_data[asset1], price_data[asset2])[0, 1]
                    
                    if abs(corr) > correlation_threshold:
                        edge = GraphEdge(
                            source=asset1,
                            target=asset2,
                            weight=abs(corr),
                            edge_type="positive_correlation" if corr > 0 else "negative_correlation"
                        )
                        graph.add_edge(edge)
        
        graph.build_adjacency_matrix()
        
        self.current_graph = graph
        self.graph_history.append(graph)
        
        self.metrics["graphs_processed"] += 1
        self.metrics["nodes_tracked"] = len(graph.nodes)
        self.metrics["edges_tracked"] = len(graph.edges)
        
        return graph
    
    def _extract_node_features(self, prices: np.ndarray) -> np.ndarray:
        """Extract features for a node from price data."""
        features = np.zeros(self.node_dim)
        
        if len(prices) > 1:
            returns = np.diff(prices) / (prices[:-1] + 1e-10)
            
            features[0] = np.mean(returns)
            features[1] = np.std(returns)
            features[2] = np.min(returns)
            features[3] = np.max(returns)
            
            if len(returns) > 5:
                features[4] = np.mean(returns[-5:])
                features[5] = np.std(returns[-5:])
            
            if len(returns) > 20:
                features[6] = np.mean(returns[-20:])
                features[7] = np.std(returns[-20:])
            
            features[8] = (prices[-1] - prices[0]) / (prices[0] + 1e-10)
            features[9] = prices[-1] / (np.mean(prices) + 1e-10)
        
        return features
    
    async def forward(self, graph: Optional[DynamicGraph] = None) -> np.ndarray:
        """Forward pass through GNN layers."""
        if graph is None:
            graph = self.current_graph
        
        if graph is None or not graph.nodes:
            return np.zeros((1, self.hidden_dim))
        
        node_ids = list(graph.nodes.keys())
        node_features = np.array([graph.nodes[nid].features for nid in node_ids])
        
        if node_features.shape[1] != self.node_dim:
            padding = np.zeros((node_features.shape[0], self.node_dim - node_features.shape[1]))
            node_features = np.concatenate([node_features, padding], axis=1)
        
        adjacency = graph.adjacency_matrix
        if adjacency is None:
            adjacency = graph.build_adjacency_matrix()
        
        h = node_features
        for gcn_layer in self.gcn_layers:
            h = gcn_layer.forward(h, adjacency)
        
        h = self.gat_layer.forward(h, adjacency)
        
        return h
    
    async def predict_relationships(self, graph: Optional[DynamicGraph] = None) -> Dict[str, Any]:
        """Predict future relationships between assets."""
        embeddings = await self.forward(graph)
        
        if graph is None:
            graph = self.current_graph
        
        node_ids = list(graph.nodes.keys())
        n = len(node_ids)
        
        predicted_edges = []
        
        for i in range(n):
            for j in range(i + 1, n):
                similarity = np.dot(embeddings[i], embeddings[j]) / (
                    np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j]) + 1e-10
                )
                
                if similarity > 0.5:
                    predicted_edges.append({
                        "source": node_ids[i],
                        "target": node_ids[j],
                        "predicted_strength": float(similarity)
                    })
        
        return {
            "predicted_edges": predicted_edges,
            "num_predictions": len(predicted_edges),
            "timestamp": datetime.now().isoformat()
        }
    
    async def detect_communities(self, graph: Optional[DynamicGraph] = None) -> Dict[str, List[str]]:
        """Detect asset communities using spectral clustering."""
        if graph is None:
            graph = self.current_graph
        
        if graph is None or len(graph.nodes) < 2:
            return {"community_0": list(graph.nodes.keys()) if graph else []}
        
        adjacency = graph.adjacency_matrix
        if adjacency is None:
            adjacency = graph.build_adjacency_matrix()
        
        degree = np.diag(np.sum(adjacency, axis=1))
        laplacian = degree - adjacency
        
        try:
            eigenvalues, eigenvectors = np.linalg.eigh(laplacian)
            
            k = min(3, len(eigenvalues))
            features = eigenvectors[:, 1:k+1]
            
            node_ids = list(graph.nodes.keys())
            communities = {}
            
            for i, node_id in enumerate(node_ids):
                community_idx = int(np.argmax(np.abs(features[i]))) if features.shape[1] > 0 else 0
                community_key = f"community_{community_idx}"
                
                if community_key not in communities:
                    communities[community_key] = []
                communities[community_key].append(node_id)
            
            return communities
        except:
            return {"community_0": list(graph.nodes.keys())}
    
    async def compute_centrality(self, graph: Optional[DynamicGraph] = None) -> Dict[str, float]:
        """Compute node centrality scores."""
        if graph is None:
            graph = self.current_graph
        
        if graph is None or not graph.nodes:
            return {}
        
        adjacency = graph.adjacency_matrix
        if adjacency is None:
            adjacency = graph.build_adjacency_matrix()
        
        degree_centrality = np.sum(adjacency, axis=1)
        
        if degree_centrality.sum() > 0:
            degree_centrality = degree_centrality / degree_centrality.sum()
        
        node_ids = list(graph.nodes.keys())
        
        return {node_ids[i]: float(degree_centrality[i]) for i in range(len(node_ids))}
    
    async def track_graph_evolution(self) -> Dict[str, Any]:
        """Track how the market graph evolves over time."""
        if len(self.graph_history) < 2:
            return {"evolution": "insufficient_history"}
        
        prev_graph = self.graph_history[-2]
        curr_graph = self.graph_history[-1]
        
        prev_edges = {(e.source, e.target) for e in prev_graph.edges}
        curr_edges = {(e.source, e.target) for e in curr_graph.edges}
        
        new_edges = curr_edges - prev_edges
        removed_edges = prev_edges - curr_edges
        
        return {
            "new_relationships": list(new_edges),
            "broken_relationships": list(removed_edges),
            "stability": 1.0 - len(new_edges | removed_edges) / (len(prev_edges | curr_edges) + 1),
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_asset_embedding(self, asset: str) -> Optional[np.ndarray]:
        """Get learned embedding for a specific asset."""
        if self.current_graph is None or asset not in self.current_graph.nodes:
            return None
        
        embeddings = await self.forward()
        node_ids = list(self.current_graph.nodes.keys())
        
        if asset in node_ids:
            idx = node_ids.index(asset)
            return embeddings[idx]
        
        return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get GNN metrics."""
        return {
            **self.metrics,
            "num_layers": self.num_layers,
            "node_dim": self.node_dim,
            "hidden_dim": self.hidden_dim,
            "graph_history_size": len(self.graph_history)
        }
    
    async def shutdown(self):
        """Shutdown the GNN system."""
        self.current_graph = None
        self.graph_history.clear()
        self.temporal_gnn.memory.clear()
        self.initialized = False
        logger.info("Graph Neural Market Network shutdown complete")
