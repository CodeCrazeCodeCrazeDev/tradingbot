"""
MICROFISH - Micro-Pattern Fish Detection for Market Microstructure
====================================================================

Advanced micro-pattern recognition system that "fishes" for hidden patterns
in market microstructure data. Detects subtle anomalies, order flow imbalances,
and micro-level trading signals that precede larger market moves.

Features:
- Micro-pattern detection in tick data
- Order flow imbalance analysis
- Hidden liquidity detection
- Micro-momentum signals
- Anomaly fishing in high-frequency data
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import deque
import asyncio

logger = logging.getLogger(__name__)


class MicroPatternType(Enum):
    """Types of micro-patterns detected by MICROFISH."""
    ICEBERG_ORDER = "iceberg_order"
    SPOOFING = "spoofing"
    LAYERING = "layering"
    MOMENTUM_IGNITION = "momentum_ignition"
    QUOTE_STUFFING = "quote_stuffing"
    HIDDEN_LIQUIDITY = "hidden_liquidity"
    MICRO_REVERSAL = "micro_reversal"
    TICK_CLUSTER = "tick_cluster"
    VOLUME_ANOMALY = "volume_anomaly"
    SPREAD_COMPRESSION = "spread_compression"


@dataclass
class MicroPattern:
    """Detected micro-pattern."""
    pattern_type: MicroPatternType
    confidence: float
    timestamp: float
    price_level: float
    volume: float
    direction: int  # 1 for bullish, -1 for bearish, 0 for neutral
    metadata: Dict = field(default_factory=dict)


@dataclass
class MicroFishConfig:
    """Configuration for MICROFISH system."""
    tick_window: int = 1000
    pattern_threshold: float = 0.7
    anomaly_sensitivity: float = 0.8
    hidden_dim: int = 128
    num_attention_heads: int = 8
    num_fish_layers: int = 4
    dropout: float = 0.1
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


class TickEncoder(nn.Module):
    """Encodes individual tick data into embeddings."""
    
    def __init__(self, input_dim: int = 6, hidden_dim: int = 128):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU()
        )
        self.positional_encoding = nn.Parameter(
            torch.randn(1, 10000, hidden_dim) * 0.02
        )
    
    def forward(self, ticks: torch.Tensor) -> torch.Tensor:
        """
        Encode tick data.
        
        Args:
            ticks: [batch, seq_len, features] tick data
                   features: [price, volume, bid, ask, trade_direction, timestamp_delta]
        """
        batch_size, seq_len, _ = ticks.shape
        encoded = self.encoder(ticks)
        encoded = encoded + self.positional_encoding[:, :seq_len, :]
        return encoded


class MicroPatternAttention(nn.Module):
    """Multi-head attention for detecting micro-patterns."""
    
    def __init__(self, hidden_dim: int = 128, num_heads: int = 8, dropout: float = 0.1):
        super().__init__()
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True
        )
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.norm2 = nn.LayerNorm(hidden_dim)
        self.ffn = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 4, hidden_dim),
            nn.Dropout(dropout)
        )
    
    def forward(
        self, 
        x: torch.Tensor, 
        mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass with attention weights."""
        attn_out, attn_weights = self.attention(x, x, x, attn_mask=mask)
        x = self.norm1(x + attn_out)
        x = self.norm2(x + self.ffn(x))
        return x, attn_weights


