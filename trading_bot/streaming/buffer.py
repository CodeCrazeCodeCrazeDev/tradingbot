"""
Stream Buffer - Buffers streaming data
"""

import logging
from typing import Dict, Any, Optional, List
from collections import deque

logger = logging.getLogger(__name__)


class StreamBuffer:
    """Buffers streaming data"""
    
    def __init__(self, config: Dict[str, Any] = None, max_size: int = 10000):
        try:
            self.config = config or {}
            self.max_size = max_size
            self.buffers: Dict[str, deque] = {}
            self._running = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        try:
            logger.info("StreamBuffer initialized")
            return True
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    async def start(self) -> bool:
        try:
            self._running = True
            return True
        except Exception as e:
            logger.error(f"Error in start: {e}")
            raise
    
    async def stop(self) -> bool:
        try:
            self._running = False
            return True
        except Exception as e:
            logger.error(f"Error in stop: {e}")
            raise
    
    def push(self, channel: str, data: Any):
        try:
            if channel not in self.buffers:
                self.buffers[channel] = deque(maxlen=self.max_size)
            self.buffers[channel].append(data)
        except Exception as e:
            logger.error(f"Error in push: {e}")
            raise
    
    def pop(self, channel: str) -> Optional[Any]:
        try:
            if channel in self.buffers and self.buffers[channel]:
                return self.buffers[channel].popleft()
            return None
        except Exception as e:
            logger.error(f"Error in pop: {e}")
            raise
    
    def get_all(self, channel: str) -> List[Any]:
        try:
            if channel in self.buffers:
                return list(self.buffers[channel])
            return []
        except Exception as e:
            logger.error(f"Error in get_all: {e}")
            raise


_buffer: Optional[StreamBuffer] = None
def get_buffer() -> StreamBuffer:
    try:
        global _buffer
        if _buffer is None:
            _buffer = StreamBuffer()
        return _buffer
    except Exception as e:
        logger.error(f"Error in get_buffer: {e}")
        raise

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_buffer().initialize(config)
async def start() -> bool:
    return await get_buffer().start()
async def stop() -> bool:
    return await get_buffer().stop()
