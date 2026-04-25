"""
OPENCLAW - Open-Source Claw Feature Extraction System
======================================================

Advanced feature extraction system that "claws" out relevant features
from multiple data sources. Uses attention-based feature selection
and adaptive feature importance weighting.

Features:
- Multi-source feature extraction
- Adaptive feature importance
- Cross-domain feature fusion
- Real-time feature streaming
- Feature quality scoring
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import deque
import asyncio

logger = logging.getLogger(__name__)


class FeatureSource(Enum):
    """Sources of features for OPENCLAW."""
    PRICE = "price"
    VOLUME = "volume"
    ORDER_BOOK = "order_book"
    TECHNICAL = "technical"
    SENTIMENT = "sentiment"
    FUNDAMENTAL = "fundamental"
    ALTERNATIVE = "alternative"
    MACRO = "macro"


@dataclass
class ExtractedFeature:
    """A feature extracted by OPENCLAW."""
    name: str
    value: float
    importance: float
    source: FeatureSource
    timestamp: float
    quality_score: float
    metadata: Dict = field(default_factory=dict)


@dataclass
class OpenClawConfig:
    """Configuration for OPENCLAW system."""
    hidden_dim: int = 256
    num_claw_heads: int = 8
    num_extraction_layers: int = 4
    feature_dim: int = 64
    max_features: int = 512
    importance_threshold: float = 0.1
    dropout: float = 0.1
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


class FeatureEncoder(nn.Module):
    """Encodes raw features into embeddings."""
    
    def __init__(self, input_dims: Dict[str, int], hidden_dim: int = 256):
        super().__init__()
        self.encoders = nn.ModuleDict()
        
        for source, dim in input_dims.items():
            self.encoders[source] = nn.Sequential(
                nn.Linear(dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.GELU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.LayerNorm(hidden_dim)
            )
        
        self.source_embeddings = nn.Embedding(
            len(FeatureSource), hidden_dim
        )
    
    def forward(
        self, 
        features: Dict[str, torch.Tensor]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Encode features from multiple sources.
        
        Args:
            features: Dictionary mapping source names to feature tensors
        
        Returns:
            Tuple of (encoded_features, source_ids)
        """
        encoded_list = []
        source_ids = []
        
        for i, (source, tensor) in enumerate(features.items()):
            if source in self.encoders:
                encoded = self.encoders[source](tensor)
                encoded_list.append(encoded)
                source_ids.extend([i] * tensor.shape[1])
        
        if not encoded_list:
            raise ValueError("No valid features provided")
        
        combined = torch.cat(encoded_list, dim=1)
        source_tensor = torch.tensor(source_ids, device=combined.device)
        
        return combined, source_tensor


class ClawAttention(nn.Module):
    """
    Attention mechanism that "claws" out important features.
    Uses learned queries to extract relevant information.
    """
    
    def __init__(
        self, 
        hidden_dim: int = 256, 
        num_heads: int = 8,
        num_queries: int = 64,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.learned_queries = nn.Parameter(
            torch.randn(1, num_queries, hidden_dim) * 0.02
        )
        
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
        
        self.importance_scorer = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
    
    def forward(
        self, 
        features: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Extract important features using learned queries.
        
        Args:
            features: [batch, seq_len, hidden_dim] input features
        
        Returns:
            Tuple of (extracted_features, importance_scores, attention_weights)
        """
        batch_size = features.shape[0]
        queries = self.learned_queries.expand(batch_size, -1, -1)
        
        attn_out, attn_weights = self.attention(
            queries, features, features
        )
        
        x = self.norm1(queries + attn_out)
        x = self.norm2(x + self.ffn(x))
        
        importance = self.importance_scorer(x).squeeze(-1)
        
        return x, importance, attn_weights


class FeatureQualityAssessor(nn.Module):
    """Assesses the quality of extracted features."""
    
    def __init__(self, hidden_dim: int = 256):
        super().__init__()
        
        self.quality_network = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
        
        self.stability_network = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )
    
    def forward(
        self, 
        features: torch.Tensor,
        historical_features: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Assess feature quality.
        
        Args:
            features: Current extracted features
            historical_features: Optional historical features for stability
        """
        quality = self.quality_network(features).squeeze(-1)
        
        if historical_features is not None:
            combined = torch.cat([features, historical_features], dim=-1)
            stability = self.stability_network(combined).squeeze(-1)
        else:
            stability = torch.ones_like(quality)
        
        return {
            'quality': quality,
            'stability': stability,
            'overall': quality * stability
        }


class CrossDomainFusion(nn.Module):
    """Fuses features across different domains."""
    
    def __init__(self, hidden_dim: int = 256, num_domains: int = 8):
        super().__init__()
        
        self.domain_attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=8,
            dropout=0.1,
            batch_first=True
        )
        
        self.domain_gate = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.Sigmoid()
        )
        
        self.fusion_layer = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
    
    def forward(
        self, 
        domain_features: Dict[str, torch.Tensor]
    ) -> torch.Tensor:
        """
        Fuse features from multiple domains.
        
        Args:
            domain_features: Dictionary of domain -> features
        
        Returns:
            Fused feature representation
        """
        feature_list = list(domain_features.values())
        stacked = torch.stack(feature_list, dim=1)
        
        attn_out, _ = self.domain_attention(stacked, stacked, stacked)
        
        pooled = attn_out.mean(dim=1)
        
        return self.fusion_layer(pooled)


