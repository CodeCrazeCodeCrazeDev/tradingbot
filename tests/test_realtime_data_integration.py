"""
REAL-TIME DATA INTEGRATION TEST SUITE
=====================================

Tests for real-time market data handling, data feeds, and connectivity.
Includes mock data providers for testing without live connections.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Any, Dict, List
import sys
import os
import asyncio
import json
from dataclasses import field
import numpy
import pandas

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# MOCK REAL-TIME DATA PROVIDER
# ============================================================================

class MockRealtimeDataProvider:
    """Mock real-time data provider for testing"""
    
    def __init__(self):
        self.symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD']
        self.base_prices = {
            'EURUSD': 1.1000,
            'GBPUSD': 1.2500,
            'USDJPY': 150.00,
            'AUDUSD': 0.6500,
            'USDCAD': 1.3500
        }
        self.tick_count = 0
        self.is_connected = False
    
    def connect(self):
        """Simulate connection"""
        self.is_connected = True
        return True
    
    def disconnect(self):
        """Simulate disconnection"""
        self.is_connected = False
    
    def get_tick(self, symbol: str) -> Dict[str, Any]:
        """Generate mock tick data"""
        if not self.is_connected:
            raise ConnectionError("Not connected")
        
        if symbol not in self.base_prices:
            raise ValueError(f"Unknown symbol: {symbol}")
        
        self.tick_count += 1
        base = self.base_prices[symbol]
        
        # Add random noise
        noise = np.random.normal(0, 0.0001)
        bid = base + noise
        ask = bid + 0.0002  # 2 pip spread
        
        return {
            'symbol': symbol,
            'bid': bid,
            'ask': ask,
            'time': datetime.now(),
            'volume': np.random.randint(100, 1000),
            'tick_id': self.tick_count
        }
    
    def get_ohlcv(self, symbol: str, timeframe: str = 'M1', count: int = 100) -> List[Dict]:
        """Generate mock OHLCV data"""
        if not self.is_connected:
            raise ConnectionError("Not connected")
        
        base = self.base_prices.get(symbol, 1.0)
        data = []
        
        current_time = datetime.now()
        for i in range(count):
            time_offset = timedelta(minutes=i) if timeframe == 'M1' else timedelta(hours=i)
            bar_time = current_time - time_offset
            
            open_price = base + np.random.normal(0, 0.001)
            close_price = open_price + np.random.normal(0, 0.001)
            high_price = max(open_price, close_price) + abs(np.random.normal(0, 0.0005))
            low_price = min(open_price, close_price) - abs(np.random.normal(0, 0.0005))
            
            data.append({
                'time': bar_time,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': np.random.randint(100, 10000)
            })
        
        return list(reversed(data))
    
    def subscribe(self, symbol: str, callback):
        """Mock subscription"""
        return True
    
    def unsubscribe(self, symbol: str):
        """Mock unsubscription"""
        return True


# ============================================================================
# REAL-TIME DATA HANDLER TESTS
# ============================================================================

class TestRealtimeDataHandler:
    """Tests for real-time data handling"""
    
    @pytest.fixture
    def data_provider(self):
        """Create mock data provider"""
        provider = MockRealtimeDataProvider()
        provider.connect()
        return provider
    
    def test_connect(self):
        """Test connection"""
        provider = MockRealtimeDataProvider()
        assert provider.is_connected is False
        
        result = provider.connect()
        
        assert result is True
        assert provider.is_connected is True
    
    def test_disconnect(self, data_provider):
        """Test disconnection"""
        data_provider.disconnect()
        
        assert data_provider.is_connected is False
    
    def test_get_tick(self, data_provider):
        """Test tick data retrieval"""
        tick = data_provider.get_tick('EURUSD')
        
        assert tick['symbol'] == 'EURUSD'
        assert 'bid' in tick
        assert 'ask' in tick
        assert tick['ask'] > tick['bid']
        assert 'time' in tick
    
    def test_get_tick_not_connected(self):
        """Test tick retrieval when not connected"""
        provider = MockRealtimeDataProvider()
        
        with pytest.raises(ConnectionError):
            provider.get_tick('EURUSD')
    
    def test_get_tick_unknown_symbol(self, data_provider):
        """Test tick retrieval for unknown symbol"""
        with pytest.raises(ValueError):
            data_provider.get_tick('UNKNOWN')
    
    def test_get_ohlcv(self, data_provider):
        """Test OHLCV data retrieval"""
        ohlcv = data_provider.get_ohlcv('EURUSD', 'M1', 50)
        
        assert len(ohlcv) == 50
        assert all('open' in bar for bar in ohlcv)
        assert all('high' in bar for bar in ohlcv)
        assert all('low' in bar for bar in ohlcv)
        assert all('close' in bar for bar in ohlcv)
        assert all('volume' in bar for bar in ohlcv)
    
    def test_ohlcv_data_validity(self, data_provider):
        """Test OHLCV data validity"""
        ohlcv = data_provider.get_ohlcv('EURUSD', 'M1', 100)
        
        for bar in ohlcv:
            # High should be highest
            assert bar['high'] >= bar['open']
            assert bar['high'] >= bar['close']
            
            # Low should be lowest
            assert bar['low'] <= bar['open']
            assert bar['low'] <= bar['close']
            
            # Volume should be positive
            assert bar['volume'] > 0
    
    def test_multiple_symbols(self, data_provider):
        """Test data retrieval for multiple symbols"""
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        
        for symbol in symbols:
            tick = data_provider.get_tick(symbol)
            assert tick['symbol'] == symbol
    
    def test_tick_sequence(self, data_provider):
        """Test tick sequence"""
        ticks = [data_provider.get_tick('EURUSD') for _ in range(10)]
        
        # Tick IDs should be sequential
        tick_ids = [t['tick_id'] for t in ticks]
        assert tick_ids == sorted(tick_ids)


# ============================================================================
# DATA FEED PROCESSOR TESTS
# ============================================================================

class TestDataFeedProcessor:
    """Tests for data feed processing"""
    
    @pytest.fixture
    def processor(self):
        """Create data feed processor"""
        class DataFeedProcessor:
            def __init__(self):
                self.buffer = []
                self.max_buffer_size = 1000
                self.callbacks = []
            
            def process_tick(self, tick: Dict) -> Dict:
                """Process incoming tick"""
                processed = {
                    **tick,
                    'mid': (tick['bid'] + tick['ask']) / 2,
                    'spread': tick['ask'] - tick['bid'],
                    'processed_at': datetime.now()
                }
                
                self.buffer.append(processed)
                if len(self.buffer) > self.max_buffer_size:
                    self.buffer.pop(0)
                
                # Notify callbacks
                for callback in self.callbacks:
                    callback(processed)
                
                return processed
            
            def get_latest(self, symbol: str, count: int = 1) -> List[Dict]:
                """Get latest ticks for symbol"""
                symbol_ticks = [t for t in self.buffer if t['symbol'] == symbol]
                return symbol_ticks[-count:]
            
            def calculate_vwap(self, symbol: str, period: int = 100) -> float:
                """Calculate VWAP"""
                ticks = self.get_latest(symbol, period)
                if not ticks:
                    return 0.0
                
                total_value = sum(t['mid'] * t['volume'] for t in ticks)
                total_volume = sum(t['volume'] for t in ticks)
                
                return total_value / total_volume if total_volume > 0 else 0.0
            
            def add_callback(self, callback):
                """Add tick callback"""
                self.callbacks.append(callback)
            
            def clear_buffer(self):
                """Clear tick buffer"""
                self.buffer = []
        
        return DataFeedProcessor()
    
    def test_process_tick(self, processor):
        """Test tick processing"""
        tick = {
            'symbol': 'EURUSD',
            'bid': 1.1000,
            'ask': 1.1002,
            'time': datetime.now(),
            'volume': 100
        }
        
        processed = processor.process_tick(tick)
        
        assert processed['mid'] == 1.1001
        assert processed['spread'] == pytest.approx(0.0002, rel=0.01)
        assert 'processed_at' in processed
    
    def test_buffer_management(self, processor):
        """Test buffer management"""
        for i in range(1100):
            tick = {
                'symbol': 'EURUSD',
                'bid': 1.1000 + i * 0.0001,
                'ask': 1.1002 + i * 0.0001,
                'time': datetime.now(),
                'volume': 100
            }
            processor.process_tick(tick)
        
        # Buffer should not exceed max size
        assert len(processor.buffer) == 1000
    
    def test_get_latest(self, processor):
        """Test getting latest ticks"""
        for i in range(10):
            tick = {
                'symbol': 'EURUSD',
                'bid': 1.1000 + i * 0.0001,
                'ask': 1.1002 + i * 0.0001,
                'time': datetime.now(),
                'volume': 100
            }
            processor.process_tick(tick)
        
        latest = processor.get_latest('EURUSD', 5)
        
        assert len(latest) == 5
    
    def test_calculate_vwap(self, processor):
        """Test VWAP calculation"""
        for i in range(100):
            tick = {
                'symbol': 'EURUSD',
                'bid': 1.1000,
                'ask': 1.1002,
                'time': datetime.now(),
                'volume': 100
            }
            processor.process_tick(tick)
        
        vwap = processor.calculate_vwap('EURUSD', 100)
        
        assert vwap == pytest.approx(1.1001, rel=0.001)
    
    def test_callback_notification(self, processor):
        """Test callback notification"""
        received_ticks = []
        
        def callback(tick):
            received_ticks.append(tick)
        
        processor.add_callback(callback)
        
        tick = {
            'symbol': 'EURUSD',
            'bid': 1.1000,
            'ask': 1.1002,
            'time': datetime.now(),
            'volume': 100
        }
        processor.process_tick(tick)
        
        assert len(received_ticks) == 1


# ============================================================================
# DATA STALENESS DETECTOR TESTS
# ============================================================================

class TestDataStalenessDetector:
    """Tests for data staleness detection"""
    
    @pytest.fixture
    def detector(self):
        """Create staleness detector"""
        class StalenessDetector:
            def __init__(self, max_age_seconds: int = 60):
                self.max_age_seconds = max_age_seconds
                self.last_update_times = {}
            
            def update(self, symbol: str, timestamp: datetime = None):
                """Update last seen time for symbol"""
                self.last_update_times[symbol] = timestamp or datetime.now()
            
            def is_stale(self, symbol: str) -> bool:
                """Check if data is stale"""
                if symbol not in self.last_update_times:
                    return True
                
                age = (datetime.now() - self.last_update_times[symbol]).total_seconds()
                return age > self.max_age_seconds
            
            def get_age(self, symbol: str) -> float:
                """Get data age in seconds"""
                if symbol not in self.last_update_times:
                    return float('inf')
                
                return (datetime.now() - self.last_update_times[symbol]).total_seconds()
            
            def get_stale_symbols(self) -> List[str]:
                """Get list of stale symbols"""
                return [s for s in self.last_update_times if self.is_stale(s)]
        
        return StalenessDetector(max_age_seconds=60)
    
    def test_update(self, detector):
        """Test update"""
        detector.update('EURUSD')
        
        assert 'EURUSD' in detector.last_update_times
    
    def test_is_stale_fresh(self, detector):
        """Test fresh data is not stale"""
        detector.update('EURUSD')
        
        assert detector.is_stale('EURUSD') is False
    
    def test_is_stale_old(self, detector):
        """Test old data is stale"""
        detector.update('EURUSD', datetime.now() - timedelta(seconds=120))
        
        assert detector.is_stale('EURUSD') is True
    
    def test_is_stale_unknown(self, detector):
        """Test unknown symbol is stale"""
        assert detector.is_stale('UNKNOWN') is True
    
    def test_get_age(self, detector):
        """Test age calculation"""
        detector.update('EURUSD')
        
        age = detector.get_age('EURUSD')
        
        assert age < 1  # Should be very small
    
    def test_get_stale_symbols(self, detector):
        """Test getting stale symbols"""
        detector.update('EURUSD')
        detector.update('GBPUSD', datetime.now() - timedelta(seconds=120))
        detector.update('USDJPY', datetime.now() - timedelta(seconds=120))
        
        stale = detector.get_stale_symbols()
        
        assert 'EURUSD' not in stale
        assert 'GBPUSD' in stale
        assert 'USDJPY' in stale


# ============================================================================
# DATA QUALITY CHECKER TESTS
# ============================================================================

class TestDataQualityChecker:
    """Tests for data quality checking"""
    
    @pytest.fixture
    def checker(self):
        """Create data quality checker"""
        class DataQualityChecker:
            def __init__(self):
                self.checks = []
                self.quality_score = 100.0
            
            def check_tick(self, tick: Dict) -> Dict:
                """Check tick data quality"""
                issues = []
                
                # Check required fields
                required = ['symbol', 'bid', 'ask', 'time']
                for field in required:
                    if field not in tick:
                        issues.append(f"Missing field: {field}")
                
                if not issues:
                    # Check bid/ask relationship
                    if tick['ask'] <= tick['bid']:
                        issues.append("Ask <= Bid")
                    
                    # Check for negative prices
                    if tick['bid'] <= 0 or tick['ask'] <= 0:
                        issues.append("Negative or zero price")
                    
                    # Check spread
                    spread = tick['ask'] - tick['bid']
                    if spread > tick['bid'] * 0.01:  # More than 1%
                        issues.append(f"Excessive spread: {spread}")
                
                result = {
                    'valid': len(issues) == 0,
                    'issues': issues,
                    'timestamp': datetime.now()
                }
                
                self.checks.append(result)
                self._update_quality_score()
                
                return result
            
            def _update_quality_score(self):
                """Update quality score based on recent checks"""
                recent = self.checks[-100:]
                if recent:
                    valid_count = sum(1 for c in recent if c['valid'])
                    self.quality_score = (valid_count / len(recent)) * 100
            
            def get_quality_score(self) -> float:
                """Get current quality score"""
                return self.quality_score
            
            def get_recent_issues(self, count: int = 10) -> List[Dict]:
                """Get recent issues"""
                failed = [c for c in self.checks if not c['valid']]
                return failed[-count:]
        
        return DataQualityChecker()
    
    def test_check_valid_tick(self, checker):
        """Test checking valid tick"""
        tick = {
            'symbol': 'EURUSD',
            'bid': 1.1000,
            'ask': 1.1002,
            'time': datetime.now()
        }
        
        result = checker.check_tick(tick)
        
        assert result['valid'] is True
        assert len(result['issues']) == 0
    
    def test_check_missing_field(self, checker):
        """Test checking tick with missing field"""
        tick = {
            'symbol': 'EURUSD',
            'bid': 1.1000,
            # Missing 'ask' and 'time'
        }
        
        result = checker.check_tick(tick)
        
        assert result['valid'] is False
        assert any('Missing field' in issue for issue in result['issues'])
    
    def test_check_invalid_spread(self, checker):
        """Test checking tick with invalid spread"""
        tick = {
            'symbol': 'EURUSD',
            'bid': 1.1000,
            'ask': 1.0900,  # Ask < Bid
            'time': datetime.now()
        }
        
        result = checker.check_tick(tick)
        
        assert result['valid'] is False
    
    def test_quality_score(self, checker):
        """Test quality score calculation"""
        # Add some valid ticks
        for _ in range(90):
            tick = {
                'symbol': 'EURUSD',
                'bid': 1.1000,
                'ask': 1.1002,
                'time': datetime.now()
            }
            checker.check_tick(tick)
        
        # Add some invalid ticks
        for _ in range(10):
            tick = {
                'symbol': 'EURUSD',
                'bid': 1.1000,
                'ask': 1.0900,  # Invalid
                'time': datetime.now()
            }
            checker.check_tick(tick)
        
        score = checker.get_quality_score()
        
        assert score == 90.0


# ============================================================================
# CONNECTIVITY MONITOR TESTS
# ============================================================================

class TestConnectivityMonitor:
    """Tests for connectivity monitoring"""
    
    @pytest.fixture
    def monitor(self):
        """Create connectivity monitor"""
        class ConnectivityMonitor:
            def __init__(self):
                self.connections = {}
                self.reconnect_attempts = {}
                self.max_reconnect_attempts = 5
            
            def register_connection(self, name: str, check_func):
                """Register a connection to monitor"""
                self.connections[name] = {
                    'check_func': check_func,
                    'status': 'unknown',
                    'last_check': None
                }
                self.reconnect_attempts[name] = 0
            
            def check_connection(self, name: str) -> bool:
                """Check connection status"""
                if name not in self.connections:
                    return False
                
                conn = self.connections[name]
                try:
                    result = conn['check_func']()
                    conn['status'] = 'connected' if result else 'disconnected'
                    conn['last_check'] = datetime.now()
                    
                    if result:
                        self.reconnect_attempts[name] = 0
                    
                    return result
                except Exception:
                    conn['status'] = 'error'
                    conn['last_check'] = datetime.now()
                    return False
            
            def check_all(self) -> Dict[str, bool]:
                """Check all connections"""
                return {name: self.check_connection(name) for name in self.connections}
            
            def get_status(self) -> Dict[str, str]:
                """Get status of all connections"""
                return {name: conn['status'] for name, conn in self.connections.items()}
            
            def should_reconnect(self, name: str) -> bool:
                """Check if should attempt reconnection"""
                if name not in self.connections:
                    return False
                
                if self.connections[name]['status'] != 'disconnected':
                    return False
                
                return self.reconnect_attempts[name] < self.max_reconnect_attempts
            
            def record_reconnect_attempt(self, name: str):
                """Record reconnection attempt"""
                self.reconnect_attempts[name] = self.reconnect_attempts.get(name, 0) + 1
        
        return ConnectivityMonitor()
    
    def test_register_connection(self, monitor):
        """Test connection registration"""
        monitor.register_connection('test', lambda: True)
        
        assert 'test' in monitor.connections
    
    def test_check_connection_success(self, monitor):
        """Test successful connection check"""
        monitor.register_connection('test', lambda: True)
        
        result = monitor.check_connection('test')
        
        assert result is True
        assert monitor.connections['test']['status'] == 'connected'
    
    def test_check_connection_failure(self, monitor):
        """Test failed connection check"""
        monitor.register_connection('test', lambda: False)
        
        result = monitor.check_connection('test')
        
        assert result is False
        assert monitor.connections['test']['status'] == 'disconnected'
    
    def test_check_connection_error(self, monitor):
        """Test connection check with error"""
        def error_func():
            raise Exception("Connection error")
        
        monitor.register_connection('test', error_func)
        
        result = monitor.check_connection('test')
        
        assert result is False
        assert monitor.connections['test']['status'] == 'error'
    
    def test_check_all(self, monitor):
        """Test checking all connections"""
        monitor.register_connection('conn1', lambda: True)
        monitor.register_connection('conn2', lambda: False)
        
        results = monitor.check_all()
        
        assert results['conn1'] is True
        assert results['conn2'] is False
    
    def test_should_reconnect(self, monitor):
        """Test reconnection logic"""
        monitor.register_connection('test', lambda: False)
        monitor.check_connection('test')
        
        assert monitor.should_reconnect('test') is True
        
        # Exhaust reconnect attempts
        for _ in range(5):
            monitor.record_reconnect_attempt('test')
        
        assert monitor.should_reconnect('test') is False


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
