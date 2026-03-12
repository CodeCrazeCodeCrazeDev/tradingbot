"""
Enhanced Directional Change Core Module
========================================

Advanced DC Framework with:
- Multi-threshold event detection
- Overshoot exploitation (scaling law: ⟨ω⟩ ≈ δ)
- TMV (Total Move Value) triggers
- Coastline strategy with cascading/de-cascading
- Market-making through overshoot trading
- Mean-reversion positioning at extremes
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import math
import numpy
import pandas

logger = logging.getLogger(__name__)


class DCDirection(Enum):
    """Directional change direction"""
    UPTURN = "upturn"
    DOWNTURN = "downturn"
    NEUTRAL = "neutral"


class DCPhase(Enum):
    """Current phase in DC cycle"""
    DC_CONFIRMATION = "dc_confirmation"  # Just confirmed a DC
    OVERSHOOT = "overshoot"  # In overshoot phase
    EXTREME_OVERSHOOT = "extreme_overshoot"  # Extreme overshoot (mean reversion opportunity)


class TradingMode(Enum):
    """Trading mode based on DC signals"""
    TREND_FOLLOWING = "trend_following"
    CONTRARIAN = "contrarian"
    MARKET_MAKING = "market_making"
    WAITING = "waiting"


@dataclass
class DCEvent:
    """Directional Change Event"""
    timestamp: datetime
    direction: DCDirection
    threshold: float
    start_price: float
    end_price: float
    duration_ticks: int
    duration_seconds: float
    
    # Overshoot metrics
    overshoot_magnitude: float = 0.0
    overshoot_ticks: int = 0
    
    # TMV metrics
    tmv: float = 0.0
    
    # Confirmation
    confirmed: bool = False
    
    def __post_init__(self):
        """Calculate derived metrics"""
        if self.start_price > 0:
            self.price_change = (self.end_price - self.start_price) / self.start_price
        else:
            self.price_change = 0


@dataclass
class OvershootEvent:
    """Overshoot Event following a DC"""
    dc_event: DCEvent
    start_price: float
    current_price: float
    peak_price: float
    magnitude: float  # As multiple of threshold
    ticks: int
    is_extreme: bool  # magnitude > 2 * threshold
    
    @property
    def expected_magnitude(self) -> float:
        """Expected overshoot magnitude based on scaling law ⟨ω⟩ ≈ δ"""
        return self.dc_event.threshold
    
    @property
    def deviation_from_expected(self) -> float:
        """How much overshoot deviates from expected"""
        return self.magnitude - self.expected_magnitude


@dataclass
class TMVSignal:
    """Total Move Value Signal"""
    timestamp: datetime
    tmv: float
    threshold: float
    direction: DCDirection
    signal_strength: float  # 0 to 1
    should_trade: bool
    position_type: str  # 'contrarian' or 'trend'
    
    @property
    def is_valid(self) -> bool:
        """TMV >= 2 is valid contrarian signal"""
        return self.tmv >= 2.0


@dataclass
class CoastlinePosition:
    """Position in coastline strategy"""
    entry_price: float
    entry_time: datetime
    direction: str  # 'long' or 'short'
    size: float
    cascade_level: int  # 0 = initial, 1+ = cascaded
    stop_loss: float
    take_profit: float
    dc_threshold: float
    
    # P&L tracking
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    is_open: bool = True


class EnhancedDCDetector:
    """
    Enhanced Directional Change Detector
    
    Features:
    - Multi-threshold detection (0.5%, 1%, 2%, etc.)
    - Intrinsic time calculation
    - Event-driven architecture
    """
    
    def __init__(self, thresholds: List[float] = None):
        """
        Initialize detector
        
        Args:
            thresholds: List of DC thresholds (e.g., [0.005, 0.01, 0.02])
        """
        self.thresholds = thresholds or [0.005, 0.01, 0.02]
        
        # State per threshold
        self.states: Dict[float, Dict[str, Any]] = {}
        for threshold in self.thresholds:
            self.states[threshold] = {
                'direction': DCDirection.NEUTRAL,
                'extreme_price': 0.0,
                'extreme_time': None,
                'last_dc_price': 0.0,
                'last_dc_time': None,
                'tick_count': 0,
                'dc_count': 0,
            }
        
        # Event history
        self.events: Dict[float, deque] = {t: deque(maxlen=1000) for t in self.thresholds}
        
        # Price history
        self.prices: deque = deque(maxlen=100000)
        self.timestamps: deque = deque(maxlen=100000)
        
        # Intrinsic time
        self.intrinsic_time: Dict[float, int] = {t: 0 for t in self.thresholds}
    
    def process_tick(self, price: float, timestamp: datetime = None) -> Dict[float, Optional[DCEvent]]:
        """
        Process a price tick
        
        Args:
            price: Current price
            timestamp: Tick timestamp
            
        Returns:
            Dictionary of threshold -> DCEvent (if triggered)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        self.prices.append(price)
        self.timestamps.append(timestamp)
        
        events = {}
        
        for threshold in self.thresholds:
            event = self._process_threshold(price, timestamp, threshold)
            events[threshold] = event
            
            if event:
                self.events[threshold].append(event)
                self.intrinsic_time[threshold] += 1
        
        return events
    
    def _process_threshold(self, price: float, timestamp: datetime, 
                          threshold: float) -> Optional[DCEvent]:
        """Process tick for specific threshold"""
        state = self.states[threshold]
        
        # Initialize if first tick
        if state['extreme_price'] == 0:
            state['extreme_price'] = price
            state['extreme_time'] = timestamp
            state['last_dc_price'] = price
            state['last_dc_time'] = timestamp
            return None
        
        state['tick_count'] += 1
        
        # Check for directional change
        if state['direction'] == DCDirection.NEUTRAL:
            # Determine initial direction
            change = (price - state['extreme_price']) / state['extreme_price']
            if change >= threshold:
                state['direction'] = DCDirection.UPTURN
                state['extreme_price'] = price
                state['extreme_time'] = timestamp
            elif change <= -threshold:
                state['direction'] = DCDirection.DOWNTURN
                state['extreme_price'] = price
                state['extreme_time'] = timestamp
            return None
        
        elif state['direction'] == DCDirection.UPTURN:
            # Update extreme if price continues up
            if price > state['extreme_price']:
                state['extreme_price'] = price
                state['extreme_time'] = timestamp
            
            # Check for downturn
            change = (price - state['extreme_price']) / state['extreme_price']
            if change <= -threshold:
                # DC confirmed - create event
                event = DCEvent(
                    timestamp=timestamp,
                    direction=DCDirection.DOWNTURN,
                    threshold=threshold,
                    start_price=state['last_dc_price'],
                    end_price=state['extreme_price'],
                    duration_ticks=state['tick_count'],
                    duration_seconds=(timestamp - state['last_dc_time']).total_seconds() if state['last_dc_time'] else 0,
                    confirmed=True,
                )
                
                # Update state
                state['direction'] = DCDirection.DOWNTURN
                state['last_dc_price'] = state['extreme_price']
                state['last_dc_time'] = state['extreme_time']
                state['extreme_price'] = price
                state['extreme_time'] = timestamp
                state['tick_count'] = 0
                state['dc_count'] += 1
                
                return event
        
        elif state['direction'] == DCDirection.DOWNTURN:
            # Update extreme if price continues down
            if price < state['extreme_price']:
                state['extreme_price'] = price
                state['extreme_time'] = timestamp
            
            # Check for upturn
            change = (price - state['extreme_price']) / state['extreme_price']
            if change >= threshold:
                # DC confirmed - create event
                event = DCEvent(
                    timestamp=timestamp,
                    direction=DCDirection.UPTURN,
                    threshold=threshold,
                    start_price=state['last_dc_price'],
                    end_price=state['extreme_price'],
                    duration_ticks=state['tick_count'],
                    duration_seconds=(timestamp - state['last_dc_time']).total_seconds() if state['last_dc_time'] else 0,
                    confirmed=True,
                )
                
                # Update state
                state['direction'] = DCDirection.UPTURN
                state['last_dc_price'] = state['extreme_price']
                state['last_dc_time'] = state['extreme_time']
                state['extreme_price'] = price
                state['extreme_time'] = timestamp
                state['tick_count'] = 0
                state['dc_count'] += 1
                
                return event
        
        return None
    
    def get_current_state(self, threshold: float) -> Dict[str, Any]:
        """Get current state for threshold"""
        return self.states.get(threshold, {})
    
    def get_recent_events(self, threshold: float, n: int = 10) -> List[DCEvent]:
        """Get recent events for threshold"""
        return list(self.events.get(threshold, []))[-n:]
    
    def get_intrinsic_time(self, threshold: float) -> int:
        """Get intrinsic time (number of DC events)"""
        return self.intrinsic_time.get(threshold, 0)


