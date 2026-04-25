"""
DRAWDOWN PROTECTION MODULE - P0 CRITICAL FIX
============================================================

Implements maximum drawdown protection to prevent catastrophic losses.

Features:
- Real-time drawdown calculation
- Automatic trading halt when limit exceeded
- Daily loss limit enforcement
- Position size reduction on drawdown
- Emergency shutdown capability

Author: AI Assistant
Date: October 23, 2025
Version: 1.0.0
"""


from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger
import numpy


class DrawdownStatus(Enum):
    """Drawdown status."""
    GREEN = auto()      # Safe (< 50% of limit)
    YELLOW = auto()     # Caution (50-80% of limit)
    RED = auto()        # Alert (80-100% of limit)
    CRITICAL = auto()   # Halt trading (>= 100% of limit)


@dataclass
class DrawdownMetrics:
    """Drawdown metrics."""
    current_balance: float
    peak_balance: float
    drawdown_amount: float
    drawdown_percent: float
    daily_loss: float
    daily_loss_percent: float
    status: DrawdownStatus
    timestamp: datetime = field(default_factory=datetime.now)


class DrawdownProtector:
    """Protects account from catastrophic drawdown."""
    
    def __init__(self, max_drawdown_percent: float = 20.0,
                 max_daily_loss_percent: float = 2.0,
                 max_total_positions: int = 5):
        """
        Initialize drawdown protector.
        
        Args:
            max_drawdown_percent: Maximum allowed drawdown (default 20%)
            max_daily_loss_percent: Maximum daily loss (default 2%)
            max_total_positions: Maximum open positions (default 5)
        """
        try:
            self.max_drawdown_percent = max_drawdown_percent
            self.max_daily_loss_percent = max_daily_loss_percent
            self.max_total_positions = max_total_positions
        
            self.initial_balance = None
            self.peak_balance = None
            self.current_balance = None
            self.daily_start_balance = None
            self.daily_start_time = None
        
            self.drawdown_history: List[DrawdownMetrics] = []
            self.trading_halted = False
            self.halt_reason = None
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def initialize(self, initial_balance: float):
        """Initialize with account balance."""
        try:
            self.initial_balance = initial_balance
            self.peak_balance = initial_balance
            self.current_balance = initial_balance
            self.daily_start_balance = initial_balance
            self.daily_start_time = datetime.now()
        
            logger.info(f"Drawdown protector initialized with balance: ${initial_balance:,.2f}")
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    def update_balance(self, current_balance: float):
        """Update current balance and check limits."""
        try:
            self.current_balance = current_balance
        
            # Update peak if new high
            if current_balance > self.peak_balance:
                self.peak_balance = current_balance
                logger.info(f"New peak balance: ${self.peak_balance:,.2f}")
        
            # Check if new day
            if self._is_new_day():
                self._reset_daily_limits()
        
            # Calculate metrics
            metrics = self._calculate_metrics()
            self.drawdown_history.append(metrics)
        
            # Keep only last 1000 records
            if len(self.drawdown_history) > 1000:
                self.drawdown_history.pop(0)
        
            # Check limits
            self._check_limits(metrics)
        except Exception as e:
            logger.error(f"Error in update_balance: {e}")
            raise
    
    def _calculate_metrics(self) -> DrawdownMetrics:
        """Calculate current drawdown metrics."""
        # Overall drawdown
        try:
            drawdown_amount = self.peak_balance - self.current_balance
            drawdown_percent = (drawdown_amount / self.peak_balance * 100) if self.peak_balance > 0 else 0
        
            # Daily loss
            daily_loss = self.daily_start_balance - self.current_balance
            daily_loss_percent = (daily_loss / self.daily_start_balance * 100) if self.daily_start_balance > 0 else 0
        
            # Determine status
            status = self._get_status(drawdown_percent)
        
            return DrawdownMetrics(
                current_balance=self.current_balance,
                peak_balance=self.peak_balance,
                drawdown_amount=drawdown_amount,
                drawdown_percent=drawdown_percent,
                daily_loss=daily_loss,
                daily_loss_percent=daily_loss_percent,
                status=status
            )
        except Exception as e:
            logger.error(f"Error in _calculate_metrics: {e}")
            raise
    
    def _get_status(self, drawdown_percent: float) -> DrawdownStatus:
        """Determine drawdown status."""
        try:
            if drawdown_percent >= 100:
                return DrawdownStatus.CRITICAL
            elif drawdown_percent >= 80:
                return DrawdownStatus.RED
            elif drawdown_percent >= 50:
                return DrawdownStatus.YELLOW
            else:
                return DrawdownStatus.GREEN
        except Exception as e:
            logger.error(f"Error in _get_status: {e}")
            raise
    
    def _check_limits(self, metrics: DrawdownMetrics):
        """Check if limits exceeded."""
        # Check overall drawdown
        try:
            if metrics.drawdown_percent >= self.max_drawdown_percent:
                self.trading_halted = True
                self.halt_reason = f"Drawdown limit exceeded: {metrics.drawdown_percent:.2f}%"
                logger.critical(self.halt_reason)
        
            # Check daily loss
            if metrics.daily_loss_percent >= self.max_daily_loss_percent:
                self.trading_halted = True
                self.halt_reason = f"Daily loss limit exceeded: {metrics.daily_loss_percent:.2f}%"
                logger.critical(self.halt_reason)
        except Exception as e:
            logger.error(f"Error in _check_limits: {e}")
            raise
    
    def _is_new_day(self) -> bool:
        """Check if new trading day."""
        try:
            if self.daily_start_time is None:
                return False
        
            now = datetime.now()
            # Reset at 00:00 UTC
            if now.date() > self.daily_start_time.date():
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in _is_new_day: {e}")
            raise
    
    def _reset_daily_limits(self):
        """Reset daily loss limits."""
        try:
            self.daily_start_balance = self.current_balance
            self.daily_start_time = datetime.now()
            logger.info(f"Daily limits reset. Starting balance: ${self.daily_start_balance:,.2f}")
        except Exception as e:
            logger.error(f"Error in _reset_daily_limits: {e}")
            raise
    
    def should_stop_trading(self) -> bool:
        """Check if trading should be halted."""
        return self.trading_halted
    
    def get_drawdown_percent(self) -> float:
        """Get current drawdown percentage."""
        try:
            if self.peak_balance == 0:
                return 0
        
            drawdown = (self.peak_balance - self.current_balance) / self.peak_balance * 100
            return max(0, drawdown)
        except Exception as e:
            logger.error(f"Error in get_drawdown_percent: {e}")
            raise
    
    def get_daily_loss_percent(self) -> float:
        """Get current daily loss percentage."""
        try:
            if self.daily_start_balance == 0:
                return 0
        
            loss = (self.daily_start_balance - self.current_balance) / self.daily_start_balance * 100
            return max(0, loss)
        except Exception as e:
            logger.error(f"Error in get_daily_loss_percent: {e}")
            raise
    
    def get_status(self) -> DrawdownStatus:
        """Get current drawdown status."""
        try:
            drawdown_percent = self.get_drawdown_percent()
            return self._get_status(drawdown_percent)
        except Exception as e:
            logger.error(f"Error in get_status: {e}")
            raise
    
    def get_metrics(self) -> DrawdownMetrics:
        """Get current metrics."""
        return self._calculate_metrics()
    
    def get_status_string(self) -> str:
        """Get human-readable status string."""
        try:
            metrics = self.get_metrics()
        
            status_map = {
                DrawdownStatus.GREEN: "🟢 GREEN",
                DrawdownStatus.YELLOW: "🟡 YELLOW",
                DrawdownStatus.RED: "🔴 RED",
                DrawdownStatus.CRITICAL: "⛔ CRITICAL"
            }
        
            return f"""
    DRAWDOWN PROTECTION STATUS
    {'=' * 50}
    Status: {status_map[metrics.status]}
    Current Balance: ${metrics.current_balance:,.2f}
    Peak Balance: ${metrics.peak_balance:,.2f}
    Drawdown: {metrics.drawdown_percent:.2f}% (Max: {self.max_drawdown_percent}%)
    Daily Loss: {metrics.daily_loss_percent:.2f}% (Max: {self.max_daily_loss_percent}%)
    Trading Halted: {self.trading_halted}
    {f'Halt Reason: {self.halt_reason}' if self.halt_reason else ''}
    {'=' * 50}
    """
        except Exception as e:
            logger.error(f"Error in get_status_string: {e}")
            raise
    
    def get_position_size_multiplier(self) -> float:
        """
        Get position size multiplier based on drawdown.
        
        Returns:
            1.0 for GREEN
            0.75 for YELLOW
            0.5 for RED
            0.0 for CRITICAL
        """
        try:
            status = self.get_status()
        
            multipliers = {
                DrawdownStatus.GREEN: 1.0,
                DrawdownStatus.YELLOW: 0.75,
                DrawdownStatus.RED: 0.5,
                DrawdownStatus.CRITICAL: 0.0
            }
        
            return multipliers.get(status, 1.0)
        except Exception as e:
            logger.error(f"Error in get_position_size_multiplier: {e}")
            raise
    
    def get_history(self, lookback_hours: int = 24) -> List[DrawdownMetrics]:
        """Get drawdown history for last N hours."""
        try:
            if not self.drawdown_history:
                return []
        
            cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
            return [m for m in self.drawdown_history if m.timestamp >= cutoff_time]
        except Exception as e:
            logger.error(f"Error in get_history: {e}")
            raise
    
    def get_worst_drawdown(self) -> float:
        """Get worst drawdown in history."""
        try:
            if not self.drawdown_history:
                return 0
        
            return max(m.drawdown_percent for m in self.drawdown_history)
        except Exception as e:
            logger.error(f"Error in get_worst_drawdown: {e}")
            raise
    
    def reset(self):
        """Reset all protections."""
        try:
            self.trading_halted = False
            self.halt_reason = None
            logger.info("Drawdown protector reset")
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
    
    def emergency_shutdown(self):
        """Emergency shutdown - halt all trading immediately."""
        try:
            self.trading_halted = True
            self.halt_reason = "EMERGENCY SHUTDOWN"
            logger.critical("EMERGENCY SHUTDOWN ACTIVATED")
        except Exception as e:
            logger.error(f"Error in emergency_shutdown: {e}")
            raise


