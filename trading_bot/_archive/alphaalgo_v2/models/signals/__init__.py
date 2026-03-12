"""
signals package
"""

try:
    from .ensemble import EnsembleSignalGenerator, retry
    from .generator import SignalGenerator
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in signals: {e}')

__all__ = [
    'EnsembleSignalGenerator',
    'SignalGenerator',
    'retry',
]