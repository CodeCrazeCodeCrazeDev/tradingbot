"""
Deep Learning Module for AlphaEngine
=====================================

Implements:
- DeepLOB: CNN-LSTM hybrid for limit order book prediction
- Multi-Scale LSTM with attention for trend prediction
- Transformer-based price prediction
- Feature extraction and preprocessing
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Try to import deep learning libraries
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available. Deep learning features will be limited.")

try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class PredictionHorizon(Enum):
    """Prediction time horizons"""
    ULTRA_SHORT = "ultra_short"  # 10-50 ticks (5-30 seconds)
    SHORT = "short"  # 100-500 ticks (1-5 minutes)
    MEDIUM = "medium"  # 1000+ ticks (5-30 minutes)
    LONG = "long"  # 5000+ ticks (30+ minutes)


@dataclass
class LOBSnapshot:
    """Limit Order Book snapshot"""
    timestamp: datetime
    bid_prices: np.ndarray  # 10 levels
    bid_volumes: np.ndarray
    ask_prices: np.ndarray
    ask_volumes: np.ndarray
    mid_price: float = 0.0
    spread: float = 0.0
    imbalance: float = 0.0
    microprice: float = 0.0
    
    def __post_init__(self):
        if len(self.bid_prices) > 0 and len(self.ask_prices) > 0:
            self.mid_price = (self.bid_prices[0] + self.ask_prices[0]) / 2
            self.spread = self.ask_prices[0] - self.bid_prices[0]
            
            # Order imbalance
            total_bid = np.sum(self.bid_volumes)
            total_ask = np.sum(self.ask_volumes)
            self.imbalance = (total_bid - total_ask) / (total_bid + total_ask + 1e-10)
            
            # Microprice (volume-weighted mid)
            self.microprice = (self.bid_prices[0] * self.ask_volumes[0] + 
                              self.ask_prices[0] * self.bid_volumes[0]) / \
                             (self.bid_volumes[0] + self.ask_volumes[0] + 1e-10)
    
    def to_features(self) -> np.ndarray:
        """Convert to feature array for model input"""
        features = np.concatenate([
            self.bid_prices,
            self.bid_volumes,
            self.ask_prices,
            self.ask_volumes,
            [self.mid_price, self.spread, self.imbalance, self.microprice]
        ])
        return features


@dataclass
class PricePrediction:
    """Price prediction output"""
    timestamp: datetime
    horizon: PredictionHorizon
    direction_prob: float  # Probability of price increase
    magnitude: float  # Expected move magnitude
    confidence: float  # Model confidence
    features_importance: Dict[str, float] = field(default_factory=dict)
    
    @property
    def direction(self) -> str:
        if self.direction_prob > 0.55:
            return "up"
        elif self.direction_prob < 0.45:
            return "down"
        return "neutral"


class LOBPreprocessor:
    """Preprocessor for Limit Order Book data"""
    
    def __init__(self, n_levels: int = 10, normalize: bool = True):
        self.n_levels = n_levels
        self.normalize = normalize
        self.price_scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.volume_scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.fitted = False
        
    def fit(self, lob_data: List[LOBSnapshot]):
        """Fit scalers on historical data"""
        if not SKLEARN_AVAILABLE or not self.normalize:
            self.fitted = True
            return
        
        prices = []
        volumes = []
        
        for snapshot in lob_data:
            prices.extend(snapshot.bid_prices.tolist())
            prices.extend(snapshot.ask_prices.tolist())
            volumes.extend(snapshot.bid_volumes.tolist())
            volumes.extend(snapshot.ask_volumes.tolist())
        
        self.price_scaler.fit(np.array(prices).reshape(-1, 1))
        self.volume_scaler.fit(np.array(volumes).reshape(-1, 1))
        self.fitted = True
    
    def transform(self, snapshot: LOBSnapshot) -> np.ndarray:
        """Transform LOB snapshot to normalized features"""
        if not self.fitted:
            return snapshot.to_features()
        
        if self.normalize and SKLEARN_AVAILABLE:
            bid_prices = self.price_scaler.transform(
                snapshot.bid_prices.reshape(-1, 1)).flatten()
            ask_prices = self.price_scaler.transform(
                snapshot.ask_prices.reshape(-1, 1)).flatten()
            bid_volumes = self.volume_scaler.transform(
                snapshot.bid_volumes.reshape(-1, 1)).flatten()
            ask_volumes = self.volume_scaler.transform(
                snapshot.ask_volumes.reshape(-1, 1)).flatten()
            
            # Normalize other features
            mid_price = self.price_scaler.transform([[snapshot.mid_price]])[0, 0]
            spread = snapshot.spread / (snapshot.mid_price + 1e-10)  # Relative spread
            
            features = np.concatenate([
                bid_prices, bid_volumes, ask_prices, ask_volumes,
                [mid_price, spread, snapshot.imbalance, snapshot.microprice]
            ])
        else:
            features = snapshot.to_features()
        
        return features
    
    def create_sequence(self, snapshots: List[LOBSnapshot], 
                       seq_length: int = 100) -> np.ndarray:
        """Create sequence of LOB features for model input"""
        features = [self.transform(s) for s in snapshots[-seq_length:]]
        
        # Pad if necessary
        while len(features) < seq_length:
            features.insert(0, np.zeros_like(features[0]))
        
        return np.array(features)


if TORCH_AVAILABLE:
    class ConvBlock(nn.Module):
        """Convolutional block for DeepLOB"""
        
        def __init__(self, in_channels: int, out_channels: int, 
                     kernel_size: Tuple[int, int] = (1, 2)):
            super().__init__()
            self.conv = nn.Conv2d(in_channels, out_channels, kernel_size)
            self.bn = nn.BatchNorm2d(out_channels)
            self.relu = nn.LeakyReLU(0.01)
            
        def forward(self, x):
            return self.relu(self.bn(self.conv(x)))
    
    
    class InceptionModule(nn.Module):
        """Inception module for multi-scale feature extraction"""
        
        def __init__(self, in_channels: int, out_channels: int):
            super().__init__()
            self.conv1 = nn.Conv2d(in_channels, out_channels, (1, 1))
            self.conv3 = nn.Conv2d(in_channels, out_channels, (1, 3), padding=(0, 1))
            self.conv5 = nn.Conv2d(in_channels, out_channels, (1, 5), padding=(0, 2))
            self.pool = nn.MaxPool2d((1, 3), stride=1, padding=(0, 1))
            self.pool_conv = nn.Conv2d(in_channels, out_channels, (1, 1))
            self.bn = nn.BatchNorm2d(out_channels * 4)
            
        def forward(self, x):
            out1 = self.conv1(x)
            out3 = self.conv3(x)
            out5 = self.conv5(x)
            out_pool = self.pool_conv(self.pool(x))
            out = torch.cat([out1, out3, out5, out_pool], dim=1)
            return F.leaky_relu(self.bn(out), 0.01)
    
    
    class DeepLOBModel(nn.Module):
        """
        DeepLOB: Deep Learning for Limit Order Book
        
        CNN-LSTM hybrid architecture for price movement prediction
        from limit order book data.
