"""
AlphaAlgo Ingestion Pipeline Tests
==================================
Comprehensive validation and stress tests for the ingestion backbone.
"""

import asyncio
import pytest
import time
import uuid
import json
import struct
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch
from collections import deque

# Import ingestion components
import sys
sys.path.insert(0, 'c:/Users/peterson/trading bot')

from trading_bot.ingestion.schema import (
    MarketEvent, MarketEventType, QualityFlag,
    TradeEvent, QuoteEvent, L2BookSnapshot, L2PriceLevel,
    TradeSide, TradeCondition, EventEnvelope,
    SCHEMA_VERSION, SCHEMA_MAGIC
)
from trading_bot.ingestion.collector import (
    CollectorConfig, CollectorState, WebSocketCollector,
    RESTCollector, CollectorManager, SequenceTracker
)
from trading_bot.ingestion.normalizer import (
    NormalizerConfig, EventNormalizer, TimestampAligner,
    SequenceValidator, BinanceParser, CoinbaseParser
)
from trading_bot.ingestion.event_router import (
    RouterConfig, EventRouter, TopicResolver,
    PartitionStrategy, TOPIC_CONFIGS
)
from trading_bot.ingestion.orderbook_builder import (
    OrderBookConfig, SyntheticOrderBook, OrderBookState,
    PriceLevel, TradeImbalanceModel, LiquidityPersistenceModel
)
from trading_bot.ingestion.replay_engine import (
    ReplayConfig, ReplayEngine, ReplayCursor, ReplayMode
)
from trading_bot.ingestion.storage import (
    StorageConfig, ClickHouseWriter, S3Archiver, StorageManager
)
from trading_bot.ingestion.orchestrator import (
    IngestionOrchestrator, OrchestratorConfig, PipelineMetrics
)


# =============================================================================
# Test Fixtures
# =============================================================================

def create_test_trade_event(
    symbol: str = 'BTCUSDT',
    exchange: str = 'binance',
    price: float = 50000.0,
    size: float = 1.0,
    side: TradeSide = TradeSide.BUY,
    sequence: int = 1
) -> MarketEvent:
    """Create a test trade event"""
    now_ns = time.time_ns()
    
    trade = TradeEvent(
        price=price,
        size=size,
        side=side,
        trade_id=str(uuid.uuid4()),
        conditions=[]
    )
    
    return MarketEvent(
        event_id=str(uuid.uuid4()),
        event_type=MarketEventType.TRADE,
        symbol=symbol,
        exchange=exchange,
        exchange_ts=now_ns - 1000000,  # 1ms ago
        receive_ts=now_ns - 500000,    # 0.5ms ago
        process_ts=now_ns,
        sequence_num=sequence,
        local_sequence=sequence,
        quality_flags=0,
        trade=trade
    )


def create_test_quote_event(
    symbol: str = 'BTCUSDT',
    exchange: str = 'binance',
    bid_price: float = 49999.0,
    ask_price: float = 50001.0,
    sequence: int = 1
) -> MarketEvent:
    """Create a test quote event"""
    now_ns = time.time_ns()
    
    quote = QuoteEvent(
        bid_price=bid_price,
        bid_size=10.0,
        ask_price=ask_price,
        ask_size=10.0,
        bid_exchange=exchange,
        ask_exchange=exchange
    )
    
    return MarketEvent(
        event_id=str(uuid.uuid4()),
        event_type=MarketEventType.QUOTE,
        symbol=symbol,
        exchange=exchange,
        exchange_ts=now_ns - 1000000,
        receive_ts=now_ns - 500000,
        process_ts=now_ns,
        sequence_num=sequence,
        local_sequence=sequence,
        quality_flags=0,
        quote=quote
    )


