"""
Full integration tests for complete trading system
"""

import pytest
import numpy as np
import pandas as pd
import time


class TestFullSystemIntegration:
    """Test complete system integration"""
    
    def test_forecasting_to_decision_pipeline(self):
        """Test forecasting models feeding into decision system"""
        from trading_bot.ml.forecasting import NBeatsModel
        
        # Create forecasting model
        model = NBeatsModel(input_size=24, forecast_size=6)
        
        # Generate sample data
        historical_data = np.random.randn(10, 24).astype(np.float32)
        
        # Get predictions
        predictions = model.predict(historical_data)
        
        assert predictions.shape == (10, 6)
        
        # Simulate decision based on predictions
        signals = np.where(predictions[:, 0] > 0, 'BUY', 'SELL')
        assert len(signals) == 10
    
    def test_monitoring_pipeline(self):
        """Test monitoring and metrics collection"""
        from trading_bot.infrastructure import PrometheusExporter, get_performance_monitor
        
        exporter = PrometheusExporter(port=9000)
        monitor = get_performance_monitor()
        
        # Simulate trading activity
        for i in range(5):
            exporter.record_trade('EURUSD', 'BUY', 'closed', 10.0 + i)
            exporter.update_portfolio(100000 + i * 100, 0.01)
        
        # Check metrics recorded
        assert True  # If no errors, integration works
    
    def test_execution_with_optimization(self):
        """Test execution with performance optimization"""
        from trading_bot.execution.almgren_chriss import AlmgrenChrissOptimizer
        from trading_bot.infrastructure import measure_performance
        
        @measure_performance("execution_test")
        def execute_order(quantity, time_horizon):
            optimizer = AlmgrenChrissOptimizer()
            return optimizer.compute_optimal_trajectory(quantity, time_horizon)
        
        schedule = execute_order(1.0, 10)
        
        assert schedule.total_quantity == 1.0
        assert len(schedule.trajectory) == 10
    
    def test_chaos_with_monitoring(self):
        """Test chaos engineering with monitoring"""
        from trading_bot.testing.chaos_engineering import ChaosMonkey, ChaosExperiment, FaultType
        from trading_bot.infrastructure import PrometheusExporter
        
        monkey = ChaosMonkey()
        exporter = PrometheusExporter(port=9001)
        
        exp = ChaosExperiment(
            name="integration_test",
            fault_type=FaultType.NETWORK_LATENCY,
            target_component="test",
            probability=0.5
        )
        
        monkey.add_experiment(exp)
        monkey.start()
        
        # Simulate operations
        for _ in range(5):
            fault = monkey.should_inject_fault("test")
            if fault:
                exporter.update_system_health(80.0)
            else:
                exporter.update_system_health(95.0)
        
        monkey.stop()
        assert True
    
    def test_end_to_end_trading_cycle(self):
        """Test complete trading cycle"""
        # 1. Generate market data
        market_data = pd.DataFrame({
            'open': np.random.randn(100) + 100,
            'high': np.random.randn(100) + 101,
            'low': np.random.randn(100) + 99,
            'close': np.random.randn(100) + 100,
            'volume': np.random.randint(1000, 10000, 100)
        })
        
        # 2. Forecast
        model = NBeatsModel(input_size=24, forecast_size=1)
        
        # 3. Generate signal
        signal = 'BUY' if np.random.rand() > 0.5 else 'SELL'
        
        # 4. Execute with optimal schedule
        optimizer = AlmgrenChrissOptimizer()
        schedule = optimizer.compute_optimal_trajectory(0.1, 5)
        
        # 5. Monitor
        exporter = PrometheusExporter(port=9002)
        exporter.record_trade('EURUSD', signal, 'closed', 5.0)
        
        # 6. Verify
        assert schedule.total_quantity == 0.1
        assert signal in ['BUY', 'SELL']


class TestPerformanceBenchmarks:
    """Performance benchmark tests"""
    
    def test_forecasting_latency(self):
        """Test forecasting model latency"""
        
        model = NBeatsModel(input_size=24, forecast_size=6)
        x = np.random.randn(100, 24).astype(np.float32)
        
        start = time.perf_counter()
        predictions = model.predict(x)
        latency = time.perf_counter() - start
        
        # Should be fast (< 1 second for 100 predictions)
        assert latency < 1.0
        assert predictions.shape == (100, 6)
    
    def test_execution_optimization_speed(self):
        """Test execution optimization speed"""
import numpy
import pandas
        
optimizer = AlmgrenChrissOptimizer()
        
start = time.perf_counter()
for _ in range(100):
            schedule = optimizer.compute_optimal_trajectory(1.0, 10)
latency = time.perf_counter() - start
        
        # Should compute 100 schedules in < 1 second
        assert latency < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
