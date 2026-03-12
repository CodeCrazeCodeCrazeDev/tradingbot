"""
import os
Directional Change (DC) Core Engine
====================================

Event-driven trading based on intrinsic time using directional change thresholds.
Implements the AlphaEngine methodology with overshoot mechanics and coastline strategy.

Key Concepts:
- DC Event: Price reversal exceeding threshold δ
- Overshoot (OS): Price continuation after DC event
- TMV: Total Move Value for position triggers
- Coastline: Counter-trending with cascading positions
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
import threading
from abc import ABC, abstractmethod
import numpy
import pandas

logger = logging.getLogger(__name__)


class DCDirection(Enum):
    """Direction of directional change event"""
    UPTURN = "upturn"
    DOWNTURN = "downturn"
    NONE = "none"


class TrendState(Enum):
    """Current trend state in DC framework"""
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    UNDEFINED = "undefined"


@dataclass
class DCEvent:
    """Represents a single directional change event"""
    timestamp: datetime
    direction: DCDirection
    threshold: float
    trigger_price: float
    extreme_price: float
    dc_price: float
    overshoot: float = 0.0
    tmv: float = 0.0
    duration_ticks: int = 0
    duration_time: timedelta = field(default_factory=lambda: timedelta(0))
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'direction': self.direction.value,
            'threshold': self.threshold,
            'trigger_price': self.trigger_price,
            'extreme_price': self.extreme_price,
            'dc_price': self.dc_price,
            'overshoot': self.overshoot,
            'tmv': self.tmv,
            'duration_ticks': self.duration_ticks,
            'confidence': self.confidence,
        }


@dataclass
class DCThreshold:
    """Configuration for DC threshold detection"""
    value: float  # Threshold percentage (e.g., 0.01 for 1%)
    name: str = ""
    min_ticks: int = 1  # Minimum ticks before DC confirmation
    max_lookback: int = 1000  # Maximum lookback for extreme detection
    adaptive: bool = False  # Whether to adapt threshold based on volatility
    
    def __post_init__(self):
        try:
            if not self.name:
                self.name = f"DC_{self.value*100:.2f}%"
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


@dataclass
class OvershootEvent:
    """Represents an overshoot event after DC"""
    dc_event: DCEvent
    overshoot_magnitude: float  # In units of threshold
    overshoot_price: float
    timestamp: datetime
    is_extreme: bool = False


@dataclass
class Position:
    """Trading position for coastline strategy"""
    entry_price: float
    size: float
    direction: str  # 'long' or 'short'
    entry_time: datetime
    cascade_level: int = 0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    unrealized_pnl: float = 0.0


class DCThresholdManager:
    """Manages multiple DC thresholds simultaneously"""
    
    def __init__(self, thresholds: List[float] = None):
        """
        Initialize with multiple thresholds
        
        Args:
            thresholds: List of threshold values (e.g., [0.005, 0.01, 0.02])
        """
        try:
            if thresholds is None:
                thresholds = [0.005, 0.01, 0.015, 0.02, 0.05]  # 0.5%, 1%, 1.5%, 2%, 5%
        
            self.thresholds = [DCThreshold(value=t) for t in thresholds]
            self.engines: Dict[float, 'DirectionalChangeDetector'] = {}
        
            for threshold in self.thresholds:
                self.engines[threshold.value] = DirectionalChangeDetector(threshold)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def process_price(self, price: float, timestamp: datetime) -> Dict[float, Optional[DCEvent]]:
        """Process price across all thresholds"""
        try:
            results = {}
            for threshold_value, engine in self.engines.items():
                event = engine.process_price(price, timestamp)
                results[threshold_value] = event
            return results
        except Exception as e:
            logger.error(f"Error in process_price: {e}")
            raise
    
    def get_consensus_signal(self) -> Tuple[DCDirection, float]:
        """Get consensus signal across all thresholds"""
        try:
            directions = []
            for engine in self.engines.values():
                if engine.current_trend != TrendState.UNDEFINED:
                    directions.append(engine.current_trend)
        
            if not directions:
                return DCDirection.NONE, 0.0
        
            uptrend_count = sum(1 for d in directions if d == TrendState.UPTREND)
            downtrend_count = sum(1 for d in directions if d == TrendState.DOWNTREND)
        
            total = len(directions)
            if uptrend_count > downtrend_count:
                return DCDirection.UPTURN, uptrend_count / total
            elif downtrend_count > uptrend_count:
                return DCDirection.DOWNTURN, downtrend_count / total
            else:
                return DCDirection.NONE, 0.5
        except Exception as e:
            logger.error(f"Error in get_consensus_signal: {e}")
            raise


class DirectionalChangeDetector:
    """Core DC event detection engine"""
    
    def __init__(self, threshold: DCThreshold):
        """
        Initialize DC detector
        
        Args:
            threshold: DC threshold configuration
        """
        try:
            self.threshold = threshold
            self.current_trend = TrendState.UNDEFINED
            self.extreme_price: Optional[float] = None
            self.extreme_time: Optional[datetime] = None
            self.dc_price: Optional[float] = None
            self.dc_time: Optional[datetime] = None
            self.tick_count = 0
            self.dc_tick_count = 0
        
            # Event history
            self.events: deque = deque(maxlen=1000)
            self.prices: deque = deque(maxlen=10000)
        
            # Statistics
            self.total_dc_events = 0
            self.total_overshoots = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def process_price(self, price: float, timestamp: datetime) -> Optional[DCEvent]:
        """
        Process a new price tick and detect DC events
        
        Args:
            price: Current price
            timestamp: Current timestamp
            
        Returns:
            DCEvent if a directional change occurred, None otherwise
        """
        try:
            self.prices.append((price, timestamp))
            self.tick_count += 1
        
            # Initialize on first price
            if self.extreme_price is None:
                self.extreme_price = price
                self.extreme_time = timestamp
                return None
        
            event = None
        
            if self.current_trend == TrendState.UNDEFINED:
                # Determine initial trend
                event = self._initialize_trend(price, timestamp)
            elif self.current_trend == TrendState.UPTREND:
                event = self._process_uptrend(price, timestamp)
            elif self.current_trend == TrendState.DOWNTREND:
                event = self._process_downtrend(price, timestamp)
        
            if event:
                self.events.append(event)
                self.total_dc_events += 1
                logger.info(f"DC Event: {event.direction.value} at {price:.5f}, "
                           f"threshold={self.threshold.value*100:.2f}%, TMV={event.tmv:.2f}")
        
            return event
        except Exception as e:
            logger.error(f"Error in process_price: {e}")
            raise
    
    def _initialize_trend(self, price: float, timestamp: datetime) -> Optional[DCEvent]:
        """Initialize trend direction based on first significant move"""
        try:
            up_change = (price - self.extreme_price) / self.extreme_price
            down_change = (self.extreme_price - price) / self.extreme_price
        
            if up_change >= self.threshold.value:
                self.current_trend = TrendState.UPTREND
                self.dc_price = price
                self.dc_time = timestamp
                self.dc_tick_count = self.tick_count
            
                event = DCEvent(
                    timestamp=timestamp,
                    direction=DCDirection.UPTURN,
                    threshold=self.threshold.value,
                    trigger_price=price,
                    extreme_price=self.extreme_price,
                    dc_price=price,
                    duration_ticks=self.tick_count,
                )
            
                # Update extreme for new trend
                self.extreme_price = price
                self.extreme_time = timestamp
            
                return event
            
            elif down_change >= self.threshold.value:
                self.current_trend = TrendState.DOWNTREND
                self.dc_price = price
                self.dc_time = timestamp
                self.dc_tick_count = self.tick_count
            
                event = DCEvent(
                    timestamp=timestamp,
                    direction=DCDirection.DOWNTURN,
                    threshold=self.threshold.value,
                    trigger_price=price,
                    extreme_price=self.extreme_price,
                    dc_price=price,
                    duration_ticks=self.tick_count,
                )
            
                # Update extreme for new trend
                self.extreme_price = price
                self.extreme_time = timestamp
            
                return event
        
            return None
        except Exception as e:
            logger.error(f"Error in _initialize_trend: {e}")
            raise
    
    def _process_uptrend(self, price: float, timestamp: datetime) -> Optional[DCEvent]:
        """Process price during uptrend - look for downturn"""
        # Update extreme if price makes new high
        try:
            if price > self.extreme_price:
                self.extreme_price = price
                self.extreme_time = timestamp
                return None
        
            # Check for downturn (reversal)
            down_change = (self.extreme_price - price) / self.extreme_price
        
            if down_change >= self.threshold.value:
                # Calculate overshoot from previous DC
                overshoot = self._calculate_overshoot()
                tmv = self._calculate_tmv()
            
                event = DCEvent(
                    timestamp=timestamp,
                    direction=DCDirection.DOWNTURN,
                    threshold=self.threshold.value,
                    trigger_price=price,
                    extreme_price=self.extreme_price,
                    dc_price=price,
                    overshoot=overshoot,
                    tmv=tmv,
                    duration_ticks=self.tick_count - self.dc_tick_count,
                    duration_time=timestamp - self.dc_time if self.dc_time else timedelta(0),
                )
            
                # Switch to downtrend
                self.current_trend = TrendState.DOWNTREND
                self.dc_price = price
                self.dc_time = timestamp
                self.dc_tick_count = self.tick_count
                self.extreme_price = price
                self.extreme_time = timestamp
            
                return event
        
            return None
        except Exception as e:
            logger.error(f"Error in _process_uptrend: {e}")
            raise
    
    def _process_downtrend(self, price: float, timestamp: datetime) -> Optional[DCEvent]:
        """Process price during downtrend - look for upturn"""
        # Update extreme if price makes new low
        try:
            if price < self.extreme_price:
                self.extreme_price = price
                self.extreme_time = timestamp
                return None
        
            # Check for upturn (reversal)
            up_change = (price - self.extreme_price) / self.extreme_price
        
            if up_change >= self.threshold.value:
                # Calculate overshoot from previous DC
                overshoot = self._calculate_overshoot()
                tmv = self._calculate_tmv()
            
                event = DCEvent(
                    timestamp=timestamp,
                    direction=DCDirection.UPTURN,
                    threshold=self.threshold.value,
                    trigger_price=price,
                    extreme_price=self.extreme_price,
                    dc_price=price,
                    overshoot=overshoot,
                    tmv=tmv,
                    duration_ticks=self.tick_count - self.dc_tick_count,
                    duration_time=timestamp - self.dc_time if self.dc_time else timedelta(0),
                )
            
                # Switch to uptrend
                self.current_trend = TrendState.UPTREND
                self.dc_price = price
                self.dc_time = timestamp
                self.dc_tick_count = self.tick_count
                self.extreme_price = price
                self.extreme_time = timestamp
            
                return event
        
            return None
        except Exception as e:
            logger.error(f"Error in _process_downtrend: {e}")
            raise
    
    def _calculate_overshoot(self) -> float:
        """Calculate overshoot in units of threshold"""
        try:
            if self.dc_price is None or self.extreme_price is None:
                return 0.0
        
            if self.current_trend == TrendState.UPTREND:
                # Overshoot is how far price went above DC price
                os_magnitude = (self.extreme_price - self.dc_price) / self.dc_price
            else:
                # Overshoot is how far price went below DC price
                os_magnitude = (self.dc_price - self.extreme_price) / self.dc_price
        
            # Return in units of threshold
            return os_magnitude / self.threshold.value if self.threshold.value > 0 else 0.0
        except Exception as e:
            logger.error(f"Error in _calculate_overshoot: {e}")
            raise
    
    def _calculate_tmv(self) -> float:
        """Calculate Total Move Value (TMV)"""
        # TMV = 1 (DC) + overshoot
        return 1.0 + self._calculate_overshoot()
    
    def get_current_overshoot(self, current_price: float) -> float:
        """Get current overshoot from last DC price"""
        try:
            if self.dc_price is None:
                return 0.0
        
            if self.current_trend == TrendState.UPTREND:
                os_magnitude = (current_price - self.dc_price) / self.dc_price
            else:
                os_magnitude = (self.dc_price - current_price) / self.dc_price
        
            return os_magnitude / self.threshold.value if self.threshold.value > 0 else 0.0
        except Exception as e:
            logger.error(f"Error in get_current_overshoot: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detector statistics"""
        return {
            'threshold': self.threshold.value,
            'total_events': self.total_dc_events,
            'current_trend': self.current_trend.value,
            'extreme_price': self.extreme_price,
            'dc_price': self.dc_price,
            'tick_count': self.tick_count,
        }


