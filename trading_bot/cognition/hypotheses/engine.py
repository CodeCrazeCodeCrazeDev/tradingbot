"""Hypothesis Engine and Anti-Overfitting Research Pipeline."""

import time
import logging
from typing import Dict, Any, List, Optional
from .contracts import Hypothesis, HypothesisStatus

logger = logging.getLogger("alphaalgo.cognition.hypotheses")


class HypothesisEngine:
    """Generates, evaluates, and applies rigorous anti-overfitting protocols to research hypotheses."""

    def __init__(self, max_p_value: float = 0.05, min_deflated_sharpe: float = 1.0, max_pbo: float = 0.30):
        self.max_p_value = max_p_value
        self.min_deflated_sharpe = min_deflated_sharpe
        self.max_pbo = max_pbo
        self.hypotheses: Dict[str, Hypothesis] = {}

    def create_hypothesis(
        self,
        hypothesis_id: str,
        origin: str,
        mechanism: str,
        predictions: List[str],
        null_hypothesis: str,
        alternative_hypothesis: str,
        required_data: Optional[List[str]] = None,
        evaluation_protocol: Optional[Dict[str, Any]] = None
    ) -> Hypothesis:
        """Constructs a new unverified hypothesis object."""
        h = Hypothesis(
            hypothesis_id=hypothesis_id,
            origin=origin,
            mechanism=mechanism,
            predictions=predictions,
            required_data=required_data or ["OHLCV"],
            null_hypothesis=null_hypothesis,
            alternative_hypothesis=alternative_hypothesis,
            evaluation_protocol=evaluation_protocol or {"method": "walk_forward", "n_splits": 5}
        )
        self.hypotheses[hypothesis_id] = h
        return h

    def evaluate_research_pipeline(
        self,
        hypothesis_id: str,
        p_value: float,
        deflated_sharpe: float,
        pbo_probability: float,
        lookahead_detected: bool = False,
        data_leakage_detected: bool = False
    ) -> Hypothesis:
        """Applies multi-stage anti-overfitting protocol to a hypothesis."""
        h = self.hypotheses.get(hypothesis_id)
        if not h:
            raise ValueError(f"Hypothesis '{hypothesis_id}' not found.")

        h.p_value = round(p_value, 4)
        h.deflated_sharpe = round(deflated_sharpe, 4)
        h.pbo_probability = round(pbo_probability, 4)

        # Anti-Overfitting Gates
        if lookahead_detected:
            h.status = HypothesisStatus.REJECTED
            h.rejection_reason = "Lookahead bias detected in backtest"
        elif data_leakage_detected:
            h.status = HypothesisStatus.REJECTED
            h.rejection_reason = "Data leakage across train/validation splits"
        elif p_value > self.max_p_value:
            h.status = HypothesisStatus.REJECTED
            h.rejection_reason = f"p-value {p_value:.4f} exceeded threshold {self.max_p_value}"
        elif deflated_sharpe < self.min_deflated_sharpe:
            h.status = HypothesisStatus.REJECTED
            h.rejection_reason = f"Deflated Sharpe {deflated_sharpe:.4f} below minimum {self.min_deflated_sharpe}"
        elif pbo_probability > self.max_pbo:
            h.status = HypothesisStatus.REJECTED
            h.rejection_reason = f"PBO probability {pbo_probability:.4f} exceeded limit {self.max_pbo}"
        else:
            h.status = HypothesisStatus.VALIDATED
            h.rejection_reason = None

        logger.info(f"Hypothesis '{hypothesis_id}' evaluation result: {h.status.value} (Reason: {h.rejection_reason})")
        return h
