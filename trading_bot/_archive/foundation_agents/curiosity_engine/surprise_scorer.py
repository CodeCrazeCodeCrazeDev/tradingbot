"""
Surprise Scorer - Information-Theoretic Surprise Metrics
=========================================================

Implements surprise quantification using information theory:
1. Shannon Surprise: -log(P(event))
2. Bayesian Surprise: KL divergence between prior and posterior
3. Prediction Error: Difference from expected values
4. Novelty Score: How different from past experiences

Based on the Foundation Agents paper (arXiv:2504.01990) curiosity systems.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import deque

logger = logging.getLogger(__name__)


class SurpriseType(Enum):
    """Types of surprise metrics"""
    SHANNON = "shannon"              # Information-theoretic surprise
    BAYESIAN = "bayesian"            # KL divergence surprise
    PREDICTION_ERROR = "prediction_error"  # Prediction-based surprise
    NOVELTY = "novelty"              # Novelty-based surprise
    COMPOSITE = "composite"          # Combined surprise score


@dataclass
class SurpriseMetric:
    """A surprise measurement"""
    metric_id: str
    surprise_type: SurpriseType
    value: float  # Surprise value (higher = more surprising)
    
    # Context
    event_description: str
    observed: Any
    expected: Optional[Any] = None
    
    # Probability estimates
    prior_probability: Optional[float] = None
    posterior_probability: Optional[float] = None
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'metric_id': self.metric_id,
            'surprise_type': self.surprise_type.value,
            'value': self.value,
            'event_description': self.event_description,
            'prior_probability': self.prior_probability,
            'timestamp': self.timestamp.isoformat()
        }


class ProbabilityEstimator:
    """Estimates probabilities for surprise calculation"""
    
    def __init__(self, num_bins: int = 20):
        self.num_bins = num_bins
        self.distributions: Dict[str, Dict] = {}
    
    def update_distribution(self, variable: str, value: float):
        """Update the distribution estimate for a variable"""
        if variable not in self.distributions:
            self.distributions[variable] = {
                'values': deque(maxlen=1000),
                'histogram': None,
                'bin_edges': None
            }
        
        self.distributions[variable]['values'].append(value)
        
        # Rebuild histogram periodically
        values = list(self.distributions[variable]['values'])
        if len(values) >= 50:
            hist, edges = np.histogram(values, bins=self.num_bins, density=True)
            self.distributions[variable]['histogram'] = hist
            self.distributions[variable]['bin_edges'] = edges
    
    def estimate_probability(self, variable: str, value: float) -> float:
        """Estimate probability of a value"""
        if variable not in self.distributions:
            return 0.5  # Uniform prior
        
        dist = self.distributions[variable]
        if dist['histogram'] is None:
            return 0.5
        
        # Find bin
        edges = dist['bin_edges']
        hist = dist['histogram']
        
        bin_idx = np.searchsorted(edges[:-1], value) - 1
        bin_idx = max(0, min(bin_idx, len(hist) - 1))
        
        # Get probability density
        density = hist[bin_idx]
        bin_width = edges[1] - edges[0]
        
        # Convert to probability (approximate)
        probability = density * bin_width
        
        # Ensure valid probability
        return max(0.001, min(0.999, probability))
    
    def get_distribution_stats(self, variable: str) -> Dict[str, float]:
        """Get statistics for a variable's distribution"""
        if variable not in self.distributions:
            return {}
        
        values = list(self.distributions[variable]['values'])
        if not values:
            return {}
        
        return {
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'median': np.median(values)
        }


class ShannonSurprise:
    """Shannon information-theoretic surprise: -log(P(event))"""
    
    def __init__(self, probability_estimator: ProbabilityEstimator):
        self.prob_estimator = probability_estimator
    
    def compute(self, variable: str, value: float) -> float:
        """Compute Shannon surprise"""
        probability = self.prob_estimator.estimate_probability(variable, value)
        
        # Shannon surprise: -log2(P)
        surprise = -np.log2(probability)
        
        return surprise


