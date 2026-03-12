"""
Position and risk management system for AlphaAlgo 2.0
"""

import logging
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Trading position details."""
    symbol: str
    direction: str  # LONG or SHORT
    size: float
    entry_price: float
    stop_loss: float
    take_profit: float
    timestamp: datetime = None
    current_price: float = 0.0  # Track current price for P&L
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.current_price == 0.0:
            self.current_price = self.entry_price
    
    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized P/L."""
        if self.current_price == 0:
            return 0.0
        if self.direction == "LONG":
            return (self.current_price - self.entry_price) * self.size
        else:  # SHORT
            return (self.entry_price - self.current_price) * self.size
    
    @property
    def risk_amount(self) -> float:
        """Calculate risk amount."""
        return abs(self.entry_price - self.stop_loss) * self.size


class PositionManager:
    """
    Manages trading positions and risk.
    Implements sophisticated position sizing and risk management.
    Thread-safe for concurrent access.
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        max_risk_per_trade: float = 0.02,  # 2% per trade
        max_portfolio_risk: float = 0.05,   # 5% total
        max_correlation: float = 0.7,
        max_positions: int = 10
    ):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_risk_per_trade = max_risk_per_trade
        self.max_portfolio_risk = max_portfolio_risk
        self.max_correlation = max_correlation
        self.max_positions = max_positions
        
        # Thread lock for position safety
        self._lock = threading.RLock()
        
        # Active positions
        self.positions: Dict[str, Position] = {}
        
        # Position history (bounded to prevent memory leak)
        self.position_history: List[Dict] = []
        self._max_history_size = 10000
        
        # Risk metrics
        self.portfolio_metrics = {
            'total_exposure': 0.0,
            'total_risk': 0.0,
            'correlation_matrix': None,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0
        }
        
        logger.info("✅ Position Manager initialized")
        logger.info(f"   Initial capital: ${initial_capital:,.2f}")
    
    def open_position(
        self,
        symbol: str,
        direction: str,
        price: float,
        stop_loss: float,
        take_profit: float,
        confidence: float = 0.5
    ) -> Optional[Position]:
        """
        Open new trading position.
        
        Args:
            symbol: Trading symbol
            direction: LONG or SHORT
            price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            confidence: Trade confidence (0-1)
        
        Returns:
            New position if successful
        """
        with self._lock:  # Thread-safe position access
            try:
                # Check if symbol already has position
                if symbol in self.positions:
                    logger.warning(f"⚠️ Position already exists for {symbol}")
                    return None
                
                # Check maximum positions
                if len(self.positions) >= self.max_positions:
                    logger.warning("⚠️ Maximum positions reached")
                    return None
                
                # Calculate position size
                size = self._calculate_position_size(
                    price=price,
                    stop_loss=stop_loss,
                    confidence=confidence
                )
                
                if size == 0:
                    logger.warning("⚠️ Position size too small")
                    return None
                
                # Check portfolio risk
                if not self._check_portfolio_risk(symbol, size * price):
                    logger.warning("⚠️ Portfolio risk too high")
                    return None
                
                # Create position
                position = Position(
                    symbol=symbol,
                    direction=direction,
                    size=size,
                    entry_price=price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    current_price=price
                )
                
                # Add to active positions
                self.positions[symbol] = position
                
                # Update portfolio metrics
                self._update_portfolio_metrics()
                
                logger.info(f"✅ Opened {direction} position in {symbol}")
                logger.info(f"   Size: {size:.4f}")
                logger.info(f"   Entry: ${price:.4f}")
                logger.info(f"   Stop: ${stop_loss:.4f}")
                logger.info(f"   Target: ${take_profit:.4f}")
                
                return position
                
            except Exception as e:
                logger.error(f"❌ Error opening position: {str(e)}")
                return None
    
    def close_position(
        self,
        symbol: str,
        price: float,
        reason: str = "manual"
    ) -> Optional[float]:
        """
        Close trading position.
        
        Args:
            symbol: Trading symbol
            price: Exit price
            reason: Reason for closing
        
        Returns:
            Realized P/L if successful
        """
        with self._lock:  # Thread-safe position access
            if symbol not in self.positions:
                logger.warning(f"⚠️ No position found for {symbol}")
                return None
            
            try:
                position = self.positions[symbol]
                
                # Calculate P/L
                if position.direction == "LONG":
                    pnl = (price - position.entry_price) * position.size
                else:
                    pnl = (position.entry_price - price) * position.size
                
                # Update capital
                self.current_capital += pnl
                
                # Record to history
                self.position_history.append({
                    'symbol': symbol,
                    'direction': position.direction,
                    'size': position.size,
                    'entry_price': position.entry_price,
                    'exit_price': price,
                    'pnl': pnl,
                    'entry_time': position.timestamp,
                    'exit_time': datetime.now(),
                    'reason': reason
                })
                
                # Limit history size to prevent memory leak
                if len(self.position_history) > self._max_history_size:
                    self.position_history = self.position_history[-5000:]
                
                # Remove position
                del self.positions[symbol]
                
                # Update portfolio metrics
                self._update_portfolio_metrics()
                
                logger.info(f"✅ Closed position in {symbol}")
                logger.info(f"   P/L: ${pnl:.2f}")
                logger.info(f"   Reason: {reason}")
                
                return pnl
                
            except Exception as e:
                logger.error(f"❌ Error closing position: {str(e)}")
                return None
    
    def update_position_price(self, symbol: str, current_price: float) -> bool:
        """Update current price for a position (thread-safe)."""
        with self._lock:
            if symbol in self.positions:
                self.positions[symbol].current_price = current_price
                return True
            return False
    
    def _calculate_position_size(
        self,
        price: float,
        stop_loss: float,
        confidence: float
    ) -> float:
        """
        Calculate optimal position size using Kelly Criterion.
        
        Kelly Criterion: f* = (p * b - q) / b
        where:
        - f* = fraction of capital to bet
        - p = probability of winning
        - q = probability of losing (1-p)
        - b = odds (win/loss ratio)
        """
        # Risk amount in dollars
        risk_amount = self.current_capital * self.max_risk_per_trade
        
        # Calculate Kelly fraction if we have trading history
        if len(self.position_history) > 10:
            winning_trades = [p for p in self.position_history if p['pnl'] > 0]
            losing_trades = [p for p in self.position_history if p['pnl'] <= 0]
            
            if winning_trades and losing_trades:
                # Win probability
                p = len(winning_trades) / len(self.position_history)
                q = 1 - p
                
                # Average win/loss ratio
                avg_win = np.mean([abs(t['pnl']) for t in winning_trades])
                avg_loss = np.mean([abs(t['pnl']) for t in losing_trades])
                b = avg_win / avg_loss if avg_loss > 0 else 1.0
                
                # Kelly fraction
                kelly_fraction = (p * b - q) / b if b > 0 else 0
                
                # Use half-Kelly for safety
                kelly_fraction = max(0, min(kelly_fraction * 0.5, self.max_risk_per_trade))
                
                # Adjust risk amount
                risk_amount = self.current_capital * kelly_fraction
        
        # Adjust for confidence
        risk_amount *= confidence
        
        # Calculate size based on stop loss
        price_risk = abs(price - stop_loss)
        if price_risk == 0:
            return 0
        
        size = risk_amount / price_risk
        
        # Round to appropriate precision
        return round(size, 4)
    
    def _check_portfolio_risk(
        self,
        new_symbol: str,
        new_exposure: float
    ) -> bool:
        """Check if new position exceeds portfolio risk limits."""
        # Calculate total exposure
        total_exposure = sum(
            pos.size * pos.entry_price
            for pos in self.positions.values()
        ) + new_exposure
        
        # Check exposure ratio
        if total_exposure / self.current_capital > self.max_portfolio_risk:
            return False
        
        # Check correlations if we have history
        if len(self.position_history) > 0:
            correlations = self._calculate_correlations(new_symbol)
            if correlations and max(correlations) > self.max_correlation:
                return False
        
        return True
    
    def _calculate_correlations(self, symbol: str) -> Optional[List[float]]:
        """
        Calculate correlations with existing positions.
        Uses historical price data to compute correlation matrix.
        """
        if not self.positions:
            return None
        
        try:
            # Get historical prices from position history
            prices = {}
            symbols = [symbol] + list(self.positions.keys())
            
            for sym in symbols:
                # Extract prices from history
                sym_history = [
                    p['exit_price'] for p in self.position_history
                    if p['symbol'] == sym
                ]
                
                if len(sym_history) < 10:
                    # Not enough data - use neutral correlation
                    prices[sym] = np.zeros(10)
                else:
                    prices[sym] = np.array(sym_history[-100:])  # Last 100 prices
            
            # Ensure all arrays have same length
            min_length = min(len(prices[sym]) for sym in symbols)
            if min_length < 2:
                return [0.0] * (len(symbols) - 1)
            
            # Calculate correlation matrix
            price_matrix = np.array([prices[sym][-min_length:] for sym in symbols])
            correlation_matrix = np.corrcoef(price_matrix)
            
            # Get correlations with new symbol
            correlations = correlation_matrix[0, 1:]
            
            return list(np.abs(correlations))  # Return absolute correlations
            
        except Exception as e:
            logger.warning(f"⚠️ Error calculating correlations: {e}")
            return [0.0] * len(self.positions)
    
    def _update_portfolio_metrics(self):
        """Update portfolio risk metrics."""
        if not self.positions:
            self.portfolio_metrics = {
                'total_exposure': 0.0,
                'total_risk': 0.0,
                'correlation_matrix': None,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0
            }
            return
        
        # Calculate exposure
        total_exposure = sum(
            pos.size * pos.entry_price
            for pos in self.positions.values()
        )
        
        # Calculate total risk
        total_risk = sum(
            pos.risk_amount
            for pos in self.positions.values()
        )
        
        # Calculate metrics from history
        if self.position_history:
            returns = [p['pnl'] / self.initial_capital for p in self.position_history]
            std_returns = np.std(returns) if len(returns) > 1 else 1e-10
            sharpe_ratio = np.mean(returns) / (std_returns + 1e-10)
            
            # Calculate drawdown
            cumulative = np.cumsum(returns)
            max_drawdown = np.min(cumulative - np.maximum.accumulate(cumulative))
        else:
            sharpe_ratio = 0.0
            max_drawdown = 0.0
        
        self.portfolio_metrics = {
            'total_exposure': total_exposure,
            'total_risk': total_risk,
            'correlation_matrix': self._calculate_correlations(
                list(self.positions.keys())[0]
            ) if self.positions else None,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown
        }
    
    def get_position_summary(self) -> Dict:
        """Get summary of current positions."""
        with self._lock:
            return {
                'num_positions': len(self.positions),
                'total_exposure': self.portfolio_metrics['total_exposure'],
                'total_risk': self.portfolio_metrics['total_risk'],
                'current_capital': self.current_capital,
                'return_pct': (self.current_capital / self.initial_capital - 1) * 100,
                'sharpe_ratio': self.portfolio_metrics['sharpe_ratio'],
                'max_drawdown': self.portfolio_metrics['max_drawdown'],
                'positions': [
                    {
                        'symbol': symbol,
                        'direction': pos.direction,
                        'size': pos.size,
                        'entry_price': pos.entry_price,
                        'current_price': pos.current_price,
                        'current_pnl': pos.unrealized_pnl,
                        'risk_amount': pos.risk_amount
                    }
                    for symbol, pos in self.positions.items()
                ]
            }
    
    def get_trading_history(self) -> Dict:
        """Get trading history summary."""
        with self._lock:
            if not self.position_history:
                return {'total_trades': 0, 'trades': []}
            
            # Calculate metrics
            total_trades = len(self.position_history)
            winning_trades = sum(1 for p in self.position_history if p['pnl'] > 0)
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': winning_trades / total_trades if total_trades > 0 else 0,
                'total_pnl': sum(p['pnl'] for p in self.position_history),
                'avg_pnl': np.mean([p['pnl'] for p in self.position_history]),
                'max_pnl': max(p['pnl'] for p in self.position_history),
                'min_pnl': min(p['pnl'] for p in self.position_history),
                'trades': self.position_history[-100:]  # Last 100 trades only
            }
