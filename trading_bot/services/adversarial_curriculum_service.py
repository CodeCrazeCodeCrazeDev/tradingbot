"""
Adversarial Curriculum Service
==============================

Wraps Adversarial Curriculum capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.event_bus import Event, EventPriority, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AdversarialCurriculumService(BaseService):
    """
    Adversarial Curriculum Service
    
    Provides curriculum-based adversarial training:
    - Anti-cheat detection
    - Curriculum orchestration
    - Failure handling and regression management
    - Progressive difficulty scaling
    """
    
    SERVICE_NAME = "adversarial_curriculum"
    SERVICE_TYPE = "training"
    PRIORITY = ServicePriority.LOW
    DEPENDENCIES = ["ai_analysis"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._training_interval: float = config.get('interval', 180.0) if config else 180.0
        self._task: Optional[asyncio.Task] = None
        
        # Curriculum components
        self._anti_cheat = None
        self._orchestrator = None
        self._regression_manager = None
        self._last_result: Optional[Dict] = None
        
    async def start(self) -> None:
        """Start Adversarial Curriculum service"""
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._training_loop())
        
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [EventTypes.AI_LEARNING_CYCLE, EventTypes.TRADE_FAILED],
                self._on_event
            )
        
        logger.info("AdversarialCurriculumService started")
    
    async def stop(self) -> None:
        """Stop Adversarial Curriculum service"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._event_bus:
            self._event_bus.unsubscribe(self.SERVICE_NAME)
        
        logger.info("AdversarialCurriculumService stopped")
    
    async def health_check(self) -> ServiceHealth:
        """Check service health"""
        components = [
            self._anti_cheat,
            self._orchestrator,
            self._regression_manager,
        ]
        loaded = sum(1 for c in components if c is not None)
        
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/3 Adversarial Curriculum components loaded",
            metrics={'components_loaded': loaded}
        )
    
    async def _load_components(self) -> None:
        """Load Adversarial Curriculum components"""
        try:
            from trading_bot.adversarial_curriculum import AntiCheatSystem
            self._anti_cheat = AntiCheatSystem()
            logger.info("AntiCheatSystem loaded")
        except ImportError as e:
            logger.warning(f"AntiCheatSystem not available: {e}")
        
        try:
            from trading_bot.adversarial_curriculum import CurriculumOrchestrator
            self._orchestrator = CurriculumOrchestrator()
            logger.info("CurriculumOrchestrator loaded")
        except ImportError as e:
            logger.warning(f"CurriculumOrchestrator not available: {e}")
        
        try:
            from trading_bot.adversarial_curriculum import RegressionManager
            self._regression_manager = RegressionManager()
            logger.info("RegressionManager loaded")
        except ImportError as e:
            logger.warning(f"RegressionManager not available: {e}")
    
    async def _on_event(self, event: Event) -> None:
        """Handle incoming events"""
        if event.event_type == EventTypes.TRADE_FAILED:
            await self._handle_failure(event.payload)
    
    async def _handle_failure(self, failure_data: Dict) -> None:
        """Handle trade failure for curriculum learning"""
        if self._regression_manager:
            try:
                # Record failure for curriculum adjustment
                pass
            except Exception as e:
                logger.error(f"Failure handling error: {e}")
    
    async def _training_loop(self) -> None:
        """Run periodic curriculum training"""
        while self._running:
            try:
                result = await self._run_training_cycle()
                self._last_result = result
                
                if result and self._event_bus:
                    await self._event_bus.publish(Event(
                        event_type=EventTypes.AI_LEARNING_CYCLE,
                        payload={
                            'source': 'adversarial_curriculum',
                            'result': result
                        },
                        source=self.SERVICE_NAME
                    ))
                
                await asyncio.sleep(self._training_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Curriculum training error: {e}")
                await asyncio.sleep(60)
    
    async def _run_training_cycle(self) -> Dict[str, Any]:
        """Run curriculum training cycle"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'adversarial_curriculum',
            'components': {}
        }
        
        if self._anti_cheat:
            results['components']['anti_cheat'] = {'status': 'ready'}
        if self._orchestrator:
            results['components']['orchestrator'] = {'status': 'ready'}
        if self._regression_manager:
            results['components']['regression_manager'] = {'status': 'ready'}
        
        return results
    
    def get_last_result(self) -> Optional[Dict]:
        """Get last training result"""
        return self._last_result
