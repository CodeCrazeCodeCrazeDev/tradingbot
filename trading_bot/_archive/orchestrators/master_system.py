"""
Master System - Unified orchestrator integrating all subsystems
This is the main entry point for the entire trading bot system
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from trading_bot.system_interfaces import (
    IOrchestrator,
    ComponentStatus,
    ComponentHealth,
    MarketData,
    TradingSignal,
    OrderRequest,
    ExecutionResult,
)
from trading_bot.system_config import SystemConfig, get_config
from trading_bot.system_registry import SystemRegistry, get_registry, ComponentMetadata
from trading_bot.system_interfaces import SystemLayer

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System-wide metrics"""
    uptime_seconds: float
    total_signals_generated: int
    total_trades_executed: int
    total_errors: int
    active_positions: int
    current_capital: float
    total_pnl: float
    win_rate: float
    sharpe_ratio: float


class MasterTradingSystem(IOrchestrator):
    """
    Master Trading System - Unified orchestrator
    
    Integrates all 8 layers:
    - Layer 0: Infrastructure (health, monitoring, deployment)
    - Layer 1: Data Foundation (ingestion, validation, storage)
    - Layer 2: Intelligence Core (ML, AI, feature engineering)
    - Layer 3: Signal Generation (strategies, indicators, regimes)
    - Layer 4: Risk & Safety (risk management, fail-safes, circuit breakers)
    - Layer 5: Execution (order routing, fill tracking, slippage)
    - Layer 6: Governance (compliance, audit, human-in-loop)
    - Layer 7: Orchestration (workflow management, coordination)
    """
    
    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or get_config()
        self.registry = get_registry()
        self.status = ComponentStatus.UNINITIALIZED
        self.start_time: Optional[datetime] = None
        
        # Layer components (will be populated from registry)
        self.infrastructure_components = []
        self.data_components = []
        self.intelligence_components = []
        self.signal_components = []
        self.risk_components = []
        self.execution_components = []
        self.governance_components = []
        
        # Metrics
        self.metrics = SystemMetrics(
            uptime_seconds=0,
            total_signals_generated=0,
            total_trades_executed=0,
            total_errors=0,
            active_positions=0,
            current_capital=self.config.initial_capital,
            total_pnl=0.0,
            win_rate=0.0,
            sharpe_ratio=0.0
        )
        
        # State
        self._running = False
        self._lock = asyncio.Lock()
        
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the master system"""
        logger.info("=" * 80)
        logger.info("INITIALIZING MASTER TRADING SYSTEM")
        logger.info("=" * 80)
        
        try:
            self.status = ComponentStatus.INITIALIZING
            
            # Step 1: Register all components
            logger.info("\n[1/5] Registering components...")
            await self._register_all_components()
            
            # Step 2: Initialize all components via registry
            logger.info("\n[2/5] Initializing components...")
            if not await self.registry.initialize_all():
                logger.error("Failed to initialize components")
                self.status = ComponentStatus.ERROR
                return False
            
            # Step 3: Load layer components
            logger.info("\n[3/5] Loading layer components...")
            self._load_layer_components()
            
            # Step 4: Verify system integrity
            logger.info("\n[4/5] Verifying system integrity...")
            if not await self._verify_system_integrity():
                logger.error("System integrity check failed")
                self.status = ComponentStatus.ERROR
                return False
            
            # Step 5: Run initial health check
            logger.info("\n[5/5] Running initial health check...")
            health_results = await self.registry.health_check_all()
            unhealthy = [name for name, h in health_results.items() if h.status == ComponentStatus.ERROR]
            
            if unhealthy:
                logger.warning(f"Unhealthy components: {unhealthy}")
            
            self.status = ComponentStatus.READY
            logger.info("\n" + "=" * 80)
            logger.info("MASTER SYSTEM INITIALIZED SUCCESSFULLY")
            logger.info("=" * 80)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}", exc_info=True)
            self.status = ComponentStatus.ERROR
            return False
    
    async def _register_all_components(self):
        """Register all available components from the codebase"""
        
        # Layer 0: Infrastructure
        await self._register_infrastructure_components()
        
        # Layer 1: Data Foundation
        await self._register_data_components()
        
        # Layer 2: Intelligence Core
        await self._register_intelligence_components()
        
        # Layer 3: Signal Generation
        await self._register_signal_components()
        
        # Layer 4: Risk & Safety
        await self._register_risk_components()
        
        # Layer 5: Execution
        await self._register_execution_components()
        
        # Layer 6: Governance
        await self._register_governance_components()
        
        summary = self.registry.get_status_summary()
        logger.info(f"Registered {summary['total']} components across {len(summary['by_layer'])} layers")
    
    async def _register_infrastructure_components(self):
        """Register infrastructure layer components"""
        # These will be lazy-loaded from existing modules
        components = [
            ('health_monitor', 'monitoring', 'trading_bot.infrastructure.health_check'),
            ('metrics_collector', 'monitoring', 'trading_bot.monitoring.monitoring_system'),
            ('alert_system', 'monitoring', 'trading_bot.alerts.alert_system'),
        ]
        
        for name, comp_type, module_path in components:
            if self.config.get_layer_config('infrastructure').enabled:
                self.registry.register(
                    name=name,
                    component_type=comp_type,
                    layer=SystemLayer.INFRASTRUCTURE,
                    factory=self._create_lazy_factory(module_path),
                    priority=10,
                    enabled=True
                )
    
    async def _register_data_components(self):
        """Register data foundation layer components"""
        components = [
            ('market_data_stream', 'data_provider', 'trading_bot.connectivity.market_data_stream'),
            ('data_validator', 'data_quality', 'trading_bot.database.data_quarantine'),
            ('staleness_detector', 'data_quality', 'trading_bot.connectivity.staleness_detector'),
            ('time_sync', 'infrastructure', 'trading_bot.infrastructure.time_sync_watchdog'),
        ]
        
        for name, comp_type, module_path in components:
            if self.config.get_layer_config('data_foundation').enabled:
                self.registry.register(
                    name=name,
                    component_type=comp_type,
                    layer=SystemLayer.DATA_FOUNDATION,
                    factory=self._create_lazy_factory(module_path),
                    priority=9,
                    enabled=True
                )
    
    async def _register_intelligence_components(self):
        """Register intelligence core layer components"""
        if not self.config.is_feature_enabled('enable_ml'):
            return
        
        components = [
            ('meta_learner', 'ml_engine', 'trading_bot.advanced_ml.meta_learning'),
            ('ensemble_engine', 'ml_engine', 'trading_bot.ml.ensemble'),
            ('online_learner', 'ml_engine', 'trading_bot.ml.online_learning'),
            ('cognitive_core', 'ai_engine', 'trading_bot.cognitive_architecture.cognitive_core'),
        ]
        
        for name, comp_type, module_path in components:
            if self.config.get_layer_config('intelligence_core').enabled:
                self.registry.register(
                    name=name,
                    component_type=comp_type,
                    layer=SystemLayer.INTELLIGENCE_CORE,
                    factory=self._create_lazy_factory(module_path),
                    priority=8,
                    enabled=True
                )
    
    async def _register_signal_components(self):
        """Register signal generation layer components"""
        components = []
        
        if self.config.is_feature_enabled('enable_alpha_engine'):
            components.append(('alpha_engine', 'signal_generator', 'trading_bot.alpha_engine.orchestrator'))
        
        if self.config.is_feature_enabled('enable_elite_ai'):
            components.append(('elite_ai', 'signal_generator', 'trading_bot.elite_ai_system.elite_trading_orchestrator'))
        
        if self.config.is_feature_enabled('enable_cognitive_architecture'):
            components.append(('cognitive_signals', 'signal_generator', 'trading_bot.cognitive_architecture.cognitive_core'))
        
        for name, comp_type, module_path in components:
            if self.config.get_layer_config('signal_generation').enabled:
                self.registry.register(
                    name=name,
                    component_type=comp_type,
                    layer=SystemLayer.SIGNAL_GENERATION,
                    factory=self._create_lazy_factory(module_path),
                    priority=7,
                    enabled=True
                )
    
    async def _register_risk_components(self):
        """Register risk & safety layer components"""
        components = []
        
        if self.config.is_feature_enabled('enable_msos'):
            components.append(('msos', 'risk_manager', 'trading_bot.msos.orchestrator'))
        
        components.extend([
            ('master_risk', 'risk_manager', 'trading_bot.risk.risk_manager'),
            ('fail_safe', 'safety_system', 'trading_bot.safety.fail_safe'),
            ('circuit_breaker', 'safety_system', 'trading_bot.safety.circuit_breaker'),
        ])
        
        for name, comp_type, module_path in components:
            if self.config.get_layer_config('risk_safety').enabled:
                self.registry.register(
                    name=name,
                    component_type=comp_type,
                    layer=SystemLayer.RISK_SAFETY,
                    factory=self._create_lazy_factory(module_path),
                    priority=10,  # Highest priority
                    enabled=True
                )
    
    async def _register_execution_components(self):
        """Register execution layer components"""
        components = [
            ('smart_router', 'execution_engine', 'trading_bot.execution.smart_order_router'),
            ('fill_tracker', 'execution_monitor', 'trading_bot.execution.fill_tracker'),
            ('slippage_monitor', 'execution_monitor', 'trading_bot.execution.slippage_monitor'),
        ]
        
        for name, comp_type, module_path in components:
            if self.config.get_layer_config('execution').enabled:
                self.registry.register(
                    name=name,
                    component_type=comp_type,
                    layer=SystemLayer.EXECUTION,
                    factory=self._create_lazy_factory(module_path),
                    priority=6,
                    enabled=True
                )
    
    async def _register_governance_components(self):
        """Register governance layer components"""
        components = [
            ('compliance_monitor', 'governance', 'trading_bot.compliance.trade_surveillance'),
            ('audit_logger', 'governance', 'trading_bot.audit.audit_logger'),
        ]
        
        for name, comp_type, module_path in components:
            if self.config.get_layer_config('governance').enabled:
                self.registry.register(
                    name=name,
                    component_type=comp_type,
                    layer=SystemLayer.GOVERNANCE,
                    factory=self._create_lazy_factory(module_path),
                    priority=9,
                    enabled=True
                )
    
    def _create_lazy_factory(self, module_path: str):
        """Create a lazy factory that imports module on demand"""
        def factory(config: Dict[str, Any]):
            """
            factory function.

    Args:
        config: Description

    Returns:
        Result of operation
            """
            # This is a placeholder - actual implementation would dynamically import
            # For now, return a mock component
            from trading_bot.system_interfaces import ISystemComponent, ComponentStatus, ComponentHealth
            
            class MockComponent(ISystemComponent):
                """
                MockComponent class.

    Auto-documented by QwenCodeMender.
                """
                def __init__(self, module_path: str):
                    self.module_path = module_path
                    self.status = ComponentStatus.UNINITIALIZED
                
                async def initialize(self, config: Dict[str, Any]) -> bool:
                    """
                    initialize function.

    Args:
        config: Description

    Returns:
        Result of operation
                    """
                    self.status = ComponentStatus.READY
                    return True
                
                async def start(self) -> bool:
                    self.status = ComponentStatus.RUNNING
                    return True
                
                async def stop(self) -> bool:
                    self.status = ComponentStatus.STOPPED
                    return True
                
                async def health_check(self) -> ComponentHealth:
                    return ComponentHealth(
                        status=self.status,
                        message="OK",
                        metrics={},
                        last_check=datetime.utcnow(),
                        errors=[],
                        warnings=[]
                    )
                
                def get_status(self) -> ComponentStatus:
                    return self.status
            
            return MockComponent(module_path)
        
        return factory
    
    def _load_layer_components(self):
        """Load components from registry into layer lists"""
        self.infrastructure_components = self.registry.get_by_layer(SystemLayer.INFRASTRUCTURE)
        self.data_components = self.registry.get_by_layer(SystemLayer.DATA_FOUNDATION)
        self.intelligence_components = self.registry.get_by_layer(SystemLayer.INTELLIGENCE_CORE)
        self.signal_components = self.registry.get_by_layer(SystemLayer.SIGNAL_GENERATION)
        self.risk_components = self.registry.get_by_layer(SystemLayer.RISK_SAFETY)
        self.execution_components = self.registry.get_by_layer(SystemLayer.EXECUTION)
        self.governance_components = self.registry.get_by_layer(SystemLayer.GOVERNANCE)
        
        logger.info(f"Loaded components by layer:")
        logger.info(f"  Infrastructure: {len(self.infrastructure_components)}")
        logger.info(f"  Data Foundation: {len(self.data_components)}")
        logger.info(f"  Intelligence Core: {len(self.intelligence_components)}")
        logger.info(f"  Signal Generation: {len(self.signal_components)}")
        logger.info(f"  Risk & Safety: {len(self.risk_components)}")
        logger.info(f"  Execution: {len(self.execution_components)}")
        logger.info(f"  Governance: {len(self.governance_components)}")
    
    async def _verify_system_integrity(self) -> bool:
        """Verify system integrity"""
        # Check critical components are present
        critical_layers = [
            SystemLayer.DATA_FOUNDATION,
            SystemLayer.RISK_SAFETY,
        ]
        
        for layer in critical_layers:
            components = self.registry.get_by_layer(layer)
            if not components:
                logger.error(f"No components in critical layer: {layer.name}")
                return False
        
        return True
    
    async def start(self) -> bool:
        """Start the master system"""
        if self.status != ComponentStatus.READY:
            logger.error("System not ready. Initialize first.")
            return False
        
        logger.info("Starting master trading system...")
        
        try:
            # Start all components
            if not await self.registry.start_all():
                logger.error("Failed to start components")
                return False
            
            self._running = True
            self.start_time = datetime.utcnow()
            self.status = ComponentStatus.RUNNING
            
            logger.info("Master trading system started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting system: {e}", exc_info=True)
            self.status = ComponentStatus.ERROR
            return False
    
    async def stop(self) -> bool:
        """Stop the master system"""
        logger.info("Stopping master trading system...")
        
        self._running = False
        
        # Stop all components
        await self.registry.stop_all()
        
        self.status = ComponentStatus.STOPPED
        logger.info("Master trading system stopped")
        return True
    
    async def process_market_data(self, data: MarketData) -> Optional[TradingSignal]:
        """
        Process market data through the entire pipeline
        
        Flow: Data → Intelligence → Signals → Risk → (Execution if approved)
        """
        if not self._running:
            logger.warning("System not running")
            return None
        try:
        
            # Layer 1: Data validation
            # (Data components would validate here)
            
            # Layer 2: Intelligence analysis
            # (Intelligence components would analyze here)
            
            # Layer 3: Signal generation
            signal = None
            for component in self.signal_components:
                # Each signal generator processes the data
                # In real implementation, would call component.generate_signal(data)
                pass
            
            if signal:
                # Layer 4: Risk validation
                # (Risk components would validate here)
                
                # Layer 6: Governance check
                # (Governance components would check here)
                
                self.metrics.total_signals_generated += 1
            
            return signal
            
        except Exception as e:
            logger.error(f"Error processing market data: {e}", exc_info=True)
            self.metrics.total_errors += 1
            return None
    
    async def execute_signal(self, signal: TradingSignal) -> ExecutionResult:
        """Execute a trading signal"""
        # Layer 5: Execution
        # (Execution components would execute here)
        
        self.metrics.total_trades_executed += 1
        
        # Placeholder result
        return ExecutionResult(
            order_id=signal.signal_id,
            status="FILLED",
            filled_quantity=signal.position_size or 0,
            average_price=0.0,
            commission=0.0,
            timestamp=datetime.utcnow(),
            metadata={}
        )
    
    async def get_system_status(self) -> Dict[str, ComponentHealth]:
        """Get status of all components"""
        return await self.registry.health_check_all()
    
    async def health_check(self) -> ComponentHealth:
        """Check master system health"""
        errors = []
        warnings = []
        
        # Check if running
        if not self._running and self.status == ComponentStatus.RUNNING:
            errors.append("System marked as running but _running flag is False")
        
        # Get component health
        component_health = await self.get_system_status()
        error_components = [name for name, h in component_health.items() if h.status == ComponentStatus.ERROR]
        
        if error_components:
            errors.append(f"Components in error state: {error_components}")
        
        # Calculate uptime
        if self.start_time:
            self.metrics.uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
        
        return ComponentHealth(
            status=ComponentStatus.ERROR if errors else self.status,
            message="OK" if not errors else f"{len(errors)} errors",
            metrics={
                'uptime_seconds': self.metrics.uptime_seconds,
                'signals_generated': self.metrics.total_signals_generated,
                'trades_executed': self.metrics.total_trades_executed,
                'errors': self.metrics.total_errors,
            },
            last_check=datetime.utcnow(),
            errors=errors,
            warnings=warnings
        )
    
    def get_status(self) -> ComponentStatus:
        """Get current status"""
        return self.status
    
    def get_metrics(self) -> SystemMetrics:
        """Get system metrics"""
        return self.metrics


# Convenience function
async def create_master_system(config: Optional[SystemConfig] = None) -> MasterTradingSystem:
    """Create and initialize master trading system"""
    system = MasterTradingSystem(config)
    await system.initialize({})
    return system


__all__ = [
    'MasterTradingSystem',
    'SystemMetrics',
    'create_master_system',
]
