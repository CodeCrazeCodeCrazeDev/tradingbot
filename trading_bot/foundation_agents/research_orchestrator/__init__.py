"""
Research Orchestrator - Self-Directed Research Loops
=====================================================

Implements autonomous research capabilities:
- Experiment Designer: Autonomous experiment design
- Methodology Evolver: Meta-learning over research methods
- Research Loop: Self-directed research cycles
- Validation Framework: Rigorous hypothesis testing
- Publication Generator: Generate research reports
"""

from .experiment_designer import ExperimentDesigner, Experiment, ExperimentType
from .methodology_evolver import MethodologyEvolver, ResearchMethod, MethodPerformance
from .research_loop import ResearchLoop, ResearchCycle, ResearchState
from .validation_framework import ValidationFramework, ValidationResult

__all__ = [
    "ExperimentDesigner",
    "Experiment",
    "ExperimentType",
    "MethodologyEvolver",
    "ResearchMethod",
    "MethodPerformance",
    "ResearchLoop",
    "ResearchCycle",
    "ResearchState",
    "ValidationFramework",
    "ValidationResult",
]