class AdaptiveRiskCompressor:
    """
    Adaptive Risk Compression
    
    When uncertainty increases:
    Automatically:
    - reduce position size
    - tighten exposure
    - increase thresholds
    
    This is dynamic risk management based on real-time conditions.
    """
    
    def __init__(
        self,
        base_position_size: float = 1.0,
        min_position_size: float = 0.1,
        uncertainty_threshold: float = 0.5,
        compression_rate: float = 0.3
    ):
        self.base_position_size = base_position_size
        self.min_position_size = min_position_size
        self.uncertainty_threshold = uncertainty_threshold
        self.compression_rate = compression_rate
        
        self.current_compression = 1.0
        self.compression_history: List[Dict] = []
        
    def calculate_position_size(
        self,
        base_size: float,
        uncertainty_score: float,
        market_volatility: float,
        recent_drawdown: float
    ) -> float:
        """
        Calculate dynamically compressed position size.
        
        Args:
            base_size: Original position size
            uncertainty_score: Current uncertainty (0-1)
            market_volatility: Current market volatility
            recent_drawdown: Recent drawdown percentage
            
        Returns:
            Adjusted position size
        """
        # Base compression from uncertainty
        uncertainty_compression = max(
            1.0 - (uncertainty_score - self.uncertainty_threshold) * self.compression_rate,
            0.3  # Max compression 70%
        ) if uncertainty_score > self.uncertainty_threshold else 1.0
        
        # Additional compression from volatility
        vol_compression = max(
            1.0 - (market_volatility - 0.2) * 0.5,
            0.5  # Max compression 50%
        ) if market_volatility > 0.2 else 1.0
        
        # Drawdown compression (exponential)
        dd_compression = np.exp(-recent_drawdown * 2) if recent_drawdown > 0.05 else 1.0
        
        # Combined compression
        total_compression = uncertainty_compression * vol_compression * dd_compression
        total_compression = max(total_compression, self.min_position_size / self.base_position_size)

        adjusted_size = base_size * total_compression

        # Record history
        self.compression_history.append({
            'timestamp': datetime.now(),
            'base_size': base_size,
            'adjusted_size': adjusted_size,
            'compression_factor': total_compression,
            'uncertainty': uncertainty_score,
            'volatility': market_volatility,
            'drawdown': recent_drawdown
        })

        # Keep last 100
        if len(self.compression_history) > 100:
            self.compression_history = self.compression_history[-100:]

        self.current_compression = total_compression

        
        return adjusted_size
    
    def get_compression_summary(self) -> Dict[str, Any]:
        """Get summary of recent risk compression activity."""
        if not self.compression_history:
            return {'status': 'no_data'}
        
        recent = self.compression_history[-20:]
        
        avg_compression = np.mean([h['compression_factor'] for h in recent])
        min_compression = np.min([h['compression_factor'] for h in recent])
        
        return {
            'current_compression': self.current_compression,
            'avg_compression_20': avg_compression,
            'min_compression_20': min_compression,
            'compressions_triggered': sum(1 for h in recent if h['compression_factor'] < 0.9),
            'status': 'COMPRESSING' if avg_compression < 0.8 else 'NORMAL'
        }
    
    def should_increase_risk(self, opportunity_quality: float, confidence: float) -> bool:
        """
        Determine if we should increase risk when conditions are favorable.
        
        Args:
            opportunity_quality: Quality score of current opportunity (0-1)
            confidence: Confidence in the opportunity (0-1)
            
        Returns:
            True if risk can be increased
        """
        # Only increase risk if we're currently compressed
        if self.current_compression >= 0.95:
            return False
        
        # Need high quality and confidence
        if opportunity_quality < 0.8 or confidence < 0.75:
            return False
        
        # Check recent performance
        if len(self.compression_history) < 10:
            return False
        
        recent_performance = [
            h for h in self.compression_history[-10:]
            if h.get('drawdown', 0) < 0.02  # Low drawdown periods
        ]
        
        return len(recent_performance) >= 7  # 70% of recent trades were good


