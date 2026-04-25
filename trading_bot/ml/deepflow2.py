"""
DeepFlow 2.0 - Optical Flow Analysis for Price Movement
========================================================

Advanced optical flow-inspired analysis for detecting price movement
patterns, momentum flows, and market dynamics. Treats price charts
as visual sequences and applies flow estimation techniques.

Features:
- Price flow estimation
- Momentum flow vectors
- Flow-based trend detection
- Multi-scale flow analysis
- Flow divergence/convergence detection
- Temporal flow consistency
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
from collections import deque

logger = logging.getLogger(__name__)


class FlowType(Enum):
    """Types of flow patterns detected by DeepFlow."""
    STRONG_UPFLOW = "strong_upflow"
    WEAK_UPFLOW = "weak_upflow"
    STRONG_DOWNFLOW = "strong_downflow"
    WEAK_DOWNFLOW = "weak_downflow"
    DIVERGENT = "divergent"
    CONVERGENT = "convergent"
    ROTATIONAL = "rotational"
    STAGNANT = "stagnant"
    ACCELERATING = "accelerating"
    DECELERATING = "decelerating"


@dataclass
class FlowVector:
    """A flow vector representing price movement."""
    magnitude: float
    direction: float  # angle in radians
    x_component: float
    y_component: float
    confidence: float
    timestamp: float


@dataclass
class DeepFlowConfig:
    """Configuration for DeepFlow 2.0 system."""
    hidden_dim: int = 256
    num_scales: int = 4
    num_flow_layers: int = 6
    correlation_radius: int = 4
    context_dim: int = 128
    flow_dim: int = 64
    num_heads: int = 8
    dropout: float = 0.1
    sequence_length: int = 100
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


class CorrelationVolume(nn.Module):
    """
    Computes correlation volume between price sequences.
    Inspired by RAFT optical flow architecture.
    """
    
    def __init__(self, num_levels: int = 4, radius: int = 4):
        super().__init__()
        self.num_levels = num_levels
        self.radius = radius
    
    def forward(
        self, 
        fmap1: torch.Tensor, 
        fmap2: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute correlation volume.
        
        Args:
            fmap1: [batch, channels, length] first feature map
            fmap2: [batch, channels, length] second feature map
        
        Returns:
            Correlation volume
        """
        batch, channels, length = fmap1.shape
        
        fmap1 = fmap1 / (fmap1.norm(dim=1, keepdim=True) + 1e-8)
        fmap2 = fmap2 / (fmap2.norm(dim=1, keepdim=True) + 1e-8)
        
        corr = torch.einsum('bci,bcj->bij', fmap1, fmap2)
        
        corr_pyramid = [corr]
        for _ in range(self.num_levels - 1):
            corr = F.avg_pool1d(corr, kernel_size=2, stride=2)
            corr_pyramid.append(corr)
        
        return corr_pyramid


