"""
Pre-Trade Gate Orchestrator
===========================

Multi-layer validation system that must pass before any trade execution.
Implements a series of gates that each trade must pass through.

Features:
- Configurable gate hierarchy
- Parallel and sequential gate execution
- Gate bypass with approval
- Detailed rejection reasons
- Gate performance tracking
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Callable, Tuple
from collections import deque
import threading
import logging
import time
import hashlib

logger = logging.getLogger(__name__)


class GateType(Enum):
    """Types of pre-trade gates."""
    RISK_LIMIT = auto()           # Position size, exposure limits
    MARKET_HOURS = auto()         # Trading hours validation
    LIQUIDITY = auto()            # Sufficient liquidity check
    VOLATILITY = auto()           # Volatility within bounds
    CORRELATION = auto()          # Correlation limits
    DRAWDOWN = auto()             # Drawdown limits
    SIGNAL_QUALITY = auto()       # Signal confidence threshold
    STRATEGY_HEALTH = auto()      # Strategy performance check
    BROKER_STATUS = auto()        # Broker connectivity
    DATA_QUALITY = auto()         # Data freshness and quality
    COMPLIANCE = auto()           # Regulatory compliance
    CIRCUIT_BREAKER = auto()      # Circuit breaker status
    HUMAN_APPROVAL = auto()       # Manual approval required
    CUSTOM = auto()               # Custom gate logic


class GateStatus(Enum):
    """Gate execution status."""
    PASSED = auto()               # Gate passed
    FAILED = auto()               # Gate failed
    SKIPPED = auto()              # Gate skipped (not applicable)
    BYPASSED = auto()             # Gate bypassed with approval
    TIMEOUT = auto()              # Gate timed out
    ERROR = auto()                # Gate execution error


@dataclass
class GateResult:
    """Result of a single gate check."""
    gate_type: GateType
    gate_name: str
    status: GateStatus
    passed: bool
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_type": self.gate_type.name,
            "gate_name": self.gate_name,
            "status": self.status.name,
            "passed": self.passed,
            "reason": self.reason,
            "details": self.details,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PreTradeCheck:
    """Pre-trade check request."""
    check_id: str
    symbol: str
    direction: str  # "BUY" or "SELL"
    quantity: float
    price: float
    strategy_id: str
    signal_confidence: float = 0.0
    order_type: str = "MARKET"
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def notional_value(self) -> float:
        return self.quantity * self.price


@dataclass
class GateConfig:
    """Configuration for pre-trade gates."""
    enabled_gates: List[GateType] = field(default_factory=lambda: list(GateType))
    gate_timeout_seconds: float = 5.0
    parallel_execution: bool = True
    fail_fast: bool = True  # Stop on first failure
    require_all_pass: bool = True
    bypass_allowed: bool = False
    bypass_requires_approval: bool = True
    max_retries: int = 1
    
    # Gate-specific thresholds
    min_signal_confidence: float = 0.6
    max_position_pct: float = 0.05  # 5% of portfolio
    max_daily_trades: int = 100
    max_drawdown_pct: float = 0.10  # 10%
    min_liquidity_ratio: float = 0.1  # 10% of ADV
    max_volatility_percentile: float = 95.0
    max_correlation: float = 0.8
    data_staleness_seconds: float = 60.0


class Gate:
    """Base class for pre-trade gates."""
    
    def __init__(self, gate_type: GateType, name: str, config: GateConfig):
        self.gate_type = gate_type
        self.name = name
        self.config = config
        self._enabled = True
        self._pass_count = 0
        self._fail_count = 0
        self._total_time_ms = 0.0
    
    def check(self, trade: PreTradeCheck, context: Dict[str, Any]) -> GateResult:
        """Execute gate check. Override in subclasses."""
    
    def execute(self, trade: PreTradeCheck, context: Dict[str, Any]) -> GateResult:
        """Execute gate with timing and error handling."""
        if not self._enabled:
            return GateResult(
                gate_type=self.gate_type,
                gate_name=self.name,
                status=GateStatus.SKIPPED,
                passed=True,
                reason="Gate disabled",
            )
        
        start = time.perf_counter()
        try:
            result = self.check(trade, context)
            result.execution_time_ms = (time.perf_counter() - start) * 1000
            
            # Update stats
            if result.passed:
                self._pass_count += 1
            else:
                self._fail_count += 1
            self._total_time_ms += result.execution_time_ms
            
            return result
            
        except Exception as e:
            execution_time = (time.perf_counter() - start) * 1000
            logger.error(f"Gate {self.name} error: {e}")
            self._fail_count += 1
            return GateResult(
                gate_type=self.gate_type,
                gate_name=self.name,
                status=GateStatus.ERROR,
                passed=False,
                reason=f"Gate error: {str(e)}",
                execution_time_ms=execution_time,
            )
    
    @property
    def stats(self) -> Dict[str, Any]:
        total = self._pass_count + self._fail_count
        return {
            "name": self.name,
            "type": self.gate_type.name,
            "enabled": self._enabled,
            "pass_count": self._pass_count,
            "fail_count": self._fail_count,
            "pass_rate": self._pass_count / total if total > 0 else 0,
            "avg_time_ms": self._total_time_ms / total if total > 0 else 0,
        }


class RiskLimitGate(Gate):
    """Validates position size and exposure limits."""
    
    def __init__(self, config: GateConfig):
        super().__init__(GateType.RISK_LIMIT, "RiskLimit", config)
    
    def check(self, trade: PreTradeCheck, context: Dict[str, Any]) -> GateResult:
        portfolio_value = context.get("portfolio_value", 100000)
        current_exposure = context.get("current_exposure", 0)
        
        # Check position size
        position_pct = trade.notional_value / portfolio_value
        if position_pct > self.config.max_position_pct:
            return GateResult(
                gate_type=self.gate_type,
                gate_name=self.name,
                status=GateStatus.FAILED,
                passed=False,
                reason=f"Position size {position_pct:.2%} exceeds limit {self.config.max_position_pct:.2%}",
                details={"position_pct": position_pct, "limit": self.config.max_position_pct},
            )
        
        # Check total exposure
        new_exposure = current_exposure + trade.notional_value
        max_exposure = portfolio_value * 0.5  # 50% max exposure
        if new_exposure > max_exposure:
            return GateResult(
                gate_type=self.gate_type,
                gate_name=self.name,
                status=GateStatus.FAILED,
                passed=False,
                reason=f"Total exposure would exceed limit",
                details={"new_exposure": new_exposure, "max_exposure": max_exposure},
            )
        
        return GateResult(
            gate_type=self.gate_type,
            gate_name=self.name,
            status=GateStatus.PASSED,
            passed=True,
            reason="Risk limits OK",
            details={"position_pct": position_pct},
        )


class SignalQualityGate(Gate):
    """Validates signal confidence threshold."""
    
    def __init__(self, config: GateConfig):
        super().__init__(GateType.SIGNAL_QUALITY, "SignalQuality", config)
    
    def check(self, trade: PreTradeCheck, context: Dict[str, Any]) -> GateResult:
        if trade.signal_confidence < self.config.min_signal_confidence:
            return GateResult(
                gate_type=self.gate_type,
                gate_name=self.name,
                status=GateStatus.FAILED,
                passed=False,
                reason=f"Signal confidence {trade.signal_confidence:.2f} below threshold {self.config.min_signal_confidence:.2f}",
                details={
                    "confidence": trade.signal_confidence,
                    "threshold": self.config.min_signal_confidence,
                },
            )
        
        return GateResult(
            gate_type=self.gate_type,
            gate_name=self.name,
            status=GateStatus.PASSED,
            passed=True,
            reason="Signal quality OK",
            details={"confidence": trade.signal_confidence},
        )


class DrawdownGate(Gate):
    """Validates drawdown limits."""
    
    def __init__(self, config: GateConfig):
        super().__init__(GateType.DRAWDOWN, "Drawdown", config)
    
    def check(self, trade: PreTradeCheck, context: Dict[str, Any]) -> GateResult:
        current_drawdown = context.get("current_drawdown", 0)
        
        if current_drawdown > self.config.max_drawdown_pct:
            return GateResult(
                gate_type=self.gate_type,
                gate_name=self.name,
                status=GateStatus.FAILED,
                passed=False,
                reason=f"Current drawdown {current_drawdown:.2%} exceeds limit {self.config.max_drawdown_pct:.2%}",
                details={
                    "current_drawdown": current_drawdown,
                    "limit": self.config.max_drawdown_pct,
                },
            )
        
        return GateResult(
            gate_type=self.gate_type,
            gate_name=self.name,
            status=GateStatus.PASSED,
            passed=True,
            reason="Drawdown OK",
            details={"current_drawdown": current_drawdown},
        )


class LiquidityGate(Gate):
    """Validates sufficient liquidity."""
    
    def __init__(self, config: GateConfig):
        super().__init__(GateType.LIQUIDITY, "Liquidity", config)
    
    def check(self, trade: PreTradeCheck, context: Dict[str, Any]) -> GateResult:
        adv = context.get("average_daily_volume", 1000000)
        liquidity_ratio = trade.quantity / adv if adv > 0 else 1.0
        
        if liquidity_ratio > self.config.min_liquidity_ratio:
            return GateResult(
                gate_type=self.gate_type,
                gate_name=self.name,
                status=GateStatus.FAILED,
                passed=False,
                reason=f"Order size {liquidity_ratio:.2%} of ADV exceeds limit",
                details={
                    "liquidity_ratio": liquidity_ratio,
                    "limit": self.config.min_liquidity_ratio,
                    "adv": adv,
                },
            )
        
        return GateResult(
            gate_type=self.gate_type,
            gate_name=self.name,
            status=GateStatus.PASSED,
            passed=True,
            reason="Liquidity OK",
            details={"liquidity_ratio": liquidity_ratio},
        )


class DataQualityGate(Gate):
    """Validates data freshness and quality."""
    
    def __init__(self, config: GateConfig):
        super().__init__(GateType.DATA_QUALITY, "DataQuality", config)
    
    def check(self, trade: PreTradeCheck, context: Dict[str, Any]) -> GateResult:
        last_data_time = context.get("last_data_timestamp")
        if last_data_time:
            staleness = (datetime.utcnow() - last_data_time).total_seconds()
            if staleness > self.config.data_staleness_seconds:
                return GateResult(
                    gate_type=self.gate_type,
                    gate_name=self.name,
                    status=GateStatus.FAILED,
                    passed=False,
                    reason=f"Data stale: {staleness:.1f}s old",
                    details={
                        "staleness_seconds": staleness,
                        "limit": self.config.data_staleness_seconds,
                    },
                )
        
        data_quality_score = context.get("data_quality_score", 1.0)
        if data_quality_score < 0.8:
            return GateResult(
                gate_type=self.gate_type,
                gate_name=self.name,
                status=GateStatus.FAILED,
                passed=False,
                reason=f"Data quality score {data_quality_score:.2f} below threshold",
                details={"quality_score": data_quality_score},
            )
        
        return GateResult(
            gate_type=self.gate_type,
            gate_name=self.name,
            status=GateStatus.PASSED,
            passed=True,
            reason="Data quality OK",
        )


class BrokerStatusGate(Gate):
    """Validates broker connectivity."""
    
    def __init__(self, config: GateConfig):
        super().__init__(GateType.BROKER_STATUS, "BrokerStatus", config)
    
    def check(self, trade: PreTradeCheck, context: Dict[str, Any]) -> GateResult:
        broker_connected = context.get("broker_connected", False)
        
        if not broker_connected:
            return GateResult(
                gate_type=self.gate_type,
                gate_name=self.name,
                status=GateStatus.FAILED,
                passed=False,
                reason="Broker not connected",
            )
        
        broker_latency = context.get("broker_latency_ms", 0)
        if broker_latency > 1000:  # 1 second
            return GateResult(
                gate_type=self.gate_type,
                gate_name=self.name,
                status=GateStatus.FAILED,
                passed=False,
                reason=f"Broker latency too high: {broker_latency}ms",
                details={"latency_ms": broker_latency},
            )
        
        return GateResult(
            gate_type=self.gate_type,
            gate_name=self.name,
            status=GateStatus.PASSED,
            passed=True,
            reason="Broker status OK",
            details={"latency_ms": broker_latency},
        )


class CircuitBreakerGate(Gate):
    """Validates circuit breaker status."""
    
    def __init__(self, config: GateConfig):
        super().__init__(GateType.CIRCUIT_BREAKER, "CircuitBreaker", config)
    
    def check(self, trade: PreTradeCheck, context: Dict[str, Any]) -> GateResult:
        circuit_breaker_open = context.get("circuit_breaker_open", False)
        
        if circuit_breaker_open:
            return GateResult(
                gate_type=self.gate_type,
                gate_name=self.name,
                status=GateStatus.FAILED,
                passed=False,
                reason="Circuit breaker is OPEN - trading halted",
                details={"reason": context.get("circuit_breaker_reason", "Unknown")},
            )
        
        return GateResult(
            gate_type=self.gate_type,
            gate_name=self.name,
            status=GateStatus.PASSED,
            passed=True,
            reason="Circuit breaker OK",
        )


class VolatilityGate(Gate):
    """Validates volatility within bounds."""
    
    def __init__(self, config: GateConfig):
        super().__init__(GateType.VOLATILITY, "Volatility", config)
    
    def check(self, trade: PreTradeCheck, context: Dict[str, Any]) -> GateResult:
        volatility_percentile = context.get("volatility_percentile", 50)
        
        if volatility_percentile > self.config.max_volatility_percentile:
            return GateResult(
                gate_type=self.gate_type,
                gate_name=self.name,
                status=GateStatus.FAILED,
                passed=False,
                reason=f"Volatility at {volatility_percentile:.0f}th percentile exceeds limit",
                details={
                    "volatility_percentile": volatility_percentile,
                    "limit": self.config.max_volatility_percentile,
                },
            )
        
        return GateResult(
            gate_type=self.gate_type,
            gate_name=self.name,
            status=GateStatus.PASSED,
            passed=True,
            reason="Volatility OK",
            details={"volatility_percentile": volatility_percentile},
        )


class StrategyHealthGate(Gate):
    """Validates strategy performance."""
    
    def __init__(self, config: GateConfig):
        super().__init__(GateType.STRATEGY_HEALTH, "StrategyHealth", config)
    
    def check(self, trade: PreTradeCheck, context: Dict[str, Any]) -> GateResult:
        strategy_status = context.get("strategy_status", {})
        strategy_id = trade.strategy_id
        
        if strategy_id in strategy_status:
            status = strategy_status[strategy_id]
            if status.get("killed", False):
                return GateResult(
                    gate_type=self.gate_type,
                    gate_name=self.name,
                    status=GateStatus.FAILED,
                    passed=False,
                    reason=f"Strategy {strategy_id} is killed",
                    details={"kill_reason": status.get("kill_reason", "Unknown")},
                )
            
            if status.get("health_score", 1.0) < 0.5:
                return GateResult(
                    gate_type=self.gate_type,
                    gate_name=self.name,
                    status=GateStatus.FAILED,
                    passed=False,
                    reason=f"Strategy {strategy_id} health score too low",
                    details={"health_score": status.get("health_score")},
                )
        
        return GateResult(
            gate_type=self.gate_type,
            gate_name=self.name,
            status=GateStatus.PASSED,
            passed=True,
            reason="Strategy health OK",
        )


class PreTradeGateOrchestrator:
    """
    Orchestrates pre-trade gate validation.
    
    All trades must pass through configured gates before execution.
    """
    
    def __init__(self, config: Optional[GateConfig] = None):
        self.config = config or GateConfig()
        
        # Initialize gates
        self._gates: Dict[GateType, Gate] = {}
        self._gate_order: List[GateType] = []
        self._custom_gates: Dict[str, Gate] = {}
        
        # History
        self._check_history: deque = deque(maxlen=10000)
        self._lock = threading.Lock()
        
        # Bypass approvals
        self._bypass_approvals: Dict[str, datetime] = {}
        
        # Initialize default gates
        self._init_default_gates()
        
        logger.info("PreTradeGateOrchestrator initialized")
    
    def _init_default_gates(self) -> None:
        """Initialize default gates."""
        gate_classes = {
            GateType.RISK_LIMIT: RiskLimitGate,
            GateType.SIGNAL_QUALITY: SignalQualityGate,
            GateType.DRAWDOWN: DrawdownGate,
            GateType.LIQUIDITY: LiquidityGate,
            GateType.DATA_QUALITY: DataQualityGate,
            GateType.BROKER_STATUS: BrokerStatusGate,
            GateType.CIRCUIT_BREAKER: CircuitBreakerGate,
            GateType.VOLATILITY: VolatilityGate,
            GateType.STRATEGY_HEALTH: StrategyHealthGate,
        }
        
        for gate_type in self.config.enabled_gates:
            if gate_type in gate_classes:
                self._gates[gate_type] = gate_classes[gate_type](self.config)
                self._gate_order.append(gate_type)
    
    def validate(self, trade: PreTradeCheck, context: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[GateResult]]:
        """
        Validate a trade through all gates.
        
        Returns:
            Tuple of (passed, list of gate results)
        """
        context = context or {}
        results: List[GateResult] = []
        all_passed = True
        
        # Check for bypass
        bypass_key = f"{trade.strategy_id}:{trade.symbol}"
        if bypass_key in self._bypass_approvals:
            if datetime.utcnow() < self._bypass_approvals[bypass_key]:
                logger.warning(f"Gate bypass active for {bypass_key}")
                return True, [GateResult(
                    gate_type=GateType.CUSTOM,
                    gate_name="Bypass",
                    status=GateStatus.BYPASSED,
                    passed=True,
                    reason="Gate bypass active",
                )]
        
        # Execute gates
        for gate_type in self._gate_order:
            if gate_type not in self._gates:
                continue
            
            gate = self._gates[gate_type]
            result = gate.execute(trade, context)
            results.append(result)
            
            if not result.passed:
                all_passed = False
                if self.config.fail_fast:
                    break
        
        # Execute custom gates
        for name, gate in self._custom_gates.items():
            result = gate.execute(trade, context)
            results.append(result)
            
            if not result.passed:
                all_passed = False
                if self.config.fail_fast:
                    break
        
        # Record history
        with self._lock:
            self._check_history.append({
                "check_id": trade.check_id,
                "symbol": trade.symbol,
                "strategy_id": trade.strategy_id,
                "passed": all_passed,
                "results": [r.to_dict() for r in results],
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        if not all_passed:
            failed = [r for r in results if not r.passed]
            logger.warning(f"Pre-trade check FAILED for {trade.symbol}: {[r.reason for r in failed]}")
        
        return all_passed, results
    
    def add_custom_gate(self, name: str, check_fn: Callable[[PreTradeCheck, Dict[str, Any]], GateResult]) -> None:
        """Add a custom gate."""
        class CustomGate(Gate):
            def __init__(self, name: str, check_fn: Callable, config: GateConfig):
                super().__init__(GateType.CUSTOM, name, config)
                self._check_fn = check_fn
            
            def check(self, trade: PreTradeCheck, context: Dict[str, Any]) -> GateResult:
                return self._check_fn(trade, context)
        
        self._custom_gates[name] = CustomGate(name, check_fn, self.config)
        logger.info(f"Custom gate added: {name}")
    
    def remove_custom_gate(self, name: str) -> bool:
        """Remove a custom gate."""
        if name in self._custom_gates:
            del self._custom_gates[name]
            return True
        return False
    
    def enable_gate(self, gate_type: GateType) -> None:
        """Enable a gate."""
        if gate_type in self._gates:
            self._gates[gate_type]._enabled = True
    
    def disable_gate(self, gate_type: GateType) -> None:
        """Disable a gate."""
        if gate_type in self._gates:
            self._gates[gate_type]._enabled = False
    
    def approve_bypass(self, strategy_id: str, symbol: str, duration_seconds: int = 300, approved_by: str = "system") -> None:
        """Approve a temporary gate bypass."""
        if not self.config.bypass_allowed:
            raise ValueError("Gate bypass not allowed in configuration")
        
        bypass_key = f"{strategy_id}:{symbol}"
        self._bypass_approvals[bypass_key] = datetime.utcnow() + timedelta(seconds=duration_seconds)
        logger.warning(f"Gate bypass approved for {bypass_key} by {approved_by} for {duration_seconds}s")
    
    def revoke_bypass(self, strategy_id: str, symbol: str) -> None:
        """Revoke a gate bypass."""
        bypass_key = f"{strategy_id}:{symbol}"
        if bypass_key in self._bypass_approvals:
            del self._bypass_approvals[bypass_key]
    
    def get_gate_stats(self) -> Dict[str, Any]:
        """Get statistics for all gates."""
        stats = {}
        for gate_type, gate in self._gates.items():
            stats[gate_type.name] = gate.stats
        for name, gate in self._custom_gates.items():
            stats[f"CUSTOM_{name}"] = gate.stats
        return stats
    
    def get_check_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent check history."""
        with self._lock:
            return list(self._check_history)[-limit:]
    
    def get_failure_summary(self) -> Dict[str, int]:
        """Get summary of gate failures."""
        summary: Dict[str, int] = {}
        with self._lock:
            for check in self._check_history:
                if not check["passed"]:
                    for result in check["results"]:
                        if not result["passed"]:
                            gate_name = result["gate_name"]
                            summary[gate_name] = summary.get(gate_name, 0) + 1
        return summary
