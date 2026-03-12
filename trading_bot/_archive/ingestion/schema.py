"""
AlphaAlgo Unified Market Event Schema
=====================================
Production-grade schema for trades, quotes, L2 book snapshots.
Versioned, backward-compatible, Protobuf-ready.

Schema Version: 1.0.0
"""

from __future__ import annotations

import struct
import hashlib
from enum import IntEnum
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import json

# Schema version for backward compatibility
SCHEMA_VERSION = "1.0.0"
SCHEMA_MAGIC = 0xAA01  # AlphaAlgo marker


class MarketEventType(IntEnum):
    """Event type discriminator - 1 byte"""
    UNKNOWN = 0
    TRADE = 1
    QUOTE = 2
    L2_SNAPSHOT = 3
    L2_DELTA = 4
    HEARTBEAT = 5
    STATUS = 6
    AUCTION = 7
    IMBALANCE = 8
    HALT = 9
    RESUME = 10


class QualityFlag(IntEnum):
    """Data quality indicators - bitfield"""
    NONE = 0
    STALE = 1 << 0           # Data older than expected
    INTERPOLATED = 1 << 1    # Synthetic/interpolated value
    DELAYED = 1 << 2         # Known delayed feed
    OUT_OF_ORDER = 1 << 3    # Sequence gap detected
    DUPLICATE = 1 << 4       # Duplicate event
    CORRECTED = 1 << 5       # Correction to prior event
    SYNTHETIC = 1 << 6       # Synthetically generated
    UNVERIFIED = 1 << 7      # Source not verified


class TradeSide(IntEnum):
    """Trade aggressor side"""
    UNKNOWN = 0
    BUY = 1
    SELL = 2


class TradeCondition(IntEnum):
    """Trade condition codes"""
    REGULAR = 0
    ODD_LOT = 1
    BLOCK = 2
    CROSS = 3
    SWEEP = 4
    OPENING = 5
    CLOSING = 6
    AUCTION = 7
    INTERMARKET_SWEEP = 8
    DERIVATIVELY_PRICED = 9


@dataclass(frozen=True, slots=True)
class ExchangeMetadata:
    """Exchange/venue identification"""
    exchange_id: str              # MIC code or internal ID
    exchange_name: str            # Human-readable name
    asset_class: str              # EQUITY, FX, CRYPTO, FUTURES, OPTIONS
    feed_type: str                # DIRECT, CONSOLIDATED, DELAYED
    feed_tier: str                # L1, L2, L3
    timezone: str                 # Exchange timezone
    currency: str                 # Quote currency
    lot_size: float               # Minimum tradeable unit
    tick_size: float              # Minimum price increment
    trading_hours_utc: str        # "09:30-16:00" format
    
    def to_bytes(self) -> bytes:
        """Serialize to bytes"""
        data = json.dumps(asdict(self)).encode('utf-8')
        return struct.pack('>H', len(data)) + data
    
    @classmethod
    def from_bytes(cls, data: bytes) -> tuple['ExchangeMetadata', int]:
        """Deserialize from bytes, return (obj, bytes_consumed)"""
        length = struct.unpack('>H', data[:2])[0]
        obj_data = json.loads(data[2:2+length].decode('utf-8'))
        return cls(**obj_data), 2 + length


@dataclass(slots=True)
class L2PriceLevel:
    """Single price level in order book"""
    price: float                  # Price level
    size: float                   # Total size at level
    order_count: int              # Number of orders (if available)
    
    def to_bytes(self) -> bytes:
        """Pack to 20 bytes: price(8) + size(8) + count(4)"""
        return struct.pack('>ddI', self.price, self.size, self.order_count)
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'L2PriceLevel':
        """Unpack from 20 bytes"""
        price, size, count = struct.unpack('>ddI', data[:20])
        return cls(price=price, size=size, order_count=count)


