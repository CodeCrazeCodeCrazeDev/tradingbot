"""
Brain Module
============================================================

Unified brain and intelligence hierarchy initialization.
"""

import logging

logger = logging.getLogger(__name__)

# Expose Base classes and Orchestrators
from .elite_brain import EliteBrainController
BrainOrchestrator = EliteBrainController

# Core components
from .tier_structure import (
    AlphaBrain,
    EliteBrainSignal,
    SignalOutput,
    MarketStateVector,
    OrderFlowIntelligence,
    MarketGeometryModel,
    RegimeContextVector,
    SentimentVector,
    MacroContext,
    RiskParameters,
    ExecutionIntelligence,
)

# Analytical Tiers (Tiers 1-9)
from .tier1_technical import Tier1TechnicalAnalysis
from .tier2_orderflow import Tier2OrderFlowIntelligence
from .tier3_structure import Tier3MarketStructure
from .tier4_regime import Tier4RegimeDetection
from .tier5_sentiment import Tier5SentimentAnalysis
from .tier6_macro import Tier6MacroAnalysis
from .tier7_risk import Tier7RiskManagement
from .tier8_execution import Tier8ExecutionIntelligence
from .tier9_metalearning import Tier9MetaLearning

# Optional components with fallback imports
try:
    from .brain_architecture import EliteBrain, BrainDecision
except ImportError:
    EliteBrain = None
    class BrainDecision: pass

try:
    from .adaptive_integration import AdaptiveIntegrationSystem
except ImportError:
    AdaptiveIntegrationSystem = None

try:
    from .alphaalgo_2_0 import SystemCapability
except ImportError:
    SystemCapability = None

try:
    from .alphaalgo_2_0_system import Alphaalgo20System
except ImportError:
    Alphaalgo20System = None

try:
    from .brain_trader import BrainTrader
except ImportError:
    BrainTrader = None

try:
    from .central_controller import CentralController
except ImportError:
    CentralController = None

try:
    from .mt5_brain_trader import MT5BrainTrader
except ImportError:
    MT5BrainTrader = None

try:
    from .tier9_metalearning import MetaLearningSystem
except ImportError:
    MetaLearningSystem = None


__all__ = [
    'AdaptiveIntegrationSystem',
    'AlphaBrain',
    'Alphaalgo20System',
    'BrainDecision',
    'BrainTrader',
    'CentralController',
    'EliteBrain',
    'EliteBrainController',
    'BrainOrchestrator',
    'EliteBrainSignal',
    'MT5BrainTrader',
    'MetaLearningSystem',
    'SystemCapability',
    # Analytical Tiers 1-9
    'Tier1TechnicalAnalysis',
    'Tier2OrderFlowIntelligence',
    'Tier3MarketStructure',
    'Tier4RegimeDetection',
    'Tier5SentimentAnalysis',
    'Tier6MacroAnalysis',
    'Tier7RiskManagement',
    'Tier8ExecutionIntelligence',
    'Tier9MetaLearning',
]
