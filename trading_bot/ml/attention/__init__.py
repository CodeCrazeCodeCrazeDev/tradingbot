"""
attention package
"""

try:
    from .feature_attention import FeatureAttention, create_feature_attention
    from .temporal_attention import TemporalAttention, create_temporal_attention
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in attention: {e}')

__all__ = [
    'FeatureAttention',
    'TemporalAttention',
    'create_feature_attention',
    'create_temporal_attention',
]