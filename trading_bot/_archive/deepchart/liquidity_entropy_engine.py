"""
DeepChart Liquidity & Entropy Engine

Combines:
- Synthetic Liquidity Shadows (Concept 4)
- Volume Entropy Tracker (Concept 5)
- Liquidity Vacuum Detector (Concept 9)

Infers hidden liquidity from L1 price response asymmetry and
tracks volume entropy to distinguish information from noise.

Math:
    response_bid = mean(|Δp| / v) for upticks
    response_ask = mean(|Δp| / v) for downticks
    asymmetry = (response_ask - response_bid) / (response_ask + response_bid)
    hidden_bid = 1 / response_bid (inverse of price impact)
    
    H = -Σ p_i × log(p_i)  (Shannon entropy)
    information_ratio = 1 - H / H_max

Performance Budget:
    - Update: O(1) per tick
    - Memory: O(window_size)
    - Latency: <0.5ms per update
"""

import numpy as np
from collections import deque
from typing import Dict, List, Tuple, Optional
import time
import logging

from .market_intelligence_core import (
    SyntheticLiquidityMap,
    VolumeEntropyState,
    LiquidityVacuum,
    MarketIntelligenceConfig,
)

logger = logging.getLogger(__name__)


class SyntheticLiquidityEngine:
    """
    Infers hidden liquidity from L1 price response asymmetry.
    
    Key insight: If price moves less on buy volume than sell volume,
    there's likely hidden bid liquidity absorbing the buys.
    """
    
    def __init__(self, config: MarketIntelligenceConfig):
        self.config = config
        self._uptick_impacts = deque(maxlen=200)
        self._downtick_impacts = deque(maxlen=200)
        self._price_levels = deque(maxlen=100)
        self._volume_at_levels: Dict[float, float] = {}
        self._last_price = 0.0
    
    def update(self, price: float, volume: float, bid: float, ask: float) -> SyntheticLiquidityMap:
        """
        Update synthetic liquidity map.
        
        Args:
            price: Current price
            volume: Trade volume
            bid: Best bid
            ask: Best ask
            
        Returns:
            SyntheticLiquidityMap with inferred liquidity
        """
        if self._last_price > 0:
            price_change = price - self._last_price
            impact = abs(price_change) / (volume + 1e-8)
            
            if price_change > 0:
                self._uptick_impacts.append(impact)
            elif price_change < 0:
                self._downtick_impacts.append(impact)
        
        self._last_price = price
        self._price_levels.append(price)
        
        # Update volume at levels
        level = round(price, 2)
        self._volume_at_levels[level] = self._volume_at_levels.get(level, 0) + volume
        
        # Prune old levels
        self._prune_volume_levels(price)
        
        # Calculate asymmetry
        asymmetry = self._calculate_asymmetry()
        
        # Estimate hidden liquidity
        hidden_bid, hidden_ask = self._estimate_hidden_liquidity()
        
        # Build liquidity profile
        bid_profile, ask_profile, levels = self._build_liquidity_profile(price)
        
        # Estimate iceberg probability
        iceberg_prob = self._estimate_iceberg_probability()
        
        return SyntheticLiquidityMap(
            bid_liquidity_profile=bid_profile,
            ask_liquidity_profile=ask_profile,
            hidden_bid_estimate=hidden_bid,
            hidden_ask_estimate=hidden_ask,
            asymmetry_score=asymmetry,
            iceberg_probability=iceberg_prob,
            price_levels=levels
        )
    
    def _calculate_asymmetry(self) -> float:
        """
        Calculate bid/ask response asymmetry.
        
        Positive = more hidden bid liquidity
        Negative = more hidden ask liquidity
        """
        if len(self._uptick_impacts) < 10 or len(self._downtick_impacts) < 10:
            return 0.0
        
        response_bid = np.mean(self._uptick_impacts)
        response_ask = np.mean(self._downtick_impacts)
        
        total = response_bid + response_ask
        if total < 1e-8:
            return 0.0
        
        # Positive asymmetry = lower impact on upticks = hidden bid liquidity
        return (response_ask - response_bid) / total
    
    def _estimate_hidden_liquidity(self) -> Tuple[float, float]:
        """
        Estimate hidden bid and ask liquidity.
        
        Inverse of price impact = liquidity estimate.
        """
        if len(self._uptick_impacts) < 10:
            return 0.5, 0.5
        
        response_bid = np.mean(self._uptick_impacts) + 1e-8
        response_ask = np.mean(self._downtick_impacts) + 1e-8
        
        # Inverse of impact = liquidity estimate
        hidden_bid = 1.0 / response_bid
        hidden_ask = 1.0 / response_ask
        
        # Normalize to [0, 1]
        total = hidden_bid + hidden_ask
        return hidden_bid / total, hidden_ask / total
    
    def _build_liquidity_profile(self, current_price: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Build synthetic liquidity profile around current price."""
        n_levels = self.config.liquidity_profile_levels
        
        if len(self._price_levels) < 10:
            levels = np.linspace(current_price * 0.99, current_price * 1.01, n_levels)
            return np.zeros(n_levels), np.zeros(n_levels), levels
        
        # Calculate price range
        prices = np.array(self._price_levels)
        price_range = np.std(prices) * 3
        if price_range < current_price * 0.001:
            price_range = current_price * 0.01
        
        levels = np.linspace(current_price - price_range, current_price + price_range, n_levels)
        
        bid_profile = np.zeros(n_levels)
        ask_profile = np.zeros(n_levels)
        
        for i, level in enumerate(levels):
            # Estimate liquidity at each level based on volume history
            level_key = round(level, 2)
            vol = self._volume_at_levels.get(level_key, 0)
            
            if level < current_price:
                bid_profile[i] = vol
            else:
                ask_profile[i] = vol
        
        # Normalize
        if np.sum(bid_profile) > 0:
            bid_profile = bid_profile / np.sum(bid_profile)
        if np.sum(ask_profile) > 0:
            ask_profile = ask_profile / np.sum(ask_profile)
        
        return bid_profile, ask_profile, levels
    
    def _estimate_iceberg_probability(self) -> float:
        """
        Estimate probability of iceberg orders.
        
        High volume with low impact suggests icebergs.
        """
        if len(self._uptick_impacts) < 20:
            return 0.3
        
        # High volume with low impact suggests icebergs
        impacts = list(self._uptick_impacts) + list(self._downtick_impacts)
        impact_std = np.std(impacts)
        impact_mean = np.mean(impacts)
        
        # Low variance in impact suggests consistent hidden liquidity
        cv = impact_std / (impact_mean + 1e-8)
        return max(0, min(1, 1 - cv))
    
    def _prune_volume_levels(self, current_price: float):
        """Remove volume levels far from current price."""
        to_remove = []
        for level in self._volume_at_levels:
            if abs(level - current_price) > current_price * 0.05:
                to_remove.append(level)
        
        for level in to_remove:
            del self._volume_at_levels[level]
    
    def reset(self):
        """Reset engine state."""
        self._uptick_impacts.clear()
        self._downtick_impacts.clear()
        self._price_levels.clear()
        self._volume_at_levels.clear()
        self._last_price = 0.0


class VolumeEntropyTracker:
    """
    Tracks volume entropy to distinguish information from noise.
    
    High entropy = random/noisy volume distribution
    Low entropy = concentrated/informed trading
    """
    
    def __init__(self, config: MarketIntelligenceConfig):
        self.config = config
        self._volume_buckets = deque(maxlen=config.entropy_window)
        self._entropy_history = deque(maxlen=100)
        self._baseline_entropy = 0.0
        self._bar_count = 0
    
    def update(self, volume: float, price_change: float) -> VolumeEntropyState:
        """
        Update volume entropy state.
        
        Args:
            volume: Trade volume
            price_change: Price change since last update
            
        Returns:
            VolumeEntropyState with entropy metrics
        """
        self._bar_count += 1
        
        # Bucket volume by price change direction and magnitude
        bucket = self._get_volume_bucket(volume, price_change)
        self._volume_buckets.append(bucket)
        
        if len(self._volume_buckets) < 20:
            return self._create_default_state()
        
        # Calculate entropy
        entropy = self._calculate_entropy()
        self._entropy_history.append(entropy)
        
        # Update baseline periodically
        if self._bar_count % 100 == 0 and len(self._entropy_history) > 10:
            self._baseline_entropy = np.mean(self._entropy_history)
        
        # Calculate information ratio
        max_entropy = np.log(10)  # 10 buckets
        information_ratio = max(0, 1 - entropy / max_entropy)
        
        # Noise floor
        noise_floor = self._baseline_entropy / max_entropy if self._baseline_entropy > 0 else 0.5
        
        # Informed trading probability
        informed_prob = self._estimate_informed_trading(entropy)
        
        # Volume clustering
        clustering = self._calculate_clustering()
        
        # Entropy trend
        entropy_trend = self._calculate_entropy_trend()
        
        return VolumeEntropyState(
            entropy=entropy,
            information_ratio=information_ratio,
            noise_floor=noise_floor,
            informed_trading_prob=informed_prob,
            volume_clustering=clustering,
            entropy_trend=entropy_trend
        )
    
    def _get_volume_bucket(self, volume: float, price_change: float) -> int:
        """
        Assign volume to bucket based on price change.
        
        10 buckets: 5 for up moves (by magnitude), 5 for down moves.
        """
        if price_change >= 0:
            bucket = min(4, int(abs(price_change) * 1000))
        else:
            bucket = 5 + min(4, int(abs(price_change) * 1000))
        return bucket
    
    def _calculate_entropy(self) -> float:
        """
        Calculate Shannon entropy of volume distribution.
        
        H = -Σ p_i × log(p_i)
        """
        buckets = np.array(self._volume_buckets)
        counts = np.bincount(buckets, minlength=10)
        total = np.sum(counts)
        
        if total == 0:
            return np.log(10)  # Maximum entropy
        
        probs = counts / total
        
        # Shannon entropy
        entropy = 0.0
        for p in probs:
            if p > 0:
                entropy -= p * np.log(p)
        
        return entropy
    
    def _estimate_informed_trading(self, entropy: float) -> float:
        """
        Estimate probability of informed trading.
        
        Low entropy = more informed trading.
        """
        max_entropy = np.log(10)
        normalized = entropy / max_entropy
        
        # Low entropy = more informed trading
        return max(0, 1 - normalized)
    
    def _calculate_clustering(self) -> float:
        """
        Calculate degree of volume clustering.
        
        High clustering = volume concentrated in few buckets.
        """
        if len(self._volume_buckets) < 20:
            return 0.5
        
        buckets = np.array(self._volume_buckets)
        
        # Check for runs of same bucket
        runs = 1
        for i in range(1, len(buckets)):
            if buckets[i] == buckets[i-1]:
                runs += 1
        
        return min(1.0, runs / len(buckets) * 2)
    
    def _calculate_entropy_trend(self) -> float:
        """
        Calculate trend in entropy (rising/falling).
        
        Rising entropy = market becoming more random.
        """
        if len(self._entropy_history) < 10:
            return 0.0
        
        recent = np.array(list(self._entropy_history)[-10:])
        std = np.std(recent)
        if std < 1e-8:
            return 0.0
        
        return (recent[-1] - recent[0]) / std
    
    def _create_default_state(self) -> VolumeEntropyState:
        """Create default state for insufficient data."""
        return VolumeEntropyState(
            entropy=np.log(10) / 2,
            information_ratio=0.5,
            noise_floor=0.5,
            informed_trading_prob=0.5,
            volume_clustering=0.5,
            entropy_trend=0.0
        )
    
    def reset(self):
        """Reset tracker state."""
        self._volume_buckets.clear()
        self._entropy_history.clear()
        self._baseline_entropy = 0.0
        self._bar_count = 0


class LiquidityVacuumDetector:
    """
    Detects liquidity vacuums (gaps in order book).
    
    Vacuums indicate jump risk - price may gap through these zones.
    """
    
    def __init__(self, config: MarketIntelligenceConfig):
        self.config = config
        self._price_history = deque(maxlen=500)
        self._volume_history = deque(maxlen=500)
        self._vacuums: List[LiquidityVacuum] = []
        self._bar_count = 0
    
    def update(self, price: float, volume: float) -> List[LiquidityVacuum]:
        """
        Update vacuum detection.
        
        Args:
            price: Current price
            volume: Trade volume
            
        Returns:
            List of detected liquidity vacuums
        """
        self._bar_count += 1
        self._price_history.append(price)
        self._volume_history.append(volume)
        
        if len(self._price_history) < 50:
            return []
        
        # Detect new vacuums
        self._detect_vacuums()
        
        # Update existing vacuums
        self._update_vacuums(price)
        
        # Prune old vacuums
        self._prune_vacuums()
        
        return self._vacuums
    
    def _detect_vacuums(self):
        """
        Detect liquidity vacuums from price/volume patterns.
        
        A vacuum is a price range with very low volume.
        """
        prices = np.array(self._price_history)
        volumes = np.array(self._volume_history)
        
        # Create price bins
        price_min, price_max = np.min(prices), np.max(prices)
        if price_max - price_min < price_min * 0.001:
            return
        
        n_bins = 20
        bins = np.linspace(price_min, price_max, n_bins + 1)
        
        # Calculate volume in each bin
        bin_volumes = np.zeros(n_bins)
        for p, v in zip(prices, volumes):
            bin_idx = min(n_bins - 1, int((p - price_min) / (price_max - price_min) * n_bins))
            bin_volumes[bin_idx] += v
        
        # Normalize
        total_vol = np.sum(bin_volumes)
        if total_vol > 0:
            bin_volumes = bin_volumes / total_vol
        
        # Find vacuums (bins with very low volume)
        mean_vol = np.mean(bin_volumes)
        threshold = mean_vol * 0.2  # 20% of average
        
        for i in range(n_bins):
            if bin_volumes[i] < threshold:
                # Check if vacuum already exists
                price_start = bins[i]
                price_end = bins[i + 1]
                
                exists = False
                for v in self._vacuums:
                    if abs(v.price_start - price_start) < (price_end - price_start) * 0.5:
                        exists = True
                        break
                
                if not exists:
                    # Calculate vacuum strength
                    strength = 1 - bin_volumes[i] / (mean_vol + 1e-8)
                    
                    # Calculate jump risk
                    jump_risk = self._calculate_jump_risk(price_start, price_end)
                    
                    vacuum = LiquidityVacuum(
                        price_start=price_start,
                        price_end=price_end,
                        vacuum_strength=min(1.0, strength),
                        jump_risk=jump_risk,
                        time_detected=time.time(),
                        persistence=0
                    )
                    self._vacuums.append(vacuum)
    
    def _calculate_jump_risk(self, price_start: float, price_end: float) -> float:
        """
        Calculate risk of price jumping through vacuum.
        
        Based on vacuum size and recent volatility.
        """
        if len(self._price_history) < 20:
            return 0.5
        
        prices = np.array(self._price_history)
        volatility = np.std(np.diff(prices))
        
        vacuum_size = price_end - price_start
        
        # Higher risk if vacuum is large relative to volatility
        risk = min(1.0, vacuum_size / (volatility * 3 + 1e-8))
        
        return risk
    
    def _update_vacuums(self, current_price: float):
        """Update existing vacuums."""
        for vacuum in self._vacuums:
            vacuum.persistence += 1
            
            # Check if price entered vacuum
            if vacuum.price_start <= current_price <= vacuum.price_end:
                # Vacuum is being filled
                vacuum.vacuum_strength *= 0.9
    
    def _prune_vacuums(self):
        """Remove old or filled vacuums."""
        self._vacuums = [
            v for v in self._vacuums
            if v.vacuum_strength > 0.1 and v.persistence < 500
        ]
        
        # Keep only top N
        if len(self._vacuums) > self.config.max_vacuums:
            self._vacuums.sort(key=lambda x: x.vacuum_strength, reverse=True)
            self._vacuums = self._vacuums[:self.config.max_vacuums]
    
    def get_vacuum_at_price(self, price: float) -> Optional[LiquidityVacuum]:
        """Get vacuum containing price, if any."""
        for vacuum in self._vacuums:
            if vacuum.price_start <= price <= vacuum.price_end:
                return vacuum
        return None
    
    def reset(self):
        """Reset detector state."""
        self._price_history.clear()
        self._volume_history.clear()
        self._vacuums.clear()
        self._bar_count = 0
