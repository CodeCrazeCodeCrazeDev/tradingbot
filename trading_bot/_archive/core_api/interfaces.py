"""
AlphaAlgo Core Interfaces - STABLE ABSTRACT INTERFACES

These interfaces are FROZEN and should NEVER change.
All implementations must conform to these interfaces.

Version: 1.0.0 (FROZEN)
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from .types import (
    Tick, OHLCV, OrderBook, Trade, MarketData,
    Signal, SignalType, SignalStrength, SignalConfidence,
    Order, OrderType, OrderSide, ExecutionResult,
    RiskDecision, RiskLevel, PositionSize, RiskMetrics,
    Position, Portfolio, TradeResult,
    TradingMode, HealthStatus,
)


# =============================================================================
# DATA INTERFACES - FROZEN
# =============================================================================

class IDataSource(ABC):
    """
    Data source interface - FROZEN
    
    All data providers must implement this interface.
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to data source"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from data source"""
        pass
    
    @abstractmethod
    async def get_tick(self, symbol: str) -> Optional[Tick]:
        """Get latest tick for symbol"""
        pass
    
    @abstractmethod
    async def get_ohlcv(
        self, 
        symbol: str, 
        timeframe: str, 
        limit: int = 100
    ) -> List[OHLCV]:
        """Get OHLCV candles for symbol"""
        pass
    
    @abstractmethod
    async def get_orderbook(self, symbol: str, depth: int = 10) -> Optional[OrderBook]:
        """Get order book for symbol"""
        pass
    
    @abstractmethod
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        pass
    
    @abstractmethod
    def get_supported_timeframes(self) -> List[str]:
        """Get list of supported timeframes"""
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected"""
        pass


class IDataValidator(ABC):
    """
    Data validator interface - FROZEN
    
    All data validators must implement this interface.
    """
    
    @abstractmethod
    def validate_tick(self, tick: Tick) -> bool:
        """Validate tick data"""
        pass
    
    @abstractmethod
    def validate_ohlcv(self, ohlcv: OHLCV) -> bool:
        """Validate OHLCV data"""
        pass
    
    @abstractmethod
    def validate_orderbook(self, orderbook: OrderBook) -> bool:
        """Validate order book data"""
        pass
    
    @abstractmethod
    def check_staleness(self, timestamp: datetime, max_age_seconds: float) -> bool:
        """Check if data is stale"""
        pass
    
    @abstractmethod
    def detect_anomalies(self, data: MarketData) -> List[str]:
        """Detect anomalies in market data"""
        pass


class IDataStorage(ABC):
    """
    Data storage interface - FROZEN
    
    All data storage implementations must implement this interface.
    """
    
    @abstractmethod
    async def store_tick(self, tick: Tick) -> bool:
        """Store tick data"""
        pass
    
    @abstractmethod
    async def store_ohlcv(self, ohlcv: OHLCV) -> bool:
        """Store OHLCV data"""
        pass
    
    @abstractmethod
    async def get_historical_ticks(
        self, 
        symbol: str, 
        start: datetime, 
        end: datetime
    ) -> List[Tick]:
        """Get historical tick data"""
        pass
    
    @abstractmethod
    async def get_historical_ohlcv(
        self, 
        symbol: str, 
        timeframe: str,
        start: datetime, 
        end: datetime
    ) -> List[OHLCV]:
        """Get historical OHLCV data"""
        pass


class IDataStream(ABC):
    """
    Real-time data stream interface - FROZEN
    
    All streaming data providers must implement this interface.
    """
    
    @abstractmethod
    async def subscribe(self, symbol: str) -> bool:
        """Subscribe to symbol updates"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, symbol: str) -> bool:
        """Unsubscribe from symbol updates"""
        pass
    
    @abstractmethod
    async def stream_ticks(self, symbol: str) -> AsyncIterator[Tick]:
        """Stream tick updates"""
        pass
    
    @abstractmethod
    async def stream_ohlcv(self, symbol: str, timeframe: str) -> AsyncIterator[OHLCV]:
        """Stream OHLCV updates"""
        pass
    
    @abstractmethod
    def add_callback(self, event_type: str, callback: Callable) -> None:
        """Add callback for events"""
        pass


