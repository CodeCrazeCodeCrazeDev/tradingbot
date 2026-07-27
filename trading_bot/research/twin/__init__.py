"""
Digital Twin Sub-package for Research OS.
Instantiates adversarial market environments (flash crashes, outages, spread expansions) to test strategy survivability.
"""

from .simulator import AdversarialMarketDigitalTwin

__all__ = [
    'AdversarialMarketDigitalTwin'
]