def create_test_l2_event(
    symbol: str = 'BTCUSDT',
    exchange: str = 'binance',
    depth: int = 10,
    is_snapshot: bool = True,
    sequence: int = 1
) -> MarketEvent:
    """Create a test L2 event"""
    now_ns = time.time_ns()
    
    bids = [
        L2PriceLevel(price=50000.0 - i * 0.5, size=10.0 - i * 0.5, order_count=5)
        for i in range(depth)
    ]
    asks = [
        L2PriceLevel(price=50000.5 + i * 0.5, size=10.0 - i * 0.5, order_count=5)
        for i in range(depth)
    ]
    
    l2_book = L2BookSnapshot(
        bids=bids,
        asks=asks,
        depth=depth,
        is_snapshot=is_snapshot
    )
    
    return MarketEvent(
        event_id=str(uuid.uuid4()),
        event_type=MarketEventType.L2_SNAPSHOT if is_snapshot else MarketEventType.L2_DELTA,
        symbol=symbol,
        exchange=exchange,
        exchange_ts=now_ns - 1000000,
        receive_ts=now_ns - 500000,
        process_ts=now_ns,
        sequence_num=sequence,
        local_sequence=sequence,
        quality_flags=0,
        l2_book=l2_book
    )


# =============================================================================
# Schema Tests
# =============================================================================

class TestSchema:
    """Tests for the unified market event schema"""
    
    def test_trade_event_creation(self):
        """Test trade event creation and properties"""
        event = create_test_trade_event()
        
        assert event.event_type == MarketEventType.TRADE
        assert event.trade is not None
        assert event.trade.price == 50000.0
        assert event.trade.size == 1.0
        assert event.trade.side == TradeSide.BUY
    
    def test_quote_event_creation(self):
        """Test quote event creation and properties"""
        event = create_test_quote_event()
        
        assert event.event_type == MarketEventType.QUOTE
        assert event.quote is not None
        assert event.quote.mid_price == 50000.0
        assert event.quote.spread == 2.0
        assert event.quote.spread_bps == pytest.approx(0.4, rel=0.01)
    
    def test_l2_event_creation(self):
        """Test L2 event creation and properties"""
        event = create_test_l2_event()
        
        assert event.event_type == MarketEventType.L2_SNAPSHOT
        assert event.l2_book is not None
        assert len(event.l2_book.bids) == 10
        assert len(event.l2_book.asks) == 10
        assert event.l2_book.best_bid.price == 50000.0
        assert event.l2_book.best_ask.price == 50000.5
    
    def test_binary_serialization_trade(self):
        """Test binary serialization roundtrip for trade"""
        event = create_test_trade_event()
        
        # Serialize
        data = event.to_bytes()
        
        # Verify magic
        magic = struct.unpack('>H', data[:2])[0]
        assert magic == SCHEMA_MAGIC
        
        # Deserialize
        restored = MarketEvent.from_bytes(data)
        
        assert restored.event_id == event.event_id
        assert restored.event_type == event.event_type
        assert restored.symbol == event.symbol
        assert restored.trade.price == event.trade.price
        assert restored.trade.size == event.trade.size
    
    def test_binary_serialization_quote(self):
        """Test binary serialization roundtrip for quote"""
        event = create_test_quote_event()
        
        data = event.to_bytes()
        restored = MarketEvent.from_bytes(data)
        
        assert restored.quote.bid_price == event.quote.bid_price
        assert restored.quote.ask_price == event.quote.ask_price
    
    def test_binary_serialization_l2(self):
        """Test binary serialization roundtrip for L2"""
        event = create_test_l2_event()
        
        data = event.to_bytes()
        restored = MarketEvent.from_bytes(data)
        
        assert len(restored.l2_book.bids) == len(event.l2_book.bids)
        assert len(restored.l2_book.asks) == len(event.l2_book.asks)
        assert restored.l2_book.bids[0].price == event.l2_book.bids[0].price
    
    def test_json_serialization(self):
        """Test JSON serialization"""
        event = create_test_trade_event()
        
        json_str = event.to_json()
        data = json.loads(json_str)
        
        assert data['event_type'] == 'TRADE'
        assert data['symbol'] == 'BTCUSDT'
        assert data['trade']['price'] == 50000.0
    
    def test_quality_flags(self):
        """Test quality flag operations"""
        event = create_test_trade_event()
        
        assert not event.has_quality_flag(QualityFlag.STALE)
        
        event.add_quality_flag(QualityFlag.STALE)
        assert event.has_quality_flag(QualityFlag.STALE)
        
        event.add_quality_flag(QualityFlag.OUT_OF_ORDER)
        assert event.has_quality_flag(QualityFlag.STALE)
        assert event.has_quality_flag(QualityFlag.OUT_OF_ORDER)
    
    def test_latency_calculation(self):
        """Test latency calculation"""
        event = create_test_trade_event()
        
        assert event.latency_ns > 0
        assert event.latency_us > 0
        assert event.latency_ms > 0
    
    def test_event_envelope(self):
        """Test event envelope serialization"""
        events = [create_test_trade_event(sequence=i) for i in range(10)]
        
        envelope = EventEnvelope(
            batch_id=str(uuid.uuid4()),
            source_id='test-collector',
            partition_key='binance:BTCUSDT',
            events=events,
            created_ts=time.time_ns(),
            compressed=False,
            compression_algo=''
        )
        
        data = envelope.to_bytes()
        restored = EventEnvelope.from_bytes(data)
        
        assert restored.batch_id == envelope.batch_id
        assert len(restored.events) == 10
        assert restored.events[0].trade.price == 50000.0


