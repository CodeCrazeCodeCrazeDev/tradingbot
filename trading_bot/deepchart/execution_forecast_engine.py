"""
DeepChart Execution Quality Forecast Engine

Forecasts execution quality (slippage, fill probability) using
historical execution data and current market conditions.

Concepts covered:
- Execution Quality Forecast (Concept 7)
- Price Response Curvature (Concept 11)

Math:
    slippage = f(spread, volatility, order_size, liquidity)
    fill_prob = g(spread, depth_imbalance, urgency)
    adverse_selection = h(information_asymmetry, toxicity)
    price_response = α × volume^β (power law)

Performance Budget:
    - Update: O(1) per tick
    - Memory: O(lookback_window)
    - Latency: <0.3ms per update
"""

import numpy as np
from collections import deque
from typing import Optional, List, Tuple
import logging

from .market_intelligence_core import (
    ExecutionQualityForecast,
    ExecutionRisk,
    PriceResponseCurve,
    SyntheticLiquidityMap,
    MarketIntelligenceConfig,
)

logger = logging.getLogger(__name__)


class ExecutionQualityForecaster:
    """
    Forecasts execution quality (slippage, fill probability).
    
    Uses historical execution data and current market conditions
    to predict execution outcomes.
    """
    
    def __init__(self, config: MarketIntelligenceConfig):
        self.config = config
        self._spread_history = deque(maxlen=config.slippage_lookback)
        self._slippage_history = deque(maxlen=100)
        self._fill_times = deque(maxlen=100)
        self._volume_history = deque(maxlen=200)
        self._bar_count = 0
    
    def update(self, price: float, bid: float, ask: float, volume: float,
               liquidity_map: Optional[SyntheticLiquidityMap] = None) -> ExecutionQualityForecast:
        """
        Update execution quality forecast.
        
        Args:
            price: Current price
            bid: Best bid
            ask: Best ask
            volume: Trade volume
            liquidity_map: Optional synthetic liquidity map
            
        Returns:
            ExecutionQualityForecast with slippage and fill predictions
        """
        self._bar_count += 1
        
        spread = ask - bid
        spread_bps = (spread / price) * 10000 if price > 0 else 10
        self._spread_history.append(spread_bps)
        self._volume_history.append(volume)
        
        if len(self._spread_history) < 10:
            return self._create_default_forecast()
        
        # Expected slippage
        expected_slippage = self._estimate_slippage(spread_bps, volume, liquidity_map)
        
        # Fill probability
        fill_prob = self._estimate_fill_probability(spread_bps, liquidity_map)
        
        # Time to fill
        time_to_fill = self._estimate_time_to_fill(spread_bps)
        
        # Adverse selection risk
        adverse_selection = self._estimate_adverse_selection(liquidity_map)
        
        # Market impact
        market_impact = self._estimate_market_impact(volume, liquidity_map)
        
        # Execution risk level
        risk_level = self._classify_execution_risk(expected_slippage, fill_prob, adverse_selection)
        
        # Optimal order size
        optimal_size = self._calculate_optimal_size(volume, liquidity_map)
        
        # Confidence
        confidence = min(1.0, len(self._spread_history) / 50)
        
        return ExecutionQualityForecast(
            expected_slippage_bps=expected_slippage,
            fill_probability=fill_prob,
            time_to_fill_ms=time_to_fill,
            adverse_selection_risk=adverse_selection,
            market_impact_estimate=market_impact,
            execution_risk=risk_level,
            optimal_order_size=optimal_size,
            confidence=confidence
        )
    
    def _estimate_slippage(self, spread_bps: float, volume: float,
                          liquidity_map: Optional[SyntheticLiquidityMap]) -> float:
        """
        Estimate expected slippage in basis points.
        
        Slippage = f(spread, volume, liquidity)
        """
        # Base slippage from spread (half spread)
        base_slippage = spread_bps * 0.5
        
        # Volume impact (square root model)
        avg_volume = np.mean(self._volume_history) if self._volume_history else volume
        volume_factor = 1 + np.sqrt(volume / (avg_volume + 1e-8)) * 0.1
        
        # Liquidity adjustment
        if liquidity_map and abs(liquidity_map.asymmetry_score) > 0.3:
            # High asymmetry = higher slippage on one side
            liquidity_factor = 1 + abs(liquidity_map.asymmetry_score)
        else:
            liquidity_factor = 1.0
        
        # Spread volatility adjustment
        if len(self._spread_history) > 10:
            spread_vol = np.std(self._spread_history)
            spread_mean = np.mean(self._spread_history)
            spread_factor = 1 + spread_vol / (spread_mean + 1e-8) * 0.5
        else:
            spread_factor = 1.0
        
        return base_slippage * volume_factor * liquidity_factor * spread_factor
    
    def _estimate_fill_probability(self, spread_bps: float,
                                   liquidity_map: Optional[SyntheticLiquidityMap]) -> float:
        """
        Estimate probability of fill.
        
        Higher spread = lower fill probability for limit orders.
        """
        # Base probability from spread
        base_prob = max(0.5, 1 - spread_bps / 20)
        
        # Liquidity adjustment
        if liquidity_map:
            # More liquidity = higher fill probability
            liquidity_factor = 0.5 + 0.5 * (1 - abs(liquidity_map.asymmetry_score))
        else:
            liquidity_factor = 0.8
        
        return min(1.0, base_prob * liquidity_factor)
    
    def _estimate_time_to_fill(self, spread_bps: float) -> float:
        """
        Estimate time to fill in milliseconds.
        
        Wider spread = longer fill time.
        """
        # Base time from spread
        base_time = 100 + spread_bps * 50
        
        # Historical adjustment
        if len(self._fill_times) > 10:
            historical_mean = np.mean(self._fill_times)
            base_time = 0.7 * base_time + 0.3 * historical_mean
        
        return base_time
    
    def _estimate_adverse_selection(self, liquidity_map: Optional[SyntheticLiquidityMap]) -> float:
        """
        Estimate adverse selection risk.
        
        High asymmetry = high adverse selection.
        """
        if not liquidity_map:
            return 0.3
        
        # High asymmetry = high adverse selection
        base_risk = abs(liquidity_map.asymmetry_score)
        
        # Iceberg orders increase adverse selection
        iceberg_factor = liquidity_map.iceberg_probability * 0.3
        
        return min(1.0, base_risk + iceberg_factor)
    
    def _estimate_market_impact(self, volume: float,
                               liquidity_map: Optional[SyntheticLiquidityMap]) -> float:
        """
        Estimate market impact using square-root model.
        
        Impact = σ × √(V/ADV)
        """
        avg_volume = np.mean(self._volume_history) if self._volume_history else volume
        
        # Square-root impact model
        base_impact = np.sqrt(volume / (avg_volume + 1e-8)) * 0.01
        
        if liquidity_map:
            # Adjust for liquidity
            liquidity_factor = 1 + (1 - max(liquidity_map.hidden_bid_estimate,
                                            liquidity_map.hidden_ask_estimate))
            return base_impact * liquidity_factor
        
        return base_impact
    
    def _classify_execution_risk(self, slippage: float, fill_prob: float,
                                adverse_selection: float) -> ExecutionRisk:
        """Classify overall execution risk."""
        risk_score = slippage / 10 + (1 - fill_prob) + adverse_selection
        
        if risk_score < 0.5:
            return ExecutionRisk.LOW
        elif risk_score < 1.0:
            return ExecutionRisk.MEDIUM
        elif risk_score < 1.5:
            return ExecutionRisk.HIGH
        return ExecutionRisk.EXTREME
    
    def _calculate_optimal_size(self, current_volume: float,
                               liquidity_map: Optional[SyntheticLiquidityMap]) -> float:
        """
        Calculate optimal order size for minimal impact.
        
        Target: 1% of average volume.
        """
        avg_volume = np.mean(self._volume_history) if self._volume_history else current_volume
        
        # Target 1% of average volume
        base_size = avg_volume * 0.01
        
        if liquidity_map:
            # Adjust for liquidity
            liquidity_factor = max(liquidity_map.hidden_bid_estimate,
                                  liquidity_map.hidden_ask_estimate)
            return base_size * (1 + liquidity_factor)
        
        return base_size
    
    def record_execution(self, slippage_bps: float, fill_time_ms: float):
        """Record actual execution for calibration."""
        self._slippage_history.append(slippage_bps)
        self._fill_times.append(fill_time_ms)
    
    def _create_default_forecast(self) -> ExecutionQualityForecast:
        """Create default forecast for insufficient data."""
        return ExecutionQualityForecast(
            expected_slippage_bps=5.0,
            fill_probability=0.8,
            time_to_fill_ms=200.0,
            adverse_selection_risk=0.3,
            market_impact_estimate=0.01,
            execution_risk=ExecutionRisk.MEDIUM,
            optimal_order_size=100.0,
            confidence=0.2
        )
    
    def reset(self):
        """Reset forecaster state."""
        self._spread_history.clear()
        self._slippage_history.clear()
        self._fill_times.clear()
        self._volume_history.clear()
        self._bar_count = 0


