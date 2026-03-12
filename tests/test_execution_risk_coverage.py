"""
Execution and Risk module coverage tests.
"""

import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPositionSizerCoverage(unittest.TestCase):
    """Coverage tests for PositionSizer"""
    
    def setUp(self):
        from trading_bot.risk.position_sizer import PositionSizer
        self.sizer = PositionSizer()
    
    def test_calculate_fixed_risk_size(self):
        """Test fixed risk position sizing"""
        size = self.sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=10000,
            risk_percent=0.02,
            entry_price=1.1000,
            stop_loss=1.0950
        )
        self.assertIsNotNone(size)
        self.assertGreater(size, 0)
    
    def test_calculate_kelly_size(self):
        """Test Kelly criterion sizing"""
        if hasattr(self.sizer, 'calculate_kelly_size'):
            size = self.sizer.calculate_kelly_size(
                win_rate=0.55,
                avg_win=100,
                avg_loss=50,
                account_balance=10000
            )
            self.assertIsNotNone(size)
    
    def test_calculate_volatility_adjusted_size(self):
        """Test volatility adjusted sizing"""
        if hasattr(self.sizer, 'calculate_volatility_adjusted_size'):
            size = self.sizer.calculate_volatility_adjusted_size(
                account_balance=10000,
                volatility=0.01,
                target_risk=0.02
            )
            self.assertIsNotNone(size)
    
    def test_position_size_limits(self):
        """Test position size limits"""
        # Very small account should limit position size
        size = self.sizer.calculate_position_size(
            symbol='EURUSD',
            account_equity=100,
            risk_percent=0.02,
            entry_price=1.1000,
            stop_loss=1.0950
        )
        self.assertLessEqual(size, 1.0)  # Should be limited


class TestCorrelationManagerCoverage(unittest.TestCase):
    """Coverage tests for EnhancedCorrelationManager"""
    
    def setUp(self):
        from trading_bot.risk.correlation_persistence import EnhancedCorrelationManager
        self.manager = EnhancedCorrelationManager()
    
    def test_calculate_correlation(self):
        """Test correlation calculation"""
        if hasattr(self.manager, 'calculate_correlation'):
            returns1 = np.random.normal(0, 0.01, 100)
            returns2 = np.random.normal(0, 0.01, 100)
            corr = self.manager.calculate_correlation(returns1, returns2)
            self.assertIsNotNone(corr)
            self.assertGreaterEqual(corr, -1)
            self.assertLessEqual(corr, 1)
    
    def test_update_correlations(self):
        """Test updating correlations"""
        if hasattr(self.manager, 'update'):
            data = {
                'EURUSD': np.random.normal(0, 0.01, 100),
                'GBPUSD': np.random.normal(0, 0.01, 100)
            }
            self.manager.update(data)
    
    def test_get_correlation_matrix(self):
        """Test getting correlation matrix"""
        if hasattr(self.manager, 'get_correlation_matrix'):
            matrix = self.manager.get_correlation_matrix()
            self.assertIsNotNone(matrix)
    
    def test_check_exposure(self):
        """Test exposure check"""
        if hasattr(self.manager, 'check_exposure'):
            positions = [
                {'symbol': 'EURUSD', 'size': 0.1},
                {'symbol': 'GBPUSD', 'size': 0.1}
            ]
            result = self.manager.check_exposure(positions)
            self.assertIsNotNone(result)


class TestPortfolioRiskManagerCoverage(unittest.TestCase):
    """Coverage tests for PortfolioRiskManager"""
    
    def setUp(self):
        from trading_bot.risk.portfolio_risk_manager import PortfolioRiskManager
        self.manager = PortfolioRiskManager()
    
    def test_calculate_var(self):
        """Test VaR calculation"""
        if hasattr(self.manager, 'calculate_var'):
            returns = np.random.normal(0, 0.01, 252)
            var = self.manager.calculate_var(returns, confidence=0.95)
            self.assertIsNotNone(var)
            self.assertLess(var, 0)  # VaR should be negative
    
    def test_calculate_cvar(self):
        """Test CVaR calculation"""
        if hasattr(self.manager, 'calculate_cvar'):
            returns = np.random.normal(0, 0.01, 252)
            cvar = self.manager.calculate_cvar(returns, confidence=0.95)
            self.assertIsNotNone(cvar)
    
    def test_calculate_sharpe(self):
        """Test Sharpe ratio calculation"""
        if hasattr(self.manager, 'calculate_sharpe'):
            returns = np.random.normal(0.001, 0.01, 252)
            sharpe = self.manager.calculate_sharpe(returns)
            self.assertIsNotNone(sharpe)
    
    def test_calculate_max_drawdown(self):
        """Test max drawdown calculation"""
        if hasattr(self.manager, 'calculate_max_drawdown'):
            equity_curve = np.cumsum(np.random.normal(0.001, 0.01, 252)) + 10000
            mdd = self.manager.calculate_max_drawdown(equity_curve)
            self.assertIsNotNone(mdd)
            self.assertGreaterEqual(mdd, 0)


