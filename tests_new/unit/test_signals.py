"""
Unit Tests for Signal System
============================
Tests for signal generation and management.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock


@pytest.mark.unit
class TestSignalSystem:
    """Test signal system functionality."""
    
    def test_signal_system_initialization(self, signal_system):
        """Test signal system initializes correctly."""
        assert signal_system is not None
    
    def test_signal_validation(self, sample_signal, assert_valid_signal):
        """Test signal structure validation."""
        assert assert_valid_signal(sample_signal)
    
    def test_signal_confidence_bounds(self, sample_signal):
        """Test signal confidence is within bounds."""
        assert 0 <= sample_signal['confidence'] <= 1
    
    def test_signal_has_required_fields(self, sample_signal):
        """Test signal has all required fields."""
        required = ['signal_id', 'symbol', 'direction', 'confidence', 
                   'entry_price', 'stop_loss', 'take_profit']
        
        for field in required:
            assert field in sample_signal, f"Missing field: {field}"


@pytest.mark.unit
class TestSignalLifecycle:
    """Test signal lifecycle management."""
    
    def test_signal_lifecycle_manager_init(self):
        """Test signal lifecycle manager initialization."""
        from trading_bot.signals import SignalLifecycleManager
        
        manager = SignalLifecycleManager()
        assert manager is not None
    
    def test_signal_provenance(self):
        """Test signal provenance tracking."""
        from trading_bot.signals import SignalProvenance
        
        provenance = SignalProvenance()
        assert provenance is not None


@pytest.mark.unit
class TestAdaptiveThresholds:
    """Test adaptive threshold system."""
    
    def test_adaptive_thresholds_init(self):
        """Test adaptive thresholds initialization."""
        from trading_bot.signals import AdaptiveThresholds
        
        thresholds = AdaptiveThresholds()
        assert thresholds is not None


@pytest.mark.unit  
class TestSignalHealthMonitor:
    """Test signal health monitoring."""
    
    def test_health_monitor_init(self):
        """Test signal health monitor initialization."""
        from trading_bot.signals import SignalHealthMonitor
        
        monitor = SignalHealthMonitor()
        assert monitor is not None
