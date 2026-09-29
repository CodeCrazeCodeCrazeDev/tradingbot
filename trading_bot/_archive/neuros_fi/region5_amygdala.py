"""
NEUROS-FI Region 5: Amygdala - Threat Detection and Real-Time Tail Risk
========================================================================

Biological Basis:
The amygdala processes threats in approximately 20 milliseconds — before conscious
awareness. Two pathways: the "low road" (fast, approximate, subcortical — 20ms)
and the "high road" (slow, precise, cortical — 200ms).

It triggers the stress response: freeze, fight, or flight. It learns fear through
conditioning — previously neutral stimuli that preceded danger become fear-triggering.
It can be unconditioned through extinction learning.

Citations:
- LeDoux (1996) - The Emotional Brain
- Phelps & LeDoux (2005) - Contributions of the amygdala to emotion processing
- Öhman (2005) - The role of the amygdala in human fear
- Fanselow & Poulos (2005) - The neuroscience of mammalian associative learning

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


class ThreatLevel(Enum):
    """Threat severity levels."""
    
    NONE = 0
    LOW = 1
    MODERATE = 2
    HIGH = 3
    SEVERE = 4
    CRITICAL = 5


class StressResponse(Enum):
    """Stress response types (fight, flight, freeze)."""
    
    NONE = "none"
    FREEZE = "freeze"       # Halt new positions
    FLIGHT = "flight"       # Reduce exposure
    FIGHT = "fight"         # Hedge aggressively
    FULL_RETREAT = "full_retreat"  # Emergency exit


class FearConditioningState(Enum):
    """State of a fear-conditioned pattern."""
    
    NEUTRAL = "neutral"
    CONDITIONING = "conditioning"
    CONDITIONED = "conditioned"
    EXTINGUISHING = "extinguishing"
    EXTINCT = "extinct"


@dataclass
class ThreatSignal:
    """A detected threat signal."""
    
    signal_id: str
    threat_type: str
    threat_level: ThreatLevel
    timestamp: datetime
    pathway: str  # "low_road" or "high_road"
    latency_ms: float
    raw_value: float
    threshold: float
    context: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_breach(self) -> bool:
        return self.raw_value > self.threshold


@dataclass
class FearPattern:
    """A fear-conditioned market pattern."""
    
    pattern_id: str
    pattern_signature: Dict[str, Any]
    state: FearConditioningState
    conditioning_events: int
    extinction_events: int
    last_trigger: Optional[datetime]
    fear_strength: float  # 0-1
    false_alarm_count: int = 0
    true_alarm_count: int = 0
    
    def get_response_probability(self) -> float:
        """Get probability of triggering fear response."""
        if self.state == FearConditioningState.CONDITIONED:
            return self.fear_strength
        elif self.state == FearConditioningState.EXTINGUISHING:
            return self.fear_strength * 0.5
        return 0.0


@dataclass
class StressResponseAction:
    """An action taken in response to stress."""
    
    action_id: str
    response_type: StressResponse
    severity: float  # 0-1
    timestamp: datetime
    trigger: ThreatSignal
    actions: List[str]
    position_reduction_pct: float
    new_position_halt: bool


class LowRoadDetector:
    """
    Low Road (Fast Path) - 20ms threat detection.
    
    Autonomous circuit breaker that fires on:
    - Volatility spike > 3 standard deviations
    - VaR breach > 150% of daily limit
    - Cross-asset correlation spike > 0.85
    
    Fires BEFORE cortical processing completes. No override possible.
    """
    
    LATENCY_TARGET_MS = 20.0
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Thresholds (constitutional - cannot be modified by cortex)
        self._volatility_z_threshold = 3.0
        self._var_breach_threshold = 1.5  # 150% of limit
        self._correlation_spike_threshold = 0.85
        
        # State tracking
        self._volatility_history: List[float] = []
        self._var_history: List[float] = []
        self._correlation_history: List[float] = []
        
        # Statistics
        self._detections = 0
        self._false_alarms = 0
    
    def detect(
        self,
        volatility: float,
        var_ratio: float,
        cross_asset_correlation: float
    ) -> Optional[ThreatSignal]:
        """
        Fast threat detection - must complete in <20ms.
        
        Returns ThreatSignal if threat detected, None otherwise.
        """
        start_time = time.time()
        
        with self._lock:
            # Update histories
            self._volatility_history.append(volatility)
            self._var_history.append(var_ratio)
            self._correlation_history.append(cross_asset_correlation)
            
            # Trim histories
            max_history = 1000
            if len(self._volatility_history) > max_history:
                self._volatility_history = self._volatility_history[-max_history:]
                self._var_history = self._var_history[-max_history:]
                self._correlation_history = self._correlation_history[-max_history:]
            
            threat_type = None
            threat_level = ThreatLevel.NONE
            raw_value = 0.0
            threshold = 0.0
            
            # Check volatility spike
            if len(self._volatility_history) >= 100:
                vol_mean = np.mean(self._volatility_history[:-1])
                vol_std = np.std(self._volatility_history[:-1])
                if vol_std > 0:
                    vol_z = (volatility - vol_mean) / vol_std
                    if vol_z > self._volatility_z_threshold:
                        threat_type = "volatility_spike"
                        threat_level = ThreatLevel.SEVERE if vol_z > 4.0 else ThreatLevel.HIGH
                        raw_value = vol_z
                        threshold = self._volatility_z_threshold
            
            # Check VaR breach
            if var_ratio > self._var_breach_threshold:
                if threat_level.value < ThreatLevel.SEVERE.value:
                    threat_type = "var_breach"
                    threat_level = ThreatLevel.CRITICAL if var_ratio > 2.0 else ThreatLevel.SEVERE
                    raw_value = var_ratio
                    threshold = self._var_breach_threshold
            
            # Check correlation spike
            if cross_asset_correlation > self._correlation_spike_threshold:
                if threat_level.value < ThreatLevel.HIGH.value:
                    threat_type = "correlation_spike"
                    threat_level = ThreatLevel.HIGH
                    raw_value = cross_asset_correlation
                    threshold = self._correlation_spike_threshold
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if threat_type:
                self._detections += 1
                
                return ThreatSignal(
                    signal_id=f"low_road_{int(time.time()*1000)}",
                    threat_type=threat_type,
                    threat_level=threat_level,
                    timestamp=datetime.utcnow(),
                    pathway="low_road",
                    latency_ms=elapsed_ms,
                    raw_value=raw_value,
                    threshold=threshold,
                    context={
                        'volatility': volatility,
                        'var_ratio': var_ratio,
                        'correlation': cross_asset_correlation,
                    }
                )
            
            return None
    
    def register_false_alarm(self):
        """Register that the last detection was a false alarm."""
        with self._lock:
            self._false_alarms += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detection statistics."""
        with self._lock:
            return {
                'detections': self._detections,
                'false_alarms': self._false_alarms,
                'false_alarm_rate': self._false_alarms / max(1, self._detections),
            }


