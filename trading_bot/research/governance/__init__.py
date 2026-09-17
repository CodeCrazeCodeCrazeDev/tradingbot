"""
Governance Sub-package for Research OS.
Establishes strict, un-bypassable gate-promotion structures for deploying trading strategies.
"""

from .gates import PromotionPipelineGatekeeper

__all__ = [
    'PromotionPipelineGatekeeper'
]