import numpy
import pandas
        
        Architecture:
        - Convolutional layers for spatial feature extraction
        - Inception modules for multi-scale patterns
        - LSTM for temporal dependencies
        - Fully connected layers for prediction
        """
        
        def __init__(self, 
                     n_levels: int = 10,
                     n_features: int = 4,  # bid_price, bid_vol, ask_price, ask_vol
                     seq_length: int = 100,
                     hidden_size: int = 64,
                     num_classes: int = 3):  # up, down, neutral
            super().__init__()
            
            self.n_levels = n_levels
            self.n_features = n_features
            self.seq_length = seq_length
            
            # Convolutional layers
            self.conv1 = ConvBlock(1, 32, (1, 2))
            self.conv2 = ConvBlock(32, 32, (1, 2))
            self.conv3 = ConvBlock(32, 32, (1, n_levels))
            
            # Inception modules
            self.inception1 = InceptionModule(32, 64)
            self.inception2 = InceptionModule(64 * 4, 64)
            
            # LSTM
            self.lstm = nn.LSTM(
                input_size=64 * 4,
                hidden_size=hidden_size,
                num_layers=2,
                batch_first=True,
                dropout=0.2,
                bidirectional=True
            )
            
            # Attention
            self.attention = nn.MultiheadAttention(
                embed_dim=hidden_size * 2,
                num_heads=4,
                dropout=0.1
            )
            
            # Output layers
            self.fc1 = nn.Linear(hidden_size * 2, 64)
            self.fc2 = nn.Linear(64, num_classes)
            self.dropout = nn.Dropout(0.3)
            
        def forward(self, x):
            # x shape: (batch, seq_length, n_levels, n_features)
            batch_size = x.size(0)
            
            # Reshape for conv: (batch * seq, 1, n_levels, n_features)
            x = x.view(-1, 1, self.n_levels, self.n_features)
            
            # Convolutional layers
            x = self.conv1(x)
            x = self.conv2(x)
            x = self.conv3(x)
            
            # Inception modules
            x = self.inception1(x)
            x = self.inception2(x)
            
            # Reshape for LSTM: (batch, seq, features)
            x = x.view(batch_size, self.seq_length, -1)
            
            # LSTM
            lstm_out, _ = self.lstm(x)
            
            # Attention
            attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
            
            # Take last timestep
            out = attn_out[:, -1, :]
            
            # Fully connected
            out = self.dropout(F.relu(self.fc1(out)))
            out = self.fc2(out)
            
            return F.softmax(out, dim=1)
    
    
    class MultiScaleLSTMModel(nn.Module):
        """
        Multi-Scale LSTM with Attention
        
        Processes price data across multiple DC thresholds simultaneously
        with attention mechanism for feature weighting.
        """
        
        def __init__(self,
                     input_size: int = 64,
                     hidden_size: int = 128,
                     num_layers: int = 3,
                     num_scales: int = 5,
                     num_classes: int = 4):  # trend_up, trend_down, ranging, volatile
            super().__init__()
            
            self.num_scales = num_scales
            
            # Separate LSTM for each scale
            self.scale_lstms = nn.ModuleList([
                nn.LSTM(
                    input_size=input_size,
                    hidden_size=hidden_size,
                    num_layers=num_layers,
                    batch_first=True,
                    dropout=0.2,
                    bidirectional=True
                )
                for _ in range(num_scales)
            ])
            
            # Cross-scale attention
            self.cross_attention = nn.MultiheadAttention(
                embed_dim=hidden_size * 2,
                num_heads=8,
                dropout=0.1
            )
            
            # Scale fusion
            self.scale_fusion = nn.Linear(hidden_size * 2 * num_scales, hidden_size * 2)
            
            # Output layers
            self.fc1 = nn.Linear(hidden_size * 2, 64)
            self.fc2 = nn.Linear(64, num_classes)
            self.fc_magnitude = nn.Linear(64, 1)  # Predicted magnitude
            self.fc_duration = nn.Linear(64, 1)  # Predicted duration
            
            self.dropout = nn.Dropout(0.3)
            
        def forward(self, x_scales: List[torch.Tensor]):
            """
            Args:
                x_scales: List of tensors, one per scale
                         Each tensor shape: (batch, seq, features)
            """
            scale_outputs = []
            
            for i, (lstm, x) in enumerate(zip(self.scale_lstms, x_scales)):
                out, _ = lstm(x)
                scale_outputs.append(out[:, -1, :])  # Last timestep
            
            # Stack scale outputs: (batch, num_scales, hidden*2)
            stacked = torch.stack(scale_outputs, dim=1)
            
            # Cross-scale attention
            attn_out, attn_weights = self.cross_attention(stacked, stacked, stacked)
            
            # Flatten and fuse
            fused = attn_out.view(attn_out.size(0), -1)
            fused = F.relu(self.scale_fusion(fused))
            
            # Shared representation
            shared = self.dropout(F.relu(self.fc1(fused)))
            
            # Outputs
            class_probs = F.softmax(self.fc2(shared), dim=1)
            magnitude = torch.sigmoid(self.fc_magnitude(shared))
            duration = F.relu(self.fc_duration(shared))
            
            return {
                'class_probs': class_probs,
                'magnitude': magnitude,
                'duration': duration,
                'attention_weights': attn_weights
            }
    
    
    class AttentionMechanism(nn.Module):
        """
        Self-attention mechanism for sequence modeling
        """
        
        def __init__(self, hidden_size: int, num_heads: int = 8):
            super().__init__()
            self.attention = nn.MultiheadAttention(
                embed_dim=hidden_size,
                num_heads=num_heads,
                dropout=0.1
            )
            self.norm = nn.LayerNorm(hidden_size)
            
        def forward(self, x, mask=None):
            # x shape: (seq, batch, hidden)
            attn_out, attn_weights = self.attention(x, x, x, attn_mask=mask)
            out = self.norm(x + attn_out)
            return out, attn_weights
    
    
    class TransformerPricePredictor(nn.Module):
        """
        Transformer-based price prediction model
        """
        
        def __init__(self,
                     input_size: int = 64,
                     d_model: int = 256,
                     nhead: int = 8,
                     num_layers: int = 6,
                     dim_feedforward: int = 1024,
                     num_classes: int = 3):
            super().__init__()
            
            self.input_projection = nn.Linear(input_size, d_model)
            
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=d_model,
                nhead=nhead,
                dim_feedforward=dim_feedforward,
                dropout=0.1,
                batch_first=True
            )
            self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
            
            self.fc1 = nn.Linear(d_model, 128)
            self.fc2 = nn.Linear(128, num_classes)
            self.fc_confidence = nn.Linear(128, 1)
            
        def forward(self, x, mask=None):
            # x shape: (batch, seq, features)
            x = self.input_projection(x)
            x = self.transformer(x, src_key_padding_mask=mask)
            
            # Global average pooling
            x = x.mean(dim=1)
            
            x = F.relu(self.fc1(x))
            probs = F.softmax(self.fc2(x), dim=1)
            confidence = torch.sigmoid(self.fc_confidence(x))
            
            return probs, confidence


class DeepLOBPredictor:
    """
    High-level interface for DeepLOB predictions
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.n_levels = self.config.get('n_levels', 10)
        self.seq_length = self.config.get('seq_length', 100)
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu') \
                      if TORCH_AVAILABLE else 'cpu'
        
        self.preprocessor = LOBPreprocessor(n_levels=self.n_levels)
        self.lob_buffer: deque = deque(maxlen=self.seq_length)
        
        if TORCH_AVAILABLE:
            self.model = DeepLOBModel(
                n_levels=self.n_levels,
                seq_length=self.seq_length,
                hidden_size=self.config.get('hidden_size', 64),
                num_classes=3
            ).to(self.device)
            self.model.eval()
        else:
            self.model = None
            logger.warning("DeepLOB model not initialized - PyTorch not available")
        
        self.predictions: List[PricePrediction] = []
        
    def update_lob(self, snapshot: LOBSnapshot):
        """Update LOB buffer with new snapshot"""
        self.lob_buffer.append(snapshot)
    
    def predict(self, horizon: PredictionHorizon = PredictionHorizon.SHORT) -> Optional[PricePrediction]:
        """
        Generate price prediction from current LOB state
        
        Args:
            horizon: Prediction time horizon
            
        Returns:
            PricePrediction or None if insufficient data
        """
        if len(self.lob_buffer) < 10:
            return None
        
        if not TORCH_AVAILABLE or self.model is None:
            # Fallback to simple heuristic
            return self._heuristic_prediction(horizon)
        
        # Prepare input
        features = self.preprocessor.create_sequence(list(self.lob_buffer), self.seq_length)
        
        # Reshape for model: (1, seq, levels, features)
        x = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
        x = x.view(1, self.seq_length, self.n_levels, -1).to(self.device)
        
        # Predict
        with torch.no_grad():
            probs = self.model(x)
        
        probs = probs.cpu().numpy()[0]
        
        # Interpret: [down, neutral, up]
        direction_prob = probs[2]  # Probability of up
        
        # Calculate confidence
        confidence = max(probs) - 0.33  # Deviation from uniform
        confidence = max(0, min(1, confidence * 3))
        
        # Estimate magnitude from LOB imbalance
        latest = self.lob_buffer[-1]
        magnitude = abs(latest.imbalance) * 0.01  # Scale imbalance to expected move
        
        prediction = PricePrediction(
            timestamp=datetime.now(),
            horizon=horizon,
            direction_prob=direction_prob,
            magnitude=magnitude,
            confidence=confidence,
        )
        
        self.predictions.append(prediction)
        return prediction
    
    def _heuristic_prediction(self, horizon: PredictionHorizon) -> PricePrediction:
        """Simple heuristic prediction when model not available"""
        latest = self.lob_buffer[-1]
        
        # Use order imbalance as direction indicator
        direction_prob = 0.5 + latest.imbalance * 0.3
        direction_prob = max(0, min(1, direction_prob))
        
        # Confidence based on imbalance strength
        confidence = abs(latest.imbalance)
        
        return PricePrediction(
            timestamp=datetime.now(),
            horizon=horizon,
            direction_prob=direction_prob,
            magnitude=abs(latest.imbalance) * 0.005,
            confidence=confidence,
        )
    
    def train(self, train_data: List[Tuple[List[LOBSnapshot], int]], 
              epochs: int = 100, batch_size: int = 32):
        """
        Train the DeepLOB model
        
        Args:
            train_data: List of (LOB sequence, label) tuples
            epochs: Number of training epochs
            batch_size: Batch size
        """
        if not TORCH_AVAILABLE:
            logger.error("Cannot train - PyTorch not available")
            return
        
        # Fit preprocessor
        all_snapshots = [s for seq, _ in train_data for s in seq]
        self.preprocessor.fit(all_snapshots)
        
        # Prepare dataset
        X = []
        y = []
        for seq, label in train_data:
            features = self.preprocessor.create_sequence(seq, self.seq_length)
            X.append(features)
            y.append(label)
        
        X = np.array(X)
        y = np.array(y)
        
        # Convert to tensors
        X_tensor = torch.tensor(X, dtype=torch.float32)
        y_tensor = torch.tensor(y, dtype=torch.long)
        
        dataset = torch.utils.data.TensorDataset(X_tensor, y_tensor)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # Training
        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()
        
        for epoch in range(epochs):
            total_loss = 0
            for batch_x, batch_y in dataloader:
                batch_x = batch_x.view(-1, self.seq_length, self.n_levels, 4).to(self.device)
                batch_y = batch_y.to(self.device)
                
                optimizer.zero_grad()
                outputs = self.model(batch_x)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(dataloader):.4f}")
        
        self.model.eval()


