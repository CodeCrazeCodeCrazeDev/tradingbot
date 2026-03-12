"""
Paper Trading Validator

Comprehensive validation system for paper trading before going live.
Tracks performance, validates against thresholds, and generates reports.
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import statistics
import math

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation status enumeration"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_MORE_DATA = "needs_more_data"


@dataclass
class Trade:
    """Individual trade record"""
    trade_id: str
    symbol: str
    direction: str  # 'buy' or 'sell'
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    quantity: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    duration_minutes: float = 0.0
    exit_reason: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'entry_price': self.entry_price,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'exit_price': self.exit_price,
            'quantity': self.quantity,
            'pnl': self.pnl,
            'pnl_pct': self.pnl_pct,
            'commission': self.commission,
            'slippage': self.slippage,
            'duration_minutes': self.duration_minutes,
            'exit_reason': self.exit_reason
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics container"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    net_profit: float = 0.0
    profit_factor: float = 0.0
    
    avg_win: float = 0.0
    avg_loss: float = 0.0
    avg_trade: float = 0.0
    avg_rr_ratio: float = 0.0
    
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    current_drawdown: float = 0.0
    
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    current_streak: int = 0
    
    avg_trade_duration_minutes: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    
    total_commission: float = 0.0
    total_slippage: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ValidationThresholds:
    """Validation thresholds configuration"""
    min_win_rate: float = 0.45
    min_profit_factor: float = 1.2
    max_drawdown: float = 0.15
    min_sharpe_ratio: float = 0.5
    max_consecutive_losses: int = 8
    min_avg_rr_ratio: float = 1.5
    min_trades: int = 50
    min_days: int = 7


@dataclass
class ValidationResult:
    """Validation result"""
    status: ValidationStatus
    passed_checks: List[str]
    failed_checks: List[str]
    warnings: List[str]
    metrics: PerformanceMetrics
    recommendations: List[str]
    ready_for_live: bool
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'status': self.status.value,
            'passed_checks': self.passed_checks,
            'failed_checks': self.failed_checks,
            'warnings': self.warnings,
            'metrics': self.metrics.to_dict(),
            'recommendations': self.recommendations,
            'ready_for_live': self.ready_for_live,
            'timestamp': self.timestamp.isoformat()
        }


class PaperTradingValidator:
    """
    Comprehensive paper trading validation system.
    
    Tracks all trades, calculates performance metrics, and validates
    against configurable thresholds before allowing live trading.
    """
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        thresholds: Optional[ValidationThresholds] = None,
        data_dir: str = "data/paper_trading"
    ):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.peak_capital = initial_capital
        self.thresholds = thresholds or ValidationThresholds()
        self.data_dir = data_dir
        
        # Trade tracking
        self.trades: List[Trade] = []
        self.open_positions: Dict[str, Trade] = {}
        
        # Session tracking
        self.session_start = datetime.now()
        self.daily_pnl: Dict[str, float] = {}
        
        # Equity curve
        self.equity_curve: List[Tuple[datetime, float]] = [(datetime.now(), initial_capital)]
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        logger.info(f"Paper Trading Validator initialized with ${initial_capital:,.2f} capital")
    
    def record_trade_entry(
        self,
        trade_id: str,
        symbol: str,
        direction: str,
        entry_price: float,
        quantity: float,
        commission: float = 0.0
    ) -> Trade:
        """Record a new trade entry"""
        trade = Trade(
            trade_id=trade_id,
            symbol=symbol,
            direction=direction,
            entry_time=datetime.now(),
            entry_price=entry_price,
            quantity=quantity,
            commission=commission
        )
        
        self.open_positions[trade_id] = trade
        logger.info(f"Trade entry recorded: {trade_id} - {direction} {quantity} {symbol} @ {entry_price}")
        
        return trade
    
    def record_trade_exit(
        self,
        trade_id: str,
        exit_price: float,
        exit_reason: str = "",
        slippage: float = 0.0
    ) -> Optional[Trade]:
        """Record a trade exit"""
        if trade_id not in self.open_positions:
            logger.warning(f"Trade {trade_id} not found in open positions")
            return None
        
        trade = self.open_positions.pop(trade_id)
        trade.exit_time = datetime.now()
        trade.exit_price = exit_price
        trade.exit_reason = exit_reason
        trade.slippage = slippage
        
        # Calculate P&L
        if trade.direction == 'buy':
            trade.pnl = (exit_price - trade.entry_price) * trade.quantity - trade.commission - slippage
        else:
            trade.pnl = (trade.entry_price - exit_price) * trade.quantity - trade.commission - slippage
        
        trade.pnl_pct = trade.pnl / (trade.entry_price * trade.quantity) if trade.entry_price > 0 else 0
        trade.duration_minutes = (trade.exit_time - trade.entry_time).total_seconds() / 60
        
        # Update capital
        self.current_capital += trade.pnl
        self.peak_capital = max(self.peak_capital, self.current_capital)
        
        # Update equity curve
        self.equity_curve.append((datetime.now(), self.current_capital))
        
        # Track daily P&L
        date_key = trade.exit_time.strftime("%Y-%m-%d")
        self.daily_pnl[date_key] = self.daily_pnl.get(date_key, 0) + trade.pnl
        
        # Add to completed trades
        self.trades.append(trade)
        
        logger.info(f"Trade exit recorded: {trade_id} - P&L: ${trade.pnl:.2f} ({trade.pnl_pct:.2%})")
        
        return trade
    
    def calculate_metrics(self) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        metrics = PerformanceMetrics()
        
        if not self.trades:
            return metrics
        
        # Basic counts
        metrics.total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]
        
        metrics.winning_trades = len(winning_trades)
        metrics.losing_trades = len(losing_trades)
        metrics.win_rate = metrics.winning_trades / metrics.total_trades if metrics.total_trades > 0 else 0
        
        # Profit/Loss
        metrics.gross_profit = sum(t.pnl for t in winning_trades)
        metrics.gross_loss = abs(sum(t.pnl for t in losing_trades))
        metrics.net_profit = metrics.gross_profit - metrics.gross_loss
        metrics.profit_factor = metrics.gross_profit / metrics.gross_loss if metrics.gross_loss > 0 else float('inf')
        
        # Averages
        metrics.avg_win = metrics.gross_profit / metrics.winning_trades if metrics.winning_trades > 0 else 0
        metrics.avg_loss = metrics.gross_loss / metrics.losing_trades if metrics.losing_trades > 0 else 0
        metrics.avg_trade = metrics.net_profit / metrics.total_trades if metrics.total_trades > 0 else 0
        metrics.avg_rr_ratio = metrics.avg_win / metrics.avg_loss if metrics.avg_loss > 0 else float('inf')
        
        # Drawdown calculation
        peak = self.initial_capital
        max_dd = 0
        for _, equity in self.equity_curve:
            peak = max(peak, equity)
            dd = (peak - equity) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        metrics.max_drawdown = (self.peak_capital - min(e[1] for e in self.equity_curve)) if self.equity_curve else 0
        metrics.max_drawdown_pct = max_dd
        metrics.current_drawdown = (self.peak_capital - self.current_capital) / self.peak_capital if self.peak_capital > 0 else 0
        
        # Risk-adjusted returns
        if len(self.trades) >= 2:
            returns = [t.pnl_pct for t in self.trades]
            avg_return = statistics.mean(returns)
            std_return = statistics.stdev(returns) if len(returns) > 1 else 0
            
            # Sharpe Ratio (assuming 0% risk-free rate for simplicity)
            metrics.sharpe_ratio = (avg_return / std_return) * math.sqrt(252) if std_return > 0 else 0
            
            # Sortino Ratio (downside deviation)
            negative_returns = [r for r in returns if r < 0]
            if negative_returns:
                downside_std = statistics.stdev(negative_returns) if len(negative_returns) > 1 else abs(negative_returns[0])
                metrics.sortino_ratio = (avg_return / downside_std) * math.sqrt(252) if downside_std > 0 else 0
            
            # Calmar Ratio
            annual_return = avg_return * 252
            metrics.calmar_ratio = annual_return / metrics.max_drawdown_pct if metrics.max_drawdown_pct > 0 else 0
        
        # Consecutive wins/losses
        current_streak = 0
        max_wins = 0
        max_losses = 0
        
        for trade in self.trades:
            if trade.pnl > 0:
                if current_streak > 0:
                    current_streak += 1
                else:
                    current_streak = 1
                max_wins = max(max_wins, current_streak)
            else:
                if current_streak < 0:
                    current_streak -= 1
                else:
                    current_streak = -1
                max_losses = max(max_losses, abs(current_streak))
        
        metrics.max_consecutive_wins = max_wins
        metrics.max_consecutive_losses = max_losses
        metrics.current_streak = current_streak
        
        # Trade duration
        durations = [t.duration_minutes for t in self.trades if t.duration_minutes > 0]
        metrics.avg_trade_duration_minutes = statistics.mean(durations) if durations else 0
        
        # Best/Worst trades
        pnls = [t.pnl for t in self.trades]
        metrics.best_trade = max(pnls) if pnls else 0
        metrics.worst_trade = min(pnls) if pnls else 0
        
        # Costs
        metrics.total_commission = sum(t.commission for t in self.trades)
        metrics.total_slippage = sum(t.slippage for t in self.trades)
        
        return metrics
    
    def validate(self) -> ValidationResult:
        """
        Validate paper trading performance against thresholds.
        
        Returns:
            ValidationResult with status, checks, and recommendations
        """
        metrics = self.calculate_metrics()
        
        passed_checks = []
        failed_checks = []
        warnings = []
        recommendations = []
        
        # Check minimum trades
        if metrics.total_trades >= self.thresholds.min_trades:
            passed_checks.append(f"[PASS] Minimum trades: {metrics.total_trades} >= {self.thresholds.min_trades}")
        else:
            failed_checks.append(f"[FAIL] Minimum trades: {metrics.total_trades} < {self.thresholds.min_trades}")
            recommendations.append(f"Complete at least {self.thresholds.min_trades - metrics.total_trades} more trades")
        
        # Check minimum days
        days_trading = (datetime.now() - self.session_start).days
        if days_trading >= self.thresholds.min_days:
            passed_checks.append(f"[PASS] Minimum days: {days_trading} >= {self.thresholds.min_days}")
        else:
            failed_checks.append(f"[FAIL] Minimum days: {days_trading} < {self.thresholds.min_days}")
            recommendations.append(f"Continue paper trading for {self.thresholds.min_days - days_trading} more days")
        
        # Check win rate
        if metrics.win_rate >= self.thresholds.min_win_rate:
            passed_checks.append(f"[PASS] Win rate: {metrics.win_rate:.1%} >= {self.thresholds.min_win_rate:.1%}")
        else:
            failed_checks.append(f"[FAIL] Win rate: {metrics.win_rate:.1%} < {self.thresholds.min_win_rate:.1%}")
            recommendations.append("Review entry criteria and signal quality")
        
        # Check profit factor
        if metrics.profit_factor >= self.thresholds.min_profit_factor:
            passed_checks.append(f"[PASS] Profit factor: {metrics.profit_factor:.2f} >= {self.thresholds.min_profit_factor:.2f}")
        else:
            failed_checks.append(f"[FAIL] Profit factor: {metrics.profit_factor:.2f} < {self.thresholds.min_profit_factor:.2f}")
            recommendations.append("Improve risk-reward ratio or cut losses faster")
        
        # Check max drawdown
        if metrics.max_drawdown_pct <= self.thresholds.max_drawdown:
            passed_checks.append(f"[PASS] Max drawdown: {metrics.max_drawdown_pct:.1%} <= {self.thresholds.max_drawdown:.1%}")
        else:
            failed_checks.append(f"[FAIL] Max drawdown: {metrics.max_drawdown_pct:.1%} > {self.thresholds.max_drawdown:.1%}")
            recommendations.append("Reduce position sizes or improve stop loss placement")
        
        # Check Sharpe ratio
        if metrics.sharpe_ratio >= self.thresholds.min_sharpe_ratio:
            passed_checks.append(f"[PASS] Sharpe ratio: {metrics.sharpe_ratio:.2f} >= {self.thresholds.min_sharpe_ratio:.2f}")
        else:
            warnings.append(f"[WARN] Sharpe ratio: {metrics.sharpe_ratio:.2f} < {self.thresholds.min_sharpe_ratio:.2f}")
            recommendations.append("Work on consistency - reduce return volatility")
        
        # Check consecutive losses
        if metrics.max_consecutive_losses <= self.thresholds.max_consecutive_losses:
            passed_checks.append(f"[PASS] Max consecutive losses: {metrics.max_consecutive_losses} <= {self.thresholds.max_consecutive_losses}")
        else:
            failed_checks.append(f"[FAIL] Max consecutive losses: {metrics.max_consecutive_losses} > {self.thresholds.max_consecutive_losses}")
            recommendations.append("Add filters to avoid trading during unfavorable conditions")
        
        # Check R:R ratio
        if metrics.avg_rr_ratio >= self.thresholds.min_avg_rr_ratio:
            passed_checks.append(f"[PASS] Avg R:R ratio: {metrics.avg_rr_ratio:.2f} >= {self.thresholds.min_avg_rr_ratio:.2f}")
        else:
            warnings.append(f"[WARN] Avg R:R ratio: {metrics.avg_rr_ratio:.2f} < {self.thresholds.min_avg_rr_ratio:.2f}")
            recommendations.append("Widen take profit or tighten stop loss")
        
        # Determine overall status
        if not failed_checks and metrics.total_trades >= self.thresholds.min_trades:
            status = ValidationStatus.PASSED
            ready_for_live = True
        elif metrics.total_trades < self.thresholds.min_trades:
            status = ValidationStatus.NEEDS_MORE_DATA
            ready_for_live = False
        else:
            status = ValidationStatus.FAILED
            ready_for_live = False
        
        return ValidationResult(
            status=status,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warnings=warnings,
            metrics=metrics,
            recommendations=recommendations,
            ready_for_live=ready_for_live
        )
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """Generate comprehensive validation report"""
        result = self.validate()
        metrics = result.metrics
        
        report = []
        report.append("=" * 80)
        report.append("PAPER TRADING VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Session Start: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Duration: {(datetime.now() - self.session_start).days} days")
        report.append("")
        
        # Status
        report.append("-" * 40)
        report.append("VALIDATION STATUS")
        report.append("-" * 40)
        status_marker = "[PASS]" if result.ready_for_live else "[FAIL]"
        report.append(f"Status: {status_marker} {result.status.value.upper()}")
        report.append(f"Ready for Live Trading: {'YES' if result.ready_for_live else 'NO'}")
        report.append("")
        
        # Capital
        report.append("-" * 40)
        report.append("CAPITAL")
        report.append("-" * 40)
        report.append(f"Initial Capital: ${self.initial_capital:,.2f}")
        report.append(f"Current Capital: ${self.current_capital:,.2f}")
        report.append(f"Peak Capital: ${self.peak_capital:,.2f}")
        report.append(f"Net P&L: ${metrics.net_profit:,.2f} ({metrics.net_profit/self.initial_capital:.1%})")
        report.append("")
        
        # Performance
        report.append("-" * 40)
        report.append("PERFORMANCE METRICS")
        report.append("-" * 40)
        report.append(f"Total Trades: {metrics.total_trades}")
        report.append(f"Winning Trades: {metrics.winning_trades}")
        report.append(f"Losing Trades: {metrics.losing_trades}")
        report.append(f"Win Rate: {metrics.win_rate:.1%}")
        report.append(f"Profit Factor: {metrics.profit_factor:.2f}")
        report.append(f"Average Win: ${metrics.avg_win:.2f}")
        report.append(f"Average Loss: ${metrics.avg_loss:.2f}")
        report.append(f"Average Trade: ${metrics.avg_trade:.2f}")
        report.append(f"Average R:R Ratio: {metrics.avg_rr_ratio:.2f}")
        report.append("")
        
        # Risk Metrics
        report.append("-" * 40)
        report.append("RISK METRICS")
        report.append("-" * 40)
        report.append(f"Max Drawdown: ${metrics.max_drawdown:.2f} ({metrics.max_drawdown_pct:.1%})")
        report.append(f"Current Drawdown: {metrics.current_drawdown:.1%}")
        report.append(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        report.append(f"Sortino Ratio: {metrics.sortino_ratio:.2f}")
        report.append(f"Calmar Ratio: {metrics.calmar_ratio:.2f}")
        report.append(f"Max Consecutive Wins: {metrics.max_consecutive_wins}")
        report.append(f"Max Consecutive Losses: {metrics.max_consecutive_losses}")
        report.append("")
        
        # Trade Statistics
        report.append("-" * 40)
        report.append("TRADE STATISTICS")
        report.append("-" * 40)
        report.append(f"Best Trade: ${metrics.best_trade:.2f}")
        report.append(f"Worst Trade: ${metrics.worst_trade:.2f}")
        report.append(f"Avg Trade Duration: {metrics.avg_trade_duration_minutes:.1f} minutes")
        report.append(f"Total Commission: ${metrics.total_commission:.2f}")
        report.append(f"Total Slippage: ${metrics.total_slippage:.2f}")
        report.append("")
        
        # Validation Checks
        report.append("-" * 40)
        report.append("VALIDATION CHECKS")
        report.append("-" * 40)
        for check in result.passed_checks:
            report.append(check)
        for check in result.failed_checks:
            report.append(check)
        for warning in result.warnings:
            report.append(warning)
        report.append("")
        
        # Recommendations
        if result.recommendations:
            report.append("-" * 40)
            report.append("RECOMMENDATIONS")
            report.append("-" * 40)
            for i, rec in enumerate(result.recommendations, 1):
                report.append(f"{i}. {rec}")
            report.append("")
        
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        # Save report
        if output_path is None:
            output_path = os.path.join(
                self.data_dir,
                f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        logger.info(f"Validation report saved to {output_path}")
        
        return report_text
    
    def save_state(self, filepath: Optional[str] = None) -> str:
        """Save validator state to file"""
        if filepath is None:
            filepath = os.path.join(self.data_dir, "validator_state.json")
        
        state = {
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'peak_capital': self.peak_capital,
            'session_start': self.session_start.isoformat(),
            'trades': [t.to_dict() for t in self.trades],
            'daily_pnl': self.daily_pnl,
            'equity_curve': [(t.isoformat(), v) for t, v in self.equity_curve],
            'thresholds': asdict(self.thresholds)
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"Validator state saved to {filepath}")
        return filepath
    
    def load_state(self, filepath: Optional[str] = None) -> bool:
        """Load validator state from file"""
        if filepath is None:
            filepath = os.path.join(self.data_dir, "validator_state.json")
        
        if not os.path.exists(filepath):
            logger.warning(f"State file not found: {filepath}")
            return False
        try:
        
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.initial_capital = state['initial_capital']
            self.current_capital = state['current_capital']
            self.peak_capital = state['peak_capital']
            self.session_start = datetime.fromisoformat(state['session_start'])
            
            self.trades = []
            for t in state['trades']:
                trade = Trade(
                    trade_id=t['trade_id'],
                    symbol=t['symbol'],
                    direction=t['direction'],
                    entry_time=datetime.fromisoformat(t['entry_time']) if t['entry_time'] else None,
                    entry_price=t['entry_price'],
                    exit_time=datetime.fromisoformat(t['exit_time']) if t['exit_time'] else None,
                    exit_price=t['exit_price'],
                    quantity=t['quantity'],
                    pnl=t['pnl'],
                    pnl_pct=t['pnl_pct'],
                    commission=t['commission'],
                    slippage=t['slippage'],
                    duration_minutes=t['duration_minutes'],
                    exit_reason=t['exit_reason']
                )
                self.trades.append(trade)
            
            self.daily_pnl = state['daily_pnl']
            self.equity_curve = [(datetime.fromisoformat(t), v) for t, v in state['equity_curve']]
            
            logger.info(f"Validator state loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return False


class LiveTradingGate:
    """
    Gate keeper for live trading.
    
    Ensures all validation requirements are met before allowing live trading.
    """
    
    def __init__(
        self,
        validator: PaperTradingValidator,
        config_path: str = "config/live_trading_config.yaml"
    ):
        self.validator = validator
        self.config_path = config_path
        self.approval_log: List[Dict] = []
    
    def check_readiness(self) -> Tuple[bool, List[str], List[str]]:
        """
        Check if system is ready for live trading.
        
        Returns:
            Tuple of (is_ready, passed_checks, failed_checks)
        """
        passed = []
        failed = []
        
        # Validate paper trading performance
        result = self.validator.validate()
        
        if result.ready_for_live:
            passed.append("Paper trading validation passed")
        else:
            failed.append(f"Paper trading validation failed: {result.status.value}")
            for check in result.failed_checks:
                failed.append(f"  - {check}")
        
        # Check configuration exists
        if os.path.exists(self.config_path):
            passed.append("Live trading configuration exists")
        else:
            failed.append("Live trading configuration not found")
        
        # Check broker connection (placeholder)
        # In real implementation, this would test actual broker connectivity
        passed.append("Broker connection check (simulated)")
        
        # Check emergency contacts configured
        # In real implementation, this would verify alert settings
        passed.append("Emergency contacts configured (simulated)")
        
        is_ready = len(failed) == 0
        
        return is_ready, passed, failed
    
    def request_approval(self, reason: str = "") -> Dict:
        """
        Request approval for live trading.
        
        Returns approval status and details.
        """
        is_ready, passed, failed = self.check_readiness()
        
        approval = {
            'timestamp': datetime.now().isoformat(),
            'is_ready': is_ready,
            'passed_checks': passed,
            'failed_checks': failed,
            'reason': reason,
            'metrics': self.validator.calculate_metrics().to_dict(),
            'approved': is_ready,
            'approval_code': f"LIVE_{datetime.now().strftime('%Y%m%d%H%M%S')}" if is_ready else None
        }
        
        self.approval_log.append(approval)
        
        return approval
    
    def get_capital_stage(self) -> Dict:
        """
        Determine appropriate capital stage based on performance.
        
        Returns stage information and recommended capital.
        """
        metrics = self.validator.calculate_metrics()
        
        stages = [
            {
                'name': 'Stage 1 - Validation',
                'capital': 100.0,
                'min_trades': 20,
                'min_win_rate': 0.50,
                'max_drawdown': 0.10
            },
            {
                'name': 'Stage 2 - Confirmation',
                'capital': 250.0,
                'min_trades': 50,
                'min_win_rate': 0.48,
                'max_drawdown': 0.12
            },
            {
                'name': 'Stage 3 - Scaling',
                'capital': 500.0,
                'min_trades': 100,
                'min_win_rate': 0.45,
                'max_drawdown': 0.15
            },
            {
                'name': 'Stage 4 - Full',
                'capital': 1000.0,
                'min_trades': 200,
                'min_win_rate': 0.45,
                'max_drawdown': 0.15
            }
        ]
        
        current_stage = None
        for stage in stages:
            if (metrics.total_trades >= stage['min_trades'] and
                metrics.win_rate >= stage['min_win_rate'] and
                metrics.max_drawdown_pct <= stage['max_drawdown']):
                current_stage = stage
        
        if current_stage is None:
            current_stage = stages[0]
            current_stage['qualified'] = False
        else:
            current_stage['qualified'] = True
        
        return current_stage


# Convenience functions
def create_paper_validator(
    initial_capital: float = 10000.0,
    min_trades: int = 50,
    min_days: int = 7
) -> PaperTradingValidator:
    """Create a paper trading validator with custom settings"""
    thresholds = ValidationThresholds(
        min_trades=min_trades,
        min_days=min_days
    )
    return PaperTradingValidator(
        initial_capital=initial_capital,
        thresholds=thresholds
    )


def quick_validate(validator: PaperTradingValidator) -> bool:
    """Quick validation check - returns True if ready for live"""
    result = validator.validate()
    return result.ready_for_live
