"""
AlphaAlgo Event Normalizer
==========================
Transforms raw exchange messages into unified MarketEvent schema.
Handles timestamp alignment, sequence validation, quality flagging.
"""

from __future__ import annotations

import asyncio
import logging
import time
import json
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime, timezone
from collections import deque
from abc import ABC, abstractmethod

from .schema import (
    MarketEvent, MarketEventType, QualityFlag,
    TradeEvent, QuoteEvent, L2BookSnapshot, L2PriceLevel,
    TradeSide, TradeCondition
)

logger = logging.getLogger(__name__)


@dataclass
class NormalizerConfig:
    """Configuration for event normalizer"""
    # Timestamp alignment
    max_clock_drift_ms: int = 1000          # Max acceptable clock drift
    use_ntp_sync: bool = True               # Use NTP for time sync
    ntp_servers: List[str] = field(default_factory=lambda: [
        'pool.ntp.org',
        'time.google.com',
        'time.cloudflare.com'
    ])
    
    # Sequence validation
    sequence_gap_threshold: int = 10        # Warn if gap exceeds this
    track_sequence_per_symbol: bool = True  # Track per symbol vs global
    
    # Quality checks
    stale_threshold_ms: int = 5000          # Mark as stale after this
    price_deviation_threshold: float = 0.1  # 10% price deviation = suspicious
    
    # Performance
    batch_size: int = 100                   # Process in batches
    max_queue_size: int = 100000            # Max pending messages


