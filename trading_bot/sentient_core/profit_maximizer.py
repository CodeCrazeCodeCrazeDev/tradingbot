"""
Profit Maximizer - Autonomous Profit Optimization Engine

Focuses on maximizing trading profits through:
- Strategy optimization
- Risk-adjusted position sizing
- Market opportunity detection
- Execution optimization
- Continuous performance improvement
"""

import asyncio
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
from pathlib import Path
import logging
import threading
import statistics

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


class MarketCondition(Enum):
    """Current market condition"""
    TRENDING_UP = auto()
    TRENDING_DOWN = auto()
    RANGING = auto()
    VOLATILE = auto()
    QUIET = auto()
    UNCERTAIN = auto()


class TradingMode(Enum):
    """Trading mode based on conditions"""
    AGGRESSIVE = auto()
    NORMAL = auto()
    CONSERVATIVE = auto()
    DEFENSIVE = auto()
    PAPER = auto()
    LIVE = auto()


@dataclass
class TradeResult:
    """Result of a trade"""
    trade_id: str
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    pnl_pct: float
    duration_seconds: float
    strategy: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Trading performance metrics"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    total_pnl: float
    expectancy: float
    avg_trade_duration: float
    best_trade: float
    worst_trade: float
    
    @classmethod
    def calculate(cls, trades: List[TradeResult]) -> 'PerformanceMetrics':
        """Calculate metrics from trade results"""
        if not trades:
            return cls(
                total_trades=0, winning_trades=0, losing_trades=0,
                win_rate=0, avg_win=0, avg_loss=0, profit_factor=0,
                sharpe_ratio=0, sortino_ratio=0, max_drawdown=0,
                total_pnl=0, expectancy=0, avg_trade_duration=0,
                best_trade=0, worst_trade=0
            )
        
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl < 0]
        
        total_wins = sum(t.pnl for t in wins)
        total_losses = abs(sum(t.pnl for t in losses))
        
        returns = [t.pnl_pct for t in trades]
        negative_returns = [r for r in returns if r < 0]
        
        # Calculate drawdown
        cumulative = []
        running = 0
        peak = 0
        max_dd = 0
        for t in trades:
            running += t.pnl
            cumulative.append(running)
            peak = max(peak, running)
            dd = (peak - running) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        return cls(
            total_trades=len(trades),
            winning_trades=len(wins),
            losing_trades=len(losses),
            win_rate=len(wins) / len(trades) if trades else 0,
            avg_win=total_wins / len(wins) if wins else 0,
            avg_loss=total_losses / len(losses) if losses else 0,
            profit_factor=total_wins / total_losses if total_losses > 0 else float('inf'),
            sharpe_ratio=statistics.mean(returns) / statistics.stdev(returns) * math.sqrt(252) if len(returns) > 1 and statistics.stdev(returns) > 0 else 0,
            sortino_ratio=statistics.mean(returns) / statistics.stdev(negative_returns) * math.sqrt(252) if negative_returns and statistics.stdev(negative_returns) > 0 else 0,
            max_drawdown=max_dd,
            total_pnl=sum(t.pnl for t in trades),
            expectancy=(len(wins)/len(trades) * (total_wins/len(wins) if wins else 0)) - (len(losses)/len(trades) * (total_losses/len(losses) if losses else 0)) if trades else 0,
            avg_trade_duration=statistics.mean([t.duration_seconds for t in trades]),
            best_trade=max(t.pnl for t in trades),
            worst_trade=min(t.pnl for t in trades),
        )


@dataclass
class OptimizationResult:
    """Result of an optimization run"""
    parameter: str
    old_value: Any
    new_value: Any
    improvement_pct: float
    confidence: float
    timestamp: datetime


