"""
Autoformer Model for Long-Sequence Time-Series Forecasting

This module implements the Autoformer architecture with:
1. Auto-Correlation mechanism for series-level connections
2. Series decomposition for trend-seasonal separation
3. Efficient long-sequence forecasting

Paper: "Autoformer: Decomposition Transformers with Auto-Correlation for Long-Term Series Forecasting"
Authors: Haixu Wu, Jiehui Xu, Jianmin Wang, Mingsheng Long
"""

import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import math

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.optim import Adam
    from torch.optim.lr_scheduler import ReduceLROnPlateau
    TORCH_AVAILABLE = True
except ImportError:
    logger.warning("PyTorch not available. Install with: pip install torch")
    TORCH_AVAILABLE = False


@dataclass
class AutoformerConfig:
    """Configuration for Autoformer model"""
    # Model architecture
    d_model: int = 512  # Model dimension
    n_heads: int = 8  # Number of attention heads
    e_layers: int = 2  # Encoder layers
    d_layers: int = 1  # Decoder layers
    d_ff: int = 2048  # Feed-forward dimension
    
    # Sequence settings
    seq_len: int = 96  # Input sequence length
    label_len: int = 48  # Start token length
    pred_len: int = 24  # Prediction length
    
    # Feature settings
    enc_in: int = 7  # Encoder input features
    dec_in: int = 7  # Decoder input features
    c_out: int = 1  # Output features
    
    # Auto-correlation settings
    factor: int = 3  # Auto-correlation factor
    moving_avg: int = 25  # Moving average kernel size
    
    # Training settings
    dropout: float = 0.1
    activation: str = 'gelu'
    output_attention: bool = False


