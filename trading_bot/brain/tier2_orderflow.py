"""
Tier 2: Volume & Order Flow Intelligence
Analyzes volume patterns and order flow to detect institutional activity
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
import logging

from trading_bot.brain.tier_structure import TierBase, MarketStateVector, OrderFlowIntelligence
from trading_bot.indicators.advanced_liquidity import (
    IcebergDetector, AbsorptionExhaustionRatio, 
    CVDMultiTimeframe, TickImbalanceBar, VolumeDeltaHeatmap
)

logger = logging.getLogger(__name__)


class BasicVolumeAnalysis:
    """Basic volume analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def calculate_obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate On-Balance Volume"""
        close_change = close.diff()
        obv = pd.Series(index=close.index, dtype=float)
        obv.iloc[0] = 0
        
        for i in range(1, len(close)):
            if close_change.iloc[i] > 0:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close_change.iloc[i] < 0:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    def calculate_volume_profile(self, df: pd.DataFrame, 
                               num_bins: int = 20) -> Dict[str, Any]:
        """Calculate Volume Profile"""
        # Determine price range
        price_min = df['low'].min()
        price_max = df['high'].max()
        
        # Create price bins
        bin_edges = np.linspace(price_min, price_max, num_bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # Initialize volume profile
        volume_profile = np.zeros(num_bins)
        
        # Distribute volume across price levels
        for i in range(len(df)):
            row = df.iloc[i]
            # Find bins that this candle touches
            bin_indices = np.where(
                (bin_edges[:-1] <= row['high']) & (bin_edges[1:] >= row['low'])
            )[0]
            
            # Distribute volume proportionally
            if len(bin_indices) > 0:
                volume_per_bin = row['volume'] / len(bin_indices)
                for idx in bin_indices:
                    volume_profile[idx] += volume_per_bin
        
        # Find point of control (price level with highest volume)
        poc_index = np.argmax(volume_profile)
        poc_price = bin_centers[poc_index]
        
        # Find value area (70% of volume)
        total_volume = volume_profile.sum()
        value_area_target = total_volume * 0.7
        
        # Start from POC and expand outward
        value_area_indices = [poc_index]
        current_volume = volume_profile[poc_index]
        
        left_idx = poc_index - 1
        right_idx = poc_index + 1
        
        while current_volume < value_area_target and (left_idx >= 0 or right_idx < num_bins):
            left_vol = volume_profile[left_idx] if left_idx >= 0 else 0
            right_vol = volume_profile[right_idx] if right_idx < num_bins else 0
            
            if left_vol > right_vol and left_idx >= 0:
                value_area_indices.append(left_idx)
                current_volume += left_vol
                left_idx -= 1
            elif right_idx < num_bins:
                value_area_indices.append(right_idx)
                current_volume += right_vol
                right_idx += 1
            
        # Get value area high and low
        vah = bin_edges[max(value_area_indices) + 1]
        val = bin_edges[min(value_area_indices)]
        
        return {
            'profile': list(zip(bin_centers, volume_profile)),
            'poc': poc_price,
            'vah': vah,
            'val': val,
            'value_area_pct': current_volume / total_volume
        }
    
    def detect_volume_climax(self, volume: pd.Series, 
                           lookback: int = 20, threshold: float = 2.0) -> Dict[str, Any]:
        """Detect Volume Climax events"""
        # Calculate average volume
        avg_volume = volume.rolling(window=lookback).mean()
        
        # Detect climax events (volume > threshold * average)
        climax_mask = volume > (avg_volume * threshold)
        climax_indices = np.where(climax_mask)[0]
        
        # Get the most recent climax event
        if len(climax_indices) > 0:
            latest_climax_idx = climax_indices[-1]
            latest_climax_volume = volume.iloc[latest_climax_idx]
            latest_climax_ratio = latest_climax_volume / avg_volume.iloc[latest_climax_idx]
            latest_climax_bars_ago = len(volume) - 1 - latest_climax_idx
            
            return {
                'detected': True,
                'latest_idx': latest_climax_idx,
                'latest_volume': latest_climax_volume,
                'latest_ratio': latest_climax_ratio,
                'bars_ago': latest_climax_bars_ago,
                'is_recent': latest_climax_bars_ago <= 5
            }
        else:
            return {
                'detected': False
            }
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze basic volume indicators"""
        close = df['close']
        volume = df['volume']
        
        # Calculate OBV
        obv = self.calculate_obv(close, volume)
        
        # Calculate Volume Profile
        volume_profile = self.calculate_volume_profile(df)
        
        # Detect Volume Climax
        volume_climax = self.detect_volume_climax(volume)
        
        # Calculate OBV trend
        obv_trend = obv.diff(5).iloc[-1]
        obv_signal = np.sign(obv_trend) * min(abs(obv_trend) / 100000, 1.0)
        
        # Calculate volume trend
        vol_sma = volume.rolling(window=20).mean()
        vol_trend = (volume.iloc[-1] / vol_sma.iloc[-1]) - 1
        vol_signal = np.sign(vol_trend) * min(abs(vol_trend), 1.0)
        
        # Current price relative to volume profile
        current_price = close.iloc[-1]
        price_vs_poc = (current_price - volume_profile['poc']) / volume_profile['poc']
        
        # Volume climax signal
        climax_signal = 0.0
        if volume_climax['detected'] and volume_climax['is_recent']:
            # Strong signal if recent climax
            climax_signal = np.sign(close.iloc[-1] - close.iloc[volume_climax['latest_idx']])
        
        # Combined signal
        basic_vol_signal = (
            0.4 * obv_signal +
            0.3 * vol_signal +
            0.3 * climax_signal
        )
        
        return {
            'basic_vol_signal': basic_vol_signal,
            'obv_trend': obv_trend,
            'volume_trend': vol_trend,
            'price_vs_poc': price_vs_poc,
            'volume_climax': volume_climax['detected'],
            'indicators': {
                'obv': obv.iloc[-1],
                'obv_change': obv_trend,
                'poc': volume_profile['poc'],
                'vah': volume_profile['vah'],
                'val': volume_profile['val'],
                'volume_sma': vol_sma.iloc[-1],
                'volume_ratio': volume.iloc[-1] / vol_sma.iloc[-1]
            }
        }


