"""Model performance monitoring for live risk throttling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class PredictionSample:
    """One prediction outcome used by the model monitor."""

    model_name: str
    symbol: str
    predicted_direction: str
    actual_direction: str
    confidence: float
    regime: str = "unknown"
    feature_drift_score: float = 0.0
    data_drift_score: float = 0.0
    pnl: float = 0.0


@dataclass(frozen=True)
class ModelHealthReport:
    """Current model health and the risk action it implies."""

    model_name: str
    samples: int
    accuracy: float
    baseline_accuracy: float
    accuracy_decay: float
    data_drift_score: float
    feature_drift_score: float
    false_confidence_rate: float
    win_rate_by_regime: Dict[str, float]
    risk_multiplier: float
    trading_halted: bool
    warnings: List[str] = field(default_factory=list)


class ModelPerformanceMonitor:
    """Continuous model health monitor.

    When quality decays, this monitor reduces risk first and can halt trading
    entirely if the degradation is severe.
    """

    def __init__(
        self,
        *,
        window_size: int = 100,
        min_samples: int = 20,
        max_accuracy_decay: float = 0.15,
        max_drift_score: float = 0.30,
        max_false_confidence_rate: float = 0.25,
    ) -> None:
        self.window_size = window_size
        self.min_samples = min_samples
        self.max_accuracy_decay = max_accuracy_decay
        self.max_drift_score = max_drift_score
        self.max_false_confidence_rate = max_false_confidence_rate
        self.samples: Dict[str, List[PredictionSample]] = {}
        self.baselines: Dict[str, float] = {}

    def set_baseline(self, model_name: str, accuracy: float) -> None:
        self.baselines[model_name] = max(0.0, min(float(accuracy), 1.0))

    def record(self, sample: PredictionSample) -> ModelHealthReport:
        window = self.samples.setdefault(sample.model_name, [])
        window.append(sample)
        del window[:-self.window_size]
        return self.report(sample.model_name)

    def report(self, model_name: str) -> ModelHealthReport:
        window = self.samples.get(model_name, [])
        if not window:
            return ModelHealthReport(
                model_name=model_name,
                samples=0,
                accuracy=1.0,
                baseline_accuracy=self.baselines.get(model_name, 1.0),
                accuracy_decay=0.0,
                data_drift_score=0.0,
                feature_drift_score=0.0,
                false_confidence_rate=0.0,
                win_rate_by_regime={},
                risk_multiplier=1.0,
                trading_halted=False,
            )

        correct = [s.predicted_direction.lower() == s.actual_direction.lower() for s in window]
        accuracy = sum(correct) / len(correct)
        baseline = self.baselines.get(model_name, accuracy)
        accuracy_decay = max(0.0, baseline - accuracy)
        data_drift = max(s.data_drift_score for s in window)
        feature_drift = max(s.feature_drift_score for s in window)
        false_confidence = [
            s for s in window
            if s.confidence >= 0.75 and s.predicted_direction.lower() != s.actual_direction.lower()
        ]
        false_confidence_rate = len(false_confidence) / len(window)
        win_rate_by_regime = self._win_rate_by_regime(window)

        warnings: List[str] = []
        if len(window) < self.min_samples:
            warnings.append(f"warming up: {len(window)}/{self.min_samples} samples")
        if accuracy_decay > self.max_accuracy_decay:
            warnings.append(f"accuracy decay {accuracy_decay:.2f} exceeds {self.max_accuracy_decay:.2f}")
        if data_drift > self.max_drift_score:
            warnings.append(f"data drift {data_drift:.2f} exceeds {self.max_drift_score:.2f}")
        if feature_drift > self.max_drift_score:
            warnings.append(f"feature drift {feature_drift:.2f} exceeds {self.max_drift_score:.2f}")
        if false_confidence_rate > self.max_false_confidence_rate:
            warnings.append(
                "false confidence rate "
                f"{false_confidence_rate:.2f} exceeds {self.max_false_confidence_rate:.2f}"
            )

        severe = (
            len(window) >= self.min_samples
            and (
                accuracy_decay > self.max_accuracy_decay * 1.5
                or data_drift > self.max_drift_score * 1.5
                or feature_drift > self.max_drift_score * 1.5
                or false_confidence_rate > self.max_false_confidence_rate * 1.5
            )
        )
        degraded = len(window) >= self.min_samples and bool(warnings)
        risk_multiplier = 0.0 if severe else 0.5 if degraded else 1.0

        return ModelHealthReport(
            model_name=model_name,
            samples=len(window),
            accuracy=accuracy,
            baseline_accuracy=baseline,
            accuracy_decay=accuracy_decay,
            data_drift_score=data_drift,
            feature_drift_score=feature_drift,
            false_confidence_rate=false_confidence_rate,
            win_rate_by_regime=win_rate_by_regime,
            risk_multiplier=risk_multiplier,
            trading_halted=severe,
            warnings=warnings,
        )

    def _win_rate_by_regime(self, samples: List[PredictionSample]) -> Dict[str, float]:
        buckets: Dict[str, List[bool]] = {}
        for sample in samples:
            buckets.setdefault(sample.regime, []).append(sample.pnl > 0)
        return {
            regime: sum(results) / len(results)
            for regime, results in buckets.items()
            if results
        }
