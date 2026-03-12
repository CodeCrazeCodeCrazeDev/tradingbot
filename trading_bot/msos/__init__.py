"""
Msos Module
============================================================

Meta-System Oversight System (MSOS) - Capital Preservation First
"""

# anti_overreaction
try:
    from .anti_overreaction import AntiOverreactionEngine
except ImportError:
    AntiOverreactionEngine = None

# assumption_engine
try:
    from .assumption_engine import AssumptionEngine
except ImportError:
    AssumptionEngine = None

# capital_governor
try:
    from .capital_governor import CapitalGovernor
except ImportError:
    CapitalGovernor = None

# core
try:
    from .core import MSOSCore, SystemHierarchy
except ImportError:
    MSOSCore = None
    SystemHierarchy = None

# data_adversarial
try:
    from .data_adversarial import DataAdversarialDefense
except ImportError:
    DataAdversarialDefense = None

# entropy_budget
try:
    from .entropy_budget import EntropyBudgetManager
except ImportError:
    EntropyBudgetManager = None

# execution_reality
try:
    from .execution_reality import ExecutionRealityChecker
except ImportError:
    ExecutionRealityChecker = None

# learning_firewall
try:
    from .learning_firewall import LearningFirewall
except ImportError:
    LearningFirewall = None

# loss_monitor
try:
    from .loss_monitor import LossMonitor
except ImportError:
    LossMonitor = None

# market_tradability
try:
    from .market_tradability import MarketTradabilityGate
except ImportError:
    MarketTradabilityGate = None

# orchestrator
try:
    from .orchestrator import (
        MSOSOrchestrator,
        OrchestratorConfig,
        OrchestratorResult,
        SystemMode,
    )
except ImportError:
    MSOSOrchestrator = None
    OrchestratorConfig = None
    OrchestratorResult = None
    SystemMode = None

# post_mortem
try:
    from .post_mortem import PostMortemEngine
except ImportError:
    PostMortemEngine = None

# quant_factory
try:
    from .quant_factory import QuantModelFactory
except ImportError:
    QuantModelFactory = None

# regime_instability
try:
    from .regime_instability import RegimeInstabilityDetector
except ImportError:
    RegimeInstabilityDetector = None

# signal_semantics
try:
    from .signal_semantics import SignalSemanticMonitor
except ImportError:
    SignalSemanticMonitor = None

# time_risk
try:
    from .time_risk import TimeRiskManager
except ImportError:
    TimeRiskManager = None

__all__ = [
    'AntiOverreactionEngine',
    'AssumptionEngine',
    'CapitalGovernor',
    'DataAdversarialDefense',
    'EntropyBudgetManager',
    'ExecutionRealityChecker',
    'LearningFirewall',
    'LossMonitor',
    'MarketTradabilityGate',
    'MSOSCore',
    'MSOSOrchestrator',
    'OrchestratorConfig',
    'OrchestratorResult',
    'PostMortemEngine',
    'QuantModelFactory',
    'RegimeInstabilityDetector',
    'SignalSemanticMonitor',
    'SystemHierarchy',
    'SystemMode',
    'TimeRiskManager',
]
