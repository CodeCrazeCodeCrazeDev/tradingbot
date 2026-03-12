"""
Network Monitor Integration
Integrates network monitoring with existing AlphaAlgo systems.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class NetworkIntegration:
    """
    Integrates network monitor with:
    - Health Monitor
    - Risk Manager
    - Trading Engine
    - Alert System
    - System Supervisor
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize network integration."""
        self.config = config
        
        # Component references
        self.network_monitor = None
        self.health_monitor = None
        self.risk_manager = None
        self.trading_engine = None
        self.alert_system = None
        self.system_supervisor = None
        
        logger.info("NetworkIntegration initialized")
    
    async def initialize(self):
        """Initialize all integrated components."""
        logger.info("Initializing network integration...")
        
        # Initialize network monitor
        await self._initialize_network_monitor()
        
        # Initialize health monitor integration
        if self.config.get('health_monitor_integration', True):
            await self._initialize_health_monitor()
        
        # Initialize risk manager integration
        if self.config.get('risk_manager_integration', True):
            await self._initialize_risk_manager()
        
        # Initialize trading engine integration
        if self.config.get('trading_engine_integration', True):
            await self._initialize_trading_engine()
        
        # Initialize alert system integration
        if self.config.get('alert_system_integration', True):
            await self._initialize_alert_system()
        
        # Initialize system supervisor integration
        if self.config.get('system_supervisor_integration', True):
            await self._initialize_system_supervisor()
        
        logger.info("Network integration initialized successfully")
    
    async def _initialize_network_monitor(self):
        """Initialize network monitor."""
        try:
            from trading_bot.connectivity.network_monitor import get_network_monitor
            
            network_config = self.config.get('network', {})
            self.network_monitor = get_network_monitor(network_config)
            
            # Start monitoring
            await self.network_monitor.start()
            
            logger.info("Network monitor started")
        
        except Exception as e:
            logger.error(f"Failed to initialize network monitor: {e}")
            raise
    
    async def _initialize_health_monitor(self):
        """Initialize health monitor integration."""
        try:
            from trading_bot.system_health.health_monitor import SystemHealthMonitor
            
            health_config = self.config.get('system_health', {}).get('health_monitor', {})
            self.health_monitor = SystemHealthMonitor(health_config)
            
            # Register network status callback
            async def network_health_callback(alert):
                """Update health monitor with network status."""
                if self.health_monitor:
                    # Add network status to health diagnostics
                    logger.info(f"Network health update: {alert['network_status']}")
            
            self.network_monitor.register_alert_callback(network_health_callback)
            
            logger.info("Health monitor integration enabled")
        
        except Exception as e:
            logger.warning(f"Health monitor integration failed: {e}")
    
    async def _initialize_risk_manager(self):
        """Initialize risk manager integration."""
        try:
            from trading_bot.risk.advanced_risk_manager import AdvancedRiskManager
            
            risk_config = self.config.get('trading', {}).get('risk', {})
            self.risk_manager = AdvancedRiskManager(risk_config)
            
            # Register network status callback
            async def network_risk_callback(alert):
                """Adjust risk parameters based on network status."""
                if self.risk_manager and self.network_monitor:
                    if self.network_monitor.is_safe_mode():
                        # Reduce risk in safe mode
                        logger.info("Risk manager: Reducing risk due to network instability")
                        try:
                            # Implement risk reduction
                            self.risk_manager.set_risk_multiplier(0.5)
                            self.risk_manager.set_max_positions(2)
                            self.risk_manager.set_stop_loss_multiplier(1.5)
                            logger.info("Risk parameters reduced for safe mode")
                        except Exception as e:
                            logger.error(f"Failed to reduce risk: {e}")
                    elif self.network_monitor.is_offline():
                        # Stop all new positions
                        logger.warning("Risk manager: Blocking new positions - network offline")
                        try:
                            # Implement position blocking
                            self.risk_manager.set_trading_allowed(False)
                            logger.info("Trading blocked due to network offline")
                        except Exception as e:
                            logger.error(f"Failed to block trading: {e}")
            
            self.network_monitor.register_alert_callback(network_risk_callback)
            
            logger.info("Risk manager integration enabled")
        
        except Exception as e:
            logger.warning(f"Risk manager integration failed: {e}")
    
    async def _initialize_trading_engine(self):
        """Initialize trading engine integration."""
        try:
            # Register network status callback for trading engine
            async def network_trading_callback(alert):
                """Control trading based on network status."""
                if self.network_monitor:
                    if not self.network_monitor.is_trading_allowed():
                        logger.warning("Trading engine: New trades blocked due to network issues")
                        try:
                            # Implement trading control
                            if hasattr(self, 'trading_engine') and self.trading_engine:
                                self.trading_engine.set_enabled(False)
                                logger.info("Trading engine disabled due to network issues")
                        except Exception as e:
                            logger.error(f"Failed to disable trading engine: {e}")
                    else:
                        logger.info("Trading engine: Normal operations resumed")
                        try:
                            if hasattr(self, 'trading_engine') and self.trading_engine:
                                self.trading_engine.set_enabled(True)
                                logger.info("Trading engine re-enabled")
                        except Exception as e:
                            logger.error(f"Failed to re-enable trading engine: {e}")
            
            self.network_monitor.register_alert_callback(network_trading_callback)
            
            logger.info("Trading engine integration enabled")
        
        except Exception as e:
            logger.warning(f"Trading engine integration failed: {e}")
    
    async def _initialize_alert_system(self):
        """Initialize alert system integration."""
        try:
            from trading_bot.connectivity.network_alerts import NetworkAlertSystem, create_alert_callback
            
            alert_config = self.config.get('alerts', {})
            self.alert_system = NetworkAlertSystem(alert_config)
            
            # Register alert callback
            callback = create_alert_callback(self.alert_system)
            self.network_monitor.register_alert_callback(callback)
            
            logger.info("Alert system integration enabled")
        
        except Exception as e:
            logger.warning(f"Alert system integration failed: {e}")
    
    async def _initialize_system_supervisor(self):
        """Initialize system supervisor integration."""
        try:
            # Register network status callback for system supervisor
            async def network_supervisor_callback(alert):
                """Report network status to system supervisor."""
                logger.info(f"System supervisor: Network status update - {alert['network_status']}")
                try:
                    # Implement supervisor reporting
                    if hasattr(self, 'system_supervisor') and self.system_supervisor:
                        await self.system_supervisor.report_network_status(
                            status=alert.get('network_status', 'unknown'),
                            latency=alert.get('latency', 0),
                            packet_loss=alert.get('packet_loss', 0),
                            timestamp=datetime.now()
                        )
                        if alert.get('network_status') == 'critical':
                            await self.system_supervisor.trigger_emergency_protocol()
                        elif alert.get('network_status') == 'degraded':
                            await self.system_supervisor.trigger_safe_mode()
                except Exception as e:
                    logger.error(f"Failed to report to supervisor: {e}")
            
            self.network_monitor.register_alert_callback(network_supervisor_callback)
            
            logger.info("System supervisor integration enabled")
        
        except Exception as e:
            logger.warning(f"System supervisor integration failed: {e}")
    
    def is_trading_allowed(self) -> bool:
        """Check if trading is allowed based on network status."""
        if self.network_monitor:
            return self.network_monitor.is_trading_allowed()
        return True
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get current network status."""
        if self.network_monitor:
            return self.network_monitor.get_current_status()
        return {'status': 'unknown'}
    
    async def shutdown(self):
        """Shutdown network monitoring."""
        logger.info("Shutting down network integration...")
        
        if self.network_monitor:
            await self.network_monitor.stop()
        
        logger.info("Network integration shutdown complete")


