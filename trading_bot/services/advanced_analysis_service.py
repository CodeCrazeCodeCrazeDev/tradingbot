"""
Advanced Analysis Service
=========================

Wraps Advanced Analysis capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.event_bus import Event, EventPriority, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AdvancedAnalysisService(BaseService):
    """
    Advanced Analysis Service
    
    Provides sophisticated market analysis:
    - Multi-Agent RL trading
    - Options hedging
    - Topological data analysis
    - Market microbiome analysis
    - Liquidity holography
    - Hawkes process modeling
    - Central bank tracking
    - Digital twin simulation
    """
    
    SERVICE_NAME = "advanced_analysis"
    SERVICE_TYPE = "analysis"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = ["market_data"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._analysis_interval: float = config.get('interval', 90.0) if config else 90.0
        self._task: Optional[asyncio.Task] = None
        
        # Advanced Analysis components
        self._orchestrator = None
        self._multi_agent = None
        self._options_hedging = None
        self._last_analysis: Optional[Dict] = None
        
    async def start(self) -> None:
        """Start Advanced Analysis service"""
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._analysis_loop())
        
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [EventTypes.MARKET_DATA_UPDATE, EventTypes.MARKET_CANDLE],
                self._on_market_data
            )
        
        logger.info("AdvancedAnalysisService started")
    
    async def stop(self) -> None:
        """Stop Advanced Analysis service"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._event_bus:
            self._event_bus.unsubscribe(self.SERVICE_NAME)
        
        logger.info("AdvancedAnalysisService stopped")
    
    async def health_check(self) -> ServiceHealth:
        """Check service health"""
        components = [
            self._orchestrator,
            self._multi_agent,
            self._options_hedging,
        ]
        loaded = sum(1 for c in components if c is not None)
        
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/3 Advanced Analysis components loaded",
            metrics={'components_loaded': loaded}
        )
    
    async def _load_components(self) -> None:
        """Load Advanced Analysis components"""
        try:
            from trading_bot.advanced_analysis import AdvancedAnalysisOrchestrator
            self._orchestrator = AdvancedAnalysisOrchestrator()
            logger.info("AdvancedAnalysisOrchestrator loaded")
        except ImportError as e:
            logger.warning(f"AdvancedAnalysisOrchestrator not available: {e}")
        
        try:
            from trading_bot.advanced_analysis import MultiAgentTradingSystem
            self._multi_agent = MultiAgentTradingSystem()
            logger.info("MultiAgentTradingSystem loaded")
        except ImportError as e:
            logger.warning(f"MultiAgentTradingSystem not available: {e}")
        
        try:
            from trading_bot.advanced_analysis import OptionsHedgingEngine
            self._options_hedging = OptionsHedgingEngine()
            logger.info("OptionsHedgingEngine loaded")
        except ImportError as e:
            logger.warning(f"OptionsHedgingEngine not available: {e}")
    
    async def _on_market_data(self, event: Event) -> None:
        """Handle market data events"""
        pass
    
    async def _analysis_loop(self) -> None:
        """Run periodic advanced analysis"""
        while self._running:
            try:
                analysis = await self._run_analysis()
                self._last_analysis = analysis
                
                if analysis and self._event_bus:
                    await self._event_bus.publish(Event(
                        event_type=EventTypes.AI_ANALYSIS_COMPLETE,
                        payload={
                            'source': 'advanced_analysis',
                            'analysis': analysis
                        },
                        source=self.SERVICE_NAME
                    ))
                
                await asyncio.sleep(self._analysis_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Advanced analysis error: {e}")
                await asyncio.sleep(60)
    
    async def _run_analysis(self) -> Dict[str, Any]:
        """Run advanced analysis"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'advanced_analysis',
            'components': {}
        }
        
        if self._orchestrator:
            results['components']['orchestrator'] = {'status': 'ready'}
        if self._multi_agent:
            results['components']['multi_agent'] = {'status': 'ready'}
        if self._options_hedging:
            results['components']['options_hedging'] = {'status': 'ready'}
        
        return results
    
    def get_last_analysis(self) -> Optional[Dict]:
        """Get last analysis result"""
        return self._last_analysis
