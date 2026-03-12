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
        self.config = config or {}
        self.max_size = max_size
        self.buffers: Dict[str, deque] = {}
        self._running = False
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        logger.info("StreamBuffer initialized")
        return True
    
    async def start(self) -> bool:
        self._running = True
        return True
    
    async def stop(self) -> bool:
        self._running = False
        return True
    
    def push(self, channel: str, data: Any):
        if channel not in self.buffers:
            self.buffers[channel] = deque(maxlen=self.max_size)
        self.buffers[channel].append(data)
    
    def pop(self, channel: str) -> Optional[Any]:
        if channel in self.buffers and self.buffers[channel]:
            return self.buffers[channel].popleft()
        return None
    
    def get_all(self, channel: str) -> List[Any]:
        if channel in self.buffers:
            return list(self.buffers[channel])
        return []


_buffer: Optional[StreamBuffer] = None
def get_buffer() -> StreamBuffer:
    global _buffer
    if _buffer is None:
        _buffer = StreamBuffer()
    return _buffer

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_buffer().initialize(config)
async def start() -> bool:
    return await get_buffer().start()
async def stop() -> bool:
    return await get_buffer().stop()
