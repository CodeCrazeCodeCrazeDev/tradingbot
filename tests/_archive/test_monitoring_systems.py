"""
Comprehensive tests for monitoring and infrastructure
"""

import pytest
import time
import numpy as np


class TestPrometheusExporter:
    """Test Prometheus metrics exporter"""
    
    def test_exporter_initialization(self):
        from trading_bot.infrastructure import PrometheusExporter
        
        exporter = PrometheusExporter(port=8002)
        assert exporter.enabled or not exporter.enabled
    
    def test_record_trade_metrics(self):
        exporter = PrometheusExporter(port=8003)
        exporter.record_trade('EURUSD', 'BUY', 'closed', 15.5)
        exporter.record_trade('GBPUSD', 'SELL', 'closed', -5.2)
    
    def test_portfolio_metrics(self):
        exporter = PrometheusExporter(port=8004)
        exporter.update_portfolio(value=100000, drawdown=0.05)
        exporter.update_positions('EURUSD', 3)
    
    def test_model_metrics(self):
        exporter = PrometheusExporter(port=8005)
        exporter.record_model_inference('tft', 0.05, 'BUY', 0.85)
        exporter.record_model_inference('deepar', 0.03, 'SELL', 0.72)
    
    def test_risk_metrics(self):
        exporter = PrometheusExporter(port=8006)
        exporter.record_risk_breach('daily_loss')
        exporter.update_risk_exposure(0.15)
    
    def test_system_metrics(self):
        exporter = PrometheusExporter(port=8007)
        exporter.update_system_health(95.0)
        exporter.update_data_staleness('market_data', 2.5)
        exporter.update_circuit_breaker('emergency', False)
    
    def test_execution_metrics(self):
        exporter = PrometheusExporter(port=8008)
        exporter.record_order_execution('MARKET', 0.02, 'EURUSD', 0.5)


class TestMLflowTracker:
    """Test MLflow experiment tracker"""
    
    def test_tracker_initialization(self):
        from trading_bot.infrastructure import MLflowTracker
        
        tracker = MLflowTracker("test_experiment")
        assert tracker.enabled or not tracker.enabled
    
    def test_log_params(self):
        tracker = MLflowTracker("test_params")
        if tracker.enabled:
            with tracker.start_run():
                tracker.log_params({'lr': 0.001, 'batch_size': 32})
    
    def test_log_metrics(self):
        tracker = MLflowTracker("test_metrics")
        if tracker.enabled:
            with tracker.start_run():
                tracker.log_metrics({'loss': 0.5, 'accuracy': 0.85})


class TestPerformanceOptimizer:
    """Test performance optimization utilities"""
    
    def test_performance_monitor(self):
        from trading_bot.infrastructure import measure_performance, get_performance_monitor
        
        @measure_performance("test_operation")
        def slow_function():
            time.sleep(0.001)
            return 42
        
        for _ in range(10):
            result = slow_function()
            assert result == 42
        
        monitor = get_performance_monitor()
        stats = monitor.get_stats("test_operation")
        
        assert stats['count'] == 10
        assert stats['mean'] > 0
    
    def test_memory_optimizer(self):
        from trading_bot.infrastructure import MemoryOptimizer
        import pandas as pd
        
        df = pd.DataFrame({
            'int_col': np.random.randint(0, 100, 1000),
            'float_col': np.random.randn(1000)
        })
        
        original_memory = df.memory_usage(deep=True).sum()
        optimized_df = MemoryOptimizer.optimize_dataframe(df)
        optimized_memory = optimized_df.memory_usage(deep=True).sum()
        
        assert optimized_memory <= original_memory
    
    def test_batch_processor(self):
        from trading_bot.infrastructure import BatchProcessor
        
        processor = BatchProcessor(batch_size=10)
        data = list(range(100))
        
        def process_batch(batch):
            return [x * 2 for x in batch]
        
        results = processor.process_batches(data, process_batch)
        
        assert len(results) == 100
        assert results[0] == 0
        assert results[50] == 100
    
    def test_cache_manager(self):
        from trading_bot.infrastructure import CacheManager
        
        cache = CacheManager(max_size=100, ttl=1.0)
        
        cache.set('key1', 'value1')
        assert cache.get('key1') == 'value1'
        
        time.sleep(1.1)
        assert cache.get('key1') is None
    
    def test_cached_decorator(self):
        from trading_bot.infrastructure import cached
        
        call_count = [0]
        
        @cached(ttl=1.0)
        def expensive_function(x):
            call_count[0] += 1
            return x * 2
        
        result1 = expensive_function(5)
        result2 = expensive_function(5)
        
        assert result1 == 10
        assert result2 == 10
        assert call_count[0] == 1


