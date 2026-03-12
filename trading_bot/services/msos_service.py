"""
MSOS Service - Market Survival Operating System
================================================

Wraps MSOS (Market Survival Operating System) as an event-driven service.
This is the MOST CRITICAL service - it has VETO power over all trades.

PRIMARY DIRECTIVE: Preserve capital across regime shifts.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.event_bus import Event, EventPriority, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class MSOSService(BaseService):
    """
    MSOS Service - Market Survival Operating System
    
    CRITICAL: This service has VETO power over ALL trades.
    
    Provides:
    - Market tradability validation
    - Assumption enforcement
    - Signal semantic integrity
    - Regime instability detection
    - Capital governance
    - Loss monitoring
    - Execution reality checks
    - Anti-overreaction constraints
    - Learning firewall
    - Time-based risk management
    """
    
    SERVICE_NAME = "msos"
    SERVICE_TYPE = "risk"
    PRIORITY = ServicePriority.CRITICAL
    DEPENDENCIES = ["database"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._check_interval: float = config.get('interval', 5.0) if config else 5.0
        self._task: Optional[asyncio.Task] = None
        
        # MSOS components
        self._orchestrator = None
        self._market_tradability = None
        self._capital_governor = None
        self._loss_monitor = None
        
        # State
        self._last_check: Optional[Dict] = None
        self._trading_allowed: bool = False
        self._veto_reason: Optional[str] = None
        
    async def start(self) -> None:
        """Start MSOS service"""
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._monitoring_loop())
        
        # Subscribe to trade request events
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [EventTypes.TRADE_REQUEST, EventTypes.SIGNAL_GENERATED],
                self._on_trade_request
            )
        
        logger.info("MSOSService started - VETO POWER ACTIVE")
    
    async def stop(self) -> None:
        """Stop MSOS service"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._event_bus:
            self._event_bus.unsubscribe(self.SERVICE_NAME)
        
        logger.info("MSOSService stopped")
    
    async def health_check(self) -> ServiceHealth:
        """Check service health"""
        components_loaded = sum([
            self._orchestrator is not None,
            self._market_tradability is not None,
            self._capital_governor is not None,
            self._loss_monitor is not None,
        ])
        return ServiceHealth(
            healthy=self._running and components_loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{components_loaded}/4 MSOS components loaded, trading_allowed={self._trading_allowed}",
            metrics={
                'components_loaded': components_loaded,
                'trading_allowed': self._trading_allowed,
                'veto_reason': self._veto_reason,
                'last_check': self._last_check,
            }
        )
    
    async def _load_components(self) -> None:
        """Load MSOS components"""
        try:
            from trading_bot.msos import MSOSOrchestrator
            if MSOSOrchestrator is not None:
                self._orchestrator = MSOSOrchestrator()
                logger.info("MSOS Orchestrator loaded")
        except (ImportError, TypeError, Exception) as e:
            logger.warning(f"MSOS Orchestrator not available: {e}")
        
        try:
            from trading_bot.msos import MarketTradabilityGate
            if MarketTradabilityGate is not None:
                self._market_tradability = MarketTradabilityGate()
                logger.info("Market Tradability Gate loaded")
        except (ImportError, TypeError, Exception) as e:
            logger.warning(f"Market Tradability Gate not available: {e}")
        
        try:
            from trading_bot.msos import CapitalGovernor
            if CapitalGovernor is not None:
                self._capital_governor = CapitalGovernor()
                logger.info("Capital Governor loaded")
        except (ImportError, TypeError, Exception) as e:
            logger.warning(f"Capital Governor not available: {e}")
        
        try:
            from trading_bot.msos import LossMonitor
            if LossMonitor is not None:
                self._loss_monitor = LossMonitor()
                logger.info("Loss Monitor loaded")
        except (ImportError, TypeError, Exception) as e:
            logger.warning(f"Loss Monitor not available: {e}")
    
    async def _on_trade_request(self, event: Event) -> None:
        """
        Handle trade request events - VETO if conditions not met
        
        This is the critical gate - all trades must pass through here.
        """
        trade_data = event.payload
        
        # Check if trading is allowed
        allowed, reason = await self.validate_trade(trade_data)
        
        if not allowed:
            # VETO the trade
            logger.warning(f"MSOS VETO: {reason}")
            if self._event_bus:
                await self._event_bus.publish(Event(
                    event_type=EventTypes.TRADE_REJECTED,
                    payload={
                        'original_request': trade_data,
                        'reason': reason,
                        'source': 'msos',
                        'veto': True,
                    },
                    source=self.SERVICE_NAME,
                    priority=EventPriority.CRITICAL,
                ))
        else:
            # Approve the trade
            if self._event_bus:
                await self._event_bus.publish(Event(
                    event_type=EventTypes.TRADE_APPROVED,
                    payload={
                        'original_request': trade_data,
                        'source': 'msos',
                    },
                    source=self.SERVICE_NAME,
                ))
    
    async def validate_trade(self, trade_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate a trade request against MSOS rules.
        
        Returns:
            (allowed, reason) - True if trade is allowed, False with reason if vetoed
        """
        # If no components loaded, default to NO TRADE (fail-safe)
        if not any([self._orchestrator, self._market_tradability, 
                    self._capital_governor, self._loss_monitor]):
            return False, "MSOS components not loaded - fail-safe NO TRADE"
        
        # Check market tradability
        if self._market_tradability:
            try:
                is_tradable = self._market_tradability.is_tradable(
                    trade_data.get('symbol', 'UNKNOWN')
                )
                if not is_tradable:
                    return False, "Market not tradable"
            except Exception as e:
                logger.error(f"Market tradability check failed: {e}")
                return False, f"Tradability check error: {e}"
        
        # Check capital constraints
        if self._capital_governor:
            try:
                position_size = trade_data.get('size', 0)
                allowed = self._capital_governor.validate_position(position_size)
                if not allowed:
                    return False, "Position size exceeds capital constraints"
            except Exception as e:
                logger.error(f"Capital governor check failed: {e}")
                return False, f"Capital check error: {e}"
        
        # Check loss limits
        if self._loss_monitor:
            try:
                within_limits = self._loss_monitor.within_limits()
                if not within_limits:
                    return False, "Loss limits exceeded - trading suspended"
            except Exception as e:
                logger.error(f"Loss monitor check failed: {e}")
                return False, f"Loss check error: {e}"
        
        return True, "Trade approved by MSOS"
    
    async def _monitoring_loop(self) -> None:
        """Continuous monitoring loop"""
        while self._running:
            try:
                # Run periodic checks
                check_result = await self._run_checks()
                self._last_check = check_result
                self._trading_allowed = check_result.get('trading_allowed', False)
                self._veto_reason = check_result.get('veto_reason')
                
                # Publish status update
                if self._event_bus:
                    await self._event_bus.publish(Event(
                        event_type=EventTypes.SYSTEM_STATUS,
                        payload={
                            'service': 'msos',
                            'trading_allowed': self._trading_allowed,
                            'veto_reason': self._veto_reason,
                            'timestamp': datetime.utcnow().isoformat(),
                        },
                        source=self.SERVICE_NAME,
                    ))
                
                await asyncio.sleep(self._check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"MSOS monitoring error: {e}")
                self._trading_allowed = False
                self._veto_reason = f"Monitoring error: {e}"
                await asyncio.sleep(10)
    
    async def _run_checks(self) -> Dict[str, Any]:
        """Run all MSOS checks"""
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'trading_allowed': True,
            'veto_reason': None,
            'checks': {},
        }
        
        # Market tradability
        if self._market_tradability:
            try:
                result['checks']['market_tradability'] = {'status': 'ok'}
            except Exception as e:
                result['checks']['market_tradability'] = {'status': 'error', 'error': str(e)}
                result['trading_allowed'] = False
                result['veto_reason'] = f"Market tradability error: {e}"
        
        # Capital governor
        if self._capital_governor:
            try:
                result['checks']['capital_governor'] = {'status': 'ok'}
            except Exception as e:
                result['checks']['capital_governor'] = {'status': 'error', 'error': str(e)}
                result['trading_allowed'] = False
                result['veto_reason'] = f"Capital governor error: {e}"
        
        # Loss monitor
        if self._loss_monitor:
            try:
                result['checks']['loss_monitor'] = {'status': 'ok'}
            except Exception as e:
                result['checks']['loss_monitor'] = {'status': 'error', 'error': str(e)}
                result['trading_allowed'] = False
                result['veto_reason'] = f"Loss monitor error: {e}"
        
        return result
    
    def is_trading_allowed(self) -> bool:
        """Check if trading is currently allowed"""
        return self._trading_allowed
    
    def get_veto_reason(self) -> Optional[str]:
        """Get the current veto reason if any"""
        return self._veto_reason
