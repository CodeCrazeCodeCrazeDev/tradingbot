"""
OPENCLIP Trading - Vision-Language Model for Market Analysis
=============================================================

Adapts CLIP-style vision-language models for trading applications.
Enables chart pattern recognition, visual market analysis, and
text-to-chart similarity matching.

Features:
- Chart image encoding
- Text description encoding
- Chart-text similarity matching
- Visual pattern recognition
- Multi-modal market analysis
- Chart captioning and description
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

logger = logging.getLogger(__name__)


class ChartPatternType(Enum):
    """Types of chart patterns recognizable by OPENCLIP."""
    HEAD_AND_SHOULDERS = "head_and_shoulders"
    INVERSE_HEAD_AND_SHOULDERS = "inverse_head_and_shoulders"
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    TRIPLE_TOP = "triple_top"
    TRIPLE_BOTTOM = "triple_bottom"
    ASCENDING_TRIANGLE = "ascending_triangle"
    DESCENDING_TRIANGLE = "descending_triangle"
    SYMMETRICAL_TRIANGLE = "symmetrical_triangle"
    BULL_FLAG = "bull_flag"
    BEAR_FLAG = "bear_flag"
    CUP_AND_HANDLE = "cup_and_handle"
    WEDGE_UP = "wedge_up"
    WEDGE_DOWN = "wedge_down"
    CHANNEL_UP = "channel_up"
    CHANNEL_DOWN = "channel_down"
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"
    CONSOLIDATION = "consolidation"
    TREND_REVERSAL = "trend_reversal"


@dataclass
class OpenCLIPConfig:
    """Configuration for OPENCLIP Trading system."""
    image_size: int = 224
    patch_size: int = 16
    vision_dim: int = 768
    text_dim: int = 512
    projection_dim: int = 512
    num_vision_layers: int = 12
    num_text_layers: int = 6
    num_heads: int = 12
    vocab_size: int = 49408
    max_text_length: int = 77
    dropout: float = 0.1
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


class PatchEmbedding(nn.Module):
    """Converts chart images to patch embeddings."""
    
    def __init__(
        self, 
        image_size: int = 224, 
        patch_size: int = 16,
        in_channels: int = 3,
        embed_dim: int = 768
    ):
        super().__init__()
        self.image_size = image_size
        self.patch_size = patch_size
        self.num_patches = (image_size // patch_size) ** 2
        
        self.projection = nn.Conv2d(
            in_channels, embed_dim,
            kernel_size=patch_size,
            stride=patch_size
        )
        
        self.cls_token = nn.Parameter(torch.randn(1, 1, embed_dim) * 0.02)
        self.position_embedding = nn.Parameter(
            torch.randn(1, self.num_patches + 1, embed_dim) * 0.02
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Convert image to patch embeddings.
        
        Args:
            x: [batch, channels, height, width] image tensor
        
        Returns:
            [batch, num_patches + 1, embed_dim] patch embeddings
        """
        batch_size = x.shape[0]
        
        x = self.projection(x)
        x = x.flatten(2).transpose(1, 2)
        
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)
        
        x = x + self.position_embedding
        
        return x


