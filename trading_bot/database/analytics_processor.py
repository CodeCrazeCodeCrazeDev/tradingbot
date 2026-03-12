"""
Real-Time Analytics Processor
Provides advanced analytics and predictive capabilities for trading
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import asyncio
from dataclasses import dataclass
import logging
from collections import deque
import torch
from sklearn.preprocessing import StandardScaler
from concurrent.futures import ProcessPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class AnalyticsResult:
    """Analytics result with predictive signals"""
    timestamp: datetime
    symbol: str
    predictions: Dict[str, float]
    confidence: float
    features: Dict[str, float]
    market_regime: str
    signals: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class AnalyticsProcessor:
    """
    Real-time analytics processor with predictive capabilities
    Features:
    - Feature engineering
    - Market regime detection
    - ML-based predictions
    - Signal aggregation
    - Performance optimization
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize processors
        self.feature_processor = FeatureProcessor(config)
        self.regime_detector = MarketRegimeDetector(config)
        self.predictor = PredictiveEngine(config)
        
        # Data buffers
        self.feature_buffer: Dict[str, deque] = {}
        self.prediction_buffer: Dict[str, deque] = {}
        
        # Process pool for parallel processing
        self.process_pool = ProcessPoolExecutor(
            max_workers=config.get('analytics_workers', 4)
        )
        
        # Performance tracking
        self.processing_times: deque = deque(maxlen=1000)
        self.prediction_accuracy: Dict[str, deque] = {}
        
        logger.info("Analytics processor initialized")
    
    async def process_data(self, 
                          symbol: str, 
                          market_data: Dict[str, Any],
                          order_flow: Dict[str, Any],
                          microstructure: Dict[str, Any]) -> AnalyticsResult:
        """Process market data and generate analytics"""
        start_time = datetime.now()
        
        try:
            # Extract features in parallel
            features = await self._extract_features(
                symbol, market_data, order_flow, microstructure
            )
            
            # Detect market regime
            regime = await self._detect_regime(symbol, features)
            
            # Generate predictions
            predictions = await self._generate_predictions(symbol, features, regime)
            
            # Aggregate signals
            signals = await self._aggregate_signals(
                symbol, predictions, features, regime
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(predictions, signals)
            
            result = AnalyticsResult(
                timestamp=datetime.now(),
                symbol=symbol,
                predictions=predictions,
                confidence=confidence,
                features=features,
                market_regime=regime,
                signals=signals,
                metadata={
                    'processing_time': (datetime.now() - start_time).total_seconds(),
                    'feature_count': len(features),
                    'signal_count': len(signals)
                }
            )
            
            # Update performance metrics
            self.processing_times.append(result.metadata['processing_time'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing analytics for {symbol}: {e}")
            raise
    
    async def _extract_features(self,
                              symbol: str,
                              market_data: Dict[str, Any],
                              order_flow: Dict[str, Any],
                              microstructure: Dict[str, Any]) -> Dict[str, float]:
        """Extract features from multiple data sources"""
        # Run feature extraction in process pool
        loop = asyncio.get_event_loop()
        features = await loop.run_in_executor(
            self.process_pool,
            self.feature_processor.extract_features,
            market_data,
            order_flow,
            microstructure
        )
        
        # Store in buffer
        if symbol not in self.feature_buffer:
            self.feature_buffer[symbol] = deque(maxlen=1000)
        self.feature_buffer[symbol].append(features)
        
        return features
    
    async def _detect_regime(self,
                           symbol: str,
                           features: Dict[str, float]) -> str:
        """Detect current market regime"""
        regime = await self.regime_detector.detect_regime(features)
        return regime
    
    async def _generate_predictions(self,
                                  symbol: str,
                                  features: Dict[str, float],
                                  regime: str) -> Dict[str, float]:
        """Generate predictions using ML models"""
        predictions = await self.predictor.predict(features, regime)
        
        # Store predictions
        if symbol not in self.prediction_buffer:
            self.prediction_buffer[symbol] = deque(maxlen=1000)
        self.prediction_buffer[symbol].append(predictions)
        
        return predictions
    
    async def _aggregate_signals(self,
                               symbol: str,
                               predictions: Dict[str, float],
                               features: Dict[str, float],
                               regime: str) -> List[Dict[str, Any]]:
        """Aggregate signals from different sources"""
        signals = []
        
        # Price direction signals
        if predictions.get('price_up_probability', 0) > 0.7:
            signals.append({
                'type': 'price_direction',
                'direction': 'up',
                'probability': predictions['price_up_probability'],
                'timeframe': '5m'
            })
        elif predictions.get('price_down_probability', 0) > 0.7:
            signals.append({
                'type': 'price_direction',
                'direction': 'down',
                'probability': predictions['price_down_probability'],
                'timeframe': '5m'
            })
        
        # Volatility signals
        vol_prediction = predictions.get('volatility_increase', 0)
        if vol_prediction > 0.8:
            signals.append({
                'type': 'volatility',
                'direction': 'increase',
                'probability': vol_prediction,
                'timeframe': '5m'
            })
        
        # Regime-based signals
        if regime == 'trending':
            trend_strength = features.get('trend_strength', 0)
            if trend_strength > 0.7:
                signals.append({
                    'type': 'trend',
                    'direction': 'with_trend',
                    'strength': trend_strength,
                    'timeframe': '15m'
                })
        
        return signals
    
    def _calculate_confidence(self,
                            predictions: Dict[str, float],
                            signals: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score"""
        if not signals:
            return 0.0
        
        # Average signal probabilities
        signal_probabilities = [
            s.get('probability', s.get('strength', 0))
            for s in signals
        ]
        
        # Weight by prediction consistency
        prediction_consistency = self._calculate_prediction_consistency(predictions)
        
        # Combine scores
        confidence = (np.mean(signal_probabilities) * 0.7 +
                     prediction_consistency * 0.3)
        
        return min(confidence, 1.0)
    
    def _calculate_prediction_consistency(self,
                                       predictions: Dict[str, float]) -> float:
        """Calculate prediction consistency score"""
        # Check for conflicting predictions
        up_prob = predictions.get('price_up_probability', 0)
        down_prob = predictions.get('price_down_probability', 0)
        
        # Higher score for clear directional bias
        direction_consistency = abs(up_prob - down_prob)
        
        # Check probability calibration
        probability_sum = up_prob + down_prob
        calibration_score = 1.0 - abs(1.0 - probability_sum)
        
        return (direction_consistency * 0.7 +
                calibration_score * 0.3)
    
    def get_analytics_metrics(self) -> Dict[str, Any]:
        """Get analytics performance metrics"""
        return {
            'avg_processing_time': np.mean(self.processing_times),
            'feature_extraction_time': self.feature_processor.get_metrics(),
            'prediction_time': self.predictor.get_metrics(),
            'memory_usage': self._get_memory_usage()
        }
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage statistics"""
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss / 1024 / 1024,  # MB
            'vms': memory_info.vms / 1024 / 1024,  # MB
            'shared': memory_info.shared / 1024 / 1024  # MB
        }

class FeatureProcessor:
    """Processes raw data into ML features"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scaler = StandardScaler()
        self.processing_times: deque = deque(maxlen=1000)
    
    def extract_features(self,
                        market_data: Dict[str, Any],
                        order_flow: Dict[str, Any],
                        microstructure: Dict[str, Any]) -> Dict[str, float]:
        """Extract features from raw data"""
        start_time = datetime.now()
        
        features = {}
        
        # Market data features
        if 'price' in market_data:
            features['price'] = market_data['price']
        if 'volume' in market_data:
            features['volume'] = market_data['volume']
        
        # Order flow features
        if 'imbalance_ratio' in order_flow:
            features['order_imbalance'] = order_flow['imbalance_ratio']
        if 'pressure_score' in order_flow:
            features['pressure'] = order_flow['pressure_score']
        
        # Microstructure features
        if 'liquidity_score' in microstructure:
            features['liquidity'] = microstructure['liquidity_score']
        
        # Calculate derived features
        features.update(self._calculate_derived_features(features))
        
        # Scale features
        scaled_features = self._scale_features(features)
        
        # Update metrics
        self.processing_times.append(
            (datetime.now() - start_time).total_seconds()
        )
        
        return scaled_features
    
    def _calculate_derived_features(self,
                                  features: Dict[str, float]) -> Dict[str, float]:
        """Calculate derived features"""
        derived = {}
        
        # Combine order flow and liquidity
        if 'order_imbalance' in features and 'liquidity' in features:
            derived['flow_impact'] = (
                features['order_imbalance'] * features['liquidity']
            )
        
        # Momentum features
        if 'pressure' in features:
            derived['momentum'] = np.tanh(features['pressure'])
        
        return derived
    
    def _scale_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Scale features to standard normal distribution"""
        feature_array = np.array(list(features.values())).reshape(1, -1)
        scaled = self.scaler.fit_transform(feature_array)
        
        return {
            key: scaled[0, i]
            for i, key in enumerate(features.keys())
        }
    
    def get_metrics(self) -> Dict[str, float]:
        """Get feature processing metrics"""
        return {
            'avg_processing_time': np.mean(self.processing_times),
            'feature_count': len(self.scaler.feature_names_in_)
            if hasattr(self.scaler, 'feature_names_in_') else 0
        }

class MarketRegimeDetector:
    """Detects current market regime"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.regime_history: deque = deque(maxlen=100)
    
    async def detect_regime(self, features: Dict[str, float]) -> str:
        """Detect current market regime"""
        # Simple regime detection based on features
        if 'momentum' in features and abs(features['momentum']) > 0.7:
            regime = 'trending'
        elif 'volatility' in features and features['volatility'] > 0.8:
            regime = 'volatile'
        else:
            regime = 'ranging'
        
        self.regime_history.append(regime)
        return regime
    
    def get_regime_stats(self) -> Dict[str, float]:
        """Get regime statistics"""
        if not self.regime_history:
            return {}
        
        regimes = list(self.regime_history)
        return {
            regime: regimes.count(regime) / len(regimes)
            for regime in set(regimes)
        }

class PredictiveEngine:
    """ML-based predictive engine"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models = self._initialize_models()
        self.prediction_times: deque = deque(maxlen=1000)
    
    def _initialize_models(self) -> Dict[str, Any]:
        """Initialize ML models"""
        return {
            'price_direction': torch.nn.Sequential(
                torch.nn.Linear(10, 64),
                torch.nn.ReLU(),
                torch.nn.Linear(64, 32),
                torch.nn.ReLU(),
                torch.nn.Linear(32, 2),
                torch.nn.Softmax(dim=1)
            ),
            'volatility': torch.nn.Sequential(
                torch.nn.Linear(10, 32),
                torch.nn.ReLU(),
                torch.nn.Linear(32, 1),
                torch.nn.Sigmoid()
            )
        }
    
    async def predict(self,
                     features: Dict[str, float],
                     regime: str) -> Dict[str, float]:
        """Generate predictions"""
        start_time = datetime.now()
        
        # Convert features to tensor
        feature_tensor = torch.tensor(
            list(features.values()),
            dtype=torch.float32
        ).reshape(1, -1)
        
        # Generate predictions
        with torch.no_grad():
            price_pred = self.models['price_direction'](feature_tensor)
            vol_pred = self.models['volatility'](feature_tensor)
        
        predictions = {
            'price_up_probability': float(price_pred[0, 0]),
            'price_down_probability': float(price_pred[0, 1]),
            'volatility_increase': float(vol_pred[0, 0])
        }
        
        # Adjust predictions based on regime
        predictions = self._adjust_predictions(predictions, regime)
        
        self.prediction_times.append(
            (datetime.now() - start_time).total_seconds()
        )
        
        return predictions
    
    def _adjust_predictions(self,
                          predictions: Dict[str, float],
                          regime: str) -> Dict[str, float]:
        """Adjust predictions based on market regime"""
        if regime == 'volatile':
            # Reduce confidence in price direction
            predictions['price_up_probability'] *= 0.8
            predictions['price_down_probability'] *= 0.8
            # Increase volatility prediction
            predictions['volatility_increase'] = max(
                predictions['volatility_increase'],
                0.7
            )
        elif regime == 'ranging':
            # Reduce all predictions
            for key in predictions:
                predictions[key] *= 0.9
        
        return predictions
    
    def get_metrics(self) -> Dict[str, float]:
        """Get prediction metrics"""
        return {
            'avg_prediction_time': np.mean(self.prediction_times),
            'model_count': len(self.models)
        }