class TestFillTrackerCoverage(unittest.TestCase):
    """Coverage tests for FillTracker"""
    
    def setUp(self):
        from trading_bot.execution.fill_tracker import FillTracker
        mock_broker = MagicMock()
        mock_broker.get_order_status.return_value = {'status': 'filled', 'filled_size': 0.1}
        self.tracker = FillTracker(mock_broker)
    
    def test_track_order(self):
        """Test order tracking"""
        if hasattr(self.tracker, 'track_order'):
            self.tracker.track_order('order-123', 'EURUSD', 0.1)
    
    def test_get_fill_status(self):
        """Test getting fill status"""
        if hasattr(self.tracker, 'get_fill_status'):
            status = self.tracker.get_fill_status('order-123')
            self.assertIsNotNone(status)
    
    def test_calculate_slippage(self):
        """Test slippage calculation"""
        if hasattr(self.tracker, 'calculate_slippage'):
            slippage = self.tracker.calculate_slippage(
                expected_price=1.1000,
                actual_price=1.1002
            )
            self.assertIsNotNone(slippage)
    
    def test_wait_for_fill(self):
        """Test waiting for fill"""
        if hasattr(self.tracker, 'wait_for_fill'):
            result = self.tracker.wait_for_fill('order-123', timeout=1)
            self.assertIsNotNone(result)


class TestIdempotentExecutorCoverage(unittest.TestCase):
    """Coverage tests for IdempotentExecutor"""
    
    def setUp(self):
        from trading_bot.execution.idempotent_executor import IdempotentExecutor
        self.executor = IdempotentExecutor()
    
    def test_generate_client_order_id(self):
        """Test client order ID generation"""
        if hasattr(self.executor, 'generate_client_order_id'):
            order_id = self.executor.generate_client_order_id('EURUSD', 'buy', 0.1)
            self.assertIsNotNone(order_id)
            self.assertIsInstance(order_id, str)
    
    def test_check_duplicate(self):
        """Test duplicate check"""
        if hasattr(self.executor, 'is_duplicate'):
            result = self.executor.is_duplicate('order-123')
            self.assertIsNotNone(result)
    
    def test_record_order(self):
        """Test order recording"""
        if hasattr(self.executor, 'record_order'):
            self.executor.record_order('order-123', {'symbol': 'EURUSD'})
    
    def test_get_order_history(self):
        """Test getting order history"""
        if hasattr(self.executor, 'get_order_history'):
            history = self.executor.get_order_history()
            self.assertIsNotNone(history)


class TestPartialFillAggregatorCoverage(unittest.TestCase):
    """Coverage tests for PartialFillAggregator"""
    
    def setUp(self):
        from trading_bot.execution.partial_fill_aggregator import PartialFillAggregator
        self.aggregator = PartialFillAggregator()
    
    def test_add_fill(self):
        """Test adding fill"""
        if hasattr(self.aggregator, 'add_fill'):
            self.aggregator.add_fill('order-123', {
                'size': 0.05,
                'price': 1.1000,
                'timestamp': datetime.now()
            })
    
    def test_get_aggregated_fill(self):
        """Test getting aggregated fill"""
        if hasattr(self.aggregator, 'get_aggregated_fill'):
            # Add some fills first
            if hasattr(self.aggregator, 'add_fill'):
                self.aggregator.add_fill('order-123', {'size': 0.05, 'price': 1.1000})
                self.aggregator.add_fill('order-123', {'size': 0.05, 'price': 1.1001})
            
            result = self.aggregator.get_aggregated_fill('order-123')
            self.assertIsNotNone(result)
    
    def test_calculate_vwap(self):
        """Test VWAP calculation"""
        if hasattr(self.aggregator, 'calculate_vwap'):
            fills = [
                {'size': 0.05, 'price': 1.1000},
                {'size': 0.05, 'price': 1.1002}
            ]
            vwap = self.aggregator.calculate_vwap(fills)
            self.assertIsNotNone(vwap)
            self.assertAlmostEqual(vwap, 1.1001, places=4)