# =============================================================================
# SIGNAL INTERFACES - FROZEN
# =============================================================================

class ISignalGenerator(ABC):
    """
    Signal generator interface - FROZEN
    
    All signal generators must implement this interface.
    """
    
    @abstractmethod
    async def generate(self, market_data: MarketData) -> Optional[Signal]:
        """Generate trading signal from market data"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get generator name"""
        pass
    
    @abstractmethod
    def get_supported_symbols(self) -> List[str]:
        """Get supported symbols"""
        pass
    
    @abstractmethod
    def get_required_data(self) -> Dict[str, Any]:
        """Get required data specifications"""
        pass


class ISignalValidator(ABC):
    """
    Signal validator interface - FROZEN
    
    All signal validators must implement this interface.
    """
    
    @abstractmethod
    def validate(self, signal: Signal, market_data: MarketData) -> bool:
        """Validate signal against market data"""
        pass
    
    @abstractmethod
    def check_expiry(self, signal: Signal) -> bool:
        """Check if signal is expired"""
        pass
    
    @abstractmethod
    def verify_price_levels(self, signal: Signal, current_price: float) -> bool:
        """Verify signal price levels are valid"""
        pass
    
    @abstractmethod
    def get_validation_score(self, signal: Signal) -> float:
        """Get validation score (0-1)"""
        pass


class ISignalAggregator(ABC):
    """
    Signal aggregator interface - FROZEN
    
    All signal aggregators must implement this interface.
    """
    
    @abstractmethod
    def add_signal(self, signal: Signal) -> None:
        """Add signal to aggregator"""
        pass
    
    @abstractmethod
    def aggregate(self) -> Optional[Signal]:
        """Aggregate signals into single signal"""
        pass
    
    @abstractmethod
    def get_consensus(self) -> Dict[str, Any]:
        """Get consensus information"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all signals"""
        pass


# =============================================================================
# RISK INTERFACES - FROZEN
# =============================================================================

class IRiskManager(ABC):
    """
    Risk manager interface - FROZEN
    
    All risk managers must implement this interface.
    """
    
    @abstractmethod
    def check_risk(self, signal: Signal, portfolio: Portfolio) -> RiskDecision:
        """Check if signal passes risk checks"""
        pass
    
    @abstractmethod
    def get_position_size(self, signal: Signal, portfolio: Portfolio) -> PositionSize:
        """Calculate position size for signal"""
        pass
    
    @abstractmethod
    def get_risk_metrics(self, portfolio: Portfolio) -> RiskMetrics:
        """Get current risk metrics"""
        pass
    
    @abstractmethod
    def check_daily_limits(self, portfolio: Portfolio) -> bool:
        """Check if daily limits are breached"""
        pass
    
    @abstractmethod
    def get_max_position_size(self, symbol: str, portfolio: Portfolio) -> float:
        """Get maximum allowed position size"""
        pass


class IPositionSizer(ABC):
    """
    Position sizer interface - FROZEN
    
    All position sizers must implement this interface.
    """
    
    @abstractmethod
    def calculate(
        self, 
        signal: Signal, 
        portfolio: Portfolio,
        risk_per_trade: float
    ) -> PositionSize:
        """Calculate position size"""
        pass
    
    @abstractmethod
    def get_method_name(self) -> str:
        """Get sizing method name"""
        pass


