import logging
logger = logging.getLogger(__name__)
"""Institutional Order Flow Detection System.

This module provides advanced institutional activity detection including:
- Iceberg order recognition
- Spoofing detection
- Stop hunt identification
- Large block trade analysis
- Dark pool activity estimation
- Whale movement tracking
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sqlite3
from pathlib import Path
from loguru import logger
from collections import deque
import asyncio
import numpy
import pandas


class OrderType(Enum):
    """Order type classification."""
    ICEBERG = "iceberg"
    BLOCK = "block"
    SWEEP = "sweep"
    SPOOF = "spoof"
    NORMAL = "normal"


class InstitutionalActivity(Enum):
    """Types of institutional activity."""
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    STOP_HUNT = "stop_hunt"
    LIQUIDITY_PROVISION = "liquidity_provision"
    MARKET_MAKING = "market_making"
    MOMENTUM_IGNITION = "momentum_ignition"


class FlowDirection(Enum):
    """Order flow direction."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class OrderFlowSignal:
    """Order flow detection signal."""
    timestamp: datetime
    signal_type: InstitutionalActivity
    direction: FlowDirection
    strength: float  # 0-1
    confidence: float  # 0-1
    price_level: float
    volume: float
    duration_minutes: int
    affected_levels: List[float]
    market_impact: float
    description: str


@dataclass
class IcebergOrder:
    """Detected iceberg order."""
    timestamp: datetime
    price_level: float
    total_volume_estimate: float
    visible_size: float
    execution_rate: float
    time_in_force: int  # minutes
    direction: str  # 'buy' or 'sell'
    confidence: float


@dataclass
class SpoofingEvent:
    """Detected spoofing event."""
    timestamp: datetime
    spoof_side: str  # 'bid' or 'ask'
    spoof_levels: List[Tuple[float, float]]  # (price, volume)
    duration_seconds: int
    cancelled_volume: float
    market_impact: float
    confidence: float


@dataclass
class BlockTrade:
    """Large block trade detection."""
    timestamp: datetime
    price: float
    volume: float
    side: str  # 'buy' or 'sell'
    venue: str
    is_dark_pool: bool
    market_impact: float
    institutional_probability: float