class OvershootCalculator:
    """
    Calculates and tracks overshoot following DC events
    
    Exploits scaling law: ⟨ω⟩ ≈ δ (expected overshoot ≈ threshold)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Overshoot history
        self.overshoots: Dict[float, deque] = {}
        
        # Current overshoot tracking
        self.current_overshoots: Dict[float, Optional[OvershootEvent]] = {}
        
        # Extreme threshold (for mean reversion signals)
        self.extreme_multiplier = self.config.get('extreme_multiplier', 2.0)
    
    def update(self, dc_event: DCEvent, current_price: float) -> Optional[OvershootEvent]:
        """
        Update overshoot calculation after DC event
        
        Args:
            dc_event: The DC event
            current_price: Current price
            
        Returns:
            OvershootEvent if in overshoot phase
        """
        threshold = dc_event.threshold
        
        if threshold not in self.overshoots:
            self.overshoots[threshold] = deque(maxlen=1000)
        
        # Calculate overshoot
        if dc_event.direction == DCDirection.UPTURN:
            # After upturn DC, overshoot is further upward movement
            overshoot_price = current_price - dc_event.end_price
            peak_price = max(current_price, dc_event.end_price)
        else:
            # After downturn DC, overshoot is further downward movement
            overshoot_price = dc_event.end_price - current_price
            peak_price = min(current_price, dc_event.end_price)
        
        # Calculate magnitude as multiple of threshold
        magnitude = abs(overshoot_price / dc_event.end_price) / threshold if dc_event.end_price > 0 else 0
        
        # Check if extreme
        is_extreme = magnitude >= self.extreme_multiplier
        
        overshoot = OvershootEvent(
            dc_event=dc_event,
            start_price=dc_event.end_price,
            current_price=current_price,
            peak_price=peak_price,
            magnitude=magnitude,
            ticks=0,  # Would need tick tracking
            is_extreme=is_extreme,
        )
        
        self.current_overshoots[threshold] = overshoot
        
        return overshoot
    
    def get_mean_reversion_signal(self, threshold: float) -> Optional[Dict[str, Any]]:
        """
        Get mean reversion signal when overshoot is extreme
        
        Returns:
            Signal dict if extreme overshoot detected
        """
        overshoot = self.current_overshoots.get(threshold)
        
        if overshoot and overshoot.is_extreme:
            # Contrarian signal
            if overshoot.dc_event.direction == DCDirection.UPTURN:
                # Extreme upward overshoot -> expect reversal down
                signal_direction = 'short'
            else:
                # Extreme downward overshoot -> expect reversal up
                signal_direction = 'long'
            
            return {
                'signal': signal_direction,
                'strength': min(overshoot.magnitude / 3, 1.0),
                'overshoot_magnitude': overshoot.magnitude,
                'expected_magnitude': overshoot.expected_magnitude,
                'deviation': overshoot.deviation_from_expected,
                'reasoning': f"Extreme overshoot ({overshoot.magnitude:.2f}x) suggests mean reversion",
            }
        
        return None
    
    def get_statistics(self, threshold: float) -> Dict[str, float]:
        """Get overshoot statistics for threshold"""
        overshoots = list(self.overshoots.get(threshold, []))
        
        if not overshoots:
            return {}
        
        magnitudes = [o.magnitude for o in overshoots]
        
        return {
            'mean_overshoot': np.mean(magnitudes),
            'std_overshoot': np.std(magnitudes),
            'max_overshoot': max(magnitudes),
            'min_overshoot': min(magnitudes),
            'expected_overshoot': threshold,  # Scaling law
            'count': len(overshoots),
        }


class TMVCalculator:
    """
    Total Move Value Calculator
    
    TMV = sum of all DC moves in intrinsic time
    TMV >= 2 triggers contrarian position
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # TMV history per threshold
        self.tmv_history: Dict[float, deque] = {}
        
        # Current TMV
        self.current_tmv: Dict[float, float] = {}
        
        # TMV trigger threshold
        self.trigger_threshold = self.config.get('trigger_threshold', 2.0)
        
        # Lookback for TMV calculation
        self.lookback_events = self.config.get('lookback_events', 10)
    
    def calculate(self, events: List[DCEvent], threshold: float) -> TMVSignal:
        """
        Calculate TMV from recent DC events
        
        Args:
            events: List of recent DC events
            threshold: DC threshold
            
        Returns:
            TMVSignal
        """
        if not events:
            return TMVSignal(
                timestamp=datetime.now(),
                tmv=0,
                threshold=threshold,
                direction=DCDirection.NEUTRAL,
                signal_strength=0,
                should_trade=False,
                position_type='none',
            )
        
        # Calculate TMV as sum of moves normalized by threshold
        tmv = 0
        for event in events[-self.lookback_events:]:
            move = abs(event.price_change) / threshold
            tmv += move
        
        self.current_tmv[threshold] = tmv
        
        if threshold not in self.tmv_history:
            self.tmv_history[threshold] = deque(maxlen=1000)
        self.tmv_history[threshold].append(tmv)
        
        # Determine signal
        latest_event = events[-1]
        should_trade = tmv >= self.trigger_threshold
        
        # Contrarian: trade opposite to last DC direction
        if latest_event.direction == DCDirection.UPTURN:
            position_type = 'short'  # Contrarian short after upturn
        elif latest_event.direction == DCDirection.DOWNTURN:
            position_type = 'long'  # Contrarian long after downturn
        else:
            position_type = 'none'
        
        signal_strength = min(tmv / 4, 1.0)  # Normalize to 0-1
        
        return TMVSignal(
            timestamp=datetime.now(),
            tmv=tmv,
            threshold=threshold,
            direction=latest_event.direction,
            signal_strength=signal_strength,
            should_trade=should_trade,
            position_type=position_type if should_trade else 'none',
        )
    
    def get_current_tmv(self, threshold: float) -> float:
        """Get current TMV for threshold"""
        return self.current_tmv.get(threshold, 0)


