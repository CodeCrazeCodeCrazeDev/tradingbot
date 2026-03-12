"""
streaming package
"""

try:
    from .kafka_stream import (
        KafkaStreamManager,
        MarketDataMessage,
        MarketDataStream,
        MockFuture,
        MockKafkaConsumer,
        MockKafkaProducer,
        StreamConfig
    )
    from .kafka_streamer import KafkaStreamer, create_kafka_streamer
    from .redis_stream import (
        MockPubSub,
        MockRedis,
        RedisConfig,
        RedisStreamManager
    )
    from .redis_streamer import (
        MarketDataDistributor,
        MockRedisStreamer,
        RedisStreamer,
        create_redis_streamer
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in streaming: {e}')

__all__ = [
    'KafkaStreamManager',
    'KafkaStreamer',
    'MarketDataDistributor',
    'MarketDataMessage',
    'MarketDataStream',
    'MockFuture',
    'MockKafkaConsumer',
    'MockKafkaProducer',
    'MockPubSub',
    'MockRedis',
    'MockRedisStreamer',
    'RedisConfig',
    'RedisStreamManager',
    'RedisStreamer',
    'StreamConfig',
    'create_kafka_streamer',
    'create_redis_streamer',
]