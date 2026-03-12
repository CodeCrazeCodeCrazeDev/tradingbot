"""
Tests for Critical Fixes Module
===============================

Comprehensive tests for all critical fix components.
"""

import asyncio
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch


class MockBrokerAdapter:
    """Mock broker for testing"""
    
    def __init__(self):
        self.positions = []
        self.closed_positions = []
    
    async def get_positions(self):
        return self.positions
    
    async def close_position(self, ticket, use_market_order=False):
        for pos in self.positions:
            if pos.get('ticket') == ticket:
                self.positions.remove(pos)
                self.closed_positions.append(pos)
                return True
        return False
    
    def add_position(self, pos):
        self.positions.append(pos)


class TestPositionStateManager:
    """Tests for PositionStateManager"""
    
    @pytest.fixture
    def manager(self, tmp_path):
        from trading_bot.critical_fixes import PositionStateManager
        broker = MockBrokerAdapter()
        return PositionStateManager(
            broker_adapter=broker,
            db_path=str(tmp_path / "test_positions.db"),
            reconciliation_interval=60,
            auto_correct=False
        )
    
    def test_add_position(self, manager):
        """Test adding a position"""
        from trading_bot.critical_fixes import PositionState
        from trading_bot.critical_fixes.position_state_manager import PositionStatus
        
        position = PositionState(
            position_id="test_001",
            symbol="EURUSD",
            direction="long",
            quantity=0.1,
            entry_price=1.1000,
            current_price=1.1050,
            unrealized_pnl=50.0,
            realized_pnl=0,
            stop_loss=1.0950,
            take_profit=1.1100,
            opened_at=datetime.now(),
            last_updated=datetime.now(),
            status=PositionStatus.OPEN
        )
        
        success = manager.add_position(position)
        assert success is True
        
        retrieved = manager.get_position("test_001")
        assert retrieved is not None
        assert retrieved.symbol == "EURUSD"
    
    def test_update_position(self, manager):
        """Test updating a position"""
        
        position = PositionState(
            position_id="test_002",
            symbol="GBPUSD",
            direction="long",
            quantity=0.1,
            entry_price=1.2500,
            current_price=1.2500,
            unrealized_pnl=0,
            realized_pnl=0,
            stop_loss=None,
            take_profit=None,
            opened_at=datetime.now(),
            last_updated=datetime.now(),
            status=PositionStatus.OPEN
        )
        
        manager.add_position(position)
        
        success = manager.update_position("test_002", {'current_price': 1.2550, 'unrealized_pnl': 50})
        assert success is True
        
        updated = manager.get_position("test_002")
        assert updated.current_price == 1.2550
    
    def test_position_checksum(self):
        """Test position checksum for integrity"""
        
        position = PositionState(
            position_id="test_003",
            symbol="USDJPY",
            direction="short",
            quantity=0.2,
            entry_price=150.00,
            current_price=149.50,
            unrealized_pnl=100,
            realized_pnl=0,
            stop_loss=150.50,
            take_profit=149.00,
            opened_at=datetime.now(),
            last_updated=datetime.now(),
            status=PositionStatus.OPEN
        )
        
        checksum1 = position.checksum()
        checksum2 = position.checksum()
        
        assert checksum1 == checksum2
        assert len(checksum1) == 16


