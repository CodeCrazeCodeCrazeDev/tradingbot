"""
Alpha Engine Service
====================

Wraps Alpha Engine module capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

from trading_bot.core.event_bus import Event, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AlphaEngineService(BaseService):
    """
    Alpha Engine Service - Core Alpha Generation
    
    Provides:
    - Alpha engine orchestrator
    - Multi-brain architecture
    - Deep learning engine
    - Risk management
    - Behavioral finance
    - Cross-asset arbitrage
    """
    
    SERVICE_NAME = "alpha_engine"
    SERVICE_TYPE = "alpha"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = ["analysis"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.config = config or {}
        self._interval: float = self.config.get('interval', 30.0)
        self._task: Optional[asyncio.Task] = None
        self._orchestrator = None
        self._multi_brain = None
        self._deep_learning = None
        
    async def start(self) -> None:
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._run_loop())
        
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [EventTypes.MARKET_DATA_UPDATE, EventTypes.AI_ANALYSIS_COMPLETE],
                self._on_event
            )
        logger.info("AlphaEngineService started")
    
    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._event_bus:
            self._event_bus.unsubscribe(self.SERVICE_NAME)
        logger.info("AlphaEngineService stopped")
    
    async def health_check(self) -> ServiceHealth:
        loaded = sum([
            self._orchestrator is not None,
            self._multi_brain is not None,
            self._deep_learning is not None
        ])
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/3 Alpha Engine components loaded"
        )
    
    async def _load_components(self) -> None:
        try:
            from trading_bot.alpha_engine import AlphaEngineOrchestrator
            self._orchestrator = AlphaEngineOrchestrator()
            logger.info("AlphaEngineOrchestrator loaded")
        except ImportError as e:
            logger.warning("AlphaEngineOrchestrator not available: %s", e)
        except Exception as e:
            logger.warning("AlphaEngineOrchestrator initialization failed: %s", e)
        
        try:
            from trading_bot.alpha_engine import MultiBrainArchitecture
            self._multi_brain = MultiBrainArchitecture(config=self.config)
            logger.info("MultiBrainArchitecture loaded")
        except ImportError as e:
            logger.warning("MultiBrainArchitecture not available: %s", e)
        except Exception as e:
            logger.warning("MultiBrainArchitecture initialization failed: %s", e)
        
        try:
            from trading_bot.alpha_engine import IntegratedDeepLearningEngine
            self._deep_learning = IntegratedDeepLearningEngine(config=self.config)
            logger.info("IntegratedDeepLearningEngine loaded")
        except ImportError as e:
            logger.warning("IntegratedDeepLearningEngine not available: %s", e)
        except Exception as e:
            logger.warning("IntegratedDeepLearningEngine initialization failed: %s", e)
    
    async def _on_event(self, event: Event) -> None:
        pass
    
    async def _run_loop(self) -> None:
        while self._running:
            try:
                if self._event_bus:
                    await self._event_bus.publish(Event(
                        event_type=EventTypes.SIGNAL_GENERATED,
                        payload={'source': 'alpha_engine', 'timestamp': datetime.utcnow().isoformat()},
                        source=self.SERVICE_NAME
                    ))
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Alpha engine loop error: %s", e)
                await asyncio.sleep(30)
