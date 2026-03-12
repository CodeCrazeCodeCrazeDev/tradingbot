"""
Advanced Statistical Indicators
Cointegration, Z-Score, Kalman Filter, HMM, Copula Models
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
try:
    from scipy import stats
except ImportError:
    scipy = None
from scipy.optimize import minimize
import logging
import numpy
import pandas

logger = logging.getLogger(__name__)


class CointegrationAnalyzer:
    """
    Cointegration Analysis
    Detects statistically linked assets for pairs trading
    """
    
    def __init__(self, significance_level: float = 0.05):
        self.significance_level = significance_level
        self.cointegrated_pairs = []
        
    def engle_granger_test(self, y: pd.Series, x: pd.Series) -> Dict[str, float]:
        """Perform Engle-Granger cointegration test."""
        # Step 1: Run regression
        X = np.column_stack([np.ones(len(x)), x.values])
        beta = np.linalg.lstsq(X, y.values, rcond=None)[0]
        
        # Step 2: Calculate residuals
        residuals = y.values - (beta[0] + beta[1] * x.values)
        
        # Step 3: ADF test on residuals
        adf_stat, p_value = self._adf_test(residuals)
        
        # Step 4: Calculate half-life
        half_life = self._calculate_half_life(residuals)
        
        return {
            'adf_statistic': adf_stat,
            'p_value': p_value,
            'is_cointegrated': p_value < self.significance_level,
            'beta': beta[1],
            'half_life': half_life,
            'spread_mean': np.mean(residuals),
            'spread_std': np.std(residuals)
        }
    
    def _adf_test(self, series: np.ndarray) -> Tuple[float, float]:
        """Augmented Dickey-Fuller test (simplified)."""
        n = len(series)
        lagged = series[:-1]
        diff = np.diff(series)
        
        # Regression: diff = alpha + beta*lagged + error
        X = np.column_stack([np.ones(n-1), lagged])
        beta = np.linalg.lstsq(X, diff, rcond=None)[0]
        
        # Calculate t-statistic
        residuals = diff - (beta[0] + beta[1] * lagged)
        std_error = np.sqrt(np.sum(residuals**2) / (n - 3))
        t_stat = beta[1] / (std_error / np.sqrt(np.sum((lagged - lagged.mean())**2)))
        
        # Approximate p-value (simplified)
        p_value = 1 - stats.norm.cdf(abs(t_stat))
        
        return t_stat, p_value
    
    def _calculate_half_life(self, spread: np.ndarray) -> float:
        """Calculate mean reversion half-life."""
        lagged = spread[:-1]
        diff = np.diff(spread)
        
        # Regression: diff = alpha + beta*lagged
        X = np.column_stack([np.ones(len(lagged)), lagged])
        beta = np.linalg.lstsq(X, diff, rcond=None)[0]
        
        # Half-life = -log(2) / log(1 + beta)
        if beta[1] < 0:
            half_life = -np.log(2) / np.log(1 + beta[1])
        else:
            half_life = np.inf
        
        return half_life
    
    def find_cointegrated_pairs(self, price_data: pd.DataFrame) -> List[Dict]:
        """Find all cointegrated pairs in a dataset."""
        pairs = []
        symbols = price_data.columns
        
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                sym1, sym2 = symbols[i], symbols[j]
                
                result = self.engle_granger_test(
                    price_data[sym1],
                    price_data[sym2]
                )
                
                if result['is_cointegrated']:
                    pairs.append({
                        'pair': (sym1, sym2),
                        'adf_stat': result['adf_statistic'],
                        'p_value': result['p_value'],
                        'beta': result['beta'],
                        'half_life': result['half_life']
                    })
        
        self.cointegrated_pairs = pairs
        return pairs


class ZScoreReversionModel:
    """
    Z-Score Reversion Models
    For mean-reversion trading signals
    """
    
    def __init__(self, lookback: int = 20, entry_threshold: float = 2.0, 
                 exit_threshold: float = 0.5):
        self.lookback = lookback
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        
    def calculate_zscore(self, series: pd.Series, window: Optional[int] = None) -> pd.Series:
        """Calculate rolling z-score."""
        window = window or self.lookback
        
        rolling_mean = series.rolling(window=window).mean()
        rolling_std = series.rolling(window=window).std()
        
        zscore = (series - rolling_mean) / rolling_std
        return zscore
    
    def generate_signals(self, spread: pd.Series) -> pd.DataFrame:
        """Generate mean-reversion trading signals."""
        zscore = self.calculate_zscore(spread)
        
        signals = pd.DataFrame(index=spread.index)
        signals['zscore'] = zscore
        signals['position'] = 0
        
        # Entry signals
        signals.loc[zscore > self.entry_threshold, 'position'] = -1  # Short
        signals.loc[zscore < -self.entry_threshold, 'position'] = 1   # Long
        
        # Exit signals
        signals.loc[abs(zscore) < self.exit_threshold, 'position'] = 0
        
        # Forward fill positions
        signals['position'] = signals['position'].replace(0, np.nan).fillna(method='ffill').fillna(0)
        
        return signals
    
    def calculate_bollinger_zscore(self, series: pd.Series, 
                                   window: int = 20, num_std: float = 2.0) -> Dict[str, pd.Series]:
        """Calculate Bollinger Band-based z-score."""
        rolling_mean = series.rolling(window=window).mean()
        rolling_std = series.rolling(window=window).std()
        
        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)
        
        # Normalized position within bands
        band_width = upper_band - lower_band
        position = (series - lower_band) / band_width
        
        return {
            'upper_band': upper_band,
            'lower_band': lower_band,
            'middle_band': rolling_mean,
            'position': position,
            'zscore': (series - rolling_mean) / rolling_std
        }


class KalmanFilterTrendline:
    """
    Kalman Filter Adaptive Trendline
    Dynamic trend smoothing with noise reduction
    """
    
    def __init__(self, process_variance: float = 0.01, 
                 measurement_variance: float = 0.1,
                 initial_estimate: Optional[float] = None):
        self.Q = process_variance  # Process variance
        self.R = measurement_variance  # Measurement variance
        self.initial_estimate = initial_estimate
        
    def filter(self, measurements: pd.Series) -> pd.DataFrame:
        """Apply Kalman filter to measurements."""
        n = len(measurements)
        
        # Initialize arrays
        filtered_state = np.zeros(n)
        predicted_state = np.zeros(n)
        error_covariance = np.zeros(n)
        kalman_gain = np.zeros(n)
        
        # Initial values
        if self.initial_estimate is not None:
            filtered_state[0] = self.initial_estimate
        else:
            filtered_state[0] = measurements.iloc[0]
        
        error_covariance[0] = 1.0
        
        for i in range(1, n):
            # Prediction step
            predicted_state[i] = filtered_state[i-1]
            predicted_covariance = error_covariance[i-1] + self.Q
            
            # Update step
            kalman_gain[i] = predicted_covariance / (predicted_covariance + self.R)
            filtered_state[i] = predicted_state[i] + kalman_gain[i] * (measurements.iloc[i] - predicted_state[i])
            error_covariance[i] = (1 - kalman_gain[i]) * predicted_covariance
        
        result = pd.DataFrame({
            'filtered': filtered_state,
            'predicted': predicted_state,
            'kalman_gain': kalman_gain,
            'error_covariance': error_covariance,
            'innovation': measurements.values - predicted_state
        }, index=measurements.index)
        
        return result
    
    def adaptive_filter(self, measurements: pd.Series) -> pd.Series:
        """Adaptive Kalman filter with dynamic variance adjustment."""
        filtered = self.filter(measurements)
        
        # Adjust process variance based on innovation
        innovation_std = filtered['innovation'].rolling(20).std()
        
        # Re-filter with adaptive variance
        adaptive_filtered = []
        P = 1.0
        x = measurements.iloc[0]
        
        for i in range(len(measurements)):
            # Adaptive Q based on recent innovation
            Q_adaptive = self.Q * (1 + innovation_std.iloc[i] if not pd.isna(innovation_std.iloc[i]) else 1)
            
            # Prediction
            x_pred = x
            P_pred = P + Q_adaptive
            
            # Update
            K = P_pred / (P_pred + self.R)
            x = x_pred + K * (measurements.iloc[i] - x_pred)
            P = (1 - K) * P_pred
            
            adaptive_filtered.append(x)
        
        return pd.Series(adaptive_filtered, index=measurements.index)


class HiddenMarkovRegime:
    """
    Hidden Markov Models for Regime Classification
    Probabilistic market state detection
    """
    
    def __init__(self, n_states: int = 3, n_iterations: int = 100):
        self.n_states = n_states
        self.n_iterations = n_iterations
        self.state_names = ['bull', 'bear', 'neutral'][:n_states]
        
        # Model parameters
        self.transition_matrix = None
        self.emission_means = None
        self.emission_stds = None
        self.initial_probs = None
        
    def fit(self, returns: pd.Series):
        """Fit HMM to return series using EM algorithm (simplified)."""
        n = len(returns)
        
        # Initialize parameters
        self.transition_matrix = np.ones((self.n_states, self.n_states)) / self.n_states
        self.initial_probs = np.ones(self.n_states) / self.n_states
        
        # Initialize emission parameters
        quantiles = np.linspace(0, 1, self.n_states + 1)
        self.emission_means = np.array([
            returns.quantile(quantiles[i:i+2].mean())
            for i in range(self.n_states)
        ])
        self.emission_stds = np.ones(self.n_states) * returns.std()
        
        # EM iterations (simplified)
        for iteration in range(self.n_iterations):
            # E-step: Calculate state probabilities
            state_probs = self._forward_backward(returns.values)
            
            # M-step: Update parameters
            self._update_parameters(returns.values, state_probs)
    
    def _forward_backward(self, observations: np.ndarray) -> np.ndarray:
        """Forward-backward algorithm (simplified)."""
        n = len(observations)
        state_probs = np.zeros((n, self.n_states))
        
        # Forward pass
        for t in range(n):
            for s in range(self.n_states):
                # Emission probability
                emission_prob = stats.norm.pdf(
                    observations[t],
                    self.emission_means[s],
                    self.emission_stds[s]
                )
                
                if t == 0:
                    state_probs[t, s] = self.initial_probs[s] * emission_prob
                else:
                    state_probs[t, s] = emission_prob * np.sum(
                        state_probs[t-1] * self.transition_matrix[:, s]
                    )
            
            # Normalize
            if state_probs[t].sum() > 0:
                state_probs[t] /= state_probs[t].sum()
        
        return state_probs
    
    def _update_parameters(self, observations: np.ndarray, state_probs: np.ndarray):
        """Update HMM parameters (M-step)."""
        # Update emission parameters
        for s in range(self.n_states):
            weights = state_probs[:, s]
            if weights.sum() > 0:
                self.emission_means[s] = np.average(observations, weights=weights)
                self.emission_stds[s] = np.sqrt(
                    np.average((observations - self.emission_means[s])**2, weights=weights)
                )
    
    def predict_regime(self, returns: pd.Series) -> pd.DataFrame:
        """Predict regime for each time point."""
        state_probs = self._forward_backward(returns.values)
        
        result = pd.DataFrame(state_probs, index=returns.index, columns=self.state_names)
        result['predicted_regime'] = result.idxmax(axis=1)
        result['confidence'] = result.max(axis=1)
        
        return result


class AdvancedStatisticalIndicators:
    """Unified interface for advanced statistical indicators."""
    
    def __init__(self):
        self.cointegration = CointegrationAnalyzer()
        self.zscore_model = ZScoreReversionModel()
        self.kalman = KalmanFilterTrendline()
        self.hmm = HiddenMarkovRegime()
        
        logger.info("✅ Advanced Statistical Indicators initialized")
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, any]:
        """Comprehensive statistical analysis."""
        results = {}
        
        try:
            # Z-Score analysis
            zscore = self.zscore_model.calculate_zscore(df['close'])
            results['zscore'] = zscore.iloc[-1] if len(zscore) > 0 else 0.0
            results['zscore_signal'] = 'OVERBOUGHT' if results['zscore'] > 2 else 'OVERSOLD' if results['zscore'] < -2 else 'NEUTRAL'
            
            # Kalman filter trend
            kalman_result = self.kalman.filter(df['close'])
            results['kalman_trend'] = kalman_result['filtered'].iloc[-1]
            results['kalman_innovation'] = kalman_result['innovation'].iloc[-1]
            
            # HMM regime detection
            returns = df['close'].pct_change().dropna()
            if len(returns) > 50:
                self.hmm.fit(returns)
                regime = self.hmm.predict_regime(returns)
                results['current_regime'] = regime['predicted_regime'].iloc[-1]
                results['regime_confidence'] = regime['confidence'].iloc[-1]
            
            logger.info("✅ Statistical analysis complete")
            
        except Exception as e:
            logger.error(f"❌ Error in statistical analysis: {e}")
        
        return results


# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=500, freq='1H')
    np.random.seed(42)
    
    df = pd.DataFrame({
        'close': np.random.randn(500).cumsum() + 100
    }, index=dates)
    
    # Initialize indicators
    stats_indicators = AdvancedStatisticalIndicators()
    
    # Analyze
    results = stats_indicators.analyze(df)
    
    logger.info("\n=== Advanced Statistical Analysis ===")
    logger.info(f"Z-Score: {results['zscore']:.2f}")
    logger.info(f"Signal: {results['zscore_signal']}")
    logger.info(f"Kalman Trend: {results['kalman_trend']:.2f}")
    logger.info(f"Regime: {results.get('current_regime', 'N/A')}")
    logger.info(f"Confidence: {results.get('regime_confidence', 0):.2%}")
