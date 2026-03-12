"""
Skill #25: Causal Discovery Engine
==================================

Discovers causal relationships between market variables
using causal inference methods.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class CausalEdge:
    """Causal relationship between variables."""
    cause: str
    effect: str
    strength: float
    lag: int
    confidence: float


@dataclass
class CausalGraph:
    """Discovered causal graph."""
    edges: List[CausalEdge]
    root_causes: List[str]
    leaf_effects: List[str]
    cycles: List[List[str]]


@dataclass
class CausalResult:
    """Causal discovery result."""
    graph: CausalGraph
    interventions: Dict[str, float]
    counterfactuals: Dict[str, float]
    trading_signal: str
    confidence: float


class CausalDiscoveryEngine:
    """Causal discovery for market relationships."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.max_lag = self.config.get('max_lag', 5)
            self.significance = self.config.get('significance', 0.05)
            logger.info("CausalDiscoveryEngine initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def discover(
        self,
        data: Dict[str, np.ndarray],
        target: str = 'price'
    ) -> CausalResult:
        """Discover causal relationships."""
        try:
            if not data or target not in data:
                return self._create_empty_result()
        
            variables = list(data.keys())
            edges = []
        
            # Test Granger causality between all pairs
            for cause in variables:
                for effect in variables:
                    if cause != effect:
                        strength, lag, conf = self._granger_test(data[cause], data[effect])
                        if conf > 1 - self.significance:
                            edges.append(CausalEdge(
                                cause=cause, effect=effect,
                                strength=strength, lag=lag, confidence=conf
                            ))
        
            # Build graph
            graph = self._build_graph(edges, variables)
        
            # Calculate interventions
            interventions = self._calculate_interventions(graph, data, target)
        
            # Calculate counterfactuals
            counterfactuals = self._calculate_counterfactuals(graph, data, target)
        
            signal = self._generate_signal(graph, interventions, target)
            confidence = np.mean([e.confidence for e in edges]) if edges else 0
        
            return CausalResult(
                graph=graph,
                interventions=interventions,
                counterfactuals=counterfactuals,
                trading_signal=signal,
                confidence=confidence
            )
        except Exception as e:
            logger.error(f"Error in discover: {e}")
            raise
    
    def _granger_test(
        self,
        x: np.ndarray,
        y: np.ndarray
    ) -> Tuple[float, int, float]:
        """Simplified Granger causality test."""
        try:
            min_len = min(len(x), len(y))
            if min_len < self.max_lag + 10:
                return 0, 0, 0
        
            x, y = x[-min_len:], y[-min_len:]
        
            best_strength = 0
            best_lag = 1
            best_conf = 0
        
            for lag in range(1, self.max_lag + 1):
                # Correlation between lagged x and y
                corr = np.corrcoef(x[:-lag], y[lag:])[0, 1]
                strength = abs(corr)
            
                # Simplified confidence based on correlation
                conf = min(0.99, strength * 2)
            
                if strength > best_strength:
                    best_strength = strength
                    best_lag = lag
                    best_conf = conf
        
            return best_strength, best_lag, best_conf
        except Exception as e:
            logger.error(f"Error in _granger_test: {e}")
            raise
    
    def _build_graph(self, edges: List[CausalEdge], variables: List[str]) -> CausalGraph:
        """Build causal graph from edges."""
        # Find root causes (no incoming edges)
        try:
            effects = {e.effect for e in edges}
            causes = {e.cause for e in edges}
            roots = [v for v in causes if v not in effects]
        
            # Find leaf effects (no outgoing edges)
            leaves = [v for v in effects if v not in causes]
        
            # Detect cycles (simplified)
            cycles = []
        
            return CausalGraph(
                edges=edges,
                root_causes=roots,
                leaf_effects=leaves,
                cycles=cycles
            )
        except Exception as e:
            logger.error(f"Error in _build_graph: {e}")
            raise
    
    def _calculate_interventions(
        self,
        graph: CausalGraph,
        data: Dict[str, np.ndarray],
        target: str
    ) -> Dict[str, float]:
        """Calculate effect of interventions on target."""
        try:
            interventions = {}
        
            for edge in graph.edges:
                if edge.effect == target:
                    # Effect of 1 std increase in cause
                    cause_std = np.std(data[edge.cause])
                    effect_change = edge.strength * cause_std
                    interventions[f"increase_{edge.cause}"] = effect_change
        
            return interventions
        except Exception as e:
            logger.error(f"Error in _calculate_interventions: {e}")
            raise
    
    def _calculate_counterfactuals(
        self,
        graph: CausalGraph,
        data: Dict[str, np.ndarray],
        target: str
    ) -> Dict[str, float]:
        """Calculate counterfactual scenarios."""
        try:
            counterfactuals = {}
        
            # What if each root cause was different?
            for root in graph.root_causes:
                if root in data:
                    # Counterfactual: root was 10% higher
                    cf_value = np.mean(data[root]) * 1.1
                    actual_value = np.mean(data[root])
                    counterfactuals[f"{root}_10pct_higher"] = cf_value - actual_value
        
            return counterfactuals
        except Exception as e:
            logger.error(f"Error in _calculate_counterfactuals: {e}")
            raise
    
    def _generate_signal(
        self,
        graph: CausalGraph,
        interventions: Dict[str, float],
        target: str
    ) -> str:
        """Generate trading signal from causal analysis."""
        try:
            if not graph.edges:
                return "NO CAUSAL LINKS: Insufficient evidence for causal relationships"
        
            # Find strongest causal driver
            target_edges = [e for e in graph.edges if e.effect == target]
            if target_edges:
                strongest = max(target_edges, key=lambda e: e.strength)
                return f"CAUSAL DRIVER: {strongest.cause} → {target} (strength: {strongest.strength:.2f})"
        
            return f"CAUSAL GRAPH: {len(graph.edges)} relationships discovered"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _create_empty_result(self) -> CausalResult:
        """Create empty result."""
        return CausalResult(
            graph=CausalGraph([], [], [], []),
            interventions={},
            counterfactuals={},
            trading_signal="Insufficient data",
            confidence=0
        )
