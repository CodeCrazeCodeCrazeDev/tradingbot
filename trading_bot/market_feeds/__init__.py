"""Market data feed adapters — Level-2 order book plumbing.

Contracts + file replay (recorded real data) + broker-polling feed.
No synthetic book generation: a feed either reads recorded data or polls a
real broker; absence of data raises instead of fabricating liquidity.
"""

from .lob import LOBSnapshot, LOBFeed, LOBFileFeed, BrokerLOBFeed

__all__ = [
    "LOBSnapshot",
    "LOBFeed",
    "LOBFileFeed",
    "BrokerLOBFeed",
]