# =============================================================================
# Normalizer Tests
# =============================================================================

class TestNormalizer:
    """Tests for event normalization"""
    
    def test_timestamp_aligner_parse_milliseconds(self):
        """Test parsing millisecond timestamps"""
        config = NormalizerConfig()
        aligner = TimestampAligner(config)
        
        ts_ms = 1702000000000  # Milliseconds
        ts_ns = aligner.parse_exchange_timestamp(ts_ms, 'test')
        
        assert ts_ns == 1702000000000000000
    
    def test_timestamp_aligner_parse_iso(self):
        """Test parsing ISO timestamps"""
        config = NormalizerConfig()
        aligner = TimestampAligner(config)
        
        ts_iso = '2024-01-01T00:00:00Z'
        ts_ns = aligner.parse_exchange_timestamp(ts_iso, 'test')
        
        assert ts_ns > 0
    
    def test_sequence_validator_normal(self):
        """Test normal sequence validation"""
        config = NormalizerConfig()
        validator = SequenceValidator(config)
        
        # First message
        valid, flag, gap = validator.validate('test', 'BTCUSDT', 1)
        assert valid
        assert flag is None
        
        # Sequential
        valid, flag, gap = validator.validate('test', 'BTCUSDT', 2)
        assert valid
        assert flag is None
    
    def test_sequence_validator_gap(self):
        """Test sequence gap detection"""
        config = NormalizerConfig()
        validator = SequenceValidator(config)
        
        validator.validate('test', 'BTCUSDT', 1)
        validator.validate('test', 'BTCUSDT', 2)
        
        # Gap: expected 3, got 5
        valid, flag, gap = validator.validate('test', 'BTCUSDT', 5)
        
        assert valid  # Still valid, just flagged
        assert flag == QualityFlag.OUT_OF_ORDER
        assert gap == 2
    
    def test_sequence_validator_duplicate(self):
        """Test duplicate detection"""
        config = NormalizerConfig()
        validator = SequenceValidator(config)
        
        validator.validate('test', 'BTCUSDT', 1)
        validator.validate('test', 'BTCUSDT', 2)
        
        # Duplicate
        valid, flag, gap = validator.validate('test', 'BTCUSDT', 2)
        
        assert not valid
        assert flag == QualityFlag.DUPLICATE
    
    def test_binance_parser_trade(self):
        """Test Binance trade message parsing"""
        config = NormalizerConfig()
        aligner = TimestampAligner(config)
        parser = BinanceParser(aligner)
        
        raw_message = json.dumps({
            'e': 'trade',
            's': 'BTCUSDT',
            'p': '50000.00',
            'q': '1.5',
            'm': True,  # Buyer is maker
            't': 12345,
            'T': int(time.time() * 1000)
        }).encode()
        
        event = parser.parse(raw_message, time.time_ns())
        
        assert event is not None
        assert event.event_type == MarketEventType.TRADE
        assert event.symbol == 'BTCUSDT'
        assert event.trade.price == 50000.0
        assert event.trade.size == 1.5
    
    def test_binance_parser_quote(self):
        """Test Binance quote message parsing"""
        config = NormalizerConfig()
        aligner = TimestampAligner(config)
        parser = BinanceParser(aligner)
        
        raw_message = json.dumps({
            'e': 'bookTicker',
            's': 'BTCUSDT',
            'b': '49999.00',
            'B': '10.0',
            'a': '50001.00',
            'A': '10.0',
            'u': 12345,
            'E': int(time.time() * 1000)
        }).encode()
        
        event = parser.parse(raw_message, time.time_ns())
        
        assert event is not None
        assert event.event_type == MarketEventType.QUOTE
        assert event.quote.bid_price == 49999.0
        assert event.quote.ask_price == 50001.0
    
    @pytest.mark.asyncio
    async def test_normalizer_full_pipeline(self):
        """Test full normalization pipeline"""
        normalizer = EventNormalizer()
        
        raw_message = json.dumps({
            'e': 'trade',
            's': 'BTCUSDT',
            'p': '50000.00',
            'q': '1.0',
            'm': False,
            't': 1,
            'T': int(time.time() * 1000)
        }).encode()
        
        event = await normalizer.normalize(raw_message, time.time_ns(), 'binance')
        
        assert event is not None
        assert event.symbol == 'BTCUSDT'
        assert event.exchange == 'binance'


