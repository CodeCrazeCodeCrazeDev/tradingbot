"""
DeepChart Lightweight Models - CPU-Friendly Deep Learning

All models designed for:
- Minimal inference cost (<5ms per symbol)
- ONNX export compatibility
- CPU-only inference (no GPU required)
- Real-time updates
- <1M parameters total

Model Architectures:
1. TemporalCNN - Dilated causal convolutions for sequence modeling
2. LightweightTransformer - Tiny transformer encoder (~200K params)
3. RegimeAutoencoder - Latent regime extraction
4. DeepChartModel - Ensemble combining all models

Outputs:
- Trend confidence [0, 1]
- Local volatility regime [0, 1, 2]
- Liquidity zone probability [0, 1]
- Breakout probability [0, 1]
- Reversion probability [0, 1]
- Latent state vector (8-dim for visualization)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
import logging
import warnings
import json
import os

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

# Try to import torch, fall back to numpy-only implementation
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, using numpy-only implementation")
# Try to import ONNX runtime
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger.warning("ONNX Runtime not available")


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class ModelConfig:
    """Configuration for DeepChart models."""
    # Input dimensions
    input_dim: int = 32              # Feature vector size
    sequence_length: int = 64        # Lookback window
    
    # Model dimensions (kept small for CPU)
    hidden_dim: int = 64             # Hidden layer size
    latent_dim: int = 8              # Latent state dimension
    num_heads: int = 2               # Attention heads (transformer)
    num_layers: int = 2              # Number of layers
    
    # CNN settings
    kernel_sizes: List[int] = field(default_factory=lambda: [3, 5, 7])
    dilation_rates: List[int] = field(default_factory=lambda: [1, 2, 4])
    
    # Regularization
    dropout: float = 0.1
    
    # Output settings
    num_regimes: int = 4             # Number of regime states
    
    # Inference settings
    use_onnx: bool = True            # Use ONNX for inference if available
    quantize: bool = False           # Quantize model (int8)
    
    # Paths
    model_dir: str = "models/deepchart"


@dataclass
class ModelOutput:
    """Output from DeepChart model."""
    # Primary predictions
    trend_confidence: float = 0.0        # [0, 1] confidence in trend
    trend_direction: int = 0             # -1, 0, 1
    volatility_regime: int = 0           # 0=low, 1=normal, 2=high
    volatility_score: float = 0.0        # [0, 1]
    
    # Probabilities
    breakout_probability: float = 0.0    # [0, 1]
    reversion_probability: float = 0.0   # [0, 1]
    liquidity_zone_prob: float = 0.0     # [0, 1] near liquidity zone
    
    # Regime probabilities
    regime_probs: np.ndarray = field(default_factory=lambda: np.zeros(4))
    regime_id: int = 0
    
    # Latent state (for visualization)
    latent_state: np.ndarray = field(default_factory=lambda: np.zeros(8))
    
    # Confidence metrics
    prediction_confidence: float = 0.0   # Overall confidence
    model_uncertainty: float = 0.0       # Epistemic uncertainty
    
    # Metadata
    timestamp: float = 0.0
    inference_time_ms: float = 0.0


# =============================================================================
# NUMPY-ONLY IMPLEMENTATIONS (Fallback)
# =============================================================================

class NumpyTemporalCNN:
    """
    Numpy-only implementation of Temporal CNN.
    Uses pre-trained weights loaded from file.
    """
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.weights = {}
        self._initialized = False
    
    def load_weights(self, path: str) -> bool:
        """Load pre-trained weights from numpy file."""
        try:
            self.weights = np.load(path, allow_pickle=True).item()
            self._initialized = True
            return True
        except Exception as e:
            logger.warning(f"Could not load weights: {e}")
            self._initialize_random_weights()
            return False
    
    def _initialize_random_weights(self):
        """Initialize with random weights (for testing)."""
        np.random.seed(42)
        
        # Conv layers
        for i, (k, d) in enumerate(zip(self.config.kernel_sizes, self.config.dilation_rates)):
            self.weights[f'conv{i}_w'] = np.random.randn(self.config.hidden_dim, self.config.input_dim, k) * 0.1
            self.weights[f'conv{i}_b'] = np.zeros(self.config.hidden_dim)
        
        # Output layers
        self.weights['fc1_w'] = np.random.randn(self.config.hidden_dim, self.config.hidden_dim * len(self.config.kernel_sizes)) * 0.1
        self.weights['fc1_b'] = np.zeros(self.config.hidden_dim)
        self.weights['fc2_w'] = np.random.randn(self.config.latent_dim + 5, self.config.hidden_dim) * 0.1
        self.weights['fc2_b'] = np.zeros(self.config.latent_dim + 5)
        
        self._initialized = True
    
    def _conv1d(self, x: np.ndarray, w: np.ndarray, b: np.ndarray, dilation: int = 1) -> np.ndarray:
        """1D convolution with dilation."""
        # x: (batch, channels, length)
        # w: (out_channels, in_channels, kernel_size)
        batch, in_ch, length = x.shape
        out_ch, _, kernel_size = w.shape
        
        # Dilated kernel effective size
        effective_k = (kernel_size - 1) * dilation + 1
        
        # Pad for causal convolution
        pad_size = effective_k - 1
        x_padded = np.pad(x, ((0, 0), (0, 0), (pad_size, 0)), mode='constant')
        
        # Output
        out_length = length
        output = np.zeros((batch, out_ch, out_length))
        
        for b_idx in range(batch):
            for o in range(out_ch):
                for t in range(out_length):
                    val = b[o]
                    for i in range(in_ch):
                        for k in range(kernel_size):
                            idx = t + pad_size - k * dilation
                            if 0 <= idx < x_padded.shape[2]:
                                val += x_padded[b_idx, i, idx] * w[o, i, kernel_size - 1 - k]
                    output[b_idx, o, t] = val
        
        return output
    
    def _relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)
    
    def _global_avg_pool(self, x: np.ndarray) -> np.ndarray:
        """Global average pooling over time dimension."""
        return np.mean(x, axis=2)
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass.
        
        Args:
            x: Input tensor of shape (batch, sequence_length, input_dim)
        
        Returns:
            Output tensor of shape (batch, latent_dim + 5)
        """
        if not self._initialized:
            self._initialize_random_weights()
        
        # Transpose to (batch, channels, length)
        x = np.transpose(x, (0, 2, 1))
        
        # Multi-scale convolutions
        conv_outputs = []
        for i, (k, d) in enumerate(zip(self.config.kernel_sizes, self.config.dilation_rates)):
            h = self._conv1d(x, self.weights[f'conv{i}_w'], self.weights[f'conv{i}_b'], dilation=d)
            h = self._relu(h)
            h = self._global_avg_pool(h)
            conv_outputs.append(h)
        
        # Concatenate
        h = np.concatenate(conv_outputs, axis=1)
        
        # FC layers
        h = np.dot(h, self.weights['fc1_w'].T) + self.weights['fc1_b']
        h = self._relu(h)
        h = np.dot(h, self.weights['fc2_w'].T) + self.weights['fc2_b']
        
        return h


