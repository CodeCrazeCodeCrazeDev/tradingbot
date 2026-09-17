"""
Discovery sub-package for Research OS.
Exposes pluggable Literature Discovery Providers.
"""

from .providers import (
    ArxivDiscoveryProvider,
    SemanticScholarDiscoveryProvider,
    LocalArchiveDiscoveryProvider
)

__all__ = [
    'ArxivDiscoveryProvider',
    'SemanticScholarDiscoveryProvider',
    'LocalArchiveDiscoveryProvider'
]
