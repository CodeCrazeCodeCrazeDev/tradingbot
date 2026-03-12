"""
Market Intent Decomposition Engine (MIDE) - Feature Extractor

Extracts the 12 observable features from cheap market data (L1 trades, quotes).
Each feature is mathematically defined and carries specific intent information.

NON-NEGOTIABLE: All features computable from L1 data only.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Deque, Optional, Tuple
from collections import deque
import time

from .intent_decomposition_core import ObservableFeatures, MIDEConfig


# =============================================================================
# FEATURE STATISTICS TRACKER
# =============================================================================

@dataclass
class FeatureStatistics:
    """
    Rolling statistics for feature normalization.
    """
    mean: np.ndarray = field(default_factory=lambda: np.zeros(12, dtype=np.float32))
    std: np.ndarray = field(default_factory=lambda: np.ones(12, dtype=np.float32))
    count: int = 0
    window: int = 100
    
    # Rolling buffers
    _buffer: Deque = field(default_factory=lambda: deque(maxlen=100))
    
    def update(self, features: np.ndarray):
        """Update statistics with new features."""
        self._buffer.append(features)
        self.count += 1
        
        if len(self._buffer) >= 10:
            arr = np.array(self._buffer)
            self.mean = np.mean(arr, axis=0).astype(np.float32)
            self.std = np.std(arr, axis=0).astype(np.float32)
            self.std = np.maximum(self.std, 1e-6)  # Prevent division by zero
    
    def normalize(self, features: np.ndarray) -> np.ndarray:
        """Z-score normalize features."""
        normalized = (features - self.mean) / self.std
        return np.clip(normalized, -3, 3).astype(np.float32)


# =============================================================================
# TRADE DATA BUFFER
# =============================================================================

@dataclass
class TradeData:
    """Single trade record."""
    price: float
    volume: float
    timestamp: float
    is_buy: bool  # True if trade at ask (buy aggressor)


@dataclass
class QuoteData:
    """Single quote record."""
    bid: float
    ask: float
    bid_size: float
    ask_size: float
    timestamp: float
    
    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2
    
    @property
    def spread(self) -> float:
        return self.ask - self.bid
    
    @property
    def spread_bps(self) -> float:
        return (self.spread / self.mid) * 10000 if self.mid > 0 else 0


# =============================================================================
# INTENT FEATURE EXTRACTOR
# =============================================================================

class IntentFeatureExtractor:
    """
    Extracts the 12 observable features for intent inference.
    
    Features:
    1. Price Response Per Unit Volume (ρ)
    2. Spread-Crossing Frequency (f_cross)
    3. Reaction Half-Life (τ_1/2)
    4. Volume Entropy (H_v)
    5. Price Curvature vs Volume (κ)
    6. Micro-Friction Persistence (φ)
    7. Execution Efficiency vs Volatility (η)
    8. Trade Arrival Irregularity (ψ)
    9. Size Clustering Coefficient (γ)
    10. Quote Imbalance Persistence (ω)
    11. Aggressor Ratio Asymmetry (α)
    12. Momentum Decay Rate (λ_m)
    """
    
    def __init__(self, config: Optional[MIDEConfig] = None):
        self.config = config or MIDEConfig()
        
        # Trade buffer
        self.trades: Deque[TradeData] = deque(maxlen=500)
        self.quotes: Deque[QuoteData] = deque(maxlen=500)
        
        # Feature-specific buffers
        self._price_impacts: Deque[float] = deque(maxlen=100)
        self._spread_crosses: Deque[bool] = deque(maxlen=100)
        self._burst_half_lives: Deque[float] = deque(maxlen=20)
        self._friction_values: Deque[float] = deque(maxlen=50)
        self._efficiency_values: Deque[float] = deque(maxlen=50)
        self._volatility_values: Deque[float] = deque(maxlen=50)
        self._imbalance_signs: Deque[int] = deque(maxlen=30)
        self._momentum_values: Deque[float] = deque(maxlen=50)
        
        # Statistics for normalization
        self.stats = FeatureStatistics()
        
        # State
        self._last_price: Optional[float] = None
        self._last_volume: Optional[float] = None
        self._last_burst_time: Optional[float] = None
        self._burst_peak_price: Optional[float] = None
        self._bar_count = 0
    
    def add_trade(self, price: float, volume: float, timestamp: float, 
                  bid: float, ask: float) -> None:
        """
        Add a new trade and update internal state.
        
        Args:
            price: Trade price
            volume: Trade volume
            timestamp: Trade timestamp
            bid: Best bid at time of trade
            ask: Best ask at time of trade
        """
        # Determine aggressor side
        is_buy = price >= ask - (ask - bid) * 0.1  # Trade at or near ask = buy
        
        trade = TradeData(
            price=price,
            volume=volume,
            timestamp=timestamp,
            is_buy=is_buy
        )
        self.trades.append(trade)
        
        # Update spread crossing
        if bid > 0 and ask > 0:
            crossed = price >= ask or price <= bid
            self._spread_crosses.append(crossed)
        
        # Update price impact
        if self._last_price is not None and volume > 0:
            impact = abs(price - self._last_price) / (volume + 1e-8)
            self._price_impacts.append(impact)
        
        # Update friction
        if self._last_price is not None and len(self.quotes) > 0:
            spread = self.quotes[-1].spread
            if spread > 0 and volume > 0:
                friction = abs(price - self._last_price) / (spread * volume + 1e-8)
                self._friction_values.append(friction)
        
        # Detect burst and track half-life
        self._detect_burst_and_halflife(price, volume, timestamp)
        
        # Update momentum
        if self._last_price is not None:
            momentum = price - self._last_price
            self._momentum_values.append(momentum)
        
        self._last_price = price
        self._last_volume = volume
    
    def add_quote(self, bid: float, ask: float, bid_size: float, 
                  ask_size: float, timestamp: float) -> None:
        """Add a new quote update."""
        quote = QuoteData(
            bid=bid,
            ask=ask,
            bid_size=bid_size,
            ask_size=ask_size,
            timestamp=timestamp
        )
        self.quotes.append(quote)
        
        # Update imbalance
        total_size = bid_size + ask_size
        if total_size > 0:
            imbalance = (bid_size - ask_size) / total_size
            self._imbalance_signs.append(1 if imbalance > 0 else -1)
    
    def _detect_burst_and_halflife(self, price: float, volume: float, 
                                    timestamp: float) -> None:
        """Detect volume bursts and measure half-life."""
        if len(self.trades) < 20:
            return
        
        # Calculate EMA of volume
        volumes = [t.volume for t in list(self.trades)[-20:]]
        ema_vol = np.mean(volumes)
        
        # Detect burst
        if volume > 2 * ema_vol:
            self._last_burst_time = timestamp
            self._burst_peak_price = price
        
        # Check for half-life completion
        if self._last_burst_time is not None and self._burst_peak_price is not None:
            time_since_burst = timestamp - self._last_burst_time
            if time_since_burst > 0:
                # Check if price has reverted 50%
                max_deviation = abs(price - self._burst_peak_price)
                if len(self._price_impacts) > 0:
                    recent_prices = [t.price for t in list(self.trades)[-10:]]
                    if len(recent_prices) > 1:
                        current_deviation = abs(recent_prices[-1] - self._burst_peak_price)
                        if current_deviation < 0.5 * max_deviation and max_deviation > 0:
                            self._burst_half_lives.append(time_since_burst)
                            self._last_burst_time = None
    
    def extract_features(self) -> ObservableFeatures:
        """
        Extract all 12 features from current state.
        
        Returns:
            ObservableFeatures with all 12 features populated
        """
        start_time = time.perf_counter()
        
        features = ObservableFeatures(timestamp=time.time())
        
        if len(self.trades) < 10:
            features.is_valid = False
            return features
        
        # 1. Price Response Per Unit Volume (ρ)
        features.price_response_per_volume = self._compute_price_response()
        
        # 2. Spread-Crossing Frequency (f_cross)
        features.spread_crossing_freq = self._compute_spread_crossing_freq()
        
        # 3. Reaction Half-Life (τ_1/2)
        features.reaction_half_life = self._compute_reaction_halflife()
        
        # 4. Volume Entropy (H_v)
        features.volume_entropy = self._compute_volume_entropy()
        
        # 5. Price Curvature vs Volume (κ)
        features.price_curvature = self._compute_price_curvature()
        
        # 6. Micro-Friction Persistence (φ)
        features.friction_persistence = self._compute_friction_persistence()
        
        # 7. Execution Efficiency vs Volatility (η)
        features.execution_efficiency = self._compute_execution_efficiency()
        
        # 8. Trade Arrival Irregularity (ψ)
        features.arrival_irregularity = self._compute_arrival_irregularity()
        
        # 9. Size Clustering Coefficient (γ)
        features.size_clustering = self._compute_size_clustering()
        
        # 10. Quote Imbalance Persistence (ω)
        features.imbalance_persistence = self._compute_imbalance_persistence()
        
        # 11. Aggressor Ratio Asymmetry (α)
        features.aggressor_asymmetry = self._compute_aggressor_asymmetry()
        
        # 12. Momentum Decay Rate (λ_m)
        features.momentum_decay_rate = self._compute_momentum_decay()
        
        # Update statistics and normalize
        raw_features = features.to_array()
        self.stats.update(raw_features)
        normalized = self.stats.normalize(raw_features)
        
        # Create normalized features
        features = ObservableFeatures.from_array(normalized, features.timestamp)
        features.staleness_ms = (time.perf_counter() - start_time) * 1000
        features.is_valid = True
        
        self._bar_count += 1
        
        return features
    
    def _compute_price_response(self) -> float:
        """
        Feature 1: Price Response Per Unit Volume (ρ)
        
        ρ = |Δp| / (v + ε)
        
        High ρ → Urgent directional (large impact per unit)
        Low ρ → Passive accumulation (absorbing without moving price)
        """
        if len(self._price_impacts) < 5:
            return 0.0
        
        return float(np.mean(list(self._price_impacts)[-20:]))
    
    def _compute_spread_crossing_freq(self) -> float:
        """
        Feature 2: Spread-Crossing Frequency (f_cross)
        
        f_cross = count(trades crossing spread) / count(all trades)
        
        High → Urgent directional (paying spread to execute)
        Low → Passive/Mechanical (patient execution)
        """
        if len(self._spread_crosses) < 5:
            return 0.5
        
        crosses = list(self._spread_crosses)[-20:]
        return float(np.mean(crosses))
    
    def _compute_reaction_halflife(self) -> float:
        """
        Feature 3: Reaction Half-Life (τ_1/2)
        
        Time for price to revert 50% after burst.
        
        Short → Urgent (permanent impact)
        Long → Noise (temporary impact)
        """
        if len(self._burst_half_lives) < 2:
            return 10.0  # Default
        
        return float(np.mean(list(self._burst_half_lives)[-10:]))
    
    def _compute_volume_entropy(self) -> float:
        """
        Feature 4: Volume Entropy (H_v)
        
        H_v = -Σ p_k × log(p_k) / log(K)
        
        High → Noise (random sizing)
        Low → Mechanical (clustered sizes)
        """
        if len(self.trades) < 20:
            return 0.5
        
        volumes = [t.volume for t in list(self.trades)[-50:]]
        
        try:
            # Discretize into 10 bins
            hist, _ = np.histogram(volumes, bins=10)
            hist = hist / hist.sum()
            hist = hist[hist > 0]  # Remove zeros
            entropy = -np.sum(hist * np.log(hist)) / np.log(10)
            return float(np.clip(entropy, 0, 1))
        except Exception as e:
            logger.error(f"Error: {e}")
            return 0.5
    
    def _compute_price_curvature(self) -> float:
        """
        Feature 5: Price Curvature vs Volume (κ)
        
        Fit p(v) = a×v² + b×v + c; κ = 2a
        
        κ > 0 (convex) → Urgent (accelerating impact)
        κ < 0 (concave) → Passive (decelerating impact)
        κ ≈ 0 (linear) → Mechanical (constant impact)
        """
        if len(self.trades) < 30:
            return 0.0
        
        trades = list(self.trades)[-30:]
        prices = np.array([t.price for t in trades])
        cum_volumes = np.cumsum([t.volume for t in trades])
        
        try:
            # Fit quadratic
            coeffs = np.polyfit(cum_volumes, prices, 2)
            curvature = 2 * coeffs[0]
            # Normalize with sign-preserving log
            return float(np.sign(curvature) * np.log1p(abs(curvature) * 1000))
        except Exception as e:
            logger.error(f"Error: {e}")
            return 0.0
    
    def _compute_friction_persistence(self) -> float:
        """
        Feature 6: Micro-Friction Persistence (φ)
        
        φ = autocorr(friction, lag=1)
        
        High φ → Persistent intent (institutional)
        Low φ → Transient intent (noise)
        """
        if len(self._friction_values) < 10:
            return 0.0
        
        friction = np.array(list(self._friction_values)[-30:])
        if len(friction) < 5:
            return 0.0
        try:
        
            # Compute autocorrelation at lag 1
            mean = np.mean(friction)
            var = np.var(friction)
            if var < 1e-10:
                return 0.0
            autocorr = np.corrcoef(friction[:-1], friction[1:])[0, 1]
            return float(np.clip(autocorr, -1, 1))
        except:
            return 0.0
    
    def _compute_execution_efficiency(self) -> float:
        """
        Feature 7: Execution Efficiency vs Volatility (η)
        
        η = corr(efficiency, volatility)
        
        η > 0 → Urgent (more efficient in volatile markets)
        η < 0 → Passive (less efficient in volatile markets)
        """
        if len(self.trades) < 50:
            return 0.0
        
        trades = list(self.trades)[-50:]
        prices = np.array([t.price for t in trades])
        
        # Compute efficiency (price efficiency ratio)
        window = 10
        efficiencies = []
        volatilities = []
        
        for i in range(window, len(prices)):
            net_move = abs(prices[i] - prices[i-window])
            total_move = np.sum(np.abs(np.diff(prices[i-window:i+1])))
            if total_move > 0:
                efficiencies.append(net_move / total_move)
                volatilities.append(np.std(prices[i-window:i+1]))
        
        if len(efficiencies) < 10:
            return 0.0
        try:
        
            corr = np.corrcoef(efficiencies, volatilities)[0, 1]
            return float(np.clip(corr, -1, 1))
        except:
            return 0.0
    
    def _compute_arrival_irregularity(self) -> float:
        """
        Feature 8: Trade Arrival Irregularity (ψ)
        
        ψ = CV(inter_arrival_times) = std/mean
        
        Low ψ → Mechanical (regular intervals)
        High ψ → Noise (random arrivals)
        """
        if len(self.trades) < 20:
            return 1.0
        
        trades = list(self.trades)[-50:]
        timestamps = [t.timestamp for t in trades]
        
        inter_arrivals = np.diff(timestamps)
        inter_arrivals = inter_arrivals[inter_arrivals > 0]
        
        if len(inter_arrivals) < 5:
            return 1.0
        
        mean_iat = np.mean(inter_arrivals)
        std_iat = np.std(inter_arrivals)
        
        if mean_iat < 1e-10:
            return 1.0
        
        cv = std_iat / mean_iat
        return float(np.clip(cv, 0, 3))
    
    def _compute_size_clustering(self) -> float:
        """
        Feature 9: Size Clustering Coefficient (γ)
        
        γ = max(cluster_counts) / total_trades
        
        High γ → Mechanical (same size repeated)
        Low γ → Noise (random sizes)
        """
        if len(self.trades) < 20:
            return 0.5
        
        volumes = [t.volume for t in list(self.trades)[-100:]]
        
        try:
            # Round to nearest "lot" (use percentile-based rounding)
            lot_size = np.percentile(volumes, 10)
            if lot_size < 1e-10:
                lot_size = 1.0
            rounded = np.round(np.array(volumes) / lot_size) * lot_size
            
            # Count clusters
            unique, counts = np.unique(rounded, return_counts=True)
            max_count = np.max(counts)
            
            return float(max_count / len(volumes))
        except:
            return 0.5
    
    def _compute_imbalance_persistence(self) -> float:
        """
        Feature 10: Quote Imbalance Persistence (ω)
        
        ω = sign consistency over lookback
        
        High ω → Passive accumulation (persistent pressure)
        Low ω → Noise (random imbalance)
        """
        if len(self._imbalance_signs) < 5:
            return 0.0
        
        signs = np.array(list(self._imbalance_signs)[-20:])
        
        # Compute sign consistency
        if len(signs) < 2:
            return 0.0
        
        consistency = np.mean(signs[:-1] * signs[1:])
        return float(np.clip(consistency, -1, 1))
    
    def _compute_aggressor_asymmetry(self) -> float:
        """
        Feature 11: Aggressor Ratio Asymmetry (α)
        
        α = (buy_aggressor - sell_aggressor) / total
        
        |α| > 0.3 → Urgent directional
        |α| < 0.1 → Mechanical/Noise (balanced)
        """
        if len(self.trades) < 10:
            return 0.0
        
        trades = list(self.trades)[-50:]
        buy_count = sum(1 for t in trades if t.is_buy)
        sell_count = len(trades) - buy_count
        
        total = buy_count + sell_count
        if total == 0:
            return 0.0
        
        alpha = (buy_count - sell_count) / total
        return float(np.clip(alpha, -1, 1))
    
    def _compute_momentum_decay(self) -> float:
        """
        Feature 12: Momentum Decay Rate (λ_m)
        
        Fit: momentum(t+k) = momentum(t) × exp(-λ_m × k)
        
        Low λ_m → Urgent (momentum persists)
        High λ_m → Noise (momentum decays quickly)
        """
        if len(self._momentum_values) < 20:
            return 0.5
        
        momentum = np.array(list(self._momentum_values)[-30:])
        
        # Compute cumulative momentum
        cum_momentum = np.cumsum(momentum)
        
        try:
            # Fit exponential decay to absolute momentum
            abs_cum = np.abs(cum_momentum)
            if abs_cum[0] < 1e-10:
                return 0.5
            
            # Simple decay estimate
            decay_ratios = abs_cum[1:] / (abs_cum[:-1] + 1e-10)
            decay_ratios = decay_ratios[decay_ratios > 0]
            
            if len(decay_ratios) < 5:
                return 0.5
            
            # Average decay rate
            avg_decay = -np.mean(np.log(np.clip(decay_ratios, 0.01, 10)))
            return float(np.clip(avg_decay, 0, 2))
        except:
            return 0.5
    
    def get_feature_sequence(self, length: int = 64) -> np.ndarray:
        """
        Get sequence of features for model input.
        
        Returns:
            Array of shape (length, 12) with normalized features
        """
        # Extract current features
        current = self.extract_features()
        
        # For now, return repeated current features
        # In production, this would use historical feature buffer
        sequence = np.tile(current.to_array(), (length, 1))
        
        return sequence.astype(np.float32)
    
    def reset(self):
        """Reset all buffers."""
        self.trades.clear()
        self.quotes.clear()
        self._price_impacts.clear()
        self._spread_crosses.clear()
        self._burst_half_lives.clear()
        self._friction_values.clear()
        self._efficiency_values.clear()
        self._volatility_values.clear()
        self._imbalance_signs.clear()
        self._momentum_values.clear()
        self._last_price = None
        self._last_volume = None
        self._last_burst_time = None
        self._burst_peak_price = None
        self._bar_count = 0
