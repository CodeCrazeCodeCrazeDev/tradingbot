"""Research MVP substrate for auditable AlphaAlgo experiments.

This module intentionally focuses on the unglamorous foundations: clean data,
point-in-time universes, corporate actions, transaction costs, paper trading,
portfolio accounting, experiment lineage, benchmark metadata, and a small
customer-facing reporting/onboarding surface.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import asdict, dataclass, field, is_dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


class DatasetLicenseStatus(str, Enum):
    """Dataset license/compliance states used by the research substrate."""

    PUBLIC = "public"
    LICENSED = "licensed"
    PERMISSIONED = "permissioned"
    INTERNAL_GENERATED = "internal_generated"
    UNKNOWN = "unknown"
    PRIVATE = "private"
    STOLEN = "stolen"
    CONFIDENTIAL = "confidential"
    MATERIAL_NONPUBLIC = "material_nonpublic"


class CorporateActionType(str, Enum):
    """Supported corporate action adjustment types."""

    SPLIT = "split"
    DIVIDEND = "dividend"


class OrderSide(str, Enum):
    """Paper-trading order side."""

    BUY = "buy"
    SELL = "sell"


ALLOWED_DATASET_LICENSES = {
    DatasetLicenseStatus.PUBLIC,
    DatasetLicenseStatus.LICENSED,
    DatasetLicenseStatus.PERMISSIONED,
    DatasetLicenseStatus.INTERNAL_GENERATED,
}


@dataclass(frozen=True)
class MarketBar:
    """Canonical OHLCV bar after schema normalization and validation."""

    symbol: str
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float
    source_id: str
    adjusted: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CleanDataIssue:
    """Rejected input row with an explicit reason."""

    row_index: int
    reason: str
    row: Dict[str, Any]


@dataclass(frozen=True)
class CleanDataReport:
    """Output of the clean data pipeline."""

    bars: List[MarketBar]
    rejected_rows: List[CleanDataIssue]
    warnings: List[str]
    duplicate_count: int
    missing_sessions: List[str]
    lineage_hash: str


@dataclass(frozen=True)
class CorporateAction:
    """Split or cash dividend that can adjust historical bars."""

    symbol: str
    effective_at: float
    action_type: CorporateActionType
    ratio: float = 1.0
    cash_amount: float = 0.0
    source_id: str = "corporate-actions"


@dataclass(frozen=True)
class UniverseMembership:
    """Point-in-time universe membership.

    ``end_at`` is inclusive. A delisted symbol remains available for bars before
    its end date, which prevents survivorship-only research.
    """

    universe_id: str
    symbol: str
    start_at: float
    end_at: Optional[float] = None
    exchange: Optional[str] = None


@dataclass(frozen=True)
class BrokerFeeModel:
    """Broker and exchange fee model used by the paper ledger."""

    per_share_fee: float = 0.0
    per_order_fee: float = 0.0
    fee_bps: float = 0.0
    min_fee: float = 0.0
    exchange_fee_bps: float = 0.0
    exchange_rebate_bps: float = 0.0

    def calculate(self, quantity: float, price: float, liquidity_flag: str = "taker") -> float:
        notional = abs(quantity) * price
        base_fee = abs(quantity) * self.per_share_fee + self.per_order_fee
        bps_fee = notional * self.fee_bps / 10000.0
        exchange_fee = notional * self.exchange_fee_bps / 10000.0
        exchange_rebate = 0.0
        if liquidity_flag.lower() == "maker":
            exchange_rebate = notional * self.exchange_rebate_bps / 10000.0
        total = base_fee + bps_fee + exchange_fee - exchange_rebate
        return max(self.min_fee, round(total, 10))


@dataclass(frozen=True)
class TransactionCostBreakdown:
    """Deterministic estimate of implementation shortfall and broker fees."""

    symbol: str
    side: OrderSide
    quantity: float
    reference_price: float
    notional: float
    spread_cost: float
    slippage_cost: float
    market_impact_cost: float
    broker_fee: float
    total_cost: float
    total_bps: float
    estimated_fill_price: float


class ResearchTransactionCostModel:
    """Small transaction cost model suitable for reproducible MVP research."""

    def __init__(
        self,
        broker_fee_model: Optional[BrokerFeeModel] = None,
        half_spread_bps: float = 1.0,
        slippage_bps: float = 2.0,
        market_impact_coefficient_bps: float = 5.0,
        default_average_daily_volume: float = 1_000_000.0,
    ) -> None:
        self.broker_fee_model = broker_fee_model or BrokerFeeModel()
        self.half_spread_bps = half_spread_bps
        self.slippage_bps = slippage_bps
        self.market_impact_coefficient_bps = market_impact_coefficient_bps
        self.default_average_daily_volume = default_average_daily_volume

    def estimate(
        self,
        symbol: str,
        side: OrderSide | str,
        quantity: float,
        price: float,
        average_daily_volume: Optional[float] = None,
        liquidity_flag: str = "taker",
    ) -> TransactionCostBreakdown:
        side_enum = OrderSide(side)
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if price <= 0:
            raise ValueError("price must be positive")

        notional = abs(quantity) * price
        adv = average_daily_volume or self.default_average_daily_volume
        participation = min(abs(quantity) / max(adv, 1.0), 1.0)
        market_impact_bps = self.market_impact_coefficient_bps * math.sqrt(participation)

        spread_cost = notional * self.half_spread_bps / 10000.0
        slippage_cost = notional * self.slippage_bps / 10000.0
        market_impact_cost = notional * market_impact_bps / 10000.0
        broker_fee = self.broker_fee_model.calculate(quantity, price, liquidity_flag)
        total_cost = spread_cost + slippage_cost + market_impact_cost + broker_fee
        total_bps = 0.0 if notional == 0 else total_cost / notional * 10000.0
        per_share_cost = total_cost / abs(quantity)
        if side_enum == OrderSide.BUY:
            estimated_fill_price = price + per_share_cost
        else:
            estimated_fill_price = max(0.0, price - per_share_cost)

        return TransactionCostBreakdown(
            symbol=symbol.upper(),
            side=side_enum,
            quantity=quantity,
            reference_price=price,
            notional=notional,
            spread_cost=spread_cost,
            slippage_cost=slippage_cost,
            market_impact_cost=market_impact_cost,
            broker_fee=broker_fee,
            total_cost=total_cost,
            total_bps=total_bps,
            estimated_fill_price=estimated_fill_price,
        )


@dataclass(frozen=True)
class PaperOrder:
    """Order intent consumed by the paper ledger."""

    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PaperFill:
    """Executed paper-trading fill with cost evidence."""

    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    timestamp: float
    reference_price: float
    fill_price: float
    cost: TransactionCostBreakdown
    cash_after: float
    realized_pnl: float = 0.0


@dataclass
class PaperPosition:
    """Mutable paper position state."""

    symbol: str
    quantity: float = 0.0
    average_cost: float = 0.0
    realized_pnl: float = 0.0


@dataclass(frozen=True)
class PortfolioSnapshot:
    """Portfolio mark-to-market state at a point in time."""

    timestamp: float
    cash: float
    positions: Dict[str, float]
    market_value: float
    gross_exposure: float
    net_liquidation_value: float
    unrealized_pnl: float
    realized_pnl: float
    returns: float
    max_drawdown: float


class CleanDataPipeline:
    """Normalize, validate, sort, deduplicate, and lineage-hash OHLCV rows."""

    FIELD_ALIASES = {
        "symbol": ("symbol", "ticker", "asset"),
        "timestamp": ("timestamp", "datetime", "date", "time"),
        "open": ("open", "o"),
        "high": ("high", "h"),
        "low": ("low", "l"),
        "close": ("close", "c", "price"),
        "volume": ("volume", "vol", "v"),
        "source_id": ("source_id", "source", "vendor"),
    }

    def __init__(self, expected_interval_seconds: float = 86400.0, gap_factor: float = 1.5) -> None:
        self.expected_interval_seconds = expected_interval_seconds
        self.gap_factor = gap_factor

    def normalize(self, raw_rows: Iterable[Mapping[str, Any]]) -> CleanDataReport:
        accepted: List[MarketBar] = []
        rejected: List[CleanDataIssue] = []
        duplicate_count = 0
        seen: set[Tuple[str, float]] = set()

        for index, raw_row in enumerate(raw_rows):
            row = dict(raw_row)
            try:
                bar = self._row_to_bar(row)
                self._validate_bar(bar)
            except Exception as exc:
                rejected.append(CleanDataIssue(index, str(exc), row))
                continue

            key = (bar.symbol, bar.timestamp)
            if key in seen:
                duplicate_count += 1
                continue
            seen.add(key)
            accepted.append(bar)

        bars = sorted(accepted, key=lambda item: (item.symbol, item.timestamp))
        missing_sessions = self._find_missing_sessions(bars)
        warnings: List[str] = []
        if rejected:
            warnings.append(f"{len(rejected)} rows rejected during cleaning")
        if duplicate_count:
            warnings.append(f"{duplicate_count} duplicate rows removed")
        warnings.extend(missing_sessions)

        lineage_hash = hash_market_bars(bars)
        return CleanDataReport(
            bars=bars,
            rejected_rows=rejected,
            warnings=warnings,
            duplicate_count=duplicate_count,
            missing_sessions=missing_sessions,
            lineage_hash=lineage_hash,
        )

    def _row_to_bar(self, row: Mapping[str, Any]) -> MarketBar:
        normalized = {str(key).strip().lower(): value for key, value in row.items()}
        values: Dict[str, Any] = {}
        for canonical, aliases in self.FIELD_ALIASES.items():
            for alias in aliases:
                if alias in normalized:
                    values[canonical] = normalized[alias]
                    break

        missing = [field for field in ("symbol", "timestamp", "open", "high", "low", "close", "volume") if field not in values]
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")

        symbol = str(values["symbol"]).strip().upper()
        timestamp = _parse_timestamp(values["timestamp"])
        source_id = str(values.get("source_id") or "unknown").strip() or "unknown"
        return MarketBar(
            symbol=symbol,
            timestamp=timestamp,
            open=float(values["open"]),
            high=float(values["high"]),
            low=float(values["low"]),
            close=float(values["close"]),
            volume=float(values["volume"]),
            source_id=source_id,
        )

    @staticmethod
    def _validate_bar(bar: MarketBar) -> None:
        if not bar.symbol:
            raise ValueError("symbol is required")
        if min(bar.open, bar.high, bar.low, bar.close) <= 0:
            raise ValueError("OHLC prices must be positive")
        if bar.volume < 0:
            raise ValueError("volume must be non-negative")
        if bar.high < max(bar.open, bar.low, bar.close):
            raise ValueError("high is lower than open/low/close")
        if bar.low > min(bar.open, bar.high, bar.close):
            raise ValueError("low is higher than open/high/close")

    def _find_missing_sessions(self, bars: Sequence[MarketBar]) -> List[str]:
        by_symbol: Dict[str, List[MarketBar]] = {}
        for bar in bars:
            by_symbol.setdefault(bar.symbol, []).append(bar)

        gaps: List[str] = []
        threshold = self.expected_interval_seconds * self.gap_factor
        for symbol, symbol_bars in by_symbol.items():
            ordered = sorted(symbol_bars, key=lambda item: item.timestamp)
            for previous, current in zip(ordered, ordered[1:]):
                if current.timestamp - previous.timestamp > threshold:
                    gaps.append(f"{symbol} missing session between {previous.timestamp:.0f} and {current.timestamp:.0f}")
        return gaps


class CorporateActionsHandler:
    """Apply simple backward adjustments for splits and cash dividends."""

    def apply(self, bars: Sequence[MarketBar], actions: Sequence[CorporateAction]) -> List[MarketBar]:
        actions_by_symbol: Dict[str, List[CorporateAction]] = {}
        for action in actions:
            actions_by_symbol.setdefault(action.symbol.upper(), []).append(action)

        adjusted: List[MarketBar] = []
        for bar in bars:
            current = bar
            for action in sorted(actions_by_symbol.get(bar.symbol, []), key=lambda item: item.effective_at):
                if current.timestamp < action.effective_at:
                    current = self._apply_action(current, action)
            adjusted.append(current)
        return sorted(adjusted, key=lambda item: (item.symbol, item.timestamp))

    @staticmethod
    def _apply_action(bar: MarketBar, action: CorporateAction) -> MarketBar:
        action_type = CorporateActionType(action.action_type)
        metadata = dict(bar.metadata)
        applied = list(metadata.get("corporate_actions_applied", []))
        applied.append(
            {
                "type": action_type.value,
                "effective_at": action.effective_at,
                "source_id": action.source_id,
            }
        )
        metadata["corporate_actions_applied"] = applied

        if action_type == CorporateActionType.SPLIT:
            if action.ratio <= 0:
                raise ValueError("split ratio must be positive")
            return replace(
                bar,
                open=bar.open / action.ratio,
                high=bar.high / action.ratio,
                low=bar.low / action.ratio,
                close=bar.close / action.ratio,
                volume=bar.volume * action.ratio,
                adjusted=True,
                metadata=metadata,
            )

        if action_type == CorporateActionType.DIVIDEND:
            if action.cash_amount < 0:
                raise ValueError("cash dividend must be non-negative")
            factor = max((bar.close - action.cash_amount) / bar.close, 0.0001)
            return replace(
                bar,
                open=bar.open * factor,
                high=bar.high * factor,
                low=bar.low * factor,
                close=bar.close * factor,
                adjusted=True,
                metadata=metadata,
            )

        raise ValueError(f"unsupported corporate action: {action_type}")


class SurvivorshipFreeUniverse:
    """Point-in-time universe filter that keeps delisted names before delist."""

    def __init__(self, memberships: Sequence[UniverseMembership]) -> None:
        self.memberships = [
            replace(membership, symbol=membership.symbol.upper()) for membership in memberships
        ]

    def active_symbols(self, universe_id: str, timestamp: float) -> List[str]:
        symbols = {
            membership.symbol
            for membership in self.memberships
            if membership.universe_id == universe_id and self._is_active(membership, timestamp)
        }
        return sorted(symbols)

    def filter_bars(self, universe_id: str, bars: Sequence[MarketBar]) -> List[MarketBar]:
        return [
            bar
            for bar in sorted(bars, key=lambda item: (item.symbol, item.timestamp))
            if bar.symbol in self.active_symbols(universe_id, bar.timestamp)
        ]

    @staticmethod
    def _is_active(membership: UniverseMembership, timestamp: float) -> bool:
        if timestamp < membership.start_at:
            return False
        if membership.end_at is not None and timestamp > membership.end_at:
            return False
        return True


class PaperTradingLedger:
    """Deterministic paper-trading ledger with cash, fills, positions, and PnL."""

    def __init__(
        self,
        starting_cash: float,
        cost_model: Optional[ResearchTransactionCostModel] = None,
    ) -> None:
        if starting_cash <= 0:
            raise ValueError("starting_cash must be positive")
        self.starting_cash = starting_cash
        self.cash = starting_cash
        self.cost_model = cost_model or ResearchTransactionCostModel()
        self.positions: Dict[str, PaperPosition] = {}
        self.fills: List[PaperFill] = []
        self.rejected_orders: List[str] = []

    def execute_order(
        self,
        order: PaperOrder,
        bar: MarketBar,
        average_daily_volume: Optional[float] = None,
    ) -> Optional[PaperFill]:
        symbol = order.symbol.upper()
        if symbol != bar.symbol:
            raise ValueError("order symbol must match execution bar symbol")
        if order.quantity <= 0:
            self.rejected_orders.append(f"{order.order_id}: quantity must be positive")
            return None
        side = OrderSide(order.side)

        cost = self.cost_model.estimate(
            symbol=symbol,
            side=side,
            quantity=order.quantity,
            price=bar.close,
            average_daily_volume=average_daily_volume,
        )
        position = self.positions.setdefault(symbol, PaperPosition(symbol=symbol))

        if side == OrderSide.BUY:
            cash_required = order.quantity * bar.close + cost.total_cost
            if cash_required > self.cash:
                self.rejected_orders.append(f"{order.order_id}: insufficient cash")
                return None
            previous_cost_basis = position.quantity * position.average_cost
            new_quantity = position.quantity + order.quantity
            position.average_cost = (previous_cost_basis + cash_required) / new_quantity
            position.quantity = new_quantity
            self.cash -= cash_required
            realized_pnl = 0.0
            fill_price = cash_required / order.quantity
        else:
            if order.quantity > position.quantity:
                self.rejected_orders.append(f"{order.order_id}: insufficient position")
                return None
            proceeds = order.quantity * bar.close - cost.total_cost
            realized_pnl = proceeds - order.quantity * position.average_cost
            position.quantity -= order.quantity
            position.realized_pnl += realized_pnl
            if position.quantity == 0:
                position.average_cost = 0.0
            self.cash += proceeds
            fill_price = proceeds / order.quantity

        fill = PaperFill(
            order_id=order.order_id,
            symbol=symbol,
            side=side,
            quantity=order.quantity,
            timestamp=bar.timestamp,
            reference_price=bar.close,
            fill_price=fill_price,
            cost=cost,
            cash_after=self.cash,
            realized_pnl=realized_pnl,
        )
        self.fills.append(fill)
        return fill

    def snapshot(self, timestamp: float, prices: Mapping[str, float]) -> PortfolioSnapshot:
        return PortfolioAccounting.mark_to_market(
            cash=self.cash,
            positions=self.positions,
            prices=prices,
            timestamp=timestamp,
            starting_cash=self.starting_cash,
        )


class PortfolioAccounting:
    """Mark-to-market and performance calculations for paper portfolios."""

    @staticmethod
    def mark_to_market(
        cash: float,
        positions: Mapping[str, PaperPosition],
        prices: Mapping[str, float],
        timestamp: float,
        starting_cash: float,
        previous_equity_curve: Optional[Sequence[float]] = None,
    ) -> PortfolioSnapshot:
        market_value = 0.0
        gross_exposure = 0.0
        unrealized_pnl = 0.0
        realized_pnl = 0.0
        quantities: Dict[str, float] = {}

        for symbol, position in positions.items():
            if position.quantity == 0:
                continue
            price = prices.get(symbol)
            if price is None:
                continue
            value = position.quantity * price
            market_value += value
            gross_exposure += abs(value)
            unrealized_pnl += position.quantity * (price - position.average_cost)
            realized_pnl += position.realized_pnl
            quantities[symbol] = position.quantity

        equity = cash + market_value
        returns = 0.0 if starting_cash == 0 else equity / starting_cash - 1.0
        equity_curve = list(previous_equity_curve or []) + [equity]
        peak = max(equity_curve) if equity_curve else equity
        drawdowns = [0.0 if running_peak == 0 else equity_value / running_peak - 1.0 for equity_value, running_peak in _running_peaks(equity_curve)]
        max_drawdown = min(drawdowns) if drawdowns else 0.0

        return PortfolioSnapshot(
            timestamp=timestamp,
            cash=cash,
            positions=quantities,
            market_value=market_value,
            gross_exposure=gross_exposure,
            net_liquidation_value=equity,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=realized_pnl,
            returns=returns,
            max_drawdown=max_drawdown,
        )


@dataclass(frozen=True)
class ExperimentRecord:
    """Immutable-ish experiment record stored by deterministic ID."""

    experiment_id: str
    name: str
    config: Dict[str, Any]
    data_lineage_hash: str
    code_version: str
    created_at: float
    artifact_hashes: Dict[str, str] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


class ExperimentRegistry:
    """In-memory registry for reproducible research runs."""

    def __init__(self) -> None:
        self.records: Dict[str, ExperimentRecord] = {}

    def make_experiment_id(
        self,
        name: str,
        config: Mapping[str, Any],
        data_lineage_hash: str,
        code_version: str,
    ) -> str:
        return _stable_hash(
            {
                "name": name,
                "config": dict(config),
                "data_lineage_hash": data_lineage_hash,
                "code_version": code_version,
            }
        )

    def record(
        self,
        name: str,
        config: Mapping[str, Any],
        data_lineage_hash: str,
        code_version: str,
        artifact_hashes: Optional[Mapping[str, str]] = None,
        metrics: Optional[Mapping[str, float]] = None,
        tags: Optional[Sequence[str]] = None,
    ) -> ExperimentRecord:
        experiment_id = self.make_experiment_id(name, config, data_lineage_hash, code_version)
        if experiment_id in self.records:
            return self.records[experiment_id]

        record = ExperimentRecord(
            experiment_id=experiment_id,
            name=name,
            config=dict(config),
            data_lineage_hash=data_lineage_hash,
            code_version=code_version,
            created_at=time.time(),
            artifact_hashes=dict(artifact_hashes or {}),
            metrics=dict(metrics or {}),
            tags=list(tags or []),
        )
        self.records[experiment_id] = record
        return record

    def get(self, experiment_id: str) -> ExperimentRecord:
        return self.records[experiment_id]


@dataclass(frozen=True)
class BenchmarkDataset:
    """Metadata record for real benchmark datasets and their compliance state."""

    dataset_id: str
    name: str
    asset_class: str
    source_uri: str
    license_status: DatasetLicenseStatus
    provenance: List[str]
    timestamp: float
    compliance_score: float
    notes: str = ""


class BenchmarkDatasetRegistry:
    """Registry that refuses private, stolen, unknown, or unprovenanced data."""

    def __init__(self) -> None:
        self.datasets: Dict[str, BenchmarkDataset] = {}

    @classmethod
    def with_default_datasets(cls) -> "BenchmarkDatasetRegistry":
        registry = cls()
        registry.register(
            BenchmarkDataset(
                dataset_id="fred_macro_public",
                name="FRED public macro time series",
                asset_class="macro",
                source_uri="https://fred.stlouisfed.org/",
                license_status=DatasetLicenseStatus.PUBLIC,
                provenance=["public catalog", "timestamped API/file pull", "local content hash"],
                timestamp=0.0,
                compliance_score=0.95,
                notes="Public macro benchmark metadata; caller must comply with source terms.",
            )
        )
        registry.register(
            BenchmarkDataset(
                dataset_id="sec_companyfacts_public",
                name="SEC company facts public filings",
                asset_class="fundamentals",
                source_uri="https://www.sec.gov/dera/data/companyfacts",
                license_status=DatasetLicenseStatus.PUBLIC,
                provenance=["SEC public filing", "accession timestamp", "local content hash"],
                timestamp=0.0,
                compliance_score=0.95,
                notes="Public filings metadata; not a market-data substitute.",
            )
        )
        registry.register(
            BenchmarkDataset(
                dataset_id="user_supplied_point_in_time_equities",
                name="User supplied point-in-time equities feed",
                asset_class="equities",
                source_uri="permissioned://customer/vendor/point-in-time-equities",
                license_status=DatasetLicenseStatus.PERMISSIONED,
                provenance=["customer license attestation", "vendor export timestamp", "local content hash"],
                timestamp=0.0,
                compliance_score=0.90,
                notes="Requires the customer to provide proof of vendor rights.",
            )
        )
        return registry

    def register(self, dataset: BenchmarkDataset) -> BenchmarkDataset:
        dataset = self._normalize_dataset(dataset)
        problems = self._validate(dataset)
        if problems:
            raise ValueError("; ".join(problems))
        self.datasets[dataset.dataset_id] = dataset
        return dataset

    def get(self, dataset_id: str) -> BenchmarkDataset:
        return self.datasets[dataset_id]

    def list(self) -> List[BenchmarkDataset]:
        return [self.datasets[key] for key in sorted(self.datasets)]

    @staticmethod
    def _validate(dataset: BenchmarkDataset) -> List[str]:
        problems: List[str] = []
        license_status = _coerce_dataset_license(dataset.license_status)
        if license_status not in ALLOWED_DATASET_LICENSES:
            problems.append(f"dataset license is not allowed: {license_status.value}")
        if not dataset.provenance:
            problems.append("dataset provenance is required")
        if not dataset.source_uri:
            problems.append("dataset source_uri is required")
        if dataset.compliance_score < 0.80:
            problems.append("dataset compliance_score must be at least 0.80")
        return problems

    @staticmethod
    def _normalize_dataset(dataset: BenchmarkDataset) -> BenchmarkDataset:
        return replace(dataset, license_status=_coerce_dataset_license(dataset.license_status))


@dataclass(frozen=True)
class ResearchRunConfig:
    """Configuration hashed into a reproducible research run ID."""

    experiment_name: str
    strategy_name: str
    starting_cash: float
    benchmark_dataset_id: str
    universe_id: str
    cost_assumptions: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    code_version: str = "local"


@dataclass(frozen=True)
class ResearchRunReport:
    """Evidence bundle produced by the reproducible research runner."""

    run_id: str
    experiment: ExperimentRecord
    data_lineage_hash: str
    fills: List[PaperFill]
    final_snapshot: PortfolioSnapshot
    metrics: Dict[str, float]
    warnings: List[str]


class ReproducibleResearchRunner:
    """Run paper-trading experiments with deterministic lineage and costs."""

    def __init__(
        self,
        experiment_registry: Optional[ExperimentRegistry] = None,
        cost_model: Optional[ResearchTransactionCostModel] = None,
    ) -> None:
        self.experiment_registry = experiment_registry or ExperimentRegistry()
        self.cost_model = cost_model or ResearchTransactionCostModel()

    def run(
        self,
        config: ResearchRunConfig,
        bars: Sequence[MarketBar],
        orders: Sequence[PaperOrder],
        data_quality: Optional[CleanDataReport] = None,
    ) -> ResearchRunReport:
        if config.starting_cash <= 0:
            raise ValueError("starting_cash must be positive")
        ordered_bars = sorted(bars, key=lambda item: (item.timestamp, item.symbol))
        ordered_orders = sorted(orders, key=lambda item: (item.timestamp, item.symbol, item.order_id))
        data_lineage_hash = data_quality.lineage_hash if data_quality else hash_market_bars(ordered_bars)

        ledger = PaperTradingLedger(config.starting_cash, self.cost_model)
        orders_by_key: Dict[Tuple[str, float], List[PaperOrder]] = {}
        for order in ordered_orders:
            orders_by_key.setdefault((order.symbol.upper(), order.timestamp), []).append(order)

        prices: Dict[str, float] = {}
        equity_curve: List[float] = []
        snapshots: List[PortfolioSnapshot] = []
        for bar in ordered_bars:
            prices[bar.symbol] = bar.close
            for order in orders_by_key.get((bar.symbol, bar.timestamp), []):
                ledger.execute_order(order, bar, average_daily_volume=max(bar.volume, 1.0))
            snapshot = PortfolioAccounting.mark_to_market(
                cash=ledger.cash,
                positions=ledger.positions,
                prices=prices,
                timestamp=bar.timestamp,
                starting_cash=config.starting_cash,
                previous_equity_curve=equity_curve,
            )
            equity_curve.append(snapshot.net_liquidation_value)
            snapshots.append(snapshot)

        final_snapshot = snapshots[-1] if snapshots else ledger.snapshot(time.time(), prices)
        metrics = {
            "final_equity": final_snapshot.net_liquidation_value,
            "total_return": final_snapshot.returns,
            "max_drawdown": final_snapshot.max_drawdown,
            "fill_count": float(len(ledger.fills)),
            "rejected_order_count": float(len(ledger.rejected_orders)),
            "total_cost": sum(fill.cost.total_cost for fill in ledger.fills),
        }
        config_payload = _to_jsonable(config)
        experiment = self.experiment_registry.record(
            name=config.experiment_name,
            config=config_payload,
            data_lineage_hash=data_lineage_hash,
            code_version=config.code_version,
            artifact_hashes={"orders": _stable_hash(ordered_orders), "bars": data_lineage_hash},
            metrics=metrics,
            tags=[config.strategy_name, config.benchmark_dataset_id, config.universe_id],
        )

        warnings = list(data_quality.warnings if data_quality else [])
        warnings.extend(ledger.rejected_orders)
        return ResearchRunReport(
            run_id=experiment.experiment_id,
            experiment=experiment,
            data_lineage_hash=data_lineage_hash,
            fills=list(ledger.fills),
            final_snapshot=final_snapshot,
            metrics=metrics,
            warnings=warnings,
        )


class CustomerReportBuilder:
    """Small customer-facing report and JSON payload builder."""

    def build_payload(self, report: ResearchRunReport) -> Dict[str, Any]:
        return {
            "run_id": report.run_id,
            "experiment": _to_jsonable(report.experiment),
            "data_lineage_hash": report.data_lineage_hash,
            "metrics": dict(report.metrics),
            "final_snapshot": _to_jsonable(report.final_snapshot),
            "fills": [_to_jsonable(fill) for fill in report.fills],
            "warnings": list(report.warnings),
            "kill_criteria": [
                "Reject if data lineage cannot be reproduced",
                "Reject if transaction costs are omitted",
                "Reject if paper trading diverges from accounting ledger",
                "Reject if benchmark or universe is not point-in-time",
            ],
        }

    def build_markdown(self, report: ResearchRunReport) -> str:
        payload = self.build_payload(report)
        metrics = payload["metrics"]
        lines = [
            f"# AlphaAlgo Research Report: {report.experiment.name}",
            "",
            f"- Run ID: `{report.run_id}`",
            f"- Data lineage: `{report.data_lineage_hash}`",
            f"- Final equity: `{metrics['final_equity']:.2f}`",
            f"- Total return: `{metrics['total_return']:.4f}`",
            f"- Max drawdown: `{metrics['max_drawdown']:.4f}`",
            f"- Total transaction cost: `{metrics['total_cost']:.4f}`",
            f"- Fill count: `{int(metrics['fill_count'])}`",
            "",
            "## Evidence",
            "",
            "- Clean data lineage is hashed into the experiment ID.",
            "- Broker fees, spread, slippage, and market impact are included.",
            "- Paper-trading fills reconcile to portfolio accounting.",
            "- This report is research evidence, not live deployment approval.",
        ]
        if report.warnings:
            lines.extend(["", "## Warnings", ""])
            lines.extend(f"- {warning}" for warning in report.warnings)
        lines.extend(["", "## Kill Criteria", ""])
        lines.extend(f"- {item}" for item in payload["kill_criteria"])
        return "\n".join(lines)


@dataclass(frozen=True)
class OnboardingRequest:
    """Minimum customer inputs required for a credible research workspace."""

    customer_name: str
    asset_universe: List[str]
    data_sources: List[BenchmarkDataset]
    strategy_description: str
    benchmark_dataset_ids: List[str]
    cost_assumptions: Dict[str, Any]
    risk_limits: Dict[str, Any]
    paper_trading_required: bool = True


@dataclass(frozen=True)
class OnboardingChecklist:
    """Result of the simple onboarding workflow."""

    accepted: bool
    missing_items: List[str]
    rejected_items: List[str]
    next_steps: List[str]
    normalized_config: Dict[str, Any]


class OnboardingWorkflow:
    """Reject hand-wavy onboarding before research claims are made."""

    REQUIRED_COST_FIELDS = ("half_spread_bps", "slippage_bps", "broker_fee_model")
    REQUIRED_RISK_FIELDS = ("max_drawdown", "max_position_size", "kill_switch")

    def evaluate(self, request: OnboardingRequest) -> OnboardingChecklist:
        missing: List[str] = []
        rejected: List[str] = []

        if not request.customer_name.strip():
            missing.append("customer_name")
        if not request.asset_universe:
            missing.append("asset_universe")
        if not request.strategy_description.strip():
            missing.append("strategy_description")
        if not request.benchmark_dataset_ids:
            missing.append("benchmark_dataset_ids")
        for field_name in self.REQUIRED_COST_FIELDS:
            if field_name not in request.cost_assumptions:
                missing.append(f"cost_assumptions.{field_name}")
        for field_name in self.REQUIRED_RISK_FIELDS:
            if field_name not in request.risk_limits:
                missing.append(f"risk_limits.{field_name}")
        if not request.paper_trading_required:
            rejected.append("paper_trading_required must remain true for MVP onboarding")

        for dataset in request.data_sources:
            problems = BenchmarkDatasetRegistry._validate(dataset)
            rejected.extend(f"{dataset.dataset_id}: {problem}" for problem in problems)

        accepted = not missing and not rejected
        next_steps = [
            "load point-in-time benchmark data",
            "run clean data pipeline and corporate action adjustment",
            "run reproducible paper-trading experiment",
            "deliver customer report with lineage, costs, and kill criteria",
        ]
        if not accepted:
            next_steps.insert(0, "fix onboarding gaps before claiming alpha")

        normalized_config = {
            "customer_name": request.customer_name.strip(),
            "asset_universe": sorted({symbol.upper() for symbol in request.asset_universe}),
            "benchmark_dataset_ids": sorted(request.benchmark_dataset_ids),
            "paper_trading_required": request.paper_trading_required,
        }
        return OnboardingChecklist(
            accepted=accepted,
            missing_items=missing,
            rejected_items=rejected,
            next_steps=next_steps,
            normalized_config=normalized_config,
        )


def hash_market_bars(bars: Sequence[MarketBar]) -> str:
    return _stable_hash(sorted(bars, key=lambda item: (item.symbol, item.timestamp)))


def _parse_timestamp(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            raise ValueError("timestamp is required")
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return float(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _coerce_dataset_license(value: DatasetLicenseStatus | str) -> DatasetLicenseStatus:
    try:
        return DatasetLicenseStatus(value)
    except ValueError:
        return DatasetLicenseStatus.UNKNOWN


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(_to_jsonable(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _to_jsonable(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, set):
        return [_to_jsonable(item) for item in sorted(value, key=repr)]
    return value


def _running_peaks(values: Sequence[float]) -> List[Tuple[float, float]]:
    peak = values[0] if values else 0.0
    pairs: List[Tuple[float, float]] = []
    for value in values:
        peak = max(peak, value)
        pairs.append((value, peak))
    return pairs
