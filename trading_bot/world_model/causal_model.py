"""
Causal World Model
==================
Reason over cause-effect relationships instead of just correlations.
E.g., Fed Decision -> Liquidity -> Bond Yields -> Equities.
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
import networkx as nx

class CausalWorldModel(nn.Module):
    """
    Structural Dynamics Model based on causal dependencies.
    """
    def __init__(self, latent_dim: int = 64):
        super().__init__()
        self.latent_dim = latent_dim

        # Causal graph (conceptual nodes)
        self.graph = nx.DiGraph()
        self.graph.add_edges_from([
            ("macro", "liquidity"),
            ("liquidity", "yields"),
            ("yields", "dollar"),
            ("dollar", "equities"),
            ("equities", "risk_appetite")
        ])

        # Mapping from latent segments to causal nodes
        self.causal_projections = nn.ModuleDict({
            node: nn.Linear(latent_dim, 1) for node in self.graph.nodes
        })

        # Structural Equation Models (SEMs) for edges
        self.sems = nn.ModuleDict({
            f"{u}->{v}": nn.Linear(1, 1) for u, v in self.graph.edges
        })

    def forward(self, z: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Estimates the state of causal nodes from latent Z.
        """
        node_states = {node: proj(z) for node, proj in self.causal_projections.items()}
        return node_states

    def structural_impact(self, node_name: str, intervention_value: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Predicts how an intervention on one causal node propagates through the graph.
        """
        results = {node_name: intervention_value}

        # Breadth-first propagation through DiGraph
        for u, v in nx.bfs_edges(self.graph, source=node_name):
            edge_key = f"{u}->{v}"
            if edge_key in self.sems and u in results:
                results[v] = self.sems[edge_key](results[u])

        return results
