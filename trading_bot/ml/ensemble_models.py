"""
Ensemble methods for combining multiple ML models.
"""
import numpy as np
import pandas as pd
import logging
import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from datetime import datetime

try:
    import torch
except ImportError:
    torch = None

try:
    from trading_bot.ml.predictive_models import TransformerModel
except ImportError:
    TransformerModel = None

try:
    from trading_bot.ml.reinforcement import PPOAgent
except ImportError:
    PPOAgent = None

logger = logging.getLogger(__name__)


class ModelEnsemble:
    """
    Ensemble class for combining multiple ML models.
    
    This class implements various ensemble methods for combining predictions
    from multiple models:
    - Simple averaging
    - Weighted averaging
    - Stacking
    - Voting
    
    It supports both predictive models (TransformerModel) and reinforcement
    learning models (PPOAgent).
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the ModelEnsemble.
        
        Args:
            config: Configuration dictionary with ensemble parameters
        """
        self.config = config or {}
        self.ensemble_method = self.config.get('ensemble_method', 'weighted_average')
        self.models = []
        self.model_weights = []
        self.meta_model = None
        self.is_trained = False
        self.training_history = []
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Initialize weights if provided
        initial_weights = self.config.get('initial_weights', None)
        if initial_weights:
            self.model_weights = initial_weights
    
    def add_model(self, model: Union[TransformerModel, PPOAgent], weight: float = 1.0) -> None:
        """
        Add a model to the ensemble.
        
        Args:
            model: The model to add (TransformerModel or PPOAgent)
            weight: Initial weight for the model in the ensemble
        """
        self.models.append(model)
        self.model_weights.append(weight)
        
        # Normalize weights
        total_weight = sum(self.model_weights)
        self.model_weights = [w / total_weight for w in self.model_weights]
    
    def predict_price(self, df: pd.DataFrame, n_future: int = 1) -> np.ndarray:
        """
        Generate price predictions using the ensemble of predictive models.
        
        Args:
            df: DataFrame containing market data
            n_future: Number of future time steps to predict
            
        Returns:
            Array of predicted prices
        """
        if not self.models:
            raise ValueError("No models in the ensemble")
        
        predictions = []
        valid_weights = []
        
        # Get predictions from each model
        for i, model in enumerate(self.models):
            if isinstance(model, TransformerModel):
                try:
                    pred = model.predict(df, n_future=n_future)
                    predictions.append(pred)
                    valid_weights.append(self.model_weights[i])
                except Exception as e:
                    logger.info(f"Error in model {i}: {str(e)}")
        
        if not predictions:
            raise ValueError("No valid predictions from any model")
        
        # Normalize valid weights
        total_weight = sum(valid_weights)
        valid_weights = [w / total_weight for w in valid_weights]
        
        # Apply ensemble method
        if self.ensemble_method == 'simple_average':
            # Simple averaging
            ensemble_pred = np.mean(predictions, axis=0)
        
        elif self.ensemble_method == 'weighted_average':
            # Weighted averaging
            ensemble_pred = np.zeros_like(predictions[0])
            for i, pred in enumerate(predictions):
                ensemble_pred += pred * valid_weights[i]
        
        elif self.ensemble_method == 'median':
            # Median ensemble
            ensemble_pred = np.median(predictions, axis=0)
        
        else:
            raise ValueError(f"Unsupported ensemble method: {self.ensemble_method}")
        
        return ensemble_pred
    
    def get_trading_action(self, df: pd.DataFrame) -> Tuple[int, Dict[str, float]]:
        """
        Get trading action using the ensemble of reinforcement learning models.
        
        Args:
            df: DataFrame containing market data
            
        Returns:
            Tuple of (action, probabilities)
        """
        if not self.models:
            raise ValueError("No models in the ensemble")
        
        actions = []
        probs_list = []
        valid_weights = []
        
        # Get actions from each model
        for i, model in enumerate(self.models):
            if isinstance(model, PPOAgent):
                try:
                    state = model.preprocess_state(df.tail(1))
                    action, probs = model.get_action(state[0])
                    actions.append(action)
                    probs_list.append(probs)
                    valid_weights.append(self.model_weights[i])
                except Exception as e:
                    logger.info(f"Error in model {i}: {str(e)}")
        
        if not actions:
            raise ValueError("No valid actions from any model")
        
        # Normalize valid weights
        total_weight = sum(valid_weights)
        valid_weights = [w / total_weight for w in valid_weights]
        
        # Combine probabilities using weighted average
        combined_probs = {'hold': 0.0, 'buy': 0.0, 'sell': 0.0}
        for i, probs in enumerate(probs_list):
            for action, prob in probs.items():
                combined_probs[action] += prob * valid_weights[i]
        
        # Select action with highest probability
        action_map = {'hold': 0, 'buy': 1, 'sell': 2}
        reverse_map = {0: 'hold', 1: 'buy', 2: 'sell'}
        
        if self.ensemble_method == 'majority_vote':
            # Count votes for each action
            action_counts = {0: 0, 1: 0, 2: 0}
            for i, action in enumerate(actions):
                action_counts[action] += valid_weights[i]
            
            # Select action with most votes
            ensemble_action = max(action_counts, key=action_counts.get)
        else:
            # Select action with highest probability
            ensemble_action = action_map[max(combined_probs, key=combined_probs.get)]
        
        return ensemble_action, combined_probs
    
    def train_meta_model(self, df: pd.DataFrame, target_col: str = 'close') -> Dict[str, Any]:
        """
        Train a meta-model for stacking ensemble.
        
        Args:
            df: DataFrame containing market data
            target_col: Target column for prediction
            
        Returns:
            Training history
        """
        # Split data for training and validation
        train_size = int(len(df) * 0.8)
        train_df = df.iloc[:train_size]
        val_df = df.iloc[train_size:]
        
        # Get base model predictions
        base_predictions = []
        for model in self.models:
            if isinstance(model, TransformerModel):
                # Train the model if not already trained
                if not model.is_trained:
                    model.train(train_df, target_col=target_col)
                
                # Get predictions for training and validation sets
                train_preds = []
                for i in range(len(train_df) - 20):  # Assuming window_size=20
                    pred = model.predict(train_df.iloc[i:i+20])
                    train_preds.append(pred[0])
                
                val_preds = []
                for i in range(len(val_df) - 20):
                    pred = model.predict(val_df.iloc[i:i+20])
                    val_preds.append(pred[0])
                
                base_predictions.append((train_preds, val_preds))
        
        # Prepare meta-model training data
        X_train = np.column_stack([train_pred for train_pred, _ in base_predictions])
        y_train = train_df[target_col].values[20:20+len(X_train)]
        
        X_val = np.column_stack([val_pred for _, val_pred in base_predictions])
        y_val = val_df[target_col].values[20:20+len(X_val)]
        
        # Create and train meta-model (simple linear regression)
        self.meta_model = torch.nn.Linear(len(self.models), 1)
        self.meta_model.to(self.device)
        
        criterion = torch.nn.MSELoss()
        optimizer = torch.optim.Adam(self.meta_model.parameters(), lr=0.001)
        
        # Convert to PyTorch tensors
        X_train_tensor = torch.FloatTensor(X_train).to(self.device)
        y_train_tensor = torch.FloatTensor(y_train).reshape(-1, 1).to(self.device)
        X_val_tensor = torch.FloatTensor(X_val).to(self.device)
        y_val_tensor = torch.FloatTensor(y_val).reshape(-1, 1).to(self.device)
        
        # Training loop
        epochs = self.config.get('meta_model_epochs', 100)
        batch_size = self.config.get('meta_model_batch_size', 32)
        history = {'train_loss': [], 'val_loss': []}
        
        for epoch in range(epochs):
            # Mini-batch training
            permutation = torch.randperm(X_train_tensor.size()[0])
            total_loss = 0.0
            
            for i in range(0, X_train_tensor.size()[0], batch_size):
                indices = permutation[i:i+batch_size]
                batch_x, batch_y = X_train_tensor[indices], y_train_tensor[indices]
                
                # Forward pass
                outputs = self.meta_model(batch_x)
                loss = criterion(outputs, batch_y)
                
                # Backward and optimize
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            # Calculate validation loss
            with torch.no_grad():
                val_outputs = self.meta_model(X_val_tensor)
                val_loss = criterion(val_outputs, y_val_tensor).item()
            
            # Record history
            avg_train_loss = total_loss / (len(X_train_tensor) / batch_size)
            history['train_loss'].append(avg_train_loss)
            history['val_loss'].append(val_loss)
            
            # Print progress every 10 epochs
            if (epoch + 1) % 10 == 0:
                logger.info(f'Epoch [{epoch+1}/{epochs}], Train Loss: {avg_train_loss:.4f}, Val Loss: {val_loss:.4f}')
        
        # Update model weights based on meta-model coefficients
        with torch.no_grad():
            self.model_weights = self.meta_model.weight.cpu().numpy().flatten().tolist()
            # Ensure weights are positive and normalized
            self.model_weights = [max(0.0, w) for w in self.model_weights]
            total_weight = sum(self.model_weights)
            if total_weight > 0:
                self.model_weights = [w / total_weight for w in self.model_weights]
            else:
                # If all weights are negative, use equal weights
                self.model_weights = [1.0 / len(self.models) for _ in self.models]
        
        self.is_trained = True
        self.training_history = history
        
        return history
    
    def evaluate(self, df: pd.DataFrame, target_col: str = 'close') -> Dict[str, Any]:
        """
        Evaluate the ensemble model on test data.
        
        Args:
            df: DataFrame containing market data
            target_col: Target column for prediction
            
        Returns:
            Dictionary with evaluation metrics
        """
        if not self.models:
            raise ValueError("No models in the ensemble")
        
        # Make predictions
        predictions = []
        window_size = 20  # Assuming window_size=20
        
        for i in range(len(df) - window_size):
            try:
                pred = self.predict_price(df.iloc[i:i+window_size])
                predictions.append(pred[0])
            except Exception as e:
                logger.info(f"Error in prediction at index {i}: {str(e)}")
                predictions.append(None)
        
        # Remove None values
        valid_indices = [i for i, p in enumerate(predictions) if p is not None]
        valid_predictions = [predictions[i] for i in valid_indices]
        valid_targets = df[target_col].values[window_size + np.array(valid_indices)]
        
        if not valid_predictions:
            raise ValueError("No valid predictions for evaluation")
        
        # Calculate metrics
        mse = np.mean((np.array(valid_predictions) - valid_targets) ** 2)
        mae = np.mean(np.abs(np.array(valid_predictions) - valid_targets))
        
        # Calculate directional accuracy
        directions_pred = np.sign(np.diff(np.array([df[target_col].values[window_size-1]] + valid_predictions)))
        directions_true = np.sign(np.diff(np.array([df[target_col].values[window_size-1]] + valid_targets.tolist())))
        directional_accuracy = np.mean(directions_pred == directions_true)
        
        return {
            'mse': mse,
            'mae': mae,
            'rmse': np.sqrt(mse),
            'directional_accuracy': directional_accuracy,
            'num_predictions': len(valid_predictions)
        }
    
    def save_model(self, path: str) -> bool:
        """
        Save the ensemble model to disk.
        
        Args:
            path: Path to save the model
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Save meta-model if exists
            if self.meta_model is not None:
                torch.save(self.meta_model.state_dict(), f"{path}.meta")
            
            # Save ensemble configuration
            ensemble_data = {
                'ensemble_method': self.ensemble_method,
                'model_weights': self.model_weights,
                'is_trained': self.is_trained,
                'training_history': self.training_history,
                'config': self.config,
                'metadata': {
                    'version': '1.0',
                    'timestamp': datetime.now().isoformat(),
                    'num_models': len(self.models)
                }
            }
            
            with open(f"{path}.json", 'w') as f:
                json.dump(ensemble_data, f, indent=2)
            
            # Save individual models
            for i, model in enumerate(self.models):
                if isinstance(model, TransformerModel):
                    model.save_model(f"{path}_model_{i}_transformer")
                elif isinstance(model, PPOAgent):
                    model.save_model(f"{path}_model_{i}_ppo")
            
            return True
        
        except Exception as e:
            logger.info(f"Error saving ensemble model: {str(e)}")
            return False
    
    def load_model(self, path: str) -> bool:
        """
        Load the ensemble model from disk.
        
        Args:
            path: Path to load the model from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load ensemble configuration
            with open(f"{path}.json", 'r') as f:
                ensemble_data = json.load(f)
            
            self.ensemble_method = ensemble_data['ensemble_method']
            self.model_weights = ensemble_data['model_weights']
            self.is_trained = ensemble_data['is_trained']
            self.training_history = ensemble_data['training_history']
            self.config = ensemble_data['config']
            
            # Load meta-model if exists
            if os.path.exists(f"{path}.meta"):
                # Create meta-model with correct input size
                input_size = len(self.model_weights)
                self.meta_model = torch.nn.Linear(input_size, 1)
                self.meta_model.load_state_dict(torch.load(f"{path}.meta"))
                self.meta_model.to(self.device)
            
            # Load individual models
            self.models = []
            for i in range(ensemble_data['metadata']['num_models']):
                # Try loading as TransformerModel
                transformer_path = f"{path}_model_{i}_transformer"
                ppo_path = f"{path}_model_{i}_ppo"
                
                if os.path.exists(f"{transformer_path}.pt"):
                    model = TransformerModel()
                    if model.load_model(transformer_path):
                        self.models.append(model)
                
                elif os.path.exists(f"{ppo_path}.pt"):
                    model = PPOAgent()
                    if model.load_model(ppo_path):
                        self.models.append(model)
            
            # Verify models were loaded
            if len(self.models) != ensemble_data['metadata']['num_models']:
                logger.info(f"Warning: Only {len(self.models)} of {ensemble_data['metadata']['num_models']} models were loaded")
            
            return True
        
        except Exception as e:
            logger.info(f"Error loading ensemble model: {str(e)}")
            return False


