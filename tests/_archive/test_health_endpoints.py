"""
Unit tests for Health Check Endpoints

Tests for health check manager and endpoints
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient

from trading_bot.infrastructure.health_endpoints import (
    HealthCheckManager,
    HealthStatus,
    ComponentHealth,
    setup_health_endpoints
)


class TestComponentHealth:
    """Test suite for ComponentHealth"""
    
    def test_initialization(self):
        """Test component health initialization"""
        component = ComponentHealth('test_component')
        
        assert component.name == 'test_component'
        assert component.status == HealthStatus.HEALTHY
        assert component.error_message is None
    
    @pytest.mark.asyncio
    async def test_check_success(self):
        """Test successful health check"""
        def check_func():
            return True
        
        component = ComponentHealth('test', check_func)
        result = await component.check()
        
        assert result is True
        assert component.status == HealthStatus.HEALTHY
        assert component.error_message is None
    
    @pytest.mark.asyncio
    async def test_check_failure(self):
        """Test failed health check"""
        def check_func():
            return False
        
        component = ComponentHealth('test', check_func)
        result = await component.check()
        
        assert result is False
        assert component.status == HealthStatus.UNHEALTHY
        assert component.error_message is not None
    
    @pytest.mark.asyncio
    async def test_check_exception(self):
        """Test health check with exception"""
        def check_func():
            raise Exception("Test error")
        
        component = ComponentHealth('test', check_func)
        result = await component.check()
        
        assert result is False
        assert component.status == HealthStatus.UNHEALTHY
        assert "Test error" in component.error_message
    
    @pytest.mark.asyncio
    async def test_async_check_function(self):
        """Test async health check function"""
        async def async_check():
            await asyncio.sleep(0.1)
            return True
        
        component = ComponentHealth('test', async_check)
        result = await component.check()
        
        assert result is True
        assert component.status == HealthStatus.HEALTHY


class TestHealthCheckManager:
    """Test suite for HealthCheckManager"""
    
    @pytest.fixture
    def manager(self):
        """Create health check manager"""
        config = {
            'check_interval': 30,
            'startup_grace_period': 60,
            'max_component_age': 300
        }
        return HealthCheckManager(config)
    
    def test_initialization(self):
        """Test manager initialization"""
        manager = HealthCheckManager()
        
        assert manager is not None
        assert len(manager.components) == 0
        assert manager.overall_status == HealthStatus.HEALTHY
    
    def test_register_component(self, manager):
        """Test registering a component"""
        def check_func():
            return True
        
        manager.register_component('test_component', check_func)
        
        assert 'test_component' in manager.components
        assert manager.components['test_component'].name == 'test_component'
    
    def test_register_component_with_metadata(self, manager):
        """Test registering component with metadata"""
        metadata = {'critical': True, 'timeout': 10}
        
        manager.register_component('test', lambda: True, metadata)
        
        assert manager.components['test'].metadata == metadata
    
    @pytest.mark.asyncio
    async def test_check_all_healthy(self, manager):
        """Test checking all components when healthy"""
        manager.register_component('comp1', lambda: True)
        manager.register_component('comp2', lambda: True)
        
        results = await manager.check_all()
        
        assert len(results) == 2
        assert results['comp1']['status'] == HealthStatus.HEALTHY.value
        assert results['comp2']['status'] == HealthStatus.HEALTHY.value
        assert manager.overall_status == HealthStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_check_all_with_failure(self, manager):
        """Test checking all components with one failure"""
        manager.register_component('comp1', lambda: True)
        manager.register_component('comp2', lambda: False)
        
        results = await manager.check_all()
        
        assert results['comp1']['status'] == HealthStatus.HEALTHY.value
        assert results['comp2']['status'] == HealthStatus.UNHEALTHY.value
        assert manager.overall_status == HealthStatus.UNHEALTHY
    
    def test_is_alive(self, manager):
        """Test liveness check"""
        assert manager.is_alive() is True
    
    def test_is_ready_during_grace_period(self, manager):
        """Test readiness during startup grace period"""
        # Just started, should not be ready
        assert manager.is_ready() is False
    
    def test_is_ready_after_grace_period(self):
        """Test readiness after grace period"""
        config = {'startup_grace_period': 0}  # No grace period
        manager = HealthCheckManager(config)
        
        # Should be ready immediately
        assert manager.is_ready() is True
    
    @pytest.mark.asyncio
    async def test_is_ready_with_critical_component_failure(self):
        """Test readiness with critical component failure"""
        config = {'startup_grace_period': 0}
        manager = HealthCheckManager(config)
        
        # Register critical component that fails
        manager.register_component(
            'critical',
            lambda: False,
            {'critical': True}
        )
        
        await manager.check_all()
        
        assert manager.is_ready() is False
    
    def test_get_status_summary(self, manager):
        """Test getting status summary"""
        summary = manager.get_status_summary()
        
        assert 'status' in summary
        assert 'uptime_seconds' in summary
        assert 'startup_time' in summary
        assert 'components' in summary
        assert 'ready' in summary
        assert 'alive' in summary
    
    @pytest.mark.asyncio
    async def test_multiple_components(self, manager):
        """Test with multiple components"""
        components = {
            'database': lambda: True,
            'broker': lambda: True,
            'cache': lambda: True,
            'api': lambda: True
        }
        
        for name, check_func in components.items():
            manager.register_component(name, check_func)
        
        results = await manager.check_all()
        
        assert len(results) == 4
        assert all(r['status'] == HealthStatus.HEALTHY.value for r in results.values())


class TestHealthEndpoints:
    """Test suite for health check endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app with health endpoints"""
        app = FastAPI()
        manager = HealthCheckManager({'startup_grace_period': 0})
        
        # Register test components
        manager.register_component('test_db', lambda: True, {'critical': True})
        manager.register_component('test_cache', lambda: True)
        
        setup_health_endpoints(app, manager)
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test /health endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'ready' in data
        assert 'alive' in data
        assert 'timestamp' in data
    
    def test_liveness_endpoint(self, client):
        """Test /health/live endpoint"""
        response = client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'alive'
        assert 'timestamp' in data
    
    @pytest.mark.asyncio
    async def test_readiness_endpoint(self, client):
        """Test /health/ready endpoint"""
        response = client.get("/health/ready")
        
        # Should be ready (no grace period)
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'components' in data
        assert 'overall' in data
    
    def test_status_endpoint(self, client):
        """Test /health/status endpoint"""
        response = client.get("/health/status")
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'uptime_seconds' in data
        assert 'detailed_checks' in data
        assert 'timestamp' in data


class TestHealthCheckFunctions:
    """Test example health check functions"""
    
    def test_check_database_connection(self):
        """Test database connection check"""
        from trading_bot.infrastructure.health_endpoints import check_database_connection
        
        # Mock database
        class MockDB:
            is_connected = True
        
        result = check_database_connection(MockDB())
        assert result is True
        
        result = check_database_connection(None)
        assert result is False
    
    def test_check_broker_connection(self):
        """Test broker connection check"""
        from trading_bot.infrastructure.health_endpoints import check_broker_connection
        
        # Mock broker
        class MockBroker:
            connected = True
        
        result = check_broker_connection(MockBroker())
        assert result is True
        
        result = check_broker_connection(None)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_data_freshness(self):
        """Test data freshness check"""
        from trading_bot.infrastructure.health_endpoints import check_data_freshness
        
        # Mock data stream
        class MockDataStream:
            last_update = datetime.now()
        
        result = await check_data_freshness(MockDataStream(), max_age_seconds=60)
        assert result is True
        
        # Old data
        class OldDataStream:
            last_update = datetime.now() - timedelta(seconds=120)
        
        result = await check_data_freshness(OldDataStream(), max_age_seconds=60)
        assert result is False
    
    def test_check_memory_usage(self):
        """Test memory usage check"""
        from trading_bot.infrastructure.health_endpoints import check_memory_usage
        
        # Should pass with reasonable limit
        result = check_memory_usage(max_memory_mb=10000)
        assert isinstance(result, bool)
    
    def test_check_disk_space(self):
        """Test disk space check"""
        from trading_bot.infrastructure.health_endpoints import check_disk_space
import json
        
        # Should pass with reasonable limit
        result = check_disk_space(min_free_gb=1)
        assert isinstance(result, bool)


class TestHealthStatusEnum:
    """Test HealthStatus enum"""
    
    def test_enum_values(self):
        """Test enum values"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
