"""
Institutional-Grade Predictive Planning World Model (WM-V2) Core
==============================================================

Implementation of the Neural Predictive Core using a hybrid Transformer-Mamba (SSM)
architecture. Designed for high-frequency tick data, multi-asset correlations,
and probabilistic future scenario simulation.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import logging
from dataclasses import dataclass, field
from .world_state import MarketWorldState, VolatilityRegime, LiquidityCondition, SystemMode

logger = logging.getLogger(__name__)

# =============================================================================
# 1. Mamba/SSM Backbone Components
# =============================================================================

class MambaBlock(nn.Module):
    """
    Simplified Mamba-style State-Space Model block for long-range temporal modeling.
    Provides linear scaling for high-frequency tick data.
    """
    def __init__(self, d_model: int, d_state: int = 16, d_conv: int = 4, expand: int = 2):
        super().__init__()
        self.d_model = d_model
        self.d_state = d_state
        self.d_conv = d_conv
        self.expand = expand
        self.d_inner = int(self.expand * self.d_model)

        self.in_proj = nn.Linear(self.d_model, self.d_inner * 2, bias=False)
        self.conv1d = nn.Conv1d(
            in_channels=self.d_inner,
            out_channels=self.d_inner,
            bias=True,
            kernel_size=d_conv,
            groups=self.d_inner,
            padding=d_conv - 1,
        )
        self.x_proj = nn.Linear(self.d_inner, self.d_state * 2 + 1, bias=False)
        self.dt_proj = nn.Linear(1, self.d_inner, bias=True)

        # S4D real initialization
        A = torch.arange(1, self.d_state + 1, dtype=torch.float32).repeat(self.d_inner, 1)
        self.A_log = nn.Parameter(torch.log(A))
        self.D = nn.Parameter(torch.ones(self.d_inner))
        self.out_proj = nn.Linear(self.d_inner, self.d_model, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: [batch, seq_len, d_model]"""
        (b, l, d) = x.shape
        x_and_res = self.in_proj(x)
        (x, res) = x_and_res.split(split_size=[self.d_inner, self.d_inner], dim=-1)

        x = x.transpose(1, 2)
        x = self.conv1d(x)[:, :, :l]
        x = x.transpose(1, 2)
        x = F.silu(x)

        y = self._ssm(x)
        y = y * F.silu(res)
        return self.out_proj(y)

    def _ssm(self, x: torch.Tensor) -> torch.Tensor:
        A = -torch.exp(self.A_log)
        D = self.D
        x_dbl = self.x_proj(x)
        (delta, B, C) = x_dbl.split(split_size=[1, self.d_state, self.d_state], dim=-1)
        delta = F.softplus(self.dt_proj(delta))

        # Recurrent scan approximation for training
        y = torch.zeros_like(x)
        h = torch.zeros(x.size(0), self.d_inner, self.d_state, device=x.device)
        for t in range(x.size(1)):
            dt = delta[:, t, :].unsqueeze(-1)
            dA = torch.exp(dt * A)
            dB = dt * B[:, t, :].unsqueeze(1)
            h = dA * h + dB * x[:, t, :].unsqueeze(-1)
            y[:, t, :] = (h * C[:, t, :].unsqueeze(1)).sum(dim=-1)
        return y + x * D

# =============================================================================
# 2. Unified Cross-Asset Encoder
# =============================================================================