class OvershootCalculator:
    """
    Calculates and tracks overshoot events
    
    Implements the scaling law: ⟨ω⟩ ≈ δ
    Where ω is overshoot and δ is threshold
    """
    
    def __init__(self, threshold: float):
        try:
            self.threshold = threshold
            self.overshoots: List[OvershootEvent] = []
            self.expected_overshoot = threshold  # Scaling law expectation
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_overshoot(self, dc_event: DCEvent, current_price: float, 
                           timestamp: datetime) -> OvershootEvent:
        """Calculate overshoot from DC event"""
        try:
            if dc_event.direction == DCDirection.UPTURN:
                # In uptrend, overshoot is price above DC price
                os_price_diff = current_price - dc_event.dc_price
            else:
                # In downtrend, overshoot is price below DC price
                os_price_diff = dc_event.dc_price - current_price
        
            os_magnitude = os_price_diff / dc_event.dc_price / self.threshold
        
            event = OvershootEvent(
                dc_event=dc_event,
                overshoot_magnitude=os_magnitude,
                overshoot_price=current_price,
                timestamp=timestamp,
                is_extreme=os_magnitude > 2.0  # More than 2x threshold is extreme
            )
        
            self.overshoots.append(event)
            return event
        except Exception as e:
            logger.error(f"Error in calculate_overshoot: {e}")
            raise
    
    def get_mean_overshoot(self) -> float:
        """Get mean overshoot (should approximate threshold per scaling law)"""
        try:
            if not self.overshoots:
                return self.expected_overshoot
            return np.mean([os.overshoot_magnitude for os in self.overshoots])
        except Exception as e:
            logger.error(f"Error in get_mean_overshoot: {e}")
            raise
    
    def get_overshoot_distribution(self) -> Dict[str, float]:
        """Get overshoot distribution statistics"""
        try:
            if not self.overshoots:
                return {'mean': 0, 'std': 0, 'min': 0, 'max': 0}
        
            magnitudes = [os.overshoot_magnitude for os in self.overshoots]
            return {
                'mean': np.mean(magnitudes),
                'std': np.std(magnitudes),
                'min': np.min(magnitudes),
                'max': np.max(magnitudes),
                'count': len(magnitudes),
            }
        except Exception as e:
            logger.error(f"Error in get_overshoot_distribution: {e}")
            raise


