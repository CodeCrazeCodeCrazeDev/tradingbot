"""
Layer 1: Data Foundation
========================

The foundation layer handles all data acquisition, validation, preprocessing,
and fusion from multiple sources.

Components:
- DataSource: Abstract interface for data providers
- DataValidator: Validates data quality and freshness
- DataPreprocessor: Cleans and normalizes data
- DataFusion: Combines multiple data sources
- DataFoundation: Master coordinator for all data operations

Integrates:
- trading_bot/data/market_data_stream.py
- trading_bot/connectivity/staleness_detector.py
- trading_bot/database/data_quarantine.py
- trading_bot/intel/ (news, sentiment)
- trading_bot/alternative_data/ (satellite, credit card)
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum
from collections import deque
import pandas as pd
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class DataQuality(Enum):
    """Data quality levels"""
    EXCELLENT = "excellent"  # Fresh, validated, complete
    GOOD = "good"           # Minor issues, usable
    DEGRADED = "degraded"   # Some issues, use with caution
    POOR = "poor"           # Significant issues
    QUARANTINED = "quarantined"  # Do not use


class DataSourceType(Enum):
    """Types of data sources"""
    MARKET_DATA = "market_data"
    NEWS = "news"
    SENTIMENT = "sentiment"
    ALTERNATIVE = "alternative"
    FUNDAMENTAL = "fundamental"
    ON_CHAIN = "on_chain"


@dataclass
class DataPacket:
    """Standardized data packet"""
    source: str
    source_type: DataSourceType
    symbol: str
    timestamp: datetime
    data: Any
    quality: DataQuality
    latency_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    quality: DataQuality
    issues: List[str] = field(default_factory=list)
    corrections: Dict[str, Any] = field(default_factory=dict)


class DataSource(ABC):
    """Abstract base class for data sources"""
    
    def __init__(self, name: str, source_type: DataSourceType):
        self.name = name
        self.source_type = source_type
        self.is_connected = False
        self.last_update = None
        self.error_count = 0
        
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to data source"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from data source"""
        pass
    
    @abstractmethod
    async def fetch(self, symbol: str, **kwargs) -> Optional[DataPacket]:
        """Fetch data for a symbol"""
        pass
    
    @abstractmethod
    async def subscribe(self, symbol: str, callback: Callable):
        """Subscribe to real-time updates"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get source status"""
        return {
            'name': self.name,
            'type': self.source_type.value,
            'connected': self.is_connected,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'error_count': self.error_count
        }