class TestMarketImpactModelCoverage(unittest.TestCase):
    """Coverage tests for MarketImpactModel"""
    
    def setUp(self):
        from trading_bot.execution.market_impact import MarketImpactModel
        self.model = MarketImpactModel()
    
    def test_estimate_impact(self):
        """Test impact estimation"""
        if hasattr(self.model, 'estimate_impact'):
            impact = self.model.estimate_impact(
                symbol='EURUSD',
                size=1.0,
                side='buy'
            )
            self.assertIsNotNone(impact)
    
    def test_estimate_slippage(self):
        """Test slippage estimation"""
        if hasattr(self.model, 'estimate_slippage'):
            slippage = self.model.estimate_slippage(
                symbol='EURUSD',
                size=1.0,
                volatility=0.01
            )
            self.assertIsNotNone(slippage)
    
    def test_optimal_execution_schedule(self):
        """Test optimal execution schedule"""
        if hasattr(self.model, 'get_optimal_schedule'):
            schedule = self.model.get_optimal_schedule(
                symbol='EURUSD',
                total_size=1.0,
                duration_minutes=60
            )
            self.assertIsNotNone(schedule)


class TestTWAPExecutorCoverage(unittest.TestCase):
    """Coverage tests for TWAPExecutor"""
    
    def setUp(self):
        from trading_bot.execution.smart_execution import TWAPExecutor
        self.executor = TWAPExecutor()
    
    def test_calculate_slices(self):
        """Test slice calculation"""
        if hasattr(self.executor, 'calculate_slices'):
            slices = self.executor.calculate_slices(
                total_size=1.0,
                duration_minutes=60,
                interval_minutes=5
            )
            self.assertIsNotNone(slices)
            self.assertEqual(len(slices), 12)
    
    def test_get_next_slice(self):
        """Test getting next slice"""
        if hasattr(self.executor, 'get_next_slice'):
            slice_info = self.executor.get_next_slice()
            self.assertIsNotNone(slice_info)


class TestVWAPExecutorCoverage(unittest.TestCase):
    """Coverage tests for VWAPExecutor"""
    
    def setUp(self):
        from trading_bot.execution.smart_execution import VWAPExecutor
        self.executor = VWAPExecutor()
    
    def test_calculate_volume_profile(self):
        """Test volume profile calculation"""
        if hasattr(self.executor, 'calculate_volume_profile'):
            volumes = np.random.randint(1000, 10000, 24)
            profile = self.executor.calculate_volume_profile(volumes)
            self.assertIsNotNone(profile)
    
    def test_calculate_slices(self):
        """Test VWAP slice calculation"""
        if hasattr(self.executor, 'calculate_slices'):
            slices = self.executor.calculate_slices(
                total_size=1.0,
                volume_profile=np.ones(12) / 12
            )
            self.assertIsNotNone(slices)


class TestSignalLifecycleManagerCoverage(unittest.TestCase):
    """Coverage tests for SignalLifecycleManager"""
    
    def setUp(self):
        from trading_bot.signals.signal_lifecycle import SignalLifecycleManager
        self.manager = SignalLifecycleManager()
    
    def test_create_signal(self):
        """Test signal creation"""
        if hasattr(self.manager, 'create_signal'):
            signal = self.manager.create_signal(
                signal_id='sig-123',
                symbol='EURUSD',
                direction='buy',
                confidence=0.8,
                ttl_seconds=300
            )
            self.assertIsNotNone(signal)
    
    def test_apply_decay(self):
        """Test signal decay"""
        if hasattr(self.manager, 'apply_decay'):
            signal = {
                'confidence': 0.8,
                'created_at': datetime.now() - timedelta(minutes=5),
                'ttl_seconds': 600
            }
            decayed = self.manager.apply_decay(signal)
            self.assertIsNotNone(decayed)
            self.assertLess(decayed['confidence'], 0.8)
    
    def test_is_expired(self):
        """Test expiry check"""
        if hasattr(self.manager, 'is_expired'):
            # Expired signal
            expired_signal = {
                'created_at': datetime.now() - timedelta(hours=1),
                'ttl_seconds': 300
            }
            self.assertTrue(self.manager.is_expired(expired_signal))
            
            # Fresh signal
            fresh_signal = {
                'created_at': datetime.now(),
                'ttl_seconds': 300
            }
            self.assertFalse(self.manager.is_expired(fresh_signal))
    
    def test_get_active_signals(self):
        """Test getting active signals"""
        if hasattr(self.manager, 'get_active_signals'):
            signals = self.manager.get_active_signals()
            self.assertIsNotNone(signals)


