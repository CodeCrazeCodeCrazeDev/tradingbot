"""End-to-end workflow tests."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from trading_bot.validation.data_validator import DataQualityValidator, DataQualityMonitor
from trading_bot.risk.portfolio_risk_manager import PortfolioRiskManager
from trading_bot.error_handling.robust_error_handler import RobustErrorHandler


class TestCompleteTradeWorkflow:
    """Test complete trade workflow."""
    
    @pytest.fixture
    def validator(self):
        """Create validator."""
        return DataQualityValidator()
    
    @pytest.fixture
    def risk_manager(self):
        """Create risk manager."""
        config = {
            'max_var': 0.05,
            'max_cvar': 0.08,
            'max_drawdown': 0.15,
            'max_correlation_risk': 0.10,
            'max_sector_exposure': 0.25
        }
        return PortfolioRiskManager(config)
    
    @pytest.fixture
    def error_handler(self):
        """Create error handler."""
        return RobustErrorHandler()
    
    def test_workflow_data_validation(self, validator):
        """Test data validation in workflow."""
        ohlcv = {
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000,
            'time': datetime.now()
        }
        
        is_valid, issues = validator.validate_ohlcv(ohlcv)
        assert is_valid
        assert len(issues) == 0
    
    def test_workflow_risk_calculation(self, risk_manager):
        """Test risk calculation in workflow."""
        risk_manager.update_equity(10000.0)
        risk_manager.add_position('pos1', 'EURUSD', 1.0, 1.1000, 'forex')
        risk_manager.update_position_price('pos1', 1.1050)
        
        report = risk_manager.get_risk_report()
        assert report['is_safe'] is not None
        assert report['num_positions'] == 1
    
    @pytest.mark.asyncio
    async def test_workflow_error_recovery(self, error_handler):
        """Test error recovery in workflow."""
        call_count = 0
        
        async def trade_execution():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network error")
            return {'success': True, 'ticket': '123'}
        
        result = await error_handler.execute_with_retry(
            trade_execution,
            error_context="trade_execution"
        )
        
        assert result['success'] == True
        assert call_count == 2
    
    def test_workflow_position_lifecycle(self, risk_manager):
        """Test complete position lifecycle."""
        # 1. Add position
        risk_manager.add_position('pos1', 'EURUSD', 1.0, 1.1000, 'forex')
        assert 'pos1' in risk_manager.positions
        
        # 2. Update price (profit)
        risk_manager.update_position_price('pos1', 1.1050)
        # Use approximate comparison for floating point
        assert abs(risk_manager.positions['pos1']['pnl'] - 0.0050) < 1e-10
        
        # 3. Update equity
        risk_manager.update_equity(10050.0)
        assert risk_manager.current_equity == 10050.0
        
        # 4. Remove position
        risk_manager.remove_position('pos1')
        assert 'pos1' not in risk_manager.positions
    
    def test_workflow_multi_position_management(self, risk_manager):
        """Test managing multiple positions."""
        positions = [
            ('pos1', 'EURUSD', 1.0, 1.1000, 'forex'),
            ('pos2', 'GBPUSD', 1.0, 1.2500, 'forex'),
            ('pos3', 'AAPL', 100.0, 150.0, 'stocks'),
        ]
        
        # Add positions
        for pos_id, symbol, size, price, sector in positions:
            risk_manager.add_position(pos_id, symbol, size, price, sector)
        
        assert len(risk_manager.positions) == 3
        
        # Update prices
        risk_manager.update_position_price('pos1', 1.1050)
        risk_manager.update_position_price('pos2', 1.2600)
        risk_manager.update_position_price('pos3', 155.0)
        
        # Check total exposure
        total_exposure = risk_manager.calculate_total_exposure()
        expected = 1.0 * 1.1050 + 1.0 * 1.2600 + 100.0 * 155.0
        assert abs(total_exposure - expected) < 0.01
    
    def test_workflow_risk_monitoring(self, risk_manager):
        """Test risk monitoring workflow."""
        risk_manager.update_equity(10000.0)
        
        # Add positions
        for i in range(3):
            risk_manager.add_position(
                f'pos{i}',
                f'SYM{i}',
                1.0,
                100.0 + i,
                'forex'
            )
        
        # Get risk report
        report = risk_manager.get_risk_report()
        
        assert report['num_positions'] == 3
        assert 'violations' in report
        assert isinstance(report['violations'], list)


class TestDataQualityWorkflow:
    """Test data quality monitoring workflow."""
    
    @pytest.fixture
    def monitor(self):
        """Create monitor."""
        return DataQualityMonitor()
    
    def test_workflow_continuous_monitoring(self, monitor):
        """Test continuous data quality monitoring."""
        # Process multiple data points
        for i in range(10):
            ohlcv = {
                'open': 100.0 + i * 0.1,
                'high': 105.0 + i * 0.1,
                'low': 95.0 + i * 0.1,
                'close': 102.0 + i * 0.1,
                'volume': 1000 + i * 10,
                'time': datetime.now() + timedelta(minutes=i)
            }
            result = monitor.process_data(ohlcv)
            assert result['valid']
        
        # Check quality report
        report = monitor.get_quality_report()
        assert report['valid_records'] == 10
        assert report['invalid_records'] == 0
    
    def test_workflow_quality_degradation(self, monitor):
        """Test quality degradation detection."""
        # Process valid data
        for i in range(5):
            ohlcv = {
                'open': 100.0,
                'high': 105.0,
                'low': 95.0,
                'close': 102.0,
                'volume': 1000,
                'time': datetime.now() + timedelta(minutes=i)
            }
            monitor.process_data(ohlcv)
        
        score_before = monitor.quality_score
        
        # Process invalid data
        invalid_ohlcv = {
            'open': 100.0,
            'high': 95.0,  # Invalid
            'low': 90.0,
            'close': 102.0,
            'volume': 1000,
            'time': datetime.now() + timedelta(minutes=5)
        }
        monitor.process_data(invalid_ohlcv)
        
        score_after = monitor.quality_score
        assert score_after < score_before
    
    def test_workflow_staleness_detection(self, monitor):
        """Test staleness detection in workflow."""
        # Process fresh data
        ohlcv = {
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000,
            'time': datetime.now()
        }
        result = monitor.process_data(ohlcv)
        assert result['valid']
        assert len(result['warnings']) == 0


class TestErrorRecoveryWorkflow:
    """Test error recovery workflow."""
    
    @pytest.fixture
    def handler(self):
        """Create handler."""
        return RobustErrorHandler()
    
    @pytest.mark.asyncio
    async def test_workflow_connection_recovery(self, handler):
        """Test connection recovery workflow."""
        attempts = []
        
        async def unreliable_api():
            attempts.append(len(attempts) + 1)
            if len(attempts) < 3:
                raise ConnectionError("Connection failed")
            return "success"
        
        result = await handler.execute_with_retry(
            unreliable_api,
            error_context="api_call"
        )
        
        assert result == "success"
        assert len(attempts) == 3
    
    @pytest.mark.asyncio
    async def test_workflow_error_categorization(self, handler):
        """Test error categorization workflow."""
        errors = [
            (ConnectionError("Network error"), ["connection", "network"]),
            (ValueError("Invalid data"), ["data", "unknown"]),
            (TimeoutError("Request timeout"), ["timeout", "connection"]),
        ]
        
        for error, expected_types in errors:
            error_type = handler.categorize_error(error)
            assert error_type.value in expected_types
    
    @pytest.mark.asyncio
    async def test_workflow_error_history(self, handler):
        """Test error history tracking workflow."""
        # Generate multiple errors
        for i in range(5):
            error = Exception(f"Error {i}")
            await handler.handle_error(error, f"context{i}")
        
        report = handler.get_error_report()
        assert report['total_errors'] == 5
        assert 'recovery_rate' in report


class TestIntegrationWorkflow:
    """Test integrated workflow across multiple systems."""
    
    def test_workflow_data_to_risk(self):
        """Test workflow from data validation to risk calculation."""
        # 1. Validate data
        validator = DataQualityValidator()
        ohlcv = {
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000,
            'time': datetime.now()
        }
        is_valid, issues = validator.validate_ohlcv(ohlcv)
        assert is_valid
        
        # 2. Use data for risk calculation
        risk_manager = PortfolioRiskManager()
        risk_manager.update_equity(10000.0)
        risk_manager.add_position('pos1', 'EURUSD', 1.0, 102.0, 'forex')
        
        # 3. Get risk report
        report = risk_manager.get_risk_report()
        assert report['num_positions'] == 1
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling_integration(self):
        """Test error handling integrated with other systems."""
        handler = RobustErrorHandler()
        risk_manager = PortfolioRiskManager()
        
        # Simulate workflow with error recovery
        async def workflow():
            try:
                # Add position
                risk_manager.add_position('pos1', 'EURUSD', 1.0, 1.1000, 'forex')
                
                # Get risk report (might fail)
                report = risk_manager.get_risk_report()
                return report
            except Exception as e:
                await handler.handle_error(e, "workflow")
                raise
        
        result = await handler.execute_with_retry(
            workflow,
            error_context="integrated_workflow"
        )
        
        assert result is not None
    
    def test_workflow_complete_cycle(self):
        """Test complete workflow cycle."""
        # Initialize systems
        validator = DataQualityValidator()
        monitor = DataQualityMonitor()
        risk_manager = PortfolioRiskManager()
        
        # 1. Validate and monitor data
        ohlcv = {
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000,
            'time': datetime.now()
        }
        
        is_valid, _ = validator.validate_ohlcv(ohlcv)
        assert is_valid
        
        monitor_result = monitor.process_data(ohlcv)
        assert monitor_result['valid']
        
        # 2. Update risk manager
        risk_manager.update_equity(10000.0)
        risk_manager.add_position('pos1', 'EURUSD', 1.0, 102.0, 'forex')
        
        # 3. Get reports
        quality_report = monitor.get_quality_report()
        risk_report = risk_manager.get_risk_report()
        
        assert quality_report['quality_score'] > 0
        assert risk_report['num_positions'] == 1
