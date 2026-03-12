"""
DeepChart Confidence & Strategy View Engine

Combines:
- Model Disagreement Heatmap (Concept 10)
- Information Flow Speedometer (Concept 13)
- Strategy-Specific Views (Concept 14)
- Confidence-Weighted Overlays (Concept 15)

Produces confidence-weighted visualizations that fade by uncertainty.

Math:
    disagreement = variance(model_predictions)
    confidence_adjusted = base_confidence × (1 - disagreement)
    opacity = min(1, confidence / threshold)
    
    discovery_efficiency = |Δp_informed| / |Δp_total|
    information_share = correlation(price, fundamental_value)

Performance Budget:
    - Update: O(N_models) per tick
    - Memory: O(N_overlays)
    - Latency: <0.5ms per update
"""

import numpy as np
from collections import deque
from typing import Dict, List, Optional, Any
import time
import logging

from .market_intelligence_core import (
    ModelDisagreement,
    InformationFlowState,
    StrategyView,
    StrategyLens,
    ConfidenceWeightedOverlay,
    MarketIntelligenceConfig,
)

logger = logging.getLogger(__name__)


class ModelDisagreementTracker:
    """
    Tracks disagreement between multiple models.
    
    High disagreement = high uncertainty = fade overlays.
    """
    
    def __init__(self, config: MarketIntelligenceConfig):
        self.config = config
        self._model_predictions: Dict[str, deque] = {}
        self._disagreement_history = deque(maxlen=100)
        self._bar_count = 0
    
    def update(self, predictions: Dict[str, float]) -> ModelDisagreement:
        """
        Update model disagreement metrics.
        
        Args:
            predictions: Dict of model_name -> prediction value
            
        Returns:
            ModelDisagreement with uncertainty metrics
        """
        self._bar_count += 1
        
        # Store predictions
        for model_name, pred in predictions.items():
            if model_name not in self._model_predictions:
                self._model_predictions[model_name] = deque(maxlen=100)
            self._model_predictions[model_name].append(pred)
        
        if len(predictions) < 2:
            return self._create_default_disagreement(predictions)
        
        # Calculate disagreement metrics
        pred_values = list(predictions.values())
        
        # Variance
        variance = np.var(pred_values)
        
        # Entropy of prediction distribution
        entropy = self._calculate_entropy(pred_values)
        
        # Overall disagreement score
        disagreement_score = self._calculate_disagreement(pred_values)
        self._disagreement_history.append(disagreement_score)
        
        # Confidence adjusted for disagreement
        base_confidence = 1 - variance
        confidence_adjusted = base_confidence * (1 - disagreement_score)
        
        return ModelDisagreement(
            disagreement_score=disagreement_score,
            model_predictions=predictions,
            variance=variance,
            entropy=entropy,
            confidence_adjusted=max(0, min(1, confidence_adjusted))
        )
    
    def _calculate_disagreement(self, predictions: List[float]) -> float:
        """
        Calculate disagreement score.
        
        Based on coefficient of variation and range.
        """
        if len(predictions) < 2:
            return 0.0
        
        mean = np.mean(predictions)
        std = np.std(predictions)
        
        # Coefficient of variation
        cv = std / (abs(mean) + 1e-8)
        
        # Range relative to mean
        range_rel = (max(predictions) - min(predictions)) / (abs(mean) + 1e-8)
        
        # Combined score
        return min(1.0, cv * 0.5 + range_rel * 0.5)
    
    def _calculate_entropy(self, predictions: List[float]) -> float:
        """
        Calculate entropy of prediction distribution.
        
        Discretize predictions and compute Shannon entropy.
        """
        if len(predictions) < 2:
            return 0.0
        
        # Discretize to 10 bins
        pred_min, pred_max = min(predictions), max(predictions)
        if pred_max - pred_min < 1e-8:
            return 0.0
        
        bins = np.linspace(pred_min, pred_max, 11)
        hist, _ = np.histogram(predictions, bins=bins)
        
        # Normalize
        probs = hist / np.sum(hist)
        
        # Shannon entropy
        entropy = 0.0
        for p in probs:
            if p > 0:
                entropy -= p * np.log(p)
        
        return entropy
    
    def get_average_disagreement(self) -> float:
        """Get average disagreement over recent history."""
        if not self._disagreement_history:
            return 0.5
        return np.mean(self._disagreement_history)
    
    def _create_default_disagreement(self, predictions: Dict[str, float]) -> ModelDisagreement:
        """Create default disagreement for insufficient models."""
        return ModelDisagreement(
            disagreement_score=0.5,
            model_predictions=predictions,
            variance=0.0,
            entropy=0.0,
            confidence_adjusted=0.5
        )
    
    def reset(self):
        """Reset tracker state."""
        self._model_predictions.clear()
        self._disagreement_history.clear()
        self._bar_count = 0


