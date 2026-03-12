"""
Real-time data streaming using Kafka
Implements high-throughput market data ingestion
"""

import asyncio
import logging
import json
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import threading

logger = logging.getLogger(__name__)


@dataclass
class StreamConfig:
    """Kafka stream configuration"""
    bootstrap_servers: List[str] = field(default_factory=lambda: ['localhost:9092'])
    topics: List[str] = field(default_factory=list)
    group_id: str = 'alphaalgo_consumer'
    auto_offset_reset: str = 'latest'
    enable_auto_commit: bool = True
    max_poll_records: int = 500
    session_timeout_ms: int = 30000
    
    # Producer config
    compression_type: str = 'gzip'
    acks: str = 'all'
    retries: int = 3


@dataclass
class MarketDataMessage:
    """Market data message structure"""
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    last: float
    volume: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class KafkaStreamManager:
    """
    Manages Kafka streaming for real-time market data
    Handles both producing and consuming market data
    """
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self.producer = None
        self.consumer = None
        self.running = False
        self.callbacks: Dict[str, List[Callable]] = {}
        self.message_buffer = deque(maxlen=10000)
        self.stats = {
            'messages_received': 0,
            'messages_sent': 0,
            'errors': 0,
            'last_message_time': None
        }
        
    async def initialize(self):
        """Initialize Kafka producer and consumer"""
        try:
            # Try to import kafka-python
            from kafka import KafkaProducer, KafkaConsumer
            
            # Initialize producer
            self.producer = KafkaProducer(
                bootstrap_servers=self.config.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                compression_type=self.config.compression_type,
                acks=self.config.acks,
                retries=self.config.retries
            )
            
            # Initialize consumer
            if self.config.topics:
                self.consumer = KafkaConsumer(
                    *self.config.topics,
                    bootstrap_servers=self.config.bootstrap_servers,
                    group_id=self.config.group_id,
                    auto_offset_reset=self.config.auto_offset_reset,
                    enable_auto_commit=self.config.enable_auto_commit,
                    max_poll_records=self.config.max_poll_records,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
                )
            
            logger.info("Kafka stream manager initialized successfully")
            
        except ImportError:
            logger.warning("kafka-python not installed, using mock implementation")
            self.producer = MockKafkaProducer()
            self.consumer = MockKafkaConsumer()
        except Exception as e:
            logger.error(f"Failed to initialize Kafka: {e}")
            # Fallback to mock
            self.producer = MockKafkaProducer()
            self.consumer = MockKafkaConsumer()
    
    async def start(self):
        """Start consuming messages"""
        if not self.consumer:
            await self.initialize()
        
        self.running = True
        asyncio.create_task(self._consume_loop())
        logger.info("Kafka stream started")
    
    async def stop(self):
        """Stop consuming messages"""
        self.running = False
        if self.producer:
            self.producer.close()
        if self.consumer:
            self.consumer.close()
        logger.info("Kafka stream stopped")
    
    async def _consume_loop(self):
        """Main consumption loop"""
        while self.running:
            try:
                # Poll for messages
                messages = self.consumer.poll(timeout_ms=1000)
                
                for topic_partition, records in messages.items():
                    for record in records:
                        await self._process_message(record.value, record.topic)
                        self.stats['messages_received'] += 1
                        self.stats['last_message_time'] = datetime.now()
                
                await asyncio.sleep(0.01)  # Small delay to prevent CPU spinning
                
            except Exception as e:
                logger.error(f"Error in consume loop: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(1)
    
    async def _process_message(self, message: Dict[str, Any], topic: str):
        """Process incoming message"""
        try:
            # Add to buffer
            self.message_buffer.append({
                'topic': topic,
                'message': message,
                'timestamp': datetime.now()
            })
            
            # Call registered callbacks
            if topic in self.callbacks:
                for callback in self.callbacks[topic]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(message)
                        else:
                            callback(message)
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def publish(self, topic: str, message: Dict[str, Any]):
        """Publish message to Kafka topic"""
        try:
            if not self.producer:
                await self.initialize()
            
            future = self.producer.send(topic, message)
            # Wait for send to complete
            future.get(timeout=10)
            
            self.stats['messages_sent'] += 1
            
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            self.stats['errors'] += 1
    
    def subscribe(self, topic: str, callback: Callable):
        """Subscribe to topic with callback"""
        if topic not in self.callbacks:
            self.callbacks[topic] = []
        self.callbacks[topic].append(callback)
        logger.info(f"Subscribed to topic: {topic}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics"""
        return {
            **self.stats,
            'buffer_size': len(self.message_buffer),
            'running': self.running
        }


class MockKafkaProducer:
    """Mock Kafka producer for testing"""
    def __init__(self):
        self.messages = []
    
    def send(self, topic, message):
        self.messages.append({'topic': topic, 'message': message})
        return MockFuture()
    


class MockKafkaConsumer:
    """Mock Kafka consumer for testing"""
    def __init__(self):
        self.messages = []
    
    def poll(self, timeout_ms=1000):
        pass
    
    def close(self):
        pass


class MockFuture:
    """Mock future for testing"""
    def get(self, timeout=10):
        return None


# Market data specific streaming
class MarketDataStream:
    """
    High-level market data streaming interface
    Wraps Kafka stream manager with market data specific logic
    """
    
    def __init__(self, config: StreamConfig):
        self.stream_manager = KafkaStreamManager(config)
        self.subscribers: Dict[str, List[Callable]] = {}
        
    async def initialize(self):
        """Initialize stream"""
        await self.stream_manager.initialize()
        
        # Subscribe to market data topics
        self.stream_manager.subscribe('market_data', self._handle_market_data)
        self.stream_manager.subscribe('trades', self._handle_trades)
        self.stream_manager.subscribe('orderbook', self._handle_orderbook)
    
    async def start(self):
        """Start streaming"""
        await self.stream_manager.start()
    
    async def stop(self):
        """Stop streaming"""
        await self.stream_manager.stop()
    
    async def _handle_market_data(self, message: Dict[str, Any]):
        """Handle market data message"""
        try:
            # Parse message
            data = MarketDataMessage(
                symbol=message['symbol'],
                timestamp=datetime.fromisoformat(message['timestamp']),
                bid=message['bid'],
                ask=message['ask'],
                last=message['last'],
                volume=message['volume'],
                source=message.get('source', 'unknown'),
                metadata=message.get('metadata', {})
            )
            
            # Notify subscribers
            if data.symbol in self.subscribers:
                for callback in self.subscribers[data.symbol]:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
        
        except Exception as e:
            logger.error(f"Error handling market data: {e}")
    
    async def _handle_trades(self, message: Dict[str, Any]):
        """Handle trade message"""
        logger.debug(f"Trade: {message}")
    
    async def _handle_orderbook(self, message: Dict[str, Any]):
        """Handle orderbook message"""
        logger.debug(f"Orderbook: {message}")
    
    def subscribe_symbol(self, symbol: str, callback: Callable):
        """Subscribe to symbol updates"""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)
        logger.info(f"Subscribed to symbol: {symbol}")
    
    async def publish_market_data(self, data: MarketDataMessage):
        """Publish market data"""
        message = {
            'symbol': data.symbol,
            'timestamp': data.timestamp.isoformat(),
            'bid': data.bid,
            'ask': data.ask,
            'last': data.last,
            'volume': data.volume,
            'source': data.source,
            'metadata': data.metadata
        }
        await self.stream_manager.publish('market_data', message)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics"""
        return self.stream_manager.get_stats()
