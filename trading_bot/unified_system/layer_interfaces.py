"""
Layer Interfaces - Abstract base classes for all architecture layers

Defines the contract that each layer must implement for proper integration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from .unified_types import (
    LayerStatus,
    LayerMetrics,
    MarketData,
    TradingSignal,
    Order,
    Position,
    RiskMetrics,
    TradingDecision,
    SystemHealth,
)


class ILayer(ABC):
    """Base interface for all architecture layers"""
    
    @property
    @abstractmethod
    def layer_id(self) -> int:
        """Layer number (0-10)"""
        pass
    
    @property
    @abstractmethod
    def layer_name(self) -> str:
        """Human-readable layer name"""
        pass
    
    @property
    @abstractmethod
    def status(self) -> LayerStatus:
        """Current layer status"""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the layer with configuration"""
        pass
    
    @abstractmethod
    async def start(self) -> bool:
        """Start the layer"""
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """Stop the layer gracefully"""
        pass
    
    @abstractmethod
    async def health_check(self) -> LayerMetrics:
        """Perform health check and return metrics"""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[int]:
        """Return list of layer IDs this layer depends on"""
        pass


class IInfrastructureLayer(ILayer):
    """
    Layer 0: Infrastructure & Hardware
    
    Responsibilities:
    - Hardware resource management (CPU, GPU, Memory)
    - Network configuration and optimization
    - Container/Kubernetes orchestration
    - Clock discipline and time synchronization
    """
    
    @property
    def layer_id(self) -> int:
        return 0
    
    @property
    def layer_name(self) -> str:
        return "Infrastructure"
    
    @abstractmethod
    async def get_resource_usage(self) -> Dict[str, float]:
        """Get current resource usage (CPU, memory, GPU)"""
        pass
    
    @abstractmethod
    async def optimize_resources(self) -> bool:
        """Optimize resource allocation"""
        pass
    
    @abstractmethod
    async def get_network_status(self) -> Dict[str, Any]:
        """Get network connectivity status"""
        pass


class IObservabilityLayer(ILayer):
    """
    Layer 1: Observability & Health
    
    Responsibilities:
    - Logging (structured, centralized)
    - Metrics collection and export
    - Distributed tracing
    - Alerting and notifications
    - Health checking and auto-healing
    - Configuration and secrets management
    """
    
    @property
    def layer_id(self) -> int:
        return 1
    
    @property
    def layer_name(self) -> str:
        return "Observability"
    
    @abstractmethod
    async def log(self, level: str, message: str, context: Dict[str, Any]) -> None:
        """Log a message with context"""
        pass
    
    @abstractmethod
    async def record_metric(self, name: str, value: float, tags: Dict[str, str]) -> None:
        """Record a metric"""
        pass
    
    @abstractmethod
    async def create_alert(self, severity: str, message: str, context: Dict[str, Any]) -> None:
        """Create an alert"""
        pass
    
    @abstractmethod
    async def get_system_health(self) -> SystemHealth:
        """Get overall system health"""
        pass


class IConnectivityLayer(ILayer):
    """
    Layer 2: Connectivity & Ingestion
    
    Responsibilities:
    - Exchange WebSocket/REST connectors
    - Failover and reconnection logic
    - Staleness detection
    - Alternative data scrapers/APIs
    - Time synchronization
    - Sequence guarding and deduplication
    """
    
    @property
    def layer_id(self) -> int:
        return 2
    
    @property
    def layer_name(self) -> str:
        return "Connectivity"
    
    @abstractmethod
    async def connect(self, exchange: str, config: Dict[str, Any]) -> bool:
        """Connect to an exchange"""
        pass
    
    @abstractmethod
    async def disconnect(self, exchange: str) -> bool:
        """Disconnect from an exchange"""
        pass
    
    @abstractmethod
    async def subscribe(self, symbol: str, data_type: str, callback: Callable) -> bool:
        """Subscribe to market data"""
        pass
    
    @abstractmethod
    async def get_connection_status(self) -> Dict[str, Any]:
        """Get status of all connections"""
        pass


