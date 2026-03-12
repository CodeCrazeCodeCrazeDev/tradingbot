"""
Tier 3: Market Structure & Liquidity Dynamics
Analyzes market geometry, support/resistance, and liquidity zones
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

from trading_bot.brain.tier_structure import TierBase, MarketStateVector, OrderFlowIntelligence, MarketGeometryModel
from trading_bot.advanced_features.liquidity_holography import (
    LiquidityHolographyEngine, LiquidityGravityWell, TemporalLiquidityAnalyzer
)
from trading_bot.indicators.advanced_statistical import (
    CointegrationAnalyzer, ZScoreReversionModel, KalmanFilterTrendline, 
    HiddenMarkovRegime
)

logger = logging.getLogger(__name__)


@dataclass
class MarketLevel:
    """Represents a key market level"""
    price: float
    type: str  # support, resistance, liquidity_pool, order_block
    strength: float  # 0.0 to 1.0
    confidence: float
    metadata: Dict[str, Any]


class MarketStructureAnalysis:
    """Analyzes market structure and key levels"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.levels: List[MarketLevel] = []
    
    def detect_support_resistance(self, df: pd.DataFrame) -> List[MarketLevel]:
        """Detect support and resistance levels"""
        levels = []
        window = 20
        
        for i in range(window, len(df)):
            window_data = df.iloc[i-window:i]
            
            # Local highs
            if df['high'].iloc[i-1] == window_data['high'].max():
                strength = self._calculate_level_strength(df, i, 'resistance')
                
                levels.append(MarketLevel(
                    price=df['high'].iloc[i-1],
                    type='resistance',
                    strength=strength,
                    confidence=min(strength * 1.2, 1.0),
                    metadata={'touches': 1}
                ))
            
            # Local lows
            if df['low'].iloc[i-1] == window_data['low'].min():
                strength = self._calculate_level_strength(df, i, 'support')
                
                levels.append(MarketLevel(
                    price=df['low'].iloc[i-1],
                    type='support',
                    strength=strength,
                    confidence=min(strength * 1.2, 1.0),
                    metadata={'touches': 1}
                ))
        
        # Merge nearby levels
        merged_levels = self._merge_nearby_levels(levels)
        self.levels = merged_levels
        
        return merged_levels
    
    def _calculate_level_strength(self, df: pd.DataFrame, idx: int, level_type: str) -> float:
        """Calculate the strength of a support/resistance level"""
        price = df['high'].iloc[idx-1] if level_type == 'resistance' else df['low'].iloc[idx-1]
        volume = df['volume'].iloc[idx-1]
        
        # Volume factor (0.0 to 1.0)
        volume_ma = df['volume'].rolling(20).mean().iloc[idx-1]
        volume_factor = min(volume / volume_ma, 2.0) / 2.0
        
        # Price rejection factor
        if level_type == 'resistance':
            rejection = (df['high'].iloc[idx-1] - df['close'].iloc[idx-1]) / (df['high'].iloc[idx-1] - df['low'].iloc[idx-1])
        else:
            rejection = (df['close'].iloc[idx-1] - df['low'].iloc[idx-1]) / (df['high'].iloc[idx-1] - df['low'].iloc[idx-1])
        
        # Combine factors
        strength = (volume_factor * 0.6) + (rejection * 0.4)
        return min(strength, 1.0)
    
    def _merge_nearby_levels(self, levels: List[MarketLevel], 
                           threshold: float = 0.001) -> List[MarketLevel]:
        """Merge levels that are very close to each other"""
        if not levels:
            return []
        
        # Sort levels by price
        sorted_levels = sorted(levels, key=lambda x: x.price)
        merged = []
        
        current = sorted_levels[0]
        
        for next_level in sorted_levels[1:]:
            # If levels are close enough
            if abs(next_level.price - current.price) / current.price < threshold:
                # Merge into stronger level
                if next_level.strength > current.strength:
                    current = next_level
            else:
                merged.append(current)
                current = next_level
        
        merged.append(current)
        return merged
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Complete market structure analysis"""
        # Detect key levels
        levels = self.detect_support_resistance(df)
        
        # Current price
        current_price = df['close'].iloc[-1]
        
        # Find nearest levels
        nearest_support = None
        nearest_resistance = None
        
        for level in sorted(levels, key=lambda x: x.price):
            if level.price < current_price:
                if nearest_support is None or level.price > nearest_support.price:
                    nearest_support = level
            else:
                if nearest_resistance is None or level.price < nearest_resistance.price:
                    nearest_resistance = level
        
        # Calculate market structure state
        structure_state = self._determine_structure_state(df)
        
        return {
            'levels': levels,
            'nearest_support': nearest_support,
            'nearest_resistance': nearest_resistance,
            'structure_state': structure_state,
            'current_phase': structure_state['phase'],
            'trend_structure': structure_state['trend']
        }
    
    def _determine_structure_state(self, df: pd.DataFrame) -> Dict[str, str]:
        """Determine the current market structure state"""
        # Calculate swing highs and lows
        highs = df['high'].rolling(5).max()
        lows = df['low'].rolling(5).min()
        
        # Determine trend structure
        higher_highs = highs.diff() > 0
        higher_lows = lows.diff() > 0
        
        if higher_highs.iloc[-3:].all() and higher_lows.iloc[-3:].all():
            trend = 'uptrend'
        elif (not higher_highs.iloc[-3:].any()) and (not higher_lows.iloc[-3:].any()):
            trend = 'downtrend'
        else:
            trend = 'ranging'
        
        # Determine market phase
        if trend == 'uptrend':
            if df['volume'].iloc[-5:].mean() > df['volume'].rolling(20).mean().iloc[-1]:
                phase = 'accumulation'
            else:
                phase = 'markup'
        elif trend == 'downtrend':
            if df['volume'].iloc[-5:].mean() > df['volume'].rolling(20).mean().iloc[-1]:
                phase = 'distribution'
            else:
                phase = 'markdown'
        else:
            phase = 'consolidation'
        
        return {
            'trend': trend,
            'phase': phase
        }


class LiquidityAnalysis:
    """Advanced liquidity analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.holography = LiquidityHolographyEngine()
        self.gravity_wells = LiquidityGravityWell()
        self.temporal_analyzer = TemporalLiquidityAnalyzer()
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze liquidity landscape"""
        # Create 3D liquidity map
        liquidity_map = self.holography.create_map(df)
        
        # Detect gravity wells
        wells = self.gravity_wells.detect(df)
        
        # Find absorption zones
        zones = self.absorption_zones.find_zones(df)
        
        # Current price
        current_price = df['close'].iloc[-1]
        
        # Find nearest liquidity zones
        nearest_well = None
        nearest_zone = None
        min_well_dist = float('inf')
        min_zone_dist = float('inf')
        
        for well in wells:
            dist = abs(well['price'] - current_price)
            if dist < min_well_dist:
                min_well_dist = dist
                nearest_well = well
        
        for zone in zones:
            dist = abs(zone['center'] - current_price)
            if dist < min_zone_dist:
                min_zone_dist = dist
                nearest_zone = zone
        
        # Calculate liquidity score (-1 to 1)
        # Positive means price is approaching liquidity
        # Negative means price is leaving liquidity
        if nearest_well and nearest_zone:
            well_direction = np.sign(nearest_well['price'] - current_price)
            zone_direction = np.sign(nearest_zone['center'] - current_price)
            
            liquidity_score = (
                0.6 * well_direction * (1 - min_well_dist/current_price) +
                0.4 * zone_direction * (1 - min_zone_dist/current_price)
            )
        else:
            liquidity_score = 0.0
        
        return {
            'liquidity_map': liquidity_map,
            'gravity_wells': wells,
            'absorption_zones': zones,
            'nearest_well': nearest_well,
            'nearest_zone': nearest_zone,
            'liquidity_score': liquidity_score
        }


class StatisticalAnalysis:
    """Statistical market analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.cointegration = CointegrationAnalyzer()
        self.zscore = ZScoreReversionModel()
        self.kalman = KalmanFilterTrendline()
        self.hmm = HiddenMarkovRegime()
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze statistical indicators"""
        close = df['close']
        
        # Calculate z-score
        zscore = self.zscore.calculate_zscore(close)
        
        # Kalman filter trend
        kalman_trend = self.kalman.filter(close)
        
        # HMM regime detection
        self.hmm.fit(close.pct_change().dropna())
        regime = self.hmm.predict_regime(close.pct_change().dropna())
        
        # Mean reversion probability
        mean_rev_prob = 1.0 - abs(zscore.iloc[-1]) / 4.0  # Scale to 0-1
        mean_rev_prob = max(min(mean_rev_prob, 1.0), 0.0)
        
        # Market efficiency (from Hurst exponent)
        # efficiency = 1.0 - abs(hurst - 0.5) * 2
        
        return {
            'zscore': zscore.iloc[-1],
            'zscore_signal': 'oversold' if zscore.iloc[-1] < -2 else 'overbought' if zscore.iloc[-1] > 2 else 'neutral',
            'kalman_trend': kalman_trend['filtered'].iloc[-1],
            'regime': regime['predicted_regime'].iloc[-1],
            'regime_confidence': regime['confidence'].iloc[-1],
            'mean_reversion_probability': mean_rev_prob,
            'market_efficiency': 0.5  # Placeholder
        }


class Tier3MarketStructure(TierBase):
    """
    Tier 3: Market Structure & Liquidity Dynamics
    
    Analyzes market geometry and liquidity landscape:
    - Support/Resistance levels
    - Liquidity pools and order blocks
    - Market structure analysis
    - Statistical edge detection
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Tier 3: Market Structure", config)
        self.structure_analysis = None
        self.liquidity_analysis = None
        self.statistical_analysis = None
    
    def _initialize_components(self) -> None:
        """Initialize tier-specific components"""
        self.structure_analysis = MarketStructureAnalysis(self.config.get('structure', {}))
        self.liquidity_analysis = LiquidityAnalysis(self.config.get('liquidity', {}))
        self.statistical_analysis = StatisticalAnalysis(self.config.get('statistical', {}))
    
    def process(self, market_data: pd.DataFrame, 
               previous_tier_output: Optional[OrderFlowIntelligence] = None,
               additional_inputs: Optional[Dict[str, Any]] = None) -> MarketGeometryModel:
        """
        Process market data and generate market structure analysis
        
        Args:
            market_data: DataFrame with OHLCV data
            previous_tier_output: Output from Tier 2 (OrderFlowIntelligence)
            additional_inputs: Additional inputs (not used in Tier 3)
            
        Returns:
            MarketGeometryModel with market structure analysis
        """
        if not self.validate_input(market_data):
            logger.error("Invalid input data for Tier 3")
            return None
        try:
        
            # Analyze market structure
            structure_results = self.structure_analysis.analyze(market_data)
            
            # Analyze liquidity
            liquidity_results = self.liquidity_analysis.analyze(market_data)
            
            # Analyze statistical indicators
            stat_results = self.statistical_analysis.analyze(market_data)
            
            # Combine results
            key_levels = {
                level.price: {
                    'type': level.type,
                    'strength': level.strength,
                    'confidence': level.confidence
                } for level in structure_results['levels']
            }
            
            liquidity_zones = {
                'wells': liquidity_results['gravity_wells'],
                'absorption': liquidity_results['absorption_zones']
            }
            
            # Calculate market efficiency
            market_efficiency = stat_results['market_efficiency']
            
            # Calculate statistical edge
            mean_reversion_edge = stat_results['mean_reversion_probability']
            regime_edge = stat_results['regime_confidence']
            liquidity_edge = abs(liquidity_results['liquidity_score'])
            
            statistical_edge = (
                0.4 * mean_reversion_edge +
                0.3 * regime_edge +
                0.3 * liquidity_edge
            )
            
            # Calculate overall signal (-1 to 1)
            structure_signal = 1.0 if structure_results['structure_state']['trend'] == 'uptrend' else -1.0 if structure_results['structure_state']['trend'] == 'downtrend' else 0.0
            liquidity_signal = liquidity_results['liquidity_score']
            stat_signal = -np.sign(stat_results['zscore']) * min(abs(stat_results['zscore']) / 2, 1.0)
            
            signal_value = (
                0.4 * structure_signal +
                0.3 * liquidity_signal +
                0.3 * stat_signal
            )
            
            # Calculate confidence (0 to 1)
            structure_conf = 1.0 if abs(structure_signal) > 0.7 else abs(structure_signal)
            liquidity_conf = abs(liquidity_signal)
            stat_conf = stat_results['regime_confidence']
            
            confidence = (
                0.4 * structure_conf +
                0.3 * liquidity_conf +
                0.3 * stat_conf
            )
            
            # Create metadata
            metadata = {
                'structure': structure_results,
                'liquidity': liquidity_results,
                'statistical': stat_results
            }
            
            # Create market geometry model
            geometry = MarketGeometryModel(
                timestamp=market_data.index[-1],
                signal_value=signal_value,
                confidence=confidence,
                key_levels=key_levels,
                liquidity_zones=liquidity_zones,
                mean_reversion_probability=stat_results['mean_reversion_probability'],
                statistical_edge=statistical_edge,
                market_efficiency=market_efficiency,
                metadata=metadata
            )
            
            self.last_output = geometry
            return geometry
            
        except Exception as e:
            logger.error(f"Error processing Tier 3: {str(e)}")
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
    
    # Initialize and process
    tier3 = Tier3MarketStructure()
    tier3.initialize()
    result = tier3.process(df)
    
    # Print results
    logger.info("\n=== Tier 3: Market Structure Results ===")
    logger.info(f"Signal: {result.signal_value:.4f}")
    logger.info(f"Confidence: {result.confidence:.2%}")
    logger.info(f"Statistical Edge: {result.statistical_edge:.2%}")
    logger.info(f"Market Efficiency: {result.market_efficiency:.2%}")
    logger.info(f"Mean Reversion Probability: {result.mean_reversion_probability:.2%}")
    logger.info("\nKey Levels:")
    for price, info in result.key_levels.items():
        logger.info(f"- {info['type'].title()}: {price:.2f} (strength: {info['strength']:.2f})")
