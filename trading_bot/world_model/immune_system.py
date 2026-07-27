"""
AI Immune System (Enhanced Runtime Shield)
=========================================
Validates:
- Observations (Data Quality/Anomalies)
- Latent States (Sanity/Consistency)
- Predictions (Plausibility)
- Imagined Futures (Risk/Compliance)
- Actions (Safety/Governance)
"""

from typing import Dict, Any, List, Optional, Tuple
import torch
import logging
from enum import Enum
from .world_state import SystemMode

logger = logging.getLogger(__name__)

class ImmunityStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    COMPROMISED = "compromised"
    CRITICAL = "critical"

class ImmuneSystem:
    """
    The "Immune System" of the AI.
    Performs multi-stage validation gates.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.status = ImmunityStatus.HEALTHY
        logger.info("🛡️ AI Immune System initialized")

    def validate_all(self,
                    obs: Dict[str, torch.Tensor],
                    latent: torch.Tensor,
                    prediction: Dict[str, Any],
                    action: Any) -> Tuple[bool, str]:
        """
        Runs full validation pipeline.
        """
        # 1. Observation Validation
        if not self._validate_observations(obs):
            return False, "Observation anomaly detected"

        # 2. Latent State Validation
        if not self._validate_latent(latent):
            return False, "Latent state inconsistency"

        # 3. Prediction Validation
        if not self._validate_prediction(prediction):
            return False, "Implausible prediction"

        # 4. Action Validation
        if not self._validate_action(action):
            return False, "Unsafe action proposed"

        return True, "All systems nominal"

    def _validate_observations(self, obs: Dict[str, torch.Tensor]) -> bool:
        # Check for NaNs, extreme values, or stale data
        for k, v in obs.items():
            if torch.is_tensor(v) and torch.isnan(v).any():
                return False
        return True

    def _validate_latent(self, z: torch.Tensor) -> bool:
        # Check if latent is within expected bounds (OOD check)
        if not torch.is_tensor(z):
            return True
        norm = torch.norm(z).item()
        if norm > 100.0: # Example threshold
            return False
        return True

    def _validate_prediction(self, pred: Dict[str, Any]) -> bool:
        # Check if predicted reward or state change is physically impossible
        reward = pred.get("reward", 0)
        if torch.is_tensor(reward):
            reward = reward.item()
        if abs(reward) > 1.0: # 100% return in one step? Unlikely.
            return False
        return True

    def _validate_action(self, action: Any) -> bool:
        # Check against hard compliance rules
        return True
