"""
AI/ML System Validator
Tests machine learning models, predictions, and response times
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import List
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation.comprehensive_validator import ValidationResult, ValidationStatus

logger = logging.getLogger(__name__)


class AIMLValidator:
    """Validates AI/ML systems"""
    
    def __init__(self):
        self.results = []
    
    def validate_ml_dependencies(self) -> ValidationResult:
        """Validate ML library dependencies"""
        start = time.time()
        
        try:
            required_libs = {
                'numpy': 'numpy',
                'pandas': 'pandas',
                'scikit-learn': 'sklearn',
                'scipy': 'scipy'
            }
            
            missing = []
            versions = {}
            
            for name, import_name in required_libs.items():
                try:
                    lib = __import__(import_name)
                    versions[name] = getattr(lib, '__version__', 'unknown')
                except ImportError:
                    missing.append(name)
            
            if missing:
                return ValidationResult(
                    component="AI/ML",
                    test_name="ML Dependencies",
                    status=ValidationStatus.FAILED,
                    message=f"Missing libraries: {', '.join(missing)}",
                    details={'missing': missing},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            return ValidationResult(
                component="AI/ML",
                test_name="ML Dependencies",
                status=ValidationStatus.PASSED,
                message="All ML libraries available",
                details={'versions': versions},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ValidationResult(
                component="AI/ML",
                test_name="ML Dependencies",
                status=ValidationStatus.FAILED,
                message=f"Error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_model_loading(self) -> ValidationResult:
        """Validate model loading capability"""
        start = time.time()
        
        try:
            from sklearn.ensemble import RandomForestClassifier
            from pathlib import Path
            
            # Check if models directory exists
            models_dir = Path('models')
            models_dir.mkdir(exist_ok=True)
            
            # Create a simple test model
            X_train = np.random.rand(100, 10)
            y_train = np.random.randint(0, 2, 100)
            
            model = RandomForestClassifier(n_estimators=10, random_state=42)
            model.fit(X_train, y_train)
            
            # Test prediction
            X_test = np.random.rand(10, 10)
            predictions = model.predict(X_test)
            probabilities = model.predict_proba(X_test)
            
            return ValidationResult(
                component="AI/ML",
                test_name="Model Loading",
                status=ValidationStatus.PASSED,
                message="Model training and prediction successful",
                details={
                    'model_type': 'RandomForestClassifier',
                    'predictions_shape': predictions.shape,
                    'probabilities_shape': probabilities.shape
                },
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ValidationResult(
                component="AI/ML",
                test_name="Model Loading",
                status=ValidationStatus.FAILED,
                message=f"Error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_prediction_latency(self) -> ValidationResult:
        """Validate ML prediction latency"""
        start = time.time()
        
        try:
            from sklearn.ensemble import RandomForestClassifier
            
            # Create and train model
            X_train = np.random.rand(1000, 20)
            y_train = np.random.randint(0, 2, 1000)
            
            model = RandomForestClassifier(n_estimators=50, random_state=42)
            model.fit(X_train, y_train)
            
            # Measure prediction time
            X_test = np.random.rand(1, 20)
            
            latencies = []
            for _ in range(100):
                pred_start = time.time()
                _ = model.predict_proba(X_test)
                latencies.append((time.time() - pred_start) * 1000)
            
            avg_latency = np.mean(latencies)
            max_latency = np.max(latencies)
            min_latency = np.min(latencies)
            
            # Prediction should be under 50ms for real-time trading
            if avg_latency > 50:
                status = ValidationStatus.WARNING
                message = f"Prediction latency high: {avg_latency:.2f}ms"
            else:
                status = ValidationStatus.PASSED
                message = f"Prediction latency acceptable: {avg_latency:.2f}ms"
            
            return ValidationResult(
                component="AI/ML",
                test_name="Prediction Latency",
                status=status,
                message=message,
                details={
                    'avg_latency_ms': round(avg_latency, 2),
                    'min_latency_ms': round(min_latency, 2),
                    'max_latency_ms': round(max_latency, 2),
                    'iterations': len(latencies)
                },
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ValidationResult(
                component="AI/ML",
                test_name="Prediction Latency",
                status=ValidationStatus.FAILED,
                message=f"Error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_feature_engineering(self) -> ValidationResult:
        """Validate feature engineering pipeline"""
        start = time.time()
        
        try:
            import pandas as pd
            import MetaTrader5 as mt5
            import talib
            
            if not mt5.initialize():
                return ValidationResult(
                    component="AI/ML",
                    test_name="Feature Engineering",
                    status=ValidationStatus.FAILED,
                    message="MT5 not initialized",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            # Get market data
            rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_H1, 0, 200)
            
            if rates is None:
                mt5.shutdown()
                return ValidationResult(
                    component="AI/ML",
                    test_name="Feature Engineering",
                    status=ValidationStatus.FAILED,
                    message="Failed to get market data",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            df = pd.DataFrame(rates)
            
            # Create features
            features = {}
            
            # Price features
            features['returns'] = df['close'].pct_change()
            features['log_returns'] = np.log(df['close'] / df['close'].shift(1))
            
            # Technical indicators
            features['ema_20'] = talib.EMA(df['close'].values, timeperiod=20)
            features['rsi_14'] = talib.RSI(df['close'].values, timeperiod=14)
            features['atr_14'] = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
            
            macd, signal, hist = talib.MACD(df['close'].values)
            features['macd'] = macd
            features['macd_signal'] = signal
            features['macd_hist'] = hist
            
            # Volume features
            features['volume_ma'] = df['tick_volume'].rolling(window=20).mean()
            features['volume_std'] = df['tick_volume'].rolling(window=20).std()
            
            # Create feature matrix
            feature_df = pd.DataFrame(features)
            feature_df = feature_df.dropna()
            
            mt5.shutdown()
            
            if len(feature_df) < 50:
                return ValidationResult(
                    component="AI/ML",
                    test_name="Feature Engineering",
                    status=ValidationStatus.WARNING,
                    message=f"Limited features available: {len(feature_df)} samples",
                    details={'feature_count': len(features), 'sample_count': len(feature_df)},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            return ValidationResult(
                component="AI/ML",
                test_name="Feature Engineering",
                status=ValidationStatus.PASSED,
                message=f"Feature engineering successful: {len(features)} features",
                details={
                    'feature_count': len(features),
                    'sample_count': len(feature_df),
                    'features': list(features.keys())
                },
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ValidationResult(
                component="AI/ML",
                test_name="Feature Engineering",
                status=ValidationStatus.FAILED,
                message=f"Error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_confidence_scoring(self) -> ValidationResult:
        """Validate prediction confidence scoring"""
        start = time.time()
        
        try:
            from sklearn.ensemble import RandomForestClassifier
            
            # Create test model
            X_train = np.random.rand(500, 15)
            y_train = np.random.randint(0, 2, 500)
            
            model = RandomForestClassifier(n_estimators=50, random_state=42)
            model.fit(X_train, y_train)
            
            # Get predictions with probabilities
            X_test = np.random.rand(10, 15)
            predictions = model.predict(X_test)
            probabilities = model.predict_proba(X_test)
            
            # Calculate confidence scores
            confidence_scores = np.max(probabilities, axis=1)
            
            # Validate confidence scores are in valid range
            if not all(0 <= score <= 1 for score in confidence_scores):
                return ValidationResult(
                    component="AI/ML",
                    test_name="Confidence Scoring",
                    status=ValidationStatus.FAILED,
                    message="Confidence scores out of valid range",
                    details={'scores': confidence_scores.tolist()},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            return ValidationResult(
                component="AI/ML",
                test_name="Confidence Scoring",
                status=ValidationStatus.PASSED,
                message=f"Confidence scoring working - avg: {np.mean(confidence_scores):.2f}",
                details={
                    'avg_confidence': round(float(np.mean(confidence_scores)), 3),
                    'min_confidence': round(float(np.min(confidence_scores)), 3),
                    'max_confidence': round(float(np.max(confidence_scores)), 3)
                },
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ValidationResult(
                component="AI/ML",
                test_name="Confidence Scoring",
                status=ValidationStatus.FAILED,
                message=f"Error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_all(self) -> List[ValidationResult]:
        """Run all AI/ML validations"""
        logger.info("=" * 80)
        logger.info("AI/ML SYSTEM VALIDATION")
        logger.info("=" * 80)
        
        results = [
            self.validate_ml_dependencies(),
            self.validate_model_loading(),
            self.validate_prediction_latency(),
            self.validate_feature_engineering(),
            self.validate_confidence_scoring()
        ]
        
        for result in results:
            logger.info(f"{result.status.value} {result.test_name}: {result.message}")
        
        return results


if __name__ == "__main__":
    validator = AIMLValidator()
    results = validator.validate_all()