@dataclass(slots=True)
class TradeEvent:
    """Individual trade execution"""
    price: float                  # Execution price
    size: float                   # Execution size
    side: TradeSide               # Aggressor side
    trade_id: str                 # Exchange trade ID
    conditions: List[TradeCondition] = field(default_factory=list)
    
    def to_bytes(self) -> bytes:
        """Serialize trade event"""
        trade_id_bytes = self.trade_id.encode('utf-8')[:64].ljust(64, b'\x00')
        conditions_packed = sum(1 << c.value for c in self.conditions)
        return struct.pack(
            '>ddB64sI',
            self.price,
            self.size,
            self.side.value,
            trade_id_bytes,
            conditions_packed
        )
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'TradeEvent':
        """Deserialize trade event"""
        price, size, side, trade_id_bytes, conditions_packed = struct.unpack(
            '>ddB64sI', data[:85]
        )
        trade_id = trade_id_bytes.rstrip(b'\x00').decode('utf-8')
        conditions = [
            TradeCondition(i) for i in range(16) 
            if conditions_packed & (1 << i)
        ]
        return cls(
            price=price,
            size=size,
            side=TradeSide(side),
            trade_id=trade_id,
            conditions=conditions
        )


@dataclass(slots=True)
class QuoteEvent:
    """Best bid/offer quote"""
    bid_price: float              # Best bid price
    bid_size: float               # Best bid size
    ask_price: float              # Best ask price
    ask_size: float               # Best ask size
    bid_exchange: str             # Exchange showing best bid
    ask_exchange: str             # Exchange showing best ask
    
    @property
    def mid_price(self) -> float:
        """Calculate mid price"""
        if self.bid_price > 0 and self.ask_price > 0:
            return (self.bid_price + self.ask_price) / 2
        return 0.0
    
    @property
    def spread(self) -> float:
        """Calculate spread"""
        if self.bid_price > 0 and self.ask_price > 0:
            return self.ask_price - self.bid_price
        return 0.0
    
    @property
    def spread_bps(self) -> float:
        """Spread in basis points"""
        mid = self.mid_price
        if mid > 0:
            return (self.spread / mid) * 10000
        return 0.0
    
    def to_bytes(self) -> bytes:
        """Serialize quote event"""
        bid_ex = self.bid_exchange.encode('utf-8')[:8].ljust(8, b'\x00')
        ask_ex = self.ask_exchange.encode('utf-8')[:8].ljust(8, b'\x00')
        return struct.pack(
            '>dddd8s8s',
            self.bid_price,
            self.bid_size,
            self.ask_price,
            self.ask_size,
            bid_ex,
            ask_ex
        )
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'QuoteEvent':
        """Deserialize quote event"""
        bp, bs, ap, as_, bid_ex, ask_ex = struct.unpack('>dddd8s8s', data[:48])
        return cls(
            bid_price=bp,
            bid_size=bs,
            ask_price=ap,
            ask_size=as_,
            bid_exchange=bid_ex.rstrip(b'\x00').decode('utf-8'),
            ask_exchange=ask_ex.rstrip(b'\x00').decode('utf-8')
        )


@dataclass(slots=True)
class L2BookSnapshot:
    """Level 2 order book snapshot"""
    bids: List[L2PriceLevel]      # Bid levels, best first
    asks: List[L2PriceLevel]      # Ask levels, best first
    depth: int                    # Number of levels
    is_snapshot: bool             # True=full snapshot, False=delta
    
    @property
    def best_bid(self) -> Optional[L2PriceLevel]:
        return self.bids[0] if self.bids else None
    
    @property
    def best_ask(self) -> Optional[L2PriceLevel]:
        return self.asks[0] if self.asks else None
    
    @property
    def total_bid_size(self) -> float:
        return sum(level.size for level in self.bids)
    
    @property
    def total_ask_size(self) -> float:
        return sum(level.size for level in self.asks)
    
    @property
    def imbalance(self) -> float:
        """Order book imbalance: positive = more bids"""
        total_bid = self.total_bid_size
        total_ask = self.total_ask_size
        total = total_bid + total_ask
        if total > 0:
            return (total_bid - total_ask) / total
        return 0.0
    
    def to_bytes(self) -> bytes:
        """Serialize L2 snapshot"""
        header = struct.pack('>HH?', len(self.bids), len(self.asks), self.is_snapshot)
        bid_bytes = b''.join(level.to_bytes() for level in self.bids)
        ask_bytes = b''.join(level.to_bytes() for level in self.asks)
        return header + bid_bytes + ask_bytes
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'L2BookSnapshot':
        """Deserialize L2 snapshot"""
        num_bids, num_asks, is_snapshot = struct.unpack('>HH?', data[:5])
        offset = 5
        bids = []
        for _ in range(num_bids):
            bids.append(L2PriceLevel.from_bytes(data[offset:offset+20]))
            offset += 20
        asks = []
        for _ in range(num_asks):
            asks.append(L2PriceLevel.from_bytes(data[offset:offset+20]))
            offset += 20
        return cls(bids=bids, asks=asks, depth=max(num_bids, num_asks), is_snapshot=is_snapshot)