class FlowEncoder(nn.Module):
    """Encodes price sequences for flow estimation."""
    
    def __init__(self, input_dim: int = 5, hidden_dim: int = 256):
        super().__init__()
        
        self.conv1 = nn.Conv1d(input_dim, hidden_dim // 4, kernel_size=7, padding=3)
        self.conv2 = nn.Conv1d(hidden_dim // 4, hidden_dim // 2, kernel_size=5, padding=2)
        self.conv3 = nn.Conv1d(hidden_dim // 2, hidden_dim, kernel_size=3, padding=1)
        
        self.norm1 = nn.BatchNorm1d(hidden_dim // 4)
        self.norm2 = nn.BatchNorm1d(hidden_dim // 2)
        self.norm3 = nn.BatchNorm1d(hidden_dim)
        
        self.residual = nn.Conv1d(input_dim, hidden_dim, kernel_size=1)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Encode price sequence.
        
        Args:
            x: [batch, features, length] price data
               features: [open, high, low, close, volume]
        """
        residual = self.residual(x)
        
        x = F.gelu(self.norm1(self.conv1(x)))
        x = F.gelu(self.norm2(self.conv2(x)))
        x = F.gelu(self.norm3(self.conv3(x)))
        
        return x + residual


class ContextEncoder(nn.Module):
    """Encodes context for flow refinement."""
    
    def __init__(self, input_dim: int = 5, context_dim: int = 128, hidden_dim: int = 256):
        super().__init__()
        
        self.encoder = nn.Sequential(
            nn.Conv1d(input_dim, hidden_dim // 2, kernel_size=7, padding=3),
            nn.BatchNorm1d(hidden_dim // 2),
            nn.GELU(),
            nn.Conv1d(hidden_dim // 2, hidden_dim, kernel_size=5, padding=2),
            nn.BatchNorm1d(hidden_dim),
            nn.GELU(),
            nn.Conv1d(hidden_dim, context_dim + hidden_dim, kernel_size=3, padding=1)
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Encode context.
        
        Returns:
            Tuple of (context_features, hidden_state)
        """
        out = self.encoder(x)
        context = out[:, :128]
        hidden = out[:, 128:]
        return context, hidden


class FlowHead(nn.Module):
    """Predicts flow vectors from features."""
    
    def __init__(self, hidden_dim: int = 256, flow_dim: int = 64):
        super().__init__()
        
        self.conv1 = nn.Conv1d(hidden_dim, hidden_dim, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(hidden_dim, flow_dim, kernel_size=3, padding=1)
        
        self.flow_predictor = nn.Conv1d(flow_dim, 2, kernel_size=1)
        
        self.magnitude_head = nn.Sequential(
            nn.Conv1d(flow_dim, flow_dim // 2, kernel_size=1),
            nn.GELU(),
            nn.Conv1d(flow_dim // 2, 1, kernel_size=1),
            nn.Softplus()
        )
        
        self.confidence_head = nn.Sequential(
            nn.Conv1d(flow_dim, flow_dim // 2, kernel_size=1),
            nn.GELU(),
            nn.Conv1d(flow_dim // 2, 1, kernel_size=1),
            nn.Sigmoid()
        )
    
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Predict flow vectors.
        
        Args:
            x: [batch, hidden_dim, length] features
        
        Returns:
            Dictionary with flow predictions
        """
        x = F.gelu(self.conv1(x))
        x = F.gelu(self.conv2(x))
        
        flow = self.flow_predictor(x)
        magnitude = self.magnitude_head(x)
        confidence = self.confidence_head(x)
        
        return {
            'flow': flow,
            'magnitude': magnitude,
            'confidence': confidence
        }


class GRUFlowUpdate(nn.Module):
    """GRU-based iterative flow update."""
    
    def __init__(self, hidden_dim: int = 256, context_dim: int = 128):
        super().__init__()
        
        self.gru = nn.GRU(
            input_size=context_dim + 2,
            hidden_size=hidden_dim,
            batch_first=True
        )
        
        self.flow_head = FlowHead(hidden_dim)
    
    def forward(
        self,
        hidden: torch.Tensor,
        context: torch.Tensor,
        flow: torch.Tensor
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Update flow estimate.
        
        Args:
            hidden: Hidden state
            context: Context features
            flow: Current flow estimate
        
        Returns:
            Updated hidden state and flow predictions
        """
        flow_input = torch.cat([context, flow], dim=1)
        flow_input = flow_input.transpose(1, 2)
        hidden = hidden.transpose(1, 2)
        
        output, new_hidden = self.gru(flow_input, hidden.unsqueeze(0))
        
        output = output.transpose(1, 2)
        new_hidden = new_hidden.squeeze(0).transpose(1, 2)
        
        flow_pred = self.flow_head(output)
        
        return new_hidden, flow_pred


class MultiScaleFlowEstimator(nn.Module):
    """Estimates flow at multiple scales."""
    
    def __init__(self, config: DeepFlowConfig):
        super().__init__()
        self.config = config
        
        self.encoders = nn.ModuleList([
            FlowEncoder(5, config.hidden_dim // (2 ** i))
            for i in range(config.num_scales)
        ])
        
        self.flow_heads = nn.ModuleList([
            FlowHead(config.hidden_dim // (2 ** i), config.flow_dim // (2 ** i))
            for i in range(config.num_scales)
        ])
        
        self.upsample = nn.ModuleList([
            nn.ConvTranspose1d(2, 2, kernel_size=4, stride=2, padding=1)
            for _ in range(config.num_scales - 1)
        ])
    
    def forward(self, x: torch.Tensor) -> List[Dict[str, torch.Tensor]]:
        """
        Estimate flow at multiple scales.
        
        Args:
            x: [batch, features, length] price data
        
        Returns:
            List of flow predictions at each scale
        """
        flows = []
        current = x
        
        for i, (encoder, flow_head) in enumerate(zip(self.encoders, self.flow_heads)):
            features = encoder(current)
            flow_pred = flow_head(features)
            flows.append(flow_pred)
            
            if i < len(self.encoders) - 1:
                current = F.avg_pool1d(current, kernel_size=2, stride=2)
        
        return flows


class FlowAttention(nn.Module):
    """Attention mechanism for flow refinement."""
    
    def __init__(self, hidden_dim: int = 256, num_heads: int = 8):
        super().__init__()
        
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            dropout=0.1,
            batch_first=True
        )
        
        self.norm = nn.LayerNorm(hidden_dim)
        
        self.ffn = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 4),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim * 4, hidden_dim)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply attention to flow features."""
        x = x.transpose(1, 2)
        
        attn_out, _ = self.attention(x, x, x)
        x = self.norm(x + attn_out)
        x = x + self.ffn(x)
        
        return x.transpose(1, 2)


class FlowClassifier(nn.Module):
    """Classifies flow patterns."""
    
    def __init__(self, hidden_dim: int = 256, num_classes: int = 10):
        super().__init__()
        
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim + 2, hidden_dim),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, num_classes)
        )
    
    def forward(
        self, 
        features: torch.Tensor,
        flow: torch.Tensor
    ) -> torch.Tensor:
        """
        Classify flow pattern.
        
        Args:
            features: [batch, hidden_dim, length] features
            flow: [batch, 2, length] flow vectors
        """
        feat_pooled = self.global_pool(features).squeeze(-1)
        flow_pooled = self.global_pool(flow).squeeze(-1)
        
        combined = torch.cat([feat_pooled, flow_pooled], dim=-1)
        
        return self.classifier(combined)


class DeepFlowNet(nn.Module):
    """
    Complete DeepFlow 2.0 network for price flow estimation.
    """
    
    def __init__(self, config: DeepFlowConfig):
        super().__init__()
        self.config = config
        
        self.feature_encoder = FlowEncoder(5, config.hidden_dim)
        self.context_encoder = ContextEncoder(5, config.context_dim, config.hidden_dim)
        
        self.correlation = CorrelationVolume(config.num_scales, config.correlation_radius)
        
        self.multi_scale = MultiScaleFlowEstimator(config)
        
        self.flow_attention = FlowAttention(config.hidden_dim, config.num_heads)
        
        self.gru_update = GRUFlowUpdate(config.hidden_dim, config.context_dim)
        
        self.flow_classifier = FlowClassifier(config.hidden_dim, len(FlowType))
        
        self.trend_predictor = nn.Sequential(
            nn.Linear(config.hidden_dim + 2, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, 3)  # up, down, sideways
        )
        
        self.momentum_predictor = nn.Sequential(
            nn.Linear(config.hidden_dim + 2, config.hidden_dim // 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim // 2, 1),
            nn.Tanh()
        )
    
    def forward(
        self,
        price_sequence: torch.Tensor,
        num_iterations: int = 12
    ) -> Dict[str, torch.Tensor]:
        """
        Estimate price flow.
        
        Args:
            price_sequence: [batch, features, length] price data
            num_iterations: Number of flow refinement iterations
        
        Returns:
            Dictionary with flow estimates and predictions
        """
        features = self.feature_encoder(price_sequence)
        context, hidden = self.context_encoder(price_sequence)
        
        features = self.flow_attention(features)
        
        multi_scale_flows = self.multi_scale(price_sequence)
        
        flow = torch.zeros(
            price_sequence.shape[0], 2, price_sequence.shape[2],
            device=price_sequence.device
        )
        
        flow_predictions = []
        for _ in range(num_iterations):
            hidden, flow_pred = self.gru_update(hidden, context, flow)
            flow = flow + flow_pred['flow']
            flow_predictions.append(flow_pred)
        
        flow_type_logits = self.flow_classifier(features, flow)
        
        feat_pooled = F.adaptive_avg_pool1d(features, 1).squeeze(-1)
        flow_pooled = F.adaptive_avg_pool1d(flow, 1).squeeze(-1)
        combined = torch.cat([feat_pooled, flow_pooled], dim=-1)
        
        trend_logits = self.trend_predictor(combined)
        momentum = self.momentum_predictor(combined)
        
        return {
            'flow': flow,
            'flow_magnitude': flow_predictions[-1]['magnitude'],
            'flow_confidence': flow_predictions[-1]['confidence'],
            'flow_type_logits': flow_type_logits,
            'flow_type_probs': F.softmax(flow_type_logits, dim=-1),
            'trend_logits': trend_logits,
            'trend_probs': F.softmax(trend_logits, dim=-1),
            'momentum': momentum,
            'multi_scale_flows': multi_scale_flows,
            'features': features
        }


class DeepFlow2:
    """
    DeepFlow 2.0 - Complete Optical Flow System for Trading
    
    Applies optical flow concepts to price movement analysis:
    - Flow vector estimation
    - Multi-scale flow analysis
    - Flow-based trend detection
    - Momentum flow tracking
    """
    
    def __init__(self, config: Optional[DeepFlowConfig] = None):
        self.config = config or DeepFlowConfig()
        self.device = self.config.device
        
        self.model = DeepFlowNet(self.config).to(self.device)
        
        self.flow_buffer = deque(maxlen=1000)
        self.flow_history: List[FlowVector] = []
        self.running = False
        
        self.flow_type_names = [f.value for f in FlowType]
        
        logger.info("🌊 DeepFlow 2.0 initialized")
        logger.info(f"   Device: {self.device}")
        logger.info(f"   Sequence length: {self.config.sequence_length}")
    
    async def start(self):
        """Start the DeepFlow system."""
        self.running = True
        logger.info("🌊 DeepFlow 2.0 started")
    
    async def stop(self):
        """Stop the DeepFlow system."""
        self.running = False
        logger.info("🌊 DeepFlow 2.0 stopped")
    
    def estimate_flow(
        self, 
        price_data: np.ndarray,
        num_iterations: int = 12
    ) -> Dict[str, Any]:
        """
        Estimate price flow from OHLCV data.
        
        Args:
            price_data: [length, 5] OHLCV data
            num_iterations: Flow refinement iterations
        
        Returns:
            Flow estimation results
        """
        if price_data.shape[1] != 5:
            raise ValueError("Expected OHLCV data with 5 features")
        
        data_tensor = torch.tensor(
            price_data.T, dtype=torch.float32
        ).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            result = self.model(data_tensor, num_iterations)
        
        flow = result['flow'][0].cpu().numpy()
        
        flow_vectors = []
        for i in range(flow.shape[1]):
            x, y = flow[0, i], flow[1, i]
            magnitude = np.sqrt(x**2 + y**2)
            direction = np.arctan2(y, x)
            
            flow_vectors.append({
                'x': float(x),
                'y': float(y),
                'magnitude': float(magnitude),
                'direction': float(direction),
                'confidence': float(result['flow_confidence'][0, 0, i].cpu())
            })
        
        flow_type_probs = result['flow_type_probs'][0].cpu().numpy()
        flow_type_idx = np.argmax(flow_type_probs)
        
        trend_probs = result['trend_probs'][0].cpu().numpy()
        trend_idx = np.argmax(trend_probs)
        trends = ['uptrend', 'downtrend', 'sideways']
        
        return {
            'flow_vectors': flow_vectors,
            'flow_type': self.flow_type_names[flow_type_idx],
            'flow_type_confidence': float(flow_type_probs[flow_type_idx]),
            'trend': trends[trend_idx],
            'trend_confidence': float(trend_probs[trend_idx]),
            'momentum': float(result['momentum'][0].cpu()),
            'avg_magnitude': float(result['flow_magnitude'][0].mean().cpu()),
            'avg_confidence': float(result['flow_confidence'][0].mean().cpu())
        }
    
    def analyze_flow_divergence(
        self, 
        price_data: np.ndarray
    ) -> Dict[str, Any]:
        """
        Analyze flow divergence/convergence patterns.
        
        Args:
            price_data: OHLCV data
        
        Returns:
            Divergence analysis results
        """
        result = self.estimate_flow(price_data)
        flow_vectors = result['flow_vectors']
        
        if len(flow_vectors) < 10:
            return {'divergence': 0, 'convergence': 0, 'pattern': 'insufficient_data'}
        
        first_half = flow_vectors[:len(flow_vectors)//2]
        second_half = flow_vectors[len(flow_vectors)//2:]
        
        first_avg_dir = np.mean([v['direction'] for v in first_half])
        second_avg_dir = np.mean([v['direction'] for v in second_half])
        
        first_avg_mag = np.mean([v['magnitude'] for v in first_half])
        second_avg_mag = np.mean([v['magnitude'] for v in second_half])
        
        direction_diff = abs(second_avg_dir - first_avg_dir)
        magnitude_ratio = second_avg_mag / (first_avg_mag + 1e-8)
        
        if direction_diff > np.pi / 4:
            if magnitude_ratio > 1.2:
                pattern = 'divergent_accelerating'
            else:
                pattern = 'divergent'
        elif direction_diff < np.pi / 8:
            if magnitude_ratio < 0.8:
                pattern = 'convergent_decelerating'
            else:
                pattern = 'convergent'
        else:
            pattern = 'neutral'
        
        return {
            'divergence': float(direction_diff),
            'magnitude_change': float(magnitude_ratio - 1),
            'pattern': pattern,
            'first_half_direction': float(first_avg_dir),
            'second_half_direction': float(second_avg_dir)
        }
    
    def detect_flow_anomalies(
        self, 
        price_data: np.ndarray,
        threshold: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalous flow patterns.
        
        Args:
            price_data: OHLCV data
            threshold: Standard deviation threshold for anomaly
        
        Returns:
            List of detected anomalies
        """
        result = self.estimate_flow(price_data)
        flow_vectors = result['flow_vectors']
        
        magnitudes = [v['magnitude'] for v in flow_vectors]
        mean_mag = np.mean(magnitudes)
        std_mag = np.std(magnitudes)
        
        anomalies = []
        for i, vector in enumerate(flow_vectors):
            z_score = (vector['magnitude'] - mean_mag) / (std_mag + 1e-8)
            
            if abs(z_score) > threshold:
                anomalies.append({
                    'index': i,
                    'z_score': float(z_score),
                    'magnitude': vector['magnitude'],
                    'direction': vector['direction'],
                    'type': 'spike' if z_score > 0 else 'collapse'
                })
        
        return anomalies
    
    def get_flow_signals(
        self, 
        price_data: np.ndarray
    ) -> Dict[str, Any]:
        """
        Generate trading signals from flow analysis.
        
        Args:
            price_data: OHLCV data
        
        Returns:
            Trading signals based on flow
        """
        flow_result = self.estimate_flow(price_data)
        divergence_result = self.analyze_flow_divergence(price_data)
        
        momentum = flow_result['momentum']
        flow_type = flow_result['flow_type']
        trend = flow_result['trend']
        
        if momentum > 0.3 and trend == 'uptrend':
            signal = 'strong_buy'
            strength = min(1.0, momentum + 0.2)
        elif momentum > 0.1 and trend == 'uptrend':
            signal = 'buy'
            strength = momentum + 0.1
        elif momentum < -0.3 and trend == 'downtrend':
            signal = 'strong_sell'
            strength = min(1.0, abs(momentum) + 0.2)
        elif momentum < -0.1 and trend == 'downtrend':
            signal = 'sell'
            strength = abs(momentum) + 0.1
        else:
            signal = 'hold'
            strength = 0.5
        
        if 'divergent' in divergence_result['pattern']:
            if signal in ['buy', 'strong_buy']:
                signal = 'hold'
                strength *= 0.5
        
        return {
            'signal': signal,
            'strength': float(strength),
            'momentum': float(momentum),
            'flow_type': flow_type,
            'trend': trend,
            'divergence_pattern': divergence_result['pattern'],
            'confidence': flow_result['avg_confidence']
        }
    
    def stream_price(self, ohlcv: np.ndarray, timestamp: float):
        """
        Stream price data for continuous flow analysis.
        
        Args:
            ohlcv: Single OHLCV bar
            timestamp: Bar timestamp
        """
        self.flow_buffer.append({
            'data': ohlcv,
            'timestamp': timestamp
        })
    
    def get_realtime_flow(self) -> Optional[Dict[str, Any]]:
        """Get flow analysis from buffered data."""
        if len(self.flow_buffer) < 20:
            return None
        
        data = np.array([item['data'] for item in self.flow_buffer])
        return self.estimate_flow(data)
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        return {
            'running': self.running,
            'buffer_size': len(self.flow_buffer),
            'flow_history_size': len(self.flow_history),
            'device': self.device
        }
    
    def save(self, filepath: str):
        """Save model weights."""
        torch.save({
            'model': self.model.state_dict(),
            'config': self.config
        }, filepath)
        logger.info(f"🌊 DeepFlow 2.0 saved to {filepath}")
    
    def load(self, filepath: str):
        """Load model weights."""
        state = torch.load(filepath, map_location=self.device)
        self.model.load_state_dict(state['model'])
        logger.info(f"🌊 DeepFlow 2.0 loaded from {filepath}")


__all__ = [
    'DeepFlow2',
    'DeepFlowConfig',
    'DeepFlowNet',
    'FlowVector',
    'FlowType',
    'FlowEncoder',
    'CorrelationVolume',
    'MultiScaleFlowEstimator',
    'FlowAttention'
]