class MarketDataSource(DataSource):
    """Market data source integrating existing components"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("market_data", DataSourceType.MARKET_DATA)
        self.config = config or {}
        self._stream = None
        self._callbacks: Dict[str, List[Callable]] = {}
        
    async def connect(self) -> bool:
        """Connect to market data stream"""
        try:
            # Import existing market data stream
            from trading_bot.data.market_data_stream import MarketDataStream
            
            self._stream = MarketDataStream(self.config)
            await self._stream.connect()
            self.is_connected = True
            logger.info("Market data source connected")
            return True
        except Exception as e:
            logger.error(f"Failed to connect market data source: {e}")
            self.error_count += 1
            return False
    
    async def disconnect(self):
        """Disconnect from market data stream"""
        if self._stream:
            await self._stream.disconnect()
        self.is_connected = False
        
    async def fetch(self, symbol: str, timeframe: str = '1H', 
                   bars: int = 100) -> Optional[DataPacket]:
        """Fetch OHLCV data"""
        if not self.is_connected:
            return None
        try:
            
            start_time = datetime.now()
            data = await self._stream.get_ohlcv(symbol, timeframe, bars)
            latency = (datetime.now() - start_time).total_seconds() * 1000
            
            self.last_update = datetime.now()
            
            return DataPacket(
                source=self.name,
                source_type=self.source_type,
                symbol=symbol,
                timestamp=datetime.now(),
                data=data,
                quality=DataQuality.EXCELLENT,
                latency_ms=latency,
                metadata={'timeframe': timeframe, 'bars': bars}
            )
        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            self.error_count += 1
            return None
    
    async def subscribe(self, symbol: str, callback: Callable):
        """Subscribe to real-time updates"""
        if symbol not in self._callbacks:
            self._callbacks[symbol] = []
        self._callbacks[symbol].append(callback)
        
        if self._stream:
            await self._stream.subscribe(symbol, self._on_tick)
    
    async def _on_tick(self, symbol: str, tick: Dict):
        """Handle incoming tick"""
        self.last_update = datetime.now()
        
        packet = DataPacket(
            source=self.name,
            source_type=self.source_type,
            symbol=symbol,
            timestamp=datetime.now(),
            data=tick,
            quality=DataQuality.EXCELLENT,
            latency_ms=0
        )
        
        for callback in self._callbacks.get(symbol, []):
            try:
                await callback(packet)
            except Exception as e:
                logger.error(f"Callback error: {e}")


class NewsDataSource(DataSource):
    """News and sentiment data source"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("news", DataSourceType.NEWS)
        self.config = config or {}
        self._collector = None
        
    async def connect(self) -> bool:
        """Connect to news sources"""
        try:
            from trading_bot.analysis.news_collector import NewsCollector
            self._collector = NewsCollector(self.config)
            self.is_connected = True
            logger.info("News data source connected")
            return True
        except Exception as e:
            logger.error(f"Failed to connect news source: {e}")
            self.error_count += 1
            return False
    
    async def disconnect(self):
        self.is_connected = False
        
    async def fetch(self, symbol: str, **kwargs) -> Optional[DataPacket]:
        """Fetch news for symbol"""
        if not self._collector:
            return None
        try:
            
            start_time = datetime.now()
            news = await self._collector.get_news(symbol, **kwargs)
            latency = (datetime.now() - start_time).total_seconds() * 1000
            
            self.last_update = datetime.now()
            
            return DataPacket(
                source=self.name,
                source_type=self.source_type,
                symbol=symbol,
                timestamp=datetime.now(),
                data=news,
                quality=DataQuality.GOOD,
                latency_ms=latency
            )
        except Exception as e:
            logger.error(f"Failed to fetch news: {e}")
            return None
    
    async def subscribe(self, symbol: str, callback: Callable):
        """Subscribe to news updates"""
        pass  # News typically polled, not streamed


class SentimentDataSource(DataSource):
    """Sentiment analysis data source"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("sentiment", DataSourceType.SENTIMENT)
        self.config = config or {}
        self._analyzer = None
        
    async def connect(self) -> bool:
        """Connect to sentiment analyzer"""
        try:
            from trading_bot.analysis.sentiment_analyzer import SentimentAnalyzer
            self._analyzer = SentimentAnalyzer(self.config)
            self.is_connected = True
            logger.info("Sentiment data source connected")
            return True
        except Exception as e:
            logger.error(f"Failed to connect sentiment source: {e}")
            self.error_count += 1
            return False
    
    async def disconnect(self):
        self.is_connected = False
        
    async def fetch(self, symbol: str, **kwargs) -> Optional[DataPacket]:
        """Fetch sentiment for symbol"""
        if not self._analyzer:
            return None
        try:
            
            start_time = datetime.now()
            sentiment = await self._analyzer.analyze(symbol, **kwargs)
            latency = (datetime.now() - start_time).total_seconds() * 1000
            
            self.last_update = datetime.now()
            
            return DataPacket(
                source=self.name,
                source_type=self.source_type,
                symbol=symbol,
                timestamp=datetime.now(),
                data=sentiment,
                quality=DataQuality.GOOD,
                latency_ms=latency
            )
        except Exception as e:
            logger.error(f"Failed to fetch sentiment: {e}")
            return None
    


class AlternativeDataSource(DataSource):
    """Alternative data source (satellite, credit card, etc.)"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("alternative", DataSourceType.ALTERNATIVE)
        self.config = config or {}
        self._providers = {}
        
    async def connect(self) -> bool:
        """Connect to alternative data providers"""
        try:
            # Import existing alternative data systems
            from trading_bot.alternative_data.satellite_imagery import SatelliteImageryAnalyzer
            
            self._providers['satellite'] = SatelliteImageryAnalyzer(self.config)
            self.is_connected = True
            logger.info("Alternative data source connected")
            return True
        except Exception as e:
            logger.error(f"Failed to connect alternative data: {e}")
            self.error_count += 1
            return False
    
    async def disconnect(self):
        self.is_connected = False
        
    async def fetch(self, symbol: str, data_type: str = 'all', 
                   **kwargs) -> Optional[DataPacket]:
        """Fetch alternative data"""
        if not self._providers:
            return None
        try:
            
            start_time = datetime.now()
            alt_data = {}
            
            for name, provider in self._providers.items():
                if data_type == 'all' or data_type == name:
                    try:
                        alt_data[name] = await provider.analyze(symbol, **kwargs)
                    except Exception:
                        pass
            
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self.last_update = datetime.now()
            
            return DataPacket(
                source=self.name,
                source_type=self.source_type,
                symbol=symbol,
                timestamp=datetime.now(),
                data=alt_data,
                quality=DataQuality.GOOD,
                latency_ms=latency
            )
        except Exception as e:
            logger.error(f"Failed to fetch alternative data: {e}")
    
    async def subscribe(self, symbol: str, callback: Callable):
        pass


