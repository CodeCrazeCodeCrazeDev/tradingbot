"""
AlphaAlgo Institutional - Layer 7: Monitoring, Audit & Evolution
=================================================================

The Monitoring & Evolution Layer is responsible for:
- System health monitoring
- Performance attribution
- Model decay detection
- Strategy evolution
- Audit trail maintenance
- Continuous improvement

This layer operates as the EVOLUTION & AUDIT ENGINE.

Key principles:
- All models decay; systems must adapt
- Evolution is mostly subtraction, not addition
- Continuous monitoring is mandatory
- Audit trails are non-negotiable
- Performance must be attributed
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
import numpy as np
from collections import defaultdict
import uuid
import json
import hashlib

from .core_types import (
    EvolutionEvent, ModelStatus, MarketRegime, CommitteeType, CommitteeVote,
    CommitteeDecision, RiskLevel, SystemConstants
)

logger = logging.getLogger(__name__)


# =============================================================================
# MONITORING TYPES
# =============================================================================

class HealthStatus(Enum):
    """System health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"


class DecayType(Enum):
    """Types of model decay."""
    PERFORMANCE = "performance"  # Returns degrading
    SIGNAL = "signal"  # Signal quality degrading
    REGIME = "regime"  # Regime mismatch
    CORRELATION = "correlation"  # Correlation breakdown
    CAPACITY = "capacity"  # Capacity exhaustion
    STRUCTURAL = "structural"  # Market structure change


class EvolutionAction(Enum):
    """Evolution actions."""
    NONE = "none"
    RETRAIN = "retrain"
    RECALIBRATE = "recalibrate"
    REDUCE_ALLOCATION = "reduce_allocation"
    PAUSE = "pause"
    RETIRE = "retire"
    MUTATE = "mutate"
    REPLACE = "replace"


@dataclass
class HealthCheck:
    """A health check result."""
    component: str
    status: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAttribution:
    """Performance attribution breakdown."""
    strategy_id: str
    period_start: datetime
    period_end: datetime
    total_return: float
    alpha: float
    beta_contribution: float
    factor_contributions: Dict[str, float]
    timing_contribution: float
    selection_contribution: float
    residual: float


@dataclass
class DecaySignal:
    """A model decay signal."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    strategy_id: str = ""
    decay_type: DecayType = DecayType.PERFORMANCE
    severity: float = 0.0  # 0-1
    detected_at: datetime = field(default_factory=datetime.utcnow)
    evidence: Dict[str, Any] = field(default_factory=dict)
    recommended_action: EvolutionAction = EvolutionAction.NONE


@dataclass
class AuditEntry:
    """An audit log entry."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: str = ""
    component: str = ""
    action: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    user: str = "system"
    hash: str = ""
    
    def compute_hash(self, previous_hash: str = "") -> str:
        """Compute hash for audit chain."""
        content = f"{previous_hash}{self.timestamp.isoformat()}{self.event_type}{self.action}{json.dumps(self.details, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]


# =============================================================================
# HEALTH MONITOR
# =============================================================================

class HealthMonitor:
    """Monitors system health."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.health_history: List[HealthCheck] = []
        self.component_status: Dict[str, HealthStatus] = {}
    
    def check_component(
        self,
        component: str,
        check_func: Callable[[], Tuple[bool, str, Dict[str, Any]]]
    ) -> HealthCheck:
        """
        Check health of a component.
        
        Args:
            component: Component name
            check_func: Function returning (is_healthy, message, metrics)
            
        Returns:
            HealthCheck result
        """
        try:
            is_healthy, message, metrics = check_func()
            status = HealthStatus.HEALTHY if is_healthy else HealthStatus.WARNING
        except Exception as e:
            status = HealthStatus.FAILED
            message = str(e)
            metrics = {}
        
        check = HealthCheck(
            component=component,
            status=status,
            message=message,
            metrics=metrics
        )
        
        self.health_history.append(check)
        self.component_status[component] = status
        
        return check
    
    def get_overall_health(self) -> HealthStatus:
        """Get overall system health."""
        if not self.component_status:
            return HealthStatus.HEALTHY
        
        statuses = list(self.component_status.values())
        
        if HealthStatus.FAILED in statuses:
            return HealthStatus.FAILED
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        if HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get health report."""
        return {
            'overall_status': self.get_overall_health().value,
            'components': {k: v.value for k, v in self.component_status.items()},
            'last_check': self.health_history[-1].timestamp.isoformat() if self.health_history else None,
            'check_count': len(self.health_history)
        }


