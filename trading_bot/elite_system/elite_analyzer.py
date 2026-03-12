"""
Elite Analyzer - Unified Advanced Analysis Module
Provides comprehensive market analysis combining all elite system components
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Import elite system components
try:
    from trading_bot.elite_system.market_analysis import EliteMarketAnalyzer
except ImportError:
    EliteMarketAnalyzer = None

try:
    from trading_bot.elite_system.pattern_recognition import ElitePatternRecognizer
except ImportError:
    ElitePatternRecognizer = None

try:
    from trading_bot.elite_system.regime_detection import EliteRegimeDetector
except ImportError:
    EliteRegimeDetector = None

try:
    from trading_bot.elite_system.market_psychology import EliteMarketPsychology
except ImportError:
    EliteMarketPsychology = None

try:
    from trading_bot.elite_system.order_flow_decryptor import OrderFlowDecryptor
except ImportError:
    OrderFlowDecryptor = None

class AnalysisStrength(Enum):
    """Analysis signal strength"""
    VERY_STRONG = "VERY_STRONG"
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    NEUTRAL = "NEUTRAL"

@dataclass
class EliteAnalysis:
    """Comprehensive elite analysis result"""
    timestamp: datetime
    symbol: str
    timeframe: str
    
    # Market regime
    regime: Optional[str] = None
    regime_confidence: float = 0.0
    
    # Pattern recognition
    patterns: List[str] = None
    pattern_strength: float = 0.0
    
    # Market psychology
    sentiment: Optional[str] = None
    sentiment_score: float = 0.0
    
    # Order flow
    order_flow_bias: Optional[str] = None
    order_flow_strength: float = 0.0
    
    # Overall analysis
    overall_bias: Optional[str] = None
    overall_strength: AnalysisStrength = AnalysisStrength.NEUTRAL
    confidence: float = 0.0
    
    # Recommendations
    entry_zones: List[float] = None
    stop_loss: Optional[float] = None
    take_profit: List[float] = None
    
    # Metadata
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.patterns is None:
            self.patterns = []
        if self.entry_zones is None:
            self.entry_zones = []
        if self.take_profit is None:
            self.take_profit = []
        if self.metadata is None:
            self.metadata = {}

class EliteAnalyzer:
    """
    Elite Analyzer - Unified Advanced Analysis System
    
    Combines all elite system components for comprehensive market analysis:
    - Market regime detection
    - Pattern recognition
    - Market psychology
    - Order flow analysis
    - Price action intelligence
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Elite Analyzer
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.is_initialized = False
        
        # Initialize components
        self.market_analyzer = None
        self.pattern_recognizer = None
        self.regime_detector = None
        self.psychology_analyzer = None
        self.order_flow_analyzer = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all analysis components"""
        try:
            if EliteMarketAnalyzer:
                self.market_analyzer = EliteMarketAnalyzer(self.config)
            
            if ElitePatternRecognizer:
                self.pattern_recognizer = ElitePatternRecognizer(self.config)
            
            if EliteRegimeDetector:
                self.regime_detector = EliteRegimeDetector(self.config)
            
            if EliteMarketPsychology:
                self.psychology_analyzer = EliteMarketPsychology(self.config)
            
            if OrderFlowDecryptor:
                self.order_flow_analyzer = OrderFlowDecryptor(self.config)
            
            self.is_initialized = True
            
        except Exception as e:
            print(f"Warning: Some elite components could not be initialized: {e}")
            self.is_initialized = True  # Continue with available components
    
    def analyze(self, data: pd.DataFrame, symbol: str = "UNKNOWN", 
                timeframe: str = "1H") -> EliteAnalysis:
        """
        Perform comprehensive elite analysis
        
        Args:
            data: Market data DataFrame with OHLCV columns
            symbol: Trading symbol
            timeframe: Timeframe string
            
        Returns:
            EliteAnalysis object with comprehensive results
        """
        if not self.is_initialized:
            self._initialize_components()
        
        analysis = EliteAnalysis(
            timestamp=datetime.now(),
            symbol=symbol,
            timeframe=timeframe
        )
        
        try:
            # Regime detection
            if self.regime_detector:
                regime_result = self._analyze_regime(data)
                analysis.regime = regime_result.get('regime', 'UNKNOWN')
                analysis.regime_confidence = regime_result.get('confidence', 0.0)
            
            # Pattern recognition
            if self.pattern_recognizer:
                pattern_result = self._analyze_patterns(data)
                analysis.patterns = pattern_result.get('patterns', [])
                analysis.pattern_strength = pattern_result.get('strength', 0.0)
            
            # Market psychology
            if self.psychology_analyzer:
                psych_result = self._analyze_psychology(data)
                analysis.sentiment = psych_result.get('sentiment', 'NEUTRAL')
                analysis.sentiment_score = psych_result.get('score', 0.0)
            
            # Order flow
            if self.order_flow_analyzer:
                flow_result = self._analyze_order_flow(data)
                analysis.order_flow_bias = flow_result.get('bias', 'NEUTRAL')
                analysis.order_flow_strength = flow_result.get('strength', 0.0)
            
            # Synthesize overall analysis
            self._synthesize_analysis(analysis, data)
            
        except Exception as e:
            print(f"Error in elite analysis: {e}")
            analysis.metadata['error'] = str(e)
        
        return analysis
    
    def _analyze_regime(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze market regime"""
        try:
            if hasattr(self.regime_detector, 'detect_regime'):
                result = self.regime_detector.detect_regime(data)
                return result if isinstance(result, dict) else {'regime': str(result), 'confidence': 0.7}
            
            # Fallback: Simple volatility-based regime
            returns = data['close'].pct_change()
            volatility = returns.std()
            
            if volatility > 0.02:
                return {'regime': 'HIGH_VOLATILITY', 'confidence': 0.6}
            elif volatility < 0.005:
                return {'regime': 'LOW_VOLATILITY', 'confidence': 0.6}
            else:
                return {'regime': 'NORMAL', 'confidence': 0.5}
                
        except Exception as e:
            print(f"Regime detection error: {e}")
            return {'regime': 'UNKNOWN', 'confidence': 0.0}
    
    def _analyze_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze chart patterns"""
        try:
            if hasattr(self.pattern_recognizer, 'recognize_patterns'):
                result = self.pattern_recognizer.recognize_patterns(data)
                return result if isinstance(result, dict) else {'patterns': [], 'strength': 0.0}
            
            # Fallback: Simple trend detection
            close = data['close'].values
            if len(close) < 20:
                return {'patterns': [], 'strength': 0.0}
            
            sma_20 = pd.Series(close).rolling(20).mean().iloc[-1]
            current = close[-1]
            
            patterns = []
            if current > sma_20 * 1.02:
                patterns.append('UPTREND')
            elif current < sma_20 * 0.98:
                patterns.append('DOWNTREND')
            else:
                patterns.append('SIDEWAYS')
            
            return {'patterns': patterns, 'strength': 0.5}
            
        except Exception as e:
            print(f"Pattern recognition error: {e}")
            return {'patterns': [], 'strength': 0.0}
    
    def _analyze_psychology(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze market psychology"""
        try:
            if hasattr(self.psychology_analyzer, 'analyze_sentiment'):
                result = self.psychology_analyzer.analyze_sentiment(data)
                return result if isinstance(result, dict) else {'sentiment': 'NEUTRAL', 'score': 0.0}
            
            # Fallback: Volume-based sentiment
            if 'volume' in data.columns:
                volume_ma = data['volume'].rolling(20).mean()
                current_volume = data['volume'].iloc[-1]
                
                if current_volume > volume_ma.iloc[-1] * 1.5:
                    return {'sentiment': 'STRONG', 'score': 0.7}
                elif current_volume < volume_ma.iloc[-1] * 0.5:
                    return {'sentiment': 'WEAK', 'score': 0.3}
            
            return {'sentiment': 'NEUTRAL', 'score': 0.5}
            
        except Exception as e:
            print(f"Psychology analysis error: {e}")
            return {'sentiment': 'NEUTRAL', 'score': 0.0}
    
    def _analyze_order_flow(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze order flow"""
        try:
            if hasattr(self.order_flow_analyzer, 'analyze_flow'):
                result = self.order_flow_analyzer.analyze_flow(data)
                return result if isinstance(result, dict) else {'bias': 'NEUTRAL', 'strength': 0.0}
            
            # Fallback: Price action based flow
            close = data['close'].values
            if len(close) < 10:
                return {'bias': 'NEUTRAL', 'strength': 0.0}
            
            recent_change = (close[-1] - close[-10]) / close[-10]
            
            if recent_change > 0.01:
                return {'bias': 'BULLISH', 'strength': min(abs(recent_change) * 50, 1.0)}
            elif recent_change < -0.01:
                return {'bias': 'BEARISH', 'strength': min(abs(recent_change) * 50, 1.0)}
            
            return {'bias': 'NEUTRAL', 'strength': 0.0}
            
        except Exception as e:
            print(f"Order flow analysis error: {e}")
            return {'bias': 'NEUTRAL', 'strength': 0.0}
    
    def _synthesize_analysis(self, analysis: EliteAnalysis, data: pd.DataFrame):
        """Synthesize overall analysis from components"""
        try:
            # Determine overall bias
            biases = []
            strengths = []
            
            if analysis.order_flow_bias and analysis.order_flow_bias != 'NEUTRAL':
                biases.append(analysis.order_flow_bias)
                strengths.append(analysis.order_flow_strength)
            
            if analysis.patterns:
                if 'UPTREND' in analysis.patterns:
                    biases.append('BULLISH')
                    strengths.append(analysis.pattern_strength)
                elif 'DOWNTREND' in analysis.patterns:
                    biases.append('BEARISH')
                    strengths.append(analysis.pattern_strength)
            
            # Calculate overall bias
            if biases:
                bullish_count = biases.count('BULLISH')
                bearish_count = biases.count('BEARISH')
                
                if bullish_count > bearish_count:
                    analysis.overall_bias = 'BULLISH'
                elif bearish_count > bullish_count:
                    analysis.overall_bias = 'BEARISH'
                else:
                    analysis.overall_bias = 'NEUTRAL'
                
                # Calculate confidence
                if strengths:
                    analysis.confidence = np.mean(strengths)
                    
                    if analysis.confidence > 0.7:
                        analysis.overall_strength = AnalysisStrength.VERY_STRONG
                    elif analysis.confidence > 0.5:
                        analysis.overall_strength = AnalysisStrength.STRONG
                    elif analysis.confidence > 0.3:
                        analysis.overall_strength = AnalysisStrength.MODERATE
                    else:
                        analysis.overall_strength = AnalysisStrength.WEAK
            
            # Calculate entry zones and targets
            if len(data) > 0:
                current_price = data['close'].iloc[-1]
                atr = self._calculate_atr(data)
                
                if analysis.overall_bias == 'BULLISH':
                    analysis.entry_zones = [
                        current_price - atr * 0.5,
                        current_price - atr * 0.25
                    ]
                    analysis.stop_loss = current_price - atr * 2.0
                    analysis.take_profit = [
                        current_price + atr * 2.0,
                        current_price + atr * 3.0,
                        current_price + atr * 4.0
                    ]
                elif analysis.overall_bias == 'BEARISH':
                    analysis.entry_zones = [
                        current_price + atr * 0.5,
                        current_price + atr * 0.25
                    ]
                    analysis.stop_loss = current_price + atr * 2.0
                    analysis.take_profit = [
                        current_price - atr * 2.0,
                        current_price - atr * 3.0,
                        current_price - atr * 4.0
                    ]
            
        except Exception as e:
            print(f"Synthesis error: {e}")
    
    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            high = data['high'].values
            low = data['low'].values
            close = data['close'].values
            
            tr_list = []
            for i in range(1, len(data)):
                tr = max(
                    high[i] - low[i],
                    abs(high[i] - close[i-1]),
                    abs(low[i] - close[i-1])
                )
                tr_list.append(tr)
            
            if len(tr_list) >= period:
                return np.mean(tr_list[-period:])
            elif tr_list:
                return np.mean(tr_list)
            else:
                return data['close'].iloc[-1] * 0.01  # 1% fallback
                
        except Exception:
            return data['close'].iloc[-1] * 0.01
    
    def get_info(self) -> Dict[str, Any]:
        """Get analyzer information"""
        return {
            'is_initialized': self.is_initialized,
            'components': {
                'market_analyzer': self.market_analyzer is not None,
                'pattern_recognizer': self.pattern_recognizer is not None,
                'regime_detector': self.regime_detector is not None,
                'psychology_analyzer': self.psychology_analyzer is not None,
                'order_flow_analyzer': self.order_flow_analyzer is not None
            }
        }

# Export for compatibility
__all__ = ['EliteAnalyzer', 'EliteAnalysis', 'AnalysisStrength']
