"""
drift_detection package
"""

try:
    from .adwin import Adwin, create_adwin
    from .adwin_detector import (
        ADWINDetector,
        ConceptDriftMonitor,
        DriftDetection,
        PageHinkleyDetector
    )
    from .monitor import Monitor, create_monitor
    from .page_hinkley import PageHinkley, create_page_hinkley
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in drift_detection: {e}')

__all__ = [
    'ADWINDetector',
    'Adwin',
    'ConceptDriftMonitor',
    'DriftDetection',
    'Monitor',
    'PageHinkley',
    'PageHinkleyDetector',
    'create_adwin',
    'create_monitor',
    'create_page_hinkley',
]