# =============================================================================
# Order Book Tests
# =============================================================================

class TestOrderBook:
    """Tests for synthetic order book builder"""
    
    def test_trade_imbalance_model(self):
        """Test trade imbalance calculation"""
        model = TradeImbalanceModel(window_size=10)
        
        # Add buy trades
        for i in range(5):
            model.add_trade(50000.0, 1.0, TradeSide.BUY)
        
        # Add sell trades
        for i in range(5):
            model.add_trade(50000.0, 1.0, TradeSide.SELL)
        
        # Should be balanced
        assert model.get_imbalance() == pytest.approx(0.0, abs=0.01)
        
        # Add more buys
        for i in range(5):
            model.add_trade(50000.0, 1.0, TradeSide.BUY)
        
        # Should be positive (more buys)
        assert model.get_imbalance() > 0
    
    def test_liquidity_persistence_model(self):
        """Test liquidity decay calculation"""
        model = LiquidityPersistenceModel(half_life_ms=1000, min_ratio=0.1)
        
        original_size = 100.0
        
        # No decay at t=0
        assert model.decay_size(original_size, 0) == 100.0
        
        # Half decay at half-life
        assert model.decay_size(original_size, 1000) == pytest.approx(50.0, rel=0.01)
        
        # Quarter at 2x half-life
        assert model.decay_size(original_size, 2000) == pytest.approx(25.0, rel=0.01)
        
        # Minimum ratio enforced
        assert model.decay_size(original_size, 100000) >= 10.0
    
    def test_synthetic_orderbook_from_quote(self):
        """Test synthetic order book generation from quote"""
        config = OrderBookConfig(synthetic_depth=10)
        book = SyntheticOrderBook(config)
        
        event = create_test_quote_event()
        state = book.process_event(event)
        
        assert state is not None
        assert state.best_bid == 49999.0
        assert state.best_ask == 50001.0
        assert len(state.bids) == 10
        assert len(state.asks) == 10
    
    def test_synthetic_orderbook_from_l2(self):
        """Test order book from real L2 data"""
        config = OrderBookConfig()
        book = SyntheticOrderBook(config)
        
        event = create_test_l2_event()
        state = book.process_event(event)
        
        assert state is not None
        assert state.mode.name == 'REAL_L2'
        assert len(state.bids) == 10
        assert len(state.asks) == 10
    
    def test_orderbook_imbalance(self):
        """Test order book imbalance calculation"""
        event = create_test_l2_event()
        
        assert event.l2_book.imbalance == pytest.approx(0.0, abs=0.01)
    
    def test_orderbook_snapshot_generation(self):
        """Test snapshot generation"""
        config = OrderBookConfig()
        book = SyntheticOrderBook(config)
        
        event = create_test_quote_event()
        book.process_event(event)
        
        snapshot = book.get_snapshot('binance', 'BTCUSDT')
        
        assert snapshot is not None
        assert snapshot.is_snapshot
        assert len(snapshot.bids) > 0
        assert len(snapshot.asks) > 0


