"""
AAMIS v3.0 - Advanced Risk Management System

This module implements:
1. Smart Capital Allocation
2. Volatility Targeting
3. Kelly / Anti-Kelly Allocation
4. Market Regime VaR
5. Stop-Distribution Optimization
6. Tail-Risk Hedging
7. Smart Position Pyramiding
8. Slippage Modeling
9. Spread Modeling
10. Trade Sequencing Logic
11. Adaptive Leverage Intelligence
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import random
from collections import deque
import numpy

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels"""
    MINIMAL = "MINIMAL"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class MarketRegime(Enum):
    """Market regime types"""
    LOW_VOL_TRENDING = "LOW_VOL_TRENDING"
    LOW_VOL_RANGING = "LOW_VOL_RANGING"
    HIGH_VOL_TRENDING = "HIGH_VOL_TRENDING"
    HIGH_VOL_RANGING = "HIGH_VOL_RANGING"
    CRISIS = "CRISIS"
    RECOVERY = "RECOVERY"


class AllocationMethod(Enum):
    """Capital allocation methods"""
    EQUAL_WEIGHT = "EQUAL_WEIGHT"
    RISK_PARITY = "RISK_PARITY"
    KELLY = "KELLY"
    ANTI_KELLY = "ANTI_KELLY"
    VOLATILITY_SCALED = "VOLATILITY_SCALED"
    REGIME_ADAPTIVE = "REGIME_ADAPTIVE"


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics"""
    var_95: float = 0.0  # Value at Risk (95%)
    var_99: float = 0.0  # Value at Risk (99%)
    cvar_95: float = 0.0  # Conditional VaR (95%)
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    tail_risk: float = 0.0
    correlation_risk: float = 0.0


@dataclass
class PositionSizing:
    """Position sizing recommendation"""
    base_size: float
    adjusted_size: float
    kelly_size: float
    volatility_adjusted_size: float
    regime_adjusted_size: float
    final_size: float
    confidence: float
    reasoning: List[str] = field(default_factory=list)


@dataclass
class StopLossOptimization:
    """Optimized stop loss parameters"""
    optimal_stop: float
    atr_based_stop: float
    volatility_stop: float
    support_based_stop: float
    trailing_stop: float
    time_stop: int  # seconds
    confidence: float


class SmartCapitalAllocator:
    """
    Smart Capital Allocation System
    Dynamically allocates capital based on multiple factors
    """
    
    def __init__(self, total_capital: float = 100000.0):
        self.total_capital = total_capital
        self.allocated_capital: Dict[str, float] = {}
        self.allocation_history: List[Dict] = []
        
    def allocate_capital(self, strategies: List[Dict], method: AllocationMethod = AllocationMethod.RISK_PARITY) -> Dict[str, float]:
        """Allocate capital across strategies"""
        logger.info(f"💰 Allocating capital using {method.value}")
        
        if method == AllocationMethod.EQUAL_WEIGHT:
            allocations = self._equal_weight_allocation(strategies)
        elif method == AllocationMethod.RISK_PARITY:
            allocations = self._risk_parity_allocation(strategies)
        elif method == AllocationMethod.KELLY:
            allocations = self._kelly_allocation(strategies)
        elif method == AllocationMethod.ANTI_KELLY:
            allocations = self._anti_kelly_allocation(strategies)
        elif method == AllocationMethod.VOLATILITY_SCALED:
            allocations = self._volatility_scaled_allocation(strategies)
        else:
            allocations = self._regime_adaptive_allocation(strategies)
        
        self.allocated_capital = allocations
        self.allocation_history.append({
            'timestamp': datetime.now(),
            'method': method.value,
            'allocations': allocations
        })
        
        return allocations
    
    def _equal_weight_allocation(self, strategies: List[Dict]) -> Dict[str, float]:
        """Equal weight allocation"""
        weight = 1.0 / len(strategies) if strategies else 0
        return {s['name']: self.total_capital * weight for s in strategies}
    
    def _risk_parity_allocation(self, strategies: List[Dict]) -> Dict[str, float]:
        """Risk parity allocation - equal risk contribution"""
        # Calculate inverse volatility weights
        volatilities = [s.get('volatility', 0.1) for s in strategies]
        inv_vols = [1.0 / v if v > 0 else 0 for v in volatilities]
        total_inv_vol = sum(inv_vols)
        
        weights = [iv / total_inv_vol if total_inv_vol > 0 else 0 for iv in inv_vols]
        
        return {s['name']: self.total_capital * w for s, w in zip(strategies, weights)}
    
    def _kelly_allocation(self, strategies: List[Dict]) -> Dict[str, float]:
        """Kelly criterion allocation"""
        allocations = {}
        
        for strategy in strategies:
            win_rate = strategy.get('win_rate', 0.5)
            win_loss_ratio = strategy.get('win_loss_ratio', 1.5)
            
            # Kelly formula: f* = (bp - q) / b
            # where b = win/loss ratio, p = win probability, q = 1-p
            b = win_loss_ratio
            p = win_rate
            q = 1 - p
            
            kelly_fraction = (b * p - q) / b if b > 0 else 0
            kelly_fraction = max(0, min(0.25, kelly_fraction))  # Cap at 25%
            
            allocations[strategy['name']] = self.total_capital * kelly_fraction
        
        return allocations
    
    def _anti_kelly_allocation(self, strategies: List[Dict]) -> Dict[str, float]:
        """Anti-Kelly allocation (conservative)"""
        kelly_allocations = self._kelly_allocation(strategies)
        
        # Use half-Kelly for safety
        return {name: alloc * 0.5 for name, alloc in kelly_allocations.items()}
    
    def _volatility_scaled_allocation(self, strategies: List[Dict]) -> Dict[str, float]:
        """Volatility-scaled allocation"""
        target_vol = 0.15  # 15% target volatility
        allocations = {}
        
        for strategy in strategies:
            strategy_vol = strategy.get('volatility', 0.1)
            vol_scalar = target_vol / strategy_vol if strategy_vol > 0 else 1.0
            vol_scalar = min(2.0, max(0.5, vol_scalar))  # Limit scaling
            
            base_weight = 1.0 / len(strategies)
            allocations[strategy['name']] = self.total_capital * base_weight * vol_scalar
        
        return allocations
    
    def _regime_adaptive_allocation(self, strategies: List[Dict]) -> Dict[str, float]:
        """Regime-adaptive allocation"""
        # Simplified: reduce allocation in high-vol regimes
        regime = strategies[0].get('regime', MarketRegime.LOW_VOL_TRENDING) if strategies else MarketRegime.LOW_VOL_TRENDING
        
        regime_multipliers = {
            MarketRegime.LOW_VOL_TRENDING: 1.0,
            MarketRegime.LOW_VOL_RANGING: 0.8,
            MarketRegime.HIGH_VOL_TRENDING: 0.7,
            MarketRegime.HIGH_VOL_RANGING: 0.5,
            MarketRegime.CRISIS: 0.2,
            MarketRegime.RECOVERY: 0.6
        }
        
        multiplier = regime_multipliers.get(regime, 0.5)
        base_allocations = self._risk_parity_allocation(strategies)
        
        return {name: alloc * multiplier for name, alloc in base_allocations.items()}


class VolatilityTargeter:
    """
    Volatility Targeting System
    Maintains consistent portfolio volatility
    """
    
    def __init__(self, target_volatility: float = 0.15):
        self.target_volatility = target_volatility
        self.volatility_history: deque = deque(maxlen=252)  # 1 year
        
    def calculate_position_scalar(self, current_volatility: float) -> float:
        """Calculate position scalar to target volatility"""
        if current_volatility <= 0:
            return 1.0
        
        scalar = self.target_volatility / current_volatility
        
        # Limit extreme scaling
        scalar = min(2.0, max(0.25, scalar))
        
        logger.info(f"📊 Volatility targeting: Current={current_volatility:.2%}, Target={self.target_volatility:.2%}, Scalar={scalar:.2f}")
        
        return scalar
    
    def update_volatility(self, returns: List[float]):
        """Update volatility estimate"""
        if returns:
            vol = np.std(returns) * np.sqrt(252)  # Annualized
            self.volatility_history.append(vol)
    
    def get_current_volatility(self) -> float:
        """Get current volatility estimate"""
        if not self.volatility_history:
            return self.target_volatility
        return np.mean(list(self.volatility_history)[-20:])  # 20-day average


class KellyCalculator:
    """
    Kelly Criterion Calculator
    Optimal position sizing based on edge and odds
    """
    
    def __init__(self):
        self.kelly_history: List[Dict] = []
        
    def calculate_kelly(self, win_rate: float, win_loss_ratio: float, 
                       confidence: float = 1.0) -> Dict:
        """Calculate Kelly fraction"""
        # Kelly formula: f* = (bp - q) / b
        b = win_loss_ratio
        p = win_rate
        q = 1 - p
        
        full_kelly = (b * p - q) / b if b > 0 else 0
        
        # Adjust for confidence
        adjusted_kelly = full_kelly * confidence
        
        # Calculate fractional Kelly options
        result = {
            'full_kelly': max(0, full_kelly),
            'half_kelly': max(0, full_kelly * 0.5),
            'quarter_kelly': max(0, full_kelly * 0.25),
            'confidence_adjusted': max(0, adjusted_kelly),
            'recommended': max(0, min(0.25, full_kelly * 0.5)),  # Half-Kelly capped at 25%
            'edge': b * p - q,
            'is_positive_edge': (b * p - q) > 0
        }
        
        self.kelly_history.append({
            'timestamp': datetime.now(),
            'win_rate': win_rate,
            'win_loss_ratio': win_loss_ratio,
            'result': result
        })
        
        logger.info(f"🎯 Kelly: Full={result['full_kelly']:.2%}, Recommended={result['recommended']:.2%}, Edge={result['edge']:.3f}")
        
        return result


class RegimeVaRCalculator:
    """
    Market Regime-Aware VaR Calculator
    Adjusts VaR based on current market regime
    """
    
    def __init__(self):
        self.var_history: List[Dict] = []
        
    def calculate_regime_var(self, returns: List[float], regime: MarketRegime, 
                            confidence_level: float = 0.95) -> Dict:
        """Calculate regime-adjusted VaR"""
        if not returns:
            return {'var': 0, 'cvar': 0, 'regime_multiplier': 1.0}
        
        # Base VaR calculation
        sorted_returns = sorted(returns)
        var_index = int(len(sorted_returns) * (1 - confidence_level))
        base_var = abs(sorted_returns[var_index]) if var_index < len(sorted_returns) else 0
        
        # CVaR (Expected Shortfall)
        cvar = abs(np.mean(sorted_returns[:var_index])) if var_index > 0 else base_var
        
        # Regime multipliers
        regime_multipliers = {
            MarketRegime.LOW_VOL_TRENDING: 1.0,
            MarketRegime.LOW_VOL_RANGING: 1.2,
            MarketRegime.HIGH_VOL_TRENDING: 1.5,
            MarketRegime.HIGH_VOL_RANGING: 1.8,
            MarketRegime.CRISIS: 3.0,
            MarketRegime.RECOVERY: 1.3
        }
        
        multiplier = regime_multipliers.get(regime, 1.5)
        
        result = {
            'base_var': base_var,
            'regime_var': base_var * multiplier,
            'cvar': cvar,
            'regime_cvar': cvar * multiplier,
            'regime': regime.value,
            'regime_multiplier': multiplier,
            'confidence_level': confidence_level
        }
        
        self.var_history.append({
            'timestamp': datetime.now(),
            'result': result
        })
        
        logger.info(f"📉 Regime VaR: Base={base_var:.2%}, Adjusted={result['regime_var']:.2%} ({regime.value})")
        
        return result


class StopLossOptimizer:
    """
    Stop Loss Distribution Optimizer
    Finds optimal stop loss placement
    """
    
    def __init__(self):
        self.optimization_history: List[Dict] = []
        
    def optimize_stop_loss(self, entry_price: float, volatility: float, 
                          atr: float, support_levels: List[float] = None) -> StopLossOptimization:
        """Optimize stop loss placement"""
        # ATR-based stop (2x ATR)
        atr_stop = entry_price - (2 * atr)
        
        # Volatility-based stop (2 standard deviations)
        vol_stop = entry_price * (1 - 2 * volatility)
        
        # Support-based stop (below nearest support)
        if support_levels:
            nearest_support = max([s for s in support_levels if s < entry_price], default=entry_price * 0.98)
            support_stop = nearest_support * 0.995  # Just below support
        else:
            support_stop = entry_price * 0.98
        
        # Trailing stop (1.5x ATR)
        trailing_stop = entry_price - (1.5 * atr)
        
        # Time stop (max hold time)
        time_stop = 3600 * 24  # 24 hours default
        
        # Optimal stop (weighted average)
        optimal_stop = (atr_stop * 0.4 + vol_stop * 0.3 + support_stop * 0.3)
        
        result = StopLossOptimization(
            optimal_stop=optimal_stop,
            atr_based_stop=atr_stop,
            volatility_stop=vol_stop,
            support_based_stop=support_stop,
            trailing_stop=trailing_stop,
            time_stop=time_stop,
            confidence=0.75
        )
        
        self.optimization_history.append({
            'timestamp': datetime.now(),
            'entry_price': entry_price,
            'result': result
        })
        
        logger.info(f"🛑 Stop Optimization: Optimal={optimal_stop:.5f}, ATR={atr_stop:.5f}, Vol={vol_stop:.5f}")
        
        return result


class TailRiskHedger:
    """
    Tail Risk Hedging System
    Protects against extreme market events
    """
    
    def __init__(self):
        self.hedge_positions: List[Dict] = []
        
    def calculate_hedge_requirement(self, portfolio_value: float, 
                                   tail_risk_exposure: float) -> Dict:
        """Calculate required hedge for tail risk"""
        # Target: protect against 20% drawdown
        max_acceptable_loss = portfolio_value * 0.20
        
        # Current tail risk exposure
        potential_tail_loss = portfolio_value * tail_risk_exposure
        
        # Hedge requirement
        hedge_needed = max(0, potential_tail_loss - max_acceptable_loss)
        
        # Hedge instruments
        hedge_options = {
            'put_options': {
                'notional': hedge_needed,
                'strike_delta': 0.25,  # 25-delta puts
                'estimated_cost': hedge_needed * 0.02  # ~2% premium
            },
            'vix_calls': {
                'notional': hedge_needed * 0.5,
                'estimated_cost': hedge_needed * 0.01
            },
            'inverse_etf': {
                'notional': hedge_needed * 0.3,
                'estimated_cost': hedge_needed * 0.001  # Low cost
            }
        }
        
        result = {
            'portfolio_value': portfolio_value,
            'tail_risk_exposure': tail_risk_exposure,
            'potential_tail_loss': potential_tail_loss,
            'hedge_needed': hedge_needed,
            'hedge_options': hedge_options,
            'recommended_hedge': 'put_options' if hedge_needed > portfolio_value * 0.1 else 'inverse_etf'
        }
        
        logger.info(f"🛡️ Tail Risk Hedge: Exposure={tail_risk_exposure:.2%}, Hedge Needed=${hedge_needed:,.0f}")
        
        return result


class PositionPyramider:
    """
    Smart Position Pyramiding System
    Adds to winning positions intelligently
    """
    
    def __init__(self):
        self.pyramid_history: List[Dict] = []
        
    def calculate_pyramid_levels(self, entry_price: float, direction: str,
                                atr: float, max_additions: int = 3) -> List[Dict]:
        """Calculate pyramid entry levels"""
        levels = []
        
        for i in range(max_additions):
            if direction == 'LONG':
                # Add on pullbacks in uptrend
                level_price = entry_price + (atr * (i + 1) * 0.5)
                stop_price = entry_price - (atr * 1.5)
            else:
                # Add on rallies in downtrend
                level_price = entry_price - (atr * (i + 1) * 0.5)
                stop_price = entry_price + (atr * 1.5)
            
            # Decreasing size for each level
            size_multiplier = 1.0 / (i + 1)
            
            levels.append({
                'level': i + 1,
                'price': level_price,
                'size_multiplier': size_multiplier,
                'stop_price': stop_price,
                'profit_target': entry_price + (atr * (i + 2) * 2) if direction == 'LONG' else entry_price - (atr * (i + 2) * 2)
            })
        
        logger.info(f"📈 Pyramid Levels: {len(levels)} levels calculated for {direction}")
        
        return levels


class SlippageModeler:
    """
    Slippage Modeling System
    Predicts and accounts for execution slippage
    """
    
    def __init__(self):
        self.slippage_history: deque = deque(maxlen=1000)
        
    def estimate_slippage(self, order_size: float, avg_daily_volume: float,
                         spread: float, volatility: float) -> Dict:
        """Estimate expected slippage"""
        # Market impact component
        participation_rate = order_size / avg_daily_volume if avg_daily_volume > 0 else 0
        market_impact = participation_rate * 0.1  # 10% of participation rate
        
        # Spread component
        spread_cost = spread / 2  # Half spread
        
        # Volatility component
        vol_slippage = volatility * 0.1  # 10% of volatility
        
        # Total expected slippage
        total_slippage = market_impact + spread_cost + vol_slippage
        
        # Slippage distribution (for Monte Carlo)
        slippage_std = total_slippage * 0.5
        
        result = {
            'expected_slippage': total_slippage,
            'market_impact': market_impact,
            'spread_cost': spread_cost,
            'volatility_slippage': vol_slippage,
            'slippage_std': slippage_std,
            'worst_case_slippage': total_slippage + 2 * slippage_std,
            'slippage_bps': total_slippage * 10000
        }
        
        self.slippage_history.append(result)
        
        logger.info(f"💸 Slippage Estimate: {result['slippage_bps']:.2f}bps (Worst: {result['worst_case_slippage']*10000:.2f}bps)")
        
        return result


class SpreadModeler:
    """
    Spread Modeling System
    Analyzes and predicts bid-ask spreads
    """
    
    def __init__(self):
        self.spread_history: deque = deque(maxlen=1000)
        
    def analyze_spread(self, current_spread: float, historical_spreads: List[float],
                      time_of_day: int, volatility: float) -> Dict:
        """Analyze spread conditions"""
        # Historical statistics
        avg_spread = np.mean(historical_spreads) if historical_spreads else current_spread
        spread_std = np.std(historical_spreads) if len(historical_spreads) > 1 else 0
        
        # Spread percentile
        percentile = np.percentile(historical_spreads, 50) if historical_spreads else current_spread
        spread_ratio = current_spread / percentile if percentile > 0 else 1.0
        
        # Time-of-day adjustment
        # Spreads typically wider at open/close
        time_multipliers = {
            9: 1.5, 10: 1.2, 11: 1.0, 12: 1.0, 13: 1.0, 14: 1.0, 15: 1.1, 16: 1.3
        }
        time_multiplier = time_multipliers.get(time_of_day, 1.0)
        
        # Volatility adjustment
        vol_multiplier = 1.0 + volatility * 2
        
        # Expected spread
        expected_spread = avg_spread * time_multiplier * vol_multiplier
        
        result = {
            'current_spread': current_spread,
            'avg_spread': avg_spread,
            'spread_std': spread_std,
            'spread_ratio': spread_ratio,
            'expected_spread': expected_spread,
            'is_favorable': current_spread < avg_spread,
            'recommendation': 'EXECUTE' if spread_ratio < 1.2 else 'WAIT'
        }
        
        self.spread_history.append(result)
        
        return result


class TradeSequencer:
    """
    Trade Sequencing Logic
    Optimizes the order of trade execution
    """
    
    def __init__(self):
        self.sequence_history: List[Dict] = []
        
    def sequence_trades(self, trades: List[Dict]) -> List[Dict]:
        """Sequence trades for optimal execution"""
        # Sort by priority factors
        scored_trades = []
        
        for trade in trades:
            score = 0
            
            # Urgency (time-sensitive signals)
            if trade.get('urgency', 'normal') == 'high':
                score += 100
            
            # Liquidity (execute liquid trades first)
            liquidity = trade.get('liquidity', 1.0)
            score += liquidity * 50
            
            # Size (smaller trades first to reduce impact)
            size = trade.get('size', 0)
            score -= size / 10000  # Penalty for large trades
            
            # Correlation (diversify execution)
            correlation = trade.get('correlation_to_existing', 0)
            score -= abs(correlation) * 30
            
            # Spread favorability
            if trade.get('spread_favorable', False):
                score += 20
            
            scored_trades.append((trade, score))
        
        # Sort by score (descending)
        sequenced = [t for t, s in sorted(scored_trades, key=lambda x: x[1], reverse=True)]
        
        # Add sequence numbers
        for i, trade in enumerate(sequenced):
            trade['sequence_number'] = i + 1
            trade['execution_delay'] = i * 0.5  # 0.5 second delay between trades
        
        logger.info(f"📋 Trade Sequencing: {len(sequenced)} trades sequenced")
        
        return sequenced


class AdaptiveLeverageManager:
    """
    Adaptive Leverage Intelligence
    Dynamically adjusts leverage based on conditions
    """
    
    def __init__(self, max_leverage: float = 10.0):
        self.max_leverage = max_leverage
        self.current_leverage = 1.0
        self.leverage_history: List[Dict] = []
        
    def calculate_optimal_leverage(self, volatility: float, regime: MarketRegime,
                                  win_rate: float, drawdown: float) -> Dict:
        """Calculate optimal leverage"""
        # Base leverage from volatility targeting
        target_vol = 0.15
        vol_based_leverage = target_vol / volatility if volatility > 0 else 1.0
        
        # Regime adjustment
        regime_multipliers = {
            MarketRegime.LOW_VOL_TRENDING: 1.0,
            MarketRegime.LOW_VOL_RANGING: 0.8,
            MarketRegime.HIGH_VOL_TRENDING: 0.6,
            MarketRegime.HIGH_VOL_RANGING: 0.4,
            MarketRegime.CRISIS: 0.2,
            MarketRegime.RECOVERY: 0.5
        }
        regime_mult = regime_multipliers.get(regime, 0.5)
        
        # Win rate adjustment
        win_rate_mult = 0.5 + win_rate  # 0.5 to 1.5
        
        # Drawdown adjustment
        if drawdown > 0.15:
            dd_mult = 0.3
        elif drawdown > 0.10:
            dd_mult = 0.5
        elif drawdown > 0.05:
            dd_mult = 0.7
        else:
            dd_mult = 1.0
        
        # Calculate optimal leverage
        optimal = vol_based_leverage * regime_mult * win_rate_mult * dd_mult
        optimal = min(self.max_leverage, max(0.5, optimal))
        
        result = {
            'optimal_leverage': optimal,
            'vol_based_leverage': vol_based_leverage,
            'regime_multiplier': regime_mult,
            'win_rate_multiplier': win_rate_mult,
            'drawdown_multiplier': dd_mult,
            'max_leverage': self.max_leverage,
            'recommendation': 'REDUCE' if optimal < self.current_leverage else 'INCREASE' if optimal > self.current_leverage else 'MAINTAIN'
        }
        
        self.current_leverage = optimal
        self.leverage_history.append({
            'timestamp': datetime.now(),
            'result': result
        })
        
        logger.info(f"⚖️ Adaptive Leverage: {optimal:.2f}x (Regime: {regime.value}, DD: {drawdown:.2%})")
        
        return result


class AdvancedRiskManagementSystem:
    """
    Complete Advanced Risk Management System
    Integrates all risk management components
    """
    
    def __init__(self, total_capital: float = 100000.0):
        self.capital_allocator = SmartCapitalAllocator(total_capital)
        self.volatility_targeter = VolatilityTargeter()
        self.kelly_calculator = KellyCalculator()
        self.regime_var = RegimeVaRCalculator()
        self.stop_optimizer = StopLossOptimizer()
        self.tail_hedger = TailRiskHedger()
        self.pyramider = PositionPyramider()
        self.slippage_modeler = SlippageModeler()
        self.spread_modeler = SpreadModeler()
        self.trade_sequencer = TradeSequencer()
        self.leverage_manager = AdaptiveLeverageManager()
        
    def comprehensive_risk_analysis(self, portfolio: Dict, market_data: Dict) -> Dict:
        """Perform comprehensive risk analysis"""
        logger.info("🔬 Running comprehensive risk analysis...")
        
        analysis = {
            'timestamp': datetime.now(),
            'portfolio': portfolio,
            'market_data': market_data
        }
        
        # 1. Calculate regime VaR
        returns = portfolio.get('returns', [random.gauss(0, 0.01) for _ in range(100)])
        regime = market_data.get('regime', MarketRegime.LOW_VOL_TRENDING)
        analysis['var'] = self.regime_var.calculate_regime_var(returns, regime)
        
        # 2. Calculate Kelly sizing
        win_rate = portfolio.get('win_rate', 0.55)
        win_loss_ratio = portfolio.get('win_loss_ratio', 1.5)
        analysis['kelly'] = self.kelly_calculator.calculate_kelly(win_rate, win_loss_ratio)
        
        # 3. Volatility targeting
        current_vol = market_data.get('volatility', 0.15)
        analysis['vol_scalar'] = self.volatility_targeter.calculate_position_scalar(current_vol)
        
        # 4. Optimal leverage
        drawdown = portfolio.get('drawdown', 0.05)
        analysis['leverage'] = self.leverage_manager.calculate_optimal_leverage(
            current_vol, regime, win_rate, drawdown
        )
        
        # 5. Tail risk hedging
        portfolio_value = portfolio.get('value', 100000)
        tail_exposure = analysis['var']['regime_var']
        analysis['hedge'] = self.tail_hedger.calculate_hedge_requirement(portfolio_value, tail_exposure)
        
        # 6. Slippage estimate
        avg_order_size = portfolio.get('avg_order_size', 10000)
        avg_daily_volume = market_data.get('avg_daily_volume', 1000000)
        spread = market_data.get('spread', 0.0001)
        analysis['slippage'] = self.slippage_modeler.estimate_slippage(
            avg_order_size, avg_daily_volume, spread, current_vol
        )
        
        # 7. Overall risk score
        analysis['risk_score'] = self._calculate_risk_score(analysis)
        analysis['risk_level'] = self._determine_risk_level(analysis['risk_score'])
        
        logger.info(f"🔬 Risk Analysis Complete: Score={analysis['risk_score']:.2f}, Level={analysis['risk_level'].value}")
        
        return analysis
    
    def _calculate_risk_score(self, analysis: Dict) -> float:
        """Calculate overall risk score (0-100, higher = more risk)"""
        score = 0
        
        # VaR contribution (0-30)
        var = analysis['var']['regime_var']
        score += min(30, var * 100)
        
        # Leverage contribution (0-20)
        leverage = analysis['leverage']['optimal_leverage']
        score += min(20, leverage * 2)
        
        # Drawdown contribution (0-25)
        # (would need portfolio drawdown)
        score += 10  # Placeholder
        
        # Slippage contribution (0-15)
        slippage = analysis['slippage']['slippage_bps']
        score += min(15, slippage / 10)
        
        # Tail risk contribution (0-10)
        hedge_needed = analysis['hedge']['hedge_needed']
        portfolio_value = analysis['hedge']['portfolio_value']
        score += min(10, (hedge_needed / portfolio_value) * 100) if portfolio_value > 0 else 0
        
        return min(100, score)
    
    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from score"""
        if score < 20:
            return RiskLevel.MINIMAL
        elif score < 40:
            return RiskLevel.LOW
        elif score < 60:
            return RiskLevel.MODERATE
        elif score < 80:
            return RiskLevel.HIGH
        else:
            return RiskLevel.EXTREME
    
    def get_risk_report(self) -> Dict:
        """Get comprehensive risk report"""
        return {
            'capital_allocated': self.capital_allocator.allocated_capital,
            'current_leverage': self.leverage_manager.current_leverage,
            'kelly_history': len(self.kelly_calculator.kelly_history),
            'var_history': len(self.regime_var.var_history),
            'slippage_samples': len(self.slippage_modeler.slippage_history)
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create risk management system
    risk_system = AdvancedRiskManagementSystem(total_capital=100000)
    
    # Sample portfolio and market data
    portfolio = {
        'value': 100000,
        'returns': [random.gauss(0.001, 0.02) for _ in range(100)],
        'win_rate': 0.55,
        'win_loss_ratio': 1.5,
        'drawdown': 0.08,
        'avg_order_size': 10000
    }
    
    market_data = {
        'regime': MarketRegime.HIGH_VOL_TRENDING,
        'volatility': 0.20,
        'avg_daily_volume': 1000000,
        'spread': 0.0002
    }
    
    # Run comprehensive analysis
    analysis = risk_system.comprehensive_risk_analysis(portfolio, market_data)
    
    print("\n" + "="*80)
    logger.info("ADVANCED RISK MANAGEMENT REPORT")
    print("="*80)
    logger.info(f"Risk Score: {analysis['risk_score']:.2f}/100")
    logger.info(f"Risk Level: {analysis['risk_level'].value}")
    logger.info(f"\nVaR (95%): {analysis['var']['regime_var']:.2%}")
    logger.info(f"Kelly Fraction: {analysis['kelly']['recommended']:.2%}")
    logger.info(f"Volatility Scalar: {analysis['vol_scalar']:.2f}x")
    logger.info(f"Optimal Leverage: {analysis['leverage']['optimal_leverage']:.2f}x")
    logger.info(f"Hedge Needed: ${analysis['hedge']['hedge_needed']:,.0f}")
    logger.info(f"Expected Slippage: {analysis['slippage']['slippage_bps']:.2f}bps")
    print("="*80)
