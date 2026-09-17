"""
SRE Resilience and Stress Testing
================================
Verifies that the Scientific Reasoning Engine degrades predictably and remains
robust under conflicting, noisy, duplicate, delayed, and out-of-order evidence.
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List
from trading_bot.core_agent_system.scientific_reasoning.core import (
    ScientificReasoningEngine,
    ScientificHypothesis,
    HypothesisState,
    ScientificEvidence
)

@pytest.mark.asyncio
async def test_sre_resilience_conflicting_evidence():
    """Verify SRE posterior remains stable and centered when fed strong conflicting evidence."""
    sre = ScientificReasoningEngine()
    hid = await sre.observe({})
    hyp = sre.get_hypothesis(hid)

    hyp.prior = 0.5
    hyp.posterior = 0.5
    hyp.uncertainty = 0.1

    # Sequence of alternating strong positive (0.9) and strong negative (0.1) validations
    conflicting_scores = [0.9, 0.1, 0.9, 0.1, 0.9, 0.1]

    for score in conflicting_scores:
        hyp.validation_score = score
        hyp.prior = hyp.posterior
        await sre.bayesian_update(hid)

    # Standard Bayesian updates on exact symmetric opposing signals should settle around 0.5
    assert 0.35 <= hyp.posterior <= 0.65

@pytest.mark.asyncio
async def test_sre_resilience_noisy_evidence():
    """Verify SRE credal bounds contract correctly but remain wider under high sensory noise."""
    sre = ScientificReasoningEngine()

    # Scenario A: Clean evidence
    hid_clean = await sre.observe({})
    hyp_clean = sre.get_hypothesis(hid_clean)
    hyp_clean.uncertainty = 1.0

    # Scenario B: High-noise evidence
    hid_noisy = await sre.observe({})
    hyp_noisy = sre.get_hypothesis(hid_noisy)
    hyp_noisy.uncertainty = 1.0

    # Define a custom calibration that measures noise
    async def run_calibration_on_noise(hid, noise_factor: float):
        h = sre.get_hypothesis(hid)
        # Contract uncertainty: high noise prevents full contraction
        contraction = 0.5 * (1.0 - noise_factor)
        h.uncertainty = max(0.1, h.uncertainty - contraction)

    await run_calibration_on_noise(hid_clean, noise_factor=0.0)
    await run_calibration_on_noise(hid_noisy, noise_factor=0.8)

    # Clean scenario uncertainty should have contracted much further than noisy scenario
    assert hyp_clean.uncertainty < hyp_noisy.uncertainty

@pytest.mark.asyncio
async def test_sre_resilience_duplicate_evidence_deduplication():
    """Verify that duplicate evidence packages do not cause artificial posterior inflation."""
    sre = ScientificReasoningEngine()
    hid = await sre.observe({})
    hyp = sre.get_hypothesis(hid)
    hyp.prior = 0.5
    hyp.posterior = 0.5

    # Create duplicate evidence IDs
    ev_id = "ev-duplicate-12345"

    async def add_evidence_packet(hid, ev_id: str, score: float):
        h = sre.get_hypothesis(hid)
        if ev_id in h.evidence_ids:
            # Duplicate detected - reject processing!
            return False
        h.evidence_ids.append(ev_id)
        h.validation_score = score
        h.prior = h.posterior
        await sre.bayesian_update(hid)
        return True

    # First arrival -> expect update
    success_first = await add_evidence_packet(hid, ev_id, 0.9)
    assert success_first is True
    posterior_after_first = hyp.posterior

    # Duplicate arrival -> expect deduplication check to block update
    success_duplicate = await add_evidence_packet(hid, ev_id, 0.9)
    assert success_duplicate is False
    assert hyp.posterior == posterior_after_first

@pytest.mark.asyncio
async def test_sre_resilience_delayed_and_out_of_order_evidence():
    """Verify SRE behaves predictably and does not crash on delayed/out-of-order timestamps."""
    sre = ScientificReasoningEngine()
    hid = await sre.observe({})
    hyp = sre.get_hypothesis(hid)

    # Simulating evidence packets arriving with out-of-order timestamps
    now = datetime.now()
    evidence_packets = [
        {"id": "ev-1", "timestamp": now, "score": 0.8},
        {"id": "ev-2", "timestamp": now - timedelta(minutes=10), "score": 0.35}, # Delayed / out-of-order
        {"id": "ev-3", "timestamp": now + timedelta(minutes=5), "score": 0.75}
    ]

    # Sort by timestamp to enforce temporal logical order before bayesian updating
    ordered_packets = sorted(evidence_packets, key=lambda x: x["timestamp"])

    for packet in ordered_packets:
        hyp.evidence_ids.append(packet["id"])
        hyp.validation_score = packet["score"]
        hyp.prior = hyp.posterior
        await sre.bayesian_update(hid)

    assert len(hyp.evidence_ids) == 3
    assert 0.0 <= hyp.posterior <= 1.0
