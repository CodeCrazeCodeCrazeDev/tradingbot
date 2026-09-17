from enum import Enum, auto
from dataclasses import dataclass, field
import uuid
from typing import Dict, List, Any

class HypothesisState(Enum):
    OBSERVATION = auto()
    REJECTED = auto()
    INSTITUTIONALIZED = auto()
    CONFIRMED = auto()
    INCONCLUSIVE = auto()

@dataclass
class ScientificHypothesis:
    id: str = field(default_factory=lambda: f"hyp-{uuid.uuid4().hex[:12]}")
    state: HypothesisState = HypothesisState.OBSERVATION
    posterior: float = 0.5
    novelty_score: float = 0.0
    vfe: float = 0.0
    validation_score: float = 0.0

def test_metrics():
    from trading_bot.observability.scientific_metrics import ScientificMetrics
    metrics = ScientificMetrics()

    registry = {
        "h1": ScientificHypothesis(state=HypothesisState.REJECTED, posterior=0.1),
        "h2": ScientificHypothesis(state=HypothesisState.INSTITUTIONALIZED, posterior=0.9, validation_score=0.8),
        "h3": ScientificHypothesis(state=HypothesisState.REJECTED, posterior=0.05)
    }

    metrics.update_from_registry(registry)

    print(f"Survival Rate: {metrics.survival_rate}")
    print(f"Rejection Rate: {metrics.rejection_rate}")
    assert metrics.survival_rate == 1/3
    assert metrics.rejection_rate == 2/3

    # Test bottleneck detection
    many_rejected = {f"h{i}": ScientificHypothesis(state=HypothesisState.REJECTED) for i in range(25)}
    metrics.update_from_registry(many_rejected)
    print(f"Bottlenecks: {metrics.bottlenecks_detected}")
    assert len(metrics.bottlenecks_detected) > 0

if __name__ == "__main__":
    test_metrics()
    print("Metrics test passed!")
