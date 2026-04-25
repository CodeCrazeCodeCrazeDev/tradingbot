"""
GETS: Governed Evolving Time-Series Foundation System

A hierarchical temporal intelligence stack that extracts edge from the structure of
agreement, disagreement, stability, and uncertainty across multiple foundation
time-series models—operating under strict governance with bounded, auditable, reversible
evolution.

Core Principle:
- Inference (live): predicts, embeds, scores uncertainty—never rewrites itself
- Adaptation (offline): studies failures, proposes improvements
- Evolution (sandbox): tests mutations, validates changes
- Promotion (governance): audited, champion-challenger validated upgrades only

Five-Layer Architecture:
1. Temporal Perception Layer: Foundation model inference (Kronos, TimesFM, Moirai, TTM)
2. Forecast & Representation Layer: Trading-native multi-task heads
3. Self-Diagnosis Layer: Introspection engine, disagreement geometry, stability testing
4. Controlled Evolution Layer: Sandbox-only improvement generation
5. Governance & Promotion Layer: Audited, reversible capability promotion
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core.temporal_perception import TemporalPerceptionLayer
    from .core.forecast_representation import ForecastRepresentationLayer
    from .core.self_diagnosis import SelfDiagnosisLayer
    from .core.controlled_evolution import ControlledEvolutionLayer
    from .core.governance_promotion import GovernancePromotionLayer
    from .gets_system import GETS

__version__ = "0.1.0"

__all__ = [
    "GETS",
    "TemporalPerceptionLayer",
    "ForecastRepresentationLayer",
    "SelfDiagnosisLayer",
    "ControlledEvolutionLayer",
    "GovernancePromotionLayer",
    "MultiModalAwareness",
    "RealtimeInferencePipeline",
    "BacktestEngine",
    "MetricsCollector",
    "ModelCheckpoint",
    "SystemSnapshot",
]

def create_gets(config: dict = None) -> "GETS":
    """Factory function to create a GETS instance."""
    from .gets_system import GETS
    return GETS(config)
