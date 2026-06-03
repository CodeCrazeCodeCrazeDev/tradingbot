"""
FWM Risk Shadow Model & Adversarial Veto
========================================

Adversarial model that identifies paths to maximum drawdown.
Provides the mandatory Veto Layer for institutional governance.
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
from .world_state import MarketWorldState, SystemMode


class RiskShadowModel(nn.Module):
    """
    Adversarial World Model focused on finding failure modes.
    Trained to minimize the agent's reward (Worst-Case analysis).
    """
    def __init__(self, latent_dim: int = 256):
        super().__init__()
        # Forecasts correlation breakdown probability
        self.correlation_gate = nn.Linear(latent_dim, 1)
        # Forecasts liquidity void probability
        self.fragility_gate = nn.Linear(latent_dim, 1)
        # Extreme value tail risk head
        self.tail_risk_head = nn.Linear(latent_dim, 1)

    def evaluate_risk(self, z: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Identify hidden risks in the current latent state.
        """
        with torch.no_grad():
            corr_breakdown = torch.sigmoid(self.correlation_gate(z))
            liquidity_fragility = torch.sigmoid(self.fragility_gate(z))
            tail_risk = torch.sigmoid(self.tail_risk_head(z))

            return {
                'correlation_breakdown': corr_breakdown,
                'liquidity_fragility': liquidity_fragility,
                'tail_risk': tail_risk,
                'aggregate_risk': (corr_breakdown + liquidity_fragility + tail_risk) / 3.0
            }


class InstitutionalVetoGate:
    """
    Mandatory governance layer that can override trade signals.
    """
    def __init__(self, risk_model: RiskShadowModel):
        self.risk_model = risk_model
        # Institutional Thresholds
        self.MAX_ALLOWED_RISK = 0.75
        self.MAX_ALLOWED_FRAGILITY = 0.6
        self.MAX_ALLOWED_UNCERTAINTY = 0.8

    def check_veto(self, z: torch.Tensor, world_state: MarketWorldState) -> Tuple[bool, str]:
        """
        Check if any institutional constraints are breached.
        Returns: (is_vetoed, reason)
        """
        risk_out = self.risk_model.evaluate_risk(z)

        # 1. Ignorance Veto
        if world_state.ignorance_score > self.MAX_ALLOWED_UNCERTAINTY:
            return True, "Epistemic uncertainty exceeds institutional limit (Ignorance Veto)"

        # 2. Fragility Veto
        if risk_out['liquidity_fragility'].mean().item() > self.MAX_ALLOWED_FRAGILITY:
            return True, "Liquidity fragility indicates imminent void (Fragility Veto)"

        # 3. Aggregate Risk Veto
        if risk_out['aggregate_risk'].mean().item() > self.MAX_ALLOWED_RISK:
            return True, "Aggregate risk signature is too high for current regime"

        return False, "Allowed"

    def recommend_system_mode(self, z: torch.Tensor, current_state: MarketWorldState) -> SystemMode:
        """
        Autonomous mode shift recommendations.
        """
        risk_out = self.risk_model.evaluate_risk(z)
        risk_score = risk_out['aggregate_risk'].mean().item()

        if risk_score > 0.8:
            return SystemMode.HALT
        elif risk_score > 0.6:
            return SystemMode.DEFENSIVE
        elif risk_score > 0.4:
            return SystemMode.REDUCED_RISK
        else:
            return SystemMode.NORMAL