class InformationFlowEngine:
    """
    Tracks information flow and price discovery efficiency.
    
    Measures how efficiently price incorporates new information.
    """
    
    def __init__(self, config: MarketIntelligenceConfig):
        self.config = config
        self._price_history = deque(maxlen=500)
        self._volume_history = deque(maxlen=500)
        self._return_history = deque(maxlen=200)
        self._bar_count = 0
    
    def update(self, price: float, volume: float) -> InformationFlowState:
        """
        Update information flow state.
        
        Args:
            price: Current price
            volume: Trade volume
            
        Returns:
            InformationFlowState with discovery metrics
        """
        self._bar_count += 1
        self._price_history.append(price)
        self._volume_history.append(volume)
        
        if len(self._price_history) >= 2:
            ret = (price - self._price_history[-2]) / self._price_history[-2]
            self._return_history.append(ret)
        
        if len(self._price_history) < 50:
            return self._create_default_state()
        
        # Discovery efficiency
        discovery_efficiency = self._calculate_discovery_efficiency()
        
        # Information share
        information_share = self._calculate_information_share()
        
        # Lead-lag score
        lead_lag = self._calculate_lead_lag()
        
        # Noise ratio
        noise_ratio = self._calculate_noise_ratio()
        
        # Speed of adjustment
        speed = self._calculate_speed_of_adjustment()
        
        # Information asymmetry
        asymmetry = self._calculate_information_asymmetry()
        
        return InformationFlowState(
            discovery_efficiency=discovery_efficiency,
            information_share=information_share,
            lead_lag_score=lead_lag,
            noise_ratio=noise_ratio,
            speed_of_adjustment=speed,
            information_asymmetry=asymmetry
        )
    
    def _calculate_discovery_efficiency(self) -> float:
        """
        Calculate price discovery efficiency.
        
        Efficiency = |net_move| / total_path_length
        """
        if len(self._price_history) < 20:
            return 0.5
        
        prices = np.array(self._price_history)[-20:]
        
        # Net move
        net_move = abs(prices[-1] - prices[0])
        
        # Total path length
        path_length = np.sum(np.abs(np.diff(prices)))
        
        if path_length < 1e-8:
            return 1.0
        
        return min(1.0, net_move / path_length)
    
    def _calculate_information_share(self) -> float:
        """
        Calculate information share.
        
        Based on variance ratio test.
        """
        if len(self._return_history) < 50:
            return 0.5
        
        returns = np.array(self._return_history)
        
        # Variance ratio: var(k-period returns) / (k × var(1-period returns))
        k = 5
        if len(returns) < k * 2:
            return 0.5
        
        var_1 = np.var(returns)
        
        # k-period returns
        k_returns = []
        for i in range(0, len(returns) - k, k):
            k_returns.append(np.sum(returns[i:i+k]))
        
        if len(k_returns) < 5:
            return 0.5
        
        var_k = np.var(k_returns)
        
        # Variance ratio
        vr = var_k / (k * var_1 + 1e-8)
        
        # VR close to 1 = efficient
        return max(0, 1 - abs(1 - vr))
    
    def _calculate_lead_lag(self) -> float:
        """
        Calculate lead-lag score.
        
        Positive = leading, negative = lagging.
        """
        if len(self._return_history) < 20:
            return 0.0
        
        returns = np.array(self._return_history)
        
        # Autocorrelation at lag 1
        if len(returns) < 3:
            return 0.0
        try:
        
            autocorr = np.corrcoef(returns[:-1], returns[1:])[0, 1]
            if np.isnan(autocorr):
                return 0.0
            return float(autocorr)
        except Exception as e:
            logger.error(f"Error: {e}")
            return 0.0
    
    def _calculate_noise_ratio(self) -> float:
        """
        Calculate noise ratio in price discovery.
        
        High frequency variance / low frequency variance.
        """
        if len(self._return_history) < 50:
            return 0.5
        
        returns = np.array(self._return_history)
        
        # High frequency variance (1-bar)
        var_hf = np.var(returns)
        
        # Low frequency variance (10-bar)
        lf_returns = []
        for i in range(0, len(returns) - 10, 10):
            lf_returns.append(np.sum(returns[i:i+10]))
        
        if len(lf_returns) < 3:
            return 0.5
        
        var_lf = np.var(lf_returns) / 10
        
        # Noise ratio
        if var_lf < 1e-8:
            return 1.0
        
        return min(1.0, var_hf / var_lf - 1)
    
    def _calculate_speed_of_adjustment(self) -> float:
        """
        Calculate speed of adjustment to new information.
        
        Based on how quickly price moves after volume spike.
        """
        if len(self._volume_history) < 20:
            return 0.5
        
        volumes = np.array(self._volume_history)
        prices = np.array(self._price_history)
        
        # Find volume spikes
        vol_mean = np.mean(volumes)
        vol_std = np.std(volumes)
        
        spikes = volumes > vol_mean + vol_std
        
        if np.sum(spikes) < 3:
            return 0.5
        
        # Calculate price move after spikes
        moves_after_spike = []
        for i in range(len(spikes) - 5):
            if spikes[i]:
                move = abs(prices[i+5] - prices[i]) / prices[i]
                moves_after_spike.append(move)
        
        if not moves_after_spike:
            return 0.5
        
        # Higher moves = faster adjustment
        return min(1.0, np.mean(moves_after_spike) * 100)
    
    def _calculate_information_asymmetry(self) -> float:
        """
        Calculate degree of information asymmetry.
        
        Based on volume-price relationship.
        """
        if len(self._volume_history) < 50:
            return 0.5
        
        volumes = np.array(self._volume_history)[-50:]
        returns = np.array(self._return_history)[-50:] if len(self._return_history) >= 50 else np.zeros(50)
        
        if len(returns) < len(volumes):
            returns = np.concatenate([np.zeros(len(volumes) - len(returns)), returns])
        try:
        
        # Correlation between volume and absolute returns
            corr = np.corrcoef(volumes, np.abs(returns))[0, 1]
            if np.isnan(corr):
                return 0.5
            return abs(corr)
        except Exception as e:
            logger.error(f"Error: {e}")
            return 0.5
    
    def _create_default_state(self) -> InformationFlowState:
        """Create default state for insufficient data."""
        return InformationFlowState(
            discovery_efficiency=0.5,
            information_share=0.5,
            lead_lag_score=0.0,
            noise_ratio=0.5,
            speed_of_adjustment=0.5,
            information_asymmetry=0.5
        )
    
    def reset(self):
        """Reset engine state."""
        self._price_history.clear()
        self._volume_history.clear()
        self._return_history.clear()
        self._bar_count = 0