class NetworkAwareTrading:
    """
    Wrapper for trading operations that respects network status.
    Use this to ensure all trading operations check network status first.
    """
    
    def __init__(self, network_integration: NetworkIntegration):
        """Initialize network-aware trading."""
        self.network_integration = network_integration
    
    async def execute_trade(self, trade_params: Dict[str, Any]) -> bool:
        """
        Execute trade with network status check.
        
        Args:
            trade_params: Trade parameters
        
        Returns:
            True if trade executed, False if blocked
        """
        # Check network status
        if not self.network_integration.is_trading_allowed():
            logger.warning("Trade blocked: Network not stable")
            return False
        
        # Check if in safe mode
        if self.network_integration.network_monitor.is_safe_mode():
            logger.warning("Trade blocked: System in Safe Mode")
            return False
        
        # Execute trade
        logger.info("Executing trade with network protection...")
        try:
            # Implement actual trade execution
            if hasattr(self, 'broker') and self.broker:
                result = await self.broker.execute_order(
                    symbol=trade_params.get('symbol'),
                    side=trade_params.get('side'),
                    size=trade_params.get('size'),
                    order_type=trade_params.get('order_type', 'market'),
                    price=trade_params.get('price'),
                    stop_loss=trade_params.get('stop_loss'),
                    take_profit=trade_params.get('take_profit')
                )
                if result.get('success'):
                    logger.info(f"Trade executed: {result.get('ticket')}")
                    return True
                else:
                    logger.error(f"Trade execution failed: {result.get('error')}")
                    return False
            else:
                logger.error("Broker not available")
                return False
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return False
    
    async def modify_position(self, position_id: str, params: Dict[str, Any]) -> bool:
        """
        Modify position with network status check.
        
        Args:
            position_id: Position ID
            params: Modification parameters (SL, TP, etc.)
        
        Returns:
            True if modified, False if blocked
        """
        # Allow modifications in safe mode
        if self.network_integration.network_monitor.is_offline():
            logger.error("Position modification blocked: Network offline")
            return False
        
        logger.info("Modifying position with network protection...")
        try:
            # Implement actual position modification
            if hasattr(self, 'broker') and self.broker:
                result = await self.broker.modify_order(
                    ticket=position_id,
                    stop_loss=params.get('stop_loss'),
                    take_profit=params.get('take_profit')
                )
                if result.get('success'):
                    logger.info(f"Position modified: {position_id}")
                    return True
                else:
                    logger.error(f"Modification failed: {result.get('error')}")
                    return False
            else:
                logger.error("Broker not available")
                return False
        except Exception as e:
            logger.error(f"Position modification error: {e}")
            return False
    
    async def close_position(self, position_id: str) -> bool:
        """
        Close position with network status check.
        
        Args:
            position_id: Position ID
        
        Returns:
            True if closed, False if blocked
        """
        # Allow closing in safe mode
        if self.network_integration.network_monitor.is_offline():
            logger.error("Position close blocked: Network offline")
            return False
        
        logger.info("Closing position with network protection...")
        try:
            # Implement actual position close
            if hasattr(self, 'broker') and self.broker:
                result = await self.broker.close_order(ticket=position_id)
                if result.get('success'):
                    logger.info(f"Position closed: {position_id}")
                    return True
                else:
                    logger.error(f"Close failed: {result.get('error')}")
                    return False
            else:
                logger.error("Broker not available")
                return False
        except Exception as e:
            logger.error(f"Position close error: {e}")
            return False
    
    async def api_call_with_retry(self, api_func, *args, **kwargs):
        """
        Execute API call with network-aware retry logic.
        
        Args:
            api_func: Async API function to call
            *args, **kwargs: Function arguments
        
        Returns:
            API call result
        """
        if self.network_integration.network_monitor:
            return await self.network_integration.network_monitor.api_call_with_retry(
                api_func, *args, **kwargs
            )
        else:
            # Fallback to direct call
            return await api_func(*args, **kwargs)
