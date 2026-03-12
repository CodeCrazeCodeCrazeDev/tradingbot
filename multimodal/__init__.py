"""
Phase 6: Multimodal Intelligence
Combines text, price, and alternative data
"""

from .text_encoder import (
    NewsEncoder,
    SocialMediaEncoder,
    MultiSourceTextProcessor
)

from .price_encoder import (
    PricePatternEncoder,
    TechnicalIndicatorEncoder,
    MarketMicrostructureEncoder,
    PriceEncoder
)

from .alt_data import (
    SatelliteDataProcessor,
    WeatherDataProcessor,
    MacroDataProcessor,
    AlternativeDataIntegration
)

from .fusion_network import (
    CrossModalAttention,
    ModalityFusionLayer,
    MultimodalFusion
)

__all__ = [
    'NewsEncoder',
    'SocialMediaEncoder',
    'MultiSourceTextProcessor',
    'PricePatternEncoder',
    'TechnicalIndicatorEncoder',
    'MarketMicrostructureEncoder',
    'PriceEncoder',
    'SatelliteDataProcessor',
    'WeatherDataProcessor',
    'MacroDataProcessor',
    'AlternativeDataIntegration',
    'CrossModalAttention',
    'ModalityFusionLayer',
    'MultimodalFusion'
]
