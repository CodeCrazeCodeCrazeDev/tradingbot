"""
Temporal Prediction Mesh with Quantum-Inspired Forecasting
Multi-timescale probabilistic forecasting with wave function evolution
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
try:
    from scipy import signal as scipy_signal
except ImportError:
    scipy = None
from scipy.fft import fft, ifft
import pywt  # Wavelet transforms
import numpy
import pandas

logger = logging.getLogger(__name__)


class Timeframe(Enum):
    """Trading timeframes"""
    MICROSECOND = "microsecond"
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class ProbabilityWave:
    """Quantum-inspired probability wave function"""
    amplitudes: np.ndarray  # Complex amplitudes
    outcomes: np.ndarray  # Possible outcomes (price levels)
    timeframe: Timeframe
    timestamp: datetime = field(default_factory=datetime.now)
    
    def collapse(self) -> Tuple[float, float]:
        """Collapse wave function to most probable outcome"""
        probabilities = np.abs(self.amplitudes) ** 2
        probabilities /= probabilities.sum()  # Normalize
        
        expected_value = np.sum(self.outcomes * probabilities)
        variance = np.sum((self.outcomes - expected_value) ** 2 * probabilities)
        
        return expected_value, np.sqrt(variance)
    
    def get_probability_distribution(self) -> Dict[float, float]:
        """Get probability distribution over outcomes"""
        probabilities = np.abs(self.amplitudes) ** 2
        probabilities /= probabilities.sum()
        
        return {float(outcome): float(prob) 
                for outcome, prob in zip(self.outcomes, probabilities)}


@dataclass
class TemporalPrediction:
    """Prediction for a specific timeframe"""
    timeframe: Timeframe
    expected_value: float
    confidence_interval: Tuple[float, float]
    probability_distribution: Dict[float, float]
    hurst_exponent: float
    dominant_cycle: Optional[float]
    signal_quality: float  # 0-1
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MultiScaleForecast:
    """Complete multi-timescale forecast"""
    predictions: Dict[Timeframe, TemporalPrediction]
    synchronized_entry_windows: List[Tuple[datetime, datetime]]
    optimal_timeframe: Timeframe
    conviction: float
    synthesis: str
    timestamp: datetime = field(default_factory=datetime.now)


class SignalDecomposer:
    """Advanced signal decomposition using multiple methods"""
    
    def __init__(self):
        self.wavelet_family = 'db4'  # Daubechies wavelet
        
    def fourier_decomposition(self, data: np.ndarray, 
                             sampling_rate: float = 1.0) -> Dict[str, Any]:
        """Decompose signal into frequency components"""
        
        # FFT
        fft_values = fft(data)
        frequencies = np.fft.fftfreq(len(data), 1/sampling_rate)
        
        # Power spectrum
        power = np.abs(fft_values) ** 2
        
        # Find dominant frequencies
        positive_freq_idx = frequencies > 0
        dominant_idx = np.argsort(power[positive_freq_idx])[-5:]  # Top 5
        dominant_freqs = frequencies[positive_freq_idx][dominant_idx]
        dominant_powers = power[positive_freq_idx][dominant_idx]
        
        # Convert to periods
        dominant_periods = 1 / dominant_freqs
        
        return {
            'frequencies': frequencies,
            'power_spectrum': power,
            'dominant_frequencies': dominant_freqs,
            'dominant_periods': dominant_periods,
            'dominant_powers': dominant_powers
        }
    
    def wavelet_decomposition(self, data: np.ndarray, 
                             levels: int = 5) -> Dict[str, Any]:
        """Multi-resolution wavelet decomposition"""
        
        # Discrete wavelet transform
        coeffs = pywt.wavedec(data, self.wavelet_family, level=levels)
        
        # Reconstruct at each level
        reconstructions = []
        for i in range(len(coeffs)):
            # Zero out all coefficients except level i
            coeffs_copy = [np.zeros_like(c) for c in coeffs]
            coeffs_copy[i] = coeffs[i]
            reconstruction = pywt.waverec(coeffs_copy, self.wavelet_family)
            reconstructions.append(reconstruction[:len(data)])
        
        return {
            'coefficients': coeffs,
            'reconstructions': reconstructions,
            'levels': levels,
            'approximation': coeffs[0],
            'details': coeffs[1:]
        }
    
    def calculate_hurst_exponent(self, data: np.ndarray) -> float:
        """
        Calculate Hurst exponent
        H < 0.5: Mean-reverting
        H = 0.5: Random walk
        H > 0.5: Trending
        """
        
        lags = range(2, min(100, len(data) // 2))
        tau = []
        
        for lag in lags:
            # Calculate standard deviation of differences
            diff = data[lag:] - data[:-lag]
            tau.append(np.std(diff))
        
        # Log-log regression
        lags_log = np.log(list(lags))
        tau_log = np.log(tau)
        
        # Fit line
        poly = np.polyfit(lags_log, tau_log, 1)
        hurst = poly[0]
        
        return float(hurst)
    
    def detect_regime_changes(self, data: np.ndarray, 
                             window: int = 50) -> List[int]:
        """Detect structural breaks in time series"""
        
        changes = []
        
        for i in range(window, len(data) - window):
            # Compare statistics before and after
            before = data[i-window:i]
            after = data[i:i+window]
            
            # Mean shift
            mean_shift = abs(np.mean(after) - np.mean(before)) / np.std(data)
            
            # Volatility shift
            vol_shift = abs(np.std(after) - np.std(before)) / np.std(data)
            
            # If significant shift detected
            if mean_shift > 2.0 or vol_shift > 1.5:
                changes.append(i)
        
        return changes


class QuantumForecaster:
    """Quantum-inspired probabilistic forecasting"""
    
    def __init__(self, n_outcomes: int = 100):
        self.n_outcomes = n_outcomes
        
    def create_probability_wave(self, current_price: float, 
                               volatility: float,
                               trend: float,
                               timeframe: Timeframe) -> ProbabilityWave:
        """Create quantum probability wave for future price"""
        
        # Define outcome space (possible future prices)
        price_range = volatility * 3  # 3 sigma
        outcomes = np.linspace(current_price - price_range, 
                              current_price + price_range, 
                              self.n_outcomes)
        
        # Initialize wave function
        amplitudes = np.zeros(self.n_outcomes, dtype=complex)
        
        # Base distribution (Gaussian around current price + trend)
        expected_price = current_price + trend
        for i, outcome in enumerate(outcomes):
            # Gaussian amplitude
            amplitude = np.exp(-((outcome - expected_price) ** 2) / (2 * volatility ** 2))
            
            # Add phase (represents momentum/trend direction)
            phase = np.arctan2(trend, volatility) if volatility > 0 else 0
            
            amplitudes[i] = amplitude * np.exp(1j * phase)
        
        # Normalize
        norm = np.sqrt(np.sum(np.abs(amplitudes) ** 2))
        if norm > 0:
            amplitudes /= norm
        
        return ProbabilityWave(
            amplitudes=amplitudes,
            outcomes=outcomes,
            timeframe=timeframe
        )
    
    def evolve_wave_function(self, wave: ProbabilityWave, 
                            time_steps: int,
                            market_forces: Dict[str, float]) -> ProbabilityWave:
        """Evolve wave function forward in time"""
        
        # Extract market forces
        momentum = market_forces.get('momentum', 0.0)
        mean_reversion = market_forces.get('mean_reversion', 0.0)
        volatility_expansion = market_forces.get('volatility_expansion', 0.0)
        
        amplitudes = wave.amplitudes.copy()
        
        for _ in range(time_steps):
            # Apply evolution operators
            
            # Momentum operator (shifts distribution)
            if momentum != 0:
                shift = int(momentum * len(amplitudes) * 0.1)
                amplitudes = np.roll(amplitudes, shift)
            
            # Mean reversion operator (contracts distribution)
            if mean_reversion > 0:
                center_idx = len(amplitudes) // 2
                for i in range(len(amplitudes)):
                    distance = abs(i - center_idx)
                    amplitudes[i] *= (1 + mean_reversion * distance / len(amplitudes))
            
            # Volatility operator (expands distribution)
            if volatility_expansion > 0:
                # Diffusion
                amplitudes_new = amplitudes.copy()
                for i in range(1, len(amplitudes) - 1):
                    amplitudes_new[i] += volatility_expansion * (
                        amplitudes[i-1] + amplitudes[i+1] - 2*amplitudes[i]
                    )
                amplitudes = amplitudes_new
            
            # Renormalize
            norm = np.sqrt(np.sum(np.abs(amplitudes) ** 2))
            if norm > 0:
                amplitudes /= norm
        
        return ProbabilityWave(
            amplitudes=amplitudes,
            outcomes=wave.outcomes,
            timeframe=wave.timeframe
        )
    
    def calculate_interference(self, waves: List[ProbabilityWave]) -> ProbabilityWave:
        """Calculate interference pattern from multiple waves"""
        
        if not waves:
            raise ValueError("Need at least one wave")
        
        # All waves must have same outcome space
        outcomes = waves[0].outcomes
        
        # Superposition: Add amplitudes
        total_amplitude = np.zeros(len(outcomes), dtype=complex)
        
        for wave in waves:
            # Ensure compatible outcome spaces
            if not np.allclose(wave.outcomes, outcomes):
                # Interpolate to common grid
                amplitude_interp = np.interp(outcomes, wave.outcomes, 
                                            np.abs(wave.amplitudes))
                phase_interp = np.interp(outcomes, wave.outcomes,
                                        np.angle(wave.amplitudes))
                amplitude = amplitude_interp * np.exp(1j * phase_interp)
            else:
                amplitude = wave.amplitudes
            
            total_amplitude += amplitude
        
        # Normalize
        norm = np.sqrt(np.sum(np.abs(total_amplitude) ** 2))
        if norm > 0:
            total_amplitude /= norm
        
        return ProbabilityWave(
            amplitudes=total_amplitude,
            outcomes=outcomes,
            timeframe=waves[0].timeframe
        )


class TemporalPredictionMesh:
    """
    Multi-timescale forecasting system with quantum-inspired probability evolution
    """
    
    def __init__(self):
        self.decomposer = SignalDecomposer()
        self.quantum_forecaster = QuantumForecaster()
        self.prediction_history: Dict[Timeframe, List[TemporalPrediction]] = {}
        
    def analyze_timeseries(self, data: pd.Series) -> Dict[str, Any]:
        """Comprehensive time series analysis"""
        
        values = data.values
        
        # Fourier analysis
        fourier = self.decomposer.fourier_decomposition(values)
        
        # Wavelet analysis
        wavelet = self.decomposer.wavelet_decomposition(values)
        
        # Hurst exponent
        hurst = self.decomposer.calculate_hurst_exponent(values)
        
        # Regime changes
        regime_changes = self.decomposer.detect_regime_changes(values)
        
        return {
            'fourier': fourier,
            'wavelet': wavelet,
            'hurst_exponent': hurst,
            'regime_changes': regime_changes,
            'trend_strength': self._calculate_trend_strength(values),
            'mean_reversion_strength': self._calculate_mean_reversion(values, hurst)
        }
    
    def _calculate_trend_strength(self, data: np.ndarray) -> float:
        """Calculate trend strength (0-1)"""
        if len(data) < 2:
            return 0.0
        
        # Linear regression slope
        x = np.arange(len(data))
        slope, _ = np.polyfit(x, data, 1)
        
        # Normalize by volatility
        volatility = np.std(data)
        if volatility > 0:
            trend_strength = abs(slope * len(data)) / volatility
            return min(trend_strength / 2, 1.0)  # Cap at 1.0
        return 0.0
    
    def _calculate_mean_reversion(self, data: np.ndarray, hurst: float) -> float:
        """Calculate mean reversion strength (0-1)"""
        # Hurst < 0.5 indicates mean reversion
        if hurst < 0.5:
            return (0.5 - hurst) * 2  # Scale to 0-1
        return 0.0
    
    def forecast_timeframe(self, data: pd.Series, 
                          timeframe: Timeframe,
                          horizon: int = 1) -> TemporalPrediction:
        """Generate forecast for specific timeframe"""
        
        # Analyze time series
        analysis = self.analyze_timeseries(data)
        
        current_price = data.iloc[-1]
        volatility = data.std()
        
        # Calculate trend
        trend = self._calculate_trend_strength(data.values) * volatility
        if data.iloc[-1] < data.iloc[0]:
            trend *= -1
        
        # Create probability wave
        wave = self.quantum_forecaster.create_probability_wave(
            current_price=current_price,
            volatility=volatility,
            trend=trend,
            timeframe=timeframe
        )
        
        # Evolve wave function
        market_forces = {
            'momentum': analysis['trend_strength'],
            'mean_reversion': analysis['mean_reversion_strength'],
            'volatility_expansion': 0.1 if volatility > data.rolling(20).std().mean() else 0.0
        }
        
        evolved_wave = self.quantum_forecaster.evolve_wave_function(
            wave, horizon, market_forces
        )
        
        # Collapse to prediction
        expected_value, std_dev = evolved_wave.collapse()
        
        # Confidence interval (95%)
        confidence_interval = (
            expected_value - 1.96 * std_dev,
            expected_value + 1.96 * std_dev
        )
        
        # Get probability distribution
        prob_dist = evolved_wave.get_probability_distribution()
        
        # Signal quality based on Hurst and analysis
        hurst = analysis['hurst_exponent']
        if abs(hurst - 0.5) > 0.2:  # Strong trend or mean reversion
            signal_quality = min(abs(hurst - 0.5) * 2, 1.0)
        else:
            signal_quality = 0.3  # Random walk
        
        # Dominant cycle
        dominant_cycle = None
        if analysis['fourier']['dominant_periods'].size > 0:
            dominant_cycle = float(analysis['fourier']['dominant_periods'][0])
        
        prediction = TemporalPrediction(
            timeframe=timeframe,
            expected_value=expected_value,
            confidence_interval=confidence_interval,
            probability_distribution=prob_dist,
            hurst_exponent=hurst,
            dominant_cycle=dominant_cycle,
            signal_quality=signal_quality
        )
        
        # Store in history
        if timeframe not in self.prediction_history:
            self.prediction_history[timeframe] = []
        self.prediction_history[timeframe].append(prediction)
        
        return prediction
    
    def multi_scale_forecast(self, data: pd.Series,
                            timeframes: Optional[List[Timeframe]] = None) -> MultiScaleForecast:
        """Generate forecasts across multiple timeframes"""
        
        if timeframes is None:
            timeframes = [
                Timeframe.MINUTE,
                Timeframe.HOUR,
                Timeframe.DAILY,
                Timeframe.WEEKLY
            ]
        
        # Generate prediction for each timeframe
        predictions = {}
        for tf in timeframes:
            # Adjust horizon based on timeframe
            horizon_map = {
                Timeframe.MINUTE: 5,
                Timeframe.HOUR: 4,
                Timeframe.DAILY: 5,
                Timeframe.WEEKLY: 4
            }
            horizon = horizon_map.get(tf, 1)
            
            predictions[tf] = self.forecast_timeframe(data, tf, horizon)
        
        # Find optimal timeframe (highest signal quality)
        optimal_tf = max(predictions.items(), 
                        key=lambda x: x[1].signal_quality)[0]
        
        # Identify synchronized entry windows
        entry_windows = self._find_synchronized_windows(predictions)
        
        # Calculate overall conviction
        conviction = self._calculate_multi_scale_conviction(predictions)
        
        # Generate synthesis
        synthesis = self._synthesize_forecast(predictions, optimal_tf)
        
        return MultiScaleForecast(
            predictions=predictions,
            synchronized_entry_windows=entry_windows,
            optimal_timeframe=optimal_tf,
            conviction=conviction,
            synthesis=synthesis
        )
    
    def _find_synchronized_windows(self, 
                                  predictions: Dict[Timeframe, TemporalPrediction]) -> List[Tuple[datetime, datetime]]:
        """Find time windows where multiple timeframes align"""
        
        windows = []
        
        # Check if predictions agree on direction
        directions = []
        for pred in predictions.values():
            if pred.expected_value > 0:
                directions.append(1)
            elif pred.expected_value < 0:
                directions.append(-1)
            else:
                directions.append(0)
        
        # If majority agree, create entry window
        if abs(sum(directions)) >= len(directions) * 0.6:
            # Window is now + next hour (simplified)
            start = datetime.now()
            end = start + timedelta(hours=1)
            windows.append((start, end))
        
        return windows
    
    def _calculate_multi_scale_conviction(self, 
                                         predictions: Dict[Timeframe, TemporalPrediction]) -> float:
        """Calculate conviction based on multi-timeframe alignment"""
        
        # Weight by signal quality
        total_quality = sum(p.signal_quality for p in predictions.values())
        
        if total_quality == 0:
            return 0.0
        
        # Check alignment
        weighted_direction = 0.0
        for pred in predictions.values():
            direction = np.sign(pred.expected_value)
            weighted_direction += direction * pred.signal_quality
        
        # Normalize
        conviction = abs(weighted_direction) / total_quality
        
        return conviction * 100  # 0-100 scale
    
    def _synthesize_forecast(self, predictions: Dict[Timeframe, TemporalPrediction],
                            optimal_tf: Timeframe) -> str:
        """Generate narrative synthesis of multi-scale forecast"""
        
        parts = []
        
        # Overall direction
        optimal_pred = predictions[optimal_tf]
        direction = "BULLISH" if optimal_pred.expected_value > 0 else "BEARISH"
        parts.append(f"Multi-timeframe analysis: {direction}")
        
        # Optimal timeframe
        parts.append(f"Optimal timeframe: {optimal_tf.value}")
        parts.append(f"Signal quality: {optimal_pred.signal_quality:.2f}")
        
        # Hurst interpretation
        hurst = optimal_pred.hurst_exponent
        if hurst > 0.6:
            parts.append(f"Strong trending behavior (H={hurst:.2f})")
        elif hurst < 0.4:
            parts.append(f"Mean-reverting behavior (H={hurst:.2f})")
        else:
            parts.append(f"Random walk behavior (H={hurst:.2f})")
        
        # Cycle information
        if optimal_pred.dominant_cycle:
            parts.append(f"Dominant cycle: {optimal_pred.dominant_cycle:.1f} periods")
        
        return ". ".join(parts)


# Example usage
if __name__ == "__main__":
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=1000, freq='1H')
    
    # Simulate price with trend + cycles + noise
    t = np.arange(1000)
    trend = 0.05 * t
    cycle1 = 10 * np.sin(2 * np.pi * t / 50)  # 50-period cycle
    cycle2 = 5 * np.sin(2 * np.pi * t / 20)   # 20-period cycle
    noise = np.random.randn(1000) * 2
    
    price = 100 + trend + cycle1 + cycle2 + noise
    data = pd.Series(price, index=dates)
    
    # Initialize mesh
    mesh = TemporalPredictionMesh()
    
    # Multi-scale forecast
    forecast = mesh.multi_scale_forecast(data)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"MULTI-SCALE TEMPORAL FORECAST")
    logger.info(f"{'='*80}")
    logger.info(f"\nOptimal Timeframe: {forecast.optimal_timeframe.value}")
    logger.info(f"Conviction: {forecast.conviction:.1f}%")
    logger.info(f"\nSynthesis: {forecast.synthesis}")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"TIMEFRAME PREDICTIONS")
    logger.info(f"{'='*80}")
    
    for tf, pred in forecast.predictions.items():
        logger.info(f"\n{tf.value.upper()}:")
        logger.info(f"  Expected Value: {pred.expected_value:.2f}")
        logger.info(f"  95% CI: [{pred.confidence_interval[0]:.2f}, {pred.confidence_interval[1]:.2f}]")
        logger.info(f"  Hurst Exponent: {pred.hurst_exponent:.3f}")
        logger.info(f"  Signal Quality: {pred.signal_quality:.2f}")
        if pred.dominant_cycle:
            logger.info(f"  Dominant Cycle: {pred.dominant_cycle:.1f} periods")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"SYNCHRONIZED ENTRY WINDOWS")
    logger.info(f"{'='*80}")
    
    for start, end in forecast.synchronized_entry_windows:
        logger.info(f"  {start} to {end}")
