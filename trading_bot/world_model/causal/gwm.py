import torch
import torch.nn as nn
import torch.nn.functional as F
import networkx as nx
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class StructuralCausalModel(nn.Module):
    """
    Institutional SCM for financial markets.
    Implements Structural Equation Models (SEMs) and Pearl's Do-Calculus.

    Source: CWMI (Causal World Model Induction) / Pearl (2009).
    """
    def __init__(self, latent_dim: int = 256):
        super().__init__()
        self.latent_dim = latent_dim

        # Canonical Causal DAG for Institutional Markets
        self.dag = nx.DiGraph()
        self.dag.add_edges_from([
            ("Macro_Regime", "Interest_Rates"),
            ("Interest_Rates", "Liquidity"),
            ("Liquidity", "Market_Volatility"),
            ("Market_Volatility", "Price_Dynamics"),
            ("Order_Flow", "Price_Dynamics"),
            ("Liquidity", "Slippage_Impact"),
            ("Order_Size", "Slippage_Impact")
        ])

        self.nodes = list(self.dag.nodes)

        # Mapping from Latent Space (Z) to Causal Nodes
        self.z_to_node = nn.ModuleDict({
            node: nn.Sequential(
                nn.Linear(latent_dim, 64),
                nn.GELU(),
                nn.Linear(64, 1) # Each node is a scalar causal factor
            ) for node in self.nodes
        })

        # Structural Equation Models: f(Parents, Noise)
        self.sems = nn.ModuleDict()
        for node in self.nodes:
            parents = list(self.dag.predecessors(node))
            in_dim = len(parents) + 1 # Parents + Noise
            self.sems[node] = nn.Sequential(
                nn.Linear(in_dim, 32),
                nn.GELU(),
                nn.Linear(32, 1)
            )

    def forward(self, z: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Observational inference: Z -> Causal State."""
        return {node: self.z_to_node[node](z) for node in self.nodes}

    def do_intervention(self, observations: Dict[str, torch.Tensor], interventions: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Structural Intervention (do-operator).
        Predicts downstream effects of forcing specific nodes to values.
        """
        results = observations.copy()
        results.update(interventions)

        # Topologically sort nodes for propagation
        sorted_nodes = list(nx.topological_sort(self.dag))

        for node in sorted_nodes:
            if node in interventions:
                continue # Value fixed by 'do'

            parents = list(self.dag.predecessors(node))
            if not parents:
                continue

            # Input to SEM = [Parent_Values, Noise (assumed 0 for mean prediction)]
            parent_values = torch.cat([results[p] for p in parents], dim=-1)
            noise = torch.zeros(parent_values.size(0), 1, device=parent_values.device)
            sem_input = torch.cat([parent_values, noise], dim=-1)

            results[node] = self.sems[node](sem_input)

        return results

class GenerativeWorldModel(nn.Module):
    """
    Unified Generative World Model (GWM).
    Combines Latent Dynamics (Mamba/Transformer) with SCM for counterfactuals.

    Architecture:
    1. Encoder: Multi-modal (Tick, OrderBook, Macro) -> Latent Z
    2. Dynamics Core: Hybrid Mamba-Transformer (Linear Scaling for Ticks)
    3. Causal Layer: SCM for interventions
    4. Execution Head: Grounded in real transaction data
    """
    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        self.latent_dim = config.get('latent_dim', 256)

        # Predictive Planning Core (WM-V2)
        from trading_bot.world_model.v2_core import PredictiveMarketCore
        self.core = PredictiveMarketCore(latent_dim=self.latent_dim)

        # Structural Causal Model
        self.scm = StructuralCausalModel(latent_dim=self.latent_dim)

        # Execution Grounding Head
        self.execution_head = nn.Sequential(
            nn.Linear(self.latent_dim + 1, 64), # Latent + OrderSize
            nn.GELU(),
            nn.Linear(64, 2) # [Slippage, FillProb]
        )

    async def simulate_rollouts(self, state_data: Dict, horizon: int = 10) -> List[Dict]:
        """Generates multiple probabilistic future scenarios."""
        # This would call the core dynamics and SCM
        return [{"scenario": "bull", "confidence": 0.7, "trajectories": []}]

    async def intervene(self, state_data: torch.Tensor, intervention: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Perform a counterfactual simulation.
        'If I execute X, what is the effect on Y?'
        """
        # 1. Map Latent to Causal Nodes
        observations = self.scm(state_data)

        # 2. Apply Do-Calculus
        counterfactual_state = self.scm.do_intervention(observations, intervention)

        return counterfactual_state

    def ground_execution(self, z: torch.Tensor, order_size: float) -> Tuple[float, float]:
        """Predicts execution outcomes based on grounded market state."""
        order_tensor = torch.tensor([[order_size]], device=z.device)
        feat = torch.cat([z, order_tensor], dim=-1)
        out = self.execution_head(feat)
        return out[0, 0].item(), torch.sigmoid(out[0, 1]).item()
