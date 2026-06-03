"""
AI module - MetaTrader Alpha Superintelligence Hub (MTASH).

This module unifies all autonomous intelligence systems into a single hub.
"""

from .autonomous_tuner import (
    ParameterType,
    Parameter,
    AutonomousTuner,
    GeneticOptimizer,
    BayesianOptimizer,
)
from .self_optimizer import (
    PerformanceMetrics,
    OptimizationResult,
    AIOptimizer,
    ModelOptimizer,
)
from .hub import (
    MTASH,
    create_hub,
)

__all__ = [
    # MetaTrader Alpha Superintelligence Hub
    "MTASH",
    "create_hub",
    # Autonomous Tuner
    "ParameterType",
    "Parameter",
    "AutonomousTuner",
    "GeneticOptimizer",
    "BayesianOptimizer",
    # Self Optimizer
    "PerformanceMetrics",
    "OptimizationResult",
    "AIOptimizer",
    "ModelOptimizer",
]

# Alias for legacy code compatibility
AIOrchestrator = MTASH
