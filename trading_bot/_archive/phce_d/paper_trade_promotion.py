"""
PHCE-D Module 9: Paper-Trade Promotion Layer

Turn validated candidates into paper-traded evidence before any capital eligibility.

Hard rules:
- No live execution path
- Paper fills must use realistic execution assumptions (P0 #4)
- Cold start: insufficient sample NEVER produces BUY/SELL/PAPER_TRADE_CANDIDATE (P0 #5)
- If realistic execution removes the edge → REJECTED or NO_TRADE
- No benchmark comparison → invalid promotion

Integrates with:
- trading_bot.validation.paper_trading_validator
- trading_bot.core.autonomy_control_plane
- trading_bot.core.research_mvp_pipeline (PaperLedger)
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .core_types import (
    DecisionOutput,
    ExecutionRealismConfig,
    GatewayResult,
    Hypothesis,
    PaperTradePromotionThresholds,
    PaperTradeStage,
    VerificationReport,
)

logger = logging.getLogger(__name__)


@dataclass
class PaperTradeRecord:
    """A single paper-trade record with realistic execution."""
    trade_id: str
    hypothesis_id: str
    symbol: str
    direction: str
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    entry_timestamp: float
    exit_timestamp: Optional[float]
    # Realistic execution costs
    spread_cost: float
    slippage_cost: float
    market_impact_cost: float
    broker_fee: float
    total_cost: float
    # Realistic fill
    fill_rate: float  # 0-1, partial fill simulation
    delay_jitter_ms: float
    # PnL
    realized_pnl: float = 0.0
    realized_pnl_after_cost: float = 0.0
    # Regime at entry
    regime_at_entry: str = ""
    # Status
    stage: PaperTradeStage = PaperTradeStage.ACCUMULATING_EVIDENCE


@dataclass
class PromotionAssessment:
    """Assessment of whether a paper-trade candidate is ready for promotion."""
    hypothesis_id: str
    stage: PaperTradeStage
    total_trades: int
    total_days: int
    regimes_observed: int
    cost_adjusted_sharpe: float
    max_drawdown_pct: float
    benchmark_delta: float
    hit_rate: float
    meets_thresholds: bool
    failure_reasons: List[str]
    processing_time_ms: float


class ExecutionRealismEngine:
    """
    P0 #4: Execution Realism Module

    Paper trading with ideal fills is fake evidence.
    This engine punishes signals using realistic execution assumptions:
    - Half-spread minimum penalty
    - Slippage penalty
    - Partial-fill simulation
    - Delay jitter
    - Market impact estimate
    - Liquidity rejection

    Hard rule: if realistic execution removes the edge, output REJECTED or NO_TRADE.
    """

    def __init__(self, config: Optional[ExecutionRealismConfig] = None):
        self.config = config or ExecutionRealismConfig()

    def apply_realism(
        self,
        notional: float,
        mid_price: float,
        side: str,
        average_daily_volume: float = 1_000_000.0,
    ) -> Dict[str, Any]:
        """
        Apply realistic execution assumptions to a paper trade.

        Returns cost breakdown and fill details.
        """
        if notional <= 0 or mid_price <= 0:
            return {"total_cost": 0.0, "fill_rate": 0.0, "edge_survives": False}

        quantity = notional / mid_price
        participation = quantity / max(average_daily_volume, 1.0)

        # Half-spread penalty
        spread_cost = notional * self.config.half_spread_penalty_bps / 10000.0

        # Slippage penalty
        slippage_cost = notional * self.config.slippage_penalty_bps / 10000.0

        # Market impact (square-root model)
        impact_bps = self.config.market_impact_coefficient_bps * math.sqrt(participation)
        market_impact_cost = notional * impact_bps / 10000.0

        # Broker fee (approximate)
        broker_fee = max(1.0, notional * 0.001)  # 0.1% or $1 minimum

        total_cost = spread_cost + slippage_cost + market_impact_cost + broker_fee

        # Partial fill
        fill_rate = self.config.partial_fill_rate
        if participation > self.config.liquidity_rejection_threshold:
            fill_rate *= 0.5  # Severe fill degradation for large orders

        # Delay jitter
        delay_jitter = self.config.delay_jitter_ms

        # Fill price
        cost_per_share = total_cost / max(quantity, 1)
        if side == "buy":
            fill_price = mid_price + cost_per_share
        else:
            fill_price = max(0.0, mid_price - cost_per_share)

        return {
            "spread_cost": spread_cost,
            "slippage_cost": slippage_cost,
            "market_impact_cost": market_impact_cost,
            "broker_fee": broker_fee,
            "total_cost": total_cost,
            "total_cost_bps": total_cost / notional * 10000 if notional > 0 else 0,
            "fill_rate": fill_rate,
            "fill_price": fill_price,
            "delay_jitter_ms": delay_jitter,
            "participation_rate": participation,
            "edge_survives": True,  # Caller must compare against expected edge
        }


class PaperTradePromotionLayer:
    """
    Module 9: Paper-Trade Promotion Layer

    Turns validated PAPER_TRADE_CANDIDATEs into paper-traded evidence
    before any capital eligibility.

    No live execution path. Ever.

    Kill criteria:
    - Weak-signal strategy fails to outperform no-trade baseline
    - Negative paper-trade Sharpe delta
    - Unstable edge after realistic cost assumptions
    - Insufficient sample size for promotion
    """

    def __init__(
        self,
        thresholds: Optional[PaperTradePromotionThresholds] = None,
        execution_realism: Optional[ExecutionRealismConfig] = None,
        # Integration hooks
        paper_trading_validator=None,
    ):
        self.thresholds = thresholds or PaperTradePromotionThresholds()
        self.execution_realism_engine = ExecutionRealismEngine(execution_realism)
        self.paper_trading_validator = paper_trading_validator

        # Paper trade records per hypothesis
        self._records: Dict[str, List[PaperTradeRecord]] = {}
        self._assessments: Dict[str, PromotionAssessment] = {}

        # Statistics
        self.total_candidates = 0
        self.total_promoted = 0
        self.total_failed = 0
        self.cold_start_blocks = 0

    def record_paper_trade(
        self,
        hypothesis_id: str,
        symbol: str,
        direction: str,
        entry_price: float,
        quantity: float,
        notional: float,
        mid_price: float,
        average_daily_volume: float = 1_000_000.0,
        regime_at_entry: str = "",
        now: Optional[float] = None,
    ) -> PaperTradeRecord:
        """
        Record a paper trade entry with realistic execution assumptions.

        Args:
            hypothesis_id: The hypothesis this trade is based on
            symbol: Trading symbol
            direction: "buy" or "sell"
            entry_price: Intended entry price
            quantity: Order quantity
            notional: Order notional value
            mid_price: Current mid price
            average_daily_volume: ADV for market impact
            regime_at_entry: Regime label at entry time
            now: Current timestamp

        Returns:
            PaperTradeRecord with realistic execution costs applied
        """
        now = now or time.time()

        # Apply execution realism
        realism = self.execution_realism_engine.apply_realism(
            notional, mid_price, direction, average_daily_volume
        )

        record = PaperTradeRecord(
            trade_id=f"pt_{int(now * 1000)}_{symbol}",
            hypothesis_id=hypothesis_id,
            symbol=symbol,
            direction=direction,
            entry_price=realism.get("fill_price", entry_price),
            exit_price=None,
            quantity=quantity * realism.get("fill_rate", 0.95),
            entry_timestamp=now,
            exit_timestamp=None,
            spread_cost=realism.get("spread_cost", 0.0),
            slippage_cost=realism.get("slippage_cost", 0.0),
            market_impact_cost=realism.get("market_impact_cost", 0.0),
            broker_fee=realism.get("broker_fee", 0.0),
            total_cost=realism.get("total_cost", 0.0),
            fill_rate=realism.get("fill_rate", 0.95),
            delay_jitter_ms=realism.get("delay_jitter_ms", 50.0),
            regime_at_entry=regime_at_entry,
        )

        if hypothesis_id not in self._records:
            self._records[hypothesis_id] = []
        self._records[hypothesis_id].append(record)

        logger.info(
            f"Paper trade recorded: {record.trade_id} "
            f"cost={realism.get('total_cost_bps', 0):.1f}bps "
            f"fill_rate={realism.get('fill_rate', 0.95):.0%}"
        )

        return record

    def close_paper_trade(
        self,
        hypothesis_id: str,
        trade_id: str,
        exit_price: float,
        now: Optional[float] = None,
    ) -> Optional[PaperTradeRecord]:
        """Close a paper trade and calculate realized PnL after costs."""
        now = now or time.time()
        records = self._records.get(hypothesis_id, [])

        for record in records:
            if record.trade_id == trade_id and record.exit_price is None:
                record.exit_price = exit_price
                record.exit_timestamp = now

                # Calculate PnL after cost
                if record.direction == "buy":
                    raw_pnl = (exit_price - record.entry_price) * record.quantity
                else:
                    raw_pnl = (record.entry_price - exit_price) * record.quantity

                record.realized_pnl = raw_pnl
                record.realized_pnl_after_cost = raw_pnl - record.total_cost

                return record

        return None

    def assess_promotion(
        self,
        hypothesis_id: str,
        benchmark_sharpe: float = 0.0,
        now: Optional[float] = None,
    ) -> PromotionAssessment:
        """
        Assess whether a paper-trade candidate is ready for promotion
        to the next governance review.

        Promotion requires:
        - Minimum trade count
        - Minimum day count
        - Minimum regimes observed
        - Cost-adjusted Sharpe above threshold
        - Max drawdown below threshold
        - Benchmark delta if required
        """
        start = time.monotonic()
        now = now or time.time()

        records = self._records.get(hypothesis_id, [])
        closed = [r for r in records if r.exit_price is not None]

        # Basic counts
        total_trades = len(closed)
        if total_trades == 0:
            return PromotionAssessment(
                hypothesis_id=hypothesis_id,
                stage=PaperTradeStage.ACCUMULATING_EVIDENCE,
                total_trades=0, total_days=0, regimes_observed=0,
                cost_adjusted_sharpe=0.0, max_drawdown_pct=0.0,
                benchmark_delta=0.0, hit_rate=0.0,
                meets_thresholds=False,
                failure_reasons=["no_closed_trades"],
                processing_time_ms=(time.monotonic() - start) * 1000,
            )

        # Day count
        entry_dates = set()
        for r in closed:
            entry_dates.add(int(r.entry_timestamp // 86400))
        total_days = len(entry_dates)

        # Regimes observed
        regimes = set(r.regime_at_entry for r in closed if r.regime_at_entry)
        regimes_observed = len(regimes)

        # Hit rate
        wins = sum(1 for r in closed if r.realized_pnl_after_cost > 0)
        hit_rate = wins / total_trades

        # Cost-adjusted Sharpe
        pnls = [r.realized_pnl_after_cost for r in closed]
        avg_pnl = sum(pnls) / len(pnls)
        variance = sum((p - avg_pnl) ** 2 for p in pnls) / len(pnls)
        std_pnl = math.sqrt(variance) if variance > 0 else 1.0
        cost_adjusted_sharpe = avg_pnl / std_pnl if std_pnl > 0 else 0.0

        # Max drawdown
        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        for p in pnls:
            cumulative += p
            peak = max(peak, cumulative)
            dd = (peak - cumulative) / peak if peak > 0 else 0.0
            max_dd = max(max_dd, dd)
        max_drawdown_pct = max_dd * 100

        # Benchmark delta
        benchmark_delta = cost_adjusted_sharpe - benchmark_sharpe

        # Check thresholds
        failure_reasons = []
        if total_trades < self.thresholds.min_trades:
            failure_reasons.append(f"trades_{total_trades}_below_{self.thresholds.min_trades}")
        if total_days < self.thresholds.min_days:
            failure_reasons.append(f"days_{total_days}_below_{self.thresholds.min_days}")
        if regimes_observed < self.thresholds.min_regimes:
            failure_reasons.append(f"regimes_{regimes_observed}_below_{self.thresholds.min_regimes}")
        if cost_adjusted_sharpe < self.thresholds.min_cost_adjusted_sharpe:
            failure_reasons.append(f"sharpe_{cost_adjusted_sharpe:.2f}_below_{self.thresholds.min_cost_adjusted_sharpe}")
        if max_drawdown_pct > self.thresholds.max_drawdown_pct:
            failure_reasons.append(f"drawdown_{max_drawdown_pct:.1f}%_above_{self.thresholds.max_drawdown_pct}%")
        if self.thresholds.benchmark_delta_required and benchmark_delta <= 0:
            failure_reasons.append(f"benchmark_delta_{benchmark_delta:.2f}_not_positive")

        meets_thresholds = len(failure_reasons) == 0

        # Determine stage
        if meets_thresholds:
            stage = PaperTradeStage.PASSED_THRESHOLD
            self.total_promoted += 1
        elif cost_adjusted_sharpe < 0:
            stage = PaperTradeStage.FAILED
            self.total_failed += 1
        else:
            stage = PaperTradeStage.ACCUMULATING_EVIDENCE

        assessment = PromotionAssessment(
            hypothesis_id=hypothesis_id,
            stage=stage,
            total_trades=total_trades,
            total_days=total_days,
            regimes_observed=regimes_observed,
            cost_adjusted_sharpe=cost_adjusted_sharpe,
            max_drawdown_pct=max_drawdown_pct,
            benchmark_delta=benchmark_delta,
            hit_rate=hit_rate,
            meets_thresholds=meets_thresholds,
            failure_reasons=failure_reasons,
            processing_time_ms=(time.monotonic() - start) * 1000,
        )

        self._assessments[hypothesis_id] = assessment
        return assessment

    def check_cold_start(self, hypothesis_id: str, sample_size: int) -> bool:
        """
        P0 #5: Cold Start Protocol

        Hard rule: insufficient_sample_size → RESEARCH_ONLY
        No exceptions. No "but the LLM thinks it looks good."
        No "small live test." No "confidence score."
        Cold start should never produce BUY, SELL, or PAPER_TRADE_CANDIDATE.
        """
        if sample_size < self.thresholds.min_trades:
            self.cold_start_blocks += 1
            logger.warning(
                f"COLD START BLOCK: hypothesis {hypothesis_id} has "
                f"{sample_size} samples, need {self.thresholds.min_trades}"
            )
            return True  # Cold start is active — block trade-positive outputs
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Return promotion layer statistics."""
        return {
            "total_candidates": self.total_candidates,
            "total_promoted": self.total_promoted,
            "total_failed": self.total_failed,
            "cold_start_blocks": self.cold_start_blocks,
            "active_hypotheses": len(self._records),
            "promotion_rate": self.total_promoted / max(1, self.total_candidates),
        }
