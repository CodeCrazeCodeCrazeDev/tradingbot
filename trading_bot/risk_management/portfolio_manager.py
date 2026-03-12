"""
Elite Trading Bot - Portfolio Manager

This module provides portfolio management capabilities for the Elite Trading Bot,
including position tracking, allocation management, and portfolio optimization.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
import uuid

import numpy as np
import pandas as pd
import numpy
import pandas

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Individual position in the portfolio."""
    id: str
    symbol: str
    direction: str             # "long" or "short"
    quantity: float           # Number of shares/units
    entry_price: float        # Average entry price
    current_price: float      # Current market price
    market_value: float       # Current market value
    unrealized_pnl: float     # Unrealized P&L
    realized_pnl: float = 0.0 # Realized P&L from partial closes
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    entry_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)
    sector: str = "Unknown"
    weight: float = 0.0       # Weight in portfolio (%)
    risk_amount: float = 0.0  # Amount at risk
    notes: str = ""


@dataclass
class Allocation:
    """Portfolio allocation by category."""
    cash: float = 0.0
    equities: float = 0.0
    forex: float = 0.0
    crypto: float = 0.0
    commodities: float = 0.0
    bonds: float = 0.0
    other: float = 0.0
    
    def total_invested(self) -> float:
        """Get total invested amount (excluding cash)."""
        return self.equities + self.forex + self.crypto + self.commodities + self.bonds + self.other
    
    def total_value(self) -> float:
        """Get total portfolio value."""
        return self.cash + self.total_invested()


@dataclass
class Exposure:
    """Portfolio exposure metrics."""
    gross_exposure: float     # Sum of absolute position values
    net_exposure: float       # Net long/short exposure
    long_exposure: float      # Total long exposure
    short_exposure: float     # Total short exposure
    leverage: float           # Gross exposure / portfolio value
    beta: Optional[float] = None  # Portfolio beta vs benchmark


