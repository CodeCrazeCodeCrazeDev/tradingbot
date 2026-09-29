"""
NEUROS-FI: Neural Oscillation Framework - Temporal Multi-Scale Processing
==========================================================================

Biological Basis:
The brain operates simultaneously at five temporal scales, corresponding to
five neural oscillation bands. Faster bands make faster, more local decisions.
Slower bands provide context and override authority. The thalamus synchronizes
timing across bands to ensure coherent integration.

Oscillation Bands:
- Gamma (γ): 30-100 Hz — Nanoseconds to Milliseconds (execution)
- Beta (β): 13-30 Hz — Seconds to Minutes (active trading)
- Alpha (α): 8-13 Hz — Minutes to Hours (attention gating)
- Theta (θ): 4-8 Hz — Hours to Days (memory encoding)
- Delta (δ): 0.5-4 Hz — Days to Weeks (consolidation)

Citations:
- Buzsáki & Draguhn (2004) - Neuronal oscillations in cortical networks
- Engel et al. (2001) - Dynamic predictions: oscillations and synchrony in top-down processing
- Fries (2005) - A mechanism for cognitive dynamics: neuronal communication through neuronal coherence
- Canolty & Knight (2010) - The functional role of cross-frequency coupling

Constitutional Version: 5.0
"""

import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class OscillationBandType(Enum):
    """The five neural oscillation bands."""
    
    GAMMA = auto()   # 30-100 Hz: Nanoseconds-Milliseconds
    BETA = auto()    # 13-30 Hz: Seconds-Minutes
    ALPHA = auto()   # 8-13 Hz: Minutes-Hours
    THETA = auto()   # 4-8 Hz: Hours-Days
    DELTA = auto()   # 0.5-4 Hz: Days-Weeks


@dataclass
class OscillationState:
    """State of an oscillation band."""
    
    band: OscillationBandType
    frequency_hz: float
    phase: float  # 0 to 2π
    amplitude: float  # 0 to 1
    coherence: float  # 0 to 1 (synchronization quality)
    last_update: datetime
    
    def advance_phase(self, elapsed_seconds: float):
        """Advance phase based on elapsed time."""
        self.phase = (self.phase + 2 * np.pi * self.frequency_hz * elapsed_seconds) % (2 * np.pi)
        self.last_update = datetime.utcnow()


@dataclass
class CrossFrequencyCoupling:
    """Coupling between two oscillation bands."""
    
    slow_band: OscillationBandType
    fast_band: OscillationBandType
    coupling_strength: float  # 0 to 1
    phase_amplitude_coupling: float  # PAC strength
    last_measured: datetime


@dataclass
class ProcessingWindow:
    """A processing window for a specific band."""
    
    band: OscillationBandType
    window_id: str
    start_time: datetime
    duration: timedelta
    is_active: bool
    priority: float


class OscillationBand(ABC):
    """
    Abstract base class for an oscillation band.
    
    Each band operates at a specific temporal scale and has
    specific financial functions.
    """
    
    def __init__(
        self,
        band_type: OscillationBandType,
        frequency_range: Tuple[float, float],
        time_horizon: timedelta
    ):
        self.band_type = band_type
        self.frequency_range = frequency_range
        self.time_horizon = time_horizon
        
        # State
        self._state = OscillationState(
            band=band_type,
            frequency_hz=np.mean(frequency_range),
            phase=0.0,
            amplitude=1.0,
            coherence=0.8,
            last_update=datetime.utcnow(),
        )
        
        self._lock = threading.RLock()
        
        # Processing queue
        self._processing_queue: List[Dict[str, Any]] = []
        
        # Callbacks
        self._phase_callbacks: List[Callable] = []
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data at this band's temporal scale."""
        pass
    
    def update_phase(self, elapsed_seconds: float):
        """Update oscillation phase."""
        with self._lock:
            self._state.advance_phase(elapsed_seconds)
            
            # Check for phase callbacks (e.g., at phase 0)
            if self._state.phase < 0.1:  # Near phase 0
                for callback in self._phase_callbacks:
                    try:
                        callback(self._state)
                    except Exception as e:
                        logger.error(f"Phase callback error: {e}")
    
    def get_phase(self) -> float:
        """Get current phase."""
        with self._lock:
            return self._state.phase
    
    def get_state(self) -> OscillationState:
        """Get current state."""
        with self._lock:
            return self._state
    
    def is_in_processing_window(self) -> bool:
        """Check if currently in optimal processing window."""
        with self._lock:
            # Optimal window is around phase 0 (peak coherence)
            return self._state.phase < np.pi / 4 or self._state.phase > 7 * np.pi / 4
    
    def register_phase_callback(self, callback: Callable):
        """Register callback for phase events."""
        self._phase_callbacks.append(callback)


