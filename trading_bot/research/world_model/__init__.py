"""
World Model Sub-package for Research OS.
Learns latent market regimes, volatility clustering, and transition matrices.
"""

from .model import MarkovRegimeSwitchingWorldModel

__all__ = [
    'MarkovRegimeSwitchingWorldModel'
]
