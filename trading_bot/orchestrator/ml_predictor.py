"""
Machine Learning Predictor for Opportunity Success Rates
Uses ensemble models to predict which opportunities will be profitable
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
import joblib
from collections import deque
import asyncio
import numpy
import pandas

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    """Result of ML prediction"""
    opportunity_id: str
    success_probability: float
    expected_return: float
    confidence_interval: Tuple[float, float]
    risk_score: float
    sharpe_ratio: float
    feature_importance: Dict[str, float]
    metadata: Dict[str, Any]

class OpportunityPredictor:
    """
    Predicts success probability and expected returns for trading opportunities
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Model parameters
        self.lookback_window = self.config.get('lookback_window', 100)
        self.min_samples = self.config.get('min_samples', 1000)
        self.retrain_frequency = self.config.get('retrain_frequency', 1000)
        
        # Feature engineering
        self.feature_extractor = MLFeatureExtractor()
        self.scaler = StandardScaler()
        
        # Models
        self.models = {}
        self._initialize_models()
        
        # Training data
        self.training_data = deque(maxlen=10000)
        self.prediction_cache = {}
        
        # Performance tracking
        self.prediction_history = deque(maxlen=1000)
        self.model_performance = {}
        
        logger.info("Opportunity Predictor initialized")
    
    def _initialize_models(self):
        """Initialize ML models"""
        # Success classifier
        self.models['success_classifier'] = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        
        # Return predictor
        self.models['return_predictor'] = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        # Risk predictor
        self.models['risk_predictor'] = MLPRegressor(
            hidden_layer_sizes=(100, 50, 25),
            activation='relu',
            solver='adam',
            random_state=42
        )
        
        # Load pre-trained models if available
        self._load_models()
    
    async def predict_batch(self, opportunities: List[Dict]) -> List[PredictionResult]:
        """
        Predict success for a batch of opportunities
        """
        predictions = []
        
        for opp in opportunities:
            # Check cache
            opp_id = opp.get('unique_id', str(datetime.now().timestamp()))
            
            if opp_id in self.prediction_cache:
                predictions.append(self.prediction_cache[opp_id])
                continue
            
            # Extract features
            features = self.feature_extractor.extract_features(opp)
            
            # Make prediction
            prediction = await self._predict_single(opp_id, features, opp)
            
            # Cache result
            self.prediction_cache[opp_id] = prediction
            predictions.append(prediction)
        
        return predictions
    
    async def _predict_single(self, opp_id: str, features: np.ndarray, 
                             opp_data: Dict) -> PredictionResult:
        """
        Make prediction for single opportunity
        """
        # Scale features
        if len(self.training_data) > self.min_samples:
            features_scaled = self.scaler.transform(features.reshape(1, -1))
        else:
            features_scaled = features.reshape(1, -1)
        
        # Get predictions from each model
        if self._models_trained():
            success_prob = self.models['success_classifier'].predict_proba(features_scaled)[0, 1]
            expected_return = self.models['return_predictor'].predict(features_scaled)[0]
            risk_score = self.models['risk_predictor'].predict(features_scaled)[0]
        else:
            # Use heuristic predictions if models not trained
            success_prob = self._heuristic_success_probability(opp_data)
            expected_return = self._heuristic_expected_return(opp_data)
            risk_score = self._heuristic_risk_score(opp_data)
        
        # Calculate Sharpe ratio
        sharpe_ratio = expected_return / risk_score if risk_score > 0 else 0
        
        # Calculate confidence interval
        confidence_interval = self._calculate_confidence_interval(
            expected_return, risk_score
        )
        
        # Get feature importance
        feature_importance = self._get_feature_importance(features)
        
        return PredictionResult(
            opportunity_id=opp_id,
            success_probability=success_prob,
            expected_return=expected_return,
            confidence_interval=confidence_interval,
            risk_score=risk_score,
            sharpe_ratio=sharpe_ratio,
            feature_importance=feature_importance,
            metadata={
                'opportunity_type': opp_data.get('type'),
                'model_confidence': self._calculate_model_confidence()
            }
        )
    
    def _models_trained(self) -> bool:
        """Check if models are trained"""
        try:
            # Check if models have been fitted
            return hasattr(self.models['success_classifier'], 'classes_')
        except Exception:
            return False
    
    def _heuristic_success_probability(self, opp_data: Dict) -> float:
        """
        Heuristic success probability when ML models not available
        """
        base_prob = 0.5
        
        # Adjust based on opportunity type
        type_adjustments = {
            'ARBITRAGE': 0.3,
            'MOMENTUM': 0.1,
            'NEWS': 0.05,
            'CORRELATION': 0.15,
            'MARKET_MAKING': 0.2
        }
        
        adjustment = type_adjustments.get(opp_data.get('type'), 0)
        
        # Adjust based on confidence
        confidence = opp_data.get('confidence', 0.5)
        
        return min(0.95, base_prob + adjustment + confidence * 0.2)
    
    def _heuristic_expected_return(self, opp_data: Dict) -> float:
        """
        Heuristic expected return when ML models not available
        """
        # Use opportunity's own estimate if available
        if 'expected_return' in opp_data:
            return opp_data['expected_return']
        
        # Otherwise estimate based on type
        type_returns = {
            'ARBITRAGE': 0.002,
            'MOMENTUM': 0.03,
            'NEWS': 0.02,
            'CORRELATION': 0.01,
            'MARKET_MAKING': 0.001
        }
        
        return type_returns.get(opp_data.get('type'), 0.01)
    
    def _heuristic_risk_score(self, opp_data: Dict) -> float:
        """
        Heuristic risk score when ML models not available
        """
        if 'risk' in opp_data:
            return opp_data['risk']
        
        # Estimate based on type
        type_risks = {
            'ARBITRAGE': 0.1,
            'MOMENTUM': 0.5,
            'NEWS': 0.4,
            'CORRELATION': 0.3,
            'MARKET_MAKING': 0.2
        }
        
        return type_risks.get(opp_data.get('type'), 0.5)
    
    def _calculate_confidence_interval(self, expected_return: float, 
                                      risk_score: float) -> Tuple[float, float]:
        """
        Calculate confidence interval for expected return
        """
        # Simple confidence interval based on risk
        std_dev = risk_score * expected_return
        
        lower = expected_return - 1.96 * std_dev
        upper = expected_return + 1.96 * std_dev
        
        return (lower, upper)
    
    def _get_feature_importance(self, features: np.ndarray) -> Dict[str, float]:
        """
        Get feature importance for prediction
        """
        if not self._models_trained():
            return {}
        try:
        
            # Get feature importance from Random Forest
            importance = self.models['success_classifier'].feature_importances_
            
            # Map to feature names
            feature_names = self.feature_extractor.get_feature_names()
            
            importance_dict = {}
            for name, imp in zip(feature_names, importance):
                importance_dict[name] = float(imp)
            
            return importance_dict
        except Exception:
            return {}
    
    def _calculate_model_confidence(self) -> float:
        """
        Calculate confidence in model predictions
        """
        if not self._models_trained():
            return 0.3  # Low confidence for heuristic predictions
        
        # Base confidence on training data size and performance
        data_confidence = min(1.0, len(self.training_data) / self.min_samples)
        
        # Get average model performance
        perf_confidence = self._get_average_model_performance()
        
        return data_confidence * 0.5 + perf_confidence * 0.5
    
    def _get_average_model_performance(self) -> float:
        """
        Get average performance across models
        """
        if not self.model_performance:
            return 0.5
        
        performances = []
        for model_name, metrics in self.model_performance.items():
            if 'accuracy' in metrics:
                performances.append(metrics['accuracy'])
        
        return np.mean(performances) if performances else 0.5
    
    async def train_models(self, training_data: List[Dict]):
        """
        Train or retrain models with new data
        """
        logger.info("Training ML models...")
        
        # Add to training data
        self.training_data.extend(training_data)
        
        if len(self.training_data) < self.min_samples:
            logger.warning(f"Insufficient training data: {len(self.training_data)} < {self.min_samples}")
            return
        
        # Prepare training dataset
        X, y_success, y_return, y_risk = self._prepare_training_data()
        
        # Split data
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_success_train, y_success_test = y_success[:split_idx], y_success[split_idx:]
        y_return_train, y_return_test = y_return[:split_idx], y_return[split_idx:]
        y_risk_train, y_risk_test = y_risk[:split_idx], y_risk[split_idx:]
        
        # Fit scaler
        self.scaler.fit(X_train)
        X_train_scaled = self.scaler.transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train success classifier
        self.models['success_classifier'].fit(X_train_scaled, y_success_train)
        success_accuracy = self.models['success_classifier'].score(X_test_scaled, y_success_test)
        
        # Train return predictor
        self.models['return_predictor'].fit(X_train_scaled, y_return_train)
        return_r2 = self.models['return_predictor'].score(X_test_scaled, y_return_test)
        
        # Train risk predictor
        self.models['risk_predictor'].fit(X_train_scaled, y_risk_train)
        risk_r2 = self.models['risk_predictor'].score(X_test_scaled, y_risk_test)
        
        # Update performance metrics
        self.model_performance = {
            'success_classifier': {'accuracy': success_accuracy},
            'return_predictor': {'r2': return_r2},
            'risk_predictor': {'r2': risk_r2}
        }
        
        logger.info(f"Models trained - Success accuracy: {success_accuracy:.3f}, "
                   f"Return R2: {return_r2:.3f}, Risk R2: {risk_r2:.3f}")
        
        # Save models
        self._save_models()
    
    def _prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare training data for models
        """
        X = []
        y_success = []
        y_return = []
        y_risk = []
        
        for sample in self.training_data:
            # Extract features
            features = self.feature_extractor.extract_features(sample['opportunity'])
            X.append(features)
            
            # Extract labels
            y_success.append(1 if sample['outcome']['success'] else 0)
            y_return.append(sample['outcome']['return'])
            y_risk.append(sample['outcome']['risk_realized'])
        
        return np.array(X), np.array(y_success), np.array(y_return), np.array(y_risk)
    
    def _save_models(self):
        """Save trained models to disk"""
        try:
            for name, model in self.models.items():
                joblib.dump(model, f'models/{name}.pkl')
            joblib.dump(self.scaler, 'models/scaler.pkl')
            logger.info("Models saved successfully")
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def _load_models(self):
        """Load pre-trained models from disk"""
        try:
            for name in self.models.keys():
                self.models[name] = joblib.load(f'models/{name}.pkl')
            self.scaler = joblib.load('models/scaler.pkl')
            logger.info("Models loaded successfully")
        except Exception as e:
            logger.info(f"No pre-trained models found: {e}")


class MLFeatureExtractor:
    """
    Extracts features from opportunities for ML models
    """
    
    def __init__(self):
        self.feature_names = [
            'type_encoded', 'confidence', 'volatility', 'volume',
            'spread', 'momentum', 'risk_score', 'time_of_day',
            'day_of_week', 'market_cap', 'sector_encoded',
            'correlation', 'rsi', 'macd', 'volume_ratio',
            'price_position', 'trend_strength', 'news_sentiment',
            'options_flow', 'institutional_flow'
        ]
    
    def extract_features(self, opportunity: Dict) -> np.ndarray:
        """
        Extract feature vector from opportunity
        """
        features = []
        
        # Opportunity type encoding
        type_encoding = self._encode_opportunity_type(opportunity.get('type'))
        features.append(type_encoding)
        
        # Basic metrics
        features.append(opportunity.get('confidence', 0.5))
        features.append(opportunity.get('volatility', 0.2))
        features.append(opportunity.get('volume', 100000) / 1000000)  # Normalize
        features.append(opportunity.get('spread', 0.001))
        features.append(opportunity.get('momentum', 0))
        features.append(opportunity.get('risk_score', 0.5))
        
        # Time features
        now = datetime.now()
        features.append(now.hour / 24)  # Normalize
        features.append(now.weekday() / 7)  # Normalize
        
        # Market features
        features.append(opportunity.get('market_cap', 1000000) / 1000000000)  # Normalize to billions
        features.append(self._encode_sector(opportunity.get('sector')))
        
        # Technical indicators
        features.append(opportunity.get('correlation', 0))
        features.append(opportunity.get('rsi', 50) / 100)  # Normalize
        features.append(opportunity.get('macd', 0))
        features.append(opportunity.get('volume_ratio', 1))
        features.append(opportunity.get('price_position', 0.5))
        features.append(opportunity.get('trend_strength', 0))
        
        # Sentiment and flow
        features.append(opportunity.get('news_sentiment', 0))
        features.append(opportunity.get('options_flow', 0))
        features.append(opportunity.get('institutional_flow', 0))
        
        return np.array(features)
    
    def _encode_opportunity_type(self, opp_type: str) -> float:
        """Encode opportunity type as numeric"""
        type_map = {
            'ARBITRAGE': 0.1,
            'MOMENTUM': 0.2,
            'NEWS': 0.3,
            'CORRELATION': 0.4,
            'MARKET_MAKING': 0.5,
            'VOLATILITY': 0.6,
            'FLOW': 0.7,
            'BREAKOUT': 0.8
        }
        return type_map.get(opp_type, 0.5)
    
    def _encode_sector(self, sector: str) -> float:
        """Encode sector as numeric"""
        sector_map = {
            'TECH': 0.1,
            'FINANCE': 0.2,
            'HEALTHCARE': 0.3,
            'ENERGY': 0.4,
            'CONSUMER': 0.5,
            'INDUSTRIAL': 0.6,
            'CRYPTO': 0.7,
            'FOREX': 0.8,
            'COMMODITY': 0.9
        }
        return sector_map.get(sector, 0.5)
    
    def get_feature_names(self) -> List[str]:
        """Get feature names"""
        return self.feature_names


class SuccessPredictor:
    """
    Specialized predictor for success probability
    """
    
    def __init__(self):
        self.ensemble = ModelEnsemble()
        self.calibrator = ProbabilityCalibrator()
    
    def predict_success(self, opportunity: Dict) -> float:
        """
        Predict success probability with calibration
        """
        # Get ensemble prediction
        raw_probability = self.ensemble.predict_proba(opportunity)
        
        # Calibrate probability
        calibrated = self.calibrator.calibrate(raw_probability, opportunity)
        
        return calibrated


class ModelEnsemble:
    """
    Ensemble of multiple models for robust predictions
    """
    
    def __init__(self):
        self.models = []
        self.weights = []
        self._initialize_ensemble()
    
    def _initialize_ensemble(self):
        """Initialize ensemble models"""
        # Add different model types
        self.models.append(RandomForestClassifier(n_estimators=50))
        self.weights.append(0.3)
        
        self.models.append(GradientBoostingRegressor(n_estimators=50))
        self.weights.append(0.3)
        
        self.models.append(MLPRegressor(hidden_layer_sizes=(50, 25)))
        self.weights.append(0.4)
    
    def predict_proba(self, opportunity: Dict) -> float:
        """
        Get weighted ensemble prediction
        """
        predictions = []
        
        for model, weight in zip(self.models, self.weights):
            try:
                # Get prediction from model
                pred = 0.5  # Placeholder - would use actual model prediction
                predictions.append(pred * weight)
            except Exception:
                continue
        
        return sum(predictions) if predictions else 0.5


class ProbabilityCalibrator:
    """
    Calibrates predicted probabilities to match actual outcomes
    """
    
    def __init__(self):
        self.calibration_data = deque(maxlen=1000)
        self.calibration_curve = None
    
    def calibrate(self, raw_probability: float, opportunity: Dict) -> float:
        """
        Calibrate probability based on historical performance
        """
        if not self.calibration_curve:
            return raw_probability
        
        # Apply calibration curve
        calibrated = self._apply_calibration(raw_probability)
        
        # Adjust for opportunity type
        type_adjustment = self._get_type_adjustment(opportunity.get('type'))
        
        final = calibrated * type_adjustment
        
        return min(0.99, max(0.01, final))
    
    def _apply_calibration(self, prob: float) -> float:
        """Apply calibration curve"""
        # Placeholder - would use isotonic regression or similar
        return prob
    
    def _get_type_adjustment(self, opp_type: str) -> float:
        """Get adjustment factor for opportunity type"""
        adjustments = {
            'ARBITRAGE': 1.2,
            'MOMENTUM': 0.9,
            'NEWS': 0.95,
            'CORRELATION': 1.1
        }
        return adjustments.get(opp_type, 1.0)
