"""
Unified Master System - The central orchestrator integrating all 11 layers

This is the main entry point for the entire trading system, coordinating
all 177+ modules through the 11-layer architecture.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .unified_types import (
    SystemStatus,
    LayerStatus,
    TradingMode,
    OperationMode,
    MarketRegime,
    MarketData,
    TradingSignal,
    TradingDecision,
    Order,
    Position,
    RiskMetrics,
    SystemHealth,
)
from .unified_config import UnifiedConfig, get_config
from .layer_registry import LayerRegistry, get_layer_registry
from .layer_interfaces import (
    ILayer,
    IInfrastructureLayer,
    IObservabilityLayer,
    IConnectivityLayer,
    IDataFoundationLayer,
    IIntelligenceLayer,
    ISignalLayer,
    IRiskSafetyLayer,
    IDecisionLayer,
    IExecutionLayer,
    IOrchestrationLayer,
    IGovernanceLayer,
)

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System-wide metrics"""
    uptime_seconds: float = 0.0
    total_signals: int = 0
    total_trades: int = 0
    total_errors: int = 0
    active_positions: int = 0
    current_capital: float = 0.0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0


class UnifiedMasterSystem:
    """
    Unified Master System - Central orchestrator for the trading bot
    
    Integrates all 11 architecture layers:
    - Layer 0: Infrastructure & Hardware
    - Layer 1: Observability & Health
    - Layer 2: Connectivity & Ingestion
    - Layer 3: Data Foundation
    - Layer 4: Intelligence Core
    - Layer 5: Signal Generation
    - Layer 6: Risk & Safety
    - Layer 7: Decision Verification
    - Layer 8: Execution
    - Layer 9: Orchestration
    - Layer 10: Governance
    
    Usage:
        system = UnifiedMasterSystem()
        await system.initialize()
        await system.start()
        
        # Process market data
        decision = await system.process_tick(market_data)
        
        # Shutdown
        await system.shutdown()
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the master system
        
        Args:
            config: Optional configuration dictionary
        """
        # Configuration
        if isinstance(config, UnifiedConfig):
            self.config = config
        elif isinstance(config, dict):
            self.config = UnifiedConfig.from_dict(config)
        else:
            self.config = get_config()
        
        # Registry
        self.registry = get_layer_registry()
        
        # State
        self.status = SystemStatus.OFFLINE
        self.start_time: Optional[datetime] = None
        self.metrics = SystemMetrics(current_capital=self.config.initial_capital)
        
        # Locks
        self._lock = asyncio.Lock()
        self._running = False
        
        # Event handlers
        self._on_signal_handlers: List = []
        self._on_trade_handlers: List = []
        self._on_error_handlers: List = []
        
        logger.info(f"UnifiedMasterSystem created: {self.config.system_name} v{self.config.system_version}")
    
    async def initialize(self) -> bool:
        """
        Initialize the master system and all layers
        
        Returns:
            True if initialization successful
        """
        logger.info("=" * 80)
        logger.info("INITIALIZING UNIFIED MASTER SYSTEM")
        logger.info(f"System: {self.config.system_name} v{self.config.system_version}")
        logger.info(f"Mode: {self.config.trading_mode.value}")
        logger.info(f"Environment: {self.config.environment}")
        logger.info("=" * 80)
        
        try:
            self.status = SystemStatus.INITIALIZING
            
            # Step 1: Validate configuration
            logger.info("\n[1/6] Validating configuration...")
            valid, errors = self.config.validate()
            if not valid:
                for error in errors:
                    logger.error(f"Config error: {error}")
                return False
            logger.info("Configuration valid")
            
            # Step 2: Register all layers
            logger.info("\n[2/6] Registering layers...")
            await self._register_layers()
            
            # Step 3: Initialize all layers
            logger.info("\n[3/6] Initializing layers...")
            if not await self.registry.initialize_all(self.config.to_dict()):
                logger.error("Failed to initialize layers")
                self.status = SystemStatus.OFFLINE
                return False
            
            # Step 4: Verify layer dependencies
            logger.info("\n[4/6] Verifying layer dependencies...")
            if not await self._verify_dependencies():
                logger.error("Layer dependency verification failed")
                return False
            
            # Step 5: Run health checks
            logger.info("\n[5/6] Running health checks...")
            health_results = await self.registry.health_check_all()
            unhealthy = [
                layer_id for layer_id, metrics in health_results.items()
                if metrics.status == LayerStatus.ERROR
            ]
            if unhealthy:
                logger.warning(f"Unhealthy layers: {unhealthy}")
            
            # Step 6: Initialize metrics
            logger.info("\n[6/6] Initializing metrics...")
            self.metrics = SystemMetrics(current_capital=self.config.initial_capital)
            
            self.status = SystemStatus.READY
            logger.info("\n" + "=" * 80)
            logger.info("UNIFIED MASTER SYSTEM INITIALIZED SUCCESSFULLY")
            logger.info("=" * 80)
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization error: {e}", exc_info=True)
            self.status = SystemStatus.OFFLINE
            return False
    
    async def _register_layers(self):
        """Register all layer implementations"""
        # Import layer implementations
        from .layers import (
            InfrastructureLayerImpl,
            ObservabilityLayerImpl,
            ConnectivityLayerImpl,
            DataFoundationLayerImpl,
            IntelligenceLayerImpl,
            SignalLayerImpl,
            RiskSafetyLayerImpl,
            DecisionLayerImpl,
            ExecutionLayerImpl,
            OrchestrationLayerImpl,
            GovernanceLayerImpl,
        )
        
        # Register each layer
        layers = [
            (0, InfrastructureLayerImpl),
            (1, ObservabilityLayerImpl),
            (2, ConnectivityLayerImpl),
            (3, DataFoundationLayerImpl),
            (4, IntelligenceLayerImpl),
            (5, SignalLayerImpl),
            (6, RiskSafetyLayerImpl),
            (7, DecisionLayerImpl),
            (8, ExecutionLayerImpl),
            (9, OrchestrationLayerImpl),
            (10, GovernanceLayerImpl),
        ]
        
        for layer_id, layer_class in layers:
            layer_config = self.config.layer_configs.get(layer_id, {})
            self.registry.register(
                layer_id=layer_id,
                layer_class=layer_class,
                config=layer_config if isinstance(layer_config, dict) else {},
                enabled=True,
            )
    
    async def _verify_dependencies(self) -> bool:
        """Verify all layer dependencies are satisfied"""
        for layer_id in self.registry.list_layers():
            layer = self.registry.get(layer_id)
            if layer is None:
                continue
            
            deps = layer.get_dependencies()
            for dep_id in deps:
                dep_layer = self.registry.get(dep_id)
                if dep_layer is None:
                    logger.error(f"Layer {layer_id} depends on missing layer {dep_id}")
                    return False
        
        return True
    
    async def start(self) -> bool:
        """
        Start the trading system
        
        Returns:
            True if started successfully
        """
        if self.status != SystemStatus.READY:
            logger.error(f"Cannot start: system is {self.status.value}")
            return False
        
        logger.info("Starting Unified Master System...")
        
        try:
            # Start all layers
            if not await self.registry.start_all():
                logger.error("Failed to start layers")
                return False
            
            self.status = SystemStatus.RUNNING
            self.start_time = datetime.utcnow()
            self._running = True
            
            logger.info("Unified Master System started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Start error: {e}", exc_info=True)
            return False
    
    async def stop(self) -> bool:
        """
        Stop the trading system gracefully
        
        Returns:
            True if stopped successfully
        """
        logger.info("Stopping Unified Master System...")
        
        self._running = False
        
        try:
            # Stop all layers
            await self.registry.stop_all()
            
            self.status = SystemStatus.SHUTDOWN
            logger.info("Unified Master System stopped")
            return True
            
        except Exception as e:
            logger.error(f"Stop error: {e}", exc_info=True)
            return False
    
    async def shutdown(self) -> bool:
        """Alias for stop()"""
        return await self.stop()
    
    async def process_tick(self, data: MarketData) -> Optional[TradingDecision]:
        """
        Process a market tick through the full pipeline
        
        Args:
            data: Market data tick
            
        Returns:
            Trading decision if signal generated, None otherwise
        """
        if not self._running:
            return None
        try:
        
            # Layer 3: Data Foundation - Validate and enrich data
            data_layer: IDataFoundationLayer = self.registry.get(3)
            if data_layer and not await data_layer.validate_data(data):
                logger.warning(f"Data validation failed for {data.symbol}")
                return None
            
            # Layer 4: Intelligence - Get predictions
            intel_layer: IIntelligenceLayer = self.registry.get(4)
            if intel_layer:
                regime = await intel_layer.detect_regime(data.symbol)
            else:
                regime = MarketRegime.UNKNOWN.value
            
            # Layer 5: Signal Generation - Generate signals
            signal_layer: ISignalLayer = self.registry.get(5)
            if signal_layer:
                signals = await signal_layer.generate_signals(data.symbol, data)
                if not signals:
                    return None
                
                # Blend signals
                signal = await signal_layer.blend_signals(signals)
            else:
                return None
            
            # Layer 6: Risk & Safety - Validate trade
            risk_layer: IRiskSafetyLayer = self.registry.get(6)
            if risk_layer:
                valid, reason = await risk_layer.validate_trade(signal)
                if not valid:
                    logger.info(f"Trade rejected by risk layer: {reason}")
                    return None
                
                # Check circuit breakers
                if not await risk_layer.check_circuit_breakers():
                    logger.warning("Circuit breaker triggered")
                    return None
                
                # Calculate position size
                position_size = await risk_layer.calculate_position_size(signal)
                signal.position_size = position_size
            
            # Layer 7: Decision Verification - Verify signal
            decision_layer: IDecisionLayer = self.registry.get(7)
            if decision_layer:
                verified, score, reason = await decision_layer.verify_signal(signal)
                if not verified:
                    logger.info(f"Signal not verified: {reason}")
                    return None
                
                signal.verified = True
                signal.verification_score = score
                
                # Generate final decision
                decision = await decision_layer.generate_decision(signal)
            else:
                return None
            
            # Layer 10: Governance - Request approval if needed
            gov_layer: IGovernanceLayer = self.registry.get(10)
            if gov_layer and self.config.governance.require_human_approval:
                approved, reason = await gov_layer.request_approval(
                    "trade",
                    {"decision": decision, "signal": signal}
                )
                if not approved:
                    logger.info(f"Trade not approved: {reason}")
                    return None
            
            # Update metrics
            self.metrics.total_signals += 1
            
            # Notify handlers
            for handler in self._on_signal_handlers:
                await handler(signal)
            
            return decision
            
        except Exception as e:
            logger.error(f"Error processing tick: {e}", exc_info=True)
            self.metrics.total_errors += 1
            return None
    
    async def execute_decision(self, decision: TradingDecision) -> Optional[Order]:
        """
        Execute a trading decision
        
        Args:
            decision: Trading decision to execute
            
        Returns:
            Executed order if successful, None otherwise
        """
        if not self._running:
            return None
        try:
        
            # Layer 8: Execution
            exec_layer: IExecutionLayer = self.registry.get(8)
            if not exec_layer:
                logger.error("Execution layer not available")
                return None
            
            # Create order from decision
            order = Order(
                order_id=f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                symbol=decision.signal.symbol,
                side=decision.action,
                order_type=self.config.execution.default_order_type,
                quantity=decision.position_size,
                price=decision.entry_price,
                stop_price=decision.stop_loss,
                signal_id=decision.signal.signal_id,
            )
            
            # Execute
            executed_order = await exec_layer.execute_order(order)
            
            # Log to governance
            gov_layer: IGovernanceLayer = self.registry.get(10)
            if gov_layer:
                await gov_layer.audit_log("trade_executed", {
                    "order": executed_order,
                    "decision": decision,
                })
            
            # Update metrics
            self.metrics.total_trades += 1
            
            # Notify handlers
            for handler in self._on_trade_handlers:
                await handler(executed_order)
            
            return executed_order
            
        except Exception as e:
            logger.error(f"Error executing decision: {e}", exc_info=True)
            self.metrics.total_errors += 1
            return None
    
    async def emergency_stop(self) -> bool:
        """
        Trigger emergency stop - close all positions and halt trading
        
        Returns:
            True if emergency stop successful
        """
        logger.critical("EMERGENCY STOP TRIGGERED")
        
        try:
            # Layer 6: Risk - Emergency stop
            risk_layer: IRiskSafetyLayer = self.registry.get(6)
            if risk_layer:
                await risk_layer.emergency_stop()
            
            # Layer 8: Execution - Close all positions
            exec_layer: IExecutionLayer = self.registry.get(8)
            if exec_layer:
                await exec_layer.close_all_positions()
            
            # Layer 10: Governance - Emergency shutdown
            gov_layer: IGovernanceLayer = self.registry.get(10)
            if gov_layer:
                await gov_layer.emergency_shutdown()
            
            self.status = SystemStatus.EMERGENCY
            self._running = False
            
            logger.critical("EMERGENCY STOP COMPLETED")
            return True
            
        except Exception as e:
            logger.critical(f"Emergency stop error: {e}", exc_info=True)
            return False
    
    async def get_health(self) -> SystemHealth:
        """
        Get system health status
        
        Returns:
            System health metrics
        """
        uptime = 0.0
        if self.start_time:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        # Get layer status
        layer_status = {}
        for layer_id in self.registry.list_layers():
            info = self.registry.get_info(layer_id)
            if info:
                layer_status[info.layer_name] = info.status
        
        # Get positions
        exec_layer: IExecutionLayer = self.registry.get(8)
        positions = []
        if exec_layer:
            positions = await exec_layer.get_positions()
        
        return SystemHealth(
            status=self.status,
            uptime_seconds=uptime,
            layer_status=layer_status,
            signals_generated=self.metrics.total_signals,
            trades_executed=self.metrics.total_trades,
            active_positions=len(positions),
            error_count=self.metrics.total_errors,
        )
    
    async def get_positions(self) -> List[Position]:
        """Get all open positions"""
        exec_layer: IExecutionLayer = self.registry.get(8)
        if exec_layer:
            return await exec_layer.get_positions()
        return []
    
    async def get_risk_metrics(self) -> RiskMetrics:
        """Get current risk metrics"""
        risk_layer: IRiskSafetyLayer = self.registry.get(6)
        if risk_layer:
            return await risk_layer.get_risk_metrics()
        return RiskMetrics()
    
    def on_signal(self, handler):
        """Register signal handler"""
        self._on_signal_handlers.append(handler)
    
    def on_trade(self, handler):
        """Register trade handler"""
        self._on_trade_handlers.append(handler)
    
    def on_error(self, handler):
        """Register error handler"""
        self._on_error_handlers.append(handler)
    
    def get_status(self) -> SystemStatus:
        """Get current system status"""
        return self.status
    
    def get_metrics(self) -> SystemMetrics:
        """Get system metrics"""
        if self.start_time:
            self.metrics.uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
        return self.metrics
    
    def get_summary(self) -> Dict[str, Any]:
        """Get system summary"""
        return {
            "system_name": self.config.system_name,
            "version": self.config.system_version,
            "status": self.status.value,
            "trading_mode": self.config.trading_mode.value,
            "environment": self.config.environment,
            "uptime_seconds": self.metrics.uptime_seconds,
            "layers": self.registry.get_summary(),
            "metrics": {
                "total_signals": self.metrics.total_signals,
                "total_trades": self.metrics.total_trades,
                "total_errors": self.metrics.total_errors,
                "win_rate": self.metrics.win_rate,
            }
        }


async def quick_start(config: Optional[Dict[str, Any]] = None) -> UnifiedMasterSystem:
    """
    Quick start the unified trading system
    
    Args:
        config: Optional configuration
        
    Returns:
        Initialized UnifiedMasterSystem
    """
    system = UnifiedMasterSystem(config)
    await system.initialize()
    return system