class AdvancedVolumeAnalysis:
    """Advanced volume analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.volume_delta_heatmap = VolumeDeltaHeatmap(
            price_bins=self.config.get('heatmap_bins', 50)
        )
        self.cvd_multi_tf = CVDMultiTimeframe(
            timeframes=self.config.get('cvd_timeframes', ['5T', '15T', '1H', '4H'])
        )
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze advanced volume indicators"""
        # Create Volume Delta Heatmap
        heatmap = self.volume_delta_heatmap.create_heatmap(df)
        high_activity_zones = self.volume_delta_heatmap.get_high_activity_zones(heatmap)
        
        # Calculate CVD across multiple timeframes
        cvd_dict = self.cvd_multi_tf.calculate_multi_tf(df)
        cvd_alignment = self.cvd_multi_tf.get_alignment_score(cvd_dict)
        
        # Get CVD trends
        cvd_trends = {}
        for tf, cvd in cvd_dict.items():
            if len(cvd) > 1:
                cvd_trends[tf] = cvd.iloc[-1] - cvd.iloc[-2]
        
        # Determine if price is near high activity zone
        current_price = df['close'].iloc[-1]
        near_high_activity = any(abs(current_price - zone) / current_price < 0.01 
                               for zone in high_activity_zones)
        
        # Calculate combined signal
        # Positive when CVD is rising across timeframes
        adv_vol_signal = (cvd_alignment * 2 - 1)  # Convert 0-1 to -1 to 1
        
        return {
            'adv_vol_signal': adv_vol_signal,
            'cvd_alignment': cvd_alignment,
            'near_high_activity': near_high_activity,
            'high_activity_zones': high_activity_zones,
            'indicators': {
                'cvd_values': {tf: cvd.iloc[-1] for tf, cvd in cvd_dict.items()},
                'cvd_trends': cvd_trends,
                'high_activity_count': len(high_activity_zones)
            }
        }


class PressureAnalysis:
    """Order flow pressure analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.absorption_ratio = AbsorptionExhaustionRatio(
            lookback=self.config.get('absorption_lookback', 20)
        )
        self.tick_imbalance = TickImbalanceBar(
            imbalance_threshold=self.config.get('tib_threshold', 1000)
        )
    
    def analyze(self, df: pd.DataFrame, tick_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Analyze order flow pressure indicators"""
        # Calculate Absorption vs Exhaustion Ratio
        absorption = self.absorption_ratio.calculate(df)
        
        # Process Tick Imbalance Bars if tick data is available
        tib_data = None
        if tick_data is not None:
            tib_data = self.tick_imbalance.create_bars(tick_data)
        
        # Get latest absorption ratio
        latest_absorption = absorption.iloc[-1] if len(absorption) > 0 else 1.0
        
        # Determine pressure signal
        if latest_absorption > 1.2:
            pressure_signal = 1.0  # Strong absorption (bullish)
        elif latest_absorption < 0.8:
            pressure_signal = -1.0  # Strong exhaustion (bearish)
        else:
            pressure_signal = 0.0  # Neutral
        
        # Add TIB signal if available
        if tib_data is not None and not tib_data.empty:
            latest_tib = tib_data.iloc[-1]
            tib_signal = np.sign(latest_tib.get('imbalance', 0))
            
            # Combine signals
            pressure_signal = 0.7 * pressure_signal + 0.3 * tib_signal
        
        return {
            'pressure_signal': pressure_signal,
            'absorption_ratio': latest_absorption,
            'absorption_signal': 'SUPPORT' if latest_absorption > 1.2 else 'RESISTANCE' if latest_absorption < 0.8 else 'NEUTRAL',
            'indicators': {
                'absorption_ratio': latest_absorption,
                'tib_available': tib_data is not None and not tib_data.empty
            }
        }


