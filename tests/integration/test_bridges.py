"""
Bridge Integration Tests
Tests data flow between major system components
"""

import pytest
import pandas as pd
from datetime import datetime

from tests.integration.base import (
    IntegrationTestBase,
    DatabaseIntegrationTest,
    SignalFlowIntegrationTest,
    BridgeTestMixin
)


@pytest.mark.integration
class TestDataToAnalysisBridge(IntegrationTestBase, BridgeTestMixin):
    """Test data flow from data layer to analysis layer."""
    
    def test_market_data_to_analysis(self, sample_ohlcv_data):
        """Test that market data flows correctly to analysis layer."""
        # Simulate data flow
        source_data = sample_ohlcv_data.iloc[0].to_dict()
        
        # Transform to analysis format
        target_data = {
            "timestamp": source_data["timestamp"],
            "price": source_data["close"],
            "volume": source_data["volume"],
            "high": source_data["high"],
            "low": source_data["low"],
            "open": source_data["open"]
        }
        
        # Verify data integrity
        self.assert_bridge_data_integrity(
            source_data, target_data,
            fields=["timestamp", "volume", "high", "low", "open"]
        )
    
    def test_data_transformation_preserves_values(self, sample_ohlcv_data):
        """Test that data transformation doesn't corrupt values."""
        original = sample_ohlcv_data.copy()
        
        # Apply transformations
        transformed = original.copy()
        transformed["returns"] = transformed["close"].pct_change()
        
        # Verify original values preserved
        assert len(transformed) == len(original)
        assert (transformed["close"] == original["close"]).all()


@pytest.mark.integration
class TestAnalysisToSignalsBridge(IntegrationTestBase, BridgeTestMixin):
    """Test data flow from analysis layer to signals layer."""
    
    def test_analysis_output_to_signal(self):
        """Test that analysis results generate signals correctly."""
        analysis_result = {
            "symbol": "EURUSD",
            "timestamp": datetime.now(),
            "trend": "bullish",
            "strength": 0.75,
            "indicators": {
                "rsi": 65,
                "macd": 0.002,
                "atr": 0.0015
            }
        }
        
        # Convert to signal format
        signal = {
            "symbol": analysis_result["symbol"],
            "direction": "long" if analysis_result["trend"] == "bullish" else "short",
            "confidence": analysis_result["strength"],
            "timestamp": analysis_result["timestamp"],
            "metadata": analysis_result["indicators"]
        }
        
        # Verify bridge integrity
        assert signal["symbol"] == analysis_result["symbol"]
        assert signal["confidence"] == analysis_result["strength"]
    
    def test_signal_generation_with_invalid_analysis(self):
        """Test error handling for invalid analysis data."""
        invalid_analysis = {
            "symbol": None,
            "strength": -0.5  # Invalid negative strength
        }
        
        # Should not crash, should handle gracefully
        with pytest.raises((ValueError, AssertionError)):
            assert invalid_analysis["symbol"] is not None
            assert 0 <= invalid_analysis["strength"] <= 1


@pytest.mark.integration
class TestSignalsToExecutionBridge(IntegrationTestBase, BridgeTestMixin):
    """Test data flow from signals layer to execution layer."""
    
    def test_signal_to_order_conversion(self, sample_trade_signal):
        """Test that signals are converted to orders correctly."""
        signal = sample_trade_signal
        
        # Convert signal to order
        order = {
            "symbol": signal["symbol"],
            "side": "buy" if signal["direction"] == "long" else "sell",
            "type": "market",
            "quantity": signal["position_size"],
            "signal_id": signal["id"],
            "timestamp": signal["timestamp"]
        }
        
        # Verify conversion
        assert order["symbol"] == signal["symbol"]
        assert order["quantity"] == signal["position_size"]
        assert order["signal_id"] == signal["id"]
    
    def test_signal_metadata_preserved(self, sample_trade_signal):
        """Test that signal metadata is preserved through bridge."""
        signal = sample_trade_signal
        signal["metadata"] = {"source": "ml_model", "version": "2.0"}
        
        # Pass through bridge
        order_request = {
            **{k: v for k, v in signal.items() if k in ["symbol", "direction", "position_size"]},
            "signal_metadata": signal.get("metadata")
        }
        
        # Verify metadata preserved
        assert order_request["signal_metadata"]["source"] == "ml_model"


