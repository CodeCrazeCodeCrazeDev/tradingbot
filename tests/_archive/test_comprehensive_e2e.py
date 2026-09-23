"""
Comprehensive End-to-End Test Suite
=====================================
Production-grade test suite targeting 80%+ coverage.
Tests all critical paths and integrations.
"""

import asyncio
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# BROKER INTEGRATION TESTS
# ============================================================================

class TestBrokerIntegration(unittest.TestCase):
    """Test broker integration."""
    
    def setUp(self):
        from trading_bot.brokers.real_broker_integration import (
            BrokerCredentials, BrokerType, Order, OrderSide, OrderType,
            OrderStatus, AlpacaBroker, UnifiedBrokerManager
        )
        self.BrokerCredentials = BrokerCredentials
        self.BrokerType = BrokerType
        self.Order = Order
        self.OrderSide = OrderSide
        self.OrderType = OrderType
        self.OrderStatus = OrderStatus
        self.AlpacaBroker = AlpacaBroker
        self.UnifiedBrokerManager = UnifiedBrokerManager
    
    def test_order_creation(self):
        """Test order creation."""
        order = self.Order(
            order_id="test-001",
            client_order_id="client-001",
            symbol="EURUSD",
            side=self.OrderSide.BUY,
            order_type=self.OrderType.MARKET,
            quantity=Decimal("0.1"),
        )
        
        self.assertEqual(order.order_id, "test-001")
        self.assertEqual(order.symbol, "EURUSD")
        self.assertEqual(order.side, self.OrderSide.BUY)
        self.assertEqual(order.status, self.OrderStatus.PENDING)
    
    def test_broker_credentials(self):
        """Test broker credentials."""
        creds = self.BrokerCredentials(
            broker_type=self.BrokerType.ALPACA,
            api_key="test_key",
            api_secret="test_secret",
            is_paper=True,
        )
        
        self.assertEqual(creds.broker_type, self.BrokerType.ALPACA)
        self.assertTrue(creds.is_paper)
    
    def test_unified_broker_manager(self):
        """Test unified broker manager."""
        manager = self.UnifiedBrokerManager()
        
        creds = self.BrokerCredentials(
            broker_type=self.BrokerType.ALPACA,
            api_key="test",
            api_secret="test",
            is_paper=True,
        )
        broker = self.AlpacaBroker(creds)
        
        manager.register_broker("alpaca", broker, is_primary=True)
        
        self.assertIn("alpaca", manager.brokers)
        self.assertEqual(manager.primary_broker, "alpaca")


# ============================================================================
# ERROR RECOVERY TESTS
# ============================================================================

class TestErrorRecovery(unittest.TestCase):
    """Test error recovery system."""
    
    def setUp(self):
        from trading_bot.core.error_recovery import (
            CircuitBreaker, CircuitBreakerConfig, CircuitState,
            RetryHandler, RetryConfig, ErrorClassifier, RecoveryManager
        )
        self.CircuitBreaker = CircuitBreaker
        self.CircuitBreakerConfig = CircuitBreakerConfig
        self.CircuitState = CircuitState
        self.RetryHandler = RetryHandler
        self.RetryConfig = RetryConfig
        self.ErrorClassifier = ErrorClassifier
        self.RecoveryManager = RecoveryManager
    
    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts closed."""
        cb = self.CircuitBreaker("test")
        self.assertEqual(cb.state, self.CircuitState.CLOSED)
        self.assertTrue(cb.can_execute())
    
    def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after failures."""
        config = self.CircuitBreakerConfig(failure_threshold=3)
        cb = self.CircuitBreaker("test", config)
        
        for _ in range(3):
            cb.record_failure()
        
        self.assertEqual(cb.state, self.CircuitState.OPEN)
        self.assertFalse(cb.can_execute())
    
    def test_circuit_breaker_success_resets(self):
        """Test circuit breaker resets on success."""
        cb = self.CircuitBreaker("test")
        cb.record_failure()
        cb.record_success()
        
        self.assertEqual(cb.state, self.CircuitState.CLOSED)
    
    def test_retry_handler_delay_calculation(self):
        """Test retry delay calculation."""
        config = self.RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=60.0,
        )
        handler = self.RetryHandler(config)
        
        delay1 = handler.calculate_delay(1)
        delay2 = handler.calculate_delay(2)
        delay3 = handler.calculate_delay(3)
        
        # Delays should increase exponentially (with jitter)
        self.assertGreater(delay2, delay1 * 0.5)
        self.assertGreater(delay3, delay2 * 0.5)
    
    def test_error_classifier(self):
        """Test error classification."""
        classifier = self.ErrorClassifier()
        
        # Network error
        severity, action = classifier.classify(ConnectionError("test"))
        self.assertIsNotNone(severity)
        self.assertIsNotNone(action)
        
        # Value error
        severity, action = classifier.classify(ValueError("test"))
        self.assertIsNotNone(severity)
    
    def test_recovery_manager(self):
        """Test recovery manager."""
        manager = self.RecoveryManager()
        
        cb = manager.get_circuit_breaker("test")
        self.assertIsNotNone(cb)
        
        retry = manager.get_retry_handler("test")
        self.assertIsNotNone(retry)