class FishNet(nn.Module):
    """
    Neural network that "fishes" for micro-patterns in market data.
    Uses attention mechanisms to identify subtle patterns.
    """
    
    def __init__(self, config: MicroFishConfig):
        super().__init__()
        self.config = config
        
        self.tick_encoder = TickEncoder(
            input_dim=6, 
            hidden_dim=config.hidden_dim
        )
        
        self.fish_layers = nn.ModuleList([
            MicroPatternAttention(
                hidden_dim=config.hidden_dim,
                num_heads=config.num_attention_heads,
                dropout=config.dropout
            )
            for _ in range(config.num_fish_layers)
        ])
        
        self.pattern_classifier = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim, len(MicroPatternType))
        )
        
        self.confidence_head = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim // 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim // 2, 1),
            nn.Sigmoid()
        )
        
        self.direction_head = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim // 2),
            nn.GELU(),
            nn.Linear(config.hidden_dim // 2, 3)  # bullish, bearish, neutral
        )
        
        self.anomaly_detector = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.GELU(),
            nn.Linear(config.hidden_dim, 1),
            nn.Sigmoid()
        )
    
    def forward(
        self, 
        ticks: torch.Tensor,
        return_attention: bool = False
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass to detect micro-patterns.
        
        Args:
            ticks: [batch, seq_len, 6] tick data
            return_attention: whether to return attention weights
        
        Returns:
            Dictionary with pattern predictions, confidence, direction, anomaly scores
        """
        encoded = self.tick_encoder(ticks)
        
        attention_weights = []
        x = encoded
        for layer in self.fish_layers:
            x, attn = layer(x)
            attention_weights.append(attn)
        
        pooled = x.mean(dim=1)
        
        pattern_logits = self.pattern_classifier(pooled)
        confidence = self.confidence_head(pooled)
        direction_logits = self.direction_head(pooled)
        anomaly_score = self.anomaly_detector(pooled)
        
        result = {
            'pattern_logits': pattern_logits,
            'pattern_probs': F.softmax(pattern_logits, dim=-1),
            'confidence': confidence,
            'direction_logits': direction_logits,
            'direction_probs': F.softmax(direction_logits, dim=-1),
            'anomaly_score': anomaly_score,
            'features': pooled
        }
        
        if return_attention:
            result['attention_weights'] = attention_weights
        
        return result


class OrderFlowAnalyzer(nn.Module):
    """Analyzes order flow for imbalances and hidden patterns."""
    
    def __init__(self, hidden_dim: int = 128):
        super().__init__()
        
        self.flow_encoder = nn.Sequential(
            nn.Linear(10, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        self.imbalance_detector = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Tanh()  # -1 to 1 for sell/buy imbalance
        )
        
        self.toxicity_detector = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
        
        self.hidden_liquidity_detector = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
    
    def forward(self, order_flow: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Analyze order flow data.
        
        Args:
            order_flow: [batch, seq_len, 10] order flow features
                       [bid_vol, ask_vol, bid_depth, ask_depth, trade_vol,
                        trade_direction, spread, mid_price_change, vwap_diff, time_delta]
        """
        encoded = self.flow_encoder(order_flow)
        pooled = encoded.mean(dim=1)
        
        return {
            'imbalance': self.imbalance_detector(pooled),
            'toxicity': self.toxicity_detector(pooled),
            'hidden_liquidity': self.hidden_liquidity_detector(pooled),
            'features': pooled
        }


class IcebergDetector(nn.Module):
    """Detects iceberg orders (large hidden orders)."""
    
    def __init__(self, hidden_dim: int = 128):
        super().__init__()
        
        self.sequence_encoder = nn.LSTM(
            input_size=8,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=0.1,
            bidirectional=True
        )
        
        self.detector = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )
        
        self.size_estimator = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 1),
            nn.ReLU()
        )
    
    def forward(self, trade_sequence: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Detect iceberg orders in trade sequence.
        
        Args:
            trade_sequence: [batch, seq_len, 8] trade features
        """
        output, (hidden, _) = self.sequence_encoder(trade_sequence)
        
        final_hidden = torch.cat([hidden[-2], hidden[-1]], dim=-1)
        
        return {
            'iceberg_probability': self.detector(final_hidden),
            'estimated_size': self.size_estimator(final_hidden),
            'sequence_features': output
        }


class SpoofingDetector(nn.Module):
    """Detects spoofing and layering patterns."""
    
    def __init__(self, hidden_dim: int = 128):
        super().__init__()
        
        self.book_encoder = nn.Sequential(
            nn.Linear(20, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        self.temporal_conv = nn.Conv1d(
            in_channels=hidden_dim,
            out_channels=hidden_dim,
            kernel_size=5,
            padding=2
        )
        
        self.spoof_detector = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
        
        self.layer_detector = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
    
    def forward(self, order_book_sequence: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Detect spoofing patterns in order book sequence.
        
        Args:
            order_book_sequence: [batch, seq_len, 20] order book snapshots
        """
        encoded = self.book_encoder(order_book_sequence)
        
        conv_input = encoded.transpose(1, 2)
        conv_out = self.temporal_conv(conv_input).transpose(1, 2)
        
        pooled = conv_out.mean(dim=1)
        
        return {
            'spoofing_probability': self.spoof_detector(pooled),
            'layering_probability': self.layer_detector(pooled),
            'features': pooled
        }


class MICROFISH:
    """
    MICROFISH - Complete Micro-Pattern Detection System
    
    Fishes for hidden patterns in market microstructure data including:
    - Iceberg orders
    - Spoofing/layering
    - Hidden liquidity
    - Micro-momentum signals
    - Order flow anomalies
    """
    
    def __init__(self, config: Optional[MicroFishConfig] = None):
        self.config = config or MicroFishConfig()
        self.device = self.config.device
        
        self.fish_net = FishNet(self.config).to(self.device)
        self.order_flow_analyzer = OrderFlowAnalyzer(
            self.config.hidden_dim
        ).to(self.device)
        self.iceberg_detector = IcebergDetector(
            self.config.hidden_dim
        ).to(self.device)
        self.spoofing_detector = SpoofingDetector(
            self.config.hidden_dim
        ).to(self.device)
        
        self.tick_buffer = deque(maxlen=self.config.tick_window)
        self.pattern_history: List[MicroPattern] = []
        self.running = False
        
        logger.info("🐟 MICROFISH initialized")
        logger.info(f"   Device: {self.device}")
        logger.info(f"   Tick window: {self.config.tick_window}")
    
    async def start(self):
        """Start the MICROFISH system."""
        self.running = True
        logger.info("🐟 MICROFISH started")
    
    async def stop(self):
        """Stop the MICROFISH system."""
        self.running = False
        logger.info("🐟 MICROFISH stopped")
    
    def process_tick(self, tick: Dict[str, float]) -> Optional[MicroPattern]:
        """
        Process a single tick and detect patterns.
        
        Args:
            tick: Dictionary with tick data
                 {price, volume, bid, ask, trade_direction, timestamp}
        
        Returns:
            Detected pattern if any
        """
        tick_array = np.array([
            tick.get('price', 0),
            tick.get('volume', 0),
            tick.get('bid', 0),
            tick.get('ask', 0),
            tick.get('trade_direction', 0),
            tick.get('timestamp_delta', 0)
        ])
        
        self.tick_buffer.append(tick_array)
        
        if len(self.tick_buffer) < 100:
            return None
        
        return self._detect_patterns()
    
    def _detect_patterns(self) -> Optional[MicroPattern]:
        """Run pattern detection on buffered ticks."""
        ticks = np.array(list(self.tick_buffer))
        ticks_tensor = torch.tensor(ticks, dtype=torch.float32).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            result = self.fish_net(ticks_tensor)
        
        pattern_probs = result['pattern_probs'][0].cpu().numpy()
        confidence = result['confidence'][0].item()
        direction_probs = result['direction_probs'][0].cpu().numpy()
        anomaly_score = result['anomaly_score'][0].item()
        
        if confidence < self.config.pattern_threshold:
            return None
        
        pattern_idx = np.argmax(pattern_probs)
        pattern_type = list(MicroPatternType)[pattern_idx]
        
        direction = np.argmax(direction_probs) - 1
        
        pattern = MicroPattern(
            pattern_type=pattern_type,
            confidence=confidence,
            timestamp=ticks[-1, 5],
            price_level=ticks[-1, 0],
            volume=ticks[-1, 1],
            direction=direction,
            metadata={
                'pattern_probs': pattern_probs.tolist(),
                'anomaly_score': anomaly_score
            }
        )
        
        self.pattern_history.append(pattern)
        return pattern
    
    def analyze_order_flow(self, order_flow_data: np.ndarray) -> Dict[str, Any]:
        """
        Analyze order flow for imbalances and toxicity.
        
        Args:
            order_flow_data: [seq_len, 10] order flow features
        
        Returns:
            Analysis results
        """
        flow_tensor = torch.tensor(
            order_flow_data, dtype=torch.float32
        ).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            result = self.order_flow_analyzer(flow_tensor)
        
        return {
            'imbalance': result['imbalance'][0].item(),
            'toxicity': result['toxicity'][0].item(),
            'hidden_liquidity_prob': result['hidden_liquidity'][0].item()
        }
    
    def detect_iceberg(self, trade_sequence: np.ndarray) -> Dict[str, Any]:
        """
        Detect iceberg orders in trade sequence.
        
        Args:
            trade_sequence: [seq_len, 8] trade features
        
        Returns:
            Iceberg detection results
        """
        trade_tensor = torch.tensor(
            trade_sequence, dtype=torch.float32
        ).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            result = self.iceberg_detector(trade_tensor)
        
        return {
            'iceberg_probability': result['iceberg_probability'][0].item(),
            'estimated_hidden_size': result['estimated_size'][0].item()
        }
    
    def detect_spoofing(self, order_book_sequence: np.ndarray) -> Dict[str, Any]:
        """
        Detect spoofing and layering patterns.
        
        Args:
            order_book_sequence: [seq_len, 20] order book snapshots
        
        Returns:
            Spoofing detection results
        """
        book_tensor = torch.tensor(
            order_book_sequence, dtype=torch.float32
        ).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            result = self.spoofing_detector(book_tensor)
        
        return {
            'spoofing_probability': result['spoofing_probability'][0].item(),
            'layering_probability': result['layering_probability'][0].item()
        }
    
    def get_micro_signals(self) -> Dict[str, Any]:
        """
        Get aggregated micro-signals from recent patterns.
        
        Returns:
            Aggregated signals for trading decisions
        """
        if not self.pattern_history:
            return {
                'signal': 0,
                'confidence': 0,
                'patterns_detected': 0
            }
        
        recent_patterns = self.pattern_history[-50:]
        
        bullish_count = sum(1 for p in recent_patterns if p.direction == 1)
        bearish_count = sum(1 for p in recent_patterns if p.direction == -1)
        
        avg_confidence = np.mean([p.confidence for p in recent_patterns])
        
        if bullish_count > bearish_count * 1.5:
            signal = 1
        elif bearish_count > bullish_count * 1.5:
            signal = -1
        else:
            signal = 0
        
        pattern_counts = {}
        for p in recent_patterns:
            pattern_counts[p.pattern_type.value] = pattern_counts.get(
                p.pattern_type.value, 0
            ) + 1
        
        return {
            'signal': signal,
            'confidence': avg_confidence,
            'patterns_detected': len(recent_patterns),
            'bullish_patterns': bullish_count,
            'bearish_patterns': bearish_count,
            'pattern_distribution': pattern_counts
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        return {
            'running': self.running,
            'tick_buffer_size': len(self.tick_buffer),
            'patterns_detected': len(self.pattern_history),
            'device': self.device
        }
    
    def save(self, filepath: str):
        """Save model weights."""
        torch.save({
            'fish_net': self.fish_net.state_dict(),
            'order_flow_analyzer': self.order_flow_analyzer.state_dict(),
            'iceberg_detector': self.iceberg_detector.state_dict(),
            'spoofing_detector': self.spoofing_detector.state_dict(),
            'config': self.config
        }, filepath)
        logger.info(f"🐟 MICROFISH saved to {filepath}")
    
    def load(self, filepath: str):
        """Load model weights."""
        state = torch.load(filepath, map_location=self.device)
        self.fish_net.load_state_dict(state['fish_net'])
        self.order_flow_analyzer.load_state_dict(state['order_flow_analyzer'])
        self.iceberg_detector.load_state_dict(state['iceberg_detector'])
        self.spoofing_detector.load_state_dict(state['spoofing_detector'])
        logger.info(f"🐟 MICROFISH loaded from {filepath}")


__all__ = [
    'MICROFISH',
    'MicroFishConfig',
    'MicroPattern',
    'MicroPatternType',
    'FishNet',
    'OrderFlowAnalyzer',
    'IcebergDetector',
    'SpoofingDetector'
]