class InstitutionalFlowDetector:
    """Advanced institutional order flow detection system."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the institutional flow detector.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.db_path = Path(config.get('db_path', 'data/institutional_flow.db'))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Detection parameters
        self.iceberg_threshold = config.get('iceberg_threshold', 10000)  # Min volume for iceberg
        self.block_trade_threshold = config.get('block_trade_threshold', 50000)  # Min volume for block
        self.spoof_detection_window = config.get('spoof_detection_window', 30)  # seconds
        self.volume_profile_periods = config.get('volume_profile_periods', 100)
        
        # Data buffers
        self.order_book_history = deque(maxlen=1000)
        self.trade_history = deque(maxlen=5000)
        self.volume_profile = deque(maxlen=self.volume_profile_periods)
        
        # Detection state
        self.active_icebergs = {}
        self.potential_spoofs = {}
        self.flow_signals = deque(maxlen=500)
        
        # Initialize database
        self._init_database()
        
        logger.info("Institutional Flow Detector initialized")
    
    def _init_database(self):
        """Initialize SQLite database for flow data storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS flow_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    signal_type TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    strength REAL NOT NULL,
                    confidence REAL NOT NULL,
                    price_level REAL NOT NULL,
                    volume REAL NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    affected_levels TEXT NOT NULL,
                    market_impact REAL NOT NULL,
                    description TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS iceberg_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    price_level REAL NOT NULL,
                    total_volume_estimate REAL NOT NULL,
                    visible_size REAL NOT NULL,
                    execution_rate REAL NOT NULL,
                    time_in_force INTEGER NOT NULL,
                    direction TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS spoofing_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    spoof_side TEXT NOT NULL,
                    spoof_levels TEXT NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    cancelled_volume REAL NOT NULL,
                    market_impact REAL NOT NULL,
                    confidence REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS block_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    price REAL NOT NULL,
                    volume REAL NOT NULL,
                    side TEXT NOT NULL,
                    venue TEXT NOT NULL,
                    is_dark_pool BOOLEAN NOT NULL,
                    market_impact REAL NOT NULL,
                    institutional_probability REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    async def analyze_order_flow(self, order_book: Dict[str, Any], 
                                trades: List[Dict[str, Any]]) -> List[OrderFlowSignal]:
        """Analyze order flow for institutional activity.
        
        Args:
            order_book: Current order book data
            trades: Recent trade data
            
        Returns:
            List of detected flow signals
        """
        signals = []
        
        try:
            # Update data buffers
            self.order_book_history.append({
                'timestamp': datetime.now(),
                'bids': order_book.get('bids', []),
                'asks': order_book.get('asks', []),
                'bid_volume': sum(level[1] for level in order_book.get('bids', [])),
                'ask_volume': sum(level[1] for level in order_book.get('asks', []))
            })
            
            for trade in trades:
                self.trade_history.append(trade)
            
            # Detect different types of institutional activity
            iceberg_signals = await self._detect_iceberg_orders(order_book, trades)
            spoof_signals = await self._detect_spoofing(order_book)
            block_signals = await self._detect_block_trades(trades)
            stop_hunt_signals = await self._detect_stop_hunts(trades, order_book)
            accumulation_signals = await self._detect_accumulation_distribution(trades)
            
            signals.extend(iceberg_signals)
            signals.extend(spoof_signals)
            signals.extend(block_signals)
            signals.extend(stop_hunt_signals)
            signals.extend(accumulation_signals)
            
            # Store signals
            await self._store_flow_signals(signals)
            
            # Update flow signals buffer
            self.flow_signals.extend(signals)
            
            logger.info(f"Detected {len(signals)} institutional flow signals")
            return signals
            
        except Exception as e:
            logger.error(f"Error analyzing order flow: {e}")
            return []
    
    async def _detect_iceberg_orders(self, order_book: Dict[str, Any], 
                                   trades: List[Dict[str, Any]]) -> List[OrderFlowSignal]:
        """Detect iceberg orders in the order book."""
        signals = []
        
        try:
            current_time = datetime.now()
            
            # Analyze bid and ask sides
            for side, levels in [('bid', order_book.get('bids', [])), 
                               ('ask', order_book.get('asks', []))]:
                
                for price, volume in levels[:10]:  # Check top 10 levels
                    # Look for consistent volume at same price level
                    level_key = f"{side}_{price}"
                    
                    if level_key not in self.active_icebergs:
                        self.active_icebergs[level_key] = {
                            'first_seen': current_time,
                            'total_volume': volume,
                            'executions': 0,
                            'avg_visible_size': volume,
                            'price': price,
                            'side': side
                        }
                    else:
                        iceberg = self.active_icebergs[level_key]
                        
                        # Check if volume replenished (sign of iceberg)
                        if volume > iceberg['avg_visible_size'] * 0.8:
                            iceberg['executions'] += 1
                            iceberg['total_volume'] += volume
                            iceberg['avg_visible_size'] = (
                                iceberg['avg_visible_size'] + volume
                            ) / 2
                            
                            # Detect iceberg if multiple replenishments
                            if (iceberg['executions'] >= 3 and 
                                iceberg['total_volume'] >= self.iceberg_threshold):
                                
                                duration = (current_time - iceberg['first_seen']).total_seconds() / 60
                                
                                # Calculate confidence based on consistency
                                confidence = min(0.9, iceberg['executions'] / 10)
                                
                                signal = OrderFlowSignal(
                                    timestamp=current_time,
                                    signal_type=InstitutionalActivity.LIQUIDITY_PROVISION,
                                    direction=FlowDirection.BULLISH if side == 'bid' else FlowDirection.BEARISH,
                                    strength=min(1.0, iceberg['total_volume'] / (self.iceberg_threshold * 5)),
                                    confidence=confidence,
                                    price_level=price,
                                    volume=iceberg['total_volume'],
                                    duration_minutes=int(duration),
                                    affected_levels=[price],
                                    market_impact=0.3,
                                    description=f"Iceberg order detected at {price} ({side})"
                                )
                                
                                signals.append(signal)
                                
                                # Store iceberg order
                                iceberg_order = IcebergOrder(
                                    timestamp=current_time,
                                    price_level=price,
                                    total_volume_estimate=iceberg['total_volume'],
                                    visible_size=iceberg['avg_visible_size'],
                                    execution_rate=iceberg['executions'] / duration if duration > 0 else 0,
                                    time_in_force=int(duration),
                                    direction=side,
                                    confidence=confidence
                                )
                                
                                await self._store_iceberg_order(iceberg_order)
            
            # Clean up old icebergs
            cutoff_time = current_time - timedelta(minutes=30)
            self.active_icebergs = {
                k: v for k, v in self.active_icebergs.items()
                if v['first_seen'] > cutoff_time
            }
            
        except Exception as e:
            logger.error(f"Error detecting iceberg orders: {e}")
        
        return signals
    
    async def _detect_spoofing(self, order_book: Dict[str, Any]) -> List[OrderFlowSignal]:
        """Detect spoofing activity in the order book."""
        signals = []
        
        try:
            current_time = datetime.now()
            
            # Look for large orders that appear and disappear quickly
            for side, levels in [('bid', order_book.get('bids', [])), 
                               ('ask', order_book.get('asks', []))]:
                
                for price, volume in levels[:5]:  # Check top 5 levels
                    if volume > self.block_trade_threshold * 0.5:  # Large order threshold
                        
                        level_key = f"{side}_{price}"
                        
                        if level_key not in self.potential_spoofs:
                            self.potential_spoofs[level_key] = {
                                'first_seen': current_time,
                                'volume': volume,
                                'price': price,
                                'side': side,
                                'appearances': 1
                            }
                        else:
                            spoof = self.potential_spoofs[level_key]
                            spoof['appearances'] += 1
                            
                            # Check if order keeps appearing/disappearing
                            duration = (current_time - spoof['first_seen']).total_seconds()
                            
                            if (duration < self.spoof_detection_window and 
                                spoof['appearances'] >= 3):
                                
                                confidence = min(0.8, spoof['appearances'] / 5)
                                
                                signal = OrderFlowSignal(
                                    timestamp=current_time,
                                    signal_type=InstitutionalActivity.MOMENTUM_IGNITION,
                                    direction=FlowDirection.BEARISH if side == 'bid' else FlowDirection.BULLISH,
                                    strength=0.7,
                                    confidence=confidence,
                                    price_level=price,
                                    volume=volume,
                                    duration_minutes=int(duration / 60),
                                    affected_levels=[price],
                                    market_impact=0.5,
                                    description=f"Potential spoofing detected at {price} ({side})"
                                )
                                
                                signals.append(signal)
                                
                                # Store spoofing event
                                spoofing_event = SpoofingEvent(
                                    timestamp=current_time,
                                    spoof_side=side,
                                    spoof_levels=[(price, volume)],
                                    duration_seconds=int(duration),
                                    cancelled_volume=volume,
                                    market_impact=0.5,
                                    confidence=confidence
                                )
                                
                                await self._store_spoofing_event(spoofing_event)
            
            # Clean up old potential spoofs
            cutoff_time = current_time - timedelta(seconds=self.spoof_detection_window * 2)
            self.potential_spoofs = {
                k: v for k, v in self.potential_spoofs.items()
                if v['first_seen'] > cutoff_time
            }
            
        except Exception as e:
            logger.error(f"Error detecting spoofing: {e}")
        
        return signals
    
    async def _detect_block_trades(self, trades: List[Dict[str, Any]]) -> List[OrderFlowSignal]:
        """Detect large block trades."""
        signals = []
        
        try:
            for trade in trades:
                volume = trade.get('volume', 0)
                price = trade.get('price', 0)
                side = trade.get('side', 'unknown')
                timestamp = trade.get('timestamp', datetime.now())
                
                if volume >= self.block_trade_threshold:
                    # Estimate if it's institutional
                    institutional_prob = self._calculate_institutional_probability(trade)
                    
                    if institutional_prob > 0.6:
                        # Determine if it's dark pool
                        is_dark_pool = self._is_likely_dark_pool(trade)
                        
                        # Calculate market impact
                        market_impact = min(1.0, volume / (self.block_trade_threshold * 2))
                        
                        signal = OrderFlowSignal(
                            timestamp=timestamp,
                            signal_type=InstitutionalActivity.ACCUMULATION if side == 'buy' else InstitutionalActivity.DISTRIBUTION,
                            direction=FlowDirection.BULLISH if side == 'buy' else FlowDirection.BEARISH,
                            strength=market_impact,
                            confidence=institutional_prob,
                            price_level=price,
                            volume=volume,
                            duration_minutes=1,
                            affected_levels=[price],
                            market_impact=market_impact,
                            description=f"Block trade: {volume:,.0f} @ {price} ({'Dark Pool' if is_dark_pool else 'Lit Market'})"
                        )
                        
                        signals.append(signal)
                        
                        # Store block trade
                        block_trade = BlockTrade(
                            timestamp=timestamp,
                            price=price,
                            volume=volume,
                            side=side,
                            venue='dark_pool' if is_dark_pool else 'exchange',
                            is_dark_pool=is_dark_pool,
                            market_impact=market_impact,
                            institutional_probability=institutional_prob
                        )
                        
                        await self._store_block_trade(block_trade)
            
        except Exception as e:
            logger.error(f"Error detecting block trades: {e}")
        
        return signals
    
    async def _detect_stop_hunts(self, trades: List[Dict[str, Any]], 
                               order_book: Dict[str, Any]) -> List[OrderFlowSignal]:
        """Detect stop hunting activity."""
        signals = []
        
        try:
            # Look for rapid price movements followed by reversals
            if len(self.trade_history) < 20:
                return signals
            
            recent_trades = list(self.trade_history)[-20:]
            prices = [trade.get('price', 0) for trade in recent_trades]
            volumes = [trade.get('volume', 0) for trade in recent_trades]
            
            if len(prices) < 10:
                return signals
            
            # Calculate price movement and volume
            price_change = (prices[-1] - prices[0]) / prices[0]
            avg_volume = np.mean(volumes)
            recent_volume = np.mean(volumes[-5:])
            
            # Detect potential stop hunt patterns
            if (abs(price_change) > 0.002 and  # Significant move
                recent_volume > avg_volume * 2 and  # Volume spike
                len(set(prices[-3:])) > 1):  # Price reversal
                
                # Determine direction
                if price_change > 0:
                    direction = FlowDirection.BULLISH
                    activity = InstitutionalActivity.STOP_HUNT
                else:
                    direction = FlowDirection.BEARISH
                    activity = InstitutionalActivity.STOP_HUNT
                
                signal = OrderFlowSignal(
                    timestamp=datetime.now(),
                    signal_type=activity,
                    direction=direction,
                    strength=min(1.0, abs(price_change) * 100),
                    confidence=0.6,
                    price_level=prices[-1],
                    volume=sum(volumes[-5:]),
                    duration_minutes=5,
                    affected_levels=[min(prices[-10:]), max(prices[-10:])],
                    market_impact=abs(price_change),
                    description=f"Potential stop hunt: {price_change:.2%} move with volume spike"
                )
                
                signals.append(signal)
            
        except Exception as e:
            logger.error(f"Error detecting stop hunts: {e}")
        
        return signals
    
    async def _detect_accumulation_distribution(self, trades: List[Dict[str, Any]]) -> List[OrderFlowSignal]:
        """Detect accumulation/distribution patterns."""
        signals = []
        
        try:
            if len(self.trade_history) < 50:
                return signals
            
            recent_trades = list(self.trade_history)[-50:]
            
            # Calculate buy/sell volume imbalance
            buy_volume = sum(trade.get('volume', 0) for trade in recent_trades 
                           if trade.get('side') == 'buy')
            sell_volume = sum(trade.get('volume', 0) for trade in recent_trades 
                            if trade.get('side') == 'sell')
            
            total_volume = buy_volume + sell_volume
            if total_volume == 0:
                return signals
            
            imbalance = (buy_volume - sell_volume) / total_volume
            
            # Detect significant imbalances
            if abs(imbalance) > 0.3:  # 30% imbalance threshold
                
                if imbalance > 0:
                    activity = InstitutionalActivity.ACCUMULATION
                    direction = FlowDirection.BULLISH
                    description = f"Accumulation detected: {imbalance:.1%} buy imbalance"
                else:
                    activity = InstitutionalActivity.DISTRIBUTION
                    direction = FlowDirection.BEARISH
                    description = f"Distribution detected: {abs(imbalance):.1%} sell imbalance"
                
                # Calculate average price
                avg_price = np.mean([trade.get('price', 0) for trade in recent_trades])
                
                signal = OrderFlowSignal(
                    timestamp=datetime.now(),
                    signal_type=activity,
                    direction=direction,
                    strength=abs(imbalance),
                    confidence=0.7,
                    price_level=avg_price,
                    volume=total_volume,
                    duration_minutes=10,
                    affected_levels=[avg_price],
                    market_impact=abs(imbalance) * 0.5,
                    description=description
                )
                
                signals.append(signal)
            
        except Exception as e:
            logger.error(f"Error detecting accumulation/distribution: {e}")
        
        return signals
    
    def _calculate_institutional_probability(self, trade: Dict[str, Any]) -> float:
        """Calculate probability that a trade is institutional."""
        volume = trade.get('volume', 0)
        price = trade.get('price', 0)
        
        # Factors that increase institutional probability
        prob = 0.5  # Base probability
        
        # Large volume
        if volume > self.block_trade_threshold:
            prob += 0.3
        elif volume > self.block_trade_threshold * 0.5:
            prob += 0.2
        
        # Round numbers (institutions often trade round lots)
        if volume % 1000 == 0:
            prob += 0.1
        
        # Time of day (institutions more active during market hours)
        hour = datetime.now().hour
        if 9 <= hour <= 16:  # Market hours
            prob += 0.1
        
        return min(1.0, prob)
    
    def _is_likely_dark_pool(self, trade: Dict[str, Any]) -> bool:
        """Determine if trade is likely from dark pool."""
        volume = trade.get('volume', 0)
        
        # Large trades are more likely to be dark pool
        if volume > self.block_trade_threshold * 2:
            return True
        
        # Check if trade is at mid-market (common for dark pools)
        # This would require actual bid/ask data
        return False
    
    async def _store_flow_signals(self, signals: List[OrderFlowSignal]):
        """Store flow signals in database."""
        with sqlite3.connect(self.db_path) as conn:
            for signal in signals:
                conn.execute('''
                    INSERT INTO flow_signals 
                    (timestamp, signal_type, direction, strength, confidence,
                     price_level, volume, duration_minutes, affected_levels,
                     market_impact, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal.timestamp, signal.signal_type.value, signal.direction.value,
                    signal.strength, signal.confidence, signal.price_level,
                    signal.volume, signal.duration_minutes, str(signal.affected_levels),
                    signal.market_impact, signal.description
                ))
            conn.commit()
    
    async def _store_iceberg_order(self, iceberg: IcebergOrder):
        """Store iceberg order in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO iceberg_orders 
                (timestamp, price_level, total_volume_estimate, visible_size,
                 execution_rate, time_in_force, direction, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                iceberg.timestamp, iceberg.price_level, iceberg.total_volume_estimate,
                iceberg.visible_size, iceberg.execution_rate, iceberg.time_in_force,
                iceberg.direction, iceberg.confidence
            ))
            conn.commit()
    
    async def _store_spoofing_event(self, spoof: SpoofingEvent):
        """Store spoofing event in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO spoofing_events 
                (timestamp, spoof_side, spoof_levels, duration_seconds,
                 cancelled_volume, market_impact, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                spoof.timestamp, spoof.spoof_side, str(spoof.spoof_levels),
                spoof.duration_seconds, spoof.cancelled_volume,
                spoof.market_impact, spoof.confidence
            ))
            conn.commit()
    
    async def _store_block_trade(self, block: BlockTrade):
        """Store block trade in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO block_trades 
                (timestamp, price, volume, side, venue, is_dark_pool,
                 market_impact, institutional_probability)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                block.timestamp, block.price, block.volume, block.side,
                block.venue, block.is_dark_pool, block.market_impact,
                block.institutional_probability
            ))
            conn.commit()
    
    def get_recent_signals(self, minutes: int = 60) -> List[OrderFlowSignal]:
        """Get recent flow signals.
        
        Args:
            minutes: Number of minutes to look back
            
        Returns:
            List of recent flow signals
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [signal for signal in self.flow_signals if signal.timestamp > cutoff_time]
    
    def get_flow_summary(self) -> Dict[str, Any]:
        """Get summary of recent institutional flow activity.
        
        Returns:
            Flow activity summary
        """
        recent_signals = self.get_recent_signals(60)
        
        if not recent_signals:
            return {
                'total_signals': 0,
                'bullish_signals': 0,
                'bearish_signals': 0,
                'avg_confidence': 0,
                'dominant_activity': 'none',
                'market_impact_score': 0
            }
        
        bullish_count = sum(1 for s in recent_signals if s.direction == FlowDirection.BULLISH)
        bearish_count = sum(1 for s in recent_signals if s.direction == FlowDirection.BEARISH)
        
        avg_confidence = np.mean([s.confidence for s in recent_signals])
        market_impact = np.mean([s.market_impact for s in recent_signals])
        
        # Determine dominant activity
        activity_counts = {}
        for signal in recent_signals:
            activity = signal.signal_type.value
            activity_counts[activity] = activity_counts.get(activity, 0) + 1
        
        dominant_activity = max(activity_counts.items(), key=lambda x: x[1])[0] if activity_counts else 'none'
        
        return {
            'total_signals': len(recent_signals),
            'bullish_signals': bullish_count,
            'bearish_signals': bearish_count,
            'avg_confidence': avg_confidence,
            'dominant_activity': dominant_activity,
            'market_impact_score': market_impact,
            'activity_breakdown': activity_counts
        }
