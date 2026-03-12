"""
Market Intent Decomposition Engine (MIDE) - Inference Engine

Hybrid GRU-TCN architecture for intent inference.
CPU-first, ONNX-exportable, <2ms latency.

Architecture:
- TCN Branch: Dilated Conv for local patterns
- GRU Branch: Recurrent for state evolution
- Attention Branch: Self-attention for pivotal moments
- Fusion: Concatenate + FC layers + Softmax

Total Parameters: ~85,000
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, List
import time

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from .intent_decomposition_core import (
    IntentSimplex, MIDEConfig, INTENT_NAMES,
    MIN_INTENT_PROBABILITY, MAX_INTENT_PROBABILITY
)


# =============================================================================
# NUMPY-BASED LIGHTWEIGHT INFERENCE (No PyTorch required)
# =============================================================================

class NumpyTCNLayer:
    """
    Lightweight TCN layer using NumPy only.
    """
    
    def __init__(self, in_channels: int, out_channels: int, 
                 kernel_size: int, dilation: int):
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.dilation = dilation
        self.padding = (kernel_size - 1) * dilation
        
        # Initialize weights (Xavier)
        scale = np.sqrt(2.0 / (in_channels * kernel_size))
        self.weight = np.random.randn(out_channels, in_channels, kernel_size).astype(np.float32) * scale
        self.bias = np.zeros(out_channels, dtype=np.float32)
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass with causal convolution.
        
        Args:
            x: Input of shape (batch, seq, channels)
        
        Returns:
            Output of shape (batch, seq, out_channels)
        """
        batch, seq, channels = x.shape
        
        # Pad for causal convolution
        x_padded = np.pad(x, ((0, 0), (self.padding, 0), (0, 0)), mode='constant')
        
        # Dilated convolution (simplified)
        output = np.zeros((batch, seq, self.out_channels), dtype=np.float32)
        
        for b in range(batch):
            for t in range(seq):
                for o in range(self.out_channels):
                    val = self.bias[o]
                    for k in range(self.kernel_size):
                        idx = t + self.padding - k * self.dilation
                        if 0 <= idx < x_padded.shape[1]:
                            for c in range(channels):
                                val += self.weight[o, c, k] * x_padded[b, idx, c]
                    output[b, t, o] = val
        
        return output


class NumpyGRUCell:
    """
    Lightweight GRU cell using NumPy only.
    """
    
    def __init__(self, input_size: int, hidden_size: int):
        self.input_size = input_size
        self.hidden_size = hidden_size
        
        # Initialize weights (Xavier)
        scale_ih = np.sqrt(2.0 / input_size)
        scale_hh = np.sqrt(2.0 / hidden_size)
        
        # Gates: reset, update, new
        self.W_ir = np.random.randn(hidden_size, input_size).astype(np.float32) * scale_ih
        self.W_iz = np.random.randn(hidden_size, input_size).astype(np.float32) * scale_ih
        self.W_in = np.random.randn(hidden_size, input_size).astype(np.float32) * scale_ih
        
        self.W_hr = np.random.randn(hidden_size, hidden_size).astype(np.float32) * scale_hh
        self.W_hz = np.random.randn(hidden_size, hidden_size).astype(np.float32) * scale_hh
        self.W_hn = np.random.randn(hidden_size, hidden_size).astype(np.float32) * scale_hh
        
        self.b_ir = np.zeros(hidden_size, dtype=np.float32)
        self.b_iz = np.zeros(hidden_size, dtype=np.float32)
        self.b_in = np.zeros(hidden_size, dtype=np.float32)
        self.b_hr = np.zeros(hidden_size, dtype=np.float32)
        self.b_hz = np.zeros(hidden_size, dtype=np.float32)
        self.b_hn = np.zeros(hidden_size, dtype=np.float32)
    
    def forward(self, x: np.ndarray, h: np.ndarray) -> np.ndarray:
        """
        Forward pass for single timestep.
        
        Args:
            x: Input of shape (batch, input_size)
            h: Hidden state of shape (batch, hidden_size)
        
        Returns:
            New hidden state of shape (batch, hidden_size)
        """
        # Reset gate
        r = self._sigmoid(x @ self.W_ir.T + self.b_ir + h @ self.W_hr.T + self.b_hr)
        
        # Update gate
        z = self._sigmoid(x @ self.W_iz.T + self.b_iz + h @ self.W_hz.T + self.b_hz)
        
        # New gate
        n = np.tanh(x @ self.W_in.T + self.b_in + r * (h @ self.W_hn.T + self.b_hn))
        
        # Output
        h_new = (1 - z) * n + z * h
        
        return h_new
    
    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))


