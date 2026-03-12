"""
Predictive Intelligence
=======================

Multi-horizon forecasting and probability modeling system.
Predicts future market movements across multiple timeframes.

Features:
- Multi-horizon price forecasting (1m, 5m, 15m, 1h, 4h, 1d)
- Probability distribution modeling
- Scenario analysis (bull, bear, neutral)
- Confidence intervals
- Ensemble predictions
- Trend reversal prediction
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.debug("scikit-learn not available for advanced forecasting")

try:
    from scipy.stats import norm
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.debug("scipy not available for probability modeling")


class ForecastHorizon(Enum):
    """Forecast time horizons"""
    VERY_SHORT = "1m"  # 1 minute
    SHORT = "5m"  # 5 minutes
    MEDIUM = "15m"  # 15 minutes
    LONG = "1h"  # 1 hour
    VERY_LONG = "4h"  # 4 hours
    DAILY = "1d"  # 1 day


class ScenarioType(Enum):
    """Market scenario types"""
    BULL = "bull"
    BEAR = "bear"
    NEUTRAL = "neutral"
    VOLATILE = "volatile"
    BREAKOUT_UP = "breakout_up"
    BREAKOUT_DOWN = "breakout_down"


@dataclass
class PriceForecast:
    """Price forecast for a specific horizon"""
    horizon: ForecastHorizon
    predicted_price: float
    confidence_lower: float
    confidence_upper: float
    confidence_level: float
    probability_up: float
    probability_down: float
    expected_return: float
    predicted_at: datetime
    features_used: List[str] = field(default_factory=list)


@dataclass
class ScenarioForecast:
    """Forecast for a specific market scenario"""
    scenario: ScenarioType
    probability: float
    expected_price_change: float
    expected_volatility: float
    duration_estimate: timedelta
    key_drivers: List[str]
    confidence: float


@dataclass
class TrendPrediction:
    """Trend reversal/continuation prediction"""
    current_trend: str  # 'up', 'down', 'sideways'
    reversal_probability: float
    continuation_probability: float
    expected_reversal_time: Optional[datetime]
    reversal_confidence: float
    key_signals: List[str]


class PredictiveIntelligence:
    """
    Multi-horizon predictive system.
    
    Predicts:
    - Future prices across multiple timeframes
    - Probability distributions
    - Market scenarios
    - Trend reversals
    - Volatility changes
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Prediction settings
        self.confidence_level = self.config.get('confidence_level', 0.95)
        self.min_training_samples = self.config.get('min_training_samples', 100)
        self.ensemble_size = self.config.get('ensemble_size', 3)
        
        # Forecast history
        self.forecast_history: List[PriceForecast] = []
        self.scenario_history: List[ScenarioForecast] = []
        self.trend_predictions: List[TrendPrediction] = []
        
        # Initialize models
        self._init_models()
        
        logger.info("Predictive Intelligence initialized")
    
    def _init_models(self):
        """Initialize prediction models"""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available - using simplified predictions")
            self.models = {}
            self.scaler = None
            return
        
        # Ensemble of models for robust predictions
        self.models = {
            'rf': RandomForestRegressor(n_estimators=50, random_state=42, max_depth=10),
            'gb': GradientBoostingRegressor(n_estimators=50, random_state=42, max_depth=5),
            'ridge': Ridge(alpha=1.0, random_state=42)
        }
        
        self.scaler = StandardScaler()
        self.models_trained = False
    
    async def forecast_price(
        self,
        market_data: pd.DataFrame,
        symbol: str,
        horizons: Optional[List[ForecastHorizon]] = None
    ) -> Dict[ForecastHorizon, PriceForecast]:
        """
        Forecast prices for multiple time horizons.
        
        Args:
            market_data: Historical OHLCV data
            symbol: Trading symbol
            horizons: List of forecast horizons (default: all)
        
        Returns:
            Dictionary of forecasts by horizon
        """
        try:
            if market_data is None or len(market_data) < 50:
                return {}
            
            if horizons is None:
                horizons = list(ForecastHorizon)
            
            forecasts = {}
            
            for horizon in horizons:
                forecast = await self._forecast_single_horizon(
                    market_data=market_data,
                    symbol=symbol,
                    horizon=horizon
                )
                
                if forecast:
                    forecasts[horizon] = forecast
                    self.forecast_history.append(forecast)
            
            # Keep only recent history
            if len(self.forecast_history) > 1000:
                self.forecast_history = self.forecast_history[-1000:]
            
            logger.debug(f"Generated {len(forecasts)} forecasts for {symbol}")
            return forecasts
            
        except Exception as e:
            logger.error(f"Error forecasting price: {e}")
            return {}
    
    async def _forecast_single_horizon(
        self,
        market_data: pd.DataFrame,
        symbol: str,
        horizon: ForecastHorizon
    ) -> Optional[PriceForecast]:
        """Forecast price for a single horizon"""
        try:
            close = market_data['close'].values
            current_price = close[-1]
            
            # Extract features
            features = self._extract_forecast_features(market_data)
            
            if SKLEARN_AVAILABLE and len(market_data) >= self.min_training_samples:
                # Use ML models
                predicted_price, confidence_interval = self._ml_forecast(
                    features=features,
                    current_price=current_price,
                    horizon=horizon,
                    market_data=market_data
                )
            else:
                # Simple statistical forecast
                predicted_price, confidence_interval = self._simple_forecast(
                    close=close,
                    horizon=horizon
                )
            
            # Calculate probabilities
            prob_up, prob_down = self._calculate_direction_probabilities(
                current_price=current_price,
                predicted_price=predicted_price,
                confidence_interval=confidence_interval
            )
            
            # Expected return
            expected_return = (predicted_price - current_price) / current_price
            
            forecast = PriceForecast(
                horizon=horizon,
                predicted_price=predicted_price,
                confidence_lower=confidence_interval[0],
                confidence_upper=confidence_interval[1],
                confidence_level=self.confidence_level,
                probability_up=prob_up,
                probability_down=prob_down,
                expected_return=expected_return,
                predicted_at=datetime.now(),
                features_used=['price', 'volume', 'volatility', 'momentum']
            )
            
            return forecast
            
        except Exception as e:
            logger.error(f"Error forecasting horizon {horizon}: {e}")
            return None
    
    def _extract_forecast_features(self, data: pd.DataFrame) -> np.ndarray:
        """Extract features for forecasting"""
        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            volume = data.get('volume', pd.Series([0] * len(data))).values
            
            # Price features
            returns = np.diff(close, prepend=close[0]) / close
            
            # Moving averages
            ma_5 = pd.Series(close).rolling(5).mean().fillna(close).values
            ma_10 = pd.Series(close).rolling(10).mean().fillna(close).values
            ma_20 = pd.Series(close).rolling(20).mean().fillna(close).values
            
            # Volatility
            volatility = pd.Series(returns).rolling(20).std().fillna(0).values
            
            # Momentum
            roc = (close - np.roll(close, 10)) / np.roll(close, 10)
            roc[:10] = 0
            
            # Range
            atr = pd.Series(high - low).rolling(14).mean().fillna(0).values
            
            # Volume
            volume_ma = pd.Series(volume).rolling(20).mean().fillna(1).values
            volume_ratio = np.where(volume_ma > 0, volume / volume_ma, 1.0)
            
            # Combine features
            features = np.column_stack([
                close / close[-1],  # Normalized price
                (close - ma_5) / close,  # Distance from MA5
                (close - ma_10) / close,  # Distance from MA10
                (close - ma_20) / close,  # Distance from MA20
                volatility,
                roc,
                atr / close,  # Normalized ATR
                volume_ratio
            ])
            
            features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting forecast features: {e}")
            return np.array([[0.0] * 8])
    
    def _ml_forecast(
        self,
        features: np.ndarray,
        current_price: float,
        horizon: ForecastHorizon,
        market_data: pd.DataFrame
    ) -> Tuple[float, Tuple[float, float]]:
        """ML-based forecast using ensemble"""
        try:
            # Prepare training data
            X, y = self._prepare_training_data(features, market_data, horizon)
            
            if len(X) < 20:
                return self._simple_forecast(market_data['close'].values, horizon)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train and predict with ensemble
            predictions = []
            
            for model_name, model in self.models.items():
                try:
                    model.fit(X_scaled[:-1], y)
                    pred = model.predict(X_scaled[-1:])
                    predictions.append(pred[0])
                except Exception as e:
                    logger.debug(f"Model {model_name} failed: {e}")
            
            if not predictions:
                return self._simple_forecast(market_data['close'].values, horizon)
            
            # Ensemble prediction (mean)
            predicted_change = np.mean(predictions)
            predicted_price = current_price * (1 + predicted_change)
            
            # Confidence interval (std of predictions)
            std_predictions = np.std(predictions) if len(predictions) > 1 else 0.01
            z_score = 1.96  # 95% confidence
            
            confidence_lower = current_price * (1 + predicted_change - z_score * std_predictions)
            confidence_upper = current_price * (1 + predicted_change + z_score * std_predictions)
            
            self.models_trained = True
            
            return predicted_price, (confidence_lower, confidence_upper)
            
        except Exception as e:
            logger.error(f"Error in ML forecast: {e}")
            return self._simple_forecast(market_data['close'].values, horizon)
    
    def _prepare_training_data(
        self,
        features: np.ndarray,
        market_data: pd.DataFrame,
        horizon: ForecastHorizon
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for supervised learning"""
        
        # Determine lookahead based on horizon
        horizon_map = {
            ForecastHorizon.VERY_SHORT: 1,
            ForecastHorizon.SHORT: 5,
            ForecastHorizon.MEDIUM: 15,
            ForecastHorizon.LONG: 60,
            ForecastHorizon.VERY_LONG: 240,
            ForecastHorizon.DAILY: 1440
        }
        
        lookahead = horizon_map.get(horizon, 5)
        
        close = market_data['close'].values
        
        # Create target (future returns)
        y = []
        X = []
        
        for i in range(len(close) - lookahead):
            future_return = (close[i + lookahead] - close[i]) / close[i]
            y.append(future_return)
            X.append(features[i])
        
        return np.array(X), np.array(y)
    
    def _simple_forecast(
        self,
        close: np.ndarray,
        horizon: ForecastHorizon
    ) -> Tuple[float, Tuple[float, float]]:
        """Simple statistical forecast"""
        try:
            current_price = close[-1]
            
            # Calculate recent trend
            if len(close) >= 20:
                recent_returns = np.diff(close[-20:]) / close[-20:-1]
                mean_return = np.mean(recent_returns)
                std_return = np.std(recent_returns)
            else:
                mean_return = 0.0
                std_return = 0.01
            
            # Horizon multiplier
            horizon_multiplier = {
                ForecastHorizon.VERY_SHORT: 0.2,
                ForecastHorizon.SHORT: 0.5,
                ForecastHorizon.MEDIUM: 1.0,
                ForecastHorizon.LONG: 2.0,
                ForecastHorizon.VERY_LONG: 4.0,
                ForecastHorizon.DAILY: 8.0
            }.get(horizon, 1.0)
            
            # Predicted change
            predicted_change = mean_return * horizon_multiplier
            predicted_price = current_price * (1 + predicted_change)
            
            # Confidence interval
            z_score = 1.96
            margin = z_score * std_return * np.sqrt(horizon_multiplier)
            
            confidence_lower = current_price * (1 + predicted_change - margin)
            confidence_upper = current_price * (1 + predicted_change + margin)
            
            return predicted_price, (confidence_lower, confidence_upper)
            
        except Exception as e:
            logger.error(f"Error in simple forecast: {e}")
            return close[-1], (close[-1] * 0.99, close[-1] * 1.01)
    
    def _calculate_direction_probabilities(
        self,
        current_price: float,
        predicted_price: float,
        confidence_interval: Tuple[float, float]
    ) -> Tuple[float, float]:
        """Calculate probability of up/down movement"""
        try:
            if not SCIPY_AVAILABLE:
                # Simple probability based on prediction
                if predicted_price > current_price:
                    return 0.6, 0.4
                elif predicted_price < current_price:
                    return 0.4, 0.6
                else:
                    return 0.5, 0.5
            
            # Use normal distribution
            mean = predicted_price
            std = (confidence_interval[1] - confidence_interval[0]) / (2 * 1.96)
            
            # Probability of price > current
            prob_up = 1 - norm.cdf(current_price, loc=mean, scale=std)
            prob_down = 1 - prob_up
            
            return float(prob_up), float(prob_down)
            
        except Exception:
            return 0.5, 0.5
    
    async def forecast_scenarios(
        self,
        market_data: pd.DataFrame,
        symbol: str
    ) -> List[ScenarioForecast]:
        """
        Forecast different market scenarios with probabilities.
        
        Args:
            market_data: Historical data
            symbol: Trading symbol
        
        Returns:
            List of scenario forecasts
        """
        try:
            if market_data is None or len(market_data) < 50:
                return []
            
            close = market_data['close'].values
            current_price = close[-1]
            
            # Calculate market conditions
            volatility = np.std(np.diff(close[-20:]) / close[-20:-1]) if len(close) >= 20 else 0.01
            trend = (close[-1] - close[-20]) / close[-20] if len(close) >= 20 else 0.0
            momentum = (close[-1] - close[-5]) / close[-5] if len(close) >= 5 else 0.0
            
            scenarios = []
            
            # Bull scenario
            if trend > 0 or momentum > 0:
                scenarios.append(ScenarioForecast(
                    scenario=ScenarioType.BULL,
                    probability=min(0.3 + trend * 10, 0.7),
                    expected_price_change=0.02,
                    expected_volatility=volatility * 1.2,
                    duration_estimate=timedelta(hours=4),
                    key_drivers=['positive_momentum', 'uptrend'],
                    confidence=0.7
                ))
            
            # Bear scenario
            if trend < 0 or momentum < 0:
                scenarios.append(ScenarioForecast(
                    scenario=ScenarioType.BEAR,
                    probability=min(0.3 + abs(trend) * 10, 0.7),
                    expected_price_change=-0.02,
                    expected_volatility=volatility * 1.3,
                    duration_estimate=timedelta(hours=4),
                    key_drivers=['negative_momentum', 'downtrend'],
                    confidence=0.7
                ))
            
            # Neutral scenario
            if abs(trend) < 0.005 and abs(momentum) < 0.005:
                scenarios.append(ScenarioForecast(
                    scenario=ScenarioType.NEUTRAL,
                    probability=0.6,
                    expected_price_change=0.0,
                    expected_volatility=volatility,
                    duration_estimate=timedelta(hours=2),
                    key_drivers=['low_momentum', 'ranging'],
                    confidence=0.75
                ))
            
            # Volatile scenario
            if volatility > 0.015:
                scenarios.append(ScenarioForecast(
                    scenario=ScenarioType.VOLATILE,
                    probability=0.5,
                    expected_price_change=0.0,
                    expected_volatility=volatility * 1.5,
                    duration_estimate=timedelta(hours=1),
                    key_drivers=['high_volatility'],
                    confidence=0.8
                ))
            
            # Normalize probabilities
            total_prob = sum(s.probability for s in scenarios)
            if total_prob > 0:
                for scenario in scenarios:
                    scenario.probability /= total_prob
            
            self.scenario_history.extend(scenarios)
            
            if len(self.scenario_history) > 500:
                self.scenario_history = self.scenario_history[-500:]
            
            logger.debug(f"Generated {len(scenarios)} scenario forecasts")
            return scenarios
            
        except Exception as e:
            logger.error(f"Error forecasting scenarios: {e}")
            return []
    
    async def predict_trend_reversal(
        self,
        market_data: pd.DataFrame,
        symbol: str
    ) -> TrendPrediction:
        """
        Predict trend reversal probability.
        
        Args:
            market_data: Historical data
            symbol: Trading symbol
        
        Returns:
            Trend reversal prediction
        """
        try:
            if market_data is None or len(market_data) < 50:
                return TrendPrediction(
                    current_trend='unknown',
                    reversal_probability=0.0,
                    continuation_probability=0.0,
                    expected_reversal_time=None,
                    reversal_confidence=0.0,
                    key_signals=[]
                )
            
            close = market_data['close'].values
            high = market_data['high'].values
            low = market_data['low'].values
            
            # Determine current trend
            current_trend = self._determine_trend(close)
            
            # Reversal signals
            reversal_signals = []
            reversal_score = 0.0
            
            # 1. Divergence check (simplified)
            if len(close) >= 20:
                price_trend = close[-1] - close[-20]
                momentum_trend = (close[-1] - close[-5]) - (close[-15] - close[-20])
                
                if (price_trend > 0 and momentum_trend < 0) or (price_trend < 0 and momentum_trend > 0):
                    reversal_signals.append('momentum_divergence')
                    reversal_score += 0.3
            
            # 2. Overbought/Oversold (RSI-like)
            if len(close) >= 14:
                gains = []
                losses = []
                for i in range(1, 15):
                    change = close[-i] - close[-i-1]
                    if change > 0:
                        gains.append(change)
                    else:
                        losses.append(abs(change))
                
                avg_gain = np.mean(gains) if gains else 0.0
                avg_loss = np.mean(losses) if losses else 0.0
                
                if avg_loss > 0:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                    
                    if rsi > 70:
                        reversal_signals.append('overbought')
                        reversal_score += 0.25
                    elif rsi < 30:
                        reversal_signals.append('oversold')
                        reversal_score += 0.25
            
            # 3. Support/Resistance test
            if current_trend == 'up':
                recent_high = np.max(high[-20:])
                if close[-1] >= recent_high * 0.995:
                    reversal_signals.append('resistance_test')
                    reversal_score += 0.2
            elif current_trend == 'down':
                recent_low = np.min(low[-20:])
                if close[-1] <= recent_low * 1.005:
                    reversal_signals.append('support_test')
                    reversal_score += 0.2
            
            # 4. Volatility expansion
            if len(close) >= 40:
                recent_vol = np.std(np.diff(close[-10:]) / close[-10:-1])
                historical_vol = np.std(np.diff(close[-40:-10]) / close[-40:-10])
                
                if recent_vol > historical_vol * 1.5:
                    reversal_signals.append('volatility_expansion')
                    reversal_score += 0.15
            
            # Calculate probabilities
            reversal_probability = min(reversal_score, 0.9)
            continuation_probability = 1.0 - reversal_probability
            
            # Estimate reversal time
            expected_reversal_time = None
            if reversal_probability > 0.6:
                expected_reversal_time = datetime.now() + timedelta(hours=2)
            
            prediction = TrendPrediction(
                current_trend=current_trend,
                reversal_probability=reversal_probability,
                continuation_probability=continuation_probability,
                expected_reversal_time=expected_reversal_time,
                reversal_confidence=0.7 if len(reversal_signals) >= 2 else 0.5,
                key_signals=reversal_signals
            )
            
            self.trend_predictions.append(prediction)
            
            if len(self.trend_predictions) > 200:
                self.trend_predictions = self.trend_predictions[-200:]
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting trend reversal: {e}")
            return TrendPrediction(
                current_trend='unknown',
                reversal_probability=0.0,
                continuation_probability=0.0,
                expected_reversal_time=None,
                reversal_confidence=0.0,
                key_signals=[]
            )
    
    def _determine_trend(self, close: np.ndarray) -> str:
        """Determine current trend direction"""
        try:
            if len(close) < 20:
                return 'unknown'
            
            # Simple trend based on moving averages
            ma_short = np.mean(close[-5:])
            ma_long = np.mean(close[-20:])
            
            if ma_short > ma_long * 1.002:
                return 'up'
            elif ma_short < ma_long * 0.998:
                return 'down'
            else:
                return 'sideways'
                
        except Exception:
            return 'unknown'
    
    def get_prediction_statistics(self) -> Dict[str, Any]:
        """Get prediction statistics and accuracy"""
        return {
            'total_forecasts': len(self.forecast_history),
            'total_scenarios': len(self.scenario_history),
            'total_trend_predictions': len(self.trend_predictions),
            'models_trained': self.models_trained if SKLEARN_AVAILABLE else False,
            'recent_forecasts': [
                {
                    'horizon': f.horizon.value,
                    'predicted_price': f.predicted_price,
                    'confidence': f.confidence_level,
                    'probability_up': f.probability_up,
                    'predicted_at': f.predicted_at.isoformat()
                }
                for f in self.forecast_history[-5:]
            ],
            'recent_scenarios': [
                {
                    'scenario': s.scenario.value,
                    'probability': s.probability,
                    'expected_change': s.expected_price_change
                }
                for s in self.scenario_history[-5:]
            ]
        }
