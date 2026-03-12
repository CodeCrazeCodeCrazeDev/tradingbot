"""
Advanced Liquidity & Order Flow Indicators
Iceberg Detection, Absorption Ratio, CVD Multi-TF, TIB Analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import logging
import numpy
import pandas

logger = logging.getLogger(__name__)


@dataclass
class IcebergOrder:
    """Detected iceberg order."""
    timestamp: pd.Timestamp
    price: float
    cumulative_volume: float
    detection_confidence: float
    side: str  # 'buy' or 'sell'
    absorption_strength: float


class IcebergDetector:
    """
    Iceberg Order Detection
    Detects hidden institutional accumulation/distribution
    """
    
    def __init__(self, volume_threshold: float = 2.0, price_tolerance: float = 0.0001):
        self.volume_threshold = volume_threshold
        self.price_tolerance = price_tolerance
        self.detected_icebergs: List[IcebergOrder] = []
        
    def detect(self, df: pd.DataFrame) -> List[IcebergOrder]:
        """Detect iceberg orders in price/volume data."""
        icebergs = []
        
        # Calculate volume profile
        avg_volume = df['volume'].rolling(20).mean()
        volume_std = df['volume'].rolling(20).std()
        
        for i in range(20, len(df)):
            current_price = df['close'].iloc[i]
            current_volume = df['volume'].iloc[i]
            
            # Check for repeated large volume at similar price
            price_mask = (
                (df['close'].iloc[i-20:i] >= current_price * (1 - self.price_tolerance)) &
                (df['close'].iloc[i-20:i] <= current_price * (1 + self.price_tolerance))
            )
            
            similar_price_volumes = df['volume'].iloc[i-20:i][price_mask]
            
            if len(similar_price_volumes) >= 3:
                cumulative = similar_price_volumes.sum()
                avg_vol = avg_volume.iloc[i]
                
                # Iceberg detected if cumulative volume is significantly high
                if cumulative > avg_vol * self.volume_threshold * len(similar_price_volumes):
                    # Determine side
                    price_change = df['close'].iloc[i] - df['close'].iloc[i-20]
                    side = 'buy' if price_change >= 0 else 'sell'
                    
                    # Calculate absorption strength
                    absorption = cumulative / (avg_vol * 20)
                    
                    # Confidence based on volume consistency
                    volume_consistency = 1.0 - (similar_price_volumes.std() / similar_price_volumes.mean())
                    
                    iceberg = IcebergOrder(
                        timestamp=df.index[i],
                        price=current_price,
                        cumulative_volume=cumulative,
                        detection_confidence=volume_consistency,
                        side=side,
                        absorption_strength=absorption
                    )
                    
                    icebergs.append(iceberg)
        
        self.detected_icebergs = icebergs
        return icebergs


class AbsorptionExhaustionRatio:
    """
    Absorption vs Exhaustion Imbalance Ratio
    Identifies strong reversals early
    """
    
    def __init__(self, lookback: int = 20):
        self.lookback = lookback
        
    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate absorption/exhaustion ratio.
        > 1.0: Absorption (support)
        < 1.0: Exhaustion (resistance)
        """
        ratio = pd.Series(index=df.index, dtype=float)
        
        for i in range(self.lookback, len(df)):
            window = df.iloc[i-self.lookback:i]
            
            # Absorption: High volume with small price change (support)
            volume_increase = window['volume'] > window['volume'].mean()
            price_stable = abs(window['close'].pct_change()) < window['close'].pct_change().std()
            absorption_bars = (volume_increase & price_stable).sum()
            
            # Exhaustion: High volume with large price change (resistance)
            price_volatile = abs(window['close'].pct_change()) > window['close'].pct_change().std()
            exhaustion_bars = (volume_increase & price_volatile).sum()
            
            if exhaustion_bars > 0:
                ratio.iloc[i] = absorption_bars / exhaustion_bars
            else:
                ratio.iloc[i] = 2.0  # Strong absorption
        
        return ratio


