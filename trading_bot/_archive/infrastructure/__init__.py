"""
infrastructure package - Layer 7: Infrastructure & Orchestration
"""

try:
    # Core orchestration components (required for canonical architecture)
    from .orchestration import SystemOrchestrator, SystemState, LayerStatus
    from .config import ConfigManager, SystemConfig, TradingConfig, DataConfig, RiskConfig, ExecutionConfig, MonitoringConfig
    from .logging import setup_logging, get_logger, get_performance_logger, PerformanceLogger, LogContext, trading_context
    
    # Existing infrastructure components
    from .auto_scaler import AutoScaler, LoadBalancer, ScalingPolicy
    from .cloud_infrastructure import (
        AutoScaler,
        CloudInfrastructure,
        DistributedTracer,
        KubernetesDeploymentGenerator,
        LoadBalancer,
        LogAggregator,
        Message,
        MessagePriority,
        MessageQueue,
        RedisCache,
        ScalingConfig,
        ScalingPolicy,
        SecretsManager,
        ServiceInstance,
        ServiceStatus,
        TraceSpan,
        get_infrastructure
    )
    from .disaster_recovery import (
        DisasterRecoveryManager,
        FailoverManager,
        RecoveryAction,
        RecoveryEvent,
        StateManager,
        SystemSnapshot,
        SystemState,
        get_disaster_recovery_manager,
        get_state_manager
    )
    from .edge_computing import (
        CloudProvider,
        ComputeNode,
        EdgeComputingManager,
        InfrastructureOrchestrator,
        LatencyMetrics,
        LowLatencyMeshNetwork,
        MultiCloudFailoverSystem,
        NodeStatus,
        ZeroTrustSecurity,
        retry
    )
    from .free_infrastructure import (
        FreeAutoScaler,
        FreeBackupManager,
        FreeCacheManager,
        FreeDeploymentTarget,
        FreeInfrastructure,
        FreeLoadBalancer,
        FreeSystemMonitor,
        SystemHealth
    )
    from .health_check import HealthCheck, initialize_health_check
    from .health_endpoints import (
        ComponentHealth,
        HealthCheckManager,
        HealthStatus,
        check_broker_connection,
        check_data_freshness,
        check_database_connection,
        check_disk_space,
        check_memory_usage,
        setup_health_endpoints
    )
    from .health_monitoring import (
        AlertManager,
        ComponentHealth,
        ComponentType,
        HealthChecker,
        HealthMonitoringSystem,
        HealthStatus,
        MetricsCollector,
        SystemHealth,
        check_broker_health,
        check_database_health,
        create_health_app,
        run_health_server
    )
    from .kubernetes_orchestrator import (
        KubernetesOrchestrator,
        ResourceMetrics,
        ScalingDecision,
        ScalingMode,
        VolatilityMonitor,
        retry
    )
    from .memory_optimizer import (
        MemoryMonitor,
        MemoryOptimizer,
        get_current_memory_mb,
        get_memory_optimizer,
        is_memory_available,
        memory_efficient,
        memory_efficient_async,
        optimize_memory_now
    )
    from .mlflow_tracker import MLflowTracker, get_tracker
    from .network_optimizer import (
        ConnectionPoolManager,
        NetworkOptimizer,
        get_network_optimizer,
        get_pool_manager,
        measure_endpoint_latency,
        optimize_request_settings
    )
    from .performance_optimizer import (
        BatchProcessor,
        CacheManager,
        MemoryOptimizer,
        PerformanceMonitor,
        cached,
        get_performance_monitor,
        measure_performance
    )
    from .prometheus_exporter import PrometheusExporter, get_exporter
    from .self_healing import (
        ComponentHealth,
        ComponentStatus,
        HealthMetrics,
        RecoveryAction,
        ScalingAction,
        SelfHealingSystem
    )
    from .time_sync_watchdog import TimeSyncWatchdog
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in infrastructure: {e}')

__all__ = [
    # Core orchestration components
    'SystemOrchestrator',
    'SystemState', 
    'LayerStatus',
    'ConfigManager',
    'SystemConfig',
    'TradingConfig',
    'DataConfig', 
    'RiskConfig',
    'ExecutionConfig',
    'MonitoringConfig',
    'setup_logging',
    'get_logger',
    'get_performance_logger',
    'PerformanceLogger',
    'LogContext',
    'trading_context',
    
    # Existing infrastructure components
    'AlertManager',
    'AutoScaler',
    'BatchProcessor',
    'CacheManager',
    'CloudInfrastructure',
    'CloudProvider',
    'ComponentHealth',
    'ComponentStatus',
    'ComponentType',
    'ComputeNode',
    'ConnectionPoolManager',
    'DisasterRecoveryManager',
    'DistributedTracer',
    'EdgeComputingManager',
    'FailoverManager',
    'FreeAutoScaler',
    'FreeBackupManager',
    'FreeCacheManager',
    'FreeDeploymentTarget',
    'FreeInfrastructure',
    'FreeLoadBalancer',
    'FreeSystemMonitor',
    'HealthCheck',
    'HealthCheckManager',
    'HealthChecker',
    'HealthMetrics',
    'HealthMonitoringSystem',
    'HealthStatus',
    'InfrastructureOrchestrator',
    'KubernetesDeploymentGenerator',
    'KubernetesOrchestrator',
    'LatencyMetrics',
    'LoadBalancer',
    'LogAggregator',
    'LowLatencyMeshNetwork',
    'MLflowTracker',
    'MemoryMonitor',
    'MemoryOptimizer',
    'Message',
    'MessagePriority',
    'MessageQueue',
    'MetricsCollector',
    'MultiCloudFailoverSystem',
    'NetworkOptimizer',
    'NodeStatus',
    'PerformanceMonitor',
    'PrometheusExporter',
    'RecoveryAction',
    'RecoveryEvent',
    'RedisCache',
    'ResourceMetrics',
    'ScalingAction',
    'ScalingConfig',
    'ScalingDecision',
    'ScalingMode',
    'ScalingPolicy',
    'SecretsManager',
    'SelfHealingSystem',
    'ServiceInstance',
    'ServiceStatus',
    'StateManager',
    'SystemHealth',
    'SystemSnapshot',
    'SystemState',
    'TimeSyncWatchdog',
    'TraceSpan',
    'VolatilityMonitor',
    'ZeroTrustSecurity',
    'cached',
    'check_broker_connection',
    'check_broker_health',
    'check_data_freshness',
    'check_database_connection',
    'check_database_health',
    'check_disk_space',
    'check_memory_usage',
    'create_health_app',
    'get_current_memory_mb',
    'get_disaster_recovery_manager',
    'get_exporter',
    'get_infrastructure',
    'get_memory_optimizer',
    'get_network_optimizer',
    'get_performance_monitor',
    'get_pool_manager',
    'get_state_manager',
    'get_tracker',
    'initialize_health_check',
    'is_memory_available',
    'measure_endpoint_latency',
    'measure_performance',
    'memory_efficient',
    'memory_efficient_async',
    'optimize_memory_now',
    'optimize_request_settings',
    'retry',
    'run_health_server',
    'setup_health_endpoints',
]