class BayesianSurprise:
    """Bayesian surprise: KL divergence between prior and posterior"""
    
    def __init__(self):
        self.priors: Dict[str, Dict[str, float]] = {}
    
    def set_prior(self, variable: str, mean: float, std: float):
        """Set prior distribution parameters"""
        self.priors[variable] = {'mean': mean, 'std': std}
    
    def compute(
        self,
        variable: str,
        observed_value: float,
        likelihood_std: float = 1.0
    ) -> Tuple[float, Dict[str, float]]:
        """
        Compute Bayesian surprise using conjugate Gaussian update
        
        Returns surprise value and posterior parameters
        """
        if variable not in self.priors:
            # Use uninformative prior
            self.priors[variable] = {'mean': 0.0, 'std': 10.0}
        
        prior = self.priors[variable]
        prior_mean = prior['mean']
        prior_std = prior['std']
        
        # Bayesian update (Gaussian conjugate)
        prior_var = prior_std ** 2
        likelihood_var = likelihood_std ** 2
        
        posterior_var = 1 / (1/prior_var + 1/likelihood_var)
        posterior_mean = posterior_var * (prior_mean/prior_var + observed_value/likelihood_var)
        posterior_std = np.sqrt(posterior_var)
        
        # KL divergence between prior and posterior (both Gaussian)
        kl_divergence = (
            np.log(prior_std / posterior_std) +
            (posterior_std**2 + (posterior_mean - prior_mean)**2) / (2 * prior_std**2) -
            0.5
        )
        
        # Update prior for next time
        self.priors[variable] = {'mean': posterior_mean, 'std': posterior_std}
        
        posterior = {'mean': posterior_mean, 'std': posterior_std}
        
        return max(0, kl_divergence), posterior


class PredictionErrorSurprise:
    """Surprise based on prediction errors"""
    
    def __init__(self):
        self.predictions: Dict[str, deque] = {}
        self.errors: Dict[str, deque] = {}
    
    def record_prediction(self, variable: str, predicted: float, actual: float):
        """Record a prediction and its error"""
        if variable not in self.predictions:
            self.predictions[variable] = deque(maxlen=100)
            self.errors[variable] = deque(maxlen=100)
        
        error = actual - predicted
        self.predictions[variable].append(predicted)
        self.errors[variable].append(error)
    
    def compute(self, variable: str, predicted: float, actual: float) -> float:
        """Compute surprise based on prediction error"""
        self.record_prediction(variable, predicted, actual)
        
        errors = list(self.errors.get(variable, []))
        if len(errors) < 10:
            # Not enough history, use simple error
            return abs(actual - predicted)
        
        # Normalize by historical error distribution
        error = actual - predicted
        mean_error = np.mean(errors)
        std_error = np.std(errors)
        
        if std_error == 0:
            return abs(error)
        
        # Z-score of error
        z_error = abs(error - mean_error) / std_error
        
        return z_error


class NoveltySurprise:
    """Novelty-based surprise using state similarity"""
    
    def __init__(self, memory_size: int = 1000):
        self.memory: deque = deque(maxlen=memory_size)
        self.state_counts: Dict[str, int] = {}
    
    def _hash_state(self, state: Dict[str, Any]) -> str:
        """Create a hash for a state"""
        # Discretize continuous values
        discretized = {}
        for key, value in state.items():
            if isinstance(value, (int, float)):
                # Discretize to bins
                discretized[key] = round(value, 1)
            else:
                discretized[key] = str(value)
        
        return str(sorted(discretized.items()))
    
    def compute(self, state: Dict[str, Any]) -> float:
        """Compute novelty surprise for a state"""
        state_hash = self._hash_state(state)
        
        # Count-based novelty
        count = self.state_counts.get(state_hash, 0)
        self.state_counts[state_hash] = count + 1
        
        # Novelty decreases with familiarity
        novelty = 1.0 / (1 + np.sqrt(count))
        
        # Also compute distance-based novelty
        if self.memory:
            # Simple feature-based distance
            distances = []
            for past_state in list(self.memory)[-100:]:
                dist = self._state_distance(state, past_state)
                distances.append(dist)
            
            min_distance = min(distances) if distances else 1.0
            distance_novelty = min(1.0, min_distance)
            
            # Combine count and distance novelty
            novelty = 0.5 * novelty + 0.5 * distance_novelty
        
        self.memory.append(state)
        
        return novelty
    
    def _state_distance(self, state1: Dict, state2: Dict) -> float:
        """Compute distance between two states"""
        common_keys = set(state1.keys()) & set(state2.keys())
        
        if not common_keys:
            return 1.0
        
        distances = []
        for key in common_keys:
            v1, v2 = state1[key], state2[key]
            
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                # Normalize by typical range
                diff = abs(v1 - v2)
                distances.append(min(1.0, diff))
            elif v1 != v2:
                distances.append(1.0)
            else:
                distances.append(0.0)
        
        return np.mean(distances) if distances else 1.0


