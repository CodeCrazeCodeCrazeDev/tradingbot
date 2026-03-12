"""
Advanced AI Service
===================

Wraps Advanced AI capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.event_bus import Event, EventPriority, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AdvancedAIService(BaseService):
    """
    Advanced AI Service
    
    Provides cutting-edge AI capabilities:
    - Neural Architecture Search
    - Multi-Armed Bandit strategy selection
    - Meta-Reinforcement Learning
    - Automated Feature Engineering
    - Code Synthesis
    - Cognitive Systems
    - Distributed Intelligence
    - Safety Verification
    """
    
    SERVICE_NAME = "advanced_ai"
    SERVICE_TYPE = "ai"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = ["market_data", "ai_analysis"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._analysis_interval: float = config.get('interval', 120.0) if config else 120.0
        self._task: Optional[asyncio.Task] = None
        
        # Advanced AI components
        self._nas = None
        self._bandit = None
        self._meta_rl = None
        self._feature_engine = None
        self._cognitive = None
        self._last_analysis: Optional[Dict] = None
        
    async def start(self) -> None:
        """Start Advanced AI service"""
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._analysis_loop())
        
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [EventTypes.AI_ANALYSIS_COMPLETE],
                self._on_analysis
            )
        
        logger.info("AdvancedAIService started")
    
    async def stop(self) -> None:
        """Stop Advanced AI service"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._event_bus:
            self._event_bus.unsubscribe(self.SERVICE_NAME)
        
        logger.info("AdvancedAIService stopped")
    
    async def health_check(self) -> ServiceHealth:
        """Check service health"""
        components = [
            self._nas,
            self._bandit,
            self._meta_rl,
            self._feature_engine,
            self._cognitive,
        ]
        loaded = sum(1 for c in components if c is not None)
        
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/5 Advanced AI components loaded",
            metrics={'components_loaded': loaded}
        )
    
    async def _load_components(self) -> None:
        """Load Advanced AI components"""
        try:
            from trading_bot.advanced_ai import create_nas_optimizer
            self._nas = create_nas_optimizer()
            logger.info("NAS Optimizer loaded")
        except ImportError as e:
            logger.warning(f"NAS Optimizer not available: {e}")
        
        try:
            from trading_bot.advanced_ai import create_strategy_bandit
            self._bandit = create_strategy_bandit()
            logger.info("Strategy Bandit loaded")
        except ImportError as e:
            logger.warning(f"Strategy Bandit not available: {e}")
        
        try:
            from trading_bot.advanced_ai import create_meta_learner
            self._meta_rl = create_meta_learner()
            logger.info("Meta Learner loaded")
        except ImportError as e:
            logger.warning(f"Meta Learner not available: {e}")
        
        try:
            from trading_bot.advanced_ai import create_feature_engine
            self._feature_engine = create_feature_engine()
            logger.info("Feature Engine loaded")
        except ImportError as e:
            logger.warning(f"Feature Engine not available: {e}")
        
        try:
            from trading_bot.advanced_ai import create_cognitive_system
            self._cognitive = create_cognitive_system()
            logger.info("Cognitive System loaded")
        except ImportError as e:
            logger.warning(f"Cognitive System not available: {e}")
    
    async def _on_analysis(self, event: Event) -> None:
        """Handle analysis events"""
        pass
    
    async def _analysis_loop(self) -> None:
        """Run periodic advanced AI analysis"""
        while self._running:
            try:
                analysis = await self._run_analysis()
                self._last_analysis = analysis
                
                if analysis and self._event_bus:
                    await self._event_bus.publish(Event(
                        event_type=EventTypes.AI_PREDICTION_READY,
                        payload={
                            'source': 'advanced_ai',
                            'analysis': analysis
                        },
                        source=self.SERVICE_NAME
                    ))
                
                await asyncio.sleep(self._analysis_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Advanced AI error: {e}")
                await asyncio.sleep(60)
    
    async def _run_analysis(self) -> Dict[str, Any]:
        """Run advanced AI analysis"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'advanced_ai',
            'components': {}
        }
        
        if self._nas:
            results['components']['nas'] = {'status': 'ready'}
        if self._bandit:
            results['components']['bandit'] = {'status': 'ready'}
        if self._meta_rl:
            results['components']['meta_rl'] = {'status': 'ready'}
        if self._feature_engine:
            results['components']['feature_engine'] = {'status': 'ready'}
        if self._cognitive:
            results['components']['cognitive'] = {'status': 'ready'}
        
        return results
    
    def get_last_analysis(self) -> Optional[Dict]:
        """Get last analysis result"""
        return self._last_analysis
