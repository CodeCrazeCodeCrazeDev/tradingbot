"""
AlphaAlgo MSOS - Execution Reality Checks

Every strategy must declare:
- Latency tolerance
- Slippage tolerance
- Market impact assumptions

If real execution violates assumptions:
- Strategy is disabled
- Size reduced automatically

Ignoring execution drift is forbidden.

Author: AlphaAlgo MSOS
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class ExecutionQuality(Enum):
    """Execution quality levels"""
    EXCELLENT = auto()
    GOOD = auto()
    ACCEPTABLE = auto()
    DEGRADED = auto()
    POOR = auto()
    FAILED = auto()


@dataclass
class LatencyTolerance:
    """Latency tolerance specification and tracking"""
    declared_max_ms: float = 100.0  # Declared maximum latency
    current_latency_ms: float = 0.0
    average_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    violation_count: int = 0
    is_violated: bool = False
    
    def check_violation(self) -> bool:
        """Check if latency tolerance is violated"""
        try:
            self.is_violated = self.current_latency_ms > self.declared_max_ms
            if self.is_violated:
                self.violation_count += 1
            return self.is_violated
        except Exception as e:
            logger.error(f"Error in check_violation: {e}")
            raise


@dataclass
class SlippageTolerance:
    """Slippage tolerance specification and tracking"""
    declared_max_bps: float = 10.0  # Declared maximum slippage in basis points
    current_slippage_bps: float = 0.0
    average_slippage_bps: float = 0.0
    worst_slippage_bps: float = 0.0
    slippage_volatility: float = 0.0
    violation_count: int = 0
    is_violated: bool = False
    
    def check_violation(self) -> bool:
        """Check if slippage tolerance is violated"""
        try:
            self.is_violated = self.current_slippage_bps > self.declared_max_bps
            if self.is_violated:
                self.violation_count += 1
            return self.is_violated
        except Exception as e:
            logger.error(f"Error in check_violation: {e}")
            raise


@dataclass
class MarketImpact:
    """Market impact tracking"""
    declared_max_impact_bps: float = 20.0  # Declared maximum impact
    current_impact_bps: float = 0.0
    average_impact_bps: float = 0.0
    impact_per_unit: float = 0.0  # Impact per unit of size
    is_adversarial: bool = False  # Market reacting adversely
    violation_count: int = 0
    is_violated: bool = False
    
    def check_violation(self) -> bool:
        """Check if market impact tolerance is violated"""
        try:
            self.is_violated = self.current_impact_bps > self.declared_max_impact_bps
            if self.is_violated:
                self.violation_count += 1
            return self.is_violated
        except Exception as e:
            logger.error(f"Error in check_violation: {e}")
            raise


@dataclass
class ExecutionResult:
    """Result from execution reality check"""
    strategy_id: str
    quality: ExecutionQuality
    is_valid: bool
    can_trade: bool
    size_multiplier: float  # 0-1, how much to reduce size
    latency: LatencyTolerance
    slippage: SlippageTolerance
    impact: MarketImpact
    violations: List[str]
    reason: str
    action_required: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy_id': self.strategy_id,
            'quality': self.quality.name,
            'is_valid': self.is_valid,
            'can_trade': self.can_trade,
            'size_multiplier': self.size_multiplier,
            'latency_violated': self.latency.is_violated,
            'slippage_violated': self.slippage.is_violated,
            'impact_violated': self.impact.is_violated,
            'violations': self.violations,
            'reason': self.reason,
            'action_required': self.action_required,
            'timestamp': self.timestamp
        }


class LatencyTracker:
    """Tracks execution latency"""
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self._latencies: Deque[float] = deque(maxlen=window_size)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, latency_ms: float, declared_max: float) -> LatencyTolerance:
        """Update with new latency measurement"""
        try:
            self._latencies.append(latency_ms)
        
            result = LatencyTolerance(declared_max_ms=declared_max)
            result.current_latency_ms = latency_ms
        
            if len(self._latencies) >= 10:
                latencies = np.array(list(self._latencies))
                result.average_latency_ms = np.mean(latencies)
                result.p95_latency_ms = np.percentile(latencies, 95)
                result.p99_latency_ms = np.percentile(latencies, 99)
        
            result.check_violation()
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class SlippageTracker:
    """Tracks execution slippage"""
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self._slippages: Deque[float] = deque(maxlen=window_size)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, slippage_bps: float, declared_max: float) -> SlippageTolerance:
        """Update with new slippage measurement"""
        try:
            self._slippages.append(slippage_bps)
        
            result = SlippageTolerance(declared_max_bps=declared_max)
            result.current_slippage_bps = slippage_bps
        
            if len(self._slippages) >= 10:
                slippages = np.array(list(self._slippages))
                result.average_slippage_bps = np.mean(slippages)
                result.worst_slippage_bps = np.max(slippages)
                result.slippage_volatility = np.std(slippages)
        
            result.check_violation()
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class ImpactTracker:
    """Tracks market impact"""
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self._impacts: Deque[Tuple[float, float]] = deque(maxlen=window_size)  # (impact, size)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(
        self,
        impact_bps: float,
        size: float,
        declared_max: float
    ) -> MarketImpact:
        """Update with new impact measurement"""
        try:
            self._impacts.append((impact_bps, size))
        
            result = MarketImpact(declared_max_impact_bps=declared_max)
            result.current_impact_bps = impact_bps
        
            if len(self._impacts) >= 10:
                impacts = np.array([i[0] for i in self._impacts])
                sizes = np.array([i[1] for i in self._impacts])
            
                result.average_impact_bps = np.mean(impacts)
            
                # Calculate impact per unit
                if np.sum(sizes) > 0:
                    result.impact_per_unit = np.sum(impacts * sizes) / np.sum(sizes)
            
                # Check for adversarial behavior (impact increasing with size)
                if len(sizes) >= 20:
                    correlation = np.corrcoef(sizes, impacts)[0, 1]
                    result.is_adversarial = correlation > 0.5
        
            result.check_violation()
        
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise


class ExecutionRealityChecker:
    """
    Main Execution Reality Checker
    
    RULES:
    1. Every strategy MUST declare execution tolerances
    2. Real execution is continuously compared to declarations
    3. Violations trigger automatic size reduction or disabling
    4. Ignoring execution drift is FORBIDDEN
    """
    
    # Violation thresholds
    MAX_CONSECUTIVE_VIOLATIONS = 3
    VIOLATION_RATE_THRESHOLD = 0.1  # 10% violation rate
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.logger = logging.getLogger("msos.execution")
        
            # Per-strategy trackers
            self._latency_trackers: Dict[str, LatencyTracker] = {}
            self._slippage_trackers: Dict[str, SlippageTracker] = {}
            self._impact_trackers: Dict[str, ImpactTracker] = {}
        
            # Strategy declarations
            self._declarations: Dict[str, Dict[str, float]] = {}
        
            # Violation tracking
            self._consecutive_violations: Dict[str, int] = {}
            self._total_executions: Dict[str, int] = {}
            self._total_violations: Dict[str, int] = {}
        
            # Disabled strategies
            self._disabled_strategies: Dict[str, str] = {}
        
            self.logger.info("Execution Reality Checker initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def register_strategy(
        self,
        strategy_id: str,
        latency_max_ms: float,
        slippage_max_bps: float,
        impact_max_bps: float
    ):
        """Register strategy execution tolerances"""
        try:
            self._declarations[strategy_id] = {
                'latency_max_ms': latency_max_ms,
                'slippage_max_bps': slippage_max_bps,
                'impact_max_bps': impact_max_bps
            }
        
            self._latency_trackers[strategy_id] = LatencyTracker()
            self._slippage_trackers[strategy_id] = SlippageTracker()
            self._impact_trackers[strategy_id] = ImpactTracker()
        
            self._consecutive_violations[strategy_id] = 0
            self._total_executions[strategy_id] = 0
            self._total_violations[strategy_id] = 0
        
            self.logger.info(
                f"Strategy {strategy_id} registered: "
                f"latency={latency_max_ms}ms, slippage={slippage_max_bps}bps, "
                f"impact={impact_max_bps}bps"
            )
        except Exception as e:
            logger.error(f"Error in register_strategy: {e}")
            raise
    
    def check_execution(
        self,
        strategy_id: str,
        latency_ms: float,
        slippage_bps: float,
        impact_bps: float,
        size: float = 1.0
    ) -> ExecutionResult:
        """
        Check execution against declared tolerances.
        
        If violations occur, size is reduced or strategy disabled.
        """
        # Check if strategy is disabled
        try:
            if strategy_id in self._disabled_strategies:
                return ExecutionResult(
                    strategy_id=strategy_id,
                    quality=ExecutionQuality.FAILED,
                    is_valid=False,
                    can_trade=False,
                    size_multiplier=0.0,
                    latency=LatencyTolerance(),
                    slippage=SlippageTolerance(),
                    impact=MarketImpact(),
                    violations=[f"Strategy disabled: {self._disabled_strategies[strategy_id]}"],
                    reason="Strategy is disabled",
                    action_required="Strategy must be re-evaluated before trading"
                )
        
            # Check if strategy is registered
            if strategy_id not in self._declarations:
                return ExecutionResult(
                    strategy_id=strategy_id,
                    quality=ExecutionQuality.FAILED,
                    is_valid=False,
                    can_trade=False,
                    size_multiplier=0.0,
                    latency=LatencyTolerance(),
                    slippage=SlippageTolerance(),
                    impact=MarketImpact(),
                    violations=["Strategy not registered"],
                    reason="Strategy must declare execution tolerances",
                    action_required="Register strategy with execution tolerances"
                )
        
            declarations = self._declarations[strategy_id]
        
            # Update trackers
            latency = self._latency_trackers[strategy_id].update(
                latency_ms, declarations['latency_max_ms']
            )
            slippage = self._slippage_trackers[strategy_id].update(
                slippage_bps, declarations['slippage_max_bps']
            )
            impact = self._impact_trackers[strategy_id].update(
                impact_bps, size, declarations['impact_max_bps']
            )
        
            # Track executions
            self._total_executions[strategy_id] += 1
        
            # Check violations
            violations = []
            if latency.is_violated:
                violations.append(f"Latency: {latency_ms:.1f}ms > {declarations['latency_max_ms']:.1f}ms")
            if slippage.is_violated:
                violations.append(f"Slippage: {slippage_bps:.1f}bps > {declarations['slippage_max_bps']:.1f}bps")
            if impact.is_violated:
                violations.append(f"Impact: {impact_bps:.1f}bps > {declarations['impact_max_bps']:.1f}bps")
            if impact.is_adversarial:
                violations.append("Market impact is adversarial")
        
            # Update violation tracking
            if violations:
                self._consecutive_violations[strategy_id] += 1
                self._total_violations[strategy_id] += 1
            else:
                self._consecutive_violations[strategy_id] = 0
        
            # Calculate violation rate
            violation_rate = (
                self._total_violations[strategy_id] / 
                max(1, self._total_executions[strategy_id])
            )
        
            # Determine quality and actions
            quality, size_multiplier, action = self._determine_quality(
                violations,
                self._consecutive_violations[strategy_id],
                violation_rate,
                impact.is_adversarial
            )
        
            # Check if strategy should be disabled
            if self._consecutive_violations[strategy_id] >= self.MAX_CONSECUTIVE_VIOLATIONS:
                self._disable_strategy(
                    strategy_id,
                    f"Consecutive violations: {self._consecutive_violations[strategy_id]}"
                )
                quality = ExecutionQuality.FAILED
                size_multiplier = 0.0
        
            if violation_rate > self.VIOLATION_RATE_THRESHOLD * 2:
                self._disable_strategy(
                    strategy_id,
                    f"Violation rate: {violation_rate:.1%}"
                )
                quality = ExecutionQuality.FAILED
                size_multiplier = 0.0
        
            is_valid = quality in [ExecutionQuality.EXCELLENT, ExecutionQuality.GOOD, ExecutionQuality.ACCEPTABLE]
            can_trade = quality != ExecutionQuality.FAILED
        
            reason = self._generate_reason(quality, violations, violation_rate)
        
            result = ExecutionResult(
                strategy_id=strategy_id,
                quality=quality,
                is_valid=is_valid,
                can_trade=can_trade,
                size_multiplier=size_multiplier,
                latency=latency,
                slippage=slippage,
                impact=impact,
                violations=violations,
                reason=reason,
                action_required=action
            )
        
            if violations:
                self.logger.warning(
                    f"[{strategy_id}] Execution violations: {violations} | "
                    f"Quality: {quality.name} | Size: {size_multiplier:.1%}"
                )
        
            return result
        except Exception as e:
            logger.error(f"Error in check_execution: {e}")
            raise
    
    def _determine_quality(
        self,
        violations: List[str],
        consecutive: int,
        rate: float,
        adversarial: bool
    ) -> Tuple[ExecutionQuality, float, str]:
        """Determine execution quality and size multiplier"""
        try:
            if adversarial:
                return (
                    ExecutionQuality.POOR,
                    0.3,
                    "REDUCE SIZE to 30%. Market is adversarial."
                )
        
            if consecutive >= self.MAX_CONSECUTIVE_VIOLATIONS:
                return (
                    ExecutionQuality.FAILED,
                    0.0,
                    "DISABLE STRATEGY. Too many consecutive violations."
                )
        
            if rate > self.VIOLATION_RATE_THRESHOLD * 2:
                return (
                    ExecutionQuality.FAILED,
                    0.0,
                    "DISABLE STRATEGY. Violation rate too high."
                )
        
            if len(violations) >= 2:
                return (
                    ExecutionQuality.POOR,
                    0.3,
                    "REDUCE SIZE to 30%. Multiple violations."
                )
        
            if len(violations) == 1:
                return (
                    ExecutionQuality.DEGRADED,
                    0.5,
                    "REDUCE SIZE to 50%. Single violation."
                )
        
            if rate > self.VIOLATION_RATE_THRESHOLD:
                return (
                    ExecutionQuality.ACCEPTABLE,
                    0.7,
                    "REDUCE SIZE to 70%. Elevated violation rate."
                )
        
            if rate > self.VIOLATION_RATE_THRESHOLD / 2:
                return (
                    ExecutionQuality.GOOD,
                    0.9,
                    "Monitor execution quality."
                )
        
            return (
                ExecutionQuality.EXCELLENT,
                1.0,
                "Normal operations."
            )
        except Exception as e:
            logger.error(f"Error in _determine_quality: {e}")
            raise
    
    def _generate_reason(
        self,
        quality: ExecutionQuality,
        violations: List[str],
        rate: float
    ) -> str:
        """Generate explanation"""
        try:
            if quality == ExecutionQuality.FAILED:
                return f"Execution failed: {violations}. Violation rate: {rate:.1%}"
            elif quality == ExecutionQuality.POOR:
                return f"Poor execution: {violations}"
            elif quality == ExecutionQuality.DEGRADED:
                return f"Degraded execution: {violations}"
            elif quality == ExecutionQuality.ACCEPTABLE:
                return f"Acceptable execution. Violation rate: {rate:.1%}"
            elif quality == ExecutionQuality.GOOD:
                return "Good execution quality"
            else:
                return "Excellent execution quality"
        except Exception as e:
            logger.error(f"Error in _generate_reason: {e}")
            raise
    
    def _disable_strategy(self, strategy_id: str, reason: str):
        """Disable a strategy"""
        try:
            self._disabled_strategies[strategy_id] = reason
            self.logger.critical(f"Strategy {strategy_id} DISABLED: {reason}")
        except Exception as e:
            logger.error(f"Error in _disable_strategy: {e}")
            raise
    
    def enable_strategy(self, strategy_id: str):
        """Re-enable a disabled strategy"""
        try:
            if strategy_id in self._disabled_strategies:
                del self._disabled_strategies[strategy_id]
                self._consecutive_violations[strategy_id] = 0
                self.logger.info(f"Strategy {strategy_id} re-enabled")
        except Exception as e:
            logger.error(f"Error in enable_strategy: {e}")
            raise
    
    def get_disabled_strategies(self) -> Dict[str, str]:
        """Get all disabled strategies"""
        return self._disabled_strategies.copy()
    
    def get_strategy_stats(self, strategy_id: str) -> Dict[str, Any]:
        """Get execution statistics for a strategy"""
        try:
            if strategy_id not in self._total_executions:
                return {}
        
            return {
                'total_executions': self._total_executions[strategy_id],
                'total_violations': self._total_violations[strategy_id],
                'violation_rate': self._total_violations[strategy_id] / max(1, self._total_executions[strategy_id]),
                'consecutive_violations': self._consecutive_violations[strategy_id],
                'is_disabled': strategy_id in self._disabled_strategies
            }
        except Exception as e:
            logger.error(f"Error in get_strategy_stats: {e}")
            raise