class SurpriseScorer:
    """
    Surprise Scorer
    
    Central system for computing surprise metrics.
    Combines multiple surprise measures for comprehensive assessment.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Probability estimator
        self.prob_estimator = ProbabilityEstimator(
            num_bins=self.config.get('num_bins', 20)
        )
        
        # Surprise calculators
        self.shannon = ShannonSurprise(self.prob_estimator)
        self.bayesian = BayesianSurprise()
        self.prediction_error = PredictionErrorSurprise()
        self.novelty = NoveltySurprise(
            memory_size=self.config.get('memory_size', 1000)
        )
        
        # History
        self.surprise_history: deque = deque(maxlen=10000)
        
        # Statistics
        self.stats = {
            'total_computed': 0,
            'avg_surprise': 0.0,
            'max_surprise': 0.0,
            'by_type': {st.value: [] for st in SurpriseType}
        }
        
        logger.info("Surprise Scorer initialized")
    
    def update_distribution(self, variable: str, value: float):
        """Update probability distribution for a variable"""
        self.prob_estimator.update_distribution(variable, value)
    
    def compute_shannon_surprise(
        self,
        variable: str,
        value: float,
        description: str = ""
    ) -> SurpriseMetric:
        """Compute Shannon surprise for an observation"""
        self.update_distribution(variable, value)
        
        surprise_value = self.shannon.compute(variable, value)
        probability = self.prob_estimator.estimate_probability(variable, value)
        
        metric = SurpriseMetric(
            metric_id=f"shannon_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            surprise_type=SurpriseType.SHANNON,
            value=surprise_value,
            event_description=description or f"Observed {variable}={value}",
            observed=value,
            prior_probability=probability
        )
        
        self._record_metric(metric)
        return metric
    
    def compute_bayesian_surprise(
        self,
        variable: str,
        value: float,
        description: str = ""
    ) -> SurpriseMetric:
        """Compute Bayesian surprise for an observation"""
        surprise_value, posterior = self.bayesian.compute(variable, value)
        
        metric = SurpriseMetric(
            metric_id=f"bayesian_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            surprise_type=SurpriseType.BAYESIAN,
            value=surprise_value,
            event_description=description or f"Bayesian update for {variable}",
            observed=value,
            metadata={'posterior': posterior}
        )
        
        self._record_metric(metric)
        return metric
    
    def compute_prediction_surprise(
        self,
        variable: str,
        predicted: float,
        actual: float,
        description: str = ""
    ) -> SurpriseMetric:
        """Compute surprise based on prediction error"""
        surprise_value = self.prediction_error.compute(variable, predicted, actual)
        
        metric = SurpriseMetric(
            metric_id=f"pred_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            surprise_type=SurpriseType.PREDICTION_ERROR,
            value=surprise_value,
            event_description=description or f"Prediction error for {variable}",
            observed=actual,
            expected=predicted,
            metadata={'error': actual - predicted}
        )
        
        self._record_metric(metric)
        return metric
    
    def compute_novelty_surprise(
        self,
        state: Dict[str, Any],
        description: str = ""
    ) -> SurpriseMetric:
        """Compute novelty-based surprise for a state"""
        surprise_value = self.novelty.compute(state)
        
        metric = SurpriseMetric(
            metric_id=f"novelty_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            surprise_type=SurpriseType.NOVELTY,
            value=surprise_value,
            event_description=description or "State novelty",
            observed=state
        )
        
        self._record_metric(metric)
        return metric
    
    def compute_composite_surprise(
        self,
        variable: str,
        value: float,
        predicted: Optional[float] = None,
        state: Optional[Dict] = None,
        description: str = ""
    ) -> SurpriseMetric:
        """Compute composite surprise combining multiple metrics"""
        components = {}
        
        # Shannon surprise
        self.update_distribution(variable, value)
        shannon_surprise = self.shannon.compute(variable, value)
        components['shannon'] = shannon_surprise
        
        # Bayesian surprise
        bayesian_surprise, _ = self.bayesian.compute(variable, value)
        components['bayesian'] = bayesian_surprise
        
        # Prediction error surprise
        if predicted is not None:
            pred_surprise = self.prediction_error.compute(variable, predicted, value)
            components['prediction'] = pred_surprise
        
        # Novelty surprise
        if state is not None:
            novelty_surprise = self.novelty.compute(state)
            components['novelty'] = novelty_surprise
        
        # Weighted combination
        weights = {
            'shannon': 0.3,
            'bayesian': 0.3,
            'prediction': 0.25,
            'novelty': 0.15
        }
        
        total_weight = sum(weights[k] for k in components.keys())
        composite = sum(
            components[k] * weights[k] / total_weight
            for k in components.keys()
        )
        
        metric = SurpriseMetric(
            metric_id=f"composite_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            surprise_type=SurpriseType.COMPOSITE,
            value=composite,
            event_description=description or f"Composite surprise for {variable}",
            observed=value,
            expected=predicted,
            metadata={'components': components}
        )
        
        self._record_metric(metric)
        return metric
    
    def _record_metric(self, metric: SurpriseMetric):
        """Record a surprise metric"""
        self.surprise_history.append(metric)
        self.stats['total_computed'] += 1
        
        # Update running statistics
        values = [m.value for m in self.surprise_history]
        self.stats['avg_surprise'] = np.mean(values)
        self.stats['max_surprise'] = max(self.stats['max_surprise'], metric.value)
        
        # Track by type
        self.stats['by_type'][metric.surprise_type.value].append(metric.value)
        if len(self.stats['by_type'][metric.surprise_type.value]) > 100:
            self.stats['by_type'][metric.surprise_type.value] = \
                self.stats['by_type'][metric.surprise_type.value][-100:]
    
    def get_surprise_threshold(self, percentile: float = 95) -> float:
        """Get surprise threshold at given percentile"""
        values = [m.value for m in self.surprise_history]
        if not values:
            return 1.0
        return np.percentile(values, percentile)
    
    def is_surprising(
        self,
        metric: SurpriseMetric,
        threshold_percentile: float = 90
    ) -> bool:
        """Check if a metric represents a surprising event"""
        threshold = self.get_surprise_threshold(threshold_percentile)
        return metric.value > threshold
    
    def get_most_surprising(self, n: int = 10) -> List[SurpriseMetric]:
        """Get the most surprising events"""
        sorted_metrics = sorted(
            self.surprise_history,
            key=lambda m: m.value,
            reverse=True
        )
        return sorted_metrics[:n]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get surprise statistics"""
        type_stats = {}
        for st, values in self.stats['by_type'].items():
            if values:
                type_stats[st] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'max': np.max(values)
                }
        
        return {
            'total_computed': self.stats['total_computed'],
            'avg_surprise': self.stats['avg_surprise'],
            'max_surprise': self.stats['max_surprise'],
            'by_type': type_stats,
            'threshold_90': self.get_surprise_threshold(90),
            'threshold_95': self.get_surprise_threshold(95)
        }
