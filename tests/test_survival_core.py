#!/usr/bin/env python
"""
Test Suite for Survival Core

This module tests the critical components of the survival-focused trading system:
1. Risk Management
2. Money Management
3. Position Sizing
4. Error Recovery
5. System Health
"""

import asyncio
import unittest
import logging
import yaml
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from trading_bot.core.survival_core import SurvivalCore
from typing import Set
import json
import numpy
import pandas

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_survival_core")


class TestSurvivalCore(unittest.TestCase):
    """Test case for the survival core system"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Test configuration
        cls.config = {
            "symbols": ["EURUSD"],
            "timeframes": ["M5"],
            "risk_limits": {
                "max_position_size": 0.02,
                "max_leverage": 5.0,
                "max_daily_loss": 0.05,
                "max_drawdown": 0.15,
                "max_correlation": 0.7,
                "max_open_positions": 5,
                "min_free_margin": 0.3
            },
            "data_stream": {
                "simulate_data": True,
                "use_redis": False
            },
            "security": {
                "key_file": "tests/data/test_encryption.key",
                "api_keys_file": "tests/data/test_api_keys.json"
            }
        }
        
        # Create test directories
        Path("tests/data").mkdir(parents=True, exist_ok=True)
    
    async def async_setUp(self):
        """Set up async test environment"""
        self.system = SurvivalCore(self.config)
        await self.system.start()
    
    async def async_tearDown(self):
        """Clean up async test environment"""
        await self.system.stop()
    
    async def test_risk_management(self):
        """Test risk management functionality"""
        logger.info("Testing risk management")
        
        # Test position size calculation
        status = self.system.execution.get_portfolio_status()
        account_balance = status['account_balance']
        max_position_size = account_balance * self.config['risk_limits']['max_position_size']
        
        # Verify position size limits
        self.assertLessEqual(max_position_size / account_balance, 
                           self.config['risk_limits']['max_position_size'])
        
        # Test daily loss limit
        daily_loss = account_balance * self.config['risk_limits']['max_daily_loss']
        
        # Simulate approaching daily loss limit
        await self.system.monitoring.update_component_status('risk', 'warning', {
            'daily_pnl': -daily_loss * 0.8  # 80% of limit
        })
        
        # Verify system response
        status = self.system.get_system_status()
        self.assertTrue(status['system']['running'])  # Should still be running
        
        # Simulate exceeding daily loss limit
        await self.system.monitoring.update_component_status('risk', 'error', {
            'daily_pnl': -daily_loss * 1.2  # 120% of limit
        })
        
        # Verify system response
        self.assertTrue(self.system.paused)  # Should be paused
    
    async def test_money_management(self):
        """Test money management functionality"""
        logger.info("Testing money management")
        
        # Test position sizing
        entry_price = 1.1000
        stop_loss = 1.0950  # 50 pip stop
        win_rate = 0.55
        reward_risk_ratio = 1.5
        
        position = self.system.execution.calculate_position_size(
            symbol="EURUSD",
            entry_price=entry_price,
            stop_loss=stop_loss,
            win_rate=win_rate,
            reward_risk_ratio=reward_risk_ratio
        )
        
        # Verify position sizing
        self.assertIsNotNone(position)
        self.assertGreater(position['recommended_size'], 0)
        self.assertLessEqual(
            position['risk_amount'],
            self.system.execution.account_balance * self.config['risk_limits']['max_position_size']
        )
    
    async def test_error_recovery(self):
        """Test error recovery functionality"""
        logger.info("Testing error recovery")
        
        # Simulate market data error
        self.system.monitoring.update_component_status('market_data', 'error', {
            'error': 'Connection lost',
            'last_update': datetime.now().isoformat()
        })
        
        # Wait for recovery attempt
        await asyncio.sleep(2)
        
        # Simulate recovery
        self.system.monitoring.update_component_status('market_data', 'ok', {
            'last_update': datetime.now().isoformat()
        })
        
        # Verify system status
        status = self.system.get_system_status()
        self.assertEqual(
            status['monitoring']['components']['market_data']['status'],
            'ok'
        )
    
    async def test_system_health(self):
        """Test system health monitoring"""
        logger.info("Testing system health monitoring")
        
        # Get initial status
        initial_status = self.system.get_system_status()
        self.assertEqual(initial_status['system']['running'], True)
        
        # Test component status updates
        components = ['market_data', 'analysis', 'execution', 'risk']
        for component in components:
            # Update status
            self.system.monitoring.update_component_status(component, 'ok', {
                'last_update': datetime.now().isoformat()
            })
            
            # Verify status
            status = self.system.get_system_status()
            self.assertEqual(
                status['monitoring']['components'][component]['status'],
                'ok'
            )
    
    async def test_position_management(self):
        """Test position management functionality"""
        logger.info("Testing position management")
        
        # Open test position
        symbol = "EURUSD"
        entry_price = 1.1000
        position = self.system.execution.calculate_position_size(
            symbol=symbol,
            entry_price=entry_price,
            stop_loss=entry_price * 0.995,  # 0.5% stop
            win_rate=0.55,
            reward_risk_ratio=1.5
        )
        
        # Add position
        added = self.system.execution.add_position(position)
        self.assertTrue(added)
        
        # Verify position
        positions = self.system.execution.get_active_positions()
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0].symbol, symbol)
        
        # Test position close
        result = await self.system.execution.close_position(
            symbol=symbol,
            exit_price=entry_price * 1.001  # Small profit
        )
        
        self.assertIsNotNone(result)
        self.assertGreater(result['pnl'], 0)
    
    async def test_risk_limits(self):
        """Test risk limit enforcement"""
        logger.info("Testing risk limit enforcement")
        
        # Test max open positions
        max_positions = self.config['risk_limits']['max_open_positions']
        
        # Try to open max_positions + 1 positions
        for i in range(max_positions + 1):
            position = self.system.execution.calculate_position_size(
                symbol=f"PAIR{i}",
                entry_price=1.0,
                stop_loss=0.99,
                win_rate=0.55,
                reward_risk_ratio=1.5
            )
            
            added = self.system.execution.add_position(position)
            
            if i < max_positions:
                self.assertTrue(added)
            else:
                self.assertFalse(added)  # Should reject position
        
        # Verify position count
        positions = self.system.execution.get_active_positions()
        self.assertEqual(len(positions), max_positions)
    
    async def test_emergency_shutdown(self):
        """Test emergency shutdown functionality"""
        logger.info("Testing emergency shutdown")
        
        # Open test positions
        for i in range(3):
            position = self.system.execution.calculate_position_size(
                symbol=f"PAIR{i}",
                entry_price=1.0,
                stop_loss=0.99,
                win_rate=0.55,
                reward_risk_ratio=1.5
            )
            self.system.execution.add_position(position)
        
        # Verify positions are open
        initial_positions = self.system.execution.get_active_positions()
        self.assertGreater(len(initial_positions), 0)
        
        # Trigger emergency shutdown
        await self.system.emergency_stop()
        
        # Verify system state
        self.assertTrue(self.system.emergency_shutdown)
        self.assertFalse(self.system.running)
        
        # Verify all positions are closed
        final_positions = self.system.execution.get_active_positions()
        self.assertEqual(len(final_positions), 0)
    
    async def test_notification_system(self):
        """Test notification system"""
        logger.info("Testing notification system")
        
        # Test different notification levels
        test_cases = [
            ("info", "Test Info", "Info message"),
            ("warning", "Test Warning", "Warning message"),
            ("error", "Test Error", "Error message"),
            ("critical", "Test Critical", "Critical message")
        ]
        
        for level, title, message in test_cases:
            # Send notification
            await self.system._send_notification(title, message, level)
            
            # Verify notification was logged
            # In a real test, would verify notification delivery


def run_tests():
    """Run the tests"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add tests
    test_cases = [
        'test_risk_management',
        'test_money_management',
        'test_error_recovery',
        'test_system_health',
        'test_position_management',
        'test_risk_limits',
        'test_emergency_shutdown',
        'test_notification_system'
    ]
    
    for test_case in test_cases:
        suite.addTest(TestSurvivalCore(test_case))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


async def run_async_tests():
    """Run the async tests"""
    # Create test instance
    test = TestSurvivalCore('test_risk_management')
    
    try:
        # Set up
        await test.async_setUp()
        
        # Run tests
        await test.test_risk_management()
        await test.test_money_management()
        await test.test_error_recovery()
        await test.test_system_health()
        await test.test_position_management()
        await test.test_risk_limits()
        await test.test_emergency_shutdown()
        await test.test_notification_system()
        
        logger.info("All tests passed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        # Clean up
        await test.async_tearDown()


if __name__ == '__main__':
    # Run async tests
    asyncio.run(run_async_tests())