class StrategyViewEngine:
    """
    Generates strategy-specific views of market state.
    
    Same data, different lens for different trading strategies.
    """
    
    def __init__(self, config: MarketIntelligenceConfig):
        self.config = config
        self._price_history = deque(maxlen=200)
        self._volume_history = deque(maxlen=200)
        self._bar_count = 0
    
    def update(self, price: float, volume: float, 
               latent_state: Any = None,
               memory_levels: List[Any] = None) -> Dict[StrategyLens, StrategyView]:
        """
        Generate strategy-specific views.
        
        Args:
            price: Current price
            volume: Trade volume
            latent_state: Optional latent market state
            memory_levels: Optional memory levels
            
        Returns:
            Dict of strategy lens -> strategy view
        """
        self._bar_count += 1
        self._price_history.append(price)
        self._volume_history.append(volume)
        
        views = {}
        
        # Generate view for each strategy type
        views[StrategyLens.MOMENTUM] = self._generate_momentum_view(price, memory_levels)
        views[StrategyLens.MEAN_REVERSION] = self._generate_mean_reversion_view(price)
        views[StrategyLens.BREAKOUT] = self._generate_breakout_view(price, memory_levels)
        views[StrategyLens.SCALPING] = self._generate_scalping_view(price)
        views[StrategyLens.SWING] = self._generate_swing_view(price, memory_levels)
        
        return views
    
    def _generate_momentum_view(self, price: float, 
                                memory_levels: List[Any] = None) -> StrategyView:
        """Generate momentum strategy view."""
        if len(self._price_history) < 20:
            return self._create_default_view(StrategyLens.MOMENTUM)
        
        prices = np.array(self._price_history)
        
        # Momentum signal
        momentum = (prices[-1] - prices[-20]) / prices[-20]
        signal_strength = np.tanh(momentum * 100)  # Normalize to [-1, 1]
        
        # Confidence based on trend consistency
        changes = np.diff(prices[-10:])
        consistency = np.mean(np.sign(changes) == np.sign(momentum))
        confidence = consistency
        
        # Key levels (recent highs/lows)
        key_levels = [np.max(prices[-20:]), np.min(prices[-20:])]
        
        # Risk/reward
        risk_reward = abs(momentum) / (np.std(np.diff(prices[-20:])) + 1e-8)
        
        # Entry quality
        entry_quality = confidence * abs(signal_strength)
        
        # Timing
        timing_score = 1 - abs(momentum) / (np.max(np.abs(np.diff(prices[-20:]))) + 1e-8)
        
        return StrategyView(
            lens=StrategyLens.MOMENTUM,
            signal_strength=float(signal_strength),
            confidence=float(confidence),
            key_levels=key_levels,
            risk_reward=float(risk_reward),
            entry_quality=float(entry_quality),
            timing_score=float(timing_score)
        )
    
    def _generate_mean_reversion_view(self, price: float) -> StrategyView:
        """Generate mean reversion strategy view."""
        if len(self._price_history) < 50:
            return self._create_default_view(StrategyLens.MEAN_REVERSION)
        
        prices = np.array(self._price_history)
        
        # Mean and std
        mean = np.mean(prices[-50:])
        std = np.std(prices[-50:])
        
        # Z-score
        zscore = (price - mean) / (std + 1e-8)
        
        # Signal: negative zscore = buy, positive = sell
        signal_strength = -np.tanh(zscore)
        
        # Confidence based on mean-reverting behavior
        returns = np.diff(prices[-20:])
        autocorr = np.corrcoef(returns[:-1], returns[1:])[0, 1] if len(returns) > 2 else 0
        confidence = max(0, -autocorr)  # Negative autocorr = mean reverting
        
        # Key levels (mean +/- 2 std)
        key_levels = [mean - 2*std, mean, mean + 2*std]
        
        # Risk/reward
        risk_reward = abs(zscore)
        
        # Entry quality (better at extremes)
        entry_quality = min(1.0, abs(zscore) / 2)
        
        # Timing
        timing_score = entry_quality * confidence
        
        return StrategyView(
            lens=StrategyLens.MEAN_REVERSION,
            signal_strength=float(signal_strength),
            confidence=float(confidence),
            key_levels=key_levels,
            risk_reward=float(risk_reward),
            entry_quality=float(entry_quality),
            timing_score=float(timing_score)
        )
    
    def _generate_breakout_view(self, price: float,
                               memory_levels: List[Any] = None) -> StrategyView:
        """Generate breakout strategy view."""
        if len(self._price_history) < 50:
            return self._create_default_view(StrategyLens.BREAKOUT)
        
        prices = np.array(self._price_history)
        
        # Recent range
        high = np.max(prices[-20:])
        low = np.min(prices[-20:])
        range_size = high - low
        
        # Distance to breakout levels
        dist_to_high = (high - price) / (range_size + 1e-8)
        dist_to_low = (price - low) / (range_size + 1e-8)
        
        # Signal: positive near high, negative near low
        if dist_to_high < dist_to_low:
            signal_strength = 1 - dist_to_high
        else:
            signal_strength = -(1 - dist_to_low)
        
        # Confidence based on range compression
        vol_short = np.std(prices[-10:])
        vol_long = np.std(prices[-50:])
        compression = vol_short / (vol_long + 1e-8)
        confidence = max(0, 1 - compression)
        
        # Key levels
        key_levels = [low, high]
        
        # Risk/reward
        risk_reward = range_size / (vol_short + 1e-8)
        
        # Entry quality (better when compressed near level)
        entry_quality = confidence * (1 - min(dist_to_high, dist_to_low))
        
        # Timing
        timing_score = confidence
        
        return StrategyView(
            lens=StrategyLens.BREAKOUT,
            signal_strength=float(signal_strength),
            confidence=float(confidence),
            key_levels=key_levels,
            risk_reward=float(risk_reward),
            entry_quality=float(entry_quality),
            timing_score=float(timing_score)
        )
    
    def _generate_scalping_view(self, price: float) -> StrategyView:
        """Generate scalping strategy view."""
        if len(self._price_history) < 10:
            return self._create_default_view(StrategyLens.SCALPING)
        
        prices = np.array(self._price_history)
        volumes = np.array(self._volume_history)
        
        # Very short-term momentum
        momentum = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
        signal_strength = np.tanh(momentum * 200)
        
        # Confidence based on volume
        vol_ratio = volumes[-1] / (np.mean(volumes[-10:]) + 1e-8) if len(volumes) >= 10 else 1
        confidence = min(1.0, vol_ratio)
        
        # Key levels (very tight)
        spread = np.mean(np.abs(np.diff(prices[-10:]))) if len(prices) >= 10 else 0.001
        key_levels = [price - spread, price + spread]
        
        # Risk/reward (tight)
        risk_reward = 1.0  # Scalping typically 1:1
        
        # Entry quality
        entry_quality = confidence * abs(signal_strength)
        
        # Timing (immediate)
        timing_score = 0.9  # Scalping is always "now"
        
        return StrategyView(
            lens=StrategyLens.SCALPING,
            signal_strength=float(signal_strength),
            confidence=float(confidence),
            key_levels=key_levels,
            risk_reward=float(risk_reward),
            entry_quality=float(entry_quality),
            timing_score=float(timing_score)
        )
    
    def _generate_swing_view(self, price: float,
                            memory_levels: List[Any] = None) -> StrategyView:
        """Generate swing trading strategy view."""
        if len(self._price_history) < 100:
            return self._create_default_view(StrategyLens.SWING)
        
        prices = np.array(self._price_history)
        
        # Longer-term trend
        trend = (prices[-1] - prices[-100]) / prices[-100]
        signal_strength = np.tanh(trend * 50)
        
        # Confidence based on trend strength
        efficiency = abs(prices[-1] - prices[-100]) / np.sum(np.abs(np.diff(prices[-100:])))
        confidence = efficiency
        
        # Key levels (swing highs/lows)
        key_levels = [np.min(prices[-100:]), np.max(prices[-100:])]
        
        # Risk/reward
        risk_reward = abs(trend) / (np.std(np.diff(prices[-100:])) + 1e-8) * 10
        
        # Entry quality
        entry_quality = confidence * (1 - abs(signal_strength))  # Better at pullbacks
        
        # Timing
        timing_score = entry_quality
        
        return StrategyView(
            lens=StrategyLens.SWING,
            signal_strength=float(signal_strength),
            confidence=float(confidence),
            key_levels=key_levels,
            risk_reward=float(risk_reward),
            entry_quality=float(entry_quality),
            timing_score=float(timing_score)
        )
    
    def _create_default_view(self, lens: StrategyLens) -> StrategyView:
        """Create default view for insufficient data."""
        return StrategyView(
            lens=lens,
            signal_strength=0.0,
            confidence=0.2,
            key_levels=[],
            risk_reward=1.0,
            entry_quality=0.0,
            timing_score=0.0
        )
    
    def reset(self):
        """Reset engine state."""
        self._price_history.clear()
        self._volume_history.clear()
        self._bar_count = 0


