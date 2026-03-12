"""
Innovative Decision Layer - 110 Decision-Making Concepts

This module implements 110 innovative decision-making concepts for trading,
organized into 11 categories with 10 concepts each.

CATEGORIES:
1. Cognitive Decision Patterns (1-10)
2. Probabilistic Decision Models (11-20)
3. Behavioral Finance Decisions (21-30)
4. Game Theory Decisions (31-40)
5. Temporal Decision Intelligence (41-50)
6. Risk-Aware Decisions (51-60)
7. Market Microstructure Decisions (61-70)
8. Adaptive Learning Decisions (71-80)
9. Multi-Agent Decision Systems (81-90)
10. Meta-Decision Intelligence (91-100)
11. Quantitative & Statistical Edge (101-110)

Author: AlphaAlgo Innovation Lab
"""

from .core_types import (
    DecisionConcept,
    DecisionContext,
    DecisionResult,
    AggregatedDecision,
    DecisionCategory,
    DecisionAction,
    DecisionUrgency,
)

from .innovative_decision_engine import (
    InnovativeDecisionEngine,
    create_decision_engine,
    quick_decide,
)

# Integration, Persistence, and Analytics
from .decision_integration_bridge import (
    DecisionLayerBridge,
    ParallelDecisionBridge,
    TradingSignal,
    create_decision_bridge,
    quick_analyze,
)

from .decision_persistence import DecisionPersistence

from .decision_analytics import (
    DecisionAnalytics,
    ConceptPerformanceTracker,
)

# Import all concept classes for direct access
from .concepts_1_cognitive import COGNITIVE_CONCEPTS
from .concepts_2_probabilistic import PROBABILISTIC_CONCEPTS
from .concepts_3_behavioral import BEHAVIORAL_CONCEPTS
from .concepts_4_game_theory import GAME_THEORY_CONCEPTS
from .concepts_5_temporal import TEMPORAL_CONCEPTS
from .concepts_6_risk import RISK_CONCEPTS
from .concepts_7_microstructure import MICROSTRUCTURE_CONCEPTS
from .concepts_8_adaptive import ADAPTIVE_CONCEPTS
from .concepts_9_multiagent import MULTIAGENT_CONCEPTS
from .concepts_10_meta import META_CONCEPTS
from .concepts_11_quantitative_edge import QUANTITATIVE_EDGE_CONCEPTS

# All 110 concepts combined
ALL_CONCEPTS = (
    COGNITIVE_CONCEPTS +
    PROBABILISTIC_CONCEPTS +
    BEHAVIORAL_CONCEPTS +
    GAME_THEORY_CONCEPTS +
    TEMPORAL_CONCEPTS +
    RISK_CONCEPTS +
    MICROSTRUCTURE_CONCEPTS +
    ADAPTIVE_CONCEPTS +
    MULTIAGENT_CONCEPTS +
    META_CONCEPTS +
    QUANTITATIVE_EDGE_CONCEPTS
)

__all__ = [
    # Core types
    'DecisionConcept',
    'DecisionContext',
    'DecisionResult',
    'AggregatedDecision',
    'DecisionCategory',
    'DecisionAction',
    'DecisionUrgency',
    # Engine
    'InnovativeDecisionEngine',
    'create_decision_engine',
    'quick_decide',
    # Integration Bridge
    'DecisionLayerBridge',
    'ParallelDecisionBridge',
    'TradingSignal',
    'create_decision_bridge',
    'quick_analyze',
    # Persistence
    'DecisionPersistence',
    # Analytics
    'DecisionAnalytics',
    'ConceptPerformanceTracker',
    # Concept lists
    'ALL_CONCEPTS',
    'COGNITIVE_CONCEPTS',
    'PROBABILISTIC_CONCEPTS',
    'BEHAVIORAL_CONCEPTS',
    'GAME_THEORY_CONCEPTS',
    'TEMPORAL_CONCEPTS',
    'RISK_CONCEPTS',
    'MICROSTRUCTURE_CONCEPTS',
    'ADAPTIVE_CONCEPTS',
    'MULTIAGENT_CONCEPTS',
    'META_CONCEPTS',
    'QUANTITATIVE_EDGE_CONCEPTS',
]