class TimestampAligner:
    """
    Aligns timestamps across different sources.
    Handles clock drift, NTP sync, exchange timestamp parsing.
    """
    
    def __init__(self, config: NormalizerConfig):
        self.config = config
        self._clock_offset_ns: int = 0
        self._last_sync: float = 0
        self._sync_interval: float = 300  # 5 minutes
        
        # Track drift per exchange
        self._exchange_offsets: Dict[str, int] = {}
        
    async def sync_clock(self):
        """Synchronize with NTP servers"""
        if not self.config.use_ntp_sync:
            return
        try:
        
            import ntplib
            client = ntplib.NTPClient()
            
            offsets = []
            for server in self.config.ntp_servers[:3]:
                try:
                    response = client.request(server, version=3)
                    offset_ns = int(response.offset * 1e9)
                    offsets.append(offset_ns)
                except Exception:
                    continue
            
            if offsets:
                # Use median offset
                offsets.sort()
                self._clock_offset_ns = offsets[len(offsets) // 2]
                self._last_sync = time.time()
                logger.info(f"NTP sync complete, offset: {self._clock_offset_ns / 1e6:.2f}ms")
        except ImportError:
            logger.warning("ntplib not installed, skipping NTP sync")
        except Exception as e:
            logger.error(f"NTP sync failed: {e}")
    
    def get_current_time_ns(self) -> int:
        """Get current time in nanoseconds with NTP correction"""
        return time.time_ns() + self._clock_offset_ns
    
    def align_exchange_timestamp(
        self,
        exchange_ts: int,
        exchange: str,
        receive_ts: int
    ) -> Tuple[int, bool]:
        """
        Align exchange timestamp.
        Returns (aligned_ts, is_valid)
        """
        # Check if exchange timestamp is reasonable
        drift_ns = abs(exchange_ts - receive_ts)
        drift_ms = drift_ns / 1e6
        
        if drift_ms > self.config.max_clock_drift_ms:
            # Excessive drift - use receive timestamp
            logger.warning(f"Clock drift {drift_ms:.0f}ms for {exchange}")
            return receive_ts, False
        
        # Track exchange-specific offset
        if exchange not in self._exchange_offsets:
            self._exchange_offsets[exchange] = exchange_ts - receive_ts
        else:
            # Exponential moving average
            alpha = 0.1
            self._exchange_offsets[exchange] = int(
                alpha * (exchange_ts - receive_ts) +
                (1 - alpha) * self._exchange_offsets[exchange]
            )
        
        return exchange_ts, True
    
    def parse_exchange_timestamp(
        self,
        ts_value: Any,
        exchange: str
    ) -> int:
        """
        Parse exchange timestamp to nanoseconds.
        Handles various formats: ms, us, ns, ISO string.
        """
        if ts_value is None:
            return self.get_current_time_ns()
        
        if isinstance(ts_value, str):
            # ISO format
            try:
                dt = datetime.fromisoformat(ts_value.replace('Z', '+00:00'))
                return int(dt.timestamp() * 1e9)
            except ValueError:
                pass
            # Try numeric string
                ts_value = float(ts_value)
            except ValueError:
                return self.get_current_time_ns()
        
        if isinstance(ts_value, (int, float)):
            # Detect unit based on magnitude
            if ts_value > 1e18:
                # Already nanoseconds
                return int(ts_value)
            elif ts_value > 1e15:
                # Microseconds
                return int(ts_value * 1e3)
            elif ts_value > 1e12:
                # Milliseconds
                return int(ts_value * 1e6)
            else:
                # Seconds
                return int(ts_value * 1e9)
        
        return self.get_current_time_ns()


class SequenceValidator:
    """
    Validates message sequence numbers.
    Detects gaps, duplicates, out-of-order messages.
    """
    
    def __init__(self, config: NormalizerConfig):
        self.config = config
        
        # Sequence tracking: key -> (expected_seq, last_seen_seq)
        self._sequences: Dict[str, Tuple[int, int]] = {}
        
        # Gap history for analysis
        self._gaps: deque = deque(maxlen=1000)
        
        # Stats
        self.total_validated: int = 0
        self.gaps_detected: int = 0
        self.duplicates_detected: int = 0
        self.out_of_order_detected: int = 0
    
    def _get_key(self, exchange: str, symbol: str) -> str:
        """Get tracking key"""
        if self.config.track_sequence_per_symbol:
            return f"{exchange}:{symbol}"
        return exchange
    
    def validate(
        self,
        exchange: str,
        symbol: str,
        sequence: int
    ) -> Tuple[bool, Optional[QualityFlag], Optional[int]]:
        """
        Validate sequence number.
        Returns (is_valid, quality_flag, gap_size)
        """
        key = self._get_key(exchange, symbol)
        self.total_validated += 1
        
        if key not in self._sequences:
            # First message
            self._sequences[key] = (sequence + 1, sequence)
            return True, None, None
        
        expected, last_seen = self._sequences[key]
        
        if sequence == expected:
            # Perfect sequence
            self._sequences[key] = (sequence + 1, sequence)
            return True, None, None
        
        if sequence < last_seen:
            # Duplicate or out-of-order
            if sequence == last_seen:
                self.duplicates_detected += 1
                return False, QualityFlag.DUPLICATE, None
            else:
                self.out_of_order_detected += 1
                return False, QualityFlag.OUT_OF_ORDER, None
        
        # Gap detected
        gap_size = sequence - expected
        self.gaps_detected += 1
        self._gaps.append({
            'key': key,
            'expected': expected,
            'actual': sequence,
            'gap': gap_size,
            'timestamp': time.time_ns()
        })
        
        # Update tracking
        self._sequences[key] = (sequence + 1, sequence)
        
        if gap_size > self.config.sequence_gap_threshold:
            logger.warning(f"Large sequence gap: {key} expected {expected}, got {sequence}")
        
        return True, QualityFlag.OUT_OF_ORDER, gap_size
    
    def reset(self, exchange: Optional[str] = None, symbol: Optional[str] = None):
        """Reset sequence tracking"""
        if exchange is None:
            self._sequences.clear()
        else:
            key = self._get_key(exchange, symbol or '')
            self._sequences.pop(key, None)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return {
            'total_validated': self.total_validated,
            'gaps_detected': self.gaps_detected,
            'duplicates_detected': self.duplicates_detected,
            'out_of_order_detected': self.out_of_order_detected,
            'tracked_streams': len(self._sequences),
            'recent_gaps': list(self._gaps)[-10:],
        }


class ExchangeParser(ABC):
    """Abstract base class for exchange-specific message parsing"""
    
    @abstractmethod
    def parse(self, raw_message: bytes, receive_ts: int) -> Optional[MarketEvent]:
        """Parse raw message into MarketEvent"""
        pass
    
    @abstractmethod
    def get_exchange_name(self) -> str:
        """Get exchange identifier"""
        pass


class BinanceParser(ExchangeParser):
    """Parser for Binance WebSocket messages"""
    
    def __init__(self, timestamp_aligner: TimestampAligner):
        self.timestamp_aligner = timestamp_aligner
        self._local_sequence: int = 0
    
    def get_exchange_name(self) -> str:
        return 'binance'
    
    def parse(self, raw_message: bytes, receive_ts: int) -> Optional[MarketEvent]:
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError:
            logger.error("Failed to parse Binance message")
            return None
        
        event_type = data.get('e', '')
        
        if event_type == 'trade':
            return self._parse_trade(data, receive_ts)
        elif event_type == 'bookTicker':
            return self._parse_quote(data, receive_ts)
        elif event_type == 'depthUpdate':
            return self._parse_l2(data, receive_ts)
        
        return None
    
    def _parse_trade(self, data: Dict, receive_ts: int) -> MarketEvent:
        self._local_sequence += 1
        
        exchange_ts = self.timestamp_aligner.parse_exchange_timestamp(
            data.get('T'), 'binance'
        )
        
        trade = TradeEvent(
            price=float(data['p']),
            size=float(data['q']),
            side=TradeSide.BUY if data.get('m', False) else TradeSide.SELL,
            trade_id=str(data.get('t', '')),
            conditions=[]
        )
        
        return MarketEvent(
            event_id=str(uuid.uuid4()),
            event_type=MarketEventType.TRADE,
            symbol=data['s'],
            exchange='binance',
            exchange_ts=exchange_ts,
            receive_ts=receive_ts,
            process_ts=time.time_ns(),
            sequence_num=data.get('t', 0),
            local_sequence=self._local_sequence,
            quality_flags=0,
            trade=trade,
            raw_message=None
        )
    
    def _parse_quote(self, data: Dict, receive_ts: int) -> MarketEvent:
        self._local_sequence += 1
        
        exchange_ts = self.timestamp_aligner.parse_exchange_timestamp(
            data.get('E'), 'binance'
        )
        
        quote = QuoteEvent(
            bid_price=float(data['b']),
            bid_size=float(data['B']),
            ask_price=float(data['a']),
            ask_size=float(data['A']),
            bid_exchange='binance',
            ask_exchange='binance'
        )
        
        return MarketEvent(
            event_id=str(uuid.uuid4()),
            event_type=MarketEventType.QUOTE,
            symbol=data['s'],
            exchange='binance',
            exchange_ts=exchange_ts,
            receive_ts=receive_ts,
            process_ts=time.time_ns(),
            sequence_num=data.get('u', 0),
            local_sequence=self._local_sequence,
            quality_flags=0,
            quote=quote,
            raw_message=None
        )
    
    def _parse_l2(self, data: Dict, receive_ts: int) -> MarketEvent:
        self._local_sequence += 1
        
        exchange_ts = self.timestamp_aligner.parse_exchange_timestamp(
            data.get('E'), 'binance'
        )
        
        bids = [
            L2PriceLevel(price=float(p), size=float(s), order_count=0)
            for p, s in data.get('b', [])
        ]
        asks = [
            L2PriceLevel(price=float(p), size=float(s), order_count=0)
            for p, s in data.get('a', [])
        ]
        
        l2_book = L2BookSnapshot(
            bids=bids,
            asks=asks,
            depth=max(len(bids), len(asks)),
            is_snapshot=False
        )
        
        return MarketEvent(
            event_id=str(uuid.uuid4()),
            event_type=MarketEventType.L2_DELTA,
            symbol=data['s'],
            exchange='binance',
            exchange_ts=exchange_ts,
            receive_ts=receive_ts,
            process_ts=time.time_ns(),
            sequence_num=data.get('u', 0),
            local_sequence=self._local_sequence,
            quality_flags=0,
            l2_book=l2_book,
            raw_message=None
        )


class CoinbaseParser(ExchangeParser):
    """Parser for Coinbase WebSocket messages"""
    
    def __init__(self, timestamp_aligner: TimestampAligner):
        self.timestamp_aligner = timestamp_aligner
        self._local_sequence: int = 0
    
    def get_exchange_name(self) -> str:
        return 'coinbase'
    
    def parse(self, raw_message: bytes, receive_ts: int) -> Optional[MarketEvent]:
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError:
            return None
        
        msg_type = data.get('type', '')
        
        if msg_type == 'match' or msg_type == 'last_match':
            return self._parse_trade(data, receive_ts)
        elif msg_type == 'ticker':
            return self._parse_quote(data, receive_ts)
        elif msg_type == 'l2update':
            return self._parse_l2(data, receive_ts)
        
        return None
    
    def _parse_trade(self, data: Dict, receive_ts: int) -> MarketEvent:
        self._local_sequence += 1
        
        exchange_ts = self.timestamp_aligner.parse_exchange_timestamp(
            data.get('time'), 'coinbase'
        )
        
        side_str = data.get('side', '').lower()
        side = TradeSide.BUY if side_str == 'buy' else TradeSide.SELL if side_str == 'sell' else TradeSide.UNKNOWN
        
        trade = TradeEvent(
            price=float(data.get('price', 0)),
            size=float(data.get('size', 0)),
            side=side,
            trade_id=str(data.get('trade_id', '')),
            conditions=[]
        )
        
        return MarketEvent(
            event_id=str(uuid.uuid4()),
            event_type=MarketEventType.TRADE,
            symbol=data.get('product_id', ''),
            exchange='coinbase',
            exchange_ts=exchange_ts,
            receive_ts=receive_ts,
            process_ts=time.time_ns(),
            sequence_num=data.get('sequence', 0),
            local_sequence=self._local_sequence,
            quality_flags=0,
            trade=trade,
            raw_message=None
        )
    
    def _parse_quote(self, data: Dict, receive_ts: int) -> MarketEvent:
        self._local_sequence += 1
        
        exchange_ts = self.timestamp_aligner.parse_exchange_timestamp(
            data.get('time'), 'coinbase'
        )
        
        quote = QuoteEvent(
            bid_price=float(data.get('best_bid', 0)),
            bid_size=float(data.get('best_bid_size', 0)),
            ask_price=float(data.get('best_ask', 0)),
            ask_size=float(data.get('best_ask_size', 0)),
            bid_exchange='coinbase',
            ask_exchange='coinbase'
        )
        
        return MarketEvent(
            event_id=str(uuid.uuid4()),
            event_type=MarketEventType.QUOTE,
            symbol=data.get('product_id', ''),
            exchange='coinbase',
            exchange_ts=exchange_ts,
            receive_ts=receive_ts,
            process_ts=time.time_ns(),
            sequence_num=data.get('sequence', 0),
            local_sequence=self._local_sequence,
            quality_flags=0,
            quote=quote,
            raw_message=None
        )
    
    def _parse_l2(self, data: Dict, receive_ts: int) -> MarketEvent:
        self._local_sequence += 1
        
        exchange_ts = self.timestamp_aligner.parse_exchange_timestamp(
            data.get('time'), 'coinbase'
        )
        
        bids = []
        asks = []
        
        for change in data.get('changes', []):
            side, price, size = change
            level = L2PriceLevel(price=float(price), size=float(size), order_count=0)
            if side == 'buy':
                bids.append(level)
            else:
                asks.append(level)
        
        l2_book = L2BookSnapshot(
            bids=bids,
            asks=asks,
            depth=max(len(bids), len(asks)),
            is_snapshot=False
        )
        
        return MarketEvent(
            event_id=str(uuid.uuid4()),
            event_type=MarketEventType.L2_DELTA,
            symbol=data.get('product_id', ''),
            exchange='coinbase',
            exchange_ts=exchange_ts,
            receive_ts=receive_ts,
            process_ts=time.time_ns(),
            sequence_num=0,
            local_sequence=self._local_sequence,
            quality_flags=0,
            l2_book=l2_book,
            raw_message=None
        )


class GenericParser(ExchangeParser):
    """Generic parser for unknown exchanges"""
    
    def __init__(self, exchange: str, timestamp_aligner: TimestampAligner):
        self.exchange = exchange
        self.timestamp_aligner = timestamp_aligner
        self._local_sequence: int = 0
    
    def get_exchange_name(self) -> str:
        return self.exchange
    
    def parse(self, raw_message: bytes, receive_ts: int) -> Optional[MarketEvent]:
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError:
            return None
        
        self._local_sequence += 1
        
        # Try to detect event type from common fields
        if any(k in data for k in ['trade', 'price', 'size', 'qty']):
            return self._parse_as_trade(data, receive_ts)
        elif any(k in data for k in ['bid', 'ask', 'bbo']):
            return self._parse_as_quote(data, receive_ts)
        elif any(k in data for k in ['bids', 'asks', 'orderbook', 'depth']):
            return self._parse_as_l2(data, receive_ts)
        
        return None
    
    def _parse_as_trade(self, data: Dict, receive_ts: int) -> MarketEvent:
        exchange_ts = self.timestamp_aligner.parse_exchange_timestamp(
            data.get('timestamp') or data.get('time') or data.get('ts'),
            self.exchange
        )
        
        price = float(data.get('price') or data.get('p') or 0)
        size = float(data.get('size') or data.get('qty') or data.get('q') or data.get('amount') or 0)
        
        side_raw = data.get('side') or data.get('direction') or ''
        if isinstance(side_raw, str):
            side_raw = side_raw.lower()
        side = TradeSide.BUY if side_raw in ('buy', 'b', 1) else TradeSide.SELL if side_raw in ('sell', 's', -1) else TradeSide.UNKNOWN
        
        trade = TradeEvent(
            price=price,
            size=size,
            side=side,
            trade_id=str(data.get('trade_id') or data.get('id') or ''),
            conditions=[]
        )
        
        return MarketEvent(
            event_id=str(uuid.uuid4()),
            event_type=MarketEventType.TRADE,
            symbol=data.get('symbol') or data.get('instrument') or data.get('pair') or '',
            exchange=self.exchange,
            exchange_ts=exchange_ts,
            receive_ts=receive_ts,
            process_ts=time.time_ns(),
            sequence_num=data.get('sequence') or data.get('seq') or 0,
            local_sequence=self._local_sequence,
            quality_flags=0,
            trade=trade,
            raw_message=None
        )
    
    def _parse_as_quote(self, data: Dict, receive_ts: int) -> MarketEvent:
        exchange_ts = self.timestamp_aligner.parse_exchange_timestamp(
            data.get('timestamp') or data.get('time') or data.get('ts'),
            self.exchange
        )
        
        quote = QuoteEvent(
            bid_price=float(data.get('bid') or data.get('bid_price') or data.get('b') or 0),
            bid_size=float(data.get('bid_size') or data.get('bid_qty') or data.get('B') or 0),
            ask_price=float(data.get('ask') or data.get('ask_price') or data.get('a') or 0),
            ask_size=float(data.get('ask_size') or data.get('ask_qty') or data.get('A') or 0),
            bid_exchange=self.exchange,
            ask_exchange=self.exchange
        )
        
        return MarketEvent(
            event_id=str(uuid.uuid4()),
            event_type=MarketEventType.QUOTE,
            symbol=data.get('symbol') or data.get('instrument') or data.get('pair') or '',
            exchange=self.exchange,
            exchange_ts=exchange_ts,
            receive_ts=receive_ts,
            process_ts=time.time_ns(),
            sequence_num=data.get('sequence') or data.get('seq') or 0,
            local_sequence=self._local_sequence,
            quality_flags=0,
            quote=quote,
            raw_message=None
        )
    
    def _parse_as_l2(self, data: Dict, receive_ts: int) -> MarketEvent:
        exchange_ts = self.timestamp_aligner.parse_exchange_timestamp(
            data.get('timestamp') or data.get('time') or data.get('ts'),
            self.exchange
        )
        
        bids_raw = data.get('bids') or data.get('b') or []
        asks_raw = data.get('asks') or data.get('a') or []
        
        bids = []
        for item in bids_raw:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                bids.append(L2PriceLevel(
                    price=float(item[0]),
                    size=float(item[1]),
                    order_count=int(item[2]) if len(item) > 2 else 0
                ))
            elif isinstance(item, dict):
                bids.append(L2PriceLevel(
                    price=float(item.get('price') or item.get('p') or 0),
                    size=float(item.get('size') or item.get('qty') or item.get('q') or 0),
                    order_count=int(item.get('count') or item.get('n') or 0)
                ))
        
        asks = []
        for item in asks_raw:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                asks.append(L2PriceLevel(
                    price=float(item[0]),
                    size=float(item[1]),
                    order_count=int(item[2]) if len(item) > 2 else 0
                ))
            elif isinstance(item, dict):
                asks.append(L2PriceLevel(
                    price=float(item.get('price') or item.get('p') or 0),
                    size=float(item.get('size') or item.get('qty') or item.get('q') or 0),
                    order_count=int(item.get('count') or item.get('n') or 0)
                ))
        
        l2_book = L2BookSnapshot(
            bids=bids,
            asks=asks,
            depth=max(len(bids), len(asks)),
            is_snapshot=data.get('type') == 'snapshot' or data.get('action') == 'snapshot'
        )
        
        return MarketEvent(
            event_id=str(uuid.uuid4()),
            event_type=MarketEventType.L2_SNAPSHOT if l2_book.is_snapshot else MarketEventType.L2_DELTA,
            symbol=data.get('symbol') or data.get('instrument') or data.get('pair') or '',
            exchange=self.exchange,
            exchange_ts=exchange_ts,
            receive_ts=receive_ts,
            process_ts=time.time_ns(),
            sequence_num=data.get('sequence') or data.get('seq') or 0,
            local_sequence=self._local_sequence,
            quality_flags=0,
            l2_book=l2_book,
            raw_message=None
        )


class EventNormalizer:
    """
    Main normalizer that coordinates parsing, validation, and quality checks.
    """
    
    def __init__(self, config: Optional[NormalizerConfig] = None):
        self.config = config or NormalizerConfig()
        
        # Components
        self.timestamp_aligner = TimestampAligner(self.config)
        self.sequence_validator = SequenceValidator(self.config)
        
        # Parsers
        self._parsers: Dict[str, ExchangeParser] = {}
        self._register_default_parsers()
        
        # Price tracking for deviation checks
        self._last_prices: Dict[str, float] = {}
        
        # Stats
        self.events_normalized: int = 0
        self.events_dropped: int = 0
        self.quality_flags_added: int = 0
        
        logger.info("EventNormalizer initialized")
    
    def _register_default_parsers(self):
        """Register default exchange parsers"""
        self._parsers['binance'] = BinanceParser(self.timestamp_aligner)
        self._parsers['coinbase'] = CoinbaseParser(self.timestamp_aligner)
    
    def register_parser(self, exchange: str, parser: ExchangeParser):
        """Register custom parser for an exchange"""
        self._parsers[exchange] = parser
        logger.info(f"Registered parser for {exchange}")
    
    def get_parser(self, exchange: str) -> ExchangeParser:
        """Get parser for exchange, create generic if not found"""
        if exchange not in self._parsers:
            self._parsers[exchange] = GenericParser(exchange, self.timestamp_aligner)
        return self._parsers[exchange]
    
    async def normalize(
        self,
        raw_message: bytes,
        receive_ts: int,
        exchange: str
    ) -> Optional[MarketEvent]:
        """
        Normalize a raw message into a MarketEvent.
        Returns None if message cannot be parsed or should be dropped.
        """
        # Get parser
        parser = self.get_parser(exchange)
        
        # Parse message
        event = parser.parse(raw_message, receive_ts)
        
        if event is None:
            self.events_dropped += 1
            return None
        
        # Validate sequence
        is_valid, quality_flag, gap_size = self.sequence_validator.validate(
            event.exchange,
            event.symbol,
            event.sequence_num
        )
        
        if quality_flag:
            event.add_quality_flag(quality_flag)
            self.quality_flags_added += 1
        
        # Check for stale data
        if self._is_stale(event):
            event.add_quality_flag(QualityFlag.STALE)
            self.quality_flags_added += 1
        
        # Check for price deviation
        if event.trade and self._has_price_deviation(event):
            event.add_quality_flag(QualityFlag.UNVERIFIED)
            self.quality_flags_added += 1
        
        # Update process timestamp
        event.process_ts = time.time_ns()
        
        self.events_normalized += 1
        return event
    
    def _is_stale(self, event: MarketEvent) -> bool:
        """Check if event is stale"""
        age_ms = (event.receive_ts - event.exchange_ts) / 1e6
        return age_ms > self.config.stale_threshold_ms
    
    def _has_price_deviation(self, event: MarketEvent) -> bool:
        """Check for suspicious price deviation"""
        if not event.trade:
            return False
        
        key = f"{event.exchange}:{event.symbol}"
        price = event.trade.price
        
        if key in self._last_prices:
            last_price = self._last_prices[key]
            if last_price > 0:
                deviation = abs(price - last_price) / last_price
                if deviation > self.config.price_deviation_threshold:
                    logger.warning(f"Price deviation {deviation:.2%} for {key}")
                    return True
        
        self._last_prices[key] = price
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get normalizer statistics"""
        return {
            'events_normalized': self.events_normalized,
            'events_dropped': self.events_dropped,
            'quality_flags_added': self.quality_flags_added,
            'sequence_stats': self.sequence_validator.get_stats(),
            'parsers_registered': list(self._parsers.keys()),
        }
