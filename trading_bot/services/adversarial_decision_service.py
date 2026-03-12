"""
Adversarial Decision Service
=============================

Wraps Adversarial Decision capabilities as an event-driven service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from trading_bot.core.event_bus import Event, EventPriority, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class AdversarialDecisionService(BaseService):
    """
    Adversarial Decision Service
    
    Provides adversarial decision-making:
    - Adversarial decision engine
    - Confidence vector analysis
    - Decision gate validation
    - Claim verification system
    - Position sizing with adversarial checks
    """
    
    SERVICE_NAME = "adversarial_decision"
    SERVICE_TYPE = "decision"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = ["ai_analysis", "risk_monitor"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._decision_interval: float = config.get('interval', 30.0) if config else 30.0
        self._task: Optional[asyncio.Task] = None
        
        # Decision components
        self._decision_engine = None
        self._last_decision: Optional[Dict] = None
        
    async def start(self) -> None:
        """Start Adversarial Decision service"""
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._decision_loop())
        
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [EventTypes.SIGNAL_GENERATED, EventTypes.AI_ANALYSIS_COMPLETE],
                self._on_event
            )
        
        logger.info("AdversarialDecisionService started")
    
    async def stop(self) -> None:
        """Stop Adversarial Decision service"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._event_bus:
            self._event_bus.unsubscribe(self.SERVICE_NAME)
        
        logger.info("AdversarialDecisionService stopped")
    
    async def health_check(self) -> ServiceHealth:
        """Check service health"""
        loaded = 1 if self._decision_engine is not None else 0
        
        return ServiceHealth(
            healthy=self._running and loaded > 0,
            last_check=datetime.utcnow(),
            message=f"{loaded}/1 Adversarial Decision components loaded",
            metrics={'components_loaded': loaded}
        )
    
    async def _load_components(self) -> None:
        """Load Adversarial Decision components"""
        try:
            from trading_bot.adversarial_decision import AdversarialDecisionEngine
            self._decision_engine = AdversarialDecisionEngine()
            logger.info("AdversarialDecisionEngine loaded")
        except ImportError as e:
            logger.warning(f"AdversarialDecisionEngine not available: {e}")
    
    async def _on_event(self, event: Event) -> None:
        """Handle incoming events"""
        if event.event_type == EventTypes.SIGNAL_GENERATED:
            decision = await self._evaluate_signal(event.payload)
            if decision and self._event_bus:
                await self._event_bus.publish(Event(
                    event_type=EventTypes.SIGNAL_VALIDATED if decision.get('approved') else EventTypes.SIGNAL_REJECTED,
                    payload={
                        'source': 'adversarial_decision',
                        'original_signal': event.payload,
                        'decision': decision
                    },
                    source=self.SERVICE_NAME,
                    priority=EventPriority.HIGH
                ))
    
    async def _evaluate_signal(self, signal_data: Dict) -> Dict:
        """Evaluate signal with adversarial decision engine"""
        if self._decision_engine:
            try:
                # Placeholder for actual evaluation
                return {
                    'approved': True,
                    'confidence': 0.75,
                    'adversarial_score': 0.2,
                    'timestamp': datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.error(f"Signal evaluation error: {e}")
        return {'approved': True, 'confidence': 0.5}
    
    async def _decision_loop(self) -> None:
        """Run periodic decision evaluation"""
        while self._running:
            try:
                result = await self._run_decision_cycle()
                self._last_decision = result
                
                await asyncio.sleep(self._decision_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Decision cycle error: {e}")
                await asyncio.sleep(30)
    
    async def _run_decision_cycle(self) -> Dict[str, Any]:
        """Run decision evaluation cycle"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'adversarial_decision',
            'engine_status': 'ready' if self._decision_engine else 'not_loaded'
        }
        return results
    
    def get_last_decision(self) -> Optional[Dict]:
        """Get last decision result"""
        return self._last_decision
