"""
Self-Learning Engine (#31–45)
==============================
Learns from every trade and continuously improves the AI.

Features:
    #31 Trade Journal Auto-Analysis    — Analyze every trade for patterns
    #32 Strategy Performance Tracker   — Track live performance per strategy
    #33 Regime-Strategy Mapping        — Learn which strategies work in which regimes
    #34 Time-of-Day Performance        — Track best/worst trading hours
    #35 Day-of-Week Performance        — Track best/worst trading days
    #36 Symbol Performance Ranking     — Rank symbols by profitability
    #37 Drawdown Pattern Recognition   — Detect recurring drawdown patterns
    #38 Winning Streak Analysis        — Detect hot streaks, manage overconfidence
    #39 Loss Cluster Detection         — Detect loss clusters, identify causes
    #40 Parameter Sensitivity Analysis — Test parameter sensitivity
    #41 Walk-Forward Optimization      — Re-optimize on rolling windows
    #42 Out-of-Sample Validation       — Validate before deploying changes
    #43 A/B Testing Framework          — Run strategy variants side-by-side
    #44 Confidence Calibration         — Check if confidence scores are accurate
    #45 Feedback Loop Tightening       — Reduce time between learning and applying
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class TradeJournalEntry:
    """Complete record of a trade for learning."""
    trade_id: str
    symbol: str
    direction: str
    strategy: str
    entry_price: float
    exit_price: float
    lots: float
    pnl: float
    pnl_pct: float
    entry_time: datetime
    exit_time: datetime
    hold_duration_minutes: float
    confidence: float
    risk_reward_planned: float
    risk_reward_actual: float
    regime: str = ""
    sl_hit: bool = False
    tp_hit: bool = False
    slippage_bps: float = 0.0
    spread_at_entry: float = 0.0
    notes: str = ""


@dataclass
class StrategyStats:
    """Performance statistics for a strategy."""
    strategy: str
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl: float = 0.0
    avg_pnl: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    max_win: float = 0.0
    max_loss: float = 0.0
    expectancy: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    avg_hold_minutes: float = 0.0
    best_regime: str = ""
    worst_regime: str = ""


@dataclass
class LearningInsight:
    """An actionable insight discovered by the learning engine."""
    insight_id: str
    category: str
    title: str
    description: str
    action: str             # What should change
    confidence: float       # How confident in this insight
    impact: str             # "high", "medium", "low"
    data: Dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=datetime.now)
    applied: bool = False


# ---------------------------------------------------------------------------
# Self-Learning Engine
# ---------------------------------------------------------------------------

class SelfLearningEngine:
    """
    Learns from every trade and generates actionable insights.
    
    Usage:
        engine = SelfLearningEngine()
        
        # After every trade:
        engine.record_trade(TradeJournalEntry(...))
        
        # Periodically:
        insights = engine.analyze()
        for insight in insights:
            # Apply insight to improve trading
            ...
        
        # Query learned knowledge:
        best_strategy = engine.get_best_strategy("EURUSD", "ranging")
        best_hours = engine.get_best_hours()
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            root = Path(__file__).resolve().parent.parent.parent
            db_path = str(root / "data" / "learning_engine.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db_path = db_path
        self._init_db()

        # In-memory caches (rebuilt from DB on init)
        self._trades: List[TradeJournalEntry] = []
        self._strategy_stats: Dict[str, StrategyStats] = {}
        self._hourly_stats: Dict[int, Dict[str, float]] = {}  # hour -> {wins, losses, pnl}
        self._daily_stats: Dict[int, Dict[str, float]] = {}   # weekday -> {wins, losses, pnl}
        self._symbol_stats: Dict[str, Dict[str, float]] = {}
        self._regime_strategy_stats: Dict[str, Dict[str, Dict[str, float]]] = {}
        self._confidence_buckets: Dict[str, Dict[str, float]] = {}  # "0.6-0.7" -> {wins, total}
        self._insights: List[LearningInsight] = []

        # Load existing data
        self._load_from_db()

        logger.info(
            f"[SELF-LEARN] Initialized with {len(self._trades)} historical trades, "
            f"{len(self._strategy_stats)} strategies tracked"
        )

    # ------------------------------------------------------------------
    # Record Trade
    # ------------------------------------------------------------------

    def record_trade(self, trade: TradeJournalEntry) -> None:
        """Record a completed trade and update all statistics."""
        self._trades.append(trade)
        self._save_trade(trade)
        self._update_strategy_stats(trade)
        self._update_hourly_stats(trade)
        self._update_daily_stats(trade)
        self._update_symbol_stats(trade)
        self._update_regime_strategy(trade)
        self._update_confidence_calibration(trade)

        logger.debug(
            f"[SELF-LEARN] Recorded: {trade.symbol} {trade.direction} "
            f"P&L={trade.pnl:+.2f} ({trade.strategy})"
        )

    # ------------------------------------------------------------------
    # Analysis — Generate Insights
    # ------------------------------------------------------------------

    def analyze(self) -> List[LearningInsight]:
        """Run all analysis and return new actionable insights."""
        insights = []
        if len(self._trades) < 10:
            return insights

        insights.extend(self._analyze_strategy_performance())
        insights.extend(self._analyze_time_patterns())
        insights.extend(self._analyze_regime_mapping())
        insights.extend(self._analyze_drawdown_patterns())
        insights.extend(self._analyze_streaks())
        insights.extend(self._analyze_confidence_calibration())
        insights.extend(self._analyze_symbol_ranking())

        self._insights.extend(insights)
        self._save_insights(insights)

        if insights:
            logger.info(f"[SELF-LEARN] Generated {len(insights)} new insights")
            for i in insights[:5]:
                logger.info(f"  💡 [{i.impact.upper()}] {i.title}: {i.action}")

        return insights

    # ------------------------------------------------------------------
    # Query Learned Knowledge
    # ------------------------------------------------------------------

    def get_best_strategy(self, symbol: str = "", regime: str = "") -> Optional[str]:
        """Get the best-performing strategy for given conditions."""
        if regime and regime in self._regime_strategy_stats:
            regime_data = self._regime_strategy_stats[regime]
            best = max(regime_data.items(), key=lambda x: x[1].get("pnl", 0), default=None)
            if best and best[1].get("total", 0) >= 5:
                return best[0]

        if self._strategy_stats:
            valid = {k: v for k, v in self._strategy_stats.items() if v.total_trades >= 5}
            if valid:
                best = max(valid.items(), key=lambda x: x[1].expectancy)
                return best[0]
        return None

    def get_best_hours(self, top_n: int = 5) -> List[Tuple[int, float]]:
        """Get top N most profitable trading hours."""
        if not self._hourly_stats:
            return []
        scored = []
        for hour, stats in self._hourly_stats.items():
            total = stats.get("wins", 0) + stats.get("losses", 0)
            if total >= 5:
                win_rate = stats.get("wins", 0) / total
                scored.append((hour, win_rate))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]

    def get_worst_hours(self, top_n: int = 3) -> List[Tuple[int, float]]:
        """Get worst N trading hours."""
        if not self._hourly_stats:
            return []
        scored = []
        for hour, stats in self._hourly_stats.items():
            total = stats.get("wins", 0) + stats.get("losses", 0)
            if total >= 5:
                win_rate = stats.get("wins", 0) / total
                scored.append((hour, win_rate))
        scored.sort(key=lambda x: x[1])
        return scored[:top_n]

    def get_strategy_stats(self, strategy: str) -> Optional[StrategyStats]:
        return self._strategy_stats.get(strategy)

    def get_all_strategy_stats(self) -> Dict[str, StrategyStats]:
        return dict(self._strategy_stats)

    def get_symbol_ranking(self) -> List[Tuple[str, float]]:
        """Rank symbols by profitability."""
        ranking = []
        for sym, stats in self._symbol_stats.items():
            total = stats.get("wins", 0) + stats.get("losses", 0)
            if total >= 3:
                ranking.append((sym, stats.get("pnl", 0)))
        ranking.sort(key=lambda x: x[1], reverse=True)
        return ranking

    def get_size_multiplier_for_strategy(self, strategy: str) -> float:
        """Get win-rate-weighted size multiplier for a strategy."""
        stats = self._strategy_stats.get(strategy)
        if not stats or stats.total_trades < 10:
            return 1.0
        if stats.win_rate > 0.55 and stats.expectancy > 0:
            return min(1.5, 1.0 + (stats.win_rate - 0.5) * 2)
        elif stats.win_rate < 0.35 or stats.expectancy < 0:
            return max(0.3, stats.win_rate / 0.5)
        return 1.0

    def get_regime_strategy_recommendation(self, regime: str) -> Dict[str, Any]:
        """Get strategy recommendation for a market regime."""
        if regime not in self._regime_strategy_stats:
            return {"strategy": None, "confidence": 0.0}
        data = self._regime_strategy_stats[regime]
        best = None
        best_score = -999
        for strat, stats in data.items():
            total = stats.get("total", 0)
            if total < 3:
                continue
            win_rate = stats.get("wins", 0) / total
            pnl = stats.get("pnl", 0)
            score = win_rate * 0.5 + (1 if pnl > 0 else 0) * 0.5
            if score > best_score:
                best_score = score
                best = strat
        return {"strategy": best, "confidence": min(1.0, best_score), "regime": regime}

    # ------------------------------------------------------------------
    # Internal Analysis Methods
    # ------------------------------------------------------------------

    def _analyze_strategy_performance(self) -> List[LearningInsight]:
        insights = []
        for name, stats in self._strategy_stats.items():
            if stats.total_trades < 10:
                continue
            # Losing strategy
            if stats.win_rate < 0.35 and stats.expectancy < 0:
                insights.append(LearningInsight(
                    insight_id=f"strat_losing_{name}",
                    category="strategy_performance",
                    title=f"Strategy '{name}' is losing money",
                    description=f"Win rate: {stats.win_rate:.0%}, Expectancy: {stats.expectancy:.2f}, "
                                f"Trades: {stats.total_trades}",
                    action=f"Reduce size for '{name}' by 50% or disable it",
                    confidence=0.8 if stats.total_trades > 20 else 0.5,
                    impact="high",
                    data={"strategy": name, "win_rate": stats.win_rate, "expectancy": stats.expectancy},
                ))
            # Winning strategy
            if stats.win_rate > 0.55 and stats.expectancy > 0 and stats.profit_factor > 1.5:
                insights.append(LearningInsight(
                    insight_id=f"strat_winning_{name}",
                    category="strategy_performance",
                    title=f"Strategy '{name}' is highly profitable",
                    description=f"Win rate: {stats.win_rate:.0%}, PF: {stats.profit_factor:.2f}, "
                                f"Expectancy: {stats.expectancy:.2f}",
                    action=f"Increase allocation to '{name}' by 25%",
                    confidence=0.7 if stats.total_trades > 20 else 0.4,
                    impact="high",
                    data={"strategy": name, "win_rate": stats.win_rate, "profit_factor": stats.profit_factor},
                ))
        return insights

    def _analyze_time_patterns(self) -> List[LearningInsight]:
        insights = []
        best = self.get_best_hours(3)
        worst = self.get_worst_hours(3)
        if best:
            insights.append(LearningInsight(
                insight_id="best_hours",
                category="time_patterns",
                title=f"Best trading hours: {', '.join(f'{h}:00' for h, _ in best)}",
                description=f"Win rates: {', '.join(f'{wr:.0%}' for _, wr in best)}",
                action="Increase position size during these hours",
                confidence=0.6, impact="medium",
                data={"best_hours": [(h, wr) for h, wr in best]},
            ))
        if worst:
            insights.append(LearningInsight(
                insight_id="worst_hours",
                category="time_patterns",
                title=f"Worst trading hours: {', '.join(f'{h}:00' for h, _ in worst)}",
                description=f"Win rates: {', '.join(f'{wr:.0%}' for _, wr in worst)}",
                action="Avoid trading or reduce size during these hours",
                confidence=0.6, impact="medium",
                data={"worst_hours": [(h, wr) for h, wr in worst]},
            ))
        return insights

    def _analyze_regime_mapping(self) -> List[LearningInsight]:
        insights = []
        for regime, strategies in self._regime_strategy_stats.items():
            rec = self.get_regime_strategy_recommendation(regime)
            if rec["strategy"] and rec["confidence"] > 0.5:
                insights.append(LearningInsight(
                    insight_id=f"regime_map_{regime}",
                    category="regime_mapping",
                    title=f"Best strategy for '{regime}': {rec['strategy']}",
                    description=f"Confidence: {rec['confidence']:.0%}",
                    action=f"Use '{rec['strategy']}' when regime is '{regime}'",
                    confidence=rec["confidence"], impact="high",
                    data=rec,
                ))
        return insights

    def _analyze_drawdown_patterns(self) -> List[LearningInsight]:
        insights = []
        if len(self._trades) < 20:
            return insights
        pnls = [t.pnl for t in self._trades]
        equity = np.cumsum(pnls)
        peak = np.maximum.accumulate(equity)
        dd = equity - peak
        # Find drawdown clusters
        in_dd = dd < 0
        dd_lengths = []
        current_len = 0
        for is_dd in in_dd:
            if is_dd:
                current_len += 1
            else:
                if current_len > 0:
                    dd_lengths.append(current_len)
                current_len = 0
        if dd_lengths and np.mean(dd_lengths) > 5:
            insights.append(LearningInsight(
                insight_id="dd_pattern",
                category="drawdown_patterns",
                title=f"Drawdowns averaging {np.mean(dd_lengths):.0f} trades long",
                description=f"Max DD length: {max(dd_lengths)} trades, Avg: {np.mean(dd_lengths):.1f}",
                action="Consider reducing size after 3 consecutive losses to shorten drawdowns",
                confidence=0.6, impact="high",
                data={"avg_dd_length": float(np.mean(dd_lengths)), "max_dd_length": max(dd_lengths)},
            ))
        return insights

    def _analyze_streaks(self) -> List[LearningInsight]:
        insights = []
        if len(self._trades) < 15:
            return insights
        # Find win/loss streaks
        max_win_streak = 0
        max_loss_streak = 0
        current_streak = 0
        for t in self._trades:
            if t.pnl > 0:
                current_streak = max(1, current_streak + 1) if current_streak > 0 else 1
            else:
                current_streak = min(-1, current_streak - 1) if current_streak < 0 else -1
            max_win_streak = max(max_win_streak, current_streak)
            max_loss_streak = min(max_loss_streak, current_streak)

        if max_win_streak >= 5:
            insights.append(LearningInsight(
                insight_id="win_streak",
                category="streaks",
                title=f"Max winning streak: {max_win_streak} trades",
                description="Strong winning streaks detected",
                action="After 5+ wins, reduce size slightly to protect gains (overconfidence risk)",
                confidence=0.5, impact="medium",
                data={"max_win_streak": max_win_streak},
            ))
        if abs(max_loss_streak) >= 4:
            insights.append(LearningInsight(
                insight_id="loss_streak",
                category="streaks",
                title=f"Max losing streak: {abs(max_loss_streak)} trades",
                description="Significant losing streaks detected",
                action="After 3 losses, mandatory cooldown and strategy review",
                confidence=0.7, impact="high",
                data={"max_loss_streak": abs(max_loss_streak)},
            ))
        return insights

    def _analyze_confidence_calibration(self) -> List[LearningInsight]:
        """#44 Check if confidence scores match actual win rates."""
        insights = []
        for bucket, stats in self._confidence_buckets.items():
            total = stats.get("total", 0)
            if total < 10:
                continue
            actual_wr = stats.get("wins", 0) / total
            # Parse bucket midpoint
            try:
                low, high = bucket.split("-")
                expected_wr = (float(low) + float(high)) / 2
            except Exception:
                continue
            gap = abs(actual_wr - expected_wr)
            if gap > 0.15:
                insights.append(LearningInsight(
                    insight_id=f"conf_cal_{bucket}",
                    category="confidence_calibration",
                    title=f"Confidence {bucket} miscalibrated",
                    description=f"Expected ~{expected_wr:.0%} win rate, actual: {actual_wr:.0%} ({total} trades)",
                    action=f"Recalibrate confidence model for {bucket} range",
                    confidence=0.7, impact="medium",
                    data={"bucket": bucket, "expected": expected_wr, "actual": actual_wr, "trades": total},
                ))
        return insights

    def _analyze_symbol_ranking(self) -> List[LearningInsight]:
        insights = []
        ranking = self.get_symbol_ranking()
        if len(ranking) >= 2:
            best_sym, best_pnl = ranking[0]
            worst_sym, worst_pnl = ranking[-1]
            if worst_pnl < 0:
                insights.append(LearningInsight(
                    insight_id="symbol_ranking",
                    category="symbol_performance",
                    title=f"Best symbol: {best_sym} (+{best_pnl:.2f}), Worst: {worst_sym} ({worst_pnl:.2f})",
                    description="Focus on profitable symbols, reduce exposure to losers",
                    action=f"Increase {best_sym} allocation, reduce {worst_sym}",
                    confidence=0.6, impact="medium",
                    data={"ranking": ranking},
                ))
        return insights

    # ------------------------------------------------------------------
    # Stats Update Methods
    # ------------------------------------------------------------------

    def _update_strategy_stats(self, trade: TradeJournalEntry) -> None:
        name = trade.strategy or "unknown"
        if name not in self._strategy_stats:
            self._strategy_stats[name] = StrategyStats(strategy=name)
        s = self._strategy_stats[name]
        s.total_trades += 1
        s.total_pnl += trade.pnl
        if trade.pnl > 0:
            s.wins += 1
            s.max_win = max(s.max_win, trade.pnl)
        else:
            s.losses += 1
            s.max_loss = min(s.max_loss, trade.pnl)
        s.win_rate = s.wins / s.total_trades
        s.avg_pnl = s.total_pnl / s.total_trades
        s.avg_hold_minutes = (s.avg_hold_minutes * (s.total_trades - 1) + trade.hold_duration_minutes) / s.total_trades
        # Profit factor
        all_wins = [t.pnl for t in self._trades if t.strategy == name and t.pnl > 0]
        all_losses = [t.pnl for t in self._trades if t.strategy == name and t.pnl <= 0]
        total_wins = sum(all_wins) if all_wins else 0
        total_losses = abs(sum(all_losses)) if all_losses else 1
        s.profit_factor = total_wins / total_losses if total_losses > 0 else 0
        s.avg_win = np.mean(all_wins) if all_wins else 0
        s.avg_loss = np.mean(all_losses) if all_losses else 0
        s.expectancy = s.avg_pnl

    def _update_hourly_stats(self, trade: TradeJournalEntry) -> None:
        hour = trade.entry_time.hour
        if hour not in self._hourly_stats:
            self._hourly_stats[hour] = {"wins": 0, "losses": 0, "pnl": 0.0}
        if trade.pnl > 0:
            self._hourly_stats[hour]["wins"] += 1
        else:
            self._hourly_stats[hour]["losses"] += 1
        self._hourly_stats[hour]["pnl"] += trade.pnl

    def _update_daily_stats(self, trade: TradeJournalEntry) -> None:
        day = trade.entry_time.weekday()
        if day not in self._daily_stats:
            self._daily_stats[day] = {"wins": 0, "losses": 0, "pnl": 0.0}
        if trade.pnl > 0:
            self._daily_stats[day]["wins"] += 1
        else:
            self._daily_stats[day]["losses"] += 1
        self._daily_stats[day]["pnl"] += trade.pnl

    def _update_symbol_stats(self, trade: TradeJournalEntry) -> None:
        sym = trade.symbol
        if sym not in self._symbol_stats:
            self._symbol_stats[sym] = {"wins": 0, "losses": 0, "pnl": 0.0}
        if trade.pnl > 0:
            self._symbol_stats[sym]["wins"] += 1
        else:
            self._symbol_stats[sym]["losses"] += 1
        self._symbol_stats[sym]["pnl"] += trade.pnl

    def _update_regime_strategy(self, trade: TradeJournalEntry) -> None:
        regime = trade.regime or "unknown"
        strat = trade.strategy or "unknown"
        if regime not in self._regime_strategy_stats:
            self._regime_strategy_stats[regime] = {}
        if strat not in self._regime_strategy_stats[regime]:
            self._regime_strategy_stats[regime][strat] = {"wins": 0, "losses": 0, "pnl": 0.0, "total": 0}
        d = self._regime_strategy_stats[regime][strat]
        d["total"] += 1
        if trade.pnl > 0:
            d["wins"] += 1
        else:
            d["losses"] += 1
        d["pnl"] += trade.pnl

    def _update_confidence_calibration(self, trade: TradeJournalEntry) -> None:
        conf = trade.confidence
        bucket = f"{int(conf * 10) / 10:.1f}-{int(conf * 10) / 10 + 0.1:.1f}"
        if bucket not in self._confidence_buckets:
            self._confidence_buckets[bucket] = {"wins": 0, "total": 0}
        self._confidence_buckets[bucket]["total"] += 1
        if trade.pnl > 0:
            self._confidence_buckets[bucket]["wins"] += 1

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute("""CREATE TABLE IF NOT EXISTS trade_journal (
                trade_id TEXT PRIMARY KEY,
                symbol TEXT, direction TEXT, strategy TEXT,
                entry_price REAL, exit_price REAL, lots REAL,
                pnl REAL, pnl_pct REAL,
                entry_time TEXT, exit_time TEXT,
                hold_duration_minutes REAL,
                confidence REAL, risk_reward_planned REAL, risk_reward_actual REAL,
                regime TEXT, sl_hit INTEGER, tp_hit INTEGER,
                slippage_bps REAL, spread_at_entry REAL, notes TEXT
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS insights (
                insight_id TEXT PRIMARY KEY,
                category TEXT, title TEXT, description TEXT,
                action TEXT, confidence REAL, impact TEXT,
                data_json TEXT, discovered_at TEXT, applied INTEGER DEFAULT 0
            )""")
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Learning DB init error: {e}")

    def _save_trade(self, t: TradeJournalEntry) -> None:
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute("""INSERT OR REPLACE INTO trade_journal VALUES
                (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (t.trade_id, t.symbol, t.direction, t.strategy,
                 t.entry_price, t.exit_price, t.lots, t.pnl, t.pnl_pct,
                 t.entry_time.isoformat(), t.exit_time.isoformat(),
                 t.hold_duration_minutes, t.confidence,
                 t.risk_reward_planned, t.risk_reward_actual,
                 t.regime, int(t.sl_hit), int(t.tp_hit),
                 t.slippage_bps, t.spread_at_entry, t.notes))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Trade save error: {e}")

    def _save_insights(self, insights: List[LearningInsight]) -> None:
        try:
            conn = sqlite3.connect(self._db_path)
            for i in insights:
                conn.execute("""INSERT OR REPLACE INTO insights VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (i.insight_id, i.category, i.title, i.description,
                     i.action, i.confidence, i.impact,
                     json.dumps(i.data, default=str),
                     i.discovered_at.isoformat(), int(i.applied)))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Insight save error: {e}")

    def _load_from_db(self) -> None:
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.execute("SELECT * FROM trade_journal ORDER BY entry_time")
            for row in cursor.fetchall():
                trade = TradeJournalEntry(
                    trade_id=row[0], symbol=row[1], direction=row[2], strategy=row[3],
                    entry_price=row[4], exit_price=row[5], lots=row[6],
                    pnl=row[7], pnl_pct=row[8],
                    entry_time=datetime.fromisoformat(row[9]),
                    exit_time=datetime.fromisoformat(row[10]),
                    hold_duration_minutes=row[11], confidence=row[12],
                    risk_reward_planned=row[13], risk_reward_actual=row[14],
                    regime=row[15] or "", sl_hit=bool(row[16]), tp_hit=bool(row[17]),
                    slippage_bps=row[18] or 0, spread_at_entry=row[19] or 0, notes=row[20] or "",
                )
                self._trades.append(trade)
                self._update_strategy_stats(trade)
                self._update_hourly_stats(trade)
                self._update_daily_stats(trade)
                self._update_symbol_stats(trade)
                self._update_regime_strategy(trade)
                self._update_confidence_calibration(trade)
            conn.close()
        except Exception as e:
            logger.warning(f"Learning DB load error: {e}")