class DataValidator:
    """
    Validates data quality and freshness
    
    Integrates:
    - trading_bot/connectivity/staleness_detector.py
    - trading_bot/database/data_quarantine.py
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Staleness thresholds (seconds)
        self.staleness_thresholds = {
            DataSourceType.MARKET_DATA: 5,
            DataSourceType.NEWS: 300,
            DataSourceType.SENTIMENT: 60,
            DataSourceType.ALTERNATIVE: 3600,
            DataSourceType.FUNDAMENTAL: 86400,
            DataSourceType.ON_CHAIN: 60
        }
        
        # Quarantine tracking
        self.quarantine_count = 0
        self.quarantine_history: deque = deque(maxlen=1000)
        
        try:
            # Import existing validators
            from trading_bot.connectivity.staleness_detector import StalenessDetector
            self._staleness_detector = StalenessDetector()
        except Exception:
            self._staleness_detector = None

        try:
            from trading_bot.database.data_quarantine import DataQuarantine
            self._quarantine = DataQuarantine()
        except Exception:
            self._quarantine = None
    
    def validate(self, packet: DataPacket) -> ValidationResult:
        """Validate a data packet"""
        issues = []
        corrections = {}
        
        # Check staleness
        age = (datetime.now() - packet.timestamp).total_seconds()
        threshold = self.staleness_thresholds.get(packet.source_type, 60)
        
        if age > threshold * 2:
            issues.append(f"Data severely stale: {age:.1f}s old (threshold: {threshold}s)")
            return ValidationResult(
                is_valid=False,
                quality=DataQuality.QUARANTINED,
                issues=issues
            )
        elif age > threshold:
            issues.append(f"Data stale: {age:.1f}s old (threshold: {threshold}s)")
        
        # Check for null/empty data
        if packet.data is None:
            issues.append("Data is null")
            return ValidationResult(
                is_valid=False,
                quality=DataQuality.QUARANTINED,
                issues=issues
            )
        
        # Type-specific validation
        if packet.source_type == DataSourceType.MARKET_DATA:
            result = self._validate_market_data(packet, issues, corrections)
            if result:
                return result
        
        # Determine quality
        if len(issues) == 0:
            quality = DataQuality.EXCELLENT
        elif len(issues) <= 2:
            quality = DataQuality.GOOD
        elif len(issues) <= 5:
            quality = DataQuality.DEGRADED
        else:
            quality = DataQuality.POOR
        
        return ValidationResult(
            is_valid=quality != DataQuality.QUARANTINED,
            quality=quality,
            issues=issues,
            corrections=corrections
        )
    
    def _validate_market_data(self, packet: DataPacket, 
                              issues: List[str],
                              corrections: Dict) -> Optional[ValidationResult]:
        """Validate market data specifically"""
        data = packet.data
        
        if isinstance(data, pd.DataFrame):
            # Check for required columns
            required = ['open', 'high', 'low', 'close', 'volume']
            missing = [col for col in required if col not in data.columns]
            if missing:
                issues.append(f"Missing columns: {missing}")
            
            # Check for NaN values
            nan_count = data.isnull().sum().sum()
            if nan_count > 0:
                issues.append(f"Contains {nan_count} NaN values")
                # Attempt correction
                corrections['filled_nan'] = True
            
            # Check for outliers (price > 3 std from mean)
            if 'close' in data.columns:
                mean = data['close'].mean()
                std = data['close'].std()
                outliers = ((data['close'] - mean).abs() > 3 * std).sum()
                if outliers > 0:
                    issues.append(f"Contains {outliers} price outliers")
            
            # Check OHLC consistency
            if all(col in data.columns for col in ['open', 'high', 'low', 'close']):
                invalid_ohlc = (
                    (data['high'] < data['low']) |
                    (data['high'] < data['open']) |
                    (data['high'] < data['close']) |
                    (data['low'] > data['open']) |
                    (data['low'] > data['close'])
                ).sum()
                if invalid_ohlc > 0:
                    issues.append(f"Contains {invalid_ohlc} invalid OHLC bars")
        
        return None
    
    def quarantine(self, packet: DataPacket, reason: str):
        """Quarantine bad data"""
        self.quarantine_count += 1
        self.quarantine_history.append({
            'timestamp': datetime.now(),
            'source': packet.source,
            'symbol': packet.symbol,
            'reason': reason
        })
        
        if self._quarantine:
            self._quarantine.add(packet.data, reason)
        
        logger.warning(f"Data quarantined: {packet.source}/{packet.symbol} - {reason}")


class DataPreprocessor:
    """
    Preprocesses and normalizes data
    
    Operations:
    - Missing value handling
    - Outlier detection/removal
    - Normalization
    - Feature engineering
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def preprocess(self, packet: DataPacket) -> DataPacket:
        """Preprocess a data packet"""
        if packet.source_type == DataSourceType.MARKET_DATA:
            return self._preprocess_market_data(packet)
        elif packet.source_type == DataSourceType.SENTIMENT:
            return self._preprocess_sentiment(packet)
        return packet
    
    def _preprocess_market_data(self, packet: DataPacket) -> DataPacket:
        """Preprocess market data"""
        data = packet.data
        
        if not isinstance(data, pd.DataFrame):
            return packet
        
        # Handle missing values
        data = data.ffill().bfill()
        
        # Add technical features
        if 'close' in data.columns:
            # Returns
            data['returns'] = data['close'].pct_change()
            
            # Moving averages
            data['sma_20'] = data['close'].rolling(20).mean()
            data['sma_50'] = data['close'].rolling(50).mean()
            
            # Volatility
            data['volatility'] = data['returns'].rolling(20).std() * np.sqrt(252)
            
            # RSI
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            data['rsi'] = 100 - (100 / (1 + rs))
        
        # Update packet
        packet.data = data
        packet.metadata['preprocessed'] = True
        packet.metadata['features_added'] = ['returns', 'sma_20', 'sma_50', 'volatility', 'rsi']
        
        return packet
    
    def _preprocess_sentiment(self, packet: DataPacket) -> DataPacket:
        """Preprocess sentiment data"""
        data = packet.data
        
        if isinstance(data, dict):
            # Normalize sentiment scores to [-1, 1]
            if 'score' in data:
                data['normalized_score'] = max(-1, min(1, data['score']))
            
            # Add confidence weighting
            if 'confidence' in data and 'score' in data:
                data['weighted_score'] = data['score'] * data['confidence']
        
        packet.data = data
        packet.metadata['preprocessed'] = True
        
        return packet