class CVDMultiTimeframe:
    """
    Cumulative Volume Delta Multi-Timeframe View
    Improves confidence in flow direction
    """
    
    def __init__(self, timeframes: List[str] = None):
        self.timeframes = timeframes or ['5T', '15T', '1H', '4H']
        self.cvd_cache = {}
        
    def calculate_cvd(self, df: pd.DataFrame) -> pd.Series:
        """Calculate basic CVD (Cumulative Volume Delta)."""
        # Approximate delta using close vs open
        delta = np.where(
            df['close'] > df['open'],
            df['volume'],
            -df['volume']
        )
        
        cvd = pd.Series(delta, index=df.index).cumsum()
        return cvd
    
    def calculate_multi_tf(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate CVD across multiple timeframes."""
        cvd_results = {}
        
        for tf in self.timeframes:
            # Resample to timeframe
            resampled = df.resample(tf).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            # Calculate CVD for this timeframe
            cvd = self.calculate_cvd(resampled)
            
            # Interpolate back to original timeframe
            cvd_interpolated = cvd.reindex(df.index, method='ffill')
            
            cvd_results[tf] = cvd_interpolated
            self.cvd_cache[tf] = cvd
        
        return cvd_results
    
    def get_alignment_score(self, cvd_dict: Dict[str, pd.Series]) -> float:
        """
        Calculate alignment score across timeframes.
        1.0 = All timeframes aligned
        0.0 = No alignment
        """
        # Get last value direction for each timeframe
        directions = []
        for tf, cvd in cvd_dict.items():
            if len(cvd) >= 2:
                direction = 1 if cvd.iloc[-1] > cvd.iloc[-2] else -1
                directions.append(direction)
        
        if not directions:
            return 0.5
        
        # Calculate alignment
        alignment = abs(sum(directions)) / len(directions)
        return alignment


class TickImbalanceBar:
    """
    Tick Imbalance Bar Analysis (TIB)
    Creates adaptive bars based on trade imbalance, not time
    """
    
    def __init__(self, imbalance_threshold: int = 1000):
        self.imbalance_threshold = imbalance_threshold
        self.bars = []
        
    def create_bars(self, ticks: pd.DataFrame) -> pd.DataFrame:
        """
        Create tick imbalance bars from tick data.
        ticks should have: timestamp, price, volume, side (1=buy, -1=sell)
        """
        bars = []
        current_bar = {
            'open': None,
            'high': -np.inf,
            'low': np.inf,
            'close': None,
            'volume': 0,
            'buy_volume': 0,
            'sell_volume': 0,
            'tick_count': 0,
            'start_time': None,
            'end_time': None
        }
        
        cumulative_imbalance = 0
        
        for idx, tick in ticks.iterrows():
            # Initialize bar
            if current_bar['open'] is None:
                current_bar['open'] = tick['price']
                current_bar['start_time'] = tick.name
            
            # Update bar
            current_bar['high'] = max(current_bar['high'], tick['price'])
            current_bar['low'] = min(current_bar['low'], tick['price'])
            current_bar['close'] = tick['price']
            current_bar['volume'] += tick['volume']
            current_bar['tick_count'] += 1
            current_bar['end_time'] = tick.name
            
            # Track buy/sell volume
            if tick.get('side', 1) > 0:
                current_bar['buy_volume'] += tick['volume']
                cumulative_imbalance += tick['volume']
            else:
                current_bar['sell_volume'] += tick['volume']
                cumulative_imbalance -= tick['volume']
            
            # Check if bar should close
            if abs(cumulative_imbalance) >= self.imbalance_threshold:
                bars.append(current_bar.copy())
                
                # Reset for next bar
                current_bar = {
                    'open': None,
                    'high': -np.inf,
                    'low': np.inf,
                    'close': None,
                    'volume': 0,
                    'buy_volume': 0,
                    'sell_volume': 0,
                    'tick_count': 0,
                    'start_time': None,
                    'end_time': None
                }
                cumulative_imbalance = 0
        
        # Convert to DataFrame
        if bars:
            df_bars = pd.DataFrame(bars)
            df_bars['imbalance'] = df_bars['buy_volume'] - df_bars['sell_volume']
            df_bars['imbalance_ratio'] = df_bars['buy_volume'] / (df_bars['sell_volume'] + 1)
            return df_bars
        else:
            return pd.DataFrame()


class VolumeDeltaHeatmap:
    """
    Volume Delta Heatmap (Footprint Chart Style)
    Visualizes real buy/sell pressure at each price level
    """
    
    def __init__(self, price_bins: int = 50):
        self.price_bins = price_bins
        
    def create_heatmap(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create volume delta heatmap."""
        # Determine price range
        price_min = df['low'].min()
        price_max = df['high'].max()
        price_step = (price_max - price_min) / self.price_bins
        
        # Create price levels
        price_levels = np.arange(price_min, price_max, price_step)
        
        # Initialize heatmap
        heatmap = pd.DataFrame(
            index=df.index,
            columns=price_levels,
            data=0.0
        )
        
        # Fill heatmap
        for idx, row in df.iterrows():
            # Determine which price levels this candle touched
            touched_levels = price_levels[
                (price_levels >= row['low']) & (price_levels <= row['high'])
            ]
            
            # Distribute volume across touched levels
            if len(touched_levels) > 0:
                # Approximate delta
                delta = row['volume'] if row['close'] > row['open'] else -row['volume']
                volume_per_level = delta / len(touched_levels)
                
                for level in touched_levels:
                    heatmap.loc[idx, level] = volume_per_level
        
        return heatmap
    
    def get_high_activity_zones(self, heatmap: pd.DataFrame, 
                               threshold_percentile: float = 90) -> List[float]:
        """Identify price levels with high activity."""
        # Sum volume across time for each price level
        level_totals = heatmap.abs().sum(axis=0)
        
        # Find levels above threshold
        threshold = level_totals.quantile(threshold_percentile / 100)
        high_activity = level_totals[level_totals >= threshold]
        
        return list(high_activity.index)


class OrderBookImbalance:
    """
    Order Book Imbalance Sentiment
    Analyzes depth data for directional bias
    """
    
    def __init__(self, depth_levels: int = 10):
        self.depth_levels = depth_levels
        
    def calculate_imbalance(self, bid_depth: List[Tuple[float, float]], 
                           ask_depth: List[Tuple[float, float]]) -> Dict[str, float]:
        """
        Calculate order book imbalance.
        bid_depth/ask_depth: List of (price, volume) tuples
        """
        # Sum volumes
        total_bid_volume = sum(vol for _, vol in bid_depth[:self.depth_levels])
        total_ask_volume = sum(vol for _, vol in ask_depth[:self.depth_levels])
        
        # Calculate imbalance ratio
        total_volume = total_bid_volume + total_ask_volume
        if total_volume > 0:
            imbalance_ratio = (total_bid_volume - total_ask_volume) / total_volume
        else:
            imbalance_ratio = 0.0
        
        # Calculate weighted imbalance (closer levels have more weight)
        weighted_bid = sum(
            vol * (1 / (i + 1)) 
            for i, (_, vol) in enumerate(bid_depth[:self.depth_levels])
        )
        weighted_ask = sum(
            vol * (1 / (i + 1)) 
            for i, (_, vol) in enumerate(ask_depth[:self.depth_levels])
        )
        
        weighted_total = weighted_bid + weighted_ask
        if weighted_total > 0:
            weighted_imbalance = (weighted_bid - weighted_ask) / weighted_total
        else:
            weighted_imbalance = 0.0
        
        return {
            'imbalance_ratio': imbalance_ratio,
            'weighted_imbalance': weighted_imbalance,
            'bid_volume': total_bid_volume,
            'ask_volume': total_ask_volume,
            'sentiment': 'BULLISH' if imbalance_ratio > 0.2 else 'BEARISH' if imbalance_ratio < -0.2 else 'NEUTRAL'
        }


class AdvancedLiquidityIndicators:
    """Unified interface for advanced liquidity indicators."""
    
    def __init__(self):
        self.iceberg_detector = IcebergDetector()
        self.absorption_ratio = AbsorptionExhaustionRatio()
        self.cvd_multi_tf = CVDMultiTimeframe()
        self.tib_analyzer = TickImbalanceBar()
        self.volume_heatmap = VolumeDeltaHeatmap()
        self.orderbook_analyzer = OrderBookImbalance()
        
        logger.info("✅ Advanced Liquidity Indicators initialized")
    
    def analyze_liquidity(self, df: pd.DataFrame) -> Dict[str, any]:
        """Comprehensive liquidity analysis."""
        results = {}
        
        try:
            # Iceberg detection
            icebergs = self.iceberg_detector.detect(df)
            results['icebergs_detected'] = len(icebergs)
            results['latest_iceberg'] = icebergs[-1] if icebergs else None
            
            # Absorption ratio
            absorption = self.absorption_ratio.calculate(df)
            results['absorption_ratio'] = absorption.iloc[-1] if len(absorption) > 0 else 1.0
            results['absorption_signal'] = 'SUPPORT' if results['absorption_ratio'] > 1.2 else 'RESISTANCE' if results['absorption_ratio'] < 0.8 else 'NEUTRAL'
            
            # CVD multi-timeframe
            cvd_dict = self.cvd_multi_tf.calculate_multi_tf(df)
            results['cvd_alignment'] = self.cvd_multi_tf.get_alignment_score(cvd_dict)
            results['cvd_values'] = {tf: cvd.iloc[-1] for tf, cvd in cvd_dict.items()}
            
            # Volume heatmap
            heatmap = self.volume_heatmap.create_heatmap(df)
            high_activity = self.volume_heatmap.get_high_activity_zones(heatmap)
            results['high_activity_zones'] = high_activity
            
            logger.info("✅ Liquidity analysis complete")
            
        except Exception as e:
            logger.error(f"❌ Error in liquidity analysis: {e}")
        
        return results


# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=500, freq='1min')
    np.random.seed(42)
    
    df = pd.DataFrame({
        'open': np.random.randn(500).cumsum() + 100,
        'high': np.random.randn(500).cumsum() + 102,
        'low': np.random.randn(500).cumsum() + 98,
        'close': np.random.randn(500).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 500)
    }, index=dates)
    
    # Initialize indicators
    liquidity = AdvancedLiquidityIndicators()
    
    # Analyze
    results = liquidity.analyze_liquidity(df)
    
    logger.info("\n=== Advanced Liquidity Analysis ===")
    logger.info(f"Icebergs Detected: {results['icebergs_detected']}")
    logger.info(f"Absorption Ratio: {results['absorption_ratio']:.2f}")
    logger.info(f"Signal: {results['absorption_signal']}")
    logger.info(f"CVD Alignment: {results['cvd_alignment']:.2%}")
    logger.info(f"High Activity Zones: {len(results['high_activity_zones'])} levels")
