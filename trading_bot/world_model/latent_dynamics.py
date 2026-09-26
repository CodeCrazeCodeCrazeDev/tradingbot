"""
Latent Dynamics - world models over latent state space.

``AgenticPlanningWorldModel`` predicts next-state and action-success
estimates used by the planning agent. ``MarketStateEncoder`` (canonical
implementation in ``unified_world_model``) is re-exported for the flat
import path.
"""

import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class WorldModel:
    """Config-dict world model used by IntegratedAgentSystem.

    Wraps AgenticPlanningWorldModel when torch is available; degrades to a
    latent-state container otherwise. Accepts {'input_dim','latent_dim',
    'hidden_dim','action_dim'}.
    """

    def __init__(self, config: Optional[Dict[str, int]] = None):
        config = config or {}
        self.config = config
        self.input_dim = config.get("input_dim", 20)
        self.latent_dim = config.get("latent_dim", 64)
        self.hidden_dim = config.get("hidden_dim", 128)
        self.action_dim = config.get("action_dim", 8)
        self._model = None
        try:
            self._model = AgenticPlanningWorldModel(
                latent_dim=self.latent_dim,
                hidden_dim=self.hidden_dim,
                action_dim=self.action_dim,
            )
        except Exception as e:
            logger.warning(f"WorldModel: AgenticPlanningWorldModel unavailable ({e}); running as config container")

    def predict(self, state, action=None):
        if self._model is not None:
            return self._model(state, action)
        return state


try:
    import torch
    import torch.nn as nn

    class AgenticPlanningWorldModel(nn.Module):
        """Latent world model: (state, action) -> (next_state, success_prob)."""

        def __init__(self, latent_dim: int = 512, hidden_dim: int = 512, action_dim: int = 8):
            super().__init__()
            self.latent_dim = latent_dim
            self.hidden_dim = hidden_dim
            self.action_dim = action_dim
            self.training_stage = "IDLE"

            self.transition = nn.Sequential(
                nn.Linear(latent_dim + action_dim, hidden_dim),
                nn.GELU(),
                nn.Linear(hidden_dim, latent_dim),
            )
            self.success_head = nn.Sequential(
                nn.Linear(latent_dim + action_dim, hidden_dim),
                nn.GELU(),
                nn.Linear(hidden_dim, 1),
                nn.Sigmoid(),
            )

        def forward(self, state, action):
            x = torch.cat([state, action], dim=-1)
            prospective_next = self.transition(x)
            success_estimate = self.success_head(x)
            return prospective_next, success_estimate

        def wm_amt_inject_latent_predictions(self, states, actions, next_states):
            """Stage 1: World-Model AMT - latent prediction loss."""
            self.training_stage = "WM-AMT"
            pred, _ = self.forward(states, actions)
            return nn.functional.mse_loss(pred, next_states)

        def fe_sft_format_structure(self, states, actions, structured_targets):
            """Stage 2: FE-SFT - structural formatting loss."""
            self.training_stage = "FE-SFT"
            pred, _ = self.forward(states, actions)
            return nn.functional.mse_loss(pred, structured_targets)

        def fc_rl_refine_foresight(self, states, actions, actual_success_outcomes):
            """Stage 3: FC-RL - foresight refinement via success BCE."""
            self.training_stage = "FC-RL"
            _, success = self.forward(states, actions)
            return nn.functional.binary_cross_entropy(success, actual_success_outcomes)

    class MarketStateDecoder(nn.Module):
        """Decodes latent representation back to market state."""

        def __init__(self, latent_dim: int = 32, output_dim: int = 20):
            super().__init__()
            self.decoder = nn.Sequential(
                nn.Linear(latent_dim, 64),
                nn.ReLU(),
                nn.Linear(64, 64),
                nn.ReLU(),
                nn.Linear(64, output_dim)
            )

        def forward(self, z: torch.Tensor) -> torch.Tensor:
            """Decode latent state to market state."""
            return self.decoder(z)


    class LatentDynamicsModel(nn.Module):
        """
        Predicts evolution of latent state over time.
        Includes stochastic and deterministic paths.
        """

        def __init__(self, latent_dim: int = 32, hidden_dim: int = 64):
            super().__init__()

            # Deterministic path (GRU)
            self.rnn = nn.GRU(
                input_size=latent_dim,
                hidden_size=hidden_dim,
                num_layers=2,
                batch_first=True
            )

            # Prior network (predicts next latent state)
            self.prior = nn.Sequential(
                nn.Linear(hidden_dim, 64),
                nn.ReLU(),
                nn.Linear(64, latent_dim * 2)  # Mean and logvar
            )

            self.latent_dim = latent_dim
            self.hidden_dim = hidden_dim

        def forward(
            self,
            latent_state: torch.Tensor,
            hidden_state: Optional[torch.Tensor] = None
        ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            """
            Predict next latent state distribution.

            Returns:
                mean, logvar, new_hidden_state
            """
            # Update RNN state
            _, hidden_state = self.rnn(latent_state.unsqueeze(1), hidden_state)

            # Predict next latent state
            prior_params = self.prior(hidden_state[-1])
            mean, logvar = torch.chunk(prior_params, 2, dim=-1)

            return mean, logvar, hidden_state

        def sample_prediction(
            self,
            mean: torch.Tensor,
            logvar: torch.Tensor
        ) -> torch.Tensor:
            """Sample from predicted distribution."""
            std = torch.exp(0.5 * logvar)
            eps = torch.randn_like(std)
            return mean + eps * std

except ImportError:
    pass

try:
    from .unified_world_model import MarketStateEncoder  # noqa: F401
except ImportError:
    pass
