"""
Rigorous unit tests validating the epistemological Research Computer framework.
Verifies Epistemic CPU cycles execution, descriptive Research Compilers parsing,
Curiosity-based Schedulers, Cognitive Memory, and multi-variable Epistemic Objective scores.
"""

import pytest
import pandas as pd
import numpy as np

from trading_bot.research.research_computer import (
    EpistemicInstruction,
    CPUCycleTrace,
    EpistemicMetrics,
    EpistemicObjectiveFunction,
    CompiledPipeline,
    ResearchCompiler,
    ResearchMemory,
    ResearchScheduler,
    ResearchCPU,
    QuantitativeResearchComputer
)


def test_epistemic_objective_function():
    """Verifies multivariable scoring prioritizes quality and reproducibility over raw Sharpe."""
    obj_fun = EpistemicObjectiveFunction()

    # Model A: High Quality, High Reproducibility, Modest Sharpe -> High score
    metrics_a = EpistemicMetrics(
        knowledge_quality=0.90,
        reproducibility=1.0,
        robustness=0.85,
        capital_efficiency=0.90,
        scientific_throughput=0.80,
        operational_reliability=0.95,
        risk_adjusted_return=1.85  # Modest Sharpe
    )
    score_a = obj_fun.compute_epistemic_score(metrics_a)

    # Model B: Low Quality, Low Reproducibility, Outstanding Overfit Sharpe -> Low score
    metrics_b = EpistemicMetrics(
        knowledge_quality=0.20,
        reproducibility=0.10,
        robustness=0.30,
        capital_efficiency=0.50,
        scientific_throughput=0.80,
        operational_reliability=0.90,
        risk_adjusted_return=4.20  # Overfit Sharpe
    )
    score_b = obj_fun.compute_epistemic_score(metrics_b)

    assert score_a > score_b


def test_research_compiler_descriptive_science():
    """Verifies that the compiler translates descriptive statements into structured pipelines."""
    compiler = ResearchCompiler()

    # Compile a standard book imbalance hypothesis
    pipeline = compiler.compile_hypothesis(
        "Momentum persists when order book imbalance exceeds 0.25 and volatility is low."
    )

    assert "Raw_Bar_Feed_M1" in pipeline.required_datasets
    assert "Order_Book_Tick_L2_Feed" in pipeline.required_datasets
    assert "order_book_imbalance" in pipeline.features_to_generate
    assert "Spearman_IC" in pipeline.statistical_tests
    assert "Independent_Peer_Review" in pipeline.validation_promotion_gates


def test_research_memory_cognitive_logs():
    """Verifies that ResearchMemory logs experiment histories, failures, and contradictions."""
    memory = ResearchMemory()

    metrics = EpistemicMetrics(knowledge_quality=0.8, reproducibility=1.0)

    # Log 1 successful experiment
    memory.log_experiment_result("exp-01", {"lr": 0.01}, metrics, passed_validation=True)
    assert memory.failed_experiments_count == 0
    assert len(memory.experiment_database) == 1

    # Log 1 failed experiment
    memory.log_experiment_result("exp-02", {"lr": 0.1}, metrics, passed_validation=False)
    assert memory.failed_experiments_count == 1
    assert len(memory.experiment_database) == 2

    # Log contradiction
    memory.log_contradiction("EMA crosses predict long-term trend", "evidence-ema-fail-2025")
    assert len(memory.contradictions_logged) == 1


def test_curiosity_based_scheduler():
    """Verifies that the Research Scheduler prioritizes queues based on expected information gain."""
    scheduler = ResearchScheduler()

    candidates = [
        {"experiment_id": "exp-cheap-indicator", "expected_information_gain": 0.12},
        {"experiment_id": "exp-deep-microstructure", "expected_information_gain": 0.85},
        {"experiment_id": "exp-macro-news", "expected_information_gain": 0.44}
    ]

    ordered = scheduler.schedule_experiments(candidates)

    # Highly informative experiment must be scheduled first in the queue
    assert ordered[0]["experiment_id"] == "exp-deep-microstructure"
    assert ordered[1]["experiment_id"] == "exp-macro-news"
    assert ordered[2]["experiment_id"] == "exp-cheap-indicator"


def test_quantitative_research_computer_unification():
    """Verifies Research CPU executions, cycle increments, and complete system booting."""
    computer = QuantitativeResearchComputer()
    assert computer is not None

    # Execute a CPU cycle: HYPOTHESIZE
    trace = computer.cpu.execute(
        instruction=EpistemicInstruction.HYPOTHESIZE,
        input_id="question-obi-1"
    )

    assert trace.instruction == EpistemicInstruction.HYPOTHESIZE
    assert trace.input_object_id == "question-obi-1"
    assert len(trace.output_object_id) > 0
    assert computer.cpu.cycle_count == 1
