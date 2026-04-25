"""Production golden path for AI trade decisions.

This package is the narrow, risk-first path that every strategy can adopt
before reaching backtest, paper, or live execution.
"""

from trading_bot.golden_path.monitoring import (
    ModelHealthReport,
    ModelPerformanceMonitor,
    PredictionSample,
)
from trading_bot.golden_path.agent_trap_defense import (
    AgentTrapDefenseConfig,
    AgentTrapFinding,
    AgentTrapReport,
    AgentTrapScanner,
    TrapCategory,
)
from trading_bot.golden_path.runner import GoldenPathTradingRunner, TradingMode
from trading_bot.golden_path.security_audit import SecretAuditFinding, audit_local_secrets
from trading_bot.golden_path.types import (
    AccountContext,
    MarketContext,
    ModelVote,
    RiskContext,
    TradeDecision,
    TradeIntent,
)
from trading_bot.golden_path.validator import DecisionGateConfig, TradeDecisionValidator

__all__ = [
    "AccountContext",
    "AgentTrapDefenseConfig",
    "AgentTrapFinding",
    "AgentTrapReport",
    "AgentTrapScanner",
    "DecisionGateConfig",
    "GoldenPathTradingRunner",
    "MarketContext",
    "ModelHealthReport",
    "ModelPerformanceMonitor",
    "ModelVote",
    "PredictionSample",
    "RiskContext",
    "SecretAuditFinding",
    "TradeDecision",
    "TradeDecisionValidator",
    "TradeIntent",
    "TradingMode",
    "TrapCategory",
    "audit_local_secrets",
]