class AdaptiveEnsemble(ModelEnsemble):
    """
    Adaptive ensemble that dynamically adjusts model weights based on recent performance.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the AdaptiveEnsemble.
        
        Args:
            config: Configuration dictionary with ensemble parameters
        """
        super().__init__(config)
        self.adaptation_window = self.config.get('adaptation_window', 20)
        self.adaptation_rate = self.config.get('adaptation_rate', 0.1)
        self.performance_history = []
    
    def update_weights(self, df: pd.DataFrame, target_col: str = 'close') -> None:
        """
        Update model weights based on recent performance.
        
        Args:
            df: DataFrame containing recent market data
            target_col: Target column for prediction
        """
        if len(df) < self.adaptation_window:
            return
        
        recent_data = df.tail(self.adaptation_window)
        model_errors = []
        
        # Calculate errors for each model
        for model in self.models:
            if isinstance(model, TransformerModel):
                errors = []
                for i in range(len(recent_data) - 20):  # Assuming window_size=20
                    try:
                        pred = model.predict(recent_data.iloc[i:i+20])
                        actual = recent_data[target_col].values[i+20]
                        error = (pred[0] - actual) ** 2
                        errors.append(error)
                    except Exception:
                        errors.append(float('inf'))
                
                if errors:
                    model_errors.append(np.mean(errors))
                else:
                    model_errors.append(float('inf'))
        
        # Convert errors to weights (lower error = higher weight)
        if all(np.isinf(err) for err in model_errors):
            # If all models have infinite error, use equal weights
            new_weights = [1.0 / len(self.models) for _ in self.models]
        else:
            # Replace infinite errors with max finite error * 2
            max_finite_error = max([err for err in model_errors if not np.isinf(err)], default=1.0)
            model_errors = [err if not np.isinf(err) else max_finite_error * 2 for err in model_errors]
            
            # Convert errors to weights (inverse error)
            inverse_errors = [1.0 / (err + 1e-10) for err in model_errors]
            total_inverse = sum(inverse_errors)
            new_weights = [err / total_inverse for err in inverse_errors]
        
        # Update weights using exponential moving average
        for i in range(len(self.model_weights)):
            self.model_weights[i] = (1 - self.adaptation_rate) * self.model_weights[i] + self.adaptation_rate * new_weights[i]
        
        # Record performance
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'model_errors': model_errors,
            'new_weights': new_weights,
            'updated_weights': self.model_weights
        })
    
    def predict_price(self, df: pd.DataFrame, n_future: int = 1, adapt: bool = True) -> np.ndarray:
        """
        Generate price predictions using the adaptive ensemble.
        
        Args:
            df: DataFrame containing market data
            n_future: Number of future time steps to predict
            adapt: Whether to adapt weights based on recent performance
            
        Returns:
            Array of predicted prices
        """
        # Update weights if adaptation is enabled
        if adapt and len(df) > self.adaptation_window:
            self.update_weights(df)
        
        # Call parent method for prediction
        return super().predict_price(df, n_future)