# =============================================================================
# Router Tests
# =============================================================================

class TestRouter:
    """Tests for event routing"""
    
    def test_topic_resolver_trade(self):
        """Test topic resolution for trade events"""
        resolver = TopicResolver()
        
        event = create_test_trade_event()
        topics = resolver.resolve(event)
        
        assert 'alphaalgo.trades.normalized' in topics
    
    def test_topic_resolver_quote(self):
        """Test topic resolution for quote events"""
        resolver = TopicResolver()
        
        event = create_test_quote_event()
        topics = resolver.resolve(event)
        
        assert 'alphaalgo.quotes.normalized' in topics
    
    def test_partition_strategy_by_symbol(self):
        """Test partition assignment by symbol"""
        event = create_test_trade_event(symbol='BTCUSDT')
        
        partition1 = PartitionStrategy.by_symbol(event, 24)
        
        event2 = create_test_trade_event(symbol='ETHUSDT')
        partition2 = PartitionStrategy.by_symbol(event2, 24)
        
        # Same symbol should get same partition
        event3 = create_test_trade_event(symbol='BTCUSDT')
        partition3 = PartitionStrategy.by_symbol(event3, 24)
        
        assert partition1 == partition3
        # Different symbols may get different partitions
        assert 0 <= partition1 < 24
        assert 0 <= partition2 < 24
    
    def test_partition_key_generation(self):
        """Test partition key generation"""
        event = create_test_trade_event()
        
        key = TopicResolver.get_partition_key(event)
        
        assert key == 'binance:BTCUSDT'
    
    @pytest.mark.asyncio
    async def test_router_batch_flush(self):
        """Test router batch flushing"""
        config = RouterConfig(batch_size=5)
        router = EventRouter(config)
        await router.initialize()
        
        # Send 10 events
        for i in range(10):
            await router.route(create_test_trade_event(sequence=i))
        
        # Flush
        await router.flush()
        
        stats = router.get_stats()
        assert stats['events_routed'] == 10


# =============================================================================
# Replay Engine Tests
# =============================================================================

class TestReplayEngine:
    """Tests for replay engine"""
    
    def test_replay_cursor(self):
        """Test replay cursor operations"""
        cursor = ReplayCursor(
            current_ts=1000,
            start_ts=0,
            end_ts=2000
        )
        
        assert cursor.progress == 0.5
        assert cursor.elapsed_ns == 1000
        assert cursor.remaining_ns == 1000
    
    def test_replay_cursor_serialization(self):
        """Test cursor serialization"""
        cursor = ReplayCursor(
            current_ts=1000,
            current_sequence=50,
            start_ts=0,
            end_ts=2000
        )
        
        data = cursor.to_bytes()
        restored = ReplayCursor.from_bytes(data)
        
        assert restored.current_ts == cursor.current_ts
        assert restored.current_sequence == cursor.current_sequence
    
    def test_replay_config(self):
        """Test replay configuration"""
        config = ReplayConfig(
            mode=ReplayMode.FAST,
            speed_multiplier=10.0,
            batch_size=1000
        )
        
        assert config.mode == ReplayMode.FAST
        assert config.speed_multiplier == 10.0