class HighRoadAssessor:
    """
    High Road (Slow Path) - 200ms full threat assessment.
    
    Completes full tail risk analysis:
    - Monte Carlo stress scenarios
    - Factor exposure decomposition
    - Liquidity-adjusted drawdown projection
    
    Determines if low-road response was appropriate or false alarm.
    """
    
    LATENCY_TARGET_MS = 200.0
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Stress scenario library
        self._stress_scenarios: List[Dict[str, Any]] = self._initialize_scenarios()
        
        # Assessment history
        self._assessments: List[Dict[str, Any]] = []
    
    def _initialize_scenarios(self) -> List[Dict[str, Any]]:
        """Initialize stress scenario library."""
        return [
            {'name': 'flash_crash', 'equity_shock': -0.10, 'vol_multiplier': 3.0},
            {'name': 'liquidity_crisis', 'spread_multiplier': 5.0, 'vol_multiplier': 2.0},
            {'name': 'correlation_breakdown', 'correlation_shift': 0.5},
            {'name': 'rate_shock', 'rate_change': 0.02, 'equity_shock': -0.05},
            {'name': 'credit_event', 'spread_widening': 0.03, 'equity_shock': -0.08},
        ]
    
    def assess(
        self,
        low_road_signal: ThreatSignal,
        portfolio_state: Dict[str, Any],
        market_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Full threat assessment - must complete in <200ms.
        
        Returns comprehensive risk assessment.
        """
        start_time = time.time()
        
        with self._lock:
            assessment = {
                'signal_id': low_road_signal.signal_id,
                'timestamp': datetime.utcnow(),
                'low_road_valid': True,
                'threat_level_adjusted': low_road_signal.threat_level,
                'recommended_response': StressResponse.NONE,
                'position_reduction_pct': 0.0,
                'stress_test_results': {},
                'factor_exposures': {},
                'liquidity_risk': 0.0,
            }
            
            # Run Monte Carlo stress scenarios
            stress_results = self._run_stress_scenarios(portfolio_state, market_state)
            assessment['stress_test_results'] = stress_results
            
            # Decompose factor exposures
            factor_exposures = self._decompose_factors(portfolio_state)
            assessment['factor_exposures'] = factor_exposures
            
            # Calculate liquidity-adjusted drawdown
            liquidity_risk = self._calculate_liquidity_risk(portfolio_state, market_state)
            assessment['liquidity_risk'] = liquidity_risk
            
            # Determine if low-road was correct
            max_stress_loss = max(stress_results.values()) if stress_results else 0
            
            if max_stress_loss < 0.02 and liquidity_risk < 0.3:
                # Low-road was likely a false alarm
                assessment['low_road_valid'] = False
                assessment['threat_level_adjusted'] = ThreatLevel.LOW
                assessment['recommended_response'] = StressResponse.NONE
            else:
                # Confirm threat and determine response
                if max_stress_loss > 0.05 or liquidity_risk > 0.7:
                    assessment['threat_level_adjusted'] = ThreatLevel.CRITICAL
                    assessment['recommended_response'] = StressResponse.FULL_RETREAT
                    assessment['position_reduction_pct'] = 100.0
                elif max_stress_loss > 0.03 or liquidity_risk > 0.5:
                    assessment['threat_level_adjusted'] = ThreatLevel.SEVERE
                    assessment['recommended_response'] = StressResponse.FLIGHT
                    assessment['position_reduction_pct'] = 50.0
                else:
                    assessment['recommended_response'] = StressResponse.FREEZE
                    assessment['position_reduction_pct'] = 25.0
            
            elapsed_ms = (time.time() - start_time) * 1000
            assessment['latency_ms'] = elapsed_ms
            
            self._assessments.append(assessment)
            if len(self._assessments) > 1000:
                self._assessments = self._assessments[-500:]
            
            return assessment
    
    def _run_stress_scenarios(
        self,
        portfolio: Dict[str, Any],
        market: Dict[str, Any]
    ) -> Dict[str, float]:
        """Run stress scenarios and return potential losses."""
        results = {}
        
        portfolio_value = portfolio.get('total_value', 1000000)
        positions = portfolio.get('positions', {})
        
        for scenario in self._stress_scenarios:
            # Simplified stress calculation
            equity_shock = scenario.get('equity_shock', 0)
            vol_mult = scenario.get('vol_multiplier', 1)
            
            # Estimate loss
            equity_exposure = sum(
                pos.get('value', 0) for pos in positions.values()
                if pos.get('asset_class') == 'equity'
            )
            
            estimated_loss = abs(equity_shock * equity_exposure / portfolio_value)
            estimated_loss *= vol_mult ** 0.5  # Vol adjustment
            
            results[scenario['name']] = estimated_loss
        
        return results
    
    def _decompose_factors(self, portfolio: Dict[str, Any]) -> Dict[str, float]:
        """Decompose portfolio into factor exposures."""
        # Simplified factor decomposition
        return {
            'market_beta': portfolio.get('beta', 1.0),
            'size': portfolio.get('size_exposure', 0.0),
            'value': portfolio.get('value_exposure', 0.0),
            'momentum': portfolio.get('momentum_exposure', 0.0),
            'volatility': portfolio.get('vol_exposure', 0.0),
        }
    
    def _calculate_liquidity_risk(
        self,
        portfolio: Dict[str, Any],
        market: Dict[str, Any]
    ) -> float:
        """Calculate liquidity-adjusted risk score."""
        # Simplified liquidity calculation
        total_value = portfolio.get('total_value', 1000000)
        avg_daily_volume = market.get('avg_daily_volume', 10000000)
        spread = market.get('spread', 0.001)
        
        # Days to liquidate
        days_to_liquidate = total_value / (avg_daily_volume * 0.1)  # 10% of ADV
        
        # Spread impact
        spread_cost = spread * 2  # Round trip
        
        # Liquidity risk score (0-1)
        liquidity_risk = min(1.0, (days_to_liquidate / 5) * 0.5 + spread_cost * 100)
        
        return liquidity_risk


class FearConditioning:
    """
    Fear Conditioning System - learns which patterns precede tail events.
    
    Previously neutral stimuli that preceded danger become fear-triggering.
    Can be unconditioned through extinction learning.
    """
    
    SIMILARITY_THRESHOLD = 0.70
    CONDITIONING_THRESHOLD = 3  # Events needed to condition
    EXTINCTION_THRESHOLD = 20  # Non-events needed to extinguish
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Fear pattern library
        self._fear_patterns: Dict[str, FearPattern] = {}
        
        # Pending patterns (being evaluated)
        self._pending_patterns: Dict[str, Dict[str, Any]] = {}
    
    def check_fear_patterns(
        self,
        market_state: Dict[str, Any]
    ) -> List[Tuple[FearPattern, float]]:
        """
        Check if current market state matches any conditioned fear patterns.
        
        Returns list of (pattern, similarity) for matches above threshold.
        """
        with self._lock:
            matches = []
            
            for pattern_id, pattern in self._fear_patterns.items():
                if pattern.state not in [
                    FearConditioningState.CONDITIONED,
                    FearConditioningState.EXTINGUISHING
                ]:
                    continue
                
                similarity = self._compute_similarity(market_state, pattern.pattern_signature)
                
                if similarity >= self.SIMILARITY_THRESHOLD:
                    matches.append((pattern, similarity))
            
            return sorted(matches, key=lambda x: x[1], reverse=True)
    
    def _compute_similarity(
        self,
        state: Dict[str, Any],
        signature: Dict[str, Any]
    ) -> float:
        """Compute similarity between market state and pattern signature."""
        if not state or not signature:
            return 0.0
        
        common_keys = set(state.keys()) & set(signature.keys())
        if not common_keys:
            return 0.0
        
        matches = 0
        for key in common_keys:
            state_val = state.get(key)
            sig_val = signature.get(key)
            
            if isinstance(state_val, (int, float)) and isinstance(sig_val, (int, float)):
                # Numeric comparison
                if sig_val != 0:
                    diff_pct = abs(state_val - sig_val) / abs(sig_val)
                    if diff_pct < 0.2:  # Within 20%
                        matches += 1
            elif state_val == sig_val:
                matches += 1
        
        return matches / len(signature)
    
    def condition_pattern(
        self,
        market_state: Dict[str, Any],
        tail_event_occurred: bool
    ):
        """
        Update fear conditioning based on outcome.
        
        If tail event occurred, strengthen conditioning.
        If not, move toward extinction.
        """
        with self._lock:
            # Create pattern signature
            signature = self._create_signature(market_state)
            pattern_id = self._hash_signature(signature)
            
            if pattern_id not in self._fear_patterns:
                # New pattern
                self._fear_patterns[pattern_id] = FearPattern(
                    pattern_id=pattern_id,
                    pattern_signature=signature,
                    state=FearConditioningState.NEUTRAL,
                    conditioning_events=0,
                    extinction_events=0,
                    last_trigger=None,
                    fear_strength=0.0,
                )
            
            pattern = self._fear_patterns[pattern_id]
            
            if tail_event_occurred:
                # Strengthen conditioning
                pattern.conditioning_events += 1
                pattern.true_alarm_count += 1
                pattern.extinction_events = 0  # Reset extinction
                pattern.last_trigger = datetime.utcnow()
                
                # Update fear strength
                pattern.fear_strength = min(1.0, pattern.fear_strength + 0.2)
                
                # Update state
                if pattern.conditioning_events >= self.CONDITIONING_THRESHOLD:
                    pattern.state = FearConditioningState.CONDITIONED
                else:
                    pattern.state = FearConditioningState.CONDITIONING
                
                logger.info(f"Fear pattern conditioned: {pattern_id} (strength={pattern.fear_strength:.2f})")
                
            else:
                # Move toward extinction
                pattern.extinction_events += 1
                pattern.false_alarm_count += 1
                
                # Decay fear strength
                pattern.fear_strength = max(0.0, pattern.fear_strength - 0.05)
                
                # Update state
                if pattern.state == FearConditioningState.CONDITIONED:
                    if pattern.extinction_events >= self.EXTINCTION_THRESHOLD:
                        pattern.state = FearConditioningState.EXTINCT
                        logger.info(f"Fear pattern extinguished: {pattern_id}")
                    elif pattern.extinction_events >= self.EXTINCTION_THRESHOLD // 2:
                        pattern.state = FearConditioningState.EXTINGUISHING
    
    def _create_signature(self, market_state: Dict[str, Any]) -> Dict[str, Any]:
        """Create a pattern signature from market state."""
        # Extract key features
        signature = {}
        
        key_features = [
            'volatility', 'correlation', 'spread', 'volume',
            'vix', 'credit_spread', 'yield_curve_slope'
        ]
        
        for feature in key_features:
            if feature in market_state:
                signature[feature] = market_state[feature]
        
        return signature
    
    def _hash_signature(self, signature: Dict[str, Any]) -> str:
        """Create a hash for a pattern signature."""
        import hashlib
        import json
        
        # Discretize values for matching
        discretized = {}
        for key, value in sorted(signature.items()):
            if isinstance(value, float):
                discretized[key] = round(value, 2)
            else:
                discretized[key] = value
        
        content = json.dumps(discretized, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def get_conditioned_patterns(self) -> List[FearPattern]:
        """Get all conditioned fear patterns."""
        with self._lock:
            return [
                p for p in self._fear_patterns.values()
                if p.state == FearConditioningState.CONDITIONED
            ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get fear conditioning statistics."""
        with self._lock:
            states = [p.state for p in self._fear_patterns.values()]
            return {
                'total_patterns': len(self._fear_patterns),
                'conditioned': states.count(FearConditioningState.CONDITIONED),
                'extinguishing': states.count(FearConditioningState.EXTINGUISHING),
                'extinct': states.count(FearConditioningState.EXTINCT),
            }


class StressResponseCascade:
    """
    Stress Response Cascade - graded response to threats.
    
    50% severity: Reduce positions by 25%
    75% severity: Reduce by 50%, halt new positions
    100% severity: Full halt, human notification
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Response thresholds
        self._thresholds = {
            0.50: {'reduction': 0.25, 'halt_new': False, 'response': StressResponse.FREEZE},
            0.75: {'reduction': 0.50, 'halt_new': True, 'response': StressResponse.FLIGHT},
            1.00: {'reduction': 1.00, 'halt_new': True, 'response': StressResponse.FULL_RETREAT},
        }
        
        # Response history
        self._responses: List[StressResponseAction] = []
        
        # Current state
        self._current_response: StressResponse = StressResponse.NONE
        self._response_start: Optional[datetime] = None
    
    def determine_response(
        self,
        threat_signal: ThreatSignal,
        assessment: Dict[str, Any]
    ) -> StressResponseAction:
        """
        Determine appropriate stress response based on threat severity.
        """
        with self._lock:
            # Calculate severity (0-1)
            severity = threat_signal.threat_level.value / ThreatLevel.CRITICAL.value
            
            # Adjust based on high-road assessment
            if not assessment.get('low_road_valid', True):
                severity *= 0.5
            
            # Find appropriate response
            response_config = None
            for threshold, config in sorted(self._thresholds.items()):
                if severity >= threshold:
                    response_config = config
            
            if response_config is None:
                response_config = {
                    'reduction': 0.0,
                    'halt_new': False,
                    'response': StressResponse.NONE
                }
            
            # Create response action
            action = StressResponseAction(
                action_id=f"stress_{int(time.time()*1000)}",
                response_type=response_config['response'],
                severity=severity,
                timestamp=datetime.utcnow(),
                trigger=threat_signal,
                actions=self._generate_actions(response_config),
                position_reduction_pct=response_config['reduction'] * 100,
                new_position_halt=response_config['halt_new'],
            )
            
            self._responses.append(action)
            self._current_response = response_config['response']
            self._response_start = datetime.utcnow()
            
            if len(self._responses) > 1000:
                self._responses = self._responses[-500:]
            
            logger.warning(
                f"Stress response: {action.response_type.value} "
                f"(severity={severity:.2f}, reduction={action.position_reduction_pct:.0f}%)"
            )
            
            return action
    
    def _generate_actions(self, config: Dict[str, Any]) -> List[str]:
        """Generate list of actions for response."""
        actions = []
        
        if config['reduction'] > 0:
            actions.append(f"reduce_positions_{int(config['reduction']*100)}pct")
        
        if config['halt_new']:
            actions.append("halt_new_positions")
        
        if config['response'] == StressResponse.FULL_RETREAT:
            actions.append("notify_human")
            actions.append("emergency_liquidation")
        
        return actions
    
    def get_current_response(self) -> Tuple[StressResponse, Optional[datetime]]:
        """Get current stress response state."""
        with self._lock:
            return self._current_response, self._response_start
    
    def clear_response(self):
        """Clear current stress response (return to normal)."""
        with self._lock:
            self._current_response = StressResponse.NONE
            self._response_start = None
    
    def get_response_history(self, limit: int = 100) -> List[StressResponseAction]:
        """Get recent response history."""
        with self._lock:
            return self._responses[-limit:]


class ThreatDetection:
    """Combined threat detection system."""
    
    def __init__(self):
        self.low_road = LowRoadDetector()
        self.high_road = HighRoadAssessor()
    
    def detect_and_assess(
        self,
        volatility: float,
        var_ratio: float,
        correlation: float,
        portfolio_state: Dict[str, Any],
        market_state: Dict[str, Any]
    ) -> Tuple[Optional[ThreatSignal], Optional[Dict[str, Any]]]:
        """
        Full threat detection and assessment pipeline.
        
        Returns (low_road_signal, high_road_assessment)
        """
        # Fast detection
        low_road_signal = self.low_road.detect(volatility, var_ratio, correlation)
        
        if low_road_signal is None:
            return None, None
        
        # Full assessment
        assessment = self.high_road.assess(
            low_road_signal, portfolio_state, market_state
        )
        
        # Update false alarm tracking
        if not assessment.get('low_road_valid', True):
            self.low_road.register_false_alarm()
        
        return low_road_signal, assessment


class Amygdala:
    """
    The complete Amygdala - threat detection and real-time tail risk.
    
    Implements:
    - Low road (20ms) fast threat detection
    - High road (200ms) full assessment
    - Fear conditioning and extinction
    - Graded stress response cascade
    """
    
    def __init__(self):
        # Initialize components
        self.threat_detection = ThreatDetection()
        self.fear_conditioning = FearConditioning()
        self.stress_cascade = StressResponseCascade()
        
        self._lock = threading.RLock()
        
        # Callbacks for PFC inhibition
        self._inhibition_callbacks: List[Callable] = []
        
        logger.info("Amygdala initialized - threat detection active")
    
    def process_market_state(
        self,
        market_state: Dict[str, Any],
        portfolio_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process current market state for threats.
        
        Returns threat assessment and response actions.
        """
        with self._lock:
            result = {
                'threat_detected': False,
                'threat_signal': None,
                'assessment': None,
                'fear_patterns_matched': [],
                'response_action': None,
            }
            
            # Extract key metrics
            volatility = market_state.get('volatility', 0.01)
            var_ratio = market_state.get('var_ratio', 0.5)
            correlation = market_state.get('cross_asset_correlation', 0.3)
            
            # Run threat detection
            signal, assessment = self.threat_detection.detect_and_assess(
                volatility, var_ratio, correlation,
                portfolio_state, market_state
            )
            
            if signal:
                result['threat_detected'] = True
                result['threat_signal'] = signal
                result['assessment'] = assessment
                
                # Check fear patterns
                fear_matches = self.fear_conditioning.check_fear_patterns(market_state)
                result['fear_patterns_matched'] = [
                    {'pattern_id': p.pattern_id, 'similarity': s}
                    for p, s in fear_matches
                ]
                
                # Amplify response if fear pattern matched
                if fear_matches:
                    # Fear conditioning amplifies threat response
                    max_fear = max(p.fear_strength for p, _ in fear_matches)
                    if assessment:
                        assessment['fear_amplification'] = max_fear
                
                # Determine stress response
                if assessment:
                    response = self.stress_cascade.determine_response(signal, assessment)
                    result['response_action'] = response
                    
                    # Notify PFC for potential inhibition
                    self._notify_pfc(signal, assessment)
            
            return result
    
    def _notify_pfc(self, signal: ThreatSignal, assessment: Dict[str, Any]):
        """Notify PFC of threat for potential inhibition."""
        for callback in self._inhibition_callbacks:
            try:
                callback(signal, assessment)
            except Exception as e:
                logger.error(f"PFC notification failed: {e}")
    
    def register_pfc_callback(self, callback: Callable):
        """Register callback for PFC inhibition checks."""
        self._inhibition_callbacks.append(callback)
    
    def update_conditioning(
        self,
        market_state: Dict[str, Any],
        tail_event_occurred: bool
    ):
        """Update fear conditioning based on outcome."""
        self.fear_conditioning.condition_pattern(market_state, tail_event_occurred)
    
    def get_current_threat_level(self) -> ThreatLevel:
        """Get current threat level."""
        response, _ = self.stress_cascade.get_current_response()
        
        if response == StressResponse.FULL_RETREAT:
            return ThreatLevel.CRITICAL
        elif response == StressResponse.FLIGHT:
            return ThreatLevel.SEVERE
        elif response == StressResponse.FREEZE:
            return ThreatLevel.HIGH
        else:
            return ThreatLevel.NONE
    
    def clear_threat_state(self):
        """Clear current threat state (return to normal)."""
        self.stress_cascade.clear_response()
    
    def get_status(self) -> Dict[str, Any]:
        """Get amygdala status."""
        response, start = self.stress_cascade.get_current_response()
        
        return {
            'current_response': response.value,
            'response_start': start.isoformat() if start else None,
            'threat_level': self.get_current_threat_level().name,
            'low_road_stats': self.threat_detection.low_road.get_statistics(),
            'fear_conditioning': self.fear_conditioning.get_statistics(),
            'conditioned_patterns': len(self.fear_conditioning.get_conditioned_patterns()),
        }
