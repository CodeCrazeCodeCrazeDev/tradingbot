"""
from typing import Optional, Set
AlphaAlgo Unified Main - Single Entry Point

This is the SINGLE entry point for the entire trading bot.
It coordinates all layers and provides a clean interface.

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    HUMAN LAYER                               │
    │  (Approval Gate, Dashboard, Alerts, Manual Override)         │
    └─────────────────────────────────────────────────────────────┘
                              │
    ┌─────────────────────────────────────────────────────────────┐
    │                   EVOLUTION LAYER                            │
    │  (Immutable Reward Model, Learner, Optimizer, Evolver)       │
    └─────────────────────────────────────────────────────────────┘
                              │
    ┌─────────────────────────────────────────────────────────────┐
    │                   TELEMETRY LAYER                            │
    │  (Metrics, Logging, Tracing, Health Checks)                  │
    └─────────────────────────────────────────────────────────────┘
                              │
    ┌─────────────────────────────────────────────────────────────┐
    │                    CORE API LAYER                            │
    │  (Stable Interfaces, Types, Events, Exceptions)              │
    └─────────────────────────────────────────────────────────────┘
                              │
    ┌─────────────────────────────────────────────────────────────┐
    │                 DOMAIN SUPER-MODULES                         │
    │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
    │  │  DATA   │ │ INTEL   │ │STRATEGY │ │  RISK   │            │
    │  │ ENGINE  │ │ LIGENCE │ │ ENGINE  │ │ ENGINE  │            │
    │  └─────────┘ └─────────┘ └─────────┘ └─────────┘            │
    │  ┌─────────┐                                                 │
    │  │EXECUTION│                                                 │
    │  │ ENGINE  │                                                 │
    │  └─────────┘                                                 │
    └─────────────────────────────────────────────────────────────┘

Version: 2.0.0
"""

import asyncio
import logging
logger = logging.getLogger(__name__)
import signal
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Core API
from .core_api import (
    TradingMode,
    SystemStatus,
    HealthStatus,
    EventBus,
    EventType,
    create_system_event,
)

# Evolution Layer
from .evolution_layer import (
    get_reward_model,
    verify_reward_model_integrity,
    get_evolution_orchestrator,
    record_trade_experience,
)

# Human Layer
from .human_layer import (
    get_approval_gate,
    get_alert_manager,
    get_manual_override,
    get_dashboard,
    is_trading_allowed,
    AlertPriority,
)

# Telemetry
from .telemetry import (
    setup_logging,
    get_logger,
    LogLevel,
    get_metrics_collector,
    get_health_checker,
    get_tracer,
    HealthStatus as TelemetryHealthStatus,
)

logger = get_logger(__name__)