@dataclass
class CorrelationMatrix:
    """Correlation matrix for portfolio positions."""
    symbols: List[str]
    matrix: np.ndarray
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_correlation(self, symbol1: str, symbol2: str) -> Optional[float]:
        """Get correlation between two symbols."""
        try:
            idx1 = self.symbols.index(symbol1)
            idx2 = self.symbols.index(symbol2)
            return self.matrix[idx1, idx2]
        except (ValueError, IndexError):
            return None
    
    def get_average_correlation(self) -> float:
        """Get average correlation (excluding diagonal)."""
        if self.matrix.size == 0:
            return 0.0
        
        # Get upper triangle excluding diagonal
        mask = np.triu(np.ones_like(self.matrix, dtype=bool), k=1)
        correlations = self.matrix[mask]
        
        return np.mean(np.abs(correlations)) if len(correlations) > 0 else 0.0


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics."""
    total_value: float
    total_pnl: float
    total_pnl_pct: float
    daily_pnl: float
    daily_pnl_pct: float
    unrealized_pnl: float
    realized_pnl: float
    max_drawdown: float
    current_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    win_rate: float
    profit_factor: float
    largest_win: float
    largest_loss: float
    avg_win: float
    avg_loss: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    timestamp: datetime = field(default_factory=datetime.now)


class Portfolio:
    """
    Portfolio container that tracks positions, allocations, and performance.
    """
    
    def __init__(self, initial_value: float = 100000.0):
        """
        Initialize portfolio.
        
        Args:
            initial_value: Initial portfolio value
        """
        self.initial_value = initial_value
        self.current_value = initial_value
        self.cash_balance = initial_value
        
        # Positions
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        
        # Performance tracking
        self.daily_values: List[Tuple[datetime, float]] = [(datetime.now(), initial_value)]
        self.trade_history: List[Dict[str, Any]] = []
        
        # Metrics
        self.allocation = Allocation(cash=initial_value)
        self.exposure = Exposure(gross_exposure=0, net_exposure=0, long_exposure=0, 
                               short_exposure=0, leverage=0)
        self.correlation_matrix: Optional[CorrelationMatrix] = None
        
        logger.info(f"Portfolio initialized with ${initial_value:,.2f}")
    
    def add_position(self, 
                    symbol: str,
                    direction: str,
                    quantity: float,
                    entry_price: float,
                    stop_loss: Optional[float] = None,
                    take_profit: Optional[float] = None,
                    sector: str = "Unknown") -> str:
        """
        Add a new position to the portfolio.
        
        Args:
            symbol: Trading symbol
            direction: "long" or "short"
            quantity: Number of shares/units
            entry_price: Entry price
            stop_loss: Optional stop loss level
            take_profit: Optional take profit level
            sector: Asset sector/category
            
        Returns:
            Position ID
        """
        position_id = f"pos_{uuid.uuid4().hex[:8]}"
        
        # Calculate market value
        market_value = quantity * entry_price
        
        # Check if we have enough cash (for long positions)
        if direction == "long" and market_value > self.cash_balance:
            raise ValueError(f"Insufficient cash: ${market_value:,.2f} required, ${self.cash_balance:,.2f} available")
        
        # Create position
        position = Position(
            id=position_id,
            symbol=symbol,
            direction=direction,
            quantity=quantity,
            entry_price=entry_price,
            current_price=entry_price,
            market_value=market_value,
            unrealized_pnl=0.0,
            stop_loss=stop_loss,
            take_profit=take_profit,
            sector=sector
        )
        
        # Calculate risk amount
        if stop_loss is not None:
            risk_per_share = abs(entry_price - stop_loss)
            position.risk_amount = risk_per_share * quantity
        
        # Add to positions
        self.positions[position_id] = position
        
        # Update cash balance
        if direction == "long":
            self.cash_balance -= market_value
        else:
            # For short positions, we receive cash but have liability
            self.cash_balance += market_value
        
        # Update portfolio metrics
        self._update_portfolio_metrics()
        
        # Record trade
        self.trade_history.append({
            "timestamp": datetime.now(),
            "action": "open",
            "position_id": position_id,
            "symbol": symbol,
            "direction": direction,
            "quantity": quantity,
            "price": entry_price,
            "value": market_value
        })
        
        logger.info(f"Added {direction} position: {symbol} x{quantity} @ {entry_price}")
        
        return position_id
    
    def update_position_price(self, position_id: str, current_price: float):
        """
        Update position with current market price.
        
        Args:
            position_id: Position identifier
            current_price: Current market price
        """
        if position_id not in self.positions:
            logger.warning(f"Position {position_id} not found")
            return
        
        position = self.positions[position_id]
        position.current_price = current_price
        position.last_update = datetime.now()
        
        # Calculate new market value and unrealized P&L
        if position.direction == "long":
            position.market_value = position.quantity * current_price
            position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
        else:
            # Short position
            position.market_value = position.quantity * current_price
            position.unrealized_pnl = (position.entry_price - current_price) * position.quantity
        
        # Update portfolio metrics
        self._update_portfolio_metrics()
    
    def close_position(self, 
                      position_id: str, 
                      close_price: Optional[float] = None,
                      partial_quantity: Optional[float] = None) -> Dict[str, Any]:
        """
        Close a position (fully or partially).
        
        Args:
            position_id: Position identifier
            close_price: Close price (uses current price if None)
            partial_quantity: Quantity to close (closes full position if None)
            
        Returns:
            Trade result dictionary
        """
        if position_id not in self.positions:
            raise ValueError(f"Position {position_id} not found")
        
        position = self.positions[position_id]
        
        if close_price is None:
            close_price = position.current_price
        
        if partial_quantity is None:
            partial_quantity = position.quantity
        
        if partial_quantity > position.quantity:
            raise ValueError(f"Cannot close {partial_quantity} shares, only {position.quantity} available")
        
        # Calculate P&L for closed portion
        if position.direction == "long":
            pnl = (close_price - position.entry_price) * partial_quantity
        else:
            pnl = (position.entry_price - close_price) * partial_quantity
        
        # Calculate close value
        close_value = partial_quantity * close_price
        
        # Update cash balance
        if position.direction == "long":
            self.cash_balance += close_value
        else:
            # For short positions, we pay back the borrowed shares
            self.cash_balance -= close_value
        
        # Create trade result
        trade_result = {
            "timestamp": datetime.now(),
            "action": "close",
            "position_id": position_id,
            "symbol": position.symbol,
            "direction": position.direction,
            "quantity": partial_quantity,
            "entry_price": position.entry_price,
            "close_price": close_price,
            "pnl": pnl,
            "pnl_pct": (pnl / (position.entry_price * partial_quantity)) * 100,
            "hold_time": datetime.now() - position.entry_time
        }
        
        # Update position
        if partial_quantity == position.quantity:
            # Full close
            position.realized_pnl += pnl
            self.closed_positions.append(position)
            del self.positions[position_id]
        else:
            # Partial close
            position.quantity -= partial_quantity
            position.realized_pnl += pnl
            position.market_value = position.quantity * position.current_price
            
            # Recalculate unrealized P&L for remaining quantity
            if position.direction == "long":
                position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
            else:
                position.unrealized_pnl = (position.entry_price - position.current_price) * position.quantity
        
        # Record trade
        self.trade_history.append(trade_result)
        
        # Update portfolio metrics
        self._update_portfolio_metrics()
        
        logger.info(f"Closed {partial_quantity} shares of {position.symbol} @ {close_price}, P&L: ${pnl:,.2f}")
        
        return trade_result
    
    def _update_portfolio_metrics(self):
        """Update portfolio allocation, exposure, and other metrics."""
        # Calculate total market value of positions
        total_position_value = sum(pos.market_value for pos in self.positions.values())
        
        # Update current portfolio value
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_realized_pnl = sum(pos.realized_pnl for pos in self.positions.values())
        
        self.current_value = self.cash_balance + total_position_value
        
        # Update allocation
        self.allocation = Allocation(cash=self.cash_balance)
        
        for position in self.positions.values():
            # Categorize by symbol (simplified categorization)
            if "USD" in position.symbol or "EUR" in position.symbol:
                self.allocation.forex += position.market_value
            elif "BTC" in position.symbol or "ETH" in position.symbol:
                self.allocation.crypto += position.market_value
            elif "GOLD" in position.symbol or "OIL" in position.symbol:
                self.allocation.commodities += position.market_value
            else:
                self.allocation.equities += position.market_value
        
        # Update exposure
        long_exposure = sum(pos.market_value for pos in self.positions.values() if pos.direction == "long")
        short_exposure = sum(pos.market_value for pos in self.positions.values() if pos.direction == "short")
        
        self.exposure = Exposure(
            gross_exposure=long_exposure + short_exposure,
            net_exposure=long_exposure - short_exposure,
            long_exposure=long_exposure,
            short_exposure=short_exposure,
            leverage=(long_exposure + short_exposure) / self.current_value if self.current_value > 0 else 0
        )
        
        # Update position weights
        for position in self.positions.values():
            position.weight = (position.market_value / self.current_value) * 100 if self.current_value > 0 else 0
        
        # Record daily value
        today = datetime.now().date()
        if not self.daily_values or self.daily_values[-1][0].date() != today:
            self.daily_values.append((datetime.now(), self.current_value))
    
    def calculate_metrics(self) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics."""
        # Basic P&L metrics
        total_pnl = self.current_value - self.initial_value
        total_pnl_pct = (total_pnl / self.initial_value) * 100
        
        # Daily P&L
        daily_pnl = 0.0
        daily_pnl_pct = 0.0
        
        if len(self.daily_values) > 1:
            yesterday_value = self.daily_values[-2][1]
            daily_pnl = self.current_value - yesterday_value
            daily_pnl_pct = (daily_pnl / yesterday_value) * 100
        
        # Unrealized and realized P&L
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        realized_pnl = sum(pos.realized_pnl for pos in self.positions.values())
        realized_pnl += sum(trade.get("pnl", 0) for trade in self.trade_history if trade.get("action") == "close")
        
        # Calculate drawdown
        max_drawdown, current_drawdown = self._calculate_drawdown()
        
        # Calculate Sharpe and Sortino ratios
        sharpe_ratio, sortino_ratio = self._calculate_ratios()
        
        # Trade statistics
        closed_trades = [trade for trade in self.trade_history if trade.get("action") == "close"]
        
        if closed_trades:
            trade_pnls = [trade["pnl"] for trade in closed_trades]
            winning_trades = [pnl for pnl in trade_pnls if pnl > 0]
            losing_trades = [pnl for pnl in trade_pnls if pnl < 0]
            
            win_rate = len(winning_trades) / len(trade_pnls) * 100
            
            avg_win = np.mean(winning_trades) if winning_trades else 0
            avg_loss = abs(np.mean(losing_trades)) if losing_trades else 0
            
            profit_factor = sum(winning_trades) / abs(sum(losing_trades)) if losing_trades else float('inf')
            
            largest_win = max(trade_pnls) if trade_pnls else 0
            largest_loss = min(trade_pnls) if trade_pnls else 0
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
            largest_win = 0
            largest_loss = 0
            winning_trades = []
            losing_trades = []
        
        return PortfolioMetrics(
            total_value=self.current_value,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            daily_pnl=daily_pnl,
            daily_pnl_pct=daily_pnl_pct,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=realized_pnl,
            max_drawdown=max_drawdown,
            current_drawdown=current_drawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            largest_win=largest_win,
            largest_loss=largest_loss,
            avg_win=avg_win,
            avg_loss=avg_loss,
            total_trades=len(closed_trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades)
        )
    
    def _calculate_drawdown(self) -> Tuple[float, float]:
        """Calculate maximum and current drawdown."""
        if len(self.daily_values) < 2:
            return 0.0, 0.0
        
        values = [value for _, value in self.daily_values]
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(values)
        
        # Calculate drawdown
        drawdown = (np.array(values) - running_max) / running_max * 100
        
        max_drawdown = np.min(drawdown)
        current_drawdown = drawdown[-1]
        
        return max_drawdown, current_drawdown
    
    def _calculate_ratios(self) -> Tuple[float, float]:
        """Calculate Sharpe and Sortino ratios."""
        if len(self.daily_values) < 30:  # Need at least 30 days
            return 0.0, 0.0
        
        # Calculate daily returns
        values = [value for _, value in self.daily_values]
        returns = np.diff(values) / values[:-1]
        
        if len(returns) == 0:
            return 0.0, 0.0
        
        # Annualized metrics
        mean_return = np.mean(returns) * 252
        volatility = np.std(returns) * np.sqrt(252)
        
        # Sharpe ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        sharpe_ratio = (mean_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        # Sortino ratio (downside deviation)
        negative_returns = returns[returns < 0]
        downside_deviation = np.std(negative_returns) * np.sqrt(252) if len(negative_returns) > 0 else volatility
        
        sortino_ratio = (mean_return - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
        
        return sharpe_ratio, sortino_ratio
    
    def update_correlation_matrix(self, market_data: Dict[str, pd.DataFrame]):
        """Update correlation matrix for current positions."""
        symbols = list(set(pos.symbol for pos in self.positions.values()))
        
        if len(symbols) < 2:
            self.correlation_matrix = None
            return
        
        # Calculate correlation matrix
        returns_data = {}
        
        for symbol in symbols:
            if symbol in market_data and len(market_data[symbol]) > 20:
                returns = market_data[symbol]['close'].pct_change().dropna()
                returns_data[symbol] = returns
        
        if len(returns_data) < 2:
            self.correlation_matrix = None
            return
        
        # Create returns DataFrame
        returns_df = pd.DataFrame(returns_data).dropna()
        
        if len(returns_df) < 10:
            self.correlation_matrix = None
            return
        
        # Calculate correlation matrix
        corr_matrix = returns_df.corr().values
        
        self.correlation_matrix = CorrelationMatrix(
            symbols=list(returns_df.columns),
            matrix=corr_matrix
        )
    
    def get_position_summary(self) -> Dict[str, Any]:
        """Get summary of all positions."""
        summary = {
            "total_positions": len(self.positions),
            "long_positions": len([p for p in self.positions.values() if p.direction == "long"]),
            "short_positions": len([p for p in self.positions.values() if p.direction == "short"]),
            "total_market_value": sum(pos.market_value for pos in self.positions.values()),
            "total_unrealized_pnl": sum(pos.unrealized_pnl for pos in self.positions.values()),
            "largest_position": None,
            "most_profitable": None,
            "least_profitable": None
        }
        
        if self.positions:
            # Find largest position by market value
            largest_pos = max(self.positions.values(), key=lambda p: p.market_value)
            summary["largest_position"] = {
                "symbol": largest_pos.symbol,
                "market_value": largest_pos.market_value,
                "weight": largest_pos.weight
            }
            
            # Find most and least profitable positions
            most_profitable = max(self.positions.values(), key=lambda p: p.unrealized_pnl)
            least_profitable = min(self.positions.values(), key=lambda p: p.unrealized_pnl)
            
            summary["most_profitable"] = {
                "symbol": most_profitable.symbol,
                "unrealized_pnl": most_profitable.unrealized_pnl
            }
            
            summary["least_profitable"] = {
                "symbol": least_profitable.symbol,
                "unrealized_pnl": least_profitable.unrealized_pnl
            }
        
        return summary


class PortfolioManager:
    """
    Main portfolio manager that handles multiple portfolios and provides
    portfolio optimization and risk management capabilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize portfolio manager.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Portfolios
        self.portfolios: Dict[str, Portfolio] = {}
        self.default_portfolio_id: Optional[str] = None
        
        logger.info("PortfolioManager initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "default_portfolio_value": 100000.0,
            "max_portfolios": 10,
            "enable_auto_rebalancing": False,
            "rebalance_threshold": 0.05,  # 5% deviation threshold
            "correlation_update_interval": 3600,  # 1 hour in seconds
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def create_portfolio(self, 
                        portfolio_id: str,
                        initial_value: Optional[float] = None) -> Portfolio:
        """
        Create a new portfolio.
        
        Args:
            portfolio_id: Unique portfolio identifier
            initial_value: Initial portfolio value
            
        Returns:
            Created Portfolio object
        """
        if portfolio_id in self.portfolios:
            raise ValueError(f"Portfolio {portfolio_id} already exists")
        
        if len(self.portfolios) >= self.config["max_portfolios"]:
            raise ValueError(f"Maximum number of portfolios ({self.config['max_portfolios']}) reached")
        
        if initial_value is None:
            initial_value = self.config["default_portfolio_value"]
        
        portfolio = Portfolio(initial_value)
        self.portfolios[portfolio_id] = portfolio
        
        # Set as default if it's the first portfolio
        if self.default_portfolio_id is None:
            self.default_portfolio_id = portfolio_id
        
        logger.info(f"Created portfolio {portfolio_id} with ${initial_value:,.2f}")
        
        return portfolio
    
    def get_portfolio(self, portfolio_id: Optional[str] = None) -> Optional[Portfolio]:
        """
        Get portfolio by ID.
        
        Args:
            portfolio_id: Portfolio ID (uses default if None)
            
        Returns:
            Portfolio object or None if not found
        """
        if portfolio_id is None:
            portfolio_id = self.default_portfolio_id
        
        return self.portfolios.get(portfolio_id)
    
    def update_all_portfolios(self, market_data: Dict[str, pd.DataFrame]):
        """
        Update all portfolios with current market data.
        
        Args:
            market_data: Dictionary of symbol -> market data
        """
        for portfolio in self.portfolios.values():
            # Update position prices
            for position in portfolio.positions.values():
                if position.symbol in market_data:
                    latest_data = market_data[position.symbol]
                    if not latest_data.empty:
                        current_price = latest_data['close'].iloc[-1]
                        portfolio.update_position_price(position.id, current_price)
            
            # Update correlation matrix
            portfolio.update_correlation_matrix(market_data)
    
    def get_aggregate_metrics(self) -> Dict[str, Any]:
        """Get aggregate metrics across all portfolios."""
        if not self.portfolios:
            return {}
        
        total_value = sum(p.current_value for p in self.portfolios.values())
        total_pnl = sum(p.current_value - p.initial_value for p in self.portfolios.values())
        
        aggregate = {
            "total_portfolios": len(self.portfolios),
            "total_value": total_value,
            "total_pnl": total_pnl,
            "total_pnl_pct": (total_pnl / sum(p.initial_value for p in self.portfolios.values())) * 100,
            "total_positions": sum(len(p.positions) for p in self.portfolios.values()),
            "portfolio_summaries": {}
        }
        
        # Individual portfolio summaries
        for portfolio_id, portfolio in self.portfolios.items():
            metrics = portfolio.calculate_metrics()
            aggregate["portfolio_summaries"][portfolio_id] = {
                "value": portfolio.current_value,
                "pnl": metrics.total_pnl,
                "pnl_pct": metrics.total_pnl_pct,
                "positions": len(portfolio.positions),
                "sharpe_ratio": metrics.sharpe_ratio
            }
        
        return aggregate
