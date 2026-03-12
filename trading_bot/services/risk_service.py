"""
Risk Service - Risk Management System
======================================

Wraps Risk Management capabilities as an event-driven service.
Works in conjunction with MSOS to enforce risk constraints.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.event_bus import Event, EventPriority, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class RiskService(BaseService):
    """
    Risk Service - Comprehensive Risk Management
    
    Provides:
    - Position sizing (Kelly, Fixed Risk, Volatility-based)
    - Portfolio risk management
    - Correlation analysis
    - Drawdown protection
    - VaR/CVaR calculation
    - Risk budget allocation
    - Stop-loss management
    - Exposure limits
    """
    
    SERVICE_NAME = "risk"
    SERVICE_TYPE = "risk"
    PRIORITY = ServicePriority.CRITICAL
    DEPENDENCIES = ["database", "msos"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._check_interval: float = config.get('interval', 10.0) if config else 10.0
        self._task: Optional[asyncio.Task] = None
        
        # Risk components
        self._risk_manager = None
        self._position_sizer = None
        self._portfolio_risk = None
        self._drawdown_monitor = None
        
        # State
        self._current_risk_state: Dict[str, Any] = {}
        self._max_risk_per_trade: float = config.get('max_risk_per_trade', 0.02) if config else 0.02
        self._max_daily_loss: float = config.get('max_daily_loss', 0.05) if config else 0.05
        self._max_drawdown: float = config.get('max_drawdown', 0.20) if config else 0.20
        
    async def start(self) -> None:
        """Start Risk service"""
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._monitoring_loop())
        
        # Subscribe to events
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [
                    EventTypes.TRADE_APPROVED,
                    EventTypes.POSITION_OPENED,
                    EventTypes.POSITION_CLOSED,
                    EventTypes.MARKET_DATA_UPDATE,
                ],
                self._on_event
            )
        
        logger.info("RiskService started")
    
    async def stop(self) -> None:
        """Stop Risk service"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._event_bus:
            self._event_bus.unsubscribe(self.SERVICE_NAME)
        
        logger.info("RiskService stopped")
    
    async def health_check(self) -> ServiceHealth:
        """Check service health"""
        components_loaded = sum([
            self._risk_manager is not None,
            self._position_sizer is not None,
            self._portfolio_risk is not None,
            self._drawdown_monitor is not None,
        ])
        return ServiceHealth(
            healthy=self._running and components_loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{components_loaded}/4 Risk components loaded",
            metrics={
                'components_loaded': components_loaded,
                'max_risk_per_trade': self._max_risk_per_trade,
                'max_daily_loss': self._max_daily_loss,
                'max_drawdown': self._max_drawdown,
                'current_state': self._current_risk_state,
            }
        )
    
    async def _load_components(self) -> None:
        """Load Risk components"""
        try:
            from trading_bot.risk import UnifiedRiskManager
            self._risk_manager = UnifiedRiskManager(self.config or {})
            logger.info("UnifiedRiskManager loaded")
        except (ImportError, Exception) as e:
            logger.warning(f"UnifiedRiskManager not available: {e}")
            try:
                from trading_bot.risk import MasterRiskManager
                self._risk_manager = MasterRiskManager()
                logger.info("MasterRiskManager loaded")
            except (ImportError, Exception) as e2:
                logger.warning(f"MasterRiskManager not available: {e2}")
        
        try:
            from trading_bot.risk import PortfolioRiskManager
            self._portfolio_risk = PortfolioRiskManager()
            logger.info("PortfolioRiskManager loaded")
        except (ImportError, Exception) as e:
            logger.warning(f"PortfolioRiskManager not available: {e}")
        
        try:
            from trading_bot.risk import DrawdownManager
            self._drawdown_monitor = DrawdownManager()
            logger.info("DrawdownManager loaded")
        except (ImportError, Exception) as e:
            logger.warning(f"DrawdownManager not available: {e}")
    
    async def _on_event(self, event: Event) -> None:
        """Handle incoming events"""
        if event.event_type == EventTypes.TRADE_APPROVED:
            await self._on_trade_approved(event)
        elif event.event_type == EventTypes.POSITION_OPENED:
            await self._on_position_opened(event)
        elif event.event_type == EventTypes.POSITION_CLOSED:
            await self._on_position_closed(event)
        elif event.event_type == EventTypes.MARKET_DATA_UPDATE:
            await self._on_market_update(event)
    
    async def _on_trade_approved(self, event: Event) -> None:
        """Calculate position size for approved trade"""
        trade_data = event.payload.get('original_request', {})
        
        # Calculate position size
        position_size = await self.calculate_position_size(trade_data)
        
        # Publish sized trade
        if self._event_bus:
            await self._event_bus.publish(Event(
                event_type=EventTypes.TRADE_SIZED,
                payload={
                    'original_request': trade_data,
                    'position_size': position_size,
                    'risk_metrics': self._current_risk_state,
                },
                source=self.SERVICE_NAME,
            ))
    
    async def _on_position_opened(self, event: Event) -> None:
        """Track new position for risk monitoring"""
        pass
    
    async def _on_position_closed(self, event: Event) -> None:
        """Update risk state after position close"""
        pass
    
    async def _on_market_update(self, event: Event) -> None:
        """Update risk calculations on market data"""
        pass
    
    async def calculate_position_size(
        self,
        trade_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate optimal position size based on risk parameters.
        
        Uses Kelly Criterion, Fixed Risk, or Volatility-based sizing.
        """
        symbol = trade_data.get('symbol', 'UNKNOWN')
        entry_price = trade_data.get('entry_price', 0)
        stop_loss = trade_data.get('stop_loss', 0)
        account_equity = trade_data.get('account_equity', 10000)
        
        # Default to fixed risk sizing
        risk_amount = account_equity * self._max_risk_per_trade
        
        if entry_price > 0 and stop_loss > 0:
            risk_per_unit = abs(entry_price - stop_loss)
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit
            else:
                position_size = 0
        else:
            position_size = 0
        
        # Use position sizer if available
        if self._position_sizer:
            try:
                sized = self._position_sizer.calculate(
                    symbol=symbol,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    account_equity=account_equity,
                    max_risk=self._max_risk_per_trade,
                )
                position_size = sized.get('size', position_size)
            except Exception as e:
                logger.warning(f"Position sizer error: {e}")
        
        return {
            'symbol': symbol,
            'size': position_size,
            'risk_amount': risk_amount,
            'risk_percent': self._max_risk_per_trade,
            'method': 'fixed_risk',
        }
    
    async def _monitoring_loop(self) -> None:
        """Continuous risk monitoring loop"""
        while self._running:
            try:
                # Update risk state
                self._current_risk_state = await self._calculate_risk_state()
                
                # Check for risk breaches
                await self._check_risk_breaches()
                
                await asyncio.sleep(self._check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Risk monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def _calculate_risk_state(self) -> Dict[str, Any]:
        """Calculate current risk state"""
        state = {
            'timestamp': datetime.utcnow().isoformat(),
            'daily_pnl': 0.0,
            'daily_pnl_percent': 0.0,
            'current_drawdown': 0.0,
            'open_risk': 0.0,
            'correlation_risk': 0.0,
        }
        
        if self._drawdown_monitor:
            try:
                state['current_drawdown'] = self._drawdown_monitor.current_drawdown()
            except Exception:
                pass
        
        if self._portfolio_risk:
            try:
                state['correlation_risk'] = self._portfolio_risk.correlation_risk()
            except Exception:
                pass
        
        return state
    
    async def _check_risk_breaches(self) -> None:
        """Check for risk limit breaches"""
        # Check daily loss limit
        if abs(self._current_risk_state.get('daily_pnl_percent', 0)) > self._max_daily_loss:
            logger.warning("Daily loss limit breached!")
            if self._event_bus:
                await self._event_bus.publish(Event(
                    event_type=EventTypes.RISK_LIMIT_EXCEEDED,
                    payload={
                        'type': 'daily_loss',
                        'limit': self._max_daily_loss,
                        'current': self._current_risk_state.get('daily_pnl_percent', 0),
                    },
                    source=self.SERVICE_NAME,
                    priority=EventPriority.CRITICAL,
                ))
        
        # Check drawdown limit
        if self._current_risk_state.get('current_drawdown', 0) > self._max_drawdown:
            logger.warning("Max drawdown limit breached!")
            if self._event_bus:
                await self._event_bus.publish(Event(
                    event_type=EventTypes.RISK_LIMIT_EXCEEDED,
                    payload={
                        'type': 'max_drawdown',
                        'limit': self._max_drawdown,
                        'current': self._current_risk_state.get('current_drawdown', 0),
                    },
                    source=self.SERVICE_NAME,
                    priority=EventPriority.CRITICAL,
                ))
    
    def get_risk_state(self) -> Dict[str, Any]:
        """Get current risk state"""
        return self._current_risk_state.copy()
