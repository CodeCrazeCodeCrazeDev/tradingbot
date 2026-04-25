"""
Autonomous Research Lab - Layer 5
==================================

Continuous experimentation framework for self-improvement.

Experiment Types:
1. Feature Discovery: New data sources, transformations, embeddings
2. Indicator Discovery: Novel technical indicators, ML-generated alpha
3. Data Correlation: Cross-asset relationships, lead-lag analysis

Lifecycle: Hypothesis → Backtest → Paper Trade → Live Micro → Scale/Discard
"""

from .experiment_orchestrator import AutonomousResearchLab, ExperimentResult, ResearchHypothesis
from .feature_discovery import FeatureDiscoveryExperiment
from .indicator_discovery import IndicatorDiscoveryExperiment
from .data_correlation import DataCorrelationExperiment

__all__ = [
    'AutonomousResearchLab',
    'ExperimentResult',
    'ResearchHypothesis',
    'FeatureDiscoveryExperiment',
    'IndicatorDiscoveryExperiment',
    'DataCorrelationExperiment',
]
