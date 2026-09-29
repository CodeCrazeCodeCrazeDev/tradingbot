"""
NEUROS-FI Region 3: Thalamus - Intelligent Signal Routing and Gating
=====================================================================

Biological Basis:
Every sensory signal, without exception, routes through the thalamus before
reaching the cortex. The thalamus is not passive — it gates signals based on
attention, arousal state, and cortical feedback. High-priority signals are
amplified. Background noise is suppressed.

Thalamo-cortical loops create the synchronized oscillations that bind
distributed processing across cortical regions.

Citations:
- Sherman & Guillery (2002) - The role of the thalamus in the flow of information
- Jones (2007) - The Thalamus (2nd Edition)
- Saalmann & Kastner (2011) - Cognitive and perceptual functions of the visual thalamus
- Halassa & Kastner (2017) - Thalamic functions in distributed cognitive control

Constitutional Version: 5.0
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class ThalamicNucleus(Enum):
    """Thalamic nuclei with specialized functions."""
    
    LGN = auto()       # Lateral Geniculate Nucleus - visual/image data
    MGN = auto()       # Medial Geniculate Nucleus - auditory/news data
    VPL = auto()       # Ventral Posterolateral - market data (price, volume)
    PULVINAR = auto()  # Pulvinar - attention and salience
    MD = auto()        # Mediodorsal - executive/PFC relay
    RETICULAR = auto() # Reticular nucleus - gating control


class SignalPriority(Enum):
    """Signal priority levels for gating."""
    
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    BACKGROUND = 1


class GatingState(Enum):
    """Thalamic gating states."""
    
    OPEN = "open"           # Signal passes through
    ATTENUATED = "attenuated"  # Signal reduced
    BLOCKED = "blocked"     # Signal suppressed
    AMPLIFIED = "amplified" # Signal boosted


@dataclass
class DataFeed:
    """A data feed routed through the thalamus."""
    
    feed_id: str
    feed_type: str
    source: str
    nucleus: ThalamicNucleus
    priority: SignalPriority
    latency_ms: float
    quality_score: float  # 0-1
    last_update: datetime
    update_frequency_hz: float
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SalienceScore:
    """Salience score for a signal."""
    
    feed_id: str
    timestamp: datetime
    regime_relevance: float      # How relevant to current regime
    information_coefficient: float  # Recent predictive power
    uniqueness: float            # Decorrelation from other feeds
    attentional_priority: float  # PFC attention signal
    composite_salience: float    # Combined score
    
    def __post_init__(self):
        # Compute composite if not set
        if self.composite_salience == 0:
            self.composite_salience = (
                0.3 * self.regime_relevance +
                0.3 * self.information_coefficient +
                0.2 * self.uniqueness +
                0.2 * self.attentional_priority
            )


@dataclass
class GatedSignal:
    """A signal after thalamic gating."""
    
    signal_id: str
    feed_id: str
    timestamp: datetime
    raw_value: Any
    gating_state: GatingState
    gain: float  # Amplification/attenuation factor
    gated_value: Any
    salience: SalienceScore
    routing_target: str  # Which cortical column receives this


@dataclass
class ThalamoCorticalSync:
    """Synchronization state between thalamus and cortex."""
    
    oscillation_band: str  # gamma, beta, alpha, theta, delta
    frequency_hz: float
    phase: float
    coherence: float  # 0-1, how synchronized
    last_sync: datetime


class SalienceScorer:
    """
    Computes salience scores for incoming signals.
    
    Salience determines which signals get amplified vs suppressed.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Historical IC tracking
        self._ic_history: Dict[str, List[float]] = {}
        self._ic_window = 100  # Number of observations
        
        # Correlation matrix for uniqueness
        self._correlation_matrix: Dict[Tuple[str, str], float] = {}
        
        # Current regime
        self._current_regime: str = "normal"
        self._regime_relevance_map: Dict[str, Dict[str, float]] = {
            'bull': {'momentum': 0.9, 'value': 0.4, 'volatility': 0.3},
            'bear': {'momentum': 0.3, 'value': 0.7, 'volatility': 0.8},
            'normal': {'momentum': 0.6, 'value': 0.6, 'volatility': 0.5},
            'crisis': {'momentum': 0.2, 'value': 0.3, 'volatility': 1.0},
        }
        
        # Attentional priorities from PFC
        self._attentional_priorities: Dict[str, float] = {}
    
    def compute_salience(
        self,
        feed_id: str,
        feed_type: str,
        signal_value: float
    ) -> SalienceScore:
        """Compute salience score for a signal."""
        with self._lock:
            # Regime relevance
            regime_map = self._regime_relevance_map.get(self._current_regime, {})
            regime_relevance = regime_map.get(feed_type, 0.5)
            
            # Information coefficient (historical predictive power)
            ic_history = self._ic_history.get(feed_id, [])
            if ic_history:
                information_coefficient = np.mean(ic_history[-self._ic_window:])
            else:
                information_coefficient = 0.5  # Prior
            
            # Uniqueness (decorrelation)
            uniqueness = self._compute_uniqueness(feed_id)
            
            # Attentional priority from PFC
            attentional_priority = self._attentional_priorities.get(feed_id, 0.5)
            
            return SalienceScore(
                feed_id=feed_id,
                timestamp=datetime.utcnow(),
                regime_relevance=regime_relevance,
                information_coefficient=information_coefficient,
                uniqueness=uniqueness,
                attentional_priority=attentional_priority,
                composite_salience=0,  # Computed in __post_init__
            )
    
    def _compute_uniqueness(self, feed_id: str) -> float:
        """Compute uniqueness (decorrelation from other feeds)."""
        correlations = []
        for (f1, f2), corr in self._correlation_matrix.items():
            if f1 == feed_id or f2 == feed_id:
                correlations.append(abs(corr))
        
        if correlations:
            avg_correlation = np.mean(correlations)
            return 1.0 - avg_correlation  # Higher uniqueness = lower correlation
        return 0.5  # Prior
    
    def update_ic(self, feed_id: str, ic_value: float):
        """Update information coefficient for a feed."""
        with self._lock:
            if feed_id not in self._ic_history:
                self._ic_history[feed_id] = []
            self._ic_history[feed_id].append(ic_value)
            
            # Trim history
            if len(self._ic_history[feed_id]) > self._ic_window * 2:
                self._ic_history[feed_id] = self._ic_history[feed_id][-self._ic_window:]
    
    def update_correlation(self, feed1: str, feed2: str, correlation: float):
        """Update correlation between two feeds."""
        with self._lock:
            self._correlation_matrix[(feed1, feed2)] = correlation
            self._correlation_matrix[(feed2, feed1)] = correlation
    
    def set_regime(self, regime: str):
        """Set current market regime."""
        with self._lock:
            self._current_regime = regime
    
    def set_attentional_priority(self, feed_id: str, priority: float):
        """Set attentional priority from PFC."""
        with self._lock:
            self._attentional_priorities[feed_id] = max(0.0, min(1.0, priority))


