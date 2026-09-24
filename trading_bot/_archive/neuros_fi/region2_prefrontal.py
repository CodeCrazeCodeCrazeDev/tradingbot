"""
NEUROS-FI Region 2: Prefrontal Cortex - Executive Control and Goal Maintenance
===============================================================================

Biological Basis:
The PFC holds goals in working memory while inhibiting reflexive responses.
It arbitrates between competing strategies based on context.

- Dorsolateral PFC (dlPFC): Systematic deliberative reasoning
- Ventromedial PFC (vmPFC): Risk-value integration
- Orbitofrontal Cortex (OFC): Expected value updates on surprise
- Working Memory: Active context maintenance
- Inhibitory Control: Suppress reflexive responses to noise

Citations:
- Miller & Cohen (2001) - An integrative theory of prefrontal cortex function
- Fuster (2001) - The prefrontal cortex—an update
- Bechara et al. (2000) - Emotion, decision making and the orbitofrontal cortex
- Goldman-Rakic (1995) - Cellular basis of working memory

Constitutional Version: 5.0
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class ExecutiveFunction(Enum):
    """Executive functions implemented by the PFC."""
    
    WORKING_MEMORY = auto()
    INHIBITORY_CONTROL = auto()
    COGNITIVE_FLEXIBILITY = auto()
    PLANNING = auto()
    DECISION_MAKING = auto()
    ATTENTION_CONTROL = auto()


class StrategyState(Enum):
    """State of a trading strategy in working memory."""
    
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EVALUATING = "evaluating"
    TERMINATED = "terminated"


class InhibitionType(Enum):
    """Types of inhibitory control."""
    
    RESPONSE_INHIBITION = auto()  # Stop impulsive actions
    INTERFERENCE_CONTROL = auto()  # Filter distracting signals
    COGNITIVE_INHIBITION = auto()  # Suppress irrelevant thoughts


@dataclass
class StrategyHypothesis:
    """A trading strategy hypothesis held in working memory."""
    
    strategy_id: str
    name: str
    state: StrategyState
    capital_allocation: float
    expected_sharpe: float
    regime_conditions: List[str]
    last_performance: float
    confidence: float
    activation_time: datetime
    last_update: datetime
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkingMemoryItem:
    """An item held in working memory."""
    
    item_id: str
    item_type: str
    content: Any
    priority: float  # 0-1, higher = more important
    decay_rate: float  # How fast it fades from memory
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    
    def get_activation(self) -> float:
        """Get current activation level (decays over time)."""
        elapsed = (datetime.utcnow() - self.last_accessed).total_seconds()
        return self.priority * np.exp(-self.decay_rate * elapsed / 3600)


@dataclass
class InhibitionSignal:
    """A signal to inhibit a response."""
    
    signal_id: str
    inhibition_type: InhibitionType
    target: str
    strength: float  # 0-1
    reason: str
    timestamp: datetime
    duration: timedelta
    active: bool = True


@dataclass
class ExpectedValueUpdate:
    """Update to expected value from OFC."""
    
    context: str
    previous_value: float
    observed_outcome: float
    prediction_error: float
    new_expected_value: float
    timestamp: datetime


class WorkingMemory:
    """
    Working Memory System - maintains active context for all decisions.
    
    Biological basis: dlPFC maintains task-relevant information in an
    active state through persistent neural firing.
    
    Capacity limited to ~7±2 items (Miller's Law), but items can be
    chunked into higher-level representations.
    """
    
    CAPACITY = 7  # Miller's Law
    
    def __init__(self):
        self._items: Dict[str, WorkingMemoryItem] = {}
        self._lock = threading.RLock()
        self._access_history: List[Tuple[datetime, str]] = []
        
        # Portfolio state (always in working memory)
        self._portfolio_state: Dict[str, Any] = {
            'positions': {},
            'factor_exposures': {},
            'unrealized_pnl': 0.0,
            'liquidity_constraints': {},
            'current_regime': 'normal',
        }
        
        logger.info("Working Memory initialized - capacity: 7±2 items")
    
    def store(
        self,
        item_id: str,
        item_type: str,
        content: Any,
        priority: float = 0.5,
        decay_rate: float = 0.1
    ) -> bool:
        """
        Store an item in working memory.
        
        If at capacity, lowest activation item is displaced.
        """
        with self._lock:
            now = datetime.utcnow()
            
            # Check if item already exists
            if item_id in self._items:
                self._items[item_id].content = content
                self._items[item_id].last_accessed = now
                self._items[item_id].access_count += 1
                return True
            
            # Check capacity
            if len(self._items) >= self.CAPACITY:
                # Find lowest activation item
                min_activation = float('inf')
                min_item_id = None
                
                for iid, item in self._items.items():
                    activation = item.get_activation()
                    if activation < min_activation:
                        min_activation = activation
                        min_item_id = iid
                
                # Displace if new item has higher priority
                if min_item_id and priority > min_activation:
                    del self._items[min_item_id]
                    logger.debug(f"Working memory displaced: {min_item_id}")
                else:
                    logger.debug(f"Working memory at capacity, item rejected: {item_id}")
                    return False
            
            # Store new item
            self._items[item_id] = WorkingMemoryItem(
                item_id=item_id,
                item_type=item_type,
                content=content,
                priority=priority,
                decay_rate=decay_rate,
                created_at=now,
                last_accessed=now,
            )
            
            self._access_history.append((now, item_id))
            return True
    
    def retrieve(self, item_id: str) -> Optional[Any]:
        """Retrieve an item from working memory."""
        with self._lock:
            if item_id in self._items:
                item = self._items[item_id]
                item.last_accessed = datetime.utcnow()
                item.access_count += 1
                self._access_history.append((datetime.utcnow(), item_id))
                return item.content
            return None
    
    def update_portfolio_state(self, updates: Dict[str, Any]):
        """Update the always-active portfolio state."""
        with self._lock:
            self._portfolio_state.update(updates)
    
    def get_portfolio_state(self) -> Dict[str, Any]:
        """Get current portfolio state."""
        with self._lock:
            return self._portfolio_state.copy()
    
    def get_active_items(self) -> List[WorkingMemoryItem]:
        """Get all items with activation above threshold."""
        with self._lock:
            threshold = 0.1
            return [
                item for item in self._items.values()
                if item.get_activation() > threshold
            ]
    
    def clear_decayed(self):
        """Clear items that have decayed below threshold."""
        with self._lock:
            threshold = 0.05
            to_remove = [
                iid for iid, item in self._items.items()
                if item.get_activation() < threshold
            ]
            for iid in to_remove:
                del self._items[iid]
            
            if to_remove:
                logger.debug(f"Cleared {len(to_remove)} decayed items from working memory")
    
    def get_status(self) -> Dict[str, Any]:
        """Get working memory status."""
        with self._lock:
            return {
                'item_count': len(self._items),
                'capacity': self.CAPACITY,
                'utilization': len(self._items) / self.CAPACITY,
                'items': [
                    {
                        'id': item.item_id,
                        'type': item.item_type,
                        'activation': item.get_activation(),
                        'access_count': item.access_count,
                    }
                    for item in self._items.values()
                ],
            }


class DorsolateralPFC:
    """
    Dorsolateral Prefrontal Cortex (dlPFC) - Deliberative Reasoning
    
    Maintains the current strategy portfolio in working memory.
    Runs deliberative arbitration when strategies conflict.
    """
    
    def __init__(self, working_memory: WorkingMemory):
        self._working_memory = working_memory
        self._active_strategies: Dict[str, StrategyHypothesis] = {}
        self._lock = threading.RLock()
        
        # Deliberation parameters
        self._min_sharpe_threshold = 0.5
        self._max_strategy_count = 20
        self._regime_weights: Dict[str, float] = {
            'bull': 1.2,
            'normal': 1.0,
            'bear': 0.7,
            'crisis': 0.3,
        }
    
    def register_strategy(
        self,
        strategy_id: str,
        name: str,
        expected_sharpe: float,
        regime_conditions: List[str],
        initial_allocation: float = 0.0
    ) -> bool:
        """Register a strategy in working memory."""
        with self._lock:
            if len(self._active_strategies) >= self._max_strategy_count:
                # Find worst performing strategy to replace
                worst_id = min(
                    self._active_strategies.keys(),
                    key=lambda x: self._active_strategies[x].last_performance
                )
                if expected_sharpe > self._active_strategies[worst_id].expected_sharpe:
                    del self._active_strategies[worst_id]
                else:
                    return False
            
            now = datetime.utcnow()
            hypothesis = StrategyHypothesis(
                strategy_id=strategy_id,
                name=name,
                state=StrategyState.EVALUATING,
                capital_allocation=initial_allocation,
                expected_sharpe=expected_sharpe,
                regime_conditions=regime_conditions,
                last_performance=0.0,
                confidence=0.5,
                activation_time=now,
                last_update=now,
            )
            
            self._active_strategies[strategy_id] = hypothesis
            
            # Store in working memory
            self._working_memory.store(
                item_id=f"strategy_{strategy_id}",
                item_type="strategy_hypothesis",
                content=hypothesis,
                priority=expected_sharpe / 5.0,  # Normalize to 0-1
            )
            
            return True
    
    def deliberate_allocation(
        self,
        current_regime: str,
        total_capital: float
    ) -> Dict[str, float]:
        """
        Deliberative arbitration between competing strategies.
        
        Returns optimal capital allocation based on:
        - Regime-conditional expected Sharpe
        - Strategy confidence
        - Correlation between strategies
        """
        with self._lock:
            allocations = {}
            regime_weight = self._regime_weights.get(current_regime, 1.0)
            
            # Calculate regime-adjusted scores
            scores = {}
            total_score = 0.0
            
            for sid, strategy in self._active_strategies.items():
                if strategy.state == StrategyState.TERMINATED:
                    continue
                
                # Check regime compatibility
                if current_regime in strategy.regime_conditions or not strategy.regime_conditions:
                    regime_factor = 1.0
                else:
                    regime_factor = 0.5
                
                # Calculate score
                score = (
                    strategy.expected_sharpe *
                    strategy.confidence *
                    regime_weight *
                    regime_factor
                )
                
                if score > self._min_sharpe_threshold * 0.5:
                    scores[sid] = score
                    total_score += score
            
            # Allocate capital proportionally
            if total_score > 0:
                for sid, score in scores.items():
                    allocations[sid] = (score / total_score) * total_capital
                    self._active_strategies[sid].capital_allocation = allocations[sid]
                    self._active_strategies[sid].state = StrategyState.ACTIVE
            
            return allocations
    
    def update_strategy_performance(
        self,
        strategy_id: str,
        performance: float,
        confidence_adjustment: float = 0.0
    ):
        """Update strategy performance and confidence."""
        with self._lock:
            if strategy_id in self._active_strategies:
                strategy = self._active_strategies[strategy_id]
                strategy.last_performance = performance
                strategy.confidence = max(0.1, min(1.0,
                    strategy.confidence + confidence_adjustment
                ))
                strategy.last_update = datetime.utcnow()
    
    def get_active_strategies(self) -> List[StrategyHypothesis]:
        """Get all active strategies."""
        with self._lock:
            return [
                s for s in self._active_strategies.values()
                if s.state == StrategyState.ACTIVE
            ]


class VentromedialPFC:
    """
    Ventromedial Prefrontal Cortex (vmPFC) - Risk-Value Integration
    
    Integrates risk-adjusted value across the book continuously.
    Overrides local signals when portfolio-level value is negative.
    """
    
    def __init__(self, working_memory: WorkingMemory):
        self._working_memory = working_memory
        self._lock = threading.RLock()
        
        # Value integration state
        self._integrated_value: float = 0.0
        self._risk_adjusted_value: float = 0.0
        self._value_history: List[Tuple[datetime, float]] = []
        
        # Risk parameters
        self._risk_aversion = 2.0  # CRRA coefficient
        self._value_threshold = -0.02  # -2% triggers override
    
    def integrate_value(
        self,
        position_values: Dict[str, float],
        position_risks: Dict[str, float]
    ) -> Tuple[float, bool]:
        """
        Integrate risk-adjusted value across all positions.
        
        Returns:
            Tuple of (risk_adjusted_value, should_override)
        """
        with self._lock:
            total_value = sum(position_values.values())
            total_risk = sum(position_risks.values())
            
            # Risk-adjusted value (CRRA utility)
            if total_risk > 0:
                risk_penalty = self._risk_aversion * (total_risk ** 2) / 2
                self._risk_adjusted_value = total_value - risk_penalty
            else:
                self._risk_adjusted_value = total_value
            
            self._integrated_value = total_value
            self._value_history.append((datetime.utcnow(), self._risk_adjusted_value))
            
            # Trim history
            if len(self._value_history) > 1000:
                self._value_history = self._value_history[-500:]
            
            # Check for override condition
            should_override = self._risk_adjusted_value < self._value_threshold
            
            if should_override:
                logger.warning(
                    f"vmPFC override triggered: risk-adjusted value "
                    f"{self._risk_adjusted_value:.4f} < {self._value_threshold}"
                )
            
            return self._risk_adjusted_value, should_override
    
    def get_value_trend(self, lookback_minutes: int = 60) -> float:
        """Get the trend in risk-adjusted value."""
        with self._lock:
            if len(self._value_history) < 2:
                return 0.0
            
            cutoff = datetime.utcnow() - timedelta(minutes=lookback_minutes)
            recent = [v for t, v in self._value_history if t > cutoff]
            
            if len(recent) < 2:
                return 0.0
            
            # Simple linear trend
            return (recent[-1] - recent[0]) / len(recent)
    
    def should_override_local_signal(
        self,
        local_signal_value: float,
        local_signal_risk: float
    ) -> bool:
        """
        Determine if a local positive signal should be overridden
        due to negative portfolio-level value.
        """
        with self._lock:
            # Local signal is positive but portfolio is suffering
            if local_signal_value > 0 and self._risk_adjusted_value < self._value_threshold:
                # Check if local signal would help or hurt
                marginal_impact = local_signal_value - self._risk_aversion * local_signal_risk
                
                # Override if marginal impact is negative
                return marginal_impact < 0
            
            return False


class OrbitofrontalCortex:
    """
    Orbitofrontal Cortex (OFC) - Expected Value Updates
    
    Updates expected value estimates when trade outcomes differ from predictions.
    Each surprise recalibrates the expected value map.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Expected value maps
        self._expected_values: Dict[str, float] = {}
        self._value_updates: List[ExpectedValueUpdate] = []
        
        # Learning rate for value updates
        self._learning_rate = 0.1
        self._surprise_sensitivity = 1.5
    
    def update_expected_value(
        self,
        context: str,
        observed_outcome: float,
        predicted_outcome: Optional[float] = None
    ) -> ExpectedValueUpdate:
        """
        Update expected value based on observed outcome.
        
        Implements Rescorla-Wagner learning rule.
        """
        with self._lock:
            # Get current expected value
            if predicted_outcome is not None:
                current_ev = predicted_outcome
            else:
                current_ev = self._expected_values.get(context, 0.0)
            
            # Calculate prediction error
            prediction_error = observed_outcome - current_ev
            
            # Update expected value (Rescorla-Wagner)
            # Larger surprises drive larger updates
            surprise_factor = min(
                self._surprise_sensitivity,
                1.0 + abs(prediction_error)
            )
            
            new_ev = current_ev + self._learning_rate * surprise_factor * prediction_error
            self._expected_values[context] = new_ev
            
            # Record update
            update = ExpectedValueUpdate(
                context=context,
                previous_value=current_ev,
                observed_outcome=observed_outcome,
                prediction_error=prediction_error,
                new_expected_value=new_ev,
                timestamp=datetime.utcnow(),
            )
            self._value_updates.append(update)
            
            # Trim history
            if len(self._value_updates) > 1000:
                self._value_updates = self._value_updates[-500:]
            
            return update
    
    def get_expected_value(self, context: str) -> float:
        """Get expected value for a context."""
        with self._lock:
            return self._expected_values.get(context, 0.0)
    
    def get_recent_updates(self, limit: int = 100) -> List[ExpectedValueUpdate]:
        """Get recent value updates."""
        with self._lock:
            return self._value_updates[-limit:]
    
    def get_surprise_statistics(self) -> Dict[str, float]:
        """Get statistics on recent prediction errors."""
        with self._lock:
            if not self._value_updates:
                return {'mean': 0.0, 'std': 0.0, 'max': 0.0}
            
            errors = [u.prediction_error for u in self._value_updates[-100:]]
            return {
                'mean': np.mean(errors),
                'std': np.std(errors),
                'max': max(abs(e) for e in errors),
            }


class InhibitoryControl:
    """
    Inhibitory Control System - Suppress reflexive responses to noise.
    
    When the amygdala fires on a known false-alarm pattern,
    inhibitory control engages and overrides the de-risk cascade.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Active inhibition signals
        self._active_inhibitions: Dict[str, InhibitionSignal] = {}
        
        # Known false-alarm patterns
        self._false_alarm_patterns: Dict[str, float] = {}  # pattern -> frequency
        
        # Inhibition thresholds
        self._response_threshold = 0.7
        self._interference_threshold = 0.5
    
    def create_inhibition(
        self,
        target: str,
        inhibition_type: InhibitionType,
        strength: float,
        reason: str,
        duration_seconds: float = 60.0
    ) -> InhibitionSignal:
        """Create an inhibition signal."""
        with self._lock:
            signal = InhibitionSignal(
                signal_id=f"inhib_{int(time.time()*1000)}",
                inhibition_type=inhibition_type,
                target=target,
                strength=min(1.0, max(0.0, strength)),
                reason=reason,
                timestamp=datetime.utcnow(),
                duration=timedelta(seconds=duration_seconds),
            )
            
            self._active_inhibitions[signal.signal_id] = signal
            logger.info(f"Inhibition created: {target} - {reason}")
            
            return signal
    
    def check_inhibition(self, target: str) -> Tuple[bool, float]:
        """
        Check if a target is currently inhibited.
        
        Returns:
            Tuple of (is_inhibited, inhibition_strength)
        """
        with self._lock:
            self._cleanup_expired()
            
            max_strength = 0.0
            for signal in self._active_inhibitions.values():
                if signal.target == target and signal.active:
                    max_strength = max(max_strength, signal.strength)
            
            is_inhibited = max_strength > self._response_threshold
            return is_inhibited, max_strength
    
    def should_inhibit_amygdala_response(
        self,
        trigger_pattern: str,
        amygdala_strength: float
    ) -> bool:
        """
        Determine if an amygdala response should be inhibited.
        
        If the trigger pattern is a known false-alarm, inhibit.
        """
        with self._lock:
            # Check if pattern is known false-alarm
            false_alarm_freq = self._false_alarm_patterns.get(trigger_pattern, 0.0)
            
            # Higher false-alarm frequency = stronger inhibition
            if false_alarm_freq > 0.5:
                # Create inhibition
                self.create_inhibition(
                    target="amygdala_response",
                    inhibition_type=InhibitionType.RESPONSE_INHIBITION,
                    strength=false_alarm_freq,
                    reason=f"Known false-alarm pattern: {trigger_pattern}",
                    duration_seconds=300.0,
                )
                return True
            
            return False
    
    def register_false_alarm(self, pattern: str):
        """Register a pattern as a false alarm (for learning)."""
        with self._lock:
            current = self._false_alarm_patterns.get(pattern, 0.0)
            # Exponential moving average
            self._false_alarm_patterns[pattern] = 0.9 * current + 0.1 * 1.0
    
    def register_true_alarm(self, pattern: str):
        """Register a pattern as a true alarm (for learning)."""
        with self._lock:
            current = self._false_alarm_patterns.get(pattern, 0.0)
            # Exponential moving average toward 0
            self._false_alarm_patterns[pattern] = 0.9 * current
    
    def _cleanup_expired(self):
        """Remove expired inhibition signals."""
        now = datetime.utcnow()
        expired = []
        
        for sig_id, signal in self._active_inhibitions.items():
            if now > signal.timestamp + signal.duration:
                expired.append(sig_id)
        
        for sig_id in expired:
            del self._active_inhibitions[sig_id]
    
    def get_active_inhibitions(self) -> List[InhibitionSignal]:
        """Get all active inhibition signals."""
        with self._lock:
            self._cleanup_expired()
            return list(self._active_inhibitions.values())


class ExecutiveControl:
    """
    Executive Control System - coordinates all PFC functions.
    
    Implements cognitive control allocation based on task demands.
    """
    
    def __init__(self, working_memory: WorkingMemory):
        self._working_memory = working_memory
        self._lock = threading.RLock()
        
        # Control allocation
        self._control_budget = 1.0  # Total cognitive control available
        self._allocated_control: Dict[str, float] = {}
        
        # Task demands
        self._active_tasks: Dict[str, float] = {}  # task -> demand
    
    def allocate_control(self, task: str, demand: float) -> float:
        """
        Allocate cognitive control to a task.
        
        Returns actual allocation (may be less than demand if budget exhausted).
        """
        with self._lock:
            available = self._control_budget - sum(self._allocated_control.values())
            allocation = min(demand, available)
            
            if allocation > 0:
                self._allocated_control[task] = allocation
                self._active_tasks[task] = demand
            
            return allocation
    
    def release_control(self, task: str):
        """Release control allocated to a task."""
        with self._lock:
            if task in self._allocated_control:
                del self._allocated_control[task]
            if task in self._active_tasks:
                del self._active_tasks[task]
    
    def get_available_control(self) -> float:
        """Get available cognitive control."""
        with self._lock:
            return self._control_budget - sum(self._allocated_control.values())


class PrefrontalCortex:
    """
    The complete Prefrontal Cortex - integrates all PFC subregions.
    
    Coordinates:
    - Working Memory (active context)
    - dlPFC (deliberative reasoning)
    - vmPFC (risk-value integration)
    - OFC (expected value updates)
    - Inhibitory Control (suppress noise responses)
    - Executive Control (cognitive resource allocation)
    """
    
    def __init__(self):
        # Initialize components
        self.working_memory = WorkingMemory()
        self.dlpfc = DorsolateralPFC(self.working_memory)
        self.vmpfc = VentromedialPFC(self.working_memory)
        self.ofc = OrbitofrontalCortex()
        self.inhibitory_control = InhibitoryControl()
        self.executive_control = ExecutiveControl(self.working_memory)
        
        self._lock = threading.RLock()
        
        logger.info("Prefrontal Cortex initialized - all subregions active")
    
    def process_decision(
        self,
        signal: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        regime: str
    ) -> Dict[str, Any]:
        """
        Process a trading decision through the PFC.
        
        Integrates all PFC functions:
        1. Update working memory with current state
        2. Check inhibitory control
        3. Deliberate on strategy allocation
        4. Integrate risk-value
        5. Update expected values
        """
        with self._lock:
            result = {
                'approved': True,
                'allocation': {},
                'inhibited': False,
                'override': False,
                'reasoning': [],
            }
            
            # 1. Update working memory
            self.working_memory.update_portfolio_state(portfolio_state)
            self.working_memory.store(
                item_id="current_signal",
                item_type="signal",
                content=signal,
                priority=signal.get('confidence', 0.5),
            )
            
            # 2. Check inhibitory control
            signal_type = signal.get('type', 'unknown')
            is_inhibited, strength = self.inhibitory_control.check_inhibition(signal_type)
            
            if is_inhibited:
                result['approved'] = False
                result['inhibited'] = True
                result['reasoning'].append(f"Signal inhibited (strength: {strength:.2f})")
                return result
            
            # 3. Deliberate on allocation
            total_capital = portfolio_state.get('total_capital', 1000000)
            allocation = self.dlpfc.deliberate_allocation(regime, total_capital)
            result['allocation'] = allocation
            result['reasoning'].append(f"Allocated to {len(allocation)} strategies")
            
            # 4. Risk-value integration
            position_values = portfolio_state.get('position_values', {})
            position_risks = portfolio_state.get('position_risks', {})
            
            risk_adj_value, should_override = self.vmpfc.integrate_value(
                position_values, position_risks
            )
            
            if should_override:
                result['override'] = True
                result['reasoning'].append(
                    f"vmPFC override: risk-adjusted value {risk_adj_value:.4f}"
                )
            
            # 5. Update expected values based on recent outcomes
            recent_outcome = signal.get('recent_outcome')
            if recent_outcome is not None:
                context = f"{signal_type}_{regime}"
                update = self.ofc.update_expected_value(context, recent_outcome)
                result['reasoning'].append(
                    f"OFC update: prediction error {update.prediction_error:.4f}"
                )
            
            return result
    
    def inhibit_amygdala_response(
        self,
        trigger_pattern: str,
        amygdala_strength: float
    ) -> bool:
        """
        Attempt to inhibit an amygdala response.
        
        Returns True if inhibition was applied.
        """
        return self.inhibitory_control.should_inhibit_amygdala_response(
            trigger_pattern, amygdala_strength
        )
    
    def register_strategy(
        self,
        strategy_id: str,
        name: str,
        expected_sharpe: float,
        regime_conditions: List[str]
    ) -> bool:
        """Register a new strategy in working memory."""
        return self.dlpfc.register_strategy(
            strategy_id, name, expected_sharpe, regime_conditions
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get PFC status."""
        return {
            'working_memory': self.working_memory.get_status(),
            'active_strategies': len(self.dlpfc.get_active_strategies()),
            'risk_adjusted_value': self.vmpfc._risk_adjusted_value,
            'active_inhibitions': len(self.inhibitory_control.get_active_inhibitions()),
            'available_control': self.executive_control.get_available_control(),
            'ofc_surprise_stats': self.ofc.get_surprise_statistics(),
        }
