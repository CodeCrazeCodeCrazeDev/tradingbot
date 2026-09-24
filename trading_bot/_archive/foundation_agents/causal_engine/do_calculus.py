"""
Do-Calculus - Causal Intervention Analysis
=============================================

Implements Pearl's do-calculus for causal inference:
1. Intervention effects (do-operator)
2. Back-door criterion
3. Front-door criterion
4. Causal effect identification

Based on Judea Pearl's causal inference framework.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class Intervention:
    """Represents a causal intervention"""
    target_variable: str
    intervention_value: Any
    
    # Context
    conditioning_set: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        if self.conditioning_set:
            return f"do({self.target_variable}={self.intervention_value} | {self.conditioning_set})"
        return f"do({self.target_variable}={self.intervention_value})"


@dataclass
class CausalEffect:
    """Represents a causal effect estimate"""
    cause: str
    effect: str
    
    # Estimates
    average_treatment_effect: float = 0.0
    conditional_treatment_effect: Dict[str, float] = field(default_factory=dict)
    
    # Uncertainty
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    standard_error: float = 0.0
    
    # Identification
    identifiable: bool = False
    identification_strategy: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'cause': self.cause,
            'effect': self.effect,
            'ate': self.average_treatment_effect,
            'ci': self.confidence_interval,
            'identifiable': self.identifiable,
            'strategy': self.identification_strategy
        }


@dataclass
class CausalGraph:
    """Causal graph for do-calculus operations"""
    nodes: Set[str] = field(default_factory=set)
    edges: List[Tuple[str, str]] = field(default_factory=list)  # (from, to)
    
    # Edge types
    edge_types: Dict[Tuple[str, str], str] = field(default_factory=dict)
    
    def add_edge(self, from_node: str, to_node: str, edge_type: str = "direct"):
        """Add edge to graph"""
        self.nodes.add(from_node)
        self.nodes.add(to_node)
        self.edges.append((from_node, to_node))
        self.edge_types[(from_node, to_node)] = edge_type
    
    def get_parents(self, node: str) -> Set[str]:
        """Get parent nodes"""
        return {e[0] for e in self.edges if e[1] == node}
    
    def get_children(self, node: str) -> Set[str]:
        """Get child nodes"""
        return {e[1] for e in self.edges if e[0] == node}
    
    def get_ancestors(self, node: str) -> Set[str]:
        """Get all ancestors"""
        ancestors = set()
        to_visit = [node]
        
        while to_visit:
            current = to_visit.pop()
            parents = self.get_parents(current)
            ancestors.update(parents)
            to_visit.extend(parents)
        
        return ancestors
    
    def get_descendants(self, node: str) -> Set[str]:
        """Get all descendants"""
        descendants = set()
        to_visit = [node]
        
        while to_visit:
            current = to_visit.pop()
            children = self.get_children(current)
            descendants.update(children)
            to_visit.extend(children)
        
        return descendants
    
    def get_backdoor_paths(self, x: str, y: str) -> List[List[str]]:
        """Find all backdoor paths from X to Y (paths with arrow into X)"""
        paths = []
        
        # Find paths that start with an edge into X
        parents_of_x = self.get_parents(x)
        
        for parent in parents_of_x:
            # Find all paths from parent to Y
            paths.extend(self._find_all_paths(parent, y, visited={x}))
        
        return paths
    
    def _find_all_paths(
        self,
        start: str,
        end: str,
        visited: Optional[Set[str]] = None
    ) -> List[List[str]]:
        """Find all paths between nodes"""
        if visited is None:
            visited = set()
        
        if start == end:
            return [[start]]
        
        if start in visited:
            return []
        
        visited.add(start)
        paths = []
        
        # Get neighbors (both parents and children for undirected search)
        neighbors = self.get_children(start).union(self.get_parents(start))
        
        for neighbor in neighbors:
            if neighbor not in visited:
                subpaths = self._find_all_paths(neighbor, end, visited.copy())
                for path in subpaths:
                    paths.append([start] + path)
        
        return paths
    
    def get_adjacency_matrix(self) -> np.ndarray:
        """Get adjacency matrix representation"""
        node_list = sorted(self.nodes)
        n = len(node_list)
        adj = np.zeros((n, n))
        
        node_idx = {node: i for i, node in enumerate(node_list)}
        
        for edge in self.edges:
            i, j = node_idx[edge[0]], node_idx[edge[1]]
            adj[i, j] = 1
        
        return adj


class DoCalculus:
    """
    Do-Calculus Engine
    
    Implements Pearl's do-calculus for causal effect estimation.
    Allows computing P(Y | do(X)) from observational data.
    """
    
    def __init__(self):
        self.graph: Optional[CausalGraph] = None
        self.data: Optional[Dict[str, np.ndarray]] = None
        
        # Statistics
        self.stats = {
            'effects_computed': 0,
            'identifiable_effects': 0,
            'backdoor_applied': 0,
            'frontdoor_applied': 0
        }
        
        logger.info("Do-Calculus Engine initialized")
    
    def set_graph(self, graph: CausalGraph):
        """Set the causal graph"""
        self.graph = graph
    
    def set_data(self, data: Dict[str, np.ndarray]):
        """Set observational data"""
        self.data = data
    
    def is_identifiable(self, x: str, y: str) -> Tuple[bool, str]:
        """Check if causal effect P(y | do(x)) is identifiable"""
        if not self.graph:
            return False, "No causal graph provided"
        
        if x not in self.graph.nodes or y not in self.graph.nodes:
            return False, "Variables not in graph"
        
        # Check backdoor criterion
        backdoor_adjustment = self._find_backdoor_adjustment(x, y)
        if backdoor_adjustment is not None:
            return True, f"backdoor: adjust for {backdoor_adjustment}"
        
        # Check frontdoor criterion
        frontdoor_path = self._find_frontdoor_path(x, y)
        if frontdoor_path:
            return True, f"frontdoor: through {frontdoor_path}"
        
        # Check if there are no confounding paths
        ancestors_x = self.graph.get_ancestors(x)
        ancestors_y = self.graph.get_ancestors(y)
        
        if not ancestors_x.intersection(ancestors_y):
            return True, "no confounding: X and Y have no common ancestors"
        
        return False, "Effect not identifiable with current graph"
    
    def _find_backdoor_adjustment(self, x: str, y: str) -> Optional[List[str]]:
        """Find adjustment set for backdoor criterion"""
        # A set Z satisfies backdoor criterion if:
        # 1. Z blocks all backdoor paths from X to Y
        # 2. Z contains no descendants of X
        
        # Get all backdoor paths
        backdoor_paths = self.graph.get_backdoor_paths(x, y)
        
        if not backdoor_paths:
            return []  # No backdoor paths, empty set suffices
        
        # Find nodes that appear in backdoor paths (excluding X and Y)
        path_nodes = set()
        for path in backdoor_paths:
            path_nodes.update(path)
        path_nodes.discard(x)
        path_nodes.discard(y)
        
        # Remove descendants of X
        descendants_x = self.graph.get_descendants(x)
        candidates = path_nodes - descendants_x
        
        # Find minimal set that blocks all paths
        # This is a simplified version; full algorithm is NP-hard
        minimal_set = []
        blocked_paths = set()
        
        for node in candidates:
            # Check if this node blocks remaining paths
            newly_blocked = set()
            for i, path in enumerate(backdoor_paths):
                if i not in blocked_paths and node in path:
                    newly_blocked.add(i)
            
            if newly_blocked:
                minimal_set.append(node)
                blocked_paths.update(newly_blocked)
        
        if len(blocked_paths) == len(backdoor_paths):
            return minimal_set
        
        return None
    
    def _find_frontdoor_path(self, x: str, y: str) -> Optional[List[str]]:
        """Find frontdoor path if it exists"""
        # Frontdoor criterion requires:
        # 1. Z intercepts all directed paths from X to Y
        # 2. There is no backdoor path from X to Z
        # 3. All backdoor paths from Z to Y are blocked by X
        
        # This is a simplified check
        children_x = self.graph.get_children(x)
        
        for z in children_x:
            # Check if Z is on path to Y
            if y in self.graph.get_descendants(z):
                # Simplified check - full criterion is more complex
                return [z]
        
        return None
    
    def compute_causal_effect(
        self,
        x: str,
        y: str,
        intervention_value: Optional[float] = None
    ) -> CausalEffect:
        """Compute causal effect P(Y | do(X))"""
        identifiable, strategy = self.is_identifiable(x, y)
        
        effect = CausalEffect(
            cause=x,
            effect=y,
            identifiable=identifiable,
            identification_strategy=strategy
        )
        
        if not identifiable or not self.data:
            return effect
        
        # Apply appropriate identification strategy
        if "backdoor" in strategy:
            effect = self._apply_backdoor_adjustment(x, y, strategy, effect)
            self.stats['backdoor_applied'] += 1
        elif "frontdoor" in strategy:
            effect = self._apply_frontdoor_criterion(x, y, effect)
            self.stats['frontdoor_applied'] += 1
        elif "no confounding" in strategy:
            effect = self._compute_unconfounded_effect(x, y, effect)
        
        self.stats['effects_computed'] += 1
        if identifiable:
            self.stats['identifiable_effects'] += 1
        
        return effect
    
    def _apply_backdoor_adjustment(
        self,
        x: str,
        y: str,
        strategy: str,
        effect: CausalEffect
    ) -> CausalEffect:
        """Apply backdoor adjustment formula"""
        # P(y | do(x)) = sum_z P(y | x, z) P(z)
        
        try:
            x_data = self.data[x]
            y_data = self.data[y]
            
            # Parse adjustment set from strategy string
            # Format: "backdoor: adjust for [var1, var2]"
            if "adjust for" in strategy:
                import re
                match = re.search(r'\[(.*?)\]', strategy)
                if match:
                    z_vars = [v.strip() for v in match.group(1).split(',')]
                else:
                    z_vars = []
            else:
                z_vars = []
            
            if not z_vars:
                # No adjustment needed
                effect.average_treatment_effect = np.mean(y_data[x_data > np.median(x_data)]) - \
                                                 np.mean(y_data[x_data <= np.median(x_data)])
            else:
                # Stratify by Z and compute weighted average
                # Simplified: compute effect within strata and average
                z_data = np.column_stack([self.data[z] for z in z_vars])
                
                # Discretize Z for stratification
                z_bins = np.array([np.digitize(z_data[:, i], bins=3) for i in range(len(z_vars))]).T
                
                effects_in_strata = []
                strata_weights = []
                
                unique_strata = np.unique(z_bins, axis=0)
                
                for stratum in unique_strata:
                    mask = np.all(z_bins == stratum, axis=1)
                    if np.sum(mask) > 10:  # Minimum sample size
                        x_stratum = x_data[mask]
                        y_stratum = y_data[mask]
                        
                        treated = y_stratum[x_stratum > np.median(x_stratum)]
                        control = y_stratum[x_stratum <= np.median(x_stratum)]
                        
                        if len(treated) > 0 and len(control) > 0:
                            strata_effect = np.mean(treated) - np.mean(control)
                            effects_in_strata.append(strata_effect)
                            strata_weights.append(np.sum(mask))
                
                if effects_in_strata:
                    # Weighted average
                    weights = np.array(strata_weights) / np.sum(strata_weights)
                    effect.average_treatment_effect = np.average(effects_in_strata, weights=weights)
            
            # Compute confidence interval (simplified)
            se = np.std(y_data) / np.sqrt(len(y_data))
            effect.standard_error = se
            effect.confidence_interval = (
                effect.average_treatment_effect - 1.96 * se,
                effect.average_treatment_effect + 1.96 * se
            )
            
        except Exception as e:
            logger.error(f"Backdoor adjustment error: {e}")
        
        return effect
    
    def _apply_frontdoor_criterion(
        self,
        x: str,
        y: str,
        effect: CausalEffect
    ) -> CausalEffect:
        """Apply frontdoor criterion formula"""
        # P(y | do(x)) = sum_z P(z | x) sum_x' P(y | x', z) P(x')
        # This requires knowing the mediator Z
        
        # Simplified implementation
        try:
            # Find mediator (first variable on path from X to Y)
            children_x = self.graph.get_children(x)
            mediators = [z for z in children_x if y in self.graph.get_descendants(z)]
            
            if mediators:
                z = mediators[0]
                z_data = self.data[z]
                x_data = self.data[x]
                y_data = self.data[y]
                
                # Simplified: compute mediated effect
                # Full formula involves two-stage summation
                effect.average_treatment_effect = np.corrcoef(x_data, z_data)[0, 1] * \
                                                 np.corrcoef(z_data, y_data)[0, 1]
        
        except Exception as e:
            logger.error(f"Frontdoor criterion error: {e}")
        
        return effect
    
    def _compute_unconfounded_effect(
        self,
        x: str,
        y: str,
        effect: CausalEffect
    ) -> CausalEffect:
        """Compute effect when there's no confounding"""
        try:
            x_data = self.data[x]
            y_data = self.data[y]
            
            # Simple difference in means
            high_x = y_data[x_data > np.median(x_data)]
            low_x = y_data[x_data <= np.median(x_data)]
            
            effect.average_treatment_effect = np.mean(high_x) - np.mean(low_x)
            
            # Confidence interval
            pooled_se = np.sqrt(
                np.var(high_x) / len(high_x) + np.var(low_x) / len(low_x)
            )
            effect.standard_error = pooled_se
            effect.confidence_interval = (
                effect.average_treatment_effect - 1.96 * pooled_se,
                effect.average_treatment_effect + 1.96 * pooled_se
            )
        
        except Exception as e:
            logger.error(f"Unconfounded effect computation error: {e}")
        
        return effect
    
    def counterfactual(
        self,
        x: str,
        y: str,
        observed_values: Dict[str, float],
        counterfactual_x: float
    ) -> float:
        """Compute counterfactual: What would Y be if X had been x?"""
        # Simplified counterfactual using adjustment
        # Y_x(u) = Y_{M_x}(u) where M_x is the modified model
        
        try:
            # Get current Y value
            current_y = observed_values.get(y, 0)
            current_x = observed_values.get(x, 0)
            
            # Compute causal effect
            effect = self.compute_causal_effect(x, y)
            
            # Apply effect
            delta_x = counterfactual_x - current_x
            counterfactual_y = current_y + effect.average_treatment_effect * delta_x
            
            return counterfactual_y
        
        except Exception as e:
            logger.error(f"Counterfactual computation error: {e}")
            return observed_values.get(y, 0)
    
    def get_statistics(self) -> Dict:
        """Get do-calculus statistics"""
        return {
            **self.stats,
            'has_graph': self.graph is not None,
            'has_data': self.data is not None,
            'nodes_in_graph': len(self.graph.nodes) if self.graph else 0,
            'edges_in_graph': len(self.graph.edges) if self.graph else 0
        }