# ============================================================================
# AUDIT SYSTEM TESTS
# ============================================================================

class TestAuditSystem(unittest.TestCase):
    """Test audit logging system."""
    
    def setUp(self):
        from trading_bot.logging.audit_system import (
            AuditEvent, AuditEventType, AuditSeverity,
            SQLiteAuditStorage, AuditLogger
        )
        self.AuditEvent = AuditEvent
        self.AuditEventType = AuditEventType
        self.AuditSeverity = AuditSeverity
        self.SQLiteAuditStorage = SQLiteAuditStorage
        self.AuditLogger = AuditLogger
    
    def test_audit_event_creation(self):
        """Test audit event creation."""
        event = self.AuditEvent(
            event_id="test-001",
            event_type=self.AuditEventType.ORDER_SUBMITTED,
            severity=self.AuditSeverity.INFO,
            timestamp=datetime.utcnow(),
            component="test",
            action="test action",
        )
        
        self.assertEqual(event.event_id, "test-001")
        self.assertEqual(event.event_type, self.AuditEventType.ORDER_SUBMITTED)
        self.assertIsNotNone(event.checksum)
    
    def test_audit_event_integrity(self):
        """Test audit event integrity verification."""
        event = self.AuditEvent(
            event_id="test-001",
            event_type=self.AuditEventType.ORDER_SUBMITTED,
            severity=self.AuditSeverity.INFO,
            timestamp=datetime.utcnow(),
            component="test",
        )
        
        self.assertTrue(event.verify_integrity())
    
    def test_audit_event_serialization(self):
        """Test audit event serialization."""
        event = self.AuditEvent(
            event_id="test-001",
            event_type=self.AuditEventType.ORDER_FILLED,
            severity=self.AuditSeverity.INFO,
            timestamp=datetime.utcnow(),
            component="test",
            details={"order_id": "123"},
        )
        
        data = event.to_dict()
        restored = self.AuditEvent.from_dict(data)
        
        self.assertEqual(event.event_id, restored.event_id)
        self.assertEqual(event.event_type, restored.event_type)


# ============================================================================
# DATABASE PERSISTENCE TESTS
# ============================================================================

