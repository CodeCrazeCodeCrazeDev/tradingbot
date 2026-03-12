"""
Data Feeds Module
============================================================

Auto-generated integration file.
"""

# Stub class for graceful degradation
class DataFeedManager:
    def __init__(self, config=None):
        self.config = config or {}
    async def start(self):
        pass
    async def stop(self):
        pass

# websocket_feeds
try:
    from .websocket_feeds import (
        WebSocketFeedManager,
    )
except ImportError as e:
    # websocket_feeds not available
    pass

__all__ = [
    'DataFeedManager',
    'WebSocketFeedManager',
]
