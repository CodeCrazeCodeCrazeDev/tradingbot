"""
Ensemble Methods: Combine LSTM, CNN, and Transformer for Robust Predictions

Multi-model ensemble for superior forecasting accuracy and robustness.
"""

import numpy as np
try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import torch.optim as optim
from typing import Dict, List, Optional, Tuple
import logging
from collections import deque
import numpy

logger = logging.getLogger(__name__)


class LSTMPredictor(nn.Module):
    """LSTM-based predictor for sequential patterns"""
    
    def __init__(self, input_dim: int, hidden_dim: int = 128, num_layers: int = 3):
        super(LSTMPredictor, self).__init__()
        
        self.lstm = nn.LSTM(
            input_dim,
            hidden_dim,
            num_layers,
            batch_first=True,
            dropout=0.2,
            bidirectional=True
        )
        
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, 1)
        )
    
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        prediction = self.fc(lstm_out[:, -1, :])
        return prediction


class CNNPredictor(nn.Module):
    """CNN-based predictor for local patterns"""
    
    def __init__(self, input_dim: int, num_filters: int = 64):
        super(CNNPredictor, self).__init__()
        
        self.conv_layers = nn.Sequential(
            # First conv block
            nn.Conv1d(input_dim, num_filters, kernel_size=3, padding=1),
            nn.BatchNorm1d(num_filters),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            # Second conv block
            nn.Conv1d(num_filters, num_filters * 2, kernel_size=3, padding=1),
            nn.BatchNorm1d(num_filters * 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            # Third conv block
            nn.Conv1d(num_filters * 2, num_filters * 4, kernel_size=3, padding=1),
            nn.BatchNorm1d(num_filters * 4),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        
        self.fc = nn.Sequential(
            nn.Linear(num_filters * 4, num_filters),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(num_filters, 1)
        )
    
    def forward(self, x):
        # x: (batch, seq_len, input_dim) -> (batch, input_dim, seq_len)
        x = x.transpose(1, 2)
        
        conv_out = self.conv_layers(x)
        pooled = self.global_pool(conv_out).squeeze(-1)
        prediction = self.fc(pooled)
        
        return prediction


class TransformerPredictor(nn.Module):
    """Lightweight transformer predictor"""
    
    def __init__(self, input_dim: int, d_model: int = 128, nhead: int = 4, num_layers: int = 3):
        super(TransformerPredictor, self).__init__()
        
        self.input_projection = nn.Linear(input_dim, d_model)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=0.2,
            batch_first=True
        )
        
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.fc = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(d_model // 2, 1)
        )
    
    def forward(self, x):
        x = self.input_projection(x)
        transformer_out = self.transformer(x)
        prediction = self.fc(transformer_out[:, -1, :])
        return prediction


class EnsemblePredictor:
    """
    Ensemble predictor combining LSTM, CNN, and Transformer
    
    Uses weighted averaging with learned confidence weights.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Model parameters
        self.input_dim = self.config.get('input_dim', 10)
        self.hidden_dim = self.config.get('hidden_dim', 128)
        self.num_filters = self.config.get('num_filters', 64)
        self.d_model = self.config.get('d_model', 128)
        
        # Training parameters
        self.learning_rate = self.config.get('learning_rate', 1e-4)
        self.weight_decay = self.config.get('weight_decay', 1e-5)
        self.ensemble_method = self.config.get('ensemble_method', 'weighted')  # 'weighted', 'stacking', 'voting'
        
        # Initialize device
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Initialize models
        self.lstm_model = LSTMPredictor(self.input_dim, self.hidden_dim).to(self.device)
        self.cnn_model = CNNPredictor(self.input_dim, self.num_filters).to(self.device)
        self.transformer_model = TransformerPredictor(self.input_dim, self.d_model).to(self.device)
        
        # Ensemble weights (learnable)
        self.ensemble_weights = nn.Parameter(torch.ones(3) / 3).to(self.device)
        
        # Meta-learner for stacking
        if self.ensemble_method == 'stacking':
            self.meta_learner = nn.Sequential(
                nn.Linear(3, 16),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(16, 1)
            ).to(self.device)
        
        # Optimizers
        self.lstm_optimizer = optim.AdamW(
            self.lstm_model.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay
        )
        self.cnn_optimizer = optim.AdamW(
            self.cnn_model.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay
        )
        self.transformer_optimizer = optim.AdamW(
            self.transformer_model.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay
        )
        
        if self.ensemble_method == 'weighted':
            self.ensemble_optimizer = optim.AdamW(
                [self.ensemble_weights],
                lr=self.learning_rate * 0.1
            )
        elif self.ensemble_method == 'stacking':
            self.meta_optimizer = optim.AdamW(
                self.meta_learner.parameters(),
                lr=self.learning_rate
            )
        
        # Loss tracking
        self.train_losses = {
            'lstm': deque(maxlen=100),
            'cnn': deque(maxlen=100),
            'transformer': deque(maxlen=100),
            'ensemble': deque(maxlen=100)
        }
        
        logger.info(f"Ensemble Predictor initialized on {self.device}")
        logger.info(f"Ensemble method: {self.ensemble_method}")
        logger.info(f"Total parameters: {self._count_parameters():,}")
    
    def _count_parameters(self) -> int:
        """Count total trainable parameters"""
        total = 0
        total += sum(p.numel() for p in self.lstm_model.parameters())
        total += sum(p.numel() for p in self.cnn_model.parameters())
        total += sum(p.numel() for p in self.transformer_model.parameters())
        if self.ensemble_method == 'stacking':
            total += sum(p.numel() for p in self.meta_learner.parameters())
        return total
    
    def predict(self, x: np.ndarray, return_individual: bool = False) -> Dict:
        """
        Make ensemble prediction
        
        Args:
            x: Input data (batch, seq_len, input_dim) or (seq_len, input_dim)
            return_individual: Whether to return individual model predictions
            
        Returns:
            Dictionary with predictions and metadata
        """
        self.lstm_model.eval()
        self.cnn_model.eval()
        self.transformer_model.eval()
        
        # Handle single sample
        if x.ndim == 2:
            x = x[np.newaxis, ...]
        
        with torch.no_grad():
            x_tensor = torch.FloatTensor(x).to(self.device)
            
            # Get individual predictions
            lstm_pred = self.lstm_model(x_tensor)
            cnn_pred = self.cnn_model(x_tensor)
            transformer_pred = self.transformer_model(x_tensor)
            
            # Ensemble prediction
            if self.ensemble_method == 'weighted':
                # Softmax weights for proper normalization
                weights = torch.softmax(self.ensemble_weights, dim=0)
                ensemble_pred = (
                    weights[0] * lstm_pred +
                    weights[1] * cnn_pred +
                    weights[2] * transformer_pred
                )
            elif self.ensemble_method == 'stacking':
                # Stack predictions and use meta-learner
                stacked = torch.cat([lstm_pred, cnn_pred, transformer_pred], dim=1)
                ensemble_pred = self.meta_learner(stacked)
            else:  # voting (simple average)
                ensemble_pred = (lstm_pred + cnn_pred + transformer_pred) / 3
            
            # Calculate prediction variance (uncertainty)
            predictions = torch.stack([lstm_pred, cnn_pred, transformer_pred], dim=0)
            variance = predictions.var(dim=0)
        
        result = {
            'prediction': ensemble_pred.cpu().numpy().squeeze(),
            'uncertainty': variance.cpu().numpy().squeeze(),
            'confidence': 1.0 / (1.0 + variance.cpu().numpy().squeeze())
        }
        
        if return_individual:
            result['individual_predictions'] = {
                'lstm': lstm_pred.cpu().numpy().squeeze(),
                'cnn': cnn_pred.cpu().numpy().squeeze(),
                'transformer': transformer_pred.cpu().numpy().squeeze()
            }
            if self.ensemble_method == 'weighted':
                result['weights'] = torch.softmax(self.ensemble_weights, dim=0).cpu().numpy()
        
        return result
    
    def train_step(self, x: torch.Tensor, y: torch.Tensor) -> Dict[str, float]:
        """
        Single training step
        
        Args:
            x: Input tensor (batch, seq_len, input_dim)
            y: Target tensor (batch, 1)
            
        Returns:
            Dictionary of losses
        """
        self.lstm_model.train()
        self.cnn_model.train()
        self.transformer_model.train()
        
        x = x.to(self.device)
        y = y.to(self.device)
        
        # Train individual models
        lstm_pred = self.lstm_model(x)
        lstm_loss = nn.MSELoss()(lstm_pred, y)
        self.lstm_optimizer.zero_grad()
        lstm_loss.backward()
        self.lstm_optimizer.step()
        
        cnn_pred = self.cnn_model(x)
        cnn_loss = nn.MSELoss()(cnn_pred, y)
        self.cnn_optimizer.zero_grad()
        cnn_loss.backward()
        self.cnn_optimizer.step()
        
        transformer_pred = self.transformer_model(x)
        transformer_loss = nn.MSELoss()(transformer_pred, y)
        self.transformer_optimizer.zero_grad()
        transformer_loss.backward()
        self.transformer_optimizer.step()
        
        # Train ensemble
        with torch.no_grad():
            lstm_pred = self.lstm_model(x)
            cnn_pred = self.cnn_model(x)
            transformer_pred = self.transformer_model(x)
        
        if self.ensemble_method == 'weighted':
            weights = torch.softmax(self.ensemble_weights, dim=0)
            ensemble_pred = (
                weights[0] * lstm_pred +
                weights[1] * cnn_pred +
                weights[2] * transformer_pred
            )
            ensemble_loss = nn.MSELoss()(ensemble_pred, y)
            self.ensemble_optimizer.zero_grad()
            ensemble_loss.backward()
            self.ensemble_optimizer.step()
        elif self.ensemble_method == 'stacking':
            self.meta_learner.train()
            stacked = torch.cat([lstm_pred, cnn_pred, transformer_pred], dim=1)
            ensemble_pred = self.meta_learner(stacked)
            ensemble_loss = nn.MSELoss()(ensemble_pred, y)
            self.meta_optimizer.zero_grad()
            ensemble_loss.backward()
            self.meta_optimizer.step()
        else:
            ensemble_pred = (lstm_pred + cnn_pred + transformer_pred) / 3
            ensemble_loss = nn.MSELoss()(ensemble_pred, y)
        
        # Track losses
        losses = {
            'lstm': lstm_loss.item(),
            'cnn': cnn_loss.item(),
            'transformer': transformer_loss.item(),
            'ensemble': ensemble_loss.item()
        }
        
        for key, value in losses.items():
            self.train_losses[key].append(value)
        
        return losses
    
    def get_model_importance(self) -> Dict[str, float]:
        """
        Get importance scores for each model
        
        Returns:
            Dictionary of importance scores
        """
        if self.ensemble_method == 'weighted':
            weights = torch.softmax(self.ensemble_weights, dim=0).cpu().detach().numpy()
            return {
                'lstm': float(weights[0]),
                'cnn': float(weights[1]),
                'transformer': float(weights[2])
            }
        else:
            # Equal importance for other methods
            return {
                'lstm': 1/3,
                'cnn': 1/3,
                'transformer': 1/3
            }
    
    def save_models(self, path_prefix: str):
        """Save all models"""
        torch.save(self.lstm_model.state_dict(), f"{path_prefix}_lstm.pth")
        torch.save(self.cnn_model.state_dict(), f"{path_prefix}_cnn.pth")
        torch.save(self.transformer_model.state_dict(), f"{path_prefix}_transformer.pth")
        
        if self.ensemble_method == 'weighted':
            torch.save(self.ensemble_weights, f"{path_prefix}_weights.pth")
        elif self.ensemble_method == 'stacking':
            torch.save(self.meta_learner.state_dict(), f"{path_prefix}_meta.pth")
        
        logger.info(f"Models saved with prefix: {path_prefix}")
    
    def load_models(self, path_prefix: str):
        """Load all models"""
        self.lstm_model.load_state_dict(torch.load(f"{path_prefix}_lstm.pth", map_location=self.device))
        self.cnn_model.load_state_dict(torch.load(f"{path_prefix}_cnn.pth", map_location=self.device))
        self.transformer_model.load_state_dict(torch.load(f"{path_prefix}_transformer.pth", map_location=self.device))
        
        if self.ensemble_method == 'weighted':
            self.ensemble_weights = torch.load(f"{path_prefix}_weights.pth", map_location=self.device)
        elif self.ensemble_method == 'stacking':
            self.meta_learner.load_state_dict(torch.load(f"{path_prefix}_meta.pth", map_location=self.device))
        
        logger.info(f"Models loaded from prefix: {path_prefix}")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'input_dim': 10,
        'hidden_dim': 128,
        'ensemble_method': 'weighted'
    }
    
    ensemble = EnsemblePredictor(config)
    
    # Generate sample data
    x = np.random.randn(32, 100, 10)
    
    # Make prediction
    result = ensemble.predict(x[0], return_individual=True)
    
    logger.info(f"Ensemble prediction: {result['prediction']:.4f}")
    logger.info(f"Uncertainty: {result['uncertainty']:.4f}")
    logger.info(f"Confidence: {result['confidence']:.4f}")
    logger.info(f"Individual predictions: {result['individual_predictions']}")
    logger.info(f"Model importance: {ensemble.get_model_importance()}")
