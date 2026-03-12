"""
AlphaAlgo V2 Core Interfaces

STABILITY GUARANTEE: These interfaces are FROZEN and will NEVER change.
All components must implement these interfaces to ensure compatibility.

Design Principles:
1. Single Responsibility - Each interface has one clear purpose
2. Interface Segregation - Small, focused interfaces
3. Dependency Inversion - Depend on abstractions, not implementations
4. Liskov Substitution - Any implementation can be swapped
"""

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, List, Optional
import pandas as pd
from datetime import datetime

from .types import (
    Signal,
    Order,
    Position,
    Trade,
    TradeResult,
    MarketData,
    Tick,
    OHLCV,
    RiskDecision,
    ExecutionResult,
    EvolutionProposal,
)


class IDataSource(ABC):
    """
    Data source interface - STABLE API
    
    Provides market data from various sources (MT5, Yahoo, Binance, etc.)
    All data sources must implement this interface.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get data source name"""
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if data source is connected"""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to data source"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from data source"""
        pass
    
    @abstractmethod
    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        bars: int = 100,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get OHLCV (candlestick) data
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD', 'BTCUSDT')
            timeframe: Timeframe (e.g., 'M1', 'M5', 'H1', 'D1')
            bars: Number of bars to fetch
            start: Start datetime (optional)
            end: End datetime (optional)
            
        Returns:
            DataFrame with columns: open, high, low, close, volume, time
        """
        pass
    
    @abstractmethod
    async def get_tick(self, symbol: str) -> Tick:
        """
        Get latest tick data
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Tick with bid, ask, last, volume, time
        """
        pass
    
    @abstractmethod
    async def subscribe(
        self,
        symbol: str,
        callback: Callable[[Tick], Awaitable[None]]
    ) -> str:
        """
        Subscribe to real-time tick updates
        
        Args:
            symbol: Trading symbol
            callback: Async callback function for tick updates
            
        Returns:
            Subscription ID for unsubscribing
        """
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from tick updates
        
        Args:
            subscription_id: ID returned from subscribe()
            
        Returns:
            True if successfully unsubscribed
        """
        pass
    
    @abstractmethod
    async def get_symbols(self) -> List[str]:
        """Get list of available symbols"""
        pass


