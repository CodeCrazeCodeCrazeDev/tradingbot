"""
Hawkes Process Module - Self-Exciting Point Process for Institutional Detection

Implements Hawkes Process models to detect "stealth accumulation" patterns
in order flow that precede institutional positioning.

Features:
- Self-exciting point process modeling
- Institutional order clustering detection
- Stealth accumulation pattern recognition
- Order flow event prediction
- Intensity function estimation
- Branching ratio analysis
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of market events"""
    TRADE = "trade"
    QUOTE_UPDATE = "quote_update"
    LARGE_ORDER = "large_order"
    ICEBERG_DETECTED = "iceberg_detected"
    CANCEL = "cancel"
    AGGRESSIVE_BUY = "aggressive_buy"
    AGGRESSIVE_SELL = "aggressive_sell"
    BLOCK_TRADE = "block_trade"
    SWEEP = "sweep"


class InstitutionalPattern(Enum):
    """Detected institutional patterns"""
    STEALTH_ACCUMULATION = "stealth_accumulation"
    STEALTH_DISTRIBUTION = "stealth_distribution"
    ICEBERG_SEQUENCE = "iceberg_sequence"
    LAYERING = "layering"
    SPOOFING = "spoofing"
    MOMENTUM_IGNITION = "momentum_ignition"
    QUOTE_STUFFING = "quote_stuffing"
    ABSORPTION = "absorption"


@dataclass
class MarketEvent:
    """Single market event for Hawkes process"""
    timestamp: datetime
    event_type: EventType
    price: float
    volume: float
    side: str  # BUY, SELL
    is_aggressive: bool = False
    order_id: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HawkesIntensity:
    """Hawkes process intensity at a point in time"""
    timestamp: datetime
    baseline_intensity: float  # μ (mu)
    excited_intensity: float  # Self-excited component
    total_intensity: float  # λ(t)
    branching_ratio: float  # n* = α/β
    expected_events: float  # Expected events in next window
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'baseline_intensity': self.baseline_intensity,
            'excited_intensity': self.excited_intensity,
            'total_intensity': self.total_intensity,
            'branching_ratio': self.branching_ratio,
            'expected_events': self.expected_events
        }


@dataclass
class InstitutionalSignal:
    """Detected institutional activity signal"""
    signal_id: str
    timestamp: datetime
    pattern: InstitutionalPattern
    confidence: float
    direction: str  # ACCUMULATION, DISTRIBUTION, NEUTRAL
    intensity_score: float
    clustering_score: float
    events_involved: int
    estimated_size: float
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'signal_id': self.signal_id,
            'timestamp': self.timestamp.isoformat(),
            'pattern': self.pattern.value,
            'confidence': self.confidence,
            'direction': self.direction,
            'intensity_score': self.intensity_score,
            'clustering_score': self.clustering_score,
            'events_involved': self.events_involved,
            'estimated_size': self.estimated_size,
            'reasoning': self.reasoning
        }


class HawkesKernel:
    """
    Exponential decay kernel for Hawkes process
    
    g(t) = α * exp(-β * t)
    
    Where:
    - α (alpha): Jump size / excitation magnitude
    - β (beta): Decay rate
    """
    
    def __init__(self, alpha: float = 0.5, beta: float = 1.0):
        self.alpha = alpha
        self.beta = beta
    
    def evaluate(self, t: float) -> float:
        """Evaluate kernel at time t"""
        if t < 0:
            return 0.0
        return self.alpha * np.exp(-self.beta * t)
    
    def integral(self, t: float) -> float:
        """Integral of kernel from 0 to t"""
        if t <= 0:
            return 0.0
        return (self.alpha / self.beta) * (1 - np.exp(-self.beta * t))
    
    @property
    def branching_ratio(self) -> float:
        """Branching ratio n* = α/β"""
        return self.alpha / self.beta if self.beta > 0 else float('inf')


