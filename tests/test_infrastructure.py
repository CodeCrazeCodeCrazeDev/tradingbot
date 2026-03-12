"""
Tests for Production Infrastructure (Phase 8)
"""

import unittest
import numpy as np
from datetime import datetime, timedelta
from infrastructure.auto_scaling import (
    AutoScaler,
    ResourceMetrics
)
from infrastructure.monitoring import (
    PerformanceMonitor,
    PerformanceMetrics
)
from infrastructure.health_check import HealthCheck
from enum import auto
import numpy


class TestAutoScaling(unittest.TestCase):
    """Test auto-scaling system."""
    
    def setUp(self):
        self.scaler = AutoScaler(
            update_interval=60,
            history_size=1000
        )
    
    def test_resource_metrics(self):
        """Test resource metrics collection."""
        metrics = self.scaler._get_resource_metrics()
        
        self.assertIsInstance(metrics, ResourceMetrics)
        self.assertGreaterEqual(metrics.cpu_usage, 0.0)
        self.assertLessEqual(metrics.cpu_usage, 1.0)
        self.assertGreaterEqual(metrics.memory_usage, 0.0)
        self.assertLessEqual(metrics.memory_usage, 1.0)
    
    def test_scaling_decision(self):
        """Test scaling decision making."""
        metrics = ResourceMetrics(
            cpu_usage=0.9,        # High CPU
            memory_usage=0.8,     # High memory
            gpu_usage=None,
            gpu_memory=None,
            network_io=100.0,
            disk_io=50.0
        )
        
        market_state = {
            'volatility': 0.02,   # High volatility
            'volume': 1.5         # High volume
        }
        
        decision = self.scaler._make_scaling_decision(metrics, market_state)
        
        self.assertEqual(decision['action'], 'up')
        self.assertGreater(decision['workers'], self.scaler.current_workers)
    
    def test_resource_pressure(self):
        """Test resource pressure calculation."""
        metrics = ResourceMetrics(
            cpu_usage=0.8,
            memory_usage=0.7,
            gpu_usage=0.6,
            gpu_memory=0.5,
            network_io=100.0,
            disk_io=50.0
        )
        
        pressure = self.scaler._calculate_resource_pressure(metrics)
        
        self.assertGreaterEqual(pressure, 0.0)
        self.assertLessEqual(pressure, 1.0)
    
    def test_market_pressure(self):
        """Test market pressure calculation."""
        market_state = {
            'volatility': 0.02,
            'volume': 1.5,
            'trades_per_second': 5.0
        }
        
        pressure = self.scaler._calculate_market_pressure(market_state)
        
        self.assertGreaterEqual(pressure, 0.0)
        self.assertLessEqual(pressure, 1.0)


class TestPerformanceMonitor(unittest.TestCase):
    """Test performance monitoring."""
    
    def setUp(self):
        self.monitor = PerformanceMonitor()
    
    def test_metrics_update(self):
        """Test metrics update and alert generation."""
        metrics = PerformanceMetrics(
            latency=100.0,
            throughput=10.0,
            error_rate=0.01,
            success_rate=0.95,
            pnl=1000.0,
            sharpe=2.0,
            drawdown=0.05
        )
        
        alerts = self.monitor.update_metrics(metrics)
        
        self.assertIsInstance(alerts, list)
        self.assertGreater(len(self.monitor.history), 0)
    
    def test_alert_generation(self):
        """Test alert generation for critical conditions."""
        # High latency metrics
        metrics = PerformanceMetrics(
            latency=2000.0,  # Critical latency
            throughput=10.0,
            error_rate=0.01,
            success_rate=0.95,
            pnl=1000.0,
            sharpe=2.0,
            drawdown=0.05
        )
        
        alerts = self.monitor.update_metrics(metrics)
        
        self.assertGreater(len(alerts), 0)
        self.assertEqual(alerts[0]['level'], 'critical')
        self.assertIn('latency', alerts[0]['metric'])
    
    def test_metrics_summary(self):
        """Test metrics summary generation."""
        # Add some metrics
        for _ in range(10):
            metrics = PerformanceMetrics(
                latency=np.random.normal(100, 20),
                throughput=np.random.normal(10, 2),
                error_rate=np.random.uniform(0, 0.05),
                success_rate=np.random.uniform(0.9, 1.0),
                pnl=np.random.normal(1000, 200),
                sharpe=np.random.normal(2, 0.5),
                drawdown=np.random.uniform(0, 0.1)
            )
            self.monitor.update_metrics(metrics)
        
        summary = self.monitor.get_metrics_summary(
            window=timedelta(hours=1)
        )
        
        self.assertIn('latency', summary)
        self.assertIn('throughput', summary)
        self.assertIn('error_rate', summary)
        self.assertIn('success_rate', summary)
        self.assertIn('pnl', summary)
    
    def test_alert_acknowledgment(self):
        """Test alert acknowledgment."""
        # Generate alert
        metrics = PerformanceMetrics(
            latency=2000.0,  # Critical latency
            throughput=10.0,
            error_rate=0.01,
            success_rate=0.95,
            pnl=1000.0,
            sharpe=2.0,
            drawdown=0.05
        )
        
        alerts = self.monitor.update_metrics(metrics)
        alert_id = alerts[0]['id']
        
        # Acknowledge alert
        self.monitor.acknowledge_alert(alert_id)
        
        # Check alert is acknowledged
        current_alerts = self.monitor.get_current_alerts()
        self.assertNotIn(alert_id, [a['id'] for a in current_alerts])


class TestHealthCheck(unittest.TestCase):
    """Test health checking system."""
    
    def setUp(self):
        self.health_check = HealthCheck(
            check_interval=60,
            history_size=1000
        )
    
    def test_component_checks(self):
        """Test individual component health checks."""
        # Data feed check
        data_feed = self.health_check._check_data_feed()
        self.assertIn('status', data_feed)
        self.assertIn('last_check', data_feed)
        
        # Model check
        model = self.health_check._check_model()
        self.assertIn('status', model)
        self.assertIn('last_check', model)
        
        # Database check
        database = self.health_check._check_database()
        self.assertIn('status', database)
        self.assertIn('last_check', database)
    
    def test_complete_health_check(self):
        """Test complete health check."""
        status = self.health_check.check_all()
        
        self.assertIn('is_healthy', status)
        self.assertIn('components', status)
        self.assertIn('system_resources', status)
    
    def test_component_history(self):
        """Test component history tracking."""
        # Run some checks
        for _ in range(5):
            self.health_check.check_all()
        
        history = self.health_check.get_component_history(
            component='data_feed',
            window=timedelta(hours=1)
        )
        
        self.assertGreater(len(history), 0)
        for entry in history:
            self.assertIn('timestamp', entry)
            self.assertIn('status', entry)
    
    def test_health_report(self):
        """Test health report generation."""
        # Run checks
        self.health_check.check_all()
        
        report = self.health_check.generate_health_report()
        
        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 0)
        self.assertIn('SYSTEM HEALTH REPORT', report)


if __name__ == '__main__':
    unittest.main()
