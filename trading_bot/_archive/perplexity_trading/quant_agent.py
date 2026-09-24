"""
Quantitative Analysis Agent for Perplexity Trading Architecture
============================================================

Advanced quantitative analysis agent that performs:
- Statistical arbitrage detection
- Factor model analysis
- Machine learning predictions
- Risk-adjusted return optimization
- Regime detection and adaptation
- Alpha generation and decay analysis
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import asyncio

from .core_types import (
    SubTask,
    SubTaskResult,
    Citation,
    AgentType,
    RetrievalSource,
)
from .trading_agents import BaseTradingAgent, AgentContext

logger = logging.getLogger(__name__)


class QuantStrategy(Enum):
    """Quantitative strategy types"""
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    STAT_ARB = "statistical_arbitrage"
    FACTOR = "factor_model"
    ML_ENSEMBLE = "ml_ensemble"
    VOLATILITY = "volatility"
    PAIRS_TRADING = "pairs_trading"
    MARKET_MAKING = "market_making"


class RegimeType(Enum):
    """Market regime types"""
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    MEAN_REVERTING = "mean_reverting"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    CRISIS = "crisis"
    RECOVERY = "recovery"
    UNKNOWN = "unknown"


@dataclass
class QuantSignal:
    """Quantitative trading signal"""
    strategy: QuantStrategy
    direction: float  # -1 to 1
    strength: float   # 0 to 1
    confidence: float # 0 to 1
    half_life: float  # Expected signal decay in hours
    sharpe_estimate: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FactorExposure:
    """Factor exposure analysis"""
    factor_name: str
    exposure: float
    t_stat: float
    contribution: float


class QuantAgent(BaseTradingAgent):
    """
    Advanced Quantitative Analysis Agent
    
    Capabilities:
    - Statistical analysis (z-scores, cointegration, correlation)
    - Factor model decomposition
    - Regime detection using HMM-style analysis
    - Alpha signal generation
    - Risk-adjusted optimization
    - Machine learning ensemble predictions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.agent_type = AgentType.REASONING  # Uses reasoning type for complex analysis
        self.name = "Quant Agent"
        self.description = "Advanced quantitative analysis and alpha generation"
        
        # Strategy weights (adaptive)
        self.strategy_weights = {
            QuantStrategy.MEAN_REVERSION: 0.20,
            QuantStrategy.MOMENTUM: 0.20,
            QuantStrategy.STAT_ARB: 0.15,
            QuantStrategy.FACTOR: 0.15,
            QuantStrategy.ML_ENSEMBLE: 0.15,
            QuantStrategy.VOLATILITY: 0.15,
        }
        
        # Regime-specific adjustments
        self.regime_adjustments = {
            RegimeType.TRENDING_BULL: {'momentum': 1.5, 'mean_reversion': 0.5},
            RegimeType.TRENDING_BEAR: {'momentum': 1.5, 'mean_reversion': 0.5},
            RegimeType.MEAN_REVERTING: {'momentum': 0.5, 'mean_reversion': 1.5},
            RegimeType.HIGH_VOLATILITY: {'volatility': 1.5, 'momentum': 0.7},
            RegimeType.LOW_VOLATILITY: {'mean_reversion': 1.3, 'volatility': 0.7},
            RegimeType.CRISIS: {'momentum': 0.3, 'mean_reversion': 0.3, 'volatility': 0.5},
        }
        
        # Performance tracking per strategy
        self.strategy_performance: Dict[QuantStrategy, Dict[str, float]] = {}
    
    async def analyze(self, context: AgentContext) -> SubTaskResult:
        """Execute comprehensive quantitative analysis"""
        start_time = datetime.utcnow()
        citations = []
        
        try:
            # Validate inputs
            is_valid, error = self.validate_inputs(context)
            if not is_valid:
                return SubTaskResult(
                    subtask_id=context.subtask.id,
                    success=False,
                    error=error,
                )
            
            output_data = {}
            reasoning_parts = []
            
            # Get market data
            ohlcv = context.input_data.get('ohlcv_data', context.market_data)
            if not ohlcv:
                ohlcv = context.input_data.get('ohlcv', [])
            
            if not ohlcv or len(ohlcv) < 50:
                return SubTaskResult(
                    subtask_id=context.subtask.id,
                    success=False,
                    error="Insufficient data for quantitative analysis (need 50+ bars)",
                )
            
            # Extract price series
            closes = np.array([bar.get('close', 0) for bar in ohlcv[-200:]])
            highs = np.array([bar.get('high', 0) for bar in ohlcv[-200:]])
            lows = np.array([bar.get('low', 0) for bar in ohlcv[-200:]])
            volumes = np.array([bar.get('volume', 0) for bar in ohlcv[-200:]])
            
            # 1. Detect market regime
            regime = await self._detect_regime(closes, volumes)
            output_data['regime'] = regime.value
            reasoning_parts.append(f"Detected regime: {regime.value}")
            citations.append(self.create_citation(
                RetrievalSource.CALCULATION,
                "Regime Detection",
                f"Market regime: {regime.value}",
                confidence=0.85,
            ))
            
            # 2. Generate signals from each strategy
            signals: List[QuantSignal] = []
            
            # Mean Reversion Signal
            mr_signal = await self._mean_reversion_signal(closes)
            signals.append(mr_signal)
            reasoning_parts.append(f"Mean Reversion: {mr_signal.direction:.2f} (conf: {mr_signal.confidence:.0%})")
            
            # Momentum Signal
            mom_signal = await self._momentum_signal(closes, volumes)
            signals.append(mom_signal)
            reasoning_parts.append(f"Momentum: {mom_signal.direction:.2f} (conf: {mom_signal.confidence:.0%})")
            
            # Volatility Signal
            vol_signal = await self._volatility_signal(closes, highs, lows)
            signals.append(vol_signal)
            reasoning_parts.append(f"Volatility: {vol_signal.direction:.2f} (conf: {vol_signal.confidence:.0%})")
            
            # Factor Model Signal
            factor_signal = await self._factor_model_signal(closes, volumes, context.input_data)
            signals.append(factor_signal)
            reasoning_parts.append(f"Factor Model: {factor_signal.direction:.2f} (conf: {factor_signal.confidence:.0%})")
            
            # ML Ensemble Signal
            ml_signal = await self._ml_ensemble_signal(closes, highs, lows, volumes)
            signals.append(ml_signal)
            reasoning_parts.append(f"ML Ensemble: {ml_signal.direction:.2f} (conf: {ml_signal.confidence:.0%})")
            
            # 3. Combine signals with regime-adjusted weights
            combined_signal = await self._combine_signals(signals, regime)
            output_data['quant_signals'] = [
                {
                    'strategy': s.strategy.value,
                    'direction': s.direction,
                    'strength': s.strength,
                    'confidence': s.confidence,
                    'sharpe_estimate': s.sharpe_estimate,
                }
                for s in signals
            ]
            output_data['combined_signal'] = combined_signal
            
            # 4. Calculate risk metrics
            risk_metrics = await self._calculate_risk_metrics(closes, combined_signal)
            output_data['risk_metrics'] = risk_metrics
            reasoning_parts.append(f"Risk-adjusted signal: {combined_signal['direction']:.2f}")
            
            # 5. Generate alpha estimate
            alpha_estimate = await self._estimate_alpha(signals, regime, risk_metrics)
            output_data['alpha_estimate'] = alpha_estimate
            reasoning_parts.append(f"Alpha estimate: {alpha_estimate['expected_return']:.2%} (decay: {alpha_estimate['half_life_hours']:.1f}h)")
            
            citations.append(self.create_citation(
                RetrievalSource.CALCULATION,
                "Quantitative Analysis",
                f"Combined signal: {combined_signal['direction']:.2f}, Alpha: {alpha_estimate['expected_return']:.2%}",
                confidence=combined_signal['confidence'],
            ))
            
            # 6. Determine trading signal
            if combined_signal['direction'] > 0.3:
                output_data['trading_signal'] = 'BUY'
            elif combined_signal['direction'] < -0.3:
                output_data['trading_signal'] = 'SELL'
            else:
                output_data['trading_signal'] = 'HOLD'
            
            output_data['signal_strength'] = abs(combined_signal['direction'])
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return SubTaskResult(
                subtask_id=context.subtask.id,
                success=True,
                output_data=output_data,
                citations=citations,
                confidence=combined_signal['confidence'],
                reasoning=" | ".join(reasoning_parts),
                execution_time_ms=execution_time,
            )
            
        except Exception as e:
            logger.error(f"Quant agent error: {e}", exc_info=True)
            return SubTaskResult(
                subtask_id=context.subtask.id,
                success=False,
                error=str(e),
            )
    
    async def _detect_regime(self, closes: np.ndarray, volumes: np.ndarray) -> RegimeType:
        """Detect current market regime using statistical analysis"""
        if len(closes) < 50:
            return RegimeType.UNKNOWN
        
        # Calculate returns
        returns = np.diff(closes) / closes[:-1]
        
        # Trend detection
        ma_20 = np.mean(closes[-20:])
        ma_50 = np.mean(closes[-50:])
        price = closes[-1]
        
        # Volatility analysis
        recent_vol = np.std(returns[-20:]) * np.sqrt(252)
        historical_vol = np.std(returns[-50:]) * np.sqrt(252)
        vol_ratio = recent_vol / historical_vol if historical_vol > 0 else 1.0
        
        # Mean reversion test (Hurst exponent approximation)
        hurst = self._estimate_hurst(closes[-50:])
        
        # Determine regime
        if vol_ratio > 1.5:
            if np.mean(returns[-10:]) < -0.02:
                return RegimeType.CRISIS
            return RegimeType.HIGH_VOLATILITY
        
        if vol_ratio < 0.7:
            return RegimeType.LOW_VOLATILITY
        
        if hurst < 0.4:
            return RegimeType.MEAN_REVERTING
        
        if price > ma_20 > ma_50:
            return RegimeType.TRENDING_BULL
        elif price < ma_20 < ma_50:
            return RegimeType.TRENDING_BEAR
        
        return RegimeType.UNKNOWN
    
    def _estimate_hurst(self, prices: np.ndarray) -> float:
        """Estimate Hurst exponent (simplified R/S analysis)"""
        if len(prices) < 20:
            return 0.5
        
        returns = np.diff(np.log(prices))
        n = len(returns)
        
        # Simplified Hurst estimation
        mean_return = np.mean(returns)
        cumulative = np.cumsum(returns - mean_return)
        
        r = np.max(cumulative) - np.min(cumulative)
        s = np.std(returns)
        
        if s == 0 or r == 0:
            return 0.5
        
        # R/S statistic
        rs = r / s
        
        # Approximate Hurst from R/S
        hurst = np.log(rs) / np.log(n) if n > 1 else 0.5
        
        return max(0.0, min(1.0, hurst))
    
    async def _mean_reversion_signal(self, closes: np.ndarray) -> QuantSignal:
        """Generate mean reversion signal using z-score"""
        if len(closes) < 50:
            return QuantSignal(
                strategy=QuantStrategy.MEAN_REVERSION,
                direction=0.0, strength=0.0, confidence=0.3,
                half_life=24.0, sharpe_estimate=0.0,
            )
        
        # Calculate z-score
        mean = np.mean(closes[-50:])
        std = np.std(closes[-50:])
        
        if std == 0:
            return QuantSignal(
                strategy=QuantStrategy.MEAN_REVERSION,
                direction=0.0, strength=0.0, confidence=0.3,
                half_life=24.0, sharpe_estimate=0.0,
            )
        
        z_score = (closes[-1] - mean) / std
        
        # Signal: negative z-score = buy (expect reversion up)
        direction = -np.tanh(z_score / 2)  # Bounded between -1 and 1
        strength = min(abs(z_score) / 3, 1.0)
        
        # Confidence based on historical mean reversion success
        confidence = 0.5 + 0.3 * strength if abs(z_score) > 1.5 else 0.4
        
        # Estimate half-life using Ornstein-Uhlenbeck
        half_life = self._estimate_half_life(closes[-50:])
        
        # Sharpe estimate
        expected_return = direction * std * 0.5  # Conservative estimate
        sharpe = expected_return / std * np.sqrt(252) if std > 0 else 0
        
        return QuantSignal(
            strategy=QuantStrategy.MEAN_REVERSION,
            direction=direction,
            strength=strength,
            confidence=confidence,
            half_life=half_life,
            sharpe_estimate=sharpe,
            metadata={'z_score': z_score, 'mean': mean, 'std': std},
        )
    
    def _estimate_half_life(self, prices: np.ndarray) -> float:
        """Estimate mean reversion half-life"""
        if len(prices) < 20:
            return 24.0
        
        # Simple AR(1) estimation
        y = prices[1:]
        x = prices[:-1]
        
        # OLS regression
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        
        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        
        if denominator == 0:
            return 24.0
        
        beta = numerator / denominator
        
        # Half-life = -log(2) / log(beta)
        if beta <= 0 or beta >= 1:
            return 24.0
        
        half_life = -np.log(2) / np.log(beta)
        
        return max(1.0, min(168.0, half_life))  # Clamp between 1h and 1 week
    
    async def _momentum_signal(self, closes: np.ndarray, volumes: np.ndarray) -> QuantSignal:
        """Generate momentum signal"""
        if len(closes) < 50:
            return QuantSignal(
                strategy=QuantStrategy.MOMENTUM,
                direction=0.0, strength=0.0, confidence=0.3,
                half_life=48.0, sharpe_estimate=0.0,
            )
        
        # Multiple timeframe momentum
        mom_5 = (closes[-1] - closes[-5]) / closes[-5] if closes[-5] != 0 else 0
        mom_10 = (closes[-1] - closes[-10]) / closes[-10] if closes[-10] != 0 else 0
        mom_20 = (closes[-1] - closes[-20]) / closes[-20] if closes[-20] != 0 else 0
        
        # Volume-weighted momentum
        if len(volumes) >= 20 and np.sum(volumes[-20:]) > 0:
            vol_weight = volumes[-20:] / np.sum(volumes[-20:])
            returns = np.diff(closes[-21:]) / closes[-21:-1]
            vol_weighted_mom = np.sum(returns * vol_weight)
        else:
            vol_weighted_mom = mom_20
        
        # Combine momentum signals
        combined_mom = 0.3 * mom_5 + 0.3 * mom_10 + 0.2 * mom_20 + 0.2 * vol_weighted_mom
        
        # Normalize to -1 to 1
        direction = np.tanh(combined_mom * 20)  # Scale factor
        strength = min(abs(combined_mom) * 10, 1.0)
        
        # Confidence based on momentum consistency
        mom_signs = [np.sign(mom_5), np.sign(mom_10), np.sign(mom_20)]
        consistency = abs(sum(mom_signs)) / 3
        confidence = 0.4 + 0.4 * consistency
        
        # Sharpe estimate
        returns = np.diff(closes[-50:]) / closes[-50:-1]
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        return QuantSignal(
            strategy=QuantStrategy.MOMENTUM,
            direction=direction,
            strength=strength,
            confidence=confidence,
            half_life=48.0,  # Momentum typically has longer decay
            sharpe_estimate=sharpe,
            metadata={'mom_5': mom_5, 'mom_10': mom_10, 'mom_20': mom_20},
        )
    
    async def _volatility_signal(self, closes: np.ndarray, highs: np.ndarray, lows: np.ndarray) -> QuantSignal:
        """Generate volatility-based signal"""
        if len(closes) < 50:
            return QuantSignal(
                strategy=QuantStrategy.VOLATILITY,
                direction=0.0, strength=0.0, confidence=0.3,
                half_life=12.0, sharpe_estimate=0.0,
            )
        
        # Calculate ATR
        tr = np.maximum(
            highs[-20:] - lows[-20:],
            np.maximum(
                np.abs(highs[-20:] - closes[-21:-1]),
                np.abs(lows[-20:] - closes[-21:-1])
            )
        )
        atr = np.mean(tr)
        
        # Volatility regime
        returns = np.diff(closes) / closes[:-1]
        recent_vol = np.std(returns[-20:])
        historical_vol = np.std(returns[-50:])
        
        vol_ratio = recent_vol / historical_vol if historical_vol > 0 else 1.0
        
        # Volatility mean reversion signal
        # High vol tends to revert down, low vol tends to expand
        vol_signal = -np.tanh((vol_ratio - 1) * 2)
        
        # Direction based on volatility regime
        # In high vol: prefer short or neutral
        # In low vol: prefer long (vol expansion often accompanies moves)
        if vol_ratio > 1.3:
            direction = -0.3  # Slight bearish bias in high vol
        elif vol_ratio < 0.7:
            direction = 0.2   # Slight bullish bias in low vol
        else:
            direction = 0.0
        
        strength = abs(vol_ratio - 1)
        confidence = 0.5 + 0.2 * min(strength, 1.0)
        
        return QuantSignal(
            strategy=QuantStrategy.VOLATILITY,
            direction=direction,
            strength=min(strength, 1.0),
            confidence=confidence,
            half_life=12.0,
            sharpe_estimate=0.0,  # Vol signals are more about risk management
            metadata={'atr': atr, 'vol_ratio': vol_ratio, 'recent_vol': recent_vol},
        )
    
    async def _factor_model_signal(
        self,
        closes: np.ndarray,
        volumes: np.ndarray,
        input_data: Dict[str, Any],
    ) -> QuantSignal:
        """Generate factor model signal"""
        factors: List[FactorExposure] = []
        
        # Value factor (mean reversion proxy)
        if len(closes) >= 50:
            z_score = (closes[-1] - np.mean(closes[-50:])) / np.std(closes[-50:])
            factors.append(FactorExposure(
                factor_name="value",
                exposure=-z_score * 0.1,
                t_stat=abs(z_score),
                contribution=-z_score * 0.1 * 0.3,
            ))
        
        # Momentum factor
        if len(closes) >= 20:
            mom = (closes[-1] - closes[-20]) / closes[-20]
            factors.append(FactorExposure(
                factor_name="momentum",
                exposure=mom,
                t_stat=abs(mom) / 0.05,  # Rough t-stat
                contribution=mom * 0.3,
            ))
        
        # Size factor (volume proxy)
        if len(volumes) >= 20:
            vol_z = (volumes[-1] - np.mean(volumes[-20:])) / (np.std(volumes[-20:]) + 1)
            factors.append(FactorExposure(
                factor_name="liquidity",
                exposure=vol_z * 0.05,
                t_stat=abs(vol_z),
                contribution=vol_z * 0.05 * 0.2,
            ))
        
        # Volatility factor
        if len(closes) >= 50:
            returns = np.diff(closes) / closes[:-1]
            vol = np.std(returns[-20:])
            hist_vol = np.std(returns[-50:])
            vol_factor = (vol - hist_vol) / hist_vol if hist_vol > 0 else 0
            factors.append(FactorExposure(
                factor_name="volatility",
                exposure=-vol_factor * 0.1,  # Negative exposure to vol
                t_stat=abs(vol_factor) / 0.2,
                contribution=-vol_factor * 0.1 * 0.2,
            ))
        
        # Combine factor contributions
        total_contribution = sum(f.contribution for f in factors)
        direction = np.tanh(total_contribution * 5)
        
        # Confidence based on t-stats
        avg_t_stat = np.mean([f.t_stat for f in factors]) if factors else 0
        confidence = min(0.4 + 0.1 * avg_t_stat, 0.85)
        
        return QuantSignal(
            strategy=QuantStrategy.FACTOR,
            direction=direction,
            strength=min(abs(total_contribution) * 5, 1.0),
            confidence=confidence,
            half_life=36.0,
            sharpe_estimate=total_contribution * 2,  # Rough estimate
            metadata={'factors': [f.__dict__ for f in factors]},
        )
    
    async def _ml_ensemble_signal(
        self,
        closes: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        volumes: np.ndarray,
    ) -> QuantSignal:
        """Generate ML ensemble signal (simplified without actual ML)"""
        if len(closes) < 50:
            return QuantSignal(
                strategy=QuantStrategy.ML_ENSEMBLE,
                direction=0.0, strength=0.0, confidence=0.3,
                half_life=24.0, sharpe_estimate=0.0,
            )
        
        # Feature engineering
        features = {}
        
        # Price features
        features['return_1'] = (closes[-1] - closes[-2]) / closes[-2]
        features['return_5'] = (closes[-1] - closes[-5]) / closes[-5]
        features['return_20'] = (closes[-1] - closes[-20]) / closes[-20]
        
        # Volatility features
        returns = np.diff(closes) / closes[:-1]
        features['vol_5'] = np.std(returns[-5:])
        features['vol_20'] = np.std(returns[-20:])
        features['vol_ratio'] = features['vol_5'] / features['vol_20'] if features['vol_20'] > 0 else 1
        
        # Volume features
        features['vol_ma_ratio'] = volumes[-1] / np.mean(volumes[-20:]) if np.mean(volumes[-20:]) > 0 else 1
        
        # Technical features
        features['rsi'] = self._calculate_rsi(closes[-15:])
        features['ma_cross'] = 1 if np.mean(closes[-5:]) > np.mean(closes[-20:]) else -1
        
        # Simple "ensemble" prediction (weighted combination)
        # In production, this would be actual ML models
        predictions = []
        
        # "Model 1": Momentum-based
        pred1 = np.tanh(features['return_5'] * 20)
        predictions.append(pred1)
        
        # "Model 2": Mean reversion
        z_score = (closes[-1] - np.mean(closes[-50:])) / np.std(closes[-50:])
        pred2 = -np.tanh(z_score / 2)
        predictions.append(pred2)
        
        # "Model 3": RSI-based
        pred3 = (50 - features['rsi']) / 50  # Normalized RSI signal
        predictions.append(pred3)
        
        # "Model 4": Volume-price
        pred4 = features['vol_ma_ratio'] * features['return_1'] * 10
        predictions.append(np.tanh(pred4))
        
        # Ensemble average
        direction = np.mean(predictions)
        
        # Confidence from prediction agreement
        pred_std = np.std(predictions)
        confidence = max(0.3, 0.7 - pred_std)
        
        return QuantSignal(
            strategy=QuantStrategy.ML_ENSEMBLE,
            direction=direction,
            strength=min(abs(direction), 1.0),
            confidence=confidence,
            half_life=24.0,
            sharpe_estimate=direction * 1.5,  # Rough estimate
            metadata={'features': features, 'predictions': predictions},
        )
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    async def _combine_signals(
        self,
        signals: List[QuantSignal],
        regime: RegimeType,
    ) -> Dict[str, Any]:
        """Combine signals with regime-adjusted weights"""
        if not signals:
            return {'direction': 0.0, 'strength': 0.0, 'confidence': 0.3}
        
        # Get regime adjustments
        adjustments = self.regime_adjustments.get(regime, {})
        
        # Calculate weighted signal
        total_weight = 0.0
        weighted_direction = 0.0
        weighted_confidence = 0.0
        
        for signal in signals:
            base_weight = self.strategy_weights.get(signal.strategy, 0.1)
            
            # Apply regime adjustment
            strategy_key = signal.strategy.value.split('_')[0]  # Get first word
            regime_mult = adjustments.get(strategy_key, 1.0)
            
            # Confidence-weighted
            weight = base_weight * regime_mult * signal.confidence
            
            weighted_direction += signal.direction * weight
            weighted_confidence += signal.confidence * weight
            total_weight += weight
        
        if total_weight > 0:
            final_direction = weighted_direction / total_weight
            final_confidence = weighted_confidence / total_weight
        else:
            final_direction = 0.0
            final_confidence = 0.3
        
        return {
            'direction': final_direction,
            'strength': min(abs(final_direction), 1.0),
            'confidence': final_confidence,
            'regime': regime.value,
            'signal_count': len(signals),
        }
    
    async def _calculate_risk_metrics(
        self,
        closes: np.ndarray,
        combined_signal: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate risk metrics for the signal"""
        returns = np.diff(closes) / closes[:-1]
        
        # VaR (95%)
        var_95 = np.percentile(returns, 5)
        
        # CVaR (Expected Shortfall)
        cvar = np.mean(returns[returns <= var_95])
        
        # Max drawdown
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdowns)
        
        # Sharpe ratio
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # Sortino ratio
        downside_returns = returns[returns < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else np.std(returns)
        sortino = np.mean(returns) / downside_std * np.sqrt(252) if downside_std > 0 else 0
        
        return {
            'var_95': var_95,
            'cvar': cvar,
            'max_drawdown': max_drawdown,
            'sharpe': sharpe,
            'sortino': sortino,
            'volatility': np.std(returns) * np.sqrt(252),
        }
    
    async def _estimate_alpha(
        self,
        signals: List[QuantSignal],
        regime: RegimeType,
        risk_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Estimate expected alpha from signals"""
        # Average expected return from signals
        expected_returns = [s.direction * s.sharpe_estimate / np.sqrt(252) for s in signals]
        avg_expected_return = np.mean(expected_returns) if expected_returns else 0
        
        # Average half-life
        half_lives = [s.half_life for s in signals]
        avg_half_life = np.mean(half_lives) if half_lives else 24.0
        
        # Regime adjustment
        regime_mult = {
            RegimeType.TRENDING_BULL: 1.2,
            RegimeType.TRENDING_BEAR: 1.2,
            RegimeType.MEAN_REVERTING: 1.1,
            RegimeType.HIGH_VOLATILITY: 0.7,
            RegimeType.LOW_VOLATILITY: 0.9,
            RegimeType.CRISIS: 0.3,
            RegimeType.RECOVERY: 1.0,
            RegimeType.UNKNOWN: 0.8,
        }.get(regime, 0.8)
        
        adjusted_return = avg_expected_return * regime_mult
        
        # Risk-adjusted alpha
        vol = risk_metrics.get('volatility', 0.15)
        risk_adjusted_alpha = adjusted_return / vol if vol > 0 else 0
        
        return {
            'expected_return': adjusted_return,
            'half_life_hours': avg_half_life,
            'regime_adjustment': regime_mult,
            'risk_adjusted_alpha': risk_adjusted_alpha,
            'confidence': np.mean([s.confidence for s in signals]) if signals else 0.3,
        }
