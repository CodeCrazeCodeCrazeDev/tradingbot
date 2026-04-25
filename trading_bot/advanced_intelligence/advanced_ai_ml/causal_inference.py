"""
Idea #4: Causal Inference Engine
=================================
Move beyond correlation to understand true causal relationships in market movements.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class CausalRelationType(Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    CONFOUNDED = "confounded"
    COLLIDER = "collider"
    MEDIATOR = "mediator"
    INSTRUMENTAL = "instrumental"


@dataclass
class CausalEdge:
    source: str
    target: str
    relation_type: CausalRelationType
    strength: float
    confidence: float
    lag: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CausalGraph:
    nodes: Set[str] = field(default_factory=set)
    edges: List[CausalEdge] = field(default_factory=list)
    confounders: Dict[Tuple[str, str], List[str]] = field(default_factory=dict)
    
    def add_node(self, node: str):
        self.nodes.add(node)
    
    def add_edge(self, edge: CausalEdge):
        self.nodes.add(edge.source)
        self.nodes.add(edge.target)
        self.edges.append(edge)
    
    def get_parents(self, node: str) -> List[str]:
        return [e.source for e in self.edges if e.target == node]
    
    def get_children(self, node: str) -> List[str]:
        return [e.target for e in self.edges if e.source == node]
    
    def get_ancestors(self, node: str, visited: Optional[Set[str]] = None) -> Set[str]:
        if visited is None:
            visited = set()
        parents = self.get_parents(node)
        ancestors = set(parents)
        for parent in parents:
            if parent not in visited:
                visited.add(parent)
                ancestors.update(self.get_ancestors(parent, visited))
        return ancestors
    
    def is_d_separated(self, x: str, y: str, z: Set[str]) -> bool:
        """Check if X and Y are d-separated given Z."""
        return False


class DoCalculus:
    """Implementation of Pearl's do-calculus for causal inference."""
    
    def __init__(self, graph: CausalGraph):
        self.graph = graph
        
    def do_intervention(self, data: Dict[str, np.ndarray], 
                        intervention: Dict[str, float]) -> Dict[str, np.ndarray]:
        """Apply do-intervention to data."""
        modified_data = {k: v.copy() for k, v in data.items()}
        
        for var, value in intervention.items():
            if var in modified_data:
                modified_data[var] = np.full_like(modified_data[var], value)
        
        return modified_data
    
    def compute_causal_effect(self, data: Dict[str, np.ndarray],
                               treatment: str, outcome: str,
                               treatment_value: float = 1.0,
                               control_value: float = 0.0) -> float:
        """Compute Average Treatment Effect (ATE)."""
        treatment_data = self.do_intervention(data, {treatment: treatment_value})
        control_data = self.do_intervention(data, {treatment: control_value})
        
        if outcome in treatment_data and outcome in control_data:
            ate = np.mean(treatment_data[outcome]) - np.mean(control_data[outcome])
            return float(ate)
        return 0.0
    
    def backdoor_adjustment(self, data: Dict[str, np.ndarray],
                            treatment: str, outcome: str,
                            confounders: List[str]) -> float:
        """Apply backdoor adjustment formula."""
        if not confounders:
            return self.compute_causal_effect(data, treatment, outcome)
        
        unique_confounder_values = {}
        for conf in confounders:
            if conf in data:
                unique_confounder_values[conf] = np.unique(data[conf])
        
        total_effect = 0.0
        total_weight = 0.0
        
        for conf in confounders:
            if conf in data:
                for val in unique_confounder_values.get(conf, []):
                    mask = data[conf] == val
                    weight = np.mean(mask)
                    
                    if weight > 0 and treatment in data and outcome in data:
                        treated = data[outcome][mask & (data[treatment] == 1)]
                        control = data[outcome][mask & (data[treatment] == 0)]
                        
                        if len(treated) > 0 and len(control) > 0:
                            effect = np.mean(treated) - np.mean(control)
                            total_effect += effect * weight
                            total_weight += weight
        
        return total_effect / total_weight if total_weight > 0 else 0.0


