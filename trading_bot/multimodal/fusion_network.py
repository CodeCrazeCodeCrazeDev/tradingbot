"""
Phase 6: Multimodal Intelligence - Multimodal Fusion
Combines text, price, and alternative data
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
import numpy as np
import logging
from .text_encoder import MultiSourceTextProcessor
from .price_encoder import PriceEncoder

logger = logging.getLogger(__name__)


class CrossModalAttention(nn.Module):
    """
    Attention mechanism between different modalities.
    Allows modalities to attend to each other.
    """
    
    def __init__(self, hidden_dim: int = 64, num_heads: int = 8):
        try:
            super().__init__()
        
            self.attention = nn.MultiheadAttention(
                embed_dim=hidden_dim,
                num_heads=num_heads,
                dropout=0.1
            )
        
            self.norm1 = nn.LayerNorm(hidden_dim)
            self.norm2 = nn.LayerNorm(hidden_dim)
        
            self.ffn = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim * 4),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(hidden_dim * 4, hidden_dim)
            )
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Cross-modal attention forward pass."""
        # Self attention
        try:
            attn_output, _ = self.attention(
                query=query,
                key=key,
                value=value,
                attn_mask=mask
            )
        
            # Add & norm
            out1 = self.norm1(query + attn_output)
        
            # FFN
            ffn_output = self.ffn(out1)
        
            # Add & norm
            out2 = self.norm2(out1 + ffn_output)
        
            return out2
        except Exception as e:
            logger.error(f"Error in forward: {e}")
            raise


