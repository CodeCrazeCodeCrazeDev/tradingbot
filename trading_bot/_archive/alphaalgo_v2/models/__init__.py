"""
models package
"""

try:
    from .brain import IntelligenceBrain, IntelligenceResult, retry
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in models: {e}')

__all__ = [
    'IntelligenceBrain',
    'IntelligenceResult',
    'retry',
]