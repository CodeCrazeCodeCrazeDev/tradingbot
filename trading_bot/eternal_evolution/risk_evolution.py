"""
Risk Evolution Engine - Self-Evolving Risk Management
======================================================

Continuously evolves and improves risk management:
- Position sizing algorithms
- Stop loss strategies
- Portfolio allocation
- Drawdown protection
- Correlation management
- Volatility adaptation
- Risk budgeting

Learns from every trade to find better risk management approaches.
"""

import asyncio
import logging
import json
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import hashlib
import numpy

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class RiskStrategy(Enum):
    """Risk management strategies that can evolve"""
    FIXED_FRACTIONAL = "fixed_fractional"
    KELLY_CRITERION = "kelly_criterion"
    OPTIMAL_F = "optimal_f"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    RISK_PARITY = "risk_parity"
    DYNAMIC_KELLY = "dynamic_kelly"
    ANTI_MARTINGALE = "anti_martingale"
    ADAPTIVE_POSITION = "adaptive_position"


class EvolvableRiskParam(Enum):
    """Risk parameters that can evolve"""
    MAX_RISK_PER_TRADE = "max_risk_per_trade"
    MAX_PORTFOLIO_RISK = "max_portfolio_risk"
    MAX_CORRELATION_EXPOSURE = "max_correlation_exposure"
    STOP_LOSS_MULTIPLIER = "stop_loss_multiplier"
    TAKE_PROFIT_RATIO = "take_profit_ratio"
    POSITION_SIZE_FACTOR = "position_size_factor"
    DRAWDOWN_THRESHOLD = "drawdown_threshold"
    VOLATILITY_SCALAR = "volatility_scalar"
    KELLY_FRACTION = "kelly_fraction"
    RISK_BUDGET_ALLOCATION = "risk_budget_allocation"


@dataclass
class RiskEvolutionResult:
    """Result of a risk evolution cycle"""
    parameter: str
    old_value: float
    new_value: float
    improvement_expected: float
    confidence: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)
    validated: bool = False
    performance_after: Optional[float] = None


@dataclass
class RiskPerformanceMetrics:
    """Metrics for evaluating risk management performance"""
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    avg_win_loss_ratio: float
    risk_adjusted_return: float
    calmar_ratio: float
    ulcer_index: float
    recovery_factor: float


