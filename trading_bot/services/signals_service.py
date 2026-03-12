"""
Signals Service - Trading Signal Generation
============================================

Wraps Signal generation capabilities as an event-driven service.
Coordinates signal generation from multiple sources.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from trading_bot.core.event_bus import Event, EventPriority, EventTypes
from trading_bot.core.service_registry import BaseService, ServiceHealth, ServicePriority

logger = logging.getLogger(__name__)


class SignalsService(BaseService):
    """
    Signals Service - Trading Signal Management
    
    Provides:
    - Signal lifecycle management
    - Signal provenance tracking
    - Signal validation
    - Multi-source signal aggregation
    - Signal TTL and decay
    - News gating
    - Confidence calibration
    """
    
    SERVICE_NAME = "signals"
    SERVICE_TYPE = "signals"
    PRIORITY = ServicePriority.HIGH
    DEPENDENCIES = ["analysis"]
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._signal_interval: float = config.get('interval', 60.0) if config else 60.0
        self._task: Optional[asyncio.Task] = None
        
        # Signal components
        self._signal_lifecycle = None
        self._signal_provenance = None
        self._confidence_calibrator = None
        self._news_gating = None
        
        # State
        self._active_signals: Dict[str, Dict] = {}
        self._signal_history: List[Dict] = []
        self._signal_stats: Dict[str, Any] = {
            'total_generated': 0,
            'total_validated': 0,
            'total_rejected': 0,
            'avg_confidence': 0.0,
        }
        
    async def start(self) -> None:
        """Start Signals service"""
        self._running = True
        await self._load_components()
        self._task = asyncio.create_task(self._signal_loop())
        
        # Subscribe to events
        if self._event_bus:
            self._event_bus.subscribe(
                self.SERVICE_NAME,
                [
                    EventTypes.AI_ANALYSIS_COMPLETE,
                    EventTypes.ALPHA_SIGNAL,
                    EventTypes.MARKET_DATA_UPDATE,
                ],
                self._on_event
            )
        
        logger.info("SignalsService started")
    
    async def stop(self) -> None:
        """Stop Signals service"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._event_bus:
            self._event_bus.unsubscribe(self.SERVICE_NAME)
        
        logger.info("SignalsService stopped")
    
    async def health_check(self) -> ServiceHealth:
        """Check service health"""
        components_loaded = sum([
            self._signal_lifecycle is not None,
            self._signal_provenance is not None,
            self._confidence_calibrator is not None,
            self._news_gating is not None,
        ])
        return ServiceHealth(
            healthy=self._running,
            last_check=datetime.utcnow(),
            message=f"{components_loaded}/4 Signal components loaded",
            metrics={
                'components_loaded': components_loaded,
                'active_signals': len(self._active_signals),
                'signal_stats': self._signal_stats,
            }
        )
    
    async def _load_components(self) -> None:
        """Load Signal components"""
        try:
            from trading_bot.signals import SignalLifecycle
            self._signal_lifecycle = SignalLifecycle()
            logger.info("SignalLifecycle loaded")
        except ImportError as e:
            logger.warning(f"SignalLifecycle not available: {e}")
        
        try:
            from trading_bot.signals import SignalProvenance
            self._signal_provenance = SignalProvenance()
            logger.info("SignalProvenance loaded")
        except ImportError as e:
            logger.warning(f"SignalProvenance not available: {e}")
        
        try:
            from trading_bot.ml import ConfidenceCalibrator
            self._confidence_calibrator = ConfidenceCalibrator()
            logger.info("ConfidenceCalibrator loaded")
        except ImportError as e:
            logger.warning(f"ConfidenceCalibrator not available: {e}")
        
        try:
            from trading_bot.signals import NewsGating
            self._news_gating = NewsGating()
            logger.info("NewsGating loaded")
        except ImportError as e:
            logger.warning(f"NewsGating not available: {e}")
    
    async def _on_event(self, event: Event) -> None:
        """Handle incoming events"""
        if event.event_type == EventTypes.AI_ANALYSIS_COMPLETE:
            await self._on_analysis_complete(event)
        elif event.event_type == EventTypes.ALPHA_SIGNAL:
            await self._on_alpha_signal(event)
        elif event.event_type == EventTypes.MARKET_DATA_UPDATE:
            await self._on_market_update(event)
    
    async def _on_analysis_complete(self, event: Event) -> None:
        """Process completed AI analysis into signals"""
        analysis = event.payload.get('analysis', {})
        source = event.payload.get('source', 'unknown')
        
        # Extract signals from analysis
        signals = await self._extract_signals(analysis, source)
        
        for signal in signals:
            await self._process_signal(signal)
    
    async def _on_alpha_signal(self, event: Event) -> None:
        """Process alpha signal from alpha engine"""
        signal = event.payload
        await self._process_signal(signal)
    
    async def _on_market_update(self, event: Event) -> None:
        """Update signal validity on market data"""
        # Decay old signals
        await self._decay_signals()
    
    async def _extract_signals(
        self,
        analysis: Dict[str, Any],
        source: str
    ) -> List[Dict[str, Any]]:
        """Extract trading signals from analysis results"""
        signals = []
        
        # Check for explicit signals in analysis
        if 'signals' in analysis:
            for sig in analysis['signals']:
                sig['source'] = source
                signals.append(sig)
        
        # Check for recommendations
        if 'recommendation' in analysis:
            rec = analysis['recommendation']
            if rec.get('action') in ['buy', 'sell']:
                signals.append({
                    'symbol': rec.get('symbol'),
                    'direction': rec.get('action'),
                    'confidence': rec.get('confidence', 0.5),
                    'source': source,
                    'timestamp': datetime.utcnow().isoformat(),
                })
        
        return signals
    
    async def _process_signal(self, signal: Dict[str, Any]) -> None:
        """Process and validate a trading signal"""
        signal_id = f"SIG_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        signal['signal_id'] = signal_id
        signal['created_at'] = datetime.utcnow().isoformat()
        signal['status'] = 'pending'
        
        self._signal_stats['total_generated'] += 1
        
        # Validate signal
        is_valid, reason = await self._validate_signal(signal)
        
        if not is_valid:
            signal['status'] = 'rejected'
            signal['reject_reason'] = reason
            self._signal_stats['total_rejected'] += 1
            logger.info(f"Signal {signal_id} rejected: {reason}")
            return
        
        # Calibrate confidence
        if self._confidence_calibrator:
            try:
                calibrated = self._confidence_calibrator.calibrate(
                    signal.get('confidence', 0.5)
                )
                signal['calibrated_confidence'] = calibrated
            except Exception:
                signal['calibrated_confidence'] = signal.get('confidence', 0.5)
        
        # Check news gating
        if self._news_gating:
            try:
                news_blocked = self._news_gating.is_blocked(signal.get('symbol'))
                if news_blocked:
                    signal['status'] = 'news_blocked'
                    logger.info(f"Signal {signal_id} blocked by news gating")
                    return
            except Exception:
                pass
        
        # Signal validated
        signal['status'] = 'validated'
        self._active_signals[signal_id] = signal
        self._signal_stats['total_validated'] += 1
        
        # Update average confidence
        confidences = [s.get('confidence', 0) for s in self._active_signals.values()]
        if confidences:
            self._signal_stats['avg_confidence'] = sum(confidences) / len(confidences)
        
        # Publish validated signal
        if self._event_bus:
            await self._event_bus.publish(Event(
                event_type=EventTypes.SIGNAL_GENERATED,
                payload=signal,
                source=self.SERVICE_NAME,
            ))
        
        logger.info(f"Signal {signal_id} validated: {signal.get('symbol')} {signal.get('direction')}")
    
    async def _validate_signal(self, signal: Dict[str, Any]) -> tuple[bool, str]:
        """Validate a trading signal"""
        # Check required fields
        if not signal.get('symbol'):
            return False, "Missing symbol"
        
        if not signal.get('direction') or signal['direction'] not in ['buy', 'sell', 'long', 'short']:
            return False, "Invalid direction"
        
        # Check confidence threshold
        confidence = signal.get('confidence', 0)
        min_confidence = self.config.get('min_confidence', 0.5)
        if confidence < min_confidence:
            return False, f"Confidence {confidence} below threshold {min_confidence}"
        
        # Use signal lifecycle if available
        if self._signal_lifecycle:
            try:
                valid = self._signal_lifecycle.validate(signal)
                if not valid:
                    return False, "Failed lifecycle validation"
            except Exception as e:
                logger.warning(f"Lifecycle validation error: {e}")
        
        return True, "Valid"
    
    async def _decay_signals(self) -> None:
        """Decay old signals based on TTL"""
        now = datetime.utcnow()
        ttl_seconds = self.config.get('signal_ttl_seconds', 300)  # 5 minutes default
        
        expired = []
        for signal_id, signal in self._active_signals.items():
            created_at = datetime.fromisoformat(signal['created_at'])
            age = (now - created_at).total_seconds()
            
            if age > ttl_seconds:
                expired.append(signal_id)
            else:
                # Apply decay to confidence
                decay_rate = self.config.get('decay_rate', 0.01)
                signal['decayed_confidence'] = signal.get('confidence', 0) * (1 - decay_rate * age / ttl_seconds)
        
        # Remove expired signals
        for signal_id in expired:
            signal = self._active_signals.pop(signal_id)
            signal['status'] = 'expired'
            self._signal_history.append(signal)
    
    async def _signal_loop(self) -> None:
        """Main signal processing loop"""
        while self._running:
            try:
                # Periodic signal decay
                await self._decay_signals()
                
                # Clean up old history
                max_history = self.config.get('max_history', 1000)
                if len(self._signal_history) > max_history:
                    self._signal_history = self._signal_history[-max_history:]
                
                await asyncio.sleep(self._signal_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Signal loop error: {e}")
                await asyncio.sleep(10)
    
    def get_active_signals(self) -> Dict[str, Dict]:
        """Get all active signals"""
        return self._active_signals.copy()
    
    def get_signal_stats(self) -> Dict[str, Any]:
        """Get signal statistics"""
        return self._signal_stats.copy()