# =============================================================================
# PERFORMANCE ATTRIBUTOR
# =============================================================================

class PerformanceAttributor:
    """Attributes performance to sources."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.attribution_history: List[PerformanceAttribution] = []
    
    def compute_attribution(
        self,
        strategy_id: str,
        strategy_returns: np.ndarray,
        benchmark_returns: np.ndarray,
        factor_returns: Dict[str, np.ndarray],
        period_start: datetime,
        period_end: datetime
    ) -> PerformanceAttribution:
        """
        Compute performance attribution.
        
        Args:
            strategy_id: Strategy identifier
            strategy_returns: Strategy returns
            benchmark_returns: Benchmark returns
            factor_returns: Factor returns by name
            period_start: Period start
            period_end: Period end
            
        Returns:
            PerformanceAttribution
        """
        if len(strategy_returns) == 0:
            return PerformanceAttribution(
                strategy_id=strategy_id,
                period_start=period_start,
                period_end=period_end,
                total_return=0.0,
                alpha=0.0,
                beta_contribution=0.0,
                factor_contributions={},
                timing_contribution=0.0,
                selection_contribution=0.0,
                residual=0.0
            )
        
        # Total return
        total_return = np.prod(1 + strategy_returns) - 1
        
        # Beta to benchmark
        if len(benchmark_returns) > 0 and np.std(benchmark_returns) > 0:
            beta = np.cov(strategy_returns, benchmark_returns)[0, 1] / np.var(benchmark_returns)
            benchmark_total = np.prod(1 + benchmark_returns) - 1
            beta_contribution = beta * benchmark_total
        else:
            beta = 0.0
            beta_contribution = 0.0
        
        # Factor contributions
        factor_contributions = {}
        explained_return = beta_contribution
        
        for factor_name, factor_ret in factor_returns.items():
            if len(factor_ret) > 0 and np.std(factor_ret) > 0:
                factor_beta = np.cov(strategy_returns, factor_ret)[0, 1] / np.var(factor_ret)
                factor_total = np.prod(1 + factor_ret) - 1
                contribution = factor_beta * factor_total
                factor_contributions[factor_name] = contribution
                explained_return += contribution
        
        # Alpha (unexplained return)
        alpha = total_return - explained_return
        
        # Simplified timing/selection (would need more data in practice)
        timing_contribution = alpha * 0.3
        selection_contribution = alpha * 0.5
        residual = alpha * 0.2
        
        attribution = PerformanceAttribution(
            strategy_id=strategy_id,
            period_start=period_start,
            period_end=period_end,
            total_return=total_return,
            alpha=alpha,
            beta_contribution=beta_contribution,
            factor_contributions=factor_contributions,
            timing_contribution=timing_contribution,
            selection_contribution=selection_contribution,
            residual=residual
        )
        
        self.attribution_history.append(attribution)
        return attribution
    
    def get_attribution_summary(self, strategy_id: str = None) -> Dict[str, Any]:
        """Get attribution summary."""
        relevant = self.attribution_history
        if strategy_id:
            relevant = [a for a in relevant if a.strategy_id == strategy_id]
        
        if not relevant:
            return {}
        
        return {
            'avg_total_return': np.mean([a.total_return for a in relevant]),
            'avg_alpha': np.mean([a.alpha for a in relevant]),
            'avg_beta_contribution': np.mean([a.beta_contribution for a in relevant]),
            'attribution_count': len(relevant)
        }


# =============================================================================
# DECAY DETECTOR
# =============================================================================

class DecayDetector:
    """Detects model decay."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Decay thresholds
        self.sharpe_decay_threshold = self.config.get('sharpe_decay_threshold', 0.3)
        self.return_decay_threshold = self.config.get('return_decay_threshold', 0.5)
        self.signal_decay_threshold = self.config.get('signal_decay_threshold', 0.4)
        
        # Lookback periods
        self.short_lookback = self.config.get('short_lookback', 20)
        self.long_lookback = self.config.get('long_lookback', 60)
        
        # Decay signals
        self.decay_signals: List[DecaySignal] = []
    
    def detect_performance_decay(
        self,
        strategy_id: str,
        returns: np.ndarray
    ) -> Optional[DecaySignal]:
        """
        Detect performance decay.
        
        Args:
            strategy_id: Strategy identifier
            returns: Historical returns
            
        Returns:
            DecaySignal if decay detected, None otherwise
        """
        if len(returns) < self.long_lookback:
            return None
        
        # Compare short-term vs long-term Sharpe
        short_returns = returns[-self.short_lookback:]
        long_returns = returns[-self.long_lookback:]
        
        short_sharpe = np.mean(short_returns) / np.std(short_returns) * np.sqrt(252) if np.std(short_returns) > 0 else 0
        long_sharpe = np.mean(long_returns) / np.std(long_returns) * np.sqrt(252) if np.std(long_returns) > 0 else 0
        
        # Check for decay
        if long_sharpe > 0:
            decay_ratio = (long_sharpe - short_sharpe) / long_sharpe
        else:
            decay_ratio = 0
        
        if decay_ratio > self.sharpe_decay_threshold:
            severity = min(1.0, decay_ratio)
            
            signal = DecaySignal(
                strategy_id=strategy_id,
                decay_type=DecayType.PERFORMANCE,
                severity=severity,
                evidence={
                    'short_sharpe': short_sharpe,
                    'long_sharpe': long_sharpe,
                    'decay_ratio': decay_ratio
                },
                recommended_action=self._get_recommended_action(severity)
            )
            
            self.decay_signals.append(signal)
            return signal
        
        return None
    
    def detect_signal_decay(
        self,
        strategy_id: str,
        signal_accuracy: List[float]
    ) -> Optional[DecaySignal]:
        """
        Detect signal quality decay.
        
        Args:
            strategy_id: Strategy identifier
            signal_accuracy: Historical signal accuracy
            
        Returns:
            DecaySignal if decay detected
        """
        if len(signal_accuracy) < self.long_lookback:
            return None
        
        short_accuracy = np.mean(signal_accuracy[-self.short_lookback:])
        long_accuracy = np.mean(signal_accuracy[-self.long_lookback:])
        
        if long_accuracy > 0:
            decay_ratio = (long_accuracy - short_accuracy) / long_accuracy
        else:
            decay_ratio = 0
        
        if decay_ratio > self.signal_decay_threshold:
            severity = min(1.0, decay_ratio)
            
            signal = DecaySignal(
                strategy_id=strategy_id,
                decay_type=DecayType.SIGNAL,
                severity=severity,
                evidence={
                    'short_accuracy': short_accuracy,
                    'long_accuracy': long_accuracy,
                    'decay_ratio': decay_ratio
                },
                recommended_action=self._get_recommended_action(severity)
            )
            
            self.decay_signals.append(signal)
            return signal
        
        return None
    
    def detect_regime_mismatch(
        self,
        strategy_id: str,
        strategy_regime: MarketRegime,
        current_regime: MarketRegime,
        regime_performance: Dict[MarketRegime, float]
    ) -> Optional[DecaySignal]:
        """
        Detect regime mismatch.
        
        Args:
            strategy_id: Strategy identifier
            strategy_regime: Regime strategy was designed for
            current_regime: Current market regime
            regime_performance: Performance by regime
            
        Returns:
            DecaySignal if mismatch detected
        """
        if strategy_regime == current_regime:
            return None
        
        # Check if strategy performs poorly in current regime
        current_perf = regime_performance.get(current_regime, 0)
        designed_perf = regime_performance.get(strategy_regime, 0)
        
        if designed_perf > 0 and current_perf < designed_perf * 0.5:
            severity = min(1.0, 1 - current_perf / designed_perf)
            
            signal = DecaySignal(
                strategy_id=strategy_id,
                decay_type=DecayType.REGIME,
                severity=severity,
                evidence={
                    'strategy_regime': strategy_regime.value,
                    'current_regime': current_regime.value,
                    'current_performance': current_perf,
                    'designed_performance': designed_perf
                },
                recommended_action=EvolutionAction.PAUSE
            )
            
            self.decay_signals.append(signal)
            return signal
        
        return None
    
    def _get_recommended_action(self, severity: float) -> EvolutionAction:
        """Get recommended action based on severity."""
        if severity > 0.8:
            return EvolutionAction.RETIRE
        elif severity > 0.6:
            return EvolutionAction.PAUSE
        elif severity > 0.4:
            return EvolutionAction.REDUCE_ALLOCATION
        elif severity > 0.2:
            return EvolutionAction.RECALIBRATE
        else:
            return EvolutionAction.NONE
    
    def get_active_decay_signals(self, strategy_id: str = None) -> List[DecaySignal]:
        """Get active decay signals."""
        signals = self.decay_signals
        if strategy_id:
            signals = [s for s in signals if s.strategy_id == strategy_id]
        
        # Only return recent signals (last 7 days)
        cutoff = datetime.utcnow() - timedelta(days=7)
        return [s for s in signals if s.detected_at > cutoff]


