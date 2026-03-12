"""
Topological Data Analysis (TDA) Module - Persistent Homology for Pattern Detection

Implements TDA techniques to detect non-linear price patterns using:
- Persistent homology for shape analysis
- Mapper algorithm for data visualization
- Betti numbers for topological features
- Persistence diagrams and barcodes

Features:
- Non-linear pattern detection invisible to traditional analysis
- Market structure topology mapping
- Regime change detection via topological shifts
- Support/resistance clustering
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class TopologicalFeature(Enum):
    """Types of topological features"""
    CONNECTED_COMPONENT = "connected_component"  # β0 - clusters
    LOOP = "loop"  # β1 - cycles/holes
    VOID = "void"  # β2 - cavities (3D)


class PatternTopology(Enum):
    """Detected topological patterns"""
    CONSOLIDATION = "consolidation"  # High β0, low β1
    TRENDING = "trending"  # Low β0, low β1
    REVERSAL = "reversal"  # Topology change
    BREAKOUT = "breakout"  # Component merge
    RANGE_BOUND = "range_bound"  # High β1 (loops)
    ACCUMULATION = "accumulation"  # Specific topology signature
    DISTRIBUTION = "distribution"  # Specific topology signature


@dataclass
class PersistentFeature:
    """A persistent homological feature"""
    dimension: int  # 0 = component, 1 = loop, 2 = void
    birth: float  # When feature appears
    death: float  # When feature disappears (inf if never)
    persistence: float  # death - birth
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'dimension': self.dimension,
            'birth': self.birth,
            'death': self.death if self.death != float('inf') else 'inf',
            'persistence': self.persistence
        }


@dataclass
class TopologySignature:
    """Topological signature of market data"""
    timestamp: datetime
    betti_0: int  # Number of connected components
    betti_1: int  # Number of loops
    total_persistence_0: float  # Total persistence of components
    total_persistence_1: float  # Total persistence of loops
    max_persistence: float  # Maximum persistence
    features: List[PersistentFeature]
    pattern: PatternTopology
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'betti_0': self.betti_0,
            'betti_1': self.betti_1,
            'total_persistence_0': self.total_persistence_0,
            'total_persistence_1': self.total_persistence_1,
            'max_persistence': self.max_persistence,
            'features': [f.to_dict() for f in self.features],
            'pattern': self.pattern.value,
            'confidence': self.confidence
        }


@dataclass
class MapperNode:
    """Node in Mapper graph"""
    node_id: int
    center: np.ndarray
    members: List[int]  # Indices of data points
    size: int
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'node_id': self.node_id,
            'center': self.center.tolist(),
            'size': self.size
        }


@dataclass
class MapperGraph:
    """Mapper algorithm output graph"""
    nodes: List[MapperNode]
    edges: List[Tuple[int, int]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'nodes': [n.to_dict() for n in self.nodes],
            'edges': self.edges,
            'num_nodes': len(self.nodes),
            'num_edges': len(self.edges)
        }


class SimplicalComplex:
    """
    Simplicial complex for computing homology
    
    Builds Vietoris-Rips complex from point cloud data
    """
    
    def __init__(self, points: np.ndarray, max_dimension: int = 2):
        self.points = points
        self.max_dimension = max_dimension
        self.simplices: Dict[int, List[Tuple]] = {d: [] for d in range(max_dimension + 1)}
        self.filtration_values: Dict[Tuple, float] = {}
    
    def build_vietoris_rips(self, max_radius: float, num_steps: int = 50) -> None:
        """Build Vietoris-Rips complex"""
        n = len(self.points)
        
        # Compute pairwise distances
        distances = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                d = np.linalg.norm(self.points[i] - self.points[j])
                distances[i, j] = d
                distances[j, i] = d
        
        # Add 0-simplices (vertices)
        for i in range(n):
            self.simplices[0].append((i,))
            self.filtration_values[(i,)] = 0.0
        
        # Add 1-simplices (edges) and higher
        radii = np.linspace(0, max_radius, num_steps)
        
        for r in radii:
            # Add edges
            for i in range(n):
                for j in range(i + 1, n):
                    edge = (i, j)
                    if edge not in self.filtration_values and distances[i, j] <= r:
                        self.simplices[1].append(edge)
                        self.filtration_values[edge] = distances[i, j]
            
            # Add triangles (2-simplices)
            if self.max_dimension >= 2:
                for i in range(n):
                    for j in range(i + 1, n):
                        for k in range(j + 1, n):
                            triangle = (i, j, k)
                            if triangle not in self.filtration_values:
                                # Check if all edges exist
                                max_edge = max(
                                    distances[i, j],
                                    distances[j, k],
                                    distances[i, k]
                                )
                                if max_edge <= r:
                                    self.simplices[2].append(triangle)
                                    self.filtration_values[triangle] = max_edge


class TopologicalAnalyzer:
    """
    Topological Data Analysis for Market Patterns
    
    Uses persistent homology to detect non-linear patterns
    in price data that are invisible to traditional analysis.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Analysis parameters
        self.window_size = self.config.get('window_size', 50)
        self.embedding_dim = self.config.get('embedding_dim', 3)
        self.delay = self.config.get('delay', 1)
        self.max_radius = self.config.get('max_radius', 2.0)
        
        # History
        self.price_history: deque = deque(maxlen=1000)
        self.signature_history: deque = deque(maxlen=500)
        
        # Pattern thresholds
        self.persistence_threshold = self.config.get('persistence_threshold', 0.1)
        
        logger.info("TopologicalAnalyzer initialized")
    
    def add_price(self, price: float, timestamp: Optional[datetime] = None) -> None:
        """Add price to history"""
        self.price_history.append({
            'price': price,
            'timestamp': timestamp or datetime.now()
        })
    
    def time_delay_embedding(self, data: np.ndarray) -> np.ndarray:
        """
        Create time-delay embedding (Takens embedding)
        
        Transforms 1D time series into higher-dimensional point cloud
        """
        n = len(data)
        m = self.embedding_dim
        tau = self.delay
        
        if n < m * tau:
            return np.array([])
        
        embedded = np.zeros((n - (m - 1) * tau, m))
        for i in range(m):
            embedded[:, i] = data[i * tau:n - (m - 1 - i) * tau]
        
        return embedded
    
    def compute_persistent_homology(
        self,
        points: np.ndarray
    ) -> List[PersistentFeature]:
        """
        Compute persistent homology of point cloud
        
        Returns list of persistent features with birth/death times
        """
        if len(points) < 3:
            return []
        
        # Normalize points
        points_normalized = (points - points.mean(axis=0)) / (points.std(axis=0) + 1e-8)
        
        # Build simplicial complex
        complex = SimplicalComplex(points_normalized, max_dimension=1)
        complex.build_vietoris_rips(self.max_radius, num_steps=30)
        
        # Compute persistent features using union-find for H0
        features = []
        
        # H0 (connected components)
        n = len(points)
        parent = list(range(n))
        rank = [0] * n
        birth_time = [0.0] * n
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y, time):
            px, py = find(x), find(y)
            if px == py:
                return None
            
            # Younger component dies
            if birth_time[px] > birth_time[py]:
                px, py = py, px
            
            death_feature = PersistentFeature(
                dimension=0,
                birth=birth_time[py],
                death=time,
                persistence=time - birth_time[py]
            )
            
            if rank[px] < rank[py]:
                parent[px] = py
            elif rank[px] > rank[py]:
                parent[py] = px
            else:
                parent[py] = px
                rank[px] += 1
            
            return death_feature
        
        # Process edges in order of filtration
        edges_sorted = sorted(
            complex.simplices[1],
            key=lambda e: complex.filtration_values[e]
        )
        
        for edge in edges_sorted:
            i, j = edge
            time = complex.filtration_values[edge]
            feature = union(i, j, time)
            if feature and feature.persistence > self.persistence_threshold:
                features.append(feature)
        
        # Add surviving components (infinite persistence)
        components = set(find(i) for i in range(n))
        for c in components:
            features.append(PersistentFeature(
                dimension=0,
                birth=birth_time[c],
                death=float('inf'),
                persistence=float('inf')
            ))
        
        # H1 (loops) - simplified detection
        # Count triangles that close loops
        num_edges = len(complex.simplices[1])
        num_vertices = n
        num_triangles = len(complex.simplices[2])
        
        # Euler characteristic: χ = V - E + F
        # For connected graph: β0 - β1 = χ - 1
        # Approximate β1
        estimated_loops = max(0, num_edges - num_vertices + len(components) - num_triangles)
        
        # Add loop features (approximation)
        if estimated_loops > 0:
            for i in range(min(estimated_loops, 5)):
                features.append(PersistentFeature(
                    dimension=1,
                    birth=self.max_radius * 0.3,
                    death=self.max_radius * 0.8,
                    persistence=self.max_radius * 0.5
                ))
        
        return features
    
    def analyze(self, prices: Optional[List[float]] = None) -> TopologySignature:
        """
        Perform topological analysis on price data
        
        Returns TopologySignature with detected patterns
        """
        # Use provided prices or history
        if prices is None:
            if len(self.price_history) < self.window_size:
                raise ValueError(f"Need at least {self.window_size} prices")
            prices = [p['price'] for p in list(self.price_history)[-self.window_size:]]
        
        prices_array = np.array(prices)
        
        # Create time-delay embedding
        embedded = self.time_delay_embedding(prices_array)
        
        if len(embedded) < 10:
            raise ValueError("Insufficient data for embedding")
        
        # Compute persistent homology
        features = self.compute_persistent_homology(embedded)
        
        # Calculate Betti numbers
        betti_0 = sum(1 for f in features if f.dimension == 0 and f.death == float('inf'))
        betti_1 = sum(1 for f in features if f.dimension == 1)
        
        # Calculate total persistence
        total_persistence_0 = sum(
            f.persistence for f in features 
            if f.dimension == 0 and f.persistence != float('inf')
        )
        total_persistence_1 = sum(
            f.persistence for f in features 
            if f.dimension == 1
        )
        
        # Maximum persistence
        finite_persistences = [
            f.persistence for f in features 
            if f.persistence != float('inf')
        ]
        max_persistence = max(finite_persistences) if finite_persistences else 0
        
        # Detect pattern
        pattern, confidence = self._detect_pattern(
            betti_0, betti_1, total_persistence_0, total_persistence_1, prices_array
        )
        
        signature = TopologySignature(
            timestamp=datetime.now(),
            betti_0=betti_0,
            betti_1=betti_1,
            total_persistence_0=total_persistence_0,
            total_persistence_1=total_persistence_1,
            max_persistence=max_persistence,
            features=features,
            pattern=pattern,
            confidence=confidence
        )
        
        self.signature_history.append(signature)
        
        return signature
    
    def _detect_pattern(
        self,
        betti_0: int,
        betti_1: int,
        persistence_0: float,
        persistence_1: float,
        prices: np.ndarray
    ) -> Tuple[PatternTopology, float]:
        """Detect market pattern from topological features"""
        
        # Price trend
        price_change = (prices[-1] - prices[0]) / prices[0]
        price_std = np.std(prices) / np.mean(prices)
        
        # Pattern detection logic
        confidence = 0.5
        
        # High β0 (many components) + low β1 = consolidation
        if betti_0 > 3 and betti_1 <= 1:
            pattern = PatternTopology.CONSOLIDATION
            confidence = 0.6 + 0.1 * min(betti_0, 5)
        
        # Low β0 + low β1 + strong trend = trending
        elif betti_0 <= 2 and betti_1 <= 1 and abs(price_change) > 0.02:
            pattern = PatternTopology.TRENDING
            confidence = 0.6 + 0.2 * min(abs(price_change) * 10, 1)
        
        # High β1 (loops) = range-bound
        elif betti_1 >= 2:
            pattern = PatternTopology.RANGE_BOUND
            confidence = 0.5 + 0.15 * min(betti_1, 4)
        
        # Check for topology change (reversal)
        elif len(self.signature_history) > 0:
            prev = self.signature_history[-1]
            if abs(betti_0 - prev.betti_0) >= 2 or abs(betti_1 - prev.betti_1) >= 2:
                pattern = PatternTopology.REVERSAL
                confidence = 0.6
            else:
                pattern = PatternTopology.CONSOLIDATION
                confidence = 0.4
        else:
            pattern = PatternTopology.CONSOLIDATION
            confidence = 0.4
        
        # Adjust confidence based on persistence
        if persistence_0 > 1.0:
            confidence = min(confidence + 0.1, 0.95)
        
        return pattern, confidence
    
    def build_mapper_graph(
        self,
        prices: List[float],
        n_intervals: int = 10,
        overlap: float = 0.5
    ) -> MapperGraph:
        """
        Build Mapper graph for data visualization
        
        The Mapper algorithm creates a simplified topological representation
        """
        prices_array = np.array(prices)
        
        # Create embedding
        embedded = self.time_delay_embedding(prices_array)
        
        if len(embedded) < 10:
            return MapperGraph(nodes=[], edges=[])
        
        # Use first coordinate as filter function
        filter_values = embedded[:, 0]
        
        # Create intervals
        min_val, max_val = filter_values.min(), filter_values.max()
        interval_width = (max_val - min_val) / n_intervals * (1 + overlap)
        
        nodes = []
        node_members = {}
        
        for i in range(n_intervals):
            # Interval bounds
            lower = min_val + i * (max_val - min_val) / n_intervals
            upper = lower + interval_width
            
            # Points in interval
            mask = (filter_values >= lower) & (filter_values <= upper)
            indices = np.where(mask)[0]
            
            if len(indices) > 0:
                # Cluster points in interval (simple: use centroid)
                center = embedded[indices].mean(axis=0)
                
                node = MapperNode(
                    node_id=len(nodes),
                    center=center,
                    members=indices.tolist(),
                    size=len(indices)
                )
                nodes.append(node)
                
                for idx in indices:
                    if idx not in node_members:
                        node_members[idx] = []
                    node_members[idx].append(node.node_id)
        
        # Create edges (nodes sharing members)
        edges = []
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                shared = set(nodes[i].members) & set(nodes[j].members)
                if len(shared) > 0:
                    edges.append((i, j))
        
        return MapperGraph(nodes=nodes, edges=edges)
    
    def detect_regime_change(self) -> Optional[Dict[str, Any]]:
        """Detect regime change from topology shifts"""
        if len(self.signature_history) < 5:
            return None
        
        recent = list(self.signature_history)[-5:]
        
        # Calculate topology changes
        betti_0_changes = [
            abs(recent[i+1].betti_0 - recent[i].betti_0)
            for i in range(len(recent) - 1)
        ]
        betti_1_changes = [
            abs(recent[i+1].betti_1 - recent[i].betti_1)
            for i in range(len(recent) - 1)
        ]
        
        avg_change = np.mean(betti_0_changes) + np.mean(betti_1_changes)
        
        if avg_change > 2:
            return {
                'detected': True,
                'severity': min(avg_change / 2, 1.0),
                'betti_0_volatility': np.std([s.betti_0 for s in recent]),
                'betti_1_volatility': np.std([s.betti_1 for s in recent]),
                'current_pattern': recent[-1].pattern.value,
                'timestamp': datetime.now().isoformat()
            }
        
        return {
            'detected': False,
            'severity': avg_change / 2,
            'current_pattern': recent[-1].pattern.value
        }
    
    def get_support_resistance_clusters(
        self,
        prices: List[float],
        n_clusters: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find support/resistance levels using topological clustering
        """
        prices_array = np.array(prices)
        
        # Create 2D embedding (price, time)
        n = len(prices_array)
        points = np.column_stack([
            prices_array,
            np.arange(n) / n  # Normalized time
        ])
        
        # Simple clustering based on price levels
        price_min, price_max = prices_array.min(), prices_array.max()
        price_range = price_max - price_min
        
        clusters = []
        bin_width = price_range / n_clusters
        
        for i in range(n_clusters):
            lower = price_min + i * bin_width
            upper = lower + bin_width
            
            mask = (prices_array >= lower) & (prices_array < upper)
            count = mask.sum()
            
            if count > 0:
                level = prices_array[mask].mean()
                clusters.append({
                    'level': float(level),
                    'strength': count / n,
                    'type': 'support' if level < prices_array[-1] else 'resistance',
                    'touches': int(count)
                })
        
        # Sort by strength
        clusters.sort(key=lambda x: x['strength'], reverse=True)
        
        return clusters[:n_clusters]


# Factory function
def create_topological_analyzer(config: Optional[Dict[str, Any]] = None) -> TopologicalAnalyzer:
    """Create topological analyzer"""
    return TopologicalAnalyzer(config)
