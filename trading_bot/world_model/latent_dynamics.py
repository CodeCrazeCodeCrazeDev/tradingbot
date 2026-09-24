"""
Latent Dynamics - world models over latent state space.

``AgenticPlanningWorldModel`` predicts next-state and action-success
estimates used by the planning agent. ``MarketStateEncoder`` (canonical
implementation in ``unified_world_model``) is re-exported for the flat
import path.
"""

import logging
from typing import Dict, Optional

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

except ImportError:
    pass

try:
    from .unified_world_model import MarketStateEncoder  # noqa: F401
except ImportError:
    pass