class TestRealtimeRiskCalculator:
    """Tests for RealtimeRiskCalculator"""
    
    @pytest.fixture
    def calculator(self):
        from trading_bot.critical_fixes import RealtimeRiskCalculator, RiskLimits
        
        limits = RiskLimits(
            max_risk_per_trade=0.02,
            max_drawdown=0.20,
            emergency_shutdown_drawdown=0.25
        )
        return RealtimeRiskCalculator(limits=limits)
    
    def test_equity_tracking(self, calculator):
        """Test equity and drawdown tracking"""
        calculator.update_equity(10000)
        calculator.update_equity(9500)  # 5% drawdown
        
        metrics = calculator.calculate_risk(equity=9500)
        
        assert metrics.current_drawdown == pytest.approx(0.05, rel=0.01)
    
    def test_absolute_limits_enforced(self):
        """Test that absolute limits cannot be exceeded"""
        
        # Try to set limits above absolute max
        limits = RiskLimits(
            max_drawdown=0.50,  # Above ABSOLUTE_MAX_DRAWDOWN
            max_risk_per_trade=0.10  # Above ABSOLUTE_MAX_RISK_PER_TRADE
        )
        
        calculator = RealtimeRiskCalculator(limits=limits)
        
        # Should be capped at absolute limits
        assert calculator.limits.max_drawdown <= calculator.ABSOLUTE_MAX_DRAWDOWN
        assert calculator.limits.max_risk_per_trade <= calculator.ABSOLUTE_MAX_RISK_PER_TRADE
    
    def test_can_open_position(self, calculator):
        """Test position opening checks"""
        calculator.update_equity(10000)
        
        # Should allow reasonable position
        can_open, reason = calculator.can_open_position(
            symbol='EURUSD',
            quantity=0.1,
            price=1.1000,
            stop_loss=1.0950,
            equity=10000
        )
        
        assert can_open is True
    
    def test_position_blocked_at_max_positions(self, calculator):
        """Test that positions are blocked when at max"""
        calculator.update_equity(10000)
        
        # Add max positions
        positions = [
            {'position_id': str(i), 'symbol': 'EURUSD', 'quantity': 0.01, 'current_price': 1.1}
            for i in range(calculator.limits.max_open_positions)
        ]
        calculator.update_positions(positions)
        
        can_open, reason = calculator.can_open_position(
            symbol='EURUSD',
            quantity=0.01,
            price=1.1000,
            stop_loss=1.0950,
            equity=10000
        )
        
        assert can_open is False
        assert "Max positions" in reason


class TestMultiLayerKillSwitch:
    """Tests for MultiLayerKillSwitch"""
    
    @pytest.fixture
    def kill_switch(self, tmp_path):
        from trading_bot.critical_fixes import MultiLayerKillSwitch
        broker = MockBrokerAdapter()
        return MultiLayerKillSwitch(
            broker_adapter=broker,
            db_path=str(tmp_path / "test_kill_switch.db"),
            heartbeat_timeout=30
        )
    
    def test_initial_state(self, kill_switch):
        """Test initial state is inactive"""
        assert kill_switch.is_active is False
        assert kill_switch.can_trade is True
    
    @pytest.mark.asyncio
    async def test_soft_activation(self, kill_switch):
        """Test soft kill switch activation"""
        from trading_bot.critical_fixes import KillSwitchLevel
        from trading_bot.critical_fixes.multi_layer_kill_switch import KillSwitchTrigger
        
        event = await kill_switch.activate(
            KillSwitchLevel.SOFT,
            KillSwitchTrigger.MANUAL_CODE,
            "Test activation",
            "test"
        )
        
        assert kill_switch.is_active is True
        assert kill_switch.current_level == KillSwitchLevel.SOFT
        assert kill_switch.can_trade is False
    
    @pytest.mark.asyncio
    async def test_cannot_downgrade_hard(self, kill_switch):
        """Test that HARD level cannot be downgraded"""
        from trading_bot.critical_fixes.multi_layer_kill_switch import KillSwitchTrigger, KillSwitchBypassError
        
        # Activate HARD
        await kill_switch.activate(
            KillSwitchLevel.HARD,
            KillSwitchTrigger.DRAWDOWN,
            "Test",
            "test"
        )
        
        # Try to downgrade to SOFT
        with pytest.raises(KillSwitchBypassError):
            await kill_switch.activate(
                KillSwitchLevel.SOFT,
                KillSwitchTrigger.MANUAL_CODE,
                "Downgrade attempt",
                "test"
            )
    
    def test_heartbeat(self, kill_switch):
        """Test heartbeat functionality"""
        initial_heartbeat = kill_switch._last_heartbeat
        kill_switch.heartbeat()
        
        assert kill_switch._last_heartbeat >= initial_heartbeat


