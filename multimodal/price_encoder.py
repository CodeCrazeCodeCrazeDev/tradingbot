"""
Phase 6: Multimodal Intelligence - Price Pattern Encoding
Encodes price patterns and technical indicators
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


class PricePatternEncoder(nn.Module):
    """
    Encodes price patterns using transformer architecture.
    Captures temporal dependencies and technical patterns.
    """
    
    def __init__(
        self,
        input_dim: int = 5,  # OHLCV
        hidden_dim: int = 64,
        num_layers: int = 4,
        num_heads: int = 8,
        dropout: float = 0.1
    ):
        super().__init__()
        
        # Input projection
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        
        # Positional encoding
        self.pos_encoder = PositionalEncoding(hidden_dim, dropout)
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers
        )
        
        # Pattern detection heads
        self.pattern_heads = nn.ModuleDict({
            'trend': nn.Linear(hidden_dim, 3),  # UP, DOWN, SIDEWAYS
            'volatility': nn.Linear(hidden_dim, 1),
            'momentum': nn.Linear(hidden_dim, 1),
            'support_resistance': nn.Linear(hidden_dim, 2)  # Support, Resistance
        })
        
        logger.info("✅ Price Pattern Encoder initialized")
        logger.info(f"   Input dim: {input_dim}")
        logger.info(f"   Hidden dim: {hidden_dim}")
        logger.info(f"   Layers: {num_layers}")
        logger.info(f"   Heads: {num_heads}")
    
    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Encode price sequence and detect patterns.
        
        Args:
            x: Price data [batch, seq_len, features]
            mask: Optional attention mask
        
        Returns:
            Dictionary with pattern detections
        """
        # Project input
        x = self.input_proj(x)
        
        # Add positional encoding
        x = self.pos_encoder(x)
        
        # Transformer encoding
        if mask is not None:
            encoded = self.transformer(x, src_key_padding_mask=mask)
        else:
            encoded = self.transformer(x)
        
        # Global representation (mean pooling)
        global_repr = encoded.mean(dim=1)
        
        # Pattern detection
        patterns = {
            name: head(global_repr)
            for name, head in self.pattern_heads.items()
        }
        
        return {
            'encoded': encoded,
            'global': global_repr,
            'patterns': patterns
        }


class PositionalEncoding(nn.Module):
    """Positional encoding for transformer."""
    
    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2) * (-np.log(10000.0) / d_model)
        )
        
        pe = torch.zeros(max_len, 1, d_model)
        pe[:, 0, 0:2] = torch.sin(position * div_term)
        pe[:, 0, 1:2] = torch.cos(position * div_term)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Add positional encoding."""
        x = x + self.pe[:x.size(0)]
        return self.dropout(x)


class TechnicalIndicatorEncoder(nn.Module):
    """
    Encodes technical indicators and derived features.
    Combines multiple indicator families.
    """
    
    def __init__(self, input_dim: int = 20, hidden_dim: int = 64):
        super().__init__()
        
        # Indicator families
        self.families = nn.ModuleDict({
            'momentum': self._create_family_encoder(5, hidden_dim),  # RSI, MACD, etc.
            'trend': self._create_family_encoder(5, hidden_dim),     # SMAs, EMAs
            'volatility': self._create_family_encoder(5, hidden_dim), # ATR, BB
            'volume': self._create_family_encoder(5, hidden_dim)      # OBV, VWAP
        })
        
        # Combine all families
        self.combiner = nn.Sequential(
            nn.Linear(hidden_dim * len(self.families), hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        logger.info("✅ Technical Indicator Encoder initialized")
    
    def _create_family_encoder(
        self,
        family_size: int,
        hidden_dim: int
    ) -> nn.Module:
        """Create encoder for indicator family."""
        return nn.Sequential(
            nn.Linear(family_size, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim)
        )
    
    def forward(self, indicators: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Encode technical indicators.
        
        Args:
            indicators: Dictionary of indicator values by family
        
        Returns:
            Encoded representation
        """
        # Encode each family
        family_encodings = []
        
        for family_name, encoder in self.families.items():
            if family_name in indicators:
                encoding = encoder(indicators[family_name])
                family_encodings.append(encoding)
            else:
                # Zero encoding if family missing
                encoding = torch.zeros(
                    indicators[list(indicators.keys())[0]].size(0),
                    encoder[-1].out_features,
                    device=next(encoder.parameters()).device
                )
                family_encodings.append(encoding)
        
        # Combine all families
        combined = torch.cat(family_encodings, dim=-1)
        return self.combiner(combined)


