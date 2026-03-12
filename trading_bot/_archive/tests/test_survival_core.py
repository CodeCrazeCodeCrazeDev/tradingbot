"""
from typing import Set
Unit tests for the SurvivalCore class.
"""

import unittest
import asyncio
from unittest.mock import MagicMock, patch
import tempfile
import os
from pathlib import Path
import json

from trading_bot.core.survival_core import SurvivalCore
from cryptography.fernet import Fernet


class TestSurvivalCore(unittest.TestCase):
    """Test cases for the SurvivalCore class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name) / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        # Create test encryption key
        self.key_file = self.config_dir / "encryption.key"
        self.key = Fernet.generate_key()
        with open(self.key_file, 'wb') as f:
            f.write(self.key)
        
        # Create test API keys file
        self.api_keys_file = self.config_dir / "api_keys.json"
        cipher = Fernet(self.key)
        encrypted_api_key = cipher.encrypt(b"test_api_key").decode()
        encrypted_api_secret = cipher.encrypt(b"test_api_secret").decode()
        
        api_keys = {
            "test_exchange": {
                "api_key": encrypted_api_key,
                "api_secret": encrypted_api_secret
            }
        }
        
        with open(self.api_keys_file, 'w') as f:
            json.dump(api_keys, f)
        
        # Create test config
        self.config = {
            'key_file': str(self.key_file),
            'api_keys_file': str(self.api_keys_file),
            'security': {
                'key_rotation_days': 30
            },
            'telegram': {
                'token': '',
                'chat_id': ''
            },
            'email': {},
            'symbols': ['EURUSD'],
            'timeframes': ['M5'],
            'risk_limits': {
                'max_position_size': 0.01,
                'max_daily_loss': 0.03
            }
        }
        
        # Mock dependencies
        self.mock_analysis = MagicMock()
        self.mock_execution = MagicMock()
        self.mock_monitoring = MagicMock()
        self.mock_data_stream = MagicMock()
        self.mock_time_series_db = MagicMock()
        
        # Apply patches
        self.patches = [
            patch('trading_bot.core.survival_core.AnalysisOrchestrator', return_value=self.mock_analysis),
            patch('trading_bot.core.survival_core.ExecutionManager', return_value=self.mock_execution),
            patch('trading_bot.core.survival_core.MonitoringSystem', return_value=self.mock_monitoring),
            patch('trading_bot.core.survival_core.MarketDataStream', return_value=self.mock_data_stream),
            patch('trading_bot.core.survival_core.TimeSeriesDB', return_value=self.mock_time_series_db),
            patch('trading_bot.core.survival_core.telegram.Bot')
        ]
        
        for p in self.patches:
            p.start()
    
    def tearDown(self):
        """Tear down test fixtures"""
        # Stop patches
        for p in self.patches:
            p.stop()
        
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_init(self):
        """Test initialization"""
        core = SurvivalCore(self.config)
        
        # Check that components were initialized
        self.assertIsNotNone(core.encryption_key)
        self.assertIsNotNone(core.cipher)
        self.assertIsNotNone(core.api_keys)
        self.assertIsNotNone(core.data_stream)
        self.assertIsNotNone(core.time_series_db)
        self.assertIsNotNone(core.analysis)
        self.assertIsNotNone(core.execution)
        self.assertIsNotNone(core.monitoring)
        
        # Check risk limits
        self.assertEqual(core.risk_limits['max_position_size'], 0.01)
        self.assertEqual(core.risk_limits['max_daily_loss'], 0.03)
        
        # Check system state
        self.assertFalse(core.running)
        self.assertFalse(core.paused)
        self.assertFalse(core.emergency_shutdown)
    
    def test_encrypt_decrypt(self):
        """Test encryption and decryption"""
        core = SurvivalCore(self.config)
        
        # Test encryption
        secret = "test_secret"
        encrypted = core._encrypt_secret(secret)
        self.assertNotEqual(encrypted, secret)
        
        # Test decryption
        decrypted = core._decrypt_secret(encrypted)
        self.assertEqual(decrypted, secret)
        
        # Test empty values
        self.assertEqual(core._encrypt_secret(""), "")
        self.assertEqual(core._decrypt_secret(""), "")
    
    def test_load_api_keys(self):
        """Test loading API keys"""
        core = SurvivalCore(self.config)
        
        # Check that API keys were loaded
        self.assertIn("test_exchange", core.api_keys)
        self.assertEqual(core.api_keys["test_exchange"]["api_key"], "test_api_key")
        self.assertEqual(core.api_keys["test_exchange"]["api_secret"], "test_api_secret")
    
    @patch('trading_bot.core.survival_core.Path.stat')
    def test_key_rotation(self, mock_stat):
        """Test key rotation"""
        # Mock file stat to trigger key rotation
        from datetime import datetime, timedelta
        old_time = (datetime.now() - timedelta(days=31)).timestamp()
        mock_stat.return_value.st_mtime = old_time
        
        # Initialize core to trigger key rotation
        core = SurvivalCore(self.config)
        
        # Check that a new key was generated
        with open(self.key_file, 'rb') as f:
            new_key = f.read()
        
        self.assertNotEqual(new_key, self.key)
    
    def test_get_system_status(self):
        """Test getting system status"""
        core = SurvivalCore(self.config)
        
        # Mock monitoring and execution responses
        self.mock_monitoring.get_system_status.return_value = {"status": "ok"}
        self.mock_execution.get_portfolio_status.return_value = {"account_balance": 10000}
        
        # Get system status
        status = core.get_system_status()
        
        # Check status
        self.assertIn("system", status)
        self.assertIn("monitoring", status)
        self.assertIn("portfolio", status)
        self.assertIn("risk_limits", status)
        self.assertEqual(status["portfolio"]["account_balance"], 10000)
        self.assertEqual(status["system"]["running"], False)
        self.assertEqual(status["system"]["paused"], False)
        self.assertEqual(status["system"]["emergency_shutdown"], False)


class TestSurvivalCoreAsync(unittest.IsolatedAsyncioTestCase):
    """Async test cases for the SurvivalCore class"""
    
    async def asyncSetUp(self):
        """Set up test fixtures"""
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name) / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        # Create test encryption key
        self.key_file = self.config_dir / "encryption.key"
        self.key = Fernet.generate_key()
        with open(self.key_file, 'wb') as f:
            f.write(self.key)
        
        # Create test config
        self.config = {
            'key_file': str(self.key_file),
            'api_keys_file': str(self.config_dir / "api_keys.json"),
            'symbols': ['EURUSD'],
            'timeframes': ['M5']
        }
        
        # Mock dependencies
        self.mock_analysis = MagicMock()
        self.mock_execution = MagicMock()
        self.mock_monitoring = MagicMock()
        self.mock_data_stream = MagicMock()
        self.mock_time_series_db = MagicMock()
        
        # Apply patches
        self.patches = [
            patch('trading_bot.core.survival_core.AnalysisOrchestrator', return_value=self.mock_analysis),
            patch('trading_bot.core.survival_core.ExecutionManager', return_value=self.mock_execution),
            patch('trading_bot.core.survival_core.MonitoringSystem', return_value=self.mock_monitoring),
            patch('trading_bot.core.survival_core.MarketDataStream', return_value=self.mock_data_stream),
            patch('trading_bot.core.survival_core.TimeSeriesDB', return_value=self.mock_time_series_db),
            patch('trading_bot.core.survival_core.telegram.Bot')
        ]
        
        for p in self.patches:
            p.start()
    
    async def asyncTearDown(self):
        """Tear down test fixtures"""
        # Stop patches
        for p in self.patches:
            p.stop()
        
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    async def test_start_stop(self):
        """Test starting and stopping the system"""
        core = SurvivalCore(self.config)
        
        # Mock async methods
        self.mock_data_stream.connect = MagicMock(return_value=asyncio.Future())
        self.mock_data_stream.connect.return_value.set_result(None)
        
        self.mock_data_stream.disconnect = MagicMock(return_value=asyncio.Future())
        self.mock_data_stream.disconnect.return_value.set_result(None)
        
        # Start system
        await core.start()
        
        # Check system state
        self.assertTrue(core.running)
        self.assertFalse(core.paused)
        self.assertTrue(hasattr(core, 'tasks'))
        
        # Check that data stream was connected
        self.mock_data_stream.connect.assert_called_once()
        
        # Stop system
        await core.stop()
        
        # Check system state
        self.assertFalse(core.running)
        
        # Check that data stream was disconnected
        self.mock_data_stream.disconnect.assert_called_once()
    
    async def test_pause_resume(self):
        """Test pausing and resuming the system"""
        core = SurvivalCore(self.config)
        
        # Mock async methods
        self.mock_data_stream.connect = MagicMock(return_value=asyncio.Future())
        self.mock_data_stream.connect.return_value.set_result(None)
        
        # Start system
        await core.start()
        
        # Pause system
        await core.pause()
        
        # Check system state
        self.assertTrue(core.running)
        self.assertTrue(core.paused)
        
        # Check that monitoring was updated
        self.mock_monitoring.update_component_status.assert_called_with(
            'system', 'ok', {'state': 'paused', 'pause_time': core.last_health_check.isoformat()}
        )
        
        # Resume system
        await core.resume()
        
        # Check system state
        self.assertTrue(core.running)
        self.assertFalse(core.paused)
        
        # Check that monitoring was updated
        self.mock_monitoring.update_component_status.assert_called_with(
            'system', 'ok', {'state': 'running', 'resume_time': core.last_health_check.isoformat()}
        )
    
    async def test_emergency_stop(self):
        """Test emergency stop"""
        core = SurvivalCore(self.config)
        
        # Mock async methods
        self.mock_data_stream.connect = MagicMock(return_value=asyncio.Future())
        self.mock_data_stream.connect.return_value.set_result(None)
        
        self.mock_data_stream.disconnect = MagicMock(return_value=asyncio.Future())
        self.mock_data_stream.disconnect.return_value.set_result(None)
        
        # Start system
        await core.start()
        
        # Emergency stop
        await core.emergency_stop()
        
        # Check system state
        self.assertFalse(core.running)
        self.assertTrue(core.emergency_shutdown)
        
        # Check that data stream was disconnected
        self.mock_data_stream.disconnect.assert_called_once()


if __name__ == '__main__':
    unittest.main()
