"""
Model Retraining Pipeline
Automated ML model retraining with validation and deployment
"""

import json
import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RetrainingTrigger(Enum):
    """Triggers for model retraining."""
    SCHEDULED = "scheduled"
    PERFORMANCE_BASED = "performance_based"
    DRIFT_BASED = "drift_based"
    MANUAL = "manual"


@dataclass
class ModelVersion:
    """Model version information."""
    version: str
    created_at: datetime
    accuracy: float
    training_data_size: int
    hyperparameters: Dict[str, Any]
    model_path: str
    is_active: bool = False


@dataclass
class TrainingResult:
    """Result of model training."""
    success: bool
    version: Optional[str]
    accuracy: float
    training_time_seconds: float
    error_message: Optional[str] = None


class ModelRetrainingPipeline:
    """Pipeline for automated model retraining."""
    
    def __init__(
        self,
        model_name: str,
        models_dir: str = "models",
        min_accuracy_threshold: float = 0.65,
        accuracy_drop_threshold: float = 0.1
    ):
        self.model_name = model_name
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.min_accuracy_threshold = min_accuracy_threshold
        self.accuracy_drop_threshold = accuracy_drop_threshold
        self.versions: List[ModelVersion] = []
        self._load_versions()
    
    def _load_versions(self):
        """Load existing model versions."""
        versions_file = self.models_dir / f"{self.model_name}_versions.json"
        if versions_file.exists():
            with open(versions_file) as f:
                versions_data = json.load(f)
                self.versions = [
                    ModelVersion(
                        version=v['version'],
                        created_at=datetime.fromisoformat(v['created_at']),
                        accuracy=v['accuracy'],
                        training_data_size=v['training_data_size'],
                        hyperparameters=v['hyperparameters'],
                        model_path=v['model_path'],
                        is_active=v.get('is_active', False)
                    )
                    for v in versions_data
                ]
    
    def _save_versions(self):
        """Save model versions metadata."""
        versions_file = self.models_dir / f"{self.model_name}_versions.json"
        versions_data = [
            {
                'version': v.version,
                'created_at': v.created_at.isoformat(),
                'accuracy': v.accuracy,
                'training_data_size': v.training_data_size,
                'hyperparameters': v.hyperparameters,
                'model_path': v.model_path,
                'is_active': v.is_active
            }
            for v in self.versions
        ]
        with open(versions_file, 'w') as f:
            json.dump(versions_data, f, indent=2)
    
    def check_retraining_needed(
        self,
        current_accuracy: float,
        reference_accuracy: Optional[float] = None
    ) -> Tuple[bool, RetrainingTrigger]:
        """Check if retraining is needed based on current performance."""
        # Get reference accuracy from best performing version
        if reference_accuracy is None and self.versions:
            reference_accuracy = max(v.accuracy for v in self.versions)
        elif reference_accuracy is None:
            reference_accuracy = 1.0
        
        # Check accuracy drop
        accuracy_drop = reference_accuracy - current_accuracy
        if accuracy_drop > self.accuracy_drop_threshold:
            return True, RetrainingTrigger.PERFORMANCE_BASED
        
        # Check minimum threshold
        if current_accuracy < self.min_accuracy_threshold:
            return True, RetrainingTrigger.PERFORMANCE_BASED
        
        # Check if scheduled retraining is due
        if self.versions:
            last_training = max(v.created_at for v in self.versions)
            days_since_training = (datetime.now() - last_training).days
            if days_since_training >= 7:  # Weekly retraining
                return True, RetrainingTrigger.SCHEDULED
        
        return False, None
    
    def collect_training_data(
        self,
        lookback_days: int = 90,
        min_samples: int = 1000,
        symbols: List[str] = None
    ) -> pd.DataFrame:
        """Collect and prepare training data from MT5."""
        if symbols is None:
            symbols = ["EURUSD", "GBPUSD", "USDJPY"]
        
        try:
            from trading_bot.data.mt5_interface import MT5Interface
            
            all_data = []
            
            with MT5Interface() as mt5:
                for symbol in symbols:
                    # Get historical data
                    rates = mt5.get_rates(
                        symbol=symbol,
                        timeframe="H1",
                        count=min_samples // len(symbols)
                    )
                    
                    if rates is None or len(rates) == 0:
                        logger.warning(f"No data retrieved for {symbol}")
                        continue
                    
                    df = pd.DataFrame(rates)
                    df['symbol'] = symbol
                    
                    # Calculate technical features
                    df['returns'] = df['close'].pct_change()
                    df['volatility'] = df['returns'].rolling(20).std()
                    df['sma_20'] = df['close'].rolling(20).mean()
                    df['sma_50'] = df['close'].rolling(50).mean()
                    df['rsi'] = self._calculate_rsi(df['close'], 14)
                    df['atr'] = self._calculate_atr(df, 14)
                    
                    # Target: next period direction (1 if up, 0 if down)
                    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
                    
                    all_data.append(df.dropna())
            
            if not all_data:
                raise ValueError("No data retrieved from MT5")
            
            combined = pd.concat(all_data, ignore_index=True)
            
            # Feature selection
            feature_cols = ['open', 'high', 'low', 'close', 'volume', 'returns', 
                          'volatility', 'sma_20', 'sma_50', 'rsi', 'atr']
            
            # Ensure all feature columns exist
            for col in feature_cols:
                if col not in combined.columns:
                    combined[col] = 0.0
            
            logger.info(f"Collected {len(combined)} training samples from {len(symbols)} symbols")
            return combined
            
        except Exception as e:
            logger.error(f"Failed to collect training data: {e}")
            # Fallback to historical database if MT5 fails
            return self._collect_from_database(lookback_days, min_samples)
    
    def _collect_from_database(
        self,
        lookback_days: int,
        min_samples: int
    ) -> pd.DataFrame:
        """Fallback: Collect training data from historical database."""
        try:
            from trading_bot.database import get_historical_data
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)
            
            data = get_historical_data(
                start_date=start_date,
                end_date=end_date,
                limit=min_samples
            )
            
            if data is not None and len(data) > 0:
                logger.info(f"Retrieved {len(data)} samples from database")
                return data
                
        except Exception as e:
            logger.error(f"Database fallback failed: {e}")
        
        # Last resort: return empty DataFrame with expected columns
        logger.warning("All data sources failed, returning empty DataFrame")
        return pd.DataFrame(columns=[
            'timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume',
            'returns', 'volatility', 'sma_20', 'sma_50', 'rsi', 'atr', 'target'
        ])
    
    @staticmethod
    def _calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def _calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR indicator."""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(period).mean()
    
    def validate_data_quality(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Validate training data quality."""
        issues = []
        
        # Check for missing values
        missing_pct = data.isnull().mean()
        if (missing_pct > 0.05).any():
            issues.append(f"High missing value ratio in columns: {missing_pct[missing_pct > 0.05].index.tolist()}")
        
        # Check for class imbalance
        if 'target' in data.columns:
            class_balance = data['target'].value_counts(normalize=True)
            if class_balance.min() < 0.1:
                issues.append("Severe class imbalance detected")
        
        # Check for data drift (simplified)
        if len(data) > 100:
            recent_mean = data.iloc[-100:].select_dtypes(include=[np.number]).mean()
            older_mean = data.iloc[:-100].select_dtypes(include=[np.number]).mean()
            drift_score = np.abs((recent_mean - older_mean) / older_mean).mean()
            if drift_score > 0.5:
                issues.append(f"Significant data drift detected: {drift_score:.2f}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "drift_score": drift_score if 'drift_score' in locals() else 0
        }
    
    def train_new_model(
        self,
        data: pd.DataFrame,
        hyperparameters: Optional[Dict] = None
    ) -> TrainingResult:
        """Train a new model version using scikit-learn."""
        start_time = datetime.now()
        
        try:
            from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
            from sklearn.model_selection import train_test_split, cross_val_score
            from sklearn.preprocessing import StandardScaler
            from sklearn.metrics import accuracy_score, classification_report
            
            # Default hyperparameters
            if hyperparameters is None:
                hyperparameters = {
                    'model_type': 'random_forest',
                    'n_estimators': 100,
                    'max_depth': 10,
                    'min_samples_split': 5,
                    'min_samples_leaf': 2,
                    'test_size': 0.2,
                    'random_state': 42
                }
            
            # Prepare features and target
            feature_cols = ['open', 'high', 'low', 'close', 'volume', 'returns', 
                          'volatility', 'sma_20', 'sma_50', 'rsi', 'atr']
            
            X = data[feature_cols].fillna(0)
            y = data['target']
            
            # Remove rows with NaN targets
            valid_idx = y.notna()
            X = X[valid_idx]
            y = y[valid_idx]
            
            if len(X) < 100:
                raise ValueError(f"Insufficient data for training: {len(X)} samples")
            
            # Split data
            test_size = hyperparameters.get('test_size', 0.2)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=hyperparameters.get('random_state', 42),
                stratify=y if len(np.unique(y)) > 1 else None
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Select and train model
            model_type = hyperparameters.get('model_type', 'random_forest')
            
            if model_type == 'random_forest':
                model = RandomForestClassifier(
                    n_estimators=hyperparameters.get('n_estimators', 100),
                    max_depth=hyperparameters.get('max_depth', 10),
                    min_samples_split=hyperparameters.get('min_samples_split', 5),
                    min_samples_leaf=hyperparameters.get('min_samples_leaf', 2),
                    random_state=hyperparameters.get('random_state', 42),
                    n_jobs=-1
                )
            elif model_type == 'gradient_boosting':
                model = GradientBoostingClassifier(
                    n_estimators=hyperparameters.get('n_estimators', 100),
                    max_depth=hyperparameters.get('max_depth', 5),
                    learning_rate=hyperparameters.get('learning_rate', 0.1),
                    random_state=hyperparameters.get('random_state', 42)
                )
            else:
                model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
            
            # Train model
            logger.info(f"Training {model_type} model with {len(X_train)} samples...")
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            validation_accuracy = accuracy_score(y_test, y_pred)
            
            # Cross-validation score
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
            cv_accuracy = cv_scores.mean()
            
            logger.info(f"Model trained - Test accuracy: {validation_accuracy:.4f}, CV accuracy: {cv_accuracy:.4f}")
            
            # Calculate training time
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Generate version ID
            version = f"{self.model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Save model and scaler
            model_path = self.models_dir / f"{version}.pkl"
            scaler_path = self.models_dir / f"{version}_scaler.pkl"
            
            model_data = {
                'model': model,
                'scaler': scaler,
                'feature_columns': feature_cols,
                'hyperparameters': hyperparameters,
                'accuracy': validation_accuracy,
                'cv_accuracy': cv_accuracy,
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
            with open(model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Model saved to {model_path}")
            
            # Record version
            model_version = ModelVersion(
                version=version,
                created_at=datetime.now(),
                accuracy=validation_accuracy,
                training_data_size=len(X_train),
                hyperparameters=hyperparameters,
                model_path=str(model_path),
                is_active=False
            )
            self.versions.append(model_version)
            self._save_versions()
            
            return TrainingResult(
                success=True,
                version=version,
                accuracy=validation_accuracy,
                training_time_seconds=training_time
            )
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return TrainingResult(
                success=False,
                version=None,
                accuracy=0.0,
                training_time_seconds=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )
    
    def validate_new_model(
        self,
        new_version: str,
        comparison_metric: str = "accuracy"
    ) -> Dict[str, Any]:
        """Validate new model against current production model."""
        new_model = next((v for v in self.versions if v.version == new_version), None)
        if new_model is None:
            return {"error": "New model version not found"}
        
        # Get current active model
        current_model = next((v for v in self.versions if v.is_active), None)
        
        if current_model is None:
            # No current model, new model automatically becomes active
            return {
                "approved": True,
                "reason": "No current production model",
                "new_accuracy": new_model.accuracy,
                "improvement": None
            }
        
        # Compare models
        if new_model.accuracy > current_model.accuracy:
            improvement = (new_model.accuracy - current_model.accuracy) / current_model.accuracy
            return {
                "approved": True,
                "reason": "Improved accuracy",
                "new_accuracy": new_model.accuracy,
                "current_accuracy": current_model.accuracy,
                "improvement": improvement
            }
        else:
            degradation = (current_model.accuracy - new_model.accuracy) / current_model.accuracy
            return {
                "approved": False,
                "reason": "Accuracy degradation",
                "new_accuracy": new_model.accuracy,
                "current_accuracy": current_model.accuracy,
                "degradation": degradation
            }
    
    def deploy_model(self, version: str, shadow_mode: bool = False) -> bool:
        """Deploy a model version to production."""
        model_version = next((v for v in self.versions if v.version == version), None)
        if model_version is None:
            return False
        
        if not shadow_mode:
            # Deactivate current model
            for v in self.versions:
                v.is_active = False
            
            # Activate new model
            model_version.is_active = True
            self._save_versions()
        
        return True
    
    def rollback(self) -> Optional[str]:
        """Rollback to previous model version."""
        # Find previous active model
        sorted_versions = sorted(
            [v for v in self.versions if not v.is_active],
            key=lambda x: x.created_at,
            reverse=True
        )
        
        if not sorted_versions:
            return None
        
        previous_model = sorted_versions[0]
        
        # Deactivate current
        for v in self.versions:
            v.is_active = False
        
        # Activate previous
        previous_model.is_active = True
        self._save_versions()
        
        return previous_model.version
    
    def run_full_retraining_cycle(
        self,
        trigger: RetrainingTrigger = RetrainingTrigger.MANUAL
    ) -> Dict[str, Any]:
        """Run complete retraining cycle from data collection to deployment."""
        result = {
            "trigger": trigger.value,
            "started_at": datetime.now().isoformat(),
            "steps": []
        }
        
        # Step 1: Collect data
        data = self.collect_training_data()
        result["steps"].append({
            "name": "data_collection",
            "status": "completed",
            "samples": len(data)
        })
        
        # Step 2: Validate data
        quality_check = self.validate_data_quality(data)
        result["steps"].append({
            "name": "data_validation",
            "status": "passed" if quality_check["valid"] else "failed",
            "issues": quality_check["issues"]
        })
        
        if not quality_check["valid"]:
            result["status"] = "failed"
            result["reason"] = "Data validation failed"
            return result
        
        # Step 3: Train model
        training_result = self.train_new_model(data)
        result["steps"].append({
            "name": "training",
            "status": "completed" if training_result.success else "failed",
            "version": training_result.version,
            "accuracy": training_result.accuracy,
            "duration_seconds": training_result.training_time_seconds
        })
        
        if not training_result.success:
            result["status"] = "failed"
            result["reason"] = f"Training failed: {training_result.error_message}"
            return result
        
        # Step 4: Validate model
        validation = self.validate_new_model(training_result.version)
        result["steps"].append({
            "name": "validation",
            "status": "approved" if validation["approved"] else "rejected",
            "details": validation
        })
        
        if not validation["approved"]:
            result["status"] = "rejected"
            result["reason"] = validation["reason"]
            return result
        
        # Step 5: Deploy
        deployed = self.deploy_model(training_result.version)
        result["steps"].append({
            "name": "deployment",
            "status": "completed" if deployed else "failed"
        })
        
        result["status"] = "completed"
        result["deployed_version"] = training_result.version
        result["completed_at"] = datetime.now().isoformat()
        
        return result


class DriftDetector:
    """Detect data and concept drift in production."""
    
    def __init__(self, reference_data: pd.DataFrame):
        self.reference_data = reference_data
        self.reference_stats = self._compute_statistics(reference_data)
    
    def _compute_statistics(self, data: pd.DataFrame) -> Dict[str, Dict]:
        """Compute reference statistics."""
        stats = {}
        for col in data.select_dtypes(include=[np.number]).columns:
            stats[col] = {
                'mean': data[col].mean(),
                'std': data[col].std(),
                'quantiles': data[col].quantile([0.1, 0.5, 0.9]).to_dict()
            }
        return stats
    
    def detect_drift(
        self,
        current_data: pd.DataFrame,
        threshold: float = 0.05
    ) -> Dict[str, Any]:
        """Detect drift between reference and current data."""
        drift_results = {}
        
        for col in self.reference_stats.keys():
            if col not in current_data.columns:
                continue
            
            ref_mean = self.reference_stats[col]['mean']
            ref_std = self.reference_stats[col]['std']
            curr_mean = current_data[col].mean()
            
            # Calculate drift score (normalized difference)
            if ref_std > 0:
                drift_score = abs(curr_mean - ref_mean) / ref_std
            else:
                drift_score = 0 if curr_mean == ref_mean else float('inf')
            
            drift_detected = drift_score > threshold
            
            drift_results[col] = {
                'drift_detected': drift_detected,
                'drift_score': drift_score,
                'reference_mean': ref_mean,
                'current_mean': curr_mean
            }
        
        return {
            'overall_drift': any(r['drift_detected'] for r in drift_results.values()),
            'features': drift_results,
            'threshold': threshold
        }