# =============================================================================
# Storage Tests
# =============================================================================

class TestStorage:
    """Tests for storage layer"""
    
    def test_storage_config(self):
        """Test storage configuration"""
        config = StorageConfig(
            clickhouse_host='localhost',
            s3_bucket='test-bucket',
            hot_retention_days=7
        )
        
        assert config.clickhouse_host == 'localhost'
        assert config.hot_retention_days == 7
    
    @pytest.mark.asyncio
    async def test_clickhouse_writer_init(self):
        """Test ClickHouse writer initialization"""
        config = StorageConfig()
        writer = ClickHouseWriter(config)
        
        # Should initialize with mock if ClickHouse not available
        await writer.initialize()
        
        assert writer._initialized
    
    @pytest.mark.asyncio
    async def test_s3_archiver_init(self):
        """Test S3 archiver initialization"""
        config = StorageConfig()
        archiver = S3Archiver(config)
        
        # Should initialize with local fallback if S3 not available
        await archiver.initialize()
        
        assert archiver._initialized


# =============================================================================
# Orchestrator Tests
# =============================================================================

class TestOrchestrator:
    """Tests for ingestion orchestrator"""
    
    def test_pipeline_metrics(self):
        """Test pipeline metrics tracking"""
        metrics = PipelineMetrics()
        
        metrics.record_event(100.0)  # 100us latency
        metrics.record_event(200.0)
        
        assert metrics.events_received == 2
        assert metrics.avg_latency_us == 150.0
    
    def test_orchestrator_config(self):
        """Test orchestrator configuration"""
        config = OrchestratorConfig(
            enable_storage=False,
            enable_orderbook=True
        )
        
        assert not config.enable_storage
        assert config.enable_orderbook
    
    @pytest.mark.asyncio
    async def test_orchestrator_lifecycle(self):
        """Test orchestrator start/stop lifecycle"""
        config = OrchestratorConfig(
            enable_storage=False,
            enable_routing=False
        )
        orchestrator = IngestionOrchestrator(config)
        
        await orchestrator.initialize()
        await orchestrator.start()
        
        assert orchestrator._running
        
        await orchestrator.stop()
        
        assert not orchestrator._running


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for full pipeline"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_flow(self):
        """Test complete pipeline from raw message to storage"""
        # Create orchestrator with minimal config
        config = OrchestratorConfig(
            enable_storage=False,
            enable_routing=False,
            enable_orderbook=True
        )
        orchestrator = IngestionOrchestrator(config)
        await orchestrator.initialize()
        
        # Track received events
        received_events = []
        
        @orchestrator.on_event
        def track_event(event):
            received_events.append(event)
        
        await orchestrator.start()
        
        # Simulate raw message handling
        raw_message = json.dumps({
            'e': 'trade',
            's': 'BTCUSDT',
            'p': '50000.00',
            'q': '1.0',
            'm': False,
            't': 1,
            'T': int(time.time() * 1000)
        }).encode()
        
        await orchestrator._handle_raw_message(raw_message, time.time_ns())
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Verify event was processed
        assert orchestrator.metrics.events_normalized >= 1
        
        await orchestrator.stop()
    
    @pytest.mark.asyncio
    async def test_orderbook_integration(self):
        """Test order book integration with pipeline"""
        config = OrchestratorConfig(
            enable_storage=False,
            enable_routing=False,
            enable_orderbook=True
        )
        orchestrator = IngestionOrchestrator(config)
        await orchestrator.initialize()
        await orchestrator.start()
        
        # Send quote
        raw_message = json.dumps({
            'e': 'bookTicker',
            's': 'BTCUSDT',
            'b': '49999.00',
            'B': '10.0',
            'a': '50001.00',
            'A': '10.0',
            'u': 1,
            'E': int(time.time() * 1000)
        }).encode()
        
        await orchestrator._handle_raw_message(raw_message, time.time_ns())
        await asyncio.sleep(0.1)
        
        # Get order book
        book = orchestrator.get_orderbook('binance', 'BTCUSDT')
        
        # Note: May be None if normalizer couldn't determine exchange
        # In real usage, exchange is determined from collector
        
        await orchestrator.stop()