class IDataFoundationLayer(ILayer):
    """
    Layer 3: Data Foundation & Real-time Intelligence
    
    Responsibilities:
    - Normalized market data
    - Order book reconstruction
    - Alternative/sentiment/macro/on-chain streams
    - Feature stores (real-time + historical)
    - Event enrichment
    - Causal inference features
    """
    
    @property
    def layer_id(self) -> int:
        return 3
    
    @property
    def layer_name(self) -> str:
        return "DataFoundation"
    
    @abstractmethod
    async def get_market_data(self, symbol: str, timeframe: str, limit: int) -> List[MarketData]:
        """Get historical market data"""
        pass
    
    @abstractmethod
    async def get_realtime_data(self, symbol: str) -> Optional[MarketData]:
        """Get latest real-time data"""
        pass
    
    @abstractmethod
    async def get_features(self, symbol: str, feature_set: str) -> Dict[str, float]:
        """Get computed features for a symbol"""
        pass
    
    @abstractmethod
    async def validate_data(self, data: MarketData) -> bool:
        """Validate data quality"""
        pass


class IIntelligenceLayer(ILayer):
    """
    Layer 4: Intelligence Core / Prediction / Feature Core
    
    Responsibilities:
    - Mixture of Experts (MoE)
    - Multi-modal fusion
    - Time-series forecasting (TFT, Informer, N-BEATS)
    - Regime detection and concept drift
    - Market state embedding
    - Order flow / microstructure intelligence
    - Continual / meta / few-shot / transfer learning
    """
    
    @property
    def layer_id(self) -> int:
        return 4
    
    @property
    def layer_name(self) -> str:
        return "Intelligence"
    
    @abstractmethod
    async def predict(self, symbol: str, horizon: int) -> Dict[str, Any]:
        """Generate predictions for a symbol"""
        pass
    
    @abstractmethod
    async def detect_regime(self, symbol: str) -> str:
        """Detect current market regime"""
        pass
    
    @abstractmethod
    async def get_expert_signals(self, symbol: str) -> List[Dict[str, Any]]:
        """Get signals from all experts"""
        pass
    
    @abstractmethod
    async def update_models(self, data: List[MarketData]) -> bool:
        """Update models with new data (online learning)"""
        pass


class ISignalLayer(ILayer):
    """
    Layer 5: Signal Generation & Opportunity Generation
    
    Responsibilities:
    - Multi-strategy / Multi-brain signal engines
    - Regime-conditioned signal blending
    - Opportunity scanners (arbitrage, momentum, liquidity events)
    - Alternative data + sentiment + on-chain signals
    """
    
    @property
    def layer_id(self) -> int:
        return 5
    
    @property
    def layer_name(self) -> str:
        return "SignalGeneration"
    
    @abstractmethod
    async def generate_signals(self, symbol: str, data: MarketData) -> List[TradingSignal]:
        """Generate trading signals for a symbol"""
        pass
    
    @abstractmethod
    async def scan_opportunities(self) -> List[Dict[str, Any]]:
        """Scan for trading opportunities across all symbols"""
        pass
    
    @abstractmethod
    async def blend_signals(self, signals: List[TradingSignal]) -> TradingSignal:
        """Blend multiple signals into a single signal"""
        pass
    
    @abstractmethod
    async def get_active_strategies(self) -> List[str]:
        """Get list of active strategies"""
        pass


class IRiskSafetyLayer(ILayer):
    """
    Layer 6: Risk, Safety & Reality Gate
    
    Responsibilities:
    - Pre-trade checks
    - Position sizing (ML Kelly / adversarial)
    - VaR / CVaR / stress / tail-risk / drawdown control
    - Black swan / flash-crash / liquidity crisis detectors
    - Hard limits (leverage, concentration, monthly growth)
    - Reality gap detection (simulation vs live divergence)
    """
    
    @property
    def layer_id(self) -> int:
        return 6
    
    @property
    def layer_name(self) -> str:
        return "RiskSafety"
    
    @abstractmethod
    async def validate_trade(self, signal: TradingSignal) -> tuple[bool, str]:
        """Validate a trade against risk rules"""
        pass
    
    @abstractmethod
    async def calculate_position_size(self, signal: TradingSignal) -> float:
        """Calculate optimal position size"""
        pass
    
    @abstractmethod
    async def get_risk_metrics(self) -> RiskMetrics:
        """Get current risk metrics"""
        pass
    
    @abstractmethod
    async def check_circuit_breakers(self) -> bool:
        """Check if any circuit breakers are triggered"""
        pass
    
    @abstractmethod
    async def emergency_stop(self) -> bool:
        """Trigger emergency stop"""
        pass