class TestDataValidator:
    """Tests for DataValidator"""
    
    @pytest.fixture
    def validator(self):
        from trading_bot.critical_fixes import DataValidator
        return DataValidator(
            max_price_change_pct=0.10,
            max_staleness_seconds=5,
            max_spread_pct=0.05
        )
    
    def test_valid_tick(self, validator):
        """Test validation of valid tick"""
        report = validator.validate_tick(
            symbol='EURUSD',
            bid=1.1000,
            ask=1.1002,
            timestamp=datetime.now()
        )
        
        assert report.is_usable is True
        assert report.quality_score >= 90
    
    def test_stale_data_detection(self, validator):
        """Test stale data is detected"""
        report = validator.validate_tick(
            symbol='EURUSD',
            bid=1.1000,
            ask=1.1002,
            timestamp=datetime.now() - timedelta(seconds=10)
        )
        
        assert any(i.issue_type.value == 'stale' for i in report.issues)
    
    def test_inverted_spread_detection(self, validator):
        """Test inverted spread is detected"""
        report = validator.validate_tick(
            symbol='EURUSD',
            bid=1.1010,  # bid > ask
            ask=1.1000,
            timestamp=datetime.now()
        )
        
        assert report.is_usable is False
        assert any(i.issue_type.value == 'spread_inverted' for i in report.issues)
    
    def test_price_spike_detection(self, validator):
        """Test price spike detection"""
        # Build history
        for price in [1.1000, 1.1001, 1.1002, 1.1001, 1.1000]:
            validator.validate_tick(
                symbol='EURUSD',
                bid=price,
                ask=price + 0.0002,
                timestamp=datetime.now()
            )
        
        # Large spike
        report = validator.validate_tick(
            symbol='EURUSD',
            bid=1.2000,  # 9% spike
            ask=1.2002,
            timestamp=datetime.now()
        )
        
        assert any(i.issue_type.value == 'price_spike' for i in report.issues)


class TestExecutionQualityMonitor:
    """Tests for ExecutionQualityMonitor"""
    
    @pytest.fixture
    def monitor(self):
        from trading_bot.critical_fixes import ExecutionQualityMonitor
        return ExecutionQualityMonitor(commission_rate=0.0001)
    
    def test_record_execution(self, monitor):
        """Test execution recording"""
        monitor.record_order_sent(
            order_id='order_001',
            symbol='EURUSD',
            direction='buy',
            quantity=0.1,
            expected_price=1.1000,
            order_type='market',
            venue='test'
        )
        
        record = monitor.record_execution(
            order_id='order_001',
            execution_id='exec_001',
            executed_price=1.1003,
            executed_quantity=0.1
        )
        
        assert record is not None
        assert record.slippage_bps == pytest.approx(2.7, rel=0.1)  # ~3 pips
    
    def test_slippage_model_update(self, monitor):
        """Test slippage model is updated"""
        for i in range(20):
            monitor.record_order_sent(
                order_id=f'order_{i}',
                symbol='EURUSD',
                direction='buy',
                quantity=0.1,
                expected_price=1.1000,
                order_type='market',
                venue='test'
            )
            
            monitor.record_execution(
                order_id=f'order_{i}',
                execution_id=f'exec_{i}',
                executed_price=1.1000 + (i % 5) * 0.0001,
                executed_quantity=0.1
            )
        
        expected = monitor.get_expected_slippage('EURUSD', 'market')
        
        assert expected['sample_size'] >= 10
        assert expected['confidence'] in ('medium', 'high')


class TestSilentFailureDetector:
    """Tests for SilentFailureDetector"""
    
    @pytest.fixture
    def detector(self):
        from trading_bot.critical_fixes import SilentFailureDetector
        return SilentFailureDetector(
            heartbeat_timeout=5,
            auto_remediate=False
        )
    
    def test_register_component(self, detector):
        """Test component registration"""
        detector.register_component(
            component_id='test_component',
            name='Test Component',
            heartbeat_interval=5,
            output_interval=10
        )
        
        health = detector.get_component_health('test_component')
        assert health is not None
        assert health.name == 'Test Component'
    
    def test_heartbeat_tracking(self, detector):
        """Test heartbeat tracking"""
        detector.register_component(
            component_id='test_component',
            name='Test Component',
            heartbeat_interval=5,
            output_interval=10
        )
        
        detector.heartbeat('test_component')
        
        health = detector.get_component_health('test_component')
        assert health.last_heartbeat is not None
    
    def test_output_recording(self, detector):
        """Test output recording"""
        detector.register_component(
            component_id='test_component',
            name='Test Component',
            heartbeat_interval=5,
            output_interval=10,
            expected_throughput=60
        )
        
        for i in range(10):
            detector.record_output('test_component', {'value': i}, latency_ms=5)
        
        health = detector.get_component_health('test_component')
        assert health.throughput_per_minute > 0


