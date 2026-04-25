# Schema Contracts and API Documentation

This document provides comprehensive documentation for the schema contracts and APIs used in the trading bot system, with a focus on testing, validation, and performance optimization.

## Table of Contents

1. [Schema Contracts](#schema-contracts)
   - [Market Data Schemas](#market-data-schemas)
   - [Trading Schemas](#trading-schemas)
   - [Validation Schemas](#validation-schemas)
2. [API Contracts](#api-contracts)
   - [Opportunity Scanner API](#opportunity-scanner-api)
   - [Orchestrator API](#orchestrator-api)
   - [Execution Engine API](#execution-engine-api)
   - [Risk Manager API](#risk-manager-api)
3. [Database Interfaces](#database-interfaces)
   - [Robust Database Manager](#robust-database-manager)
   - [Shared Memory Manager](#shared-memory-manager)
4. [Testing Framework](#testing-framework)
   - [End-to-End Testing](#end-to-end-testing)
   - [Synthetic Data Generation](#synthetic-data-generation)
   - [Test Reporting](#test-reporting)
5. [Performance Monitoring](#performance-monitoring)
   - [Performance Tracker](#performance-tracker)
   - [Latency Budget Tracker](#latency-budget-tracker)
6. [Parallel Processing](#parallel-processing)
   - [Parallel Scanner](#parallel-scanner)

## Schema Contracts

### Market Data Schemas

The system uses Pydantic models to enforce schema validation for all market data:

#### MarketTick

Represents a single market tick with price and volume information.

```python
class MarketTick(BaseModel):
    timestamp: datetime
    symbol: str
    price: float
    volume: float = 0.0
    bid: Optional[float] = None
    ask: Optional[float] = None
    direction: Optional[str] = None  # "buy" or "sell"
    source: Optional[str] = None
```

#### OHLCBar

Represents an OHLC (Open, High, Low, Close) bar for a specific timeframe.

```python
class OHLCBar(BaseModel):
    timestamp: datetime
    symbol: str
    timeframe: TimeFrame
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    tick_count: Optional[int] = None
```

#### OrderBook

Represents the current state of the order book with bids and asks.

```python
class OrderBook(BaseModel):
    timestamp: datetime
    symbol: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
```

#### OrderFlowSnapshot

Represents a snapshot of order flow analysis.

```python
class OrderFlowSnapshot(BaseModel):
    timestamp: datetime
    symbol: str
    delta: float  # Buy volume - sell volume
    imbalance: float  # Ratio of buy/sell
    absorption: Optional[float] = None
    exhaustion: Optional[float] = None
    large_orders: Optional[List[Dict[str, Any]]] = None
```

### Trading Schemas

#### TradingOpportunity

Represents a trading opportunity detected by scanners.

```python
class TradingOpportunity(BaseModel):
    id: str
    timestamp: datetime
    symbol: str
    type: OpportunityType
    direction: Direction
    confidence: float
    expected_return: float
    risk_score: float
    timeframe: TimeFrame
    entry_price: float
    stop_loss: float
    take_profit: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

#### TradingDecision

Represents a decision to trade based on one or more opportunities.

```python
class TradingDecision(BaseModel):
    decision_id: str
    timestamp: datetime
    opportunity_ids: List[str]
    action: str  # BUY/SELL/HOLD
    symbols: List[str]
    allocation: Dict[str, float]
    risk_score: float
    expected_return: float
    confidence: float
    execution_plan: ExecutionPlan
    metadata: Dict[str, Any]
```

#### ExecutionResult

Represents the result of executing an order.

```python
class ExecutionResult(BaseModel):
    order_id: str
    success: bool
    executed_price: float
    executed_quantity: float
    slippage: float
    execution_time: float
    fees: float
    venue: str
    metadata: Dict[str, Any]
```

#### Trade

Represents a complete trade with lifecycle information.

```python
class Trade(BaseModel):
    trade_id: str
    decision_id: str
    opportunity_ids: List[str]
    symbol: str
    direction: Direction
    entry_price: float
    current_price: Optional[float] = None
    stop_loss: float
    take_profit: float
    size: float
    status: TradeStatus
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[ExitReason] = None
    pnl: Optional[float] = None
    execution_details: Dict[str, Any]
    metadata: Dict[str, Any]
```

### Validation Schemas

#### ValidationResult

Represents the result of a validation check.

```python
class ValidationResult(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

#### TestCase

Defines a test case for system components.

```python
class TestCase(BaseModel):
    test_id: str
    name: str
    description: str
    component: str
    inputs: Dict[str, Any]
    expected_outputs: Dict[str, Any]
    timeout_seconds: float = 10.0
    tags: List[str] = Field(default_factory=list)
    enabled: bool = True
```

#### TestResult

Represents the result of a test execution.

```python
class TestResult(BaseModel):
    test_id: str
    success: bool
    execution_time: float
    actual_outputs: Dict[str, Any]
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    timestamp: datetime
```

## API Contracts

### Opportunity Scanner API

The Opportunity Scanner API is responsible for detecting trading opportunities in market data.

#### UnifiedScanner

```python
class UnifiedScanner:
    async def initialize(self, market_stream, data_processor, microstructure, order_flow):
        """Initialize scanner with data pipeline components"""
        
    async def scan_opportunities(self, symbol: str, market_data: Dict[str, Any]) -> List[OpportunityData]:
        """Scan for opportunities based on market data"""
        
    def get_opportunity_metrics(self) -> Dict[str, Any]:
        """Get opportunity scanning metrics"""
```

#### ParallelScanner

```python
class ParallelScanner:
    async def initialize(self, *args, **kwargs):
        """Initialize the base scanner and all registered scanners"""
        
    def register_scanner(self, name: str, scanner: Any, config: Optional[Dict[str, Any]] = None):
        """Register a scanner for parallel execution"""
        
    async def scan_opportunities(self, symbol: str, market_data: Dict[str, Any]) -> List[OpportunityData]:
        """Scan for opportunities using parallel processing"""
        
    def get_opportunity_metrics(self) -> Dict[str, Any]:
        """Get opportunity scanning metrics"""
```

### Orchestrator API

The Orchestrator API coordinates trading decisions and execution.

#### MasterOrchestrator

```python
class MasterOrchestrator:
    async def orchestrate_trading(self, market_data: Dict) -> List[TradingDecision]:
        """Main orchestration logic that coordinates all systems"""
        
    async def execute_decisions(self):
        """Execute queued trading decisions"""
        
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        
    def adjust_trading_mode(self, market_conditions: Dict):
        """Dynamically adjust trading mode based on market conditions"""
```

### Execution Engine API

The Execution Engine API handles order execution with various algorithms.

#### ExecutionEngine

```python
class ExecutionEngine:
    async def execute(self, decision: TradingDecision) -> ExecutionResult:
        """Execute a trading decision using optimal strategy"""
        
    async def execute_order(self, order: Dict) -> Dict:
        """Execute a specific order"""
```

### Risk Manager API

The Risk Manager API handles risk assessment and management.

#### RiskManager

```python
class RiskManager:
    async def assess_portfolio_risk(self, positions: Dict, market_data: Dict) -> RiskMetrics:
        """Comprehensive portfolio risk assessment"""
        
    async def validate_trade(self, trade: Dict) -> Tuple[bool, str]:
        """Validate if trade fits within risk limits"""
        
    def calculate_optimal_hedge(self, positions: Dict, market_data: Dict) -> Dict:
        """Calculate optimal hedge for portfolio"""
```

## Database Interfaces

### Robust Database Manager

```python
class RobustDatabaseManager:
    async def initialize(self):
        """Initialize database connections with fallbacks"""
        
    async def write_market_data(self, data: Union[Dict, pd.DataFrame], symbol: str, timeframe: str):
        """Write market data with caching and fallbacks"""
        
    async def get_market_data(self, symbol: str, timeframe: str, start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None, limit: Optional[int] = None) -> pd.DataFrame:
        """Get market data with caching and fallbacks"""
        
    async def write_trade(self, trade_data: Dict[str, Any]) -> bool:
        """Write trade data to database"""
        
    async def get_trades(self, symbol: Optional[str] = None, status: Optional[str] = None,
                       start_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
                       limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get trades with filtering"""
```

### Shared Memory Manager

```python
class SharedMemoryManager:
    def put(self, data: Any, obj_id: Optional[str] = None) -> str:
        """Store an object in shared memory"""
        
    def get(self, obj_id: str) -> Any:
        """Retrieve an object from shared memory"""
        
    def get_dataframe(self, obj_id: str) -> pd.DataFrame:
        """Retrieve a DataFrame from shared memory"""
        
    def exists(self, obj_id: str) -> bool:
        """Check if an object exists in shared memory"""
        
    def delete(self, obj_id: str) -> bool:
        """Delete an object from shared memory"""
```

## Testing Framework

### End-to-End Testing

```python
class EndToEndTest:
    async def setup(self):
        """Set up test environment"""
        
    async def run(self):
        """Run the test"""
        
    async def execute(self):
        """Execute the test (to be implemented by subclasses)"""
        
    async def teardown(self):
        """Clean up after test"""
        
    def get_result(self) -> TestResult:
        """Get test result"""
        
    def save_report(self):
        """Save test report to file"""
```

### Synthetic Data Generation

```python
class SyntheticDataGenerator:
    def generate_tick(self, timestamp: Optional[datetime] = None) -> MarketTick:
        """Generate a single market tick"""
        
    def generate_ticks(self, count: int, start_time: Optional[datetime] = None,
                     interval_seconds: float = 1.0) -> List[MarketTick]:
        """Generate multiple market ticks"""
        
    def generate_ohlc_bars(self, count: int, timeframe: TimeFrame,
                         start_time: Optional[datetime] = None) -> List[OHLCBar]:
        """Generate OHLC bars"""
        
    def generate_market_data(self, symbol: str = "SYNTHETIC", days: int = 30,
                           timeframes: List[TimeFrame] = None) -> Dict[TimeFrame, pd.DataFrame]:
        """Generate comprehensive market data for multiple timeframes"""
```

### Test Reporting

```python
class ReportGenerator:
    def generate_report(self, test_report: TestReport) -> str:
        """Generate a comprehensive HTML report"""
```

## Performance Monitoring

### Performance Tracker

```python
class PerformanceTracker:
    def get_latency_tracker(self, component: str) -> LatencyTracker:
        """Get or create a latency tracker for a component"""
        
    def get_throughput_tracker(self, component: str) -> ThroughputTracker:
        """Get or create a throughput tracker for a component"""
        
    def track_latency(self, component: str):
        """Decorator to track function latency"""
        
    def track_throughput(self, component: str):
        """Decorator to track function throughput"""
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
```

### Latency Budget Tracker

```python
class LatencyBudgetTracker:
    def start_trace(self, path: str) -> str:
        """Start tracing a critical path"""
        
    def start_component(self, trace_id: str, component: str) -> bool:
        """Start timing a component within a trace"""
        
    def end_component(self, trace_id: str) -> bool:
        """End timing the current component within a trace"""
        
    def end_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """End a trace and get results"""
        
    def trace_path(self, path: str):
        """Decorator to trace a critical path"""
        
    def trace_component(self, component: str):
        """Decorator to trace a component within a critical path"""
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get latency budget metrics"""
```

## Parallel Processing

### Parallel Scanner

```python
class ParallelScanner:
    async def initialize(self, *args, **kwargs):
        """Initialize the base scanner and all registered scanners"""
        
    def register_scanner(self, name: str, scanner: Any, config: Optional[Dict[str, Any]] = None):
        """Register a scanner for parallel execution"""
        
    async def scan_opportunities(self, symbol: str, market_data: Dict[str, Any]) -> List[OpportunityData]:
        """Scan for opportunities using parallel processing"""
        
    async def _scan_with_process_pool(self, symbol: str, market_data: Dict[str, Any]) -> List[OpportunityData]:
        """Scan using process pool for maximum CPU utilization"""
        
    async def _scan_with_thread_pool(self, symbol: str, market_data: Dict[str, Any]) -> List[OpportunityData]:
        """Scan using thread pool for I/O-bound scanners"""
        
    async def _scan_with_asyncio(self, symbol: str, market_data: Dict[str, Any]) -> List[OpportunityData]:
        """Scan using asyncio for concurrent execution"""
        
    async def _scan_adaptive(self, symbol: str, market_data: Dict[str, Any]) -> List[OpportunityData]:
        """Adaptive scanning strategy based on scanner type"""
```
