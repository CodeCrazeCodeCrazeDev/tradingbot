"""
SRE Reasoning Quality and Benchmark Tests
========================================
Measures precision, recall, false rejection rate, and confidence calibration
of the centralized Scientific Reasoning Engine (SRE).
"""

import pytest
import asyncio
import numpy as np
from typing import Dict, List, Any
from trading_bot.core_agent_system.scientific_reasoning.core import (
    ScientificReasoningEngine,
    ScientificHypothesis,
    HypothesisState
)

def calculate_precision_recall(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculates precision, recall, and false rejection rate from benchmark runs."""
    tp, fp, tn, fn = 0, 0, 0, 0

    for r in results:
        actual_true = r["ground_truth"]
        predicted_confirmed = r["predicted_state"] == HypothesisState.INSTITUTIONALIZED

        if actual_true and predicted_confirmed:
            tp += 1
        elif not actual_true and predicted_confirmed:
            fp += 1
        elif not actual_true and not predicted_confirmed:
            tn += 1
        elif actual_true and not predicted_confirmed:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    false_rejection_rate = fn / (tp + fn) if (tp + fn) > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "false_rejection_rate": false_rejection_rate
    }

def calculate_expected_calibration_error(results: List[Dict[str, Any]], num_bins: int = 5) -> float:
    """Calculates the Expected Calibration Error (ECE) for confidence predictions."""
    bin_boundaries = np.linspace(0, 1, num_bins + 1)
    ece = 0.0
    total_samples = len(results)

    for i in range(num_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        # Get samples in bin
        bin_indices = [
            j for j, r in enumerate(results)
            if bin_lower <= r["confidence"] < bin_upper
        ]

        if not bin_indices:
            continue

        bin_size = len(bin_indices)
        bin_accuracies = [results[idx]["ground_truth"] for idx in bin_indices]
        bin_confidences = [results[idx]["confidence"] for idx in bin_indices]

        accuracy = np.mean(bin_accuracies)
        confidence = np.mean(bin_confidences)

        ece += (bin_size / total_samples) * abs(accuracy - confidence)

    return ece

@pytest.mark.asyncio
async def test_sre_reasoning_quality_benchmarks():
    """Run a batch of simulated research scenarios to evaluate SRE precision, recall, and ECE."""
    sre = ScientificReasoningEngine()

    # We will simulate 30 hypothesis evaluation runs with known ground truths.
    # Group A: True signals (ground_truth = True) -> should have high validation score and multiple updates
    # Group B: Noise signals (ground_truth = False) -> should have low validation score and multiple updates
    benchmark_runs = []

    for i in range(30):
        ground_truth = (i % 2 == 0) # Symmetric split of signal vs. noise
        hid = await sre.observe({})
        hyp = sre.get_hypothesis(hid)

        # Assign simulated validation score corresponding to ground truth
        if ground_truth:
            hyp.prior = 0.5
            hyp.posterior = 0.5
            hyp.uncertainty = 0.1 # Decreased uncertainty on evidence

            # Run 4 successive experiment verification rounds (accumulation)
            for _ in range(4):
                hyp.validation_score = np.random.uniform(0.7, 0.95)
                hyp.prior = hyp.posterior
                await sre.bayesian_update(hid)
        else:
            hyp.prior = 0.5
            hyp.posterior = 0.5
            hyp.uncertainty = 0.1 # Decreased uncertainty on evidence

            # Run 4 successive experiment verification rounds (accumulation)
            for _ in range(4):
                hyp.validation_score = np.random.uniform(0.05, 0.35)
                hyp.prior = hyp.posterior
                await sre.bayesian_update(hid)

        # Retire after recursive updates complete
        await sre.retire_hypothesis(hid)

        benchmark_runs.append({
            "hypothesis_id": hid,
            "ground_truth": ground_truth,
            "predicted_state": hyp.state,
            "confidence": hyp.posterior
        })

    # Evaluate SRE reasoning quality metrics
    metrics = calculate_precision_recall(benchmark_runs)
    ece = calculate_expected_calibration_error(benchmark_runs)

    print(f"\nSRE Benchmark Metrics:")
    print(f"Precision: {metrics['precision']:.2%}")
    print(f"Recall: {metrics['recall']:.2%}")
    print(f"False Rejection Rate: {metrics['false_rejection_rate']:.2%}")
    print(f"Expected Calibration Error (ECE): {ece:.4f}")

    # Assert acceptable scientific reasoning thresholds
    assert metrics["precision"] >= 0.80 # Acceptable precision floor
    assert metrics["recall"] >= 0.80    # Acceptable recall floor
    assert metrics["false_rejection_rate"] <= 0.20
    assert ece <= 0.25 # Calibration error must be low
