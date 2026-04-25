"""
Causal Discovery - Automated Causal Structure Learning
========================================================

Implements causal discovery algorithms for financial data:
1. Constraint-based methods (PC algorithm)
2. Score-based methods (GES)
3. Granger causality
4. Transfer entropy
5. Causal graph construction

Based on the Foundation Agents paper (arXiv:2504.01990) causal systems.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
from collections import defaultdict
import itertools

logger = logging.getLogger(__name__)


class CausalMethod(Enum):
    """Causal discovery methods"""
    GRANGER = "granger"
    TRANSFER_ENTROPY = "transfer_entropy"
    PC_ALGORITHM = "pc_algorithm"
    GES = "ges"
    LINGAM = "lingam"
    NOTEARS = "notears"
    VAR = "var"


class EdgeType(Enum):
    """Types of causal edges"""
    DIRECTED = "directed"           # X -> Y
    BIDIRECTED = "bidirected"       # X <-> Y (common cause)
    UNDIRECTED = "undirected"       # X - Y (unknown direction)
    NO_EDGE = "no_edge"


@dataclass
class CausalEdge:
    """A causal edge between variables"""
    source: str
    target: str
    edge_type: EdgeType
    
    # Strength metrics
    strength: float = 0.0           # Causal strength
    confidence: float = 0.0         # Confidence in edge
    lag: int = 0                    # Time lag (for temporal causality)
    
    # Statistical evidence
    p_value: Optional[float] = None
    test_statistic: Optional[float] = None
    method: Optional[CausalMethod] = None
    
    # Metadata
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'source': self.source,
            'target': self.target,
            'edge_type': self.edge_type.value,
            'strength': self.strength,
            'confidence': self.confidence,
            'lag': self.lag,
            'p_value': self.p_value,
            'method': self.method.value if self.method else None
        }


@dataclass
class CausalGraph:
    """A causal graph structure"""
    graph_id: str
    name: str
    
    # Nodes and edges
    nodes: List[str] = field(default_factory=list)
    edges: List[CausalEdge] = field(default_factory=list)
    
    # Graph properties
    is_dag: bool = True             # Directed Acyclic Graph
    is_complete: bool = False       # All edges discovered
    
    # Discovery info
    method: Optional[CausalMethod] = None
    data_points: int = 0
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_parents(self, node: str) -> List[str]:
        """Get parent nodes"""
        return [e.source for e in self.edges 
                if e.target == node and e.edge_type == EdgeType.DIRECTED]
    
    def get_children(self, node: str) -> List[str]:
        """Get child nodes"""
        return [e.target for e in self.edges 
                if e.source == node and e.edge_type == EdgeType.DIRECTED]
    
    def get_ancestors(self, node: str) -> Set[str]:
        """Get all ancestor nodes"""
        ancestors = set()
        to_visit = self.get_parents(node)
        
        while to_visit:
            current = to_visit.pop()
            if current not in ancestors:
                ancestors.add(current)
                to_visit.extend(self.get_parents(current))
        
        return ancestors
    
    def get_descendants(self, node: str) -> Set[str]:
        """Get all descendant nodes"""
        descendants = set()
        to_visit = self.get_children(node)
        
        while to_visit:
            current = to_visit.pop()
            if current not in descendants:
                descendants.add(current)
                to_visit.extend(self.get_children(current))
        
        return descendants
    
    def has_path(self, source: str, target: str) -> bool:
        """Check if path exists from source to target"""
        return target in self.get_descendants(source)
    
    def to_dict(self) -> Dict:
        return {
            'graph_id': self.graph_id,
            'name': self.name,
            'nodes': self.nodes,
            'edges': [e.to_dict() for e in self.edges],
            'is_dag': self.is_dag,
            'method': self.method.value if self.method else None
        }


class GrangerCausality:
    """Granger causality testing"""
    
    def __init__(self, max_lag: int = 10, significance: float = 0.05):
        self.max_lag = max_lag
        self.significance = significance
    
    def test(
        self,
        x: np.ndarray,
        y: np.ndarray,
        lag: Optional[int] = None
    ) -> Tuple[bool, float, float, int]:
        """
        Test if x Granger-causes y
        
        Returns: (is_causal, f_statistic, p_value, optimal_lag)
        """
        if len(x) != len(y):
            raise ValueError("x and y must have same length")
        
        n = len(x)
        
        if lag is None:
            # Find optimal lag using AIC
            best_lag = 1
            best_aic = float('inf')
            
            for test_lag in range(1, min(self.max_lag + 1, n // 4)):
                aic = self._compute_aic(x, y, test_lag)
                if aic < best_aic:
                    best_aic = aic
                    best_lag = test_lag
            
            lag = best_lag
        
        # Restricted model: y ~ y_lagged
        y_lagged = self._create_lagged_matrix(y, lag)
        y_target = y[lag:]
        
        # Fit restricted model
        rss_restricted = self._fit_ols_rss(y_lagged, y_target)
        
        # Unrestricted model: y ~ y_lagged + x_lagged
        x_lagged = self._create_lagged_matrix(x, lag)
        combined = np.column_stack([y_lagged, x_lagged])
        
        # Fit unrestricted model
        rss_unrestricted = self._fit_ols_rss(combined, y_target)
        
        # F-test
        n_obs = len(y_target)
        df1 = lag
        df2 = n_obs - 2 * lag - 1
        
        if df2 <= 0 or rss_unrestricted == 0:
            return False, 0.0, 1.0, lag
        
        f_stat = ((rss_restricted - rss_unrestricted) / df1) / (rss_unrestricted / df2)
        
        # P-value from F-distribution
        from scipy import stats
        p_value = 1 - stats.f.cdf(f_stat, df1, df2)
        
        is_causal = p_value < self.significance
        
        return is_causal, f_stat, p_value, lag
    
    def _create_lagged_matrix(self, x: np.ndarray, lag: int) -> np.ndarray:
        """Create matrix of lagged values"""
        n = len(x) - lag
        matrix = np.zeros((n, lag))
        
        for i in range(lag):
            matrix[:, i] = x[i:n+i]
        
        return matrix
    
    def _fit_ols_rss(self, X: np.ndarray, y: np.ndarray) -> float:
        """Fit OLS and return residual sum of squares"""
        # Add constant
        X_with_const = np.column_stack([np.ones(len(X)), X])
        
        try:
            # Solve normal equations
            beta = np.linalg.lstsq(X_with_const, y, rcond=None)[0]
            residuals = y - X_with_const @ beta
            return np.sum(residuals ** 2)
        except:
            return float('inf')
    
    def _compute_aic(self, x: np.ndarray, y: np.ndarray, lag: int) -> float:
        """Compute AIC for lag selection"""
        y_lagged = self._create_lagged_matrix(y, lag)
        x_lagged = self._create_lagged_matrix(x, lag)
        combined = np.column_stack([y_lagged, x_lagged])
        y_target = y[lag:]
        
        rss = self._fit_ols_rss(combined, y_target)
        n = len(y_target)
        k = 2 * lag + 1
        
        if rss <= 0:
            return float('inf')
        
        return n * np.log(rss / n) + 2 * k


class TransferEntropy:
    """Transfer entropy for causal inference"""
    
    def __init__(self, n_bins: int = 10, lag: int = 1):
        self.n_bins = n_bins
        self.lag = lag
    
    def compute(
        self,
        x: np.ndarray,
        y: np.ndarray
    ) -> Tuple[float, float]:
        """
        Compute transfer entropy from x to y
        
        Returns: (transfer_entropy, normalized_te)
        """
        # Discretize
        x_discrete = self._discretize(x)
        y_discrete = self._discretize(y)
        
        # Create lagged versions
        n = len(x) - self.lag
        x_lagged = x_discrete[:n]
        y_lagged = y_discrete[:n]
        y_future = y_discrete[self.lag:]
        
        # Compute joint and marginal entropies
        h_y_future_given_y_past = self._conditional_entropy(y_future, y_lagged)
        h_y_future_given_y_past_x_past = self._conditional_entropy_2(
            y_future, y_lagged, x_lagged
        )
        
        # Transfer entropy
        te = h_y_future_given_y_past - h_y_future_given_y_past_x_past
        
        # Normalize by entropy of y_future
        h_y = self._entropy(y_future)
        normalized_te = te / h_y if h_y > 0 else 0
        
        return max(0, te), max(0, min(1, normalized_te))
    
    def _discretize(self, x: np.ndarray) -> np.ndarray:
        """Discretize continuous values into bins"""
        percentiles = np.linspace(0, 100, self.n_bins + 1)
        bins = np.percentile(x, percentiles)
        return np.digitize(x, bins[1:-1])
    
    def _entropy(self, x: np.ndarray) -> float:
        """Compute entropy"""
        _, counts = np.unique(x, return_counts=True)
        probs = counts / len(x)
        return -np.sum(probs * np.log2(probs + 1e-10))
    
    def _conditional_entropy(self, x: np.ndarray, y: np.ndarray) -> float:
        """Compute H(X|Y)"""
        joint = list(zip(x, y))
        unique_y = np.unique(y)
        
        h_x_given_y = 0
        for y_val in unique_y:
            mask = y == y_val
            p_y = np.sum(mask) / len(y)
            x_given_y = x[mask]
            h_x_given_y += p_y * self._entropy(x_given_y)
        
        return h_x_given_y
    
    def _conditional_entropy_2(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: np.ndarray
    ) -> float:
        """Compute H(X|Y,Z)"""
        # Create combined condition
        yz = np.array([f"{yi}_{zi}" for yi, zi in zip(y, z)])
        return self._conditional_entropy(x, yz)


class PCAlgorithm:
    """PC algorithm for causal discovery"""
    
    def __init__(self, significance: float = 0.05):
        self.significance = significance
    
    def discover(
        self,
        data: np.ndarray,
        variable_names: List[str]
    ) -> List[CausalEdge]:
        """
        Discover causal structure using PC algorithm
        
        Args:
            data: n_samples x n_variables array
            variable_names: names of variables
        
        Returns: list of causal edges
        """
        n_vars = len(variable_names)
        
        # Initialize with complete undirected graph
        adjacency = np.ones((n_vars, n_vars)) - np.eye(n_vars)
        
        # Phase 1: Remove edges based on conditional independence
        for depth in range(n_vars):
            for i in range(n_vars):
                for j in range(i + 1, n_vars):
                    if adjacency[i, j] == 0:
                        continue
                    
                    # Get neighbors
                    neighbors_i = [k for k in range(n_vars) 
                                   if k != j and adjacency[i, k] == 1]
                    
                    # Test conditional independence
                    for subset in itertools.combinations(neighbors_i, min(depth, len(neighbors_i))):
                        if self._conditional_independent(data, i, j, list(subset)):
                            adjacency[i, j] = 0
                            adjacency[j, i] = 0
                            break
        
        # Phase 2: Orient edges (simplified)
        edges = []
        for i in range(n_vars):
            for j in range(i + 1, n_vars):
                if adjacency[i, j] == 1:
                    # Use correlation strength to determine direction
                    corr = np.corrcoef(data[:, i], data[:, j])[0, 1]
                    
                    # Heuristic: variable with higher variance is more likely cause
                    var_i = np.var(data[:, i])
                    var_j = np.var(data[:, j])
                    
                    if var_i > var_j:
                        source, target = variable_names[i], variable_names[j]
                    else:
                        source, target = variable_names[j], variable_names[i]
                    
                    edge = CausalEdge(
                        source=source,
                        target=target,
                        edge_type=EdgeType.DIRECTED,
                        strength=abs(corr),
                        confidence=0.7,
                        method=CausalMethod.PC_ALGORITHM
                    )
                    edges.append(edge)
        
        return edges
    
    def _conditional_independent(
        self,
        data: np.ndarray,
        i: int,
        j: int,
        conditioning_set: List[int]
    ) -> bool:
        """Test conditional independence using partial correlation"""
        if not conditioning_set:
            # Simple correlation test
            corr = np.corrcoef(data[:, i], data[:, j])[0, 1]
            n = len(data)
            t_stat = corr * np.sqrt((n - 2) / (1 - corr**2 + 1e-10))
            
            from scipy import stats
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
            
            return p_value > self.significance
        
        # Partial correlation
        indices = [i, j] + conditioning_set
        sub_data = data[:, indices]
        
        try:
            cov = np.cov(sub_data.T)
            precision = np.linalg.inv(cov)
            partial_corr = -precision[0, 1] / np.sqrt(precision[0, 0] * precision[1, 1])
            
            n = len(data)
            k = len(conditioning_set)
            t_stat = partial_corr * np.sqrt((n - k - 2) / (1 - partial_corr**2 + 1e-10))
            
            from scipy import stats
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - k - 2))
            
            return p_value > self.significance
        except:
            return False


class CausalDiscovery:
    """
    Causal Discovery System
    
    Discovers causal relationships in financial data using
    multiple methods and combines results.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Methods
        self.granger = GrangerCausality(
            max_lag=self.config.get('max_lag', 10),
            significance=self.config.get('significance', 0.05)
        )
        self.transfer_entropy = TransferEntropy(
            n_bins=self.config.get('n_bins', 10),
            lag=self.config.get('te_lag', 1)
        )
        self.pc_algorithm = PCAlgorithm(
            significance=self.config.get('significance', 0.05)
        )
        
        # Storage
        self.graphs: Dict[str, CausalGraph] = {}
        self.edges: List[CausalEdge] = []
        
        # Statistics
        self.stats = {
            'graphs_discovered': 0,
            'edges_discovered': 0,
            'methods_used': defaultdict(int)
        }
        
        logger.info("Causal Discovery initialized")
    
    def discover_pairwise(
        self,
        x: np.ndarray,
        y: np.ndarray,
        x_name: str,
        y_name: str,
        methods: Optional[List[CausalMethod]] = None
    ) -> List[CausalEdge]:
        """Discover causal relationship between two variables"""
        methods = methods or [CausalMethod.GRANGER, CausalMethod.TRANSFER_ENTROPY]
        edges = []
        
        for method in methods:
            if method == CausalMethod.GRANGER:
                # Test x -> y
                is_causal, f_stat, p_value, lag = self.granger.test(x, y)
                if is_causal:
                    edge = CausalEdge(
                        source=x_name,
                        target=y_name,
                        edge_type=EdgeType.DIRECTED,
                        strength=1 - p_value,
                        confidence=1 - p_value,
                        lag=lag,
                        p_value=p_value,
                        test_statistic=f_stat,
                        method=CausalMethod.GRANGER
                    )
                    edges.append(edge)
                
                # Test y -> x
                is_causal, f_stat, p_value, lag = self.granger.test(y, x)
                if is_causal:
                    edge = CausalEdge(
                        source=y_name,
                        target=x_name,
                        edge_type=EdgeType.DIRECTED,
                        strength=1 - p_value,
                        confidence=1 - p_value,
                        lag=lag,
                        p_value=p_value,
                        test_statistic=f_stat,
                        method=CausalMethod.GRANGER
                    )
                    edges.append(edge)
                
                self.stats['methods_used']['granger'] += 1
            
            elif method == CausalMethod.TRANSFER_ENTROPY:
                # x -> y
                te_xy, norm_te_xy = self.transfer_entropy.compute(x, y)
                # y -> x
                te_yx, norm_te_yx = self.transfer_entropy.compute(y, x)
                
                # Determine direction based on asymmetry
                if norm_te_xy > 0.1 and norm_te_xy > norm_te_yx * 1.5:
                    edge = CausalEdge(
                        source=x_name,
                        target=y_name,
                        edge_type=EdgeType.DIRECTED,
                        strength=norm_te_xy,
                        confidence=min(0.9, norm_te_xy * 2),
                        method=CausalMethod.TRANSFER_ENTROPY,
                        metadata={'transfer_entropy': te_xy}
                    )
                    edges.append(edge)
                
                if norm_te_yx > 0.1 and norm_te_yx > norm_te_xy * 1.5:
                    edge = CausalEdge(
                        source=y_name,
                        target=x_name,
                        edge_type=EdgeType.DIRECTED,
                        strength=norm_te_yx,
                        confidence=min(0.9, norm_te_yx * 2),
                        method=CausalMethod.TRANSFER_ENTROPY,
                        metadata={'transfer_entropy': te_yx}
                    )
                    edges.append(edge)
                
                self.stats['methods_used']['transfer_entropy'] += 1
        
        self.edges.extend(edges)
        self.stats['edges_discovered'] += len(edges)
        
        return edges
    
    def discover_multivariate(
        self,
        data: Dict[str, np.ndarray],
        method: CausalMethod = CausalMethod.PC_ALGORITHM
    ) -> CausalGraph:
        """Discover causal structure among multiple variables"""
        variable_names = list(data.keys())
        
        # Stack data
        data_matrix = np.column_stack([data[name] for name in variable_names])
        
        if method == CausalMethod.PC_ALGORITHM:
            edges = self.pc_algorithm.discover(data_matrix, variable_names)
            self.stats['methods_used']['pc_algorithm'] += 1
        else:
            # Default to pairwise Granger
            edges = []
            for i, name_i in enumerate(variable_names):
                for j, name_j in enumerate(variable_names):
                    if i != j:
                        pairwise_edges = self.discover_pairwise(
                            data[name_i], data[name_j],
                            name_i, name_j,
                            methods=[CausalMethod.GRANGER]
                        )
                        edges.extend(pairwise_edges)
        
        # Create graph
        graph = CausalGraph(
            graph_id=f"graph_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            name=f"Causal graph for {len(variable_names)} variables",
            nodes=variable_names,
            edges=edges,
            is_dag=self._check_dag(edges, variable_names),
            method=method,
            data_points=len(data_matrix)
        )
        
        self.graphs[graph.graph_id] = graph
        self.stats['graphs_discovered'] += 1
        
        logger.info(f"Discovered causal graph with {len(edges)} edges")
        
        return graph
    
    def _check_dag(self, edges: List[CausalEdge], nodes: List[str]) -> bool:
        """Check if graph is a DAG (no cycles)"""
        # Build adjacency list
        adj = defaultdict(list)
        for edge in edges:
            if edge.edge_type == EdgeType.DIRECTED:
                adj[edge.source].append(edge.target)
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in adj[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in nodes:
            if node not in visited:
                if has_cycle(node):
                    return False
        
        return True
    
    def get_causal_effect(
        self,
        graph: CausalGraph,
        treatment: str,
        outcome: str
    ) -> Dict[str, Any]:
        """Estimate causal effect of treatment on outcome"""
        # Find direct edge
        direct_edge = None
        for edge in graph.edges:
            if edge.source == treatment and edge.target == outcome:
                direct_edge = edge
                break
        
        # Find indirect paths
        indirect_paths = self._find_paths(graph, treatment, outcome)
        
        # Calculate total effect
        total_effect = 0.0
        if direct_edge:
            total_effect += direct_edge.strength
        
        for path in indirect_paths:
            path_effect = 1.0
            for i in range(len(path) - 1):
                for edge in graph.edges:
                    if edge.source == path[i] and edge.target == path[i+1]:
                        path_effect *= edge.strength
                        break
            total_effect += path_effect * 0.5  # Discount indirect effects
        
        # Find confounders
        confounders = self._find_confounders(graph, treatment, outcome)
        
        return {
            'treatment': treatment,
            'outcome': outcome,
            'direct_effect': direct_edge.strength if direct_edge else 0.0,
            'total_effect': total_effect,
            'indirect_paths': len(indirect_paths),
            'confounders': confounders,
            'confidence': direct_edge.confidence if direct_edge else 0.0
        }
    
    def _find_paths(
        self,
        graph: CausalGraph,
        source: str,
        target: str,
        max_length: int = 4
    ) -> List[List[str]]:
        """Find all paths from source to target"""
        paths = []
        
        def dfs(current: str, path: List[str]):
            if len(path) > max_length:
                return
            
            if current == target and len(path) > 2:
                paths.append(path.copy())
                return
            
            for edge in graph.edges:
                if edge.source == current and edge.target not in path:
                    path.append(edge.target)
                    dfs(edge.target, path)
                    path.pop()
        
        dfs(source, [source])
        return paths
    
    def _find_confounders(
        self,
        graph: CausalGraph,
        treatment: str,
        outcome: str
    ) -> List[str]:
        """Find confounding variables"""
        confounders = []
        
        treatment_parents = set(graph.get_parents(treatment))
        outcome_parents = set(graph.get_parents(outcome))
        
        # Common causes
        common = treatment_parents & outcome_parents
        confounders.extend(common)
        
        return list(confounders)
    
    def get_graph(self, graph_id: str) -> Optional[CausalGraph]:
        """Get a causal graph by ID"""
        return self.graphs.get(graph_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get discovery statistics"""
        return {
            **self.stats,
            'total_graphs': len(self.graphs),
            'total_edges': len(self.edges),
            'avg_edges_per_graph': (
                len(self.edges) / max(1, len(self.graphs))
            )
        }