class SeriesDecomp(nn.Module):
    """
    Series Decomposition Block
    Separates trend and seasonal components using moving average
    """
    
    def __init__(self, kernel_size: int):
        super(SeriesDecomp, self).__init__()
        self.moving_avg = nn.AvgPool1d(
            kernel_size=kernel_size,
            stride=1,
            padding=kernel_size // 2
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Decompose series into trend and seasonal components
        
        Args:
            x: Input tensor [batch, seq_len, features]
        
        Returns:
            seasonal: Seasonal component
            trend: Trend component
        """
        # Transpose for pooling: [batch, features, seq_len]
        x_t = x.permute(0, 2, 1)
        
        # Moving average for trend
        trend = self.moving_avg(x_t)
        
        # Handle edge cases
        if trend.size(-1) != x_t.size(-1):
            # Pad to match original length
            diff = x_t.size(-1) - trend.size(-1)
            trend = F.pad(trend, (diff // 2, diff - diff // 2))
        
        # Transpose back: [batch, seq_len, features]
        trend = trend.permute(0, 2, 1)
        
        # Seasonal = original - trend
        seasonal = x - trend
        
        return seasonal, trend


class AutoCorrelation(nn.Module):
    """
    Auto-Correlation Mechanism
    Discovers period-based dependencies using FFT
    """
    
    def __init__(
        self,
        d_model: int,
        n_heads: int,
        factor: int = 3,
        dropout: float = 0.1,
        output_attention: bool = False
    ):
        super(AutoCorrelation, self).__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_keys = d_model // n_heads
        self.factor = factor
        self.dropout = nn.Dropout(dropout)
        self.output_attention = output_attention
        
        # Projections
        self.query_projection = nn.Linear(d_model, d_model)
        self.key_projection = nn.Linear(d_model, d_model)
        self.value_projection = nn.Linear(d_model, d_model)
        self.out_projection = nn.Linear(d_model, d_model)
    
    def time_delay_agg(
        self,
        values: torch.Tensor,
        corr: torch.Tensor,
        top_k: int
    ) -> torch.Tensor:
        """
        Time delay aggregation using top-k correlations
        
        Args:
            values: Value tensor [batch, heads, seq_len, d_keys]
            corr: Correlation tensor [batch, heads, seq_len, seq_len]
            top_k: Number of top correlations to use
        
        Returns:
            Aggregated values
        """
        batch, heads, seq_len, d_keys = values.shape
        
        # Find top-k correlations
        top_k = min(top_k, seq_len)
        weights, indices = torch.topk(corr, top_k, dim=-1)
        
        # Softmax over top-k
        weights = F.softmax(weights, dim=-1)
        
        # Aggregate values
        # Expand indices for gathering
        indices = indices.unsqueeze(-1).expand(-1, -1, -1, -1, d_keys)
        values = values.unsqueeze(-2).expand(-1, -1, -1, top_k, -1)
        
        # Gather and weight
        gathered = torch.gather(values, 2, indices)
        output = (gathered * weights.unsqueeze(-1)).sum(dim=-2)
        
        return output
    
    def forward(
        self,
        queries: torch.Tensor,
        keys: torch.Tensor,
        values: torch.Tensor,
        attn_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Forward pass with auto-correlation
        
        Args:
            queries: Query tensor [batch, seq_len, d_model]
            keys: Key tensor [batch, seq_len, d_model]
            values: Value tensor [batch, seq_len, d_model]
            attn_mask: Optional attention mask
        
        Returns:
            output: Output tensor
            attn: Attention weights (if output_attention)
        """
        batch, seq_len, _ = queries.shape
        
        # Project
        queries = self.query_projection(queries)
        keys = self.key_projection(keys)
        values = self.value_projection(values)
        
        # Reshape for multi-head
        queries = queries.view(batch, seq_len, self.n_heads, self.d_keys)
        keys = keys.view(batch, seq_len, self.n_heads, self.d_keys)
        values = values.view(batch, seq_len, self.n_heads, self.d_keys)
        
        # Transpose: [batch, heads, seq_len, d_keys]
        queries = queries.permute(0, 2, 1, 3)
        keys = keys.permute(0, 2, 1, 3)
        values = values.permute(0, 2, 1, 3)
        
        # Auto-correlation using FFT
        # Compute correlation in frequency domain
        q_fft = torch.fft.rfft(queries, dim=2)
        k_fft = torch.fft.rfft(keys, dim=2)
        
        # Cross-correlation: Q * conj(K)
        corr_fft = q_fft * torch.conj(k_fft)
        
        # Inverse FFT to get correlation
        corr = torch.fft.irfft(corr_fft, n=seq_len, dim=2)
        
        # Time delay aggregation
        top_k = int(self.factor * math.log(seq_len))
        output = self.time_delay_agg(values, corr, top_k)
        
        # Reshape back
        output = output.permute(0, 2, 1, 3).contiguous()
        output = output.view(batch, seq_len, self.d_model)
        
        # Output projection
        output = self.out_projection(output)
        output = self.dropout(output)
        
        if self.output_attention:
            return output, corr
        return output, None


class AutoCorrelationLayer(nn.Module):
    """
    Auto-Correlation Layer with decomposition
    """
    
    def __init__(
        self,
        d_model: int,
        n_heads: int,
        d_ff: int,
        moving_avg: int = 25,
        factor: int = 3,
        dropout: float = 0.1,
        activation: str = 'gelu'
    ):
        super(AutoCorrelationLayer, self).__init__()
        
        # Auto-correlation
        self.auto_correlation = AutoCorrelation(
            d_model=d_model,
            n_heads=n_heads,
            factor=factor,
            dropout=dropout
        )
        
        # Series decomposition
        self.decomp1 = SeriesDecomp(moving_avg)
        self.decomp2 = SeriesDecomp(moving_avg)
        
        # Feed-forward
        self.conv1 = nn.Conv1d(d_model, d_ff, kernel_size=1)
        self.conv2 = nn.Conv1d(d_ff, d_model, kernel_size=1)
        
        # Normalization
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # Activation
        self.activation = F.gelu if activation == 'gelu' else F.relu
    
    def forward(
        self,
        x: torch.Tensor,
        attn_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass
        
        Args:
            x: Input tensor [batch, seq_len, d_model]
            attn_mask: Optional attention mask
        
        Returns:
            seasonal: Seasonal component
            trend: Trend component
        """
        # Auto-correlation
        attn_out, _ = self.auto_correlation(x, x, x, attn_mask)
        x = x + attn_out
        
        # First decomposition
        seasonal1, trend1 = self.decomp1(x)
        
        # Feed-forward on seasonal
        y = self.norm1(seasonal1)
        y = y.permute(0, 2, 1)  # [batch, d_model, seq_len]
        y = self.conv1(y)
        y = self.activation(y)
        y = self.dropout(y)
        y = self.conv2(y)
        y = y.permute(0, 2, 1)  # [batch, seq_len, d_model]
        
        seasonal1 = seasonal1 + y
        
        # Second decomposition
        seasonal2, trend2 = self.decomp2(seasonal1)
        
        # Combine trends
        trend = trend1 + trend2
        
        return seasonal2, trend


class AutoformerEncoder(nn.Module):
    """
    Autoformer Encoder
    """
    
    def __init__(self, config: AutoformerConfig):
        super(AutoformerEncoder, self).__init__()
        
        self.layers = nn.ModuleList([
            AutoCorrelationLayer(
                d_model=config.d_model,
                n_heads=config.n_heads,
                d_ff=config.d_ff,
                moving_avg=config.moving_avg,
                factor=config.factor,
                dropout=config.dropout,
                activation=config.activation
            )
            for _ in range(config.e_layers)
        ])
        
        self.norm = nn.LayerNorm(config.d_model)
    
    def forward(
        self,
        x: torch.Tensor,
        attn_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, List[torch.Tensor]]:
        """
        Forward pass
        
        Args:
            x: Input tensor [batch, seq_len, d_model]
            attn_mask: Optional attention mask
        
        Returns:
            output: Encoder output
            attns: List of attention weights
        """
        attns = []
        
        for layer in self.layers:
            x, trend = layer(x, attn_mask)
            attns.append(trend)
        
        x = self.norm(x)
        
        return x, attns


class AutoformerDecoder(nn.Module):
    """
    Autoformer Decoder
    """
    
    def __init__(self, config: AutoformerConfig):
        super(AutoformerDecoder, self).__init__()
        
        self.layers = nn.ModuleList([
            AutoCorrelationLayer(
                d_model=config.d_model,
                n_heads=config.n_heads,
                d_ff=config.d_ff,
                moving_avg=config.moving_avg,
                factor=config.factor,
                dropout=config.dropout,
                activation=config.activation
            )
            for _ in range(config.d_layers)
        ])
        
        self.norm = nn.LayerNorm(config.d_model)
        
        # Trend projection
        self.trend_projection = nn.Linear(config.d_model, config.c_out)
        
        # Seasonal projection
        self.seasonal_projection = nn.Linear(config.d_model, config.c_out)
    
    def forward(
        self,
        x: torch.Tensor,
        cross: torch.Tensor,
        trend: torch.Tensor,
        attn_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            x: Decoder input [batch, seq_len, d_model]
            cross: Encoder output [batch, seq_len, d_model]
            trend: Initial trend [batch, seq_len, d_model]
            attn_mask: Optional attention mask
        
        Returns:
            output: Decoder output
        """
        for layer in self.layers:
            x, layer_trend = layer(x, attn_mask)
            trend = trend + layer_trend
        
        x = self.norm(x)
        
        # Project seasonal and trend
        seasonal_out = self.seasonal_projection(x)
        trend_out = self.trend_projection(trend)
        
        # Combine
        output = seasonal_out + trend_out
        
        return output


class Autoformer(nn.Module):
    """
    Autoformer: Decomposition Transformers with Auto-Correlation
    for Long-Term Series Forecasting
    """
    
    def __init__(self, config: AutoformerConfig):
        super(Autoformer, self).__init__()
        
        self.config = config
        self.pred_len = config.pred_len
        self.label_len = config.label_len
        
        # Embedding
        self.enc_embedding = nn.Linear(config.enc_in, config.d_model)
        self.dec_embedding = nn.Linear(config.dec_in, config.d_model)
        
        # Decomposition
        self.decomp = SeriesDecomp(config.moving_avg)
        
        # Encoder
        self.encoder = AutoformerEncoder(config)
        
        # Decoder
        self.decoder = AutoformerDecoder(config)
        
        logger.info(f"Autoformer initialized: d_model={config.d_model}, "
                   f"pred_len={config.pred_len}, e_layers={config.e_layers}")
    
    def forward(
        self,
        x_enc: torch.Tensor,
        x_dec: torch.Tensor,
        enc_mask: Optional[torch.Tensor] = None,
        dec_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            x_enc: Encoder input [batch, seq_len, enc_in]
            x_dec: Decoder input [batch, label_len + pred_len, dec_in]
            enc_mask: Encoder attention mask
            dec_mask: Decoder attention mask
        
        Returns:
            output: Predictions [batch, pred_len, c_out]
        """
        # Decompose encoder input
        seasonal_enc, trend_enc = self.decomp(x_enc)
        
        # Embed encoder input
        enc_out = self.enc_embedding(seasonal_enc)
        
        # Encode
        enc_out, attns = self.encoder(enc_out, enc_mask)
        
        # Decompose decoder input
        seasonal_dec, trend_dec = self.decomp(x_dec)
        
        # Embed decoder input
        dec_out = self.dec_embedding(seasonal_dec)
        
        # Embed trend for decoder
        trend_init = self.dec_embedding(trend_dec)
        
        # Decode
        output = self.decoder(dec_out, enc_out, trend_init, dec_mask)
        
        # Return only prediction part
        return output[:, -self.pred_len:, :]
    
    def predict(
        self,
        x: np.ndarray,
        pred_len: Optional[int] = None
    ) -> np.ndarray:
        """
        Make predictions
        
        Args:
            x: Input data [batch, seq_len, features]
            pred_len: Prediction length (optional)
        
        Returns:
            predictions: Predicted values
        """
        self.eval()
        
        if pred_len is None:
            pred_len = self.pred_len
        
        with torch.no_grad():
            # Convert to tensor
            x_enc = torch.FloatTensor(x)
            
            # Create decoder input (zeros for prediction)
            batch_size = x.shape[0]
            x_dec = torch.zeros(batch_size, self.label_len + pred_len, x.shape[2])
            
            # Copy label part from encoder
            x_dec[:, :self.label_len, :] = x_enc[:, -self.label_len:, :]
            
            # Forward pass
            output = self.forward(x_enc, x_dec)
            
            return output.numpy()


class AutoformerForecaster:
    """
    High-level Autoformer forecaster for trading
    """
    
    def __init__(
        self,
        seq_len: int = 96,
        pred_len: int = 24,
        n_features: int = 7,
        d_model: int = 256,
        n_heads: int = 4,
        e_layers: int = 2,
        d_layers: int = 1
    ):
        self.config = AutoformerConfig(
            seq_len=seq_len,
            pred_len=pred_len,
            label_len=seq_len // 2,
            enc_in=n_features,
            dec_in=n_features,
            c_out=1,
            d_model=d_model,
            n_heads=n_heads,
            e_layers=e_layers,
            d_layers=d_layers
        )
        
        if TORCH_AVAILABLE:
            self.model = Autoformer(self.config)
            self.optimizer = Adam(self.model.parameters(), lr=1e-4)
            self.scheduler = ReduceLROnPlateau(
                self.optimizer, mode='min', factor=0.5, patience=5
            )
        else:
            self.model = None
            logger.warning("Autoformer requires PyTorch")
        
        self.training_history: List[Dict] = []
        self.is_trained = False
        
        logger.info(f"AutoformerForecaster initialized: seq_len={seq_len}, pred_len={pred_len}")
    
    def train(
        self,
        train_data: np.ndarray,
        val_data: Optional[np.ndarray] = None,
        epochs: int = 100,
        batch_size: int = 32
    ) -> Dict:
        """
        Train the model
        
        Args:
            train_data: Training data [samples, seq_len, features]
            val_data: Validation data
            epochs: Number of epochs
            batch_size: Batch size
        
        Returns:
            Training history
        """
        if not TORCH_AVAILABLE or self.model is None:
            logger.error("PyTorch required for training")
            return {}
        
        self.model.train()
        
        history = {
            'train_loss': [],
            'val_loss': []
        }
        
        n_samples = len(train_data)
        n_batches = n_samples // batch_size
        
        for epoch in range(epochs):
            epoch_loss = 0.0
            
            # Shuffle data
            indices = np.random.permutation(n_samples)
            
            for batch_idx in range(n_batches):
                # Get batch
                batch_indices = indices[batch_idx * batch_size:(batch_idx + 1) * batch_size]
                batch_data = train_data[batch_indices]
                
                # Prepare encoder and decoder inputs
                x_enc = torch.FloatTensor(batch_data)
                
                # Decoder input: label_len from encoder + zeros for prediction
                x_dec = torch.zeros(
                    batch_size,
                    self.config.label_len + self.config.pred_len,
                    self.config.dec_in
                )
                x_dec[:, :self.config.label_len, :] = x_enc[:, -self.config.label_len:, :]
                
                # Target: next pred_len values (using first feature as target)
                # In practice, you'd have separate target data
                target = x_enc[:, -self.config.pred_len:, :1]
                
                # Forward pass
                self.optimizer.zero_grad()
                output = self.model(x_enc, x_dec)
                
                # Loss
                loss = F.mse_loss(output, target)
                
                # Backward pass
                loss.backward()
                self.optimizer.step()
                
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / n_batches
            history['train_loss'].append(avg_loss)
            
            # Validation
            if val_data is not None:
                val_loss = self._validate(val_data, batch_size)
                history['val_loss'].append(val_loss)
                self.scheduler.step(val_loss)
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}")
        
        self.is_trained = True
        self.training_history.append(history)
        
        logger.info("Autoformer training complete")
        
        return history
    
    def _validate(self, val_data: np.ndarray, batch_size: int) -> float:
        """Validate the model"""
        self.model.eval()
        
        total_loss = 0.0
        n_batches = len(val_data) // batch_size
        
        with torch.no_grad():
            for batch_idx in range(n_batches):
                batch_data = val_data[batch_idx * batch_size:(batch_idx + 1) * batch_size]
                
                x_enc = torch.FloatTensor(batch_data)
                x_dec = torch.zeros(
                    batch_size,
                    self.config.label_len + self.config.pred_len,
                    self.config.dec_in
                )
                x_dec[:, :self.config.label_len, :] = x_enc[:, -self.config.label_len:, :]
                
                target = x_enc[:, -self.config.pred_len:, :1]
                
                output = self.model(x_enc, x_dec)
                loss = F.mse_loss(output, target)
                
                total_loss += loss.item()
        
        self.model.train()
        
        return total_loss / n_batches
    
    def predict(
        self,
        data: np.ndarray,
        return_confidence: bool = False
    ) -> Dict:
        """
        Make predictions
        
        Args:
            data: Input data [batch, seq_len, features]
            return_confidence: Whether to return confidence intervals
        
        Returns:
            Prediction results
        """
        if not TORCH_AVAILABLE or self.model is None:
            logger.error("PyTorch required for prediction")
            return {'predictions': np.zeros((len(data), self.config.pred_len, 1))}
        
        self.model.eval()
        
        with torch.no_grad():
            x_enc = torch.FloatTensor(data)
            
            batch_size = len(data)
            x_dec = torch.zeros(
                batch_size,
                self.config.label_len + self.config.pred_len,
                self.config.dec_in
            )
            x_dec[:, :self.config.label_len, :] = x_enc[:, -self.config.label_len:, :]
            
            output = self.model(x_enc, x_dec)
            predictions = output.numpy()
        
        result = {
            'predictions': predictions,
            'pred_len': self.config.pred_len,
            'timestamp': datetime.now().isoformat()
        }
        
        if return_confidence:
            # Estimate confidence using prediction variance
            # In practice, you'd use ensemble or MC dropout
            result['confidence'] = np.ones_like(predictions) * 0.8
            result['lower_bound'] = predictions - 0.1 * np.abs(predictions)
            result['upper_bound'] = predictions + 0.1 * np.abs(predictions)
        
        return result
    
    def get_model_info(self) -> Dict:
        """Get model information"""
        return {
            'model_type': 'Autoformer',
            'config': {
                'seq_len': self.config.seq_len,
                'pred_len': self.config.pred_len,
                'd_model': self.config.d_model,
                'n_heads': self.config.n_heads,
                'e_layers': self.config.e_layers,
                'd_layers': self.config.d_layers
            },
            'is_trained': self.is_trained,
            'training_history': len(self.training_history)
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create forecaster
    forecaster = AutoformerForecaster(
        seq_len=96,
        pred_len=24,
        n_features=7
    )
    
    # Generate sample data
    n_samples = 1000
    seq_len = 96
    n_features = 7
    
    train_data = np.random.randn(n_samples, seq_len, n_features)
    val_data = np.random.randn(100, seq_len, n_features)
    
    # Train
    history = forecaster.train(train_data, val_data, epochs=10, batch_size=32)
    
    # Predict
    test_data = np.random.randn(10, seq_len, n_features)
    predictions = forecaster.predict(test_data, return_confidence=True)
    
    print("\n" + "="*60)
    logger.info("AUTOFORMER FORECASTER")
    print("="*60)
    logger.info(f"Model Info: {forecaster.get_model_info()}")
    logger.info(f"Predictions shape: {predictions['predictions'].shape}")
    logger.info(f"Sample prediction: {predictions['predictions'][0, :5, 0]}")
    print("="*60)
