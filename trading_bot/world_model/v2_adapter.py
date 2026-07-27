"""
Legacy World Model Adapter (WM-V2 Migration)
===========================================

Provides a compatibility layer between the new Predictive Planning
World Model (V2) and legacy systems expecting the JEPA-based API.
"""

import torch
from typing import Dict, List, Optional, Tuple, Any
from .v2_core import WorldModelV2, MarketScenario
from .world_state import MarketWorldState

class LegacyWorldModelAdapter:
    """
    Adapts WorldModelV2 to the legacy WorldModel (JEPA) interface.
    """
    def __init__(self, model_v2: WorldModelV2):
        self.model_v2 = model_v2
        self.training = False

    def encode(self, market_state: torch.Tensor) -> torch.Tensor:
        """
        Legacy encode: maps raw state to latent.
        """
        # market_state: [batch, input_dim]
        # V2 encoder expects Dict[str, [batch, seq_len, feature_dim]]
        market_data = {'equities': market_state.unsqueeze(1)}
        z_seq = self.model_v2.encoder(market_data)
        return z_seq[:, -1, :] # Return latest latent

    def predict_next(
        self,
        latent_state: torch.Tensor,
        action: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, Dict]:
        """
        Legacy predict_next: returns next_state, reward, hidden, info.
        """
        # V2 core expects [batch, seq_len, latent_dim]
        mu, uncertainty = self.model_v2.core(latent_state.unsqueeze(1))

        # Mock hidden state for legacy compatibility
        hidden = mu

        # V2 doesn't have a single reward head like legacy,
        # but we can use the mean of simulated scenarios as a proxy.
        scenarios = self.model_v2.simulator.simulate(mu)
        reward = scenarios[0].rewards.mean().unsqueeze(0) if scenarios else torch.zeros(1)

        info = {
            'disagreement': uncertainty.mean().item(),
            'v2_adapted': True
        }

        return mu, reward, hidden, info

    def get_world_state(self, latent_state: torch.Tensor, symbol: str = "EURUSD") -> MarketWorldState:
        """
        Legacy get_world_state: bridges latent to structured MarketWorldState.
        """
        output = self.model_v2({'equities': torch.randn(1, 1, 20)}) # Dummy to get shapes
        # In reality, would use latent_state to drive heads

        return MarketWorldState(
            symbol=symbol,
            state_confidence=0.9,
            epistemic_uncertainty=0.1
        )