# =============================================================================
# EVOLUTION ENGINE
# =============================================================================

class EvolutionEngine:
    """Manages strategy evolution."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.evolution_history: List[EvolutionEvent] = []
        
        # Evolution parameters
        self.min_performance_threshold = self.config.get('min_performance_threshold', 0.0)
        self.max_strategies = self.config.get('max_strategies', 20)
        self.evolution_frequency_days = self.config.get('evolution_frequency_days', 7)
    
    def propose_evolution(
        self,
        strategy_id: str,
        decay_signals: List[DecaySignal],
        performance_metrics: Dict[str, float]
    ) -> Optional[EvolutionEvent]:
        """
        Propose evolution action for a strategy.
        
        Args:
            strategy_id: Strategy identifier
            decay_signals: Active decay signals
            performance_metrics: Current performance metrics
            
        Returns:
            EvolutionEvent if action proposed
        """
        if not decay_signals:
            return None
        
        # Get most severe signal
        most_severe = max(decay_signals, key=lambda s: s.severity)
        
        # Determine action
        action = most_severe.recommended_action
        
        # Create evolution event
        event = EvolutionEvent(
            strategy_id=strategy_id,
            event_type=action.value,
            trigger=most_severe.decay_type.value,
            old_state={'status': 'active'},
            new_state={'status': action.value},
            rationale=f"Decay detected: {most_severe.decay_type.value} with severity {most_severe.severity:.2f}"
        )
        
        self.evolution_history.append(event)
        return event
    
    def execute_evolution(
        self,
        event: EvolutionEvent,
        strategy_manager: Any  # Would be actual strategy manager
    ) -> bool:
        """
        Execute evolution action.
        
        Args:
            event: Evolution event to execute
            strategy_manager: Strategy manager instance
            
        Returns:
            True if successful
        """
        # In practice, this would interact with the strategy manager
        # to actually perform the evolution action
        
        logger.info(f"Executing evolution: {event.event_type} for {event.strategy_id}")
        
        event.executed = True
        event.executed_at = datetime.utcnow()
        
        return True
    
    def get_evolution_summary(self) -> Dict[str, Any]:
        """Get evolution summary."""
        if not self.evolution_history:
            return {'total_events': 0}
        
        action_counts = defaultdict(int)
        for event in self.evolution_history:
            action_counts[event.event_type] += 1
        
        return {
            'total_events': len(self.evolution_history),
            'action_counts': dict(action_counts),
            'last_evolution': self.evolution_history[-1].timestamp.isoformat()
        }


# =============================================================================
# AUDIT LOGGER
# =============================================================================

class AuditLogger:
    """Maintains audit trail."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.audit_log: List[AuditEntry] = []
        self.last_hash = ""
    
    def log(
        self,
        event_type: str,
        component: str,
        action: str,
        details: Dict[str, Any] = None,
        user: str = "system"
    ) -> AuditEntry:
        """
        Log an audit entry.
        
        Args:
            event_type: Type of event
            component: Component involved
            action: Action taken
            details: Additional details
            user: User or system that triggered
            
        Returns:
            AuditEntry
        """
        entry = AuditEntry(
            event_type=event_type,
            component=component,
            action=action,
            details=details or {},
            user=user
        )
        
        # Compute hash for chain integrity
        entry.hash = entry.compute_hash(self.last_hash)
        self.last_hash = entry.hash
        
        self.audit_log.append(entry)
        
        return entry
    
    def verify_chain(self) -> Tuple[bool, Optional[int]]:
        """
        Verify audit chain integrity.
        
        Returns:
            Tuple of (is_valid, first_invalid_index)
        """
        if not self.audit_log:
            return True, None
        
        prev_hash = ""
        for i, entry in enumerate(self.audit_log):
            expected_hash = entry.compute_hash(prev_hash)
            if entry.hash != expected_hash:
                return False, i
            prev_hash = entry.hash
        
        return True, None
    
    def get_entries(
        self,
        component: str = None,
        event_type: str = None,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> List[AuditEntry]:
        """Get filtered audit entries."""
        entries = self.audit_log
        
        if component:
            entries = [e for e in entries if e.component == component]
        if event_type:
            entries = [e for e in entries if e.event_type == event_type]
        if start_time:
            entries = [e for e in entries if e.timestamp >= start_time]
        if end_time:
            entries = [e for e in entries if e.timestamp <= end_time]
        
        return entries
    
    def export_log(self) -> List[Dict[str, Any]]:
        """Export audit log as JSON-serializable list."""
        return [
            {
                'id': e.id,
                'timestamp': e.timestamp.isoformat(),
                'event_type': e.event_type,
                'component': e.component,
                'action': e.action,
                'details': e.details,
                'user': e.user,
                'hash': e.hash
            }
            for e in self.audit_log
        ]


# =============================================================================
# EVOLUTION & AUDIT ENGINE
# =============================================================================

class EvolutionAuditEngine:
    """
    Internal committee responsible for monitoring and evolution.
    
    Responsibilities:
    - System health monitoring
    - Performance attribution
    - Model decay detection
    - Strategy evolution
    - Audit trail maintenance
    
    Key principles:
    - All models decay
    - Evolution is mostly subtraction
    - Audit trails are non-negotiable
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.committee_type = CommitteeType.EVOLUTION_AUDIT
        
        # Initialize components
        self.health_monitor = HealthMonitor(self.config)
        self.attributor = PerformanceAttributor(self.config)
        self.decay_detector = DecayDetector(self.config)
        self.evolution_engine = EvolutionEngine(self.config)
        self.audit_logger = AuditLogger(self.config)
        
        # Log initialization
        self.audit_logger.log(
            event_type="system",
            component="EvolutionAuditEngine",
            action="initialized",
            details={'config': self.config}
        )
        
        logger.info("EvolutionAuditEngine initialized")
    
    def run_health_check(
        self,
        components: Dict[str, Callable[[], Tuple[bool, str, Dict[str, Any]]]]
    ) -> Dict[str, HealthCheck]:
        """
        Run health checks on all components.
        
        Args:
            components: Dict of component name -> check function
            
        Returns:
            Dict of component name -> HealthCheck
        """
        results = {}
        
        for name, check_func in components.items():
            result = self.health_monitor.check_component(name, check_func)
            results[name] = result
            
            # Log if not healthy
            if result.status != HealthStatus.HEALTHY:
                self.audit_logger.log(
                    event_type="health",
                    component=name,
                    action="health_check_failed",
                    details={'status': result.status.value, 'message': result.message}
                )
        
        return results
    
    def analyze_strategy(
        self,
        strategy_id: str,
        returns: np.ndarray,
        signal_accuracy: List[float],
        current_regime: MarketRegime,
        strategy_regime: MarketRegime,
        regime_performance: Dict[MarketRegime, float]
    ) -> Dict[str, Any]:
        """
        Analyze a strategy for decay and evolution needs.
        
        Returns:
            Analysis results
        """
        decay_signals = []
        
        # Check performance decay
        perf_decay = self.decay_detector.detect_performance_decay(strategy_id, returns)
        if perf_decay:
            decay_signals.append(perf_decay)
        
        # Check signal decay
        signal_decay = self.decay_detector.detect_signal_decay(strategy_id, signal_accuracy)
        if signal_decay:
            decay_signals.append(signal_decay)
        
        # Check regime mismatch
        regime_decay = self.decay_detector.detect_regime_mismatch(
            strategy_id, strategy_regime, current_regime, regime_performance
        )
        if regime_decay:
            decay_signals.append(regime_decay)
        
        # Propose evolution if needed
        evolution_event = None
        if decay_signals:
            performance_metrics = {
                'sharpe': np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0,
                'total_return': np.prod(1 + returns) - 1 if len(returns) > 0 else 0
            }
            evolution_event = self.evolution_engine.propose_evolution(
                strategy_id, decay_signals, performance_metrics
            )
            
            # Log evolution proposal
            if evolution_event:
                self.audit_logger.log(
                    event_type="evolution",
                    component=strategy_id,
                    action="evolution_proposed",
                    details={
                        'event_type': evolution_event.event_type,
                        'trigger': evolution_event.trigger,
                        'rationale': evolution_event.rationale
                    }
                )
        
        return {
            'strategy_id': strategy_id,
            'decay_signals': decay_signals,
            'evolution_event': evolution_event,
            'needs_attention': len(decay_signals) > 0
        }
    
    def vote(self, evolution_event: EvolutionEvent) -> CommitteeVote:
        """
        Vote on an evolution event.
        
        Returns:
            CommitteeVote
        """
        # Evaluate evolution proposal
        action = EvolutionAction(evolution_event.event_type)
        
        # Conservative approach - approve most evolution actions
        if action in [EvolutionAction.RETIRE, EvolutionAction.PAUSE]:
            decision = CommitteeDecision.APPROVE
            confidence = 0.9
            rationale = f"Approved {action.value}: {evolution_event.rationale}"
        elif action in [EvolutionAction.REDUCE_ALLOCATION, EvolutionAction.RECALIBRATE]:
            decision = CommitteeDecision.APPROVE
            confidence = 0.8
            rationale = f"Approved {action.value}: {evolution_event.rationale}"
        elif action == EvolutionAction.MUTATE:
            decision = CommitteeDecision.CONDITIONAL
            confidence = 0.6
            rationale = f"Conditional approval for mutation: requires validation"
        else:
            decision = CommitteeDecision.APPROVE
            confidence = 0.7
            rationale = f"Approved {action.value}"
        
        return CommitteeVote(
            committee=self.committee_type,
            decision=decision,
            confidence=confidence,
            rationale=rationale
        )
    
    def get_engine_state(self) -> Dict[str, Any]:
        """Get engine state."""
        return {
            'health': self.health_monitor.get_health_report(),
            'attribution_summary': self.attributor.get_attribution_summary(),
            'active_decay_signals': len(self.decay_detector.get_active_decay_signals()),
            'evolution_summary': self.evolution_engine.get_evolution_summary(),
            'audit_log_size': len(self.audit_logger.audit_log),
            'audit_chain_valid': self.audit_logger.verify_chain()[0]
        }


# =============================================================================
# MONITORING EVOLUTION LAYER
# =============================================================================

class MonitoringEvolutionLayer:
    """
    Layer 7: Monitoring, Audit & Evolution Layer
    
    Responsible for:
    - System health monitoring
    - Performance attribution
    - Model decay detection
    - Strategy evolution
    - Audit trail maintenance
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.engine = EvolutionAuditEngine(self.config)
        
        # Layer state
        self.last_health_check: Optional[datetime] = None
        self.last_evolution_cycle: Optional[datetime] = None
        
        logger.info("MonitoringEvolutionLayer initialized")
    
    def run_health_check(
        self,
        components: Dict[str, Callable[[], Tuple[bool, str, Dict[str, Any]]]]
    ) -> Dict[str, HealthCheck]:
        """Run health checks."""
        results = self.engine.run_health_check(components)
        self.last_health_check = datetime.utcnow()
        return results
    
    def analyze_strategy(
        self,
        strategy_id: str,
        returns: np.ndarray,
        signal_accuracy: List[float],
        current_regime: MarketRegime,
        strategy_regime: MarketRegime,
        regime_performance: Dict[MarketRegime, float]
    ) -> Dict[str, Any]:
        """Analyze strategy for decay."""
        return self.engine.analyze_strategy(
            strategy_id, returns, signal_accuracy,
            current_regime, strategy_regime, regime_performance
        )
    
    def compute_attribution(
        self,
        strategy_id: str,
        strategy_returns: np.ndarray,
        benchmark_returns: np.ndarray,
        factor_returns: Dict[str, np.ndarray],
        period_start: datetime,
        period_end: datetime
    ) -> PerformanceAttribution:
        """Compute performance attribution."""
        return self.engine.attributor.compute_attribution(
            strategy_id, strategy_returns, benchmark_returns,
            factor_returns, period_start, period_end
        )
    
    def log_audit(
        self,
        event_type: str,
        component: str,
        action: str,
        details: Dict[str, Any] = None
    ) -> AuditEntry:
        """Log audit entry."""
        return self.engine.audit_logger.log(event_type, component, action, details)
    
    def get_audit_log(
        self,
        component: str = None,
        start_time: datetime = None
    ) -> List[AuditEntry]:
        """Get audit log entries."""
        return self.engine.audit_logger.get_entries(
            component=component, start_time=start_time
        )
    
    def verify_audit_chain(self) -> Tuple[bool, Optional[int]]:
        """Verify audit chain integrity."""
        return self.engine.audit_logger.verify_chain()
    
    def get_layer_state(self) -> Dict[str, Any]:
        """Get layer state."""
        return {
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'last_evolution_cycle': self.last_evolution_cycle.isoformat() if self.last_evolution_cycle else None,
            'engine_state': self.engine.get_engine_state()
        }