class DataFusion:
    """
    Fuses data from multiple sources into unified view
    
    Implements multi-modal data fusion for comprehensive market analysis
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Source weights for fusion
        self.source_weights = {
            DataSourceType.MARKET_DATA: 0.4,
            DataSourceType.SENTIMENT: 0.2,
            DataSourceType.NEWS: 0.15,
            DataSourceType.ALTERNATIVE: 0.15,
            DataSourceType.FUNDAMENTAL: 0.1
        }
    
    def fuse(self, packets: List[DataPacket]) -> Dict[str, Any]:
        """Fuse multiple data packets into unified view"""
        if not packets:
            return {}
        
        # Group by source type
        by_type: Dict[DataSourceType, List[DataPacket]] = {}
        for packet in packets:
            if packet.source_type not in by_type:
                by_type[packet.source_type] = []
            by_type[packet.source_type].append(packet)
        
        # Build unified view
        unified = {
            'timestamp': datetime.now(),
            'symbol': packets[0].symbol if packets else None,
            'sources': list(by_type.keys()),
            'data': {},
            'quality': self._calculate_overall_quality(packets),
            'signals': {}
        }
        
        # Extract market data
        if DataSourceType.MARKET_DATA in by_type:
            market_packets = by_type[DataSourceType.MARKET_DATA]
            unified['data']['market'] = market_packets[0].data if market_packets else None
        
        # Extract sentiment
        if DataSourceType.SENTIMENT in by_type:
            sentiment_packets = by_type[DataSourceType.SENTIMENT]
            unified['data']['sentiment'] = self._aggregate_sentiment(sentiment_packets)
        
        # Extract news
        if DataSourceType.NEWS in by_type:
            news_packets = by_type[DataSourceType.NEWS]
            unified['data']['news'] = self._aggregate_news(news_packets)
        
        # Generate fused signals
        unified['signals'] = self._generate_fused_signals(unified['data'])
        
        return unified
    
    def _calculate_overall_quality(self, packets: List[DataPacket]) -> DataQuality:
        """Calculate overall data quality"""
        if not packets:
            return DataQuality.POOR
        
        quality_scores = {
            DataQuality.EXCELLENT: 4,
            DataQuality.GOOD: 3,
            DataQuality.DEGRADED: 2,
            DataQuality.POOR: 1,
            DataQuality.QUARANTINED: 0
        }
        
        total_weight = 0
        weighted_score = 0
        
        for packet in packets:
            weight = self.source_weights.get(packet.source_type, 0.1)
            score = quality_scores.get(packet.quality, 1)
            weighted_score += weight * score
            total_weight += weight
        
        avg_score = weighted_score / total_weight if total_weight > 0 else 0
        
        if avg_score >= 3.5:
            return DataQuality.EXCELLENT
        elif avg_score >= 2.5:
            return DataQuality.GOOD
        elif avg_score >= 1.5:
            return DataQuality.DEGRADED
        else:
            return DataQuality.POOR
    
    def _aggregate_sentiment(self, packets: List[DataPacket]) -> Dict[str, Any]:
        """Aggregate sentiment from multiple sources"""
        if not packets:
            return {}
        
        scores = []
        for packet in packets:
            if isinstance(packet.data, dict) and 'score' in packet.data:
                scores.append(packet.data['score'])
        
        if not scores:
            return {}
        
        return {
            'average': np.mean(scores),
            'std': np.std(scores),
            'min': np.min(scores),
            'max': np.max(scores),
            'sources': len(scores)
        }
    
    def _aggregate_news(self, packets: List[DataPacket]) -> Dict[str, Any]:
        """Aggregate news from multiple sources"""
        if not packets:
            return {}
        
        all_news = []
        for packet in packets:
            if isinstance(packet.data, list):
                all_news.extend(packet.data)
            elif isinstance(packet.data, dict) and 'articles' in packet.data:
                all_news.extend(packet.data['articles'])
        
        return {
            'count': len(all_news),
            'articles': all_news[:10]  # Top 10 most recent
        }
    
    def _generate_fused_signals(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Generate trading signals from fused data"""
        signals = {}
        
        # Market signal from technical analysis
        if 'market' in data and isinstance(data['market'], pd.DataFrame):
            df = data['market']
            if 'rsi' in df.columns:
                rsi = df['rsi'].iloc[-1]
                if rsi < 30:
                    signals['technical'] = 1.0  # Oversold
                elif rsi > 70:
                    signals['technical'] = -1.0  # Overbought
                else:
                    signals['technical'] = (50 - rsi) / 50  # Normalized
        
        # Sentiment signal
        if 'sentiment' in data and 'average' in data['sentiment']:
            signals['sentiment'] = data['sentiment']['average']
        
        # Combined signal
        if signals:
            weights = {'technical': 0.6, 'sentiment': 0.4}
            combined = sum(
                signals.get(k, 0) * weights.get(k, 0.5) 
                for k in signals
            ) / sum(weights.get(k, 0.5) for k in signals)
            signals['combined'] = combined
        
        return signals


