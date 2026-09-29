"""
Market Intent Decomposition Engine (MIDE) - Orchestrator

Master coordinator that integrates all MIDE components:
- Feature extraction
- Intent inference
- Transition logic
- Momentum tracking
- Visualization
- Strategy integration

This is the main entry point for MIDE.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Callable, Deque
from collections import deque
import time
import logging

from .intent_decomposition_core import (
    IntentSimplex, IntentState, IntentTransition, IntentPhase,
    ObservableFeatures, MIDEConfig, INTENT_NAMES, INTENT_COLORS,
    IntentRibbonSlice, IntentVisualization
)
from .intent_feature_extractor import IntentFeatureExtractor
from .intent_inference_engine import IntentInferenceEngine
from .intent_transition_logic import IntentTransitionLogic, TransitionValidator
from .intent_momentum_tracker import IntentMomentumTracker, IntentLifecycleAnalyzer


logger = logging.getLogger(__name__)


# =============================================================================
# PERFORMANCE METRICS
# =============================================================================

@dataclass
class MIDEPerformanceMetrics:
    """Performance metrics for MIDE."""
    avg_inference_latency_ms: float = 0.0
    avg_feature_extraction_ms: float = 0.0
    avg_total_latency_ms: float = 0.0
    updates_per_second: float = 0.0
    memory_usage_kb: float = 0.0
    
    # Quality metrics
    avg_confidence: float = 0.0
    avg_stability: float = 0.0
    transition_rate: float = 0.0  # Transitions per 100 bars
    
    # Validation
    constraint_violations: int = 0
    impossible_states_suppressed: int = 0


# =============================================================================
# STRATEGY INTEGRATION
# =============================================================================

@dataclass
class IntentGuidance:
    """
    Guidance for strategy based on intent state.
    """
    # Entry guidance
    should_enter: bool = False
    entry_reason: str = ""
    entry_confidence: float = 0.0
    
    # Exit guidance
    should_exit: bool = False
    exit_reason: str = ""
    exit_urgency: float = 0.0
    
    # Sizing guidance
    size_multiplier: float = 1.0
    size_reason: str = ""
    
    # Execution guidance
    execution_urgency: float = 0.5
    execution_algo: str = "default"
    max_spread_cross_bps: float = 1.0
    
    # Risk guidance
    risk_adjustment: float = 1.0
    risk_reason: str = ""


class IntentStrategyAdapter:
    """
    Adapts intent state to strategy guidance.
    """
    
    def __init__(self, config: Optional[MIDEConfig] = None):
        self.config = config or MIDEConfig()
    
    def get_entry_guidance(self, state: IntentState, 
                           signal_direction: str,
                           signal_strength: float) -> Tuple[bool, str, float]:
        """
        Get entry guidance based on intent.
        
        Args:
            state: Current intent state
            signal_direction: 'long' or 'short'
            signal_strength: Signal strength (0-1)
        
        Returns:
            Tuple of (should_enter, reason, confidence)
        """
        pi = state.simplex.to_array()
        
        # Block if exploitative dominant (likely to fade)
        if state.dominant_intent == 'exploitative' and pi[3] > 0.4:
            return False, "Exploitative flow dominant - likely mean reversion", 0.0
        
        # Block if noise dominant (no edge)
        if state.dominant_intent == 'noise' and pi[4] > 0.5:
            return False, "Noise dominant - no directional edge", 0.0
        
        # Favor if urgent directional aligns
        if state.dominant_intent == 'urgent' and pi[0] > 0.4:
            phase = state.get_intent_phase('urgent')
            if phase in [IntentPhase.EMERGING, IntentPhase.BUILDING, IntentPhase.SUSTAINED]:
                return True, "Urgent directional flow - momentum entry", state.confidence
        
        # Favor if passive accumulation detected
        if state.dominant_intent == 'passive' and pi[1] > 0.35:
            if state.persistence.values[1] > 0.5:
                return True, "Passive accumulation - institutional flow", state.confidence * 0.9
        
        # Default: allow if signal strong enough
        if signal_strength > 0.7 and state.confidence > 0.2:
            return True, "Signal strong with reasonable intent clarity", state.confidence * 0.7
        
        return False, "Intent unclear - wait for better setup", 0.0
    
    def get_exit_guidance(self, state: IntentState,
                          entry_intent: str,
                          position_bars: int) -> Tuple[bool, str, float]:
        """
        Get exit guidance based on intent change.
        
        Args:
            state: Current intent state
            entry_intent: Intent at entry
            position_bars: Bars since entry
        
        Returns:
            Tuple of (should_exit, reason, urgency)
        """
        pi = state.simplex.to_array()
        
        # Exit if supporting intent exhausted
        if entry_intent == 'urgent':
            if state.exhaustion.values[0] > 0.7:
                return True, "Urgent flow exhausted", 0.8
            if state.get_intent_phase('urgent') == IntentPhase.FADING:
                return True, "Urgent flow fading", 0.7
        
        if entry_intent == 'passive':
            phase = state.get_intent_phase('passive')
            if phase in [IntentPhase.EXHAUSTING, IntentPhase.FADING]:
                return True, "Passive accumulation ending", 0.6
        
        # Exit if exploitative becomes dominant (reversal likely)
        if pi[3] > 0.5 and state.momentum.values[3] > 0.05:
            return True, "Exploitative flow emerging - reversal risk", 0.9
        
        # Exit if intent becomes unclear
        if state.confidence < 0.1 and state.stability_score < 0.3:
            return True, "Intent unclear - reduce exposure", 0.5
        
        # Time-based exit for noise
        if entry_intent == 'noise' and position_bars > 20:
            return True, "Noise entry - time limit reached", 0.4
        
        return False, "", 0.0
    
    def get_size_multiplier(self, state: IntentState) -> Tuple[float, str]:
        """
        Get position size multiplier based on intent.
        
        Returns:
            Tuple of (multiplier, reason)
        """
        # Base on confidence
        confidence_mult = 0.5 + state.confidence
        
        # Adjust for stability
        stability_mult = 0.7 + 0.3 * state.stability_score
        
        # Adjust for intent type
        intent_mult = {
            'urgent': 1.2,
            'passive': 1.0,
            'mechanical': 0.8,
            'exploitative': 0.6,
            'noise': 0.5
        }[state.dominant_intent]
        
        # Adjust for exhaustion
        dominant_idx = INTENT_NAMES.index(state.dominant_intent)
        exhaustion_mult = 1.0 - 0.5 * state.exhaustion.values[dominant_idx]
        
        # Combine
        multiplier = confidence_mult * stability_mult * intent_mult * exhaustion_mult
        multiplier = np.clip(multiplier, 0.25, 1.5)
        
        reason = f"{state.dominant_intent} intent (conf={state.confidence:.2f}, stab={state.stability_score:.2f})"
        
        return float(multiplier), reason
    
    def get_execution_params(self, state: IntentState) -> Dict:
        """
        Get execution parameters based on intent.
        
        Returns:
            Dict with execution parameters
        """
        pi = state.simplex.to_array()
        
        # Urgent dominant: Be aggressive
        if pi[0] > 0.4:
            return {
                'algo': 'aggressive_twap',
                'urgency': 0.8,
                'max_spread_cross_bps': 2.0,
                'participation_rate': 0.3,
                'reason': 'Urgent flow - execute quickly'
            }
        
        # Passive dominant: Be patient
        if pi[1] > 0.4:
            return {
                'algo': 'passive_pov',
                'urgency': 0.3,
                'max_spread_cross_bps': 0.5,
                'participation_rate': 0.1,
                'reason': 'Passive flow - blend in'
            }
        
        # Mechanical dominant: Match rhythm
        if pi[2] > 0.4:
            return {
                'algo': 'scheduled_twap',
                'urgency': 0.5,
                'max_spread_cross_bps': 1.0,
                'participation_rate': 0.15,
                'reason': 'Mechanical flow - regular intervals'
            }
        
        # Exploitative dominant: Be very careful
        if pi[3] > 0.4:
            return {
                'algo': 'passive_limit',
                'urgency': 0.2,
                'max_spread_cross_bps': 0.3,
                'participation_rate': 0.05,
                'reason': 'Exploitative flow - minimize footprint'
            }
        
        # Default
        return {
            'algo': 'adaptive_twap',
            'urgency': 0.5,
            'max_spread_cross_bps': 1.0,
            'participation_rate': 0.15,
            'reason': 'Mixed intent - adaptive execution'
        }
    
    def get_full_guidance(self, state: IntentState,
                          signal_direction: str = 'long',
                          signal_strength: float = 0.5,
                          entry_intent: Optional[str] = None,
                          position_bars: int = 0) -> IntentGuidance:
        """
        Get complete guidance for strategy.
        """
        guidance = IntentGuidance()
        
        # Entry
        should_enter, entry_reason, entry_conf = self.get_entry_guidance(
            state, signal_direction, signal_strength
        )
        guidance.should_enter = should_enter
        guidance.entry_reason = entry_reason
        guidance.entry_confidence = entry_conf
        
        # Exit (if in position)
        if entry_intent:
            should_exit, exit_reason, exit_urgency = self.get_exit_guidance(
                state, entry_intent, position_bars
            )
            guidance.should_exit = should_exit
            guidance.exit_reason = exit_reason
            guidance.exit_urgency = exit_urgency
        
        # Sizing
        size_mult, size_reason = self.get_size_multiplier(state)
        guidance.size_multiplier = size_mult
        guidance.size_reason = size_reason
        
        # Execution
        exec_params = self.get_execution_params(state)
        guidance.execution_urgency = exec_params['urgency']
        guidance.execution_algo = exec_params['algo']
        guidance.max_spread_cross_bps = exec_params['max_spread_cross_bps']
        
        return guidance


# =============================================================================
# MIDE ORCHESTRATOR
# =============================================================================

class IntentOrchestrator:
    """
    Master orchestrator for Market Intent Decomposition Engine.
    
    Usage:
        mide = IntentOrchestrator()
        
        # Update with market data
        state = mide.update(
            price=50000.0,
            volume=100.0,
            bid=49995.0,
            ask=50005.0,
            bid_size=50.0,
            ask_size=30.0
        )
        
        # Get strategy guidance
        guidance = mide.get_guidance(signal_direction='long', signal_strength=0.7)
        
        # Get visualization
        viz = mide.get_visualization()
    """
    
    def __init__(self, config: Optional[MIDEConfig] = None):
        self.config = config or MIDEConfig()
        
        # Core components
        self.feature_extractor = IntentFeatureExtractor(self.config)
        self.inference_engine = IntentInferenceEngine(self.config)
        self.transition_logic = IntentTransitionLogic(self.config)
        self.momentum_tracker = IntentMomentumTracker(self.config)
        
        # Strategy adapter
        self.strategy_adapter = IntentStrategyAdapter(self.config)
        
        # Validation
        self.validator = TransitionValidator()
        self.lifecycle_analyzer = IntentLifecycleAnalyzer()
        
        # State
        self._current_state: Optional[IntentState] = None
        self._state_history: Deque[IntentState] = deque(maxlen=200)
        self._feature_history: Deque[np.ndarray] = deque(maxlen=self.config.feature_window)
        
        # Metrics
        self._metrics = MIDEPerformanceMetrics()
        self._update_count = 0
        self._start_time = time.time()
        
        # Callbacks
        self._on_transition_callbacks: List[Callable] = []
        self._on_phase_change_callbacks: List[Callable] = []
        
        logger.info("MIDE Orchestrator initialized")
    
    def update(self, price: float, volume: float,
               bid: float, ask: float,
               bid_size: float = 0.0, ask_size: float = 0.0,
               timestamp: Optional[float] = None) -> IntentState:
        """
        Update MIDE with new market data.
        
        Args:
            price: Trade price
            volume: Trade volume
            bid: Best bid price
            ask: Best ask price
            bid_size: Best bid size (optional)
            ask_size: Best ask size (optional)
            timestamp: Timestamp (optional, uses current time if not provided)
        
        Returns:
            Updated IntentState
        """
        start_time = time.perf_counter()
        timestamp = timestamp or time.time()
        
        # Step 1: Add data to feature extractor
        self.feature_extractor.add_trade(price, volume, timestamp, bid, ask)
        if bid_size > 0 or ask_size > 0:
            self.feature_extractor.add_quote(bid, ask, bid_size, ask_size, timestamp)
        
        # Step 2: Extract features
        feature_start = time.perf_counter()
        features = self.feature_extractor.extract_features()
        feature_time = (time.perf_counter() - feature_start) * 1000
        
        # Step 3: Build feature sequence
        self._feature_history.append(features.to_array())
        if len(self._feature_history) < 10:
            # Not enough history, return default state
            return self._get_default_state(timestamp)
        
        feature_sequence = np.array(list(self._feature_history))
        
        # Pad if needed
        if len(feature_sequence) < self.config.feature_window:
            padding = np.zeros((self.config.feature_window - len(feature_sequence), 12))
            feature_sequence = np.vstack([padding, feature_sequence])
        
        # Step 4: Run inference
        inference_start = time.perf_counter()
        raw_simplex, inference_time = self.inference_engine.infer(feature_sequence)
        
        # Step 5: Apply transition constraints
        constrained_simplex, transition_type, bars_in_state = self.transition_logic.process(
            raw_simplex, features, price
        )
        
        # Step 6: Update momentum tracker
        state = self.momentum_tracker.update(constrained_simplex)
        state.timestamp = timestamp
        state.inference_latency_ms = inference_time
        state.transition_type = transition_type
        state.bars_in_state = bars_in_state
        
        # Step 7: Validate
        prev_simplex = self._current_state.simplex if self._current_state else None
        warnings = self.validator.validate(constrained_simplex, prev_simplex)
        if warnings:
            for w in warnings:
                logger.warning(f"MIDE validation: {w}")
        
        # Step 8: Record lifecycle
        phases = self.momentum_tracker.get_all_phases()
        self.lifecycle_analyzer.record(phases, self._update_count)
        
        # Step 9: Fire callbacks
        if self._current_state and transition_type != IntentTransition.STABLE:
            self._fire_transition_callbacks(
                self._current_state.dominant_intent,
                state.dominant_intent,
                transition_type
            )
        
        # Update state
        self._current_state = state
        self._state_history.append(state)
        self._update_count += 1
        
        # Update metrics
        total_time = (time.perf_counter() - start_time) * 1000
        self._update_metrics(feature_time, inference_time, total_time, state)
        
        return state
    
    def _get_default_state(self, timestamp: float) -> IntentState:
        """Get default state when not enough data."""
        state = IntentState(
            simplex=IntentSimplex(),
            timestamp=timestamp
        )
        self._current_state = state
        return state
    
    def _update_metrics(self, feature_time: float, inference_time: float,
                        total_time: float, state: IntentState):
        """Update performance metrics."""
        # Latency (EMA)
        alpha = 0.1
        self._metrics.avg_feature_extraction_ms = (
            alpha * feature_time + (1 - alpha) * self._metrics.avg_feature_extraction_ms
        )
        self._metrics.avg_inference_latency_ms = (
            alpha * inference_time + (1 - alpha) * self._metrics.avg_inference_latency_ms
        )
        self._metrics.avg_total_latency_ms = (
            alpha * total_time + (1 - alpha) * self._metrics.avg_total_latency_ms
        )
        
        # Throughput
        elapsed = time.time() - self._start_time
        if elapsed > 0:
            self._metrics.updates_per_second = self._update_count / elapsed
        
        # Quality
        self._metrics.avg_confidence = (
            alpha * state.confidence + (1 - alpha) * self._metrics.avg_confidence
        )
        self._metrics.avg_stability = (
            alpha * state.stability_score + (1 - alpha) * self._metrics.avg_stability
        )
        
        # Transitions
        if state.transition_type != IntentTransition.STABLE:
            self._metrics.transition_rate = (
                self._metrics.transition_rate * 0.99 + 1.0
            )
        else:
            self._metrics.transition_rate *= 0.99
    
    def _fire_transition_callbacks(self, from_intent: str, to_intent: str,
                                    transition_type: IntentTransition):
        """Fire transition callbacks."""
        for callback in self._on_transition_callbacks:
            try:
                callback(from_intent, to_intent, transition_type)
            except Exception as e:
                logger.error(f"Transition callback error: {e}")
    
    def get_state(self) -> Optional[IntentState]:
        """Get current intent state."""
        return self._current_state
    
    def get_guidance(self, signal_direction: str = 'long',
                     signal_strength: float = 0.5,
                     entry_intent: Optional[str] = None,
                     position_bars: int = 0) -> IntentGuidance:
        """
        Get strategy guidance based on current intent.
        
        Args:
            signal_direction: 'long' or 'short'
            signal_strength: Signal strength (0-1)
            entry_intent: Intent at entry (if in position)
            position_bars: Bars since entry (if in position)
        
        Returns:
            IntentGuidance with entry/exit/sizing/execution guidance
        """
        if self._current_state is None:
            return IntentGuidance()
        
        return self.strategy_adapter.get_full_guidance(
            self._current_state,
            signal_direction,
            signal_strength,
            entry_intent,
            position_bars
        )
    
    def get_visualization(self, lookback: int = 100) -> IntentVisualization:
        """
        Get visualization data for intent ribbon.
        
        Args:
            lookback: Number of bars to include
        
        Returns:
            IntentVisualization with ribbon slices and markers
        """
        viz = IntentVisualization()
        
        history = list(self._state_history)[-lookback:]
        
        for i, state in enumerate(history):
            # Create ribbon slice
            slice = IntentRibbonSlice(
                bar_index=i,
                probabilities=state.simplex.to_array(),
                dominant=state.dominant_intent,
                confidence=state.confidence,
                opacity=state.get_opacity(),
                momentum_direction=state.momentum.get_direction(
                    INTENT_NAMES.index(state.dominant_intent)
                ),
                is_transition=state.transition_type != IntentTransition.STABLE
            )
            viz.ribbon_slices.append(slice)
            
            # Add transition marker
            if state.transition_type != IntentTransition.STABLE and i > 0:
                prev_dominant = history[i-1].dominant_intent
                viz.transition_markers.append((i, prev_dominant, state.dominant_intent))
            
            # Add momentum arrow
            dominant_idx = INTENT_NAMES.index(state.dominant_intent)
            momentum_mag = abs(state.momentum.values[dominant_idx])
            if momentum_mag > 0.02:
                viz.momentum_arrows.append((i, state.dominant_intent, momentum_mag))
        
        return viz
    
    def get_metrics(self) -> MIDEPerformanceMetrics:
        """Get performance metrics."""
        return self._metrics
    
    def on_transition(self, callback: Callable):
        """Register callback for intent transitions."""
        self._on_transition_callbacks.append(callback)
    
    def get_phase(self, intent: str) -> IntentPhase:
        """Get current phase for intent."""
        return self.momentum_tracker.get_phase(intent)
    
    def get_all_phases(self) -> Dict[str, IntentPhase]:
        """Get phases for all intents."""
        return self.momentum_tracker.get_all_phases()
    
    def reset(self):
        """Reset all state."""
        self.feature_extractor.reset()
        self.transition_logic.reset()
        self.momentum_tracker.reset()
        self._current_state = None
        self._state_history.clear()
        self._feature_history.clear()
        self._update_count = 0
        self._start_time = time.time()
        logger.info("MIDE Orchestrator reset")


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_mide(config: Optional[MIDEConfig] = None) -> IntentOrchestrator:
    """Create MIDE orchestrator with optional config."""
    return IntentOrchestrator(config)


def quick_start() -> IntentOrchestrator:
    """Quick start with default config."""
    return IntentOrchestrator()