class ProfitMaximizer:
    """
    Autonomous profit optimization engine.
    
    Features:
    - Real-time performance tracking
    - Strategy parameter optimization
    - Risk-adjusted position sizing
    - Market condition adaptation
    - Continuous improvement loop
    """
    
    # Kelly Criterion parameters
    KELLY_FRACTION = 0.25  # Use quarter Kelly for safety
    MAX_POSITION_SIZE = 0.1  # 10% max position
    MIN_POSITION_SIZE = 0.01  # 1% min position
    
    # Performance thresholds
    MIN_WIN_RATE = 0.4
    MIN_PROFIT_FACTOR = 1.2
    MAX_DRAWDOWN = 0.2
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        risk_per_trade: float = 0.02,
        optimization_interval: int = 3600,
        data_path: str = "performance_data/",
    ):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.optimization_interval = optimization_interval
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # State
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._lock = threading.Lock()
        
        # Trading state
        self.trading_mode = TradingMode.PAPER
        self.market_condition = MarketCondition.UNCERTAIN
        self.is_live = False
        
        # Performance tracking
        self.trades: deque = deque(maxlen=10000)
        self.daily_pnl: Dict[str, float] = {}
        self.strategy_performance: Dict[str, PerformanceMetrics] = {}
        
        # Optimization
        self.optimizations: List[OptimizationResult] = []
        self.parameters: Dict[str, Any] = {
            'risk_per_trade': risk_per_trade,
            'max_position_size': self.MAX_POSITION_SIZE,
            'stop_loss_atr_mult': 2.0,
            'take_profit_atr_mult': 3.0,
            'max_daily_trades': 10,
            'max_concurrent_positions': 3,
            'min_signal_confidence': 0.6,
        }
        
        # Statistics
        self.stats = {
            'total_pnl': 0.0,
            'total_trades': 0,
            'optimizations_run': 0,
            'capital_growth_pct': 0.0,
        }
        
        logger.info("ProfitMaximizer initialized")
    
    async def start(self) -> None:
        """Start the profit maximization loop"""
        if self.is_running:
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._optimization_loop())
        logger.info("ProfitMaximizer started")
    
    async def stop(self) -> None:
        """Stop the profit maximization"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ProfitMaximizer stopped")
    
    async def _optimization_loop(self) -> None:
        """Main optimization loop"""
        while self.is_running:
            try:
                await self._run_optimization_cycle()
            except Exception as e:
                logger.error(f"Optimization error: {e}")
            
            await asyncio.sleep(self.optimization_interval)
    
    async def _run_optimization_cycle(self) -> None:
        """Run a complete optimization cycle"""
        # Update metrics
        self._update_performance_metrics()
        
        # Detect market condition
        self._detect_market_condition()
        
        # Optimize parameters
        await self._optimize_parameters()
        
        # Adjust trading mode
        self._adjust_trading_mode()
        
        # Save state
        self._save_state()
        
        self.stats['optimizations_run'] += 1
    
    def _update_performance_metrics(self) -> None:
        """Update performance metrics from recent trades"""
        trades_list = list(self.trades)
        
        if not trades_list:
            return
        
        # Overall metrics
        overall = PerformanceMetrics.calculate(trades_list)
        
        # Per-strategy metrics
        strategies = set(t.strategy for t in trades_list)
        for strategy in strategies:
            strategy_trades = [t for t in trades_list if t.strategy == strategy]
            self.strategy_performance[strategy] = PerformanceMetrics.calculate(strategy_trades)
        
        # Update stats
        self.stats['total_pnl'] = overall.total_pnl
        self.stats['total_trades'] = overall.total_trades
        self.stats['capital_growth_pct'] = (
            (self.current_capital - self.initial_capital) / self.initial_capital * 100
        )
    
    def _detect_market_condition(self) -> None:
        """Detect current market condition from recent trades"""
        recent_trades = [t for t in self.trades if t.timestamp > datetime.now() - timedelta(hours=24)]
        
        if not recent_trades:
            self.market_condition = MarketCondition.UNCERTAIN
            return
        
        # Analyze recent performance
        win_rate = len([t for t in recent_trades if t.pnl > 0]) / len(recent_trades)
        avg_pnl_pct = statistics.mean([t.pnl_pct for t in recent_trades])
        volatility = statistics.stdev([t.pnl_pct for t in recent_trades]) if len(recent_trades) > 1 else 0
        
        # Determine condition
        if volatility > 0.05:
            self.market_condition = MarketCondition.VOLATILE
        elif avg_pnl_pct > 0.02:
            self.market_condition = MarketCondition.TRENDING_UP
        elif avg_pnl_pct < -0.02:
            self.market_condition = MarketCondition.TRENDING_DOWN
        elif volatility < 0.01:
            self.market_condition = MarketCondition.QUIET
        else:
            self.market_condition = MarketCondition.RANGING
    
    async def _optimize_parameters(self) -> None:
        """Optimize trading parameters based on performance"""
        trades_list = list(self.trades)
        
        if len(trades_list) < 20:
            return  # Not enough data
        
        metrics = PerformanceMetrics.calculate(trades_list)
        
        # Optimize risk per trade
        if metrics.win_rate > 0.6 and metrics.profit_factor > 1.5:
            # Good performance - can increase risk slightly
            new_risk = min(0.03, self.parameters['risk_per_trade'] * 1.1)
            if new_risk != self.parameters['risk_per_trade']:
                self._record_optimization(
                    'risk_per_trade',
                    self.parameters['risk_per_trade'],
                    new_risk,
                    10.0,
                    0.7
                )
                self.parameters['risk_per_trade'] = new_risk
        
        elif metrics.win_rate < 0.4 or metrics.profit_factor < 1.0:
            # Poor performance - reduce risk
            new_risk = max(0.005, self.parameters['risk_per_trade'] * 0.8)
            if new_risk != self.parameters['risk_per_trade']:
                self._record_optimization(
                    'risk_per_trade',
                    self.parameters['risk_per_trade'],
                    new_risk,
                    -20.0,
                    0.8
                )
                self.parameters['risk_per_trade'] = new_risk
        
        # Optimize signal confidence threshold
        if metrics.win_rate < 0.5:
            # Increase confidence threshold
            new_conf = min(0.8, self.parameters['min_signal_confidence'] + 0.05)
            if new_conf != self.parameters['min_signal_confidence']:
                self._record_optimization(
                    'min_signal_confidence',
                    self.parameters['min_signal_confidence'],
                    new_conf,
                    5.0,
                    0.6
                )
                self.parameters['min_signal_confidence'] = new_conf
        
        # Optimize stop loss
        avg_loss = metrics.avg_loss
        avg_win = metrics.avg_win
        
        if avg_loss > avg_win * 1.5:
            # Losses too big - tighten stops
            new_sl = max(1.0, self.parameters['stop_loss_atr_mult'] * 0.9)
            if new_sl != self.parameters['stop_loss_atr_mult']:
                self._record_optimization(
                    'stop_loss_atr_mult',
                    self.parameters['stop_loss_atr_mult'],
                    new_sl,
                    10.0,
                    0.7
                )
                self.parameters['stop_loss_atr_mult'] = new_sl
    
    def _record_optimization(
        self,
        parameter: str,
        old_value: Any,
        new_value: Any,
        improvement_pct: float,
        confidence: float
    ) -> None:
        """Record an optimization result"""
        result = OptimizationResult(
            parameter=parameter,
            old_value=old_value,
            new_value=new_value,
            improvement_pct=improvement_pct,
            confidence=confidence,
            timestamp=datetime.now(),
        )
        self.optimizations.append(result)
        logger.info(f"Optimized {parameter}: {old_value} -> {new_value}")
    
    def _adjust_trading_mode(self) -> None:
        """Adjust trading mode based on conditions and performance"""
        trades_list = list(self.trades)
        
        if len(trades_list) < 10:
            self.trading_mode = TradingMode.CONSERVATIVE
            return
        
        recent = [t for t in trades_list if t.timestamp > datetime.now() - timedelta(hours=24)]
        metrics = PerformanceMetrics.calculate(recent) if recent else None
        
        if not metrics:
            self.trading_mode = TradingMode.CONSERVATIVE
            return
        
        # Check for emergency conditions
        if metrics.max_drawdown > self.MAX_DRAWDOWN:
            self.trading_mode = TradingMode.DEFENSIVE
            logger.warning("Switching to DEFENSIVE mode due to high drawdown")
            return
        
        # Normal mode selection
        if self.market_condition == MarketCondition.VOLATILE:
            self.trading_mode = TradingMode.CONSERVATIVE
        elif self.market_condition in [MarketCondition.TRENDING_UP, MarketCondition.TRENDING_DOWN]:
            if metrics.profit_factor > 1.5:
                self.trading_mode = TradingMode.AGGRESSIVE
            else:
                self.trading_mode = TradingMode.NORMAL
        else:
            self.trading_mode = TradingMode.NORMAL
    
    def _save_state(self) -> None:
        """Save current state to disk"""
        state = {
            'capital': self.current_capital,
            'parameters': self.parameters,
            'trading_mode': self.trading_mode.name,
            'market_condition': self.market_condition.name,
            'stats': self.stats,
            'timestamp': datetime.now().isoformat(),
        }
        
        state_file = self.data_path / "profit_maximizer_state.json"
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    # Public API
    
    def record_trade(self, trade: TradeResult) -> None:
        """Record a completed trade"""
        with self._lock:
            self.trades.append(trade)
            self.current_capital += trade.pnl
            
            # Update daily PnL
            date_key = trade.timestamp.strftime('%Y-%m-%d')
            self.daily_pnl[date_key] = self.daily_pnl.get(date_key, 0) + trade.pnl
        
        logger.info(f"Trade recorded: {trade.symbol} {trade.direction} PnL: {trade.pnl:.2f}")
    
    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        signal_confidence: float = 0.5,
    ) -> float:
        """Calculate optimal position size"""
        # Base risk amount
        risk_amount = self.current_capital * self.parameters['risk_per_trade']
        
        # Adjust for signal confidence
        confidence_mult = 0.5 + (signal_confidence * 0.5)  # 0.5 to 1.0
        risk_amount *= confidence_mult
        
        # Adjust for market condition
        condition_mult = {
            MarketCondition.TRENDING_UP: 1.1,
            MarketCondition.TRENDING_DOWN: 1.1,
            MarketCondition.RANGING: 0.8,
            MarketCondition.VOLATILE: 0.6,
            MarketCondition.QUIET: 0.9,
            MarketCondition.UNCERTAIN: 0.7,
        }.get(self.market_condition, 1.0)
        risk_amount *= condition_mult
        
        # Adjust for trading mode
        mode_mult = {
            TradingMode.AGGRESSIVE: 1.2,
            TradingMode.NORMAL: 1.0,
            TradingMode.CONSERVATIVE: 0.7,
            TradingMode.DEFENSIVE: 0.5,
            TradingMode.PAPER: 1.0,
            TradingMode.LIVE: 1.0,
        }.get(self.trading_mode, 1.0)
        risk_amount *= mode_mult
        
        # Calculate position size based on stop loss distance
        stop_distance = abs(entry_price - stop_loss)
        if stop_distance == 0:
            return 0
        
        position_size = risk_amount / stop_distance
        
        # Apply Kelly Criterion if we have enough data
        trades_list = list(self.trades)
        if len(trades_list) >= 20:
            metrics = PerformanceMetrics.calculate(trades_list)
            if metrics.win_rate > 0 and metrics.avg_win > 0 and metrics.avg_loss > 0:
                # Kelly formula: f = (bp - q) / b
                # where b = avg_win/avg_loss, p = win_rate, q = 1 - p
                b = metrics.avg_win / metrics.avg_loss
                p = metrics.win_rate
                q = 1 - p
                kelly = (b * p - q) / b if b > 0 else 0
                kelly = max(0, min(kelly * self.KELLY_FRACTION, self.MAX_POSITION_SIZE))
                
                # Blend Kelly with fixed fractional
                position_value = position_size * entry_price
                max_position_value = self.current_capital * kelly
                if position_value > max_position_value:
                    position_size = max_position_value / entry_price
        
        # Apply limits
        max_size = (self.current_capital * self.parameters['max_position_size']) / entry_price
        min_size = (self.current_capital * self.MIN_POSITION_SIZE) / entry_price
        
        return max(min_size, min(max_size, position_size))
    
    def should_trade(self, signal_confidence: float) -> Tuple[bool, str]:
        """Determine if we should take a trade"""
        # Check confidence threshold
        if signal_confidence < self.parameters['min_signal_confidence']:
            return False, f"Confidence {signal_confidence:.2f} below threshold {self.parameters['min_signal_confidence']:.2f}"
        
        # Check daily trade limit
        today = datetime.now().strftime('%Y-%m-%d')
        today_trades = len([t for t in self.trades if t.timestamp.strftime('%Y-%m-%d') == today])
        if today_trades >= self.parameters['max_daily_trades']:
            return False, f"Daily trade limit reached ({today_trades})"
        
        # Check drawdown
        if self.current_capital < self.initial_capital * (1 - self.MAX_DRAWDOWN):
            return False, "Maximum drawdown reached"
        
        # Check trading mode
        if self.trading_mode == TradingMode.DEFENSIVE:
            if signal_confidence < 0.8:
                return False, "Defensive mode - only high confidence trades"
        
        return True, "Trade approved"
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        return PerformanceMetrics.calculate(list(self.trades))
    
    def get_strategy_ranking(self) -> List[Tuple[str, float]]:
        """Get strategies ranked by performance"""
        rankings = []
        for strategy, metrics in self.strategy_performance.items():
            # Score based on multiple factors
            score = (
                metrics.profit_factor * 0.3 +
                metrics.win_rate * 0.2 +
                metrics.sharpe_ratio * 0.3 +
                (1 - metrics.max_drawdown) * 0.2
            )
            rankings.append((strategy, score))
        
        return sorted(rankings, key=lambda x: x[1], reverse=True)
    
    def get_optimization_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent optimization history"""
        return [
            {
                'parameter': o.parameter,
                'old_value': o.old_value,
                'new_value': o.new_value,
                'improvement_pct': o.improvement_pct,
                'confidence': o.confidence,
                'timestamp': o.timestamp.isoformat(),
            }
            for o in self.optimizations[-limit:]
        ]
    
    def set_live_mode(self, is_live: bool) -> None:
        """Switch between live and paper trading"""
        self.is_live = is_live
        self.trading_mode = TradingMode.LIVE if is_live else TradingMode.PAPER
        logger.info(f"Trading mode set to: {'LIVE' if is_live else 'PAPER'}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        metrics = self.get_performance_metrics()
        
        return {
            'capital': self.current_capital,
            'initial_capital': self.initial_capital,
            'growth_pct': (self.current_capital - self.initial_capital) / self.initial_capital * 100,
            'trading_mode': self.trading_mode.name,
            'market_condition': self.market_condition.name,
            'is_live': self.is_live,
            'total_trades': metrics.total_trades,
            'win_rate': metrics.win_rate,
            'profit_factor': metrics.profit_factor,
            'sharpe_ratio': metrics.sharpe_ratio,
            'max_drawdown': metrics.max_drawdown,
            'total_pnl': metrics.total_pnl,
            'parameters': self.parameters,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get profit maximizer statistics"""
        return {
            **self.stats,
            'current_capital': self.current_capital,
            'trading_mode': self.trading_mode.name,
            'market_condition': self.market_condition.name,
        }
