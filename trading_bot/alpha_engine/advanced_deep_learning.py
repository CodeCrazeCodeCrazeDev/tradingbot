"""
Advanced Deep Learning Module
==============================

Comprehensive deep learning for trading:
- DeepLOB: CNN-LSTM for Limit Order Book prediction
- Multi-Timescale LSTM with Attention
- Multi-horizon predictions (10-50 ticks, 100-500 ticks, 1000+ ticks)
- Regime classification
- Confidence scoring
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import math

logger = logging.getLogger(__name__)

# Try importing PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available. Using fallback implementations.")


class PredictionHorizon(Enum):
    """Prediction time horizons"""
    ULTRA_SHORT = "ultra_short"  # 10-50 ticks (5-30 seconds)
    SHORT = "short"  # 100-500 ticks (1-5 minutes)
    MEDIUM = "medium"  # 1000+ ticks (5-30 minutes)


class MarketRegime(Enum):
    """Market regime classifications"""
    TRENDING = "trending"
    RANGING = "ranging"
    VOLATILE = "volatile"
    CALM = "calm"


@dataclass
class LOBSnapshot:
    """Limit Order Book Snapshot"""
    timestamp: datetime
    bid_prices: List[float]  # 10 levels
    bid_volumes: List[float]
    ask_prices: List[float]
    ask_volumes: List[float]
    
    @property
    def mid_price(self) -> float:
        if self.bid_prices and self.ask_prices:
            return (self.bid_prices[0] + self.ask_prices[0]) / 2
        return 0
    
    @property
    def spread(self) -> float:
        if self.bid_prices and self.ask_prices:
            return self.ask_prices[0] - self.bid_prices[0]
        return 0
    
    @property
    def microprice(self) -> float:
        """Volume-weighted microprice"""
        if not self.bid_prices or not self.ask_prices:
            return 0
        bid_vol = self.bid_volumes[0] if self.bid_volumes else 1
        ask_vol = self.ask_volumes[0] if self.ask_volumes else 1
        return (self.bid_prices[0] * ask_vol + self.ask_prices[0] * bid_vol) / (bid_vol + ask_vol)
    
    @property
    def order_imbalance(self) -> float:
        """Order flow imbalance at best levels"""
        if not self.bid_volumes or not self.ask_volumes:
            return 0
        total = self.bid_volumes[0] + self.ask_volumes[0]
        if total == 0:
            return 0
        return (self.bid_volumes[0] - self.ask_volumes[0]) / total
    
    def to_features(self) -> np.ndarray:
        """Convert to feature array (10 levels × 4 features = 40)"""
        features = []
        for i in range(min(10, len(self.bid_prices))):
            features.extend([
                self.bid_prices[i] if i < len(self.bid_prices) else 0,
                self.bid_volumes[i] if i < len(self.bid_volumes) else 0,
                self.ask_prices[i] if i < len(self.ask_prices) else 0,
                self.ask_volumes[i] if i < len(self.ask_volumes) else 0,
            ])
        # Pad if needed
        while len(features) < 40:
            features.append(0)
        return np.array(features[:40])


@dataclass
class DeepLOBPrediction:
    """Prediction from DeepLOB model"""
    timestamp: datetime
    horizon: PredictionHorizon
    direction: str  # 'up', 'down', 'neutral'
    probability_up: float
    probability_down: float
    probability_neutral: float
    expected_magnitude: float
    confidence: float
    
    @property
    def signal_strength(self) -> float:
        """Signal strength based on probability difference"""
        return abs(self.probability_up - self.probability_down)


@dataclass
class LSTMPrediction:
    """Prediction from Multi-Timescale LSTM"""
    timestamp: datetime
    trend_probability: float  # Probability of trend continuation
    reversal_probability: float
    expected_duration_ticks: int
    volatility_forecast: float
    regime: MarketRegime
    confidence: float


if TORCH_AVAILABLE:
    
    class DeepLOBModel(nn.Module):
        """
        DeepLOB: CNN-LSTM Hybrid for LOB Prediction
        
        Architecture:
        - Convolutional layers for spatial feature extraction
        - LSTM for temporal dependencies
        - Fully connected layers for prediction
        
        Input: (batch, sequence_length, 40) - 10 levels × 4 features
        Output: (batch, 3) - probabilities for up/down/neutral
        """
        
        def __init__(self, config: Dict[str, Any] = None):
            super().__init__()
            self.config = config or {}
            
            # Architecture parameters
            self.input_dim = self.config.get('input_dim', 40)
            self.hidden_dim = self.config.get('hidden_dim', 64)
            self.num_layers = self.config.get('num_layers', 2)
            self.num_classes = self.config.get('num_classes', 3)
            
            # Convolutional layers
            self.conv1 = nn.Conv1d(self.input_dim, 32, kernel_size=3, padding=1)
            self.conv2 = nn.Conv1d(32, 64, kernel_size=3, padding=1)
            self.conv3 = nn.Conv1d(64, 64, kernel_size=3, padding=1)
            
            self.bn1 = nn.BatchNorm1d(32)
            self.bn2 = nn.BatchNorm1d(64)
            self.bn3 = nn.BatchNorm1d(64)
            
            # LSTM layers
            self.lstm = nn.LSTM(
                input_size=64,
                hidden_size=self.hidden_dim,
                num_layers=self.num_layers,
                batch_first=True,
                dropout=0.2 if self.num_layers > 1 else 0,
                bidirectional=True,
            )
            
            # Attention mechanism
            self.attention = nn.MultiheadAttention(
                embed_dim=self.hidden_dim * 2,
                num_heads=4,
                dropout=0.1,
            )
            
            # Fully connected layers
            self.fc1 = nn.Linear(self.hidden_dim * 2, 64)
            self.fc2 = nn.Linear(64, 32)
            self.fc3 = nn.Linear(32, self.num_classes)
            
            # Magnitude prediction head
            self.magnitude_head = nn.Linear(32, 1)
            
            self.dropout = nn.Dropout(0.3)
        
        def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
            """
            Forward pass
            
            Args:
                x: Input tensor (batch, seq_len, features)
                
            Returns:
                Tuple of (class_probs, magnitude)
            """
            batch_size, seq_len, features = x.shape
            
            # Reshape for conv: (batch, features, seq_len)
            x = x.permute(0, 2, 1)
            
            # Convolutional layers
            x = F.relu(self.bn1(self.conv1(x)))
            x = F.relu(self.bn2(self.conv2(x)))
            x = F.relu(self.bn3(self.conv3(x)))
            
            # Reshape for LSTM: (batch, seq_len, features)
            x = x.permute(0, 2, 1)
            
            # LSTM
            lstm_out, _ = self.lstm(x)
            
            # Attention
            # Reshape for attention: (seq_len, batch, features)
            attn_input = lstm_out.permute(1, 0, 2)
            attn_out, _ = self.attention(attn_input, attn_input, attn_input)
            
            # Take last timestep
            x = attn_out[-1]  # (batch, hidden_dim * 2)
            
            # Fully connected
            x = F.relu(self.fc1(x))
            x = self.dropout(x)
            x = F.relu(self.fc2(x))
            
            # Classification output
            class_logits = self.fc3(x)
            class_probs = F.softmax(class_logits, dim=-1)
            
            # Magnitude output
            magnitude = torch.sigmoid(self.magnitude_head(x)) * 0.05  # Max 5% move
            
            return class_probs, magnitude
    
    
    class MultiScaleLSTMModel(nn.Module):
        """
        Multi-Timescale Bi-LSTM with Attention
        
        Processes data at multiple DC thresholds simultaneously
        for comprehensive trend prediction.
        
        Input: Multiple time series at different scales
        Output: Trend probability, duration, volatility, regime
        """
        
        def __init__(self, config: Dict[str, Any] = None):
            super().__init__()
            self.config = config or {}
            
            # Architecture parameters
            self.num_scales = self.config.get('num_scales', 5)  # 0.1%, 0.5%, 1%, 2%, 5%
            self.input_dim = self.config.get('input_dim', 10)  # Features per scale
            self.hidden_dim = self.config.get('hidden_dim', 64)
            self.num_layers = self.config.get('num_layers', 2)
            
            # Per-scale LSTM encoders
            self.scale_encoders = nn.ModuleList([
                nn.LSTM(
                    input_size=self.input_dim,
                    hidden_size=self.hidden_dim,
                    num_layers=self.num_layers,
                    batch_first=True,
                    bidirectional=True,
                    dropout=0.2 if self.num_layers > 1 else 0,
                )
                for _ in range(self.num_scales)
            ])
            
            # Cross-scale attention
            self.cross_attention = nn.MultiheadAttention(
                embed_dim=self.hidden_dim * 2,
                num_heads=4,
                dropout=0.1,
            )
            
            # Fusion layer
            self.fusion = nn.Linear(self.hidden_dim * 2 * self.num_scales, 256)
            
            # Output heads
            self.trend_head = nn.Sequential(
                nn.Linear(256, 64),
                nn.ReLU(),
                nn.Linear(64, 2),  # continuation vs reversal
            )
            
            self.duration_head = nn.Sequential(
                nn.Linear(256, 64),
                nn.ReLU(),
                nn.Linear(64, 1),  # expected duration
            )
            
            self.volatility_head = nn.Sequential(
                nn.Linear(256, 64),
                nn.ReLU(),
                nn.Linear(64, 1),  # volatility forecast
            )
            
            self.regime_head = nn.Sequential(
                nn.Linear(256, 64),
                nn.ReLU(),
                nn.Linear(64, 4),  # 4 regimes
            )
        
        def forward(self, x_list: List[torch.Tensor]) -> Dict[str, torch.Tensor]:
            """
            Forward pass
            
            Args:
                x_list: List of tensors, one per scale (batch, seq_len, features)
                
            Returns:
                Dictionary of predictions
            """
            scale_outputs = []
            
            # Encode each scale
            for i, (encoder, x) in enumerate(zip(self.scale_encoders, x_list)):
                lstm_out, _ = encoder(x)
                # Take last hidden state
                scale_outputs.append(lstm_out[:, -1, :])  # (batch, hidden_dim * 2)
            
            # Stack scale outputs: (num_scales, batch, hidden_dim * 2)
            stacked = torch.stack(scale_outputs, dim=0)
            
            # Cross-scale attention
            attn_out, _ = self.cross_attention(stacked, stacked, stacked)
            
            # Flatten and fuse
            batch_size = attn_out.shape[1]
            fused = attn_out.permute(1, 0, 2).reshape(batch_size, -1)  # (batch, num_scales * hidden_dim * 2)
            fused = F.relu(self.fusion(fused))
            
            # Output predictions
            trend_logits = self.trend_head(fused)
            trend_probs = F.softmax(trend_logits, dim=-1)
            
            duration = F.relu(self.duration_head(fused)) * 1000  # Scale to ticks
            
            volatility = F.relu(self.volatility_head(fused)) * 0.1  # Max 10% vol
            
            regime_logits = self.regime_head(fused)
            regime_probs = F.softmax(regime_logits, dim=-1)
            
            return {
                'trend_probs': trend_probs,
                'duration': duration,
                'volatility': volatility,
                'regime_probs': regime_probs,
            }


class LOBPreprocessor:
    """
    Preprocesses LOB data for deep learning models
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Normalization parameters
        self.price_mean = 0.0
        self.price_std = 1.0
        self.volume_mean = 0.0
        self.volume_std = 1.0
        
        # History for normalization
        self.price_history: deque = deque(maxlen=10000)
        self.volume_history: deque = deque(maxlen=10000)
        
        self.is_fitted = False
    
    def fit(self, snapshots: List[LOBSnapshot]):
        """Fit normalization parameters"""
        prices = []
        volumes = []
        
        for snap in snapshots:
            prices.extend(snap.bid_prices + snap.ask_prices)
            volumes.extend(snap.bid_volumes + snap.ask_volumes)
        
        self.price_mean = np.mean(prices)
        self.price_std = np.std(prices) + 1e-8
        self.volume_mean = np.mean(volumes)
        self.volume_std = np.std(volumes) + 1e-8
        
        self.is_fitted = True
    
    def transform(self, snapshot: LOBSnapshot) -> np.ndarray:
        """Transform LOB snapshot to normalized features"""
        features = snapshot.to_features()
        
        # Separate prices and volumes
        normalized = np.zeros_like(features)
        for i in range(0, len(features), 4):
            # Normalize prices (indices 0, 2)
            normalized[i] = (features[i] - self.price_mean) / self.price_std
            normalized[i+2] = (features[i+2] - self.price_mean) / self.price_std
            # Normalize volumes (indices 1, 3)
            normalized[i+1] = (features[i+1] - self.volume_mean) / self.volume_std
            normalized[i+3] = (features[i+3] - self.volume_mean) / self.volume_std
        
        # Add derived features
        extra_features = np.array([
            snapshot.spread / self.price_std,
            snapshot.microprice / self.price_mean - 1,
            snapshot.order_imbalance,
        ])
        
        return np.concatenate([normalized, extra_features])
    
    def create_sequences(self, snapshots: List[LOBSnapshot], 
                        seq_length: int = 100) -> np.ndarray:
        """Create sequences for LSTM input"""
        features = [self.transform(s) for s in snapshots]
        
        sequences = []
        for i in range(len(features) - seq_length + 1):
            sequences.append(features[i:i+seq_length])
        
        return np.array(sequences)


