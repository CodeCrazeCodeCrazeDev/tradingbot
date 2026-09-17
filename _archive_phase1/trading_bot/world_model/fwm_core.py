"""
Institutional-Grade Financial World Model (FWM) Core
===================================================

Implementation of the L1 Fast Path and L2 Global Path as defined in FWM_MASTER_BLUEPRINT.md.
Utilizes Mamba-based State-Space Models (SSM) for linear-scaling tick dynamics.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from .world_state import MarketWorldState, VolatilityRegime, LiquidityCondition, SystemMode
from .fwm_risk import RiskShadowModel, InstitutionalVetoGate
from .fwm_agents import MicrostructureSimulator


class MambaSSMBlock(nn.Module):
    """
    Simplified Mamba-style State-Space Model block for Fast Path perception.
    Captures high-frequency dynamics with linear scaling.
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
        """
        x: [batch, seq_len, d_model]
        """
        (b, l, d) = x.shape
        x_and_res = self.in_proj(x)  # [b, l, 2*d_inner]
        (x, res) = x_and_res.split(split_size=[self.d_inner, self.d_inner], dim=-1)

        x = x.transpose(1, 2)
        x = self.conv1d(x)[:, :, :l]
        x = x.transpose(1, 2)

        x = F.silu(x)

        y = self._ssm(x)

        y = y * F.silu(res)
        return self.out_proj(y)

    def _ssm(self, x: torch.Tensor) -> torch.Tensor:
        """
        Discrete-time SSM transition.
        """
        A = -torch.exp(self.A_log)  # [d_inner, d_state]
        D = self.D                  # [d_inner]

        # Project x to get B, C, and delta
        x_dbl = self.x_proj(x)  # [b, l, d_state*2 + 1]
        (delta, B, C) = x_dbl.split(split_size=[1, self.d_state, self.d_state], dim=-1)
        delta = F.softplus(self.dt_proj(delta))  # [b, l, d_inner]

        # Simplified discretization and scan
        # In a real Mamba, this would be an optimized CUDA scan.
        # Here we use a recurrent approximation for the simulation.

        y = torch.zeros_like(x)
        h = torch.zeros(x.size(0), self.d_inner, self.d_state, device=x.device)

        for t in range(x.size(1)):
            # Discretize A and B
            # dA = exp(delta_t * A)
            # dB = delta_t * B
            dt = delta[:, t, :].unsqueeze(-1)  # [b, d_inner, 1]
            dA = torch.exp(dt * A)             # [b, d_inner, d_state]

            # x_t: [b, d_inner] -> [b, d_inner, 1]
            # B_t: [b, d_state] -> [b, 1, d_state]
            dB = dt * B[:, t, :].unsqueeze(1)  # [b, d_inner, d_state]

            h = dA * h + dB * x[:, t, :].unsqueeze(-1)

            # y_t = C_t * h_t
            # C_t: [b, d_state] -> [b, 1, d_state]
            y[:, t, :] = (h * C[:, t, :].unsqueeze(1)).sum(dim=-1)

        return y + x * D


