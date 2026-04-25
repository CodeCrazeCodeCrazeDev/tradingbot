"""
Cognitive Operating System (COS)
=================================

The Externalized Intelligence Core of the trading bot.

A closed recurrent recursive loop that:
    1. STRUCTURES knowledge  → Cognition Store
    2. EVALUATES ideas       → Decision Support
    3. SUPPORTS decisions    → Calibrated Simulation
    4. FEEDS execution       → Decision Router
    5. EVOLVES with feedback → Reality Calibration Loop

Loop Architecture:
    ┌──────────────────────────────────────────────────┐
    │              COGNITIVE OPERATING SYSTEM           │
    │                                                    │
    │  ┌─────────┐   ┌──────────┐   ┌───────────────┐ │
    │  │ COGNITION│──▶│ SIMULATE │──▶│   DECIDE      │ │
    │  │  STORE   │   │ (DREAM)  │   │  (SUPPORT)    │ │
    │  └────▲─────┘   └─────┬────┘   └───────┬───────┘ │
    │       │               │                 │         │
    │       │               │                 ▼         │
    │       │        ┌──────▼──────┐   ┌───────────┐   │
    │       │        │  VALIDATE   │◀──│  EXECUTE   │   │
    │       │        │  (REALITY)  │   │  (FEED)    │   │
    │       │        └──────┬──────┘   └───────────┘   │
    │       │               │                          │
    │       └───────────────┘  ← CORRECT MODEL         │
    │                                                    │
    └──────────────────────────────────────────────────┘

The loop is:
    - CLOSED:    Every output feeds back as input
    - RECURRENT: State persists across cycles
    - RECURSIVE: Insights about the loop improve the loop itself

Integration Points:
    - trading_bot.cognitive_architecture  → perception layer
    - trading_bot.world_model             → simulation engines
    - trading_bot.decision_layer          → decision concepts
    - trading_bot.feedback                → reality signal
    - trading_bot.brain                   → execution layer
"""

from .types import (
    KnowledgeNode,
    Idea,
    SimulationResult,
    DecisionTrace,
    RealityCheck,
    CalibrationDelta,
    COSCycleReport,
    COSConfig,
    KnowledgeCategory,
    IdeaStatus,
    DecisionConfidence,
    SimulationFidelity,
)
from .cognition_store import CognitionStore
from .simulation_engine import CalibratedSimulationEngine
from .decision_support import DecisionSupportSystem
from .feedback_loop import RealityCalibrationLoop
from .cos_core import CognitiveOperatingSystem

__all__ = [
    "CognitiveOperatingSystem",
    "CognitionStore",
    "CalibratedSimulationEngine",
    "DecisionSupportSystem",
    "RealityCalibrationLoop",
    "KnowledgeNode",
    "Idea",
    "SimulationResult",
    "DecisionTrace",
    "RealityCheck",
    "CalibrationDelta",
    "COSCycleReport",
    "COSConfig",
    "KnowledgeCategory",
    "IdeaStatus",
    "DecisionConfidence",
    "SimulationFidelity",
]
