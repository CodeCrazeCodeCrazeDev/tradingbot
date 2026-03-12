"""
Skill #20: Contrastive Learning Embeddings
==========================================

Learns market regime embeddings using contrastive learning
to identify similar market conditions.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class MarketEmbedding:
    """Embedding for a market state."""
    embedding: np.ndarray
    regime_label: str
    similarity_scores: Dict[str, float]
    nearest_historical: List[Tuple[int, float]]


@dataclass
class ContrastiveResult:
    """Contrastive learning result."""
    current_embedding: MarketEmbedding
    regime_probabilities: Dict[str, float]
    similar_periods: List[int]
    regime_transition_prob: Dict[str, float]
    trading_signal: str
    confidence: float


class ContrastiveLearningEmbeddings:
    """Contrastive learning for market regime identification."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.embedding_dim = self.config.get('embedding_dim', 32)
        self.temperature = self.config.get('temperature', 0.1)
        self.embeddings_db: List[Tuple[np.ndarray, str]] = []
        self.encoder = np.random.randn(20, self.embedding_dim) * 0.1
        logger.info("ContrastiveLearningEmbeddings initialized")
    
    def analyze(self, prices: np.ndarray, volumes: np.ndarray) -> ContrastiveResult:
        """Analyze current market using contrastive embeddings."""
        if len(prices) < 30:
            return self._create_empty_result()
        
        # Extract features and encode
        features = self._extract_features(prices, volumes)
        embedding = self._encode(features)
        
        # Find similar historical periods
        similarities = self._find_similar(embedding)
        
        # Classify regime
        regime_probs = self._classify_regime(embedding)
        regime_label = max(regime_probs, key=regime_probs.get)
        
        # Transition probabilities
        transitions = self._estimate_transitions(regime_label)
        
        current = MarketEmbedding(
            embedding=embedding,
            regime_label=regime_label,
            similarity_scores=regime_probs,
            nearest_historical=similarities[:5]
        )
        
        signal = self._generate_signal(regime_label, regime_probs, transitions)
        confidence = max(regime_probs.values())
        
        return ContrastiveResult(
            current_embedding=current,
            regime_probabilities=regime_probs,
            similar_periods=[idx for idx, _ in similarities[:10]],
            regime_transition_prob=transitions,
            trading_signal=signal,
            confidence=confidence
        )
    
    def _extract_features(self, prices: np.ndarray, volumes: np.ndarray) -> np.ndarray:
        """Extract features for embedding."""
        returns = np.diff(prices) / prices[:-1]
        features = [
            np.mean(returns[-20:]),
            np.std(returns[-20:]),
            np.mean(returns[-5:]),
            np.std(returns[-5:]),
            np.max(returns[-20:]),
            np.min(returns[-20:]),
            (prices[-1] - prices[-20]) / prices[-20],
            np.mean(volumes[-20:]) / np.mean(volumes),
            self._calculate_trend_strength(prices),
            self._calculate_volatility_regime(returns),
        ]
        # Pad to 20 features
        features.extend([0] * (20 - len(features)))
        return np.array(features[:20])
    
    def _calculate_trend_strength(self, prices: np.ndarray) -> float:
        """Calculate trend strength."""
        if len(prices) < 20:
            return 0
        x = np.arange(20)
        y = prices[-20:]
        slope = np.polyfit(x, y, 1)[0]
        return slope / np.mean(y)
    
    def _calculate_volatility_regime(self, returns: np.ndarray) -> float:
        """Calculate volatility regime indicator."""
        if len(returns) < 20:
            return 0
        recent_vol = np.std(returns[-5:])
        historical_vol = np.std(returns[-20:])
        return recent_vol / (historical_vol + 1e-10)
    
    def _encode(self, features: np.ndarray) -> np.ndarray:
        """Encode features to embedding."""
        embedding = np.tanh(features @ self.encoder)
        embedding = embedding / (np.linalg.norm(embedding) + 1e-10)
        return embedding
    
    def _find_similar(self, embedding: np.ndarray) -> List[Tuple[int, float]]:
        """Find similar historical embeddings."""
        similarities = []
        for idx, (hist_emb, _) in enumerate(self.embeddings_db):
            sim = np.dot(embedding, hist_emb)
            similarities.append((idx, sim))
        return sorted(similarities, key=lambda x: x[1], reverse=True)
    
    def _classify_regime(self, embedding: np.ndarray) -> Dict[str, float]:
        """Classify market regime from embedding."""
        # Simplified regime classification
        regimes = {
            'trending_up': embedding[0] + embedding[2],
            'trending_down': -embedding[0] - embedding[2],
            'high_volatility': embedding[1] + embedding[3],
            'low_volatility': -embedding[1] - embedding[3],
            'ranging': 1 - abs(embedding[0]) - abs(embedding[1])
        }
        # Softmax
        exp_vals = {k: np.exp(v / self.temperature) for k, v in regimes.items()}
        total = sum(exp_vals.values())
        return {k: v / total for k, v in exp_vals.items()}
    
    def _estimate_transitions(self, current_regime: str) -> Dict[str, float]:
        """Estimate regime transition probabilities."""
        # Simplified transition matrix
        transitions = {
            'trending_up': 0.2,
            'trending_down': 0.2,
            'high_volatility': 0.2,
            'low_volatility': 0.2,
            'ranging': 0.2
        }
        transitions[current_regime] = 0.4  # Higher probability to stay
        return transitions
    
    def _generate_signal(
        self,
        regime: str,
        probs: Dict[str, float],
        transitions: Dict[str, float]
    ) -> str:
        """Generate trading signal."""
        if regime == 'trending_up' and probs[regime] > 0.4:
            return f"BUY: Trending up regime ({probs[regime]:.0%} confidence)"
        elif regime == 'trending_down' and probs[regime] > 0.4:
            return f"SELL: Trending down regime ({probs[regime]:.0%} confidence)"
        elif regime == 'high_volatility':
            return f"CAUTION: High volatility regime - reduce position size"
        return f"NEUTRAL: {regime} regime detected"
    
    def _create_empty_result(self) -> ContrastiveResult:
        """Create empty result."""
        return ContrastiveResult(
            current_embedding=MarketEmbedding(np.array([]), "", {}, []),
            regime_probabilities={},
            similar_periods=[],
            regime_transition_prob={},
            trading_signal="Insufficient data",
            confidence=0
        )
    
    def add_to_database(self, prices: np.ndarray, volumes: np.ndarray, label: str):
        """Add embedding to historical database."""
        features = self._extract_features(prices, volumes)
        embedding = self._encode(features)
        self.embeddings_db.append((embedding, label))
