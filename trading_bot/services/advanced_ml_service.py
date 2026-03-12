"""
Advanced ML Service
===================

Wraps Advanced ML capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.event_bus import Event, EventPriority, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AdvancedMLService(BaseService):
    """
    Advanced ML Service
    
    Provides advanced machine learning capabilities:
    - MAML (Model-Agnostic Meta-Learning)
    - Few-Shot Learning
    - Transfer Learning
    - Continual Learning
    - Neural Architecture Search
    """
    
    SERVICE_NAME = "advanced_ml"
    SERVICE_TYPE = "ml"
    PRIORITY = ServicePriority.NORMAL
    DEPENDENCIES = ["data"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._learning_interval: float = config.get('interval', 300.0) if config else 300.0
        self._task: Optional[asyncio.Task] = None
        
        # Advanced ML components
        self._maml = None
        self._few_shot = None
        self._transfer = None
        self._continual = None
        self._nas = None
        self._last_result: Optional[Dict] = None
        
    async def start(self) -> None:
        """Start Advanced ML service"""
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._learning_loop())
        
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [EventTypes.AI_ANALYSIS_COMPLETE, EventTypes.AI_LEARNING_CYCLE],
                self._on_event
            )
        
        logger.info("AdvancedMLService started")
    
    async def stop(self) -> None:
        """Stop Advanced ML service"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._event_bus:
            self._event_bus.unsubscribe(self.SERVICE_NAME)
        
        logger.info("AdvancedMLService stopped")
    
    async def health_check(self) -> ServiceHealth:
        """Check service health"""
        components = [
            self._maml,
            self._few_shot,
            self._transfer,
            self._continual,
            self._nas,
        ]
        loaded = sum(1 for c in components if c is not None)
        
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/5 Advanced ML components loaded",
            metrics={'components_loaded': loaded}
        )
    
    async def _load_components(self) -> None:
        """Load Advanced ML components"""
        try:
            from trading_bot.advanced_ml import MAML
            self._maml = MAML()
            logger.info("MAML loaded")
        except ImportError as e:
            logger.warning(f"MAML not available: {e}")
        
        try:
            from trading_bot.advanced_ml import FewShotLearning
            self._few_shot = FewShotLearning()
            logger.info("FewShotLearning loaded")
        except ImportError as e:
            logger.warning(f"FewShotLearning not available: {e}")
        
        try:
            from trading_bot.advanced_ml import TransferLearning
            self._transfer = TransferLearning()
            logger.info("TransferLearning loaded")
        except ImportError as e:
            logger.warning(f"TransferLearning not available: {e}")
        
        try:
            from trading_bot.advanced_ml import ContinualLearning
            self._continual = ContinualLearning()
            logger.info("ContinualLearning loaded")
        except ImportError as e:
            logger.warning(f"ContinualLearning not available: {e}")
        
        try:
            from trading_bot.advanced_ml import NeuralArchitectureSearch
            self._nas = NeuralArchitectureSearch()
            logger.info("NeuralArchitectureSearch loaded")
        except ImportError as e:
            logger.warning(f"NeuralArchitectureSearch not available: {e}")
    
    async def _on_event(self, event: Event) -> None:
        """Handle incoming events"""
        pass
    
    async def _learning_loop(self) -> None:
        """Run periodic ML learning cycles"""
        while self._running:
            try:
                result = await self._run_learning_cycle()
                self._last_result = result
                
                if result and self._event_bus:
                    await self._event_bus.publish(Event(
                        event_type=EventTypes.AI_MODEL_UPDATED,
                        payload={
                            'source': 'advanced_ml',
                            'result': result
                        },
                        source=self.SERVICE_NAME
                    ))
                
                await asyncio.sleep(self._learning_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Advanced ML error: {e}")
                await asyncio.sleep(60)
    
    async def _run_learning_cycle(self) -> Dict[str, Any]:
        """Run ML learning cycle"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'advanced_ml',
            'components': {}
        }
        
        if self._maml:
            results['components']['maml'] = {'status': 'ready'}
        if self._few_shot:
            results['components']['few_shot'] = {'status': 'ready'}
        if self._transfer:
            results['components']['transfer'] = {'status': 'ready'}
        if self._continual:
            results['components']['continual'] = {'status': 'ready'}
        if self._nas:
            results['components']['nas'] = {'status': 'ready'}
        
        return results
    
    def get_last_result(self) -> Optional[Dict]:
        """Get last learning result"""
        return self._last_result