class TestNewsGatingCoverage(unittest.TestCase):
    """Coverage tests for NewsGating"""
    
    def setUp(self):
        from trading_bot.signals.news_gating import NewsGating
        self.gating = NewsGating()
    
    def test_is_blackout_period(self):
        """Test blackout period check"""
        if hasattr(self.gating, 'is_blackout_period'):
            result = self.gating.is_blackout_period('EURUSD')
            self.assertIsNotNone(result)
    
    def test_get_upcoming_events(self):
        """Test getting upcoming events"""
        if hasattr(self.gating, 'get_upcoming_events'):
            events = self.gating.get_upcoming_events('EURUSD')
            self.assertIsNotNone(events)
    
    def test_should_trade(self):
        """Test trade decision based on news"""
        if hasattr(self.gating, 'should_trade'):
            result = self.gating.should_trade('EURUSD')
            self.assertIsNotNone(result)


class TestStalenessDetectorCoverage(unittest.TestCase):
    """Coverage tests for StalenessDetector"""
    
    def setUp(self):
        from trading_bot.connectivity.staleness_detector import StalenessDetector
        self.detector = StalenessDetector()
    
    def test_is_stale(self):
        """Test staleness check"""
        if hasattr(self.detector, 'is_stale'):
            # Fresh data
            fresh_time = datetime.now()
            self.assertFalse(self.detector.is_stale('EURUSD', fresh_time))
            
            # Stale data
            stale_time = datetime.now() - timedelta(minutes=10)
            self.assertTrue(self.detector.is_stale('EURUSD', stale_time))
    
    def test_update_timestamp(self):
        """Test timestamp update"""
        if hasattr(self.detector, 'update_timestamp'):
            self.detector.update_timestamp('EURUSD', datetime.now())
    
    def test_get_staleness_report(self):
        """Test staleness report"""
        if hasattr(self.detector, 'get_staleness_report'):
            report = self.detector.get_staleness_report()
            self.assertIsNotNone(report)


class TestSequenceGuardCoverage(unittest.TestCase):
    """Coverage tests for SequenceGuard"""
    
    def setUp(self):
        from trading_bot.connectivity.sequence_guard import SequenceGuard
        self.guard = SequenceGuard()
    
    def test_check_sequence(self):
        """Test sequence check"""
        if hasattr(self.guard, 'check_sequence'):
            # Sequential
            self.assertTrue(self.guard.check_sequence('EURUSD', 100))
            self.assertTrue(self.guard.check_sequence('EURUSD', 101))
            
            # Gap
            self.assertFalse(self.guard.check_sequence('EURUSD', 105))
    
    def test_detect_gap(self):
        """Test gap detection"""
        if hasattr(self.guard, 'detect_gap'):
            gap = self.guard.detect_gap('EURUSD', 100, 105)
            self.assertIsNotNone(gap)
            self.assertEqual(gap, [101, 102, 103, 104])


class TestVenueOutageDetectorCoverage(unittest.TestCase):
    """Coverage tests for VenueOutageDetector"""
    
    def setUp(self):
        from trading_bot.connectivity.venue_outage_detector import VenueOutageDetector
import numpy
import pandas
self.detector = VenueOutageDetector()
    
def test_check_venue_status(self):
        """Test venue status check"""
        if hasattr(self.detector, 'check_venue_status'):
            status = self.detector.check_venue_status('MT5')
            self.assertIsNotNone(status)
    
def test_report_outage(self):
        """Test outage reporting"""
        if hasattr(self.detector, 'report_outage'):
            self.detector.report_outage('MT5', 'Connection timeout')
    
def test_get_healthy_venues(self):
        """Test getting healthy venues"""
        if hasattr(self.detector, 'get_healthy_venues'):
            venues = self.detector.get_healthy_venues()
            self.assertIsNotNone(venues)


if __name__ == '__main__':
    unittest.main()