class GammaBand(OscillationBand):
    """
    Gamma Band (γ): 30-100 Hz — Nanoseconds to Milliseconds
    
    Financial Function:
    - Co-located execution agents
    - Order book state binding across price levels
    - HFT microstructure response
    
    This is the fastest layer — running in the exchange co-location facility,
    making sub-millisecond decisions without cortical involvement.
    """
    
    def __init__(self):
        super().__init__(
            band_type=OscillationBandType.GAMMA,
            frequency_range=(30.0, 100.0),
            time_horizon=timedelta(milliseconds=100)
        )
        
        # Gamma-specific state
        self._order_book_bindings: Dict[str, Dict[str, Any]] = {}
        self._microstructure_state: Dict[str, float] = {}
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process at gamma band (sub-millisecond).
        
        Handles:
        - Order book updates
        - Execution decisions
        - Microstructure signals
        """
        with self._lock:
            result = {
                'band': 'gamma',
                'timestamp': datetime.utcnow(),
                'latency_target_ms': 1.0,
            }
            
            # Bind order book state
            if 'order_book' in data:
                self._bind_order_book(data['order_book'])
                result['order_book_bound'] = True
            
            # Process microstructure signal
            if 'microstructure' in data:
                signal = self._process_microstructure(data['microstructure'])
                result['microstructure_signal'] = signal
            
            # Execution decision (if needed)
            if 'execution_request' in data:
                decision = self._make_execution_decision(data['execution_request'])
                result['execution_decision'] = decision
            
            return result
    
    def _bind_order_book(self, order_book: Dict[str, Any]):
        """Bind order book state across price levels."""
        symbol = order_book.get('symbol', 'unknown')
        self._order_book_bindings[symbol] = {
            'bids': order_book.get('bids', []),
            'asks': order_book.get('asks', []),
            'timestamp': datetime.utcnow(),
        }
    
    def _process_microstructure(self, microstructure: Dict[str, Any]) -> float:
        """Process microstructure signal."""
        spread = microstructure.get('spread', 0.001)
        imbalance = microstructure.get('imbalance', 0)
        
        # Simple microstructure signal
        signal = -imbalance * (1 / spread) if spread > 0 else 0
        return signal
    
    def _make_execution_decision(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Make sub-millisecond execution decision."""
        return {
            'action': 'execute',
            'urgency': request.get('urgency', 0.5),
            'latency_ms': 0.5,
        }