class UnifiedTradingSystem:
    """
    The Unified Trading System - Single Entry Point
    
    This class coordinates all layers and provides a clean interface
    for running the trading bot.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # System state
        self._status = SystemStatus.STOPPED
        self._trading_mode = TradingMode(self.config.get('trading_mode', 'paper'))
        self._start_time: Optional[datetime] = None
        
        # Initialize layers
        self._init_telemetry()
        self._init_core_api()
        self._init_evolution_layer()
        self._init_human_layer()
        
        # Background tasks
        self._tasks: list = []
        self._shutdown_event = asyncio.Event()
        
        logger.info("UnifiedTradingSystem initialized", data={
            'trading_mode': self._trading_mode.value,
            'config_keys': list(self.config.keys()),
        })
    
    def _init_telemetry(self) -> None:
        """Initialize telemetry layer"""
        log_dir = self.config.get('log_dir', 'logs')
        setup_logging(
            level=LogLevel.INFO,
            log_dir=log_dir,
            console=True,
            file=True,
        )
        
        self._metrics = get_metrics_collector()
        self._health = get_health_checker()
        self._tracer = get_tracer()
        
        # Register health checks
        self._health.register_check('reward_model', self._check_reward_model)
        self._health.register_check('evolution', self._check_evolution)
        self._health.register_check('human_layer', self._check_human_layer)
    
    def _init_core_api(self) -> None:
        """Initialize core API layer"""
        self._event_bus = EventBus()
    
    def _init_evolution_layer(self) -> None:
        """Initialize evolution layer"""
        # Verify reward model integrity
        if not verify_reward_model_integrity():
            raise RuntimeError("CRITICAL: Reward model integrity check failed!")
        
        self._reward_model = get_reward_model()
        self._evolution = get_evolution_orchestrator(self.config)
        
        logger.info("Evolution layer initialized", data={
            'reward_model_version': self._reward_model.version,
            'reward_model_hash': self._reward_model.model_hash[:16],
        })
    
    def _init_human_layer(self) -> None:
        """Initialize human layer"""
        self._approval_gate = get_approval_gate(self.config)
        self._alert_manager = get_alert_manager(self.config)
        self._override = get_manual_override(self.config)
        self._dashboard = get_dashboard(self.config)
        
        # Set trading mode in approval gate
        self._approval_gate.set_trading_mode(self._trading_mode.value)
    
    # =========================================================================
    # HEALTH CHECKS
    # =========================================================================
    
    async def _check_reward_model(self) -> tuple:
        """Check reward model health"""
        if verify_reward_model_integrity():
            return (TelemetryHealthStatus.HEALTHY, "Reward model intact", {})
        return (TelemetryHealthStatus.CRITICAL, "Reward model compromised!", {})
    
    async def _check_evolution(self) -> tuple:
        """Check evolution layer health"""
        status = self._evolution.get_status()
        if status.get('reward_model_valid', False):
            return (TelemetryHealthStatus.HEALTHY, "Evolution layer healthy", status)
        return (TelemetryHealthStatus.UNHEALTHY, "Evolution layer issue", status)
    
    async def _check_human_layer(self) -> tuple:
        """Check human layer health"""
        pending = len(self._approval_gate.get_pending_requests())
        return (TelemetryHealthStatus.HEALTHY, f"{pending} pending approvals", {'pending': pending})
    
    # =========================================================================
    # LIFECYCLE
    # =========================================================================
    
    async def start(self) -> None:
        """Start the trading system"""
        if self._status != SystemStatus.STOPPED:
            logger.warning("System already running")
            return
        
        logger.info("Starting UnifiedTradingSystem...")
        self._status = SystemStatus.STARTING
        self._start_time = datetime.now()
        
        # Verify reward model one more time
        if not verify_reward_model_integrity():
            await self._alert_manager.send_alert(
                AlertPriority.EMERGENCY,
                "CRITICAL: Reward Model Compromised",
                "The reward model integrity check failed. System cannot start.",
                category="security"
            )
            raise RuntimeError("Reward model integrity check failed")
        
        # Start health checks
        await self._health.start_background_checks()
        
        # Start evolution layer
        await self._evolution.start()
        
        # Publish system started event
        await self._event_bus.publish(create_system_event(
            EventType.SYSTEM_STARTED,
            source="unified_main",
            component="UnifiedTradingSystem",
            status="started",
            message="System started successfully"
        ))
        
        # Send startup alert
        await self._alert_manager.send_alert(
            AlertPriority.MEDIUM,
            "Trading System Started",
            f"AlphaAlgo started in {self._trading_mode.value} mode",
            category="system"
        )
        
        self._status = SystemStatus.RUNNING
        logger.info("UnifiedTradingSystem started successfully")
    
    async def stop(self) -> None:
        """Stop the trading system"""
        if self._status == SystemStatus.STOPPED:
            return
        
        logger.info("Stopping UnifiedTradingSystem...")
        self._status = SystemStatus.STOPPING
        self._shutdown_event.set()
        
        # Stop evolution layer
        await self._evolution.stop()
        
        # Stop health checks
        await self._health.stop_background_checks()
        
        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Publish system stopped event
        await self._event_bus.publish(create_system_event(
            EventType.SYSTEM_STOPPED,
            source="unified_main",
            component="UnifiedTradingSystem",
            status="stopped",
            message="System stopped"
        ))
        
        self._status = SystemStatus.STOPPED
        logger.info("UnifiedTradingSystem stopped")
    
    async def run(self) -> None:
        """Run the main trading loop"""
        await self.start()
        
        try:
            while not self._shutdown_event.is_set():
                # Check if trading is allowed
                if not is_trading_allowed():
                    logger.info("Trading paused by human override")
                    await asyncio.sleep(1)
                    continue
                
                # Main trading cycle
                await self._trading_cycle()
                
                # Small delay between cycles
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info("Main loop cancelled")
        except Exception as e:
            logger.exception(f"Error in main loop: {e}")
            await self._alert_manager.send_alert(
                AlertPriority.CRITICAL,
                "Trading Loop Error",
                str(e),
                category="error"
            )
        finally:
            await self.stop()
    
    async def _trading_cycle(self) -> None:
        """Single trading cycle"""
        with self._tracer.span("trading_cycle") as span:
            try:
                # Update metrics
                self._metrics.set_gauge('system.status', 1)
                
                # This is where the actual trading logic would go
                # For now, just a placeholder
                
                span.set_tag('status', 'ok')
                
            except Exception as e:
                span.set_tag('error', True)
                span.log(f"Error: {e}")
                self._metrics.record_error()
                raise
    
    # =========================================================================
    # STATUS & CONTROL
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        uptime = (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
        
        return {
            'status': self._status.value,
            'trading_mode': self._trading_mode.value,
            'uptime_seconds': uptime,
            'health': self._health.get_health_report(),
            'metrics': self._metrics.get_all_metrics(),
            'evolution': self._evolution.get_status(),
            'pending_approvals': len(self._approval_gate.get_pending_requests()),
            'trading_allowed': is_trading_allowed(),
            'reward_model': {
                'version': self._reward_model.version,
                'hash': self._reward_model.model_hash[:16],
                'valid': verify_reward_model_integrity(),
            },
        }
    
    def get_constraints(self) -> Dict[str, Any]:
        """Get reward model constraints"""
        return self._reward_model.get_constraints_dict()
    
    async def request_approval(self, action: str, description: str, details: Dict[str, Any]) -> bool:
        """Request human approval for an action"""
        return await self._approval_gate.request_approval(action, description, details)
    
    def approve_request(self, request_id: str, approver: str) -> bool:
        """Approve a pending request"""
        return self._approval_gate.approve(request_id, approver)
    
    def reject_request(self, request_id: str, reason: str) -> bool:
        """Reject a pending request"""
        return self._approval_gate.reject(request_id, reason)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main(config: Optional[Dict[str, Any]] = None) -> None:
    """Main entry point"""
    config = config or {}
    
    # Create system
    system = UnifiedTradingSystem(config)
    
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(system.stop())
    
    for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)
            # Windows doesn't support add_signal_handler
            pass
    
    # Run system
    await system.run()


def run(config: Optional[Dict[str, Any]] = None) -> None:
    """Synchronous entry point"""
    try:
        asyncio.run(main(config))
    except KeyboardInterrupt:
        logger.info("\nShutdown requested...")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AlphaAlgo Trading Bot")
    parser.add_argument('--mode', choices=['live', 'paper', 'backtest'], default='paper')
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--log-level', choices=['debug', 'info', 'warning', 'error'], default='info')
    
    args = parser.parse_args()
    
    config = {
        'trading_mode': args.mode,
        'log_level': args.log_level,
    }
    
    if args.config:
        import yaml
        with open(args.config) as f:
            config.update(yaml.safe_load(f))
    
    run(config)
