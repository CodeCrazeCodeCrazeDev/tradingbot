"""
Drawdown Recovery System
========================

Manages position sizing during drawdowns:
1. Reduced position size after losses
2. Gradual size increase after wins
3. Recovery mode detection
4. Conservative mode triggers
5. Psychological break enforcement

Target: Faster recovery from losses
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import numpy

logger = logging.getLogger(__name__)


class RecoveryMode(Enum):
    """Recovery mode states"""
    NORMAL = "normal"
    CAUTIOUS = "cautious"
    RECOVERY = "recovery"
    AGGRESSIVE_RECOVERY = "aggressive_recovery"
    PROTECTION = "protection"


class TradingState(Enum):
    """Overall trading state"""
    ACTIVE = "active"
    REDUCED = "reduced"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class PerformanceSnapshot:
    """Snapshot of trading performance"""
    timestamp: datetime
    balance: float
    equity: float
    drawdown: float
    drawdown_pct: float
    win_streak: int
    loss_streak: int
    recent_win_rate: float
    pnl_today: float
    pnl_week: float


@dataclass
class RecoveryPlan:
    """Recovery plan after drawdown"""
    mode: RecoveryMode
    position_multiplier: float
    max_trades_per_day: int
    required_win_rate: float
    exit_conditions: List[str]
    recommendations: List[str]


class PerformanceTracker:
    """
    Tracks trading performance for recovery decisions.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initial balance
        self.initial_balance = self.config.get('initial_balance', 10000)
        self.peak_balance = self.initial_balance
        
        # Trade history
        self.trades: List[Dict] = []
        self.daily_pnl: Dict[str, float] = {}
        
        # Streak tracking
        self.current_streak = 0  # Positive = wins, negative = losses
        self.max_win_streak = 0
        self.max_loss_streak = 0
        
        logger.info("PerformanceTracker initialized")
    
    def record_trade(
        self,
        pnl: float,
        symbol: str,
        direction: str,
        entry_time: datetime,
        exit_time: datetime
    ):
        """Record a completed trade"""
        trade = {
            'pnl': pnl,
            'symbol': symbol,
            'direction': direction,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'is_win': pnl > 0,
        }
        self.trades.append(trade)
        
        # Update daily PnL
        date_key = exit_time.strftime('%Y-%m-%d')
        self.daily_pnl[date_key] = self.daily_pnl.get(date_key, 0) + pnl
        
        # Update streaks
        if pnl > 0:
            if self.current_streak >= 0:
                self.current_streak += 1
            else:
                self.current_streak = 1
            self.max_win_streak = max(self.max_win_streak, self.current_streak)
        else:
            if self.current_streak <= 0:
                self.current_streak -= 1
            else:
                self.current_streak = -1
            self.max_loss_streak = max(self.max_loss_streak, abs(self.current_streak))
    
    def update_balance(self, current_balance: float):
        """Update current balance and peak"""
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance
    
    def get_snapshot(self, current_balance: float) -> PerformanceSnapshot:
        """Get current performance snapshot"""
        self.update_balance(current_balance)
        
        # Calculate drawdown
        drawdown = self.peak_balance - current_balance
        drawdown_pct = drawdown / self.peak_balance if self.peak_balance > 0 else 0
        
        # Calculate recent win rate (last 20 trades)
        recent_trades = self.trades[-20:] if self.trades else []
        recent_wins = sum(1 for t in recent_trades if t['is_win'])
        recent_win_rate = recent_wins / len(recent_trades) if recent_trades else 0.5
        
        # Calculate today's PnL
        today = datetime.now().strftime('%Y-%m-%d')
        pnl_today = self.daily_pnl.get(today, 0)
        
        # Calculate week's PnL
        week_start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        pnl_week = sum(
            pnl for date, pnl in self.daily_pnl.items()
            if date >= week_start
        )
        
        return PerformanceSnapshot(
            timestamp=datetime.now(),
            balance=current_balance,
            equity=current_balance,  # Simplified
            drawdown=drawdown,
            drawdown_pct=drawdown_pct,
            win_streak=self.current_streak if self.current_streak > 0 else 0,
            loss_streak=abs(self.current_streak) if self.current_streak < 0 else 0,
            recent_win_rate=recent_win_rate,
            pnl_today=pnl_today,
            pnl_week=pnl_week
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        if not self.trades:
            return {}
        
        wins = [t['pnl'] for t in self.trades if t['is_win']]
        losses = [abs(t['pnl']) for t in self.trades if not t['is_win']]
        
        return {
            'total_trades': len(self.trades),
            'win_rate': len(wins) / len(self.trades),
            'avg_win': np.mean(wins) if wins else 0,
            'avg_loss': np.mean(losses) if losses else 0,
            'profit_factor': sum(wins) / sum(losses) if losses and sum(losses) > 0 else 0,
            'max_win_streak': self.max_win_streak,
            'max_loss_streak': self.max_loss_streak,
            'current_streak': self.current_streak,
            'total_pnl': sum(t['pnl'] for t in self.trades),
        }


class DrawdownRecoveryManager:
    """
    Manages trading during drawdown periods.
    
    PRINCIPLE: Protect capital during losing streaks, recover systematically.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize tracker
        self.tracker = PerformanceTracker(self.config.get('tracker', {}))
        
        # Drawdown thresholds
        self.cautious_threshold = self.config.get('cautious_threshold', 0.05)  # 5%
        self.recovery_threshold = self.config.get('recovery_threshold', 0.10)  # 10%
        self.protection_threshold = self.config.get('protection_threshold', 0.15)  # 15%
        self.stop_threshold = self.config.get('stop_threshold', 0.20)  # 20%
        
        # Loss streak thresholds
        self.cautious_streak = self.config.get('cautious_streak', 3)
        self.pause_streak = self.config.get('pause_streak', 5)
        
        # Position size multipliers
        self.cautious_multiplier = self.config.get('cautious_multiplier', 0.75)
        self.recovery_multiplier = self.config.get('recovery_multiplier', 0.50)
        self.protection_multiplier = self.config.get('protection_multiplier', 0.25)
        
        # Recovery requirements
        self.recovery_win_rate = self.config.get('recovery_win_rate', 0.55)
        self.recovery_trades = self.config.get('recovery_trades', 10)
        
        # Current state
        self.current_mode = RecoveryMode.NORMAL
        self.trading_state = TradingState.ACTIVE
        self.pause_until: Optional[datetime] = None
        
        logger.info("DrawdownRecoveryManager initialized")
    
    def assess_state(self, current_balance: float) -> RecoveryPlan:
        """
        Assess current state and create recovery plan.
        
        Args:
            current_balance: Current account balance
        
        Returns:
            RecoveryPlan with recommendations
        """
        snapshot = self.tracker.get_snapshot(current_balance)
        recommendations = []
        exit_conditions = []
        
        # Determine mode based on drawdown
        if snapshot.drawdown_pct >= self.stop_threshold:
            self.current_mode = RecoveryMode.PROTECTION
            self.trading_state = TradingState.STOPPED
            multiplier = 0.0
            max_trades = 0
            recommendations.append("STOP TRADING: Maximum drawdown reached")
            recommendations.append("Review strategy before resuming")
            exit_conditions.append(f"Drawdown below {self.protection_threshold:.0%}")
            
        elif snapshot.drawdown_pct >= self.protection_threshold:
            self.current_mode = RecoveryMode.PROTECTION
            self.trading_state = TradingState.REDUCED
            multiplier = self.protection_multiplier
            max_trades = 2
            recommendations.append("Protection mode: Minimal position sizes")
            recommendations.append("Focus on high-probability setups only")
            exit_conditions.append(f"Win rate above {self.recovery_win_rate:.0%} for {self.recovery_trades} trades")
            
        elif snapshot.drawdown_pct >= self.recovery_threshold:
            self.current_mode = RecoveryMode.RECOVERY
            self.trading_state = TradingState.REDUCED
            multiplier = self.recovery_multiplier
            max_trades = 3
            recommendations.append("Recovery mode: Reduced position sizes")
            recommendations.append("Be selective with trade entries")
            exit_conditions.append(f"Drawdown below {self.cautious_threshold:.0%}")
            
        elif snapshot.drawdown_pct >= self.cautious_threshold:
            self.current_mode = RecoveryMode.CAUTIOUS
            self.trading_state = TradingState.ACTIVE
            multiplier = self.cautious_multiplier
            max_trades = 5
            recommendations.append("Cautious mode: Slightly reduced sizes")
            exit_conditions.append(f"Drawdown below {self.cautious_threshold/2:.0%}")
            
        else:
            self.current_mode = RecoveryMode.NORMAL
            self.trading_state = TradingState.ACTIVE
            multiplier = 1.0
            max_trades = 10
        
        # Adjust for loss streak
        if snapshot.loss_streak >= self.pause_streak:
            self.trading_state = TradingState.PAUSED
            self.pause_until = datetime.now() + timedelta(hours=4)
            multiplier = 0.0
            max_trades = 0
            recommendations.append(f"PAUSE: {snapshot.loss_streak} consecutive losses")
            recommendations.append(f"Resume after {self.pause_until.strftime('%H:%M')}")
            
        elif snapshot.loss_streak >= self.cautious_streak:
            multiplier *= 0.75
            recommendations.append(f"Loss streak ({snapshot.loss_streak}): Further reduced size")
        
        # Adjust for win streak (gradual increase)
        if snapshot.win_streak >= 3 and self.current_mode != RecoveryMode.NORMAL:
            multiplier = min(1.0, multiplier * 1.25)
            recommendations.append(f"Win streak ({snapshot.win_streak}): Gradually increasing size")
        
        # Check daily loss limit
        daily_loss_limit = self.tracker.initial_balance * 0.03  # 3% daily
        if snapshot.pnl_today < -daily_loss_limit:
            self.trading_state = TradingState.PAUSED
            self.pause_until = datetime.now().replace(hour=0, minute=0) + timedelta(days=1)
            multiplier = 0.0
            max_trades = 0
            recommendations.append("Daily loss limit reached - trading paused until tomorrow")
        
        return RecoveryPlan(
            mode=self.current_mode,
            position_multiplier=multiplier,
            max_trades_per_day=max_trades,
            required_win_rate=self.recovery_win_rate,
            exit_conditions=exit_conditions,
            recommendations=recommendations
        )
    
    def can_trade(self) -> Tuple[bool, str]:
        """
        Check if trading is currently allowed.
        
        Returns:
            Tuple of (can_trade, reason)
        """
        if self.trading_state == TradingState.STOPPED:
            return False, "Trading stopped due to maximum drawdown"
        
        if self.trading_state == TradingState.PAUSED:
            if self.pause_until and datetime.now() < self.pause_until:
                remaining = (self.pause_until - datetime.now()).total_seconds() / 60
                return False, f"Trading paused for {remaining:.0f} more minutes"
            else:
                self.trading_state = TradingState.ACTIVE
                self.pause_until = None
        
        return True, f"Trading allowed ({self.current_mode.value} mode)"
    
    def get_position_multiplier(self, current_balance: float) -> float:
        """Get current position size multiplier"""
        plan = self.assess_state(current_balance)
        return plan.position_multiplier
    
    def record_trade(
        self,
        pnl: float,
        symbol: str,
        direction: str,
        entry_time: datetime,
        exit_time: datetime
    ):
        """Record a trade result"""
        self.tracker.record_trade(pnl, symbol, direction, entry_time, exit_time)
    
    def get_recovery_progress(self, current_balance: float) -> Dict[str, Any]:
        """Get recovery progress information"""
        snapshot = self.tracker.get_snapshot(current_balance)
        stats = self.tracker.get_statistics()
        
        # Calculate recovery progress
        if snapshot.drawdown > 0:
            recovery_needed = snapshot.drawdown
            recovery_pct = 0.0
        else:
            recovery_needed = 0
            recovery_pct = 1.0
        
        return {
            'mode': self.current_mode.value,
            'trading_state': self.trading_state.value,
            'drawdown': snapshot.drawdown,
            'drawdown_pct': snapshot.drawdown_pct,
            'recovery_needed': recovery_needed,
            'recovery_progress': recovery_pct,
            'current_streak': snapshot.win_streak if snapshot.win_streak > 0 else -snapshot.loss_streak,
            'recent_win_rate': snapshot.recent_win_rate,
            'pnl_today': snapshot.pnl_today,
            'pnl_week': snapshot.pnl_week,
            'total_trades': stats.get('total_trades', 0),
            'overall_win_rate': stats.get('win_rate', 0),
        }
    
    def reset(self, new_balance: float):
        """Reset tracker with new balance"""
        self.tracker = PerformanceTracker({
            'initial_balance': new_balance,
            **self.config.get('tracker', {})
        })
        self.current_mode = RecoveryMode.NORMAL
        self.trading_state = TradingState.ACTIVE
        self.pause_until = None