class ConfidenceOverlayEngine:
    """
    Generates confidence-weighted overlays for visualization.
    
    Overlays fade by uncertainty - visual honesty.
    """
    
    def __init__(self, config: MarketIntelligenceConfig):
        self.config = config
        self._overlays: List[ConfidenceWeightedOverlay] = []
        self._last_update = time.time()
    
    def create_overlay(self, overlay_type: str, data: Dict[str, Any],
                      confidence: float, z_index: int = 0) -> ConfidenceWeightedOverlay:
        """
        Create a confidence-weighted overlay.
        
        Args:
            overlay_type: Type of overlay (e.g., 'regime_background', 'support_level')
            data: Overlay-specific data
            confidence: Confidence level [0, 1]
            z_index: Rendering order
            
        Returns:
            ConfidenceWeightedOverlay
        """
        # Calculate opacity from confidence
        opacity = self._confidence_to_opacity(confidence)
        
        # Determine visibility
        visible = confidence >= self.config.min_confidence_display
        
        overlay = ConfidenceWeightedOverlay(
            overlay_type=overlay_type,
            data=data,
            confidence=confidence,
            opacity=opacity,
            z_index=z_index,
            visible=visible,
            staleness_ms=0.0
        )
        
        self._overlays.append(overlay)
        return overlay
    
    def _confidence_to_opacity(self, confidence: float) -> float:
        """
        Convert confidence to opacity.
        
        Uses sigmoid-like mapping for smooth transition.
        """
        # Sigmoid mapping centered at threshold
        threshold = self.config.min_confidence_display
        steepness = 10
        
        opacity = 1 / (1 + np.exp(-steepness * (confidence - threshold)))
        
        return float(opacity)
    
    def update_staleness(self):
        """Update staleness of all overlays."""
        current_time = time.time()
        elapsed_ms = (current_time - self._last_update) * 1000
        
        for overlay in self._overlays:
            overlay.staleness_ms += elapsed_ms
            
            # Decay confidence with staleness
            if overlay.staleness_ms > 100:
                decay = self.config.confidence_decay_rate ** (overlay.staleness_ms / 1000)
                overlay.confidence *= decay
                overlay.opacity = self._confidence_to_opacity(overlay.confidence)
                overlay.visible = overlay.confidence >= self.config.min_confidence_display
        
        self._last_update = current_time
    
    def get_visible_overlays(self) -> List[ConfidenceWeightedOverlay]:
        """Get all visible overlays."""
        return [o for o in self._overlays if o.visible]
    
    def get_overlays_by_type(self, overlay_type: str) -> List[ConfidenceWeightedOverlay]:
        """Get overlays of specific type."""
        return [o for o in self._overlays if o.overlay_type == overlay_type]
    
    def clear_overlays(self):
        """Clear all overlays."""
        self._overlays.clear()
    
    def prune_stale_overlays(self, max_staleness_ms: float = 5000):
        """Remove overlays that are too stale."""
        self._overlays = [o for o in self._overlays if o.staleness_ms < max_staleness_ms]
    
    def reset(self):
        """Reset engine state."""
        self._overlays.clear()
        self._last_update = time.time()
