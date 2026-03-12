"""
DeepChart Latent State Engine - Regime Detection via Lightweight Autoencoder

Extracts latent market state using CPU-friendly autoencoder.
Produces regime-as-color for visualization background.

Architecture (CPU-friendly, <100K params):
    Input: 32 features → Encoder(64→32→8) → Latent(8) → Regime Classifier(8)

Regime colors:
    TRENDING_UP: Green gradient
    TRENDING_DOWN: Red gradient
    RANGING: Blue gradient
    VOLATILE: Orange gradient
    TRANSITION: Purple gradient

Performance Budget:
    - Inference: <1ms
    - Memory: <50KB per symbol
    - ONNX exportable
"""

import numpy as np
from collections import deque
from typing import Tuple, Optional
import logging

from .market_intelligence_core import (
    LatentMarketState,
    MarketRegime,
    MarketIntelligenceConfig,
)

logger = logging.getLogger(__name__)


class LatentStateEngine:
    """
    Extracts latent market state using lightweight autoencoder.
    
    The latent vector captures market microstructure in 8 dimensions,
    which maps to regime classification and visualization colors.
    """
    
    # Regime colors (RGBA)
    REGIME_COLORS = {
        MarketRegime.TRENDING_UP: (35, 134, 54, 200),      # Green
        MarketRegime.TRENDING_DOWN: (218, 54, 51, 200),    # Red
        MarketRegime.RANGING_TIGHT: (31, 111, 235, 150),   # Blue light
        MarketRegime.RANGING_WIDE: (31, 111, 235, 200),    # Blue dark
        MarketRegime.VOLATILE_EXPANSION: (240, 136, 62, 200),  # Orange
        MarketRegime.VOLATILE_COMPRESSION: (163, 113, 247, 200),  # Purple
        MarketRegime.TRANSITION: (110, 118, 129, 150),     # Gray
        MarketRegime.UNKNOWN: (110, 118, 129, 100),        # Gray faded
    }
    
    def __init__(self, config: MarketIntelligenceConfig):
        self.config = config
        self._feature_buffer = deque(maxlen=200)
        self._regime_history = deque(maxlen=100)
        self._current_regime = MarketRegime.UNKNOWN
        self._regime_start_bar = 0
        self._bar_count = 0
        
        # Initialize lightweight encoder weights (numpy-only, ONNX compatible)
        self._init_weights()
    
    def _init_weights(self):
        """Initialize encoder weights with Xavier initialization."""
        np.random.seed(42)
        
        # Encoder: 32 → 64 → 32 → 8
        self._encoder_w1 = np.random.randn(32, 64) * np.sqrt(2.0 / 32)
        self._encoder_b1 = np.zeros(64)
        self._encoder_w2 = np.random.randn(64, 32) * np.sqrt(2.0 / 64)
        self._encoder_b2 = np.zeros(32)
        self._encoder_w3 = np.random.randn(32, self.config.latent_dim) * np.sqrt(2.0 / 32)
        self._encoder_b3 = np.zeros(self.config.latent_dim)
        
        # Classifier: 8 → 8 (8 regimes)
        self._classifier_w = np.random.randn(self.config.latent_dim, 8) * np.sqrt(2.0 / self.config.latent_dim)
        self._classifier_b = np.zeros(8)
    
    def update(self, features: np.ndarray) -> LatentMarketState:
        """
        Update latent state with new features.
        
        Args:
            features: 32-dim feature vector from feature pipeline
            
        Returns:
            LatentMarketState with regime, confidence, and visualization data
        """
        self._bar_count += 1
        self._feature_buffer.append(features)
        
        if len(self._feature_buffer) < 20:
            return self._create_unknown_state()
        
        # Normalize features
        features_norm = self._normalize_features(features)
        
        # Encode to latent space
        latent_vector = self._encode(features_norm)
        
        # Classify regime
        regime, confidence = self._classify_regime(latent_vector)
        
        # Track regime history
        self._regime_history.append(regime)
        
        # Check for regime transition
        transition_prob = self._calculate_transition_prob()
        if regime != self._current_regime:
            if confidence > 0.6 and transition_prob > 0.5:
                self._current_regime = regime
                self._regime_start_bar = self._bar_count
        
        # Calculate regime stability
        stability = self._calculate_stability()
        
        # Get regime color (adjusted by confidence)
        color = self._get_regime_color(regime, confidence)
        
        return LatentMarketState(
            regime=regime,
            regime_confidence=confidence,
            latent_vector=latent_vector,
            regime_color=color,
            transition_probability=transition_prob,
            regime_duration_bars=self._bar_count - self._regime_start_bar,
            regime_stability=stability
        )
    
    def _normalize_features(self, features: np.ndarray) -> np.ndarray:
        """Normalize features using running statistics."""
        if len(self._feature_buffer) < 20:
            return features
        
        buffer = np.array(self._feature_buffer)
        mean = np.mean(buffer, axis=0)
        std = np.std(buffer, axis=0) + 1e-8
        
        return (features - mean) / std
    
    def _encode(self, features: np.ndarray) -> np.ndarray:
        """
        Encode features to latent space.
        
        Simple feedforward encoder with ReLU activations.
        ONNX compatible operations only.
        """
        # Layer 1: 32 → 64
        h1 = np.maximum(0, features @ self._encoder_w1 + self._encoder_b1)  # ReLU
        
        # Layer 2: 64 → 32
        h2 = np.maximum(0, h1 @ self._encoder_w2 + self._encoder_b2)  # ReLU
        
        # Layer 3: 32 → 8 (latent)
        latent = np.tanh(h2 @ self._encoder_w3 + self._encoder_b3)  # Tanh for bounded output
        
        return latent
    
    def _classify_regime(self, latent: np.ndarray) -> Tuple[MarketRegime, float]:
        """
        Classify regime from latent vector.
        
        Uses softmax classification over 8 regime types.
        """
        # Classifier forward pass
        logits = latent @ self._classifier_w + self._classifier_b
        
        # Softmax
        exp_logits = np.exp(logits - np.max(logits))  # Numerical stability
        probs = exp_logits / np.sum(exp_logits)
        
        # Map to regime
        regime_idx = np.argmax(probs)
        confidence = float(probs[regime_idx])
        
        regimes = [
            MarketRegime.TRENDING_UP,
            MarketRegime.TRENDING_DOWN,
            MarketRegime.RANGING_TIGHT,
            MarketRegime.RANGING_WIDE,
            MarketRegime.VOLATILE_EXPANSION,
            MarketRegime.VOLATILE_COMPRESSION,
            MarketRegime.TRANSITION,
            MarketRegime.UNKNOWN
        ]
        
        return regimes[min(regime_idx, len(regimes) - 1)], confidence
    
    def _calculate_transition_prob(self) -> float:
        """
        Calculate probability of regime transition.
        
        Based on recent regime change frequency.
        """
        if len(self._regime_history) < 10:
            return 0.5
        
        # Count recent regime changes
        history = list(self._regime_history)
        changes = sum(1 for i in range(1, len(history))
                     if history[i] != history[i-1])
        
        return min(1.0, changes / len(history) * 2)
    
    def _calculate_stability(self) -> float:
        """
        Calculate regime stability.
        
        Stable after 50 bars in same regime.
        """
        duration = self._bar_count - self._regime_start_bar
        return min(1.0, duration / 50)
    
    def _get_regime_color(self, regime: MarketRegime, confidence: float) -> Tuple[int, int, int, int]:
        """
        Get regime color adjusted by confidence.
        
        Lower confidence = more transparent.
        """
        base_color = self.REGIME_COLORS.get(regime, self.REGIME_COLORS[MarketRegime.UNKNOWN])
        
        # Adjust alpha by confidence
        adjusted_alpha = int(base_color[3] * confidence)
        
        return (base_color[0], base_color[1], base_color[2], adjusted_alpha)
    
    def _create_unknown_state(self) -> LatentMarketState:
        """Create unknown state for insufficient data."""
        return LatentMarketState(
            regime=MarketRegime.UNKNOWN,
            regime_confidence=0.0,
            latent_vector=np.zeros(self.config.latent_dim),
            regime_color=self.REGIME_COLORS[MarketRegime.UNKNOWN],
            transition_probability=0.5,
            regime_duration_bars=0,
            regime_stability=0.0
        )
    
    def get_regime_probabilities(self, features: np.ndarray) -> np.ndarray:
        """Get probability distribution over all regimes."""
        features_norm = self._normalize_features(features)
        latent = self._encode(features_norm)
        
        logits = latent @ self._classifier_w + self._classifier_b
        exp_logits = np.exp(logits - np.max(logits))
        return exp_logits / np.sum(exp_logits)
    
    def export_weights(self) -> dict:
        """Export weights for ONNX conversion."""
        return {
            'encoder_w1': self._encoder_w1,
            'encoder_b1': self._encoder_b1,
            'encoder_w2': self._encoder_w2,
            'encoder_b2': self._encoder_b2,
            'encoder_w3': self._encoder_w3,
            'encoder_b3': self._encoder_b3,
            'classifier_w': self._classifier_w,
            'classifier_b': self._classifier_b,
        }
    
    def load_weights(self, weights: dict):
        """Load pre-trained weights."""
        self._encoder_w1 = weights['encoder_w1']
        self._encoder_b1 = weights['encoder_b1']
        self._encoder_w2 = weights['encoder_w2']
        self._encoder_b2 = weights['encoder_b2']
        self._encoder_w3 = weights['encoder_w3']
        self._encoder_b3 = weights['encoder_b3']
        self._classifier_w = weights['classifier_w']
        self._classifier_b = weights['classifier_b']
    
    def reset(self):
        """Reset engine state."""
        self._feature_buffer.clear()
        self._regime_history.clear()
        self._current_regime = MarketRegime.UNKNOWN
        self._regime_start_bar = 0
        self._bar_count = 0