@dataclass(slots=True)
class MarketEvent:
    """
    Unified market event envelope.
    All market data flows through this structure.
    """
    # Identity
    event_id: str                 # UUID or exchange-assigned ID
    event_type: MarketEventType   # Discriminator
    
    # Instrument
    symbol: str                   # Normalized symbol (e.g., "BTCUSDT", "EURUSD")
    exchange: str                 # Exchange/venue code
    
    # Timestamps (all in nanoseconds since Unix epoch)
    exchange_ts: int              # Exchange timestamp
    receive_ts: int               # Gateway receive timestamp
    process_ts: int               # Normalizer process timestamp
    
    # Sequence
    sequence_num: int             # Exchange sequence number
    local_sequence: int           # Local monotonic sequence
    
    # Quality
    quality_flags: int            # Bitfield of QualityFlag
    
    # Payload (one of these will be populated based on event_type)
    trade: Optional[TradeEvent] = None
    quote: Optional[QuoteEvent] = None
    l2_book: Optional[L2BookSnapshot] = None
    
    # Optional metadata
    raw_message: Optional[bytes] = None  # Original message for debugging
    
    def __post_init__(self):
        """Validate event consistency"""
        if self.event_type == MarketEventType.TRADE and self.trade is None:
            raise ValueError("TRADE event requires trade payload")
        if self.event_type == MarketEventType.QUOTE and self.quote is None:
            raise ValueError("QUOTE event requires quote payload")
        if self.event_type in (MarketEventType.L2_SNAPSHOT, MarketEventType.L2_DELTA) and self.l2_book is None:
            raise ValueError("L2 event requires l2_book payload")
    
    @property
    def latency_ns(self) -> int:
        """Processing latency in nanoseconds"""
        return self.process_ts - self.exchange_ts
    
    @property
    def latency_us(self) -> float:
        """Processing latency in microseconds"""
        return self.latency_ns / 1000
    
    @property
    def latency_ms(self) -> float:
        """Processing latency in milliseconds"""
        return self.latency_ns / 1_000_000
    
    def has_quality_flag(self, flag: QualityFlag) -> bool:
        """Check if quality flag is set"""
        return bool(self.quality_flags & flag.value)
    
    def add_quality_flag(self, flag: QualityFlag):
        """Add quality flag"""
        self.quality_flags |= flag.value
    
    def to_bytes(self) -> bytes:
        """
        Binary serialization format:
        - Magic (2 bytes): 0xAA01
        - Version (2 bytes): schema version encoded
        - Event type (1 byte)
        - Flags (1 byte): quality flags
        - Symbol (16 bytes): null-padded
        - Exchange (8 bytes): null-padded
        - Event ID (36 bytes): UUID string
        - Exchange TS (8 bytes): int64
        - Receive TS (8 bytes): int64
        - Process TS (8 bytes): int64
        - Sequence num (8 bytes): int64
        - Local sequence (8 bytes): int64
        - Payload length (4 bytes): uint32
        - Payload (variable): type-specific
        """
        symbol_bytes = self.symbol.encode('utf-8')[:16].ljust(16, b'\x00')
        exchange_bytes = self.exchange.encode('utf-8')[:8].ljust(8, b'\x00')
        event_id_bytes = self.event_id.encode('utf-8')[:36].ljust(36, b'\x00')
        
        # Encode version as major.minor packed
        version_parts = SCHEMA_VERSION.split('.')
        version_encoded = (int(version_parts[0]) << 8) | int(version_parts[1])
        
        header = struct.pack(
            '>HHBB16s8s36sqqqqq',
            SCHEMA_MAGIC,
            version_encoded,
            self.event_type.value,
            self.quality_flags & 0xFF,
            symbol_bytes,
            exchange_bytes,
            event_id_bytes,
            self.exchange_ts,
            self.receive_ts,
            self.process_ts,
            self.sequence_num,
            self.local_sequence
        )
        
        # Serialize payload
        payload = b''
        if self.trade:
            payload = self.trade.to_bytes()
        elif self.quote:
            payload = self.quote.to_bytes()
        elif self.l2_book:
            payload = self.l2_book.to_bytes()
        
        payload_header = struct.pack('>I', len(payload))
        
        return header + payload_header + payload
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'MarketEvent':
        """Deserialize from bytes"""
        # Parse header
        magic, version, event_type, quality_flags = struct.unpack('>HHBB', data[:6])
        
        if magic != SCHEMA_MAGIC:
            raise ValueError(f"Invalid magic: {hex(magic)}")
        
        symbol = data[6:22].rstrip(b'\x00').decode('utf-8')
        exchange = data[22:30].rstrip(b'\x00').decode('utf-8')
        event_id = data[30:66].rstrip(b'\x00').decode('utf-8')
        
        exchange_ts, receive_ts, process_ts, seq_num, local_seq = struct.unpack(
            '>qqqqq', data[66:106]
        )
        
        payload_len = struct.unpack('>I', data[106:110])[0]
        payload_data = data[110:110+payload_len]
        
        # Parse payload based on event type
        trade = None
        quote = None
        l2_book = None
        
        evt = MarketEventType(event_type)
        if evt == MarketEventType.TRADE and payload_data:
            trade = TradeEvent.from_bytes(payload_data)
        elif evt == MarketEventType.QUOTE and payload_data:
            quote = QuoteEvent.from_bytes(payload_data)
        elif evt in (MarketEventType.L2_SNAPSHOT, MarketEventType.L2_DELTA) and payload_data:
            l2_book = L2BookSnapshot.from_bytes(payload_data)
        
        return cls(
            event_id=event_id,
            event_type=evt,
            symbol=symbol,
            exchange=exchange,
            exchange_ts=exchange_ts,
            receive_ts=receive_ts,
            process_ts=process_ts,
            sequence_num=seq_num,
            local_sequence=local_seq,
            quality_flags=quality_flags,
            trade=trade,
            quote=quote,
            l2_book=l2_book
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            'event_id': self.event_id,
            'event_type': self.event_type.name,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'exchange_ts': self.exchange_ts,
            'receive_ts': self.receive_ts,
            'process_ts': self.process_ts,
            'sequence_num': self.sequence_num,
            'local_sequence': self.local_sequence,
            'quality_flags': self.quality_flags,
            'latency_us': self.latency_us,
        }
        
        if self.trade:
            result['trade'] = {
                'price': self.trade.price,
                'size': self.trade.size,
                'side': self.trade.side.name,
                'trade_id': self.trade.trade_id,
                'conditions': [c.name for c in self.trade.conditions]
            }
        
        if self.quote:
            result['quote'] = {
                'bid_price': self.quote.bid_price,
                'bid_size': self.quote.bid_size,
                'ask_price': self.quote.ask_price,
                'ask_size': self.quote.ask_size,
                'mid_price': self.quote.mid_price,
                'spread_bps': self.quote.spread_bps,
            }
        
        if self.l2_book:
            result['l2_book'] = {
                'depth': self.l2_book.depth,
                'is_snapshot': self.l2_book.is_snapshot,
                'imbalance': self.l2_book.imbalance,
                'bids': [
                    {'price': l.price, 'size': l.size, 'orders': l.order_count}
                    for l in self.l2_book.bids[:10]
                ],
                'asks': [
                    {'price': l.price, 'size': l.size, 'orders': l.order_count}
                    for l in self.l2_book.asks[:10]
                ],
            }
        
        return result
    
    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(self.to_dict())
    
    def checksum(self) -> str:
        """Calculate event checksum for integrity verification"""
        data = f"{self.event_id}:{self.symbol}:{self.exchange_ts}:{self.sequence_num}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass(slots=True)
