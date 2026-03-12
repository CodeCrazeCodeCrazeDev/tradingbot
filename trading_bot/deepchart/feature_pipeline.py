"""
DeepChart Feature Pipeline - Low-Cost Feature Engineering

Extracts microstructure features from cheap L1 + aggregated L2 data.
All features designed for minimal compute cost and maximum signal quality.

Feature Categories:
1. Rolling Imbalance Features (from trades)
2. Synthetic Depth Buckets (inferred from L1)
3. Hidden Liquidity Inference
4. Microtrend Vectors
5. Volatility Compression Metrics
6. Regime Classification Features
7. Price-to-Latent-State Embeddings
8. Volume Pulse Indicators
9. Friction/Drag Indicators

Data Dependencies:
- L1: OHLCV, bid/ask quotes, trade prints
- Aggregated L2: Top 5-10 levels (when available)
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import logging
from collections import deque
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class FeatureConfig:
    """Configuration for feature extraction."""
    # Window sizes
    short_window: int = 20          # ~1 minute at 3s bars
    medium_window: int = 100        # ~5 minutes
    long_window: int = 500          # ~25 minutes
    
    # Imbalance settings
    imbalance_decay: float = 0.94   # Exponential decay factor
    imbalance_buckets: int = 10     # Number of price buckets
    
    # Volatility settings
    vol_lookback: int = 50
    vol_compression_threshold: float = 0.5  # Percentile threshold
    
    # Liquidity inference
    liquidity_levels: int = 5       # Synthetic depth levels
    liquidity_decay: float = 0.9    # Decay for hidden liquidity
    
    # Regime detection
    regime_states: int = 4          # Number of regime states
    regime_lookback: int = 200
    
    # Update frequencies (in bars)
    fast_update: int = 1            # Every bar
    medium_update: int = 5          # Every 5 bars
    slow_update: int = 20           # Every 20 bars
    
    # Memory limits
    max_history: int = 2000         # Max bars to keep in memory
    
    # Feature normalization
    normalize: bool = True
    clip_outliers: float = 5.0      # Standard deviations


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class MicrostructureFeatures:
    """Microstructure features extracted from L1 data."""
    # Trade imbalance
    trade_imbalance: float = 0.0           # [-1, 1] buy vs sell pressure
    volume_imbalance: float = 0.0          # Volume-weighted imbalance
    tick_imbalance: float = 0.0            # Tick direction imbalance
    
    # Spread dynamics
    spread_bps: float = 0.0                # Current spread in basis points
    spread_zscore: float = 0.0             # Spread z-score vs history
    spread_expansion: float = 0.0          # Rate of spread change
    
    # Trade clustering
    trade_intensity: float = 0.0           # Trades per unit time
    burst_indicator: float = 0.0           # Trade burst detection
    inter_trade_time: float = 0.0          # Avg time between trades
    
    # Price impact
    price_impact_buy: float = 0.0          # Estimated impact of buy
    price_impact_sell: float = 0.0         # Estimated impact of sell
    
    # Friction indicators
    friction_coefficient: float = 0.0      # Resistance to price movement
    drag_indicator: float = 0.0            # Momentum decay rate
    
    timestamp: float = 0.0


@dataclass
class RegimeFeatures:
    """Market regime classification features."""
    # Regime probabilities
    trending_prob: float = 0.0             # Probability of trending regime
    ranging_prob: float = 0.0              # Probability of ranging regime
    volatile_prob: float = 0.0             # Probability of volatile regime
    quiet_prob: float = 0.0                # Probability of quiet regime
    
    # Regime characteristics
    regime_id: int = 0                     # Current regime ID
    regime_confidence: float = 0.0         # Confidence in regime
    regime_duration: int = 0               # Bars in current regime
    regime_transition_prob: float = 0.0    # Probability of regime change
    
    # Trend features
    trend_strength: float = 0.0            # [-1, 1] trend strength
    trend_direction: int = 0               # -1, 0, 1
    trend_age: int = 0                     # Bars since trend start
    
    # Volatility features
    realized_vol: float = 0.0              # Realized volatility
    vol_regime: int = 0                    # 0=low, 1=normal, 2=high
    vol_compression: float = 0.0           # Compression indicator
    vol_expansion_prob: float = 0.0        # Probability of vol expansion
    
    timestamp: float = 0.0


@dataclass
class LiquidityFeatures:
    """Liquidity and depth features (inferred from L1 when L2 unavailable)."""
    # Synthetic depth
    synthetic_bid_depth: np.ndarray = field(default_factory=lambda: np.zeros(5))
    synthetic_ask_depth: np.ndarray = field(default_factory=lambda: np.zeros(5))
    depth_imbalance: float = 0.0           # Bid vs ask depth imbalance
    
    # Liquidity zones
    support_levels: np.ndarray = field(default_factory=lambda: np.array([]))
    resistance_levels: np.ndarray = field(default_factory=lambda: np.array([]))
    liquidity_zone_strength: np.ndarray = field(default_factory=lambda: np.array([]))
    
    # Hidden liquidity
    hidden_bid_estimate: float = 0.0       # Estimated hidden bid liquidity
    hidden_ask_estimate: float = 0.0       # Estimated hidden ask liquidity
    iceberg_probability: float = 0.0       # Probability of iceberg orders
    
    # Liquidity dynamics
    liquidity_score: float = 0.0           # Overall liquidity score [0, 1]
    liquidity_trend: float = 0.0           # Improving/deteriorating
    thin_market_alert: bool = False        # Low liquidity warning
    
    timestamp: float = 0.0


@dataclass
class LatentFeatures:
    """Latent state features for visualization."""
    # Latent state vector (for visualization)
    latent_vector: np.ndarray = field(default_factory=lambda: np.zeros(8))
    
    # Derived signals
    breakout_probability: float = 0.0      # [0, 1]
    reversion_probability: float = 0.0     # [0, 1]
    trend_confidence: float = 0.0          # [0, 1]
    
    # Momentum
    micro_momentum: float = 0.0            # Short-term momentum
    macro_momentum: float = 0.0            # Long-term momentum
    momentum_divergence: float = 0.0       # Micro vs macro divergence
    
    # Volume pulse
    volume_pulse: float = 0.0              # Volume anomaly indicator
    volume_trend: float = 0.0              # Volume trend direction
    
    timestamp: float = 0.0


# =============================================================================
# FEATURE ENGINE
# =============================================================================

class DeepChartFeatureEngine:
    """
    Main feature extraction engine for DeepChart.
    
    Extracts all features from cheap L1 + aggregated L2 data.
    Optimized for minimal compute cost and real-time updates.
    
    Math Formulas:
    
    1. Trade Imbalance (Rolling):
       TI_t = Σ(sign(price_t - price_{t-1}) * volume_t) / Σ(volume_t)
       Exponential: TI_ema = α * TI_t + (1-α) * TI_ema_{t-1}
    
    2. Spread Z-Score:
       Z_spread = (spread_t - μ_spread) / σ_spread
    
    3. Volatility Compression:
       VC = σ_short / σ_long
       Compression when VC < threshold
    
    4. Friction Coefficient:
       F = |Δprice| / (volume * spread)
       Higher F = more resistance to movement
    
    5. Hidden Liquidity Estimate:
       HL = Σ(volume_i * exp(-λ * |price_i - current_price|))
       Where trades at similar prices suggest hidden liquidity
    
    6. Regime Classification:
       Using rolling statistics and HMM-style transitions
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        self.config = config or FeatureConfig()
        
        # State buffers (circular buffers for efficiency)
        self._price_buffer = deque(maxlen=self.config.max_history)
        self._volume_buffer = deque(maxlen=self.config.max_history)
        self._spread_buffer = deque(maxlen=self.config.max_history)
        self._trade_buffer = deque(maxlen=self.config.max_history)
        self._timestamp_buffer = deque(maxlen=self.config.max_history)
        
        # Running statistics (for efficiency)
        self._running_stats = {
            'price_mean': 0.0,
            'price_std': 1.0,
            'volume_mean': 1.0,
            'volume_std': 1.0,
            'spread_mean': 0.0,
            'spread_std': 1.0,
            'returns_std': 0.01,
        }
        
        # Exponential moving averages
        self._ema_state = {
            'trade_imbalance': 0.0,
            'volume_imbalance': 0.0,
            'tick_imbalance': 0.0,
            'volatility_short': 0.01,
            'volatility_long': 0.01,
        }
        
        # Regime state
        self._regime_state = {
            'current_regime': 0,
            'regime_duration': 0,
            'transition_matrix': np.eye(self.config.regime_states) * 0.9 + 0.1 / self.config.regime_states,
        }
        
        # Liquidity state
        self._liquidity_state = {
            'support_levels': [],
            'resistance_levels': [],
            'hidden_liquidity_map': {},
        }
        
        # Update counters
        self._update_counter = 0
        self._initialized = False
        
        logger.info("DeepChartFeatureEngine initialized")
    
    def update(self, 
               price: float,
               volume: float,
               bid: Optional[float] = None,
               ask: Optional[float] = None,
               timestamp: Optional[float] = None,
               l2_bids: Optional[np.ndarray] = None,
               l2_asks: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Update features with new data point.
        
        Args:
            price: Current price (close or last trade)
            volume: Current volume
            bid: Best bid price (optional)
            ask: Best ask price (optional)
            timestamp: Unix timestamp (optional)
            l2_bids: Aggregated L2 bid levels [[price, size], ...] (optional)
            l2_asks: Aggregated L2 ask levels [[price, size], ...] (optional)
        
        Returns:
            Dict with all extracted features
        """
        import time
        timestamp = timestamp or time.time()
        
        # Calculate spread
        spread = (ask - bid) if (bid and ask) else 0.0
        
        # Update buffers
        self._price_buffer.append(price)
        self._volume_buffer.append(volume)
        self._spread_buffer.append(spread)
        self._timestamp_buffer.append(timestamp)
        
        # Store trade info
        self._trade_buffer.append({
            'price': price,
            'volume': volume,
            'spread': spread,
            'timestamp': timestamp,
            'bid': bid,
            'ask': ask,
        })
        
        self._update_counter += 1
        
        # Check if we have enough data
        if len(self._price_buffer) < self.config.short_window:
            self._initialized = False
            return self._get_empty_features(timestamp)
        
        self._initialized = True
        
        # Update running statistics (slow update)
        if self._update_counter % self.config.slow_update == 0:
            self._update_running_stats()
        
        # Extract features
        microstructure = self._extract_microstructure_features(timestamp)
        regime = self._extract_regime_features(timestamp)
        liquidity = self._extract_liquidity_features(l2_bids, l2_asks, timestamp)
        latent = self._extract_latent_features(microstructure, regime, liquidity, timestamp)
        
        return {
            'microstructure': microstructure,
            'regime': regime,
            'liquidity': liquidity,
            'latent': latent,
            'timestamp': timestamp,
            'initialized': self._initialized,
        }
    
    def _update_running_stats(self):
        """Update running statistics efficiently."""
        prices = np.array(self._price_buffer)
        volumes = np.array(self._volume_buffer)
        spreads = np.array(self._spread_buffer)
        
        self._running_stats['price_mean'] = np.mean(prices)
        self._running_stats['price_std'] = max(np.std(prices), 1e-8)
        self._running_stats['volume_mean'] = max(np.mean(volumes), 1e-8)
        self._running_stats['volume_std'] = max(np.std(volumes), 1e-8)
        self._running_stats['spread_mean'] = np.mean(spreads)
        self._running_stats['spread_std'] = max(np.std(spreads), 1e-8)
        
        # Returns volatility
        returns = np.diff(prices) / prices[:-1]
        self._running_stats['returns_std'] = max(np.std(returns), 1e-8)
    
    def _extract_microstructure_features(self, timestamp: float) -> MicrostructureFeatures:
        """
        Extract microstructure features from L1 data.
        
        Formulas:
        - Trade Imbalance: TI = EMA(sign(Δprice) * volume) / EMA(volume)
        - Tick Imbalance: TI = EMA(sign(Δprice))
        - Friction: F = |Δprice| / (volume * spread + ε)
        - Drag: D = 1 - |momentum_t / momentum_{t-1}|
        """
        prices = np.array(self._price_buffer)
        volumes = np.array(self._volume_buffer)
        spreads = np.array(self._spread_buffer)
        
        # Price changes
        price_changes = np.diff(prices)
        tick_signs = np.sign(price_changes)
        
        # Trade imbalance (volume-weighted)
        # TI = Σ(sign(Δp) * v) / Σ(v)
        signed_volume = tick_signs * volumes[1:]
        trade_imbalance = np.sum(signed_volume[-self.config.short_window:]) / \
                         max(np.sum(volumes[-self.config.short_window:]), 1e-8)
        
        # Update EMA
        alpha = 1 - self.config.imbalance_decay
        self._ema_state['trade_imbalance'] = alpha * trade_imbalance + \
            (1 - alpha) * self._ema_state['trade_imbalance']
        
        # Volume imbalance (buy vs sell volume estimate)
        # Estimate buy/sell based on price position relative to mid
        mid_prices = (np.array([t.get('bid', p) for t, p in zip(self._trade_buffer, prices)] ) + 
                     np.array([t.get('ask', p) for t, p in zip(self._trade_buffer, prices)])) / 2
        buy_volume = np.sum(volumes[-self.config.short_window:][prices[-self.config.short_window:] >= mid_prices[-self.config.short_window:]])
        sell_volume = np.sum(volumes[-self.config.short_window:][prices[-self.config.short_window:] < mid_prices[-self.config.short_window:]])
        volume_imbalance = (buy_volume - sell_volume) / max(buy_volume + sell_volume, 1e-8)
        
        # Tick imbalance
        tick_imbalance = np.mean(tick_signs[-self.config.short_window:])
        
        # Spread features
        current_spread = spreads[-1] if len(spreads) > 0 else 0.0
        spread_bps = current_spread / max(prices[-1], 1e-8) * 10000
        spread_zscore = (current_spread - self._running_stats['spread_mean']) / \
                       max(self._running_stats['spread_std'], 1e-8)
        spread_expansion = (spreads[-1] - spreads[-2]) / max(spreads[-2], 1e-8) if len(spreads) > 1 else 0.0
        
        # Trade clustering
        timestamps = np.array(self._timestamp_buffer)
        if len(timestamps) > 1:
            inter_trade_times = np.diff(timestamps[-self.config.short_window:])
            trade_intensity = 1.0 / max(np.mean(inter_trade_times), 1e-8)
            inter_trade_time = np.mean(inter_trade_times)
            
            # Burst detection: unusually high trade frequency
            burst_threshold = np.percentile(inter_trade_times, 10)
            recent_itt = inter_trade_times[-5:] if len(inter_trade_times) >= 5 else inter_trade_times
            burst_indicator = np.mean(recent_itt < burst_threshold)
        else:
            trade_intensity = 0.0
            inter_trade_time = 0.0
            burst_indicator = 0.0
        
        # Price impact estimation
        # Impact = avg price change per unit volume
        abs_changes = np.abs(price_changes[-self.config.short_window:])
        vols = volumes[1:][-self.config.short_window:]
        price_impact = np.mean(abs_changes / np.maximum(vols, 1e-8))
        
        # Asymmetric impact
        buy_mask = tick_signs[-self.config.short_window:] > 0
        sell_mask = tick_signs[-self.config.short_window:] < 0
        price_impact_buy = np.mean(abs_changes[buy_mask] / np.maximum(vols[buy_mask], 1e-8)) if np.any(buy_mask) else price_impact
        price_impact_sell = np.mean(abs_changes[sell_mask] / np.maximum(vols[sell_mask], 1e-8)) if np.any(sell_mask) else price_impact
        
        # Friction coefficient
        # F = |Δprice| / (volume * spread + ε)
        friction_denom = vols * np.maximum(spreads[1:][-self.config.short_window:], 1e-8)
        friction_coefficient = np.mean(abs_changes / np.maximum(friction_denom, 1e-8))
        
        # Drag indicator (momentum decay)
        # D = 1 - |momentum_t / momentum_{t-1}|
        momentum = np.cumsum(price_changes[-self.config.short_window:])
        if len(momentum) > 1 and abs(momentum[-2]) > 1e-8:
            drag_indicator = 1.0 - min(abs(momentum[-1] / momentum[-2]), 2.0)
        else:
            drag_indicator = 0.0
        
        return MicrostructureFeatures(
            trade_imbalance=float(np.clip(self._ema_state['trade_imbalance'], -1, 1)),
            volume_imbalance=float(np.clip(volume_imbalance, -1, 1)),
            tick_imbalance=float(np.clip(tick_imbalance, -1, 1)),
            spread_bps=float(spread_bps),
            spread_zscore=float(np.clip(spread_zscore, -5, 5)),
            spread_expansion=float(np.clip(spread_expansion, -1, 1)),
            trade_intensity=float(trade_intensity),
            burst_indicator=float(burst_indicator),
            inter_trade_time=float(inter_trade_time),
            price_impact_buy=float(price_impact_buy),
            price_impact_sell=float(price_impact_sell),
            friction_coefficient=float(friction_coefficient),
            drag_indicator=float(np.clip(drag_indicator, -1, 1)),
            timestamp=timestamp,
        )
    
    def _extract_regime_features(self, timestamp: float) -> RegimeFeatures:
        """
        Extract regime classification features.
        
        Regime Detection Logic:
        1. Trending: High directional movement, low mean reversion
        2. Ranging: Low directional movement, high mean reversion
        3. Volatile: High volatility, erratic movement
        4. Quiet: Low volatility, low activity
        
        Formulas:
        - Trend Strength: TS = |price_t - price_{t-n}| / Σ|Δprice|
        - Volatility Compression: VC = σ_short / σ_long
        - Regime Probability: Softmax over regime scores
        """
        prices = np.array(self._price_buffer)
        volumes = np.array(self._volume_buffer)
        
        # Returns
        returns = np.diff(prices) / prices[:-1]
        
        # Volatility (short and long)
        vol_short = np.std(returns[-self.config.short_window:])
        vol_long = np.std(returns[-self.config.long_window:]) if len(returns) >= self.config.long_window else vol_short
        
        # Update EMA volatility
        alpha = 0.1
        self._ema_state['volatility_short'] = alpha * vol_short + (1 - alpha) * self._ema_state['volatility_short']
        self._ema_state['volatility_long'] = alpha * vol_long + (1 - alpha) * self._ema_state['volatility_long']
        
        # Volatility compression
        vol_compression = self._ema_state['volatility_short'] / max(self._ema_state['volatility_long'], 1e-8)
        
        # Trend strength (efficiency ratio)
        # TS = |net_move| / Σ|moves|
        net_move = prices[-1] - prices[-self.config.medium_window] if len(prices) >= self.config.medium_window else 0
        total_move = np.sum(np.abs(np.diff(prices[-self.config.medium_window:])))
        trend_strength = net_move / max(total_move, 1e-8)
        
        # Trend direction
        trend_direction = int(np.sign(trend_strength))
        
        # Mean reversion indicator
        # MR = correlation(price, lagged_price)
        if len(prices) >= self.config.medium_window:
            lag = min(20, len(prices) // 4)
            mean_reversion = -np.corrcoef(prices[-self.config.medium_window:-lag], 
                                          prices[-self.config.medium_window+lag:])[0, 1]
        else:
            mean_reversion = 0.0
        
        # Regime scores
        # Trending: high trend strength, low mean reversion
        trending_score = abs(trend_strength) * (1 - max(mean_reversion, 0))
        
        # Ranging: low trend strength, high mean reversion
        ranging_score = (1 - abs(trend_strength)) * max(mean_reversion, 0)
        
        # Volatile: high short-term vol relative to long-term
        volatile_score = max(vol_compression - 1, 0)
        
        # Quiet: low volatility overall
        vol_percentile = vol_short / max(self._running_stats['returns_std'], 1e-8)
        quiet_score = max(1 - vol_percentile, 0)
        
        # Softmax for probabilities
        scores = np.array([trending_score, ranging_score, volatile_score, quiet_score])
        scores = np.clip(scores, 0, 10)  # Prevent overflow
        exp_scores = np.exp(scores - np.max(scores))
        probs = exp_scores / np.sum(exp_scores)
        
        # Current regime
        current_regime = int(np.argmax(probs))
        
        # Update regime state
        if current_regime == self._regime_state['current_regime']:
            self._regime_state['regime_duration'] += 1
        else:
            self._regime_state['current_regime'] = current_regime
            self._regime_state['regime_duration'] = 1
        
        # Transition probability (simplified)
        transition_prob = 1.0 / max(self._regime_state['regime_duration'], 1)
        
        # Volatility regime
        vol_regime = 0 if vol_short < 0.5 * self._running_stats['returns_std'] else \
                    (2 if vol_short > 1.5 * self._running_stats['returns_std'] else 1)
        
        # Vol expansion probability
        vol_expansion_prob = 1.0 / (1.0 + np.exp(-5 * (vol_compression - 0.5)))
        
        return RegimeFeatures(
            trending_prob=float(probs[0]),
            ranging_prob=float(probs[1]),
            volatile_prob=float(probs[2]),
            quiet_prob=float(probs[3]),
            regime_id=current_regime,
            regime_confidence=float(np.max(probs)),
            regime_duration=self._regime_state['regime_duration'],
            regime_transition_prob=float(transition_prob),
            trend_strength=float(np.clip(trend_strength, -1, 1)),
            trend_direction=trend_direction,
            trend_age=self._regime_state['regime_duration'] if current_regime == 0 else 0,
            realized_vol=float(vol_short),
            vol_regime=vol_regime,
            vol_compression=float(vol_compression),
            vol_expansion_prob=float(vol_expansion_prob),
            timestamp=timestamp,
        )
    
    def _extract_liquidity_features(self, 
                                    l2_bids: Optional[np.ndarray],
                                    l2_asks: Optional[np.ndarray],
                                    timestamp: float) -> LiquidityFeatures:
        """
        Extract liquidity features.
        
        When L2 is unavailable, infer synthetic depth from L1 data:
        1. Use trade clustering to estimate hidden liquidity
        2. Use spread dynamics to estimate depth
        3. Use volume profile to find support/resistance
        
        Formulas:
        - Synthetic Depth: SD_i = Σ(volume_j * exp(-λ * |price_j - level_i|))
        - Hidden Liquidity: HL = volume_absorbed / price_impact
        - Liquidity Score: LS = 1 / (spread * volatility)
        """
        prices = np.array(self._price_buffer)
        volumes = np.array(self._volume_buffer)
        spreads = np.array(self._spread_buffer)
        
        current_price = prices[-1]
        
        # If L2 data available, use it directly
        if l2_bids is not None and l2_asks is not None:
            synthetic_bid_depth = l2_bids[:, 1] if len(l2_bids) > 0 else np.zeros(5)
            synthetic_ask_depth = l2_asks[:, 1] if len(l2_asks) > 0 else np.zeros(5)
        else:
            # Infer synthetic depth from L1
            synthetic_bid_depth, synthetic_ask_depth = self._infer_synthetic_depth(
                prices, volumes, current_price
            )
        
        # Depth imbalance
        total_bid = np.sum(synthetic_bid_depth)
        total_ask = np.sum(synthetic_ask_depth)
        depth_imbalance = (total_bid - total_ask) / max(total_bid + total_ask, 1e-8)
        
        # Support/Resistance levels from volume profile
        support_levels, resistance_levels, zone_strength = self._find_liquidity_zones(
            prices, volumes, current_price
        )
        
        # Hidden liquidity estimation
        # HL = volume_absorbed / price_impact
        price_changes = np.abs(np.diff(prices[-self.config.short_window:]))
        vols = volumes[1:][-self.config.short_window:]
        
        # Volume absorbed at minimal price impact suggests hidden liquidity
        low_impact_mask = price_changes < np.percentile(price_changes, 25)
        if np.any(low_impact_mask):
            hidden_volume = np.sum(vols[low_impact_mask])
            hidden_bid_estimate = hidden_volume * (1 + depth_imbalance) / 2
            hidden_ask_estimate = hidden_volume * (1 - depth_imbalance) / 2
        else:
            hidden_bid_estimate = 0.0
            hidden_ask_estimate = 0.0
        
        # Iceberg probability (large volume with small price impact)
        if len(vols) > 0:
            vol_zscore = (vols - np.mean(vols)) / max(np.std(vols), 1e-8)
            impact_zscore = (price_changes - np.mean(price_changes)) / max(np.std(price_changes), 1e-8)
            iceberg_indicator = vol_zscore - impact_zscore
            iceberg_probability = np.mean(iceberg_indicator > 1)
        else:
            iceberg_probability = 0.0
        
        # Liquidity score
        # LS = 1 / (spread * volatility)
        current_spread = spreads[-1] if len(spreads) > 0 else 0.01
        current_vol = self._ema_state['volatility_short']
        liquidity_score = 1.0 / max(current_spread * current_vol * 1000, 0.01)
        liquidity_score = min(liquidity_score, 1.0)
        
        # Liquidity trend
        if len(spreads) >= self.config.short_window:
            spread_trend = (spreads[-1] - np.mean(spreads[-self.config.short_window:])) / \
                          max(np.std(spreads[-self.config.short_window:]), 1e-8)
            liquidity_trend = -spread_trend  # Negative spread trend = improving liquidity
        else:
            liquidity_trend = 0.0
        
        # Thin market alert
        thin_market_alert = liquidity_score < 0.2 or current_spread > 2 * self._running_stats['spread_mean']
        
        return LiquidityFeatures(
            synthetic_bid_depth=synthetic_bid_depth,
            synthetic_ask_depth=synthetic_ask_depth,
            depth_imbalance=float(np.clip(depth_imbalance, -1, 1)),
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            liquidity_zone_strength=zone_strength,
            hidden_bid_estimate=float(hidden_bid_estimate),
            hidden_ask_estimate=float(hidden_ask_estimate),
            iceberg_probability=float(iceberg_probability),
            liquidity_score=float(liquidity_score),
            liquidity_trend=float(np.clip(liquidity_trend, -1, 1)),
            thin_market_alert=thin_market_alert,
            timestamp=timestamp,
        )
    
    def _infer_synthetic_depth(self, 
                               prices: np.ndarray, 
                               volumes: np.ndarray,
                               current_price: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Infer synthetic order book depth from L1 trade data.
        
        Method: Use historical trade clustering to estimate where liquidity exists.
        
        Formula:
        SD_i = Σ(volume_j * exp(-λ * |price_j - level_i|^2))
        
        Where:
        - SD_i is synthetic depth at level i
        - λ is decay parameter
        - level_i is price level
        """
        n_levels = self.config.liquidity_levels
        
        # Define price levels (percentage from current price)
        level_offsets = np.array([0.001, 0.002, 0.005, 0.01, 0.02])[:n_levels]
        
        bid_levels = current_price * (1 - level_offsets)
        ask_levels = current_price * (1 + level_offsets)
        
        # Calculate synthetic depth using Gaussian kernel
        lambda_decay = 0.001  # Decay parameter
        
        synthetic_bid = np.zeros(n_levels)
        synthetic_ask = np.zeros(n_levels)
        
        recent_prices = prices[-self.config.medium_window:]
        recent_volumes = volumes[-self.config.medium_window:]
        
        for i, (bid_level, ask_level) in enumerate(zip(bid_levels, ask_levels)):
            # Bid depth: trades below current price
            bid_mask = recent_prices < current_price
            if np.any(bid_mask):
                bid_distances = np.abs(recent_prices[bid_mask] - bid_level)
                bid_weights = np.exp(-lambda_decay * bid_distances ** 2)
                synthetic_bid[i] = np.sum(recent_volumes[bid_mask] * bid_weights)
            
            # Ask depth: trades above current price
            ask_mask = recent_prices > current_price
            if np.any(ask_mask):
                ask_distances = np.abs(recent_prices[ask_mask] - ask_level)
                ask_weights = np.exp(-lambda_decay * ask_distances ** 2)
                synthetic_ask[i] = np.sum(recent_volumes[ask_mask] * ask_weights)
        
        # Normalize
        total = np.sum(synthetic_bid) + np.sum(synthetic_ask)
        if total > 0:
            synthetic_bid /= total
            synthetic_ask /= total
        
        return synthetic_bid, synthetic_ask
    
    def _find_liquidity_zones(self,
                              prices: np.ndarray,
                              volumes: np.ndarray,
                              current_price: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Find support/resistance levels from volume profile.
        
        Method: Volume-weighted price clustering.
        """
        # Use recent data
        recent_prices = prices[-self.config.long_window:]
        recent_volumes = volumes[-self.config.long_window:]
        
        # Create volume profile (histogram)
        n_bins = 50
        price_range = np.max(recent_prices) - np.min(recent_prices)
        if price_range < 1e-8:
            return np.array([]), np.array([]), np.array([])
        
        bin_edges = np.linspace(np.min(recent_prices), np.max(recent_prices), n_bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # Volume profile
        volume_profile = np.zeros(n_bins)
        for i in range(n_bins):
            mask = (recent_prices >= bin_edges[i]) & (recent_prices < bin_edges[i + 1])
            volume_profile[i] = np.sum(recent_volumes[mask])
        
        # Find peaks (high volume nodes)
        from scipy.signal import find_peaks
        try:
            peaks, properties = find_peaks(volume_profile, height=np.mean(volume_profile))
            peak_prices = bin_centers[peaks]
            peak_strengths = volume_profile[peaks] / max(np.max(volume_profile), 1e-8)
        except Exception as e:
            logger.error(f"Error: {e}")
            peak_prices = np.array([])
            peak_strengths = np.array([])
        
        # Separate into support (below price) and resistance (above price)
        support_mask = peak_prices < current_price
        resistance_mask = peak_prices > current_price
        
        support_levels = peak_prices[support_mask][-3:] if np.any(support_mask) else np.array([])
        resistance_levels = peak_prices[resistance_mask][:3] if np.any(resistance_mask) else np.array([])
        
        # Zone strengths
        support_strengths = peak_strengths[support_mask][-3:] if np.any(support_mask) else np.array([])
        resistance_strengths = peak_strengths[resistance_mask][:3] if np.any(resistance_mask) else np.array([])
        zone_strength = np.concatenate([support_strengths, resistance_strengths])
        
        return support_levels, resistance_levels, zone_strength
    
    def _extract_latent_features(self,
                                 microstructure: MicrostructureFeatures,
                                 regime: RegimeFeatures,
                                 liquidity: LiquidityFeatures,
                                 timestamp: float) -> LatentFeatures:
        """
        Extract latent state features for visualization.
        
        Combines all features into a compact latent representation.
        """
        prices = np.array(self._price_buffer)
        volumes = np.array(self._volume_buffer)
        
        # Latent vector (8 dimensions)
        latent_vector = np.array([
            microstructure.trade_imbalance,
            microstructure.volume_imbalance,
            regime.trend_strength,
            regime.vol_compression,
            liquidity.depth_imbalance,
            liquidity.liquidity_score,
            microstructure.friction_coefficient / 10,  # Normalize
            microstructure.burst_indicator,
        ])
        
        # Breakout probability
        # High when: vol compression + building imbalance + low friction
        breakout_score = (
            (1 - regime.vol_compression) * 0.3 +  # Compression
            abs(microstructure.trade_imbalance) * 0.3 +  # Imbalance building
            (1 - microstructure.friction_coefficient / 10) * 0.2 +  # Low friction
            regime.vol_expansion_prob * 0.2  # Vol expansion expected
        )
        breakout_probability = 1.0 / (1.0 + np.exp(-5 * (breakout_score - 0.5)))
        
        # Reversion probability
        # High when: extended trend + high friction + ranging regime
        reversion_score = (
            regime.ranging_prob * 0.4 +
            microstructure.friction_coefficient / 10 * 0.3 +
            (1 - abs(regime.trend_strength)) * 0.3
        )
        reversion_probability = 1.0 / (1.0 + np.exp(-5 * (reversion_score - 0.5)))
        
        # Trend confidence
        trend_confidence = regime.trending_prob * abs(regime.trend_strength)
        
        # Momentum
        if len(prices) >= self.config.short_window:
            micro_momentum = (prices[-1] - prices[-self.config.short_window]) / prices[-self.config.short_window]
        else:
            micro_momentum = 0.0
        
        if len(prices) >= self.config.medium_window:
            macro_momentum = (prices[-1] - prices[-self.config.medium_window]) / prices[-self.config.medium_window]
        else:
            macro_momentum = micro_momentum
        
        momentum_divergence = micro_momentum - macro_momentum
        
        # Volume pulse
        if len(volumes) >= self.config.short_window:
            recent_vol = np.mean(volumes[-5:])
            avg_vol = np.mean(volumes[-self.config.short_window:])
            volume_pulse = (recent_vol - avg_vol) / max(avg_vol, 1e-8)
            
            vol_trend = np.polyfit(range(self.config.short_window), 
                                   volumes[-self.config.short_window:], 1)[0]
            volume_trend = vol_trend / max(avg_vol, 1e-8)
        else:
            volume_pulse = 0.0
            volume_trend = 0.0
        
        return LatentFeatures(
            latent_vector=latent_vector,
            breakout_probability=float(np.clip(breakout_probability, 0, 1)),
            reversion_probability=float(np.clip(reversion_probability, 0, 1)),
            trend_confidence=float(np.clip(trend_confidence, 0, 1)),
            micro_momentum=float(micro_momentum),
            macro_momentum=float(macro_momentum),
            momentum_divergence=float(momentum_divergence),
            volume_pulse=float(np.clip(volume_pulse, -5, 5)),
            volume_trend=float(np.clip(volume_trend, -1, 1)),
            timestamp=timestamp,
        )
    
    def _get_empty_features(self, timestamp: float) -> Dict[str, Any]:
        """Return empty features when not enough data."""
        return {
            'microstructure': MicrostructureFeatures(timestamp=timestamp),
            'regime': RegimeFeatures(timestamp=timestamp),
            'liquidity': LiquidityFeatures(timestamp=timestamp),
            'latent': LatentFeatures(timestamp=timestamp),
            'timestamp': timestamp,
            'initialized': False,
        }
    
    def get_feature_vector(self) -> np.ndarray:
        """
        Get flattened feature vector for ML model input.
        
        Returns:
            numpy array of shape (n_features,)
        """
        if not self._initialized:
            return np.zeros(32)  # Default feature size
        
        # Get latest features
        features = self.update(
            price=self._price_buffer[-1],
            volume=self._volume_buffer[-1],
            timestamp=time.time()
        )
        
        # Flatten into vector
        micro = features['microstructure']
        regime = features['regime']
        liquidity = features['liquidity']
        latent = features['latent']
        
        vector = np.array([
            # Microstructure (13 features)
            micro.trade_imbalance,
            micro.volume_imbalance,
            micro.tick_imbalance,
            micro.spread_bps / 100,  # Normalize
            micro.spread_zscore / 5,
            micro.spread_expansion,
            micro.trade_intensity / 100,
            micro.burst_indicator,
            micro.inter_trade_time / 10,
            micro.price_impact_buy * 1000,
            micro.price_impact_sell * 1000,
            micro.friction_coefficient / 10,
            micro.drag_indicator,
            
            # Regime (11 features)
            regime.trending_prob,
            regime.ranging_prob,
            regime.volatile_prob,
            regime.quiet_prob,
            regime.regime_confidence,
            regime.trend_strength,
            regime.trend_direction,
            regime.realized_vol * 100,
            regime.vol_regime / 2,
            regime.vol_compression,
            regime.vol_expansion_prob,
            
            # Liquidity (4 features)
            liquidity.depth_imbalance,
            liquidity.liquidity_score,
            liquidity.liquidity_trend,
            float(liquidity.thin_market_alert),
            
            # Latent (4 features)
            latent.breakout_probability,
            latent.reversion_probability,
            latent.trend_confidence,
            latent.volume_pulse / 5,
        ])
        
        # Clip and normalize
        if self.config.normalize:
            vector = np.clip(vector, -self.config.clip_outliers, self.config.clip_outliers)
        
        return vector.astype(np.float32)
    
    def reset(self):
        """Reset all state."""
        self._price_buffer.clear()
        self._volume_buffer.clear()
        self._spread_buffer.clear()
        self._trade_buffer.clear()
        self._timestamp_buffer.clear()
        self._update_counter = 0
        self._initialized = False
        
        # Reset EMAs
        for key in self._ema_state:
            self._ema_state[key] = 0.0 if 'imbalance' in key else 0.01
        
        # Reset regime
        self._regime_state['current_regime'] = 0
        self._regime_state['regime_duration'] = 0
        
        logger.info("DeepChartFeatureEngine reset")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_feature_engine(config: Optional[Dict] = None) -> DeepChartFeatureEngine:
    """Factory function to create feature engine."""
    if config:
        feature_config = FeatureConfig(**config)
    else:
        feature_config = FeatureConfig()
    return DeepChartFeatureEngine(feature_config)


if __name__ == "__main__":
    # Test the feature engine
    
    engine = DeepChartFeatureEngine()
    
    # Simulate some data
    np.random.seed(42)
    price = 100.0
    
    for i in range(200):
        # Random walk
        price += np.random.randn() * 0.1
        volume = np.random.exponential(1000)
        spread = 0.01 + np.random.exponential(0.005)
        
        features = engine.update(
            price=price,
            volume=volume,
            bid=price - spread / 2,
            ask=price + spread / 2,
            timestamp=time.time() + i,
        )
        
        if i % 50 == 0 and features['initialized']:
            print(f"\nBar {i}:")
            print(f"  Trade Imbalance: {features['microstructure'].trade_imbalance:.3f}")
            print(f"  Regime: {features['regime'].regime_id} (conf: {features['regime'].regime_confidence:.2f})")
            print(f"  Breakout Prob: {features['latent'].breakout_probability:.3f}")
            print(f"  Liquidity Score: {features['liquidity'].liquidity_score:.3f}")
    
    # Get feature vector
    vector = engine.get_feature_vector()
    print(f"\nFeature vector shape: {vector.shape}")
    print(f"Feature vector: {vector[:10]}...")
