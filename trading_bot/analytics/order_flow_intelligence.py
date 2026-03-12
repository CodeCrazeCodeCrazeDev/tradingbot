"""
Order Flow Intelligence System
Institutional-Grade Market Microstructure Analysis

This module provides comprehensive order flow analysis:
- Order book imbalance detection
- Trade flow analysis (buyer/seller initiated)
- Spoofing and layering detection
- Whale accumulation/distribution detection
- Volume profile analysis
- VWAP deviation tracking
- Institutional footprint detection
- Dark pool activity estimation

Market Maker + Professional Trader + Quantitative Analyst Perspective
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import deque
import warnings
import numpy
import pandas

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class OrderFlowSignal(Enum):
    """Order flow signal types"""
    STRONG_BUY = "STRONG_BUY"  # Heavy buying pressure
    BUY = "BUY"  # Moderate buying pressure
    NEUTRAL = "NEUTRAL"  # Balanced flow
    SELL = "SELL"  # Moderate selling pressure
    STRONG_SELL = "STRONG_SELL"  # Heavy selling pressure


class MarketActivity(Enum):
    """Market activity classification"""
    ACCUMULATION = "ACCUMULATION"  # Smart money buying
    DISTRIBUTION = "DISTRIBUTION"  # Smart money selling
    MARKUP = "MARKUP"  # Trending up
    MARKDOWN = "MARKDOWN"  # Trending down
    CONSOLIDATION = "CONSOLIDATION"  # Range-bound


class SpoofingType(Enum):
    """Types of spoofing patterns"""
    LAYERING = "LAYERING"  # Multiple fake orders at different levels
    QUOTE_STUFFING = "QUOTE_STUFFING"  # Rapid order placement/cancellation
    MOMENTUM_IGNITION = "MOMENTUM_IGNITION"  # Fake orders to trigger momentum
    WASH_TRADING = "WASH_TRADING"  # Self-trading


@dataclass
class OrderBookSnapshot:
    """Order book snapshot"""
    timestamp: datetime
    symbol: str
    bids: List[Tuple[float, float]]  # [(price, size), ...]
    asks: List[Tuple[float, float]]  # [(price, size), ...]
    
    @property
    def mid_price(self) -> float:
        try:
            if self.bids and self.asks:
                return (self.bids[0][0] + self.asks[0][0]) / 2
            return 0.0
        except Exception as e:
            logger.error(f"Error in mid_price: {e}")
            raise
    
    @property
    def spread(self) -> float:
        try:
            if self.bids and self.asks:
                return self.asks[0][0] - self.bids[0][0]
            return 0.0
        except Exception as e:
            logger.error(f"Error in spread: {e}")
            raise
    
    @property
    def bid_depth(self) -> float:
        return sum(size for _, size in self.bids)
    
    @property
    def ask_depth(self) -> float:
        return sum(size for _, size in self.asks)


@dataclass
class TradeRecord:
    """Individual trade record"""
    timestamp: datetime
    symbol: str
    price: float
    size: float
    side: str  # 'BUY' or 'SELL' (aggressor side)
    is_block: bool = False  # Block trade indicator
    
    @property
    def value(self) -> float:
        return self.price * self.size


@dataclass
class OrderFlowMetrics:
    """Order flow analysis metrics"""
    timestamp: datetime
    symbol: str
    
    # Imbalance metrics
    book_imbalance: float  # (bid_depth - ask_depth) / total_depth
    trade_imbalance: float  # (buy_volume - sell_volume) / total_volume
    
    # Pressure metrics
    buy_pressure: float  # 0-1 scale
    sell_pressure: float  # 0-1 scale
    net_pressure: float  # buy - sell
    
    # Volume metrics
    total_volume: float
    buy_volume: float
    sell_volume: float
    block_volume: float  # Large trades
    
    # Price metrics
    vwap: float
    vwap_deviation: float  # Current price vs VWAP
    
    # Flow signal
    signal: OrderFlowSignal
    signal_strength: float  # 0-1
    
    # Activity classification
    activity: MarketActivity
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'book_imbalance': round(self.book_imbalance, 4),
            'trade_imbalance': round(self.trade_imbalance, 4),
            'buy_pressure': round(self.buy_pressure, 4),
            'sell_pressure': round(self.sell_pressure, 4),
            'net_pressure': round(self.net_pressure, 4),
            'total_volume': round(self.total_volume, 0),
            'vwap': round(self.vwap, 4),
            'vwap_deviation': round(self.vwap_deviation, 4),
            'signal': self.signal.value,
            'signal_strength': round(self.signal_strength, 4),
            'activity': self.activity.value
        }


@dataclass
class SpoofingAlert:
    """Spoofing detection alert"""
    timestamp: datetime
    symbol: str
    spoof_type: SpoofingType
    confidence: float  # 0-1
    description: str
    evidence: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'spoof_type': self.spoof_type.value,
            'confidence': round(self.confidence, 4),
            'description': self.description,
            'evidence': self.evidence
        }


@dataclass
class InstitutionalFootprint:
    """Institutional activity detection"""
    timestamp: datetime
    symbol: str
    
    # Detection metrics
    is_institutional: bool
    confidence: float
    
    # Activity type
    activity_type: str  # 'ACCUMULATION', 'DISTRIBUTION', 'UNKNOWN'
    
    # Evidence
    block_trade_ratio: float  # Block trades / total trades
    avg_trade_size: float
    size_percentile: float  # Percentile of trade sizes
    
    # Estimated position
    estimated_direction: str  # 'LONG', 'SHORT', 'UNKNOWN'
    estimated_size: float  # Estimated position size
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'is_institutional': self.is_institutional,
            'confidence': round(self.confidence, 4),
            'activity_type': self.activity_type,
            'block_trade_ratio': round(self.block_trade_ratio, 4),
            'avg_trade_size': round(self.avg_trade_size, 2),
            'estimated_direction': self.estimated_direction,
            'estimated_size': round(self.estimated_size, 0)
        }


@dataclass
class VolumeProfile:
    """Volume profile analysis"""
    symbol: str
    period_start: datetime
    period_end: datetime
    
    # Price levels with volume
    price_levels: Dict[float, float]  # {price: volume}
    
    # Key levels
    poc: float  # Point of Control (highest volume price)
    value_area_high: float  # 70% of volume above this
    value_area_low: float  # 70% of volume below this
    
    # Distribution
    is_normal: bool  # Normal distribution
    is_bimodal: bool  # Two peaks
    skew: float  # Distribution skew
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'period': f"{self.period_start.date()} to {self.period_end.date()}",
            'poc': round(self.poc, 4),
            'value_area_high': round(self.value_area_high, 4),
            'value_area_low': round(self.value_area_low, 4),
            'is_normal': self.is_normal,
            'is_bimodal': self.is_bimodal,
            'skew': round(self.skew, 4)
        }


class OrderFlowIntelligence:
    """
    Order Flow Intelligence System
    
    Provides institutional-grade market microstructure analysis:
    
    1. Order Book Analysis
       - Real-time imbalance detection
       - Depth analysis at multiple levels
       - Spread dynamics
    
    2. Trade Flow Analysis
       - Buyer/seller initiated classification
       - Volume-weighted analysis
       - Block trade detection
    
    3. Spoofing Detection
       - Layering patterns
       - Quote stuffing
       - Momentum ignition
       - Wash trading
    
    4. Institutional Footprint
       - Large order detection
       - Accumulation/distribution patterns
       - Dark pool activity estimation
    
    5. Volume Profile
       - Point of Control (POC)
       - Value Area (VA)
       - Distribution analysis
    
    6. VWAP Analysis
       - Real-time VWAP calculation
       - Deviation tracking
       - Institutional benchmark comparison
    
    Key Signals:
    - Book imbalance > 0.3: Strong directional pressure
    - Trade imbalance > 0.4: Aggressive buying/selling
    - Block ratio > 0.2: Institutional activity
    - VWAP deviation > 0.5%: Price dislocation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize order flow intelligence
        
        Args:
            config: Configuration dictionary
        """
        try:
            self.config = config or {}
        
            # Thresholds
            self.imbalance_threshold = self.config.get('imbalance_threshold', 0.3)
            self.block_size_multiplier = self.config.get('block_size_multiplier', 10)
            self.spoof_confidence_threshold = self.config.get('spoof_confidence_threshold', 0.7)
        
            # Data storage
            self.order_books: Dict[str, deque] = {}  # symbol -> deque of snapshots
            self.trades: Dict[str, deque] = {}  # symbol -> deque of trades
            self.metrics_history: Dict[str, deque] = {}  # symbol -> deque of metrics
        
            # Alerts
            self.spoofing_alerts: deque = deque(maxlen=100)
            self.institutional_alerts: deque = deque(maxlen=100)
        
            # Statistics
            self.updates = 0
            self.alerts_generated = 0
        
            logger.info("OrderFlowIntelligence initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_order_book(self, snapshot: OrderBookSnapshot):
        """
        Update order book data
        
        Args:
            snapshot: Order book snapshot
        """
        try:
            symbol = snapshot.symbol
        
            if symbol not in self.order_books:
                self.order_books[symbol] = deque(maxlen=1000)
        
            self.order_books[symbol].append(snapshot)
            self.updates += 1
        
            # Check for spoofing
            self._check_spoofing(symbol)
        except Exception as e:
            logger.error(f"Error in update_order_book: {e}")
            raise
    
    def record_trade(self, trade: TradeRecord):
        """
        Record a trade
        
        Args:
            trade: Trade record
        """
        try:
            symbol = trade.symbol
        
            if symbol not in self.trades:
                self.trades[symbol] = deque(maxlen=10000)
        
            # Classify as block trade
            avg_size = self._get_average_trade_size(symbol)
            trade.is_block = trade.size > avg_size * self.block_size_multiplier
        
            self.trades[symbol].append(trade)
        except Exception as e:
            logger.error(f"Error in record_trade: {e}")
            raise
    
    def analyze(self, symbol: str) -> OrderFlowMetrics:
        """
        Analyze order flow for a symbol
        
        Args:
            symbol: Asset symbol
            
        Returns:
            OrderFlowMetrics with comprehensive analysis
        """
        # Get recent data
        try:
            order_books = list(self.order_books.get(symbol, []))
            trades = list(self.trades.get(symbol, []))
        
            if not order_books:
                return self._default_metrics(symbol)
        
            latest_book = order_books[-1]
        
            # Calculate book imbalance
            total_depth = latest_book.bid_depth + latest_book.ask_depth
            book_imbalance = (latest_book.bid_depth - latest_book.ask_depth) / total_depth if total_depth > 0 else 0
        
            # Calculate trade imbalance
            recent_trades = [t for t in trades if (datetime.now() - t.timestamp).seconds < 300]  # Last 5 min
        
            if recent_trades:
                buy_volume = sum(t.size for t in recent_trades if t.side == 'BUY')
                sell_volume = sum(t.size for t in recent_trades if t.side == 'SELL')
                total_volume = buy_volume + sell_volume
                trade_imbalance = (buy_volume - sell_volume) / total_volume if total_volume > 0 else 0
                block_volume = sum(t.size for t in recent_trades if t.is_block)
            else:
                buy_volume = sell_volume = total_volume = block_volume = 0
                trade_imbalance = 0
        
            # Calculate pressure
            buy_pressure = self._calculate_buy_pressure(book_imbalance, trade_imbalance)
            sell_pressure = self._calculate_sell_pressure(book_imbalance, trade_imbalance)
            net_pressure = buy_pressure - sell_pressure
        
            # Calculate VWAP
            vwap = self._calculate_vwap(trades)
            current_price = latest_book.mid_price
            vwap_deviation = (current_price - vwap) / vwap if vwap > 0 else 0
        
            # Determine signal
            signal, signal_strength = self._determine_signal(net_pressure, book_imbalance, trade_imbalance)
        
            # Classify activity
            activity = self._classify_activity(book_imbalance, trade_imbalance, vwap_deviation)
        
            metrics = OrderFlowMetrics(
                timestamp=datetime.now(),
                symbol=symbol,
                book_imbalance=book_imbalance,
                trade_imbalance=trade_imbalance,
                buy_pressure=buy_pressure,
                sell_pressure=sell_pressure,
                net_pressure=net_pressure,
                total_volume=total_volume,
                buy_volume=buy_volume,
                sell_volume=sell_volume,
                block_volume=block_volume,
                vwap=vwap,
                vwap_deviation=vwap_deviation,
                signal=signal,
                signal_strength=signal_strength,
                activity=activity
            )
        
            # Store in history
            if symbol not in self.metrics_history:
                self.metrics_history[symbol] = deque(maxlen=1000)
            self.metrics_history[symbol].append(metrics)
        
            return metrics
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
    
    def detect_institutional_activity(self, symbol: str) -> InstitutionalFootprint:
        """
        Detect institutional trading activity
        
        Args:
            symbol: Asset symbol
            
        Returns:
            InstitutionalFootprint analysis
        """
        try:
            trades = list(self.trades.get(symbol, []))
        
            if not trades:
                return self._default_institutional_footprint(symbol)
        
            # Recent trades (last hour)
            recent_trades = [t for t in trades if (datetime.now() - t.timestamp).seconds < 3600]
        
            if not recent_trades:
                return self._default_institutional_footprint(symbol)
        
            # Calculate metrics
            total_trades = len(recent_trades)
            block_trades = [t for t in recent_trades if t.is_block]
            block_trade_ratio = len(block_trades) / total_trades if total_trades > 0 else 0
        
            avg_trade_size = np.mean([t.size for t in recent_trades])
            all_sizes = [t.size for t in trades]
            size_percentile = np.percentile(all_sizes, 90) if all_sizes else 0
        
            # Determine if institutional
            is_institutional = (
                block_trade_ratio > 0.15 or
                avg_trade_size > size_percentile
            )
        
            confidence = min(1.0, block_trade_ratio * 2 + (avg_trade_size / size_percentile if size_percentile > 0 else 0) * 0.3)
        
            # Determine activity type
            buy_volume = sum(t.size for t in recent_trades if t.side == 'BUY')
            sell_volume = sum(t.size for t in recent_trades if t.side == 'SELL')
        
            if buy_volume > sell_volume * 1.5:
                activity_type = 'ACCUMULATION'
                estimated_direction = 'LONG'
            elif sell_volume > buy_volume * 1.5:
                activity_type = 'DISTRIBUTION'
                estimated_direction = 'SHORT'
            else:
                activity_type = 'UNKNOWN'
                estimated_direction = 'UNKNOWN'
        
            # Estimate position size
            estimated_size = abs(buy_volume - sell_volume)
        
            footprint = InstitutionalFootprint(
                timestamp=datetime.now(),
                symbol=symbol,
                is_institutional=is_institutional,
                confidence=confidence,
                activity_type=activity_type,
                block_trade_ratio=block_trade_ratio,
                avg_trade_size=avg_trade_size,
                size_percentile=size_percentile,
                estimated_direction=estimated_direction,
                estimated_size=estimated_size
            )
        
            if is_institutional and confidence > 0.7:
                self.institutional_alerts.append(footprint)
                self.alerts_generated += 1
        
            return footprint
        except Exception as e:
            logger.error(f"Error in detect_institutional_activity: {e}")
            raise
    
    def calculate_volume_profile(self,
                                symbol: str,
                                num_levels: int = 50) -> VolumeProfile:
        """
        Calculate volume profile
        
        Args:
            symbol: Asset symbol
            num_levels: Number of price levels
            
        Returns:
            VolumeProfile analysis
        """
        try:
            trades = list(self.trades.get(symbol, []))
        
            if not trades:
                return self._default_volume_profile(symbol)
        
            # Get price range
            prices = [t.price for t in trades]
            min_price = min(prices)
            max_price = max(prices)
        
            if min_price == max_price:
                return self._default_volume_profile(symbol)
        
            # Create price levels
            level_size = (max_price - min_price) / num_levels
            price_levels = {}
        
            for trade in trades:
                level = int((trade.price - min_price) / level_size) * level_size + min_price
                price_levels[level] = price_levels.get(level, 0) + trade.size
        
            # Find POC (Point of Control)
            poc = max(price_levels, key=price_levels.get)
        
            # Calculate Value Area (70% of volume)
            total_volume = sum(price_levels.values())
            target_volume = total_volume * 0.7
        
            # Start from POC and expand
            sorted_levels = sorted(price_levels.keys())
            poc_idx = sorted_levels.index(poc)
        
            va_volume = price_levels[poc]
            low_idx = poc_idx
            high_idx = poc_idx
        
            while va_volume < target_volume and (low_idx > 0 or high_idx < len(sorted_levels) - 1):
                low_vol = price_levels.get(sorted_levels[low_idx - 1], 0) if low_idx > 0 else 0
                high_vol = price_levels.get(sorted_levels[high_idx + 1], 0) if high_idx < len(sorted_levels) - 1 else 0
            
                if low_vol >= high_vol and low_idx > 0:
                    low_idx -= 1
                    va_volume += low_vol
                elif high_idx < len(sorted_levels) - 1:
                    high_idx += 1
                    va_volume += high_vol
                else:
                    break
        
            value_area_low = sorted_levels[low_idx]
            value_area_high = sorted_levels[high_idx]
        
            # Analyze distribution
            volumes = list(price_levels.values())
            skew = float(pd.Series(volumes).skew()) if len(volumes) > 2 else 0
        
            # Check for bimodal distribution
            is_bimodal = self._check_bimodal(volumes)
            is_normal = abs(skew) < 0.5 and not is_bimodal
        
            return VolumeProfile(
                symbol=symbol,
                period_start=trades[0].timestamp,
                period_end=trades[-1].timestamp,
                price_levels=price_levels,
                poc=poc,
                value_area_high=value_area_high,
                value_area_low=value_area_low,
                is_normal=is_normal,
                is_bimodal=is_bimodal,
                skew=skew
            )
        except Exception as e:
            logger.error(f"Error in calculate_volume_profile: {e}")
            raise
    
    def _check_spoofing(self, symbol: str):
        """Check for spoofing patterns"""
        try:
            order_books = list(self.order_books.get(symbol, []))
        
            if len(order_books) < 10:
                return
        
            recent_books = order_books[-10:]
        
            # Check for layering
            layering_score = self._detect_layering(recent_books)
        
            if layering_score > self.spoof_confidence_threshold:
                alert = SpoofingAlert(
                    timestamp=datetime.now(),
                    symbol=symbol,
                    spoof_type=SpoofingType.LAYERING,
                    confidence=layering_score,
                    description="Potential layering detected: Large orders placed and cancelled rapidly",
                    evidence={
                        'order_changes': len(recent_books),
                        'depth_volatility': self._calculate_depth_volatility(recent_books)
                    }
                )
                self.spoofing_alerts.append(alert)
                self.alerts_generated += 1
                logger.warning(f"Spoofing alert: {symbol} - {alert.description}")
        
            # Check for quote stuffing
            quote_stuffing_score = self._detect_quote_stuffing(recent_books)
        
            if quote_stuffing_score > self.spoof_confidence_threshold:
                alert = SpoofingAlert(
                    timestamp=datetime.now(),
                    symbol=symbol,
                    spoof_type=SpoofingType.QUOTE_STUFFING,
                    confidence=quote_stuffing_score,
                    description="Potential quote stuffing: Rapid order placement/cancellation",
                    evidence={
                        'message_rate': len(recent_books) / 10,  # Per second
                        'spread_volatility': self._calculate_spread_volatility(recent_books)
                    }
                )
                self.spoofing_alerts.append(alert)
                self.alerts_generated += 1
        except Exception as e:
            logger.error(f"Error in _check_spoofing: {e}")
            raise
    
    def _detect_layering(self, order_books: List[OrderBookSnapshot]) -> float:
        """Detect layering pattern"""
        try:
            if len(order_books) < 5:
                return 0.0
        
            # Check for large orders appearing and disappearing
            bid_depths = [ob.bid_depth for ob in order_books]
            ask_depths = [ob.ask_depth for ob in order_books]
        
            bid_volatility = np.std(bid_depths) / np.mean(bid_depths) if np.mean(bid_depths) > 0 else 0
            ask_volatility = np.std(ask_depths) / np.mean(ask_depths) if np.mean(ask_depths) > 0 else 0
        
            # High volatility in depth suggests layering
            layering_score = (bid_volatility + ask_volatility) / 2
        
            return min(1.0, layering_score * 2)
        except Exception as e:
            logger.error(f"Error in _detect_layering: {e}")
            raise
    
    def _detect_quote_stuffing(self, order_books: List[OrderBookSnapshot]) -> float:
        """Detect quote stuffing pattern"""
        try:
            if len(order_books) < 5:
                return 0.0
        
            # Check for rapid changes in top of book
            spread_changes = []
            for i in range(1, len(order_books)):
                spread_change = abs(order_books[i].spread - order_books[i-1].spread)
                spread_changes.append(spread_change)
        
            # High frequency of spread changes suggests quote stuffing
            avg_spread = np.mean([ob.spread for ob in order_books])
            change_ratio = np.mean(spread_changes) / avg_spread if avg_spread > 0 else 0
        
            return min(1.0, change_ratio * 5)
        except Exception as e:
            logger.error(f"Error in _detect_quote_stuffing: {e}")
            raise
    
    def _calculate_depth_volatility(self, order_books: List[OrderBookSnapshot]) -> float:
        """Calculate depth volatility"""
        try:
            depths = [ob.bid_depth + ob.ask_depth for ob in order_books]
            return np.std(depths) / np.mean(depths) if np.mean(depths) > 0 else 0
        except Exception as e:
            logger.error(f"Error in _calculate_depth_volatility: {e}")
            raise
    
    def _calculate_spread_volatility(self, order_books: List[OrderBookSnapshot]) -> float:
        """Calculate spread volatility"""
        try:
            spreads = [ob.spread for ob in order_books]
            return np.std(spreads) / np.mean(spreads) if np.mean(spreads) > 0 else 0
        except Exception as e:
            logger.error(f"Error in _calculate_spread_volatility: {e}")
            raise
    
    def _calculate_buy_pressure(self, book_imbalance: float, trade_imbalance: float) -> float:
        """Calculate buying pressure (0-1)"""
        # Combine book and trade imbalance
        try:
            pressure = 0.5 + (book_imbalance * 0.3 + trade_imbalance * 0.2)
            return np.clip(pressure, 0, 1)
        except Exception as e:
            logger.error(f"Error in _calculate_buy_pressure: {e}")
            raise
    
    def _calculate_sell_pressure(self, book_imbalance: float, trade_imbalance: float) -> float:
        """Calculate selling pressure (0-1)"""
        # Inverse of buy pressure
        try:
            pressure = 0.5 - (book_imbalance * 0.3 + trade_imbalance * 0.2)
            return np.clip(pressure, 0, 1)
        except Exception as e:
            logger.error(f"Error in _calculate_sell_pressure: {e}")
            raise
    
    def _calculate_vwap(self, trades: List[TradeRecord]) -> float:
        """Calculate VWAP"""
        try:
            if not trades:
                return 0.0
        
            total_value = sum(t.value for t in trades)
            total_volume = sum(t.size for t in trades)
        
            return total_value / total_volume if total_volume > 0 else 0
        except Exception as e:
            logger.error(f"Error in _calculate_vwap: {e}")
            raise
    
    def _determine_signal(self,
                         net_pressure: float,
                         book_imbalance: float,
                         trade_imbalance: float) -> Tuple[OrderFlowSignal, float]:
        """Determine order flow signal"""
        # Combine metrics
        try:
            combined = net_pressure * 0.4 + book_imbalance * 0.3 + trade_imbalance * 0.3
        
            strength = abs(combined)
        
            if combined > 0.4:
                return OrderFlowSignal.STRONG_BUY, strength
            elif combined > 0.15:
                return OrderFlowSignal.BUY, strength
            elif combined < -0.4:
                return OrderFlowSignal.STRONG_SELL, strength
            elif combined < -0.15:
                return OrderFlowSignal.SELL, strength
            else:
                return OrderFlowSignal.NEUTRAL, strength
        except Exception as e:
            logger.error(f"Error in _determine_signal: {e}")
            raise
    
    def _classify_activity(self,
                          book_imbalance: float,
                          trade_imbalance: float,
                          vwap_deviation: float) -> MarketActivity:
        """Classify market activity"""
        # Accumulation: buying pressure, price below VWAP
        try:
            if trade_imbalance > 0.2 and vwap_deviation < -0.002:
                return MarketActivity.ACCUMULATION
        
            # Distribution: selling pressure, price above VWAP
            if trade_imbalance < -0.2 and vwap_deviation > 0.002:
                return MarketActivity.DISTRIBUTION
        
            # Markup: buying pressure, price rising
            if trade_imbalance > 0.2 and vwap_deviation > 0.002:
                return MarketActivity.MARKUP
        
            # Markdown: selling pressure, price falling
            if trade_imbalance < -0.2 and vwap_deviation < -0.002:
                return MarketActivity.MARKDOWN
        
            return MarketActivity.CONSOLIDATION
        except Exception as e:
            logger.error(f"Error in _classify_activity: {e}")
            raise
    
    def _get_average_trade_size(self, symbol: str) -> float:
        """Get average trade size for symbol"""
        try:
            trades = list(self.trades.get(symbol, []))
            if not trades:
                return 1000  # Default
            return np.mean([t.size for t in trades])
        except Exception as e:
            logger.error(f"Error in _get_average_trade_size: {e}")
            raise
    
    def _check_bimodal(self, values: List[float]) -> bool:
        """Check if distribution is bimodal"""
        try:
            if len(values) < 10:
                return False
        
            # Simple check: look for two distinct peaks
            sorted_vals = sorted(values, reverse=True)
        
            if len(sorted_vals) < 3:
                return False
        
            # Check if there's a significant dip between peaks
            max_val = sorted_vals[0]
            second_max = sorted_vals[1]
        
            # Find minimum between peaks
            min_between = min(sorted_vals[:len(sorted_vals)//2])
        
            return min_between < max_val * 0.5 and second_max > max_val * 0.7
        except Exception as e:
            logger.error(f"Error in _check_bimodal: {e}")
            raise
    
    def _default_metrics(self, symbol: str) -> OrderFlowMetrics:
        """Return default metrics"""
        return OrderFlowMetrics(
            timestamp=datetime.now(),
            symbol=symbol,
            book_imbalance=0,
            trade_imbalance=0,
            buy_pressure=0.5,
            sell_pressure=0.5,
            net_pressure=0,
            total_volume=0,
            buy_volume=0,
            sell_volume=0,
            block_volume=0,
            vwap=0,
            vwap_deviation=0,
            signal=OrderFlowSignal.NEUTRAL,
            signal_strength=0,
            activity=MarketActivity.CONSOLIDATION
        )
    
    def _default_institutional_footprint(self, symbol: str) -> InstitutionalFootprint:
        """Return default institutional footprint"""
        return InstitutionalFootprint(
            timestamp=datetime.now(),
            symbol=symbol,
            is_institutional=False,
            confidence=0,
            activity_type='UNKNOWN',
            block_trade_ratio=0,
            avg_trade_size=0,
            size_percentile=0,
            estimated_direction='UNKNOWN',
            estimated_size=0
        )
    
    def _default_volume_profile(self, symbol: str) -> VolumeProfile:
        """Return default volume profile"""
        return VolumeProfile(
            symbol=symbol,
            period_start=datetime.now(),
            period_end=datetime.now(),
            price_levels={},
            poc=0,
            value_area_high=0,
            value_area_low=0,
            is_normal=True,
            is_bimodal=False,
            skew=0
        )
    
    def get_recent_alerts(self, limit: int = 10) -> Dict[str, List[Dict]]:
        """Get recent alerts"""
        return {
            'spoofing': [a.to_dict() for a in list(self.spoofing_alerts)[-limit:]],
            'institutional': [a.to_dict() for a in list(self.institutional_alerts)[-limit:]]
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            'updates': self.updates,
            'alerts_generated': self.alerts_generated,
            'symbols_tracked': len(self.order_books),
            'total_trades': sum(len(t) for t in self.trades.values())
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create system
    ofi = OrderFlowIntelligence()
    
    # Simulate order book updates
    logger.info("\n=== Simulating Order Flow ===")
    
    for i in range(100):
        # Create order book snapshot
        mid_price = 100 + np.random.randn() * 0.5
        spread = 0.02 + np.random.rand() * 0.03
        
        bids = [(mid_price - spread/2 - j*0.01, np.random.randint(100, 1000)) for j in range(5)]
        asks = [(mid_price + spread/2 + j*0.01, np.random.randint(100, 1000)) for j in range(5)]
        
        snapshot = OrderBookSnapshot(
            timestamp=datetime.now(),
            symbol='AAPL',
            bids=bids,
            asks=asks
        )
        ofi.update_order_book(snapshot)
        
        # Record trades
        for _ in range(np.random.randint(1, 5)):
            trade = TradeRecord(
                timestamp=datetime.now(),
                symbol='AAPL',
                price=mid_price + np.random.randn() * 0.01,
                size=np.random.randint(100, 5000),
                side=np.random.choice(['BUY', 'SELL'])
            )
            ofi.record_trade(trade)
    
    # Analyze
    logger.info("\n=== Order Flow Analysis ===")
    metrics = ofi.analyze('AAPL')
    logger.info(f"Symbol: {metrics.symbol}")
    logger.info(f"Book Imbalance: {metrics.book_imbalance:.4f}")
    logger.info(f"Trade Imbalance: {metrics.trade_imbalance:.4f}")
    logger.info(f"Net Pressure: {metrics.net_pressure:.4f}")
    logger.info(f"Signal: {metrics.signal.value} (strength: {metrics.signal_strength:.4f})")
    logger.info(f"Activity: {metrics.activity.value}")
    logger.info(f"VWAP: {metrics.vwap:.4f}")
    logger.info(f"VWAP Deviation: {metrics.vwap_deviation:.4%}")
    
    # Institutional detection
    logger.info("\n=== Institutional Activity ===")
    footprint = ofi.detect_institutional_activity('AAPL')
    logger.info(f"Is Institutional: {footprint.is_institutional}")
    logger.info(f"Confidence: {footprint.confidence:.4f}")
    logger.info(f"Activity Type: {footprint.activity_type}")
    logger.info(f"Block Trade Ratio: {footprint.block_trade_ratio:.4f}")
    
    # Volume profile
    logger.info("\n=== Volume Profile ===")
    profile = ofi.calculate_volume_profile('AAPL')
    logger.info(f"POC: {profile.poc:.4f}")
    logger.info(f"Value Area: [{profile.value_area_low:.4f}, {profile.value_area_high:.4f}]")
    logger.info(f"Distribution: {'Normal' if profile.is_normal else 'Bimodal' if profile.is_bimodal else 'Skewed'}")
    
    # Alerts
    logger.info("\n=== Recent Alerts ===")
    alerts = ofi.get_recent_alerts(5)
    logger.info(f"Spoofing Alerts: {len(alerts['spoofing'])}")
    logger.info(f"Institutional Alerts: {len(alerts['institutional'])}")
    
    # Statistics
    stats = ofi.get_statistics()
    logger.info(f"\n=== Statistics ===")
    logger.info(f"Updates: {stats['updates']}")
    logger.info(f"Alerts Generated: {stats['alerts_generated']}")