class UnifiedCrossAssetEncoder(nn.Module):
    """
    Encoder for heterogeneous market data: FX, Equities, Macro, and Microstructure.
    Maps everything to a unified high-dimensional latent space.
    """
    def __init__(self, asset_dims: Dict[str, int], latent_dim: int = 256):
        super().__init__()
        self.asset_dims = asset_dims
        self.latent_dim = latent_dim

        self.encoders = nn.ModuleDict()
        for asset_type, dim in asset_dims.items():
            self.encoders[asset_type] = nn.Sequential(
                nn.Linear(dim, 128),
                nn.LayerNorm(128),
                nn.GELU(),
                nn.Linear(128, latent_dim)
            )

        # Position embeddings for temporal awareness
        self.pos_embedding = nn.Parameter(torch.randn(1, 1024, latent_dim) * 0.02)

    def forward(self, market_data: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Processes dictionary of asset types to [batch, seq_len, latent_dim].
        """
        encoded_streams = []
        for asset_type, data in market_data.items():
            if asset_type in self.encoders:
                # data expected as [batch, seq_len, feature_dim]
                encoded = self.encoders[asset_type](data)
                encoded_streams.append(encoded)

        if not encoded_streams:
            return torch.zeros(1, 1, self.latent_dim)

        # Global multi-asset synthesis (summing for now, could be concat + attn)
        # Assuming all streams have the same sequence length
        fused = torch.stack(encoded_streams).sum(dim=0)

        seq_len = fused.size(1)
        fused = fused + self.pos_embedding[:, :seq_len, :]
        return fused

# =============================================================================
# 3. Hybrid Predictive Core
# =============================================================================

class PredictiveMarketCore(nn.Module):
    """
    Hybrid Transformer-Mamba backbone.
    Mamba layers process high-frequency dynamics.
    Transformer layers model global cross-asset correlations.
    """
    def __init__(self, latent_dim: int = 256, n_heads: int = 8, n_layers: int = 6):
        super().__init__()
        self.latent_dim = latent_dim

        # Mixed layers: SSM for local temporal, Attention for global relational
        self.layers = nn.ModuleList()
        for i in range(n_layers):
            if i % 2 == 0:
                self.layers.append(MambaBlock(d_model=latent_dim))
            else:
                self.layers.append(nn.TransformerEncoderLayer(
                    d_model=latent_dim,
                    nhead=n_heads,
                    dim_feedforward=latent_dim * 4,
                    batch_first=True,
                    activation="gelu"
                ))

        self.norm = nn.LayerNorm(latent_dim)

        # Forecasting Heads
        self.state_head = nn.Linear(latent_dim, latent_dim)
        self.uncertainty_head = nn.Linear(latent_dim, latent_dim) # Evidential parameters

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            next_state_mu: [batch, latent_dim]
            uncertainty_params: [batch, latent_dim]
        """
        for layer in self.layers:
            if isinstance(layer, MambaBlock):
                x = x + layer(x)
            else:
                x = x + layer(x)

        x = self.norm(x)

        # We focus on the last timestep for planning
        last_step = x[:, -1, :]

        mu = self.state_head(last_step)
        uncertainty = self.uncertainty_head(last_step)

        return mu, uncertainty

# =============================================================================
# 4. Future Scenario Simulator
# =============================================================================

@dataclass
class MarketScenario:
    name: str
    trajectory: torch.Tensor  # [horizon, latent_dim]
    rewards: torch.Tensor     # [horizon]
    confidence: float
    reasoning: str = ""

class FutureScenarioSimulator:
    """
    Generates multiple probabilistic future trajectories.
    Models Bull, Bear, and Volatile scenarios.
    """
    def __init__(self, core: PredictiveMarketCore, horizon: int = 20):
        self.core = core
        self.horizon = horizon

    def simulate(self, current_latent: torch.Tensor, n_scenarios: int = 3) -> List[MarketScenario]:
        """
        Generates diverse trajectories using ancestral sampling or diverse beam search.
        current_latent: [batch, latent_dim]
        """
        scenarios = []
        names = ["Scenario_A (Bull)", "Scenario_B (Bear)", "Scenario_C (Mean)"]
        batch_size = current_latent.size(0)
        device = current_latent.device

        for i in range(min(n_scenarios, len(names))):
            trajectory = []
            current = current_latent.clone()

            # Simplified diverse sampling: perturb current latent based on scenario type
            perturbation = torch.randn_like(current) * 0.05
            if i == 0: perturbation += 0.02 # Bull bias
            if i == 1: perturbation -= 0.02 # Bear bias

            for _ in range(self.horizon):
                # Predict next: input needs [batch, seq_len, latent_dim]
                mu, _ = self.core(current.unsqueeze(1))
                current = mu + perturbation
                trajectory.append(current)

            # trajectory: [horizon, batch, latent_dim] -> [batch, horizon, latent_dim]
            full_trajectory = torch.stack(trajectory).transpose(0, 1)

            # INTELL-01: Rewards must be grounded in predicted execution dynamics and price moves
            # Calculate grounded rewards based on the trajectory
            # For each step in the horizon, we estimate reward = (price_change - costs)
            scenario_rewards = []
            for t in range(self.horizon):
                step_latent = full_trajectory[:, t, :]
                # Predicted price change is encoded in latent transitions
                # We use the volatility head as a proxy for risk-adjusted reward potential
                # in this simplified implementation. In full, we'd decode to prices.
                pred_vol = torch.zeros(batch_size, device=device) # Placeholder
                if hasattr(self.core, 'volatility_head'):
                    pred_vol = F.softplus(self.core.volatility_head(step_latent)).squeeze(-1)

                # Reward = direction * magnitude - impact
                # Here we use a more stable grounded heuristic than randn
                step_reward = (step_latent.mean(dim=-1) * 0.1) - (pred_vol * 0.01)
                scenario_rewards.append(step_reward)

            grounded_rewards = torch.stack(scenario_rewards, dim=1) # [batch, horizon]

            scenarios.append(MarketScenario(
                name=names[i],
                trajectory=full_trajectory,
                rewards=grounded_rewards,
                confidence=0.9 - (i * 0.1)
            ))

        return scenarios

# =============================================================================
# 5. Internalized Causal and Execution Dynamics
# =============================================================================

class CausalDynamicsModel(nn.Module):
    """
    Native causal intervention model using do-calculus.
    Allows perturbing specific dimensions of the latent space to simulate
    interventions (e.g., 'What if volatility doubles?').
    """
    def __init__(self, latent_dim: int = 256):
        super().__init__()
        self.latent_dim = latent_dim
        # Causal adjacency matrix (learned)
        self.causal_graph = nn.Parameter(torch.eye(latent_dim) + torch.randn(latent_dim, latent_dim) * 0.01)

    def do_intervention(self, z: torch.Tensor, intervention: Dict[int, float]) -> torch.Tensor:
        """
        Applies a 'do' operator to specific dimensions of the latent vector.
        z: [batch, latent_dim]
        intervention: {dimension_index: value}
        """
        z_perturbed = z.clone()
        for idx, val in intervention.items():
            if idx < self.latent_dim:
                z_perturbed[:, idx] = val

        # Propagate effects through the causal graph (single-step linear propagation for now)
        z_final = torch.matmul(z_perturbed, self.causal_graph)
        return z_final

class ExecutionSimulator(nn.Module):
    """
    Predicts slippage, market impact, and fill probability based on order size.
    Trading decisions without execution modeling are incomplete.
    """
    def __init__(self, latent_dim: int = 256):
        super().__init__()
        self.slippage_head = nn.Sequential(
            nn.Linear(latent_dim + 1, 64), # latent + normalized_order_size
            nn.ReLU(),
            nn.Linear(64, 1)
        )
        self.fill_prob_head = nn.Sequential(
            nn.Linear(latent_dim + 1, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, z: torch.Tensor, order_size: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        z: [batch, latent_dim]
        order_size: [batch, 1] (normalized)
        """
        x = torch.cat([z, order_size], dim=-1)
        return {
            "expected_slippage": self.slippage_head(x),
            "fill_probability": self.fill_prob_head(x)
        }

# =============================================================================
# 6. Redesigned World Model (V2 Wrapper)
# =============================================================================

class WorldModelV2(nn.Module):
    """
    Unified World Model V2 following the Predictive Planning paradigm.
    """
    def __init__(self, asset_dims: Dict[str, int], latent_dim: int = 256):
        super().__init__()
        self.encoder = UnifiedCrossAssetEncoder(asset_dims, latent_dim)
        self.core = PredictiveMarketCore(latent_dim)
        self.simulator = FutureScenarioSimulator(self.core)

        # Internalized Capabilities
        self.causal_model = CausalDynamicsModel(latent_dim)
        self.execution_sim = ExecutionSimulator(latent_dim)

        # Explicit Capability Heads
        self.regime_classifier = nn.Linear(latent_dim, 10) # Market regimes
        self.volatility_head = nn.Linear(latent_dim, 1)    # Predicted volatility
        self.liquidity_head = nn.Linear(latent_dim, 1)     # Predicted liquidity

    def forward(self, market_data: Dict[str, torch.Tensor], order_size: Optional[torch.Tensor] = None) -> Dict[str, Any]:
        """
        The main 'Think' step of the World Model.
        """
        # 1. Encode multi-asset state
        z_seq = self.encoder(market_data)

        # 2. Internalize current dynamics
        current_mu, uncertainty = self.core(z_seq)

        # 3. Simulate hypothetical futures
        scenarios = self.simulator.simulate(current_mu)

        # 4. Probabilistic Regime & Dynamics Assessment
        regime_logits = self.regime_classifier(current_mu)
        volatility = F.softplus(self.volatility_head(current_mu))
        liquidity = torch.sigmoid(self.liquidity_head(current_mu))

        # 5. Execution Modeling
        batch_size = current_mu.size(0)
        if order_size is None:
            order_size = torch.zeros(batch_size, 1, device=current_mu.device)

        exec_metrics = self.execution_sim(current_mu, order_size)

        return {
            "current_state": current_mu,
            "uncertainty": uncertainty,
            "scenarios": scenarios,
            "regime_logits": regime_logits,
            "volatility": volatility,
            "liquidity": liquidity,
            "execution": exec_metrics
        }

    def simulate_what_if(self, market_data: Dict[str, torch.Tensor], intervention: Dict[int, float]) -> List[MarketScenario]:
        """
        Simulates futures under a specific causal intervention.
        """
        z_seq = self.encoder(market_data)
        current_mu, _ = self.core(z_seq)

        # Apply causal intervention
        z_perturbed = self.causal_model.do_intervention(current_mu, intervention)

        # Simulate from the perturbed state
        return self.simulator.simulate(z_perturbed)

    def save(self, path: str):
        torch.save(self.state_dict(), path)
        logger.info(f"Model V2 saved to {path}")

    def load(self, path: str):
        # SEC-05: Use weights_only=True for safe loading
        self.load_state_dict(torch.load(path, weights_only=True))
        logger.info(f"Model V2 loaded from {path}")