class DeepLOBPredictor:
    """
    High-level interface for DeepLOB predictions
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize model
        if TORCH_AVAILABLE:
            self.model = DeepLOBModel(config)
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)
            self.model.eval()
        else:
            self.model = None
        
        # Preprocessor
        self.preprocessor = LOBPreprocessor(config)
        
        # Prediction history
        self.predictions: deque = deque(maxlen=1000)
        
        # Sequence length
        self.seq_length = self.config.get('seq_length', 100)
        
        # LOB history
        self.lob_history: deque = deque(maxlen=self.seq_length + 100)
    
    def update(self, snapshot: LOBSnapshot):
        """Update with new LOB snapshot"""
        self.lob_history.append(snapshot)
        
        # Fit preprocessor if needed
        if not self.preprocessor.is_fitted and len(self.lob_history) >= 100:
            self.preprocessor.fit(list(self.lob_history))
    
    def predict(self, horizon: PredictionHorizon = PredictionHorizon.SHORT) -> Optional[DeepLOBPrediction]:
        """
        Generate prediction
        
        Args:
            horizon: Prediction horizon
            
        Returns:
            DeepLOBPrediction or None if insufficient data
        """
        if len(self.lob_history) < self.seq_length:
            return None
        
        if not self.preprocessor.is_fitted:
            return None
        
        # Use fallback if PyTorch not available
        if not TORCH_AVAILABLE or self.model is None:
            return self._fallback_predict(horizon)
        
        # Prepare input
        recent_snapshots = list(self.lob_history)[-self.seq_length:]
        sequences = self.preprocessor.create_sequences(recent_snapshots, self.seq_length)
        
        if len(sequences) == 0:
            return None
        
        # Get last sequence
        x = torch.FloatTensor(sequences[-1:]).to(self.device)
        
        # Predict
        with torch.no_grad():
            class_probs, magnitude = self.model(x)
        
        probs = class_probs[0].cpu().numpy()
        mag = magnitude[0].item()
        
        # Determine direction
        if probs[0] > probs[1] and probs[0] > probs[2]:
            direction = 'up'
        elif probs[1] > probs[0] and probs[1] > probs[2]:
            direction = 'down'
        else:
            direction = 'neutral'
        
        # Calculate confidence
        confidence = max(probs) - np.median(probs)
        
        prediction = DeepLOBPrediction(
            timestamp=datetime.now(),
            horizon=horizon,
            direction=direction,
            probability_up=probs[0],
            probability_down=probs[1],
            probability_neutral=probs[2],
            expected_magnitude=mag,
            confidence=confidence,
        )
        
        self.predictions.append(prediction)
        
        return prediction
    
    def _fallback_predict(self, horizon: PredictionHorizon) -> DeepLOBPrediction:
        """Fallback prediction using simple heuristics"""
        recent = list(self.lob_history)[-20:]
        
        if len(recent) < 2:
            return DeepLOBPrediction(
                timestamp=datetime.now(),
                horizon=horizon,
                direction='neutral',
                probability_up=0.33,
                probability_down=0.33,
                probability_neutral=0.34,
                expected_magnitude=0.001,
                confidence=0.0,
            )
        
        # Simple momentum-based prediction
        price_changes = []
        for i in range(1, len(recent)):
            if recent[i-1].mid_price > 0:
                change = (recent[i].mid_price - recent[i-1].mid_price) / recent[i-1].mid_price
                price_changes.append(change)
        
        if not price_changes:
            return DeepLOBPrediction(
                timestamp=datetime.now(),
                horizon=horizon,
                direction='neutral',
                probability_up=0.33,
                probability_down=0.33,
                probability_neutral=0.34,
                expected_magnitude=0.001,
                confidence=0.0,
            )
        
        avg_change = np.mean(price_changes)
        volatility = np.std(price_changes)
        
        # Order imbalance signal
        imbalance = recent[-1].order_imbalance
        
        # Combined signal
        signal = avg_change * 100 + imbalance * 0.5
        
        if signal > 0.1:
            direction = 'up'
            prob_up = min(0.5 + signal * 0.3, 0.8)
            prob_down = (1 - prob_up) * 0.6
            prob_neutral = 1 - prob_up - prob_down
        elif signal < -0.1:
            direction = 'down'
            prob_down = min(0.5 + abs(signal) * 0.3, 0.8)
            prob_up = (1 - prob_down) * 0.6
            prob_neutral = 1 - prob_up - prob_down
        else:
            direction = 'neutral'
            prob_neutral = 0.5
            prob_up = prob_down = 0.25
        
        return DeepLOBPrediction(
            timestamp=datetime.now(),
            horizon=horizon,
            direction=direction,
            probability_up=prob_up,
            probability_down=prob_down,
            probability_neutral=prob_neutral,
            expected_magnitude=volatility * 2,
            confidence=abs(signal) / 2,
        )
    
    def get_multi_horizon_predictions(self) -> Dict[PredictionHorizon, DeepLOBPrediction]:
        """Get predictions for all horizons"""
        return {
            horizon: self.predict(horizon)
            for horizon in PredictionHorizon
        }


class MultiScaleLSTMPredictor:
    """
    High-level interface for Multi-Scale LSTM predictions
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # DC thresholds for multi-scale
        self.thresholds = self.config.get('thresholds', [0.001, 0.005, 0.01, 0.02, 0.05])
        
        # Initialize model
        if TORCH_AVAILABLE:
            self.model = MultiScaleLSTMModel({
                'num_scales': len(self.thresholds),
                **config
            })
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)
            self.model.eval()
        else:
            self.model = None
        
        # Per-scale data history
        self.scale_histories: Dict[float, deque] = {
            t: deque(maxlen=1000) for t in self.thresholds
        }
        
        # Price history
        self.price_history: deque = deque(maxlen=10000)
        
        # Prediction history
        self.predictions: deque = deque(maxlen=1000)
        
        # Technical indicators
        self.indicators: Dict[str, deque] = {
            'rsi': deque(maxlen=1000),
            'macd': deque(maxlen=1000),
            'bb_position': deque(maxlen=1000),
        }
    
    def update(self, price: float, volume: float = 0, timestamp: datetime = None):
        """Update with new price data"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.price_history.append({
            'price': price,
            'volume': volume,
            'timestamp': timestamp,
        })
        
        # Update technical indicators
        self._update_indicators()
        
        # Update per-scale features
        self._update_scale_features()
    
    def _update_indicators(self):
        """Update technical indicators"""
        prices = [p['price'] for p in self.price_history]
        
        if len(prices) < 26:
            return
        
        # RSI
        rsi = self._calculate_rsi(prices, 14)
        self.indicators['rsi'].append(rsi)
        
        # MACD
        macd = self._calculate_macd(prices)
        self.indicators['macd'].append(macd)
        
        # Bollinger Band position
        bb_pos = self._calculate_bb_position(prices, 20)
        self.indicators['bb_position'].append(bb_pos)
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, prices: List[float]) -> float:
        """Calculate MACD"""
        if len(prices) < 26:
            return 0.0
        
        ema12 = self._ema(prices, 12)
        ema26 = self._ema(prices, 26)
        
        return ema12 - ema26
    
    def _ema(self, prices: List[float], period: int) -> float:
        """Calculate EMA"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        multiplier = 2 / (period + 1)
        ema = prices[-period]
        
        for price in prices[-period+1:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _calculate_bb_position(self, prices: List[float], period: int = 20) -> float:
        """Calculate position within Bollinger Bands (0-1)"""
        if len(prices) < period:
            return 0.5
        
        recent = prices[-period:]
        mean = np.mean(recent)
        std = np.std(recent)
        
        if std == 0:
            return 0.5
        
        upper = mean + 2 * std
        lower = mean - 2 * std
        
        current = prices[-1]
        position = (current - lower) / (upper - lower)
        
        return np.clip(position, 0, 1)
    
    def _update_scale_features(self):
        """Update features for each scale"""
        prices = [p['price'] for p in self.price_history]
        
        if len(prices) < 50:
            return
        
        for threshold in self.thresholds:
            features = self._extract_scale_features(prices, threshold)
            self.scale_histories[threshold].append(features)
    
    def _extract_scale_features(self, prices: List[float], threshold: float) -> np.ndarray:
        """Extract features for a specific scale"""
        # Returns at this scale
        lookback = int(1 / threshold)  # Adaptive lookback
        lookback = max(10, min(lookback, len(prices) - 1))
        
        returns = []
        for i in range(1, lookback + 1):
            if len(prices) > i:
                ret = (prices[-1] - prices[-i-1]) / prices[-i-1]
                returns.append(ret)
        
        if not returns:
            return np.zeros(10)
        
        # Features
        features = [
            np.mean(returns),
            np.std(returns),
            np.min(returns),
            np.max(returns),
            returns[-1] if returns else 0,  # Most recent return
            self.indicators['rsi'][-1] / 100 if self.indicators['rsi'] else 0.5,
            self.indicators['macd'][-1] / prices[-1] if self.indicators['macd'] else 0,
            self.indicators['bb_position'][-1] if self.indicators['bb_position'] else 0.5,
            threshold,  # Scale identifier
            len(prices) / 10000,  # Normalized time
        ]
        
        return np.array(features)
    
    def predict(self) -> Optional[LSTMPrediction]:
        """Generate prediction"""
        # Check if we have enough data
        min_history = min(len(h) for h in self.scale_histories.values())
        if min_history < 50:
            return None
        
        # Use fallback if PyTorch not available
        if not TORCH_AVAILABLE or self.model is None:
            return self._fallback_predict()
        
        # Prepare inputs for each scale
        seq_length = 50
        x_list = []
        
        for threshold in self.thresholds:
            history = list(self.scale_histories[threshold])[-seq_length:]
            x = torch.FloatTensor([history]).to(self.device)
            x_list.append(x)
        
        # Predict
        with torch.no_grad():
            outputs = self.model(x_list)
        
        trend_probs = outputs['trend_probs'][0].cpu().numpy()
        duration = outputs['duration'][0].item()
        volatility = outputs['volatility'][0].item()
        regime_probs = outputs['regime_probs'][0].cpu().numpy()
        
        # Determine regime
        regime_idx = np.argmax(regime_probs)
        regime = [MarketRegime.TRENDING, MarketRegime.RANGING, 
                 MarketRegime.VOLATILE, MarketRegime.CALM][regime_idx]
        
        prediction = LSTMPrediction(
            timestamp=datetime.now(),
            trend_probability=trend_probs[0],
            reversal_probability=trend_probs[1],
            expected_duration_ticks=int(duration),
            volatility_forecast=volatility,
            regime=regime,
            confidence=max(trend_probs) - 0.5,
        )
        
        self.predictions.append(prediction)
        
        return prediction
    
    def _fallback_predict(self) -> LSTMPrediction:
        """Fallback prediction using heuristics"""
        prices = [p['price'] for p in self.price_history]
        
        if len(prices) < 50:
            return LSTMPrediction(
                timestamp=datetime.now(),
                trend_probability=0.5,
                reversal_probability=0.5,
                expected_duration_ticks=100,
                volatility_forecast=0.02,
                regime=MarketRegime.CALM,
                confidence=0.0,
            )
        
        # Calculate trend
        short_ma = np.mean(prices[-10:])
        long_ma = np.mean(prices[-50:])
        trend = (short_ma - long_ma) / long_ma
        
        # Calculate volatility
        returns = np.diff(prices[-50:]) / prices[-51:-1]
        volatility = np.std(returns) * np.sqrt(252)
        
        # Determine regime
        if volatility > 0.4:
            regime = MarketRegime.VOLATILE
        elif volatility < 0.1:
            regime = MarketRegime.CALM
        elif abs(trend) > 0.02:
            regime = MarketRegime.TRENDING
        else:
            regime = MarketRegime.RANGING
        
        # Trend probability
        if trend > 0.01:
            trend_prob = min(0.5 + trend * 10, 0.8)
        elif trend < -0.01:
            trend_prob = max(0.5 + trend * 10, 0.2)
        else:
            trend_prob = 0.5
        
        return LSTMPrediction(
            timestamp=datetime.now(),
            trend_probability=trend_prob,
            reversal_probability=1 - trend_prob,
            expected_duration_ticks=int(100 / (volatility + 0.01)),
            volatility_forecast=volatility,
            regime=regime,
            confidence=abs(trend_prob - 0.5),
        )


class IntegratedDeepLearningEngine:
    """
    Integrated Deep Learning Engine
    
    Combines DeepLOB and Multi-Scale LSTM for comprehensive predictions
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize predictors
        self.lob_predictor = DeepLOBPredictor(config.get('lob', {}))
        self.lstm_predictor = MultiScaleLSTMPredictor(config.get('lstm', {}))
        
        # Ensemble weights
        self.lob_weight = self.config.get('lob_weight', 0.4)
        self.lstm_weight = self.config.get('lstm_weight', 0.6)
        
        # Combined predictions
        self.combined_predictions: deque = deque(maxlen=1000)
    
    def update_lob(self, snapshot: LOBSnapshot):
        """Update LOB predictor"""
        self.lob_predictor.update(snapshot)
    
    def update_price(self, price: float, volume: float = 0, timestamp: datetime = None):
        """Update LSTM predictor"""
        self.lstm_predictor.update(price, volume, timestamp)
    
    def predict(self) -> Dict[str, Any]:
        """Generate combined prediction"""
        lob_pred = self.lob_predictor.predict(PredictionHorizon.SHORT)
        lstm_pred = self.lstm_predictor.predict()
        
        if lob_pred is None and lstm_pred is None:
            return {
                'direction': 'neutral',
                'confidence': 0,
                'should_trade': False,
            }
        
        # Combine predictions
        combined_up = 0
        combined_down = 0
        total_weight = 0
        
        if lob_pred:
            combined_up += lob_pred.probability_up * self.lob_weight
            combined_down += lob_pred.probability_down * self.lob_weight
            total_weight += self.lob_weight
        
        if lstm_pred:
            # Map trend probability to direction
            if lstm_pred.trend_probability > 0.5:
                combined_up += lstm_pred.trend_probability * self.lstm_weight
                combined_down += lstm_pred.reversal_probability * self.lstm_weight
            else:
                combined_up += lstm_pred.reversal_probability * self.lstm_weight
                combined_down += lstm_pred.trend_probability * self.lstm_weight
            total_weight += self.lstm_weight
        
        if total_weight > 0:
            combined_up /= total_weight
            combined_down /= total_weight
        
        # Determine direction
        if combined_up > combined_down + 0.1:
            direction = 'long'
        elif combined_down > combined_up + 0.1:
            direction = 'short'
        else:
            direction = 'neutral'
        
        confidence = abs(combined_up - combined_down)
        
        result = {
            'direction': direction,
            'probability_up': combined_up,
            'probability_down': combined_down,
            'confidence': confidence,
            'should_trade': confidence > 0.2,
            'lob_prediction': lob_pred,
            'lstm_prediction': lstm_pred,
            'regime': lstm_pred.regime if lstm_pred else MarketRegime.CALM,
            'volatility_forecast': lstm_pred.volatility_forecast if lstm_pred else 0.02,
        }
        
        self.combined_predictions.append(result)
        
        return result