class ISignalGenerator(ABC):
    """
    Signal generator interface - STABLE API
    
    Generates trading signals from market data.
    All signal generators (technical, ML, sentiment) must implement this.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get signal generator name"""
        pass
    
    @property
    @abstractmethod
    def confidence_threshold(self) -> float:
        """Minimum confidence to generate signal"""
        pass
    
    @abstractmethod
    async def generate(
        self,
        symbol: str,
        data: MarketData,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Signal]:
        """
        Generate trading signal
        
        Args:
            symbol: Trading symbol
            data: Market data (OHLCV, ticks, etc.)
            context: Additional context (regime, sentiment, etc.)
            
        Returns:
            Signal if conditions met, None otherwise
        """
        pass
    
    @abstractmethod
    def get_confidence(self, signal: Signal) -> float:
        """
        Get signal confidence score
        
        Args:
            signal: Generated signal
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        pass
    
    @abstractmethod
    async def validate(self, signal: Signal) -> bool:
        """
        Validate signal before execution
        
        Args:
            signal: Signal to validate
            
        Returns:
            True if signal is valid
        """
        pass


class IRiskManager(ABC):
    """
    Risk manager interface - STABLE API
    
    Manages all risk-related decisions including position sizing,
    risk limits, and trade validation.
    """
    
    @property
    @abstractmethod
    def current_risk(self) -> float:
        """Get current portfolio risk as percentage"""
        pass
    
    @property
    @abstractmethod
    def daily_pnl(self) -> float:
        """Get current daily P&L"""
        pass
    
    @property
    @abstractmethod
    def max_drawdown(self) -> float:
        """Get maximum drawdown"""
        pass
    
    @abstractmethod
    def validate_trade(
        self,
        signal: Signal,
        position_size: float
    ) -> RiskDecision:
        """
        Validate trade against risk limits
        
        Args:
            signal: Trading signal
            position_size: Proposed position size
            
        Returns:
            RiskDecision with allowed/rejected and reason
        """
        pass
    
    @abstractmethod
    def get_position_size(
        self,
        signal: Signal,
        account_balance: float,
        method: str = "kelly"
    ) -> float:
        """
        Calculate optimal position size
        
        Args:
            signal: Trading signal
            account_balance: Current account balance
            method: Sizing method ('kelly', 'fixed', 'volatility')
            
        Returns:
            Position size in lots/units
        """
        pass
    
    @abstractmethod
    def check_limits(self) -> Dict[str, bool]:
        """
        Check all risk limits
        
        Returns:
            Dict with limit name and whether it's breached
        """
        pass
    
    @abstractmethod
    def update_position(self, position: Position) -> None:
        """Update risk calculations with new position"""
        pass
    
    @abstractmethod
    def update_trade(self, trade: Trade) -> None:
        """Update risk calculations with completed trade"""
        pass
    
    @abstractmethod
    def emergency_close_all(self) -> bool:
        """Emergency close all positions"""
        pass


class IExecutor(ABC):
    """
    Order executor interface - STABLE API
    
    Executes orders through broker connections.
    All broker adapters must implement this interface.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get executor/broker name"""
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to broker"""
        pass
    
    @property
    @abstractmethod
    def is_paper_mode(self) -> bool:
        """Check if in paper trading mode"""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to broker"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from broker"""
        pass
    
    @abstractmethod
    async def execute(self, order: Order) -> ExecutionResult:
        """
        Execute order
        
        Args:
            order: Order to execute
            
        Returns:
            ExecutionResult with fill details
        """
        pass
    
    @abstractmethod
    async def cancel(self, order_id: str) -> bool:
        """
        Cancel pending order
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if successfully cancelled
        """
        pass
    
    @abstractmethod
    async def modify(
        self,
        order_id: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> bool:
        """
        Modify existing order
        
        Args:
            order_id: Order ID to modify
            stop_loss: New stop loss price
            take_profit: New take profit price
            
        Returns:
            True if successfully modified
        """
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get current position for symbol"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all open positions"""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information (balance, equity, margin)"""
        pass
    
    @abstractmethod
    async def close_position(
        self,
        symbol: str,
        volume: Optional[float] = None
    ) -> ExecutionResult:
        """
        Close position
        
        Args:
            symbol: Symbol to close
            volume: Volume to close (None = close all)
            
        Returns:
            ExecutionResult with close details
        """
        pass


class IRewardModel(ABC):
    """
    Reward model interface - STABLE API
    
    Defines what "success" means for the trading system.
    The reward function is IMMUTABLE and cannot be modified by evolution.
    """
    
    @abstractmethod
    def calculate_reward(self, trade_result: TradeResult) -> float:
        """
        Calculate reward for a trade
        
        Args:
            trade_result: Result of completed trade
            
        Returns:
            Reward score (higher is better)
        """
        pass
    
    @abstractmethod
    def calculate_portfolio_reward(
        self,
        trades: List[TradeResult],
        period_days: int = 30
    ) -> float:
        """
        Calculate portfolio-level reward
        
        Args:
            trades: List of trade results
            period_days: Evaluation period
            
        Returns:
            Portfolio reward score
        """
        pass
    
    @abstractmethod
    def get_constraints(self) -> Dict[str, float]:
        """
        Get immutable constraints
        
        Returns:
            Dict of constraint name to value
        """
        pass
    
    @abstractmethod
    def check_constraints(self, metrics: Dict[str, float]) -> Dict[str, bool]:
        """
        Check if metrics violate constraints
        
        Args:
            metrics: Current performance metrics
            
        Returns:
            Dict of constraint name to violation status
        """
        pass


class IEvolutionEngine(ABC):
    """
    Evolution engine interface - STABLE API
    
    Enables self-improvement within safety bounds.
    All improvements require validation and (for critical changes) human approval.
    """
    
    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if evolution is enabled"""
        pass
    
    @abstractmethod
    async def analyze(self) -> Dict[str, Any]:
        """
        Analyze system for improvement opportunities
        
        Returns:
            Analysis results with identified issues and opportunities
        """
        pass
    
    @abstractmethod
    async def propose(
        self,
        analysis: Dict[str, Any]
    ) -> List[EvolutionProposal]:
        """
        Generate improvement proposals
        
        Args:
            analysis: Analysis results
            
        Returns:
            List of improvement proposals
        """
        pass
    
    @abstractmethod
    async def validate(self, proposal: EvolutionProposal) -> bool:
        """
        Validate proposal safety
        
        Args:
            proposal: Proposal to validate
            
        Returns:
            True if proposal is safe to deploy
        """
        pass
    
    @abstractmethod
    async def deploy(
        self,
        proposal: EvolutionProposal,
        approved_by: Optional[str] = None
    ) -> bool:
        """
        Deploy approved proposal
        
        Args:
            proposal: Proposal to deploy
            approved_by: Human approver (required for critical changes)
            
        Returns:
            True if successfully deployed
        """
        pass
    
    @abstractmethod
    async def rollback(self, proposal_id: str) -> bool:
        """
        Rollback a deployed proposal
        
        Args:
            proposal_id: ID of proposal to rollback
            
        Returns:
            True if successfully rolled back
        """
        pass
    
    @abstractmethod
    def get_history(self) -> List[EvolutionProposal]:
        """Get history of evolution proposals"""
        pass


class ILearningEngine(ABC):
    """
    Learning engine interface - STABLE API
    
    Handles continuous learning from market feedback.
    """
    
    @abstractmethod
    async def learn_from_trade(self, trade: Trade) -> None:
        """Learn from completed trade"""
        pass
    
    @abstractmethod
    async def learn_from_prediction(
        self,
        prediction: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> None:
        """Learn from prediction vs actual outcome"""
        pass
    
    @abstractmethod
    async def update_models(self) -> Dict[str, bool]:
        """
        Update ML models with new data
        
        Returns:
            Dict of model name to update success
        """
        pass
    
    @abstractmethod
    def get_learning_metrics(self) -> Dict[str, float]:
        """Get learning performance metrics"""
        pass


class IMonitor(ABC):
    """
    Monitoring interface - STABLE API
    
    Provides system health and performance monitoring.
    """
    
    @abstractmethod
    def get_health(self) -> Dict[str, Any]:
        """Get system health status"""
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, float]:
        """Get performance metrics"""
        pass
    
    @abstractmethod
    def log_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        severity: str = "info"
    ) -> None:
        """Log system event"""
        pass
    
    @abstractmethod
    def alert(
        self,
        message: str,
        severity: str = "warning",
        channels: Optional[List[str]] = None
    ) -> None:
        """Send alert notification"""
        pass
