from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
from pathlib import Path
from datetime import timedelta
from typing import Dict, List
"""Reporting engine – schedules and generates performance reports.

Phase-1 capabilities:
    • Daily, weekly and monthly stub reports.
    • Real-time 30-minute check-in (placeholder for emotional state & open trades).

Future improvements: attach trade statistics, equity curves, and advanced analytics.
"""

import datetime as _dt
import pathlib
import statistics
from typing import Any, List, Sequence

import schedule  # type: ignore
from loguru import logger

from trading_bot.config import get


class Reporter:  # noqa: B024 – simple orchestrator
    """Schedules reporting jobs using the `schedule` library."""

    def __init__(self, *, log_dir: str | pathlib.Path | None = None) -> None:
        log_dir = pathlib.Path(log_dir or "reports").expanduser()
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir = log_dir

        # Schedule jobs based on config
        self._setup_jobs()

    # ------------------------------------------------------------------
    # Scheduling helpers
    # ------------------------------------------------------------------

    def _setup_jobs(self) -> None:  # noqa: D401
        # 30-minute check-in
        schedule.every(30).minutes.do(self.real_time_check_in)

        # Daily summary
        daily_time = str(get("reporting.report_times_utc.daily", "23:59"))
        schedule.every().day.at(daily_time).do(self.daily_report)

        # Weekly report
        weekly_time = str(get("reporting.report_times_utc.weekly", "Fri 23:59"))
        day_name, at_time = weekly_time.split(maxsplit=1)
        getattr(schedule.every(), day_name.lower()).at(at_time).do(self.weekly_report)

        # Monthly report – first day following last day (simplified)
        monthly_time = str(get("reporting.report_times_utc.monthly", "last day 23:59"))
        *_, at_time = monthly_time.split()
        schedule.every().day.at(at_time).do(self._monthly_wrapper)

        logger.info("Reporting jobs scheduled.")

    # ------------------------------------------------------------------
    # Report generators (stubs)
    # ------------------------------------------------------------------

    def real_time_check_in(self) -> None:  # noqa: D401 (imperative)
        now = _dt.datetime.utcnow()
        try:
            # Get live trade stats
            open_trades = self._get_open_trades()
            pnl = self._calculate_current_pnl()
            win_rate = self._calculate_win_rate()
            
            logger.info(f"[Check-in] {now.isoformat()} – Open trades: {len(open_trades)}, P&L: {pnl:.2f}, Win rate: {win_rate:.1%}")
        except Exception as e:
            logger.error(f"Check-in failed: {e}")
            logger.info("[Check-in] {} – placeholder for live trade stats.", now.isoformat())

    def daily_report(self) -> None:  # noqa: D401
        now = _dt.datetime.utcnow()
        file = self.log_dir / f"daily_{now:%Y%m%d}.txt"
        with file.open("w", encoding="utf-8") as fh:
            fh.write(f"Daily Report – {now:%Y-%m-%d UTC}\n")
            trades = self._get_daily_trades(now.date())
            fh.write(f"Total Trades: {len(trades)}\n")
            if trades:
                winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
                losing_trades = [t for t in trades if t.get("pnl", 0) < 0]
                fh.write(f"Winning Trades: {len(winning_trades)}\n")
                fh.write(f"Losing Trades: {len(losing_trades)}\n")
                fh.write(f"Win Rate: {len(winning_trades)/len(trades)*100:.1f}%\n\n")
                total_pnl = sum(t.get("pnl", 0) for t in trades)
                fh.write(f"Total P&L: {total_pnl:.2f}\n")
                fh.write(f"Average Trade: {total_pnl/len(trades):.2f}\n")
                fh.write(f"Best Trade: {max(t.get('pnl', 0) for t in trades):.2f}\n")
                fh.write(f"Worst Trade: {min(t.get('pnl', 0) for t in trades):.2f}\n")
            else:
                fh.write("No trades today.\n")
        logger.success("Daily report saved: {}", file)

    def weekly_report(self) -> None:  # noqa: D401
        now = _dt.datetime.utcnow()
        week = now.isocalendar().week
        file = self.log_dir / f"weekly_{now:%Y}_W{week:02d}.txt"
        try:
            with file.open("w", encoding="utf-8") as fh:
                fh.write(f"Weekly Report – Year {now:%Y} Week {week}\n")
                fh.write("="*50 + "\n\n")
                
                # Compile weekly stats
                week_start = now - _dt.timedelta(days=now.weekday())
                trades = self._get_trades_in_range(week_start.date(), now.date())
                
                fh.write(f"Total Trades: {len(trades)}\n")
                
                if trades:
                    winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
                    losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
                    
                    fh.write(f"Winning Trades: {len(winning_trades)}\n")
                    fh.write(f"Losing Trades: {len(losing_trades)}\n")
                    fh.write(f"Win Rate: {len(winning_trades)/len(trades)*100:.1f}%\n\n")
                    
                    total_pnl = sum(t.get('pnl', 0) for t in trades)
                    fh.write(f"Total P&L: {total_pnl:.2f}\n")
                    fh.write(f"Average Trade: {total_pnl/len(trades):.2f}\n")
                    fh.write(f"Best Trade: {max(t.get('pnl', 0) for t in trades):.2f}\n")
                    fh.write(f"Worst Trade: {min(t.get('pnl', 0) for t in trades):.2f}\n\n")
                    
                    # Group by symbol
                    symbols = {}
                    for trade in trades:
                        sym = trade.get('symbol', 'N/A')
                        if sym not in symbols:
                            symbols[sym] = []
                        symbols[sym].append(trade)
                    
                    fh.write("Performance by Symbol:\n")
                    for sym, sym_trades in symbols.items():
                        sym_pnl = sum(t.get('pnl', 0) for t in sym_trades)
                        fh.write(f"  {sym}: {len(sym_trades)} trades, P&L: {sym_pnl:.2f}\n")
                else:
                    fh.write("No trades this week.\n")
                    
        except Exception as e:
            logger.error(f"Weekly report generation failed: {e}")
            with file.open("w", encoding="utf-8") as fh:
                fh.write(f"Weekly Report – Year {now:%Y} Week {week}\n")
                fh.write(f"Error generating report: {e}\n")
        
        logger.success("Weekly report saved: {}", file)

    def _monthly_wrapper(self) -> None:  # noqa: D401
        today = _dt.date.today()
        last_day = (today.replace(day=28) + _dt.timedelta(days=4)).replace(day=1) - _dt.timedelta(days=1)
        if today != last_day:
            return  # run only on last day
        self.monthly_report()

    def monthly_report(self) -> None:  # noqa: D401
        now = _dt.datetime.utcnow()
        file = self.log_dir / f"monthly_{now:%Y%m}.txt"
        try:
            with file.open("w", encoding="utf-8") as fh:
                fh.write(f"Monthly Report – {now:%B %Y}\n")
                fh.write("="*50 + "\n\n")
                
                # Compile monthly stats
                month_start = now.replace(day=1)
                month_end = (month_start + _dt.timedelta(days=32)).replace(day=1) - _dt.timedelta(days=1)
                trades = self._get_trades_in_range(month_start.date(), month_end.date())
                
                fh.write(f"Total Trades: {len(trades)}\n")
                
                if trades:
                    winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
                    losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
                    
                    fh.write(f"Winning Trades: {len(winning_trades)}\n")
                    fh.write(f"Losing Trades: {len(losing_trades)}\n")
                    fh.write(f"Win Rate: {len(winning_trades)/len(trades)*100:.1f}%\n\n")
                    
                    total_pnl = sum(t.get('pnl', 0) for t in trades)
                    fh.write(f"Total P&L: {total_pnl:.2f}\n")
                    fh.write(f"Average Trade: {total_pnl/len(trades):.2f}\n")
                    fh.write(f"Best Trade: {max(t.get('pnl', 0) for t in trades):.2f}\n")
                    fh.write(f"Worst Trade: {min(t.get('pnl', 0) for t in trades):.2f}\n\n")
                    
                    # Profit factor
                    total_wins = sum(t.get('pnl', 0) for t in winning_trades)
                    total_losses = abs(sum(t.get('pnl', 0) for t in losing_trades))
                    profit_factor = total_wins / total_losses if total_losses > 0 else 0
                    fh.write(f"Profit Factor: {profit_factor:.2f}\n\n")
                    
                    # Group by symbol
                    symbols = {}
                    for trade in trades:
                        sym = trade.get('symbol', 'N/A')
                        if sym not in symbols:
                            symbols[sym] = []
                        symbols[sym].append(trade)
                    
                    fh.write("Performance by Symbol:\n")
                    for sym, sym_trades in symbols.items():
                        sym_pnl = sum(t.get('pnl', 0) for t in sym_trades)
                        sym_wins = len([t for t in sym_trades if t.get('pnl', 0) > 0])
                        fh.write(f"  {sym}: {len(sym_trades)} trades, {sym_wins} wins, P&L: {sym_pnl:.2f}\n")
                else:
                    fh.write("No trades this month.\n")
                    
        except Exception as e:
            logger.error(f"Monthly report generation failed: {e}")
            with file.open("w", encoding="utf-8") as fh:
                fh.write(f"Monthly Report – {now:%B %Y}\n")
                fh.write(f"Error generating report: {e}\n")
        
        logger.success("Monthly report saved: {}", file)
    
    # Helper methods for data retrieval
    def _get_open_trades(self) -> List[Dict]:
        """Get currently open trades."""
        try:
            from trading_bot.position_manager import PositionManager
            if hasattr(self, 'position_manager'):
                return self.position_manager.get_all_positions()
        except Exception as e:
            logger.debug(f"Could not get open trades: {e}")
        return []
    
    def _calculate_current_pnl(self) -> float:
        """Calculate current unrealized P&L."""
        try:
            trades = self._get_open_trades()
            return sum(t.pnl if hasattr(t, 'pnl') else t.get('pnl', 0) for t in trades)
        except Exception as e:
            logger.debug(f"Could not calculate P&L: {e}")
        return 0.0
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate from recent trades."""
        try:
            from trading_bot.trade_journal import TradeJournal
            if hasattr(self, 'trade_journal'):
                recent_trades = self.trade_journal.get_recent_trades(limit=20)
                if recent_trades:
                    wins = len([t for t in recent_trades if t.get('pnl', 0) > 0])
                    return wins / len(recent_trades)
        except Exception as e:
            logger.debug(f"Could not calculate win rate: {e}")
        return 0.0
    
    def _get_daily_trades(self, date) -> List[Dict]:
        """Get trades for a specific date."""
        try:
            if hasattr(self, 'trade_journal'):
                return self.trade_journal.get_trades_by_date(date)
        except Exception as e:
            logger.debug(f"Could not get daily trades: {e}")
        return []
    
    def _get_trades_in_range(self, start_date, end_date) -> List[Dict]:
        """Get trades within a date range."""
        try:
            if hasattr(self, 'trade_journal'):
                return self.trade_journal.get_trades_in_range(start_date, end_date)
        except Exception as e:
            logger.debug(f"Could not get trades in range: {e}")
        return []

    # ------------------------------------------------------------------
    # Driver
    # ------------------------------------------------------------------

    def run_pending(self) -> None:  # noqa: D401
        """Run due scheduled jobs. Call this in your main event loop."""
        schedule.run_pending()
