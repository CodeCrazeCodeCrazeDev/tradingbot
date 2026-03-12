"""
Machine learning pipeline for AlphaAlgo 2.0
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
import logging
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ModelMetrics:
    """Model performance metrics."""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    confusion_matrix: np.ndarray
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class FeatureProcessor:
    """
    Feature engineering and preprocessing.
    Handles technical indicators and derived features.
    """
    
    def __init__(
        self,
        feature_config: Dict,
        scale_features: bool = True
    ):
        self.feature_config = feature_config
        self.scale_features = scale_features
        
        # Preprocessing
        self.scalers = {}
        self.feature_names = []
        
        logger.info("✅ Feature Processor initialized")
    
    def create_features(
        self,
        data: pd.DataFrame,
        is_training: bool = True
    ) -> pd.DataFrame:
        """
        Create features from raw data.
        
        Args:
            data: Raw price/volume data
            is_training: Whether in training mode
        
        Returns:
            DataFrame with engineered features
        """
        features = pd.DataFrame(index=data.index)
        
        # Price features
        if 'price' in self.feature_config:
            price_features = self._create_price_features(data)
            features = pd.concat([features, price_features], axis=1)
        
        # Volume features
        if 'volume' in self.feature_config:
            volume_features = self._create_volume_features(data)
            features = pd.concat([features, volume_features], axis=1)
        
        # Technical indicators
        if 'indicators' in self.feature_config:
            indicator_features = self._create_indicator_features(data)
            features = pd.concat([features, indicator_features], axis=1)
        
        # Scale features
        if self.scale_features:
            features = self._scale_features(features, is_training)
        
        if is_training:
            self.feature_names = features.columns.tolist()
        
        return features
    
    def _create_price_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create price-based features."""
        features = pd.DataFrame(index=data.index)
        config = self.feature_config['price']
        
        # Returns
        if config.get('returns', True):
            features['returns'] = data['close'].pct_change()
            features['log_returns'] = np.log1p(features['returns'])
        
        # Moving averages
        if 'ma_windows' in config:
            for window in config['ma_windows']:
                features[f'sma_{window}'] = data['close'].rolling(window).mean()
                features[f'sma_{window}_slope'] = features[f'sma_{window}'].diff()
        
        # Price levels
        if config.get('levels', True):
            features['price_level'] = (data['close'] - data['close'].rolling(20).min()) / \
                                    (data['close'].rolling(20).max() - data['close'].rolling(20).min())
        
        return features
    
    def _create_volume_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create volume-based features."""
        features = pd.DataFrame(index=data.index)
        config = self.feature_config['volume']
        
        # Volume changes
        if config.get('changes', True):
            features['volume_change'] = data['volume'].pct_change()
            features['volume_ma_ratio'] = data['volume'] / data['volume'].rolling(20).mean()
        
        # Volume profiles
        if 'profile_windows' in config:
            for window in config['profile_windows']:
                features[f'volume_profile_{window}'] = data['volume'].rolling(window).sum() / \
                                                     data['volume'].rolling(window).mean()
        
        return features
    
    def _create_indicator_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create technical indicator features."""
        features = pd.DataFrame(index=data.index)
        config = self.feature_config['indicators']
        
        # RSI
        if config.get('rsi', True):
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            features['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        if config.get('macd', True):
            exp1 = data['close'].ewm(span=12, adjust=False).mean()
            exp2 = data['close'].ewm(span=26, adjust=False).mean()
            features['macd'] = exp1 - exp2
            features['macd_signal'] = features['macd'].ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands
        if config.get('bbands', True):
            ma20 = data['close'].rolling(20).mean()
            std20 = data['close'].rolling(20).std()
            features['bb_upper'] = ma20 + (std20 * 2)
            features['bb_lower'] = ma20 - (std20 * 2)
            features['bb_width'] = (features['bb_upper'] - features['bb_lower']) / ma20
        
        return features
    
    def _scale_features(
        self,
        features: pd.DataFrame,
        is_training: bool
    ) -> pd.DataFrame:
        """Scale features using StandardScaler."""
        scaled_features = pd.DataFrame(index=features.index)
        
        for column in features.columns:
            if is_training:
                scaler = StandardScaler()
                scaled_data = scaler.fit_transform(
                    features[[column]].fillna(0)
                )
                self.scalers[column] = scaler
            else:
                scaler = self.scalers[column]
                scaled_data = scaler.transform(
                    features[[column]].fillna(0)
                )
            
            scaled_features[column] = scaled_data.flatten()
        
        return scaled_features


class MarketPredictor(nn.Module):
    """
    Neural network for market prediction.
    Uses LSTM architecture with attention.
    """
    
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2
    ):
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True
        )
        
        # Attention mechanism
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1)
        )
        
        # Output layers
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 3)  # UP, DOWN, NEUTRAL
        )
    
    def forward(
        self,
        x: torch.Tensor,
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass with attention."""
        # LSTM output
        lstm_out, hidden = self.lstm(x, hidden)
        
        # Attention weights
        attention_weights = self.attention(lstm_out)
        attention_weights = torch.softmax(attention_weights, dim=1)
        
        # Apply attention
        context = torch.sum(lstm_out * attention_weights, dim=1)
        
        # Final prediction
        output = self.fc(context)
        
        return output, attention_weights


class MLPipeline:
    """
    Complete machine learning pipeline.
    Handles data processing, training, and prediction.
    """
    
    def __init__(
        self,
        feature_config: Dict,
        model_params: Dict,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.feature_processor = FeatureProcessor(feature_config)
        self.device = device
        
        # Model parameters
        self.model_params = model_params
        self.model = None
        
        # Training history
        self.train_history = []
        
        logger.info("✅ ML Pipeline initialized")
        logger.info(f"   Device: {device}")
    
    def prepare_data(
        self,
        data: pd.DataFrame,
        sequence_length: int,
        is_training: bool = True
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Prepare data for model.
        
        Args:
            data: Raw market data
            sequence_length: Length of input sequences
            is_training: Whether in training mode
        
        Returns:
            Tuple of (features, labels)
        """
        # Create features
        features = self.feature_processor.create_features(
            data,
            is_training
        )
        
        # Create sequences
        sequences = []
        labels = []
        
        for i in range(len(features) - sequence_length):
            seq = features.iloc[i:i+sequence_length].values
            
            if is_training:
                # Calculate future returns
                future_return = data['close'].iloc[i+sequence_length+5] / \
                              data['close'].iloc[i+sequence_length] - 1
                
                # Create label
                if future_return > 0.001:
                    label = 0  # UP
                elif future_return < -0.001:
                    label = 1  # DOWN
                else:
                    label = 2  # NEUTRAL
                
                labels.append(label)
            
            sequences.append(seq)
        
        # Convert to tensors
        X = torch.FloatTensor(sequences).to(self.device)
        
        if is_training:
            y = torch.LongTensor(labels).to(self.device)
        else:
            y = None
        
        return X, y
    
    def train(
        self,
        train_data: pd.DataFrame,
        val_data: pd.DataFrame,
        sequence_length: int = 20,
        batch_size: int = 32,
        epochs: int = 100,
        learning_rate: float = 0.001
    ) -> Dict:
        """
        Train the model.
        
        Args:
            train_data: Training data
            val_data: Validation data
            sequence_length: Length of input sequences
            batch_size: Training batch size
            epochs: Number of epochs
            learning_rate: Learning rate
        
        Returns:
            Training history
        """
        try:
            logger.info("🚀 Starting model training...")
            
            # Prepare data
            X_train, y_train = self.prepare_data(
                train_data,
                sequence_length,
                is_training=True
            )
            
            X_val, y_val = self.prepare_data(
                val_data,
                sequence_length,
                is_training=True
            )
            
            # Initialize model
            self.model = MarketPredictor(
                input_dim=len(self.feature_processor.feature_names),
                **self.model_params
            ).to(self.device)
            
            # Loss and optimizer
            criterion = nn.CrossEntropyLoss()
            optimizer = torch.optim.Adam(
                self.model.parameters(),
                lr=learning_rate
            )
            
            # Training loop
            best_val_loss = float('inf')
            patience = 10
            patience_counter = 0
            
            for epoch in range(epochs):
                # Training
                self.model.train()
                train_losses = []
                
                for i in range(0, len(X_train), batch_size):
                    batch_X = X_train[i:i+batch_size]
                    batch_y = y_train[i:i+batch_size]
                    
                    optimizer.zero_grad()
                    
                    outputs, _ = self.model(batch_X)
                    loss = criterion(outputs, batch_y)
                    
                    loss.backward()
                    optimizer.step()
                    
                    train_losses.append(loss.item())
                
                # Validation
                self.model.eval()
                val_losses = []
                val_preds = []
                val_true = []
                
                with torch.no_grad():
                    for i in range(0, len(X_val), batch_size):
                        batch_X = X_val[i:i+batch_size]
                        batch_y = y_val[i:i+batch_size]
                        
                        outputs, _ = self.model(batch_X)
                        loss = criterion(outputs, batch_y)
                        
                        val_losses.append(loss.item())
                        val_preds.extend(outputs.argmax(dim=1).cpu().numpy())
                        val_true.extend(batch_y.cpu().numpy())
                
                # Calculate metrics
                train_loss = np.mean(train_losses)
                val_loss = np.mean(val_losses)
                val_metrics = self._calculate_metrics(val_true, val_preds)
                
                # Record history
                self.train_history.append({
                    'epoch': epoch + 1,
                    'train_loss': train_loss,
                    'val_loss': val_loss,
                    'val_metrics': val_metrics
                })
                
                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if patience_counter >= patience:
                    logger.info(f"Early stopping at epoch {epoch + 1}")
                    break
                
                # Log progress
                if (epoch + 1) % 10 == 0:
                    logger.info(
                        f"Epoch {epoch + 1}/{epochs} - "
                        f"Train Loss: {train_loss:.4f}, "
                        f"Val Loss: {val_loss:.4f}, "
                        f"Accuracy: {val_metrics.accuracy:.4f}"
                    )
            
            logger.info("✅ Training completed")
            return self.train_history
            
        except Exception as e:
            logger.error(f"❌ Training error: {str(e)}")
            raise
    
    def predict(
        self,
        data: pd.DataFrame,
        sequence_length: int = 20
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate predictions.
        
        Args:
            data: Market data
            sequence_length: Length of input sequences
        
        Returns:
            Tuple of (predictions, attention_weights)
        """
        try:
            if self.model is None:
                raise ValueError("Model not trained")
            
            # Prepare data
            X, _ = self.prepare_data(
                data,
                sequence_length,
                is_training=False
            )
            
            # Generate predictions
            self.model.eval()
            predictions = []
            attention_weights = []
            
            with torch.no_grad():
                outputs, attn = self.model(X)
                predictions = outputs.softmax(dim=1).cpu().numpy()
                attention_weights = attn.cpu().numpy()
            
            return predictions, attention_weights
            
        except Exception as e:
            logger.error(f"❌ Prediction error: {str(e)}")
            raise
    
    def _calculate_metrics(
        self,
        y_true: List[int],
        y_pred: List[int]
    ) -> ModelMetrics:
        """Calculate model performance metrics."""
        from sklearn.metrics import (
            accuracy_score,
            precision_score,
            recall_score,
            f1_score,
            roc_auc_score,
            confusion_matrix
        )
        
        return ModelMetrics(
            accuracy=accuracy_score(y_true, y_pred),
            precision=precision_score(y_true, y_pred, average='weighted'),
            recall=recall_score(y_true, y_pred, average='weighted'),
            f1_score=f1_score(y_true, y_pred, average='weighted'),
            roc_auc=roc_auc_score(y_true, y_pred, multi_class='ovr'),
            confusion_matrix=confusion_matrix(y_true, y_pred)
        )
    
    def save_model(self, filepath: str):
        """Save trained model."""
        if self.model is None:
            logger.warning("⚠️ No model to save")
            return
        
        torch.save({
            'model_state': self.model.state_dict(),
            'feature_processor': self.feature_processor,
            'model_params': self.model_params,
            'train_history': self.train_history
        }, filepath)
        
        logger.info(f"💾 Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model."""
        state = torch.load(filepath)
        
        self.feature_processor = state['feature_processor']
        self.model_params = state['model_params']
        self.train_history = state['train_history']
        
        self.model = MarketPredictor(
            input_dim=len(self.feature_processor.feature_names),
            **self.model_params
        ).to(self.device)
        
        self.model.load_state_dict(state['model_state'])
        
        logger.info(f"📂 Model loaded from {filepath}")
    
    def plot_training_history(
        self,
        filename: Optional[str] = None
    ):
        """Plot training history."""
        try:
            import matplotlib.pyplot as plt
            
            # Create figure
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
            
            # Get history data
            epochs = [h['epoch'] for h in self.train_history]
            train_loss = [h['train_loss'] for h in self.train_history]
            val_loss = [h['val_loss'] for h in self.train_history]
            accuracy = [h['val_metrics'].accuracy for h in self.train_history]
            
            # Plot loss
            ax1.plot(epochs, train_loss, label='Train Loss')
            ax1.plot(epochs, val_loss, label='Val Loss')
            ax1.set_title('Training History')
            ax1.set_xlabel('Epoch')
            ax1.set_ylabel('Loss')
            ax1.legend()
            ax1.grid(True)
            
            # Plot accuracy
            ax2.plot(epochs, accuracy, label='Validation Accuracy')
            ax2.set_title('Model Accuracy')
            ax2.set_xlabel('Epoch')
            ax2.set_ylabel('Accuracy')
            ax2.legend()
            ax2.grid(True)
            
            plt.tight_layout()
            
            if filename:
                plt.savefig(filename)
                logger.info(f"✅ Training plot saved to {filename}")
            else:
                plt.show()
            
        except ImportError:
            logger.warning("⚠️ matplotlib not available for plotting")
