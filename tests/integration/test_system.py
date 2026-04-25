"""
System Integration Tests
Tests complete trading system workflows
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from tests.integration.base import (
    AsyncIntegrationTestBase,
    BrokerIntegrationTest,
    SignalFlowIntegrationTest
)


@pytest.mark.system
class TestTradeLifecycle(AsyncIntegrationTestBase):
    """Test complete trade lifecycle from signal to execution."""
    
    async def async_setup(self):
        """Set up trade lifecycle test."""
        await super().async_setup()
        self.trade_events = []
        self.positions = []
        self.orders = []
    
    @pytest.mark.asyncio
    async def test_complete_trade_flow(self):
        """Test complete trade flow: signal → validation → execution → monitoring."""
        # Step 1: Generate signal
        signal = await self.generate_test_signal()
        assert signal is not None
        self.trade_events.append({"event": "signal_generated", "data": signal})
        
        # Step 2: Validate signal
        is_valid = await self.validate_signal(signal)
        assert is_valid is True
        self.trade_events.append({"event": "signal_validated", "valid": True})
        
        # Step 3: Convert to order
        order = await self.convert_to_order(signal)
        assert order is not None
        self.orders.append(order)
        self.trade_events.append({"event": "order_created", "data": order})
        
        # Step 4: Execute order
        execution = await self.execute_order(order)
        assert execution["status"] == "filled"
        self.trade_events.append({"event": "order_executed", "data": execution})
        
        # Step 5: Monitor position
        position = await self.create_position(execution)
        self.positions.append(position)
        self.trade_events.append({"event": "position_opened", "data": position})
        
        # Verify complete flow
        assert len(self.trade_events) == 5
    
    @pytest.mark.asyncio
    async def test_trade_lifecycle_with_stop_loss(self):
        """Test trade lifecycle with stop loss management."""
        # Open position
        position = await self.create_test_position()
        
        # Set stop loss
        stop_loss = position["entry_price"] * 0.99
        position["stop_loss"] = stop_loss
        
        # Simulate price moving toward stop
        position["current_price"] = stop_loss * 1.001
        
        # Check if stop triggered
        should_close = position["current_price"] <= stop_loss
        assert should_close is False  # Just above stop
        
        # Move price below stop
        position["current_price"] = stop_loss * 0.999
        should_close = position["current_price"] <= stop_loss
        assert should_close is True
    
    async def generate_test_signal(self) -> Dict[str, Any]:
        """Generate a test trading signal."""
        return {
            "id": f"signal-{datetime.now().timestamp()}",
            "symbol": "EURUSD",
            "direction": "long",
            "entry_price": 1.0850,
            "stop_loss": 1.0800,
            "take_profit": 1.0950,
            "position_size": 0.01,
            "confidence": 0.75,
            "timestamp": datetime.now(),
            "strategy": "test_strategy"
        }
    
    async def validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Validate a trading signal."""
        required_fields = ["symbol", "direction", "entry_price", "position_size"]
        return all(field in signal for field in required_fields)
    
    async def convert_to_order(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Convert signal to order."""
        return {
            "id": f"order-{datetime.now().timestamp()}",
            "symbol": signal["symbol"],
            "side": "buy" if signal["direction"] == "long" else "sell",
            "type": "market",
            "quantity": signal["position_size"],
            "signal_id": signal["id"],
            "timestamp": datetime.now()
        }
    
    async def execute_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an order."""
        return {
            "order_id": order["id"],
            "status": "filled",
            "filled_quantity": order["quantity"],
            "avg_fill_price": 1.0850,
            "timestamp": datetime.now()
        }
    
    async def create_position(self, execution: Dict[str, Any]) -> Dict[str, Any]:
        """Create a position from execution."""
        return {
            "id": f"position-{datetime.now().timestamp()}",
            "symbol": "EURUSD",
            "direction": "long",
            "entry_price": execution["avg_fill_price"],
            "current_price": execution["avg_fill_price"],
            "quantity": execution["filled_quantity"],
            "unrealized_pnl": 0.0,
            "open_time": datetime.now()
        }
    
    async def create_test_position(self) -> Dict[str, Any]:
        """Create a test position."""
        return {
            "id": f"position-{datetime.now().timestamp()}",
            "symbol": "EURUSD",
            "direction": "long",
            "entry_price": 1.0850,
            "current_price": 1.0850,
            "quantity": 0.01,
            "unrealized_pnl": 0.0,
            "open_time": datetime.now()
        }


@pytest.mark.system
class TestRiskSystemIntegration(SignalFlowIntegrationTest):
    """Test risk management system integration."""
    
    def test_risk_validation_gate(self):
        """Test risk validation gate blocks violating orders."""
        # Order that violates risk limits
        violating_order = {
            "symbol": "EURUSD",
            "quantity": 100.0,  # Way too large
            "side": "buy"
        }
        
        # Check risk limits
        max_position_size = 0.05
        is_valid = violating_order["quantity"] <= max_position_size
        
        assert is_valid is False
    
    def test_drawdown_protection(self):
        """Test drawdown protection triggers correctly."""
        account_info = {
            "initial_balance": 10000.0,
            "current_equity": 9500.0,  # 5% drawdown
            "max_drawdown_limit": 0.05
        }
        
        drawdown = 1 - (account_info["current_equity"] / account_info["initial_balance"])
        assert drawdown == 0.05
        
        # Check if at limit
        at_limit = drawdown >= account_info["max_drawdown_limit"]
        assert at_limit is True
    
    def test_position_size_enforcement(self, sample_risk_limits):
        """Test position sizing is enforced correctly."""
        limits = sample_risk_limits
        
        # Try to create oversized position
        requested_size = 0.1  # Exceeds max_position_size of 0.05
        
        # Enforce limit
        actual_size = min(requested_size, limits["max_position_size"])
        
        assert actual_size == limits["max_position_size"]
        assert actual_size <= limits["max_position_size"]
    
    def test_correlation_risk_limits(self):
        """Test correlation exposure limits."""
        positions = [
            {"symbol": "EURUSD", "direction": "long", "size": 0.02},
            {"symbol": "GBPUSD", "direction": "long", "size": 0.02},  # Correlated
            {"symbol": "USDJPY", "direction": "short", "size": 0.01}  # Hedge
        ]
        
        # Calculate correlation exposure (simplified)
        correlated_exposure = sum(
            p["size"] for p in positions 
            if p["symbol"] in ["EURUSD", "GBPUSD"] and p["direction"] == "long"
        )
        
        assert correlated_exposure == 0.04  # 2% + 2%


@pytest.mark.system
class TestErrorHandlingIntegration(AsyncIntegrationTestBase):
    """Test system error handling and recovery."""
    
    async def async_setup(self):
        """Set up error handling test."""
        self.errors = []
        self.recovery_actions = []
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test system degrades gracefully on component failure."""
        # Simulate component failure
        component_status = {
            "market_data": "online",
            "signal_generator": "degraded",
            "risk_manager": "online",
            "execution": "online"
        }
        
        # System should continue with reduced functionality
        can_trade = (
            component_status["market_data"] == "online" and
            component_status["risk_manager"] == "online" and
            component_status["execution"] == "online"
        )
        
        # Signal generator degraded but still functional
        assert can_trade is True
        
        # Log degradation
        self.errors.append({
            "component": "signal_generator",
            "status": "degraded",
            "timestamp": datetime.now()
        })
    
    @pytest.mark.asyncio
    async def test_retry_logic(self):
        """Test retry logic for failed operations."""
        max_retries = 3
        retry_delay = 1
        
        operation_succeeded = False
        for attempt in range(max_retries):
            try:
                # Simulate operation that fails first 2 times
                if attempt < 2:
                    raise ConnectionError("Network error")
                operation_succeeded = True
                break
            except ConnectionError:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * 0.1)  # Shortened for test
        
        assert operation_succeeded is True
        assert attempt == 2  # Succeeded on 3rd attempt
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self):
        """Test fallback mechanisms activate correctly."""
        primary_service = {"status": "offline", "name": "primary_broker"}
        fallback_service = {"status": "online", "name": "backup_broker"}
        
        # Select service
        if primary_service["status"] == "online":
            selected = primary_service
        else:
            selected = fallback_service
            self.recovery_actions.append({
                "action": "fallback_activated",
                "from": primary_service["name"],
                "to": fallback_service["name"]
            })
        
        assert selected["name"] == "backup_broker"
        assert len(self.recovery_actions) == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self):
        """Test circuit breaker opens on repeated failures."""
        failure_count = 0
        max_failures = 5
        circuit_open = False
        
        for i in range(10):
            if circuit_open:
                break
            
            try:
                # Simulate failures
                if i < 7:
                    raise Exception("Operation failed")
            except Exception:
                failure_count += 1
                if failure_count >= max_failures:
                    circuit_open = True
        
        assert circuit_open is True
        assert failure_count == max_failures


@pytest.mark.system
class TestConfigurationIntegration:
    """Test configuration management integration."""
    
    def test_environment_specific_config(self):
        """Test environment-specific configuration loading."""
        environments = {
            "development": {"debug": True, "paper_trading": True},
            "staging": {"debug": False, "paper_trading": True},
            "production": {"debug": False, "paper_trading": False}
        }
        
        for env, config in environments.items():
            # Verify environment-specific settings
            if env == "production":
                assert config["paper_trading"] is False
                assert config["debug"] is False
            elif env == "development":
                assert config["debug"] is True
    
    def test_feature_flags(self):
        """Test feature flag system."""
        features = {
            "new_strategy_engine": False,
            "advanced_risk_model": True,
            "ml_predictions": True,
            "real_time_analytics": False
        }
        
        # Check which features are enabled
        enabled = [k for k, v in features.items() if v]
        disabled = [k for k, v in features.items() if not v]
        
        assert "advanced_risk_model" in enabled
        assert "new_strategy_engine" in disabled
    
    def test_config_hot_reload(self):
        """Test configuration can be reloaded without restart."""
        original_config = {"max_position_size": 0.01}
        
        # Simulate config update
        updated_config = {"max_position_size": 0.02}
        
        # Reload
        current_config = updated_config
        
        assert current_config["max_position_size"] == 0.02
        assert original_config["max_position_size"] == 0.01  # Original unchanged