class ModalityFusionLayer(nn.Module):
    """
    Fuses multiple modalities using cross-attention.
    Allows each modality to influence others.
    """
    
    def __init__(self, hidden_dim: int = 64, num_heads: int = 8):
        try:
            super().__init__()
        
            # Cross-modal attention blocks
            self.price_to_text = CrossModalAttention(hidden_dim, num_heads)
            self.text_to_price = CrossModalAttention(hidden_dim, num_heads)
        
            # Optional alternative data attention
            self.alt_to_price = CrossModalAttention(hidden_dim, num_heads)
            self.alt_to_text = CrossModalAttention(hidden_dim, num_heads)
        
            # Fusion layer
            self.fusion = nn.Sequential(
                nn.Linear(hidden_dim * 3, hidden_dim * 2),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(hidden_dim * 2, hidden_dim)
            )
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def forward(
        self,
        price_features: torch.Tensor,
        text_features: torch.Tensor,
        alt_features: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Fuse multiple modalities.
        
        Args:
            price_features: Price modality features
            text_features: Text modality features
            alt_features: Optional alternative data features
        
        Returns:
            Fused representation
        """
        # Cross-modal attention
        try:
            price_attended = self.text_to_price(
                price_features,
                text_features,
                text_features
            )
        
            text_attended = self.price_to_text(
                text_features,
                price_features,
                price_features
            )
        
            if alt_features is not None:
                # Alternative data attention
                price_attended = self.alt_to_price(
                    price_attended,
                    alt_features,
                    alt_features
                )
            
                text_attended = self.alt_to_text(
                    text_attended,
                    alt_features,
                    alt_features
                )
            
                # Concatenate all features
                combined = torch.cat([
                    price_attended,
                    text_attended,
                    alt_features
                ], dim=-1)
            else:
                # Without alternative data
                combined = torch.cat([
                    price_attended,
                    text_attended,
                    torch.zeros_like(price_attended)
                ], dim=-1)
        
            # Final fusion
            return self.fusion(combined)
        except Exception as e:
            logger.error(f"Error in forward: {e}")
            raise


class MultimodalFusion:
    """
    Complete multimodal fusion system.
    Combines price, text, and alternative data.
    """
    
    def __init__(
        self,
        hidden_dim: int = 64,
        num_fusion_layers: int = 3,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        # Encoders
        try:
            self.text_processor = MultiSourceTextProcessor()
            self.price_encoder = PriceEncoder(hidden_dim=hidden_dim)
        
            # Fusion layers
            self.fusion_layers = nn.ModuleList([
                ModalityFusionLayer(hidden_dim=hidden_dim)
                for _ in range(num_fusion_layers)
            ]).to(device)
        
            # Final prediction layers
            self.prediction_head = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(hidden_dim, 3)  # BUY, SELL, HOLD
            ).to(device)
        
            self.device = device
            logger.info("✅ Multimodal Fusion System initialized")
            logger.info(f"   Hidden dim: {hidden_dim}")
            logger.info(f"   Fusion layers: {num_fusion_layers}")
            logger.info(f"   Device: {device}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def process_all_data(
        self,
        price_data: Dict,
        news_articles: List[str],
        social_posts: List[str],
        alt_data: Optional[Dict] = None
    ) -> Dict:
        """
        Process and fuse all available data.
        
        Args:
            price_data: Dictionary with price/indicator data
            news_articles: List of news articles
            social_posts: List of social media posts
            alt_data: Optional alternative data
        
        Returns:
            Dictionary with predictions and analysis
        """
        # Process text data
        try:
            text_output = self.text_processor.process_all_sources(
                news_articles,
                social_posts
            )
        
            # Convert price data to tensors
            price_tensors = {
                'ohlcv': torch.tensor(price_data['ohlcv']).float(),
                'indicators': {
                    k: torch.tensor(v).float()
                    for k, v in price_data['indicators'].items()
                }
            }
        
            if 'order_book' in price_data:
                price_tensors['order_book'] = torch.tensor(
                    price_data['order_book']
                ).float()
                price_tensors['trade_flow'] = torch.tensor(
                    price_data['trade_flow']
                ).float()
        
            # Encode price data
            price_output = self.price_encoder.encode(
                price_tensors['ohlcv'],
                price_tensors['indicators'],
                price_tensors.get('order_book'),
                price_tensors.get('trade_flow')
            )
        
            # Prepare alternative data if available
            if alt_data is not None:
                alt_features = self._process_alt_data(alt_data)
            else:
                alt_features = None
        
            # Fuse modalities
            fused = self._fuse_modalities(
                price_output['encoding'],
                text_output['news_embeddings'],
                alt_features
            )
        
            # Generate predictions
            predictions = self.prediction_head(fused)
            probabilities = torch.softmax(predictions, dim=-1)
        
            return {
                'predictions': probabilities.detach().cpu().numpy(),
                'fused_features': fused.detach().cpu().numpy(),
                'price_patterns': price_output['patterns'],
                'text_sentiment': text_output['combined_sentiment'],
                'symbol_mentions': text_output['symbol_mentions']
            }
        except Exception as e:
            logger.error(f"Error in process_all_data: {e}")
            raise
    
    def _fuse_modalities(
        self,
        price_features: torch.Tensor,
        text_features: torch.Tensor,
        alt_features: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Apply multi-layer fusion."""
        # Move to device
        try:
            price_features = price_features.to(self.device)
            text_features = text_features.to(self.device)
            if alt_features is not None:
                alt_features = alt_features.to(self.device)
        
            # Apply fusion layers
            fused = price_features
            for layer in self.fusion_layers:
                fused = layer(fused, text_features, alt_features)
        
            return fused
        except Exception as e:
            logger.error(f"Error in _fuse_modalities: {e}")
            raise
    
    def _process_alt_data(self, alt_data: Dict) -> torch.Tensor:
        """Process alternative data sources."""
        # Example alternative data processing
        try:
            features = []
        
            if 'satellite' in alt_data:
                features.append(alt_data['satellite'])
        
            if 'weather' in alt_data:
                features.append(alt_data['weather'])
        
            if 'macro' in alt_data:
                features.append(alt_data['macro'])
        
            if features:
                return torch.cat(features, dim=-1)
            else:
                return None
        except Exception as e:
            logger.error(f"Error in _process_alt_data: {e}")
            raise
    
    def explain_fusion(
        self,
        price_data: Dict,
        text_data: Dict,
        fused_output: Dict
    ) -> str:
        """
        Generate explanation of fusion process.
        
        Returns:
            Human-readable explanation
        """
        # Get predictions
        try:
            action_probs = fused_output['predictions'][0]
            actions = ['BUY', 'SELL', 'HOLD']
            predicted_action = actions[np.argmax(action_probs)]
        
            # Extract key signals
            price_patterns = fused_output['price_patterns']
            sentiment = fused_output['text_sentiment']
        
            # Build explanation
            explanation = [
                f"Predicted Action: {predicted_action} "
                f"({action_probs[np.argmax(action_probs)]:.1%} confidence)\n",
                "\nPrice Analysis:",
                f"- Trend: {price_patterns['trend']}",
                f"- Volatility: {price_patterns['volatility']:.2f}",
                f"- Momentum: {price_patterns['momentum']:.2f}",
                "\nText Analysis:",
                f"- Overall Sentiment: {sentiment:.2f}",
                f"- Symbol Mentions: {fused_output['symbol_mentions']}"
            ]
        
            return "\n".join(explanation)
        except Exception as e:
            logger.error(f"Error in explain_fusion: {e}")
            raise
    
    def save(self, filepath: str):
        """Save fusion system."""
        try:
            torch.save({
                'fusion_layers': [l.state_dict() for l in self.fusion_layers],
                'prediction_head': self.prediction_head.state_dict()
            }, filepath)
        
            # Save encoders
            self.price_encoder.save(filepath + '.price')
            self.text_processor.save_state(filepath + '.text')
        
            logger.info(f"💾 Fusion system saved to {filepath}")
        except Exception as e:
            logger.error(f"Error in save: {e}")
            raise
    
    def load(self, filepath: str):
        """Load fusion system."""
        try:
            state = torch.load(filepath)
        
            for layer, state_dict in zip(self.fusion_layers, state['fusion_layers']):
                layer.load_state_dict(state_dict)
        
            self.prediction_head.load_state_dict(state['prediction_head'])
        
            # Load encoders
            self.price_encoder.load(filepath + '.price')
            self.text_processor.load_state(filepath + '.text')
        
            logger.info(f"📂 Fusion system loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error in load: {e}")
            raise
