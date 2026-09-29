"""
Curiosity Engine - Autonomous Research Discovery
=================================================

Implements curiosity-driven exploration:
- Anomaly Detector: Multi-dimensional anomaly detection
- Surprise Scorer: Information-theoretic surprise metrics
- Hypothesis Generator: Auto-generate research questions
- Interestingness Ranker: Prioritize research directions
- Counterfactual Reasoner: "What-if" scenario analysis
- Research Agenda: Self-directed research planning
"""

from .anomaly_detector import AnomalyDetector, Anomaly, AnomalyType
from .surprise_scorer import SurpriseScorer, SurpriseMetric
from .hypothesis_generator import HypothesisGenerator, Hypothesis, HypothesisType
from .interestingness_ranker import InterestingnessRanker, ResearchPriority
from .counterfactual_reasoner import CounterfactualReasoner, Counterfactual
from .research_agenda import ResearchAgenda, ResearchQuestion

__all__ = [
    "AnomalyDetector",
    "Anomaly",
    "AnomalyType",
    "SurpriseScorer",
    "SurpriseMetric",
    "HypothesisGenerator",
    "Hypothesis",
    "HypothesisType",
    "InterestingnessRanker",
    "ResearchPriority",
    "CounterfactualReasoner",
    "Counterfactual",
    "ResearchAgenda",
    "ResearchQuestion",
]