class HawkesProcessDetector:
    """
    Hawkes Process Detector for Institutional Activity
    
    Uses self-exciting point processes to detect clustering
    of order flow events that indicate institutional activity.
    
    The intensity function is:
    λ(t) = μ + Σ g(t - t_i) for all t_i < t
    
    Where:
    - μ (mu): Baseline intensity
    - g(): Excitation kernel (exponential decay)
    - t_i: Past event times
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Hawkes parameters
        self.mu = self.config.get('baseline_intensity', 0.1)  # Baseline rate
        self.alpha = self.config.get('alpha', 0.5)  # Excitation magnitude
        self.beta = self.config.get('beta', 1.0)  # Decay rate
        
        # Create kernel
        self.kernel = HawkesKernel(self.alpha, self.beta)
        
        # Event history
        self.events: deque = deque(maxlen=10000)
        self.buy_events: deque = deque(maxlen=5000)
        self.sell_events: deque = deque(maxlen=5000)
        
        # Detection thresholds
        self.intensity_threshold = self.config.get('intensity_threshold', 2.0)
        self.clustering_threshold = self.config.get('clustering_threshold', 0.7)
        self.min_events_for_signal = self.config.get('min_events', 5)
        
        # Signal history
        self.signals: deque = deque(maxlen=1000)
        
        # Calibration data
        self.calibration_window = timedelta(hours=1)
        self.last_calibration: Optional[datetime] = None
        
        logger.info(f"HawkesProcessDetector initialized: μ={self.mu}, α={self.alpha}, β={self.beta}")
    
    def add_event(self, event: MarketEvent) -> Optional[InstitutionalSignal]:
        """
        Add a new market event and check for institutional patterns
        
        Returns signal if institutional activity detected
        """
        # Store event
        self.events.append(event)
        
        if event.side == 'BUY':
            self.buy_events.append(event)
        else:
            self.sell_events.append(event)
        
        # Calculate current intensity
        intensity = self.calculate_intensity(event.timestamp)
        
        # Check for institutional patterns
        signal = self._detect_institutional_pattern(event, intensity)
        
        if signal:
            self.signals.append(signal)
            logger.info(f"Institutional signal detected: {signal.pattern.value}, confidence={signal.confidence:.2f}")
        
        return signal
    
    def calculate_intensity(
        self,
        t: datetime,
        event_filter: Optional[EventType] = None,
        side_filter: Optional[str] = None
    ) -> HawkesIntensity:
        """
        Calculate Hawkes intensity at time t
        
        λ(t) = μ + Σ α * exp(-β * (t - t_i))
        """
        # Select events to consider
        if side_filter == 'BUY':
            events = list(self.buy_events)
        elif side_filter == 'SELL':
            events = list(self.sell_events)
        else:
            events = list(self.events)
        
        if event_filter:
            events = [e for e in events if e.event_type == event_filter]
        
        # Calculate excited intensity
        excited = 0.0
        for event in events:
            dt = (t - event.timestamp).total_seconds()
            if dt > 0:
                excited += self.kernel.evaluate(dt)
        
        total = self.mu + excited
        
        # Calculate expected events in next time window (e.g., 1 minute)
        window_seconds = 60
        expected = total * window_seconds
        
        return HawkesIntensity(
            timestamp=t,
            baseline_intensity=self.mu,
            excited_intensity=excited,
            total_intensity=total,
            branching_ratio=self.kernel.branching_ratio,
            expected_events=expected
        )
    
    def _detect_institutional_pattern(
        self,
        current_event: MarketEvent,
        intensity: HawkesIntensity
    ) -> Optional[InstitutionalSignal]:
        """Detect institutional patterns from event clustering"""
        import uuid
        
        # Check if intensity is elevated
        if intensity.total_intensity < self.mu * self.intensity_threshold:
            return None
        
        # Get recent events
        recent_window = timedelta(minutes=5)
        recent_events = [
            e for e in self.events
            if (current_event.timestamp - e.timestamp) < recent_window
        ]
        
        if len(recent_events) < self.min_events_for_signal:
            return None
        
        # Analyze event clustering
        pattern, confidence, direction = self._analyze_clustering(recent_events)
        
        if confidence < self.clustering_threshold:
            return None
        
        # Calculate metrics
        total_volume = sum(e.volume for e in recent_events)
        buy_volume = sum(e.volume for e in recent_events if e.side == 'BUY')
        sell_volume = sum(e.volume for e in recent_events if e.side == 'SELL')
        
        # Determine direction
        if buy_volume > sell_volume * 1.5:
            direction = "ACCUMULATION"
        elif sell_volume > buy_volume * 1.5:
            direction = "DISTRIBUTION"
        else:
            direction = "NEUTRAL"
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            pattern, recent_events, intensity, buy_volume, sell_volume
        )
        
        return InstitutionalSignal(
            signal_id=str(uuid.uuid4())[:8],
            timestamp=current_event.timestamp,
            pattern=pattern,
            confidence=confidence,
            direction=direction,
            intensity_score=intensity.total_intensity / self.mu,
            clustering_score=confidence,
            events_involved=len(recent_events),
            estimated_size=total_volume,
            reasoning=reasoning
        )
    
    def _analyze_clustering(
        self,
        events: List[MarketEvent]
    ) -> Tuple[InstitutionalPattern, float, str]:
        """Analyze event clustering to identify pattern type"""
        if not events:
            return InstitutionalPattern.ABSORPTION, 0.0, "NEUTRAL"
        
        # Calculate inter-arrival times
        timestamps = sorted([e.timestamp for e in events])
        inter_arrivals = []
        for i in range(1, len(timestamps)):
            dt = (timestamps[i] - timestamps[i-1]).total_seconds()
            inter_arrivals.append(dt)
        
        if not inter_arrivals:
            return InstitutionalPattern.ABSORPTION, 0.0, "NEUTRAL"
        
        # Analyze patterns
        mean_iat = np.mean(inter_arrivals)
        std_iat = np.std(inter_arrivals) if len(inter_arrivals) > 1 else 0
        cv = std_iat / mean_iat if mean_iat > 0 else 0  # Coefficient of variation
        
        # Count event types
        large_orders = sum(1 for e in events if e.event_type == EventType.LARGE_ORDER)
        icebergs = sum(1 for e in events if e.event_type == EventType.ICEBERG_DETECTED)
        cancels = sum(1 for e in events if e.event_type == EventType.CANCEL)
        aggressive = sum(1 for e in events if e.is_aggressive)
        
        # Volume analysis
        volumes = [e.volume for e in events]
        volume_trend = np.polyfit(range(len(volumes)), volumes, 1)[0] if len(volumes) > 1 else 0
        
        # Pattern detection logic
        pattern = InstitutionalPattern.ABSORPTION
        confidence = 0.5
        
        # Stealth accumulation: Regular small orders with occasional large ones
        if cv < 0.5 and large_orders > 0 and icebergs > 0:
            pattern = InstitutionalPattern.STEALTH_ACCUMULATION
            confidence = 0.7 + 0.1 * min(icebergs, 3)
        
        # Iceberg sequence: Multiple iceberg detections
        elif icebergs >= 3:
            pattern = InstitutionalPattern.ICEBERG_SEQUENCE
            confidence = 0.6 + 0.1 * min(icebergs, 4)
        
        # Layering: High cancel ratio
        elif cancels > len(events) * 0.3:
            pattern = InstitutionalPattern.LAYERING
            confidence = 0.5 + 0.2 * (cancels / len(events))
        
        # Momentum ignition: Aggressive orders with volume increase
        elif aggressive > len(events) * 0.5 and volume_trend > 0:
            pattern = InstitutionalPattern.MOMENTUM_IGNITION
            confidence = 0.6 + 0.1 * (aggressive / len(events))
        
        # Absorption: Large orders absorbing flow
        elif large_orders >= 2:
            pattern = InstitutionalPattern.ABSORPTION
            confidence = 0.5 + 0.15 * min(large_orders, 3)
        
        # Determine direction from buy/sell ratio
        buys = sum(1 for e in events if e.side == 'BUY')
        sells = len(events) - buys
        
        if buys > sells * 1.3:
            direction = "ACCUMULATION"
        elif sells > buys * 1.3:
            direction = "DISTRIBUTION"
        else:
            direction = "NEUTRAL"
        
        return pattern, min(confidence, 0.95), direction
    
    def _generate_reasoning(
        self,
        pattern: InstitutionalPattern,
        events: List[MarketEvent],
        intensity: HawkesIntensity,
        buy_volume: float,
        sell_volume: float
    ) -> str:
        """Generate human-readable reasoning for the signal"""
        
        reasoning_parts = []
        
        # Intensity analysis
        intensity_ratio = intensity.total_intensity / self.mu
        reasoning_parts.append(
            f"Event intensity {intensity_ratio:.1f}x above baseline"
        )
        
        # Clustering analysis
        reasoning_parts.append(
            f"Detected {len(events)} clustered events in 5-minute window"
        )
        
        # Volume analysis
        total_volume = buy_volume + sell_volume
        if buy_volume > sell_volume:
            reasoning_parts.append(
                f"Buy-side dominant: {buy_volume/total_volume:.0%} of volume"
            )
        else:
            reasoning_parts.append(
                f"Sell-side dominant: {sell_volume/total_volume:.0%} of volume"
            )
        
        # Pattern-specific reasoning
        if pattern == InstitutionalPattern.STEALTH_ACCUMULATION:
            reasoning_parts.append(
                "Pattern: Regular small orders with hidden iceberg orders - typical institutional accumulation"
            )
        elif pattern == InstitutionalPattern.ICEBERG_SEQUENCE:
            reasoning_parts.append(
                "Pattern: Multiple iceberg orders detected - large hidden institutional interest"
            )
        elif pattern == InstitutionalPattern.LAYERING:
            reasoning_parts.append(
                "Pattern: High order cancellation rate - potential layering/spoofing activity"
            )
        elif pattern == InstitutionalPattern.MOMENTUM_IGNITION:
            reasoning_parts.append(
                "Pattern: Aggressive orders with increasing volume - momentum ignition attempt"
            )
        elif pattern == InstitutionalPattern.ABSORPTION:
            reasoning_parts.append(
                "Pattern: Large orders absorbing opposing flow - institutional absorption"
            )
        
        return ". ".join(reasoning_parts) + "."
    
    def calibrate(self, historical_events: List[MarketEvent]) -> Dict[str, float]:
        """
        Calibrate Hawkes parameters from historical data
        
        Uses maximum likelihood estimation (MLE) to fit parameters
        """
        if len(historical_events) < 100:
            logger.warning("Insufficient data for calibration")
            return {'mu': self.mu, 'alpha': self.alpha, 'beta': self.beta}
        
        # Sort events by timestamp
        events = sorted(historical_events, key=lambda e: e.timestamp)
        
        # Calculate inter-arrival times
        times = []
        t0 = events[0].timestamp
        for e in events:
            times.append((e.timestamp - t0).total_seconds())
        
        times = np.array(times)
        T = times[-1]  # Total observation time
        n = len(times)  # Number of events
        
        # Simple moment-based estimation
        # Mean intensity
        mean_intensity = n / T
        
        # Estimate branching ratio from clustering
        inter_arrivals = np.diff(times)
        cv = np.std(inter_arrivals) / np.mean(inter_arrivals) if np.mean(inter_arrivals) > 0 else 1
        
        # Higher CV suggests more clustering (higher branching ratio)
        estimated_branching = min(0.9, max(0.1, cv - 0.5))
        
        # Estimate parameters
        # μ = λ * (1 - n*)
        # α/β = n*
        estimated_mu = mean_intensity * (1 - estimated_branching)
        estimated_beta = 1.0  # Assume unit decay rate
        estimated_alpha = estimated_branching * estimated_beta
        
        # Update parameters
        self.mu = estimated_mu
        self.alpha = estimated_alpha
        self.beta = estimated_beta
        self.kernel = HawkesKernel(self.alpha, self.beta)
        
        self.last_calibration = datetime.now()
        
        logger.info(
            f"Calibrated Hawkes parameters: μ={self.mu:.4f}, "
            f"α={self.alpha:.4f}, β={self.beta:.4f}, n*={self.kernel.branching_ratio:.4f}"
        )
        
        return {
            'mu': self.mu,
            'alpha': self.alpha,
            'beta': self.beta,
            'branching_ratio': self.kernel.branching_ratio,
            'mean_intensity': mean_intensity
        }
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current detector state"""
        now = datetime.now()
        intensity = self.calculate_intensity(now)
        
        return {
            'timestamp': now.isoformat(),
            'total_events': len(self.events),
            'buy_events': len(self.buy_events),
            'sell_events': len(self.sell_events),
            'current_intensity': intensity.to_dict(),
            'signals_detected': len(self.signals),
            'parameters': {
                'mu': self.mu,
                'alpha': self.alpha,
                'beta': self.beta,
                'branching_ratio': self.kernel.branching_ratio
            }
        }
    
    def get_recent_signals(self, n: int = 10) -> List[InstitutionalSignal]:
        """Get most recent institutional signals"""
        return list(self.signals)[-n:]
    
    def predict_next_event(self, horizon_seconds: float = 60) -> Dict[str, Any]:
        """Predict probability of event in next time horizon"""
        now = datetime.now()
        intensity = self.calculate_intensity(now)
        
        # Expected number of events
        expected = intensity.total_intensity * horizon_seconds
        
        # Probability of at least one event (Poisson approximation)
        prob_at_least_one = 1 - np.exp(-expected)
        
        return {
            'horizon_seconds': horizon_seconds,
            'expected_events': expected,
            'probability_at_least_one': prob_at_least_one,
            'current_intensity': intensity.total_intensity,
            'is_elevated': intensity.total_intensity > self.mu * 1.5
        }


# Factory function
def create_hawkes_detector(config: Optional[Dict[str, Any]] = None) -> HawkesProcessDetector:
    """Create Hawkes process detector"""
    return HawkesProcessDetector(config)
