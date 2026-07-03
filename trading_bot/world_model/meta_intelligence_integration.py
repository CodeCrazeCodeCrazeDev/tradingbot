"""
Meta-Intelligence Layer Integration
====================================
Maps World Model metrics to the ControlledObject schema.
Enables the Meta-Intelligence layer to manage the World Model as a resource.
"""

import logging
from typing import Dict, Any
from ..neuros_evolution.controlled_objects import (
    ControlledObject, ControlledObjectType, RiskTier, PromotionStatus,
    CostProfile, LatencyProfile
)

logger = logging.getLogger(__name__)

class WorldModelMetaIntelligenceAdapter:
    """
    Adapter to expose World Model as a Controlled Object.
    """
    def __init__(self, world_model):
        self.world_model = world_model
        self.object_id = "world_model_v2_integrated"

    def get_controlled_object_record(self) -> ControlledObject:
        """
        Creates a ControlledObject representation of the current world model.
        """
        return ControlledObject(
            object_id=self.object_id,
            version="2.0.0",
            owner="core_system",
            object_type=ControlledObjectType.SPECIALIST_MODEL,
            task_scope=["prediction", "simulation", "uncertainty_estimation"],
            capability_mapping=["CAP-WM-01", "CAP-WM-02"], # Example IDs
            risk_tier=RiskTier.MEDIUM,
            regime_applicability=["universal"],
            cost_profile=CostProfile(compute_cost_per_hour=0.5),
            latency_profile=LatencyProfile(p50_ms=20.0, p95_ms=50.0),
            known_failure_modes=[],
            forbidden_uses=["high_leverage_unhedged"],
            promotion_status=PromotionStatus.DEPLOYED,
            rollback_target=None,
            provenance_trail=[] # Required for promotion eligibility
        )

    def export_metrics(self) -> Dict[str, float]:
        """
        Exposes metrics required by the Meta-Intelligence layer.
        """
        # In a real system, these would be tracked over time
        return {
            "prediction_accuracy": 0.85,
            "calibration_error": 0.05,
            "epistemic_uncertainty": 0.12,
            "aleatoric_uncertainty": 0.08,
            "regime_accuracy": 0.92,
            "simulation_accuracy": 0.78,
            "causal_consistency": 0.88,
            "ood_detection_rate": 0.95
        }
