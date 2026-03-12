"""
Tests for data layer
"""

import pytest
import asyncio
import pandas as pd
from datetime import datetime

from ..data.pipeline import DataPipeline
from ..data.sources.mock import MockDataSource
from ..data.validation.quality import DataQualityValidator, QualityReport
from ..data.storage.cache import DataCache
import pandas

import logging
from typing import Dict, List, Optional, Any, Tuple

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator


logger = logging.getLogger(__name__)



class TestMockDataSource:
    """Tests for MockDataSource"""
    
    @pytest.fixture
    def mock_source(self):
        return MockDataSource({"name": "test_mock"})
    
    @pytest.mark.asyncio
    async def test_connect(self, mock_source):
        """Test connection"""
        result = await mock_source.connect()
        assert result is True
        assert mock_source.is_connected
    
    @pytest.mark.asyncio
    async def test_get_ohlcv(self, mock_source):
        """Test OHLCV data generation"""
        await mock_source.connect()
        
        df = await mock_source.get_ohlcv("EURUSD", "M15", bars=100)
        
        assert df is not None
        assert len(df) == 100
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns
    
    @pytest.mark.asyncio
    async def test_get_tick(self, mock_source):
        """Test tick generation"""
        await mock_source.connect()
        
        tick = await mock_source.get_tick("EURUSD")
        
        assert tick is not None
        assert tick.symbol == "EURUSD"
        assert tick.bid > 0
        assert tick.ask > tick.bid
    
    @pytest.mark.asyncio
    async def test_get_symbols(self, mock_source):
        """Test symbol list"""
        await mock_source.connect()
        
        symbols = await mock_source.get_symbols()
        
        assert len(symbols) > 0
        assert "EURUSD" in symbols


class TestDataQualityValidator:
    """Tests for DataQualityValidator"""
    
    @pytest.fixture
    def validator(self):
        return DataQualityValidator()
    
    def test_validate_valid_data(self, validator):
        """Test validation of valid data"""
        df = pd.DataFrame({
            'time': pd.date_range(start='2024-01-01', periods=100, freq='15min'),
            'open': [1.0850 + i * 0.0001 for i in range(100)],
            'high': [1.0860 + i * 0.0001 for i in range(100)],
            'low': [1.0840 + i * 0.0001 for i in range(100)],
            'close': [1.0855 + i * 0.0001 for i in range(100)],
            'volume': [1000 + i * 10 for i in range(100)],
        })
        
        report = validator.validate_ohlcv(df, "EURUSD")
        
        assert report.passed
        assert report.score > 0.7
        assert len(report.issues) == 0
    
    def test_validate_empty_data(self, validator):
        """Test validation of empty data"""
        df = pd.DataFrame()
        
        report = validator.validate_ohlcv(df, "EURUSD")
        
        assert not report.passed
        assert report.score == 0.0
    
    def test_validate_missing_columns(self, validator):
        """Test validation with missing columns"""
        df = pd.DataFrame({
            'open': [1.0850],
            'close': [1.0855],
        })
        
        report = validator.validate_ohlcv(df, "EURUSD")
        
        assert not report.passed
        assert any("Missing columns" in issue for issue in report.issues)
    
    def test_validate_ohlc_consistency(self, validator):
        """Test OHLC consistency check"""
        # Invalid: high < low
        df = pd.DataFrame({
            'time': [datetime.now()],
            'open': [1.0850],
            'high': [1.0840],  # Invalid: lower than low
            'low': [1.0860],
            'close': [1.0855],
            'volume': [1000],
        })
        
        report = validator.validate_ohlcv(df, "EURUSD")
        
        assert not report.passed
        assert any("High < Low" in issue for issue in report.issues)
    
    def test_validate_tick(self, validator):
        """Test tick validation"""
        assert validator.validate_tick(1.0850, 1.0852, 1.0851, "EURUSD")
        assert not validator.validate_tick(1.0852, 1.0850, 1.0851, "EURUSD")  # bid > ask
        assert not validator.validate_tick(-1.0, 1.0852, 1.0851, "EURUSD")  # negative


class TestDataCache:
    """Tests for DataCache"""
    
    @pytest.fixture
    def cache(self):
        return DataCache(max_size=100, default_ttl=60)
    
    def test_set_get(self, cache):
        """Test set and get"""
        cache.set("key1", "value1")
        
        assert cache.get("key1") == "value1"
    
    def test_get_missing(self, cache):
        """Test get missing key"""
        assert cache.get("nonexistent") is None
    
    def test_delete(self, cache):
        """Test delete"""
        cache.set("key1", "value1")
        assert cache.delete("key1")
        assert cache.get("key1") is None
    
    def test_clear(self, cache):
        """Test clear"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        assert len(cache) == 0
    
    def test_max_size(self, cache):
        """Test max size eviction"""
        small_cache = DataCache(max_size=3, default_ttl=60)
        
        small_cache.set("key1", "value1")
        small_cache.set("key2", "value2")
        small_cache.set("key3", "value3")
        small_cache.set("key4", "value4")  # Should evict key1
        
        assert len(small_cache) == 3
        assert small_cache.get("key1") is None  # Evicted
        assert small_cache.get("key4") == "value4"
    
    def test_stats(self, cache):
        """Test statistics"""
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        
        stats = cache.get_stats()
        
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


class TestDataPipeline:
    """Tests for DataPipeline"""
    
    @pytest.fixture
    def pipeline(self):
        return DataPipeline()
    
    @pytest.mark.asyncio
    async def test_initialize(self, pipeline):
        """Test pipeline initialization"""
        result = await pipeline.initialize()
        
        assert result is True
        assert "mock" in pipeline._sources
    
    @pytest.mark.asyncio
    async def test_get_market_data(self, pipeline):
        """Test getting market data"""
        await pipeline.initialize()
        
        data = await pipeline.get_market_data("EURUSD", "M15", bars=50)
        
        assert data is not None
        assert data.symbol == "EURUSD"
        assert data.timeframe == "M15"
        assert data.ohlcv is not None
        assert len(data.ohlcv) == 50
    
    @pytest.mark.asyncio
    async def test_get_tick(self, pipeline):
        """Test getting tick"""
        await pipeline.initialize()
        
        tick = await pipeline.get_tick("EURUSD")
        
        assert tick is not None
        assert tick.symbol == "EURUSD"
    
    @pytest.mark.asyncio
    async def test_caching(self, pipeline):
        """Test data caching"""
        await pipeline.initialize()
        
        # First call
        data1 = await pipeline.get_market_data("EURUSD", "M15", bars=50)
        
        # Second call should use cache
        data2 = await pipeline.get_market_data("EURUSD", "M15", bars=50)
        
        # Should be same data (from cache)
        assert data1.ohlcv.equals(data2.ohlcv)
    
    @pytest.mark.asyncio
    async def test_shutdown(self, pipeline):
        """Test pipeline shutdown"""
        await pipeline.initialize()
        await pipeline.shutdown()
        
        assert len(pipeline._sources) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