class DataFoundation:
    """
    Master coordinator for Layer 1: Data Foundation
    
    Manages all data sources, validation, preprocessing, and fusion
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.sources: Dict[str, DataSource] = {}
        self.validator = DataValidator(config)
        self.preprocessor = DataPreprocessor(config)
        self.fusion = DataFusion(config)
        
        # Data cache
        self.cache: Dict[str, DataPacket] = {}
        self.cache_ttl = config.get('cache_ttl', 60)  # seconds
        
        # Statistics
        self.stats = {
            'packets_received': 0,
            'packets_validated': 0,
            'packets_quarantined': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Initialize default sources
        self._init_default_sources()
        
        logger.info("Data Foundation initialized")
    
    def _init_default_sources(self):
        """Initialize default data sources"""
        # Market data
        self.sources['market'] = MarketDataSource(self.config.get('market', {}))
        
        # News
        self.sources['news'] = NewsDataSource(self.config.get('news', {}))
        
        # Sentiment
        self.sources['sentiment'] = SentimentDataSource(self.config.get('sentiment', {}))
        
        # Alternative data
        self.sources['alternative'] = AlternativeDataSource(self.config.get('alternative', {}))
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect all data sources"""
        results = {}
        for name, source in self.sources.items():
            try:
                results[name] = await source.connect()
            except Exception as e:
                logger.error(f"Failed to connect {name}: {e}")
                results[name] = False
        return results
    
    async def disconnect_all(self):
        """Disconnect all data sources"""
        for source in self.sources.values():
            try:
                await source.disconnect()
            except Exception as e:
                logger.error(f"Disconnect error: {e}")
    
    async def fetch_all(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Fetch data from all sources and return fused view"""
        packets = []
        
        # Fetch from each source
        for name, source in self.sources.items():
            if not source.is_connected:
                continue
            try:
                
                packet = await source.fetch(symbol, **kwargs)
                if packet:
                    # Validate
                    validation = self.validator.validate(packet)
                    self.stats['packets_validated'] += 1
                    
                    if validation.is_valid:
                        # Preprocess
                        packet = self.preprocessor.preprocess(packet)
                        packet.quality = validation.quality
                        packets.append(packet)
                        self.stats['packets_received'] += 1
                    else:
                        self.validator.quarantine(packet, '; '.join(validation.issues))
                        self.stats['packets_quarantined'] += 1
            except Exception as e:
                logger.error(f"Error fetching from {name}: {e}")
        
        # Fuse all data
        return self.fusion.fuse(packets)
    
    async def fetch_market_data(self, symbol: str, timeframe: str = '1H',
                                bars: int = 100) -> Optional[pd.DataFrame]:
        """Fetch market data specifically"""
        source = self.sources.get('market')
        if not source or not source.is_connected:
            return None
        
        packet = await source.fetch(symbol, timeframe=timeframe, bars=bars)
        if packet:
            validation = self.validator.validate(packet)
            if validation.is_valid:
                packet = self.preprocessor.preprocess(packet)
                return packet.data
        return None
    
    async def subscribe(self, symbol: str, callback: Callable):
        """Subscribe to real-time updates for a symbol"""
        for source in self.sources.values():
            if source.is_connected:
                await source.subscribe(symbol, callback)
    
    def get_status(self) -> Dict[str, Any]:
        """Get foundation status"""
        return {
            'sources': {name: source.get_status() for name, source in self.sources.items()},
            'validator': {
                'quarantine_count': self.validator.quarantine_count
            },
            'stats': self.stats
        }
    
    def add_source(self, name: str, source: DataSource):
        """Add a custom data source"""
        self.sources[name] = source
        logger.info(f"Added data source: {name}")
    
    def remove_source(self, name: str):
        """Remove a data source"""
        if name in self.sources:
            del self.sources[name]
            logger.info(f"Removed data source: {name}")
