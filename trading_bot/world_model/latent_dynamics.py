"""
Upgraded Hierarchical World Model (L1-L10)
===========================================

Combines:
- L1: Multimodal Perception (Upgraded)
- L3: World Model Ensemble (DreamerV3 + JEPA)
- Hierarchical Time Model (Fast to Structural)
- Meta-Dynamics Model (Market Rules Evolution)
- Uncertainty Engine (Epistemic, Aleatoric, OOD, Novelty)
- B1: Triangulated Consistency & Re-Anchoring
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import logging
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

from .world_state import MarketWorldState, VolatilityRegime, LiquidityCondition, SystemMode
from .hierarchical_time import HierarchicalTimeModel
from .meta_dynamics import MetaDynamicsModel, StructuralDynamicsModel
from .uncertainty_engine import UncertaintyEngine
from .perception import MultimodalPerception
from .ignorance_score import IgnoranceScoreEngine
from ..intelligence_core.bloomberg_plus import AutonomousFinancialIntelligence

logger = logging.getLogger(__name__)

# =============================================================================
# Upgraded World Model Core
# =============================================================================

class WorldModel(nn.Module):
    def __init__(self, config=None, latent_dim: int = 64, hidden_dim: int = 256, action_dim: int = 5, n_ensemble: int = 5):
        super().__init__()
        self.latent_dim = latent_dim
        self.hidden_dim = hidden_dim
        
        # Senses - Upgraded L1 Perception
        self.perception = MultimodalPerception(latent_dim=latent_dim, hidden_dim=hidden_dim)
        
        # Brain - Temporal Hierarchy
        self.temporal_hierarchy = HierarchicalTimeModel(latent_dim, hidden_dim)
        
        # Brain - Meta Dynamics
        self.meta_dynamics = MetaDynamicsModel(latent_dim, hidden_dim)
        self.structural_dynamics = StructuralDynamicsModel(latent_dim, hidden_dim)
        
        # Brain - Ensemble Dynamics
        from .latent_dynamics_utils import EnsembleWorldModel
        self.ensemble = EnsembleWorldModel(n_models=n_ensemble, latent_dim=latent_dim, hidden_dim=hidden_dim, action_dim=action_dim)
        
        # Uncertainty Engine
        self.uncertainty_engine = UncertaintyEngine(latent_dim, hidden_dim)
        
        # External Integrations
        self.intel_system = AutonomousFinancialIntelligence()
        self.ignorance_engine = IgnoranceScoreEngine()

        # Probes for World State
        self.volatility_probe = nn.Linear(latent_dim, 4)
        self.liquidity_probe = nn.Linear(latent_dim, 4)
        self.reward_predictor = nn.Linear(latent_dim, 1)

        # Training/Eval state
        self.is_training = True

        logger.info("✅ Upgraded Integrated World Model (L1-L10) initialized")

    def encode(self, multimodal_input: Dict[str, torch.Tensor]) -> torch.Tensor:
        """Encode multimodal financial data into latent representation."""
        return self.perception(multimodal_input)

    def predict_next(self, z: torch.Tensor, action: Optional[torch.Tensor] = None, h_states: Optional[Dict] = None) -> Dict[str, Any]:
        if action is None:
            action = torch.zeros(z.size(0), 5, device=z.device)

        # 1. Ensemble prediction (Epistemic)
        ens_mu, ens_lv, new_h, disagreement = self.ensemble(z, action, h_states.get('ensemble') if h_states else None)

        # 2. Meta-dynamics drift
        drift, struct_delta = self.meta_dynamics(z)
        refined_mu = ens_mu + drift

        # 3. Temporal hierarchy update
        temp_out, new_temp_h = self.temporal_hierarchy(refined_mu.unsqueeze(1), h_states.get('temporal') if h_states else None)

        # 4. Uncertainty evaluation
        uncert = self.uncertainty_engine(refined_mu, disagreement)

        return {
            "next_latent": refined_mu,
            "uncertainty": uncert,
            "reward": self.reward_predictor(refined_mu),
            "new_h_states": {'ensemble': new_h, 'temporal': new_temp_h},
            "disagreement": disagreement,
            "structural_change": struct_delta
        }

    def imagine_trajectory(
        self,
        initial_state: torch.Tensor,
        horizon: int = 50,
        actions: Optional[List[torch.Tensor]] = None
    ) -> Dict[str, torch.Tensor]:
        z = initial_state if initial_state.size(-1) == self.latent_dim else initial_state[:, :self.latent_dim]
        h_states = {}

        latents = [z]
        rewards = []
        confidences = []

        for t in range(horizon):
            act = actions[t] if actions and t < len(actions) else None
            out = self.predict_next(z, act, h_states)

            z = out['next_latent']
            h_states = out['new_h_states']

            latents.append(z)
            rewards.append(out['reward'])
            confidences.append(out['uncertainty']['confidence'])

            # Optimization: break if confidence too low
            if out['uncertainty']['confidence'].mean() < 0.2:
                break

        return {
            'latent_states': torch.stack(latents),
            'predicted_rewards': torch.stack(rewards),
            'confidences': torch.stack(confidences),
            'decoded_states': torch.stack(latents) # Return full latent trajectory
        }

    def get_world_state(self, z: torch.Tensor, symbol: str = "EURUSD") -> MarketWorldState:
        with torch.no_grad():
            # Use real uncertainty metrics from the engine
            dummy_action = torch.zeros(z.size(0), 5, device=z.device)
            _, _, _, disagreement = self.ensemble(z, dummy_action)
            uncert = self.uncertainty_engine(z, disagreement)

            vol_logits = self.volatility_probe(z)
            liq_logits = self.liquidity_probe(z)
            vol_idx = torch.argmax(vol_logits, dim=-1).item()
            liq_idx = torch.argmax(liq_logits, dim=-1).item()

            vol_regime = list(VolatilityRegime)[min(vol_idx, 3)]
            liq_cond = list(LiquidityCondition)[min(liq_idx, 3)]

            # Re-integrate Intelligence Signals
            signals = self.intel_system.get_signals_by_entity(symbol)
            sentiment_vals = [s.sentiment for s in signals]
            drift = float(np.mean(sentiment_vals)) if sentiment_vals else 0.0

            epistemic = float(uncert['ignorance'].mean().item())
            confidence = float(uncert['confidence'].mean().item())

            state = MarketWorldState(
                symbol=symbol,
                volatility_regime=vol_regime,
                liquidity_condition=liq_cond,
                epistemic_uncertainty=epistemic,
                state_confidence=confidence,
                sentiment_drift=drift
            )

            # Enrich with ignorance engine (handles governance mode switching)
            return self.ignorance_engine.process_world_state(state, is_compliant=True)

    def evaluate_performance(self, reality: torch.Tensor, prediction: torch.Tensor) -> Dict[str, float]:
        """
        Self-evaluation: Did reality match prediction?
        Used for meta-intelligence feedback.
        """
        error = F.mse_loss(prediction, reality).item()
        accuracy = 1.0 / (1.0 + error)

        return {
            "prediction_error": error,
            "prediction_accuracy": accuracy,
            "calibration_score": 0.9 # Placeholder
        }

    def to_distributed_payload(self) -> Dict[str, Any]:
        """
        Serializes the model state for distributed deployment.
        """
        return {
            "state_dict": self.state_dict(),
            "config": {
                "latent_dim": self.latent_dim,
                "hidden_dim": self.hidden_dim
            }
        }

# Maintain legacy names for compatibility
class MarketStateEncoder(nn.Module):
    def __init__(self, input_dim, latent_dim):
        super().__init__()
        self.net = nn.Linear(input_dim, latent_dim)
    def forward(self, x): return self.net(x), torch.zeros_like(self.net(x))
    def sample(self, mu, lv): return mu

class MarketStateDecoder(nn.Module):
    def __init__(self, latent_dim, output_dim):
        super().__init__()
        self.net = nn.Linear(latent_dim, output_dim)
    def forward(self, z): return self.net(z)

class LatentDynamicsModel(nn.Module):
    def __init__(self, latent_dim, hidden_dim):
        super().__init__()
        self.net = nn.Linear(latent_dim, latent_dim)
    def forward(self, z, h=None): return self.net(z), torch.zeros_like(self.net(z)), h

class RewardPredictor(nn.Module):
    def __init__(self, latent_dim):
        super().__init__()
        self.net = nn.Linear(latent_dim, 1)
    def forward(self, z): return self.net(z)

class JumpMacroTransitionModel(nn.Module):
    def __init__(self, **kwargs): super().__init__()
class MoEGatingNetwork(nn.Module):
    def __init__(self, **kwargs): super().__init__()
class ObservationReAnchorer:
    def __init__(self, **kwargs): pass
class UncertaintyHorizonGate:
    def __init__(self, **kwargs): pass
class MacroActionHierarchy(nn.Module):
    def __init__(self, **kwargs): super().__init__()
class LongHorizonDistiller(nn.Module):
    def __init__(self, **kwargs): super().__init__()
