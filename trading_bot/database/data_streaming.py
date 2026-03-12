"""
Data Streaming Module for Elite Trading Bot
Handles real-time market data streaming and processing
"""

import asyncio
import numpy as np
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from collections import deque
import logging
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

try:
    import redis.asyncio
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import zmq.asyncio
    ZMQ_AVAILABLE = True
except ImportError:
    ZMQ_AVAILABLE = False

logger = logging.getLogger(__name__)

class MarketDataStream:
    """
    High-performance market data streaming with real-time processing
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.streams: Dict[str, asyncio.Queue] = {}
        self.processors: Dict[str, List[Callable]] = {}
        self.buffer_sizes = config.get('buffer_sizes', {})
        self.buffers: Dict[str, deque] = {}
        
        # Redis for pub/sub and caching
        self.redis = None
        
        # Thread pool for CPU-intensive operations
        self.executor = ThreadPoolExecutor(
            max_workers=config.get('max_workers', 10)
        )
        
        # ZMQ for high-speed data distribution (optional)
        if ZMQ_AVAILABLE:
            self.zmq_context = zmq.asyncio.Context()
            self.publishers: Dict[str, Any] = {}
        else:
            self.zmq_context = None
            self.publishers = {}
        
        # Performance metrics
        self.metrics = {
            'messages_processed': 0,
            'processing_times': deque(maxlen=1000),
            'buffer_sizes': {},
            'last_update': datetime.now()
        }
    
    async def initialize(self):
        """Initialize connections and streams"""
        # Initialize Redis (optional)
        if REDIS_AVAILABLE and 'redis_url' in self.config:
            try:
                self.redis = await redis.asyncio.from_url(
                    self.config['redis_url'],
                    decode_responses=True
                )
            except Exception as e:
                logger.warning(f"Redis initialization failed: {e}. Continuing without Redis.")
                self.redis = None
        
        # Initialize ZMQ publishers (optional)
        if ZMQ_AVAILABLE:
            await self._setup_zmq_publishers()
        else:
            logger.info("ZMQ not available, using in-process queues")
            self.publishers = {
                data_type: asyncio.Queue() for data_type in ['ticks', 'bars', 'indicators', 'signals']
            }
        
        logger.info("Market data streaming initialized")
    
    async def _setup_zmq_publishers(self):
        """Setup ZMQ publishers for different data types"""
        base_port = self.config.get('zmq_base_port', 5555)
        use_zmq = self.config.get('use_zmq', True)
        
        if not use_zmq:
            logger.info("ZMQ disabled in configuration, using in-process queues instead")
            # Create in-process queues instead
            self.publishers = {
            data_type: asyncio.Queue() for data_type in ['ticks', 'bars', 'indicators', 'signals']
            }
            return
        try:
        
            for data_type in ['ticks', 'bars', 'indicators', 'signals']:
                if not ZMQ_AVAILABLE or not self.zmq_context:
                    self.publishers[data_type] = asyncio.Queue()
                    continue
                    
                socket = self.zmq_context.socket(zmq.PUB)
                try:
                    # Try to bind to specific port
                    socket.bind(f"tcp://127.0.0.1:{base_port}")
                    logger.info(f"ZMQ publisher for {data_type} bound to port {base_port}")
                except Exception as e:
                    logger.warning(f"Failed to bind ZMQ socket to port {base_port}: {e}")
                    try:
                    # Try with dynamic port assignment
                        socket.bind("tcp://127.0.0.1:*")
                        port = socket.get_monitor_socket().recv_json()['bound_addr'].split(':')[-1]
                        logger.info(f"ZMQ publisher for {data_type} bound to dynamic port {port}")
                    except Exception as e2:
                        logger.error(f"Failed to bind ZMQ socket with dynamic port: {e2}")
                        # Fallback to in-process queue
                        socket.close()
                        socket = asyncio.Queue()
                        logger.info(f"Falling back to in-process queue for {data_type}")
                
                self.publishers[data_type] = socket
                base_port += 1
        except Exception as e:
            logger.error(f"Error setting up ZMQ publishers: {e}")
            logger.info("Falling back to in-process queues for all data types")
            # Fallback to in-process queues
            self.publishers = {
                data_type: asyncio.Queue() for data_type in ['ticks', 'bars', 'indicators', 'signals']
            }
    
    async def create_stream(self, stream_id: str, buffer_size: int = 1000):
        """Create a new data stream"""
        if stream_id in self.streams:
            return
        
        self.streams[stream_id] = asyncio.Queue()
        self.buffers[stream_id] = deque(maxlen=buffer_size)
        self.processors[stream_id] = []
        self.metrics['buffer_sizes'][stream_id] = 0
        
        # Start processing task
        asyncio.create_task(self._process_stream(stream_id))
        
        logger.info(f"Created stream: {stream_id}")
    
    def add_processor(self, stream_id: str, processor: Callable):
        """Add a processor function to a stream"""
        if stream_id not in self.processors:
            raise ValueError(f"Stream {stream_id} does not exist")
        
        self.processors[stream_id].append(processor)
        logger.info(f"Added processor to stream {stream_id}")
    
    async def push_data(self, stream_id: str, data: Any):
        """Push data to a stream"""
        if stream_id not in self.streams:
            await self.create_stream(stream_id)
        
        start_time = datetime.now()
        
        # Add to buffer
        self.buffers[stream_id].append(data)
        
        # Push to stream for processing
        await self.streams[stream_id].put(data)
        
        # Update metrics
        self.metrics['messages_processed'] += 1
        processing_time = (datetime.now() - start_time).total_seconds()
        self.metrics['processing_times'].append(processing_time)
        self.metrics['buffer_sizes'][stream_id] = len(self.buffers[stream_id])
    
    async def _process_stream(self, stream_id: str):
        """Process data from a stream"""
        while True:
            data = await self.streams[stream_id].get()
            
            # Process in thread pool if CPU-intensive
            if self._is_cpu_intensive(data):
                await asyncio.get_event_loop().run_in_executor(
                    self.executor, 
                    self._process_data,
                    stream_id,
                    data
                )
            else:
                await self._process_data(stream_id, data)
            
            # Publish processed data
            await self._publish_data(stream_id, data)
            
            self.streams[stream_id].task_done()
    
    def _is_cpu_intensive(self, data: Any) -> bool:
        """Determine if processing will be CPU-intensive"""
        # Check data size and type
        if isinstance(data, pd.DataFrame) and len(data) > 1000:
            return True
        if isinstance(data, np.ndarray) and data.size > 10000:
            return True
        return False
    
    async def _process_data(self, stream_id: str, data: Any):
        """Process data through all registered processors"""
        processed_data = data
        
        for processor in self.processors[stream_id]:
            try:
                if asyncio.iscoroutinefunction(processor):
                    processed_data = await processor(processed_data)
                else:
                    processed_data = processor(processed_data)
            except Exception as e:
                logger.error(f"Error in processor for stream {stream_id}: {e}")
    
    async def _publish_data(self, stream_id: str, data: Any):
        """Publish processed data"""
        try:
            # Determine data type and use appropriate publisher
            data_type = self._get_data_type(stream_id)
            if data_type in self.publishers:
                publisher = self.publishers[data_type]
                
                # Check if publisher is ZMQ socket or asyncio Queue
                if isinstance(publisher, asyncio.Queue):
                    # Using in-process queue
                    await publisher.put({
                        'stream_id': stream_id,
                        'data': data
                    })
                else:
                    try:
                        # Using ZMQ socket
                        await publisher.send_string(
                            f"{stream_id}:{str(data)}"
                        )
                    except Exception as e:
                        logger.warning(f"ZMQ send failed: {e}, falling back to in-memory cache")
                        # Store in memory cache as fallback
                        if stream_id not in self.buffers:
                            self.buffers[stream_id] = deque(maxlen=1000)
                        self.buffers[stream_id].append(data)
            
            # Cache in Redis if configured
            if self.config.get('enable_redis_cache', True) and self.redis:
                try:
                    await self.redis.set(
                        f"{stream_id}:latest",
                        str(data),
                        ex=self.config.get('redis_ttl', 3600)
                    )
                except Exception as e:
                    logger.warning(f"Redis cache failed: {e}, using memory cache only")
                    # Store in memory cache as fallback
                    if stream_id not in self.buffers:
                        self.buffers[stream_id] = deque(maxlen=1000)
                    self.buffers[stream_id].append(data)
        except Exception as e:
            logger.error(f"Error publishing data: {e}")
    
    def _get_data_type(self, stream_id: str) -> str:
        """Determine data type from stream ID"""
        if 'tick' in stream_id:
            return 'ticks'
        elif 'bar' in stream_id:
            return 'bars'
        elif 'indicator' in stream_id:
            return 'indicators'
        else:
            return 'signals'
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get streaming metrics"""
        now = datetime.now()
        time_diff = (now - self.metrics['last_update']).total_seconds()
        
        metrics = {
            'messages_per_second': self.metrics['messages_processed'] / time_diff,
            'average_processing_time': np.mean(self.metrics['processing_times']),
            'buffer_sizes': self.metrics['buffer_sizes'].copy(),
            'active_streams': len(self.streams)
        }
        
        # Reset counters
        self.metrics['messages_processed'] = 0
        self.metrics['last_update'] = now
        
        return metrics
    
    async def cleanup(self):
        """Cleanup resources"""
        # Close Redis connection
        if self.redis:
            await self.redis.aclose()
        
        # Close ZMQ sockets or queues
        for publisher in self.publishers.values():
            if not isinstance(publisher, asyncio.Queue):
                try:
                    publisher.close()
                except Exception as e:
                    logger.warning(f"Error closing ZMQ socket: {e}")
            # No need to close asyncio.Queue objects
        
        # Shutdown thread pool
        self.executor.shutdown()
        
        logger.info("Market data streaming cleaned up")
