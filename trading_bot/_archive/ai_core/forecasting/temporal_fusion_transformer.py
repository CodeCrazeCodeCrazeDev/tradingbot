"""
Temporal Fusion Transformer (TFT) for Multi-Horizon Forecasting

Paper: "Temporal Fusion Transformers for Interpretable Multi-horizon Time Series Forecasting"
Lim et al., 2021

Features:
- Multi-horizon probabilistic forecasting
- Variable selection network
- Temporal self-attention
- Quantile regression for uncertainty
- Interpretable architecture
"""

try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
import numpy

logger = logging.getLogger(__name__)


class VariableSelectionNetwork(nn.Module):
    """Variable selection network for feature importance."""
    
    def __init__(self, input_dim: int, hidden_dim: int, num_vars: int, dropout: float = 0.1):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_vars = num_vars
        
        # GRN for each variable
        self.grns = nn.ModuleList([
            GatedResidualNetwork(input_dim, hidden_dim, hidden_dim, dropout)
            for _ in range(num_vars)
        ])
        
        # Variable selection weights
        self.softmax = nn.Softmax(dim=-1)
        self.weight_network = GatedResidualNetwork(
            hidden_dim * num_vars, hidden_dim, num_vars, dropout
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: [batch, num_vars, input_dim]
        Returns:
            selected: [batch, hidden_dim]
            weights: [batch, num_vars]
        """
        batch_size = x.shape[0]
        
        # Process each variable
        var_outputs = []
        for i in range(self.num_vars):
            var_outputs.append(self.grns[i](x[:, i, :]))
        
        var_outputs = torch.stack(var_outputs, dim=1)  # [batch, num_vars, hidden_dim]
        
        # Compute selection weights
        flattened = var_outputs.view(batch_size, -1)
        weights = self.weight_network(flattened)
        weights = self.softmax(weights)  # [batch, num_vars]
        
        # Weighted combination
        weights_expanded = weights.unsqueeze(-1)  # [batch, num_vars, 1]
        selected = torch.sum(var_outputs * weights_expanded, dim=1)  # [batch, hidden_dim]
        
        return selected, weights


class GatedResidualNetwork(nn.Module):
    """Gated Residual Network (GRN) for feature processing."""
    
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, dropout: float = 0.1):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc_gate = nn.Linear(hidden_dim, output_dim)
        self.fc_output = nn.Linear(hidden_dim, output_dim)
        
        self.dropout = nn.Dropout(dropout)
        self.ln = nn.LayerNorm(output_dim)
        
        # Skip connection
        if input_dim != output_dim:
            self.skip = nn.Linear(input_dim, output_dim)
        else:
            self.skip = None
    
    def forward(self, x: torch.Tensor, context: Optional[torch.Tensor] = None) -> torch.Tensor:
        # Primary path
        h = F.elu(self.fc1(x))
        h = self.dropout(h)
        h = self.fc2(h)
        
        # Gating
        gate = torch.sigmoid(self.fc_gate(h))
        output = self.fc_output(h)
        output = gate * output
        
        # Skip connection
        if self.skip is not None:
            skip = self.skip(x)
        else:
            skip = x
        
        return self.ln(output + skip)


class InterpretableMultiHeadAttention(nn.Module):
    """Multi-head attention with interpretability."""
    
    def __init__(self, d_model: int, num_heads: int, dropout: float = 0.1):
        super().__init__()
        assert d_model % num_heads == 0
        
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        
        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)
        self.w_o = nn.Linear(d_model, d_model)
        
        self.dropout = nn.Dropout(dropout)
        self.attention_weights = None  # Store for interpretability
    
    def forward(self, query: torch.Tensor, key: torch.Tensor, value: torch.Tensor,
                mask: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        batch_size = query.shape[0]
        
        # Linear projections
        Q = self.w_q(query).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        K = self.w_k(key).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        V = self.w_v(value).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        
        # Attention scores
        scores = torch.matmul(Q, K.transpose(-2, -1)) / np.sqrt(self.d_k)
        
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        attention = F.softmax(scores, dim=-1)
        self.attention_weights = attention.detach()  # Store for interpretability
        attention = self.dropout(attention)
        
        # Apply attention to values
        context = torch.matmul(attention, V)
        context = context.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)
        
        output = self.w_o(context)
        
        return output, attention


class TemporalFusionTransformer(nn.Module):
    """
    Temporal Fusion Transformer for multi-horizon forecasting.
    
    Architecture:
    1. Variable selection networks (static, historical, future)
    2. LSTM encoder for historical context
    3. Multi-head attention for temporal dependencies
    4. Quantile outputs for uncertainty
    """
    
    def __init__(
        self,
        num_static_vars: int,
        num_historical_vars: int,
        num_future_vars: int,
        hidden_dim: int = 256,
        num_heads: int = 4,
        num_quantiles: int = 3,
        dropout: float = 0.1,
        horizon: int = 10
    ):
        super().__init__()
        
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.num_quantiles = num_quantiles
        self.horizon = horizon
        
        # Variable selection networks
        self.static_vsn = VariableSelectionNetwork(
            1, hidden_dim, num_static_vars, dropout
        )
        self.historical_vsn = VariableSelectionNetwork(
            1, hidden_dim, num_historical_vars, dropout
        )
        self.future_vsn = VariableSelectionNetwork(
            1, hidden_dim, num_future_vars, dropout
        )
        
        # LSTM encoder
        self.lstm_encoder = nn.LSTM(
            hidden_dim, hidden_dim, batch_first=True, dropout=dropout
        )
        
        # LSTM decoder
        self.lstm_decoder = nn.LSTM(
            hidden_dim, hidden_dim, batch_first=True, dropout=dropout
        )
        
        # Self-attention
        self.attention = InterpretableMultiHeadAttention(hidden_dim, num_heads, dropout)
        
        # Gated residual networks
        self.grn_encoder = GatedResidualNetwork(hidden_dim, hidden_dim, hidden_dim, dropout)
        self.grn_decoder = GatedResidualNetwork(hidden_dim, hidden_dim, hidden_dim, dropout)
        
        # Quantile output layers
        self.quantile_layers = nn.ModuleList([
            nn.Linear(hidden_dim, 1) for _ in range(num_quantiles)
        ])
        
        # Static context enrichment
        self.static_enrichment = GatedResidualNetwork(
            hidden_dim, hidden_dim, hidden_dim, dropout
        )
        
        logger.info(f"TFT initialized: hidden_dim={hidden_dim}, horizon={horizon}")
    
    def forward(
        self,
        static_inputs: torch.Tensor,
        historical_inputs: torch.Tensor,
        future_inputs: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Args:
            static_inputs: [batch, num_static_vars]
            historical_inputs: [batch, seq_len, num_historical_vars]
            future_inputs: [batch, horizon, num_future_vars]
        
        Returns:
            Dictionary with predictions and attention weights
        """
        batch_size = historical_inputs.shape[0]
        seq_len = historical_inputs.shape[1]
        
        # 1. Variable selection
        # Static
        static_expanded = static_inputs.unsqueeze(-1)  # [batch, num_static_vars, 1]
        static_selected, static_weights = self.static_vsn(static_expanded)
        
        # Historical
        historical_selected_list = []
        historical_weights_list = []
        for t in range(seq_len):
            hist_t = historical_inputs[:, t, :].unsqueeze(-1)
            selected, weights = self.historical_vsn(hist_t)
            historical_selected_list.append(selected)
            historical_weights_list.append(weights)
        
        historical_selected = torch.stack(historical_selected_list, dim=1)
        historical_weights = torch.stack(historical_weights_list, dim=1)
        
        # Future
        future_selected_list = []
        future_weights_list = []
        for t in range(self.horizon):
            fut_t = future_inputs[:, t, :].unsqueeze(-1)
            selected, weights = self.future_vsn(fut_t)
            future_selected_list.append(selected)
            future_weights_list.append(weights)
        
        future_selected = torch.stack(future_selected_list, dim=1)
        future_weights = torch.stack(future_weights_list, dim=1)
        
        # 2. Static context enrichment
        static_context = self.static_enrichment(static_selected)
        
        # 3. LSTM encoding
        lstm_input = historical_selected
        encoder_output, (h_n, c_n) = self.lstm_encoder(lstm_input)
        
        # 4. LSTM decoding
        decoder_input = future_selected
        decoder_output, _ = self.lstm_decoder(decoder_input, (h_n, c_n))
        
        # 5. Self-attention
        attention_output, attention_weights = self.attention(
            decoder_output, encoder_output, encoder_output
        )
        
        # 6. Gated residual network
        grn_output = self.grn_decoder(attention_output)
        
        # 7. Quantile predictions
        quantile_outputs = []
        for quantile_layer in self.quantile_layers:
            q_output = quantile_layer(grn_output)
            quantile_outputs.append(q_output)
        
        quantile_outputs = torch.stack(quantile_outputs, dim=-1)  # [batch, horizon, 1, num_quantiles]
        quantile_outputs = quantile_outputs.squeeze(2)  # [batch, horizon, num_quantiles]
        
        return {
            'predictions': quantile_outputs,
            'attention_weights': attention_weights,
            'static_weights': static_weights,
            'historical_weights': historical_weights,
            'future_weights': future_weights
        }
    
    def predict(
        self,
        static_inputs: torch.Tensor,
        historical_inputs: torch.Tensor,
        future_inputs: torch.Tensor,
        quantiles: List[float] = [0.1, 0.5, 0.9]
    ) -> Dict[str, np.ndarray]:
        """Make predictions with uncertainty quantification."""
        self.eval()
        with torch.no_grad():
            outputs = self.forward(static_inputs, historical_inputs, future_inputs)
            predictions = outputs['predictions'].cpu().numpy()
            
            return {
                'median': predictions[:, :, 1],  # 50th percentile
                'lower': predictions[:, :, 0],   # 10th percentile
                'upper': predictions[:, :, 2],   # 90th percentile
                'attention_weights': outputs['attention_weights'].cpu().numpy(),
                'static_importance': outputs['static_weights'].cpu().numpy(),
                'historical_importance': outputs['historical_weights'].cpu().numpy(),
                'future_importance': outputs['future_weights'].cpu().numpy()
            }


class QuantileLoss(nn.Module):
    """Quantile loss for probabilistic forecasting."""
    
    def __init__(self, quantiles: List[float]):
        super().__init__()
        self.quantiles = quantiles
    
    def forward(self, predictions: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Args:
            predictions: [batch, horizon, num_quantiles]
            targets: [batch, horizon]
        """
        targets = targets.unsqueeze(-1)  # [batch, horizon, 1]
        losses = []
        
        for i, q in enumerate(self.quantiles):
            errors = targets - predictions[:, :, i:i+1]
            loss = torch.max((q - 1) * errors, q * errors)
            losses.append(loss.mean())
        
        return sum(losses) / len(losses)


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*80)
    logger.info("TEMPORAL FUSION TRANSFORMER DEMO")
    print("="*80)
    
    # Create model
    model = TemporalFusionTransformer(
        num_static_vars=5,
        num_historical_vars=10,
        num_future_vars=3,
        hidden_dim=128,
        num_heads=4,
        horizon=10
    )
    
    # Create dummy data
    batch_size = 32
    seq_len = 50
    
    static = torch.randn(batch_size, 5)
    historical = torch.randn(batch_size, seq_len, 10)
    future = torch.randn(batch_size, 10, 3)
    
    # Forward pass
    outputs = model(static, historical, future)
    
    logger.info(f"\nInput shapes:")
    logger.info(f"  Static: {static.shape}")
    logger.info(f"  Historical: {historical.shape}")
    logger.info(f"  Future: {future.shape}")
    
    logger.info(f"\nOutput shapes:")
    logger.info(f"  Predictions: {outputs['predictions'].shape}")
    logger.info(f"  Attention: {outputs['attention_weights'].shape}")
    logger.info(f"  Static weights: {outputs['static_weights'].shape}")
    
    # Prediction
    predictions = model.predict(static, historical, future)
    logger.info(f"\nPrediction outputs:")
    for key, value in predictions.items():
        if isinstance(value, np.ndarray):
            logger.info(f"  {key}: {value.shape}")
    
    print("\n" + "="*80)
    logger.info("DEMO COMPLETE")
    print("="*80)
