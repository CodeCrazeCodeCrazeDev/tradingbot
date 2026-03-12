"""Advanced Risk Management Module - Fractal Position Sizing and Black Swan Protection.

This module implements revolutionary risk management techniques including Hurst Exponent-adjusted
Kelly Criterion, Black Swan Shielding, and Volatility Capacitors for dynamic risk adaptation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging
try:
    from scipy import stats
except ImportError:
    scipy = None
from scipy.optimize import minimize_scalar
from sklearn.preprocessing import StandardScaler
import warnings
import numpy
import pandas

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Container for comprehensive risk metrics."""
    var_95: float
    var_99: float
    expected_shortfall: float
    maximum_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    tail_ratio: float


@dataclass
class PositionSizeRecommendation:
    """Position sizing recommendation with risk analysis."""
    recommended_size: float
    max_safe_size: float
    kelly_fraction: float
    hurst_adjustment: float
    volatility_adjustment: float
    confidence_level: float
    risk_reward_ratio: float
    expected_return: float


class HurstExponentCalculator:
    """
    Calculates Hurst Exponent to measure market memory persistence.
    
    Used to adjust position sizing based on whether markets are trending,
    mean-reverting, or following random walk patterns.
    """
    
    def __init__(self, min_window: int = 50, max_window: int = 200):
        """
        Initialize Hurst Exponent Calculator.
        
        Args:
            min_window: Minimum window size for calculation
            max_window: Maximum window size for calculation
        """
        self.min_window = min_window
        self.max_window = max_window
    
    def calculate_hurst_exponent(self, price_series: pd.Series) -> float:
        """
        Calculate Hurst Exponent using R/S analysis.
        
        Returns:
            Hurst exponent (0.5 = random walk, >0.5 = trending, <0.5 = mean reverting)
        """
        if len(price_series) < self.min_window:
            return 0.5  # Default to random walk
        
        # Calculate log returns
        log_returns = np.log(price_series / price_series.shift(1)).dropna()
        
        if len(log_returns) < self.min_window:
            return 0.5
        
        # R/S Analysis
        lags = range(2, min(len(log_returns) // 4, self.max_window))
        rs_ratios = []
        
        for lag in lags:
            rs_ratio = self._calculate_rs_ratio(log_returns, lag)
            if rs_ratio > 0:
                rs_ratios.append(rs_ratio)
        
        if len(rs_ratios) < 3:
            return 0.5
        
        # Linear regression to find Hurst exponent
        log_lags = np.log(lags[:len(rs_ratios)])
        log_rs = np.log(rs_ratios)
        
        try:
            slope, _, _, _, _ = stats.linregress(log_lags, log_rs)
            hurst = slope
        except Exception:
            hurst = 0.5
        
        # Bound Hurst exponent to reasonable range
        return max(0.1, min(0.9, hurst))
    
    def _calculate_rs_ratio(self, returns: pd.Series, lag: int) -> float:
        """Calculate R/S ratio for a given lag."""
        try:
            # Split series into non-overlapping windows
            n_windows = len(returns) // lag
            rs_values = []
            
            for i in range(n_windows):
                window_returns = returns.iloc[i*lag:(i+1)*lag]
                
                if len(window_returns) < lag:
                    continue
                
                # Calculate mean return for window
                mean_return = window_returns.mean()
                
                # Calculate cumulative deviations
                deviations = (window_returns - mean_return).cumsum()
                
                # Calculate range
                R = deviations.max() - deviations.min()
                
                # Calculate standard deviation
                S = window_returns.std()
                
                if S > 0:
                    rs_values.append(R / S)
            
            return np.mean(rs_values) if rs_values else 0
        except Exception:
            return 0
    
    def interpret_hurst_exponent(self, hurst: float) -> Dict[str, Union[str, float]]:
        """
        Interpret Hurst exponent value.
        
        Returns:
            Dictionary with interpretation and trading implications
        """
        if hurst > 0.6:
            regime = "trending"
            persistence = "high"
            strategy_bias = "trend_following"
            position_adjustment = 1.2  # Increase position size in trending markets
        elif hurst < 0.4:
            regime = "mean_reverting"
            persistence = "low"
            strategy_bias = "mean_reversion"
            position_adjustment = 0.8  # Decrease position size in mean-reverting markets
        else:
            regime = "random_walk"
            persistence = "neutral"
            strategy_bias = "neutral"
            position_adjustment = 1.0  # Standard position size
        
        return {
            "hurst_value": hurst,
            "market_regime": regime,
            "persistence": persistence,
            "strategy_bias": strategy_bias,
            "position_adjustment": position_adjustment,
            "confidence": abs(hurst - 0.5) * 2  # Distance from random walk
        }


class FractalPositionSizer:
    """
    Advanced position sizing using fractal market analysis and Kelly Criterion.
    
    Combines Hurst Exponent analysis with dynamic Kelly Criterion to optimize
    position sizes based on market regime and volatility conditions.
    """
    
    def __init__(self, 
                 max_position_size: float = 0.1,  # 10% max position
                 kelly_multiplier: float = 0.25,   # Conservative Kelly fraction
                 volatility_lookback: int = 20,
                 confidence_threshold: float = 0.6):
        """
        Initialize Fractal Position Sizer.
        
        Args:
            max_position_size: Maximum allowed position size as fraction of capital
            kelly_multiplier: Multiplier for Kelly fraction (for safety)
            volatility_lookback: Lookback period for volatility calculation
            confidence_threshold: Minimum confidence for position sizing
        """
        self.max_position_size = max_position_size
        self.kelly_multiplier = kelly_multiplier
        self.volatility_lookback = volatility_lookback
        self.confidence_threshold = confidence_threshold
        
        self.hurst_calculator = HurstExponentCalculator()
        self.scaler = StandardScaler()
        
    def calculate_optimal_position_size(self, 
                                      price_data: pd.Series,
                                      expected_return: float,
                                      stop_loss_pct: float,
                                      take_profit_pct: float,
                                      win_probability: float) -> PositionSizeRecommendation:
        """
        Calculate optimal position size using fractal analysis and Kelly Criterion.
        
        Args:
            price_data: Historical price data
            expected_return: Expected return of the trade
            stop_loss_pct: Stop loss as percentage
            take_profit_pct: Take profit as percentage
            win_probability: Probability of winning trade
            
        Returns:
            PositionSizeRecommendation object
        """
        # Calculate Hurst exponent and market regime
        hurst_exponent = self.hurst_calculator.calculate_hurst_exponent(price_data)
        hurst_interpretation = self.hurst_calculator.interpret_hurst_exponent(hurst_exponent)
        
        # Calculate volatility adjustment
        volatility_adj = self._calculate_volatility_adjustment(price_data)
        
        # Calculate Kelly fraction
        kelly_fraction = self._calculate_kelly_fraction(
            expected_return, stop_loss_pct, take_profit_pct, win_probability
        )
        
        # Apply Hurst adjustment
        hurst_adjustment = hurst_interpretation["position_adjustment"]
        adjusted_kelly = kelly_fraction * hurst_adjustment * self.kelly_multiplier
        
        # Apply volatility adjustment
        volatility_adjusted_size = adjusted_kelly * volatility_adj
        
        # Calculate final recommended size
        recommended_size = min(volatility_adjusted_size, self.max_position_size)
        
        # Calculate maximum safe size (stress test)
        max_safe_size = self._calculate_max_safe_size(price_data, stop_loss_pct)
        
        # Ensure recommended size doesn't exceed safe size
        final_size = min(recommended_size, max_safe_size)
        
        # Calculate confidence level
        confidence = self._calculate_sizing_confidence(
            hurst_interpretation["confidence"], volatility_adj, win_probability
        )
        
        return PositionSizeRecommendation(
            recommended_size=final_size,
            max_safe_size=max_safe_size,
            kelly_fraction=kelly_fraction,
            hurst_adjustment=hurst_adjustment,
            volatility_adjustment=volatility_adj,
            confidence_level=confidence,
            risk_reward_ratio=take_profit_pct / stop_loss_pct,
            expected_return=expected_return
        )
    
    def _calculate_kelly_fraction(self, 
                                expected_return: float,
                                stop_loss_pct: float,
                                take_profit_pct: float,
                                win_probability: float) -> float:
        """Calculate Kelly fraction for optimal position sizing."""
        # Kelly formula: f = (bp - q) / b
        # where b = odds received on wager, p = probability of winning, q = probability of losing
        
        if stop_loss_pct <= 0 or win_probability <= 0 or win_probability >= 1:
            return 0.01  # Minimal position if parameters are invalid
        
        # Calculate odds ratio
        win_amount = take_profit_pct
        loss_amount = stop_loss_pct
        
        # Kelly fraction calculation
        kelly = (win_probability * win_amount - (1 - win_probability) * loss_amount) / win_amount
        
        # Ensure Kelly fraction is positive and reasonable
        return max(0.001, min(kelly, 0.5))  # Cap at 50% for safety
    
    def _calculate_volatility_adjustment(self, price_data: pd.Series) -> float:
        """Calculate volatility-based position size adjustment."""
        if len(price_data) < self.volatility_lookback:
            return 0.5  # Conservative default
        
        # Calculate returns
        returns = price_data.pct_change().dropna()
        
        if len(returns) < 10:
            return 0.5
        
        # Calculate current volatility
        current_vol = returns.tail(self.volatility_lookback).std()
        
        # Calculate historical volatility
        historical_vol = returns.std()
        
        if historical_vol == 0:
            return 0.5
        
        # Volatility ratio
        vol_ratio = current_vol / historical_vol
        
        # Inverse relationship: higher volatility = smaller position
        volatility_adjustment = 1.0 / (1.0 + vol_ratio)
        
        return max(0.1, min(volatility_adjustment, 1.0))
    
    def _calculate_max_safe_size(self, price_data: pd.Series, stop_loss_pct: float) -> float:
        """Calculate maximum safe position size based on worst-case scenarios."""
        if len(price_data) < 20:
            return self.max_position_size * 0.5
        
        # Calculate maximum historical drawdown
        returns = price_data.pct_change().dropna()
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = abs(drawdown.min())
        
        # Calculate VaR (Value at Risk) at 99% confidence
        var_99 = abs(np.percentile(returns, 1))
        
        # Use the worse of stop loss or historical worst case
        worst_case_loss = max(stop_loss_pct, max_drawdown, var_99)
        
        # Maximum safe size to limit portfolio loss to 2%
        max_portfolio_risk = 0.02
        max_safe_size = max_portfolio_risk / worst_case_loss
        
        return min(max_safe_size, self.max_position_size)
    
    def _calculate_sizing_confidence(self, 
                                   hurst_confidence: float,
                                   volatility_adj: float,
                                   win_probability: float) -> float:
        """Calculate overall confidence in position sizing recommendation."""
        # Combine multiple confidence factors
        confidence_factors = [
            hurst_confidence,
            volatility_adj,  # Higher volatility adjustment = lower confidence
            win_probability,
            0.8  # Base confidence level
        ]
        
        # Weighted average
        weights = [0.3, 0.2, 0.3, 0.2]
        confidence = sum(f * w for f, w in zip(confidence_factors, weights))
        
        return max(0.1, min(confidence, 1.0))


class BlackSwanShield:
    """
    Advanced protection system against black swan events using extreme value theory.
    
    Implements real-time VaR adjustments and tail risk hedging to protect against
    rare but catastrophic market events.
    """
    
    def __init__(self, 
                 var_confidence_levels: List[float] = [0.95, 0.99, 0.999],
                 tail_threshold: float = 0.05,
                 max_portfolio_var: float = 0.02):
        """
        Initialize Black Swan Shield.
        
        Args:
            var_confidence_levels: Confidence levels for VaR calculations
            tail_threshold: Threshold for tail event detection
            max_portfolio_var: Maximum allowed portfolio VaR
        """
        self.var_levels = var_confidence_levels
        self.tail_threshold = tail_threshold
        self.max_portfolio_var = max_portfolio_var
        
    def calculate_risk_metrics(self, returns: pd.Series) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics including tail risk measures.
        
        Returns:
            RiskMetrics object with all calculated metrics
        """
        if len(returns) < 30:
            # Return default metrics if insufficient data
            return RiskMetrics(
                var_95=0.02, var_99=0.04, expected_shortfall=0.05,
                maximum_drawdown=0.03, sharpe_ratio=0.0, sortino_ratio=0.0,
                calmar_ratio=0.0, tail_ratio=1.0
            )
        
        # Calculate VaR at different confidence levels
        var_95 = abs(np.percentile(returns, 5))
        var_99 = abs(np.percentile(returns, 1))
        
        # Calculate Expected Shortfall (Conditional VaR)
        tail_losses = returns[returns <= -var_95]
        expected_shortfall = abs(tail_losses.mean()) if len(tail_losses) > 0 else var_95
        
        # Calculate Maximum Drawdown
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        maximum_drawdown = abs(drawdown.min())
        
        # Calculate Sharpe Ratio
        excess_returns = returns - 0.02/252  # Assuming 2% risk-free rate
        sharpe_ratio = excess_returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
        # Calculate Sortino Ratio
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else returns.std()
        sortino_ratio = excess_returns.mean() / downside_std * np.sqrt(252) if downside_std > 0 else 0
        
        # Calculate Calmar Ratio
        annual_return = returns.mean() * 252
        calmar_ratio = annual_return / maximum_drawdown if maximum_drawdown > 0 else 0
        
        # Calculate Tail Ratio
        upside_tail = np.percentile(returns, 95)
        downside_tail = abs(np.percentile(returns, 5))
        tail_ratio = upside_tail / downside_tail if downside_tail > 0 else 1
        
        return RiskMetrics(
            var_95=var_95,
            var_99=var_99,
            expected_shortfall=expected_shortfall,
            maximum_drawdown=maximum_drawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            tail_ratio=tail_ratio
        )
    
    def detect_black_swan_conditions(self, 
                                   current_returns: pd.Series,
                                   market_indicators: Dict) -> Dict:
        """
        Detect conditions that may lead to black swan events.
        
        Returns:
            Dictionary with black swan risk assessment
        """
        risk_factors = {}
        
        # Volatility clustering detection
        vol_clustering = self._detect_volatility_clustering(current_returns)
        risk_factors['volatility_clustering'] = vol_clustering
        
        # Tail risk escalation
        tail_risk = self._assess_tail_risk_escalation(current_returns)
        risk_factors['tail_risk_escalation'] = tail_risk
        
        # Correlation breakdown detection
        correlation_risk = self._detect_correlation_breakdown(market_indicators)
        risk_factors['correlation_breakdown'] = correlation_risk
        
        # Liquidity stress indicators
        liquidity_stress = self._assess_liquidity_stress(market_indicators)
        risk_factors['liquidity_stress'] = liquidity_stress
        
        # Overall black swan probability
        black_swan_probability = self._calculate_black_swan_probability(risk_factors)
        
        return {
            'black_swan_probability': black_swan_probability,
            'risk_factors': risk_factors,
            'recommended_action': self._recommend_protection_action(black_swan_probability),
            'hedge_ratio': self._calculate_hedge_ratio(black_swan_probability)
        }
    
    def _detect_volatility_clustering(self, returns: pd.Series) -> Dict:
        """Detect volatility clustering patterns."""
        if len(returns) < 20:
            return {'detected': False, 'intensity': 0.0}
        
        # Calculate rolling volatility
        vol = returns.rolling(10).std()
        vol_changes = vol.pct_change().abs()
        
        # Detect clustering
        clustering_intensity = vol_changes.tail(5).mean()
        
        return {
            'detected': clustering_intensity > 0.5,
            'intensity': clustering_intensity,
            'current_volatility': vol.iloc[-1] if len(vol) > 0 else 0
        }
    
    def _assess_tail_risk_escalation(self, returns: pd.Series) -> Dict:
        """Assess escalation in tail risk."""
        if len(returns) < 50:
            return {'escalating': False, 'severity': 0.0}
        
        # Compare recent tail behavior to historical
        recent_tail = abs(np.percentile(returns.tail(20), 5))
        historical_tail = abs(np.percentile(returns, 5))
        
        escalation_ratio = recent_tail / historical_tail if historical_tail > 0 else 1
        
        return {
            'escalating': escalation_ratio > 1.5,
            'severity': escalation_ratio,
            'recent_var': recent_tail
        }
    
    def _detect_correlation_breakdown(self, market_indicators: Dict) -> Dict:
        """Detect breakdown in market correlations."""
        # Placeholder implementation
        return {'breakdown_detected': False, 'correlation_stress': 0.0}
    
    def _assess_liquidity_stress(self, market_indicators: Dict) -> Dict:
        """Assess liquidity stress conditions."""
        # Placeholder implementation
        return {'stress_detected': False, 'liquidity_score': 1.0}
    
    def _calculate_black_swan_probability(self, risk_factors: Dict) -> float:
        """Calculate overall black swan probability."""
        # Weight different risk factors
        weights = {
            'volatility_clustering': 0.3,
            'tail_risk_escalation': 0.4,
            'correlation_breakdown': 0.2,
            'liquidity_stress': 0.1
        }
        
        probability = 0.0
        for factor, data in risk_factors.items():
            if factor in weights:
                if isinstance(data, dict):
                    if 'detected' in data and data['detected']:
                        probability += weights[factor] * data.get('intensity', 0.5)
                    elif 'escalating' in data and data['escalating']:
                        probability += weights[factor] * data.get('severity', 0.5)
        
        return min(probability, 1.0)
    
    def _recommend_protection_action(self, black_swan_probability: float) -> str:
        """Recommend protection action based on black swan probability."""
        if black_swan_probability > 0.7:
            return 'emergency_hedge'
        elif black_swan_probability > 0.5:
            return 'increase_hedge'
        elif black_swan_probability > 0.3:
            return 'monitor_closely'
        else:
            return 'normal_operations'
    
    def _calculate_hedge_ratio(self, black_swan_probability: float) -> float:
        """Calculate recommended hedge ratio."""
        # Linear relationship between probability and hedge ratio
        base_hedge = 0.05  # 5% base hedge
        max_hedge = 0.25   # 25% maximum hedge
        
        hedge_ratio = base_hedge + (max_hedge - base_hedge) * black_swan_probability
        return min(hedge_ratio, max_hedge)


class VolatilityCapacitor:
    """
    Dynamic volatility-based position and exposure management system.
    
    Automatically reduces exposure when volatility contradicts market sentiment
    or when volatility spikes indicate potential regime changes.
    """
    
    def __init__(self, 
                 volatility_threshold: float = 2.0,
                 sentiment_volatility_divergence_threshold: float = 0.3,
                 capacity_decay_rate: float = 0.1):
        """
        Initialize Volatility Capacitor.
        
        Args:
            volatility_threshold: Multiplier for volatility spike detection
            sentiment_volatility_divergence_threshold: Threshold for sentiment-volatility divergence
            capacity_decay_rate: Rate at which capacity decays during stress
        """
        self.vol_threshold = volatility_threshold
        self.divergence_threshold = sentiment_volatility_divergence_threshold
        self.decay_rate = capacity_decay_rate
        
        self.current_capacity = 1.0  # Full capacity initially
        self.stress_history: List[float] = []
        
    def update_capacity(self, 
                       current_volatility: float,
                       historical_volatility: float,
                       market_sentiment: float,
                       news_sentiment: float) -> Dict:
        """
        Update volatility capacity based on current market conditions.
        
        Args:
            current_volatility: Current market volatility
            historical_volatility: Historical average volatility
            market_sentiment: Market sentiment score (-1 to 1)
            news_sentiment: News sentiment score (-1 to 1)
            
        Returns:
            Dictionary with capacity update results
        """
        # Calculate volatility stress
        vol_stress = self._calculate_volatility_stress(current_volatility, historical_volatility)
        
        # Calculate sentiment-volatility divergence
        sentiment_divergence = self._calculate_sentiment_divergence(
            current_volatility, market_sentiment, news_sentiment
        )
        
        # Calculate overall stress level
        overall_stress = max(vol_stress, sentiment_divergence)
        self.stress_history.append(overall_stress)
        
        # Keep only recent stress history
        if len(self.stress_history) > 50:
            self.stress_history = self.stress_history[-50:]
        
        # Update capacity based on stress
        if overall_stress > 0.5:
            # Reduce capacity during stress
            capacity_reduction = overall_stress * self.decay_rate
            self.current_capacity = max(0.1, self.current_capacity - capacity_reduction)
        else:
            # Gradually restore capacity during calm periods
            capacity_restoration = (1 - overall_stress) * self.decay_rate * 0.5
            self.current_capacity = min(1.0, self.current_capacity + capacity_restoration)
        
        return {
            'current_capacity': self.current_capacity,
            'volatility_stress': vol_stress,
            'sentiment_divergence': sentiment_divergence,
            'overall_stress': overall_stress,
            'recommended_exposure': self.current_capacity,
            'stress_trend': self._calculate_stress_trend()
        }
    
    def _calculate_volatility_stress(self, current_vol: float, historical_vol: float) -> float:
        """Calculate stress level based on volatility spike."""
        if historical_vol == 0:
            return 0.0
        
        vol_ratio = current_vol / historical_vol
        
        # Stress increases exponentially with volatility ratio
        if vol_ratio > self.vol_threshold:
            stress = min(1.0, (vol_ratio - 1.0) / self.vol_threshold)
        else:
            stress = 0.0
        
        return stress
    
    def _calculate_sentiment_divergence(self, 
                                      volatility: float,
                                      market_sentiment: float,
                                      news_sentiment: float) -> float:
        """Calculate divergence between sentiment and volatility."""
        # Average sentiment
        avg_sentiment = (market_sentiment + news_sentiment) / 2
        
        # Normalize volatility to [-1, 1] range (assuming volatility is positive)
        # High volatility should correspond to negative sentiment in stable markets
        vol_sentiment = -min(1.0, volatility / 0.05)  # Assuming 5% is high volatility
        
        # Calculate divergence
        divergence = abs(avg_sentiment - vol_sentiment)
        
        # Return stress level based on divergence
        return min(1.0, divergence / 2.0)  # Normalize to [0, 1]
    
    def _calculate_stress_trend(self) -> str:
        """Calculate trend in stress levels."""
        if len(self.stress_history) < 10:
            return 'insufficient_data'
        
        recent_stress = np.mean(self.stress_history[-5:])
        older_stress = np.mean(self.stress_history[-10:-5])
        
        if recent_stress > older_stress * 1.2:
            return 'increasing'
        elif recent_stress < older_stress * 0.8:
            return 'decreasing'
        else:
            return 'stable'
    
    def get_position_size_multiplier(self) -> float:
        """Get position size multiplier based on current capacity."""
        return self.current_capacity
    
    def should_reduce_exposure(self) -> Tuple[bool, str]:
        """
        Determine if exposure should be reduced.
        
        Returns:
            Tuple of (should_reduce, reason)
        """
        if self.current_capacity < 0.3:
            return True, "severe_volatility_stress"
        elif self.current_capacity < 0.5:
            return True, "moderate_volatility_stress"
        elif len(self.stress_history) >= 5 and np.mean(self.stress_history[-5:]) > 0.7:
            return True, "sustained_high_stress"
        else:
            return False, "normal_conditions"
