"""
Time-Series Transformer for Superior Price Forecasting

Implements state-of-the-art transformer architecture for financial time series prediction.
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


class PositionalEncoding(nn.Module):
    """Positional encoding for transformer"""
    
    def __init__(self, d_model: int, max_len: int = 5000):
        super(PositionalEncoding, self).__init__()
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model))
        
        pe[:, 0:2] = torch.sin(position * div_term)
        pe[:, 1:2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x):
        return x + self.pe[:, :x.size(1)]


class TimeSeriesTransformer(nn.Module):
    """
    Transformer model for time series forecasting
    
    Uses multi-head attention to capture long-range dependencies in price data.
    """
    
    def __init__(
        self,
        input_dim: int,
        d_model: int = 256,
        nhead: int = 8,
        num_encoder_layers: int = 6,
        num_decoder_layers: int = 6,
        dim_feedforward: int = 1024,
        dropout: float = 0.1,
        forecast_horizon: int = 10
    ):
        super(TimeSeriesTransformer, self).__init__()
        
        self.d_model = d_model
        self.forecast_horizon = forecast_horizon
        
        # Input embedding
        self.input_embedding = nn.Linear(input_dim, d_model)
        self.pos_encoder = PositionalEncoding(d_model)
        
        # Transformer
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_encoder_layers
        )
        
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_decoder = nn.TransformerDecoder(
            decoder_layer,
            num_layers=num_decoder_layers
        )
        
        # Output layers
        self.output_projection = nn.Sequential(
            nn.Linear(d_model, dim_feedforward // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(dim_feedforward // 2, 1)
        )
        
        # Uncertainty estimation
        self.uncertainty_head = nn.Sequential(
            nn.Linear(d_model, dim_feedforward // 4),
            nn.ReLU(),
            nn.Linear(dim_feedforward // 4, 1),
            nn.Softplus()  # Ensure positive uncertainty
        )
        
        self._init_weights()
    
    def _init_weights(self):
        """Initialize weights"""
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)
    
    def forward(self, src, tgt=None):
        """
        Forward pass
        
        Args:
            src: Source sequence (batch, seq_len, input_dim)
            tgt: Target sequence for teacher forcing (batch, forecast_horizon, input_dim)
            
        Returns:
            predictions, uncertainty
        """
        # Embed input
        src = self.input_embedding(src) * np.sqrt(self.d_model)
        src = self.pos_encoder(src)
        
        # Encode
        memory = self.transformer_encoder(src)
        
        # Decode
        if tgt is None:
            # Autoregressive generation
            tgt = torch.zeros(src.size(0), self.forecast_horizon, self.d_model).to(src.device)
        else:
            tgt = self.input_embedding(tgt) * np.sqrt(self.d_model)
        
        tgt = self.pos_encoder(tgt)
        output = self.transformer_decoder(tgt, memory)
        
        # Project to predictions
        predictions = self.output_projection(output).squeeze(-1)
        uncertainty = self.uncertainty_head(output).squeeze(-1)
        
        return predictions, uncertainty


class TransformerForecaster:
    """
    Transformer-based price forecaster
    
    Provides superior forecasting with uncertainty quantification.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Model parameters
        self.input_dim = self.config.get('input_dim', 10)  # OHLCV + indicators
        self.d_model = self.config.get('d_model', 256)
        self.nhead = self.config.get('nhead', 8)
        self.num_encoder_layers = self.config.get('num_encoder_layers', 6)
        self.num_decoder_layers = self.config.get('num_decoder_layers', 6)
        self.dim_feedforward = self.config.get('dim_feedforward', 1024)
        self.dropout = self.config.get('dropout', 0.1)
        self.forecast_horizon = self.config.get('forecast_horizon', 10)
        
        # Training parameters
        self.learning_rate = self.config.get('learning_rate', 1e-4)
        self.batch_size = self.config.get('batch_size', 32)
        self.max_grad_norm = self.config.get('max_grad_norm', 1.0)
        
        # Initialize model
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = TimeSeriesTransformer(
            input_dim=self.input_dim,
            d_model=self.d_model,
            nhead=self.nhead,
            num_encoder_layers=self.num_encoder_layers,
            num_decoder_layers=self.num_decoder_layers,
            dim_feedforward=self.dim_feedforward,
            dropout=self.dropout,
            forecast_horizon=self.forecast_horizon
        ).to(self.device)
        
        self.optimizer = optim.AdamW(self.model.parameters(), lr=self.learning_rate)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=5
        )
        
        # Loss tracking
        self.train_losses = deque(maxlen=100)
        self.val_losses = deque(maxlen=100)
        
        logger.info(f"Transformer Forecaster initialized on {self.device}")
        logger.info(f"Model parameters: {sum(p.numel() for p in self.model.parameters()):,}")
    
    def forecast(
        self,
        historical_data: np.ndarray,
        return_uncertainty: bool = True
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Generate price forecast
        
        Args:
            historical_data: Historical price data (seq_len, input_dim)
            return_uncertainty: Whether to return uncertainty estimates
            
        Returns:
            predictions, uncertainty (if requested)
        """
        self.model.eval()
        
        with torch.no_grad():
            # Prepare input
            src = torch.FloatTensor(historical_data).unsqueeze(0).to(self.device)
            
            # Generate forecast
            predictions, uncertainty = self.model(src)
            
            predictions = predictions.cpu().numpy()[0]
            uncertainty = uncertainty.cpu().numpy()[0] if return_uncertainty else None
        
        return predictions, uncertainty
    
    def train_step(self, batch_data: Dict) -> float:
        """
        Single training step
        
        Args:
            batch_data: Dictionary with 'src' and 'tgt' tensors
            
        Returns:
            loss value
        """
        self.model.train()
        
        src = batch_data['src'].to(self.device)
        tgt = batch_data['tgt'].to(self.device)
        tgt_y = batch_data['tgt_y'].to(self.device)
        
        # Forward pass
        predictions, uncertainty = self.model(src, tgt)
        
        # Negative log-likelihood loss with uncertainty
        mse_loss = (predictions - tgt_y) ** 2
        nll_loss = 0.5 * (mse_loss / uncertainty + torch.log(uncertainty))
        loss = nll_loss.mean()
        
        # Backward pass
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.model.parameters(), self.max_grad_norm)
        self.optimizer.step()
        
        return loss.item()
    
    def train_epoch(self, train_loader) -> float:
        """Train for one epoch"""
        epoch_loss = 0
        num_batches = 0
        
        for batch in train_loader:
            loss = self.train_step(batch)
            epoch_loss += loss
            num_batches += 1
        
        avg_loss = epoch_loss / num_batches
        self.train_losses.append(avg_loss)
        
        return avg_loss
    
    def validate(self, val_loader) -> float:
        """Validate model"""
        self.model.eval()
        val_loss = 0
        num_batches = 0
        
        with torch.no_grad():
            for batch in val_loader:
                src = batch['src'].to(self.device)
                tgt = batch['tgt'].to(self.device)
                tgt_y = batch['tgt_y'].to(self.device)
                
                predictions, uncertainty = self.model(src, tgt)
                
                mse_loss = (predictions - tgt_y) ** 2
                nll_loss = 0.5 * (mse_loss / uncertainty + torch.log(uncertainty))
                loss = nll_loss.mean()
                
                val_loss += loss.item()
                num_batches += 1
        
        avg_val_loss = val_loss / num_batches
        self.val_losses.append(avg_val_loss)
        self.scheduler.step(avg_val_loss)
        
        return avg_val_loss
    
    def get_attention_weights(self, historical_data: np.ndarray) -> np.ndarray:
        """
        Extract attention weights for interpretability
        
        Args:
            historical_data: Historical price data
            
        Returns:
            attention weights
        """
        self.model.eval()
        
        with torch.no_grad():
            src = torch.FloatTensor(historical_data).unsqueeze(0).to(self.device)
            
            # Hook to capture attention weights
            attention_weights = []
            
            def hook_fn(module, input, output):
                attention_weights.append(output[1])
            
            # Register hooks
            hooks = []
            for layer in self.model.transformer_encoder.layers:
                hook = layer.self_attn.register_forward_hook(hook_fn)
                hooks.append(hook)
            
            # Forward pass
            _ = self.model(src)
            
            # Remove hooks
            for hook in hooks:
                hook.remove()
        
        return torch.stack(attention_weights).cpu().numpy()
    
    def save_model(self, path: str):
        """Save model checkpoint"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'config': self.config
        }, path)
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load model checkpoint"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        logger.info(f"Model loaded from {path}")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'input_dim': 10,
        'd_model': 256,
        'nhead': 8,
        'num_encoder_layers': 6,
        'num_decoder_layers': 6,
        'forecast_horizon': 10
    }
    
    forecaster = TransformerForecaster(config)
    
    # Generate sample data
    historical_data = np.random.randn(100, 10)
    
    # Make forecast
    predictions, uncertainty = forecaster.forecast(historical_data)
    
    logger.info(f"Predictions shape: {predictions.shape}")
    logger.info(f"Uncertainty shape: {uncertainty.shape}")
    logger.info(f"Mean prediction: {predictions.mean():.4f}")
    logger.info(f"Mean uncertainty: {uncertainty.mean():.4f}")