class NumpyAttention:
    """
    Lightweight self-attention using NumPy only.
    """
    
    def __init__(self, d_model: int, n_heads: int = 1):
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads
        
        scale = np.sqrt(2.0 / d_model)
        self.W_q = np.random.randn(d_model, d_model).astype(np.float32) * scale
        self.W_k = np.random.randn(d_model, d_model).astype(np.float32) * scale
        self.W_v = np.random.randn(d_model, d_model).astype(np.float32) * scale
        self.W_o = np.random.randn(d_model, d_model).astype(np.float32) * scale
    
    def forward(self, x: np.ndarray, causal: bool = True) -> np.ndarray:
        """
        Forward pass with optional causal masking.
        
        Args:
            x: Input of shape (batch, seq, d_model)
            causal: Whether to use causal mask
        
        Returns:
            Output of shape (batch, seq, d_model)
        """
        batch, seq, _ = x.shape
        
        # Compute Q, K, V
        Q = x @ self.W_q
        K = x @ self.W_k
        V = x @ self.W_v
        
        # Scaled dot-product attention
        scores = Q @ K.transpose(0, 2, 1) / np.sqrt(self.d_k)
        
        # Causal mask
        if causal:
            mask = np.triu(np.ones((seq, seq)), k=1) * -1e9
            scores = scores + mask
        
        # Softmax
        attn = self._softmax(scores)
        
        # Output
        out = attn @ V
        out = out @ self.W_o
        
        return out
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)