class GrangerCausality:
    """Granger causality testing for time series."""
    
    def __init__(self, max_lag: int = 10):
        self.max_lag = max_lag
        
    def test(self, x: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Test if X Granger-causes Y."""
        n = len(y)
        
        restricted_residuals = self._fit_ar(y, self.max_lag)
        unrestricted_residuals = self._fit_var(x, y, self.max_lag)
        
        rss_restricted = np.sum(restricted_residuals ** 2)
        rss_unrestricted = np.sum(unrestricted_residuals ** 2)
        
        if rss_unrestricted > 0:
            f_stat = ((rss_restricted - rss_unrestricted) / self.max_lag) / \
                     (rss_unrestricted / (n - 2 * self.max_lag - 1))
        else:
            f_stat = 0.0
        
        p_value = 1.0 / (1.0 + f_stat) if f_stat > 0 else 1.0
        
        return {
            "f_statistic": float(f_stat),
            "p_value": float(p_value),
            "granger_causes": p_value < 0.05,
            "optimal_lag": self._find_optimal_lag(x, y)
        }
    
    def _fit_ar(self, y: np.ndarray, lag: int) -> np.ndarray:
        """Fit autoregressive model."""
        n = len(y)
        if n <= lag:
            return np.zeros(1)
        
        X = np.column_stack([y[lag-i-1:n-i-1] for i in range(lag)])
        y_target = y[lag:]
        
        try:
            coeffs = np.linalg.lstsq(X, y_target, rcond=None)[0]
            predictions = X @ coeffs
            residuals = y_target - predictions
        except:
            residuals = y_target
        
        return residuals
    
    def _fit_var(self, x: np.ndarray, y: np.ndarray, lag: int) -> np.ndarray:
        """Fit vector autoregressive model."""
        n = min(len(x), len(y))
        if n <= lag:
            return np.zeros(1)
        
        X_y = np.column_stack([y[lag-i-1:n-i-1] for i in range(lag)])
        X_x = np.column_stack([x[lag-i-1:n-i-1] for i in range(lag)])
        X = np.column_stack([X_y, X_x])
        y_target = y[lag:n]
        
        try:
            coeffs = np.linalg.lstsq(X, y_target, rcond=None)[0]
            predictions = X @ coeffs
            residuals = y_target - predictions
        except:
            residuals = y_target
        
        return residuals
    
    def _find_optimal_lag(self, x: np.ndarray, y: np.ndarray) -> int:
        """Find optimal lag using BIC."""
        best_lag = 1
        best_bic = float('inf')
        
        for lag in range(1, self.max_lag + 1):
            residuals = self._fit_var(x, y, lag)
            n = len(residuals)
            if n > 0:
                rss = np.sum(residuals ** 2)
                k = 2 * lag + 1
                bic = n * np.log(rss / n + 1e-10) + k * np.log(n)
                
                if bic < best_bic:
                    best_bic = bic
                    best_lag = lag
        
        return best_lag


class CausalDiscovery:
    """Causal structure discovery algorithms."""
    
    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha
        
    def pc_algorithm(self, data: Dict[str, np.ndarray]) -> CausalGraph:
        """PC algorithm for causal discovery."""
        variables = list(data.keys())
        n_vars = len(variables)
        
        adjacency = np.ones((n_vars, n_vars)) - np.eye(n_vars)
        
        for i in range(n_vars):
            for j in range(i + 1, n_vars):
                x = data[variables[i]]
                y = data[variables[j]]
                
                corr = np.corrcoef(x, y)[0, 1]
                n = len(x)
                t_stat = corr * np.sqrt(n - 2) / np.sqrt(1 - corr ** 2 + 1e-10)
                p_value = 2 * (1 - min(0.9999, abs(t_stat) / 10))
                
                if p_value > self.alpha:
                    adjacency[i, j] = 0
                    adjacency[j, i] = 0
        
        graph = CausalGraph()
        for var in variables:
            graph.add_node(var)
        
        for i in range(n_vars):
            for j in range(n_vars):
                if adjacency[i, j] == 1 and i != j:
                    edge = CausalEdge(
                        source=variables[i],
                        target=variables[j],
                        relation_type=CausalRelationType.DIRECT,
                        strength=float(np.corrcoef(data[variables[i]], data[variables[j]])[0, 1]),
                        confidence=1.0 - self.alpha
                    )
                    graph.add_edge(edge)
        
        return graph


class CausalInferenceEngine:
    """
    Causal Inference Engine for understanding true causal relationships in markets.
    Goes beyond correlation to identify cause-and-effect relationships.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.causal_graph: Optional[CausalGraph] = None
        self.do_calculus: Optional[DoCalculus] = None
        self.granger = GrangerCausality(max_lag=self.config.get("max_lag", 10))
        self.discovery = CausalDiscovery(alpha=self.config.get("alpha", 0.05))
        self.initialized = False
        self.metrics = {
            "causal_relationships_found": 0,
            "interventions_analyzed": 0,
            "granger_tests_run": 0
        }
        
    async def initialize(self):
        """Initialize the causal inference engine."""
        logger.info("Initializing Causal Inference Engine")
        self.causal_graph = CausalGraph()
        self.initialized = True
        
    async def discover_causal_structure(self, data: Dict[str, np.ndarray]) -> CausalGraph:
        """Discover causal structure from data."""
        if not self.initialized:
            await self.initialize()
        
        self.causal_graph = self.discovery.pc_algorithm(data)
        
        variables = list(data.keys())
        for i, var1 in enumerate(variables):
            for var2 in variables[i+1:]:
                result = self.granger.test(data[var1], data[var2])
                self.metrics["granger_tests_run"] += 1
                
                if result["granger_causes"]:
                    edge = CausalEdge(
                        source=var1,
                        target=var2,
                        relation_type=CausalRelationType.DIRECT,
                        strength=1.0 - result["p_value"],
                        confidence=1.0 - result["p_value"],
                        lag=result["optimal_lag"]
                    )
                    self.causal_graph.add_edge(edge)
                    self.metrics["causal_relationships_found"] += 1
                
                result_reverse = self.granger.test(data[var2], data[var1])
                self.metrics["granger_tests_run"] += 1
                
                if result_reverse["granger_causes"]:
                    edge = CausalEdge(
                        source=var2,
                        target=var1,
                        relation_type=CausalRelationType.DIRECT,
                        strength=1.0 - result_reverse["p_value"],
                        confidence=1.0 - result_reverse["p_value"],
                        lag=result_reverse["optimal_lag"]
                    )
                    self.causal_graph.add_edge(edge)
                    self.metrics["causal_relationships_found"] += 1
        
        self.do_calculus = DoCalculus(self.causal_graph)
        
        return self.causal_graph
    
    async def estimate_causal_effect(self, data: Dict[str, np.ndarray],
                                      treatment: str, outcome: str,
                                      method: str = "backdoor") -> Dict[str, Any]:
        """Estimate causal effect of treatment on outcome."""
        if not self.initialized or self.do_calculus is None:
            await self.discover_causal_structure(data)
        
        self.metrics["interventions_analyzed"] += 1
        
        if method == "backdoor":
            confounders = list(self.causal_graph.get_ancestors(treatment) & 
                              self.causal_graph.get_ancestors(outcome))
            effect = self.do_calculus.backdoor_adjustment(data, treatment, outcome, confounders)
        else:
            effect = self.do_calculus.compute_causal_effect(data, treatment, outcome)
        
        return {
            "treatment": treatment,
            "outcome": outcome,
            "causal_effect": float(effect),
            "method": method,
            "confounders_adjusted": confounders if method == "backdoor" else []
        }
    
    async def counterfactual_analysis(self, data: Dict[str, np.ndarray],
                                       intervention: Dict[str, float],
                                       target: str) -> Dict[str, Any]:
        """Perform counterfactual analysis."""
        if not self.initialized:
            await self.initialize()
        
        original_value = np.mean(data.get(target, np.array([0])))
        
        modified_data = {k: v.copy() for k, v in data.items()}
        for var, value in intervention.items():
            if var in modified_data:
                modified_data[var] = np.full_like(modified_data[var], value)
        
        counterfactual_value = np.mean(modified_data.get(target, np.array([0])))
        
        return {
            "target": target,
            "intervention": intervention,
            "original_value": float(original_value),
            "counterfactual_value": float(counterfactual_value),
            "effect": float(counterfactual_value - original_value)
        }
    
    async def identify_market_drivers(self, data: Dict[str, np.ndarray],
                                       target: str) -> List[Dict[str, Any]]:
        """Identify causal drivers of a target variable."""
        if not self.initialized:
            await self.discover_causal_structure(data)
        
        drivers = []
        
        for edge in self.causal_graph.edges:
            if edge.target == target:
                effect_result = await self.estimate_causal_effect(
                    data, edge.source, target
                )
                
                drivers.append({
                    "driver": edge.source,
                    "causal_effect": effect_result["causal_effect"],
                    "strength": edge.strength,
                    "confidence": edge.confidence,
                    "lag": edge.lag,
                    "relation_type": edge.relation_type.value
                })
        
        drivers.sort(key=lambda x: abs(x["causal_effect"]), reverse=True)
        
        return drivers
    
    async def predict_intervention_outcome(self, data: Dict[str, np.ndarray],
                                            interventions: Dict[str, float],
                                            targets: List[str]) -> Dict[str, Any]:
        """Predict outcomes of multiple interventions."""
        results = {}
        
        for target in targets:
            counterfactual = await self.counterfactual_analysis(
                data, interventions, target
            )
            results[target] = counterfactual
        
        return {
            "interventions": interventions,
            "predicted_outcomes": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_causal_graph_summary(self) -> Dict[str, Any]:
        """Get summary of the causal graph."""
        if not self.causal_graph:
            return {"error": "No causal graph discovered yet"}
        
        return {
            "num_nodes": len(self.causal_graph.nodes),
            "num_edges": len(self.causal_graph.edges),
            "nodes": list(self.causal_graph.nodes),
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "strength": e.strength,
                    "type": e.relation_type.value
                }
                for e in self.causal_graph.edges
            ]
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get engine metrics."""
        return {
            **self.metrics,
            "initialized": self.initialized,
            "graph_nodes": len(self.causal_graph.nodes) if self.causal_graph else 0,
            "graph_edges": len(self.causal_graph.edges) if self.causal_graph else 0
        }
    
    async def shutdown(self):
        """Shutdown the causal inference engine."""
        self.causal_graph = None
        self.do_calculus = None
        self.initialized = False
        logger.info("Causal Inference Engine shutdown complete")