class NumpyLightweightTransformer:
    """
    Numpy-only implementation of Lightweight Transformer.
    Simplified single-head attention for CPU efficiency.
    """
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.weights = {}
        self._initialized = False
    
    def load_weights(self, path: str) -> bool:
        """Load pre-trained weights."""
        try:
            self.weights = np.load(path, allow_pickle=True).item()
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Error: {e}")
            self._initialize_random_weights()
            return False
    
    def _initialize_random_weights(self):
        """Initialize with random weights."""
        np.random.seed(43)
        d = self.config.hidden_dim
        
        # Input projection
        self.weights['input_proj_w'] = np.random.randn(d, self.config.input_dim) * 0.1
        self.weights['input_proj_b'] = np.zeros(d)
        
        # Attention weights (simplified single-head)
        self.weights['q_w'] = np.random.randn(d, d) * 0.1
        self.weights['k_w'] = np.random.randn(d, d) * 0.1
        self.weights['v_w'] = np.random.randn(d, d) * 0.1
        self.weights['o_w'] = np.random.randn(d, d) * 0.1
        
        # FFN
        self.weights['ffn1_w'] = np.random.randn(d * 2, d) * 0.1
        self.weights['ffn1_b'] = np.zeros(d * 2)
        self.weights['ffn2_w'] = np.random.randn(d, d * 2) * 0.1
        self.weights['ffn2_b'] = np.zeros(d)
        
        # Output
        self.weights['out_w'] = np.random.randn(self.config.latent_dim + 5, d) * 0.1
        self.weights['out_b'] = np.zeros(self.config.latent_dim + 5)
        
        self._initialized = True
    
    def _softmax(self, x: np.ndarray, axis: int = -1) -> np.ndarray:
        exp_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
        return exp_x / np.sum(exp_x, axis=axis, keepdims=True)
    
    def _attention(self, x: np.ndarray) -> np.ndarray:
        """Simplified self-attention."""
        # x: (batch, seq, dim)
        Q = np.dot(x, self.weights['q_w'].T)
        K = np.dot(x, self.weights['k_w'].T)
        V = np.dot(x, self.weights['v_w'].T)
        
        # Scaled dot-product attention
        d_k = Q.shape[-1]
        scores = np.matmul(Q, np.transpose(K, (0, 2, 1))) / np.sqrt(d_k)
        
        # Causal mask
        seq_len = scores.shape[-1]
        mask = np.triu(np.ones((seq_len, seq_len)) * -1e9, k=1)
        scores = scores + mask
        
        attn = self._softmax(scores, axis=-1)
        out = np.matmul(attn, V)
        out = np.dot(out, self.weights['o_w'].T)
        
        return out
    
    def _ffn(self, x: np.ndarray) -> np.ndarray:
        """Feed-forward network."""
        h = np.dot(x, self.weights['ffn1_w'].T) + self.weights['ffn1_b']
        h = np.maximum(0, h)  # ReLU
        h = np.dot(h, self.weights['ffn2_w'].T) + self.weights['ffn2_b']
        return h
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass.
        
        Args:
            x: Input tensor of shape (batch, sequence_length, input_dim)
        
        Returns:
            Output tensor of shape (batch, latent_dim + 5)
        """
        if not self._initialized:
            self._initialize_random_weights()
        
        # Input projection
        h = np.dot(x, self.weights['input_proj_w'].T) + self.weights['input_proj_b']
        
        # Transformer layer (simplified - single layer)
        h = h + self._attention(h)
        h = h + self._ffn(h)
        
        # Take last position
        h = h[:, -1, :]
        
        # Output projection
        out = np.dot(h, self.weights['out_w'].T) + self.weights['out_b']
        
        return out


class NumpyRegimeAutoencoder:
    """
    Numpy-only implementation of Regime Autoencoder.
    Extracts latent regime representation.
    """
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.weights = {}
        self._initialized = False
    
    def load_weights(self, path: str) -> bool:
        try:
            self.weights = np.load(path, allow_pickle=True).item()
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Error: {e}")
            self._initialize_random_weights()
            return False
    
    def _initialize_random_weights(self):
        np.random.seed(44)
        
        # Encoder
        self.weights['enc1_w'] = np.random.randn(self.config.hidden_dim, self.config.input_dim) * 0.1
        self.weights['enc1_b'] = np.zeros(self.config.hidden_dim)
        self.weights['enc2_w'] = np.random.randn(self.config.latent_dim, self.config.hidden_dim) * 0.1
        self.weights['enc2_b'] = np.zeros(self.config.latent_dim)
        
        # Regime classifier
        self.weights['regime_w'] = np.random.randn(self.config.num_regimes, self.config.latent_dim) * 0.1
        self.weights['regime_b'] = np.zeros(self.config.num_regimes)
        
        self._initialized = True
    
    def encode(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Encode input to latent space.
        
        Args:
            x: Input of shape (batch, input_dim) or (batch, seq, input_dim)
        
        Returns:
            Tuple of (latent_state, regime_probs)
        """
        if not self._initialized:
            self._initialize_random_weights()
        
        # If sequence input, take mean
        if len(x.shape) == 3:
            x = np.mean(x, axis=1)
        
        # Encoder
        h = np.dot(x, self.weights['enc1_w'].T) + self.weights['enc1_b']
        h = np.maximum(0, h)
        latent = np.dot(h, self.weights['enc2_w'].T) + self.weights['enc2_b']
        latent = np.tanh(latent)
        
        # Regime classification
        regime_logits = np.dot(latent, self.weights['regime_w'].T) + self.weights['regime_b']
        regime_probs = np.exp(regime_logits - np.max(regime_logits, axis=-1, keepdims=True))
        regime_probs = regime_probs / np.sum(regime_probs, axis=-1, keepdims=True)
        
        return latent, regime_probs