class VisionTransformerBlock(nn.Module):
    """Transformer block for vision encoding."""
    
    def __init__(
        self, 
        dim: int = 768, 
        num_heads: int = 12,
        mlp_ratio: float = 4.0,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.norm1 = nn.LayerNorm(dim)
        self.attention = nn.MultiheadAttention(
            embed_dim=dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True
        )
        
        self.norm2 = nn.LayerNorm(dim)
        mlp_dim = int(dim * mlp_ratio)
        self.mlp = nn.Sequential(
            nn.Linear(dim, mlp_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(mlp_dim, dim),
            nn.Dropout(dropout)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        x = x + self.attention(
            self.norm1(x), self.norm1(x), self.norm1(x)
        )[0]
        x = x + self.mlp(self.norm2(x))
        return x


class ChartEncoder(nn.Module):
    """Encodes chart images into embeddings."""
    
    def __init__(self, config: OpenCLIPConfig):
        super().__init__()
        
        self.patch_embed = PatchEmbedding(
            image_size=config.image_size,
            patch_size=config.patch_size,
            embed_dim=config.vision_dim
        )
        
        self.blocks = nn.ModuleList([
            VisionTransformerBlock(
                dim=config.vision_dim,
                num_heads=config.num_heads,
                dropout=config.dropout
            )
            for _ in range(config.num_vision_layers)
        ])
        
        self.norm = nn.LayerNorm(config.vision_dim)
        self.projection = nn.Linear(config.vision_dim, config.projection_dim)
    
    def forward(self, images: torch.Tensor) -> torch.Tensor:
        """
        Encode chart images.
        
        Args:
            images: [batch, channels, height, width] chart images
        
        Returns:
            [batch, projection_dim] image embeddings
        """
        x = self.patch_embed(images)
        
        for block in self.blocks:
            x = block(x)
        
        x = self.norm(x)
        
        cls_embedding = x[:, 0]
        
        return self.projection(cls_embedding)


class TextTransformerBlock(nn.Module):
    """Transformer block for text encoding."""
    
    def __init__(
        self, 
        dim: int = 512, 
        num_heads: int = 8,
        mlp_ratio: float = 4.0,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.norm1 = nn.LayerNorm(dim)
        self.attention = nn.MultiheadAttention(
            embed_dim=dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True
        )
        
        self.norm2 = nn.LayerNorm(dim)
        mlp_dim = int(dim * mlp_ratio)
        self.mlp = nn.Sequential(
            nn.Linear(dim, mlp_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(mlp_dim, dim),
            nn.Dropout(dropout)
        )
    
    def forward(
        self, 
        x: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Forward pass with optional causal mask."""
        x = x + self.attention(
            self.norm1(x), self.norm1(x), self.norm1(x),
            attn_mask=attention_mask
        )[0]
        x = x + self.mlp(self.norm2(x))
        return x


class TextEncoder(nn.Module):
    """Encodes text descriptions into embeddings."""
    
    def __init__(self, config: OpenCLIPConfig):
        super().__init__()
        
        self.token_embedding = nn.Embedding(
            config.vocab_size, config.text_dim
        )
        self.position_embedding = nn.Parameter(
            torch.randn(1, config.max_text_length, config.text_dim) * 0.02
        )
        
        self.blocks = nn.ModuleList([
            TextTransformerBlock(
                dim=config.text_dim,
                num_heads=8,
                dropout=config.dropout
            )
            for _ in range(config.num_text_layers)
        ])
        
        self.norm = nn.LayerNorm(config.text_dim)
        self.projection = nn.Linear(config.text_dim, config.projection_dim)
        
        self.max_length = config.max_text_length
    
    def forward(
        self, 
        tokens: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Encode text tokens.
        
        Args:
            tokens: [batch, seq_len] token indices
            attention_mask: Optional attention mask
        
        Returns:
            [batch, projection_dim] text embeddings
        """
        seq_len = tokens.shape[1]
        
        x = self.token_embedding(tokens)
        x = x + self.position_embedding[:, :seq_len]
        
        causal_mask = torch.triu(
            torch.ones(seq_len, seq_len, device=tokens.device) * float('-inf'),
            diagonal=1
        )
        
        for block in self.blocks:
            x = block(x, causal_mask)
        
        x = self.norm(x)
        
        if attention_mask is not None:
            eos_indices = attention_mask.sum(dim=1) - 1
            batch_indices = torch.arange(x.shape[0], device=x.device)
            text_embedding = x[batch_indices, eos_indices]
        else:
            text_embedding = x[:, -1]
        
        return self.projection(text_embedding)


class ChartPatternClassifier(nn.Module):
    """Classifies chart patterns from embeddings."""
    
    def __init__(self, embed_dim: int = 512, num_patterns: int = 20):
        super().__init__()
        
        self.classifier = nn.Sequential(
            nn.Linear(embed_dim, embed_dim),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(embed_dim, embed_dim // 2),
            nn.GELU(),
            nn.Linear(embed_dim // 2, num_patterns)
        )
        
        self.confidence_head = nn.Sequential(
            nn.Linear(embed_dim, embed_dim // 2),
            nn.GELU(),
            nn.Linear(embed_dim // 2, 1),
            nn.Sigmoid()
        )
    
    def forward(self, embeddings: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Classify chart patterns."""
        logits = self.classifier(embeddings)
        confidence = self.confidence_head(embeddings)
        
        return {
            'logits': logits,
            'probabilities': F.softmax(logits, dim=-1),
            'confidence': confidence
        }


class TradingSignalGenerator(nn.Module):
    """Generates trading signals from chart-text embeddings."""
    
    def __init__(self, embed_dim: int = 512):
        super().__init__()
        
        self.signal_head = nn.Sequential(
            nn.Linear(embed_dim * 2, embed_dim),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(embed_dim, 3)  # BUY, SELL, HOLD
        )
        
        self.strength_head = nn.Sequential(
            nn.Linear(embed_dim * 2, embed_dim // 2),
            nn.GELU(),
            nn.Linear(embed_dim // 2, 1),
            nn.Sigmoid()
        )
        
        self.timeframe_head = nn.Sequential(
            nn.Linear(embed_dim * 2, embed_dim // 2),
            nn.GELU(),
            nn.Linear(embed_dim // 2, 4)  # scalp, intraday, swing, position
        )
    
    def forward(
        self, 
        chart_embedding: torch.Tensor,
        text_embedding: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """Generate trading signals from combined embeddings."""
        combined = torch.cat([chart_embedding, text_embedding], dim=-1)
        
        signal_logits = self.signal_head(combined)
        strength = self.strength_head(combined)
        timeframe_logits = self.timeframe_head(combined)
        
        return {
            'signal_logits': signal_logits,
            'signal_probs': F.softmax(signal_logits, dim=-1),
            'strength': strength,
            'timeframe_logits': timeframe_logits,
            'timeframe_probs': F.softmax(timeframe_logits, dim=-1)
        }


class OpenCLIPTrading(nn.Module):
    """
    Complete OPENCLIP model for trading applications.
    """
    
    def __init__(self, config: OpenCLIPConfig):
        super().__init__()
        self.config = config
        
        self.chart_encoder = ChartEncoder(config)
        self.text_encoder = TextEncoder(config)
        
        self.pattern_classifier = ChartPatternClassifier(
            config.projection_dim, len(ChartPatternType)
        )
        self.signal_generator = TradingSignalGenerator(config.projection_dim)
        
        self.logit_scale = nn.Parameter(torch.ones([]) * np.log(1 / 0.07))
    
    def encode_chart(self, images: torch.Tensor) -> torch.Tensor:
        """Encode chart images."""
        return F.normalize(self.chart_encoder(images), dim=-1)
    
    def encode_text(
        self, 
        tokens: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Encode text descriptions."""
        return F.normalize(
            self.text_encoder(tokens, attention_mask), dim=-1
        )
    
    def forward(
        self,
        images: Optional[torch.Tensor] = None,
        tokens: Optional[torch.Tensor] = None,
        attention_mask: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass for CLIP-style training.
        
        Args:
            images: Chart images
            tokens: Text tokens
            attention_mask: Text attention mask
        
        Returns:
            Dictionary with embeddings and similarity scores
        """
        result = {}
        
        if images is not None:
            chart_embeddings = self.encode_chart(images)
            result['chart_embeddings'] = chart_embeddings
            
            pattern_result = self.pattern_classifier(chart_embeddings)
            result['pattern_logits'] = pattern_result['logits']
            result['pattern_probs'] = pattern_result['probabilities']
            result['pattern_confidence'] = pattern_result['confidence']
        
        if tokens is not None:
            text_embeddings = self.encode_text(tokens, attention_mask)
            result['text_embeddings'] = text_embeddings
        
        if images is not None and tokens is not None:
            logit_scale = self.logit_scale.exp()
            logits_per_chart = logit_scale * chart_embeddings @ text_embeddings.t()
            logits_per_text = logits_per_chart.t()
            
            result['logits_per_chart'] = logits_per_chart
            result['logits_per_text'] = logits_per_text
            
            signal_result = self.signal_generator(
                chart_embeddings, text_embeddings
            )
            result.update(signal_result)
        
        return result


class SimpleTokenizer:
    """Simple tokenizer for text encoding."""
    
    def __init__(self, vocab_size: int = 49408, max_length: int = 77):
        self.vocab_size = vocab_size
        self.max_length = max_length
        
        self.special_tokens = {
            '<pad>': 0,
            '<sos>': 1,
            '<eos>': 2,
            '<unk>': 3
        }
        
        self.vocab = {}
        for i, char in enumerate(
            "abcdefghijklmnopqrstuvwxyz0123456789 .,!?-_()[]{}:;'\"/"
        ):
            self.vocab[char] = i + 4
    
    def encode(self, text: str) -> List[int]:
        """Encode text to token indices."""
        text = text.lower()
        tokens = [self.special_tokens['<sos>']]
        
        for char in text[:self.max_length - 2]:
            tokens.append(
                self.vocab.get(char, self.special_tokens['<unk>'])
            )
        
        tokens.append(self.special_tokens['<eos>'])
        
        while len(tokens) < self.max_length:
            tokens.append(self.special_tokens['<pad>'])
        
        return tokens[:self.max_length]
    
    def batch_encode(self, texts: List[str]) -> Tuple[torch.Tensor, torch.Tensor]:
        """Encode batch of texts."""
        encoded = [self.encode(text) for text in texts]
        tokens = torch.tensor(encoded)
        
        attention_mask = (tokens != self.special_tokens['<pad>']).long()
        
        return tokens, attention_mask


class OPENCLIP:
    """
    OPENCLIP - Vision-Language Model for Trading
    
    Provides chart pattern recognition, text-chart matching,
    and visual market analysis capabilities.
    """
    
    def __init__(self, config: Optional[OpenCLIPConfig] = None):
        self.config = config or OpenCLIPConfig()
        self.device = self.config.device
        
        self.model = OpenCLIPTrading(self.config).to(self.device)
        self.tokenizer = SimpleTokenizer(
            self.config.vocab_size, self.config.max_text_length
        )
        
        self.pattern_names = [p.value for p in ChartPatternType]
        self.running = False
        
        logger.info("📎 OPENCLIP Trading initialized")
        logger.info(f"   Device: {self.device}")
        logger.info(f"   Image size: {self.config.image_size}")
    
    async def start(self):
        """Start the OPENCLIP system."""
        self.running = True
        logger.info("📎 OPENCLIP started")
    
    async def stop(self):
        """Stop the OPENCLIP system."""
        self.running = False
        logger.info("📎 OPENCLIP stopped")
    
    def analyze_chart(
        self, 
        chart_image: np.ndarray,
        descriptions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a chart image.
        
        Args:
            chart_image: [height, width, channels] or [channels, height, width]
            descriptions: Optional text descriptions to match
        
        Returns:
            Analysis results including patterns and signals
        """
        if chart_image.shape[-1] == 3:
            chart_image = np.transpose(chart_image, (2, 0, 1))
        
        image_tensor = torch.tensor(
            chart_image, dtype=torch.float32
        ).unsqueeze(0).to(self.device)
        
        if image_tensor.max() > 1.0:
            image_tensor = image_tensor / 255.0
        
        tokens = None
        attention_mask = None
        if descriptions:
            tokens, attention_mask = self.tokenizer.batch_encode(descriptions)
            tokens = tokens.to(self.device)
            attention_mask = attention_mask.to(self.device)
        
        with torch.no_grad():
            result = self.model(image_tensor, tokens, attention_mask)
        
        output = {
            'chart_embedding': result['chart_embeddings'][0].cpu().numpy()
        }
        
        pattern_probs = result['pattern_probs'][0].cpu().numpy()
        top_patterns_idx = np.argsort(pattern_probs)[-5:][::-1]
        output['patterns'] = [
            {
                'pattern': self.pattern_names[idx],
                'probability': float(pattern_probs[idx])
            }
            for idx in top_patterns_idx
        ]
        output['pattern_confidence'] = result['pattern_confidence'][0].item()
        
        if descriptions:
            output['text_embeddings'] = result['text_embeddings'].cpu().numpy()
            
            similarities = result['logits_per_chart'][0].cpu().numpy()
            output['text_similarities'] = [
                {
                    'description': desc,
                    'similarity': float(sim)
                }
                for desc, sim in zip(descriptions, similarities)
            ]
            
            output['signal'] = {
                'action': ['BUY', 'SELL', 'HOLD'][
                    result['signal_probs'][0].argmax().item()
                ],
                'probabilities': result['signal_probs'][0].cpu().numpy().tolist(),
                'strength': result['strength'][0].item(),
                'timeframe': ['scalp', 'intraday', 'swing', 'position'][
                    result['timeframe_probs'][0].argmax().item()
                ]
            }
        
        return output
    
    def match_chart_to_descriptions(
        self,
        chart_image: np.ndarray,
        descriptions: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Match a chart to multiple text descriptions.
        
        Args:
            chart_image: Chart image array
            descriptions: List of text descriptions
        
        Returns:
            Ranked list of description matches
        """
        result = self.analyze_chart(chart_image, descriptions)
        
        matches = sorted(
            result['text_similarities'],
            key=lambda x: x['similarity'],
            reverse=True
        )
        
        return matches
    
    def find_similar_patterns(
        self,
        query_chart: np.ndarray,
        chart_database: List[np.ndarray],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find charts with similar patterns.
        
        Args:
            query_chart: Query chart image
            chart_database: List of chart images to search
            top_k: Number of similar charts to return
        
        Returns:
            List of similar charts with similarity scores
        """
        query_result = self.analyze_chart(query_chart)
        query_embedding = query_result['chart_embedding']
        
        similarities = []
        for i, chart in enumerate(chart_database):
            result = self.analyze_chart(chart)
            embedding = result['chart_embedding']
            
            similarity = np.dot(query_embedding, embedding)
            similarities.append({
                'index': i,
                'similarity': float(similarity),
                'patterns': result['patterns'][:3]
            })
        
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
    
    def generate_chart_description(
        self,
        chart_image: np.ndarray
    ) -> str:
        """
        Generate a text description of a chart.
        
        Args:
            chart_image: Chart image array
        
        Returns:
            Text description of the chart
        """
        result = self.analyze_chart(chart_image)
        
        top_pattern = result['patterns'][0]
        confidence = result['pattern_confidence']
        
        description = f"Chart shows {top_pattern['pattern'].replace('_', ' ')} "
        description += f"pattern with {top_pattern['probability']:.1%} probability. "
        description += f"Overall confidence: {confidence:.1%}."
        
        return description
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        return {
            'running': self.running,
            'device': self.device,
            'num_patterns': len(self.pattern_names),
            'image_size': self.config.image_size
        }
    
    def save(self, filepath: str):
        """Save model weights."""
        torch.save({
            'model': self.model.state_dict(),
            'config': self.config
        }, filepath)
        logger.info(f"📎 OPENCLIP saved to {filepath}")
    
    def load(self, filepath: str):
        """Load model weights."""
        state = torch.load(filepath, map_location=self.device)
        self.model.load_state_dict(state['model'])
        logger.info(f"📎 OPENCLIP loaded from {filepath}")


__all__ = [
    'OPENCLIP',
    'OpenCLIPConfig',
    'OpenCLIPTrading',
    'ChartEncoder',
    'TextEncoder',
    'ChartPatternType',
    'ChartPatternClassifier',
    'TradingSignalGenerator'
]
