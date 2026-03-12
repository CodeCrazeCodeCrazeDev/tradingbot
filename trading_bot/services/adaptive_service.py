"""
Adaptive Systems Service
========================

Wraps Adaptive Systems capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.event_bus import Event, EventPriority, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AdaptiveSystemsService(BaseService):
    """
    Adaptive Systems Service
    
    Provides adaptive learning and market analysis:
    - Adaptive learning engine
    - Adaptive risk management
    - Ensemble learning
    - Meta-learning
    - Sentiment analysis
    - Regime detection
    """
    
    SERVICE_NAME = "adaptive_systems"
    SERVICE_TYPE = "ai"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = ["market_data"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._analysis_interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        
        # Adaptive components
        self._learning_engine = None
        self._risk_manager = None
        self._ensemble = None
        self._meta_learning = None
        self._sentiment = None
        self._health_monitor = None
        self._last_analysis: Optional[Dict] = None
        
    async def start(self) -> None:
        """Start Adaptive Systems service"""
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._analysis_loop())
        
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [EventTypes.MARKET_DATA_UPDATE, EventTypes.AI_ANALYSIS_COMPLETE],
                self._on_event
            )
        
        logger.info("AdaptiveSystemsService started")
    
    async def stop(self) -> None:
        """Stop Adaptive Systems service"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._event_bus:
            self._event_bus.unsubscribe(self.SERVICE_NAME)
        
        logger.info("AdaptiveSystemsService stopped")
    
    async def health_check(self) -> ServiceHealth:
        """Check service health"""
        components = [
            self._learning_engine,
            self._risk_manager,
            self._ensemble,
            self._meta_learning,
            self._sentiment,
            self._health_monitor,
        ]
        loaded = sum(1 for c in components if c is not None)
        
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/6 Adaptive components loaded",
            metrics={'components_loaded': loaded}
        )
    
    async def _load_components(self) -> None:
        """Load Adaptive Systems components"""
        try:
            from trading_bot.adaptive_systems import AdaptiveLearningEngine
            self._learning_engine = AdaptiveLearningEngine()
            logger.info("AdaptiveLearningEngine loaded")
        except ImportError as e:
            logger.warning(f"AdaptiveLearningEngine not available: {e}")
        
        try:
            from trading_bot.adaptive_systems import AdaptiveRiskManager
            self._risk_manager = AdaptiveRiskManager()
            logger.info("AdaptiveRiskManager loaded")
        except ImportError as e:
            logger.warning(f"AdaptiveRiskManager not available: {e}")
        
        try:
            from trading_bot.adaptive_systems import EnsembleLearningSystem
            self._ensemble = EnsembleLearningSystem()
            logger.info("EnsembleLearningSystem loaded")
        except ImportError as e:
            logger.warning(f"EnsembleLearningSystem not available: {e}")
        
        try:
            from trading_bot.adaptive_systems import MetaLearningEngine
            self._meta_learning = MetaLearningEngine()
            logger.info("MetaLearningEngine loaded")
        except ImportError as e:
            logger.warning(f"MetaLearningEngine not available: {e}")
        
        try:
            from trading_bot.adaptive_systems import RealTimeSentimentEngine
            self._sentiment = RealTimeSentimentEngine()
            logger.info("RealTimeSentimentEngine loaded")
        except ImportError as e:
            logger.warning(f"RealTimeSentimentEngine not available: {e}")
        
        try:
            from trading_bot.adaptive_systems import SystemHealthMonitor
            self._health_monitor = SystemHealthMonitor()
            logger.info("SystemHealthMonitor loaded")
        except ImportError as e:
            logger.warning(f"SystemHealthMonitor not available: {e}")
    
    async def _on_event(self, event: Event) -> None:
        """Handle incoming events"""
        pass
    
    async def _analysis_loop(self) -> None:
        """Run periodic adaptive analysis"""
        while self._running:
            try:
                analysis = await self._run_analysis()
                self._last_analysis = analysis
                
                if analysis and self._event_bus:
                    await self._event_bus.publish(Event(
                        event_type=EventTypes.AI_ANALYSIS_COMPLETE,
                        payload={
                            'source': 'adaptive_systems',
                            'analysis': analysis
                        },
                        source=self.SERVICE_NAME
                    ))
                
                await asyncio.sleep(self._analysis_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Adaptive analysis error: {e}")
                await asyncio.sleep(30)
    
    async def _run_analysis(self) -> Dict[str, Any]:
        """Run adaptive systems analysis"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'adaptive_systems',
            'components': {}
        }
        
        if self._learning_engine:
            results['components']['learning'] = {'status': 'ready'}
        if self._risk_manager:
            results['components']['risk'] = {'status': 'ready'}
        if self._ensemble:
            results['components']['ensemble'] = {'status': 'ready'}
        if self._meta_learning:
            results['components']['meta_learning'] = {'status': 'ready'}
        if self._sentiment:
            results['components']['sentiment'] = {'status': 'ready'}
        
        return results
    
    def get_last_analysis(self) -> Optional[Dict]:
        """Get last analysis result"""
        return self._last_analysis
