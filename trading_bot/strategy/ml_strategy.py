from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
"""ML-enhanced StrategyEngine – integrates ML predictive models with traditional analysis.

This module extends the base StrategyEngine with machine learning capabilities
for price prediction, pattern recognition, and sentiment analysis.
"""

import datetime as _dt
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

try:
    from trading_bot.strategy.strategy_engine import StrategyEngine, Signal
except ImportError:
    StrategyEngine = None
    Signal = None

try:
    from trading_bot.data import MT5Interface
except ImportError:
    MT5Interface = None

try:
    from trading_bot.ml.predictive_models import PricePredictor
except ImportError:
    PricePredictor = None

try:
    from trading_bot.ml import StrategyOptimizer, SentimentAnalyzer
except ImportError:
    StrategyOptimizer = None
    SentimentAnalyzer = None


class MLStrategyEngine(StrategyEngine):
    """Enhanced strategy engine with ML capabilities."""

    def __init__(
        self,
        mt5i: MT5Interface,
        *,
        swing_len: int = 3,
        symbol: str = "EURUSD",
        use_price_prediction: bool = True,
        use_pattern_recognition: bool = True,
        use_sentiment: bool = False,
        confidence_threshold: float = 60.0,
    ) -> None:
        """Initialize the ML-enhanced strategy engine.
        
        Args:
            mt5i: MetaTrader 5 interface
            swing_len: Swing length for market structure analysis
            symbol: Trading symbol
            use_price_prediction: Whether to use price prediction models
            use_pattern_recognition: Whether to use pattern recognition
            use_sentiment: Whether to use sentiment analysis
            confidence_threshold: Minimum confidence threshold for signals
        """
        super().__init__(mt5i, swing_len=swing_len, symbol=symbol)
        
        # ML components
        self.price_predictor = PricePredictor() if use_price_prediction else None
        self.pattern_recognizer = self.price_predictor.pattern_recognizer if use_price_prediction else None
        self.sentiment_analyzer = SentimentAnalyzer() if use_sentiment else None
        self.strategy_optimizer = StrategyOptimizer()
        
        # Configuration
        self.use_price_prediction = use_price_prediction
        self.use_pattern_recognition = use_pattern_recognition
        self.use_sentiment = use_sentiment
        self.confidence_threshold = confidence_threshold
        
        # Cache for ML predictions
        self.prediction_cache = {}
        
        logger.info(
            "ML Strategy Engine initialized with price_prediction={}, pattern_recognition={}, sentiment={}",
            use_price_prediction,
            use_pattern_recognition,
            use_sentiment,
        )

    def analyse(self, bars) -> List[Signal]:
        """Run traditional and ML-based analysis on bars and return signals.
        
        Args:
            bars: DataFrame with OHLC price data
            
        Returns:
            List of trading signals
        """
        # Get traditional signals first
        traditional_signals = super().analyse(bars)
        
        # Run ML analysis
        ml_signals = []
        
        # Price prediction
        if self.use_price_prediction and self.price_predictor:
            price_signals = self._generate_price_prediction_signals(bars)
            ml_signals.extend(price_signals)
        
        # Pattern recognition
        if self.use_pattern_recognition and self.pattern_recognizer:
            pattern_signals = self._generate_pattern_signals(bars)
            ml_signals.extend(pattern_signals)
        
        # Sentiment analysis
        if self.use_sentiment and self.sentiment_analyzer:
            sentiment_signals = self._generate_sentiment_signals()
            ml_signals.extend(sentiment_signals)
        
        # Combine and filter signals
        combined_signals = self._combine_signals(traditional_signals, ml_signals)
        
        logger.debug(
            "Generated {} traditional signals, {} ML signals, {} combined signals.",
            len(traditional_signals),
            len(ml_signals),
            len(combined_signals),
        )
        
        return combined_signals
    
    def _generate_ml_signals(self, bars) -> List[Signal]:
        """Generate signals based on ML models.
        
        Args:
            bars: DataFrame with OHLC price data
            
        Returns:
            List of ML-based trading signals
        """
        signals = []
        
        # Price prediction
        if self.use_price_prediction and self.price_predictor:
            price_signals = self._generate_price_prediction_signals(bars)
            signals.extend(price_signals)
        
        # Pattern recognition
        if self.use_pattern_recognition and self.pattern_recognizer:
            pattern_signals = self._generate_pattern_signals(bars)
            signals.extend(pattern_signals)
        
        # Sentiment analysis
        if self.use_sentiment and self.sentiment_analyzer:
            sentiment_signals = self._generate_sentiment_signals()
            signals.extend(sentiment_signals)
        
        return signals
    
    def _generate_price_prediction_signals(self, bars: pd.DataFrame) -> List[Signal]:
        """Generate signals based on price prediction models.
        
        Args:
            bars: DataFrame with OHLC price data
            
        Returns:
            List of price prediction signals
        """
        signals = []
        
        try:
            # Skip if DataFrame is empty
            if len(bars) == 0:
                return signals
            
            # Prepare features
            features = self._prepare_features(bars)
            
            # Get price predictions
            prediction = self.price_predictor.predict_next_bars(bars, n_bars=3)
            
            if not prediction or not prediction.get('values'):
                return signals
            
            # Generate signal based on predicted direction
            current_price = bars.iloc[-1].close
            predicted_price = prediction['values'][2]  # 3rd bar prediction
            predicted_change = (predicted_price - current_price) / current_price
            
            # Only generate signal if prediction confidence is high enough
            if prediction['confidence'] >= self.confidence_threshold:
                direction = "buy" if predicted_change > 0 else "sell"
                
                # Calculate stop loss based on prediction volatility
                volatility = prediction['volatility']
                sl_pips = max(10, int(volatility * 10000 * 1.5))  # 1.5x predicted volatility
                
                # Calculate take profit based on predicted change
                tp_pips = abs(int(predicted_change * 10000))
                tp_rr = max(1.5, tp_pips / sl_pips) if sl_pips > 0 else 2.0
                
                try:
                    # Use current datetime if index is not a datetime
                    signal_time = bars.index[-1].to_pydatetime()
                except (AttributeError, TypeError):
                    signal_time = _dt.datetime.now()
                    
                signals.append(
                    Signal(
                        signal_time,
                        self.symbol,
                        direction,
                        f"ML Price Prediction: {direction.upper()} with {prediction['confidence']:.1f}% confidence",
                        stop_loss_pips=sl_pips,
                        take_profit_rr=tp_rr,
                        confidence=prediction['confidence'],
                    )
                )
                
                logger.debug(
                    "Generated price prediction signal: {} with confidence {:.1f}%",
                    direction,
                    prediction['confidence'],
                )
        
        except Exception as e:
            logger.error("Error generating price prediction signals: {}", e)
        
        return signals
    
    def _generate_pattern_signals(self, bars) -> List[Signal]:
        """Generate signals based on pattern recognition.
        
        Args:
            bars: DataFrame with OHLC price data
            
        Returns:
            List of pattern-based signals
        """
        signals = []
        
        try:
            # Detect patterns
            patterns = self.pattern_recognizer.detect_patterns(bars)
            
            # Cache patterns
            self.prediction_cache['patterns'] = patterns
            
            # Generate signals for high-confidence patterns
            for pattern in patterns:
                if pattern['confidence'] >= self.confidence_threshold:
                    direction = pattern['direction']
                    
                    # Calculate stop loss based on pattern
                    sl_pips = pattern.get('suggested_stop_pips', 15)
                    
                    # Calculate take profit based on pattern
                    tp_rr = pattern.get('suggested_rr', 2.0)
                    
                    signals.append(
                        Signal(
                            bars.index[-1].to_pydatetime(),
                            self.symbol,
                            direction,
                            f"Pattern: {pattern['name']} with {pattern['confidence']:.1f}% confidence",
                            stop_loss_pips=sl_pips,
                            take_profit_rr=tp_rr,
                            confidence=pattern['confidence'],
                        )
                    )
                    
                    logger.debug(
                        "Generated pattern signal: {} {} with confidence {:.1f}%",
                        pattern['name'],
                        direction,
                        pattern['confidence'],
                    )
        
        except Exception as e:
            logger.error("Error generating pattern signals: {}", e)
        
        return signals
    
    def _generate_sentiment_signals(self) -> List[Signal]:
        """Generate signals based on sentiment analysis.
        
        Returns:
            List of sentiment-based signals
        """
        signals = []
        
        try:
            # Get market sentiment
            news_sentiment = self.sentiment_analyzer.analyze_news(self.symbol)
            social_sentiment = self.sentiment_analyzer.analyze_social_media(self.symbol)
            
            # Combine sentiment scores
            combined_score = (news_sentiment['score'] * 0.7) + (social_sentiment['score'] * 0.3)
            combined_confidence = (news_sentiment['confidence'] * 0.7) + (social_sentiment['confidence'] * 0.3)
            
            # Cache sentiment
            self.prediction_cache['sentiment'] = {
                'news': news_sentiment,
                'social': social_sentiment,
                'combined': {
                    'score': combined_score,
                    'confidence': combined_confidence
                }
            }
            
            # Generate signal if sentiment is strong enough
            if abs(combined_score) >= 0.3 and combined_confidence >= self.confidence_threshold:
                direction = "buy" if combined_score > 0 else "sell"
                
                # Standard risk parameters for sentiment-based trades
                sl_pips = 15
                tp_rr = 2.0
                
                signals.append(
                    Signal(
                        _dt.datetime.now(),
                        self.symbol,
                        direction,
                        f"Sentiment: {direction.upper()} with {combined_confidence:.1f}% confidence",
                        stop_loss_pips=sl_pips,
                        take_profit_rr=tp_rr,
                        confidence=combined_confidence,
                    )
                )
                
                logger.debug(
                    "Generated sentiment signal: {} with confidence {:.1f}%",
                    direction,
                    combined_confidence,
                )
        
        except Exception as e:
            logger.error("Error generating sentiment signals: {}", e)
        
        return signals
    
    def _combine_signals(self, traditional_signals: List[Signal], ml_signals: List[Signal]) -> List[Signal]:
        """Combine and filter traditional and ML signals.
        
        Args:
            traditional_signals: Signals from traditional analysis
            ml_signals: Signals from ML analysis
            
        Returns:
            Combined and filtered signals
        """
        all_signals = traditional_signals + ml_signals
        
        # Filter signals below confidence threshold
        filtered_signals = [s for s in all_signals if s.confidence >= self.confidence_threshold]
        
        # Use strategy optimizer to resolve conflicting signals
        if len(filtered_signals) > 1:
            # Group signals by direction
            buy_signals = [s for s in filtered_signals if s.direction == "buy"]
            sell_signals = [s for s in filtered_signals if s.direction == "sell"]
            
            # If we have conflicting signals, use the strategy optimizer
            if buy_signals and sell_signals:
                optimized_signals = self.strategy_optimizer.resolve_conflicts(filtered_signals)
                return optimized_signals
        
        return filtered_signals
    
    def _prepare_features(self, bars) -> Dict[str, Any]:
        """Prepare features for ML models.
        
        Args:
            bars: DataFrame with OHLC price data
            
        Returns:
            Dictionary with prepared features
        """
        # This is a simplified version - in a real implementation,
        # this would extract more sophisticated features
        
        features = {
            'ohlc': bars[['open', 'high', 'low', 'close']].values,
            'returns': bars['close'].pct_change().fillna(0).values,
            'volume': bars.get('volume', pd.Series(1, index=bars.index)).values,
        }
        
        # Add technical indicators
        features['rsi'] = self._calculate_rsi(bars['close'])
        features['macd'], features['macd_signal'] = self._calculate_macd(bars['close'])
        
        return features
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI technical indicator.
        
        Args:
            prices: Series of prices
            period: RSI period
            
        Returns:
            Array of RSI values
        """
        # Calculate price changes
        delta = prices.diff().dropna()
        
        # Calculate gains and losses
        gains = delta.copy()
        losses = delta.copy()
        gains[gains < 0] = 0
        losses[losses > 0] = 0
        losses = abs(losses)
        
        # Calculate average gains and losses
        avg_gain = gains.rolling(window=period).mean()
        avg_loss = losses.rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50).values
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD technical indicator.
        
        Args:
            prices: Series of prices
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal EMA period
            
        Returns:
            Tuple of (MACD line, signal line)
        """
        # Calculate EMAs
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        # Calculate MACD line and signal line
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        
        return macd_line.values, signal_line.values
    
    def get_ml_insights(self) -> Dict[str, Any]:
        """Get insights from ML models.
        
        Returns:
            Dictionary with ML insights
        """
        return {
            'predictions': self.prediction_cache,
            'confidence_threshold': self.confidence_threshold,
        }
