import logging
import uuid
import numpy as np
from datetime import datetime
from typing import List, Tuple, Dict, Any

from .models import ReasoningHop, AnomalyDiagnosis, IntrospectionReport

logger = logging.getLogger("AlphaAlgo.Introspection")


class IntrospectionEngine:
    """
    Introspection Engine (IE).
    Enables meta-cognitive self-monitoring, confidence calibration, and self-diagnosis.
    Grounds LLM introspection concepts into the state space of Active Inference.
    """

    def __init__(self, vfe_surprise_threshold: float = 3.5, max_acceptable_entropy: float = 0.80):
        self.vfe_surprise_threshold = vfe_surprise_threshold
        self.max_acceptable_entropy = max_acceptable_entropy

    def monitor_reasoning_chain(self, decision_id: str, hops: List[ReasoningHop]) -> IntrospectionReport:
        logger.info(f"Introspection: Auditing intermediate reasoning chain for decision {decision_id}...")

        report_id = f"intro_{uuid.uuid4().hex[:10]}"

        if not hops:
            return IntrospectionReport(
                report_id=report_id,
                target_decision_id=decision_id,
                overall_confidence=0.0,
                reasoning_hops_evaluated=0,
                anomalies=[AnomalyDiagnosis(is_anomalous=True, description="Reasoning chain is empty", anomaly_type="EMPTY_REASONING_CHAIN", severity_pct=100.0)],
                is_decision_safe=False,
                evidence_consistency_score=0.0,
                decision_quality_explanation="Declining execution: Reasoning hops are empty."
            )

        anomalies: List[AnomalyDiagnosis] = []

        # 1. Analyze Variational Free Energy (VFE) perturbations & spikes (Surprise spikes)
        vfe_values = [hop.vfe_surprise for hop in hops]
        max_vfe = max(vfe_values)
        if max_vfe > self.vfe_surprise_threshold:
            anomalies.append(AnomalyDiagnosis(
                is_anomalous=True,
                description=f"Variational Free Energy surprise spiked at {max_vfe:.2f} (threshold: {self.vfe_surprise_threshold})",
                anomaly_type="VFE_SURPRISE_SPIKE",
                severity_pct=float(min((max_vfe / self.vfe_surprise_threshold) * 50.0, 100.0))
            ))

        # 2. Analyze entropy / uncertainty behavior (Confidence Calibration)
        # Higher step entropy means lower prediction certainty
        entropies = [hop.entropy for hop in hops]
        avg_entropy = float(np.mean(entropies))
        if avg_entropy > self.max_acceptable_entropy:
            anomalies.append(AnomalyDiagnosis(
                is_anomalous=True,
                description=f"Reasoning uncertainty is dangerously high (avg entropy: {avg_entropy:.2f})",
                anomaly_type="HIGH_UNCERTAINTY_ENTROPY",
                severity_pct=float(min((avg_entropy / self.max_acceptable_entropy) * 60.0, 100.0))
            ))

        # 3. Detect inconsistent evidence & logical planning loops
        evidence_text = " ".join([claim for hop in hops for claim in hop.evidence_claims]).lower()
        has_contradiction = False
        if "bullish" in evidence_text and "bearish" in evidence_text and ("severe risk" in evidence_text or "critical drop" in evidence_text):
            has_contradiction = True
            anomalies.append(AnomalyDiagnosis(
                is_anomalous=True,
                description="Evidence contains severe mutual contradictions (simultaneous high-yield bullish claims mixed with critical drop risk)",
                anomaly_type="EVIDENCE_INCONSISTENCY",
                severity_pct=85.0
            ))

        # 4. Calculate overall calibrated confidence
        # We weight the confidence of steps inversely by their entropy
        weights = [1.0 / max(hop.entropy, 0.05) for hop in hops]
        total_weight = sum(weights)
        weighted_conf = sum(hop.confidence_score * w for hop, w in zip(hops, weights)) / total_weight if total_weight > 0 else 0.5

        # Penalize confidence by the presence of anomalies
        confidence_penalty = sum(anom.severity_pct for anom in anomalies) / 200.0  # Cap penalty impact
        overall_confidence = float(max(weighted_conf - confidence_penalty, 0.0))

        # 5. Measure evidence consistency score (0.0 to 100.0)
        evidence_consistency = 100.0
        if has_contradiction:
            evidence_consistency -= 50.0
        evidence_consistency -= len(anomalies) * 15.0
        evidence_consistency = max(evidence_consistency, 0.0)

        # 6. Explaining decision quality
        is_safe = (overall_confidence >= 0.50) and (not any(anom.severity_pct > 75.0 for anom in anomalies))

        explanation = (
            f"Decision quality is {'APPROVED' if is_safe else 'REJECTED_BY_INTROSPECTION'}. "
            f"Calibrated confidence is {overall_confidence:.2f}. "
            f"Reasoning path evaluated over {len(hops)} hops with {len(anomalies)} anomalies identified. "
            f"Evidence consistency index is {evidence_consistency:.1f}%."
        )

        return IntrospectionReport(
            report_id=report_id,
            target_decision_id=decision_id,
            overall_confidence=round(overall_confidence, 2),
            reasoning_hops_evaluated=len(hops),
            anomalies=anomalies,
            is_decision_safe=is_safe,
            evidence_consistency_score=round(evidence_consistency, 2),
            decision_quality_explanation=explanation
        )