class EventEnvelope:
    """
    Wrapper for batched events with routing metadata.
    Used for Kafka/Redpanda message envelope.
    """
    batch_id: str                 # Batch identifier
    source_id: str                # Collector/source identifier
    partition_key: str            # Kafka partition key
    events: List[MarketEvent]     # Batch of events
    created_ts: int               # Batch creation timestamp (ns)
    compressed: bool = False      # Whether payload is compressed
    compression_algo: str = ''    # 'lz4', 'zstd', 'snappy'
    
    @property
    def event_count(self) -> int:
        return len(self.events)
    
    def to_bytes(self) -> bytes:
        """Serialize envelope with all events"""
        batch_id_bytes = self.batch_id.encode('utf-8')[:36].ljust(36, b'\x00')
        source_id_bytes = self.source_id.encode('utf-8')[:32].ljust(32, b'\x00')
        partition_key_bytes = self.partition_key.encode('utf-8')[:32].ljust(32, b'\x00')
        compression_bytes = self.compression_algo.encode('utf-8')[:8].ljust(8, b'\x00')
        
        header = struct.pack(
            '>36s32s32sq?8sI',
            batch_id_bytes,
            source_id_bytes,
            partition_key_bytes,
            self.created_ts,
            self.compressed,
            compression_bytes,
            len(self.events)
        )
        
        events_data = b''.join(
            struct.pack('>I', len(e.to_bytes())) + e.to_bytes()
            for e in self.events
        )
        
        return header + events_data
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'EventEnvelope':
        """Deserialize envelope"""
        batch_id = data[:36].rstrip(b'\x00').decode('utf-8')
        source_id = data[36:68].rstrip(b'\x00').decode('utf-8')
        partition_key = data[68:100].rstrip(b'\x00').decode('utf-8')
        created_ts, compressed, compression_bytes, event_count = struct.unpack(
            '>q?8sI', data[100:121]
        )
        compression_algo = compression_bytes.rstrip(b'\x00').decode('utf-8')
        
        offset = 121
        events = []
        for _ in range(event_count):
            event_len = struct.unpack('>I', data[offset:offset+4])[0]
            offset += 4
            events.append(MarketEvent.from_bytes(data[offset:offset+event_len]))
            offset += event_len
        
        return cls(
            batch_id=batch_id,
            source_id=source_id,
            partition_key=partition_key,
            events=events,
            created_ts=created_ts,
            compressed=compressed,
            compression_algo=compression_algo
        )


