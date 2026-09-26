"""
Integration tests for AlphaAlgo V2

Tests the complete trading workflow.
"""

import pytest
import asyncio
import uuid
from datetime import datetime

from ..orchestrator import AlphaAlgoOrchestrator, quick_start, SystemState
from ..core.constants import SafetyLevel, TradingMode

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



class TestAlphaAlgoOrchestrator:
    """Integration tests for main orchestrator"""
    
    @pytest.fixture
    def config(self):
        return {
            "mode": "paper",
            "initial_balance": 10000,
        }
    
    @pytest.mark.asyncio
    async def test_quick_start(self, config):
        """Test quick start"""
        orchestrator = await quick_start(config)
        
        assert orchestrator is not None
        assert orchestrator.state == SystemState.READY
        
        await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_initialize(self, config):
        """Test initialization"""
        orchestrator = AlphaAlgoOrchestrator(config)
        result = await orchestrator.initialize()
        
        assert result is True
        assert orchestrator.state == SystemState.READY
        
        await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_start_stop_trading(self, config):
        """Test start and stop trading"""
        orchestrator = AlphaAlgoOrchestrator(config)
        await orchestrator.initialize()
        
        # Start trading
        result = await orchestrator.start_trading(["EURUSD"])
        assert result is True
        assert orchestrator.is_trading
        
        # Stop trading
        result = await orchestrator.stop_trading()
        assert result is True
        assert not orchestrator.is_trading
        
        await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_emergency_stop(self, config):
        """Test emergency stop"""
        orchestrator = AlphaAlgoOrchestrator(config)
        await orchestrator.initialize()
        await orchestrator.start_trading(["EURUSD"])
        
        # Emergency stop
        result = await orchestrator.emergency_stop()
        
        assert result is True
        assert orchestrator.state == SystemState.EMERGENCY
        assert orchestrator.safety_level == SafetyLevel.BLACK
        
        await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_pause_resume(self, config):
        """Test pause and resume"""
        orchestrator = AlphaAlgoOrchestrator(config)
        await orchestrator.initialize()
        await orchestrator.start_trading(["EURUSD"])
        
        # Pause
        orchestrator.pause_trading()
        assert orchestrator.state == SystemState.PAUSED
        
        # Resume
        orchestrator.resume_trading()
        assert orchestrator.state == SystemState.TRADING
        
        await orchestrator.stop_trading()
        await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_safety_level(self, config):
        """Test safety level changes"""
        orchestrator = AlphaAlgoOrchestrator(config)
        await orchestrator.initialize()
        
        orchestrator.set_safety_level(SafetyLevel.YELLOW)
        assert orchestrator.safety_level == SafetyLevel.YELLOW
        
        orchestrator.set_safety_level(SafetyLevel.GREEN)
        assert orchestrator.safety_level == SafetyLevel.GREEN
        
        await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_get_status(self, config):
        """Test status retrieval"""
        orchestrator = AlphaAlgoOrchestrator(config)
        await orchestrator.initialize()
        
        status = orchestrator.get_status()
        
        assert "state" in status
        assert "mode" in status
        assert "safety_level" in status
        assert "session" in status
        
        await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_get_performance(self, config):
        """Test performance retrieval"""
        orchestrator = AlphaAlgoOrchestrator(config)
        await orchestrator.initialize()
        await orchestrator.start_trading(["EURUSD"])
        
        performance = orchestrator.get_performance()
        
        assert "total_trades" in performance
        
        await orchestrator.stop_trading()
        await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_evolution_cycle(self, config):
        """Test evolution cycle"""
        orchestrator = AlphaAlgoOrchestrator(config)
        await orchestrator.initialize()
        
        result = await orchestrator.run_evolution_cycle()
        
        assert "cycle_id" in result
        assert "proposals" in result
        
        await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_mode(self, config):
        """Test trading mode"""
        orchestrator = AlphaAlgoOrchestrator(config)
        
        assert orchestrator.mode == TradingMode.PAPER


class TestFullWorkflow:
    """End-to-end workflow tests"""
    
    @pytest.mark.asyncio
    async def test_complete_trading_session(self):
        """Test complete trading session"""
        config = {
            "mode": "paper",
            "initial_balance": 10000,
        }
        
        # Initialize
        orchestrator = await quick_start(config)
        assert orchestrator.state == SystemState.READY
        
        # Start trading
        await orchestrator.start_trading(["EURUSD", "GBPUSD"])
        assert orchestrator.is_trading
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        # Check status
        status = orchestrator.get_status()
        assert status["state"] == "trading"
        
        # Stop trading
        await orchestrator.stop_trading()
        assert not orchestrator.is_trading
        
        # Get final performance
        performance = orchestrator.get_performance()
        assert performance is not None
        
        # Shutdown
        await orchestrator.shutdown()
        assert orchestrator.state == SystemState.SHUTDOWN


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