class SignalGating:
    """
    Thalamic gating mechanism - controls which signals reach the cortex.
    
    High-salience signals are amplified.
    Low-salience signals are suppressed.
    """
    
    def __init__(self, salience_scorer: SalienceScorer):
        self._salience_scorer = salience_scorer
        self._lock = threading.RLock()
        
        # Gating thresholds
        self._amplification_threshold = 0.7
        self._suppression_threshold = 0.3
        self._block_threshold = 0.1
        
        # Gain parameters
        self._max_gain = 2.0
        self._min_gain = 0.1
        
        # Arousal state (affects overall gating)
        self._arousal_level = 0.5  # 0-1
        
        # Gating history
        self._gating_history: List[GatedSignal] = []
    
    def gate_signal(
        self,
        feed_id: str,
        feed_type: str,
        raw_value: Any,
        routing_target: str
    ) -> GatedSignal:
        """
        Apply thalamic gating to a signal.
        
        Returns the gated signal with appropriate gain.
        """
        with self._lock:
            # Compute salience
            salience = self._salience_scorer.compute_salience(
                feed_id, feed_type, raw_value if isinstance(raw_value, (int, float)) else 0
            )
            
            # Determine gating state and gain
            composite = salience.composite_salience * (0.5 + 0.5 * self._arousal_level)
            
            if composite >= self._amplification_threshold:
                gating_state = GatingState.AMPLIFIED
                gain = 1.0 + (composite - self._amplification_threshold) * self._max_gain
            elif composite <= self._block_threshold:
                gating_state = GatingState.BLOCKED
                gain = 0.0
            elif composite <= self._suppression_threshold:
                gating_state = GatingState.ATTENUATED
                gain = self._min_gain + (composite - self._block_threshold) * 0.5
            else:
                gating_state = GatingState.OPEN
                gain = 1.0
            
            # Apply gain to value
            if isinstance(raw_value, (int, float)):
                gated_value = raw_value * gain
            else:
                gated_value = raw_value  # Non-numeric values pass through
            
            # Create gated signal
            gated_signal = GatedSignal(
                signal_id=f"gated_{feed_id}_{int(time.time()*1000)}",
                feed_id=feed_id,
                timestamp=datetime.utcnow(),
                raw_value=raw_value,
                gating_state=gating_state,
                gain=gain,
                gated_value=gated_value,
                salience=salience,
                routing_target=routing_target,
            )
            
            # Record history
            self._gating_history.append(gated_signal)
            if len(self._gating_history) > 10000:
                self._gating_history = self._gating_history[-5000:]
            
            return gated_signal
    
    def set_arousal_level(self, level: float):
        """Set arousal level (affects overall gating sensitivity)."""
        with self._lock:
            self._arousal_level = max(0.0, min(1.0, level))
    
    def get_gating_statistics(self) -> Dict[str, Any]:
        """Get gating statistics."""
        with self._lock:
            if not self._gating_history:
                return {'total': 0}
            
            recent = self._gating_history[-1000:]
            states = [g.gating_state for g in recent]
            
            return {
                'total': len(recent),
                'amplified': states.count(GatingState.AMPLIFIED),
                'open': states.count(GatingState.OPEN),
                'attenuated': states.count(GatingState.ATTENUATED),
                'blocked': states.count(GatingState.BLOCKED),
                'avg_gain': np.mean([g.gain for g in recent]),
                'avg_salience': np.mean([g.salience.composite_salience for g in recent]),
            }


