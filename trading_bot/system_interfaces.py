"""
System Interfaces - Standard interfaces for all subsystems
Defines the contract that all major components must implement
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum


class ComponentStatus(Enum):
    """Status of a system component"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    DEGRADED = "degraded"
    ERROR = "error"
    STOPPED = "stopped"


class SystemLayer(Enum):
    """System architecture layers"""
    INFRASTRUCTURE = 0
    DATA_FOUNDATION = 1
    INTELLIGENCE_CORE = 2
    SIGNAL_GENERATION = 3
    RISK_SAFETY = 4
    EXECUTION = 5
    GOVERNANCE = 6
    ORCHESTRATION = 7


@dataclass
class ComponentHealth:
    """Health status of a component"""
    status: ComponentStatus
    message: str
    metrics: Dict[str, Any]
    last_check: datetime
    errors: List[str]
    warnings: List[str]


@dataclass
class MarketData:
    """Unified market data structure"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TradingSignal:
    """Unified trading signal structure"""
    signal_id: str
    symbol: str
    direction: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    strength: float
    timestamp: datetime
    source: str
    reasoning: str
    metadata: Dict[str, Any]
    risk_score: float
    expected_return: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None


@dataclass
class OrderRequest:
    """Unified order request structure"""
    order_id: str
    symbol: str
    side: str  # 'BUY', 'SELL'
    order_type: str  # 'MARKET', 'LIMIT', 'STOP'
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = 'GTC'
    metadata: Dict[str, Any] = None


@dataclass
class ExecutionResult:
    """Unified execution result structure"""
    order_id: str
    status: str  # 'FILLED', 'PARTIAL', 'REJECTED', 'CANCELLED'
    filled_quantity: float
    average_price: float
    commission: float
    timestamp: datetime
    metadata: Dict[str, Any]


class ISystemComponent(ABC):
    """Base interface for all system components"""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the component"""
        pass
    
    @abstractmethod
    async def start(self) -> bool:
        """Start the component"""
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """Stop the component"""
        pass
    
    @abstractmethod
    async def health_check(self) -> ComponentHealth:
        """Check component health"""
        pass
    
    @abstractmethod
    def get_status(self) -> ComponentStatus:
        """Get current status"""
        pass


class IDataProvider(ISystemComponent):
    """Interface for data providers"""
    
    @abstractmethod
    async def get_market_data(self, symbol: str, timeframe: str) -> List[MarketData]:
        """Get market data"""
        pass
    
    @abstractmethod
    async def subscribe(self, symbol: str, callback) -> bool:
        """Subscribe to real-time data"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, symbol: str) -> bool:
        """Unsubscribe from real-time data"""
        pass


class ISignalGenerator(ISystemComponent):
    """Interface for signal generators"""
    
    @abstractmethod
    async def generate_signal(self, market_data: MarketData) -> Optional[TradingSignal]:
        """Generate trading signal"""
        pass
    
    @abstractmethod
    async def validate_signal(self, signal: TradingSignal) -> bool:
        """Validate a trading signal"""
        pass


class IRiskManager(ISystemComponent):
    """Interface for risk managers"""
    
    @abstractmethod
    async def validate_trade(self, signal: TradingSignal) -> tuple[bool, str]:
        """Validate if trade is allowed"""
        pass
    
    @abstractmethod
    async def calculate_position_size(self, signal: TradingSignal, capital: float) -> float:
        """Calculate position size"""
        pass
    
    @abstractmethod
    async def check_risk_limits(self) -> tuple[bool, List[str]]:
        """Check if risk limits are breached"""
        pass


class IExecutionEngine(ISystemComponent):
    """Interface for execution engines"""
    
    @abstractmethod
    async def execute_order(self, order: OrderRequest) -> ExecutionResult:
        """Execute an order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status"""
        pass


class IIntelligenceEngine(ISystemComponent):
    """Interface for AI/ML intelligence engines"""
    
    @abstractmethod
    async def analyze(self, data: Any) -> Dict[str, Any]:
        """Analyze data and return insights"""
        pass
    
    @abstractmethod
    async def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Make predictions"""
        pass
    
    @abstractmethod
    async def learn(self, experience: Dict[str, Any]) -> bool:
        """Learn from experience"""
        pass


class IGovernanceSystem(ISystemComponent):
    """Interface for governance systems"""
    
    @abstractmethod
    async def request_approval(self, action: str, context: Dict[str, Any]) -> tuple[bool, str]:
        """Request approval for an action"""
        pass
    
    @abstractmethod
    async def audit_log(self, event: str, details: Dict[str, Any]) -> bool:
        """Log audit event"""
        pass
    
    @abstractmethod
    async def check_compliance(self, action: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Check compliance"""
        pass


class IMonitoringSystem(ISystemComponent):
    """Interface for monitoring systems"""
    
    @abstractmethod
    async def record_metric(self, name: str, value: float, tags: Dict[str, str]) -> bool:
        """Record a metric"""
        pass
    
    @abstractmethod
    async def get_metrics(self, name: str, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Get metrics"""
        pass
    
    @abstractmethod
    async def create_alert(self, level: str, message: str, context: Dict[str, Any]) -> bool:
        """Create an alert"""
        pass


class IOrchestrator(ISystemComponent):
    """Interface for orchestrators"""
    
    @abstractmethod
    async def process_market_data(self, data: MarketData) -> Optional[TradingSignal]:
        """Process market data through the entire pipeline"""
        pass
    
    @abstractmethod
    async def execute_signal(self, signal: TradingSignal) -> ExecutionResult:
        """Execute a trading signal"""
        pass
    
    @abstractmethod
    async def get_system_status(self) -> Dict[str, ComponentHealth]:
        """Get status of all components"""
        pass


# Export all interfaces
__all__ = [
    'ComponentStatus',
    'SystemLayer',
    'ComponentHealth',
    'MarketData',
    'TradingSignal',
    'OrderRequest',
    'ExecutionResult',
    'ISystemComponent',
    'IDataProvider',
    'ISignalGenerator',
    'IRiskManager',
    'IExecutionEngine',
    'IIntelligenceEngine',
    'IGovernanceSystem',
    'IMonitoringSystem',
    'IOrchestrator',
]