class IDecisionLayer(ILayer):
    """
    Layer 7: Decision Verification System / Multi-Agent Debate
    
    Responsibilities:
    - Planner, Verifier, Critic, Risk Prosecutor, Executor agents
    - Adversarial validation (TradeKiller, Red/Blue team)
    - Conviction / Confidence vector aggregation
    - Final trade ticket + sizing recommendation
    """
    
    @property
    def layer_id(self) -> int:
        return 7
    
    @property
    def layer_name(self) -> str:
        return "DecisionVerification"
    
    @abstractmethod
    async def verify_signal(self, signal: TradingSignal) -> tuple[bool, float, str]:
        """Verify a signal through multi-agent debate"""
        pass
    
    @abstractmethod
    async def generate_decision(self, signal: TradingSignal) -> TradingDecision:
        """Generate final trading decision"""
        pass
    
    @abstractmethod
    async def get_agent_consensus(self, signal: TradingSignal) -> Dict[str, Any]:
        """Get consensus from all agents"""
        pass


class IExecutionLayer(ILayer):
    """
    Layer 8: Execution
    
    Responsibilities:
    - Order routing (smart order router)
    - Fill tracking
    - Slippage control
    - Execution algorithms (TWAP, VWAP, Iceberg, etc.)
    - Code evolver integration
    """
    
    @property
    def layer_id(self) -> int:
        return 8
    
    @property
    def layer_name(self) -> str:
        return "Execution"
    
    @abstractmethod
    async def execute_order(self, order: Order) -> Order:
        """Execute an order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all open positions"""
        pass
    
    @abstractmethod
    async def close_position(self, symbol: str) -> bool:
        """Close a position"""
        pass
    
    @abstractmethod
    async def close_all_positions(self) -> bool:
        """Close all positions (emergency)"""
        pass


class IOrchestrationLayer(ILayer):
    """
    Layer 9: Orchestration & Meta-control
    
    Responsibilities:
    - Master orchestrator
    - Trading session lifecycle
    - Mode / Regime / Season / Risk regime switching
    - Circuit breakers (system-wide + per-strategy)
    - Meta-decision layer (which brains/agents to activate)
    """
    
    @property
    def layer_id(self) -> int:
        return 9
    
    @property
    def layer_name(self) -> str:
        return "Orchestration"
    
    @abstractmethod
    async def process_tick(self, data: MarketData) -> Optional[TradingDecision]:
        """Process a market tick through the full pipeline"""
        pass
    
    @abstractmethod
    async def set_trading_mode(self, mode: str) -> bool:
        """Set the trading mode"""
        pass
    
    @abstractmethod
    async def activate_strategy(self, strategy: str) -> bool:
        """Activate a strategy"""
        pass
    
    @abstractmethod
    async def deactivate_strategy(self, strategy: str) -> bool:
        """Deactivate a strategy"""
        pass
    
    @abstractmethod
    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get active trading sessions"""
        pass


class IGovernanceLayer(ILayer):
    """
    Layer 10: Human / Governance / Audit / Kill-switch
    
    Responsibilities:
    - G0 (Human), G1 (System), G2 (AI agents) hierarchy
    - Approval flows
    - Emergency kill switch
    - Mode change (Sim / Paper / Live / Dry)
    - Audit logging
    - Compliance monitoring
    """
    
    @property
    def layer_id(self) -> int:
        return 10
    
    @property
    def layer_name(self) -> str:
        return "Governance"
    
    @abstractmethod
    async def request_approval(self, action: str, context: Dict[str, Any]) -> tuple[bool, str]:
        """Request approval for an action"""
        pass
    
    @abstractmethod
    async def emergency_shutdown(self) -> bool:
        """Trigger emergency shutdown"""
        pass
    
    @abstractmethod
    async def set_operation_mode(self, mode: str) -> bool:
        """Set operation mode (simulation/paper/live)"""
        pass
    
    @abstractmethod
    async def audit_log(self, action: str, details: Dict[str, Any]) -> None:
        """Log an action for audit"""
        pass
    
    @abstractmethod
    async def get_governance_status(self) -> Dict[str, Any]:
        """Get current governance status"""
        pass