class CoastlineStrategy:
    """
    Coastline Trading Strategy
    
    Counter-trending approach with:
    - Cascading: Add to position when price moves against
    - De-cascading: Take profits when price moves favorably
    - Position management based on DC events
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Position management
        self.positions: List[CoastlinePosition] = []
        self.max_cascade_levels = self.config.get('max_cascade_levels', 5)
        self.cascade_multiplier = self.config.get('cascade_multiplier', 1.5)
        
        # Risk parameters
        self.base_position_size = self.config.get('base_position_size', 1.0)
        self.max_total_exposure = self.config.get('max_total_exposure', 10.0)
        
        # P&L tracking
        self.total_realized_pnl = 0.0
        self.trade_history: deque = deque(maxlen=1000)
    
    def should_open_position(self, tmv_signal: TMVSignal, 
                            overshoot: Optional[OvershootEvent] = None) -> Dict[str, Any]:
        """
        Determine if should open new position
        
        Args:
            tmv_signal: TMV signal
            overshoot: Current overshoot event
            
        Returns:
            Position recommendation
        """
        if not tmv_signal.should_trade:
            return {'should_open': False, 'reason': 'TMV below threshold'}
        
        # Check current exposure
        current_exposure = sum(p.size for p in self.positions if p.is_open)
        if current_exposure >= self.max_total_exposure:
            return {'should_open': False, 'reason': 'Max exposure reached'}
        
        # Calculate position size
        base_size = self.base_position_size
        
        # Adjust for TMV strength
        size_multiplier = min(tmv_signal.tmv / 2, 2.0)
        
        # Adjust for overshoot if extreme
        if overshoot and overshoot.is_extreme:
            size_multiplier *= 1.2  # Increase size for extreme overshoot
        
        position_size = base_size * size_multiplier
        
        return {
            'should_open': True,
            'direction': tmv_signal.position_type,
            'size': position_size,
            'threshold': tmv_signal.threshold,
            'tmv': tmv_signal.tmv,
            'reason': f'TMV={tmv_signal.tmv:.2f} >= {self.config.get("trigger_threshold", 2.0)}',
        }
    
    def open_position(self, price: float, direction: str, size: float,
                     threshold: float, cascade_level: int = 0) -> CoastlinePosition:
        """Open a new position"""
        # Calculate stop loss and take profit based on threshold
        if direction == 'long':
            stop_loss = price * (1 - threshold * 2)
            take_profit = price * (1 + threshold * 3)
        else:
            stop_loss = price * (1 + threshold * 2)
            take_profit = price * (1 - threshold * 3)
        
        position = CoastlinePosition(
            entry_price=price,
            entry_time=datetime.now(),
            direction=direction,
            size=size,
            cascade_level=cascade_level,
            stop_loss=stop_loss,
            take_profit=take_profit,
            dc_threshold=threshold,
        )
        
        self.positions.append(position)
        logger.info(f"Opened {direction} position: size={size}, price={price}, cascade={cascade_level}")
        
        return position
    
    def should_cascade(self, position: CoastlinePosition, current_price: float) -> Dict[str, Any]:
        """
        Determine if should cascade (add to losing position)
        
        Cascading: Add when price moves against position by threshold amount
        """
        if position.cascade_level >= self.max_cascade_levels:
            return {'should_cascade': False, 'reason': 'Max cascade level reached'}
        
        threshold = position.dc_threshold
        
        if position.direction == 'long':
            price_move = (current_price - position.entry_price) / position.entry_price
            should_cascade = price_move <= -threshold
        else:
            price_move = (position.entry_price - current_price) / position.entry_price
            should_cascade = price_move <= -threshold
        
        if should_cascade:
            new_size = position.size * self.cascade_multiplier
            return {
                'should_cascade': True,
                'new_size': new_size,
                'cascade_level': position.cascade_level + 1,
                'price_move': price_move,
                'reason': f'Price moved {price_move*100:.2f}% against position',
            }
        
        return {'should_cascade': False, 'reason': 'Price within threshold'}
    
    def should_decascade(self, position: CoastlinePosition, current_price: float) -> Dict[str, Any]:
        """
        Determine if should de-cascade (take partial profits)
        
        De-cascading: Take profits when price moves favorably by threshold amount
        """
        threshold = position.dc_threshold
        
        if position.direction == 'long':
            price_move = (current_price - position.entry_price) / position.entry_price
            should_decascade = price_move >= threshold
        else:
            price_move = (position.entry_price - current_price) / position.entry_price
            should_decascade = price_move >= threshold
        
        if should_decascade:
            # Take 50% off
            close_size = position.size * 0.5
            return {
                'should_decascade': True,
                'close_size': close_size,
                'remaining_size': position.size - close_size,
                'price_move': price_move,
                'reason': f'Price moved {price_move*100:.2f}% in favor',
            }
        
        return {'should_decascade': False, 'reason': 'Price within threshold'}
    
    def update_positions(self, current_price: float) -> List[Dict[str, Any]]:
        """
        Update all positions and return actions to take
        
        Returns:
            List of actions (cascade, decascade, close)
        """
        actions = []
        
        for position in self.positions:
            if not position.is_open:
                continue
            
            # Update unrealized P&L
            if position.direction == 'long':
                position.unrealized_pnl = (current_price - position.entry_price) * position.size
            else:
                position.unrealized_pnl = (position.entry_price - current_price) * position.size
            
            # Check stop loss
            if position.direction == 'long' and current_price <= position.stop_loss:
                actions.append({
                    'action': 'close',
                    'position': position,
                    'reason': 'stop_loss',
                    'price': current_price,
                })
            elif position.direction == 'short' and current_price >= position.stop_loss:
                actions.append({
                    'action': 'close',
                    'position': position,
                    'reason': 'stop_loss',
                    'price': current_price,
                })
            
            # Check take profit
            elif position.direction == 'long' and current_price >= position.take_profit:
                actions.append({
                    'action': 'close',
                    'position': position,
                    'reason': 'take_profit',
                    'price': current_price,
                })
            elif position.direction == 'short' and current_price <= position.take_profit:
                actions.append({
                    'action': 'close',
                    'position': position,
                    'reason': 'take_profit',
                    'price': current_price,
                })
            
            # Check cascade
            else:
                cascade_check = self.should_cascade(position, current_price)
                if cascade_check['should_cascade']:
                    actions.append({
                        'action': 'cascade',
                        'position': position,
                        **cascade_check,
                    })
                
                # Check de-cascade
                decascade_check = self.should_decascade(position, current_price)
                if decascade_check['should_decascade']:
                    actions.append({
                        'action': 'decascade',
                        'position': position,
                        **decascade_check,
                    })
        
        return actions
    
    def close_position(self, position: CoastlinePosition, price: float, reason: str):
        """Close a position"""
        if position.direction == 'long':
            pnl = (price - position.entry_price) * position.size
        else:
            pnl = (position.entry_price - price) * position.size
        
        position.realized_pnl = pnl
        position.is_open = False
        self.total_realized_pnl += pnl
        
        self.trade_history.append({
            'timestamp': datetime.now(),
            'direction': position.direction,
            'entry_price': position.entry_price,
            'exit_price': price,
            'size': position.size,
            'pnl': pnl,
            'reason': reason,
            'cascade_level': position.cascade_level,
        })
        
        logger.info(f"Closed {position.direction} position: pnl={pnl:.2f}, reason={reason}")
    
    def get_total_exposure(self) -> float:
        """Get total open exposure"""
        return sum(p.size for p in self.positions if p.is_open)
    
    def get_total_unrealized_pnl(self) -> float:
        """Get total unrealized P&L"""
        return sum(p.unrealized_pnl for p in self.positions if p.is_open)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get strategy statistics"""
        trades = list(self.trade_history)
        
        if not trades:
            return {}
        
        pnls = [t['pnl'] for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': len(wins) / len(trades) if trades else 0,
            'total_pnl': sum(pnls),
            'avg_win': np.mean(wins) if wins else 0,
            'avg_loss': np.mean(losses) if losses else 0,
            'profit_factor': sum(wins) / abs(sum(losses)) if losses else float('inf'),
            'max_cascade_used': max(t['cascade_level'] for t in trades) if trades else 0,
        }


