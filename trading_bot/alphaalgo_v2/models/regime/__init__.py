"""
regime package
"""

try:
    from .detector import RegimeAnalysis, RegimeDetector
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in regime: {e}')

__all__ = [
    'RegimeAnalysis',
    'RegimeDetector',
]