class HierarchicalEnsemble:
    """
    Hierarchical ensemble that combines multiple ensemble models for different timeframes.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the HierarchicalEnsemble.
        
        Args:
            config: Configuration dictionary with ensemble parameters
        """
        self.config = config or {}
        self.timeframes = self.config.get('timeframes', ['short', 'medium', 'long'])
        self.ensembles = {}
        
        # Create ensemble for each timeframe
        for timeframe in self.timeframes:
            self.ensembles[timeframe] = AdaptiveEnsemble(
                self.config.get(f'{timeframe}_config', {})
            )
        
        # Timeframe weights
        self.timeframe_weights = self.config.get('timeframe_weights', {})
        if not self.timeframe_weights:
            # Default to equal weights
            self.timeframe_weights = {tf: 1.0 / len(self.timeframes) for tf in self.timeframes}
    
    def add_model(self, model: Union[TransformerModel, PPOAgent], timeframe: str, weight: float = 1.0) -> None:
        """
        Add a model to a specific timeframe ensemble.
        
        Args:
            model: The model to add
            timeframe: The timeframe ensemble to add the model to
            weight: Initial weight for the model
        """
        if timeframe not in self.ensembles:
            raise ValueError(f"Unknown timeframe: {timeframe}")
        
        self.ensembles[timeframe].add_model(model, weight)
    
    def predict_price(self, df: pd.DataFrame, n_future: int = 1) -> np.ndarray:
        """
        Generate price predictions using the hierarchical ensemble.
        
        Args:
            df: DataFrame containing market data
            n_future: Number of future time steps to predict
            
        Returns:
            Array of predicted prices
        """
        predictions = {}
        valid_timeframes = []
        
        # Get predictions from each timeframe ensemble
        for timeframe, ensemble in self.ensembles.items():
            try:
                pred = ensemble.predict_price(df, n_future)
                predictions[timeframe] = pred
                valid_timeframes.append(timeframe)
            except Exception as e:
                logger.info(f"Error in {timeframe} ensemble: {str(e)}")
        
        if not predictions:
            raise ValueError("No valid predictions from any timeframe ensemble")
        
        # Combine predictions using timeframe weights
        valid_weights = {tf: self.timeframe_weights[tf] for tf in valid_timeframes}
        total_weight = sum(valid_weights.values())
        normalized_weights = {tf: w / total_weight for tf, w in valid_weights.items()}
        
        # Weighted average of predictions
        ensemble_pred = np.zeros_like(list(predictions.values())[0])
        for timeframe, pred in predictions.items():
            ensemble_pred += pred * normalized_weights[timeframe]
        
        return ensemble_pred
    
    def get_trading_action(self, df: pd.DataFrame) -> Tuple[int, Dict[str, float]]:
        """
        Get trading action using the hierarchical ensemble.
        
        Args:
            df: DataFrame containing market data
            
        Returns:
            Tuple of (action, probabilities)
        """
        actions = {}
        probs_dict = {}
        valid_timeframes = []
        
        # Get actions from each timeframe ensemble
        for timeframe, ensemble in self.ensembles.items():
            try:
                action, probs = ensemble.get_trading_action(df)
                actions[timeframe] = action
                probs_dict[timeframe] = probs
                valid_timeframes.append(timeframe)
            except Exception as e:
                logger.info(f"Error in {timeframe} ensemble: {str(e)}")
        
        if not actions:
            raise ValueError("No valid actions from any timeframe ensemble")
        
        # Combine probabilities using timeframe weights
        valid_weights = {tf: self.timeframe_weights[tf] for tf in valid_timeframes}
        total_weight = sum(valid_weights.values())
        normalized_weights = {tf: w / total_weight for tf, w in valid_weights.items()}
        
        # Weighted average of probabilities
        combined_probs = {'hold': 0.0, 'buy': 0.0, 'sell': 0.0}
        for timeframe, probs in probs_dict.items():
            for action, prob in probs.items():
                combined_probs[action] += prob * normalized_weights[timeframe]
        
        # Select action with highest probability
        action_map = {'hold': 0, 'buy': 1, 'sell': 2}
        ensemble_action = action_map[max(combined_probs, key=combined_probs.get)]
        
        return ensemble_action, combined_probs
    
    def train(self, df: pd.DataFrame, target_col: str = 'close') -> Dict[str, Any]:
        """
        Train all ensemble models.
        
        Args:
            df: DataFrame containing market data
            target_col: Target column for prediction
            
        Returns:
            Dictionary with training results for each timeframe
        """
        results = {}
        
        for timeframe, ensemble in self.ensembles.items():
            try:
                logger.info(f"Training {timeframe} ensemble...")
                if isinstance(ensemble, AdaptiveEnsemble):
                    # For adaptive ensembles, train the meta-model
                    history = ensemble.train_meta_model(df, target_col)
                    results[timeframe] = {
                        'success': True,
                        'history': history
                    }
                else:
                    # For regular ensembles, just update weights
                    ensemble.update_weights(df, target_col)
                    results[timeframe] = {
                        'success': True,
                        'weights': ensemble.model_weights
                    }
            except Exception as e:
                logger.info(f"Error training {timeframe} ensemble: {str(e)}")
                results[timeframe] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def save_model(self, path: str) -> bool:
        """
        Save the hierarchical ensemble model to disk.
        
        Args:
            path: Path to save the model
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Save hierarchical configuration
            hierarchical_data = {
                'timeframes': self.timeframes,
                'timeframe_weights': self.timeframe_weights,
                'config': self.config,
                'metadata': {
                    'version': '1.0',
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            with open(f"{path}.json", 'w') as f:
                json.dump(hierarchical_data, f, indent=2)
            
            # Save individual ensembles
            for timeframe, ensemble in self.ensembles.items():
                ensemble.save_model(f"{path}_{timeframe}")
            
            return True
        
        except Exception as e:
            logger.info(f"Error saving hierarchical ensemble: {str(e)}")
            return False
    
    def load_model(self, path: str) -> bool:
        """
        Load the hierarchical ensemble model from disk.
        
        Args:
            path: Path to load the model from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load hierarchical configuration
            with open(f"{path}.json", 'r') as f:
                hierarchical_data = json.load(f)
            
            self.timeframes = hierarchical_data['timeframes']
            self.timeframe_weights = hierarchical_data['timeframe_weights']
            self.config = hierarchical_data['config']
            
            # Load individual ensembles
            self.ensembles = {}
            for timeframe in self.timeframes:
                ensemble_path = f"{path}_{timeframe}"
                
                # Determine ensemble type from config
                ensemble_config = self.config.get(f'{timeframe}_config', {})
                if ensemble_config.get('adaptive', True):
                    ensemble = AdaptiveEnsemble(ensemble_config)
                else:
                    ensemble = ModelEnsemble(ensemble_config)
                
                if ensemble.load_model(ensemble_path):
                    self.ensembles[timeframe] = ensemble
                else:
                    logger.info(f"Warning: Failed to load ensemble for timeframe {timeframe}")
            
            return True
        
        except Exception as e:
            logger.info(f"Error loading hierarchical ensemble: {str(e)}")
            return False
