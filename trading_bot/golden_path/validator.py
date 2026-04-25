"""Unified decision gate for all AI-generated trade intents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence

from trading_bot.golden_path.agent_trap_defense import AgentTrapDefenseConfig, AgentTrapScanner
from trading_bot.golden_path.types import AccountContext, MarketContext, RiskContext, TradeDecision, TradeIntent


@dataclass(frozen=True)
class DecisionGateConfig:
    """Risk-first configuration for the final trade decision gate."""

    min_confidence: float = 0.62
    min_model_agreement: float = 0.60
    min_model_votes: int = 1
    max_spread_bps: float = 8.0
    max_slippage_bps: float = 5.0
    allowed_regimes: Sequence[str] = ("normal", "trending", "range_bound", "trending_bull", "trending_bear")
    blocked_sessions: Sequence[str] = ("closed", "rollover")
    block_high_impact_news: bool = True
    max_drawdown_pct: float = 0.20
    max_daily_loss_pct: float = 0.05
    max_trades_per_day: int = 8
    max_open_positions: int = 5
    max_correlated_exposure_pct: float = 0.08
    post_loss_cooldown_minutes: float = 30.0
    require_explanation: bool = True
    min_take_profit_rr: float = 1.0
    min_stop_loss_pips: float = 1.0
    max_stop_loss_pips: float = 250.0
    agent_trap_defense: AgentTrapDefenseConfig = field(default_factory=AgentTrapDefenseConfig)


class TradeDecisionValidator:
    """Final approval layer before backtest, paper, or live execution.

    The validator intentionally treats NO_TRADE as the safe default. Strategies
    can be creative upstream; this class is boring on purpose.
    """

    def __init__(self, config: Optional[DecisionGateConfig] = None) -> None:
        self.config = config or DecisionGateConfig()
        self.trap_scanner = AgentTrapScanner(self.config.agent_trap_defense)
        self.history: List[TradeDecision] = []

    def validate(
        self,
        intent: TradeIntent,
        *,
        market: MarketContext,
        risk: RiskContext,
        account: Optional[AccountContext] = None,
    ) -> TradeDecision:
        reasons: List[str] = []

        if intent.direction not in {"buy", "sell", "long", "short"}:
            reasons.append(f"unsupported direction: {intent.direction}")

        if intent.confidence < self.config.min_confidence:
            reasons.append(
                f"confidence {intent.confidence:.2f} below minimum {self.config.min_confidence:.2f}"
            )

        agreement = self._model_agreement(intent)
        if intent.model_votes and len(intent.model_votes) < self.config.min_model_votes:
            reasons.append(
                f"model votes {len(intent.model_votes)} below minimum {self.config.min_model_votes}"
            )
        if intent.model_votes and agreement < self.config.min_model_agreement:
            reasons.append(
                f"model agreement {agreement:.2f} below minimum {self.config.min_model_agreement:.2f}"
            )

        if market.spread_bps > self.config.max_spread_bps:
            reasons.append(
                f"spread {market.spread_bps:.2f} bps exceeds maximum {self.config.max_spread_bps:.2f}"
            )
        if market.slippage_bps > self.config.max_slippage_bps:
            reasons.append(
                f"slippage {market.slippage_bps:.2f} bps exceeds maximum {self.config.max_slippage_bps:.2f}"
            )
        if not market.market_open:
            reasons.append("market is closed")
        if market.regime.lower() not in {regime.lower() for regime in self.config.allowed_regimes}:
            reasons.append(f"market regime blocked: {market.regime}")
        if market.session.lower() in {session.lower() for session in self.config.blocked_sessions}:
            reasons.append(f"session blocked: {market.session}")
        if self.config.block_high_impact_news and market.high_impact_news:
            reasons.append("high-impact news filter active")

        if risk.kill_switch_active:
            reasons.append("kill switch active")
        if risk.model_trading_halted:
            reasons.append("model monitor halted trading")
        if risk.current_drawdown_pct >= self.config.max_drawdown_pct:
            reasons.append(
                f"drawdown {risk.current_drawdown_pct:.2%} exceeds limit {self.config.max_drawdown_pct:.2%}"
            )
        if risk.daily_loss_pct >= self.config.max_daily_loss_pct:
            reasons.append(
                f"daily loss {risk.daily_loss_pct:.2%} exceeds limit {self.config.max_daily_loss_pct:.2%}"
            )
        if risk.trades_today >= self.config.max_trades_per_day:
            reasons.append(f"max trades per day reached: {risk.trades_today}")
        if risk.open_positions >= self.config.max_open_positions:
            reasons.append(f"max open positions reached: {risk.open_positions}")
        if risk.correlated_exposure_pct >= self.config.max_correlated_exposure_pct:
            reasons.append(
                "correlated exposure "
                f"{risk.correlated_exposure_pct:.2%} exceeds limit {self.config.max_correlated_exposure_pct:.2%}"
            )
        if (
            risk.last_trade_was_loss
            and risk.minutes_since_last_loss is not None
            and risk.minutes_since_last_loss < self.config.post_loss_cooldown_minutes
        ):
            reasons.append(
                f"post-loss cooldown active for {self.config.post_loss_cooldown_minutes:.0f} minutes"
            )

        if intent.take_profit_rr < self.config.min_take_profit_rr:
            reasons.append(
                f"risk/reward {intent.take_profit_rr:.2f} below minimum {self.config.min_take_profit_rr:.2f}"
            )
        if intent.stop_loss_pips < self.config.min_stop_loss_pips:
            reasons.append(f"stop loss {intent.stop_loss_pips:.2f} pips too tight")
        if intent.stop_loss_pips > self.config.max_stop_loss_pips:
            reasons.append(f"stop loss {intent.stop_loss_pips:.2f} pips too wide")
        if self.config.require_explanation and not intent.rationale.strip():
            reasons.append("trade explanation is required")

        trap_report = self._scan_for_agent_traps(intent, market)
        if trap_report.blocked:
            reasons.append(f"agent trap defense blocked untrusted content: risk_score={trap_report.risk_score}")

        approved = len(reasons) == 0
        decision = TradeDecision(
            approved=approved,
            action=intent.direction if approved else "no_trade",
            intent=intent,
            reasons=reasons,
            explanation=self._build_explanation(intent, market, risk, reasons),
            risk_multiplier=max(0.0, min(risk.model_risk_multiplier, 1.0)) if approved else 0.0,
            metadata={
                "model_agreement": agreement,
                "spread_bps": market.spread_bps,
                "account_equity": account.equity if account else None,
                "agent_trap_risk_score": trap_report.risk_score,
                "agent_trap_findings": [
                    {
                        "category": finding.category.value,
                        "severity": finding.severity,
                        "source": finding.source,
                        "reason": finding.reason,
                        "evidence": finding.evidence,
                    }
                    for finding in trap_report.findings
                ],
            },
        )
        self.history.append(decision)
        return decision

    def validate_many(
        self,
        intents: Iterable[TradeIntent],
        *,
        market: MarketContext,
        risk: RiskContext,
        account: Optional[AccountContext] = None,
    ) -> List[TradeDecision]:
        return [self.validate(intent, market=market, risk=risk, account=account) for intent in intents]

    def _model_agreement(self, intent: TradeIntent) -> float:
        if not intent.model_votes:
            return 1.0
        normalized = "buy" if intent.direction in {"buy", "long"} else "sell"
        agree = 0
        for vote in intent.model_votes:
            vote_direction = "buy" if vote.direction.lower() in {"buy", "long"} else "sell"
            if vote_direction == normalized:
                agree += 1
        return agree / len(intent.model_votes)

    def _build_explanation(
        self,
        intent: TradeIntent,
        market: MarketContext,
        risk: RiskContext,
        reasons: List[str],
    ) -> str:
        if reasons:
            return "NO_TRADE: " + "; ".join(reasons)

        invalidation = f"invalid if stop loss of {intent.stop_loss_pips:.1f} pips is hit"
        return (
            f"{intent.direction.upper()} {intent.symbol}: {intent.rationale}. "
            f"Expected R/R {intent.take_profit_rr:.2f}; {invalidation}. "
            f"Regime={market.regime}, spread={market.spread_bps:.2f} bps, "
            f"risk multiplier={risk.model_risk_multiplier:.2f}."
        )

    def _scan_for_agent_traps(self, intent: TradeIntent, market: MarketContext):
        texts = [
            ("intent.rationale", intent.rationale),
            ("intent.strategy_name", intent.strategy_name),
        ]
        for idx, vote in enumerate(intent.model_votes):
            texts.append((f"intent.model_votes[{idx}].reason", vote.reason))
        report = self.trap_scanner.scan_texts(texts)
        metadata_report = self.trap_scanner.scan_mapping(
            {
                "intent_metadata": intent.metadata,
                "market_metadata": market.metadata,
            },
            source_prefix="trade_context",
        )
        findings = report.findings + metadata_report.findings
        risk_score = min(report.risk_score + metadata_report.risk_score, 100)
        blocked = report.blocked or metadata_report.blocked
        return type(report)(blocked=blocked, risk_score=risk_score, findings=findings)
