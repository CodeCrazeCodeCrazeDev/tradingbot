"""
Advanced Position Manager
Tracks, manages, and auto-closes positions based on multiple criteria.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents an open trading position"""
    ticket_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    entry_price: float
    current_price: float
    size: float
    stop_loss: float
    take_profit: float
    entry_time: datetime
    entry_confidence: float
    current_confidence: float
    unrealized_pnl: float
    
    @property
    def age_hours(self) -> float:
        """Get position age in hours"""
        return (datetime.now() - self.entry_time).total_seconds() / 3600
    
    @property
    def pnl_percent(self) -> float:
        """Get PnL as percentage"""
        if self.side == 'buy':
            return (self.current_price - self.entry_price) / self.entry_price
        else:
            return (self.entry_price - self.current_price) / self.entry_price


import threading
from trading_bot.brokers.broker_adapter import BrokerAdapter
from enum import auto

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        """
        decorator function.

    Args:
        func: Description

    Returns:
        Result of operation
        """
        async def wrapper(*args, **kwargs):
            """
            wrapper function.

    Auto-documented by QwenCodeMender.
            """
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



class PositionManager:
    """
    Manages open positions with intelligent auto-close logic.
    
    Features:
    - Real-time position tracking
    - Auto-close on confidence shifts
    - TP/SL monitoring
    - Position aging management
    - Max position limits
    - Risk-based position prioritization
    """
    
    def __init__(self, config: dict = None, broker_adapter: BrokerAdapter = None):
        self.config = config or {}
        self.broker = broker_adapter
        self.max_positions = self.config.get('max_positions', 10)
        self.max_positions_per_symbol = self.config.get('max_positions_per_symbol', 2)
        self.confidence_shift_threshold = self.config.get('confidence_shift_threshold', 0.6)
        self.low_confidence_threshold = self.config.get('low_confidence_threshold', 0.3)
        self.max_position_age_hours = self.config.get('max_position_age_hours', 24)
        self.aged_position_confidence_threshold = self.config.get('aged_position_confidence_threshold', 0.5)
        self.positions: dict = {}
        self.closed_positions_today = 0
        self.auto_closes_today = 0
        self.lock = threading.RLock()
        self._async_lock = asyncio.Lock()  # Reusable async lock
        self.pnl_history = []
        self._max_pnl_history = 10000  # Prevent unbounded growth
        self.health_status = {}
        self.logger = logging.getLogger("PositionManager")
        self.logger.info(f"PositionManager initialized (max_positions: {self.max_positions})")
    
    async def add_position(self, position: Position):
        """
        add_position function.

    Args:
        position: Description

    Returns:
        Result of operation
        """
        async with self._async_lock:
            if len(self.positions) >= self.max_positions:
                self.logger.warning("Max positions reached, cannot add new position")
                return False
            if sum(1 for p in self.positions.values() if p.symbol == position.symbol) >= self.max_positions_per_symbol:
                self.logger.warning(f"Max positions for {position.symbol} reached")
                return False
            self.positions[position.ticket_id] = position
            self.logger.info(f"Added position: {position.symbol} {position.side} @ {position.entry_price}")
        return True
    
    async def remove_position(self, ticket_id: str):
        """
        remove_position function.

    Args:
        ticket_id: Description

    Returns:
        Result of operation
        """
        async with self._async_lock:
            if ticket_id in self.positions:
                position = self.positions.pop(ticket_id)
                self.closed_positions_today += 1
                self.logger.info(f"Removed position: {position.symbol} (total closed today: {self.closed_positions_today})")
    
    async def update_position(self, ticket_id: str, current_price: float, current_confidence: float):
        async with self._async_lock:
            if ticket_id in self.positions:
                position = self.positions[ticket_id]
                position.current_price = current_price
                position.current_confidence = current_confidence
                if position.side == 'buy':
                    position.unrealized_pnl = (current_price - position.entry_price) * position.size
                else:
                    position.unrealized_pnl = (position.entry_price - current_price) * position.size
                self.logger.debug(f"Updated position {ticket_id}: price={current_price}, confidence={current_confidence}, pnl={position.unrealized_pnl}")
                await self._auto_close_check(position)
                await self._update_health(position)

    async def _auto_close_check(self, position: Position):
        should_close = False
        if position.current_confidence < self.low_confidence_threshold:
            should_close = True
        if position.age_hours > self.max_position_age_hours and position.current_confidence < self.aged_position_confidence_threshold:
            should_close = True
        if should_close:
            await self.close_position(position.ticket_id, reason="Auto-close logic")

    async def close_position(self, ticket_id: str, reason: str = "manual"):
        async with self._async_lock:
            position = self.positions.get(ticket_id)
            if not position:
                return False
            try:
                resp = await self.broker.close_position(ticket_id)
                if resp:
                    self.logger.info(f"Closed position {ticket_id} ({reason})")
                    await self.remove_position(ticket_id)
                    return True
                else:
                    self.logger.error(f"Failed to close position {ticket_id}")
                    return False
            except Exception as e:
                self.logger.error(f"Error closing position {ticket_id}: {e}")
                return False

    async def _update_health(self, position: Position):
        pnl = position.unrealized_pnl
        health = "excellent" if pnl > 0 else ("neutral" if pnl == 0 else "poor")
        self.health_status[position.ticket_id] = health
        self.logger.debug(f"Health for {position.ticket_id}: {health}")

    async def get_all_positions(self):
        async with self._async_lock:
            return list(self.positions.values())

    async def sync_with_broker(self):
        async with self._async_lock:
            broker_positions = await self.broker.get_positions()
            broker_ticket_ids = {p.symbol for p in broker_positions}
            local_ticket_ids = set(self.positions.keys())
            for ticket_id in local_ticket_ids - broker_ticket_ids:
                await self.remove_position(ticket_id)
            for pos in broker_positions:
                if pos.symbol not in self.positions:
                    await self.add_position(pos)

    async def get_pnl_summary(self):
        async with self._async_lock:
            total_pnl = sum(p.unrealized_pnl for p in self.positions.values())
            self.pnl_history.append(total_pnl)
            # Prevent unbounded growth
            if len(self.pnl_history) > self._max_pnl_history:
                self.pnl_history = self.pnl_history[-5000:]
            return total_pnl

    async def scale_position(self, ticket_id: str, scale_factor: float):
        async with self._async_lock:
            if ticket_id in self.positions:
                position = self.positions[ticket_id]
                new_size = position.size * scale_factor
                await self.broker.place_order(
                    symbol=position.symbol,
                    side=position.side,
                    order_type="market",
                    quantity=new_size - position.size
                )
                position.size = new_size
                self.logger.info(f"Scaled position {ticket_id} to {new_size}")
                return True
            return False

    
    def can_open_new_position(self, symbol: str) -> tuple[bool, str]:
        """
        Check if a new position can be opened.
        
        Returns:
            (can_open, reason)
        """
        # Check max total positions
        if len(self.positions) >= self.max_positions:
            return False, f"Max positions reached ({self.max_positions})"
        
        # Check max positions per symbol
        symbol_positions = [p for p in self.positions.values() if p.symbol == symbol]
        if len(symbol_positions) >= self.max_positions_per_symbol:
            return False, f"Max positions for {symbol} reached ({self.max_positions_per_symbol})"
        
        return True, "OK"
    
    def should_close_position(self, position: Position, new_decision_confidence: float,
                            new_decision_action: str) -> tuple[bool, str]:
        """
        Determine if a position should be auto-closed.
        
        Args:
            position: Position to evaluate
            new_decision_confidence: Latest decision confidence
            new_decision_action: Latest decision action ('buy', 'sell', 'hold')
            
        Returns:
            (should_close, reason)
        """
        # 1. Confidence shift (opposite signal with high confidence)
        if position.side == 'buy' and new_decision_action == 'sell':
            if new_decision_confidence >= self.confidence_shift_threshold:
                return True, f"Confidence shifted to SELL ({new_decision_confidence:.2f})"
        elif position.side == 'sell' and new_decision_action == 'buy':
            if new_decision_confidence >= self.confidence_shift_threshold:
                return True, f"Confidence shifted to BUY ({new_decision_confidence:.2f})"
        
        # 2. Very low confidence (market uncertainty)
        if position.current_confidence < self.low_confidence_threshold:
            return True, f"Low confidence ({position.current_confidence:.2f})"
        
        # 3. Take profit hit
        if position.side == 'buy' and position.current_price >= position.take_profit:
            return True, "Take profit reached"
        elif position.side == 'sell' and position.current_price <= position.take_profit:
            return True, "Take profit reached"
        
        # 4. Stop loss hit
        if position.side == 'buy' and position.current_price <= position.stop_loss:
            return True, "Stop loss hit"
        elif position.side == 'sell' and position.current_price >= position.stop_loss:
            return True, "Stop loss hit"
        
        # 5. Position aged out with declining confidence
        if position.age_hours >= self.max_position_age_hours:
            if position.current_confidence < self.aged_position_confidence_threshold:
                return True, f"Position aged out ({position.age_hours:.1f}h) with low confidence"
        
        return False, ""
    
    def get_weakest_position(self) -> Optional[Position]:
        """
        Find the weakest position to close when making room for new trades.
        
        Priority (close first):
        1. Positions with very low confidence
        2. Aged positions with declining confidence
        3. Positions near stop loss
        4. Oldest position
        
        Returns:
            Weakest position or None
        """
        if not self.positions:
            return None
        
        positions_list = list(self.positions.values())
        
        # Score each position (higher score = weaker = close first)
        scored_positions = []
        for pos in positions_list:
            score = 0
            
            # Very low confidence (highest priority)
            if pos.current_confidence < 0.3:
                score += 100
            
            # Aged with declining confidence
            if pos.age_hours > self.max_position_age_hours:
                score += 50
                if pos.current_confidence < pos.entry_confidence:
                    score += 30
            
            # Near stop loss
            if pos.side == 'buy':
                distance_to_sl = (pos.current_price - pos.stop_loss) / pos.entry_price
            else:
                distance_to_sl = (pos.stop_loss - pos.current_price) / pos.entry_price
            
            if distance_to_sl < 0.01:  # Within 1% of stop loss
                score += 40
            
            # Age factor
            score += pos.age_hours * 0.5
            
            # Confidence decline
            confidence_decline = pos.entry_confidence - pos.current_confidence
            score += confidence_decline * 50
            
            scored_positions.append((score, pos))
        
        # Sort by score (highest first)
        scored_positions.sort(key=lambda x: x[0], reverse=True)
        
        return scored_positions[0][1]
    
    async def auto_close_if_needed(self, position: Position, reason: str,
                                   close_callback) -> bool:
        """
        Auto-close a position if criteria met.
        
        Args:
            position: Position to close
            reason: Reason for closing
            close_callback: Async function to execute the close
            
        Returns:
            True if closed, False otherwise
        """
        try:
            logger.info(f"Auto-closing {position.symbol} {position.side}: {reason}")
            
            # Execute close via callback
            success = await close_callback(position.ticket_id, reason)
            
            if success:
                self.remove_position(position.ticket_id)
                self.auto_closes_today += 1
                logger.info(f"Position closed successfully (auto-closes today: {self.auto_closes_today})")
                return True
            else:
                logger.error(f"Failed to close position {position.ticket_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error auto-closing position: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get position manager status"""
        total_unrealized_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        
        return {
            'active_positions': len(self.positions),
            'max_positions': self.max_positions,
            'positions_available': self.max_positions - len(self.positions),
            'closed_today': self.closed_positions_today,
            'auto_closes_today': self.auto_closes_today,
            'total_unrealized_pnl': total_unrealized_pnl,
            'positions_by_symbol': self._get_positions_by_symbol(),
            'avg_position_age_hours': self._get_avg_age(),
            'avg_confidence': self._get_avg_confidence()
        }
    
    def _get_positions_by_symbol(self) -> Dict[str, int]:
        """Get count of positions per symbol"""
        symbol_counts = {}
        for pos in self.positions.values():
            symbol_counts[pos.symbol] = symbol_counts.get(pos.symbol, 0) + 1
        return symbol_counts
    
    def _get_avg_age(self) -> float:
        """Get average position age in hours"""
        if not self.positions:
            return 0.0
        return sum(p.age_hours for p in self.positions.values()) / len(self.positions)
    
    def _get_avg_confidence(self) -> float:
        """Get average current confidence"""
        if not self.positions:
            return 0.0
        return sum(p.current_confidence for p in self.positions.values()) / len(self.positions)
    
    def get_positions_list(self) -> List[Dict[str, Any]]:
        """Get list of all positions with details"""
        return [
            {
                'ticket_id': p.ticket_id,
                'symbol': p.symbol,
                'side': p.side,
                'entry_price': p.entry_price,
                'current_price': p.current_price,
                'size': p.size,
                'stop_loss': p.stop_loss,
                'take_profit': p.take_profit,
                'entry_time': p.entry_time.isoformat(),
                'age_hours': p.age_hours,
                'entry_confidence': p.entry_confidence,
                'current_confidence': p.current_confidence,
                'unrealized_pnl': p.unrealized_pnl,
                'pnl_percent': p.pnl_percent
            }
            for p in self.positions.values()
        ]
