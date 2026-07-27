"""
Literature sub-package for Research OS.
Handles embedding generation and duplicate/redundancy checks.
"""

from .embedding import (
    TFIDFEmbeddingProvider,
    BM25EmbeddingProvider,
    SentenceTransformersEmbeddingProvider
)
from .duplicate_detection import (
    LevenshteinDuplicateDetector,
    CosineDuplicateDetector,
    HybridEnsembleDuplicateDetector
)

__all__ = [
    'TFIDFEmbeddingProvider',
    'BM25EmbeddingProvider',
    'SentenceTransformersEmbeddingProvider',
    'LevenshteinDuplicateDetector',
    'CosineDuplicateDetector',
    'HybridEnsembleDuplicateDetector'
]