# Protobuf-equivalent schema definition for documentation
PROTOBUF_SCHEMA = """
// AlphaAlgo Market Event Schema v1.0.0
// Compatible with Protobuf 3

syntax = "proto3";
package alphaalgo.market;

option optimize_for = SPEED;

enum MarketEventType {
    UNKNOWN = 0;
    TRADE = 1;
    QUOTE = 2;
    L2_SNAPSHOT = 3;
    L2_DELTA = 4;
    HEARTBEAT = 5;
    STATUS = 6;
    AUCTION = 7;
    IMBALANCE = 8;
    HALT = 9;
    RESUME = 10;
}

enum TradeSide {
    SIDE_UNKNOWN = 0;
    BUY = 1;
    SELL = 2;
}

enum TradeCondition {
    REGULAR = 0;
    ODD_LOT = 1;
    BLOCK = 2;
    CROSS = 3;
    SWEEP = 4;
    OPENING = 5;
    CLOSING = 6;
    AUCTION = 7;
    INTERMARKET_SWEEP = 8;
    DERIVATIVELY_PRICED = 9;
}

message L2PriceLevel {
    double price = 1;
    double size = 2;
    uint32 order_count = 3;
}

message TradeEvent {
    double price = 1;
    double size = 2;
    TradeSide side = 3;
    string trade_id = 4;
    repeated TradeCondition conditions = 5;
}

message QuoteEvent {
    double bid_price = 1;
    double bid_size = 2;
    double ask_price = 3;
    double ask_size = 4;
    string bid_exchange = 5;
    string ask_exchange = 6;
}

message L2BookSnapshot {
    repeated L2PriceLevel bids = 1;
    repeated L2PriceLevel asks = 2;
    uint32 depth = 3;
    bool is_snapshot = 4;
}

message ExchangeMetadata {
    string exchange_id = 1;
    string exchange_name = 2;
    string asset_class = 3;
    string feed_type = 4;
    string feed_tier = 5;
    string timezone = 6;
    string currency = 7;
    double lot_size = 8;
    double tick_size = 9;
    string trading_hours_utc = 10;
}

message MarketEvent {
    // Identity
    string event_id = 1;
    MarketEventType event_type = 2;
    
    // Instrument
    string symbol = 3;
    string exchange = 4;
    
    // Timestamps (nanoseconds since Unix epoch)
    sfixed64 exchange_ts = 5;
    sfixed64 receive_ts = 6;
    sfixed64 process_ts = 7;
    
    // Sequence
    sfixed64 sequence_num = 8;
    sfixed64 local_sequence = 9;
    
    // Quality
    uint32 quality_flags = 10;
    
    // Payload (oneof)
    oneof payload {
        TradeEvent trade = 11;
        QuoteEvent quote = 12;
        L2BookSnapshot l2_book = 13;
    }
    
    // Debug
    bytes raw_message = 14;
}

message EventEnvelope {
    string batch_id = 1;
    string source_id = 2;
    string partition_key = 3;
    repeated MarketEvent events = 4;
    sfixed64 created_ts = 5;
    bool compressed = 6;
    string compression_algo = 7;
}
"""