class ThalamoCorticalSynchronizer:
    """
    Manages thalamo-cortical synchronization across oscillation bands.
    
    Ensures signals from different cortical columns are temporally aligned.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Oscillation bands
        self._bands = {
            'gamma': ThalamoCorticalSync('gamma', 40.0, 0.0, 0.8, datetime.utcnow()),
            'beta': ThalamoCorticalSync('beta', 20.0, 0.0, 0.7, datetime.utcnow()),
            'alpha': ThalamoCorticalSync('alpha', 10.0, 0.0, 0.6, datetime.utcnow()),
            'theta': ThalamoCorticalSync('theta', 6.0, 0.0, 0.5, datetime.utcnow()),
            'delta': ThalamoCorticalSync('delta', 2.0, 0.0, 0.4, datetime.utcnow()),
        }
        
        # Column synchronization state
        self._column_phases: Dict[str, Dict[str, float]] = {}
    
    def update_phase(self, band: str, elapsed_seconds: float):
        """Update oscillation phase."""
        with self._lock:
            if band in self._bands:
                sync = self._bands[band]
                # Phase advances with frequency
                sync.phase = (sync.phase + 2 * np.pi * sync.frequency_hz * elapsed_seconds) % (2 * np.pi)
                sync.last_sync = datetime.utcnow()
    
    def get_sync_window(self, band: str) -> Tuple[float, float]:
        """
        Get the current synchronization window for a band.
        
        Returns (start_phase, end_phase) for optimal signal integration.
        """
        with self._lock:
            if band not in self._bands:
                return (0.0, 2 * np.pi)
            
            sync = self._bands[band]
            # Optimal window is around phase 0 (peak coherence)
            window_width = np.pi / 4  # 45 degrees
            start = (sync.phase - window_width) % (2 * np.pi)
            end = (sync.phase + window_width) % (2 * np.pi)
            
            return (start, end)
    
    def is_in_sync_window(self, band: str) -> bool:
        """Check if current phase is in optimal sync window."""
        with self._lock:
            if band not in self._bands:
                return True
            
            sync = self._bands[band]
            # Check if phase is near 0 or 2π (peak)
            return sync.phase < np.pi / 4 or sync.phase > 7 * np.pi / 4
    
    def synchronize_columns(
        self,
        column_signals: Dict[str, Any],
        band: str
    ) -> Dict[str, Any]:
        """
        Synchronize signals from multiple cortical columns.
        
        Ensures temporal alignment before integration.
        """
        with self._lock:
            if not self.is_in_sync_window(band):
                # Wait for sync window (in practice, buffer the signals)
                logger.debug(f"Waiting for {band} sync window")
            
            # Apply phase-based weighting
            sync = self._bands.get(band)
            if sync:
                phase_weight = np.cos(sync.phase) * 0.5 + 0.5  # 0-1
            else:
                phase_weight = 1.0
            
            synchronized = {}
            for column, signal in column_signals.items():
                if isinstance(signal, (int, float)):
                    synchronized[column] = signal * phase_weight
                else:
                    synchronized[column] = signal
            
            return synchronized
    
    def get_coherence(self, band: str) -> float:
        """Get current coherence for a band."""
        with self._lock:
            if band in self._bands:
                return self._bands[band].coherence
            return 0.5
    
    def update_coherence(self, band: str, coherence: float):
        """Update coherence estimate for a band."""
        with self._lock:
            if band in self._bands:
                self._bands[band].coherence = max(0.0, min(1.0, coherence))


class PulvinarNucleus:
    """
    Pulvinar Nucleus - specialized for visual/image data preprocessing.
    
    Handles satellite imagery, chart patterns, and visual data feeds
    before thalamic relay to cortex.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Visual feature extractors
        self._feature_cache: Dict[str, Dict[str, float]] = {}
        
        # Attention maps
        self._attention_maps: Dict[str, np.ndarray] = {}
    
    def preprocess_visual_data(
        self,
        feed_id: str,
        image_data: Any,
        data_type: str
    ) -> Dict[str, Any]:
        """
        Preprocess visual data before thalamic relay.
        
        Extracts relevant features for financial analysis.
        """
        with self._lock:
            features = {}
            
            if data_type == 'satellite':
                # Satellite imagery features
                features = {
                    'activity_level': 0.5,  # Placeholder
                    'change_detection': 0.0,
                    'anomaly_score': 0.0,
                }
            elif data_type == 'chart':
                # Chart pattern features
                features = {
                    'trend_direction': 0.0,
                    'pattern_type': 'none',
                    'support_resistance': [],
                }
            elif data_type == 'heatmap':
                # Heatmap features
                features = {
                    'hotspot_count': 0,
                    'intensity_mean': 0.0,
                    'spatial_distribution': 'uniform',
                }
            
            self._feature_cache[feed_id] = features
            
            return {
                'feed_id': feed_id,
                'data_type': data_type,
                'features': features,
                'timestamp': datetime.utcnow(),
            }
    
    def get_attention_priority(self, feed_id: str) -> float:
        """Get attention priority for a visual feed."""
        with self._lock:
            features = self._feature_cache.get(feed_id, {})
            
            # Higher anomaly/change = higher priority
            anomaly = features.get('anomaly_score', 0)
            change = features.get('change_detection', 0)
            
            return min(1.0, anomaly + change)