class TMVCalculator:
    """
    Total Move Value (TMV) Calculator
    
    TMV = 1 + overshoot (in units of threshold)
    Used to trigger contrarian positions when TMV >= 2
    """
    
    def __init__(self, trigger_threshold: float = 2.0):
        """
        Initialize TMV calculator
        
        Args:
            trigger_threshold: TMV value to trigger position (default 2.0)
        """
        try:
            self.trigger_threshold = trigger_threshold
            self.tmv_history: List[Tuple[datetime, float]] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_tmv(self, dc_event: DCEvent, current_price: float) -> float:
        """Calculate current TMV"""
        try:
            if dc_event.direction == DCDirection.UPTURN:
                move = (current_price - dc_event.extreme_price) / dc_event.extreme_price
            else:
                move = (dc_event.extreme_price - current_price) / dc_event.extreme_price
        
            tmv = move / dc_event.threshold + 1.0
            return max(tmv, 1.0)
        except Exception as e:
            logger.error(f"Error in calculate_tmv: {e}")
            raise
    
    def should_trigger(self, tmv: float) -> bool:
        """Check if TMV exceeds trigger threshold"""
        return tmv >= self.trigger_threshold
    
    def get_signal_strength(self, tmv: float) -> float:
        """Get signal strength based on TMV (0-1 scale)"""
        try:
            if tmv < self.trigger_threshold:
                return 0.0
            # Normalize: TMV of 2 = 0.5, TMV of 3 = 0.75, TMV of 4 = 1.0
            return min((tmv - 1) / 3.0, 1.0)
        except Exception as e:
            logger.error(f"Error in get_signal_strength: {e}")
            raise