class MarketMakingEngine:
    """
    Market Making through Overshoot Trading
    
    Provides liquidity by:
    - Quoting around expected overshoot levels
    - Capturing spread during mean reversion
    - Managing inventory risk
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Quote parameters
        self.base_spread = self.config.get('base_spread', 0.001)  # 10 bps
        self.quote_size = self.config.get('quote_size', 1.0)
        
        # Inventory management
        self.inventory = 0.0
        self.max_inventory = self.config.get('max_inventory', 10.0)
        self.inventory_skew = self.config.get('inventory_skew', 0.0001)  # Skew per unit
        
        # Performance tracking
        self.quotes_placed = 0
        self.quotes_filled = 0
        self.spread_captured = 0.0
    
    def calculate_quotes(self, mid_price: float, overshoot: Optional[OvershootEvent],
                        volatility: float) -> Dict[str, Any]:
        """
        Calculate bid/ask quotes
        
        Args:
            mid_price: Current mid price
            overshoot: Current overshoot event
            volatility: Current volatility
            
        Returns:
            Quote levels
        """
        # Base spread adjusted for volatility
        spread = self.base_spread * (1 + volatility * 10)
        
        # Inventory skew
        inventory_adjustment = self.inventory * self.inventory_skew
        
        # Overshoot adjustment
        overshoot_adjustment = 0
        if overshoot:
            if overshoot.is_extreme:
                # Widen spread during extreme overshoot
                spread *= 1.5
            
            # Skew quotes based on expected mean reversion
            if overshoot.dc_event.direction == DCDirection.UPTURN:
                # Expect down move, skew bid lower
                overshoot_adjustment = -spread * 0.2
            else:
                # Expect up move, skew ask higher
                overshoot_adjustment = spread * 0.2
        
        half_spread = spread / 2
        
        bid_price = mid_price - half_spread - inventory_adjustment + overshoot_adjustment
        ask_price = mid_price + half_spread - inventory_adjustment + overshoot_adjustment
        
        return {
            'bid_price': bid_price,
            'ask_price': ask_price,
            'bid_size': self.quote_size,
            'ask_size': self.quote_size,
            'spread': spread,
            'mid_price': mid_price,
            'inventory_skew': inventory_adjustment,
            'overshoot_skew': overshoot_adjustment,
        }
    
    def on_fill(self, side: str, price: float, size: float):
        """Handle quote fill"""
        if side == 'bid':
            self.inventory += size
        else:
            self.inventory -= size
        
        self.quotes_filled += 1
    
    def get_inventory_risk(self) -> float:
        """Get current inventory risk"""
        return abs(self.inventory) / self.max_inventory if self.max_inventory > 0 else 0


class EnhancedDCEngine:
    """
    Main Enhanced DC Engine
    
    Integrates all DC components:
    - Multi-threshold detection
    - Overshoot calculation
    - TMV signals
    - Coastline strategy
    - Market making
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize components
        thresholds = self.config.get('thresholds', [0.005, 0.01, 0.02])
        
        self.detector = EnhancedDCDetector(thresholds)
        self.overshoot_calc = OvershootCalculator(self.config.get('overshoot', {}))
        self.tmv_calc = TMVCalculator(self.config.get('tmv', {}))
        self.coastline = CoastlineStrategy(self.config.get('coastline', {}))
        self.market_maker = MarketMakingEngine(self.config.get('market_making', {}))
        
        # Current state
        self.current_price = 0.0
        self.current_volatility = 0.02
        
        # Signal history
        self.signals: deque = deque(maxlen=1000)
    
    def process_tick(self, price: float, timestamp: datetime = None) -> Dict[str, Any]:
        """
        Process a price tick through all components
        
        Args:
            price: Current price
            timestamp: Tick timestamp
            
        Returns:
            Comprehensive signal dictionary
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        self.current_price = price
        
        # Detect DC events
        dc_events = self.detector.process_tick(price, timestamp)
        
        result = {
            'timestamp': timestamp,
            'price': price,
            'dc_events': {},
            'overshoots': {},
            'tmv_signals': {},
            'coastline_actions': [],
            'market_making_quotes': None,
            'trading_signal': None,
        }
        
        # Process each threshold
        for threshold, event in dc_events.items():
            if event:
                result['dc_events'][threshold] = event
                
                # Calculate overshoot
                overshoot = self.overshoot_calc.update(event, price)
                result['overshoots'][threshold] = overshoot
            
            # Calculate TMV
            recent_events = self.detector.get_recent_events(threshold, 10)
            tmv_signal = self.tmv_calc.calculate(recent_events, threshold)
            result['tmv_signals'][threshold] = tmv_signal
        
        # Update coastline positions
        coastline_actions = self.coastline.update_positions(price)
        result['coastline_actions'] = coastline_actions
        
        # Check for new position opportunities
        for threshold, tmv_signal in result['tmv_signals'].items():
            overshoot = result['overshoots'].get(threshold)
            position_rec = self.coastline.should_open_position(tmv_signal, overshoot)
            
            if position_rec['should_open']:
                result['trading_signal'] = {
                    'type': 'open_position',
                    'direction': position_rec['direction'],
                    'size': position_rec['size'],
                    'threshold': threshold,
                    'tmv': position_rec['tmv'],
                    'reason': position_rec['reason'],
                }
                break
        
        # Generate market making quotes
        primary_threshold = self.config.get('thresholds', [0.01])[0]
        overshoot = result['overshoots'].get(primary_threshold)
        result['market_making_quotes'] = self.market_maker.calculate_quotes(
            price, overshoot, self.current_volatility
        )
        
        self.signals.append(result)
        
        return result
    
    def get_consensus_signal(self) -> Dict[str, Any]:
        """
        Get consensus signal across all thresholds
        
        Returns:
            Consensus trading signal
        """
        if not self.signals:
            return {'direction': 'neutral', 'strength': 0, 'confidence': 0}
        
        latest = self.signals[-1]
        
        # Count signals by direction
        long_signals = 0
        short_signals = 0
        total_strength = 0
        
        for threshold, tmv_signal in latest['tmv_signals'].items():
            if tmv_signal.should_trade:
                if tmv_signal.position_type == 'long':
                    long_signals += 1
                    total_strength += tmv_signal.signal_strength
                elif tmv_signal.position_type == 'short':
                    short_signals += 1
                    total_strength += tmv_signal.signal_strength
        
        total_signals = long_signals + short_signals
        
        if total_signals == 0:
            return {'direction': 'neutral', 'strength': 0, 'confidence': 0}
        
        if long_signals > short_signals:
            direction = 'long'
            agreement = long_signals / total_signals
        elif short_signals > long_signals:
            direction = 'short'
            agreement = short_signals / total_signals
        else:
            direction = 'neutral'
            agreement = 0.5
        
        avg_strength = total_strength / total_signals
        
        return {
            'direction': direction,
            'strength': avg_strength,
            'confidence': agreement,
            'long_signals': long_signals,
            'short_signals': short_signals,
            'total_signals': total_signals,
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get engine status"""
        return {
            'current_price': self.current_price,
            'intrinsic_time': {t: self.detector.get_intrinsic_time(t) 
                             for t in self.detector.thresholds},
            'current_tmv': {t: self.tmv_calc.get_current_tmv(t) 
                          for t in self.detector.thresholds},
            'coastline_exposure': self.coastline.get_total_exposure(),
            'coastline_unrealized_pnl': self.coastline.get_total_unrealized_pnl(),
            'coastline_realized_pnl': self.coastline.total_realized_pnl,
            'market_maker_inventory': self.market_maker.inventory,
        }