class InstitutionalDetection:
    """Institutional order detection"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.iceberg_detector = IcebergDetector(
            volume_threshold=self.config.get('iceberg_volume_threshold', 2.0),
            price_tolerance=self.config.get('iceberg_price_tolerance', 0.0001)
        )
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze institutional activity"""
        # Detect iceberg orders
        icebergs = self.iceberg_detector.detect(df)
        
        # Process results
        iceberg_detected = len(icebergs) > 0
        recent_iceberg = None
        iceberg_signal = 0.0
        
        if iceberg_detected:
            # Get most recent iceberg
            recent_iceberg = icebergs[-1]
            
            # Generate signal based on side and recency
            bars_ago = (df.index[-1] - recent_iceberg.timestamp).total_seconds() / 60
            recency_factor = max(0, 1 - (bars_ago / 100))  # Decay factor
            
            if recent_iceberg.side == 'buy':
                iceberg_signal = recency_factor * recent_iceberg.detection_confidence
            else:
                iceberg_signal = -recency_factor * recent_iceberg.detection_confidence
        
        return {
            'iceberg_detected': iceberg_detected,
            'iceberg_signal': iceberg_signal,
            'recent_iceberg': recent_iceberg,
            'institutional_activity': iceberg_detected,
            'indicators': {
                'iceberg_count': len(icebergs),
                'iceberg_side': recent_iceberg.side if recent_iceberg else None,
                'iceberg_confidence': recent_iceberg.detection_confidence if recent_iceberg else 0.0,
                'iceberg_price': recent_iceberg.price if recent_iceberg else None
            }
        }


