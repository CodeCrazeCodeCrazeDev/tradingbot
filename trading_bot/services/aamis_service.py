"""
AAMIS V3 Service - Autonomous AI Market Intelligence System
============================================================

Wraps AAMIS V3 capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.event_bus import Event, EventPriority, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AAMISService(BaseService):
    """
    AAMIS V3 Service
    
    Provides autonomous AI market intelligence capabilities:
    - Market awareness and perception
    - Intelligence layer processing
    - Superintelligence features
    - Evolution and adaptation
    """
    
    SERVICE_NAME = "aamis_v3"
    SERVICE_TYPE = "ai"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = ["market_data"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._analysis_interval: float = config.get('interval', 30.0) if config else 30.0
        self._task: Optional[asyncio.Task] = None
        
        # AAMIS components
        self._orchestrator = None
        self._complete_system = None
        self._last_analysis: Optional[Dict] = None
        
    async def start(self) -> None:
        """Start AAMIS service"""
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._analysis_loop())
        
        # Subscribe to market events
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [EventTypes.MARKET_DATA_UPDATE, EventTypes.MARKET_TICK],
                self._on_market_data
            )
        
        logger.info("AAMISService started")
    
    async def stop(self) -> None:
        """Stop AAMIS service"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._event_bus:
            self._event_bus.unsubscribe(self.SERVICE_NAME)
        
        logger.info("AAMISService stopped")
    
    async def health_check(self) -> ServiceHealth:
        """Check service health"""
        components_loaded = sum([
            self._orchestrator is not None,
            self._complete_system is not None,
        ])
        return ServiceHealth(
            healthy=self._running and components_loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{components_loaded}/2 AAMIS components loaded",
            metrics={
                'components_loaded': components_loaded,
                'last_analysis': self._last_analysis.get('timestamp') if self._last_analysis else None
            }
        )
    
    async def _load_components(self) -> None:
        """Load AAMIS V3 components"""
        try:
            from trading_bot.aamis_v3 import AAMISMasterOrchestrator
            self._orchestrator = AAMISMasterOrchestrator()
            logger.info("AAMIS Master Orchestrator loaded")
        except ImportError as e:
            logger.warning(f"AAMIS Master Orchestrator not available: {e}")
        
        try:
            from trading_bot.aamis_v3 import CompleteAAMISSystem
            self._complete_system = CompleteAAMISSystem()
            logger.info("Complete AAMIS System loaded")
        except ImportError as e:
            logger.warning(f"Complete AAMIS System not available: {e}")
    
    async def _on_market_data(self, event: Event) -> None:
        """Handle market data events"""
        # Buffer data for batch analysis
        pass
    
    async def _analysis_loop(self) -> None:
        """Run periodic AAMIS analysis"""
        while self._running:
            try:
                analysis = await self._run_analysis()
                self._last_analysis = analysis
                
                if analysis and self._event_bus:
                    await self._event_bus.publish(Event(
                        event_type=EventTypes.AI_ANALYSIS_COMPLETE,
                        payload={
                            'source': 'aamis_v3',
                            'analysis': analysis
                        },
                        source=self.SERVICE_NAME
                    ))
                
                await asyncio.sleep(self._analysis_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"AAMIS analysis error: {e}")
                await asyncio.sleep(30)
    
    async def _run_analysis(self) -> Dict[str, Any]:
        """Run AAMIS analysis"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'aamis_v3',
            'components': {}
        }
        
        if self._orchestrator:
            try:
                # Run orchestrator analysis if available
                results['components']['orchestrator'] = {'status': 'ready'}
            except Exception as e:
                results['components']['orchestrator'] = {'error': str(e)}
        
        if self._complete_system:
            try:
                results['components']['complete_system'] = {'status': 'ready'}
            except Exception as e:
                results['components']['complete_system'] = {'error': str(e)}
        
        return results
    
    async def analyze_symbol(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a specific symbol"""
        if not self._orchestrator:
            return {'error': 'AAMIS orchestrator not loaded'}
        
        try:
            # Placeholder for actual analysis
            return {
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat(),
                'analysis': 'ready',
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_last_analysis(self) -> Optional[Dict]:
        """Get last analysis result"""
        return self._last_analysis
