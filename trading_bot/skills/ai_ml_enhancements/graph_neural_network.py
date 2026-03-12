"""
Skill #17: Graph Neural Network
===============================

Models asset relationships as graphs for cross-asset analysis
and correlation-based predictions.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EdgeType(Enum):
    """Type of relationship between assets."""
    CORRELATION = "correlation"
    CAUSATION = "causation"
    SECTOR = "sector"
    SUPPLY_CHAIN = "supply_chain"
    COMPETITION = "competition"


@dataclass
class GraphNode:
    """Node in the asset graph."""
    symbol: str
    features: np.ndarray
    embedding: np.ndarray
    node_type: str
    importance: float


@dataclass
class GraphEdge:
    """Edge connecting two assets."""
    source: str
    target: str
    edge_type: EdgeType
    weight: float
    is_directed: bool


@dataclass
class GraphPrediction:
    """Prediction from GNN."""
    symbol: str
    predicted_return: float
    confidence: float
    influential_neighbors: List[str]
    propagation_score: float


@dataclass
class GNNAnalysisResult:
    """Complete GNN analysis result."""
    predictions: Dict[str, GraphPrediction]
    graph_structure: Dict[str, List[str]]
    central_nodes: List[str]
    clusters: List[Set[str]]
    contagion_risk: float
    diversification_score: float
    trading_signals: Dict[str, str]


class GraphNeuralNetwork:
    """
    Advanced Graph Neural Network for Asset Analysis.
    
    Models cross-asset relationships and propagates information.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.hidden_dim = self.config.get('hidden_dim', 64)
            self.num_layers = self.config.get('num_layers', 3)
            self.aggregation = self.config.get('aggregation', 'mean')
        
            self.nodes: Dict[str, GraphNode] = {}
            self.edges: List[GraphEdge] = []
            self.adjacency: Dict[str, List[str]] = {}
        
            # GNN weights
            self.weights = self._initialize_weights()
        
            logger.info("GraphNeuralNetwork initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _initialize_weights(self) -> Dict:
        """Initialize GNN weights."""
        return {
            'message': np.random.randn(self.hidden_dim, self.hidden_dim) * 0.1,
            'update': np.random.randn(self.hidden_dim, self.hidden_dim) * 0.1,
            'output': np.random.randn(self.hidden_dim, 1) * 0.1,
            'attention': np.random.randn(2 * self.hidden_dim, 1) * 0.1,
        }
    
    def build_graph(
        self,
        symbols: List[str],
        price_data: Dict[str, np.ndarray],
        correlation_threshold: float = 0.5
    ):
        """
        Build asset graph from price data.
        
        Args:
            symbols: List of asset symbols
            price_data: Dict of symbol -> price array
            correlation_threshold: Minimum correlation for edge
        """
        # Create nodes
        try:
            for symbol in symbols:
                if symbol in price_data:
                    prices = price_data[symbol]
                    features = self._extract_node_features(prices)
                    embedding = np.random.randn(self.hidden_dim) * 0.1
                
                    self.nodes[symbol] = GraphNode(
                        symbol=symbol,
                        features=features,
                        embedding=embedding,
                        node_type='asset',
                        importance=0.0
                    )
                    self.adjacency[symbol] = []
        
            # Create edges based on correlation
            for i, sym1 in enumerate(symbols):
                for sym2 in symbols[i+1:]:
                    if sym1 in price_data and sym2 in price_data:
                        corr = self._calculate_correlation(
                            price_data[sym1], price_data[sym2]
                        )
                    
                        if abs(corr) > correlation_threshold:
                            edge = GraphEdge(
                                source=sym1,
                                target=sym2,
                                edge_type=EdgeType.CORRELATION,
                                weight=corr,
                                is_directed=False
                            )
                            self.edges.append(edge)
                            self.adjacency[sym1].append(sym2)
                            self.adjacency[sym2].append(sym1)
        
            # Calculate node importance (PageRank-like)
            self._calculate_node_importance()
        
            logger.info(f"Built graph with {len(self.nodes)} nodes and {len(self.edges)} edges")
        except Exception as e:
            logger.error(f"Error in build_graph: {e}")
            raise
    
    def _extract_node_features(self, prices: np.ndarray) -> np.ndarray:
        """Extract features for a node."""
        try:
            if len(prices) < 20:
                return np.zeros(10)
        
            returns = np.diff(prices) / prices[:-1]
        
            features = np.array([
                np.mean(returns),
                np.std(returns),
                np.min(returns),
                np.max(returns),
                self._calculate_sharpe(returns),
                self._calculate_skewness(returns),
                self._calculate_kurtosis(returns),
                np.mean(prices[-5:]) / np.mean(prices[-20:]) - 1,
                np.std(prices[-5:]) / np.std(prices[-20:]),
                len(prices)
            ])
        
            return features
        except Exception as e:
            logger.error(f"Error in _extract_node_features: {e}")
            raise
    
    def _calculate_correlation(self, prices1: np.ndarray, prices2: np.ndarray) -> float:
        """Calculate correlation between two price series."""
        try:
            min_len = min(len(prices1), len(prices2))
            if min_len < 10:
                return 0.0
        
            returns1 = np.diff(prices1[-min_len:]) / prices1[-min_len:-1]
            returns2 = np.diff(prices2[-min_len:]) / prices2[-min_len:-1]
        
            return np.corrcoef(returns1, returns2)[0, 1]
        except Exception as e:
            logger.error(f"Error in _calculate_correlation: {e}")
            raise
    
    def _calculate_sharpe(self, returns: np.ndarray) -> float:
        """Calculate Sharpe ratio."""
        try:
            if np.std(returns) == 0:
                return 0.0
            return np.mean(returns) / np.std(returns) * np.sqrt(252)
        except Exception as e:
            logger.error(f"Error in _calculate_sharpe: {e}")
            raise
    
    def _calculate_skewness(self, returns: np.ndarray) -> float:
        """Calculate skewness."""
        try:
            mean = np.mean(returns)
            std = np.std(returns)
            if std == 0:
                return 0.0
            return np.mean(((returns - mean) / std) ** 3)
        except Exception as e:
            logger.error(f"Error in _calculate_skewness: {e}")
            raise
    
    def _calculate_kurtosis(self, returns: np.ndarray) -> float:
        """Calculate kurtosis."""
        try:
            mean = np.mean(returns)
            std = np.std(returns)
            if std == 0:
                return 0.0
            return np.mean(((returns - mean) / std) ** 4) - 3
        except Exception as e:
            logger.error(f"Error in _calculate_kurtosis: {e}")
            raise
    
    def _calculate_node_importance(self):
        """Calculate node importance using PageRank."""
        try:
            damping = 0.85
            iterations = 20
        
            n = len(self.nodes)
            if n == 0:
                return
        
            # Initialize scores
            scores = {sym: 1.0 / n for sym in self.nodes}
        
            for _ in range(iterations):
                new_scores = {}
                for sym in self.nodes:
                    # Sum contributions from neighbors
                    neighbor_sum = 0
                    for neighbor in self.adjacency.get(sym, []):
                        num_neighbors = len(self.adjacency.get(neighbor, []))
                        if num_neighbors > 0:
                            neighbor_sum += scores[neighbor] / num_neighbors
                
                    new_scores[sym] = (1 - damping) / n + damping * neighbor_sum
            
                scores = new_scores
        
            # Update node importance
            for sym, score in scores.items():
                self.nodes[sym].importance = score
        except Exception as e:
            logger.error(f"Error in _calculate_node_importance: {e}")
            raise
    
    def analyze(
        self,
        target_symbols: Optional[List[str]] = None
    ) -> GNNAnalysisResult:
        """
        Analyze graph and generate predictions.
        
        Args:
            target_symbols: Symbols to predict (None = all)
            
        Returns:
            GNNAnalysisResult with analysis
        """
        try:
            if not self.nodes:
                return self._create_empty_result()
        
            target_symbols = target_symbols or list(self.nodes.keys())
        
            # Run message passing
            self._message_passing()
        
            # Generate predictions
            predictions = {}
            for symbol in target_symbols:
                if symbol in self.nodes:
                    pred = self._predict_node(symbol)
                    predictions[symbol] = pred
        
            # Get graph structure
            structure = {sym: neighbors for sym, neighbors in self.adjacency.items()}
        
            # Find central nodes
            central = self._find_central_nodes()
        
            # Find clusters
            clusters = self._find_clusters()
        
            # Calculate contagion risk
            contagion = self._calculate_contagion_risk()
        
            # Calculate diversification
            diversification = self._calculate_diversification(target_symbols)
        
            # Generate signals
            signals = {
                sym: self._generate_signal(pred)
                for sym, pred in predictions.items()
            }
        
            return GNNAnalysisResult(
                predictions=predictions,
                graph_structure=structure,
                central_nodes=central,
                clusters=clusters,
                contagion_risk=contagion,
                diversification_score=diversification,
                trading_signals=signals
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
    
    def _message_passing(self):
        """Run message passing layers."""
        try:
            for _ in range(self.num_layers):
                new_embeddings = {}
            
                for symbol, node in self.nodes.items():
                    # Aggregate neighbor messages
                    neighbors = self.adjacency.get(symbol, [])
                
                    if neighbors:
                        messages = []
                        for neighbor in neighbors:
                            neighbor_emb = self.nodes[neighbor].embedding
                            message = neighbor_emb @ self.weights['message']
                            messages.append(message)
                    
                        # Aggregate
                        if self.aggregation == 'mean':
                            aggregated = np.mean(messages, axis=0)
                        elif self.aggregation == 'sum':
                            aggregated = np.sum(messages, axis=0)
                        else:
                            aggregated = np.max(messages, axis=0)
                    
                        # Update
                        new_emb = np.tanh(
                            node.embedding @ self.weights['update'] + aggregated
                        )
                    else:
                        new_emb = node.embedding
                
                    new_embeddings[symbol] = new_emb
            
                # Update all embeddings
                for symbol, emb in new_embeddings.items():
                    self.nodes[symbol].embedding = emb
        except Exception as e:
            logger.error(f"Error in _message_passing: {e}")
            raise
    
    def _predict_node(self, symbol: str) -> GraphPrediction:
        """Generate prediction for a node."""
        try:
            node = self.nodes[symbol]
        
            # Predict return from embedding
            predicted_return = float(node.embedding @ self.weights['output'])
            predicted_return = np.clip(predicted_return, -0.1, 0.1)
        
            # Confidence from embedding magnitude
            confidence = min(0.9, 0.5 + np.linalg.norm(node.embedding) * 0.1)
        
            # Find influential neighbors
            neighbors = self.adjacency.get(symbol, [])
            influential = sorted(
                neighbors,
                key=lambda n: self.nodes[n].importance,
                reverse=True
            )[:5]
        
            # Propagation score
            propagation = node.importance * len(neighbors)
        
            return GraphPrediction(
                symbol=symbol,
                predicted_return=predicted_return,
                confidence=confidence,
                influential_neighbors=influential,
                propagation_score=propagation
            )
        except Exception as e:
            logger.error(f"Error in _predict_node: {e}")
            raise
    
    def _find_central_nodes(self) -> List[str]:
        """Find most central nodes."""
        try:
            sorted_nodes = sorted(
                self.nodes.items(),
                key=lambda x: x[1].importance,
                reverse=True
            )
            return [sym for sym, _ in sorted_nodes[:5]]
        except Exception as e:
            logger.error(f"Error in _find_central_nodes: {e}")
            raise
    
    def _find_clusters(self) -> List[Set[str]]:
        """Find clusters using connected components."""
        try:
            visited = set()
            clusters = []
        
            for symbol in self.nodes:
                if symbol not in visited:
                    cluster = set()
                    self._dfs(symbol, visited, cluster)
                    if len(cluster) > 1:
                        clusters.append(cluster)
        
            return clusters
        except Exception as e:
            logger.error(f"Error in _find_clusters: {e}")
            raise
    
    def _dfs(self, symbol: str, visited: Set[str], cluster: Set[str]):
        """Depth-first search for clustering."""
        try:
            visited.add(symbol)
            cluster.add(symbol)
        
            for neighbor in self.adjacency.get(symbol, []):
                if neighbor not in visited:
                    self._dfs(neighbor, visited, cluster)
        except Exception as e:
            logger.error(f"Error in _dfs: {e}")
            raise
    
    def _calculate_contagion_risk(self) -> float:
        """Calculate contagion risk in the graph."""
        try:
            if not self.edges:
                return 0.0
        
            # Average edge weight (correlation)
            avg_weight = np.mean([abs(e.weight) for e in self.edges])
        
            # Graph density
            n = len(self.nodes)
            max_edges = n * (n - 1) / 2
            density = len(self.edges) / max_edges if max_edges > 0 else 0
        
            # Contagion risk
            return avg_weight * density
        except Exception as e:
            logger.error(f"Error in _calculate_contagion_risk: {e}")
            raise
    
    def _calculate_diversification(self, symbols: List[str]) -> float:
        """Calculate diversification score."""
        try:
            if len(symbols) < 2:
                return 0.0
        
            # Count edges between selected symbols
            internal_edges = 0
            for edge in self.edges:
                if edge.source in symbols and edge.target in symbols:
                    internal_edges += 1
        
            max_edges = len(symbols) * (len(symbols) - 1) / 2
            connectivity = internal_edges / max_edges if max_edges > 0 else 0
        
            # Lower connectivity = better diversification
            return 1 - connectivity
        except Exception as e:
            logger.error(f"Error in _calculate_diversification: {e}")
            raise
    
    def _generate_signal(self, prediction: GraphPrediction) -> str:
        """Generate trading signal from prediction."""
        try:
            if prediction.confidence < 0.5:
                return "NEUTRAL: Low confidence"
        
            if prediction.predicted_return > 0.02:
                return f"STRONG BUY: {prediction.predicted_return:.1%} expected"
            elif prediction.predicted_return > 0:
                return f"BUY: {prediction.predicted_return:.1%} expected"
            elif prediction.predicted_return < -0.02:
                return f"STRONG SELL: {prediction.predicted_return:.1%} expected"
            else:
                return f"SELL: {prediction.predicted_return:.1%} expected"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _create_empty_result(self) -> GNNAnalysisResult:
        """Create empty result."""
        return GNNAnalysisResult(
            predictions={},
            graph_structure={},
            central_nodes=[],
            clusters=[],
            contagion_risk=0,
            diversification_score=0,
            trading_signals={}
        )
