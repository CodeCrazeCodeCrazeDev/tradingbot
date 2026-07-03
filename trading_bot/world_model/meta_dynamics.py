import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional, Tuple

class MetaDynamicsModel(nn.Module):
    """
    Predicts how the market rules change (the evolution of dynamics).
    Instead of predicting what the market does, it predicts how the
    underlying structural relationships are evolving.
    """
    def __init__(self, latent_dim: int = 64, hidden_dim: int = 128):
        super().__init__()
        self.latent_dim = latent_dim

        # Predicts the drift in the latent transition function
        self.dynamics_drift_net = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim)
        )

        # Predicts changes in volatility and correlation structures
        self.structure_evolution = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim)
        )

    def forward(self, current_latent: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            drift: The predicted change in the transition dynamics
            structure_delta: The predicted change in market structure
        """
        drift = self.dynamics_drift_net(current_latent)
        structure_delta = self.structure_evolution(current_latent)
        return drift, structure_delta

class StructuralDynamicsModel(nn.Module):
    """
    Predicts long-term structural shifts and regime transitions.
    Operates at the slowest time scale.
    """
    def __init__(self, latent_dim: int = 64, hidden_dim: int = 128):
        super().__init__()
        self.regime_predictor = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 4) # 4 primary volatility regimes
        )

    def forward(self, latent_state: torch.Tensor) -> torch.Tensor:
        return F.softmax(self.regime_predictor(latent_state), dim=-1)
