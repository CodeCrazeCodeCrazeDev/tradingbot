# Observability Module
# Unified monitoring, metrics, and system health tracking

from . import tracing
from . import metrics

from .unified_observability_hub import (
    UnifiedObservabilityHub,
    MetricType,
    MetricLevel,
    AlertSeverity,
    SystemHealth,
    MetricPoint,
    Alert,
    ComponentStatus,
    ObservabilityConfig,
)
from .pre_trade_gate import (
    PreTradeGateOrchestrator,
    GateType,
    GateResult,
    GateStatus,
    PreTradeCheck,
    GateConfig,
)
from .trade_quality_grader import (
    TradeQualityGrader,
    TradeGrade,
    QualityDimension,
    TradeScore,
    GradingConfig,
)
from .correlation_breakdown_detector import (
    CorrelationBreakdownDetector,
    BreakdownType,
    BreakdownSeverity,
    CorrelationAlert,
    PairCorrelation,
    BreakdownConfig,
)
from .strategy_kill_switch import (
    StrategyKillSwitchRegistry,
    KillReason,
    StrategyStatus,
    KillSwitch,
    StrategyHealth,
    KillSwitchConfig,
)

__all__ = [
    # Unified Observability Hub
    "UnifiedObservabilityHub",
    "MetricType",
    "MetricLevel",
    "AlertSeverity",
    "SystemHealth",
    "MetricPoint",
    "Alert",
    "ComponentStatus",
    "ObservabilityConfig",
    # Pre-Trade Gate
    "PreTradeGateOrchestrator",
    "GateType",
    "GateResult",
    "GateStatus",
    "PreTradeCheck",
    "GateConfig",
    # Trade Quality Grader
    "TradeQualityGrader",
    "TradeGrade",
    "QualityDimension",
    "TradeScore",
    "GradingConfig",
    # Correlation Breakdown Detector
    "CorrelationBreakdownDetector",
    "BreakdownType",
    "BreakdownSeverity",
    "CorrelationAlert",
    "PairCorrelation",
    "BreakdownConfig",
    # Strategy Kill Switch
    "StrategyKillSwitchRegistry",
    "KillReason",
    "StrategyStatus",
    "KillSwitch",
    "StrategyHealth",
    "KillSwitchConfig",
    # Tracing and Metrics
    "tracing",
    "metrics",
]