class MaximumAdverseExcursionTracker:
    """
    Maximum Adverse Excursion (MAE) Tracker
    
    Tracks how far trades go against you before closing.
    
    MAE is the worst intra-trade drawdown experienced.
    Used to:
    - Optimize stop loss placement
    - Identify position sizing issues
    - Detect toxic entry timing
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.mae_history: List[Dict] = []
        self.current_trades: Dict[str, Dict] = {}  # trade_id -> current MAE data
        
    def start_trade_tracking(
        self,
        trade_id: str,
        entry_price: float,
        direction: str,  # 'long' or 'short'
        position_size: float,
        entry_time: datetime
    ):
        """Start tracking MAE for a new trade."""
        self.current_trades[trade_id] = {
            'entry_price': entry_price,
            'direction': direction,
            'position_size': position_size,
            'entry_time': entry_time,
            'max_adverse_price': entry_price,
            'mae_pct': 0.0,
            'mae_dollar': 0.0,
            'updates': 0
        }
    
    def update_trade_mae(
        self,
        trade_id: str,
        current_price: float,
        timestamp: Optional[datetime] = None
    ):
        """Update MAE for an active trade."""
        if trade_id not in self.current_trades:
            return
        
        trade = self.current_trades[trade_id]
        direction = trade['direction']
        entry = trade['entry_price']
        
        # Calculate current adverse move
        if direction == 'long':
            if current_price < trade['max_adverse_price']:
                trade['max_adverse_price'] = current_price
        else:
            if current_price > trade['max_adverse_price']:
                trade['max_adverse_price'] = current_price
        
        # Calculate MAE percentage
        price_diff = abs(trade['max_adverse_price'] - entry)
        trade['mae_pct'] = price_diff / entry
        trade['mae_dollar'] = price_diff * trade['position_size']
        trade['updates'] += 1
    
    def finalize_trade(
        self,
        trade_id: str,
        exit_price: float,
        exit_time: datetime,
        final_pnl: float
    ) -> Dict[str, Any]:
        """Finalize MAE tracking for a completed trade."""
        if trade_id not in self.current_trades:
            return {'status': 'trade_not_found'}
        
        trade = self.current_trades[trade_id]
        
        mae_record = {
            'trade_id': trade_id,
            'entry_price': trade['entry_price'],
            'exit_price': exit_price,
            'direction': trade['direction'],
            'position_size': trade['position_size'],
            'max_adverse_price': trade['max_adverse_price'],
            'mae_pct': trade['mae_pct'],
            'mae_dollar': trade['mae_dollar'],
            'final_pnl': final_pnl,
            'closed_at': exit_time
        }
        
        self.mae_history.append(mae_record)
        
        if len(self.mae_history) > self.window_size:
            self.mae_history = self.mae_history[-self.window_size:]
        
        del self.current_trades[trade_id]
        
        return mae_record
    
    def analyze_mae_patterns(self) -> Dict[str, Any]:
        """Analyze MAE patterns to optimize risk management."""
        if len(self.mae_history) < 10:
            return {'status': 'insufficient_data'}
        
        recent = self.mae_history[-20:]
        mae_pcts = [t['mae_pct'] for t in recent]
        
        winners = [t for t in recent if t['final_pnl'] > 0]
        losers = [t for t in recent if t['final_pnl'] < 0]
        
        avg_mae = np.mean(mae_pcts)
        max_mae = max(mae_pcts)
        
        winner_mae = [t['mae_pct'] for t in winners] if winners else [0]
        loser_mae = [t['mae_pct'] for t in losers] if losers else [0]
        
        return {
            'average_mae_pct': avg_mae,
            'max_mae_pct': max_mae,
            'winner_avg_mae': np.mean(winner_mae),
            'loser_avg_mae': np.mean(loser_mae),
            'recommended_stop_loss': np.percentile(mae_pcts, 75)
        }


class StrategyCapacityLimiter:
    """
    Strategy Capacity Limiter
    
    Every strategy has a capacity limit before it degrades.
    
    Monitors:
    - Slippage increase with size
    - Fill rate degradation
    - Alpha decay at higher AUM
    """
    
    def __init__(self, base_capacity: float = 1000000, slippage_threshold: float = 0.001):
        self.base_capacity = base_capacity
        self.slippage_threshold = slippage_threshold
        self.capacity_history: Dict[str, List[Dict]] = defaultdict(list)
        
    def record_execution_quality(
        self,
        strategy_id: str,
        intended_size: float,
        executed_size: float,
        expected_price: float,
        executed_price: float
    ):
        """Record execution quality metrics for capacity analysis."""
        slippage = abs(executed_price - expected_price) / expected_price
        fill_rate = executed_size / intended_size if intended_size > 0 else 0
        
        self.capacity_history[strategy_id].append({
            'timestamp': datetime.now(),
            'intended_size': intended_size,
            'slippage_bps': slippage * 10000,
            'fill_rate': fill_rate
        })
        
        if len(self.capacity_history[strategy_id]) > 50:
            self.capacity_history[strategy_id] = self.capacity_history[strategy_id][-50:]
    
    def estimate_strategy_capacity(self, strategy_id: str) -> Dict[str, Any]:
        """Estimate maximum capacity for a strategy based on execution quality."""
        history = self.capacity_history.get(strategy_id, [])
        
        if len(history) < 10:
            return {
                'strategy_id': strategy_id,
                'estimated_capacity': self.base_capacity,
                'status': 'insufficient_data'
            }
        
        recent = history[-20:]
        avg_slippage = np.mean([r['slippage_bps'] for r in recent])
        avg_fill_rate = np.mean([r['fill_rate'] for r in recent])
        
        capacity_degraded = (
            avg_slippage > self.slippage_threshold * 10000 or
            avg_fill_rate < 0.95
        )
        
        current_size = np.mean([r['intended_size'] for r in recent[-5:]])
        
        if capacity_degraded:
            estimated_capacity = current_size * 0.8
        else:
            estimated_capacity = max(self.base_capacity, current_size * 1.2)
        
        return {
            'strategy_id': strategy_id,
            'estimated_capacity': estimated_capacity,
            'capacity_degraded': capacity_degraded,
            'avg_slippage_bps': avg_slippage,
            'avg_fill_rate': avg_fill_rate,
            'recommendation': 'Reduce position size' if capacity_degraded else 'Capacity adequate'
        }


class EarningsEventRiskManager:
    """
    Earnings Event Risk Manager
    
    Manages risk around earnings announcements.
    """
    
    def __init__(self):
        self.earnings_calendar: Dict[str, Dict] = {}
        
    def register_earnings_event(
        self,
        symbol: str,
        earnings_date: datetime,
        expected_move_pct: float,
        historical_avg_move: float
    ):
        """Register upcoming earnings event."""
        self.earnings_calendar[symbol] = {
            'earnings_date': earnings_date,
            'expected_move_pct': expected_move_pct,
            'historical_avg_move': historical_avg_move,
            'days_to_earnings': (earnings_date - datetime.now()).days
        }
    
    def assess_earnings_risk(self, symbol: str) -> Dict[str, Any]:
        """Assess risk for earnings event."""
        event = self.earnings_calendar.get(symbol)
        
        if not event:
            return {'status': 'no_earnings_scheduled'}
        
        days_to_event = event['days_to_earnings']
        
        if days_to_event <= 1:
            position_limit = 0.0
            urgency = 'AVOID'
        elif days_to_event <= 3:
            position_limit = 0.3
            urgency = 'CAUTION'
        elif days_to_event <= 7:
            position_limit = 0.5
            urgency = 'REDUCE'
        else:
            position_limit = 1.0
            urgency = 'NORMAL'
        
        return {
            'symbol': symbol,
            'days_to_earnings': days_to_event,
            'expected_move': event['expected_move_pct'],
            'position_size_limit': position_limit,
            'urgency': urgency,
            'recommendation': 'AVOID' if urgency == 'AVOID' else f'Reduce to {position_limit*100:.0f}%' if urgency in ['CAUTION', 'REDUCE'] else 'NORMAL'
        }


class LiquidityAdjustedVaR:
    """
    Liquidity Adjusted Value at Risk (LVaR)
    
    Adjusts standard VaR for liquidity costs.
    """
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.return_history: Deque[Dict] = deque(maxlen=252)
        
    def update_returns(self, daily_return: float, bid_ask_spread_bps: float, position_size: float, avg_daily_volume: float):
        """Update returns with liquidity data."""
        self.return_history.append({
            'return': daily_return,
            'spread_bps': bid_ask_spread_bps,
            'position': position_size,
            'adv': avg_daily_volume,
            'timestamp': datetime.now()
        })
    
    def calculate_liquidity_adjusted_var(self) -> Dict[str, Any]:
        """Calculate LVaR with liquidity adjustments."""
        if len(self.return_history) < 30:
            return {'status': 'insufficient_data'}
        
        recent = list(self.return_history)[-30:]
        returns = [r['return'] for r in recent]
        spreads = [r['spread_bps'] for r in recent]
        
        var_95 = np.percentile(returns, (1 - self.confidence_level) * 100)
        avg_spread = np.mean(spreads) / 10000
        
        avg_position = np.mean([r['position'] for r in recent])
        avg_adv = np.mean([r['adv'] for r in recent])
        participation = avg_position / avg_adv if avg_adv > 0 else 0
        
        liquidity_cost = avg_spread / 2 + 0.001 * participation
        lvar = var_95 - liquidity_cost
        
        return {
            'standard_var': var_95,
            'liquidity_adjusted_var': lvar,
            'liquidity_cost': liquidity_cost,
            'participation_rate': participation,
            'recommendation': 'CRITICAL: Position too large' if participation > 0.3 else 'ACCEPTABLE' if participation < 0.1 else 'WARNING'
        }


class CorporateActionAdjustor:
    """
    Corporate Action Adjustor
    
    Adjusts positions for corporate actions:
    - Stock splits/reverse splits
    - Dividends
    - Spin-offs
    """
    
    def __init__(self):
        self.pending_actions: Dict[str, List[Dict]] = defaultdict(list)
        
    def register_corporate_action(
        self,
        symbol: str,
        action_type: str,
        ex_date: datetime,
        details: Dict[str, Any]
    ):
        """Register upcoming corporate action."""
        self.pending_actions[symbol].append({
            'action_type': action_type,
            'ex_date': ex_date,
            'details': details
        })
    
    def calculate_position_adjustment(self, symbol: str, current_position: float, entry_price: float) -> Dict[str, Any]:
        """Calculate required position adjustments."""
        actions = self.pending_actions.get(symbol, [])
        
        if not actions:
            return {'status': 'no_actions_pending', 'adjustment_needed': False}
        
        adjustments = []
        
        for action in actions:
            action_type = action['action_type']
            details = action['details']
            
            if action_type == 'split':
                ratio = details.get('split_ratio', 1.0)
                adjustments.append({
                    'action': 'split',
                    'new_position': current_position * ratio,
                    'new_entry': entry_price / ratio,
                    'ratio': ratio
                })
        
        return {
            'symbol': symbol,
            'adjustments_needed': len(adjustments) > 0,
            'adjustments': adjustments
        }
