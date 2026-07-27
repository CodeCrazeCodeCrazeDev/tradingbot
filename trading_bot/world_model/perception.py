import torch
import torch.nn as nn
from typing import Dict, Optional, Tuple, List
import numpy as np

class MultimodalPerception(nn.Module):
    """
    Upgraded L1 Perception Foundation.
    Ingests broad range of financial data:
    - Price (OHLCV)
    - Tick data
    - L2 Order Book
    - Market Microstructure
    - Macro data
    - News/Sentiment
    - Options/Futures
    - On-chain (if relevant)
    - SEC/Earnings/Calendars
    """
    def __init__(self, latent_dim: int = 64, hidden_dim: int = 256):
        super().__init__()
        self.latent_dim = latent_dim

        # Specialized encoders for different data classes
        self.encoders = nn.ModuleDict({
            'market_data': nn.Sequential(nn.Linear(20, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, latent_dim)),
            'order_book': nn.Sequential(nn.Linear(100, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, latent_dim)),
            'macro_econ': nn.Sequential(nn.Linear(50, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, latent_dim)),
            'sentiment_nlp': nn.Sequential(nn.Linear(768, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, latent_dim)),
            'microstructure': nn.Sequential(nn.Linear(15, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, latent_dim))
        })

        # Cross-modal aggregator (Attention-based)
        self.aggregator = nn.MultiheadAttention(latent_dim, num_heads=4, batch_first=True)
        self.output_layer = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim)
        )

    def forward(self, multimodal_input: Dict[str, torch.Tensor]) -> torch.Tensor:
        encoded_features = []
        for key, encoder in self.encoders.items():
            if key in multimodal_input:
                feat = encoder(multimodal_input[key])
                if feat.dim() == 1:
                    feat = feat.unsqueeze(0)
                encoded_features.append(feat)

        if not encoded_features:
            return torch.zeros(1, self.latent_dim, device=next(self.parameters()).device)

        # Stack and apply attention
        # Ensure all features have same batch size
        batch_size = encoded_features[0].size(0)
        stacked = torch.stack(encoded_features, dim=1) # [B, NumModalities, Latent]
        attn_out, _ = self.aggregator(stacked, stacked, stacked)

        # Pool (mean) and project
        pooled = attn_out.mean(dim=1)
        return self.output_layer(pooled)