class BetaBand(OscillationBand):
    """
    Beta Band (β): 13-30 Hz — Seconds to Minutes
    
    Financial Function:
    - Intraday signal processing
    - Real-time position management
    - Execution algorithm parameter adjustment
    - Live PnL monitoring
    
    This is where most active trading decisions are executed.
    """
    
    def __init__(self):
        super().__init__(
            band_type=OscillationBandType.BETA,
            frequency_range=(13.0, 30.0),
            time_horizon=timedelta(minutes=5)
        )
        
        # Beta-specific state
        self._active_signals: Dict[str, float] = {}
        self._position_state: Dict[str, Dict[str, Any]] = {}
        self._pnl_tracker: Dict[str, float] = {}
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process at beta band (seconds to minutes).
        
        Handles:
        - Intraday signals
        - Position management
        - PnL monitoring
        """
        with self._lock:
            result = {
                'band': 'beta',
                'timestamp': datetime.utcnow(),
                'time_horizon_minutes': 5,
            }
            
            # Process intraday signals
            if 'signals' in data:
                processed = self._process_signals(data['signals'])
                result['processed_signals'] = processed
            
            # Update position state
            if 'positions' in data:
                self._update_positions(data['positions'])
                result['positions_updated'] = True
            
            # Monitor PnL
            if 'pnl' in data:
                self._update_pnl(data['pnl'])
                result['current_pnl'] = sum(self._pnl_tracker.values())
            
            return result
    
    def _process_signals(self, signals: Dict[str, float]) -> Dict[str, float]:
        """Process intraday signals."""
        processed = {}
        for signal_id, value in signals.items():
            # Apply beta-band filtering
            if signal_id in self._active_signals:
                # Exponential smoothing
                alpha = 0.3
                processed[signal_id] = alpha * value + (1 - alpha) * self._active_signals[signal_id]
            else:
                processed[signal_id] = value
            
            self._active_signals[signal_id] = processed[signal_id]
        
        return processed
    
    def _update_positions(self, positions: Dict[str, Dict[str, Any]]):
        """Update position state."""
        self._position_state.update(positions)
    
    def _update_pnl(self, pnl: Dict[str, float]):
        """Update PnL tracking."""
        self._pnl_tracker.update(pnl)


class AlphaBand(OscillationBand):
    """
    Alpha Band (α): 8-13 Hz — Minutes to Hours
    
    Financial Function:
    - Liquidity monitoring
    - Regime stability assessment
    - Strategy performance tracking
    - Noise filtering
    
    This is where salience decisions are made — what deserves attention.
    """
    
    def __init__(self):
        super().__init__(
            band_type=OscillationBandType.ALPHA,
            frequency_range=(8.0, 13.0),
            time_horizon=timedelta(hours=1)
        )
        
        # Alpha-specific state
        self._liquidity_state: Dict[str, float] = {}
        self._regime_stability: float = 1.0
        self._strategy_performance: Dict[str, float] = {}
        self._attention_weights: Dict[str, float] = {}
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process at alpha band (minutes to hours).
        
        Handles:
        - Liquidity monitoring
        - Regime assessment
        - Attention allocation
        """
        with self._lock:
            result = {
                'band': 'alpha',
                'timestamp': datetime.utcnow(),
                'time_horizon_hours': 1,
            }
            
            # Monitor liquidity
            if 'liquidity' in data:
                self._update_liquidity(data['liquidity'])
                result['liquidity_state'] = self._liquidity_state.copy()
            
            # Assess regime stability
            if 'market_state' in data:
                stability = self._assess_regime_stability(data['market_state'])
                result['regime_stability'] = stability
            
            # Update attention weights
            if 'signals' in data:
                weights = self._compute_attention_weights(data['signals'])
                result['attention_weights'] = weights
            
            return result
    
    def _update_liquidity(self, liquidity: Dict[str, float]):
        """Update liquidity state."""
        for symbol, liq in liquidity.items():
            if symbol in self._liquidity_state:
                # Smooth update
                self._liquidity_state[symbol] = 0.8 * self._liquidity_state[symbol] + 0.2 * liq
            else:
                self._liquidity_state[symbol] = liq
    
    def _assess_regime_stability(self, market_state: Dict[str, Any]) -> float:
        """Assess regime stability."""
        volatility = market_state.get('volatility', 0.01)
        correlation = market_state.get('correlation', 0.3)
        
        # Higher volatility and correlation = less stability
        stability = 1.0 - (volatility * 10 + abs(correlation - 0.3))
        self._regime_stability = max(0.0, min(1.0, stability))
        
        return self._regime_stability
    
    def _compute_attention_weights(self, signals: Dict[str, float]) -> Dict[str, float]:
        """Compute attention weights for signals."""
        if not signals:
            return {}
        
        # Weight by signal magnitude
        total = sum(abs(v) for v in signals.values())
        if total == 0:
            return {k: 1.0 / len(signals) for k in signals}
        
        weights = {k: abs(v) / total for k, v in signals.items()}
        self._attention_weights = weights
        
        return weights


