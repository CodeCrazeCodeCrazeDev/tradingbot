"""
Order Flow Decryptor - Advanced Footprint DNA Analysis

This module implements institutional-grade order flow analysis including:
1. Footprint DNA Analysis with Delta-Volume clustering
2. Aggressive vs. passive trade identification
3. Hidden iceberg order detection
4. TICK overlay and market microstructure analysis
5. Heatmap synthesis with economic event calendars
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
try:
    from scipy import signal, stats
except ImportError:
    scipy = None
from scipy.signal import find_peaks
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import warnings
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')

class OrderType(Enum):
    """Order flow types"""
    AGGRESSIVE_BUY = "aggressive_buy"
    AGGRESSIVE_SELL = "aggressive_sell"
    PASSIVE_BUY = "passive_buy"
    PASSIVE_SELL = "passive_sell"
    ICEBERG_BUY = "iceberg_buy"
    ICEBERG_SELL = "iceberg_sell"
    BLOCK_TRADE = "block_trade"
    ALGORITHMIC = "algorithmic"

class ParticipantType(Enum):
    """Market participant types"""
    RETAIL = "retail"
    INSTITUTIONAL = "institutional"
    MARKET_MAKER = "market_maker"
    HFT = "hft"
    HEDGE_FUND = "hedge_fund"
    BANK = "bank"
    UNKNOWN = "unknown"

class FlowDirection(Enum):
    """Order flow directions"""
    BUYING_PRESSURE = "buying_pressure"
    SELLING_PRESSURE = "selling_pressure"
    BALANCED = "balanced"
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"

@dataclass
class FootprintBar:
    """Individual footprint bar data"""
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    total_volume: float
    buy_volume: float
    sell_volume: float
    delta: float
    cumulative_delta: float
    aggressive_trades: int
    passive_trades: int
    large_trades: int
    tick_direction: int

@dataclass
class OrderFlowSignature:
    """Order flow DNA signature"""
    participant_type: ParticipantType
    order_type: OrderType
    volume_profile: np.ndarray
    price_levels: np.ndarray
    time_distribution: np.ndarray
    aggressiveness_score: float
    stealth_score: float
    impact_score: float
    confidence: float

@dataclass
class IcebergOrder:
    """Hidden iceberg order detection"""
    price_level: float
    estimated_size: float
    revealed_size: float
    hidden_ratio: float
    detection_time: datetime
    order_type: OrderType
    participant_type: ParticipantType
    completion_probability: float

@dataclass
class MarketMicrostructure:
    """Market microstructure analysis"""
    bid_ask_spread: float
    market_depth: Dict[float, float]
    order_book_imbalance: float
    tick_rule_delta: float
    effective_spread: float
    price_impact: float
    liquidity_score: float

@dataclass
class OrderFlowHeatmap:
    """Order flow heatmap data"""
    price_levels: np.ndarray
    time_periods: np.ndarray
    volume_matrix: np.ndarray
    delta_matrix: np.ndarray
    aggressiveness_matrix: np.ndarray
    participant_matrix: np.ndarray
    hotspots: List[Tuple[float, datetime, float]]

class FootprintAnalyzer:
    """Advanced footprint chart analysis with DNA pattern recognition"""
    
    def __init__(self, tick_size: float = 0.0001):
        self.tick_size = tick_size
        self.footprint_history = []
        self.dna_patterns = {}
        
    def analyze_footprint_dna(self, df: pd.DataFrame, tick_data: Optional[pd.DataFrame] = None) -> List[FootprintBar]:
        """
        Analyze footprint DNA patterns from price and volume data
        
        Args:
            df: OHLCV data
            tick_data: Optional tick-by-tick data for enhanced analysis
            
        Returns:
            List of footprint bars with DNA analysis
        """
        footprint_bars = []
        
        for i in range(len(df)):
            if i == 0:
                continue
                
            bar_data = df.iloc[i]
            prev_bar = df.iloc[i-1]
            
            # Create footprint bar
            footprint_bar = self._create_footprint_bar(bar_data, prev_bar, tick_data, i)
            footprint_bars.append(footprint_bar)
        
        # Calculate cumulative delta
        self._calculate_cumulative_delta(footprint_bars)
        
        return footprint_bars
    
    def _create_footprint_bar(self, bar_data: pd.Series, prev_bar: pd.Series, 
                            tick_data: Optional[pd.DataFrame], index: int) -> FootprintBar:
        """Create individual footprint bar with DNA analysis"""
        
        # Basic OHLCV data
        timestamp = pd.to_datetime(bar_data.name) if hasattr(bar_data.name, 'to_pydatetime') else datetime.now()
        open_price = bar_data['open']
        high_price = bar_data['high']
        low_price = bar_data['low']
        close_price = bar_data['close']
        total_volume = bar_data.get('volume', 0)
        
        # Estimate buy/sell volume using tick rule
        if tick_data is not None:
            buy_vol, sell_vol, delta = self._calculate_precise_delta(tick_data, timestamp)
        else:
            buy_vol, sell_vol, delta = self._estimate_delta_from_ohlc(bar_data, prev_bar)
        
        # Calculate tick direction
        tick_direction = 1 if close_price > prev_bar['close'] else -1 if close_price < prev_bar['close'] else 0
        
        # Estimate trade types
        aggressive_trades, passive_trades, large_trades = self._estimate_trade_types(
            bar_data, total_volume, delta
        )
        
        return FootprintBar(
            timestamp=timestamp,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            total_volume=total_volume,
            buy_volume=buy_vol,
            sell_volume=sell_vol,
            delta=delta,
            cumulative_delta=0,  # Will be calculated later
            aggressive_trades=aggressive_trades,
            passive_trades=passive_trades,
            large_trades=large_trades,
            tick_direction=tick_direction
        )
    
    def _calculate_precise_delta(self, tick_data: pd.DataFrame, timestamp: datetime) -> Tuple[float, float, float]:
        """Calculate precise delta from tick data"""
        # Filter tick data for this bar's timeframe
        bar_ticks = tick_data[tick_data.index == timestamp]
        
        if bar_ticks.empty:
            return 0, 0, 0
        
        # Classify trades as buy or sell using tick rule
        buy_volume = 0
        sell_volume = 0
        
        for _, tick in bar_ticks.iterrows():
            if 'bid' in tick and 'ask' in tick and 'price' in tick:
                mid_price = (tick['bid'] + tick['ask']) / 2
                if tick['price'] >= mid_price:
                    buy_volume += tick.get('volume', 1)
                else:
                    sell_volume += tick.get('volume', 1)
        
        delta = buy_volume - sell_volume
        return buy_volume, sell_volume, delta
    
    def _estimate_delta_from_ohlc(self, bar_data: pd.Series, prev_bar: pd.Series) -> Tuple[float, float, float]:
        """Estimate delta from OHLC data using various heuristics"""
        total_volume = bar_data.get('volume', 0)
        
        if total_volume == 0:
            return 0, 0, 0
        
        # Method 1: Close vs Open
        close_open_bias = (bar_data['close'] - bar_data['open']) / (bar_data['high'] - bar_data['low']) if bar_data['high'] != bar_data['low'] else 0
        
        # Method 2: Close vs Previous Close
        close_prev_bias = 1 if bar_data['close'] > prev_bar['close'] else -1 if bar_data['close'] < prev_bar['close'] else 0
        
        # Method 3: High/Low position
        if bar_data['high'] != bar_data['low']:
            hl_position = (bar_data['close'] - bar_data['low']) / (bar_data['high'] - bar_data['low'])
        else:
            hl_position = 0.5
        
        # Combine methods
        combined_bias = (close_open_bias + close_prev_bias * 0.3 + (hl_position - 0.5) * 2) / 3
        
        # Estimate buy/sell split
        buy_ratio = 0.5 + combined_bias * 0.3  # Conservative estimate
        buy_ratio = max(0.1, min(0.9, buy_ratio))  # Clamp between 10-90%
        
        buy_volume = total_volume * buy_ratio
        sell_volume = total_volume * (1 - buy_ratio)
        delta = buy_volume - sell_volume
        
        return buy_volume, sell_volume, delta
    
    def _estimate_trade_types(self, bar_data: pd.Series, total_volume: float, delta: float) -> Tuple[int, int, int]:
        """Estimate aggressive, passive, and large trades"""
        if total_volume == 0:
            return 0, 0, 0
        
        # Estimate based on price movement and volume
        price_range = bar_data['high'] - bar_data['low']
        avg_price = (bar_data['high'] + bar_data['low']) / 2
        
        # Aggressive trades (estimated from price impact)
        if avg_price > 0:
            price_impact = price_range / avg_price
            aggressive_ratio = min(price_impact * 100, 0.8)  # Max 80% aggressive
        else:
            aggressive_ratio = 0.3
        
        aggressive_trades = int(total_volume * aggressive_ratio / 100)  # Assume 100 shares per trade
        passive_trades = int(total_volume * (1 - aggressive_ratio) / 100)
        
        # Large trades (estimated from volume spikes)
        large_trade_threshold = total_volume * 0.1  # 10% of volume in single trade
        large_trades = max(1, int(total_volume / large_trade_threshold)) if total_volume > 1000 else 0
        
        return aggressive_trades, passive_trades, large_trades
    
    def _calculate_cumulative_delta(self, footprint_bars: List[FootprintBar]):
        """Calculate cumulative delta across bars"""
        cumulative = 0
        for bar in footprint_bars:
            cumulative += bar.delta
            bar.cumulative_delta = cumulative

class OrderFlowClassifier:
    """Classify order flow patterns and participant types"""
    
    def __init__(self):
        self.classification_models = {}
        self.participant_signatures = {}
        
    def classify_order_signatures(self, footprint_bars: List[FootprintBar]) -> List[OrderFlowSignature]:
        """
        Classify order flow signatures and identify participant types
        
        Args:
            footprint_bars: List of footprint bars
            
        Returns:
            List of order flow signatures
        """
        signatures = []
        
        # Analyze in windows
        window_size = 20
        for i in range(window_size, len(footprint_bars), window_size // 2):
            window_bars = footprint_bars[i-window_size:i]
            signature = self._analyze_window_signature(window_bars)
            signatures.append(signature)
        
        return signatures
    
    def _analyze_window_signature(self, window_bars: List[FootprintBar]) -> OrderFlowSignature:
        """Analyze order flow signature for a window of bars"""
        
        # Extract features
        volumes = np.array([bar.total_volume for bar in window_bars])
        deltas = np.array([bar.delta for bar in window_bars])
        aggressive_ratios = np.array([bar.aggressive_trades / (bar.aggressive_trades + bar.passive_trades + 1) 
                                    for bar in window_bars])
        
        # Create volume profile
        prices = np.array([bar.close_price for bar in window_bars])
        volume_profile = self._create_volume_profile(prices, volumes)
        
        # Create time distribution
        timestamps = [bar.timestamp for bar in window_bars]
        time_distribution = self._create_time_distribution(timestamps, volumes)
        
        # Calculate scores
        aggressiveness_score = np.mean(aggressive_ratios)
        stealth_score = self._calculate_stealth_score(window_bars)
        impact_score = self._calculate_impact_score(window_bars)
        
        # Classify participant type
        participant_type = self._classify_participant_type(
            aggressiveness_score, stealth_score, impact_score, volumes
        )
        
        # Classify order type
        order_type = self._classify_order_type(
            deltas, volumes, aggressive_ratios, participant_type
        )
        
        # Calculate confidence
        confidence = self._calculate_classification_confidence(
            aggressiveness_score, stealth_score, impact_score
        )
        
        return OrderFlowSignature(
            participant_type=participant_type,
            order_type=order_type,
            volume_profile=volume_profile,
            price_levels=prices,
            time_distribution=time_distribution,
            aggressiveness_score=aggressiveness_score,
            stealth_score=stealth_score,
            impact_score=impact_score,
            confidence=confidence
        )
    
    def _create_volume_profile(self, prices: np.ndarray, volumes: np.ndarray) -> np.ndarray:
        """Create volume profile distribution"""
        if len(prices) == 0:
            return np.array([])
        
        # Create price bins
        price_range = prices.max() - prices.min()
        if price_range == 0:
            return np.array([volumes.sum()])
        
        n_bins = min(20, len(prices))
        bins = np.linspace(prices.min(), prices.max(), n_bins + 1)
        
        # Aggregate volume by price level
        volume_profile, _ = np.histogram(prices, bins=bins, weights=volumes)
        
        return volume_profile
    
    def _create_time_distribution(self, timestamps: List[datetime], volumes: np.ndarray) -> np.ndarray:
        """Create time-based volume distribution"""
        if len(timestamps) == 0:
            return np.array([])
        
        # Convert to hours for distribution
        hours = np.array([ts.hour + ts.minute/60 for ts in timestamps])
        
        # Create hourly bins
        hour_bins = np.arange(0, 25, 1)  # 24 hour bins
        time_distribution, _ = np.histogram(hours, bins=hour_bins, weights=volumes)
        
        return time_distribution
    
    def _calculate_stealth_score(self, window_bars: List[FootprintBar]) -> float:
        """Calculate stealth trading score (low market impact)"""
        if not window_bars:
            return 0
        
        # Stealth characteristics:
        # 1. Consistent volume without large spikes
        volumes = np.array([bar.total_volume for bar in window_bars])
        volume_consistency = 1 - (np.std(volumes) / np.mean(volumes)) if np.mean(volumes) > 0 else 0
        volume_consistency = max(0, min(1, volume_consistency))
        
        # 2. Balanced delta (not too aggressive)
        deltas = np.array([abs(bar.delta) for bar in window_bars])
        total_volumes = np.array([bar.total_volume for bar in window_bars])
        delta_ratios = deltas / (total_volumes + 1)  # Avoid division by zero
        delta_balance = 1 - np.mean(delta_ratios)
        
        # 3. Higher passive vs aggressive ratio
        total_aggressive = sum([bar.aggressive_trades for bar in window_bars])
        total_passive = sum([bar.passive_trades for bar in window_bars])
        passive_ratio = total_passive / (total_aggressive + total_passive + 1)
        
        # Combine scores
        stealth_score = (volume_consistency + delta_balance + passive_ratio) / 3
        return max(0, min(1, stealth_score))
    
    def _calculate_impact_score(self, window_bars: List[FootprintBar]) -> float:
        """Calculate market impact score"""
        if len(window_bars) < 2:
            return 0
        
        # Calculate price impact relative to volume
        price_changes = []
        volume_ratios = []
        
        for i in range(1, len(window_bars)):
            price_change = abs(window_bars[i].close_price - window_bars[i-1].close_price)
            avg_price = (window_bars[i].close_price + window_bars[i-1].close_price) / 2
            
            if avg_price > 0:
                normalized_change = price_change / avg_price
                volume_ratio = window_bars[i].total_volume / (window_bars[i-1].total_volume + 1)
                
                price_changes.append(normalized_change)
                volume_ratios.append(volume_ratio)
        
        if not price_changes:
            return 0
        
        # Impact = price movement per unit volume
        avg_price_change = np.mean(price_changes)
        avg_volume_ratio = np.mean(volume_ratios)
        
        impact_score = avg_price_change * avg_volume_ratio * 1000  # Scale up
        return max(0, min(1, impact_score))
    
    def _classify_participant_type(self, aggressiveness_score: float, stealth_score: float, 
                                 impact_score: float, volumes: np.ndarray) -> ParticipantType:
        """Classify market participant type based on order flow characteristics"""
        
        avg_volume = np.mean(volumes) if len(volumes) > 0 else 0
        
        # Institutional characteristics: High stealth, low aggressiveness, high volume
        if stealth_score > 0.6 and aggressiveness_score < 0.4 and avg_volume > 1000:
            return ParticipantType.INSTITUTIONAL
        
        # Market maker characteristics: Balanced, high passive ratio
        if 0.4 < aggressiveness_score < 0.6 and stealth_score > 0.5:
            return ParticipantType.MARKET_MAKER
        
        # HFT characteristics: High aggressiveness, low stealth, high frequency
        if aggressiveness_score > 0.7 and stealth_score < 0.3:
            return ParticipantType.HFT
        
        # Hedge fund characteristics: Moderate stealth, strategic timing
        if stealth_score > 0.4 and impact_score > 0.3 and avg_volume > 500:
            return ParticipantType.HEDGE_FUND
        
        # Bank characteristics: High volume, moderate stealth
        if avg_volume > 2000 and stealth_score > 0.5:
            return ParticipantType.BANK
        
        # Default to retail for small, aggressive trades
        return ParticipantType.RETAIL
    
    def _classify_order_type(self, deltas: np.ndarray, volumes: np.ndarray, 
                           aggressive_ratios: np.ndarray, participant_type: ParticipantType) -> OrderType:
        """Classify order type based on flow characteristics"""
        
        avg_delta = np.mean(deltas)
        avg_aggressive_ratio = np.mean(aggressive_ratios)
        volume_consistency = 1 - (np.std(volumes) / np.mean(volumes)) if np.mean(volumes) > 0 else 0
        
        # Iceberg detection: Consistent volume, low aggressiveness
        if volume_consistency > 0.7 and avg_aggressive_ratio < 0.3:
            return OrderType.ICEBERG_BUY if avg_delta > 0 else OrderType.ICEBERG_SELL
        
        # Block trade: High volume, high impact
        if np.mean(volumes) > 1000 and participant_type in [ParticipantType.INSTITUTIONAL, ParticipantType.BANK]:
            return OrderType.BLOCK_TRADE
        
        # Algorithmic: Very consistent patterns
        if volume_consistency > 0.8 and participant_type == ParticipantType.HFT:
            return OrderType.ALGORITHMIC
        
        # Aggressive vs passive based on ratio
        if avg_aggressive_ratio > 0.6:
            return OrderType.AGGRESSIVE_BUY if avg_delta > 0 else OrderType.AGGRESSIVE_SELL
        else:
            return OrderType.PASSIVE_BUY if avg_delta > 0 else OrderType.PASSIVE_SELL
    
    def _calculate_classification_confidence(self, aggressiveness_score: float, 
                                           stealth_score: float, impact_score: float) -> float:
        """Calculate confidence in classification"""
        
        # Confidence based on how distinct the scores are
        score_variance = np.var([aggressiveness_score, stealth_score, impact_score])
        
        # Higher variance = more distinct characteristics = higher confidence
        confidence = min(1.0, score_variance * 4)  # Scale to 0-1
        
        return max(0.3, confidence)  # Minimum 30% confidence

class IcebergDetector:
    """Detect hidden iceberg orders"""
    
    def __init__(self):
        self.detected_icebergs = []
        self.volume_threshold = 1000  # Minimum volume for iceberg detection
        
    def detect_iceberg_orders(self, footprint_bars: List[FootprintBar], 
                            signatures: List[OrderFlowSignature]) -> List[IcebergOrder]:
        """
        Detect hidden iceberg orders
        
        Args:
            footprint_bars: Footprint bar data
            signatures: Order flow signatures
            
        Returns:
            List of detected iceberg orders
        """
        icebergs = []
        
        # Look for iceberg signatures
        iceberg_signatures = [sig for sig in signatures 
                            if sig.order_type in [OrderType.ICEBERG_BUY, OrderType.ICEBERG_SELL]]
        
        for signature in iceberg_signatures:
            iceberg = self._analyze_iceberg_signature(signature, footprint_bars)
            if iceberg:
                icebergs.append(iceberg)
        
        # Additional detection using volume clustering
        volume_icebergs = self._detect_volume_icebergs(footprint_bars)
        icebergs.extend(volume_icebergs)
        
        return icebergs
    
    def _analyze_iceberg_signature(self, signature: OrderFlowSignature, 
                                 footprint_bars: List[FootprintBar]) -> Optional[IcebergOrder]:
        """Analyze individual iceberg signature"""
        
        if len(signature.price_levels) == 0:
            return None
        
        # Find the dominant price level
        volume_profile = signature.volume_profile
        if len(volume_profile) == 0:
            return None
        
        dominant_level_idx = np.argmax(volume_profile)
        price_level = signature.price_levels[dominant_level_idx] if dominant_level_idx < len(signature.price_levels) else signature.price_levels[0]
        
        # Estimate total and revealed size
        total_volume = np.sum(volume_profile)
        revealed_size = np.max(volume_profile)  # Largest single showing
        
        # Calculate hidden ratio
        hidden_ratio = 1 - (revealed_size / total_volume) if total_volume > 0 else 0
        
        # Only consider significant icebergs
        if total_volume < self.volume_threshold or hidden_ratio < 0.5:
            return None
        
        # Determine order type
        order_type = signature.order_type
        
        # Estimate participant type
        participant_type = signature.participant_type
        
        # Calculate completion probability
        completion_probability = self._estimate_completion_probability(signature, footprint_bars)
        
        return IcebergOrder(
            price_level=price_level,
            estimated_size=total_volume,
            revealed_size=revealed_size,
            hidden_ratio=hidden_ratio,
            detection_time=datetime.now(),
            order_type=order_type,
            participant_type=participant_type,
            completion_probability=completion_probability
        )
    
    def _detect_volume_icebergs(self, footprint_bars: List[FootprintBar]) -> List[IcebergOrder]:
        """Detect icebergs using volume clustering analysis"""
        icebergs = []
        
        if len(footprint_bars) < 20:
            return icebergs
        
        # Extract price and volume data
        prices = np.array([bar.close_price for bar in footprint_bars])
        volumes = np.array([bar.total_volume for bar in footprint_bars])
        
        # Find volume clusters at specific price levels
        price_volume_pairs = np.column_stack((prices, volumes))
        
        # Use DBSCAN to find volume clusters
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(price_volume_pairs)
        
        clustering = DBSCAN(eps=0.3, min_samples=5).fit(scaled_data)
        
        # Analyze each cluster
        for label in set(clustering.labels_):
            if label == -1:  # Noise
                continue
            
            cluster_mask = clustering.labels_ == label
            cluster_prices = prices[cluster_mask]
            cluster_volumes = volumes[cluster_mask]
            
            # Check for iceberg characteristics
            if len(cluster_volumes) >= 5 and np.sum(cluster_volumes) > self.volume_threshold:
                # Consistent volume at similar price levels
                volume_consistency = 1 - (np.std(cluster_volumes) / np.mean(cluster_volumes))
                
                if volume_consistency > 0.6:  # High consistency suggests iceberg
                    avg_price = np.mean(cluster_prices)
                    total_size = np.sum(cluster_volumes)
                    avg_revealed = np.mean(cluster_volumes)
                    hidden_ratio = 1 - (avg_revealed / total_size)
                    
                    # Determine direction based on price trend
                    if len(cluster_prices) > 1:
                        price_trend = np.polyfit(range(len(cluster_prices)), cluster_prices, 1)[0]
                        order_type = OrderType.ICEBERG_BUY if price_trend >= 0 else OrderType.ICEBERG_SELL
                    else:
                        order_type = OrderType.ICEBERG_BUY
                    
                    iceberg = IcebergOrder(
                        price_level=avg_price,
                        estimated_size=total_size,
                        revealed_size=avg_revealed,
                        hidden_ratio=hidden_ratio,
                        detection_time=datetime.now(),
                        order_type=order_type,
                        participant_type=ParticipantType.INSTITUTIONAL,
                        completion_probability=0.7
                    )
                    
                    icebergs.append(iceberg)
        
        return icebergs
    
    def _estimate_completion_probability(self, signature: OrderFlowSignature, 
                                       footprint_bars: List[FootprintBar]) -> float:
        """Estimate probability of iceberg order completion"""
        
        # Base probability
        base_prob = 0.6
        
        # Adjust based on stealth score (higher stealth = higher completion probability)
        base_prob += signature.stealth_score * 0.2
        
        # Adjust based on participant type
        if signature.participant_type == ParticipantType.INSTITUTIONAL:
            base_prob += 0.1
        elif signature.participant_type == ParticipantType.BANK:
            base_prob += 0.15
        
        # Adjust based on market conditions (volatility)
        recent_bars = footprint_bars[-10:] if len(footprint_bars) >= 10 else footprint_bars
        if recent_bars:
            price_volatility = np.std([bar.close_price for bar in recent_bars])
            avg_price = np.mean([bar.close_price for bar in recent_bars])
            normalized_volatility = price_volatility / avg_price if avg_price > 0 else 0
            
            # High volatility reduces completion probability
            base_prob -= normalized_volatility * 100 * 0.2
        
        return max(0.2, min(0.95, base_prob))

class OrderFlowHeatmapGenerator:
    """Generate order flow heatmaps with economic event integration"""
    
    def __init__(self):
        self.economic_events = {}
        self.heatmap_history = []
        
    def generate_heatmap(self, footprint_bars: List[FootprintBar], 
                        signatures: List[OrderFlowSignature],
                        economic_calendar: Optional[Dict] = None) -> OrderFlowHeatmap:
        """
        Generate comprehensive order flow heatmap
        
        Args:
            footprint_bars: Footprint bar data
            signatures: Order flow signatures
            economic_calendar: Economic events calendar
            
        Returns:
            Order flow heatmap
        """
        if not footprint_bars:
            return self._empty_heatmap()
        
        # Create price and time grids
        prices = np.array([bar.close_price for bar in footprint_bars])
        timestamps = [bar.timestamp for bar in footprint_bars]
        
        price_levels = self._create_price_levels(prices)
        time_periods = self._create_time_periods(timestamps)
        
        # Create matrices
        volume_matrix = self._create_volume_matrix(footprint_bars, price_levels, time_periods)
        delta_matrix = self._create_delta_matrix(footprint_bars, price_levels, time_periods)
        aggressiveness_matrix = self._create_aggressiveness_matrix(footprint_bars, price_levels, time_periods)
        participant_matrix = self._create_participant_matrix(signatures, price_levels, time_periods)
        
        # Identify hotspots
        hotspots = self._identify_hotspots(volume_matrix, delta_matrix, price_levels, time_periods)
        
        # Integrate economic events
        if economic_calendar:
            hotspots = self._integrate_economic_events(hotspots, economic_calendar, time_periods)
        
        return OrderFlowHeatmap(
            price_levels=price_levels,
            time_periods=time_periods,
            volume_matrix=volume_matrix,
            delta_matrix=delta_matrix,
            aggressiveness_matrix=aggressiveness_matrix,
            participant_matrix=participant_matrix,
            hotspots=hotspots
        )
    
    def _create_price_levels(self, prices: np.ndarray, n_levels: int = 50) -> np.ndarray:
        """Create price level grid"""
        if len(prices) == 0:
            return np.array([])
        
        min_price = prices.min()
        max_price = prices.max()
        
        if min_price == max_price:
            return np.array([min_price])
        
        return np.linspace(min_price, max_price, n_levels)
    
    def _create_time_periods(self, timestamps: List[datetime], n_periods: int = 24) -> np.ndarray:
        """Create time period grid (hourly)"""
        if not timestamps:
            return np.array([])
        
        # Create hourly periods
        start_time = min(timestamps)
        end_time = max(timestamps)
        
        time_range = (end_time - start_time).total_seconds() / 3600  # Hours
        
        if time_range <= 0:
            return np.array([start_time])
        
        periods = []
        for i in range(n_periods):
            period_time = start_time + timedelta(hours=i * time_range / n_periods)
            periods.append(period_time)
        
        return np.array(periods)
    
    def _create_volume_matrix(self, footprint_bars: List[FootprintBar], 
                            price_levels: np.ndarray, time_periods: np.ndarray) -> np.ndarray:
        """Create volume heatmap matrix"""
        if len(price_levels) == 0 or len(time_periods) == 0:
            return np.array([[]])
        
        matrix = np.zeros((len(price_levels), len(time_periods)))
        
        for bar in footprint_bars:
            # Find closest price level
            price_idx = np.argmin(np.abs(price_levels - bar.close_price))
            
            # Find closest time period
            time_diffs = [abs((period - bar.timestamp).total_seconds()) for period in time_periods]
            time_idx = np.argmin(time_diffs)
            
            # Add volume to matrix
            matrix[price_idx, time_idx] += bar.total_volume
        
        return matrix
    
    def _create_delta_matrix(self, footprint_bars: List[FootprintBar], 
                           price_levels: np.ndarray, time_periods: np.ndarray) -> np.ndarray:
        """Create delta heatmap matrix"""
        if len(price_levels) == 0 or len(time_periods) == 0:
            return np.array([[]])
        
        matrix = np.zeros((len(price_levels), len(time_periods)))
        
        for bar in footprint_bars:
            price_idx = np.argmin(np.abs(price_levels - bar.close_price))
            time_diffs = [abs((period - bar.timestamp).total_seconds()) for period in time_periods]
            time_idx = np.argmin(time_diffs)
            
            matrix[price_idx, time_idx] += bar.delta
        
        return matrix
    
    def _create_aggressiveness_matrix(self, footprint_bars: List[FootprintBar], 
                                    price_levels: np.ndarray, time_periods: np.ndarray) -> np.ndarray:
        """Create aggressiveness heatmap matrix"""
        if len(price_levels) == 0 or len(time_periods) == 0:
            return np.array([[]])
        
        matrix = np.zeros((len(price_levels), len(time_periods)))
        
        for bar in footprint_bars:
            price_idx = np.argmin(np.abs(price_levels - bar.close_price))
            time_diffs = [abs((period - bar.timestamp).total_seconds()) for period in time_periods]
            time_idx = np.argmin(time_diffs)
            
            total_trades = bar.aggressive_trades + bar.passive_trades
            aggressiveness = bar.aggressive_trades / total_trades if total_trades > 0 else 0
            
            matrix[price_idx, time_idx] += aggressiveness * bar.total_volume
        
        return matrix
    
    def _create_participant_matrix(self, signatures: List[OrderFlowSignature], 
                                 price_levels: np.ndarray, time_periods: np.ndarray) -> np.ndarray:
        """Create participant type heatmap matrix"""
        if len(price_levels) == 0 or len(time_periods) == 0 or not signatures:
            return np.array([[]])
        
        # Encode participant types as numbers
        participant_encoding = {
            ParticipantType.RETAIL: 1,
            ParticipantType.INSTITUTIONAL: 2,
            ParticipantType.MARKET_MAKER: 3,
            ParticipantType.HFT: 4,
            ParticipantType.HEDGE_FUND: 5,
            ParticipantType.BANK: 6,
            ParticipantType.UNKNOWN: 0
        }
        
        matrix = np.zeros((len(price_levels), len(time_periods)))
        
        for signature in signatures:
            if len(signature.price_levels) == 0:
                continue
            
            avg_price = np.mean(signature.price_levels)
            price_idx = np.argmin(np.abs(price_levels - avg_price))
            
            # Use current time as approximation
            time_idx = len(time_periods) // 2  # Middle time period
            
            participant_code = participant_encoding.get(signature.participant_type, 0)
            matrix[price_idx, time_idx] = participant_code
        
        return matrix
    
    def _identify_hotspots(self, volume_matrix: np.ndarray, delta_matrix: np.ndarray, 
                         price_levels: np.ndarray, time_periods: np.ndarray) -> List[Tuple[float, datetime, float]]:
        """Identify order flow hotspots"""
        hotspots = []
        
        if volume_matrix.size == 0 or delta_matrix.size == 0:
            return hotspots
        
        # Find high volume areas
        volume_threshold = np.percentile(volume_matrix, 90)  # Top 10%
        high_volume_indices = np.where(volume_matrix > volume_threshold)
        
        # Find high delta areas
        delta_threshold = np.percentile(np.abs(delta_matrix), 90)  # Top 10%
        high_delta_indices = np.where(np.abs(delta_matrix) > delta_threshold)
        
        # Combine volume and delta hotspots
        all_hotspot_indices = set(zip(high_volume_indices[0], high_volume_indices[1])) | \
                             set(zip(high_delta_indices[0], high_delta_indices[1]))
        
        for price_idx, time_idx in all_hotspot_indices:
            if price_idx < len(price_levels) and time_idx < len(time_periods):
                price = price_levels[price_idx]
                timestamp = time_periods[time_idx]
                intensity = volume_matrix[price_idx, time_idx] + abs(delta_matrix[price_idx, time_idx])
                
                hotspots.append((price, timestamp, intensity))
        
        # Sort by intensity
        hotspots.sort(key=lambda x: x[2], reverse=True)
        
        return hotspots[:20]  # Top 20 hotspots
    
    def _integrate_economic_events(self, hotspots: List[Tuple[float, datetime, float]], 
                                 economic_calendar: Dict, time_periods: np.ndarray) -> List[Tuple[float, datetime, float]]:
        """Integrate economic events with hotspots"""
        enhanced_hotspots = hotspots.copy()
        
        # Add economic event impact to nearby hotspots
        for event_time, event_data in economic_calendar.items():
            event_impact = event_data.get('impact', 'medium')
            impact_multiplier = {'high': 2.0, 'medium': 1.5, 'low': 1.2}.get(event_impact, 1.0)
            
            # Find hotspots within 1 hour of event
            for i, (price, timestamp, intensity) in enumerate(enhanced_hotspots):
                time_diff = abs((timestamp - event_time).total_seconds()) / 3600  # Hours
                
                if time_diff <= 1.0:  # Within 1 hour
                    # Enhance intensity based on event impact
                    enhanced_intensity = intensity * impact_multiplier
                    enhanced_hotspots[i] = (price, timestamp, enhanced_intensity)
        
        # Re-sort by intensity
        enhanced_hotspots.sort(key=lambda x: x[2], reverse=True)
        
        return enhanced_hotspots
    
    def _empty_heatmap(self) -> OrderFlowHeatmap:
        """Return empty heatmap"""
        return OrderFlowHeatmap(
            price_levels=np.array([]),
            time_periods=np.array([]),
            volume_matrix=np.array([[]]),
            delta_matrix=np.array([[]]),
            aggressiveness_matrix=np.array([[]]),
            participant_matrix=np.array([[]]),
            hotspots=[]
        )

class OrderFlowDecryptor:
    """Main order flow decryptor combining all analysis components"""
    
    def __init__(self, tick_size: float = 0.0001):
        self.footprint_analyzer = FootprintAnalyzer(tick_size)
        self.flow_classifier = OrderFlowClassifier()
        self.iceberg_detector = IcebergDetector()
        self.heatmap_generator = OrderFlowHeatmapGenerator()
        
    def decrypt_order_flow(self, df: pd.DataFrame, tick_data: Optional[pd.DataFrame] = None,
                          economic_calendar: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Comprehensive order flow decryption
        
        Args:
            df: OHLCV data
            tick_data: Optional tick-by-tick data
            economic_calendar: Optional economic events
            
        Returns:
            Complete order flow analysis
        """
        # Analyze footprint DNA
        footprint_bars = self.footprint_analyzer.analyze_footprint_dna(df, tick_data)
        
        # Classify order signatures
        signatures = self.flow_classifier.classify_order_signatures(footprint_bars)
        
        # Detect iceberg orders
        icebergs = self.iceberg_detector.detect_iceberg_orders(footprint_bars, signatures)
        
        # Generate heatmap
        heatmap = self.heatmap_generator.generate_heatmap(footprint_bars, signatures, economic_calendar)
        
        # Generate trading signals
        signals = self._generate_order_flow_signals(footprint_bars, signatures, icebergs, heatmap)
        
        return {
            'footprint_bars': footprint_bars,
            'order_signatures': signatures,
            'iceberg_orders': icebergs,
            'heatmap': heatmap,
            'signals': signals,
            'summary': self._generate_summary(footprint_bars, signatures, icebergs)
        }
    
    def _generate_order_flow_signals(self, footprint_bars: List[FootprintBar], 
                                   signatures: List[OrderFlowSignature],
                                   icebergs: List[IcebergOrder],
                                   heatmap: OrderFlowHeatmap) -> Dict[str, Any]:
        """Generate trading signals from order flow analysis"""
        
        signals = {
            'delta_signal': self._generate_delta_signal(footprint_bars),
            'participant_signal': self._generate_participant_signal(signatures),
            'iceberg_signal': self._generate_iceberg_signal(icebergs),
            'hotspot_signal': self._generate_hotspot_signal(heatmap),
            'overall_signal': None
        }
        
        # Generate overall signal
        signals['overall_signal'] = self._generate_overall_signal(signals)
        
        return signals
    
    def _generate_delta_signal(self, footprint_bars: List[FootprintBar]) -> Dict[str, Any]:
        """Generate signal from delta analysis"""
        if not footprint_bars:
            return {'signal': 'neutral', 'strength': 0}
        
        recent_bars = footprint_bars[-10:]  # Last 10 bars
        
        # Calculate delta metrics
        total_delta = sum([bar.delta for bar in recent_bars])
        cumulative_delta = recent_bars[-1].cumulative_delta if recent_bars else 0
        
        # Delta divergence
        prices = [bar.close_price for bar in recent_bars]
        deltas = [bar.delta for bar in recent_bars]
        
        if len(prices) >= 5:
            price_trend = np.polyfit(range(len(prices)), prices, 1)[0]
            delta_trend = np.polyfit(range(len(deltas)), deltas, 1)[0]
            
            # Bullish divergence: price down, delta up
            # Bearish divergence: price up, delta down
            divergence = (price_trend < 0 and delta_trend > 0) or (price_trend > 0 and delta_trend < 0)
        else:
            divergence = False
        
        # Generate signal
        if total_delta > 0 and cumulative_delta > 0:
            signal = 'bullish'
            strength = min(abs(total_delta) / 10000, 1.0)  # Normalize
        elif total_delta < 0 and cumulative_delta < 0:
            signal = 'bearish'
            strength = min(abs(total_delta) / 10000, 1.0)
        else:
            signal = 'neutral'
            strength = 0
        
        return {
            'signal': signal,
            'strength': strength,
            'total_delta': total_delta,
            'cumulative_delta': cumulative_delta,
            'divergence': divergence
        }
    
    def _generate_participant_signal(self, signatures: List[OrderFlowSignature]) -> Dict[str, Any]:
        """Generate signal from participant analysis"""
        if not signatures:
            return {'signal': 'neutral', 'strength': 0}
        
        recent_signatures = signatures[-5:]  # Last 5 signatures
        
        # Count participant types
        participant_counts = {}
        for sig in recent_signatures:
            participant_counts[sig.participant_type] = participant_counts.get(sig.participant_type, 0) + 1
        
        # Identify dominant participant
        dominant_participant = max(participant_counts, key=participant_counts.get)
        
        # Generate signal based on dominant participant
        if dominant_participant == ParticipantType.INSTITUTIONAL:
            signal = 'institutional_flow'
            strength = 0.8
        elif dominant_participant == ParticipantType.MARKET_MAKER:
            signal = 'mm_controlled'
            strength = 0.6
        elif dominant_participant == ParticipantType.HFT:
            signal = 'hft_active'
            strength = 0.7
        else:
            signal = 'retail_dominated'
            strength = 0.4
        
        return {
            'signal': signal,
            'strength': strength,
            'dominant_participant': dominant_participant.value,
            'participant_distribution': {p.value: c for p, c in participant_counts.items()}
        }
    
    def _generate_iceberg_signal(self, icebergs: List[IcebergOrder]) -> Dict[str, Any]:
        """Generate signal from iceberg detection"""
        if not icebergs:
            return {'signal': 'no_icebergs', 'strength': 0}
        
        active_icebergs = [ice for ice in icebergs if ice.completion_probability > 0.5]
        
        if not active_icebergs:
            return {'signal': 'no_active_icebergs', 'strength': 0}
        
        # Find largest iceberg
        largest_iceberg = max(active_icebergs, key=lambda x: x.estimated_size)
        
        # Generate signal based on iceberg direction
        if largest_iceberg.order_type in [OrderType.ICEBERG_BUY, OrderType.AGGRESSIVE_BUY]:
            signal = 'iceberg_support'
        elif largest_iceberg.order_type in [OrderType.ICEBERG_SELL, OrderType.AGGRESSIVE_SELL]:
            signal = 'iceberg_resistance'
        else:
            signal = 'iceberg_detected'
        
        strength = min(largest_iceberg.estimated_size / 10000, 1.0)  # Normalize
        
        return {
            'signal': signal,
            'strength': strength,
            'iceberg_count': len(active_icebergs),
            'largest_size': largest_iceberg.estimated_size,
            'price_level': largest_iceberg.price_level
        }
    
    def _generate_hotspot_signal(self, heatmap: OrderFlowHeatmap) -> Dict[str, Any]:
        """Generate signal from hotspot analysis"""
        if not heatmap.hotspots:
            return {'signal': 'no_hotspots', 'strength': 0}
        
        # Get strongest hotspot
        strongest_hotspot = heatmap.hotspots[0]  # Already sorted by intensity
        
        price, timestamp, intensity = strongest_hotspot
        
        # Determine signal based on hotspot characteristics
        signal = 'high_activity_zone'
        strength = min(intensity / 10000, 1.0)  # Normalize
        
        return {
            'signal': signal,
            'strength': strength,
            'hotspot_price': price,
            'hotspot_time': timestamp,
            'intensity': intensity,
            'total_hotspots': len(heatmap.hotspots)
        }
    
    def _generate_overall_signal(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall order flow signal"""
        # Extract signal strengths
        delta_strength = signals['delta_signal']['strength']
        participant_strength = signals['participant_signal']['strength']
        iceberg_strength = signals['iceberg_signal']['strength']
        hotspot_strength = signals['hotspot_signal']['strength']
        
        # Weighted combination
        overall_strength = (
            delta_strength * 0.4 +
            participant_strength * 0.3 +
            iceberg_strength * 0.2 +
            hotspot_strength * 0.1
        )
        
        # Determine direction
        delta_signal = signals['delta_signal']['signal']
        if delta_signal == 'bullish':
            direction = 'bullish'
        elif delta_signal == 'bearish':
            direction = 'bearish'
        else:
            direction = 'neutral'
        
        # Quality assessment
        if overall_strength > 0.7:
            quality = 'high'
        elif overall_strength > 0.4:
            quality = 'medium'
        else:
            quality = 'low'
        
        return {
            'direction': direction,
            'strength': overall_strength,
            'quality': quality,
            'confidence': overall_strength,
            'components': {
                'delta': delta_strength,
                'participant': participant_strength,
                'iceberg': iceberg_strength,
                'hotspot': hotspot_strength
            }
        }
    
    def _generate_summary(self, footprint_bars: List[FootprintBar], 
                         signatures: List[OrderFlowSignature],
                         icebergs: List[IcebergOrder]) -> Dict[str, Any]:
        """Generate analysis summary"""
        
        summary = {
            'total_bars_analyzed': len(footprint_bars),
            'total_signatures': len(signatures),
            'total_icebergs': len(icebergs),
            'analysis_period': None,
            'dominant_flow': None,
            'key_insights': []
        }
        
        if footprint_bars:
            summary['analysis_period'] = {
                'start': footprint_bars[0].timestamp,
                'end': footprint_bars[-1].timestamp
            }
            
            # Calculate dominant flow
            total_delta = sum([bar.delta for bar in footprint_bars])
            if total_delta > 0:
                summary['dominant_flow'] = 'buying_pressure'
            elif total_delta < 0:
                summary['dominant_flow'] = 'selling_pressure'
            else:
                summary['dominant_flow'] = 'balanced'
        
        # Generate key insights
        insights = []
        
        if signatures:
            institutional_sigs = len([s for s in signatures if s.participant_type == ParticipantType.INSTITUTIONAL])
            if institutional_sigs > len(signatures) * 0.3:
                insights.append("High institutional activity detected")
        
        if icebergs:
            large_icebergs = len([i for i in icebergs if i.estimated_size > 5000])
            if large_icebergs > 0:
                insights.append(f"{large_icebergs} large iceberg orders detected")
        
        if footprint_bars:
            high_delta_bars = len([b for b in footprint_bars if abs(b.delta) > 1000])
            if high_delta_bars > len(footprint_bars) * 0.2:
                insights.append("Significant order flow imbalances present")
        
        summary['key_insights'] = insights
        
        return summary
