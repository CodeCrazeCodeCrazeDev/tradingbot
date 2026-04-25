"""Shared backtest/paper/live runner for backtest-live parity."""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Iterable, List, Optional, Protocol

from trading_bot.golden_path.types import AccountContext, MarketContext, RiskContext, TradeDecision, TradeIntent
from trading_bot.golden_path.validator import TradeDecisionValidator


class TradingMode(str, Enum):
    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"


class StrategyProtocol(Protocol):
    def analyse(self, bars: Any) -> Iterable[Any]:
        ...


class ExecutorProtocol(Protocol):
    def process(self, signals: List[Any], last_price: float) -> Any:
        ...


class GoldenPathTradingRunner:
    """Runs the same strategy and validation flow in every trading mode."""

    def __init__(
        self,
        *,
        strategy: StrategyProtocol,
        validator: TradeDecisionValidator,
        executor: Optional[ExecutorProtocol] = None,
        mode: TradingMode = TradingMode.PAPER,
        risk_context_provider: Optional[Callable[[], RiskContext]] = None,
        account_context_provider: Optional[Callable[[], AccountContext]] = None,
    ) -> None:
        self.strategy = strategy
        self.validator = validator
        self.executor = executor
        self.mode = TradingMode(mode)
        self.risk_context_provider = risk_context_provider or (lambda: RiskContext())
        self.account_context_provider = account_context_provider or (
            lambda: AccountContext(equity=10_000.0, balance=10_000.0)
        )
        self.decisions: List[TradeDecision] = []

    def run_cycle(self, bars: Any, market: MarketContext) -> List[TradeDecision]:
        """Generate, validate, and optionally execute approved decisions."""

        raw_signals = list(self.strategy.analyse(bars))
        intents = [
            signal if isinstance(signal, TradeIntent) else TradeIntent.from_signal(signal, strategy_name=self.strategy.__class__.__name__)
            for signal in raw_signals
        ]
        risk = self.risk_context_provider()
        account = self.account_context_provider()
        decisions = self.validator.validate_many(intents, market=market, risk=risk, account=account)
        self.decisions.extend(decisions)

        approved = [decision for decision in decisions if decision.approved]
        if self.executor and approved:
            self._execute_approved(raw_signals, approved, market)

        return decisions

    def _execute_approved(
        self,
        raw_signals: List[Any],
        approved: List[TradeDecision],
        market: MarketContext,
    ) -> None:
        approved_keys = {
            (decision.intent.symbol, decision.intent.direction, decision.intent.timestamp)
            for decision in approved
        }
        executable = []
        for raw_signal in raw_signals:
            intent = raw_signal if isinstance(raw_signal, TradeIntent) else TradeIntent.from_signal(raw_signal)
            key = (intent.symbol, intent.direction, intent.timestamp)
            if key in approved_keys:
                executable.append(raw_signal)
        self.executor.process(executable, market.mid_price)
