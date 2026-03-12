"""
Master Orchestrator - Coordinates all trading bot systems and modules.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
import traceback

from ..registry import ModuleRegistry, get_registry, initialize_registry
from ..registry.service_locator import ServiceLocator, get_service_locator
from .service_managers import (
    ServiceManager, DataServiceManager, AnalysisServiceManager,
    TradingServiceManager, RiskServiceManager, OptimizationServiceManager,
    OrchestrationServiceManager, SpecializedSystemServiceManager,
    InfrastructureServiceManager
)
from .event_bus import EventBus, get_event_bus, Event, EventPriority, EventHandler

logger = logging.getLogger(__name__)

@dataclass
class OrchestratorConfig:
    """Configuration for the Master Orchestrator."""
    # System settings
    mode: str = "paper"  # paper, simulation, live
    auto_start: bool = True
    graceful_shutdown_timeout: float = 30.0
    
    # Module settings
    enable_optional_modules: bool = True
    module_init_timeout: float = 60.0
    parallel_init: bool = True
    
    # Health monitoring
    health_check_interval: float = 30.0
    auto_recovery: bool = True
    max_recovery_attempts: int = 3
    
    # Performance
    max_concurrent_operations: int = 100
    enable_metrics: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    log_file_path: str = "logs/orchestrator.log"
    
    # Trading settings
    symbols: List[str] = field(default_factory=lambda: ["EURUSD"])
    timeframes: List[str] = field(default_factory=lambda: ["M5", "M15", "H1"])
    max_positions: int = 5
    risk_per_trade: float = 0.02
    
    # Feature flags
    enable_ai_features: bool = True
    enable_ml_features: bool = True
    enable_quantum_features: False
    enable_evolution_features: bool = True
    enable_sentient_features: bool = False

class SystemEventHandler(EventHandler):
    """Handles system-level events."""
    
    def __init__(self, orchestrator):
        super().__init__("SystemEventHandler")
        self.orchestrator = orchestrator
    
    async def handle(self, event: Event) -> None:
        """Handle system events."""
        if event.type == "service_unhealthy":
            await self._handle_service_unhealthy(event)
        elif event.type == "critical_error":
            await self._handle_critical_error(event)
        elif event.type == "shutdown_request":
            await self._handle_shutdown_request(event)
    
    async def _handle_service_unhealthy(self, event: Event) -> None:
        """Handle unhealthy service event."""
        service = event.data.get('service')
        logger.warning(f"Service {service} is unhealthy")
        
        # Could implement circuit breaker pattern here
        if event.data.get('error_count', 0) > 3:
            logger.error(f"Service {service} has failed multiple times, considering shutdown")
            # orchestrator.shutdown()
    
    async def _handle_critical_error(self, event: Event) -> None:
        """Handle critical error event."""
        error = event.data.get('error', 'Unknown error')
        logger.critical(f"Critical error: {error}")
        
        # Could trigger emergency shutdown
        # await self.orchestrator.emergency_shutdown()
    
    async def _handle_shutdown_request(self, event: Event) -> None:
        """Handle shutdown request."""
        reason = event.data.get('reason', 'Requested')
        logger.info(f"Shutdown requested: {reason}")
        await self.orchestrator.shutdown()

class MasterOrchestrator:
    """
    Master orchestrator for the entire trading bot system.
    
    Coordinates:
    - All service managers
    - Module initialization and lifecycle
    - Event-driven communication
    - System health and recovery
    - Trading operations
    """
    
    def __init__(self, config: OrchestratorConfig = None):
        self.config = config or OrchestratorConfig()
        
        # Core components
        self.registry: ModuleRegistry = get_registry()
        self.service_locator: ServiceLocator = get_service_locator()
        self.event_bus: EventBus = get_event_bus()
        
        # Service managers
        self.service_managers: Dict[str, ServiceManager] = {}
        self._initialize_service_managers()
        
        # System state
        self.initialized = False
        self.running = False
        self.shutdown_requested = False
        self.startup_time: Optional[datetime] = None
        
        # Event handlers
        self.system_handler = SystemEventHandler(self)
        
        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Metrics
        self.metrics = {
            'start_time': None,
            'modules_loaded': 0,
            'services_active': 0,
            'events_processed': 0,
            'errors_count': 0,
            'last_health_check': None
        }
    
    def _initialize_service_managers(self) -> None:
        """Initialize all service managers."""
        self.service_managers = {
            'data': DataServiceManager(),
            'analysis': AnalysisServiceManager(),
            'trading': TradingServiceManager(),
            'risk': RiskServiceManager(),
            'optimization': OptimizationServiceManager(),
            'orchestration': OrchestrationServiceManager(),
            'specialized': SpecializedSystemServiceManager(),
            'infrastructure': InfrastructureServiceManager()
        }
        
        # Register with service locator
        for name, manager in self.service_managers.items():
            self.service_locator.register(f"{name}_manager", manager)
    
    async def initialize(self, config: OrchestratorConfig = None) -> bool:
        """Initialize the orchestrator and all systems."""
        if config:
            self.config = config
        
        logger.info("Initializing Master Orchestrator...")
        self.startup_time = datetime.now()
        
        try:
            # Setup logging
            self._setup_logging()
            
            # Discover modules
            logger.info("Discovering modules...")
            self.registry.discover_modules()
            
            # Resolve dependencies
            logger.info("Resolving dependencies...")
            success, load_order, errors = self.registry.resolve_dependencies()
            
            if not success:
                logger.error(f"Failed to resolve dependencies: {errors}")
                return False
            
            self.metrics['modules_loaded'] = len(load_order)
            logger.info(f"Dependency order: {load_order}")
            
            # Register event handlers
            self.event_bus.subscribe_all(self.system_handler)
            
            # Initialize service managers
            logger.info("Initializing service managers...")
            
            if self.config.parallel_init:
                # Initialize managers concurrently
                tasks = []
                for manager in self.service_managers.values():
                    tasks.append(manager.initialize())
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check results
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Service manager failed: {result}")
                        return False
                    elif not result:
                        logger.error("Service manager returned False")
                        return False
            else:
                # Initialize sequentially
                for name, manager in self.service_managers.items():
                    if not await manager.initialize():
                        logger.error(f"Failed to initialize {name} manager")
                        return False
            
            # Count active services
            self.metrics['services_active'] = sum(
                len(m.services) for m in self.service_managers.values()
            )
            
            # Start monitoring
            self._start_monitoring()
            
            # Register core services
            await self._register_core_services()
            
            self.initialized = True
            logger.info("Master Orchestrator initialized successfully")
            
            # Publish initialization event
            await self.event_bus.publish(Event(
                type="orchestrator_initialized",
                data={
                    'mode': self.config.mode,
                    'modules': self.metrics['modules_loaded'],
                    'services': self.metrics['services_active']
                },
                source="MasterOrchestrator",
                priority=EventPriority.CRITICAL
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            traceback.print_exc()
            return False
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        import logging
        
        # Set log level
        level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.getLogger().setLevel(level)
        
        # Add file handler if enabled
        if self.config.log_to_file:
            from pathlib import Path
            Path(self.config.log_file_path).parent.mkdir(parents=True, exist_ok=True)
            
            handler = logging.FileHandler(self.config.log_file_path)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logging.getLogger().addHandler(handler)
    
    async def _register_core_services(self) -> None:
        """Register core services with the service locator."""
        # Register orchestrator
        self.service_locator.register("orchestrator", self)
        
        # Register event bus
        self.service_locator.register("event_bus", self.event_bus)
        
        # Register registry
        self.service_locator.register("registry", self.registry)
        
        # Register config
        self.service_locator.register("config", self.config)
    
    def _start_monitoring(self) -> None:
        """Start background monitoring."""
        if self.config.health_check_interval > 0:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while not self.shutdown_requested:
            try:
                await self._health_check()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def _health_check(self) -> None:
        """Perform system health check."""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'uptime': (datetime.now() - self.startup_time).total_seconds() if self.startup_time else 0,
            'services': {}
        }
        
        all_healthy = True
        
        for name, manager in self.service_managers.items():
            status = manager.get_status()
            health_status['services'][name] = status
            
            if not status.get('healthy_services', 0) == status.get('service_count', 0):
                all_healthy = False
        
        self.metrics['last_health_check'] = datetime.now()
        
        # Publish health status
        await self.event_bus.publish(Event(
            type="health_check",
            data=health_status,
            source="MasterOrchestrator"
        ))
        
        # Log if unhealthy
        if not all_healthy:
            logger.warning("System health check failed - some services are unhealthy")
    
    async def start(self) -> bool:
        """Start the trading system."""
        if not self.initialized:
            if not await self.initialize():
                return False
        
        logger.info("Starting trading system...")
        
        try:
            self.running = True
            self.metrics['start_time'] = datetime.now()
            
            # Start trading service
            trading_manager = self.service_managers.get('trading')
            if trading_manager:
                # Initialize trading with configured symbols
                await self._initialize_trading()
            
            logger.info("Trading system started successfully")
            
            # Publish start event
            await self.event_bus.publish(Event(
                type="system_started",
                data={
                    'mode': self.config.mode,
                    'symbols': self.config.symbols
                },
                source="MasterOrchestrator",
                priority=EventPriority.CRITICAL
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            return False
    
    async def _initialize_trading(self) -> None:
        """Initialize trading with configured parameters."""
        # Get trading engine or main trading service
        trading_service = self.service_locator.get("trading")
        
        if trading_service:
            # Configure symbols
            if hasattr(trading_service, 'set_symbols'):
                await trading_service.set_symbols(self.config.symbols)
            
            # Configure timeframes
            if hasattr(trading_service, 'set_timeframes'):
                await trading_service.set_timeframes(self.config.timeframes)
            
            # Configure risk
            if hasattr(trading_service, 'set_risk_per_trade'):
                trading_service.set_risk_per_trade(self.config.risk_per_trade)
            
            # Set mode
            if hasattr(trading_service, 'set_mode'):
                await trading_service.set_mode(self.config.mode)
    
    async def stop(self) -> None:
        """Stop the trading system."""
        logger.info("Stopping trading system...")
        
        self.running = False
        
        # Publish stop event
        await self.event_bus.publish(Event(
            type="system_stopping",
            data={},
            source="MasterOrchestrator",
            priority=EventPriority.HIGH
        ))
        
        # Stop all services
        for manager in self.service_managers.values():
            await manager.shutdown()
        
        logger.info("Trading system stopped")
    
    async def shutdown(self) -> None:
        """Shutdown the orchestrator gracefully."""
        if self.shutdown_requested:
            return
        
        logger.info("Shutting down Master Orchestrator...")
        self.shutdown_requested = True
        
        try:
            # Stop trading
            if self.running:
                await self.stop()
            
            # Cancel monitoring task
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
            
            # Shutdown event bus
            await self.event_bus.shutdown()
            
            # Clear service locator
            self.service_locator.clear()
            
            logger.info("Master Orchestrator shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def emergency_shutdown(self, reason: str = "Emergency") -> None:
        """Perform emergency shutdown."""
        logger.critical(f"EMERGENCY SHUTDOWN: {reason}")
        
        # Publish emergency event
        await self.event_bus.publish(Event(
            type="emergency_shutdown",
            data={'reason': reason},
            source="MasterOrchestrator",
            priority=EventPriority.CRITICAL
        ))
        
        # Force shutdown with shorter timeout
        self.config.graceful_shutdown_timeout = 5.0
        await self.shutdown()
    
    async def process_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a trading signal through the system.
        
        Args:
            signal: Trading signal dictionary
            
        Returns:
            Processing result
        """
        if not self.running:
            return {'status': 'error', 'message': 'System not running'}
        
        try:
            # Publish signal event
            await self.event_bus.publish(Event(
                type="signal_received",
                data=signal,
                source="MasterOrchestrator"
            ))
            
            # Get risk manager
            risk_manager = self.service_managers.get('risk')
            if risk_manager:
                # Validate signal
                risk_service = risk_manager.get_service('risk')
                if risk_service and hasattr(risk_service, 'validate_signal'):
                    if not await risk_service.validate_signal(signal):
                        return {'status': 'rejected', 'message': 'Risk validation failed'}
            
            # Get execution manager
            trading_manager = self.service_managers.get('trading')
            if trading_manager:
                # Execute signal
                execution_service = trading_manager.get_service('execution')
                if execution_service:
                    result = await execution_service.execute(signal)
                    
                    # Publish execution event
                    await self.event_bus.publish(Event(
                        type="signal_executed",
                        data={
                            'signal_id': signal.get('id'),
                            'result': result
                        },
                        source="MasterOrchestrator"
                    ))
                    
                    return result
            
            return {'status': 'error', 'message': 'No execution service available'}
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            self.metrics['errors_count'] += 1
            return {'status': 'error', 'message': str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        uptime = None
        if self.metrics['start_time']:
            uptime = (datetime.now() - self.metrics['start_time']).total_seconds()
        
        return {
            'initialized': self.initialized,
            'running': self.running,
            'uptime': uptime,
            'mode': self.config.mode,
            'metrics': self.metrics.copy(),
            'service_managers': {
                name: manager.get_status()
                for name, manager in self.service_managers.items()
            },
            'event_bus': self.event_bus.get_statistics(),
            'registry': self.registry.get_statistics()
        }
    
    async def export_state(self, filepath: str) -> bool:
        """Export system state to file."""
        try:
            state = {
                'timestamp': datetime.now().isoformat(),
                'config': self.config.__dict__,
                'status': self.get_status(),
                'modules': {}
            }
            
            # Export module states
            for name, module_info in self.registry.modules.items():
                state['modules'][name] = {
                    'initialized': module_info.initialized,
                    'enabled': module_info.enabled,
                    'dependencies': list(module_info.dependencies)
                }
            
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"System state exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export state: {e}")
            return False
    
    def __del__(self):
        """Cleanup on deletion."""
        if not self.shutdown_requested:
            # Schedule shutdown
            asyncio.create_task(self.shutdown())
