"""
forecasting package
"""

try:
    from .simple import Forecast, SimpleForecaster
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in forecasting: {e}')

__all__ = [
    'Forecast',
    'SimpleForecaster',
]