class AdaptiveFeatureSelector(nn.Module):
    """Adaptively selects the most relevant features."""
    
    def __init__(self, hidden_dim: int = 256, max_features: int = 512):
        super().__init__()
        
        self.relevance_scorer = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 1)
        )
        
        self.context_encoder = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            bidirectional=True
        )
        
        self.selection_gate = nn.Sequential(
            nn.Linear(hidden_dim * 3, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )
    
    def forward(
        self, 
        features: torch.Tensor,
        context: Optional[torch.Tensor] = None,
        top_k: int = 64
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Select top-k most relevant features.
        
        Args:
            features: [batch, num_features, hidden_dim] input features
            context: Optional context for relevance scoring
            top_k: Number of features to select
        
        Returns:
            Tuple of (selected_features, selection_indices, selection_scores)
        """
        relevance = self.relevance_scorer(features).squeeze(-1)
        
        context_out, _ = self.context_encoder(features)
        context_pooled = context_out.mean(dim=1, keepdim=True)
        context_expanded = context_pooled.expand(-1, features.shape[1], -1)
        
        combined = torch.cat([features, context_expanded], dim=-1)
        selection_scores = self.selection_gate(combined).squeeze(-1)
        
        final_scores = relevance * selection_scores
        
        top_k = min(top_k, features.shape[1])
        _, indices = torch.topk(final_scores, top_k, dim=1)
        
        batch_indices = torch.arange(
            features.shape[0], device=features.device
        ).unsqueeze(1).expand(-1, top_k)
        
        selected = features[batch_indices, indices]
        selected_scores = final_scores[batch_indices, indices]
        
        return selected, indices, selected_scores


class ClawNet(nn.Module):
    """
    Main neural network for OPENCLAW feature extraction.
    """
    
    def __init__(self, config: OpenClawConfig):
        super().__init__()
        self.config = config
        
        default_dims = {
            'price': 32,
            'volume': 16,
            'order_book': 40,
            'technical': 64,
            'sentiment': 32,
            'fundamental': 48,
            'alternative': 24,
            'macro': 16
        }
        
        self.feature_encoder = FeatureEncoder(
            default_dims, config.hidden_dim
        )
        
        self.claw_layers = nn.ModuleList([
            ClawAttention(
                hidden_dim=config.hidden_dim,
                num_heads=config.num_claw_heads,
                num_queries=config.feature_dim,
                dropout=config.dropout
            )
            for _ in range(config.num_extraction_layers)
        ])
        
        self.quality_assessor = FeatureQualityAssessor(config.hidden_dim)
        self.cross_domain_fusion = CrossDomainFusion(config.hidden_dim)
        self.adaptive_selector = AdaptiveFeatureSelector(
            config.hidden_dim, config.max_features
        )
        
        self.output_projection = nn.Linear(
            config.hidden_dim, config.feature_dim
        )
    
    def forward(
        self, 
        features: Dict[str, torch.Tensor],
        return_details: bool = False
    ) -> Dict[str, torch.Tensor]:
        """
        Extract and process features.
        
        Args:
            features: Dictionary of source -> feature tensors
            return_details: Whether to return detailed extraction info
        
        Returns:
            Dictionary with extracted features and metadata
        """
        encoded, source_ids = self.feature_encoder(features)
        
        all_importance = []
        all_attention = []
        x = encoded
        
        for claw_layer in self.claw_layers:
            x, importance, attention = claw_layer(x)
            all_importance.append(importance)
            all_attention.append(attention)
        
        quality = self.quality_assessor(x)
        
        selected, indices, scores = self.adaptive_selector(x)
        
        output = self.output_projection(selected)
        
        result = {
            'features': output,
            'importance_scores': scores,
            'quality_scores': quality['overall'],
            'selection_indices': indices
        }
        
        if return_details:
            result['all_importance'] = all_importance
            result['all_attention'] = all_attention
            result['raw_features'] = x
        
        return result


class OPENCLAW:
    """
    OPENCLAW - Complete Feature Extraction System
    
    Claws out relevant features from multiple data sources with:
    - Adaptive importance weighting
    - Cross-domain fusion
    - Quality assessment
    - Real-time streaming support
    """
    
    def __init__(self, config: Optional[OpenClawConfig] = None):
        self.config = config or OpenClawConfig()
        self.device = self.config.device
        
        self.claw_net = ClawNet(self.config).to(self.device)
        
        self.feature_buffer: Dict[str, deque] = {
            source.value: deque(maxlen=1000)
            for source in FeatureSource
        }
        self.extracted_history: List[ExtractedFeature] = []
        self.running = False
        
        logger.info("🦀 OPENCLAW initialized")
        logger.info(f"   Device: {self.device}")
        logger.info(f"   Max features: {self.config.max_features}")
    
    async def start(self):
        """Start the OPENCLAW system."""
        self.running = True
        logger.info("🦀 OPENCLAW started")
    
    async def stop(self):
        """Stop the OPENCLAW system."""
        self.running = False
        logger.info("🦀 OPENCLAW stopped")
    
    def extract_features(
        self, 
        data: Dict[str, np.ndarray],
        return_details: bool = False
    ) -> Dict[str, Any]:
        """
        Extract features from multiple data sources.
        
        Args:
            data: Dictionary mapping source names to numpy arrays
            return_details: Whether to return detailed extraction info
        
        Returns:
            Extracted features and metadata
        """
        tensors = {}
        for source, array in data.items():
            if array is not None and len(array) > 0:
                tensor = torch.tensor(
                    array, dtype=torch.float32
                ).unsqueeze(0).to(self.device)
                tensors[source] = tensor
        
        if not tensors:
            return {'features': None, 'error': 'No valid data provided'}
        
        with torch.no_grad():
            result = self.claw_net(tensors, return_details)
        
        output = {
            'features': result['features'][0].cpu().numpy(),
            'importance_scores': result['importance_scores'][0].cpu().numpy(),
            'quality_scores': result['quality_scores'][0].cpu().numpy(),
            'num_features': result['features'].shape[1]
        }
        
        if return_details:
            output['selection_indices'] = result['selection_indices'][0].cpu().numpy()
        
        return output
    
    def stream_feature(
        self, 
        source: str, 
        feature_data: np.ndarray,
        timestamp: float
    ):
        """
        Stream a feature update.
        
        Args:
            source: Feature source name
            feature_data: Feature values
            timestamp: Timestamp of the feature
        """
        if source in self.feature_buffer:
            self.feature_buffer[source].append({
                'data': feature_data,
                'timestamp': timestamp
            })
    
    def get_buffered_features(self) -> Dict[str, np.ndarray]:
        """Get all buffered features as arrays."""
        result = {}
        for source, buffer in self.feature_buffer.items():
            if buffer:
                data_list = [item['data'] for item in buffer]
                result[source] = np.array(data_list)
        return result
    
    def get_feature_importance(
        self, 
        features: np.ndarray
    ) -> np.ndarray:
        """
        Get importance scores for features.
        
        Args:
            features: Feature array
        
        Returns:
            Importance scores
        """
        tensor = torch.tensor(
            features, dtype=torch.float32
        ).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            importance = self.claw_net.adaptive_selector.relevance_scorer(
                tensor
            ).squeeze(-1)
        
        return importance[0].cpu().numpy()
    
    def select_top_features(
        self, 
        features: np.ndarray,
        top_k: int = 32
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Select top-k most important features.
        
        Args:
            features: Feature array [num_features, feature_dim]
            top_k: Number of features to select
        
        Returns:
            Tuple of (selected_features, indices)
        """
        tensor = torch.tensor(
            features, dtype=torch.float32
        ).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            selected, indices, _ = self.claw_net.adaptive_selector(
                tensor, top_k=top_k
            )
        
        return (
            selected[0].cpu().numpy(),
            indices[0].cpu().numpy()
        )
    
    def fuse_domain_features(
        self, 
        domain_features: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """
        Fuse features from multiple domains.
        
        Args:
            domain_features: Dictionary of domain -> features
        
        Returns:
            Fused feature representation
        """
        tensors = {
            k: torch.tensor(v, dtype=torch.float32).to(self.device)
            for k, v in domain_features.items()
        }
        
        with torch.no_grad():
            fused = self.claw_net.cross_domain_fusion(tensors)
        
        return fused.cpu().numpy()
    
    def assess_feature_quality(
        self, 
        features: np.ndarray
    ) -> Dict[str, float]:
        """
        Assess the quality of features.
        
        Args:
            features: Feature array
        
        Returns:
            Quality metrics
        """
        tensor = torch.tensor(
            features, dtype=torch.float32
        ).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            quality = self.claw_net.quality_assessor(tensor)
        
        return {
            'quality': quality['quality'].mean().item(),
            'stability': quality['stability'].mean().item(),
            'overall': quality['overall'].mean().item()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        buffer_sizes = {
            source: len(buffer) 
            for source, buffer in self.feature_buffer.items()
        }
        
        return {
            'running': self.running,
            'buffer_sizes': buffer_sizes,
            'total_extracted': len(self.extracted_history),
            'device': self.device
        }
    
    def save(self, filepath: str):
        """Save model weights."""
        torch.save({
            'claw_net': self.claw_net.state_dict(),
            'config': self.config
        }, filepath)
        logger.info(f"🦀 OPENCLAW saved to {filepath}")
    
    def load(self, filepath: str):
        """Load model weights."""
        state = torch.load(filepath, map_location=self.device)
        self.claw_net.load_state_dict(state['claw_net'])
        logger.info(f"🦀 OPENCLAW loaded from {filepath}")


__all__ = [
    'OPENCLAW',
    'OpenClawConfig',
    'ExtractedFeature',
    'FeatureSource',
    'ClawNet',
    'ClawAttention',
    'FeatureQualityAssessor',
    'CrossDomainFusion',
    'AdaptiveFeatureSelector'
]