class Tier2OrderFlowIntelligence(TierBase):
    """
    Tier 2: Volume & Order Flow Intelligence
    
    Analyzes volume patterns and order flow to detect institutional activity:
    - Basic Volume Analysis (OBV, Volume Profile, Volume Climax)
    - Advanced Volume Analysis (Volume Delta Heatmap, CVD Multi-Timeframe)
    - Pressure Analysis (Absorption vs Exhaustion, Tick Imbalance Bars)
    - Institutional Detection (Iceberg Orders)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Tier 2: Order Flow Intelligence", config)
        self.basic_volume = None
        self.advanced_volume = None
        self.pressure_analysis = None
        self.institutional_detection = None
    
    def _initialize_components(self) -> None:
        """Initialize tier-specific components"""
        self.basic_volume = BasicVolumeAnalysis(self.config.get('basic_volume', {}))
        self.advanced_volume = AdvancedVolumeAnalysis(self.config.get('advanced_volume', {}))
        self.pressure_analysis = PressureAnalysis(self.config.get('pressure', {}))
        self.institutional_detection = InstitutionalDetection(self.config.get('institutional', {}))
    
    def get_required_columns(self) -> List[str]:
        """Get required columns for this tier"""
        return ['open', 'high', 'low', 'close', 'volume']
    
    def process(self, market_data: pd.DataFrame, 
               previous_tier_output: Optional[MarketStateVector] = None,
               additional_inputs: Optional[Dict[str, Any]] = None) -> OrderFlowIntelligence:
        """
        Process market data and generate order flow intelligence
        
        Args:
            market_data: DataFrame with OHLCV data
            previous_tier_output: Output from Tier 1 (MarketStateVector)
            additional_inputs: Additional inputs like tick data
            
        Returns:
            OrderFlowIntelligence with order flow analysis results
        """
        if not self.validate_input(market_data):
            logger.error("Invalid input data for Tier 2")
            return None
        try:
        
            # Get tick data if available
            tick_data = additional_inputs.get('tick_data') if additional_inputs else None
            
            # Analyze basic volume indicators
            basic_vol_results = self.basic_volume.analyze(market_data)
            
            # Analyze advanced volume indicators
            adv_vol_results = self.advanced_volume.analyze(market_data)
            
            # Analyze pressure indicators
            pressure_results = self.pressure_analysis.analyze(market_data, tick_data)
            
            # Analyze institutional activity
            inst_results = self.institutional_detection.analyze(market_data)
            
            # Combine results
            basic_vol_signal = basic_vol_results['basic_vol_signal']
            adv_vol_signal = adv_vol_results['adv_vol_signal']
            pressure_signal = pressure_results['pressure_signal']
            iceberg_signal = inst_results['iceberg_signal']
            
            # Calculate buying and selling pressure
            buying_pressure = max(0, basic_vol_signal) + max(0, adv_vol_signal) + max(0, pressure_signal) + max(0, iceberg_signal)
            selling_pressure = abs(min(0, basic_vol_signal)) + abs(min(0, adv_vol_signal)) + abs(min(0, pressure_signal)) + abs(min(0, iceberg_signal))
            
            # Normalize pressures to 0-1 range
            max_pressure = max(buying_pressure, selling_pressure, 0.001)  # Avoid division by zero
            buying_pressure /= max_pressure
            selling_pressure /= max_pressure
            
            # Calculate volume imbalance (-1 to 1)
            volume_imbalance = buying_pressure - selling_pressure
            
            # Calculate institutional activity score (0 to 1)
            institutional_activity = inst_results['iceberg_detected'] * inst_results.get('iceberg_confidence', 0.5)
            
            # Calculate absorption score (0 to 1)
            absorption_score = max(0, min(pressure_results['absorption_ratio'] / 2, 1.0))
            
            # Calculate overall signal (-1 to 1)
            signal_value = (
                0.3 * basic_vol_signal +
                0.3 * adv_vol_signal +
                0.2 * pressure_signal +
                0.2 * iceberg_signal
            )
            
            # Calculate confidence (0 to 1)
            # Higher confidence when signals align
            signal_components = [
                basic_vol_signal,
                adv_vol_signal,
                pressure_signal,
                iceberg_signal
            ]
            
            # Count how many components agree with the overall signal
            agreement = sum(1 for s in signal_components if abs(s) > 0.2 and np.sign(s) == np.sign(signal_value))
            confidence = agreement / len(signal_components)
            
            # Boost confidence if CVD alignment is strong
            if adv_vol_results['cvd_alignment'] > 0.8:
                confidence = min(confidence * 1.2, 1.0)
            
            # Create metadata
            metadata = {
                'basic_volume': basic_vol_results['indicators'],
                'advanced_volume': adv_vol_results['indicators'],
                'pressure': pressure_results['indicators'],
                'institutional': inst_results['indicators'],
                'high_activity_zones': adv_vol_results['high_activity_zones']
            }
            
            # Create order flow intelligence output
            order_flow = OrderFlowIntelligence(
                timestamp=market_data.index[-1],
                signal_value=signal_value,
                confidence=confidence,
                buying_pressure=buying_pressure,
                selling_pressure=selling_pressure,
                institutional_activity=institutional_activity,
                volume_imbalance=volume_imbalance,
                absorption_score=absorption_score,
                iceberg_detected=inst_results['iceberg_detected'],
                metadata=metadata
            )
            
            self.last_output = order_flow
            return order_flow
            
        except Exception as e:
            logger.error(f"Error processing Tier 2: {str(e)}")
            return None


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=250, freq='1H')
    np.random.seed(42)
    
    df = pd.DataFrame({
        'open': np.random.randn(250).cumsum() + 100,
        'high': np.random.randn(250).cumsum() + 102,
        'low': np.random.randn(250).cumsum() + 98,
        'close': np.random.randn(250).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 250)
    }, index=dates)
    
    # Create sample tick data
    tick_data = pd.DataFrame({
        'price': np.random.randn(1000).cumsum() + 100,
        'volume': np.random.randint(1, 100, 1000),
        'side': np.random.choice([1, -1], 1000)
    }, index=pd.date_range('2024-01-01', periods=1000, freq='1min'))
    
    # Initialize and process
    tier2 = Tier2OrderFlowIntelligence()
    tier2.initialize()
    result = tier2.process(df, additional_inputs={'tick_data': tick_data})
    
    # Print results
    logger.info("\n=== Tier 2: Order Flow Intelligence Results ===")
    logger.info(f"Signal: {result.signal_value:.4f}")
    logger.info(f"Confidence: {result.confidence:.2%}")
    logger.info(f"Buying Pressure: {result.buying_pressure:.2f}")
    logger.info(f"Selling Pressure: {result.selling_pressure:.2f}")
    logger.info(f"Volume Imbalance: {result.volume_imbalance:.2f}")
    logger.info(f"Institutional Activity: {result.institutional_activity:.2f}")
    logger.info(f"Absorption Score: {result.absorption_score:.2f}")
    logger.info(f"Iceberg Detected: {result.iceberg_detected}")
