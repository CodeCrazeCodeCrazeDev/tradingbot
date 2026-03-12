"""
Discipline Engine (#2–15)
==========================
Enforces strict trading discipline. The AI cannot override these rules.

Rules enforced:
    #2  Daily Loss Circuit Breaker    — Stop trading if daily loss > 3%
    #3  Weekly Loss Limit             — Reduce size 50% if weekly loss > 5%
    #4  Consecutive Loss Cooldown     — Pause 30 min after 3 consecutive losses
    #5  Revenge Trade Detector        — Block trades after loss with increased size
    #6  Overtrading Guard             — Cap max trades per hour/day
    #7  Session-Aware Trading         — Only trade during liquid sessions
    #8  News Blackout Periods         — Pause around major economic releases
    #9  Spread Spike Filter           — Reject when spread > 2x normal
    #10 Slippage Budget               — Pause if cumulative slippage exceeds budget
    #11 Position Concentration Limit  — No single position > 25% of portfolio
    #12 Correlated Pair Exposure Cap  — Correlated pairs capped at 150%
    #13 Drawdown-Adaptive Sizing      — Reduce size as drawdown increases
    #14 Profit Lock Mechanism         — After daily target, reduce size 75%
    #15 Weekend Flat Rule             — Close all before Friday close
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TradeBlockReason(Enum):
    NONE = "none"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    WEEKLY_LOSS_LIMIT = "weekly_loss_limit"
    CONSECUTIVE_LOSSES = "consecutive_loss_cooldown"
    REVENGE_TRADE = "revenge_trade_detected"
    OVERTRADING = "overtrading_limit"
    OUTSIDE_SESSION = "outside_trading_session"
    NEWS_BLACKOUT = "news_blackout"
    SPREAD_SPIKE = "spread_too_wide"
    SLIPPAGE_BUDGET = "slippage_budget_exceeded"
    POSITION_CONCENTRATION = "position_too_concentrated"
    CORRELATED_EXPOSURE = "correlated_exposure_too_high"
    WEEKEND_FLAT = "weekend_flat_rule"


@dataclass
class DisciplineVerdict:
    """Result of discipline check — trade is either allowed or blocked."""
    allowed: bool
    block_reason: TradeBlockReason = TradeBlockReason.NONE
    message: str = ""
    size_multiplier: float = 1.0  # 1.0 = full size, 0.5 = half, etc.
    adjustments: Dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.allowed


@dataclass
class TradeRecord:
    """Minimal record of a completed trade for discipline tracking."""
    timestamp: datetime
    symbol: str
    direction: str
    lots: float
    pnl: float
    notional_value: float
    slippage_bps: float = 0.0


class DisciplineEngine:
    """
    The iron discipline of the trading bot. Cannot be overridden by the AI.
    
    Usage:
        discipline = DisciplineEngine(config)
        
        # Before every trade:
        verdict = discipline.check_trade(symbol, direction, lots, notional, spread, ...)
        if not verdict.allowed:
            logger.warning(f"Trade BLOCKED: {verdict.message}")
            return
        
        # Adjust size if needed:
        actual_lots = lots * verdict.size_multiplier
        
        # After trade completes:
        discipline.record_trade(TradeRecord(...))
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = config or {}

        # #2 Daily Loss Circuit Breaker
        self._daily_loss_limit_pct = cfg.get("daily_loss_limit_pct", 3.0)
        self._daily_pnl = 0.0
        self._daily_reset_date = datetime.now().date()

        # #3 Weekly Loss Limit
        self._weekly_loss_limit_pct = cfg.get("weekly_loss_limit_pct", 5.0)
        self._weekly_pnl = 0.0
        self._weekly_reset_date = self._get_week_start()

        # #4 Consecutive Loss Cooldown
        self._max_consecutive_losses = cfg.get("max_consecutive_losses", 3)
        self._cooldown_minutes = cfg.get("cooldown_minutes", 30)
        self._consecutive_losses = 0
        self._cooldown_until: Optional[datetime] = None

        # #5 Revenge Trade Detector
        self._last_trade_pnl: Optional[float] = None
        self._last_trade_lots: Optional[float] = None
        self._last_trade_time: Optional[datetime] = None
        self._revenge_window_seconds = cfg.get("revenge_window_seconds", 120)

        # #6 Overtrading Guard
        self._max_trades_per_hour = cfg.get("max_trades_per_hour", 10)
        self._max_trades_per_day = cfg.get("max_trades_per_day", 50)
        self._trade_timestamps: deque = deque(maxlen=1000)

        # #7 Session-Aware Trading
        self._session_only = cfg.get("session_only", True)
        self._sessions = cfg.get("sessions", {
            "london_open": 8, "london_close": 16,
            "ny_open": 13, "ny_close": 21,
        })

        # #8 News Blackout
        self._news_blackout_before_min = cfg.get("news_blackout_before_min", 15)
        self._news_blackout_after_min = cfg.get("news_blackout_after_min", 5)
        self._upcoming_news: List[datetime] = []

        # #9 Spread Spike Filter
        self._spread_multiplier_max = cfg.get("spread_multiplier_max", 2.0)
        self._normal_spreads: Dict[str, float] = {}

        # #10 Slippage Budget
        self._daily_slippage_budget_bps = cfg.get("daily_slippage_budget_bps", 50.0)
        self._daily_slippage_used = 0.0

        # #11 Position Concentration
        self._max_position_pct = cfg.get("max_position_pct", 25.0)

        # #12 Correlated Pair Exposure
        self._max_correlated_exposure_pct = cfg.get("max_correlated_exposure_pct", 150.0)
        self._correlations: Dict[Tuple[str, str], float] = {}

        # #13 Drawdown-Adaptive Sizing
        self._drawdown_adaptive = cfg.get("drawdown_adaptive", True)
        self._current_drawdown_pct = 0.0
        self._peak_equity = cfg.get("initial_equity", 100000.0)
        self._current_equity = self._peak_equity

        # #14 Profit Lock
        self._daily_profit_target_pct = cfg.get("daily_profit_target_pct", 2.0)
        self._profit_lock_active = False

        # #15 Weekend Flat
        self._weekend_flat = cfg.get("weekend_flat", True)
        self._friday_close_hour = cfg.get("friday_close_hour", 20)  # UTC

        # Stats
        self._total_checks = 0
        self._total_blocked = 0
        self._block_reasons: Dict[str, int] = {}

        logger.info(
            f"[DISCIPLINE] Initialized: daily_loss={self._daily_loss_limit_pct}%, "
            f"weekly_loss={self._weekly_loss_limit_pct}%, "
            f"max_consec_losses={self._max_consecutive_losses}, "
            f"max_trades/hr={self._max_trades_per_hour}, "
            f"max_trades/day={self._max_trades_per_day}"
        )

    # ------------------------------------------------------------------
    # Main Check — Run before EVERY trade
    # ------------------------------------------------------------------

    def check_trade(
        self,
        symbol: str,
        direction: str,
        lots: float,
        notional_value: float,
        current_spread: float = 0.0,
        portfolio_value: float = 0.0,
        open_positions: Optional[Dict[str, float]] = None,
    ) -> DisciplineVerdict:
        """
        Run ALL discipline checks. Returns verdict with allowed/blocked status.
        If allowed, may include size_multiplier < 1.0 for reduced sizing.
        """
        self._total_checks += 1
        self._reset_daily_if_needed()
        self._reset_weekly_if_needed()
        now = datetime.now()

        # #2 Daily Loss Circuit Breaker
        if self._daily_pnl < 0:
            daily_loss_pct = abs(self._daily_pnl) / max(self._peak_equity, 1) * 100
            if daily_loss_pct >= self._daily_loss_limit_pct:
                return self._block(TradeBlockReason.DAILY_LOSS_LIMIT,
                    f"Daily loss {daily_loss_pct:.1f}% exceeds limit {self._daily_loss_limit_pct}%. STOP TRADING.")

        # #3 Weekly Loss Limit (reduce size, don't fully block)
        size_mult = 1.0
        if self._weekly_pnl < 0:
            weekly_loss_pct = abs(self._weekly_pnl) / max(self._peak_equity, 1) * 100
            if weekly_loss_pct >= self._weekly_loss_limit_pct:
                size_mult = 0.5
                logger.info(f"[DISCIPLINE] Weekly loss {weekly_loss_pct:.1f}% — reducing size to 50%")

        # #4 Consecutive Loss Cooldown
        if self._cooldown_until and now < self._cooldown_until:
            remaining = (self._cooldown_until - now).total_seconds() / 60
            return self._block(TradeBlockReason.CONSECUTIVE_LOSSES,
                f"{self._consecutive_losses} consecutive losses. Cooldown: {remaining:.0f} min remaining.")

        # #5 Revenge Trade Detection
        if self._last_trade_pnl is not None and self._last_trade_pnl < 0:
            if self._last_trade_time and (now - self._last_trade_time).total_seconds() < self._revenge_window_seconds:
                if self._last_trade_lots and lots > self._last_trade_lots * 1.2:
                    return self._block(TradeBlockReason.REVENGE_TRADE,
                        f"Revenge trade detected: lost on last trade, now trying {lots:.2f} lots "
                        f"(>{self._last_trade_lots:.2f}×1.2) within {self._revenge_window_seconds}s.")

        # #6 Overtrading Guard
        recent_hour = sum(1 for t in self._trade_timestamps if (now - t).total_seconds() < 3600)
        if recent_hour >= self._max_trades_per_hour:
            return self._block(TradeBlockReason.OVERTRADING,
                f"Hourly trade limit reached: {recent_hour}/{self._max_trades_per_hour}")

        today_count = sum(1 for t in self._trade_timestamps if t.date() == now.date())
        if today_count >= self._max_trades_per_day:
            return self._block(TradeBlockReason.OVERTRADING,
                f"Daily trade limit reached: {today_count}/{self._max_trades_per_day}")

        # #7 Session-Aware Trading
        if self._session_only:
            hour = now.hour
            in_london = self._sessions["london_open"] <= hour < self._sessions["london_close"]
            in_ny = self._sessions["ny_open"] <= hour < self._sessions["ny_close"]
            if not (in_london or in_ny):
                return self._block(TradeBlockReason.OUTSIDE_SESSION,
                    f"Outside trading sessions (London {self._sessions['london_open']}-{self._sessions['london_close']}, "
                    f"NY {self._sessions['ny_open']}-{self._sessions['ny_close']}). Current hour: {hour}")

        # #8 News Blackout
        for news_time in self._upcoming_news:
            before = news_time - timedelta(minutes=self._news_blackout_before_min)
            after = news_time + timedelta(minutes=self._news_blackout_after_min)
            if before <= now <= after:
                return self._block(TradeBlockReason.NEWS_BLACKOUT,
                    f"News blackout: event at {news_time.strftime('%H:%M')}. "
                    f"Blackout: {self._news_blackout_before_min}min before, {self._news_blackout_after_min}min after.")

        # #9 Spread Spike Filter
        if current_spread > 0 and symbol in self._normal_spreads:
            normal = self._normal_spreads[symbol]
            if normal > 0 and current_spread > normal * self._spread_multiplier_max:
                return self._block(TradeBlockReason.SPREAD_SPIKE,
                    f"Spread spike: {current_spread:.1f} > {normal:.1f} × {self._spread_multiplier_max} "
                    f"(normal avg). Wait for spread to normalize.")

        # #10 Slippage Budget
        if self._daily_slippage_used >= self._daily_slippage_budget_bps:
            return self._block(TradeBlockReason.SLIPPAGE_BUDGET,
                f"Daily slippage budget exhausted: {self._daily_slippage_used:.1f}/{self._daily_slippage_budget_bps:.1f} bps")

        # #11 Position Concentration
        if portfolio_value > 0 and notional_value > 0:
            concentration = (notional_value / portfolio_value) * 100
            if concentration > self._max_position_pct:
                return self._block(TradeBlockReason.POSITION_CONCENTRATION,
                    f"Position too concentrated: {concentration:.1f}% > {self._max_position_pct}% of portfolio")

        # #12 Correlated Pair Exposure
        if open_positions and portfolio_value > 0:
            total_correlated = notional_value
            for open_sym, open_notional in open_positions.items():
                pair = tuple(sorted([symbol, open_sym]))
                corr = self._correlations.get(pair, 0.0)
                if abs(corr) > 0.7:
                    total_correlated += abs(open_notional)
            corr_pct = (total_correlated / portfolio_value) * 100
            if corr_pct > self._max_correlated_exposure_pct:
                return self._block(TradeBlockReason.CORRELATED_EXPOSURE,
                    f"Correlated exposure {corr_pct:.1f}% > {self._max_correlated_exposure_pct}% limit")

        # #13 Drawdown-Adaptive Sizing
        if self._drawdown_adaptive and self._current_drawdown_pct > 5.0:
            dd_factor = max(0.25, 1.0 - (self._current_drawdown_pct - 5.0) / 20.0)
            size_mult = min(size_mult, dd_factor)
            logger.info(f"[DISCIPLINE] Drawdown {self._current_drawdown_pct:.1f}% — size factor: {dd_factor:.2f}")

        # #14 Profit Lock
        if self._profit_lock_active:
            size_mult = min(size_mult, 0.25)
            logger.info("[DISCIPLINE] Profit lock active — size reduced to 25%")

        # #15 Weekend Flat Rule
        if self._weekend_flat and now.weekday() == 4 and now.hour >= self._friday_close_hour:
            return self._block(TradeBlockReason.WEEKEND_FLAT,
                f"Weekend flat rule: no new trades after Friday {self._friday_close_hour}:00 UTC")

        return DisciplineVerdict(
            allowed=True,
            size_multiplier=size_mult,
            message="Trade approved by discipline engine",
            adjustments={"size_multiplier": size_mult},
        )

    # ------------------------------------------------------------------
    # Record Trade — Call after EVERY trade completes
    # ------------------------------------------------------------------

    def record_trade(self, trade: TradeRecord) -> None:
        """Record a completed trade for discipline tracking."""
        now = datetime.now()
        self._trade_timestamps.append(now)

        # Update P&L
        self._daily_pnl += trade.pnl
        self._weekly_pnl += trade.pnl
        self._current_equity += trade.pnl
        if self._current_equity > self._peak_equity:
            self._peak_equity = self._current_equity
        self._current_drawdown_pct = max(0, (self._peak_equity - self._current_equity) / self._peak_equity * 100)

        # Update slippage
        self._daily_slippage_used += trade.slippage_bps

        # Track consecutive losses
        if trade.pnl < 0:
            self._consecutive_losses += 1
            if self._consecutive_losses >= self._max_consecutive_losses:
                self._cooldown_until = now + timedelta(minutes=self._cooldown_minutes)
                logger.warning(
                    f"[DISCIPLINE] ⚠️ {self._consecutive_losses} consecutive losses! "
                    f"Cooldown until {self._cooldown_until.strftime('%H:%M:%S')}"
                )
        else:
            self._consecutive_losses = 0
            self._cooldown_until = None

        # Track revenge trade data
        self._last_trade_pnl = trade.pnl
        self._last_trade_lots = trade.lots
        self._last_trade_time = now

        # Update normal spread
        # (would need spread data from trade, simplified here)

        # Check profit lock
        if self._daily_pnl > 0:
            daily_profit_pct = self._daily_pnl / max(self._peak_equity, 1) * 100
            if daily_profit_pct >= self._daily_profit_target_pct and not self._profit_lock_active:
                self._profit_lock_active = True
                logger.info(
                    f"[DISCIPLINE] 🔒 PROFIT LOCK activated! "
                    f"Daily profit {daily_profit_pct:.1f}% >= {self._daily_profit_target_pct}% target. "
                    f"Size reduced to 25%."
                )

        logger.debug(
            f"[DISCIPLINE] Trade recorded: {trade.symbol} {trade.direction} "
            f"P&L={trade.pnl:+.2f}, Daily={self._daily_pnl:+.2f}, "
            f"Consec losses={self._consecutive_losses}, DD={self._current_drawdown_pct:.1f}%"
        )

    # ------------------------------------------------------------------
    # Configuration Updates
    # ------------------------------------------------------------------

    def update_normal_spread(self, symbol: str, spread: float) -> None:
        self._normal_spreads[symbol] = spread

    def update_correlations(self, correlations: Dict[Tuple[str, str], float]) -> None:
        self._correlations.update(correlations)

    def add_news_event(self, event_time: datetime) -> None:
        self._upcoming_news.append(event_time)
        self._upcoming_news = [t for t in self._upcoming_news if t > datetime.now() - timedelta(hours=1)]

    def update_equity(self, equity: float) -> None:
        self._current_equity = equity
        if equity > self._peak_equity:
            self._peak_equity = equity
        self._current_drawdown_pct = max(0, (self._peak_equity - equity) / self._peak_equity * 100)

    # ------------------------------------------------------------------
    # Stats & Status
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        return {
            "total_checks": self._total_checks,
            "total_blocked": self._total_blocked,
            "block_reasons": dict(self._block_reasons),
            "daily_pnl": self._daily_pnl,
            "weekly_pnl": self._weekly_pnl,
            "consecutive_losses": self._consecutive_losses,
            "cooldown_active": self._cooldown_until is not None and datetime.now() < self._cooldown_until,
            "profit_lock_active": self._profit_lock_active,
            "drawdown_pct": self._current_drawdown_pct,
            "slippage_used_bps": self._daily_slippage_used,
            "trades_today": sum(1 for t in self._trade_timestamps if t.date() == datetime.now().date()),
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _block(self, reason: TradeBlockReason, message: str) -> DisciplineVerdict:
        self._total_blocked += 1
        key = reason.value
        self._block_reasons[key] = self._block_reasons.get(key, 0) + 1
        logger.warning(f"[DISCIPLINE] 🚫 BLOCKED: {message}")
        return DisciplineVerdict(allowed=False, block_reason=reason, message=message)

    def _reset_daily_if_needed(self) -> None:
        today = datetime.now().date()
        if today != self._daily_reset_date:
            logger.info(f"[DISCIPLINE] Daily reset. Yesterday P&L: {self._daily_pnl:+.2f}")
            self._daily_pnl = 0.0
            self._daily_slippage_used = 0.0
            self._profit_lock_active = False
            self._daily_reset_date = today

    def _reset_weekly_if_needed(self) -> None:
        week_start = self._get_week_start()
        if week_start != self._weekly_reset_date:
            logger.info(f"[DISCIPLINE] Weekly reset. Last week P&L: {self._weekly_pnl:+.2f}")
            self._weekly_pnl = 0.0
            self._weekly_reset_date = week_start

    @staticmethod
    def _get_week_start() -> datetime:
        now = datetime.now()
        return (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