class Thalamus:
    """
    The complete Thalamus - intelligent signal routing and gating.
    
    All 50,000+ data feeds route through here before cortical processing.
    Implements:
    - Salience-based gating
    - Thalamo-cortical synchronization
    - Visual preprocessing (Pulvinar)
    - Multi-nucleus routing
    """
    
    def __init__(self):
        # Initialize components
        self.salience_scorer = SalienceScorer()
        self.signal_gating = SignalGating(self.salience_scorer)
        self.synchronizer = ThalamoCorticalSynchronizer()
        self.pulvinar = PulvinarNucleus()
        
        self._lock = threading.RLock()
        
        # Registered data feeds
        self._feeds: Dict[str, DataFeed] = {}
        
        # Routing table (feed_type -> cortical column)
        self._routing_table: Dict[str, str] = {
            'equity_price': 'equities',
            'equity_volume': 'equities',
            'bond_yield': 'fixed_income',
            'credit_spread': 'credit',
            'fx_rate': 'fx',
            'commodity_price': 'commodities',
            'macro_indicator': 'macro',
            'satellite': 'commodities',
            'news': 'macro',
            'sentiment': 'macro',
        }
        
        # Nucleus assignments
        self._nucleus_map: Dict[str, ThalamicNucleus] = {
            'equity_price': ThalamicNucleus.VPL,
            'bond_yield': ThalamicNucleus.VPL,
            'satellite': ThalamicNucleus.LGN,
            'chart': ThalamicNucleus.LGN,
            'news': ThalamicNucleus.MGN,
            'sentiment': ThalamicNucleus.MGN,
        }
        
        # Processing statistics
        self._signals_processed = 0
        self._signals_blocked = 0
        
        logger.info("Thalamus initialized - signal routing active")
    
    def register_feed(
        self,
        feed_id: str,
        feed_type: str,
        source: str,
        priority: SignalPriority = SignalPriority.MEDIUM,
        update_frequency_hz: float = 1.0
    ) -> bool:
        """Register a new data feed."""
        with self._lock:
            nucleus = self._nucleus_map.get(feed_type, ThalamicNucleus.VPL)
            
            feed = DataFeed(
                feed_id=feed_id,
                feed_type=feed_type,
                source=source,
                nucleus=nucleus,
                priority=priority,
                latency_ms=0.0,
                quality_score=1.0,
                last_update=datetime.utcnow(),
                update_frequency_hz=update_frequency_hz,
            )
            
            self._feeds[feed_id] = feed
            logger.debug(f"Feed registered: {feed_id} -> {nucleus.name}")
            
            return True
    
    def process_signal(
        self,
        feed_id: str,
        signal_value: Any,
        timestamp: Optional[datetime] = None
    ) -> Optional[GatedSignal]:
        """
        Process an incoming signal through thalamic gating.
        
        Returns the gated signal if it passes, None if blocked.
        """
        with self._lock:
            self._signals_processed += 1
            
            # Get feed info
            feed = self._feeds.get(feed_id)
            if not feed:
                # Unknown feed - register with defaults
                self.register_feed(feed_id, 'unknown', 'unknown')
                feed = self._feeds[feed_id]
            
            # Update feed timestamp
            feed.last_update = timestamp or datetime.utcnow()
            
            # Visual preprocessing for image data
            if feed.nucleus == ThalamicNucleus.LGN:
                preprocessed = self.pulvinar.preprocess_visual_data(
                    feed_id, signal_value, feed.feed_type
                )
                signal_value = preprocessed
            
            # Determine routing target
            routing_target = self._routing_table.get(feed.feed_type, 'macro')
            
            # Apply gating
            gated = self.signal_gating.gate_signal(
                feed_id=feed_id,
                feed_type=feed.feed_type,
                raw_value=signal_value,
                routing_target=routing_target,
            )
            
            # Track blocked signals
            if gated.gating_state == GatingState.BLOCKED:
                self._signals_blocked += 1
                return None
            
            return gated
    
    def process_batch(
        self,
        signals: Dict[str, Any]
    ) -> Dict[str, List[GatedSignal]]:
        """
        Process a batch of signals, grouped by routing target.
        
        Returns signals organized by cortical column.
        """
        with self._lock:
            routed_signals: Dict[str, List[GatedSignal]] = {
                'equities': [],
                'fixed_income': [],
                'fx': [],
                'credit': [],
                'commodities': [],
                'macro': [],
            }
            
            for feed_id, value in signals.items():
                gated = self.process_signal(feed_id, value)
                if gated:
                    target = gated.routing_target
                    if target in routed_signals:
                        routed_signals[target].append(gated)
            
            return routed_signals
    
    def synchronize_and_relay(
        self,
        routed_signals: Dict[str, List[GatedSignal]],
        oscillation_band: str = 'beta'
    ) -> Dict[str, List[GatedSignal]]:
        """
        Synchronize signals across columns before cortical relay.
        
        Ensures temporal alignment using thalamo-cortical loops.
        """
        with self._lock:
            # Wait for sync window if needed
            if not self.synchronizer.is_in_sync_window(oscillation_band):
                # In production, this would buffer signals
                pass
            
            # Apply synchronization
            synchronized = {}
            for column, signals in routed_signals.items():
                if signals:
                    # Get coherence-weighted signals
                    coherence = self.synchronizer.get_coherence(oscillation_band)
                    synchronized[column] = signals  # Simplified - full impl would phase-align
            
            return synchronized
    
    def set_attention(self, feed_id: str, priority: float):
        """Set attentional priority for a feed (from PFC)."""
        self.salience_scorer.set_attentional_priority(feed_id, priority)
    
    def set_regime(self, regime: str):
        """Set current market regime (affects salience)."""
        self.salience_scorer.set_regime(regime)
    
    def set_arousal(self, level: float):
        """Set arousal level (affects overall gating sensitivity)."""
        self.signal_gating.set_arousal_level(level)
    
    def update_feed_quality(self, feed_id: str, quality: float):
        """Update quality score for a feed."""
        with self._lock:
            if feed_id in self._feeds:
                self._feeds[feed_id].quality_score = max(0.0, min(1.0, quality))
    
    def update_feed_ic(self, feed_id: str, ic: float):
        """Update information coefficient for a feed."""
        self.salience_scorer.update_ic(feed_id, ic)
    
    def get_feed_status(self, feed_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific feed."""
        with self._lock:
            feed = self._feeds.get(feed_id)
            if not feed:
                return None
            
            return {
                'feed_id': feed.feed_id,
                'feed_type': feed.feed_type,
                'source': feed.source,
                'nucleus': feed.nucleus.name,
                'priority': feed.priority.name,
                'quality': feed.quality_score,
                'last_update': feed.last_update.isoformat(),
                'is_active': feed.is_active,
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get thalamus status."""
        with self._lock:
            return {
                'registered_feeds': len(self._feeds),
                'signals_processed': self._signals_processed,
                'signals_blocked': self._signals_blocked,
                'block_rate': self._signals_blocked / max(1, self._signals_processed),
                'gating_stats': self.signal_gating.get_gating_statistics(),
                'active_feeds': sum(1 for f in self._feeds.values() if f.is_active),
                'feeds_by_nucleus': {
                    nucleus.name: sum(1 for f in self._feeds.values() if f.nucleus == nucleus)
                    for nucleus in ThalamicNucleus
                },
            }