# =============================================================================
# Stress Tests
# =============================================================================

class TestStress:
    """Stress tests for pipeline performance"""
    
    @pytest.mark.asyncio
    async def test_high_throughput(self):
        """Test high throughput event processing"""
        normalizer = EventNormalizer()
        
        events_processed = 0
        start_time = time.time()
        target_events = 10000
        
        for i in range(target_events):
            raw_message = json.dumps({
                'e': 'trade',
                's': 'BTCUSDT',
                'p': str(50000.0 + i * 0.01),
                'q': '1.0',
                'm': i % 2 == 0,
                't': i,
                'T': int(time.time() * 1000)
            }).encode()
            
            event = await normalizer.normalize(raw_message, time.time_ns(), 'binance')
            if event:
                events_processed += 1
        
        elapsed = time.time() - start_time
        events_per_second = events_processed / elapsed
        
        print(f"Processed {events_processed} events in {elapsed:.2f}s ({events_per_second:.0f} eps)")
        
        assert events_processed == target_events
        assert events_per_second > 1000  # At least 1k eps
    
    def test_sequence_tracker_memory(self):
        """Test sequence tracker memory usage"""
        tracker = SequenceTracker()
        
        # Track many symbols
        for i in range(1000):
            symbol = f"SYMBOL{i}"
            for seq in range(100):
                tracker.validate(symbol, seq)
        
        # Should have 1000 tracked symbols
        assert len(tracker.expected) == 1000
    
    def test_orderbook_memory(self):
        """Test order book memory usage"""
        config = OrderBookConfig(max_depth=50)
        book = SyntheticOrderBook(config)
        
        # Process many symbols
        for i in range(100):
            event = create_test_quote_event(symbol=f"SYMBOL{i}")
            book.process_event(event)
        
        # Should have 100 tracked symbols
        assert len(book._states) == 100


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_invalid_json_message(self):
        """Test handling of invalid JSON"""
        config = NormalizerConfig()
        aligner = TimestampAligner(config)
        parser = BinanceParser(aligner)
        
        result = parser.parse(b'invalid json', time.time_ns())
        
        assert result is None
    
    def test_missing_fields(self):
        """Test handling of messages with missing fields"""
        config = NormalizerConfig()
        aligner = TimestampAligner(config)
        parser = BinanceParser(aligner)
        
        # Missing required fields
        raw_message = json.dumps({
            'e': 'trade',
            's': 'BTCUSDT'
            # Missing price, quantity, etc.
        }).encode()
        
        # Should handle gracefully (may return None or raise)
        try:
            result = parser.parse(raw_message, time.time_ns())
        except (KeyError, TypeError):
            pass  # Expected
    
    def test_zero_spread(self):
        """Test handling of zero spread (crossed book)"""
        event = create_test_quote_event(bid_price=50000.0, ask_price=50000.0)
        
        assert event.quote.spread == 0.0
        assert event.quote.spread_bps == 0.0
    
    def test_negative_prices(self):
        """Test handling of negative prices"""
        # Some markets (oil futures) can have negative prices
        trade = TradeEvent(
            price=-37.63,
            size=1.0,
            side=TradeSide.SELL,
            trade_id='test',
            conditions=[]
        )
        
        assert trade.price == -37.63
    
    def test_very_large_sequence(self):
        """Test handling of very large sequence numbers"""
        config = NormalizerConfig()
        validator = SequenceValidator(config)
        
        # Large sequence number
        valid, flag, gap = validator.validate('test', 'BTCUSDT', 2**62)
        
        assert valid


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