class CoastlineStrategy:
    """
    Coastline Trading Strategy
    
    Counter-trending approach with cascading/de-cascading position management.
    Opens contrarian positions when TMV >= 2 and manages with cascade rules.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize coastline strategy
        
        Args:
            config: Strategy configuration
        """
        try:
            self.config = config or {}
        
            # Position management
            self.positions: List[Position] = []
            self.max_cascade_levels = self.config.get('max_cascade_levels', 5)
            self.cascade_multiplier = self.config.get('cascade_multiplier', 1.5)
            self.base_position_size = self.config.get('base_position_size', 1.0)
        
            # TMV settings
            self.tmv_trigger = self.config.get('tmv_trigger', 2.0)
            self.tmv_calculator = TMVCalculator(self.tmv_trigger)
        
            # Risk settings
            self.max_total_exposure = self.config.get('max_total_exposure', 10.0)
            self.stop_loss_threshold = self.config.get('stop_loss_threshold', 0.03)  # 3%
            self.take_profit_threshold = self.config.get('take_profit_threshold', 0.02)  # 2%
        
            # State
            self.total_pnl = 0.0
            self.trade_count = 0
            self.winning_trades = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def process_dc_event(self, dc_event: DCEvent, current_price: float,
                        timestamp: datetime) -> Optional[Dict[str, Any]]:
        """
        Process DC event and generate trading signal
        
        Args:
            dc_event: The directional change event
            current_price: Current market price
            timestamp: Current timestamp
            
        Returns:
            Trading signal dict or None
        """
        try:
            tmv = self.tmv_calculator.calculate_tmv(dc_event, current_price)
        
            signal = None
        
            if self.tmv_calculator.should_trigger(tmv):
                # Generate contrarian signal
                signal = self._generate_contrarian_signal(dc_event, current_price, 
                                                          timestamp, tmv)
        
            # Update existing positions
            self._update_positions(current_price, timestamp)
        
            return signal
        except Exception as e:
            logger.error(f"Error in process_dc_event: {e}")
            raise
    
    def _generate_contrarian_signal(self, dc_event: DCEvent, current_price: float,
                                   timestamp: datetime, tmv: float) -> Dict[str, Any]:
        """Generate contrarian trading signal"""
        # Contrarian: opposite to DC direction
        try:
            if dc_event.direction == DCDirection.UPTURN:
                direction = 'short'  # Price went up, expect reversal down
            else:
                direction = 'long'  # Price went down, expect reversal up
        
            # Calculate position size based on TMV strength
            signal_strength = self.tmv_calculator.get_signal_strength(tmv)
            position_size = self.base_position_size * signal_strength
        
            # Check cascade level
            cascade_level = self._get_cascade_level(direction)
            if cascade_level < self.max_cascade_levels:
                position_size *= (self.cascade_multiplier ** cascade_level)
            else:
                # Max cascade reached, don't add more
                return None
        
            # Check total exposure
            current_exposure = self._get_total_exposure()
            if current_exposure + position_size > self.max_total_exposure:
                position_size = max(0, self.max_total_exposure - current_exposure)
                if position_size <= 0:
                    return None
        
            # Calculate stop loss and take profit
            if direction == 'long':
                stop_loss = current_price * (1 - self.stop_loss_threshold)
                take_profit = current_price * (1 + self.take_profit_threshold)
            else:
                stop_loss = current_price * (1 + self.stop_loss_threshold)
                take_profit = current_price * (1 - self.take_profit_threshold)
        
            signal = {
                'action': 'open',
                'direction': direction,
                'size': position_size,
                'price': current_price,
                'timestamp': timestamp,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'cascade_level': cascade_level,
                'tmv': tmv,
                'dc_threshold': dc_event.threshold,
                'confidence': signal_strength,
                'reason': f"Contrarian {direction} on TMV={tmv:.2f} after {dc_event.direction.value}",
            }
        
            # Create position
            position = Position(
                entry_price=current_price,
                size=position_size,
                direction=direction,
                entry_time=timestamp,
                cascade_level=cascade_level,
                stop_loss=stop_loss,
                take_profit=take_profit,
            )
            self.positions.append(position)
        
            return signal
        except Exception as e:
            logger.error(f"Error in _generate_contrarian_signal: {e}")
            raise
    
    def _get_cascade_level(self, direction: str) -> int:
        """Get current cascade level for direction"""
        try:
            same_direction = [p for p in self.positions if p.direction == direction]
            return len(same_direction)
        except Exception as e:
            logger.error(f"Error in _get_cascade_level: {e}")
            raise
    
    def _get_total_exposure(self) -> float:
        """Get total position exposure"""
        return sum(p.size for p in self.positions)
    
    def _update_positions(self, current_price: float, timestamp: datetime) -> List[Dict[str, Any]]:
        """Update positions and check for exits"""
        try:
            closed_positions = []
        
            for position in self.positions[:]:  # Copy list for safe iteration
                # Update unrealized P&L
                if position.direction == 'long':
                    position.unrealized_pnl = (current_price - position.entry_price) / position.entry_price
                else:
                    position.unrealized_pnl = (position.entry_price - current_price) / position.entry_price
            
                # Check stop loss
                if position.stop_loss:
                    if position.direction == 'long' and current_price <= position.stop_loss:
                        closed = self._close_position(position, current_price, timestamp, 'stop_loss')
                        closed_positions.append(closed)
                    elif position.direction == 'short' and current_price >= position.stop_loss:
                        closed = self._close_position(position, current_price, timestamp, 'stop_loss')
                        closed_positions.append(closed)
            
                # Check take profit
                if position.take_profit:
                    if position.direction == 'long' and current_price >= position.take_profit:
                        closed = self._close_position(position, current_price, timestamp, 'take_profit')
                        closed_positions.append(closed)
                    elif position.direction == 'short' and current_price <= position.take_profit:
                        closed = self._close_position(position, current_price, timestamp, 'take_profit')
                        closed_positions.append(closed)
        
            return closed_positions
        except Exception as e:
            logger.error(f"Error in _update_positions: {e}")
            raise
    
    def _close_position(self, position: Position, exit_price: float,
                       timestamp: datetime, reason: str) -> Dict[str, Any]:
        """Close a position"""
        try:
            if position.direction == 'long':
                pnl = (exit_price - position.entry_price) / position.entry_price * position.size
            else:
                pnl = (position.entry_price - exit_price) / position.entry_price * position.size
        
            self.total_pnl += pnl
            self.trade_count += 1
            if pnl > 0:
                self.winning_trades += 1
        
            self.positions.remove(position)
        
            return {
                'action': 'close',
                'direction': position.direction,
                'size': position.size,
                'entry_price': position.entry_price,
                'exit_price': exit_price,
                'pnl': pnl,
                'pnl_percent': pnl / position.size * 100,
                'reason': reason,
                'timestamp': timestamp,
                'hold_time': timestamp - position.entry_time,
            }
        except Exception as e:
            logger.error(f"Error in _close_position: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get strategy statistics"""
        try:
            win_rate = self.winning_trades / self.trade_count if self.trade_count > 0 else 0
        
            return {
                'total_pnl': self.total_pnl,
                'trade_count': self.trade_count,
                'winning_trades': self.winning_trades,
                'win_rate': win_rate,
                'open_positions': len(self.positions),
                'total_exposure': self._get_total_exposure(),
            }
        except Exception as e:
            logger.error(f"Error in get_statistics: {e}")
            raise


class DirectionalChangeEngine:
    """
    Main Directional Change Engine
    
    Combines DC detection, overshoot calculation, TMV triggers,
    and coastline strategy into a unified trading engine.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize DC Engine
        
        Args:
            config: Engine configuration
        """
        try:
            self.config = config or {}
        
            # Thresholds
            self.thresholds = self.config.get('thresholds', [0.005, 0.01, 0.015, 0.02])
            self.primary_threshold = self.config.get('primary_threshold', 0.01)
        
            # Initialize components
            self.threshold_manager = DCThresholdManager(self.thresholds)
            self.primary_detector = DirectionalChangeDetector(
                DCThreshold(value=self.primary_threshold)
            )
            self.overshoot_calc = OvershootCalculator(self.primary_threshold)
            self.tmv_calc = TMVCalculator(self.config.get('tmv_trigger', 2.0))
            self.coastline = CoastlineStrategy(self.config.get('coastline_config', {}))
        
            # State
            self.current_price: Optional[float] = None
            self.last_dc_event: Optional[DCEvent] = None
            self.signals: List[Dict[str, Any]] = []
        
            # Callbacks
            self.on_dc_event: Optional[Callable[[DCEvent], None]] = None
            self.on_signal: Optional[Callable[[Dict[str, Any]], None]] = None
        
            logger.info(f"DC Engine initialized with thresholds: {self.thresholds}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def process_tick(self, price: float, timestamp: datetime = None) -> Optional[Dict[str, Any]]:
        """
        Process a price tick
        
        Args:
            price: Current price
            timestamp: Current timestamp (defaults to now)
            
        Returns:
            Trading signal if generated, None otherwise
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
        
            self.current_price = price
        
            # Process through primary detector
            dc_event = self.primary_detector.process_price(price, timestamp)
        
            # Process through all thresholds for consensus
            multi_events = self.threshold_manager.process_price(price, timestamp)
        
            signal = None
        
            if dc_event:
                self.last_dc_event = dc_event
            
                # Callback
                if self.on_dc_event:
                    self.on_dc_event(dc_event)
            
                # Generate trading signal through coastline strategy
                signal = self.coastline.process_dc_event(dc_event, price, timestamp)
            
                if signal:
                    # Enhance signal with multi-threshold consensus
                    consensus_dir, consensus_conf = self.threshold_manager.get_consensus_signal()
                    signal['consensus_direction'] = consensus_dir.value
                    signal['consensus_confidence'] = consensus_conf
                
                    # Adjust confidence based on consensus
                    if consensus_dir.value == signal['direction'] or \
                       (consensus_dir == DCDirection.UPTURN and signal['direction'] == 'short') or \
                       (consensus_dir == DCDirection.DOWNTURN and signal['direction'] == 'long'):
                        signal['confidence'] *= (0.5 + 0.5 * consensus_conf)
                
                    self.signals.append(signal)
                
                    # Callback
                    if self.on_signal:
                        self.on_signal(signal)
        
            return signal
        except Exception as e:
            logger.error(f"Error in process_tick: {e}")
            raise
    
    def process_ohlcv(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Process OHLCV DataFrame
        
        Args:
            df: DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            
        Returns:
            List of generated signals
        """
        try:
            signals = []
        
            for idx, row in df.iterrows():
                timestamp = row.get('timestamp', idx)
                if isinstance(timestamp, str):
                    timestamp = pd.to_datetime(timestamp)
                elif not isinstance(timestamp, datetime):
                    timestamp = datetime.now()
            
                # Process high and low for intrabar DC detection
                signal = self.process_tick(row['high'], timestamp)
                if signal:
                    signals.append(signal)
            
                signal = self.process_tick(row['low'], timestamp)
                if signal:
                    signals.append(signal)
            
                # Process close
                signal = self.process_tick(row['close'], timestamp)
                if signal:
                    signals.append(signal)
        
            return signals
        except Exception as e:
            logger.error(f"Error in process_ohlcv: {e}")
            raise
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current engine state"""
        return {
            'current_price': self.current_price,
            'current_trend': self.primary_detector.current_trend.value,
            'extreme_price': self.primary_detector.extreme_price,
            'dc_price': self.primary_detector.dc_price,
            'last_dc_event': self.last_dc_event.to_dict() if self.last_dc_event else None,
            'current_overshoot': self.primary_detector.get_current_overshoot(self.current_price) 
                                if self.current_price else 0,
            'open_positions': len(self.coastline.positions),
            'total_exposure': self.coastline._get_total_exposure(),
            'statistics': self.get_statistics(),
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        try:
            detector_stats = self.primary_detector.get_statistics()
            coastline_stats = self.coastline.get_statistics()
            overshoot_stats = self.overshoot_calc.get_overshoot_distribution()
        
            return {
                'detector': detector_stats,
                'coastline': coastline_stats,
                'overshoot': overshoot_stats,
                'total_signals': len(self.signals),
            }
        except Exception as e:
            logger.error(f"Error in get_statistics: {e}")
            raise
    
    def reset(self):
        """Reset engine state"""
        try:
            self.threshold_manager = DCThresholdManager(self.thresholds)
            self.primary_detector = DirectionalChangeDetector(
                DCThreshold(value=self.primary_threshold)
            )
            self.overshoot_calc = OvershootCalculator(self.primary_threshold)
            self.coastline = CoastlineStrategy(self.config.get('coastline_config', {}))
            self.current_price = None
            self.last_dc_event = None
            self.signals = []
        
            logger.info("DC Engine reset")
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise


# Utility functions
def calculate_optimal_threshold(prices: np.ndarray, target_events_per_day: int = 10) -> float:
    """
    Calculate optimal DC threshold for target event frequency
    
    Args:
        prices: Array of prices
        target_events_per_day: Desired number of DC events per day
        
    Returns:
        Optimal threshold value
    """
    # Binary search for optimal threshold
    try:
        low, high = 0.001, 0.1
    
        while high - low > 0.0001:
            mid = (low + high) / 2
            detector = DirectionalChangeDetector(DCThreshold(value=mid))
        
            for i, price in enumerate(prices):
                detector.process_price(price, datetime.now() + timedelta(minutes=i))
        
            events_per_day = detector.total_dc_events / (len(prices) / 1440)  # Assuming minute data
        
            if events_per_day > target_events_per_day:
                low = mid
            else:
                high = mid
    
        return mid
    except Exception as e:
        logger.error(f"Error in calculate_optimal_threshold: {e}")
        raise


def analyze_dc_scaling_law(prices: np.ndarray, thresholds: List[float]) -> Dict[str, Any]:
    """
    Analyze DC scaling law: ⟨ω⟩ ≈ δ
    
    Args:
        prices: Array of prices
        thresholds: List of thresholds to test
        
    Returns:
        Analysis results
    """
    try:
        results = {}
    
        for threshold in thresholds:
            detector = DirectionalChangeDetector(DCThreshold(value=threshold))
            overshoot_calc = OvershootCalculator(threshold)
        
            for i, price in enumerate(prices):
                event = detector.process_price(price, datetime.now() + timedelta(minutes=i))
                if event:
                    overshoot_calc.calculate_overshoot(event, price, datetime.now())
        
            mean_overshoot = overshoot_calc.get_mean_overshoot()
            results[threshold] = {
                'threshold': threshold,
                'mean_overshoot': mean_overshoot,
                'scaling_ratio': mean_overshoot / threshold if threshold > 0 else 0,
                'event_count': detector.total_dc_events,
            }
    
        return results
    except Exception as e:
        logger.error(f"Error in analyze_dc_scaling_law: {e}")
        raise