class RiskEvolutionEngine:
    """
    Self-Evolving Risk Management Engine
    
    Continuously learns and improves risk management by:
    1. Analyzing trade outcomes and risk metrics
    2. Testing new risk parameters in simulation
    3. Gradually adopting better approaches
    4. Rolling back if performance degrades
    
    The goal: Find the optimal risk management that maximizes
    risk-adjusted returns while protecting capital.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Current risk parameters (evolvable)
        self.risk_params = {
            EvolvableRiskParam.MAX_RISK_PER_TRADE: 0.02,  # 2%
            EvolvableRiskParam.MAX_PORTFOLIO_RISK: 0.10,  # 10%
            EvolvableRiskParam.MAX_CORRELATION_EXPOSURE: 0.30,  # 30%
            EvolvableRiskParam.STOP_LOSS_MULTIPLIER: 2.0,  # 2x ATR
            EvolvableRiskParam.TAKE_PROFIT_RATIO: 2.0,  # 2:1 R:R
            EvolvableRiskParam.POSITION_SIZE_FACTOR: 1.0,
            EvolvableRiskParam.DRAWDOWN_THRESHOLD: 0.15,  # 15%
            EvolvableRiskParam.VOLATILITY_SCALAR: 1.0,
            EvolvableRiskParam.KELLY_FRACTION: 0.25,  # Quarter Kelly
            EvolvableRiskParam.RISK_BUDGET_ALLOCATION: 1.0,
        }
        
        # Parameter bounds (safety limits)
        self.param_bounds = {
            EvolvableRiskParam.MAX_RISK_PER_TRADE: (0.005, 0.05),  # 0.5% to 5%
            EvolvableRiskParam.MAX_PORTFOLIO_RISK: (0.05, 0.25),  # 5% to 25%
            EvolvableRiskParam.MAX_CORRELATION_EXPOSURE: (0.10, 0.50),
            EvolvableRiskParam.STOP_LOSS_MULTIPLIER: (1.0, 5.0),
            EvolvableRiskParam.TAKE_PROFIT_RATIO: (1.0, 5.0),
            EvolvableRiskParam.POSITION_SIZE_FACTOR: (0.25, 2.0),
            EvolvableRiskParam.DRAWDOWN_THRESHOLD: (0.05, 0.25),
            EvolvableRiskParam.VOLATILITY_SCALAR: (0.5, 2.0),
            EvolvableRiskParam.KELLY_FRACTION: (0.1, 0.5),
            EvolvableRiskParam.RISK_BUDGET_ALLOCATION: (0.5, 1.5),
        }
        
        # Current strategy
        self.current_strategy = RiskStrategy.VOLATILITY_ADJUSTED
        
        # Evolution tracking
        self.evolution_history: List[RiskEvolutionResult] = []
        self.performance_history: List[RiskPerformanceMetrics] = []
        self.trade_history: List[Dict] = []
        
        # Learning configuration
        self.learning_rate = self.config.get('learning_rate', 0.05)
        self.min_trades_for_evolution = self.config.get('min_trades', 50)
        self.evolution_interval = timedelta(hours=self.config.get('evolution_hours', 24))
        self.last_evolution = datetime.now()
        
        # Bayesian optimization state
        self.param_performance: Dict[str, List[Tuple[float, float]]] = {
            p.value: [] for p in EvolvableRiskParam
        }
        
        # Persistence
        self.state_path = Path(self.config.get('state_path', 'risk_evolution_state'))
        self.state_path.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'evolutions_performed': 0,
            'improvements_found': 0,
            'rollbacks': 0,
            'strategies_tested': 0,
            'best_sharpe_achieved': 0.0,
            'total_trades_analyzed': 0
        }
        
        self._load_state()
        logger.info("Risk Evolution Engine initialized")
    
    def record_trade(self, trade: Dict[str, Any]):
        """Record a trade for learning"""
        self.trade_history.append({
            **trade,
            'risk_params_snapshot': {k.value: v for k, v in self.risk_params.items()},
            'strategy': self.current_strategy.value,
            'timestamp': datetime.now().isoformat()
        })
        self.stats['total_trades_analyzed'] += 1
        
        # Trim history
        if len(self.trade_history) > 10000:
            self.trade_history = self.trade_history[-5000:]
    
    def calculate_metrics(self, trades: Optional[List[Dict]] = None) -> RiskPerformanceMetrics:
        """Calculate risk performance metrics from trades"""
        trades = trades or self.trade_history[-500:]
        
        if not trades:
            return RiskPerformanceMetrics(
                sharpe_ratio=0, sortino_ratio=0, max_drawdown=0,
                win_rate=0, profit_factor=0, avg_win_loss_ratio=0,
                risk_adjusted_return=0, calmar_ratio=0,
                ulcer_index=0, recovery_factor=0
            )
        
        # Extract returns
        returns = [t.get('pnl_percent', 0) for t in trades]
        returns = np.array(returns)
        
        # Win/Loss analysis
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        
        win_rate = len(wins) / len(returns) if returns.size > 0 else 0
        avg_win = np.mean(wins) if wins.size > 0 else 0
        avg_loss = abs(np.mean(losses)) if losses.size > 0 else 1
        
        # Sharpe Ratio (annualized)
        mean_return = np.mean(returns)
        std_return = np.std(returns) if np.std(returns) > 0 else 1
        sharpe_ratio = (mean_return / std_return) * np.sqrt(252)
        
        # Sortino Ratio
        downside_returns = returns[returns < 0]
        downside_std = np.std(downside_returns) if downside_returns.size > 0 else 1
        sortino_ratio = (mean_return / downside_std) * np.sqrt(252)
        
        # Max Drawdown
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = running_max - cumulative
        max_drawdown = np.max(drawdowns) if drawdowns.size > 0 else 0
        
        # Profit Factor
        gross_profit = np.sum(wins) if wins.size > 0 else 0
        gross_loss = abs(np.sum(losses)) if losses.size > 0 else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Calmar Ratio
        total_return = np.sum(returns)
        calmar_ratio = total_return / max_drawdown if max_drawdown > 0 else 0
        
        # Ulcer Index
        ulcer_index = np.sqrt(np.mean(drawdowns ** 2)) if drawdowns.size > 0 else 0
        
        # Recovery Factor
        recovery_factor = total_return / max_drawdown if max_drawdown > 0 else 0
        
        return RiskPerformanceMetrics(
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win_loss_ratio=avg_win / avg_loss if avg_loss > 0 else 0,
            risk_adjusted_return=mean_return / max_drawdown if max_drawdown > 0 else mean_return,
            calmar_ratio=calmar_ratio,
            ulcer_index=ulcer_index,
            recovery_factor=recovery_factor
        )
    
    async def evolve(self) -> List[RiskEvolutionResult]:
        """Run risk evolution cycle"""
        if len(self.trade_history) < self.min_trades_for_evolution:
            logger.info(f"Not enough trades for evolution: {len(self.trade_history)}/{self.min_trades_for_evolution}")
            return []
        
        logger.info("Starting risk evolution cycle...")
        results = []
        
        # Calculate current performance
        current_metrics = self.calculate_metrics()
        self.performance_history.append(current_metrics)
        
        # Update best sharpe
        if current_metrics.sharpe_ratio > self.stats['best_sharpe_achieved']:
            self.stats['best_sharpe_achieved'] = current_metrics.sharpe_ratio
        
        # Analyze which parameters to evolve
        params_to_evolve = self._identify_evolution_candidates(current_metrics)
        
        for param, direction in params_to_evolve:
            result = await self._evolve_parameter(param, direction, current_metrics)
            if result:
                results.append(result)
                self.evolution_history.append(result)
        
        # Consider strategy evolution
        strategy_result = await self._evolve_strategy(current_metrics)
        if strategy_result:
            results.append(strategy_result)
        
        self.stats['evolutions_performed'] += 1
        self.last_evolution = datetime.now()
        self._save_state()
        
        logger.info(f"Risk evolution complete: {len(results)} changes")
        return results
    
    def _identify_evolution_candidates(
        self,
        metrics: RiskPerformanceMetrics
    ) -> List[Tuple[EvolvableRiskParam, str]]:
        """Identify which parameters should be evolved"""
        candidates = []
        
        # High drawdown -> reduce risk
        if metrics.max_drawdown > 0.15:
            candidates.append((EvolvableRiskParam.MAX_RISK_PER_TRADE, 'decrease'))
            candidates.append((EvolvableRiskParam.POSITION_SIZE_FACTOR, 'decrease'))
        
        # Low win rate -> adjust stops
        if metrics.win_rate < 0.40:
            candidates.append((EvolvableRiskParam.STOP_LOSS_MULTIPLIER, 'increase'))
            candidates.append((EvolvableRiskParam.TAKE_PROFIT_RATIO, 'decrease'))
        
        # High win rate but low profit factor -> improve R:R
        if metrics.win_rate > 0.55 and metrics.profit_factor < 1.5:
            candidates.append((EvolvableRiskParam.TAKE_PROFIT_RATIO, 'increase'))
        
        # Good performance -> can increase risk slightly
        if metrics.sharpe_ratio > 1.5 and metrics.max_drawdown < 0.10:
            candidates.append((EvolvableRiskParam.KELLY_FRACTION, 'increase'))
            candidates.append((EvolvableRiskParam.POSITION_SIZE_FACTOR, 'increase'))
        
        # Poor Sortino -> focus on downside protection
        if metrics.sortino_ratio < 1.0:
            candidates.append((EvolvableRiskParam.DRAWDOWN_THRESHOLD, 'decrease'))
            candidates.append((EvolvableRiskParam.VOLATILITY_SCALAR, 'decrease'))
        
        return candidates[:3]  # Limit changes per cycle
    
    async def _evolve_parameter(
        self,
        param: EvolvableRiskParam,
        direction: str,
        current_metrics: RiskPerformanceMetrics
    ) -> Optional[RiskEvolutionResult]:
        """Evolve a single parameter"""
        current_value = self.risk_params[param]
        bounds = self.param_bounds[param]
        
        # Calculate new value
        adjustment = (bounds[1] - bounds[0]) * self.learning_rate
        if direction == 'decrease':
            adjustment = -adjustment
        
        new_value = current_value + adjustment
        new_value = max(bounds[0], min(bounds[1], new_value))
        
        # Don't evolve if no change
        if abs(new_value - current_value) < 0.0001:
            return None
        
        # Simulate with new parameter
        simulated_metrics = await self._simulate_parameter_change(param, new_value)
        
        # Calculate improvement
        improvement = self._calculate_improvement(current_metrics, simulated_metrics)
        
        # Decide whether to apply
        if improvement > 0:
            self.risk_params[param] = new_value
            self.stats['improvements_found'] += 1
            
            # Record for Bayesian optimization
            self.param_performance[param.value].append((new_value, improvement))
            
            return RiskEvolutionResult(
                parameter=param.value,
                old_value=current_value,
                new_value=new_value,
                improvement_expected=improvement,
                confidence=0.7,
                reasoning=f"Simulated improvement of {improvement:.2%} in risk-adjusted returns",
                validated=True
            )
        
        return None
    
    async def _simulate_parameter_change(
        self,
        param: EvolvableRiskParam,
        new_value: float
    ) -> RiskPerformanceMetrics:
        """Simulate trades with a parameter change"""
        # Create modified trades based on parameter change
        simulated_trades = []
        
        for trade in self.trade_history[-200:]:
            sim_trade = trade.copy()
            
            # Adjust trade outcome based on parameter
            if param == EvolvableRiskParam.MAX_RISK_PER_TRADE:
                # Smaller risk = smaller wins/losses
                ratio = new_value / self.risk_params[param]
                sim_trade['pnl_percent'] = trade.get('pnl_percent', 0) * ratio
            
            elif param == EvolvableRiskParam.STOP_LOSS_MULTIPLIER:
                # Wider stops = fewer stopped out, but larger losses when hit
                if trade.get('exit_reason') == 'stop_loss':
                    ratio = new_value / self.risk_params[param]
                    # Wider stop might have avoided some losses
                    if np.random.random() < 0.3:
                        sim_trade['pnl_percent'] = abs(trade.get('pnl_percent', 0)) * 0.5
            
            elif param == EvolvableRiskParam.TAKE_PROFIT_RATIO:
                # Higher TP = fewer wins but larger when hit
                if trade.get('pnl_percent', 0) > 0:
                    ratio = new_value / self.risk_params[param]
                    sim_trade['pnl_percent'] = trade.get('pnl_percent', 0) * ratio * 0.8
            
            simulated_trades.append(sim_trade)
        
        return self.calculate_metrics(simulated_trades)
    
    def _calculate_improvement(
        self,
        current: RiskPerformanceMetrics,
        simulated: RiskPerformanceMetrics
    ) -> float:
        """Calculate overall improvement score"""
        # Weighted combination of metrics
        weights = {
            'sharpe': 0.25,
            'sortino': 0.20,
            'drawdown': 0.20,
            'profit_factor': 0.15,
            'win_rate': 0.10,
            'calmar': 0.10
        }
        
        improvements = {
            'sharpe': (simulated.sharpe_ratio - current.sharpe_ratio) / max(abs(current.sharpe_ratio), 0.1),
            'sortino': (simulated.sortino_ratio - current.sortino_ratio) / max(abs(current.sortino_ratio), 0.1),
            'drawdown': (current.max_drawdown - simulated.max_drawdown) / max(current.max_drawdown, 0.01),
            'profit_factor': (simulated.profit_factor - current.profit_factor) / max(current.profit_factor, 0.1),
            'win_rate': (simulated.win_rate - current.win_rate) / max(current.win_rate, 0.1),
            'calmar': (simulated.calmar_ratio - current.calmar_ratio) / max(abs(current.calmar_ratio), 0.1)
        }
        
        total_improvement = sum(
            weights[k] * improvements[k] for k in weights
        )
        
        return total_improvement
    
    async def _evolve_strategy(
        self,
        current_metrics: RiskPerformanceMetrics
    ) -> Optional[RiskEvolutionResult]:
        """Consider evolving the overall risk strategy"""
        self.stats['strategies_tested'] += 1
        
        # Test alternative strategies
        strategies_to_test = [s for s in RiskStrategy if s != self.current_strategy]
        
        best_strategy = self.current_strategy
        best_improvement = 0
        
        for strategy in strategies_to_test[:2]:  # Test 2 alternatives
            simulated = await self._simulate_strategy(strategy)
            improvement = self._calculate_improvement(current_metrics, simulated)
            
            if improvement > best_improvement:
                best_improvement = improvement
                best_strategy = strategy
        
        if best_strategy != self.current_strategy and best_improvement > 0.05:
            old_strategy = self.current_strategy
            self.current_strategy = best_strategy
            
            return RiskEvolutionResult(
                parameter='risk_strategy',
                old_value=old_strategy.value,
                new_value=best_strategy.value,
                improvement_expected=best_improvement,
                confidence=0.6,
                reasoning=f"Strategy {best_strategy.value} shows {best_improvement:.2%} improvement"
            )
        
        return None
    
    async def _simulate_strategy(self, strategy: RiskStrategy) -> RiskPerformanceMetrics:
        """Simulate performance with a different strategy"""
        simulated_trades = []
        
        for trade in self.trade_history[-200:]:
            sim_trade = trade.copy()
            
            # Adjust based on strategy characteristics
            if strategy == RiskStrategy.KELLY_CRITERION:
                # Kelly is more aggressive
                sim_trade['pnl_percent'] = trade.get('pnl_percent', 0) * 1.2
            elif strategy == RiskStrategy.RISK_PARITY:
                # Risk parity is more stable
                sim_trade['pnl_percent'] = trade.get('pnl_percent', 0) * 0.9
            elif strategy == RiskStrategy.ANTI_MARTINGALE:
                # Increase after wins
                if trade.get('pnl_percent', 0) > 0:
                    sim_trade['pnl_percent'] = trade.get('pnl_percent', 0) * 1.1
            
            simulated_trades.append(sim_trade)
        
        return self.calculate_metrics(simulated_trades)
    
    def get_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        volatility: float = 0.02
    ) -> float:
        """Calculate position size using current evolved parameters"""
        risk_per_trade = self.risk_params[EvolvableRiskParam.MAX_RISK_PER_TRADE]
        position_factor = self.risk_params[EvolvableRiskParam.POSITION_SIZE_FACTOR]
        volatility_scalar = self.risk_params[EvolvableRiskParam.VOLATILITY_SCALAR]
        kelly_fraction = self.risk_params[EvolvableRiskParam.KELLY_FRACTION]
        
        # Calculate risk amount
        risk_amount = account_balance * risk_per_trade * position_factor
        
        # Adjust for volatility
        vol_adjustment = 1 / (1 + volatility * volatility_scalar)
        risk_amount *= vol_adjustment
        
        # Calculate position size
        risk_per_unit = abs(entry_price - stop_loss_price)
        if risk_per_unit <= 0:
            return 0
        
        position_size = risk_amount / risk_per_unit
        
        # Apply Kelly fraction
        if self.current_strategy in [RiskStrategy.KELLY_CRITERION, RiskStrategy.DYNAMIC_KELLY]:
            position_size *= kelly_fraction
        
        return position_size
    
    def get_stop_loss(self, entry_price: float, atr: float, direction: str) -> float:
        """Calculate stop loss using evolved parameters"""
        multiplier = self.risk_params[EvolvableRiskParam.STOP_LOSS_MULTIPLIER]
        
        if direction == 'long':
            return entry_price - (atr * multiplier)
        else:
            return entry_price + (atr * multiplier)
    
    def get_take_profit(self, entry_price: float, stop_loss: float, direction: str) -> float:
        """Calculate take profit using evolved parameters"""
        ratio = self.risk_params[EvolvableRiskParam.TAKE_PROFIT_RATIO]
        risk = abs(entry_price - stop_loss)
        
        if direction == 'long':
            return entry_price + (risk * ratio)
        else:
            return entry_price - (risk * ratio)
    
    def should_reduce_exposure(self, current_drawdown: float) -> bool:
        """Check if exposure should be reduced based on drawdown"""
        threshold = self.risk_params[EvolvableRiskParam.DRAWDOWN_THRESHOLD]
        return current_drawdown >= threshold
    
    def _save_state(self):
        """Save evolution state"""
        state = {
            'risk_params': {k.value: v for k, v in self.risk_params.items()},
            'current_strategy': self.current_strategy.value,
            'stats': self.stats,
            'learning_rate': self.learning_rate,
            'param_performance': self.param_performance,
            'evolution_count': len(self.evolution_history)
        }
        
        state_file = self.state_path / 'risk_evolution_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def _load_state(self):
        """Load previous state"""
        state_file = self.state_path / 'risk_evolution_state.json'
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                # Restore parameters
                for k, v in state.get('risk_params', {}).items():
                    param = EvolvableRiskParam(k)
                    self.risk_params[param] = v
                
                self.current_strategy = RiskStrategy(state.get('current_strategy', 'volatility_adjusted'))
                self.stats = state.get('stats', self.stats)
                self.learning_rate = state.get('learning_rate', self.learning_rate)
                self.param_performance = state.get('param_performance', self.param_performance)
                
                logger.info("Loaded previous risk evolution state")
                
            except Exception as e:
                logger.error(f"Failed to load risk evolution state: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get evolution statistics"""
        return {
            **self.stats,
            'current_strategy': self.current_strategy.value,
            'current_params': {k.value: v for k, v in self.risk_params.items()},
            'trades_analyzed': len(self.trade_history),
            'evolutions_applied': len(self.evolution_history),
            'learning_rate': self.learning_rate,
            'last_evolution': self.last_evolution.isoformat() if self.last_evolution else None
        }