class MultiScaleLSTM:
    """
    Multi-Scale LSTM for trend prediction across DC thresholds
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.thresholds = self.config.get('thresholds', [0.001, 0.005, 0.01, 0.02, 0.05])
        self.seq_length = self.config.get('seq_length', 200)
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu') \
                      if TORCH_AVAILABLE else 'cpu'
        
        # Feature buffers for each scale
        self.scale_buffers: Dict[float, deque] = {
            t: deque(maxlen=self.seq_length) for t in self.thresholds
        }
        
        if TORCH_AVAILABLE:
            self.model = MultiScaleLSTMModel(
                input_size=self.config.get('input_size', 64),
                hidden_size=self.config.get('hidden_size', 128),
                num_scales=len(self.thresholds),
                num_classes=4
            ).to(self.device)
            self.model.eval()
        else:
            self.model = None
        
        # Feature extractors
        self.feature_extractors: Dict[float, 'FeatureExtractor'] = {
            t: FeatureExtractor(threshold=t) for t in self.thresholds
        }
    
    def update(self, price: float, volume: float, timestamp: datetime):
        """Update all scale buffers with new data"""
        for threshold, extractor in self.feature_extractors.items():
            features = extractor.extract(price, volume, timestamp)
            self.scale_buffers[threshold].append(features)
    
    def predict(self) -> Dict[str, Any]:
        """Generate multi-scale prediction"""
        if not TORCH_AVAILABLE or self.model is None:
            return self._heuristic_prediction()
        
        # Check if we have enough data
        min_len = min(len(buf) for buf in self.scale_buffers.values())
        if min_len < 20:
            return {'error': 'Insufficient data'}
        
        # Prepare inputs for each scale
        scale_inputs = []
        for threshold in self.thresholds:
            buf = list(self.scale_buffers[threshold])
            # Pad if necessary
            while len(buf) < self.seq_length:
                buf.insert(0, np.zeros_like(buf[0]))
            
            x = torch.tensor(np.array(buf[-self.seq_length:]), dtype=torch.float32)
            x = x.unsqueeze(0).to(self.device)
            scale_inputs.append(x)
        
        # Predict
        with torch.no_grad():
            outputs = self.model(scale_inputs)
        
        class_probs = outputs['class_probs'].cpu().numpy()[0]
        magnitude = outputs['magnitude'].cpu().item()
        duration = outputs['duration'].cpu().item()
        
        # Interpret classes: [trend_up, trend_down, ranging, volatile]
        class_names = ['trend_up', 'trend_down', 'ranging', 'volatile']
        predicted_class = class_names[np.argmax(class_probs)]
        
        return {
            'regime': predicted_class,
            'regime_probs': dict(zip(class_names, class_probs.tolist())),
            'trend_prob': class_probs[0] - class_probs[1],  # Net trend probability
            'magnitude': magnitude,
            'duration': duration,
            'confidence': float(max(class_probs)),
        }
    
    def _heuristic_prediction(self) -> Dict[str, Any]:
        """Fallback heuristic prediction"""
        # Use simple momentum across scales
        momentums = []
        for threshold, buf in self.scale_buffers.items():
            if len(buf) >= 2:
                recent = list(buf)[-10:]
                if len(recent) >= 2:
                    momentum = np.mean([f[0] if len(f) > 0 else 0 for f in recent])
                    momentums.append(momentum)
        
        if not momentums:
            return {'regime': 'unknown', 'confidence': 0}
        
        avg_momentum = np.mean(momentums)
        
        if avg_momentum > 0.01:
            regime = 'trend_up'
        elif avg_momentum < -0.01:
            regime = 'trend_down'
        else:
            regime = 'ranging'
        
        return {
            'regime': regime,
            'trend_prob': avg_momentum,
            'confidence': min(abs(avg_momentum) * 10, 1.0),
        }


class FeatureExtractor:
    """Extract features for a specific DC threshold scale"""
    
    def __init__(self, threshold: float, lookback: int = 100):
        self.threshold = threshold
        self.lookback = lookback
        self.prices: deque = deque(maxlen=lookback)
        self.volumes: deque = deque(maxlen=lookback)
        self.timestamps: deque = deque(maxlen=lookback)
        
    def extract(self, price: float, volume: float, timestamp: datetime) -> np.ndarray:
        """Extract features from new data point"""
        self.prices.append(price)
        self.volumes.append(volume)
        self.timestamps.append(timestamp)
        
        if len(self.prices) < 5:
            return np.zeros(64)
        
        prices = np.array(self.prices)
        volumes = np.array(self.volumes)
        
        features = []
        
        # Price features
        features.append(prices[-1])  # Current price
        features.append(np.mean(prices))  # Mean
        features.append(np.std(prices))  # Volatility
        features.append(prices[-1] - prices[0])  # Total change
        features.append(prices[-1] - prices[-2] if len(prices) > 1 else 0)  # Last change
        
        # Returns
        returns = np.diff(prices) / prices[:-1] if len(prices) > 1 else [0]
        features.append(np.mean(returns))
        features.append(np.std(returns))
        features.append(np.sum(returns > 0) / len(returns) if len(returns) > 0 else 0.5)  # Up ratio
        
        # Volume features
        features.append(volumes[-1])
        features.append(np.mean(volumes))
        features.append(np.std(volumes))
        features.append(volumes[-1] / (np.mean(volumes) + 1e-10))  # Relative volume
        
        # Technical indicators (simplified)
        # RSI-like
        gains = np.maximum(returns, 0)
        losses = np.abs(np.minimum(returns, 0))
        avg_gain = np.mean(gains) if len(gains) > 0 else 0
        avg_loss = np.mean(losses) if len(losses) > 0 else 1e-10
        rsi = 100 - (100 / (1 + avg_gain / avg_loss))
        features.append(rsi)
        
        # Momentum
        if len(prices) >= 10:
            momentum = prices[-1] / prices[-10] - 1
        else:
            momentum = 0
        features.append(momentum)
        
        # Volatility ratio
        if len(prices) >= 20:
            short_vol = np.std(prices[-5:])
            long_vol = np.std(prices[-20:])
            vol_ratio = short_vol / (long_vol + 1e-10)
        else:
            vol_ratio = 1
        features.append(vol_ratio)
        
        # Pad to fixed size
        while len(features) < 64:
            features.append(0)
        
        return np.array(features[:64])


class PricePredictionModel:
    """
    Unified price prediction model combining multiple approaches
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize sub-models
        self.deep_lob = DeepLOBPredictor(config.get('deep_lob', {}))
        self.multi_scale_lstm = MultiScaleLSTM(config.get('multi_scale', {}))
        
        # Ensemble weights
        self.weights = {
            'deep_lob': self.config.get('deep_lob_weight', 0.4),
            'multi_scale': self.config.get('multi_scale_weight', 0.6),
        }
        
        # Prediction history
        self.predictions: List[Dict[str, Any]] = []
        
    def update(self, lob_snapshot: Optional[LOBSnapshot] = None,
               price: float = None, volume: float = None,
               timestamp: datetime = None):
        """Update models with new data"""
        if timestamp is None:
            timestamp = datetime.now()
        
        if lob_snapshot:
            self.deep_lob.update_lob(lob_snapshot)
        
        if price is not None and volume is not None:
            self.multi_scale_lstm.update(price, volume, timestamp)
    
    def predict(self, horizon: PredictionHorizon = PredictionHorizon.SHORT) -> Dict[str, Any]:
        """
        Generate ensemble prediction
        
        Returns:
            Dictionary with prediction details
        """
        predictions = {}
        
        # DeepLOB prediction
        lob_pred = self.deep_lob.predict(horizon)
        if lob_pred:
            predictions['deep_lob'] = {
                'direction_prob': lob_pred.direction_prob,
                'magnitude': lob_pred.magnitude,
                'confidence': lob_pred.confidence,
            }
        
        # Multi-scale LSTM prediction
        lstm_pred = self.multi_scale_lstm.predict()
        if 'error' not in lstm_pred:
            predictions['multi_scale'] = {
                'regime': lstm_pred['regime'],
                'trend_prob': lstm_pred.get('trend_prob', 0),
                'confidence': lstm_pred.get('confidence', 0),
            }
        
        # Ensemble
        if not predictions:
            return {'error': 'No predictions available'}
        
        # Weighted average for direction
        total_weight = 0
        weighted_direction = 0
        weighted_confidence = 0
        
        if 'deep_lob' in predictions:
            w = self.weights['deep_lob']
            weighted_direction += predictions['deep_lob']['direction_prob'] * w
            weighted_confidence += predictions['deep_lob']['confidence'] * w
            total_weight += w
        
        if 'multi_scale' in predictions:
            w = self.weights['multi_scale']
            # Convert trend_prob to direction_prob (0-1 scale)
            trend_prob = predictions['multi_scale']['trend_prob']
            direction_prob = 0.5 + trend_prob / 2
            weighted_direction += direction_prob * w
            weighted_confidence += predictions['multi_scale']['confidence'] * w
            total_weight += w
        
        if total_weight > 0:
            ensemble_direction = weighted_direction / total_weight
            ensemble_confidence = weighted_confidence / total_weight
        else:
            ensemble_direction = 0.5
            ensemble_confidence = 0
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'horizon': horizon.value,
            'direction_prob': ensemble_direction,
            'direction': 'up' if ensemble_direction > 0.55 else ('down' if ensemble_direction < 0.45 else 'neutral'),
            'confidence': ensemble_confidence,
            'sub_predictions': predictions,
            'regime': predictions.get('multi_scale', {}).get('regime', 'unknown'),
        }
        
        self.predictions.append(result)
        return result
    
    def get_accuracy_stats(self, actual_moves: List[float]) -> Dict[str, float]:
        """Calculate prediction accuracy against actual moves"""
        if len(self.predictions) == 0 or len(actual_moves) == 0:
            return {'accuracy': 0, 'samples': 0}
        
        correct = 0
        total = min(len(self.predictions), len(actual_moves))
        
        for i in range(total):
            pred = self.predictions[i]
            actual = actual_moves[i]
            
            pred_dir = pred['direction']
            actual_dir = 'up' if actual > 0 else ('down' if actual < 0 else 'neutral')
            
            if pred_dir == actual_dir:
                correct += 1
        
        return {
            'accuracy': correct / total if total > 0 else 0,
            'samples': total,
            'correct': correct,
        }