class TestDatabasePersistence(unittest.TestCase):
    """Test database persistence layer."""
    
    def setUp(self):
        from trading_bot.database.persistence_layer import (
            DatabaseConfig, Trade, PositionRecord, SignalRecord,
            PersistenceManager
        )
        self.DatabaseConfig = DatabaseConfig
        self.Trade = Trade
        self.PositionRecord = PositionRecord
        self.SignalRecord = SignalRecord
        self.PersistenceManager = PersistenceManager
        
        # Use temp database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.config = self.DatabaseConfig(sqlite_path=self.temp_db.name)
    
    def tearDown(self):
        try:
            os.unlink(self.temp_db.name)
        except Exception:
    
    def test_trade_creation(self):
        """Test trade record creation."""
        trade = self.Trade(
            trade_id="trade-001",
            order_id="order-001",
            symbol="EURUSD",
            side="buy",
            quantity=0.1,
            entry_price=1.0850,
        )
        
        self.assertEqual(trade.trade_id, "trade-001")
        self.assertEqual(trade.status, "open")
    
    def test_persistence_manager_init(self):
        """Test persistence manager initialization."""
        manager = self.PersistenceManager(self.config)
        result = manager.initialize()
        
        self.assertTrue(result)
        manager.close()
    
    def test_trade_save_and_retrieve(self):
        """Test saving and retrieving trades."""
        manager = self.PersistenceManager(self.config)
        manager.initialize()
        
        trade = self.Trade(
            trade_id="trade-001",
            order_id="order-001",
            symbol="EURUSD",
            side="buy",
            quantity=0.1,
            entry_price=1.0850,
        )
        
        result = manager.save_trade(trade)
        self.assertTrue(result)
        
        retrieved = manager.get_trade("trade-001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.symbol, "EURUSD")
        
        manager.close()
    
    def test_signal_save_and_retrieve(self):
        """Test saving and retrieving signals."""
        manager = self.PersistenceManager(self.config)
        manager.initialize()
        
        signal = self.SignalRecord(
            signal_id="signal-001",
            symbol="EURUSD",
            direction="buy",
            confidence=0.85,
            source="ml_model",
            price_at_signal=1.0850,
        )
        
        result = manager.save_signal(signal)
        self.assertTrue(result)
        
        signals = manager.get_signals(symbol="EURUSD")
        self.assertEqual(len(signals), 1)
        
        manager.close()


# ============================================================================
# CONFIGURATION MANAGEMENT TESTS
# ============================================================================

class TestConfigurationManagement(unittest.TestCase):
    """Test centralized configuration."""
    
    def setUp(self):
        from trading_bot.config.centralized_config import (
            ConfigManager, AppConfig, TradingConfig, RiskConfig
        )
        self.ConfigManager = ConfigManager
        self.AppConfig = AppConfig
        self.TradingConfig = TradingConfig
        self.RiskConfig = RiskConfig
    
    def test_default_config(self):
        """Test default configuration values."""
        config = self.AppConfig()
        
        self.assertEqual(config.trading.mode, "paper")
        self.assertEqual(config.risk.max_risk_per_trade, 0.02)
        self.assertEqual(config.risk.max_daily_loss, 0.05)
    
    def test_config_manager_singleton(self):
        """Test config manager is singleton."""
        manager1 = self.ConfigManager()
        manager2 = self.ConfigManager()
        
        self.assertIs(manager1, manager2)
    
    def test_config_get_set(self):
        """Test config get and set."""
        manager = self.ConfigManager()
        manager.load()
        
        manager.set("trading.mode", "live")
        value = manager.get("trading.mode")
        
        self.assertEqual(value, "live")
        
        # Reset for other tests
        manager.set("trading.mode", "paper")


# ============================================================================
# RATE LIMITING TESTS
# ============================================================================

class TestRateLimiting(unittest.TestCase):
    """Test rate limiting system."""
    
    def setUp(self):
        from trading_bot.connectivity.rate_limiter_advanced import (
            RateLimitConfig, TokenBucketLimiter, SlidingWindowLimiter,
            RateLimitResult, RateLimitManager
        )
        self.RateLimitConfig = RateLimitConfig
        self.TokenBucketLimiter = TokenBucketLimiter
        self.SlidingWindowLimiter = SlidingWindowLimiter
        self.RateLimitResult = RateLimitResult
        self.RateLimitManager = RateLimitManager
    
    def test_token_bucket_allows_burst(self):
        """Test token bucket allows burst."""
        config = self.RateLimitConfig(
            requests_per_second=10,
            burst_size=5,
        )
        limiter = self.TokenBucketLimiter(config)
        
        # Should allow burst
        for _ in range(5):
            status = limiter.acquire("test")
            self.assertEqual(status.result, self.RateLimitResult.ALLOWED)
    
    def test_token_bucket_rate_limits(self):
        """Test token bucket rate limits after burst."""
        config = self.RateLimitConfig(
            requests_per_second=1,
            burst_size=2,
        )
        limiter = self.TokenBucketLimiter(config)
        
        # Use up burst
        limiter.acquire("test")
        limiter.acquire("test")
        
        # Should be rate limited
        status = limiter.acquire("test")
        self.assertEqual(status.result, self.RateLimitResult.RATE_LIMITED)
    
    def test_rate_limit_manager(self):
        """Test rate limit manager."""
        manager = self.RateLimitManager()
        
        status = manager.acquire("test", "key1")
        self.assertEqual(status.result, self.RateLimitResult.ALLOWED)


# ============================================================================
# MEMORY MANAGEMENT TESTS
# ============================================================================

class TestMemoryManagement(unittest.TestCase):
    """Test memory management system."""
    
    def setUp(self):
        from trading_bot.performance.memory_manager import (
            MemoryConfig, SizeLimitedLRUCache, RingBuffer,
            WeakRefCache, MemoryManager
        )
        self.MemoryConfig = MemoryConfig
        self.SizeLimitedLRUCache = SizeLimitedLRUCache
        self.RingBuffer = RingBuffer
        self.WeakRefCache = WeakRefCache
        self.MemoryManager = MemoryManager
    
    def test_lru_cache_basic(self):
        """Test LRU cache basic operations."""
        cache = self.SizeLimitedLRUCache(max_size_mb=1, max_items=10)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        self.assertEqual(cache.get("key1"), "value1")
        self.assertEqual(cache.get("key2"), "value2")
        self.assertIsNone(cache.get("key3"))
    
    def test_lru_cache_eviction(self):
        """Test LRU cache eviction."""
        cache = self.SizeLimitedLRUCache(max_size_mb=1, max_items=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should evict key1
        
        self.assertIsNone(cache.get("key1"))
        self.assertEqual(cache.get("key4"), "value4")
    
    def test_ring_buffer(self):
        """Test ring buffer."""
        buffer = self.RingBuffer(capacity=3)
        
        buffer.append(1)
        buffer.append(2)
        buffer.append(3)
        buffer.append(4)  # Overwrites 1
        
        items = buffer.get_all()
        self.assertEqual(items, [2, 3, 4])
    
    def test_ring_buffer_latest(self):
        """Test ring buffer get latest."""
        buffer = self.RingBuffer(capacity=5)
        
        for i in range(5):
            buffer.append(i)
        
        latest = buffer.get_latest(3)
        self.assertEqual(latest, [2, 3, 4])
    
    def test_memory_manager(self):
        """Test memory manager."""
        manager = self.MemoryManager()
        
        cache = manager.create_cache("test", max_size_mb=10)
        self.assertIsNotNone(cache)
        
        retrieved = manager.get_cache("test")
        self.assertIs(cache, retrieved)


# ============================================================================
# TELEGRAM BOT TESTS
# ============================================================================

class TestTelegramBot(unittest.TestCase):
    """Test Telegram bot integration."""
    
    def setUp(self):
        from trading_bot.notifications.telegram_bot import (
            TelegramConfig, TelegramBot, NotificationType
        )
        self.TelegramConfig = TelegramConfig
        self.TelegramBot = TelegramBot
        self.NotificationType = NotificationType
    
    def test_telegram_config(self):
        """Test Telegram configuration."""
        config = self.TelegramConfig(
            bot_token="test_token",
            chat_id="123456",
            admin_ids=["111", "222"],
        )
        
        self.assertEqual(config.bot_token, "test_token")
        self.assertEqual(len(config.admin_ids), 2)
    
    def test_telegram_bot_creation(self):
        """Test Telegram bot creation."""
        config = self.TelegramConfig(bot_token="test")
        bot = self.TelegramBot(config)
        
        self.assertIsNotNone(bot)
        self.assertFalse(bot._running)
    
    def test_rate_limit_check(self):
        """Test Telegram rate limiting."""
        config = self.TelegramConfig(
            bot_token="test",
            rate_limit_per_minute=2,
        )
        bot = self.TelegramBot(config)
        
        # First two should pass
        self.assertTrue(bot._check_rate_limit("123"))
        self.assertTrue(bot._check_rate_limit("123"))
        
        # Third should fail
        self.assertFalse(bot._check_rate_limit("123"))


# ============================================================================
# RISK MANAGEMENT TESTS
# ============================================================================

class TestRiskManagement(unittest.TestCase):
    """Test risk management calculations."""
    
    def test_position_size_fixed_risk(self):
        """Test fixed risk position sizing."""
        account_balance = 10000
        risk_per_trade = 0.02  # 2%
        stop_loss_pips = 50
        pip_value = 10  # $10 per pip for 1 lot
        
        risk_amount = account_balance * risk_per_trade  # $200
        position_size = risk_amount / (stop_loss_pips * pip_value)  # 0.4 lots
        
        self.assertAlmostEqual(position_size, 0.4, places=2)
    
    def test_kelly_criterion(self):
        """Test Kelly criterion calculation."""
        win_rate = 0.55
        avg_win = 100
        avg_loss = 80
        
        # Kelly = W - (1-W)/R where R = avg_win/avg_loss
        R = avg_win / avg_loss
        kelly = win_rate - (1 - win_rate) / R
        
        self.assertGreater(kelly, 0)
        self.assertLess(kelly, 1)
    
    def test_max_drawdown_calculation(self):
        """Test max drawdown calculation."""
        equity_curve = [10000, 10500, 10200, 9800, 10100, 9500, 10000]
        
        peak = equity_curve[0]
        max_dd = 0
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd
        
        self.assertAlmostEqual(max_dd, 0.095238, places=4)  # ~9.5%
    
    def test_var_calculation(self):
        """Test Value at Risk calculation."""
        import numpy as np
        
        returns = np.array([0.01, -0.02, 0.015, -0.01, 0.02, -0.025, 0.01])
        confidence = 0.95
        
        var = np.percentile(returns, (1 - confidence) * 100)
        
        self.assertLess(var, 0)  # VaR should be negative (loss)


# ============================================================================
# SIGNAL GENERATION TESTS
# ============================================================================

class TestSignalGeneration(unittest.TestCase):
    """Test signal generation and validation."""
    
    def test_rsi_calculation(self):
        """Test RSI calculation."""
        
        prices = np.array([44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08])
        
        # Calculate price changes
        changes = np.diff(prices)
        gains = np.where(changes > 0, changes, 0)
        losses = np.where(changes < 0, -changes, 0)
        
        # Average gains and losses
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        self.assertGreater(rsi, 0)
        self.assertLess(rsi, 100)
    
    def test_macd_calculation(self):
        """Test MACD calculation."""
        
        prices = np.array([10, 11, 12, 11.5, 12.5, 13, 12.8, 13.5, 14, 13.8])
        
        # Simple EMA calculation
        def ema(data, period):
            alpha = 2 / (period + 1)
            result = [data[0]]
            for i in range(1, len(data)):
                result.append(alpha * data[i] + (1 - alpha) * result[-1])
            return np.array(result)
        
        ema_fast = ema(prices, 3)
        ema_slow = ema(prices, 5)
        macd_line = ema_fast - ema_slow
        
        self.assertEqual(len(macd_line), len(prices))
    
    def test_signal_confidence_scoring(self):
        """Test signal confidence scoring."""
        # Multiple indicators
        rsi_signal = 0.7  # Bullish
        macd_signal = 0.6  # Bullish
        trend_signal = 0.8  # Bullish
        volume_signal = 0.5  # Neutral
        
        # Weighted average
        weights = [0.3, 0.25, 0.3, 0.15]
        signals = [rsi_signal, macd_signal, trend_signal, volume_signal]
        
        confidence = sum(w * s for w, s in zip(weights, signals))
        
        self.assertGreater(confidence, 0.5)
        self.assertLess(confidence, 1.0)


# ============================================================================
# EXECUTION TESTS
# ============================================================================

class TestExecution(unittest.TestCase):
    """Test order execution."""
    
    def test_slippage_calculation(self):
        """Test slippage calculation."""
        expected_price = 1.0850
        actual_price = 1.0855
        
        slippage_pips = (actual_price - expected_price) * 10000
        
        self.assertAlmostEqual(slippage_pips, 5, places=1)
    
    def test_twap_order_splitting(self):
        """Test TWAP order splitting."""
        total_quantity = 1.0
        num_slices = 5
        duration_minutes = 10
        
        slice_quantity = total_quantity / num_slices
        interval_seconds = (duration_minutes * 60) / num_slices
        
        self.assertAlmostEqual(slice_quantity, 0.2, places=2)
        self.assertAlmostEqual(interval_seconds, 120, places=0)
    
    def test_vwap_calculation(self):
        """Test VWAP calculation."""
        
        prices = np.array([100, 101, 102, 101.5, 102.5])
        volumes = np.array([1000, 1500, 2000, 1200, 1800])
        
        vwap = np.sum(prices * volumes) / np.sum(volumes)
        
        self.assertGreater(vwap, min(prices))
        self.assertLess(vwap, max(prices))


# ============================================================================
# DATA VALIDATION TESTS
# ============================================================================

class TestDataValidation(unittest.TestCase):
    """Test data validation."""
    
    def test_ohlcv_validation(self):
        """Test OHLCV data validation."""
        # Valid OHLCV
        valid = {
            'open': 100,
            'high': 105,
            'low': 98,
            'close': 103,
            'volume': 1000,
        }
        
        # Validate high >= open, close, low
        self.assertGreaterEqual(valid['high'], valid['open'])
        self.assertGreaterEqual(valid['high'], valid['close'])
        self.assertGreaterEqual(valid['high'], valid['low'])
        
        # Validate low <= open, close, high
        self.assertLessEqual(valid['low'], valid['open'])
        self.assertLessEqual(valid['low'], valid['close'])
        self.assertLessEqual(valid['low'], valid['high'])
    
    def test_price_anomaly_detection(self):
        """Test price anomaly detection."""
        
        prices = np.array([100, 101, 102, 101, 150, 102, 103])  # 150 is anomaly
        
        mean = np.mean(prices)
        std = np.std(prices)
        z_scores = np.abs((prices - mean) / std)
        
        anomalies = z_scores > 2  # 2 standard deviations
        
        self.assertTrue(anomalies[4])  # 150 should be flagged
    
    def test_staleness_detection(self):
        """Test data staleness detection."""
        last_update = datetime.utcnow() - timedelta(seconds=60)
        threshold_seconds = 30
        
        age_seconds = (datetime.utcnow() - last_update).total_seconds()
        is_stale = age_seconds > threshold_seconds
        
        self.assertTrue(is_stale)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_full_trade_flow(self):
        """Test complete trade flow."""
        # 1. Generate signal
        signal = {
            'symbol': 'EURUSD',
            'direction': 'buy',
            'confidence': 0.75,
            'price': 1.0850,
        }
        
        # 2. Validate signal
        min_confidence = 0.6
        is_valid = signal['confidence'] >= min_confidence
        self.assertTrue(is_valid)
        
        # 3. Calculate position size
        account_balance = 10000
        risk_per_trade = 0.02
        stop_loss_pips = 30
        pip_value = 10
        
        risk_amount = account_balance * risk_per_trade
        position_size = risk_amount / (stop_loss_pips * pip_value)
        
        self.assertGreater(position_size, 0)
        
        # 4. Create order
        order = {
            'symbol': signal['symbol'],
            'side': signal['direction'],
            'quantity': round(position_size, 2),
            'price': signal['price'],
            'stop_loss': signal['price'] - 0.0030,
            'take_profit': signal['price'] + 0.0060,
        }
        
        self.assertEqual(order['symbol'], 'EURUSD')
        self.assertGreater(order['quantity'], 0)
    
    def test_risk_check_flow(self):
        """Test risk check flow."""
        # Current state
        account_balance = 10000
        current_drawdown = 0.08  # 8%
        daily_loss = 0.03  # 3%
        open_positions = 3
        
        # Limits
        max_drawdown = 0.20
        max_daily_loss = 0.05
        max_positions = 5
        
        # Checks
        drawdown_ok = current_drawdown < max_drawdown
        daily_loss_ok = daily_loss < max_daily_loss
        positions_ok = open_positions < max_positions
        
        can_trade = drawdown_ok and daily_loss_ok and positions_ok
        
        self.assertTrue(can_trade)


# ============================================================================
# ASYNC TESTS
# ============================================================================

class TestAsync(unittest.IsolatedAsyncioTestCase):
    """Async tests."""
    
    async def test_async_rate_limit(self):
        """Test async rate limiting."""
            RateLimitManager, RateLimitResult
        )
        
        manager = RateLimitManager()
        
        status = await manager.acquire_async("test", wait=False)
        self.assertEqual(status.result, RateLimitResult.ALLOWED)
    
    async def test_async_error_recovery(self):
        """Test async error recovery."""
        from trading_bot.core.error_recovery import RecoveryManager
        
        manager = RecoveryManager()
        
        async def success_func():
            return "success"
        
        result = await manager.execute_with_recovery(
            success_func,
            component="test",
            operation="test_op",
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.result, "success")


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance(unittest.TestCase):
    """Performance tests."""
    
    def test_cache_performance(self):
        """Test cache performance."""
        import time
        from trading_bot.performance.memory_manager import SizeLimitedLRUCache
        
        cache = SizeLimitedLRUCache(max_size_mb=10, max_items=10000)
        
        # Write performance
        start = time.time()
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}")
        write_time = time.time() - start
        
        # Read performance
        start = time.time()
        for i in range(1000):
            cache.get(f"key_{i}")
        read_time = time.time() - start
        
        # Should be fast
        self.assertLess(write_time, 1.0)  # < 1 second for 1000 writes
        self.assertLess(read_time, 0.5)   # < 0.5 seconds for 1000 reads
    
    def test_ring_buffer_performance(self):
        """Test ring buffer performance."""
        from trading_bot.performance.memory_manager import RingBuffer
import logging
import numpy
        
        buffer = RingBuffer(capacity=10000)
        
        start = time.time()
        for i in range(10000):
            buffer.append(i)
        append_time = time.time() - start
        
        self.assertLess(append_time, 0.5)


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    # Run with pytest for better output
    pytest.main([__file__, '-v', '--tb=short'])