class GlobalRegimeTransformer(nn.Module):
    """
    L2: Conceptual Synthesis (The Global Path)
    Synthesizes micro-states, macro data, and options surfaces.
    """
    def __init__(self, micro_dim: int = 128, macro_dim: int = 64, latent_dim: int = 256, n_heads: int = 8):
        super().__init__()
        self.micro_proj = nn.Linear(micro_dim, latent_dim)
        self.macro_proj = nn.Linear(macro_dim, latent_dim)

        self.transformer_layer = nn.TransformerEncoderLayer(
            d_model=latent_dim,
            nhead=n_heads,
            dim_feedforward=latent_dim * 4,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(self.transformer_layer, num_layers=4)

        self.regime_head = nn.Linear(latent_dim, 10)  # Categorical regimes
        self.stability_head = nn.Linear(latent_dim, 1) # Structural stability

    def forward(self, z_micro: torch.Tensor, macro_data: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        z_micro: [batch, micro_dim]
        macro_data: [batch, macro_dim]

        Returns:
            z_macro: [batch, latent_dim]
            regime_logits: [batch, 10]
            stability_score: [batch, 1]
        """
        # Global synthesis via cross-modal attention
        micro_feat = self.micro_proj(z_micro).unsqueeze(1)
        macro_feat = self.macro_proj(macro_data).unsqueeze(1)

        combined = torch.cat([micro_feat, macro_feat], dim=1) # [batch, 2, latent_dim]
        encoded = self.transformer(combined)

        # Aggregate context (mean pooling)
        z_macro = encoded.mean(dim=1)

        regime_logits = self.regime_head(z_macro)
        stability = torch.sigmoid(self.stability_head(z_macro))

        return z_macro, regime_logits, stability


class FWM_GenerativeDynamics(nn.Module):
    """
    L3: Generative Dynamics (The Dreamer)
    Hierarchical NHSSM that simulates future trajectories.
    """
    def __init__(self, latent_dim: int = 256, action_dim: int = 5):
        super().__init__()
        self.latent_dim = latent_dim

        # Deterministic path (GRU)
        self.rnn = nn.GRUCell(latent_dim + action_dim, latent_dim)

        # Prior network (predicts next latent distribution)
        self.prior = nn.Sequential(
            nn.Linear(latent_dim, 256),
            nn.ReLU(),
            nn.Linear(256, latent_dim * 2) # Mean and logvar
        )

        # Reward/Value heads
        self.reward_pred = nn.Linear(latent_dim, 1)
        self.liquidity_fragility = nn.Linear(latent_dim, 1)

    def step(self, z_t: torch.Tensor, action: torch.Tensor, h_t: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Single rollout step in latent space.
        """
        rnn_input = torch.cat([z_t, action], dim=-1)
        h_next = self.rnn(rnn_input, h_t)

        params = self.prior(h_next)
        mean, logvar = torch.chunk(params, 2, dim=-1)

        # Sample next state
        std = torch.exp(0.5 * logvar)
        z_next = mean + std * torch.randn_like(std)

        return z_next, h_next, logvar


class FWM_DigitalTwin(nn.Module):
    """
    State-of-the-art Financial World Model Orchestrator.
    Brings together Fast Path, Global Path, and Generative Dynamics.
    """
    def __init__(self, latent_dim: int = 256):
        super().__init__()
        self.l1_fast = FWM_FastPath()
        self.l2_global = GlobalRegimeTransformer()
        self.l3_dreamer = FWM_GenerativeDynamics(latent_dim=latent_dim)

        # Risk shadow model for institutional governance
        self.risk_shadow = RiskShadowModel(latent_dim=latent_dim)
        self.veto_gate = InstitutionalVetoGate(self.risk_shadow)

        # Microstructure simulation for emergent behavior
        self.simulator = MicrostructureSimulator()

    def get_initial_state(self, tick_seq: torch.Tensor, macro_data: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Encode raw market data into starting latent state.
        """
        z_micro = self.l1_fast(tick_seq)
        z_macro, regime, stability = self.l2_global(z_micro, macro_data)
        return z_macro, z_macro # Initial hidden state is z_macro

    def validate_proposal(self, z: torch.Tensor, current_state: MarketWorldState) -> Tuple[bool, str]:
        """
        Final check against the Institutional Veto Gate.
        """
        return self.veto_gate.check_veto(z, current_state)

    def dream(self, initial_z: torch.Tensor, horizon: int = 20, intervention: Optional[Dict[str, float]] = None) -> Dict[str, torch.Tensor]:
        """
        Generate imagined future trajectories (Dreams).
        Supports Pearl's Do-Calculus interventions in latent space.
        Incorporates Agent-Based Microstructure simulation for emergent behavior.
        """
        z_t = initial_z.clone()
        h_t = initial_z.clone()

        # Apply Causal Intervention: do(z_var = value)
        if intervention:
            for dim_idx, val in intervention.items():
                idx = int(dim_idx)
                if idx < z_t.size(-1):
                    z_t[:, idx] = val

        trajectories = []
        uncertainties = []
        flows = []

        for _ in range(horizon):
            # 1. Compute emergent flow from simulated agents (Dealers, HFTs, CTAs)
            # Using partial z_t as z_micro proxy
            z_micro_proxy = z_t[:, :128]
            net_flow = self.simulator.compute_net_flow(z_t, z_micro_proxy)

            # 2. Use flow as part of the action/input to the dreamer
            action = torch.zeros(z_t.size(0), 5, device=z_t.device)
            # Inject net flow into first dimension of action
            action[:, 0] = net_flow.squeeze()

            z_t, h_t, logvar = self.l3_dreamer.step(z_t, action, h_t)

            trajectories.append(z_t)
            uncertainties.append(logvar.exp().mean(dim=-1))
            flows.append(net_flow)

        return {
            'latent_path': torch.stack(trajectories),
            'uncertainty_path': torch.stack(uncertainties),
            'emergent_flow': torch.stack(flows)
        }


class FWM_FastPath(nn.Module):
    """
    L1: Perception & Discovery (The Fast Path)
    Processes tick data, order book, and flow.
    """
    def __init__(self, input_dim: int = 64, latent_dim: int = 128):
        super().__init__()
        self.embedding = nn.Linear(input_dim, latent_dim)
        self.ssm_layers = nn.ModuleList([
            MambaSSMBlock(d_model=latent_dim) for _ in range(2)
        ])
        self.norm = nn.LayerNorm(latent_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: [batch, seq_len, input_dim] (Tick + Order Book + Flow)
        returns: z_micro [batch, latent_dim]
        """
        x = self.embedding(x)
        for ssm in self.ssm_layers:
            x = x + ssm(x)
        x = self.norm(x)
        # Return the latest micro-state
        return x[:, -1, :]
