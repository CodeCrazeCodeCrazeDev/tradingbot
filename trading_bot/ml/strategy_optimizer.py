"""
Strategy Optimizer - Advanced ML-based optimization for trading strategies
"""

import numpy as np
import pandas as pd
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import joblib
import os
import json

from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error

from trading_bot.ml.online_learning import OnlineLearner, IncrementalLearner, ConceptDriftDetector
from trading_bot.ml.feature_engineering import FeatureEngineering as FeatureEngineer
try:
    from trading_bot.ml.hyperparameter_tuning import BayesianOptimizer
except ImportError:
    BayesianOptimizer = None

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


class StrategyOptimizer:
    """
    Advanced ML-based strategy optimizer
    
    Features:
    - Hyperparameter optimization for trading strategies
    - Feature selection and engineering
    - Regime-based model switching
    - Continuous learning and adaptation
    - Performance monitoring and feedback
    """
    
    def __init__(self, config: Dict = None):
        """Initialize the strategy optimizer"""
        self.config = config or {}
        
        # Initialize components
        self.feature_engineer = FeatureEngineer()
        self.online_learner = OnlineLearner()
        self.drift_detector = ConceptDriftDetector()
        self.bayesian_optimizer = BayesianOptimizer()
        
        # Model storage
        self.models = {}
        self.feature_importance = {}
        self.performance_metrics = {}
        
        # Optimization settings
        self.optimization_interval = self.config.get('optimization_interval_hours', 24)
        self.last_optimization = datetime.now() - timedelta(hours=self.optimization_interval + 1)
        self.min_training_samples = self.config.get('min_training_samples', 1000)
        
        # Model parameters
        self.model_params = {
            'classification': {
                'n_estimators': 100,
                'max_depth': 5,
                'min_samples_split': 10,
                'min_samples_leaf': 4,
                'random_state': 42
            },
            'regression': {
                'n_estimators': 100,
                'learning_rate': 0.1,
                'max_depth': 4,
                'min_samples_split': 10,
                'min_samples_leaf': 4,
                'random_state': 42
            }
        }
        
        # Create models directory
        os.makedirs('models', exist_ok=True)
        
        logger.info("Strategy Optimizer initialized")
    
    async def optimize_strategy(self, strategy_name: str, historical_data: Dict[str, pd.DataFrame], 
                               target_variable: str, prediction_type: str = 'classification') -> Dict:
        """
        Optimize a trading strategy using machine learning
        
        Args:
            strategy_name: Name of the strategy to optimize
            historical_data: Dictionary of historical data frames by symbol
            target_variable: Target variable to predict (e.g., 'direction', 'return')
            prediction_type: Type of prediction ('classification' or 'regression')
            
        Returns:
            Dictionary with optimization results
        """
        logger.info(f"Optimizing strategy: {strategy_name}")
        
        # Check if it's time to optimize
        now = datetime.now()
        hours_since_last = (now - self.last_optimization).total_seconds() / 3600
        
        if hours_since_last < self.optimization_interval:
            logger.info(f"Skipping optimization, last run was {hours_since_last:.1f} hours ago")
            return {"status": "skipped", "reason": "too_soon"}
        
        # Prepare data for optimization
        X, y, symbols = await self._prepare_data(historical_data, target_variable)
        
        if len(X) < self.min_training_samples:
            logger.warning(f"Not enough training samples: {len(X)} < {self.min_training_samples}")
            return {"status": "skipped", "reason": "insufficient_data"}
        
        # Check for concept drift
        drift_detected = await self._check_concept_drift(strategy_name, X, y)
        
        # Optimize model
        if drift_detected or strategy_name not in self.models:
            model, best_params, feature_importance = await self._train_model(X, y, prediction_type)
            
            # Store model
            self.models[strategy_name] = model
            self.feature_importance[strategy_name] = feature_importance
            
            # Save model to disk
            model_path = f"models/{strategy_name}_model.joblib"
            joblib.dump(model, model_path)
            
            # Save feature importance
            with open(f"models/{strategy_name}_feature_importance.json", 'w') as f:
                json.dump({str(k): float(v) for k, v in feature_importance.items()}, f, indent=2)
            
            logger.info(f"Model for {strategy_name} trained and saved")
            logger.info(f"Best parameters: {best_params}")
            
            # Update last optimization time
            self.last_optimization = now
            
            return {
                "status": "optimized",
                "best_params": best_params,
                "feature_importance": feature_importance,
                "samples": len(X),
                "symbols": symbols
            }
        else:
            logger.info(f"No concept drift detected for {strategy_name}, using existing model")
            return {"status": "unchanged", "reason": "no_drift"}
    
    async def predict(self, strategy_name: str, data: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using the optimized model
        
        Args:
            strategy_name: Name of the strategy
            data: Data frame with features
            
        Returns:
            Numpy array with predictions
        """
        if strategy_name not in self.models:
            raise ValueError(f"No model found for strategy {strategy_name}")
        
        # Prepare features
        features = self.feature_engineer.transform(data)
        
        # Make prediction
        model = self.models[strategy_name]
        predictions = model.predict(features)
        
        return predictions
    
    async def predict_proba(self, strategy_name: str, data: pd.DataFrame) -> np.ndarray:
        """
        Make probability predictions using the optimized model
        
        Args:
            strategy_name: Name of the strategy
            data: Data frame with features
            
        Returns:
            Numpy array with probability predictions
        """
        if strategy_name not in self.models:
            raise ValueError(f"No model found for strategy {strategy_name}")
        
        # Prepare features
        features = self.feature_engineer.transform(data)
        
        # Make prediction
        model = self.models[strategy_name]
        
        # Check if model supports predict_proba
        if hasattr(model, 'predict_proba'):
            return model.predict_proba(features)
        else:
            # For regression models, return the prediction as is
            return model.predict(features)
    
    async def update_model(self, strategy_name: str, new_data: pd.DataFrame, 
                          new_targets: np.ndarray) -> Dict:
        """
        Update model with new data using online learning
        
        Args:
            strategy_name: Name of the strategy
            new_data: New data for updating the model
            new_targets: New target values
            
        Returns:
            Dictionary with update results
        """
        if strategy_name not in self.models:
            logger.warning(f"No model found for strategy {strategy_name}, cannot update")
            return {"status": "failed", "reason": "no_model"}
        
        # Prepare features
        features = self.feature_engineer.transform(new_data)
        
        # Update model
        model = self.models[strategy_name]
        updated = await self.online_learner.update(model, features, new_targets)
        
        if updated:
            # Save updated model
            model_path = f"models/{strategy_name}_model.joblib"
            joblib.dump(model, model_path)
            
            # Update feature importance
            if hasattr(model, 'feature_importances_'):
                feature_names = self.feature_engineer.get_feature_names()
                self.feature_importance[strategy_name] = {
                    feature_names[i]: importance 
                    for i, importance in enumerate(model.feature_importances_)
                }
                
                # Save feature importance
                with open(f"models/{strategy_name}_feature_importance.json", 'w') as f:
                    json.dump({str(k): float(v) for k, v in self.feature_importance[strategy_name].items()}, 
                             f, indent=2)
            
            logger.info(f"Model for {strategy_name} updated with {len(new_data)} new samples")
            return {"status": "updated", "samples": len(new_data)}
        else:
            logger.info(f"Model for {strategy_name} not updated, no significant changes")
            return {"status": "unchanged", "reason": "no_significant_changes"}
    
    async def evaluate_strategy(self, strategy_name: str, test_data: pd.DataFrame, 
                              test_targets: np.ndarray, prediction_type: str = 'classification') -> Dict:
        """
        Evaluate strategy performance on test data
        
        Args:
            strategy_name: Name of the strategy
            test_data: Test data for evaluation
            test_targets: True target values
            prediction_type: Type of prediction ('classification' or 'regression')
            
        Returns:
            Dictionary with evaluation metrics
        """
        if strategy_name not in self.models:
            logger.warning(f"No model found for strategy {strategy_name}, cannot evaluate")
            return {"status": "failed", "reason": "no_model"}
        
        # Prepare features
        features = self.feature_engineer.transform(test_data)
        
        # Make predictions
        model = self.models[strategy_name]
        predictions = model.predict(features)
        
        # Calculate metrics
        if prediction_type == 'classification':
            metrics = {
                'accuracy': accuracy_score(test_targets, predictions),
                'precision': precision_score(test_targets, predictions, average='weighted'),
                'recall': recall_score(test_targets, predictions, average='weighted'),
                'f1': f1_score(test_targets, predictions, average='weighted')
            }
        else:  # regression
            metrics = {
                'mse': mean_squared_error(test_targets, predictions),
                'rmse': np.sqrt(mean_squared_error(test_targets, predictions)),
                'mae': np.mean(np.abs(test_targets - predictions)),
                'r2': 1 - np.sum((test_targets - predictions) ** 2) / np.sum((test_targets - np.mean(test_targets)) ** 2)
            }
        
        # Store metrics
        self.performance_metrics[strategy_name] = metrics
        
        # Save metrics
        with open(f"models/{strategy_name}_metrics.json", 'w') as f:
            json.dump({k: float(v) for k, v in metrics.items()}, f, indent=2)
        
        logger.info(f"Evaluation metrics for {strategy_name}: {metrics}")
        return {"status": "evaluated", "metrics": metrics}
    
    async def optimize_parameters(self, strategy_name: str, param_space: Dict, 
                                historical_data: Dict[str, pd.DataFrame], target_variable: str) -> Dict:
        """
        Optimize strategy parameters using Bayesian optimization
        
        Args:
            strategy_name: Name of the strategy
            param_space: Parameter space to search
            historical_data: Historical data for optimization
            target_variable: Target variable to optimize for
            
        Returns:
            Dictionary with optimized parameters
        """
        logger.info(f"Optimizing parameters for strategy {strategy_name}")
        
        # Prepare data
        X, y, _ = await self._prepare_data(historical_data, target_variable)
        
        # Define objective function for optimization
        def objective_function(params):
            # Create model with parameters
            model = RandomForestClassifier(**params)
            
            # Use time series cross-validation
            tscv = TimeSeriesSplit(n_splits=5)
            scores = []
            
            for train_idx, test_idx in tscv.split(X):
                X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
                
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                score = f1_score(y_test, y_pred, average='weighted')
                scores.append(score)
            
            return -np.mean(scores)  # Negative because we want to maximize
        
        # Run Bayesian optimization
        best_params = self.bayesian_optimizer.optimize(
            objective_function, param_space, n_iter=50
        )
        
        logger.info(f"Optimized parameters for {strategy_name}: {best_params}")
        return {"status": "optimized", "best_params": best_params}
    
    async def _prepare_data(self, historical_data: Dict[str, pd.DataFrame], 
                          target_variable: str) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
        """Prepare data for model training"""
        # Combine data from all symbols
        combined_data = []
        symbols = []
        
        for symbol, data in historical_data.items():
            if len(data) > 0:
                # Add symbol as a feature
                data = data.copy()
                data['symbol'] = symbol
                combined_data.append(data)
                symbols.append(symbol)
        
        if not combined_data:
            raise ValueError("No valid historical data provided")
        
        # Concatenate all data
        all_data = pd.concat(combined_data, axis=0)
        
        # Extract target variable
        if target_variable not in all_data.columns:
            raise ValueError(f"Target variable {target_variable} not found in data")
        
        y = all_data[target_variable]
        
        # Generate features
        X = self.feature_engineer.fit_transform(all_data.drop(columns=[target_variable]))
        
        return X, y, symbols
    
    async def _check_concept_drift(self, strategy_name: str, X: pd.DataFrame, y: pd.Series) -> bool:
        """Check for concept drift in the data"""
        if strategy_name not in self.models:
            return True  # No model exists, so train a new one
        
        # Use concept drift detector
        drift_detected = self.drift_detector.detect_drift(X, y)
        
        if drift_detected:
            logger.info(f"Concept drift detected for strategy {strategy_name}")
        
        return drift_detected
    
    async def _train_model(self, X: pd.DataFrame, y: pd.Series, 
                         prediction_type: str) -> Tuple[Any, Dict, Dict]:
        """Train a new model with hyperparameter optimization"""
        # Split data for training and validation
        train_size = int(0.8 * len(X))
        X_train, X_val = X.iloc[:train_size], X.iloc[train_size:]
        y_train, y_val = y.iloc[:train_size], y.iloc[train_size:]
        
        # Create pipeline with preprocessing
        if prediction_type == 'classification':
            pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('model', RandomForestClassifier(**self.model_params['classification']))
            ])
            
            # Define parameter grid
            param_grid = {
                'model__n_estimators': [50, 100, 200],
                'model__max_depth': [3, 5, 7, None],
                'model__min_samples_split': [2, 5, 10],
                'model__min_samples_leaf': [1, 2, 4]
            }
        else:  # regression
            pipeline = Pipeline([
                ('scaler', StandardScaler()),
                'model', GradientBoostingRegressor(**self.model_params['regression'])
            ])
            
            # Define parameter grid
            param_grid = {
                'model__n_estimators': [50, 100, 200],
                'model__learning_rate': [0.01, 0.1, 0.2],
                'model__max_depth': [3, 4, 5],
                'model__min_samples_split': [2, 5, 10],
                'model__min_samples_leaf': [1, 2, 4]
            }
        
        # Use GridSearchCV for hyperparameter tuning
        grid_search = GridSearchCV(
            pipeline, param_grid, cv=TimeSeriesSplit(n_splits=5),
            scoring='accuracy' if prediction_type == 'classification' else 'neg_mean_squared_error',
            n_jobs=-1
        )
        
        # Fit the model
        grid_search.fit(X_train, y_train)
        
        # Get best model
        best_model = grid_search.best_estimator_
        best_params = grid_search.best_params_
        
        # Extract feature importance
        if hasattr(best_model.named_steps['model'], 'feature_importances_'):
            feature_names = self.feature_engineer.get_feature_names()
            feature_importance = {
                feature_names[i]: importance 
                for i, importance in enumerate(best_model.named_steps['model'].feature_importances_)
            }
        else:
            feature_importance = {}
        
        return best_model, best_params, feature_importance


class StrategyEnsemble:
    """
    Ensemble of multiple strategy models
    
    Features:
    - Weighted voting of multiple models
    - Dynamic weight adjustment based on performance
    - Regime-specific model selection
    - Confidence scoring
    """
    
    def __init__(self, config: Dict = None):
        """Initialize the strategy ensemble"""
        self.config = config or {}
        
        # Initialize optimizer
        self.optimizer = StrategyOptimizer(self.config)
        
        # Strategy weights
        self.strategy_weights = {}
        self.default_weight = 1.0
        
        # Performance tracking
        self.performance_history = {}
        self.weight_update_interval = self.config.get('weight_update_interval_hours', 24)
        self.last_weight_update = datetime.now() - timedelta(hours=self.weight_update_interval + 1)
        
        logger.info("Strategy Ensemble initialized")
    
    async def add_strategy(self, strategy_name: str, weight: float = 1.0):
        """Add a strategy to the ensemble"""
        self.strategy_weights[strategy_name] = weight
        logger.info(f"Added strategy {strategy_name} with weight {weight}")
    
    async def remove_strategy(self, strategy_name: str):
        """Remove a strategy from the ensemble"""
        if strategy_name in self.strategy_weights:
            del self.strategy_weights[strategy_name]
            logger.info(f"Removed strategy {strategy_name}")
    
    async def predict(self, data: pd.DataFrame) -> Dict:
        """
        Make ensemble prediction
        
        Args:
            data: Data frame with features
            
        Returns:
            Dictionary with prediction results
        """
        if not self.strategy_weights:
            raise ValueError("No strategies in ensemble")
        
        # Make predictions for each strategy
        predictions = {}
        confidences = {}
        
        for strategy_name, weight in self.strategy_weights.items():
            try:
                # Get prediction
                pred = await self.optimizer.predict(strategy_name, data)
                
                # Get confidence
                if hasattr(self.optimizer.models[strategy_name], 'predict_proba'):
                    proba = await self.optimizer.predict_proba(strategy_name, data)
                    confidence = np.max(proba, axis=1)
                else:
                    confidence = np.ones_like(pred) * 0.5
                
                predictions[strategy_name] = pred
                confidences[strategy_name] = confidence
                
            except Exception as e:
                logger.error(f"Error predicting with strategy {strategy_name}: {e}")
        
        if not predictions:
            raise ValueError("No valid predictions from any strategy")
        
        # Combine predictions with weighted voting
        final_prediction = self._combine_predictions(predictions, confidences)
        
        return final_prediction
    
    async def update_weights(self, performance_metrics: Dict[str, Dict]):
        """
        Update strategy weights based on performance
        
        Args:
            performance_metrics: Dictionary of performance metrics by strategy
        """
        # Check if it's time to update weights
        now = datetime.now()
        hours_since_last = (now - self.last_weight_update).total_seconds() / 3600
        
        if hours_since_last < self.weight_update_interval:
            logger.info(f"Skipping weight update, last update was {hours_since_last:.1f} hours ago")
            return
        
        # Update weights based on performance
        new_weights = {}
        
        for strategy_name, metrics in performance_metrics.items():
            if strategy_name in self.strategy_weights:
                # Use F1 score for classification, R2 for regression
                if 'f1' in metrics:
                    score = metrics['f1']
                elif 'r2' in metrics:
                    score = metrics['r2']
                else:
                    score = 0.5  # Default
                
                # Update weight based on performance
                new_weights[strategy_name] = max(0.1, score)
        
        # Normalize weights
        total_weight = sum(new_weights.values())
        if total_weight > 0:
            for strategy_name in new_weights:
                new_weights[strategy_name] /= total_weight
        
        # Update weights
        self.strategy_weights.update(new_weights)
        self.last_weight_update = now
        
        logger.info(f"Updated strategy weights: {self.strategy_weights}")
    
    def _combine_predictions(self, predictions: Dict[str, np.ndarray], 
                           confidences: Dict[str, np.ndarray]) -> Dict:
        """Combine predictions from multiple strategies"""
        # Get unique classes for classification
        all_preds = np.concatenate([p.reshape(-1) for p in predictions.values()])
        unique_classes = np.unique(all_preds)
        
        if len(unique_classes) <= 5:  # Classification
            # For each sample, count weighted votes for each class
            n_samples = next(iter(predictions.values())).shape[0]
            class_votes = {cls: np.zeros(n_samples) for cls in unique_classes}
            
            for strategy_name, preds in predictions.items():
                weight = self.strategy_weights.get(strategy_name, self.default_weight)
                confidence = confidences.get(strategy_name, np.ones_like(preds) * 0.5)
                
                for i, pred in enumerate(preds):
                    class_votes[pred][i] += weight * confidence[i]
            
            # Find class with highest weighted vote for each sample
            final_pred = np.zeros(n_samples)
            final_conf = np.zeros(n_samples)
            
            for i in range(n_samples):
                best_class = None
                best_vote = -1
                
                for cls, votes in class_votes.items():
                    if votes[i] > best_vote:
                        best_vote = votes[i]
                        best_class = cls
                
                final_pred[i] = best_class
                final_conf[i] = best_vote / sum(votes[i] for votes in class_votes.values())
            
            return {
                'prediction': final_pred,
                'confidence': final_conf,
                'class_votes': class_votes
            }
        else:  # Regression
            # Weighted average of predictions
            n_samples = next(iter(predictions.values())).shape[0]
            weighted_sum = np.zeros(n_samples)
            weight_sum = np.zeros(n_samples)
            
            for strategy_name, preds in predictions.items():
                weight = self.strategy_weights.get(strategy_name, self.default_weight)
                confidence = confidences.get(strategy_name, np.ones_like(preds) * 0.5)
                
                weighted_sum += preds * weight * confidence
                weight_sum += weight * confidence
            
            # Avoid division by zero
            weight_sum = np.maximum(weight_sum, 1e-10)
            final_pred = weighted_sum / weight_sum
            
            # Calculate confidence as inverse of variance
            variance = np.zeros(n_samples)
            for strategy_name, preds in predictions.items():
                weight = self.strategy_weights.get(strategy_name, self.default_weight)
                confidence = confidences.get(strategy_name, np.ones_like(preds) * 0.5)
                
                variance += weight * confidence * (preds - final_pred) ** 2
            
            variance = np.maximum(variance, 1e-10)
            final_conf = 1.0 / (1.0 + variance)
            
            return {
                'prediction': final_pred,
                'confidence': final_conf
            }