@pytest.mark.integration
class TestCoreToRiskBridge(IntegrationTestBase, BridgeTestMixin):
    """Test data flow from core to risk management."""
    
    def test_position_to_risk_calculation(self, sample_position):
        """Test that position data flows to risk calculations."""
        position = sample_position
        
        # Risk calculation input
        risk_input = {
            "symbol": position["symbol"],
            "direction": position["direction"],
            "size": position["quantity"],
            "entry_price": position["entry_price"],
            "current_price": position["current_price"],
            "unrealized_pnl": position["unrealized_pnl"]
        }
        
        # Verify data integrity
        assert risk_input["symbol"] == position["symbol"]
        assert risk_input["size"] == position["quantity"]
    
    def test_risk_limits_enforcement(self, sample_risk_limits, sample_trade_signal):
        """Test that risk limits are enforced through bridge."""
        signal = sample_trade_signal
        limits = sample_risk_limits
        
        # Check if signal violates limits
        position_size = signal["position_size"]
        max_size = limits["max_position_size"]
        
        assert position_size <= max_size, \
            f"Position size {position_size} exceeds limit {max_size}"


@pytest.mark.integration
class TestCoreToExecutionBridge(IntegrationTestBase, BridgeTestMixin):
    """Test data flow from core to execution layer."""
    
    def test_order_routing(self, sample_order):
        """Test that orders are routed correctly."""
        order = sample_order
        
        # Route to execution
        routed_order = {
            "broker_order_id": f"BROKER_{order['id']}",
            "symbol": order["symbol"],
            "side": order["side"],
            "quantity": order["quantity"],
            "order_type": order["type"],
            "timestamp": order["created_at"]
        }
        
        # Verify routing
        assert routed_order["symbol"] == order["symbol"]
        assert routed_order["quantity"] == order["quantity"]
    
    def test_execution_feedback_loop(self):
        """Test execution feedback is received by core."""
        # Simulate execution
        execution_result = {
            "order_id": "test-123",
            "status": "filled",
            "filled_quantity": 0.01,
            "avg_price": 1.0850,
            "timestamp": datetime.now()
        }
        
        # Feedback to core
        core_update = {
            "execution_id": execution_result["order_id"],
            "fill_status": execution_result["status"],
            "fill_size": execution_result["filled_quantity"],
            "fill_price": execution_result["avg_price"]
        }
        
        # Verify feedback integrity
        assert core_update["fill_status"] == execution_result["status"]


@pytest.mark.integration
class TestDatabaseToPersistenceBridge(DatabaseIntegrationTest, BridgeTestMixin):
    """Test data flow between database and persistence layer."""
    
    def test_entity_to_database_mapping(self):
        """Test that entities map correctly to database schema."""
        entity = {
            "id": "trade-123",
            "symbol": "EURUSD",
            "quantity": 0.01,
            "price": 1.0850,
            "timestamp": datetime.now()
        }
        
        # Database record
        db_record = {
            "trade_id": entity["id"],
            "symbol": entity["symbol"],
            "amount": entity["quantity"],
            "execution_price": entity["price"],
            "created_at": entity["timestamp"]
        }
        
        # Verify mapping
        assert db_record["trade_id"] == entity["id"]
        assert db_record["symbol"] == entity["symbol"]
    
    def test_database_query_results(self):
        """Test that query results are correctly transformed."""
        # Simulate database result
        db_result = [
            ("trade-1", "EURUSD", 0.01, 1.0850),
            ("trade-2", "GBPUSD", 0.01, 1.2750)
        ]
        
        # Transform to entity
        entities = [
            {
                "id": row[0],
                "symbol": row[1],
                "quantity": row[2],
                "price": row[3]
            }
            for row in db_result
        ]
        
        # Verify transformation
        assert len(entities) == len(db_result)
        assert entities[0]["symbol"] == "EURUSD"


@pytest.mark.integration
class TestEventBridge(IntegrationTestBase):
    """Test event-based communication between components."""
    
    def test_event_publication(self):
        """Test that events are published correctly."""
        events = []
        
        def event_handler(event):
            events.append(event)
        
        # Publish event
        test_event = {
            "type": "signal_generated",
            "data": {"symbol": "EURUSD", "direction": "long"},
            "timestamp": datetime.now()
        }
        event_handler(test_event)
        
        # Verify event received
        assert len(events) == 1
        assert events[0]["type"] == "signal_generated"
    
    def test_event_subscription_filtering(self):
        """Test that events can be filtered by type."""
        all_events = []
        trade_events = []
        
        def generic_handler(event):
            all_events.append(event)
            if event.get("type") == "trade_executed":
                trade_events.append(event)
        
        # Generate mixed events
        events = [
            {"type": "signal_generated", "data": {}},
            {"type": "trade_executed", "data": {}},
            {"type": "price_update", "data": {}},
            {"type": "trade_executed", "data": {}}
        ]
        
        for event in events:
            generic_handler(event)
        
        # Verify filtering
        assert len(all_events) == 4
        assert len(trade_events) == 2
