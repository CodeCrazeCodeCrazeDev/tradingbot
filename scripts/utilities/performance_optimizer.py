"""
Performance Optimizer - Continuous optimization of trading strategies
Analyzes performance and automatically adjusts parameters for better results
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/optimizer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class OptimizationMetric(Enum):
    """Optimization metrics."""
    SHARPE_RATIO = "sharpe_ratio"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    MAX_DRAWDOWN = "max_drawdown"
    TOTAL_RETURN = "total_return"
    RISK_ADJUSTED_RETURN = "risk_adjusted_return"


@dataclass
class PerformanceMetrics:
    """Trading performance metrics."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class StrategyParameters:
    """Strategy parameters to optimize."""
    rsi_buy_threshold: float = 30.0
    rsi_sell_threshold: float = 70.0
    macd_threshold: float = 0.0
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.04
    position_size: float = 0.01
    max_positions: int = 3
    risk_per_trade: float = 0.01
    confidence_threshold: float = 0.6
    volatility_multiplier: float = 1.5


class PerformanceOptimizer:
    """
    Continuous performance optimization system.
    
    Features:
    - Real-time performance tracking
    - Automatic parameter optimization
    - A/B testing of strategies
    - Regime-based adaptation
    - Risk-adjusted optimization
    """
    
    def __init__(self, optimization_interval: int = 100):
        """
        Initialize optimizer.
        
        Args:
            optimization_interval: Number of trades between optimizations
        """
        self.optimization_interval = optimization_interval
        self.current_params = StrategyParameters()
        self.best_params = StrategyParameters()
        self.performance_history: List[PerformanceMetrics] = []
        self.parameter_history: List[Dict] = []
        self.trade_history: List[Dict] = []
        
        # Optimization settings
        self.optimization_metric = OptimizationMetric.SHARPE_RATIO
        self.min_trades_for_optimization = 50
        self.parameter_bounds = self._default_parameter_bounds()
        
        # A/B testing
        self.ab_testing_enabled = False
        self.variant_a_params = StrategyParameters()
        self.variant_b_params = StrategyParameters()
        self.variant_a_performance = []
        self.variant_b_performance = []
        
        logger.info("✅ Performance Optimizer initialized")
    
    def _default_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        """Default parameter bounds for optimization."""
        return {
            'rsi_buy_threshold': (20.0, 40.0),
            'rsi_sell_threshold': (60.0, 80.0),
            'macd_threshold': (-0.001, 0.001),
            'stop_loss_pct': (0.005, 0.05),
            'take_profit_pct': (0.01, 0.10),
            'position_size': (0.005, 0.02),
            'risk_per_trade': (0.005, 0.02),
            'confidence_threshold': (0.5, 0.8),
            'volatility_multiplier': (1.0, 2.5)
        }
    
    def record_trade(self, trade_data: Dict):
        """
        Record a completed trade.
        
        Args:
            trade_data: Trade information
        """
        self.trade_history.append({
            **trade_data,
            'timestamp': datetime.now(),
            'parameters': self.current_params.__dict__.copy()
        })
        
        # Check if optimization is needed
        if len(self.trade_history) % self.optimization_interval == 0:
            asyncio.create_task(self.optimize())
    
    def calculate_performance(self, trades: List[Dict]) -> PerformanceMetrics:
        """
        Calculate performance metrics from trades.
        
        Args:
            trades: List of trade data
        
        Returns:
            PerformanceMetrics object
        """
        if not trades:
            return PerformanceMetrics()
        
        metrics = PerformanceMetrics()
        metrics.total_trades = len(trades)
        
        pnls = [t['pnl'] for t in trades]
        metrics.total_pnl = sum(pnls)
        
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] < 0]
        
        metrics.winning_trades = len(winning_trades)
        metrics.losing_trades = len(losing_trades)
        metrics.win_rate = metrics.winning_trades / metrics.total_trades if metrics.total_trades > 0 else 0
        
        if winning_trades:
            metrics.gross_profit = sum(t['pnl'] for t in winning_trades)
            metrics.avg_win = metrics.gross_profit / len(winning_trades)
            metrics.largest_win = max(t['pnl'] for t in winning_trades)
        
        if losing_trades:
            metrics.gross_loss = abs(sum(t['pnl'] for t in losing_trades))
            metrics.avg_loss = metrics.gross_loss / len(losing_trades)
            metrics.largest_loss = min(t['pnl'] for t in losing_trades)
        
        metrics.profit_factor = metrics.gross_profit / metrics.gross_loss if metrics.gross_loss > 0 else 0
        
        # Calculate Sharpe ratio
        if len(pnls) > 1:
            returns = np.array(pnls)
            metrics.sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        
        # Calculate max drawdown
        cumulative = np.cumsum(pnls)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = running_max - cumulative
        metrics.max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        
        return metrics
    
    async def optimize(self):
        """Perform parameter optimization."""
        logger.info("\n" + "="*80)
        logger.info("🔧 STARTING PARAMETER OPTIMIZATION")
        logger.info("="*80)
        
        if len(self.trade_history) < self.min_trades_for_optimization:
            logger.info(f"⏳ Not enough trades for optimization ({len(self.trade_history)}/{self.min_trades_for_optimization})")
            return
        
        # Calculate current performance
        current_performance = self.calculate_performance(self.trade_history[-self.optimization_interval:])
        self.performance_history.append(current_performance)
        
        logger.info(f"📊 Current Performance:")
        logger.info(f"   Total Trades: {current_performance.total_trades}")
        logger.info(f"   Win Rate: {current_performance.win_rate:.2%}")
        logger.info(f"   Sharpe Ratio: {current_performance.sharpe_ratio:.2f}")
        logger.info(f"   Profit Factor: {current_performance.profit_factor:.2f}")
        logger.info(f"   Max Drawdown: ${current_performance.max_drawdown:.2f}")
        
        # Perform optimization based on selected method
        new_params = await self._optimize_parameters(current_performance)
        
        if new_params:
            logger.info(f"\n🎯 New Parameters Found:")
            self._log_parameter_changes(self.current_params, new_params)
            
            # Update parameters
            self.current_params = new_params
            self.parameter_history.append({
                'timestamp': datetime.now(),
                'parameters': new_params.__dict__.copy(),
                'performance': current_performance.__dict__
            })
            
            # Save best parameters
            if self._is_better_performance(current_performance):
                self.best_params = new_params
                logger.info("🏆 New best parameters saved!")
        
        logger.info("="*80)
    
    async def _optimize_parameters(self, current_performance: PerformanceMetrics) -> Optional[StrategyParameters]:
        """
        Optimize parameters using grid search or random search.
        
        Args:
            current_performance: Current performance metrics
        
        Returns:
            Optimized parameters or None
        """
        # Simple gradient-based optimization
        new_params = StrategyParameters()
        
        # Analyze recent trades to determine adjustments
        recent_trades = self.trade_history[-50:]
        
        # Adjust RSI thresholds based on win rate
        if current_performance.win_rate < 0.5:
            # Tighten thresholds
            new_params.rsi_buy_threshold = max(
                self.parameter_bounds['rsi_buy_threshold'][0],
                self.current_params.rsi_buy_threshold - 2.0
            )
            new_params.rsi_sell_threshold = min(
                self.parameter_bounds['rsi_sell_threshold'][1],
                self.current_params.rsi_sell_threshold + 2.0
            )
        else:
            # Keep current or slightly loosen
            new_params.rsi_buy_threshold = self.current_params.rsi_buy_threshold
            new_params.rsi_sell_threshold = self.current_params.rsi_sell_threshold
        
        # Adjust stop loss based on max drawdown
        if current_performance.max_drawdown > 1000:
            new_params.stop_loss_pct = min(
                self.parameter_bounds['stop_loss_pct'][1],
                self.current_params.stop_loss_pct * 0.9
            )
        else:
            new_params.stop_loss_pct = self.current_params.stop_loss_pct
        
        # Adjust take profit based on profit factor
        if current_performance.profit_factor < 1.5:
            new_params.take_profit_pct = max(
                self.parameter_bounds['take_profit_pct'][0],
                self.current_params.take_profit_pct * 1.1
            )
        else:
            new_params.take_profit_pct = self.current_params.take_profit_pct
        
        # Adjust position size based on Sharpe ratio
        if current_performance.sharpe_ratio > 1.5:
            new_params.position_size = min(
                self.parameter_bounds['position_size'][1],
                self.current_params.position_size * 1.05
            )
        elif current_performance.sharpe_ratio < 0.5:
            new_params.position_size = max(
                self.parameter_bounds['position_size'][0],
                self.current_params.position_size * 0.95
            )
        else:
            new_params.position_size = self.current_params.position_size
        
        # Copy other parameters
        new_params.macd_threshold = self.current_params.macd_threshold
        new_params.max_positions = self.current_params.max_positions
        new_params.risk_per_trade = self.current_params.risk_per_trade
        new_params.confidence_threshold = self.current_params.confidence_threshold
        new_params.volatility_multiplier = self.current_params.volatility_multiplier
        
        return new_params
    
    def _is_better_performance(self, performance: PerformanceMetrics) -> bool:
        """Check if performance is better than best."""
        if not self.performance_history:
            return True
        
        best_performance = max(
            self.performance_history,
            key=lambda p: getattr(p, self.optimization_metric.value)
        )
        
        current_value = getattr(performance, self.optimization_metric.value)
        best_value = getattr(best_performance, self.optimization_metric.value)
        
        return current_value > best_value
    
    def _log_parameter_changes(self, old_params: StrategyParameters, new_params: StrategyParameters):
        """Log parameter changes."""
        for param in old_params.__dict__:
            old_value = getattr(old_params, param)
            new_value = getattr(new_params, param)
            
            if old_value != new_value:
                change_pct = ((new_value - old_value) / old_value * 100) if old_value != 0 else 0
                logger.info(f"   {param}: {old_value:.4f} → {new_value:.4f} ({change_pct:+.1f}%)")
    
    def get_current_parameters(self) -> StrategyParameters:
        """Get current parameters."""
        return self.current_params
    
    def get_best_parameters(self) -> StrategyParameters:
        """Get best parameters."""
        return self.best_params
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.trade_history:
            return {'status': 'no_trades'}
        
        current_performance = self.calculate_performance(self.trade_history)
        
        return {
            'total_trades': current_performance.total_trades,
            'win_rate': current_performance.win_rate,
            'total_pnl': current_performance.total_pnl,
            'sharpe_ratio': current_performance.sharpe_ratio,
            'profit_factor': current_performance.profit_factor,
            'max_drawdown': current_performance.max_drawdown,
            'avg_win': current_performance.avg_win,
            'avg_loss': current_performance.avg_loss,
            'optimizations_performed': len(self.parameter_history)
        }
    
    def save_state(self, filename: str = 'knowledge/optimizer_state.json'):
        """Save optimizer state."""
        state = {
            'current_params': self.current_params.__dict__,
            'best_params': self.best_params.__dict__,
            'parameter_history': self.parameter_history,
            'performance_summary': self.get_performance_summary(),
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(state, f, indent=2, default=str)
            logger.info(f"💾 Optimizer state saved to {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save optimizer state: {e}")
    
    def load_state(self, filename: str = 'knowledge/optimizer_state.json'):
        """Load optimizer state."""
        try:
            with open(filename, 'r') as f:
                state = json.load(f)
            
            # Restore parameters
            self.current_params = StrategyParameters(**state['current_params'])
            self.best_params = StrategyParameters(**state['best_params'])
            self.parameter_history = state.get('parameter_history', [])
            
            logger.info(f"📂 Optimizer state loaded from {filename}")
            return True
        except FileNotFoundError:
            logger.info(f"ℹ️ No saved state found at {filename}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to load optimizer state: {e}")
            return False


async def main():
    """Test the optimizer."""
    import os
    os.makedirs('logs', exist_ok=True)
    os.makedirs('knowledge', exist_ok=True)
    
    optimizer = PerformanceOptimizer(optimization_interval=20)
    
    # Simulate some trades
    for i in range(100):
        trade = {
            'id': i,
            'pnl': np.random.randn() * 100 + 50,  # Random P/L
            'symbol': 'EURUSD',
            'type': 'BUY' if np.random.rand() > 0.5 else 'SELL'
        }
        optimizer.record_trade(trade)
        await asyncio.sleep(0.1)
    
    # Display summary
    summary = optimizer.get_performance_summary()
    logger.info("\n" + "="*80)
    logger.info("📊 FINAL PERFORMANCE SUMMARY")
    logger.info("="*80)
    for key, value in summary.items():
        logger.info(f"{key}: {value}")
    
    # Save state
    optimizer.save_state()


if __name__ == '__main__':
    asyncio.run(main())
