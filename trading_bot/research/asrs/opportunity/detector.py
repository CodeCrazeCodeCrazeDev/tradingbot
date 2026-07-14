import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

class ResearchHypothesis:
    """Actionable scientific hypothesis proposed based on a detected bottleneck."""
    def __init__(
        self,
        hypothesis_id: str,
        trigger_metric: str,
        observed_value: float,
        description: str,
        target_domain: str,
        target_module: str,
        expected_improvement: float
    ):
        self.id = hypothesis_id
        self.trigger_metric = trigger_metric
        self.observed_value = observed_value
        self.description = description
        self.target_domain = target_domain
        self.target_module = target_module
        self.expected_improvement = expected_improvement
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.id,
            "trigger_metric": self.trigger_metric,
            "observed_value": self.observed_value,
            "description": self.description,
            "target_domain": self.target_domain,
            "target_module": self.target_module,
            "expected_improvement": self.expected_improvement,
            "timestamp": self.timestamp
        }

class OpportunityDiscovery:
    """
    Continuous system monitoring division.
    Inspects live system diagnostics and matches anomalies with target domains.
    """
    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        self.thresholds = thresholds or {
            "calibration_error": 0.12,
            "execution_latency_ms": 500.0,
            "slippage_bps": 1.5,
            "memory_leak_mb_hr": 25.0
        }

    def inspect_system_diagnostics(self, live_metrics: Dict[str, float]) -> List[ResearchHypothesis]:
        """Assess diagnostic metrics and output target hypotheses for any breached threshold."""
        hypotheses = []

        # 1. Calibration Error Check
        if live_metrics.get("calibration_error", 0.0) > self.thresholds["calibration_error"]:
            hypotheses.append(ResearchHypothesis(
                hypothesis_id=f"hyp-odd-{uuid.uuid4().hex[:8]}",
                trigger_metric="calibration_error",
                observed_value=live_metrics["calibration_error"],
                description="Cognitive System Controller calibration drift detected.",
                target_domain="calibration_masking",
                target_module="trading_bot.core.csc.controller",
                expected_improvement=0.25 # Sharpe / accuracy boost factor
            ))

        # 2. Latency SLA Check
        if live_metrics.get("execution_latency_ms", 0.0) > self.thresholds["execution_latency_ms"]:
            hypotheses.append(ResearchHypothesis(
                hypothesis_id=f"hyp-odd-{uuid.uuid4().hex[:8]}",
                trigger_metric="execution_latency_ms",
                observed_value=live_metrics["execution_latency_ms"],
                description="Latency breach on complete active inference reasoning hops.",
                target_domain="planning_depth",
                target_module="trading_bot.core.csc.controller",
                expected_improvement=0.35
            ))

        return hypotheses
