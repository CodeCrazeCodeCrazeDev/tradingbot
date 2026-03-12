"""
Knowledge-Action Bridge (#45 + Integration)
=============================================
Converts ALL learned knowledge into concrete trading decisions.

This is the critical link: everything the self-awareness system discovers,
everything the self-learning engine learns, feeds DIRECTLY into making
the AI a more profitable and disciplined trader.

Pipeline:
    Knowledge Ledger (what we know)
    + Self-Learning Insights (what we've learned from trades)
    + Discipline State (current risk state)
    + Profitability Analysis (signal quality)
    ──────────────────────────────────
    = Final Trade Decision + Parameters

The bridge runs continuously, pulling fresh knowledge and updating
all trading parameters in real-time.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class TradingDirective:
    """
    A concrete instruction derived from learned knowledge.
    These directives are applied to every trade decision.
    """
    directive_id: str
    source: str                 # "knowledge_gap", "self_learning", "discipline", "profitability"
    category: str               # e.g. "strategy_selection", "position_sizing", "timing"
    action: str                 # What to do
    parameter: str              # Which parameter to adjust
    value: Any                  # New value or multiplier
    confidence: float           # 0-1
    expires_at: Optional[datetime] = None
    active: bool = True
    applied_count: int = 0
    last_applied: Optional[datetime] = None


@dataclass
class TradeDecision:
    """
    Final trade decision after all knowledge has been applied.
    This is what the trading loop actually uses.
    """
    should_trade: bool = True
    symbol: str = ""
    direction: str = ""
    lots: float = 0.0
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    partial_tp: float = 0.0            # Take 50% profit here
    strategy: str = ""
    confidence: float = 0.0
    risk_reward: float = 0.0
    size_multiplier: float = 1.0       # Combined from all sources
    regime: str = ""
    needs_human_approval: bool = False
    rejection_reasons: List[str] = field(default_factory=list)
    applied_directives: List[str] = field(default_factory=list)
    knowledge_applied: Dict[str, Any] = field(default_factory=dict)


class KnowledgeActionBridge:
    """
    The bridge between knowledge and action.
    
    Pulls from:
        1. KnowledgeLedger — symbol properties, regime playbooks, risk params
        2. SelfLearningEngine — strategy stats, time patterns, confidence calibration
        3. DisciplineEngine — current risk state, loss limits
        4. ProfitabilityEngine — signal quality, confluence
    
    Outputs:
        TradingDirectives that are applied to every trade decision.
    
    Usage:
        bridge = KnowledgeActionBridge()
        
        # Connect knowledge sources
        bridge.set_knowledge_ledger(ledger)
        bridge.set_learning_engine(learning)
        bridge.set_discipline_engine(discipline)
        bridge.set_profitability_engine(profitability)
        
        # Before every trade:
        decision = await bridge.evaluate_trade(symbol, direction, lots, ...)
        if not decision.should_trade:
            return
        
        # Use decision parameters
        actual_lots = decision.lots * decision.size_multiplier
        sl = decision.stop_loss
        tp = decision.take_profit
    """

    def __init__(self, db_path: Optional[str] = None):
        # Knowledge sources (set externally)
        self._knowledge_ledger = None
        self._learning_engine = None
        self._discipline_engine = None
        self._profitability_engine = None
        self._human_approval_gate = None

        # Active directives
        self._directives: Dict[str, TradingDirective] = {}

        # Cached knowledge
        self._symbol_properties: Dict[str, Dict[str, Any]] = {}
        self._regime_playbooks: Dict[str, Dict[str, Any]] = {}
        self._strategy_rankings: Dict[str, float] = {}
        self._optimal_hours: Dict[int, float] = {}
        self._risk_parameters: Dict[str, float] = {}

        # Stats
        self._total_evaluations = 0
        self._total_approved = 0
        self._total_blocked = 0
        self._total_directives_applied = 0

        # Background sync
        self._running = False
        self._sync_task: Optional[asyncio.Task] = None
        self._sync_interval = 60  # seconds

        # Persistence
        if db_path is None:
            root = Path(__file__).resolve().parent.parent.parent
            db_path = str(root / "data" / "knowledge_bridge.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db_path = db_path
        self._init_db()

        logger.info("[BRIDGE] Knowledge-Action Bridge initialized")

    # ------------------------------------------------------------------
    # Connect Knowledge Sources
    # ------------------------------------------------------------------

    def set_knowledge_ledger(self, ledger) -> None:
        self._knowledge_ledger = ledger
        logger.info("[BRIDGE] Connected to Knowledge Ledger")

    def set_learning_engine(self, engine) -> None:
        self._learning_engine = engine
        logger.info("[BRIDGE] Connected to Self-Learning Engine")

    def set_discipline_engine(self, engine) -> None:
        self._discipline_engine = engine
        logger.info("[BRIDGE] Connected to Discipline Engine")

    def set_profitability_engine(self, engine) -> None:
        self._profitability_engine = engine
        logger.info("[BRIDGE] Connected to Profitability Engine")

    def set_human_approval_gate(self, gate) -> None:
        self._human_approval_gate = gate
        logger.info("[BRIDGE] Connected to Human Approval Gate")

    # ------------------------------------------------------------------
    # Start/Stop Background Sync
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start background knowledge sync."""
        if self._running:
            return
        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
        logger.info("[BRIDGE] Background knowledge sync started")

    async def stop(self) -> None:
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass

    async def _sync_loop(self) -> None:
        """Periodically pull fresh knowledge and update directives."""
        while self._running:
            try:
                await self._sync_knowledge()
            except Exception as e:
                logger.warning(f"[BRIDGE] Sync error: {e}")
            await asyncio.sleep(self._sync_interval)

    async def _sync_knowledge(self) -> None:
        """Pull latest knowledge from all sources and create directives."""
        directives_before = len(self._directives)

        # 1. Pull from Knowledge Ledger
        if self._knowledge_ledger:
            await self._sync_from_ledger()

        # 2. Pull from Self-Learning Engine
        if self._learning_engine:
            self._sync_from_learning()

        new_directives = len(self._directives) - directives_before
        if new_directives > 0:
            logger.info(f"[BRIDGE] Synced: {new_directives} new directives (total: {len(self._directives)})")

        # Expire old directives
        self._expire_directives()

    async def _sync_from_ledger(self) -> None:
        """Pull knowledge from the KnowledgeLedger and create directives."""
        try:
            conn = sqlite3.connect(self._knowledge_ledger._db_path)

            # Get all resolved knowledge
            cursor = conn.execute(
                "SELECT key, value_json, category FROM knowledge WHERE status = 'active'"
            )
            for key, value_json, category in cursor.fetchall():
                try:
                    value = json.loads(value_json) if value_json else {}
                except (json.JSONDecodeError, TypeError):
                    value = {"raw": value_json}

                # Convert knowledge to directives
                if category == "symbol_behavior":
                    self._create_symbol_directive(key, value)
                elif category == "regime_awareness":
                    self._create_regime_directive(key, value)
                elif category == "risk_parameters":
                    self._create_risk_directive(key, value)
                elif category == "strategy_performance":
                    self._create_strategy_directive(key, value)
                elif category == "self_performance":
                    self._create_performance_directive(key, value)

            conn.close()
        except Exception as e:
            logger.debug(f"[BRIDGE] Ledger sync error: {e}")

    def _sync_from_learning(self) -> None:
        """Pull insights from the SelfLearningEngine."""
        try:
            # Get strategy stats
            all_stats = self._learning_engine.get_all_strategy_stats()
            for name, stats in all_stats.items():
                if stats.total_trades >= 5:
                    self._strategy_rankings[name] = stats.expectancy
                    mult = self._learning_engine.get_size_multiplier_for_strategy(name)
                    self._add_directive(TradingDirective(
                        directive_id=f"learn_strat_size_{name}",
                        source="self_learning",
                        category="position_sizing",
                        action=f"Set size multiplier for {name}",
                        parameter=f"strategy_size_{name}",
                        value=mult,
                        confidence=min(0.8, stats.total_trades / 50),
                    ))

            # Get optimal hours
            best_hours = self._learning_engine.get_best_hours(5)
            worst_hours = self._learning_engine.get_worst_hours(3)
            for hour, wr in best_hours:
                self._optimal_hours[hour] = wr
            for hour, wr in worst_hours:
                self._add_directive(TradingDirective(
                    directive_id=f"learn_avoid_hour_{hour}",
                    source="self_learning",
                    category="timing",
                    action=f"Reduce size at hour {hour} (win_rate={wr:.0%})",
                    parameter=f"hour_mult_{hour}",
                    value=max(0.5, wr / 0.5),
                    confidence=0.6,
                ))

            # Get regime recommendations
            for regime in ["strong_uptrend", "weak_uptrend", "ranging",
                           "weak_downtrend", "strong_downtrend", "high_volatility"]:
                rec = self._learning_engine.get_regime_strategy_recommendation(regime)
                if rec.get("strategy") and rec.get("confidence", 0) > 0.4:
                    self._regime_playbooks[regime] = rec
                    self._add_directive(TradingDirective(
                        directive_id=f"learn_regime_{regime}",
                        source="self_learning",
                        category="strategy_selection",
                        action=f"Use {rec['strategy']} in {regime}",
                        parameter=f"regime_strategy_{regime}",
                        value=rec["strategy"],
                        confidence=rec["confidence"],
                    ))
        except Exception as e:
            logger.debug(f"[BRIDGE] Learning sync error: {e}")

    # ------------------------------------------------------------------
    # Directive Creation from Knowledge
    # ------------------------------------------------------------------

    def _create_symbol_directive(self, key: str, value: Any) -> None:
        """Convert symbol knowledge to trading directive."""
        # e.g. key = "EURUSD.spread_avg", value = {"spread_avg": 1.2}
        parts = key.split(".")
        if len(parts) >= 2:
            symbol = parts[0]
            prop = parts[1]
            if symbol not in self._symbol_properties:
                self._symbol_properties[symbol] = {}
            self._symbol_properties[symbol][prop] = value

            if prop == "spread_avg" and isinstance(value, (int, float)):
                self._add_directive(TradingDirective(
                    directive_id=f"sym_{symbol}_spread",
                    source="knowledge_gap",
                    category="execution",
                    action=f"Normal spread for {symbol} is {value}. Reject if > {value * 2}",
                    parameter=f"normal_spread_{symbol}",
                    value=value,
                    confidence=0.9,
                ))
            elif prop == "volatility_daily" and isinstance(value, (int, float)):
                self._add_directive(TradingDirective(
                    directive_id=f"sym_{symbol}_vol",
                    source="knowledge_gap",
                    category="position_sizing",
                    action=f"Daily volatility for {symbol}: {value}. Adjust position size.",
                    parameter=f"daily_vol_{symbol}",
                    value=value,
                    confidence=0.9,
                ))

    def _create_regime_directive(self, key: str, value: Any) -> None:
        """Convert regime knowledge to directive."""
        if isinstance(value, dict):
            regime = value.get("regime", key)
            action = value.get("action", "")
            risk_mult = value.get("risk_multiplier", 1.0)
            self._regime_playbooks[regime] = value
            self._add_directive(TradingDirective(
                directive_id=f"regime_{regime}",
                source="knowledge_gap",
                category="risk_management",
                action=f"In {regime}: {action}, risk_mult={risk_mult}",
                parameter=f"regime_risk_{regime}",
                value=risk_mult,
                confidence=0.8,
            ))

    def _create_risk_directive(self, key: str, value: Any) -> None:
        """Convert risk knowledge to directive."""
        if isinstance(value, dict):
            for param, val in value.items():
                if isinstance(val, (int, float)):
                    self._risk_parameters[param] = val
                    self._add_directive(TradingDirective(
                        directive_id=f"risk_{param}",
                        source="knowledge_gap",
                        category="risk_management",
                        action=f"Risk param {param} = {val}",
                        parameter=param,
                        value=val,
                        confidence=0.7,
                    ))

    def _create_strategy_directive(self, key: str, value: Any) -> None:
        """Convert strategy knowledge to directive."""
        if isinstance(value, dict):
            strategy = value.get("strategy", key)
            win_rate = value.get("win_rate", 0)
            if isinstance(win_rate, (int, float)) and win_rate > 0:
                self._strategy_rankings[strategy] = win_rate
                self._add_directive(TradingDirective(
                    directive_id=f"strat_perf_{strategy}",
                    source="knowledge_gap",
                    category="strategy_selection",
                    action=f"Strategy {strategy} win_rate={win_rate:.0%}",
                    parameter=f"strategy_wr_{strategy}",
                    value=win_rate,
                    confidence=0.6,
                ))

    def _create_performance_directive(self, key: str, value: Any) -> None:
        """Convert self-performance knowledge to directive."""
        if isinstance(value, dict):
            for metric, val in value.items():
                if metric == "win_rate" and isinstance(val, (int, float)):
                    if val < 0.4:
                        self._add_directive(TradingDirective(
                            directive_id="perf_low_wr",
                            source="knowledge_gap",
                            category="risk_management",
                            action=f"Overall win rate is low ({val:.0%}). Reduce position sizes.",
                            parameter="global_size_mult",
                            value=max(0.5, val / 0.5),
                            confidence=0.7,
                        ))
                elif metric == "max_drawdown_actual" and isinstance(val, (int, float)):
                    if val > 10:
                        self._add_directive(TradingDirective(
                            directive_id="perf_high_dd",
                            source="knowledge_gap",
                            category="risk_management",
                            action=f"Max drawdown is {val:.1f}%. Tighten risk controls.",
                            parameter="dd_risk_mult",
                            value=max(0.5, 1.0 - val / 30),
                            confidence=0.8,
                        ))

    def _add_directive(self, directive: TradingDirective) -> None:
        self._directives[directive.directive_id] = directive

    def _expire_directives(self) -> None:
        now = datetime.now()
        expired = [d_id for d_id, d in self._directives.items()
                   if d.expires_at and d.expires_at < now]
        for d_id in expired:
            del self._directives[d_id]

    # ------------------------------------------------------------------
    # Evaluate Trade — The Main Decision Point
    # ------------------------------------------------------------------

    async def evaluate_trade(
        self,
        symbol: str,
        direction: str,
        lots: float,
        entry_price: float,
        strategy: str = "",
        confidence: float = 0.0,
        notional_value: float = 0.0,
        current_spread: float = 0.0,
        atr: float = 0.0,
        portfolio_value: float = 0.0,
        open_positions: Optional[Dict[str, float]] = None,
        prices_m15=None,
        prices_h1=None,
        prices_h4=None,
        prices_d1=None,
        volumes=None,
    ) -> TradeDecision:
        """
        The MASTER trade evaluation. Applies ALL knowledge to make the decision.
        
        Returns a TradeDecision with final parameters.
        """
        self._total_evaluations += 1
        decision = TradeDecision(
            should_trade=True,
            symbol=symbol,
            direction=direction,
            lots=lots,
            entry_price=entry_price,
            strategy=strategy,
            confidence=confidence,
            risk_reward=0.0,
        )

        combined_size_mult = 1.0

        # ── Step 1: Discipline Check ──
        if self._discipline_engine:
            verdict = self._discipline_engine.check_trade(
                symbol=symbol, direction=direction, lots=lots,
                notional_value=notional_value, current_spread=current_spread,
                portfolio_value=portfolio_value, open_positions=open_positions,
            )
            if not verdict.allowed:
                decision.should_trade = False
                decision.rejection_reasons.append(f"[DISCIPLINE] {verdict.message}")
                self._total_blocked += 1
                return decision
            combined_size_mult *= verdict.size_multiplier
            decision.applied_directives.append("discipline_check")

        # ── Step 2: Profitability Analysis ──
        if self._profitability_engine:
            import numpy as np
            enhancement = self._profitability_engine.analyze_trade(
                symbol=symbol, direction=direction, entry_price=entry_price,
                prices_m15=np.array(prices_m15) if prices_m15 is not None else None,
                prices_h1=np.array(prices_h1) if prices_h1 is not None else None,
                prices_h4=np.array(prices_h4) if prices_h4 is not None else None,
                prices_d1=np.array(prices_d1) if prices_d1 is not None else None,
                volumes=np.array(volumes) if volumes is not None else None,
                atr=atr, strategy=strategy,
            )
            if not enhancement.should_take:
                decision.should_trade = False
                decision.rejection_reasons.extend(
                    [f"[PROFIT] {r}" for r in enhancement.rejection_reasons]
                )
                self._total_blocked += 1
                return decision

            decision.stop_loss = enhancement.suggested_sl
            decision.take_profit = enhancement.suggested_tp
            decision.partial_tp = enhancement.suggested_tp_partial
            decision.risk_reward = enhancement.risk_reward
            decision.regime = enhancement.regime.value
            combined_size_mult *= enhancement.size_multiplier
            decision.applied_directives.append("profitability_analysis")
            decision.knowledge_applied["signal_strength"] = enhancement.signal_strength.value
            decision.knowledge_applied["confluence"] = enhancement.confluence_score
            decision.knowledge_applied["momentum"] = enhancement.momentum_score

        # ── Step 3: Apply Knowledge Directives ──
        for d_id, directive in self._directives.items():
            if not directive.active:
                continue

            # Apply spread knowledge
            if directive.parameter == f"normal_spread_{symbol}":
                if self._discipline_engine:
                    self._discipline_engine.update_normal_spread(symbol, directive.value)
                decision.applied_directives.append(d_id)

            # Apply regime risk multiplier
            if directive.parameter == f"regime_risk_{decision.regime}":
                combined_size_mult *= directive.value
                decision.applied_directives.append(d_id)

            # Apply strategy size multiplier
            if directive.parameter == f"strategy_size_{strategy}":
                combined_size_mult *= directive.value
                decision.applied_directives.append(d_id)

            # Apply hour multiplier
            current_hour = datetime.now().hour
            if directive.parameter == f"hour_mult_{current_hour}":
                combined_size_mult *= directive.value
                decision.applied_directives.append(d_id)

            # Apply global size multiplier (from low win rate)
            if directive.parameter == "global_size_mult":
                combined_size_mult *= directive.value
                decision.applied_directives.append(d_id)

            # Apply drawdown risk multiplier
            if directive.parameter == "dd_risk_mult":
                combined_size_mult *= directive.value
                decision.applied_directives.append(d_id)

            directive.applied_count += 1
            directive.last_applied = datetime.now()

        # ── Step 4: Apply Regime Playbook ──
        if decision.regime in self._regime_playbooks:
            playbook = self._regime_playbooks[decision.regime]
            if isinstance(playbook, dict):
                action = playbook.get("action", "")
                if "STOP" in str(action).upper():
                    decision.should_trade = False
                    decision.rejection_reasons.append(
                        f"[REGIME] Playbook says STOP in {decision.regime}"
                    )
                    self._total_blocked += 1
                    return decision
                risk_mult = playbook.get("risk_multiplier", 1.0)
                if isinstance(risk_mult, (int, float)):
                    combined_size_mult *= risk_mult
                decision.applied_directives.append(f"regime_playbook_{decision.regime}")

        # ── Step 5: Human Approval Gate ──
        if self._human_approval_gate and notional_value > 0:
            if self._human_approval_gate.needs_approval(notional_value):
                decision.needs_human_approval = True
                decision.applied_directives.append("human_approval_required")

        # ── Finalize ──
        decision.size_multiplier = max(0.1, min(2.0, combined_size_mult))
        decision.lots = lots * decision.size_multiplier

        self._total_directives_applied += len(decision.applied_directives)
        self._total_approved += 1

        # Save decision
        self._save_decision(decision)

        logger.info(
            f"[BRIDGE] Trade evaluated: {symbol} {direction} | "
            f"size_mult={decision.size_multiplier:.2f}, "
            f"directives={len(decision.applied_directives)}, "
            f"regime={decision.regime}, "
            f"RR={decision.risk_reward:.1f}, "
            f"approved={'YES' if decision.should_trade else 'NO'}"
        )

        return decision

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        return {
            "total_evaluations": self._total_evaluations,
            "total_approved": self._total_approved,
            "total_blocked": self._total_blocked,
            "active_directives": len(self._directives),
            "total_directives_applied": self._total_directives_applied,
            "symbol_properties_known": len(self._symbol_properties),
            "regime_playbooks": len(self._regime_playbooks),
            "strategy_rankings": dict(self._strategy_rankings),
            "optimal_hours": dict(self._optimal_hours),
            "risk_parameters": dict(self._risk_parameters),
        }

    def get_active_directives(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": d.directive_id,
                "source": d.source,
                "category": d.category,
                "action": d.action,
                "parameter": d.parameter,
                "value": d.value,
                "confidence": d.confidence,
                "applied_count": d.applied_count,
            }
            for d in self._directives.values()
            if d.active
        ]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute("""CREATE TABLE IF NOT EXISTS trade_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT, symbol TEXT, direction TEXT,
                lots REAL, entry_price REAL, stop_loss REAL, take_profit REAL,
                strategy TEXT, confidence REAL, risk_reward REAL,
                size_multiplier REAL, regime TEXT,
                should_trade INTEGER, needs_human_approval INTEGER,
                rejection_reasons TEXT, applied_directives TEXT,
                knowledge_applied TEXT
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS directives (
                directive_id TEXT PRIMARY KEY,
                source TEXT, category TEXT, action TEXT,
                parameter TEXT, value TEXT, confidence REAL,
                active INTEGER, applied_count INTEGER,
                last_applied TEXT
            )""")
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Bridge DB init error: {e}")

    def _save_decision(self, d: TradeDecision) -> None:
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute("""INSERT INTO trade_decisions
                (timestamp, symbol, direction, lots, entry_price, stop_loss, take_profit,
                 strategy, confidence, risk_reward, size_multiplier, regime,
                 should_trade, needs_human_approval, rejection_reasons,
                 applied_directives, knowledge_applied)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (datetime.now().isoformat(), d.symbol, d.direction, d.lots,
                 d.entry_price, d.stop_loss, d.take_profit,
                 d.strategy, d.confidence, d.risk_reward,
                 d.size_multiplier, d.regime,
                 int(d.should_trade), int(d.needs_human_approval),
                 json.dumps(d.rejection_reasons),
                 json.dumps(d.applied_directives),
                 json.dumps(d.knowledge_applied, default=str)))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"Decision save error: {e}")