class MarketMicrostructureEncoder(nn.Module):
    """
    Encodes market microstructure data.
    Focuses on order book and trade flow.
    """
    
    def __init__(
        self,
        book_levels: int = 10,
        hidden_dim: int = 64
    ):
        super().__init__()
        
        # Order book encoder
        self.book_encoder = nn.Sequential(
            nn.Linear(book_levels * 4, hidden_dim),  # price/volume for bid/ask
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        # Trade flow encoder
        self.flow_encoder = nn.Sequential(
            nn.Linear(4, hidden_dim),  # volume, trades, buys, sells
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        # Combine book and flow
        self.combiner = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        logger.info("✅ Market Microstructure Encoder initialized")
        logger.info(f"   Book levels: {book_levels}")
        logger.info(f"   Hidden dim: {hidden_dim}")
    
    def forward(
        self,
        order_book: torch.Tensor,
        trade_flow: torch.Tensor
    ) -> torch.Tensor:
        """
        Encode market microstructure.
        
        Args:
            order_book: Order book data [batch, levels, 4]
            trade_flow: Trade flow metrics [batch, 4]
        
        Returns:
            Encoded representation
        """
        # Flatten and encode order book
        book_flat = order_book.view(order_book.size(0), -1)
        book_encoding = self.book_encoder(book_flat)
        
        # Encode trade flow
        flow_encoding = self.flow_encoder(trade_flow)
        
        # Combine
        combined = torch.cat([book_encoding, flow_encoding], dim=-1)
        return self.combiner(combined)


class PriceEncoder:
    """
    Complete price data encoder.
    Combines patterns, indicators, and microstructure.
    """
    
    def __init__(
        self,
        hidden_dim: int = 64,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.pattern_encoder = PricePatternEncoder(
            hidden_dim=hidden_dim
        ).to(device)
        
        self.indicator_encoder = TechnicalIndicatorEncoder(
            hidden_dim=hidden_dim
        ).to(device)
        
        self.microstructure_encoder = MarketMicrostructureEncoder(
            hidden_dim=hidden_dim
        ).to(device)
        
        # Combine all aspects
        self.final_combiner = nn.Sequential(
            nn.Linear(hidden_dim * 3, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim)
        ).to(device)
        
        self.device = device
        logger.info("✅ Complete Price Encoder initialized")
    
    def encode(
        self,
        price_data: torch.Tensor,
        indicators: Dict[str, torch.Tensor],
        order_book: Optional[torch.Tensor] = None,
        trade_flow: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Encode all price-related data.
        
        Args:
            price_data: OHLCV data
            indicators: Technical indicators
            order_book: Optional order book data
            trade_flow: Optional trade flow data
        
        Returns:
            Dictionary with encodings and patterns
        """
        # Encode patterns
        pattern_output = self.pattern_encoder(price_data)
        pattern_encoding = pattern_output['global']
        
        # Encode indicators
        indicator_encoding = self.indicator_encoder(indicators)
        
        # Encode microstructure if available
        if order_book is not None and trade_flow is not None:
            micro_encoding = self.microstructure_encoder(
                order_book,
                trade_flow
            )
        else:
            micro_encoding = torch.zeros_like(pattern_encoding)
        
        # Combine all encodings
        combined = torch.cat([
            pattern_encoding,
            indicator_encoding,
            micro_encoding
        ], dim=-1)
        
        final_encoding = self.final_combiner(combined)
        
        return {
            'encoding': final_encoding,
            'patterns': pattern_output['patterns'],
            'pattern_encoding': pattern_encoding,
            'indicator_encoding': indicator_encoding,
            'microstructure_encoding': micro_encoding
        }
    
    def save(self, filepath: str):
        """Save encoder state."""
        torch.save({
            'pattern_encoder': self.pattern_encoder.state_dict(),
            'indicator_encoder': self.indicator_encoder.state_dict(),
            'microstructure_encoder': self.microstructure_encoder.state_dict(),
            'final_combiner': self.final_combiner.state_dict()
        }, filepath)
        logger.info(f"💾 Price Encoder saved to {filepath}")
    
    def load(self, filepath: str):
        """Load encoder state."""
        state = torch.load(filepath)
        self.pattern_encoder.load_state_dict(state['pattern_encoder'])
        self.indicator_encoder.load_state_dict(state['indicator_encoder'])
        self.microstructure_encoder.load_state_dict(state['microstructure_encoder'])
        self.final_combiner.load_state_dict(state['final_combiner'])
        logger.info(f"📂 Price Encoder loaded from {filepath}")