# JSON Schema for validation
JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "AlphaAlgo Market Event",
    "version": SCHEMA_VERSION,
    "type": "object",
    "required": ["event_id", "event_type", "symbol", "exchange", "exchange_ts", "sequence_num"],
    "properties": {
        "event_id": {"type": "string", "format": "uuid"},
        "event_type": {
            "type": "string",
            "enum": ["UNKNOWN", "TRADE", "QUOTE", "L2_SNAPSHOT", "L2_DELTA", 
                     "HEARTBEAT", "STATUS", "AUCTION", "IMBALANCE", "HALT", "RESUME"]
        },
        "symbol": {"type": "string", "maxLength": 16},
        "exchange": {"type": "string", "maxLength": 8},
        "exchange_ts": {"type": "integer"},
        "receive_ts": {"type": "integer"},
        "process_ts": {"type": "integer"},
        "sequence_num": {"type": "integer"},
        "local_sequence": {"type": "integer"},
        "quality_flags": {"type": "integer", "minimum": 0, "maximum": 255},
        "trade": {
            "type": "object",
            "properties": {
                "price": {"type": "number"},
                "size": {"type": "number"},
                "side": {"type": "string", "enum": ["UNKNOWN", "BUY", "SELL"]},
                "trade_id": {"type": "string"},
                "conditions": {"type": "array", "items": {"type": "string"}}
            }
        },
        "quote": {
            "type": "object",
            "properties": {
                "bid_price": {"type": "number"},
                "bid_size": {"type": "number"},
                "ask_price": {"type": "number"},
                "ask_size": {"type": "number"},
                "mid_price": {"type": "number"},
                "spread_bps": {"type": "number"}
            }
        },
        "l2_book": {
            "type": "object",
            "properties": {
                "depth": {"type": "integer"},
                "is_snapshot": {"type": "boolean"},
                "imbalance": {"type": "number"},
                "bids": {"type": "array"},
                "asks": {"type": "array"}
            }
        }
    }
}
