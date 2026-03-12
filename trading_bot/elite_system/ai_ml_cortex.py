"""
AI/ML Cortex - Advanced Machine Learning Engine for Elite Trading Bot

This module implements sophisticated AI/ML capabilities including:
- LSTM Neural Networks for price prediction
- Economic Data Fusion Engine
- Multi-Modal Learning System
- Adaptive Model Selection
- Real-time Feature Engineering
- Ensemble Intelligence Networks
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization, Attention
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy
import pandas

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelType(Enum):
    """AI/ML Model Types"""
    LSTM = "lstm"
    GRU = "gru"
    TRANSFORMER = "transformer"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOST = "gradient_boost"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"

class PredictionHorizon(Enum):
    """Prediction Time Horizons"""
    ULTRA_SHORT = "1m"      # 1 minute
    SHORT = "5m"            # 5 minutes
    MEDIUM = "15m"          # 15 minutes
    LONG = "1h"             # 1 hour
    EXTENDED = "4h"         # 4 hours

class EconomicIndicator(Enum):
    """Economic Data Types"""
    INTEREST_RATES = "interest_rates"
    INFLATION = "inflation"
    GDP = "gdp"
    EMPLOYMENT = "employment"
    CONSUMER_CONFIDENCE = "consumer_confidence"
    MANUFACTURING_PMI = "manufacturing_pmi"
    SERVICES_PMI = "services_pmi"
    RETAIL_SALES = "retail_sales"
    TRADE_BALANCE = "trade_balance"
    CURRENCY_STRENGTH = "currency_strength"

@dataclass
class EconomicData:
    """Economic Data Point"""
    indicator: EconomicIndicator
    value: float
    timestamp: datetime
    country: str
    impact_level: str  # HIGH, MEDIUM, LOW
    previous_value: Optional[float] = None
    forecast_value: Optional[float] = None
    
    def surprise_factor(self) -> float:
        """Calculate economic surprise factor"""
        if self.forecast_value is None:
            return 0.0
        return abs(self.value - self.forecast_value) / max(abs(self.forecast_value), 0.01)

@dataclass
class ModelPrediction:
    """ML Model Prediction Result"""
    model_type: ModelType
    prediction: float
    confidence: float
    horizon: PredictionHorizon
    timestamp: datetime
    features_used: List[str]
    model_accuracy: float
    uncertainty_bounds: Tuple[float, float]
    
class FeatureEngineer:
    """Advanced Feature Engineering System"""
    
    def __init__(self):
        self.scalers = {}
        self.feature_importance = {}
        
    def engineer_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer advanced price-based features"""
        features = df.copy()
        
        # Basic OHLC features
        features['hl_ratio'] = (features['high'] - features['low']) / features['close']
        features['oc_ratio'] = (features['open'] - features['close']) / features['close']
        features['price_position'] = (features['close'] - features['low']) / (features['high'] - features['low'])
        
        # Technical indicators
        # Calculate RSI
        delta = features['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))
        
        # Calculate MACD
        exp1 = features['close'].ewm(span=12, adjust=False).mean()
        exp2 = features['close'].ewm(span=26, adjust=False).mean()
        features['macd'] = exp1 - exp2
        features['macd_signal'] = features['macd'].ewm(span=9, adjust=False).mean()
        features['macd_hist'] = features['macd'] - features['macd_signal']
        
        # Calculate Bollinger Bands
        sma = features['close'].rolling(window=20).mean()
        std = features['close'].rolling(window=20).std()
        features['bb_upper'] = sma + (std * 2)
        features['bb_middle'] = sma
        features['bb_lower'] = sma - (std * 2)
        
        # Calculate ATR
        high_low = features['high'] - features['low']
        high_close = abs(features['high'] - features['close'].shift())
        low_close = abs(features['low'] - features['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        features['atr'] = tr.rolling(window=14).mean()
        
        # Volume features
        if 'volume' in features.columns:
            features['volume_sma'] = features['volume'].rolling(window=20).mean()
            features['volume_ratio'] = features['volume'] / features['volume_sma']
            features['price_volume'] = features['close'] * features['volume']
            features['vwap'] = (features['price_volume'].rolling(20).sum() / 
                              features['volume'].rolling(20).sum())
        
        # Volatility features
        features['volatility'] = features['close'].pct_change().rolling(20).std()
        features['volatility_ratio'] = features['atr'] / features['close']
        
        # Momentum features
        features['momentum_5'] = features['close'].pct_change(5)
        features['momentum_10'] = features['close'].pct_change(10)
        features['momentum_20'] = features['close'].pct_change(20)
        
        # Fractal features
        features['fractal_high'] = self._detect_fractals(features['high'].values, 5)
        features['fractal_low'] = self._detect_fractals(features['low'].values, 5, high=False)
        
        # Time-based features
        features['hour'] = pd.to_datetime(features.index).hour
        features['day_of_week'] = pd.to_datetime(features.index).dayofweek
        features['month'] = pd.to_datetime(features.index).month
        
        return features.ffill().fillna(0)
    
    def _detect_fractals(self, data: np.ndarray, period: int, high: bool = True) -> np.ndarray:
        """Detect fractal patterns"""
        fractals = np.zeros_like(data)
        for i in range(period, len(data) - period):
            if high:
                if all(data[i] > data[i-j] for j in range(1, period+1)) and \
                   all(data[i] > data[i+j] for j in range(1, period+1)):
                    fractals[i] = 1
            else:
                if all(data[i] < data[i-j] for j in range(1, period+1)) and \
                   all(data[i] < data[i+j] for j in range(1, period+1)):
                    fractals[i] = 1
        return fractals
    
    def engineer_economic_features(self, economic_data: List[EconomicData]) -> pd.DataFrame:
        """Engineer economic-based features"""
        if not economic_data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        econ_df = pd.DataFrame([{
            'timestamp': ed.timestamp,
            f'{ed.indicator.value}_{ed.country}': ed.value,
            f'{ed.indicator.value}_{ed.country}_surprise': ed.surprise_factor(),
            f'{ed.indicator.value}_{ed.country}_impact': 1 if ed.impact_level == 'HIGH' else 0.5 if ed.impact_level == 'MEDIUM' else 0.1
        } for ed in economic_data])
        
        econ_df.set_index('timestamp', inplace=True)
        
        # Create economic momentum features
        for col in econ_df.columns:
            if not col.endswith('_surprise') and not col.endswith('_impact'):
                econ_df[f'{col}_change'] = econ_df[col].pct_change()
                econ_df[f'{col}_ma'] = econ_df[col].rolling(5).mean()
        
        return econ_df.ffill().fillna(0)

class LSTMPredictor:
    """Advanced LSTM Neural Network for Price Prediction"""
    
    def __init__(self, sequence_length: int = 60, features: int = 50):
        self.sequence_length = sequence_length
        self.features = features
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def build_model(self) -> Optional[Any]:
        """Build LSTM model architecture"""
        if not TENSORFLOW_AVAILABLE:
            logger.warning("TensorFlow not available, using fallback model")
            return None
            
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=(self.sequence_length, self.features)),
            Dropout(0.2),
            BatchNormalization(),
            
            LSTM(64, return_sequences=True),
            Dropout(0.2),
            BatchNormalization(),
            
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            
            Dense(16, activation='relu'),
            Dropout(0.1),
            Dense(1, activation='linear')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def prepare_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences for LSTM training"""
        X, y = [], []
        for i in range(self.sequence_length, len(data)):
            X.append(data[i-self.sequence_length:i])
            y.append(data[i, 0])  # Predict close price
        return np.array(X), np.array(y)
    
    def train(self, features: pd.DataFrame, target_col: str = 'close') -> Dict[str, float]:
        """Train LSTM model"""
        try:
            # Prepare data
            data = features.select_dtypes(include=[np.number]).values
            data = self.scaler.fit_transform(data)
            
            X, y = self.prepare_sequences(data)
            
            if len(X) < 100:  # Minimum data requirement
                logger.warning("Insufficient data for LSTM training")
                return {'error': 'insufficient_data'}
            
            # Build model
            self.model = self.build_model()
            if self.model is None:
                return {'error': 'model_build_failed'}
            
            # Train model
            callbacks = [
                EarlyStopping(patience=10, restore_best_weights=True),
                ReduceLROnPlateau(factor=0.5, patience=5)
            ]
            
            history = self.model.fit(
                X, y,
                epochs=100,
                batch_size=32,
                validation_split=0.2,
                callbacks=callbacks,
                verbose=0
            )
            
            self.is_trained = True
            
            return {
                'final_loss': history.history['loss'][-1],
                'final_val_loss': history.history['val_loss'][-1],
                'epochs_trained': len(history.history['loss'])
            }
            
        except Exception as e:
            logger.error(f"LSTM training error: {e}")
            return {'error': str(e)}
    
    def predict(self, features: pd.DataFrame) -> Tuple[float, float]:
        """Make prediction with confidence"""
        if not self.is_trained or self.model is None:
            return 0.0, 0.0
        try:
        
            # Prepare data
            data = features.select_dtypes(include=[np.number]).values
            data = self.scaler.transform(data)
            
            if len(data) < self.sequence_length:
                return 0.0, 0.0
            
            # Get last sequence
            X = data[-self.sequence_length:].reshape(1, self.sequence_length, -1)
            
            # Make prediction
            prediction = self.model.predict(X, verbose=0)[0][0]
            
            # Calculate confidence (simplified)
            confidence = min(0.95, max(0.1, 1.0 - abs(prediction) * 0.1))
            
            return float(prediction), float(confidence)
            
        except Exception as e:
            logger.error(f"LSTM prediction error: {e}")
            return 0.0, 0.0

class EconomicDataFusion:
    """Economic Data Integration and Fusion Engine"""
    
    def __init__(self):
        self.economic_cache = {}
        self.impact_weights = {
            EconomicIndicator.INTEREST_RATES: 0.9,
            EconomicIndicator.INFLATION: 0.8,
            EconomicIndicator.GDP: 0.7,
            EconomicIndicator.EMPLOYMENT: 0.8,
            EconomicIndicator.CONSUMER_CONFIDENCE: 0.6,
            EconomicIndicator.MANUFACTURING_PMI: 0.7,
            EconomicIndicator.SERVICES_PMI: 0.6,
            EconomicIndicator.RETAIL_SALES: 0.5,
            EconomicIndicator.TRADE_BALANCE: 0.6,
            EconomicIndicator.CURRENCY_STRENGTH: 0.8
        }
    
    def calculate_economic_sentiment(self, economic_data: List[EconomicData]) -> float:
        """Calculate overall economic sentiment score"""
        if not economic_data:
            return 0.5  # Neutral
        
        weighted_scores = []
        for data in economic_data:
            # Calculate individual indicator sentiment
            surprise = data.surprise_factor()
            impact_weight = self.impact_weights.get(data.indicator, 0.5)
            
            # Positive surprise = bullish, negative = bearish
            if data.forecast_value is not None:
                sentiment = 0.5 + (data.value - data.forecast_value) / max(abs(data.forecast_value), 0.01) * 0.3
            else:
                sentiment = 0.5  # Neutral if no forecast
            
            weighted_scores.append(sentiment * impact_weight)
        
        return np.clip(np.mean(weighted_scores), 0.0, 1.0)
    
    def get_economic_momentum(self, economic_data: List[EconomicData], lookback_days: int = 30) -> Dict[str, float]:
        """Calculate economic momentum indicators"""
        recent_cutoff = datetime.now() - timedelta(days=lookback_days)
        recent_data = [ed for ed in economic_data if ed.timestamp >= recent_cutoff]
        
        if not recent_data:
            return {'momentum': 0.0, 'acceleration': 0.0, 'volatility': 0.0}
        
        # Group by indicator
        indicator_trends = {}
        for indicator in EconomicIndicator:
            indicator_data = [ed for ed in recent_data if ed.indicator == indicator]
            if len(indicator_data) >= 2:
                values = [ed.value for ed in sorted(indicator_data, key=lambda x: x.timestamp)]
                momentum = (values[-1] - values[0]) / max(abs(values[0]), 0.01)
                indicator_trends[indicator.value] = momentum
        
        overall_momentum = np.mean(list(indicator_trends.values())) if indicator_trends else 0.0
        momentum_volatility = np.std(list(indicator_trends.values())) if len(indicator_trends) > 1 else 0.0
        
        return {
            'momentum': overall_momentum,
            'acceleration': overall_momentum * 2,  # Simplified acceleration
            'volatility': momentum_volatility
        }

class EnsembleIntelligence:
    """Ensemble Learning System for Model Combination"""
    
    def __init__(self):
        self.models = {}
        self.model_weights = {}
        self.performance_history = {}
        
    def add_model(self, name: str, model: Any, weight: float = 1.0):
        """Add model to ensemble"""
        self.models[name] = model
        self.model_weights[name] = weight
        self.performance_history[name] = []
    
    def update_model_performance(self, name: str, accuracy: float):
        """Update model performance tracking"""
        if name in self.performance_history:
            self.performance_history[name].append(accuracy)
            # Keep only last 100 performances
            self.performance_history[name] = self.performance_history[name][-100:]
            
            # Update weight based on recent performance
            recent_performance = np.mean(self.performance_history[name][-10:])
            self.model_weights[name] = max(0.1, min(2.0, recent_performance))
    
    def ensemble_predict(self, features: pd.DataFrame) -> Tuple[float, float]:
        """Make ensemble prediction"""
        predictions = []
        confidences = []
        weights = []
        
        for name, model in self.models.items():
            try:
                if hasattr(model, 'predict'):
                    if hasattr(model, 'predict_proba'):
                        pred = model.predict(features.select_dtypes(include=[np.number]).values[-1:])
                        conf = 0.8  # Default confidence for sklearn models
                    else:
                        pred, conf = model.predict(features)
                    
                    predictions.append(pred)
                    confidences.append(conf)
                    weights.append(self.model_weights.get(name, 1.0))
            except Exception as e:
                logger.warning(f"Model {name} prediction failed: {e}")
                continue
        
        if not predictions:
            return 0.0, 0.0
        
        # Weighted ensemble prediction
        weights = np.array(weights)
        weights = weights / np.sum(weights)  # Normalize weights
        
        ensemble_prediction = np.average(predictions, weights=weights)
        ensemble_confidence = np.average(confidences, weights=weights)
        
        return float(ensemble_prediction), float(ensemble_confidence)

class AIMLCortex:
    """Main AI/ML Cortex System"""
    
    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.lstm_predictor = LSTMPredictor()
        self.economic_fusion = EconomicDataFusion()
        self.ensemble = EnsembleIntelligence()
        self.models_initialized = False
        self.prediction_cache = {}
        
    def initialize_models(self):
        """Initialize all ML models"""
        try:
            # Add traditional ML models to ensemble
            self.ensemble.add_model('random_forest', RandomForestRegressor(n_estimators=100, random_state=42))
            self.ensemble.add_model('gradient_boost', GradientBoostingRegressor(n_estimators=100, random_state=42))
            self.ensemble.add_model('neural_network', MLPRegressor(hidden_layer_sizes=(100, 50), random_state=42))
            
            # Add LSTM if available
            if TENSORFLOW_AVAILABLE:
                self.ensemble.add_model('lstm', self.lstm_predictor, weight=1.5)
            
            self.models_initialized = True
            logger.info("AI/ML Cortex models initialized successfully")
            
        except Exception as e:
            logger.error(f"Model initialization error: {e}")
    
    def train_models(self, price_data: pd.DataFrame, economic_data: List[EconomicData] = None) -> Dict[str, Any]:
        """Train all models with provided data"""
        if not self.models_initialized:
            try:
                self.initialize_models()

                # Engineer features
                features = self.feature_engineer.engineer_price_features(price_data)

                if economic_data:
                    econ_features = self.feature_engineer.engineer_economic_features(economic_data)
                    if not econ_features.empty:
                        features = features.join(econ_features, how='left').ffill()

                # Prepare target variable (next period return)
                target = features['close'].pct_change().shift(-1).fillna(0)

                # Split data for training
                split_idx = int(len(features) * 0.8)
                X_train, X_test = features.iloc[:split_idx], features.iloc[split_idx:]
                y_train, y_test = target.iloc[:split_idx], target.iloc[split_idx:]

                training_results = {}

                # Train LSTM
                if TENSORFLOW_AVAILABLE:
                    lstm_results = self.lstm_predictor.train(X_train)
                    training_results['lstm'] = lstm_results

                # Train traditional ML models
                for name, model in self.ensemble.models.items():
                    if name != 'lstm':
                        try:
                            X_train_numeric = X_train.select_dtypes(include=[np.number]).fillna(0)
                            X_test_numeric = X_test.select_dtypes(include=[np.number]).fillna(0)

                            model.fit(X_train_numeric, y_train)

                            # Evaluate model
                            predictions = model.predict(X_test_numeric)
                            mse = mean_squared_error(y_test, predictions)
                            mae = mean_absolute_error(y_test, predictions)
                            r2 = r2_score(y_test, predictions)

                            training_results[name] = {
                                'mse': mse,
                                'mae': mae,
                                'r2': r2
                            }

                            # Update ensemble weights based on performance
                            self.ensemble.update_model_performance(name, max(0, r2))

                        except Exception as e:
                            logger.error(f"Training error for {name}: {e}")
                            training_results[name] = {'error': str(e)}

                return training_results

            except Exception as e:
                logger.error(f"Training process error: {e}")
                return {'error': str(e)}

    def predict(self, price_data: pd.DataFrame, economic_data: List[EconomicData] = None, 
                horizon: PredictionHorizon = PredictionHorizon.SHORT) -> ModelPrediction:
        """Generate AI/ML prediction"""
        try:
            # Engineer features
            features = self.feature_engineer.engineer_price_features(price_data)
            
            if economic_data:
                econ_features = self.feature_engineer.engineer_economic_features(economic_data)
                if not econ_features.empty:
                    features = features.join(econ_features, how='left').ffill()
            
            # Get ensemble prediction
            prediction, confidence = self.ensemble.ensemble_predict(features)
            
            # Calculate uncertainty bounds
            volatility = features['close'].pct_change().rolling(20).std().iloc[-1]
            uncertainty = volatility * (1 - confidence) * 2
            lower_bound = prediction - uncertainty
            upper_bound = prediction + uncertainty
            
            # Calculate economic sentiment impact
            economic_sentiment = 0.5
            if economic_data:
                economic_sentiment = self.economic_fusion.calculate_economic_sentiment(economic_data)
            
            # Adjust prediction based on economic sentiment
            sentiment_adjustment = (economic_sentiment - 0.5) * 0.1
            adjusted_prediction = prediction + sentiment_adjustment
            
            return ModelPrediction(
                model_type=ModelType.ENSEMBLE,
                prediction=adjusted_prediction,
                confidence=confidence,
                horizon=horizon,
                timestamp=datetime.now(),
                features_used=list(features.columns),
                model_accuracy=confidence,
                uncertainty_bounds=(lower_bound, upper_bound)
            )
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return ModelPrediction(
                model_type=ModelType.ENSEMBLE,
                prediction=0.0,
                confidence=0.0,
                horizon=horizon,
                timestamp=datetime.now(),
                features_used=[],
                model_accuracy=0.0,
                uncertainty_bounds=(0.0, 0.0)
            )
    
    def get_model_insights(self) -> Dict[str, Any]:
        """Get insights about model performance and behavior"""
        insights = {
            'ensemble_weights': self.ensemble.model_weights.copy(),
            'model_performance': {},
            'feature_importance': self.feature_engineer.feature_importance.copy(),
            'models_available': list(self.ensemble.models.keys()),
            'tensorflow_available': TENSORFLOW_AVAILABLE
        }
        
        # Add performance history
        for name, history in self.ensemble.performance_history.items():
            if history:
                insights['model_performance'][name] = {
                    'recent_accuracy': np.mean(history[-10:]) if len(history) >= 10 else np.mean(history),
                    'stability': 1.0 - np.std(history[-20:]) if len(history) >= 20 else 1.0,
                    'trend': (history[-1] - history[0]) / len(history) if len(history) > 1 else 0.0
                }
        
        return insights
    
    def adaptive_model_selection(self, market_conditions: Dict[str, float]) -> str:
        """Adaptively select best model based on market conditions"""
        volatility = market_conditions.get('volatility', 0.5)
        trend_strength = market_conditions.get('trend_strength', 0.5)
        volume_profile = market_conditions.get('volume_profile', 0.5)
        
        # High volatility favors ensemble approaches
        if volatility > 0.7:
            return 'ensemble'
        # Strong trends favor LSTM
        elif trend_strength > 0.6 and TENSORFLOW_AVAILABLE:
            return 'lstm'
        # Stable conditions favor traditional ML
        elif volatility < 0.3:
            return 'random_forest'
        else:
            return 'ensemble'

# Example usage and testing
if __name__ == "__main__":
    # Initialize AI/ML Cortex
    cortex = AIMLCortex()
    
    # Generate sample data for testing
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='1H')
    np.random.seed(42)
    
    sample_data = pd.DataFrame({
        'open': np.random.randn(len(dates)).cumsum() + 100,
        'high': np.random.randn(len(dates)).cumsum() + 102,
        'low': np.random.randn(len(dates)).cumsum() + 98,
        'close': np.random.randn(len(dates)).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, len(dates))
    }, index=dates)
    
    sample_data['high'] = np.maximum(sample_data[['open', 'close']].max(axis=1), sample_data['high'])
    sample_data['low'] = np.minimum(sample_data[['open', 'close']].min(axis=1), sample_data['low'])
    
    # Sample economic data
    economic_data = [
        EconomicData(
            indicator=EconomicIndicator.INTEREST_RATES,
            value=5.25,
            timestamp=datetime.now(),
            country='USD',
            impact_level='HIGH',
            forecast_value=5.0
        ),
        EconomicData(
            indicator=EconomicIndicator.INFLATION,
            value=3.2,
            timestamp=datetime.now(),
            country='USD',
            impact_level='HIGH',
            forecast_value=3.1
        )
    ]
    
    logger.info("AI/ML Cortex Testing")
    print("=" * 50)
    
    # Initialize and train models
    logger.info("Initializing models...")
    cortex.initialize_models()
    
    logger.info("Training models...")
    training_results = cortex.train_models(sample_data, economic_data)
    logger.info(f"Training Results: {training_results}")
    
    # Make prediction
    logger.info("\nMaking prediction...")
    prediction = cortex.predict(sample_data, economic_data, PredictionHorizon.SHORT)
    logger.info(f"Prediction: {prediction.prediction:.6f}")
    logger.info(f"Confidence: {prediction.confidence:.3f}")
    logger.info(f"Uncertainty Bounds: {prediction.uncertainty_bounds}")
    
    # Get model insights
    logger.info("\nModel Insights:")
    insights = cortex.get_model_insights()
    for key, value in insights.items():
        logger.info(f"{key}: {value}")
    
    logger.info("\nAI/ML Cortex test completed successfully!")