class ICircuitBreaker(ABC):
    """
    Circuit breaker interface - FROZEN
    
    All circuit breakers must implement this interface.
    """
    
    @abstractmethod
    def check(self, portfolio: Portfolio) -> bool:
        """Check if circuit breaker should trigger"""
        pass
    
    @abstractmethod
    def trigger(self, reason: str) -> None:
        """Trigger circuit breaker"""
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset circuit breaker"""
        pass
    
    @property
    @abstractmethod
    def is_triggered(self) -> bool:
        """Check if circuit breaker is triggered"""
        pass
    
    @property
    @abstractmethod
    def trigger_reason(self) -> Optional[str]:
        """Get trigger reason"""
        pass


# =============================================================================
# EXECUTION INTERFACES - FROZEN
# =============================================================================

class IExecutor(ABC):
    """
    Order executor interface - FROZEN
    
    All executors must implement this interface.
    """
    
    @abstractmethod
    async def execute(self, order: Order) -> ExecutionResult:
        """Execute order"""
        pass
    
    @abstractmethod
    async def cancel(self, order_id: str) -> bool:
        """Cancel order"""
        pass
    
    @abstractmethod
    async def modify(self, order_id: str, modifications: Dict[str, Any]) -> bool:
        """Modify order"""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get order status"""
        pass
    
    @abstractmethod
    def get_trading_mode(self) -> TradingMode:
        """Get current trading mode"""
        pass


class IBrokerAdapter(ABC):
    """
    Broker adapter interface - FROZEN
    
    All broker adapters must implement this interface.
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to broker"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from broker"""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get open positions"""
        pass
    
    @abstractmethod
    async def get_orders(self) -> List[Order]:
        """Get open orders"""
        pass
    
    @abstractmethod
    async def place_order(self, order: Order) -> ExecutionResult:
        """Place order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order"""
        pass
    
    @abstractmethod
    async def close_position(self, position_id: str) -> ExecutionResult:
        """Close position"""
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected"""
        pass


class IOrderRouter(ABC):
    """
    Smart order router interface - FROZEN
    
    All order routers must implement this interface.
    """
    
    @abstractmethod
    async def route(self, order: Order) -> str:
        """Route order to best venue"""
        pass
    
    @abstractmethod
    def get_available_venues(self) -> List[str]:
        """Get available venues"""
        pass
    
    @abstractmethod
    def get_venue_status(self, venue: str) -> HealthStatus:
        """Get venue health status"""
        pass


# =============================================================================
# INTELLIGENCE INTERFACES - FROZEN
# =============================================================================

class IPredictor(ABC):
    """
    Price/direction predictor interface - FROZEN
    
    All predictors must implement this interface.
    """
    
    @abstractmethod
    async def predict(self, market_data: MarketData) -> Dict[str, Any]:
        """Make prediction"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get model name"""
        pass
    
    @abstractmethod
    def get_confidence(self) -> float:
        """Get prediction confidence"""
        pass
    
    @abstractmethod
    async def update(self, new_data: MarketData) -> None:
        """Update model with new data"""
        pass


class IRegimeDetector(ABC):
    """
    Market regime detector interface - FROZEN
    
    All regime detectors must implement this interface.
    """
    
    @abstractmethod
    def detect(self, market_data: MarketData) -> str:
        """Detect current market regime"""
        pass
    
    @abstractmethod
    def get_regime_probability(self, regime: str) -> float:
        """Get probability of regime"""
        pass
    
    @abstractmethod
    def get_all_regimes(self) -> List[str]:
        """Get all possible regimes"""
        pass
    
    @abstractmethod
    def get_transition_probability(self, from_regime: str, to_regime: str) -> float:
        """Get regime transition probability"""
        pass


class ISentimentAnalyzer(ABC):
    """
    Sentiment analyzer interface - FROZEN
    
    All sentiment analyzers must implement this interface.
    """
    
    @abstractmethod
    async def analyze(self, symbol: str) -> Dict[str, Any]:
        """Analyze sentiment for symbol"""
        pass
    
    @abstractmethod
    def get_sentiment_score(self, symbol: str) -> float:
        """Get sentiment score (-1 to 1)"""
        pass
    
    @abstractmethod
    def get_sources(self) -> List[str]:
        """Get sentiment sources"""
        pass


# =============================================================================
# EVOLUTION INTERFACES - FROZEN
# =============================================================================