class ThetaBand(OscillationBand):
    """
    Theta Band (θ): 4-8 Hz — Hours to Days
    
    Financial Function:
    - End-of-day discovery consolidation
    - Sequential event pattern learning
    - Cross-day regime transitions
    
    This is where today's experience becomes tomorrow's factor library.
    """
    
    def __init__(self):
        super().__init__(
            band_type=OscillationBandType.THETA,
            frequency_range=(4.0, 8.0),
            time_horizon=timedelta(days=1)
        )
        
        # Theta-specific state
        self._daily_discoveries: List[Dict[str, Any]] = []
        self._event_sequences: List[List[Dict[str, Any]]] = []
        self._regime_transitions: List[Dict[str, Any]] = []
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process at theta band (hours to days).
        
        Handles:
        - Discovery consolidation
        - Sequence learning
        - Regime transitions
        """
        with self._lock:
            result = {
                'band': 'theta',
                'timestamp': datetime.utcnow(),
                'time_horizon_days': 1,
            }
            
            # Consolidate discoveries
            if 'discoveries' in data:
                self._consolidate_discoveries(data['discoveries'])
                result['discoveries_consolidated'] = len(self._daily_discoveries)
            
            # Learn event sequences
            if 'events' in data:
                self._learn_sequences(data['events'])
                result['sequences_learned'] = len(self._event_sequences)
            
            # Track regime transitions
            if 'regime_change' in data:
                self._record_regime_transition(data['regime_change'])
                result['regime_transitions'] = len(self._regime_transitions)
            
            return result
    
    def _consolidate_discoveries(self, discoveries: List[Dict[str, Any]]):
        """Consolidate daily discoveries."""
        self._daily_discoveries.extend(discoveries)
        
        # Keep recent discoveries
        if len(self._daily_discoveries) > 1000:
            self._daily_discoveries = self._daily_discoveries[-500:]
    
    def _learn_sequences(self, events: List[Dict[str, Any]]):
        """Learn event sequences."""
        if len(events) >= 3:
            self._event_sequences.append(events)
            
            if len(self._event_sequences) > 100:
                self._event_sequences = self._event_sequences[-50:]
    
    def _record_regime_transition(self, transition: Dict[str, Any]):
        """Record a regime transition."""
        transition['timestamp'] = datetime.utcnow()
        self._regime_transitions.append(transition)
        
        if len(self._regime_transitions) > 100:
            self._regime_transitions = self._regime_transitions[-50:]


class DeltaBand(OscillationBand):
    """
    Delta Band (δ): 0.5-4 Hz — Days to Weeks
    
    Financial Function:
    - Overnight model retraining
    - Long-horizon factor integration
    - Architectural evolution review cycles
    - Strategic world model rebuilding
    
    This is where the system becomes smarter than it was yesterday.
    """
    
    def __init__(self):
        super().__init__(
            band_type=OscillationBandType.DELTA,
            frequency_range=(0.5, 4.0),
            time_horizon=timedelta(weeks=1)
        )
        
        # Delta-specific state
        self._model_versions: List[Dict[str, Any]] = []
        self._factor_integrations: List[Dict[str, Any]] = []
        self._architecture_reviews: List[Dict[str, Any]] = []
        self._world_model_state: Dict[str, Any] = {}
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process at delta band (days to weeks).
        
        Handles:
        - Model retraining
        - Factor integration
        - Architecture evolution
        """
        with self._lock:
            result = {
                'band': 'delta',
                'timestamp': datetime.utcnow(),
                'time_horizon_weeks': 1,
            }
            
            # Model retraining
            if 'retrain_request' in data:
                version = self._retrain_model(data['retrain_request'])
                result['model_version'] = version
            
            # Factor integration
            if 'new_factors' in data:
                integrated = self._integrate_factors(data['new_factors'])
                result['factors_integrated'] = integrated
            
            # Architecture review
            if 'architecture_proposal' in data:
                review = self._review_architecture(data['architecture_proposal'])
                result['architecture_review'] = review
            
            # World model update
            if 'world_model_update' in data:
                self._update_world_model(data['world_model_update'])
                result['world_model_updated'] = True
            
            return result
    
    def _retrain_model(self, request: Dict[str, Any]) -> str:
        """Retrain model and return version."""
        version = f"v{len(self._model_versions) + 1}_{int(time.time())}"
        
        self._model_versions.append({
            'version': version,
            'timestamp': datetime.utcnow(),
            'request': request,
        })
        
        return version
    
    def _integrate_factors(self, factors: List[Dict[str, Any]]) -> int:
        """Integrate new factors into the library."""
        for factor in factors:
            self._factor_integrations.append({
                'factor': factor,
                'timestamp': datetime.utcnow(),
            })
        
        return len(factors)
    
    def _review_architecture(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Review architecture proposal."""
        review = {
            'proposal': proposal,
            'timestamp': datetime.utcnow(),
            'status': 'pending_human_review',
        }
        
        self._architecture_reviews.append(review)
        
        return review
    
    def _update_world_model(self, update: Dict[str, Any]):
        """Update the world model."""
        self._world_model_state.update(update)
        self._world_model_state['last_update'] = datetime.utcnow()


class OscillationSynchronizer:
    """
    Oscillation Synchronizer - coordinates timing across all bands.
    
    The thalamus synchronizes timing across bands to ensure coherent integration.
    All five bands operate simultaneously, with faster bands making faster decisions
    and slower bands providing context and override authority.
    """
    
    def __init__(self):
        # Initialize all bands
        self.gamma = GammaBand()
        self.beta = BetaBand()
        self.alpha = AlphaBand()
        self.theta = ThetaBand()
        self.delta = DeltaBand()
        
        self._bands = {
            OscillationBandType.GAMMA: self.gamma,
            OscillationBandType.BETA: self.beta,
            OscillationBandType.ALPHA: self.alpha,
            OscillationBandType.THETA: self.theta,
            OscillationBandType.DELTA: self.delta,
        }
        
        self._lock = threading.RLock()
        
        # Cross-frequency coupling
        self._couplings: List[CrossFrequencyCoupling] = self._initialize_couplings()
        
        # Synchronization state
        self._last_sync = datetime.utcnow()
        self._sync_quality: float = 0.8
        
        logger.info("Oscillation Synchronizer initialized - 5 bands active")
    
    def _initialize_couplings(self) -> List[CrossFrequencyCoupling]:
        """Initialize cross-frequency couplings."""
        return [
            CrossFrequencyCoupling(
                slow_band=OscillationBandType.THETA,
                fast_band=OscillationBandType.GAMMA,
                coupling_strength=0.7,
                phase_amplitude_coupling=0.5,
                last_measured=datetime.utcnow(),
            ),
            CrossFrequencyCoupling(
                slow_band=OscillationBandType.ALPHA,
                fast_band=OscillationBandType.GAMMA,
                coupling_strength=0.6,
                phase_amplitude_coupling=0.4,
                last_measured=datetime.utcnow(),
            ),
            CrossFrequencyCoupling(
                slow_band=OscillationBandType.DELTA,
                fast_band=OscillationBandType.THETA,
                coupling_strength=0.5,
                phase_amplitude_coupling=0.3,
                last_measured=datetime.utcnow(),
            ),
        ]
    
    def update_all_phases(self):
        """Update phases for all bands based on elapsed time."""
        with self._lock:
            now = datetime.utcnow()
            elapsed = (now - self._last_sync).total_seconds()
            
            for band in self._bands.values():
                band.update_phase(elapsed)
            
            self._last_sync = now
    
    def process_at_band(
        self,
        band_type: OscillationBandType,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process data at a specific band."""
        with self._lock:
            band = self._bands.get(band_type)
            if band:
                return band.process(data)
            return {}
    
    def process_hierarchical(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process data through the full hierarchy.
        
        Faster bands process first, slower bands provide context.
        """
        with self._lock:
            results = {}
            
            # Update phases
            self.update_all_phases()
            
            # Process from fastest to slowest
            # Gamma (fastest)
            if 'gamma' in data or 'execution' in data:
                gamma_data = data.get('gamma', data.get('execution', {}))
                results['gamma'] = self.gamma.process(gamma_data)
            
            # Beta
            if 'beta' in data or 'signals' in data:
                beta_data = data.get('beta', {'signals': data.get('signals', {})})
                results['beta'] = self.beta.process(beta_data)
            
            # Alpha
            if 'alpha' in data or 'market_state' in data:
                alpha_data = data.get('alpha', {'market_state': data.get('market_state', {})})
                results['alpha'] = self.alpha.process(alpha_data)
            
            # Theta
            if 'theta' in data or 'discoveries' in data:
                theta_data = data.get('theta', {'discoveries': data.get('discoveries', [])})
                results['theta'] = self.theta.process(theta_data)
            
            # Delta (slowest)
            if 'delta' in data:
                results['delta'] = self.delta.process(data['delta'])
            
            # Apply cross-frequency coupling
            results['coupling'] = self._apply_coupling(results)
            
            return results
    
    def _apply_coupling(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Apply cross-frequency coupling between bands."""
        coupling_effects = {}
        
        for coupling in self._couplings:
            slow_result = results.get(coupling.slow_band.name.lower(), {})
            fast_result = results.get(coupling.fast_band.name.lower(), {})
            
            if slow_result and fast_result:
                # Slow band modulates fast band amplitude
                slow_phase = self._bands[coupling.slow_band].get_phase()
                modulation = np.cos(slow_phase) * coupling.coupling_strength
                
                coupling_effects[f"{coupling.slow_band.name}_{coupling.fast_band.name}"] = modulation
        
        return coupling_effects
    
    def get_band(self, band_type: OscillationBandType) -> OscillationBand:
        """Get a specific band."""
        return self._bands.get(band_type)
    
    def get_sync_quality(self) -> float:
        """Get current synchronization quality."""
        with self._lock:
            # Compute based on phase coherence across bands
            phases = [band.get_phase() for band in self._bands.values()]
            
            # Simple coherence measure
            phase_variance = np.var(phases)
            self._sync_quality = 1.0 / (1.0 + phase_variance)
            
            return self._sync_quality
    
    def get_status(self) -> Dict[str, Any]:
        """Get synchronizer status."""
        with self._lock:
            return {
                'sync_quality': self.get_sync_quality(),
                'last_sync': self._last_sync.isoformat(),
                'bands': {
                    band_type.name: {
                        'phase': band.get_phase(),
                        'frequency': band.get_state().frequency_hz,
                        'in_window': band.is_in_processing_window(),
                    }
                    for band_type, band in self._bands.items()
                },
                'couplings': [
                    {
                        'slow': c.slow_band.name,
                        'fast': c.fast_band.name,
                        'strength': c.coupling_strength,
                    }
                    for c in self._couplings
                ],
            }
