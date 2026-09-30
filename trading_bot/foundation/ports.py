"""Dependency-inversion ports for AlphaAlgo bounded contexts."""

from __future__ import annotations

from typing import Any, AsyncIterator, List, Mapping, Optional, Protocol, Sequence, runtime_checkable

from .contracts import (
    ApprovalDecision,
    AuditEvent,
    DecisionProposal,
    ExecutionReport,
    Fill,
    Instrument,
    MarketEvent,
    OrderRequest,
    OrderStatus,
    PortfolioSnapshot,
    Position,
    ReconciliationResult,
    RiskDecision,
    RiskState,
)


@runtime_checkable
class ComponentLifecycle(Protocol):
    async def initialize(self, config: Mapping[str, Any]) -> bool:
        ...

    async def start(self) -> bool:
        ...

    async def stop(self) -> bool:
        ...

    async def health_check(self) -> Mapping[str, Any]:
        ...


@runtime_checkable
class MarketDataAdapter(Protocol):
    async def connect(self) -> None:
        ...

    async def disconnect(self) -> None:
        ...

    async def snapshot(self, instrument: Instrument, timeframe: Optional[str] = None) -> List[MarketEvent]:
        ...

    def stream(self, instruments: Sequence[Instrument]) -> AsyncIterator[MarketEvent]:
        ...


@runtime_checkable
class BrokerAdapter(Protocol):
    venue_id: str

    async def connect(self) -> None:
        ...

    async def disconnect(self) -> None:
        ...

    async def submit_order(self, order: OrderRequest) -> ExecutionReport:
        ...

    async def cancel_order(self, client_order_id: str) -> bool:
        ...

    async def get_order(self, client_order_id: str) -> ExecutionReport:
        ...

    async def get_positions(self) -> List[Position]:
        ...

    async def reconcile(self, portfolio: Optional[PortfolioSnapshot] = None) -> ReconciliationResult:
        ...


@runtime_checkable
class RiskService(Protocol):
    async def evaluate(self, proposal: DecisionProposal, state: RiskState) -> RiskDecision:
        ...

    async def refresh(self, portfolio: PortfolioSnapshot) -> RiskState:
        ...


@runtime_checkable
class StrategyPort(Protocol):
    strategy_id: str

    async def generate_signal(self, market: Mapping[str, Any]) -> Optional[List[Any]]:
        ...


@runtime_checkable
class AgentCapabilityPort(Protocol):
    capability_id: str

    async def analyze(self, context: Mapping[str, Any]) -> Mapping[str, Any]:
        ...


@runtime_checkable
class RiskPolicy(Protocol):
    """Subordinate risk policy; it may veto but never independently approve."""

    name: str

    async def evaluate(self, proposal: DecisionProposal, state: RiskState) -> Mapping[str, Any]:
        ...


@runtime_checkable
class ExecutionService(Protocol):
    async def submit(self, order: OrderRequest) -> ExecutionReport:
        ...

    async def cancel(self, client_order_id: str) -> bool:
        ...

    async def status(self, client_order_id: str) -> OrderStatus:
        ...

    async def reconcile(self, portfolio: Optional[PortfolioSnapshot] = None) -> ReconciliationResult:
        ...


@runtime_checkable
class WorldModelPort(Protocol):
    async def simulate(self, state: Mapping[str, Any], horizon: int = 1) -> Mapping[str, Any]:
        ...

    async def intervene(
        self,
        state: Mapping[str, Any],
        intervention: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        ...


@runtime_checkable
class PortfolioRepository(Protocol):
    async def snapshot(self, account_id: str) -> PortfolioSnapshot:
        ...

    async def record_fill(self, fill: Fill) -> None:
        ...

    async def record_audit_event(self, event: AuditEvent) -> str:
        ...


@runtime_checkable
class TradingRepository(PortfolioRepository, Protocol):
    async def record_order(self, order: OrderRequest, status: OrderStatus = OrderStatus.CREATED) -> None:
        ...

    async def record_execution(self, order: OrderRequest, report: ExecutionReport) -> None:
        ...

    async def reconcile(
        self,
        expected: PortfolioSnapshot,
        venue: str = "repository",
    ) -> ReconciliationResult:
        ...


@runtime_checkable
class GovernanceGate(Protocol):
    async def authorize(
        self,
        action: str,
        payload: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> ApprovalDecision:
        ...


@runtime_checkable
class CredentialProviderPort(Protocol):
    """Canonical secret/credential resolution boundary.

    Modules needing secrets must resolve through this port; no component may
    read environment variables or secret stores directly outside a declared
    credential-provider boundary. Resolution failure must fail closed
    (return ``None`` or raise), never fabricate a secret.
    """

    def get_secret(self, name: str) -> Optional[str]:
        ...

    def require_secret(self, name: str) -> str:
        ...