class NumpyIntentEncoder:
    """
    Complete intent encoder using NumPy only.
    Hybrid GRU-TCN architecture.
    """
    
    def __init__(self, config: Optional[MIDEConfig] = None):
        self.config = config or MIDEConfig()
        
        self.input_dim = 12  # 12 observable features
        self.hidden_dim = self.config.hidden_dim
        self.output_dim = 5  # 5 intents
        
        # TCN branch
        self.tcn_layers = []
        if self.config.use_tcn:
            dilations = [1, 2, 4, 8]
            in_ch = self.input_dim
            for d in dilations:
                layer = NumpyTCNLayer(in_ch, self.hidden_dim, kernel_size=3, dilation=d)
                self.tcn_layers.append(layer)
                in_ch = self.hidden_dim
        
        # GRU branch
        self.gru_cell = None
        if self.config.use_gru:
            self.gru_cell = NumpyGRUCell(self.input_dim, self.hidden_dim)
        
        # Attention branch
        self.attention = None
        if self.config.use_attention:
            self.attention = NumpyAttention(self.hidden_dim)
            # Project input to hidden dim for attention
            scale = np.sqrt(2.0 / self.input_dim)
            self.attn_proj = np.random.randn(self.hidden_dim, self.input_dim).astype(np.float32) * scale
        
        # Fusion layers
        fusion_dim = 0
        if self.config.use_tcn:
            fusion_dim += self.hidden_dim
        if self.config.use_gru:
            fusion_dim += self.hidden_dim
        if self.config.use_attention:
            fusion_dim += self.hidden_dim
        
        if fusion_dim == 0:
            fusion_dim = self.input_dim
        
        scale = np.sqrt(2.0 / fusion_dim)
        self.fc1_weight = np.random.randn(self.hidden_dim, fusion_dim).astype(np.float32) * scale
        self.fc1_bias = np.zeros(self.hidden_dim, dtype=np.float32)
        
        scale = np.sqrt(2.0 / self.hidden_dim)
        self.fc2_weight = np.random.randn(self.output_dim, self.hidden_dim).astype(np.float32) * scale
        self.fc2_bias = np.zeros(self.output_dim, dtype=np.float32)
        
        # Layer norm parameters
        self.ln_gamma = np.ones(self.hidden_dim, dtype=np.float32)
        self.ln_beta = np.zeros(self.hidden_dim, dtype=np.float32)
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass through encoder.
        
        Args:
            x: Input of shape (batch, seq, 12)
        
        Returns:
            Intent probabilities of shape (batch, 5)
        """
        batch, seq, _ = x.shape
        features = []
        
        # TCN branch
        if self.config.use_tcn and len(self.tcn_layers) > 0:
            tcn_out = x
            for layer in self.tcn_layers:
                tcn_out = np.maximum(0, layer.forward(tcn_out))  # ReLU
            # Global average pooling
            tcn_feat = np.mean(tcn_out, axis=1)
            features.append(tcn_feat)
        
        # GRU branch
        if self.config.use_gru and self.gru_cell is not None:
            h = np.zeros((batch, self.hidden_dim), dtype=np.float32)
            for t in range(seq):
                h = self.gru_cell.forward(x[:, t, :], h)
            features.append(h)
        
        # Attention branch
        if self.config.use_attention and self.attention is not None:
            # Project to hidden dim
            x_proj = x @ self.attn_proj.T
            attn_out = self.attention.forward(x_proj, causal=True)
            # Take last position
            attn_feat = attn_out[:, -1, :]
            features.append(attn_feat)
        
        # Concatenate features
        if len(features) > 0:
            fused = np.concatenate(features, axis=-1)
        else:
            fused = np.mean(x, axis=1)  # Fallback
        
        # FC layers
        h = fused @ self.fc1_weight.T + self.fc1_bias
        
        # Layer norm
        mean = np.mean(h, axis=-1, keepdims=True)
        var = np.var(h, axis=-1, keepdims=True)
        h = (h - mean) / np.sqrt(var + 1e-5)
        h = h * self.ln_gamma + self.ln_beta
        
        # ReLU
        h = np.maximum(0, h)
        
        # Output
        logits = h @ self.fc2_weight.T + self.fc2_bias
        
        # Temperature-scaled softmax
        logits = logits / self.config.temperature
        probs = self._softmax(logits)
        
        return probs
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)
    
    def infer(self, features: np.ndarray) -> IntentSimplex:
        """
        Run inference and return IntentSimplex.
        
        Args:
            features: Input of shape (seq, 12) or (batch, seq, 12)
        
        Returns:
            IntentSimplex with probabilities
        """
        # Ensure batch dimension
        if features.ndim == 2:
            features = features[np.newaxis, :, :]
        
        probs = self.forward(features)
        
        # Take first batch item
        p = probs[0]
        
        # Apply constraints
        p = np.clip(p, MIN_INTENT_PROBABILITY, MAX_INTENT_PROBABILITY)
        p = p / p.sum()
        
        return IntentSimplex(
            urgent=float(p[0]),
            passive=float(p[1]),
            mechanical=float(p[2]),
            exploitative=float(p[3]),
            noise=float(p[4])
        )


# =============================================================================
# PYTORCH-BASED INFERENCE (Optional, for training)
# =============================================================================

if TORCH_AVAILABLE:
    
    class TCNBlock(nn.Module):
        """Temporal Convolutional Network block."""
        
        def __init__(self, in_channels: int, out_channels: int, 
                     kernel_size: int, dilation: int, dropout: float = 0.1):
            super().__init__()
            self.conv = nn.Conv1d(
                in_channels, out_channels, kernel_size,
                padding=(kernel_size - 1) * dilation,
                dilation=dilation
            )
            self.bn = nn.BatchNorm1d(out_channels)
            self.dropout = nn.Dropout(dropout)
            self.relu = nn.ReLU()
            
            # Residual connection
            self.residual = nn.Conv1d(in_channels, out_channels, 1) if in_channels != out_channels else nn.Identity()
        
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x: (batch, channels, seq)
            out = self.conv(x)
            out = out[:, :, :x.size(2)]  # Causal: trim to original length
            out = self.bn(out)
            out = self.relu(out)
            out = self.dropout(out)
            return out + self.residual(x)
    
    
    class TCNBranch(nn.Module):
        """TCN branch for local pattern extraction."""
        
        def __init__(self, input_dim: int, hidden_dim: int, 
                     dilations: List[int] = [1, 2, 4, 8]):
            super().__init__()
            layers = []
            in_ch = input_dim
            for d in dilations:
                layers.append(TCNBlock(in_ch, hidden_dim, kernel_size=3, dilation=d))
                in_ch = hidden_dim
            self.layers = nn.Sequential(*layers)
        
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x: (batch, seq, features) -> (batch, features, seq)
            x = x.transpose(1, 2)
            x = self.layers(x)
            # Global average pooling
            return x.mean(dim=2)
    
    
    class GRUBranch(nn.Module):
        """GRU branch for sequential dependencies."""
        
        def __init__(self, input_dim: int, hidden_dim: int, num_layers: int = 2):
            super().__init__()
            self.gru = nn.GRU(
                input_dim, hidden_dim, num_layers,
                batch_first=True, dropout=0.1
            )
        
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x: (batch, seq, features)
            _, h = self.gru(x)
            return h[-1]  # Last layer hidden state
    
    
    class AttentionBranch(nn.Module):
        """Self-attention branch for pivotal moments."""
        
        def __init__(self, input_dim: int, hidden_dim: int, n_heads: int = 1):
            super().__init__()
            self.proj = nn.Linear(input_dim, hidden_dim)
            self.attn = nn.MultiheadAttention(hidden_dim, n_heads, batch_first=True)
            
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x: (batch, seq, features)
            x = self.proj(x)
            
            # Create causal mask
            seq_len = x.size(1)
            mask = torch.triu(torch.ones(seq_len, seq_len), diagonal=1).bool()
            mask = mask.to(x.device)
            
            out, _ = self.attn(x, x, x, attn_mask=mask)
            return out[:, -1, :]  # Last position
    
    
    class PyTorchIntentEncoder(nn.Module):
        """
        Complete intent encoder using PyTorch.
        For training and ONNX export.
        """
        
        def __init__(self, config: Optional[MIDEConfig] = None):
            super().__init__()
            self.config = config or MIDEConfig()
            
            self.input_dim = 12
            self.hidden_dim = self.config.hidden_dim
            self.output_dim = 5
            
            # Branches
            self.tcn = TCNBranch(self.input_dim, self.hidden_dim) if self.config.use_tcn else None
            self.gru = GRUBranch(self.input_dim, self.hidden_dim) if self.config.use_gru else None
            self.attn = AttentionBranch(self.input_dim, self.hidden_dim) if self.config.use_attention else None
            
            # Compute fusion dimension
            fusion_dim = 0
            if self.tcn:
                fusion_dim += self.hidden_dim
            if self.gru:
                fusion_dim += self.hidden_dim
            if self.attn:
                fusion_dim += self.hidden_dim
            
            if fusion_dim == 0:
                fusion_dim = self.input_dim
            
            # Fusion layers
            self.fc1 = nn.Linear(fusion_dim, self.hidden_dim)
            self.ln = nn.LayerNorm(self.hidden_dim)
            self.fc2 = nn.Linear(self.hidden_dim, self.output_dim)
            
            self.temperature = self.config.temperature
        
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """
            Forward pass.
            
            Args:
                x: Input of shape (batch, seq, 12)
            
            Returns:
                Intent probabilities of shape (batch, 5)
            """
            features = []
            
            if self.tcn:
                features.append(self.tcn(x))
            if self.gru:
                features.append(self.gru(x))
            if self.attn:
                features.append(self.attn(x))
            
            if len(features) > 0:
                fused = torch.cat(features, dim=-1)
            else:
                fused = x.mean(dim=1)
            
            h = self.fc1(fused)
            h = self.ln(h)
            h = F.relu(h)
            
            logits = self.fc2(h)
            probs = F.softmax(logits / self.temperature, dim=-1)
            
            return probs
        
        def export_onnx(self, path: str, seq_len: int = 64):
            """Export model to ONNX format."""
            dummy_input = torch.randn(1, seq_len, 12)
            torch.onnx.export(
                self, dummy_input, path,
                input_names=['features'],
                output_names=['intent_probs'],
                dynamic_axes={
                    'features': {0: 'batch', 1: 'seq'},
                    'intent_probs': {0: 'batch'}
                }
            )


# =============================================================================
# UNIFIED INFERENCE ENGINE
# =============================================================================

class IntentInferenceEngine:
    """
    Unified inference engine that uses NumPy by default,
    with optional PyTorch backend for training.
    """
    
    def __init__(self, config: Optional[MIDEConfig] = None, use_torch: bool = False):
        self.config = config or MIDEConfig()
        self.use_torch = use_torch and TORCH_AVAILABLE
        
        if self.use_torch:
            self.encoder = PyTorchIntentEncoder(self.config)
            self.encoder.eval()
        else:
            self.encoder = NumpyIntentEncoder(self.config)
        
        self._inference_times: List[float] = []
    
    def infer(self, features: np.ndarray) -> Tuple[IntentSimplex, float]:
        """
        Run inference on features.
        
        Args:
            features: Input of shape (seq, 12) or (batch, seq, 12)
        
        Returns:
            Tuple of (IntentSimplex, inference_time_ms)
        """
        start = time.perf_counter()
        
        if self.use_torch:
            with torch.no_grad():
                if features.ndim == 2:
                    features = features[np.newaxis, :, :]
                x = torch.from_numpy(features).float()
                probs = self.encoder(x).numpy()[0]
                
                simplex = IntentSimplex(
                    urgent=float(probs[0]),
                    passive=float(probs[1]),
                    mechanical=float(probs[2]),
                    exploitative=float(probs[3]),
                    noise=float(probs[4])
                )
        else:
            simplex = self.encoder.infer(features)
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        self._inference_times.append(elapsed_ms)
        
        # Keep only recent times
        if len(self._inference_times) > 100:
            self._inference_times = self._inference_times[-100:]
        
        return simplex, elapsed_ms
    
    @property
    def avg_inference_time_ms(self) -> float:
        """Average inference time in milliseconds."""
        if not self._inference_times:
            return 0.0
        return float(np.mean(self._inference_times))
    
    def export_onnx(self, path: str):
        """Export model to ONNX (requires PyTorch)."""
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch required for ONNX export")
        
        if not self.use_torch:
            # Create PyTorch model for export
            torch_encoder = PyTorchIntentEncoder(self.config)
            torch_encoder.export_onnx(path)
        else:
            self.encoder.export_onnx(path)
