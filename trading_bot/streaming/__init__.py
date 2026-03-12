"""
Streaming Module
============================================================

Auto-generated integration file.
"""

# Stub class for graceful degradation
class StreamingManager:
    def __init__(self, config=None):
        self.config = config or {}
    async def start(self):
        pass
    async def stop(self):
        pass

# kafka_stream
try:
    from .kafka_stream import (
        KafkaStreamManager,
    )
except ImportError as e:
    # kafka_stream not available
    pass

# redis_stream
try:
    from .redis_stream import (
        RedisStreamManager,
    )
except ImportError as e:
    # redis_stream not available
    pass

__all__ = [
    'KafkaStreamManager',
    'RedisStreamManager',
    'StreamingManager',
]
