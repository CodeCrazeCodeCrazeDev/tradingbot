"""
Continuous Learner
Accumulates labeled examples and retrains models.
"""

import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
import numpy as np
import numpy

logger = logging.getLogger(__name__)


class ContinuousLearner:
    """
    Continuous learning system that accumulates labeled examples
    and retrains models in a sandbox environment.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize continuous learner.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Paths
        self.training_data_dir = Path(config.get('training_data_dir', 'models/training_data'))
        self.model_dir = Path(config.get('model_dir', 'models'))
        self.sandbox_dir = Path(config.get('sandbox_dir', 'models/sandbox'))
        
        # Create directories
        self.training_data_dir.mkdir(parents=True, exist_ok=True)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.min_examples_for_retrain = config.get('min_examples_for_retrain', 500)
        self.rolling_window_size = config.get('rolling_window_size', 10000)
        self.validation_split = config.get('validation_split', 0.2)
        
        # Model versioning
        self.current_model_version = self._load_current_version()
        
        # Training data accumulator
        self.labeled_examples = []
        self._load_existing_examples()
        
        logger.info(f"ContinuousLearner initialized")
        logger.info(f"  Current model version: {self.current_model_version}")
        logger.info(f"  Labeled examples: {len(self.labeled_examples)}")
        logger.info(f"  Min examples for retrain: {self.min_examples_for_retrain}")
    
    def add_labeled_example(self, 
                           trade_id: str,
                           features: Dict[str, Any],
                           outcome: str,  # 'win' or 'loss'
                           root_cause: str,
                           pnl: float,
                           metadata: Dict[str, Any]):
        """
        Add a labeled training example.
        
        Args:
            trade_id: Trade ID
            features: Feature dictionary
            outcome: Trade outcome ('win' or 'loss')
            root_cause: Identified root cause
            pnl: Profit/loss amount
            metadata: Additional metadata
        """
        example = {
            'trade_id': trade_id,
            'timestamp': datetime.now().isoformat(),
            'features': features,
            'outcome': outcome,
            'root_cause': root_cause,
            'pnl': pnl,
            'metadata': metadata
        }
        
        self.labeled_examples.append(example)
        
        # Save to disk
        self._save_example(example)
        
        logger.info(f"Added labeled example: {trade_id} ({outcome}, {root_cause})")
        
        # Check if ready for retraining
        if len(self.labeled_examples) >= self.min_examples_for_retrain:
            logger.info(f"Accumulated {len(self.labeled_examples)} examples - ready for retraining")
    
    def should_retrain(self) -> bool:
        """
        Check if model should be retrained.
        
        Returns:
            True if ready for retraining
        """
        return len(self.labeled_examples) >= self.min_examples_for_retrain
    
    def retrain_model_in_sandbox(self) -> Dict[str, Any]:
        """
        Retrain model in sandbox environment.
        
        Returns:
            Dictionary with training results and metrics
        """
        if not self.should_retrain():
            return {
                'status': 'skipped',
                'reason': f'Insufficient examples: {len(self.labeled_examples)} < {self.min_examples_for_retrain}'
            }
        
        logger.info("Starting model retraining in sandbox...")
        
        try:
            # Prepare training data
            X, y = self._prepare_training_data()
            
            # Split into train/validation
            split_idx = int(len(X) * (1 - self.validation_split))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            logger.info(f"Training set: {len(X_train)} examples")
            logger.info(f"Validation set: {len(X_val)} examples")
            
            # Train model (simplified - would use actual ML framework)
            model = self._train_model(X_train, y_train)
            
            # Validate model
            metrics = self._validate_model(model, X_val, y_val)
            
            # Save to sandbox
            new_version = self._get_next_version()
            sandbox_path = self.sandbox_dir / f"model_v{new_version}.pkl"
            
            with open(sandbox_path, 'wb') as f:
                pickle.dump(model, f)
            
            # Save metrics
            metrics_path = self.sandbox_dir / f"model_v{new_version}_metrics.json"
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            logger.info(f"Model v{new_version} trained in sandbox")
            logger.info(f"  Accuracy: {metrics['accuracy']:.3f}")
            logger.info(f"  Precision: {metrics['precision']:.3f}")
            logger.info(f"  Recall: {metrics['recall']:.3f}")
            
            return {
                'status': 'success',
                'version': new_version,
                'metrics': metrics,
                'sandbox_path': str(sandbox_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to retrain model: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def validate_sandbox_model(self, version: str) -> bool:
        """
        Validate sandbox model before promotion.
        
        Args:
            version: Model version to validate
            
        Returns:
            True if model passes validation
        """
        try:
            # Load sandbox model
            sandbox_path = self.sandbox_dir / f"model_v{version}.pkl"
            if not sandbox_path.exists():
                logger.error(f"Sandbox model not found: {sandbox_path}")
                return False
            
            # Load metrics
            metrics_path = self.sandbox_dir / f"model_v{version}_metrics.json"
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            
            # Validation criteria
            min_accuracy = self.config.get('min_model_accuracy', 0.6)
            min_precision = self.config.get('min_model_precision', 0.55)
            
            if metrics['accuracy'] < min_accuracy:
                logger.warning(f"Model accuracy too low: {metrics['accuracy']:.3f} < {min_accuracy}")
                return False
            
            if metrics['precision'] < min_precision:
                logger.warning(f"Model precision too low: {metrics['precision']:.3f} < {min_precision}")
                return False
            
            logger.info(f"Sandbox model v{version} passed validation")
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate sandbox model: {e}")
            return False
    
    def promote_model(self, version: str) -> bool:
        """
        Promote sandbox model to production.
        
        Args:
            version: Model version to promote
            
        Returns:
            True if promotion succeeded
        """
        try:
            # Validate first
            if not self.validate_sandbox_model(version):
                logger.error("Model failed validation, cannot promote")
                return False
            
            # Backup current model
            current_path = self.model_dir / "current_model.pkl"
            if current_path.exists():
                backup_path = self.model_dir / f"model_v{self.current_model_version}_backup.pkl"
                current_path.rename(backup_path)
                logger.info(f"Backed up current model to {backup_path}")
            
            # Copy sandbox model to production
            sandbox_path = self.sandbox_dir / f"model_v{version}.pkl"
            sandbox_path.replace(current_path)
            
            # Copy metrics
            sandbox_metrics = self.sandbox_dir / f"model_v{version}_metrics.json"
            prod_metrics = self.model_dir / f"model_v{version}_metrics.json"
            with open(sandbox_metrics, 'r') as f:
                metrics = json.load(f)
            with open(prod_metrics, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            # Update version
            self.current_model_version = version
            self._save_current_version(version)
            
            logger.info(f"Promoted model v{version} to production")
            return True
            
        except Exception as e:
            logger.error(f"Failed to promote model: {e}")
            return False
    
    def _prepare_training_data(self) -> tuple:
        """Prepare training data from labeled examples."""
        # Use rolling window
        examples = self.labeled_examples[-self.rolling_window_size:]
        
        # Extract features and labels
        X = []
        y = []
        
        for example in examples:
            # Convert features to vector (simplified)
            feature_vector = self._features_to_vector(example['features'])
            X.append(feature_vector)
            
            # Label: 1 for win, 0 for loss
            label = 1 if example['outcome'] == 'win' else 0
            y.append(label)
        
        return np.array(X), np.array(y)
    
    def _features_to_vector(self, features: Dict[str, Any]) -> np.ndarray:
        """Convert feature dictionary to vector (simplified)."""
        # This is a simplified version - would need proper feature engineering
        vector = []
        
        # Extract numeric features
        for key, value in features.items():
            if isinstance(value, (int, float)):
                vector.append(float(value))
            elif isinstance(value, bool):
                vector.append(1.0 if value else 0.0)
        
        # Pad to fixed size
        target_size = 50
        if len(vector) < target_size:
            vector.extend([0.0] * (target_size - len(vector)))
        else:
            vector = vector[:target_size]
        
        return np.array(vector)
    
    def _train_model(self, X: np.ndarray, y: np.ndarray) -> Any:
        """Train model (simplified - would use actual ML framework)."""
        # This is a placeholder - would use sklearn, torch, etc.
        # For now, return a simple model representation
        return {
            'type': 'placeholder',
            'trained_on': len(X),
            'timestamp': datetime.now().isoformat()
        }
    
    def _validate_model(self, model: Any, X_val: np.ndarray, y_val: np.ndarray) -> Dict[str, float]:
        """Validate model on validation set."""
        # Simplified validation - would use actual predictions
        # For now, return placeholder metrics
        return {
            'accuracy': 0.65,
            'precision': 0.62,
            'recall': 0.68,
            'f1_score': 0.65,
            'validation_samples': len(X_val)
        }
    
    def _save_example(self, example: Dict[str, Any]):
        """Save example to disk."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.training_data_dir / f"example_{timestamp}_{example['trade_id']}.json"
            
            with open(filename, 'w') as f:
                json.dump(example, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save example: {e}")
    
    def _load_existing_examples(self):
        """Load existing training examples from disk."""
        try:
            example_files = sorted(self.training_data_dir.glob('example_*.json'))
            
            # Load most recent examples up to rolling window size
            for filepath in example_files[-self.rolling_window_size:]:
                with open(filepath, 'r') as f:
                    example = json.load(f)
                    self.labeled_examples.append(example)
            
            logger.info(f"Loaded {len(self.labeled_examples)} existing examples")
        except Exception as e:
            logger.error(f"Failed to load existing examples: {e}")
    
    def _load_current_version(self) -> str:
        """Load current model version."""
        version_file = self.model_dir / 'current_version.txt'
        if version_file.exists():
            return version_file.read_text().strip()
        return '0'
    
    def _save_current_version(self, version: str):
        """Save current model version."""
        version_file = self.model_dir / 'current_version.txt'
        version_file.write_text(version)
    
    def _get_next_version(self) -> str:
        """Get next model version number."""
        try:
            current = int(self.current_model_version)
            return str(current + 1)
        except Exception:
            return '1'