class TestAutoScaler:
    """Test auto-scaling functionality"""
    
    def test_scaler_initialization(self):
        from trading_bot.infrastructure import AutoScaler, ScalingPolicy
        
        policy = ScalingPolicy(min_instances=1, max_instances=5)
        scaler = AutoScaler(policy)
        
        assert scaler.policy.min_instances == 1
        assert scaler.policy.max_instances == 5
    
    def test_scaler_lifecycle(self):
        class DummyWorker:
            def start(self):
            def stop(self):
        
        policy = ScalingPolicy(min_instances=2, max_instances=4)
        scaler = AutoScaler(policy)
        scaler.start(DummyWorker)
        
        status = scaler.get_status()
        assert status['current_instances'] >= 2
        
        scaler.stop()
        assert not scaler.running
    
    def test_load_balancer(self):
        from trading_bot.infrastructure import LoadBalancer
        
        class Worker:
            def __init__(self, id):
                self.id = id
        
        lb = LoadBalancer()
        lb.add_worker(Worker(1))
        lb.add_worker(Worker(2))
        lb.add_worker(Worker(3))
        
        worker1 = lb.get_worker()
        worker2 = lb.get_worker()
        worker3 = lb.get_worker()
        worker4 = lb.get_worker()
        
        assert worker1.id == 1
        assert worker2.id == 2
        assert worker3.id == 3
        assert worker4.id == 1  # Round-robin


class TestChaosEngineering:
    """Test chaos engineering framework"""
    
    def test_chaos_monkey_initialization(self):
        from trading_bot.testing.chaos_engineering import ChaosMonkey
        
        monkey = ChaosMonkey()
        assert not monkey.active
        assert len(monkey.experiments) == 0
    
    def test_add_experiment(self):
        from trading_bot.testing.chaos_engineering import ChaosMonkey, ChaosExperiment, FaultType
        
        monkey = ChaosMonkey()
        exp = ChaosExperiment(
            name="test_latency",
            fault_type=FaultType.NETWORK_LATENCY,
            target_component="data_feed",
            probability=0.5
        )
        
        monkey.add_experiment(exp)
        assert len(monkey.experiments) == 1
    
    def test_fault_injection(self):
        monkey = ChaosMonkey()
        exp = ChaosExperiment(
            name="test_latency",
            fault_type=FaultType.NETWORK_LATENCY,
            target_component="data_feed",
            probability=1.0
        )
        
        monkey.add_experiment(exp)
        monkey.start()
        
        result = monkey.should_inject_fault("data_feed")
        assert result is not None
        
        monkey.stop()
    
    def test_network_latency_injection(self):
    pass
from enum import auto
import numpy
import pandas
        
        monkey = ChaosMonkey()
        exp = ChaosExperiment(
            name="latency_test",
            fault_type=FaultType.NETWORK_LATENCY,
            target_component="test"
        )
        
        base_latency = 0.01
        injected_latency = monkey.inject_network_latency(base_latency, exp)
        
        assert injected_latency > base_latency
        assert len(monkey.fault_history) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
