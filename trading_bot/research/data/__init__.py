"""
Data Discovery Sub-package for Research OS.
Includes Data Providers, Quality Validators, Dataset Registries, and Active Learning engines.
"""

from .providers import LocalCSVDataProvider, YahooFinanceDataProvider
from .validator import StandardDatasetValidator
from .registry import StandardDatasetRegistry
from .active_learning import RegimeGapActiveLearning

__all__ = [
    'LocalCSVDataProvider',
    'YahooFinanceDataProvider',
    'StandardDatasetValidator',
    'StandardDatasetRegistry',
    'RegimeGapActiveLearning'
]
