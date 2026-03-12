"""
Skill #23: Active Learning Sampler
==================================

Intelligently selects most informative samples for labeling
to improve model performance with minimal data.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class Sample:
    """Sample for active learning."""
    index: int
    features: np.ndarray
    uncertainty: float
    diversity_score: float
    acquisition_score: float


@dataclass
class ActiveLearningResult:
    """Active learning sampling result."""
    samples_to_label: List[Sample]
    model_uncertainty: float
    coverage_score: float
    expected_improvement: float
    trading_signal: str


class ActiveLearningSampler:
    """Active learning for efficient sample selection."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.strategy = self.config.get('strategy', 'uncertainty')
            self.batch_size = self.config.get('batch_size', 10)
            self.labeled_indices: List[int] = []
            logger.info("ActiveLearningSampler initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def select_samples(
        self,
        prices: np.ndarray,
        volumes: np.ndarray,
        num_samples: int = 10
    ) -> ActiveLearningResult:
        """Select most informative samples."""
        try:
            if len(prices) < 30:
                return self._create_empty_result()
        
            # Extract features for all samples
            features = self._extract_all_features(prices, volumes)
        
            # Calculate acquisition scores
            samples = []
            for i in range(len(features)):
                if i not in self.labeled_indices:
                    uncertainty = self._calculate_uncertainty(features[i])
                    diversity = self._calculate_diversity(features[i], features)
                    acquisition = self._acquisition_function(uncertainty, diversity)
                
                    samples.append(Sample(
                        index=i,
                        features=features[i],
                        uncertainty=uncertainty,
                        diversity_score=diversity,
                        acquisition_score=acquisition
                    ))
        
            # Sort by acquisition score
            samples.sort(key=lambda s: s.acquisition_score, reverse=True)
            selected = samples[:num_samples]
        
            # Calculate metrics
            model_uncertainty = np.mean([s.uncertainty for s in samples]) if samples else 0
            coverage = len(self.labeled_indices) / len(features) if features.size > 0 else 0
            expected_imp = np.mean([s.acquisition_score for s in selected]) if selected else 0
        
            signal = self._generate_signal(model_uncertainty, coverage)
        
            return ActiveLearningResult(
                samples_to_label=selected,
                model_uncertainty=model_uncertainty,
                coverage_score=coverage,
                expected_improvement=expected_imp,
                trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in select_samples: {e}")
            raise
    
    def _extract_all_features(self, prices: np.ndarray, volumes: np.ndarray) -> np.ndarray:
        """Extract features for all time windows."""
        try:
            window = 20
            features = []
            for i in range(window, len(prices)):
                f = self._extract_window_features(prices[i-window:i], volumes[i-window:i])
                features.append(f)
            return np.array(features) if features else np.array([])
        except Exception as e:
            logger.error(f"Error in _extract_all_features: {e}")
            raise
    
    def _extract_window_features(self, prices: np.ndarray, volumes: np.ndarray) -> np.ndarray:
        """Extract features from a window."""
        try:
            returns = np.diff(prices) / prices[:-1]
            return np.array([
                np.mean(returns), np.std(returns),
                np.min(returns), np.max(returns),
                prices[-1] / prices[0] - 1,
                np.mean(volumes) / (np.max(volumes) + 1e-10),
            ])
        except Exception as e:
            logger.error(f"Error in _extract_window_features: {e}")
            raise
    
    def _calculate_uncertainty(self, features: np.ndarray) -> float:
        """Calculate prediction uncertainty for a sample."""
        # Simplified: use feature variance as proxy
        return float(np.std(features))
    
    def _calculate_diversity(self, features: np.ndarray, all_features: np.ndarray) -> float:
        """Calculate diversity score (distance from labeled samples)."""
        try:
            if len(self.labeled_indices) == 0:
                return 1.0
        
            labeled_features = all_features[self.labeled_indices]
            distances = np.linalg.norm(labeled_features - features, axis=1)
            return float(np.min(distances)) if len(distances) > 0 else 1.0
        except Exception as e:
            logger.error(f"Error in _calculate_diversity: {e}")
            raise
    
    def _acquisition_function(self, uncertainty: float, diversity: float) -> float:
        """Compute acquisition score."""
        try:
            if self.strategy == 'uncertainty':
                return uncertainty
            elif self.strategy == 'diversity':
                return diversity
            else:  # combined
                return 0.5 * uncertainty + 0.5 * diversity
        except Exception as e:
            logger.error(f"Error in _acquisition_function: {e}")
            raise
    
    def label_sample(self, index: int):
        """Mark a sample as labeled."""
        try:
            if index not in self.labeled_indices:
                self.labeled_indices.append(index)
        except Exception as e:
            logger.error(f"Error in label_sample: {e}")
            raise
    
    def _generate_signal(self, uncertainty: float, coverage: float) -> str:
        """Generate signal based on model state."""
        try:
            if uncertainty > 0.5:
                return f"HIGH UNCERTAINTY ({uncertainty:.2f}): Need more labeled data"
            elif coverage < 0.1:
                return f"LOW COVERAGE ({coverage:.0%}): Collect more diverse samples"
            return f"MODEL READY: Uncertainty {uncertainty:.2f}, Coverage {coverage:.0%}"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _create_empty_result(self) -> ActiveLearningResult:
        """Create empty result."""
        return ActiveLearningResult([], 0, 0, 0, "Insufficient data")
