"""
Advanced ML Indicators
Meta-Learning, RARL, Transformers, Adaptive Ensemble, HMM, Copula Models
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
try:
    from scipy import stats
except ImportError:
    scipy = None
from sklearn.preprocessing import StandardScaler
from collections import deque
import numpy
import pandas

logger = logging.getLogger(__name__)


@dataclass
class MLSignal:
    """Machine learning signal output."""
    timestamp: pd.Timestamp
    signal_type: str
    probability: float
    confidence: float
    features: Dict[str, float]
    shap_values: Optional[Dict[str, float]] = None
    regime: Optional[str] = None


class MetaLearner:
    """
    Meta-Learning System
    AI learns how to learn - improves models automatically
    """
    
    def __init__(self, base_models: List[str] = None):
        self.base_models = base_models or ['rl', 'cnn', 'lstm', 'gbm']
        self.performance_history = {model: deque(maxlen=100) for model in self.base_models}
        self.model_weights = {model: 1.0 / len(self.base_models) for model in self.base_models}
        self.learning_rate = 0.01
        
    def update_weights(self, model_predictions: Dict[str, float], 
                      actual_outcome: float) -> Dict[str, float]:
        """Update model weights based on performance."""
        for model, prediction in model_predictions.items():
            error = abs(prediction - actual_outcome)
            self.performance_history[model].append(1.0 - error)
            
            # Calculate recent performance
            recent_perf = np.mean(list(self.performance_history[model]))
            
            # Update weight using gradient descent
            self.model_weights[model] += self.learning_rate * (recent_perf - 0.5)
        
        # Normalize weights
        total_weight = sum(self.model_weights.values())
        self.model_weights = {k: v / total_weight for k, v in self.model_weights.items()}
        
        return self.model_weights
    
    def get_ensemble_prediction(self, model_predictions: Dict[str, float]) -> float:
        """Get weighted ensemble prediction."""
        prediction = sum(
            self.model_weights[model] * pred 
            for model, pred in model_predictions.items()
        )
        return prediction


class RegimeAwareRL:
    """
    Regime-Aware Reinforcement Learning (RARL)
    RL agent changes policy based on detected regime
    """
    
    def __init__(self):
        self.regimes = ['trending', 'ranging', 'volatile', 'calm']
        self.policies = {regime: self._initialize_policy() for regime in self.regimes}
        self.current_regime = 'ranging'
        self.regime_history = deque(maxlen=100)
        
    def _initialize_policy(self) -> Dict[str, float]:
        """Initialize policy parameters."""
        return {
            'aggression': 0.5,
            'risk_tolerance': 0.5,
            'holding_period': 10,
            'take_profit': 0.02,
            'stop_loss': 0.01
        }
    
    def detect_regime(self, df: pd.DataFrame) -> str:
        """Detect current market regime."""
        # Calculate regime indicators
        returns = df['close'].pct_change()
        volatility = returns.std()
        
        # ADX for trend strength
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        
        # Classify regime
        if volatility > volatility.rolling(50).mean() * 1.5:
            regime = 'volatile'
        elif volatility < volatility.rolling(50).mean() * 0.5:
            regime = 'calm'
        elif atr.iloc[-1] > atr.rolling(50).mean().iloc[-1]:
            regime = 'trending'
        else:
            regime = 'ranging'
        
        self.current_regime = regime
        self.regime_history.append(regime)
        
        return regime
    
    def get_action(self, state: np.ndarray, regime: Optional[str] = None) -> Dict[str, float]:
        """Get action based on current regime policy."""
        regime = regime or self.current_regime
        policy = self.policies[regime]
        
        # Apply policy to state
        action = {
            'position_size': policy['aggression'] * policy['risk_tolerance'],
            'take_profit': policy['take_profit'],
            'stop_loss': policy['stop_loss'],
            'holding_period': policy['holding_period']
        }
        
        return action
    
    def update_policy(self, regime: str, reward: float):
        """Update policy based on reward."""
        policy = self.policies[regime]
        
        # Simple policy gradient update
        learning_rate = 0.01
        
        if reward > 0:
            policy['aggression'] = min(1.0, policy['aggression'] + learning_rate)
            policy['risk_tolerance'] = min(1.0, policy['risk_tolerance'] + learning_rate * 0.5)
        else:
            policy['aggression'] = max(0.1, policy['aggression'] - learning_rate)
            policy['risk_tolerance'] = max(0.1, policy['risk_tolerance'] - learning_rate * 0.5)


class ExplainableAI:
    """
    Explainable AI using SHAP-like values
    Makes AI decisions interpretable
    """
    
    def __init__(self):
        self.feature_importance = {}
        self.baseline_values = {}
        
    def calculate_shap_values(self, features: Dict[str, float], 
                             prediction: float) -> Dict[str, float]:
        """Calculate SHAP-like feature contributions."""
        shap_values = {}
        
        for feature_name, feature_value in features.items():
            # Get baseline
            baseline = self.baseline_values.get(feature_name, 0.0)
            
            # Calculate contribution (simplified SHAP)
            contribution = (feature_value - baseline) * self.feature_importance.get(feature_name, 0.1)
            shap_values[feature_name] = contribution
        
        # Normalize to sum to prediction
        total_contribution = sum(abs(v) for v in shap_values.values())
        if total_contribution > 0:
            scale = prediction / total_contribution
            shap_values = {k: v * scale for k, v in shap_values.items()}
        
        return shap_values
    
    def update_importance(self, features: Dict[str, float], outcome: float):
        """Update feature importance based on outcomes."""
        for feature_name, feature_value in features.items():
            # Update baseline
            if feature_name not in self.baseline_values:
                self.baseline_values[feature_name] = feature_value
            else:
                self.baseline_values[feature_name] = 0.9 * self.baseline_values[feature_name] + 0.1 * feature_value
            
            # Update importance
            correlation = feature_value * outcome
            if feature_name not in self.feature_importance:
                self.feature_importance[feature_name] = abs(correlation)
            else:
                self.feature_importance[feature_name] = 0.9 * self.feature_importance[feature_name] + 0.1 * abs(correlation)


class TransformerPredictor:
    """
    Self-Attention Transformer for time-series
    Simplified implementation for financial data
    """
    
    def __init__(self, sequence_length: int = 50, d_model: int = 64):
        self.sequence_length = sequence_length
        self.d_model = d_model
        self.attention_weights = None
        
    def attention(self, query: np.ndarray, key: np.ndarray, 
                 value: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Scaled dot-product attention."""
        d_k = query.shape[-1]
        scores = np.matmul(query, key.T) / np.sqrt(d_k)
        attention_weights = self._softmax(scores)
        output = np.matmul(attention_weights, value)
        return output, attention_weights
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Softmax function."""
        exp_x = np.exp(x - np.max(x))
        return exp_x / exp_x.sum(axis=-1, keepdims=True)
    
    def predict(self, sequence: np.ndarray) -> Tuple[float, np.ndarray]:
        """
        Predict next value using self-attention.
        Returns: (prediction, attention_weights)
        """
        # Simplified transformer prediction
        query = sequence[-1:].reshape(1, -1)
        key = sequence.reshape(len(sequence), -1)
        value = sequence.reshape(len(sequence), -1)
        
        output, attention_weights = self.attention(query, key, value)
        self.attention_weights = attention_weights
        
        # Simple prediction: weighted average
        prediction = np.sum(output)
        
        return prediction, attention_weights


class AdaptiveEnsemble:
    """
    Adaptive Ensemble Blending
    Dynamic weighting of RL + CNN + Gradient Boosting
    """
    
    def __init__(self):
        self.models = {
            'rl': {'weight': 0.33, 'performance': deque(maxlen=50)},
            'cnn': {'weight': 0.33, 'performance': deque(maxlen=50)},
            'gbm': {'weight': 0.34, 'performance': deque(maxlen=50)}
        }
        self.adaptation_rate = 0.05
        
    def predict(self, model_outputs: Dict[str, float]) -> float:
        """Get ensemble prediction with dynamic weights."""
        prediction = sum(
            self.models[model]['weight'] * output
            for model, output in model_outputs.items()
        )
        return prediction
    
    def update_weights(self, model_outputs: Dict[str, float], actual: float):
        """Update model weights based on performance."""
        # Calculate errors
        errors = {
            model: abs(output - actual)
            for model, output in model_outputs.items()
        }
        
        # Update performance history
        for model, error in errors.items():
            accuracy = 1.0 - min(error, 1.0)
            self.models[model]['performance'].append(accuracy)
        
        # Calculate new weights based on recent performance
        performances = {
            model: np.mean(list(data['performance'])) if data['performance'] else 0.5
            for model, data in self.models.items()
        }
        
        # Softmax weighting
        exp_perfs = {k: np.exp(v * 5) for k, v in performances.items()}
        total = sum(exp_perfs.values())
        new_weights = {k: v / total for k, v in exp_perfs.items()}
        
        # Smooth update
        for model in self.models:
            old_weight = self.models[model]['weight']
            new_weight = new_weights[model]
            self.models[model]['weight'] = (1 - self.adaptation_rate) * old_weight + self.adaptation_rate * new_weight
        
        return self.models


class HiddenMarkovModel:
    """
    Hidden Markov Model for regime classification
    Probabilistic state detection
    """
    
    def __init__(self, n_states: int = 3):
        self.n_states = n_states
        self.states = ['bull', 'bear', 'neutral'][:n_states]
        self.transition_matrix = np.ones((n_states, n_states)) / n_states
        self.emission_params = {}
        
    def fit(self, observations: np.ndarray):
        """Fit HMM to observations (simplified EM algorithm)."""
        # Initialize emission parameters
        for i, state in enumerate(self.states):
            state_obs = observations[i:self.n_states]
            self.emission_params[state] = {
                'mean': np.mean(state_obs),
                'std': np.std(state_obs)
            }
    
    def predict_state(self, observation: float) -> Tuple[str, float]:
        """Predict most likely state given observation."""
        likelihoods = {}
        
        for state in self.states:
            params = self.emission_params[state]
            # Gaussian likelihood
            likelihood = stats.norm.pdf(observation, params['mean'], params['std'])
            likelihoods[state] = likelihood
        
        # Get most likely state
        total = sum(likelihoods.values())
        if total > 0:
            probs = {k: v / total for k, v in likelihoods.items()}
        else:
            probs = {k: 1.0 / len(self.states) for k in self.states}
        
        best_state = max(probs, key=probs.get)
        confidence = probs[best_state]
        
        return best_state, confidence


class CopulaModel:
    """
    Copula-based dependency modeling
    Captures nonlinear correlations between assets
    """
    
    def __init__(self, copula_type: str = 'gaussian'):
        self.copula_type = copula_type
        self.correlation_matrix = None
        
    def fit(self, returns_df: pd.DataFrame):
        """Fit copula to returns data."""
        # Transform to uniform marginals using empirical CDF
        uniform_data = returns_df.rank() / (len(returns_df) + 1)
        
        # Estimate correlation structure
        self.correlation_matrix = uniform_data.corr()
        
    def sample_dependent_returns(self, n_samples: int = 1000) -> pd.DataFrame:
        """Generate correlated samples using copula."""
        if self.correlation_matrix is None:
            raise ValueError("Model not fitted")
        
        # Generate correlated normal samples
        mean = np.zeros(len(self.correlation_matrix))
        samples = np.random.multivariate_normal(
            mean, self.correlation_matrix.values, n_samples
        )
        
        # Transform to uniform using normal CDF
        uniform_samples = stats.norm.cdf(samples)
        
        return pd.DataFrame(uniform_samples, columns=self.correlation_matrix.columns)
    
    def tail_dependence(self) -> Dict[str, float]:
        """Calculate tail dependence coefficients."""
        # Simplified tail dependence
        tail_deps = {}
        cols = self.correlation_matrix.columns
        
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                corr = self.correlation_matrix.iloc[i, j]
                # Gaussian copula tail dependence (simplified)
                tail_dep = 2 * stats.norm.cdf(-np.sqrt((1 - corr) / (1 + corr)))
                tail_deps[f"{cols[i]}_{cols[j]}"] = tail_dep
        
        return tail_deps


class AdvancedMLIndicators:
    """Unified interface for advanced ML indicators."""
    
    def __init__(self):
        self.meta_learner = MetaLearner()
        self.rarl = RegimeAwareRL()
        self.explainable_ai = ExplainableAI()
        self.transformer = TransformerPredictor()
        self.ensemble = AdaptiveEnsemble()
        self.hmm = HiddenMarkovModel()
        self.copula = CopulaModel()
        
        logger.info("✅ Advanced ML Indicators initialized")
    
    def generate_signal(self, df: pd.DataFrame, features: Dict[str, float]) -> MLSignal:
        """Generate comprehensive ML signal."""
        # Detect regime
        regime = self.rarl.detect_regime(df)
        
        # Get model predictions
        model_predictions = {
            'rl': 0.6,  # Placeholder - would come from actual RL model
            'cnn': 0.65,
            'lstm': 0.55,
            'gbm': 0.7
        }
        
        # Meta-learning ensemble
        ensemble_pred = self.meta_learner.get_ensemble_prediction(model_predictions)
        
        # Adaptive ensemble
        adaptive_pred = self.ensemble.predict(model_predictions)
        
        # Transformer prediction
        sequence = df['close'].tail(50).values
        transformer_pred, attention = self.transformer.predict(sequence)
        
        # Combine predictions
        final_probability = (ensemble_pred + adaptive_pred) / 2
        
        # Calculate SHAP values
        shap_values = self.explainable_ai.calculate_shap_values(features, final_probability)
        
        # Calculate confidence
        confidence = 1.0 - np.std([ensemble_pred, adaptive_pred, transformer_pred])
        
        signal = MLSignal(
            timestamp=df.index[-1],
            signal_type='BUY' if final_probability > 0.5 else 'SELL',
            probability=final_probability,
            confidence=confidence,
            features=features,
            shap_values=shap_values,
            regime=regime
        )
        
        return signal


# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=200, freq='1H')
    df = pd.DataFrame({
        'open': np.random.randn(200).cumsum() + 100,
        'high': np.random.randn(200).cumsum() + 102,
        'low': np.random.randn(200).cumsum() + 98,
        'close': np.random.randn(200).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 200)
    }, index=dates)
    
    # Initialize indicators
    ml_indicators = AdvancedMLIndicators()
    
    # Generate signal
    features = {
        'rsi': 65.0,
        'macd': 0.5,
        'volume_ratio': 1.2,
        'volatility': 0.02
    }
    
    signal = ml_indicators.generate_signal(df, features)
    
    logger.info("\n=== Advanced ML Signal ===")
    logger.info(f"Signal: {signal.signal_type}")
    logger.info(f"Probability: {signal.probability:.2%}")
    logger.info(f"Confidence: {signal.confidence:.2%}")
    logger.info(f"Regime: {signal.regime}")
    logger.info(f"\nSHAP Values:")
    for feature, value in signal.shap_values.items():
        logger.info(f"  {feature}: {value:.4f}")