class IRewardModel(ABC):
    """
    Reward model interface - FROZEN
    
    This interface defines how rewards are calculated.
    The implementation should be IMMUTABLE.
    """
    
    @abstractmethod
    def calculate_reward(self, trade_result: TradeResult) -> float:
        """Calculate reward for trade result"""
        pass
    
    @abstractmethod
    def get_objectives(self) -> Dict[str, float]:
        """Get optimization objectives"""
        pass
    
    @abstractmethod
    def get_constraints(self) -> Dict[str, Any]:
        """Get constraints"""
        pass
    
    @abstractmethod
    def is_valid_action(self, action: Dict[str, Any]) -> bool:
        """Check if action is valid"""
        pass


class IEvolutionEngine(ABC):
    """
    Evolution engine interface - FROZEN
    
    All evolution engines must implement this interface.
    """
    
    @abstractmethod
    async def evolve(self) -> Dict[str, Any]:
        """Run evolution cycle"""
        pass
    
    @abstractmethod
    def get_current_fitness(self) -> float:
        """Get current fitness score"""
        pass
    
    @abstractmethod
    def get_evolution_history(self) -> List[Dict[str, Any]]:
        """Get evolution history"""
        pass
    
    @abstractmethod
    def propose_improvement(self) -> Dict[str, Any]:
        """Propose improvement"""
        pass
    
    @abstractmethod
    def apply_improvement(self, improvement: Dict[str, Any]) -> bool:
        """Apply approved improvement"""
        pass


class ILearner(ABC):
    """
    Continuous learner interface - FROZEN
    
    All learners must implement this interface.
    """
    
    @abstractmethod
    async def learn(self, experience: Dict[str, Any]) -> None:
        """Learn from experience"""
        pass
    
    @abstractmethod
    def get_learned_parameters(self) -> Dict[str, Any]:
        """Get learned parameters"""
        pass
    
    @abstractmethod
    def save_state(self, path: str) -> bool:
        """Save learner state"""
        pass
    
    @abstractmethod
    def load_state(self, path: str) -> bool:
        """Load learner state"""
        pass


# =============================================================================
# HUMAN LAYER INTERFACES - FROZEN
# =============================================================================

class IApprovalGate(ABC):
    """
    Human approval gate interface - FROZEN
    
    All approval gates must implement this interface.
    """
    
    @abstractmethod
    async def request_approval(
        self, 
        action: str, 
        details: Dict[str, Any],
        timeout_seconds: float = 3600
    ) -> bool:
        """Request human approval"""
        pass
    
    @abstractmethod
    def is_approval_required(self, action: str) -> bool:
        """Check if approval is required for action"""
        pass
    
    @abstractmethod
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get pending approval requests"""
        pass
    
    @abstractmethod
    def approve(self, request_id: str) -> bool:
        """Approve request"""
        pass
    
    @abstractmethod
    def reject(self, request_id: str, reason: str) -> bool:
        """Reject request"""
        pass


class INotifier(ABC):
    """
    Notification interface - FROZEN
    
    All notifiers must implement this interface.
    """
    
    @abstractmethod
    async def notify(
        self, 
        message: str, 
        level: str = "info",
        channel: Optional[str] = None
    ) -> bool:
        """Send notification"""
        pass
    
    @abstractmethod
    def get_available_channels(self) -> List[str]:
        """Get available notification channels"""
        pass
    
    @abstractmethod
    def set_channel_enabled(self, channel: str, enabled: bool) -> None:
        """Enable/disable notification channel"""
        pass


class IDashboard(ABC):
    """
    Dashboard interface - FROZEN
    
    All dashboards must implement this interface.
    """
    
    @abstractmethod
    async def start(self, host: str = "localhost", port: int = 8080) -> None:
        """Start dashboard server"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop dashboard server"""
        pass
    
    @abstractmethod
    def update_data(self, data: Dict[str, Any]) -> None:
        """Update dashboard data"""
        pass
    
    @abstractmethod
    def get_url(self) -> str:
        """Get dashboard URL"""
        pass
