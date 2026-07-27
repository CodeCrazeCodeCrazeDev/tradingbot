"""
Embedding Provider implementations for the Research OS.
Includes lightweight local TF-IDF and abstract integrations for other models.
"""

import numpy as np
from typing import List
from trading_bot.research.core.interfaces import EmbeddingProvider


class TFIDFEmbeddingProvider(EmbeddingProvider):
    """
    A lightweight, dependency-free local character-level TF-IDF embedding provider
    for robust similarity comparison without API calls.
    """

    def __init__(self, vocab_size: int = 500):
        self.vocab_size = vocab_size
        # Simple alphabet of common characters/symbols for char-level hashing
        self.chars = [chr(i) for i in range(97, 123)] + [chr(i) for i in range(48, 58)] + [" ", "-", "_"]
        self.char_map = {c: i for i, c in enumerate(self.chars)}

    def _text_to_vector(self, text: str) -> np.ndarray:
        """Create a normalized frequency vector based on character and n-gram occurrences."""
        text = text.lower()
        vector = np.zeros(self.vocab_size)

        # Unigrams
        for char in text:
            if char in self.char_map:
                idx = self.char_map[char] % self.vocab_size
                vector[idx] += 1.0

        # Bigrams
        for i in range(len(text) - 1):
            bigram = text[i:i+2]
            idx = hash(bigram) % self.vocab_size
            vector[idx] += 2.0

        # Trigrams
        for i in range(len(text) - 2):
            trigram = text[i:i+3]
            idx = hash(trigram) % self.vocab_size
            vector[idx] += 3.0

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector

    def embed(self, text: str) -> np.ndarray:
        return self._text_to_vector(text)

    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        return [self.embed(t) for t in texts]


class BM25EmbeddingProvider(EmbeddingProvider):
    """
    Lightweight keyword-occurrence vectorizer inspired by BM25 scoring.
    """

    def __init__(self, vocab_size: int = 1000):
        self.vocab_size = vocab_size

    def embed(self, text: str) -> np.ndarray:
        text = text.lower()
        words = [w for w in text.split() if len(w) > 2]
        vector = np.zeros(self.vocab_size)

        for word in words:
            # Simple TF scaling: tf / (tf + 0.5 + 1.5 * (doc_len / avg_doc_len))
            # Approximated locally per-document
            idx = hash(word) % self.vocab_size
            vector[idx] += 1.0

        # Apply BM25 term frequency saturation
        vector = vector / (vector + 1.2)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector

    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        return [self.embed(t) for t in texts]


class SentenceTransformersEmbeddingProvider(EmbeddingProvider):
    """
    Shell integration for full sentence-transformers models.
    Falls back to TFIDF if sentence-transformers is not installed.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._fallback = None
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except ImportError:
            self._fallback = TFIDFEmbeddingProvider()

    def embed(self, text: str) -> np.ndarray:
        if self.model is not None:
            return self.model.encode(text)
        return self._fallback.embed(text)

    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        if self.model is not None:
            return self.model.encode(texts)
        return self._fallback.embed_batch(texts)