# =============================================================================
# PYTORCH IMPLEMENTATIONS (When Available)
# =============================================================================

if TORCH_AVAILABLE:
    
    class TemporalCNNTorch(nn.Module):
        """
        Temporal CNN with dilated causal convolutions.
        
        Architecture:
        - Multi-scale dilated convolutions (kernels: 3, 5, 7)
        - Causal padding for real-time inference
        - Global average pooling
        - FC layers for output
        
        Parameters: ~150K
        """
        
        def __init__(self, config: ModelConfig):
            super().__init__()
            self.config = config
            
            # Multi-scale convolutions
            self.convs = nn.ModuleList()
            for k, d in zip(config.kernel_sizes, config.dilation_rates):
                conv = nn.Conv1d(
                    in_channels=config.input_dim,
                    out_channels=config.hidden_dim,
                    kernel_size=k,
                    dilation=d,
                    padding=(k - 1) * d,  # Causal padding
                )
                self.convs.append(conv)
            
            # Batch norm
            self.bn = nn.BatchNorm1d(config.hidden_dim * len(config.kernel_sizes))
            
            # FC layers
            self.fc1 = nn.Linear(config.hidden_dim * len(config.kernel_sizes), config.hidden_dim)
            self.fc2 = nn.Linear(config.hidden_dim, config.latent_dim + 5)
            
            self.dropout = nn.Dropout(config.dropout)
        
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """
            Forward pass.
            
            Args:
                x: Input tensor of shape (batch, sequence_length, input_dim)
            
            Returns:
                Output tensor of shape (batch, latent_dim + 5)
            """
            # Transpose to (batch, channels, length)
            x = x.transpose(1, 2)
            
            # Multi-scale convolutions
            conv_outputs = []
            for conv in self.convs:
                h = conv(x)
                # Remove future padding (causal)
                h = h[:, :, :x.shape[2]]
                h = F.relu(h)
                # Global average pooling
                h = h.mean(dim=2)
                conv_outputs.append(h)
            
            # Concatenate
            h = torch.cat(conv_outputs, dim=1)
            h = self.bn(h)
            h = self.dropout(h)
            
            # FC layers
            h = F.relu(self.fc1(h))
            h = self.dropout(h)
            out = self.fc2(h)
            
            return out
    
    
    class LightweightTransformerTorch(nn.Module):
        """
        Lightweight Transformer Encoder.
        
        Architecture:
        - 2 transformer layers
        - 2 attention heads
        - Hidden dim: 64
        - Positional encoding
        
        Parameters: ~200K
        """
        
        def __init__(self, config: ModelConfig):
            super().__init__()
            self.config = config
            
            # Input projection
            self.input_proj = nn.Linear(config.input_dim, config.hidden_dim)
            
            # Positional encoding
            self.pos_encoding = self._create_positional_encoding(
                config.sequence_length, config.hidden_dim
            )
            
            # Transformer layers
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=config.hidden_dim,
                nhead=config.num_heads,
                dim_feedforward=config.hidden_dim * 2,
                dropout=config.dropout,
                activation='relu',
                batch_first=True,
            )
            self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=config.num_layers)
            
            # Output projection
            self.output_proj = nn.Linear(config.hidden_dim, config.latent_dim + 5)
        
        def _create_positional_encoding(self, max_len: int, d_model: int) -> torch.Tensor:
            """Create sinusoidal positional encoding."""
            pe = torch.zeros(max_len, d_model)
            position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
            div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model))
            pe[:, 0::2] = torch.sin(position * div_term)
            pe[:, 1::2] = torch.cos(position * div_term)
            return pe.unsqueeze(0)
        
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """
            Forward pass.
            
            Args:
                x: Input tensor of shape (batch, sequence_length, input_dim)
            
            Returns:
                Output tensor of shape (batch, latent_dim + 5)
            """
            # Input projection
            h = self.input_proj(x)
            
            # Add positional encoding
            seq_len = h.shape[1]
            h = h + self.pos_encoding[:, :seq_len, :].to(h.device)
            
            # Causal mask
            mask = torch.triu(torch.ones(seq_len, seq_len), diagonal=1).bool().to(h.device)
            
            # Transformer
            h = self.transformer(h, mask=mask)
            
            # Take last position
            h = h[:, -1, :]
            
            # Output projection
            out = self.output_proj(h)
            
            return out
    
    
    class RegimeAutoencoderTorch(nn.Module):
        """
        Variational Autoencoder for regime extraction.
        
        Architecture:
        - Encoder: 2 FC layers -> latent
        - Regime classifier head
        - Decoder (for training only)
        
        Parameters: ~100K
        """
        
        def __init__(self, config: ModelConfig):
            super().__init__()
            self.config = config
            
            # Encoder
            self.encoder = nn.Sequential(
                nn.Linear(config.input_dim, config.hidden_dim),
                nn.ReLU(),
                nn.Dropout(config.dropout),
                nn.Linear(config.hidden_dim, config.hidden_dim // 2),
                nn.ReLU(),
            )
            
            # Latent space
            self.fc_mu = nn.Linear(config.hidden_dim // 2, config.latent_dim)
            self.fc_var = nn.Linear(config.hidden_dim // 2, config.latent_dim)
            
            # Regime classifier
            self.regime_classifier = nn.Linear(config.latent_dim, config.num_regimes)
            
            # Decoder (for training)
            self.decoder = nn.Sequential(
                nn.Linear(config.latent_dim, config.hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(config.hidden_dim // 2, config.hidden_dim),
                nn.ReLU(),
                nn.Linear(config.hidden_dim, config.input_dim),
            )
        
        def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            """Encode input to latent space."""
            # If sequence input, take mean
            if len(x.shape) == 3:
                x = x.mean(dim=1)
            
            h = self.encoder(x)
            mu = self.fc_mu(h)
            log_var = self.fc_var(h)
            
            # Reparameterization trick
            std = torch.exp(0.5 * log_var)
            eps = torch.randn_like(std)
            z = mu + eps * std
            
            return z, mu, log_var
        
        def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
            """
            Forward pass.
            
            Returns:
                Tuple of (latent, regime_probs, reconstruction, kl_loss)
            """
            z, mu, log_var = self.encode(x)
            
            # Regime classification
            regime_logits = self.regime_classifier(z)
            regime_probs = F.softmax(regime_logits, dim=-1)
            
            # Reconstruction
            recon = self.decoder(z)
            
            # KL divergence
            kl_loss = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp(), dim=-1).mean()
            
            return z, regime_probs, recon, kl_loss


# =============================================================================
# MAIN MODEL CLASS
# =============================================================================

class DeepChartModel:
    """
    Main DeepChart model combining all sub-models.
    
    Automatically selects between:
    1. ONNX inference (fastest, if available)
    2. PyTorch inference (if available)
    3. Numpy inference (fallback)
    
    Ensemble combines:
    - TemporalCNN for local patterns
    - LightweightTransformer for sequence modeling
    - RegimeAutoencoder for latent state
    """
    
    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()
        
        # Initialize models based on availability
        self._init_models()
        
        # Sequence buffer for inference
        self._sequence_buffer = []
        
        # ONNX sessions
        self._onnx_sessions = {}
        
        logger.info(f"DeepChartModel initialized (backend: {self._backend})")
    
    def _init_models(self):
        """Initialize models based on available backends."""
        if ONNX_AVAILABLE and self.config.use_onnx:
            self._backend = 'onnx'
            self._load_onnx_models()
        elif TORCH_AVAILABLE:
            self._backend = 'torch'
            self._init_torch_models()
        else:
            self._backend = 'numpy'
            self._init_numpy_models()
    
    def _init_torch_models(self):
        """Initialize PyTorch models."""
        self.temporal_cnn = TemporalCNNTorch(self.config)
        self.transformer = LightweightTransformerTorch(self.config)
        self.autoencoder = RegimeAutoencoderTorch(self.config)
        
        # Set to eval mode
        self.temporal_cnn.eval()
        self.transformer.eval()
        self.autoencoder.eval()
    
    def _init_numpy_models(self):
        """Initialize numpy-only models."""
        self.temporal_cnn = NumpyTemporalCNN(self.config)
        self.transformer = NumpyLightweightTransformer(self.config)
        self.autoencoder = NumpyRegimeAutoencoder(self.config)
    
    def _load_onnx_models(self):
        """Load ONNX models for inference."""
        model_dir = self.config.model_dir
        
        # Try to load ONNX models
        onnx_files = {
            'temporal_cnn': os.path.join(model_dir, 'temporal_cnn.onnx'),
            'transformer': os.path.join(model_dir, 'transformer.onnx'),
            'autoencoder': os.path.join(model_dir, 'autoencoder.onnx'),
        }
        
        loaded = False
        for name, path in onnx_files.items():
            if os.path.exists(path):
                try:
                    self._onnx_sessions[name] = ort.InferenceSession(
                        path,
                        providers=['CPUExecutionProvider']
                    )
                    loaded = True
                    logger.info(f"Loaded ONNX model: {name}")
                except Exception as e:
                    logger.warning(f"Failed to load ONNX model {name}: {e}")
        
        if not loaded:
            logger.warning("No ONNX models found, falling back to numpy")
            self._backend = 'numpy'
            self._init_numpy_models()
    
    def update_sequence(self, feature_vector: np.ndarray):
        """
        Update sequence buffer with new feature vector.
        
        Args:
            feature_vector: Feature vector of shape (input_dim,)
        """
        self._sequence_buffer.append(feature_vector)
        
        # Keep only last sequence_length
        if len(self._sequence_buffer) > self.config.sequence_length:
            self._sequence_buffer = self._sequence_buffer[-self.config.sequence_length:]
    
    def predict(self, feature_vector: Optional[np.ndarray] = None) -> ModelOutput:
        """
        Run inference and return predictions.
        
        Args:
            feature_vector: Optional new feature vector to add
        
        Returns:
            ModelOutput with all predictions
        """
        import time
        start_time = time.time()
        
        # Update buffer if new vector provided
        if feature_vector is not None:
            self.update_sequence(feature_vector)
        
        # Check if we have enough data
        if len(self._sequence_buffer) < 10:
            return ModelOutput(timestamp=time.time())
        
        # Prepare input
        sequence = np.array(self._sequence_buffer)
        
        # Pad if needed
        if len(sequence) < self.config.sequence_length:
            pad_size = self.config.sequence_length - len(sequence)
            sequence = np.pad(sequence, ((pad_size, 0), (0, 0)), mode='edge')
        
        # Add batch dimension
        x = sequence[np.newaxis, :, :].astype(np.float32)
        
        # Run inference
        if self._backend == 'onnx':
            output = self._predict_onnx(x)
        elif self._backend == 'torch':
            output = self._predict_torch(x)
        else:
            output = self._predict_numpy(x)
        
        # Parse output
        result = self._parse_output(output)
        result.inference_time_ms = (time.time() - start_time) * 1000
        result.timestamp = time.time()
        
        return result
    
    def _predict_onnx(self, x: np.ndarray) -> np.ndarray:
        """Run ONNX inference."""
        outputs = []
        
        for name, session in self._onnx_sessions.items():
            input_name = session.get_inputs()[0].name
            output = session.run(None, {input_name: x})[0]
            outputs.append(output)
        
        if outputs:
            return np.mean(outputs, axis=0)
        else:
            return self._predict_numpy(x)
    
    def _predict_torch(self, x: np.ndarray) -> np.ndarray:
        """Run PyTorch inference."""
        with torch.no_grad():
            x_tensor = torch.from_numpy(x)
            
            # Run all models
            cnn_out = self.temporal_cnn(x_tensor).numpy()
            trans_out = self.transformer(x_tensor).numpy()
            
            # Autoencoder
            latent, regime_probs, _, _ = self.autoencoder(x_tensor)
            ae_out = torch.cat([latent, regime_probs], dim=-1).numpy()
            
            # Ensemble (simple average)
            output = (cnn_out + trans_out) / 2
            
            # Add regime info
            output = np.concatenate([output, ae_out[:, -self.config.num_regimes:]], axis=-1)
        
        return output
    
    def _predict_numpy(self, x: np.ndarray) -> np.ndarray:
        """Run numpy inference."""
        # Run all models
        cnn_out = self.temporal_cnn.forward(x)
        trans_out = self.transformer.forward(x)
        latent, regime_probs = self.autoencoder.encode(x)
        
        # Ensemble
        output = (cnn_out + trans_out) / 2
        
        # Add regime info
        output = np.concatenate([output, regime_probs], axis=-1)
        
        return output
    
    def _parse_output(self, output: np.ndarray) -> ModelOutput:
        """Parse model output into ModelOutput structure."""
        output = output.squeeze()
        
        # Extract components
        latent_dim = self.config.latent_dim
        num_regimes = self.config.num_regimes
        
        # Latent state (first latent_dim values)
        latent_state = output[:latent_dim]
        
        # Predictions (next 5 values)
        predictions = output[latent_dim:latent_dim + 5]
        
        # Regime probabilities (last num_regimes values)
        if len(output) > latent_dim + 5:
            regime_probs = output[-num_regimes:]
            regime_probs = np.exp(regime_probs) / np.sum(np.exp(regime_probs))
        else:
            regime_probs = np.ones(num_regimes) / num_regimes
        
        # Parse predictions
        trend_raw = predictions[0] if len(predictions) > 0 else 0
        vol_raw = predictions[1] if len(predictions) > 1 else 0
        breakout_raw = predictions[2] if len(predictions) > 2 else 0
        reversion_raw = predictions[3] if len(predictions) > 3 else 0
        liquidity_raw = predictions[4] if len(predictions) > 4 else 0
        
        # Apply activations
        trend_confidence = 1 / (1 + np.exp(-trend_raw))  # Sigmoid
        trend_direction = int(np.sign(trend_raw))
        
        volatility_score = 1 / (1 + np.exp(-vol_raw))
        volatility_regime = 0 if volatility_score < 0.33 else (2 if volatility_score > 0.66 else 1)
        
        breakout_probability = 1 / (1 + np.exp(-breakout_raw))
        reversion_probability = 1 / (1 + np.exp(-reversion_raw))
        liquidity_zone_prob = 1 / (1 + np.exp(-liquidity_raw))
        
        # Overall confidence
        prediction_confidence = np.max(regime_probs)
        
        # Uncertainty (entropy of regime probs)
        entropy = -np.sum(regime_probs * np.log(regime_probs + 1e-8))
        max_entropy = np.log(num_regimes)
        model_uncertainty = entropy / max_entropy
        
        return ModelOutput(
            trend_confidence=float(trend_confidence),
            trend_direction=trend_direction,
            volatility_regime=volatility_regime,
            volatility_score=float(volatility_score),
            breakout_probability=float(breakout_probability),
            reversion_probability=float(reversion_probability),
            liquidity_zone_prob=float(liquidity_zone_prob),
            regime_probs=regime_probs,
            regime_id=int(np.argmax(regime_probs)),
            latent_state=latent_state,
            prediction_confidence=float(prediction_confidence),
            model_uncertainty=float(model_uncertainty),
        )
    
    def export_onnx(self, output_dir: str):
        """Export models to ONNX format."""
        if not TORCH_AVAILABLE:
            logger.error("PyTorch required for ONNX export")
            return
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Dummy input
        dummy_input = torch.randn(1, self.config.sequence_length, self.config.input_dim)
        
        # Export each model
        models = {
            'temporal_cnn': self.temporal_cnn,
            'transformer': self.transformer,
        }
        
        for name, model in models.items():
            output_path = os.path.join(output_dir, f'{name}.onnx')
            try:
                torch.onnx.export(
                    model,
                    dummy_input,
                    output_path,
                    input_names=['input'],
                    output_names=['output'],
                    dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}},
                    opset_version=11,
                )
                logger.info(f"Exported {name} to {output_path}")
            except Exception as e:
                logger.error(f"Failed to export {name}: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        info = {
            'backend': self._backend,
            'config': {
                'input_dim': self.config.input_dim,
                'sequence_length': self.config.sequence_length,
                'hidden_dim': self.config.hidden_dim,
                'latent_dim': self.config.latent_dim,
                'num_regimes': self.config.num_regimes,
            },
            'buffer_size': len(self._sequence_buffer),
        }
        
        # Count parameters if torch
        if self._backend == 'torch' and TORCH_AVAILABLE:
            total_params = 0
            for model in [self.temporal_cnn, self.transformer, self.autoencoder]:
                total_params += sum(p.numel() for p in model.parameters())
            info['total_parameters'] = total_params
        
        return info
    
    def reset(self):
        """Reset sequence buffer."""
        self._sequence_buffer = []


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_model(config: Optional[Dict] = None) -> DeepChartModel:
    """Factory function to create DeepChart model."""
    if config:
        model_config = ModelConfig(**config)
    else:
        model_config = ModelConfig()
    return DeepChartModel(model_config)


# Aliases for imports
TemporalCNN = TemporalCNNTorch if TORCH_AVAILABLE else NumpyTemporalCNN
LightweightTransformer = LightweightTransformerTorch if TORCH_AVAILABLE else NumpyLightweightTransformer
RegimeAutoencoder = RegimeAutoencoderTorch if TORCH_AVAILABLE else NumpyRegimeAutoencoder


if __name__ == "__main__":
    # Test the models
    config = ModelConfig()
    model = DeepChartModel(config)
    
    print(f"Model info: {model.get_model_info()}")
    
    # Simulate inference
    np.random.seed(42)
    for i in range(100):
        feature_vector = np.random.randn(config.input_dim).astype(np.float32)
        output = model.predict(feature_vector)
        
        if i % 20 == 0:
            print(f"\nStep {i}:")
            print(f"  Trend: {output.trend_direction} (conf: {output.trend_confidence:.2f})")
            print(f"  Vol regime: {output.volatility_regime}")
            print(f"  Breakout prob: {output.breakout_probability:.3f}")
            print(f"  Regime: {output.regime_id} (probs: {output.regime_probs})")
            print(f"  Inference time: {output.inference_time_ms:.2f}ms")