class PriceResponseCurveEngine:
    """
    Models non-linear price response to volume.
    
    Key insight: Price response is not linear with volume.
    Small orders have minimal impact, large orders have disproportionate impact.
    
    Model: Δp = α × V^β (power law)
    """
    
    def __init__(self, config: MarketIntelligenceConfig):
        self.config = config
        self._volume_impact_pairs = deque(maxlen=500)
        self._alpha = 0.001  # Scale parameter
        self._beta = 0.5     # Power parameter (square root model)
        self._bar_count = 0
    
    def update(self, price: float, volume: float, price_change: float) -> PriceResponseCurve:
        """
        Update price response curve.
        
        Args:
            price: Current price
            volume: Trade volume
            price_change: Absolute price change
            
        Returns:
            PriceResponseCurve with response characteristics
        """
        self._bar_count += 1
        
        if volume > 0 and price_change != 0:
            self._volume_impact_pairs.append((volume, abs(price_change)))
        
        if len(self._volume_impact_pairs) < 20:
            return self._create_default_curve()
        
        # Fit power law model
        self._fit_power_law()
        
        # Generate response curve
        volume_levels, price_response = self._generate_curve()
        
        # Calculate curvature
        curvature = self._calculate_curvature(volume_levels, price_response)
        
        # Linearity score
        linearity = self._calculate_linearity()
        
        # Saturation point
        saturation = self._estimate_saturation_point()
        
        # Elasticity
        elasticity = self._calculate_elasticity()
        
        return PriceResponseCurve(
            volume_levels=volume_levels,
            price_response=price_response,
            curvature=curvature,
            linearity_score=linearity,
            saturation_point=saturation,
            elasticity=elasticity
        )
    
    def _fit_power_law(self):
        """
        Fit power law model: Δp = α × V^β
        
        Using log-linear regression: log(Δp) = log(α) + β × log(V)
        """
        if len(self._volume_impact_pairs) < 20:
            return
        
        volumes = np.array([v for v, _ in self._volume_impact_pairs])
        impacts = np.array([i for _, i in self._volume_impact_pairs])
        
        # Filter out zeros
        mask = (volumes > 0) & (impacts > 0)
        volumes = volumes[mask]
        impacts = impacts[mask]
        
        if len(volumes) < 10:
            return
        
        # Log transform
        log_v = np.log(volumes)
        log_i = np.log(impacts)
        
        try:
            # Linear regression
            A = np.vstack([log_v, np.ones(len(log_v))]).T
            result = np.linalg.lstsq(A, log_i, rcond=None)
            self._beta = result[0][0]
            self._alpha = np.exp(result[0][1])
            
            # Constrain parameters
            self._beta = np.clip(self._beta, 0.1, 1.0)
            self._alpha = np.clip(self._alpha, 1e-6, 0.1)
        except Exception as e:
            logger.error(f"Error: {e}")
            pass
    
    def _generate_curve(self) -> Tuple[np.ndarray, np.ndarray]:
        """Generate price response curve."""
        if len(self._volume_impact_pairs) < 10:
            volume_levels = np.linspace(1, 1000, 20)
            return volume_levels, volume_levels * 0.001
        
        volumes = np.array([v for v, _ in self._volume_impact_pairs])
        
        # Generate volume levels spanning observed range
        v_min = max(1, np.percentile(volumes, 5))
        v_max = np.percentile(volumes, 95)
        
        volume_levels = np.linspace(v_min, v_max, 20)
        
        # Apply power law
        price_response = self._alpha * np.power(volume_levels, self._beta)
        
        return volume_levels, price_response
    
    def _calculate_curvature(self, volumes: np.ndarray, response: np.ndarray) -> float:
        """
        Calculate curvature of response function.
        
        Curvature = second derivative / (1 + first_derivative^2)^1.5
        """
        if len(volumes) < 3:
            return 0.0
        
        # Numerical derivatives
        dv = np.diff(volumes)
        dr = np.diff(response)
        
        first_deriv = dr / (dv + 1e-8)
        
        if len(first_deriv) < 2:
            return 0.0
        
        second_deriv = np.diff(first_deriv) / (dv[:-1] + 1e-8)
        
        # Average curvature
        curvature = np.mean(np.abs(second_deriv) / np.power(1 + first_deriv[:-1]**2, 1.5))
        
        return float(curvature)
    
    def _calculate_linearity(self) -> float:
        """
        Calculate linearity score.
        
        1.0 = perfectly linear (β = 1)
        0.0 = highly non-linear
        """
        # β = 1 is linear, β = 0.5 is square root
        return 1 - abs(1 - self._beta)
    
    def _estimate_saturation_point(self) -> float:
        """
        Estimate volume at which response saturates.
        
        Saturation = point where marginal impact decreases significantly.
        """
        if len(self._volume_impact_pairs) < 20:
            return 10000.0
        
        volumes = np.array([v for v, _ in self._volume_impact_pairs])
        
        # Saturation at 90th percentile of observed volume
        return float(np.percentile(volumes, 90))
    
    def _calculate_elasticity(self) -> float:
        """
        Calculate price elasticity to volume.
        
        Elasticity = β (the power law exponent)
        """
        return self._beta
    
    def predict_impact(self, volume: float) -> float:
        """Predict price impact for given volume."""
        return self._alpha * np.power(volume, self._beta)
    
    def _create_default_curve(self) -> PriceResponseCurve:
        """Create default curve for insufficient data."""
        volume_levels = np.linspace(1, 1000, 20)
        price_response = 0.001 * np.sqrt(volume_levels)
        
        return PriceResponseCurve(
            volume_levels=volume_levels,
            price_response=price_response,
            curvature=0.0,
            linearity_score=0.5,
            saturation_point=10000.0,
            elasticity=0.5
        )
    
    def reset(self):
        """Reset engine state."""
        self._volume_impact_pairs.clear()
        self._alpha = 0.001
        self._beta = 0.5
        self._bar_count = 0