class TestConfigIntegrityMonitor:
    """Tests for ConfigIntegrityMonitor"""
    
    @pytest.fixture
    def monitor(self):
        from trading_bot.critical_fixes import ConfigIntegrityMonitor
        return ConfigIntegrityMonitor()
    
    def test_validate_valid_config(self, monitor):
        """Test validation of valid config"""
        config = {
            'max_risk_per_trade': 0.02,
            'max_drawdown': 0.20,
            'max_leverage': 2.0,
            'emergency_shutdown_drawdown': 0.25,
            'max_position_size': 0.10,
            'max_open_positions': 10,
            'trading_enabled': True,
            'trading_mode': 'paper',
            'kill_switch_enabled': True
        }
        
        errors = monitor.validate_config(config)
        critical_errors = [e for e in errors if e.severity == 'critical']
        
        assert len(critical_errors) == 0
    
    def test_validate_invalid_range(self, monitor):
        """Test validation catches out-of-range values"""
        config = {
            'max_risk_per_trade': 0.10,  # Above max (0.05)
            'max_drawdown': 0.20
        }
        
        errors = monitor.validate_config(config)
        
        assert any(e.parameter == 'max_risk_per_trade' for e in errors)
    
    def test_immutable_parameter_protection(self, monitor):
        """Test immutable parameters cannot be changed"""
        # First set a value
        monitor._current_config = {'emergency_shutdown_drawdown': 0.25}
        
        success, error = monitor.update_parameter(
            'emergency_shutdown_drawdown',
            0.50,
            source='test'
        )
        
        assert success is False
        assert 'immutable' in error.lower()


class TestRegulatoryComplianceMonitor:
    """Tests for RegulatoryComplianceMonitor"""
    
    @pytest.fixture
    def compliance(self, tmp_path):
        from trading_bot.critical_fixes import RegulatoryComplianceMonitor
        from trading_bot.critical_fixes.regulatory_compliance import RegulatoryRegime
        
        return RegulatoryComplianceMonitor(
            regime=RegulatoryRegime.SEC,
            db_path=str(tmp_path / "test_compliance.db")
        )
    
    def test_pre_trade_check_passes(self, compliance):
        """Test pre-trade check passes for valid trade"""
        can_trade, violations = compliance.check_pre_trade(
            symbol='AAPL',
            direction='buy',
            quantity=100,
            price=150.00,
            equity=30000,  # Above PDT threshold
            existing_position=0
        )
        
        # Should pass (no critical violations)
        critical = [v for v in violations if v.severity.value == 'critical']
        assert len(critical) == 0 or can_trade is True
    
    def test_position_limit_warning(self, compliance):
        """Test position limit generates warning"""
        can_trade, violations = compliance.check_pre_trade(
            symbol='AAPL',
            direction='buy',
            quantity=1000,
            price=150.00,
            equity=10000,  # Position would be 150% of equity
            existing_position=0
        )
        
        assert any(v.violation_type.value == 'position_limit' for v in violations)
    
    def test_trade_recording(self, compliance):
        """Test trade recording"""
        report = compliance.record_trade(
            trade_id='trade_001',
            symbol='AAPL',
            direction='buy',
            quantity=100,
            price=150.00,
            venue='NYSE',
            order_type='market',
            execution_time_ms=50
        )
        
        assert report.report_id == 'rpt_trade_001'
        assert report.symbol == 'AAPL'


class TestMasterSafetyOrchestrator:
    """Tests for MasterSafetyOrchestrator"""
    
    @pytest.fixture
    def orchestrator(self, tmp_path):
        from trading_bot.critical_fixes import MasterSafetyOrchestrator
        
        broker = MockBrokerAdapter()
        config = {
            'max_risk_per_trade': 0.02,
            'max_drawdown': 0.20,
            'emergency_shutdown_drawdown': 0.25,
            'equity': 10000
        }
        
        return MasterSafetyOrchestrator(
            broker_adapter=broker,
            config=config,
            db_path=str(tmp_path / "test_safety")
        )
    
    def test_initialization(self, orchestrator):
        """Test orchestrator initializes all components"""
        assert orchestrator.position_manager is not None
        assert orchestrator.risk_calculator is not None
        assert orchestrator.kill_switch is not None
        assert orchestrator.data_validator is not None
        assert orchestrator.execution_monitor is not None
        assert orchestrator.failure_detector is not None
        assert orchestrator.config_monitor is not None
    
    def test_validate_market_data(self, orchestrator):
        """Test market data validation through orchestrator"""
        report = orchestrator.validate_market_data(
            symbol='EURUSD',
            bid=1.1000,
            ask=1.1002,
            timestamp=datetime.now()
        )
        
        assert report.is_usable is True
    
    def test_update_equity(self, orchestrator):
        """Test equity update"""
        orchestrator.update_equity(15000)
        
        assert orchestrator.config['equity'] == 15000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
