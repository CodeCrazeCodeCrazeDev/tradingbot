"""
Tier 4: Regime & Context Detection
Identifies market regime and adapts strategy accordingly
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

from trading_bot.brain.tier_structure import (
    TierBase, MarketStateVector, OrderFlowIntelligence, 
    MarketGeometryModel, RegimeContextVector
)

from trading_bot.indicators.advanced_ml import (
    RegimeAwareRL, ExplainableAI, TransformerPredictor
)

logger = logging.getLogger(__name__)


@dataclass
class MarketRegime:
    """Market regime classification"""
    name: str  # trending, ranging, volatile, etc.
    probability: float
    duration: int  # bars in this regime
    characteristics: Dict[str, float]
    optimal_strategy: str


class VolatilityRegimeClassifier:
    """Classifies volatility regimes"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.lookback = self.config.get('lookback', 20)
    
    def classify(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Classify volatility regime"""
        # Calculate volatility metrics
        returns = df['close'].pct_change()
        rolling_vol = returns.rolling(self.lookback).std() * np.sqrt(252)
        
        # Get latest volatility
        current_vol = rolling_vol.iloc[-1]
        
        # Calculate historical percentiles
        vol_percentile = pd.Series(rolling_vol).rank(pct=True).iloc[-1]
        
        # Classify regime
        if current_vol > rolling_vol.quantile(0.8):
            regime = 'high'
            probability = min((current_vol - rolling_vol.mean()) / rolling_vol.std(), 1.0)
        elif current_vol < rolling_vol.quantile(0.2):
            regime = 'low'
            probability = min((rolling_vol.mean() - current_vol) / rolling_vol.std(), 1.0)
        else:
            regime = 'normal'
            probability = 1.0 - abs(current_vol - rolling_vol.mean()) / rolling_vol.std()
        
        # Calculate duration
        duration = 0
        for i in range(len(rolling_vol)-1, -1, -1):
            if self._get_regime(rolling_vol.iloc[i], rolling_vol) == regime:
                duration += 1
            else:
                break
        
        return {
            'regime': regime,
            'probability': probability,
            'volatility': current_vol,
            'percentile': vol_percentile,
            'duration': duration,
            'characteristics': {
                'volatility': current_vol,
                'range_expansion': self._calculate_range_expansion(df),
                'gap_frequency': self._calculate_gap_frequency(df)
            }
        }
    
    def _get_regime(self, vol: float, rolling_vol: pd.Series) -> str:
        """Get regime for a single volatility value"""
        if vol > rolling_vol.quantile(0.8):
            return 'high'
        elif vol < rolling_vol.quantile(0.2):
            return 'low'
        return 'normal'
    
    def _calculate_range_expansion(self, df: pd.DataFrame) -> float:
        """Calculate recent range expansion"""
        ranges = df['high'] - df['low']
        recent_range = ranges.iloc[-5:].mean()
        historical_range = ranges.iloc[-20:-5].mean()
        
        return (recent_range / historical_range) - 1
    
    def _calculate_gap_frequency(self, df: pd.DataFrame) -> float:
        """Calculate frequency of gaps in recent bars"""
        gaps = abs(df['open'] - df['close'].shift(1))
        avg_gap = gaps.iloc[-5:].mean()
        atr = self._calculate_atr(df).iloc[-1]
        
        return avg_gap / atr if atr > 0 else 0
    
    def _calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range"""
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift())
        tr3 = abs(df['low'] - df['close'].shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        return tr.rolling(window=14).mean()


class MarketPhaseClassifier:
    """Classifies market phases"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def classify(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Classify market phase"""
        # Calculate indicators
        volume_sma = df['volume'].rolling(20).mean()
        price_sma = df['close'].rolling(20).mean()
        
        # Get trends
        volume_trend = df['volume'].iloc[-5:].mean() / volume_sma.iloc[-1] - 1
        price_trend = df['close'].iloc[-5:].mean() / price_sma.iloc[-1] - 1
        
        # Classify phase
        if price_trend > 0:
            if volume_trend > 0:
                phase = 'accumulation'
                characteristics = {
                    'volume_expansion': volume_trend,
                    'price_strength': price_trend,
                    'buying_pressure': 1.0
                }
            else:
                phase = 'markup'
                characteristics = {
                    'volume_contraction': -volume_trend,
                    'price_strength': price_trend,
                    'buying_pressure': 0.7
                }
        else:
            if volume_trend > 0:
                phase = 'distribution'
                characteristics = {
                    'volume_expansion': volume_trend,
                    'price_weakness': -price_trend,
                    'selling_pressure': 1.0
                }
            else:
                phase = 'markdown'
                characteristics = {
                    'volume_contraction': -volume_trend,
                    'price_weakness': -price_trend,
                    'selling_pressure': 0.7
                }
        
        # Calculate probability
        probability = min(abs(price_trend * 5), 1.0) * min(abs(volume_trend * 5), 1.0)
        
        # Calculate duration
        duration = self._calculate_phase_duration(df, phase)
        
        return {
            'phase': phase,
            'probability': probability,
            'duration': duration,
            'characteristics': characteristics
        }
    
    def _calculate_phase_duration(self, df: pd.DataFrame, current_phase: str) -> int:
        """Calculate how long the current phase has lasted"""
        duration = 0
        volume_sma = df['volume'].rolling(20).mean()
        price_sma = df['close'].rolling(20).mean()
        
        for i in range(len(df)-1, -1, -1):
            volume_trend = df['volume'].iloc[i] / volume_sma.iloc[i] - 1
            price_trend = df['close'].iloc[i] / price_sma.iloc[i] - 1
            
            phase = self._get_phase(price_trend, volume_trend)
            if phase == current_phase:
                duration += 1
            else:
                break
        
        return duration
    
    def _get_phase(self, price_trend: float, volume_trend: float) -> str:
        """Get phase for a single point"""
        if price_trend > 0:
            return 'accumulation' if volume_trend > 0 else 'markup'
        else:
            return 'distribution' if volume_trend > 0 else 'markdown'


class AIRegimeAnalysis:
    """AI-based regime analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.rarl = RegimeAwareRL()
        self.xai = ExplainableAI()
        self.transformer = TransformerPredictor()
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze market regime using AI models"""
        # Get regime from RARL
        regime = self.rarl.detect_regime(df)
        policy = self.rarl.get_optimal_policy(regime)
        
        # Get predictions from transformer
        prediction = self.transformer.predict(df)
        
        # Calculate SHAP values
        features = self._extract_features(df)
        shap_values = self.xai.calculate_shap_values(features, prediction)
        
        return {
            'regime': regime,
            'optimal_policy': policy,
            'prediction': prediction,
            'shap_values': shap_values,
            'confidence': prediction['confidence'],
            'uncertainty': 1.0 - prediction['confidence']
        }
    
    def _extract_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Extract features for SHAP analysis"""
        return {
            'trend': df['close'].iloc[-1] / df['close'].iloc[-20] - 1,
            'volatility': df['close'].pct_change().std() * np.sqrt(252),
            'volume': df['volume'].iloc[-1] / df['volume'].rolling(20).mean().iloc[-1],
            'range': (df['high'].iloc[-1] - df['low'].iloc[-1]) / df['close'].iloc[-1]
        }


class Tier4RegimeDetection(TierBase):
    """
    Tier 4: Regime & Context Detection
    
    Identifies market regime and adapts strategy:
    - Volatility regime classification
    - Market phase detection
    - Regime-aware reinforcement learning
    - Explainable AI metrics
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Tier 4: Regime Detection", config)
        self.volatility_classifier = None
        self.phase_classifier = None
        self.ai_analysis = None
    
    def _initialize_components(self) -> None:
        """Initialize tier-specific components"""
        self.volatility_classifier = VolatilityRegimeClassifier(self.config.get('volatility', {}))
        self.phase_classifier = MarketPhaseClassifier(self.config.get('phase', {}))
        self.ai_analysis = AIRegimeAnalysis(self.config.get('ai', {}))
    
    def process(self, market_data: pd.DataFrame, 
               previous_tier_output: Optional[MarketGeometryModel] = None,
               additional_inputs: Optional[Dict[str, Any]] = None) -> RegimeContextVector:
        """
        Process market data and detect regime
        
        Args:
            market_data: DataFrame with OHLCV data
            previous_tier_output: Output from Tier 3 (MarketGeometryModel)
            additional_inputs: Additional inputs (not used in Tier 4)
            
        Returns:
            RegimeContextVector with regime analysis
        """
        if not self.validate_input(market_data):
            logger.error("Invalid input data for Tier 4")
            return None
        try:
        
            # Classify volatility regime
            vol_regime = self.volatility_classifier.classify(market_data)
            
            # Classify market phase
            phase = self.phase_classifier.classify(market_data)
            
            # Get AI analysis
            ai_results = self.ai_analysis.analyze(market_data)
            
            # Determine overall regime
            if vol_regime['regime'] == 'high':
                if phase['phase'] in ['accumulation', 'distribution']:
                    regime_type = 'volatile_reversal'
                else:
                    regime_type = 'volatile_trend'
            else:
                if phase['phase'] in ['markup', 'markdown']:
                    regime_type = 'trending'
                else:
                    regime_type = 'ranging'
            
            # Calculate regime probability
            regime_prob = (
                0.4 * vol_regime['probability'] +
                0.3 * phase['probability'] +
                0.3 * ai_results['confidence']
            )
            
            # Get optimal policy from AI
            optimal_policy = ai_results['optimal_policy']
            
            # Calculate signal value (-1 to 1)
            if regime_type == 'trending':
                signal_value = 1.0 if phase['phase'] == 'markup' else -1.0
            elif regime_type == 'volatile_trend':
                signal_value = 0.8 if phase['phase'] == 'markup' else -0.8
            elif regime_type == 'volatile_reversal':
                signal_value = -0.5 if phase['phase'] == 'accumulation' else 0.5
            else:  # ranging
                signal_value = 0.0
            
            # Adjust signal by AI prediction
            signal_value *= ai_results['confidence']
            
            # Create metadata
            metadata = {
                'volatility': vol_regime,
                'phase': phase,
                'ai': ai_results
            }
            
            # Create regime context vector
            regime = RegimeContextVector(
                timestamp=market_data.index[-1],
                signal_value=signal_value,
                confidence=regime_prob,
                regime_type=regime_type,
                regime_probability=regime_prob,
                market_phase=phase['phase'],
                phase_probability=phase['probability'],
                optimal_policy=optimal_policy,
                shap_values=ai_results['shap_values'],
                metadata=metadata
            )
            
            self.last_output = regime
            return regime
            
        except Exception as e:
            logger.error(f"Error processing Tier 4: {str(e)}")
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
    tier4 = Tier4RegimeDetection()
    tier4.initialize()
    result = tier4.process(df)
    
    # Print results
    logger.info("\n=== Tier 4: Regime Detection Results ===")
    logger.info(f"Signal: {result.signal_value:.4f}")
    logger.info(f"Confidence: {result.confidence:.2%}")
    logger.info(f"Regime: {result.regime_type}")
    logger.info(f"Market Phase: {result.market_phase}")
    logger.info(f"Optimal Policy: {result.optimal_policy}")
    logger.info("\nTop SHAP Values:")
    for feature, value in sorted(result.shap_values.items(), 
                               key=lambda x: abs(x[1]), reverse=True)[:3]:
        logger.info(f"- {feature}: {value:.4f}")
