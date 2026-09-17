"""
Elite Trading Orchestrator - Master Coordinator for All Systems

Coordinates all elite trading system components:
- Slow Inference Engine
- Signal Validation System
- Market Psychology Engine
- Growth Optimization Framework
- Emergency Response System
- Elite Execution Engine
- Neural Evolution Framework
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from collections import deque

from .slow_inference_engine import SlowInferenceEngine, InferenceResult, AnalysisDepth
from .signal_validation_system import SignalValidationSystem, ValidationResult, ValidationStatus
from .market_psychology_engine import MarketPsychologyEngine, PsychologyState
from .growth_optimization_framework import GrowthOptimizationFramework, PositionScaling
from .emergency_response_system import EmergencyResponseSystem, EmergencyLevel
from .elite_execution_engine import EliteExecutionEngine, EntryOptimization, ExitOptimization
from .neural_evolution_framework import NeuralEvolutionFramework, EvolutionCycle

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class SystemStatus(Enum):
    INITIALIZING = "initializing"
    READY = "ready"
    ANALYZING = "analyzing"
    TRADING = "trading"
    EMERGENCY = "emergency"
    PAUSED = "paused"
    SHUTDOWN = "shutdown"


class TradingMode(Enum):
    PAPER = "paper"
    LIVE = "live"
    BACKTEST = "backtest"


@dataclass
class TradingDecision:
    """Complete trading decision from orchestrator"""
    decision_id: str
    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: List[float]
    position_size: float
    position_size_pct: float
    risk_reward_ratio: float
    expected_value: float
    
    # Analysis results
    inference_result: Optional[InferenceResult]
    validation_result: Optional[ValidationResult]
    psychology_state: Optional[PsychologyState]
    position_scaling: Optional[PositionScaling]
    entry_optimization: Optional[EntryOptimization]
    
    # Meta information
    reasoning_summary: str
    warnings: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'decision_id': self.decision_id,
            'symbol': self.symbol,
            'action': self.action,
            'confidence': self.confidence,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'position_size': self.position_size,
            'position_size_pct': self.position_size_pct,
            'risk_reward_ratio': self.risk_reward_ratio,
            'expected_value': self.expected_value,
            'reasoning_summary': self.reasoning_summary,
            'warnings': self.warnings,
            'timestamp': self.timestamp.isoformat()
        }


class EliteTradingOrchestrator:
    """
    Elite Trading Orchestrator
    
    Master coordinator that integrates all elite trading components:
    - Runs slow inference for deep analysis
    - Validates signals through multiple layers
    - Analyzes market psychology
    - Optimizes position sizing and growth
    - Handles emergencies
    - Optimizes execution
    - Evolves neural patterns
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Trading mode
        self.trading_mode = TradingMode(self.config.get('trading_mode', 'paper'))
        
        # Initialize all components
        self.slow_inference = SlowInferenceEngine(self.config.get('inference', {}))
        self.signal_validation = SignalValidationSystem(self.config.get('validation', {}))
        self.market_psychology = MarketPsychologyEngine(self.config.get('psychology', {}))
        self.growth_framework = GrowthOptimizationFramework(self.config.get('growth', {}))
        self.emergency_system = EmergencyResponseSystem(self.config.get('emergency', {}))
        self.execution_engine = EliteExecutionEngine(self.config.get('execution', {}))
        self.neural_evolution = NeuralEvolutionFramework(self.config.get('evolution', {}))
        
        # System state
        self.status = SystemStatus.INITIALIZING
        self.is_running = False
        self.last_analysis_time: Optional[datetime] = None
        
        # Decision history
        self.decision_history: deque = deque(maxlen=1000)
        self.active_positions: Dict[str, Dict[str, Any]] = {}
        
        # Analysis settings
        self.default_depth = AnalysisDepth(self.config.get('default_depth', 'deep'))
        self.min_confidence = self.config.get('min_confidence', 0.7)
        self.min_validation_score = self.config.get('min_validation_score', 0.7)
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        
        # Register emergency callback
        self.emergency_system.register_callback(self._handle_emergency)
        
        self.status = SystemStatus.READY
        logger.info("EliteTradingOrchestrator initialized")
    
    async def analyze_and_decide(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        depth: Optional[AnalysisDepth] = None
    ) -> TradingDecision:
        """
        Run complete analysis pipeline and generate trading decision
        
        Args:
            symbol: Trading symbol
            market_data: Market data including prices, volumes, indicators
            context: Additional context (news, sentiment, etc.)
            depth: Analysis depth level
            
        Returns:
            TradingDecision with complete analysis
        """
        decision_id = f"dec_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        depth = depth or self.default_depth
        context = context or {}
        
        self.status = SystemStatus.ANALYZING
        logger.info(f"Starting analysis for {symbol} with {depth.value} depth")
        
        warnings = []
        
        try:
            # Step 1: Check emergency status
            emergency_level = await self.emergency_system.monitor_market(market_data)
            if emergency_level in [EmergencyLevel.CRITICAL, EmergencyLevel.EMERGENCY]:
                self.status = SystemStatus.EMERGENCY
                return self._create_hold_decision(
                    decision_id, symbol, 
                    f"Emergency level: {emergency_level.value}",
                    warnings=["EMERGENCY: Trading suspended"]
                )
            
            # Step 2: Check if trading is allowed
            trading_allowed, reasons = self.growth_framework.check_trading_allowed()
            if not trading_allowed:
                return self._create_hold_decision(
                    decision_id, symbol,
                    f"Trading not allowed: {', '.join(reasons)}",
                    warnings=reasons
                )
            
            # Step 3: Run slow inference (deep analysis)
            inference_result = await self.slow_inference.run_inference(
                symbol, market_data, depth, context
            )
            
            # Step 4: Analyze market psychology
            psychology_state = await self.market_psychology.analyze_psychology(
                market_data, context
            )
            
            # Add psychology to context for validation
            context['market_regime'] = inference_result.market_regime
            context['psychology_state'] = psychology_state.sentiment.psychology_phase.value
            
            # Step 5: Validate signal
            signal_for_validation = {
                'signal_id': decision_id,
                'symbol': symbol,
                'action': inference_result.action,
                'entry_price': inference_result.entry_price,
                'stop_loss': inference_result.stop_loss,
                'confidence': inference_result.confidence
            }
            
            validation_result = await self.signal_validation.validate_signal(
                signal_for_validation, market_data, context
            )
            
            # Step 6: Check validation status
            if validation_result.status == ValidationStatus.FAILED:
                warnings.extend(validation_result.reasons)
                return self._create_hold_decision(
                    decision_id, symbol,
                    f"Validation failed: {validation_result.recommendation}",
                    inference_result=inference_result,
                    validation_result=validation_result,
                    psychology_state=psychology_state,
                    warnings=warnings
                )
            
            if validation_result.status == ValidationStatus.WARNING:
                warnings.extend(validation_result.reasons)
            
            # Step 7: Calculate position size
            position_signal = {
                'entry_price': inference_result.entry_price,
                'stop_loss': inference_result.stop_loss,
                'action': inference_result.action
            }
            position_scaling = self.growth_framework.calculate_position_size(
                position_signal, market_data
            )
            
            # Step 8: Optimize entry
            entry_optimization = await self.execution_engine.optimize_entry(
                signal_for_validation, market_data
            )
            
            # Step 9: Final decision checks
            final_action = inference_result.action
            final_confidence = inference_result.confidence * validation_result.overall_score
            
            # Check minimum confidence
            if final_confidence < self.min_confidence:
                final_action = 'HOLD'
                warnings.append(f"Confidence below threshold: {final_confidence:.2%}")
            
            # Check validation score
            if validation_result.overall_score < self.min_validation_score:
                final_action = 'HOLD'
                warnings.append(f"Validation score below threshold: {validation_result.overall_score:.2%}")
            
            # Create final decision
            decision = TradingDecision(
                decision_id=decision_id,
                symbol=symbol,
                action=final_action,
                confidence=final_confidence,
                entry_price=entry_optimization.optimal_entry_price if final_action != 'HOLD' else None,
                stop_loss=inference_result.stop_loss if final_action != 'HOLD' else None,
                take_profit=inference_result.take_profit if final_action != 'HOLD' else [],
                position_size=position_scaling.final_position_size if final_action != 'HOLD' else 0,
                position_size_pct=position_scaling.current_risk_pct if final_action != 'HOLD' else 0,
                risk_reward_ratio=inference_result.risk_reward_ratio,
                expected_value=inference_result.expected_value,
                inference_result=inference_result,
                validation_result=validation_result,
                psychology_state=psychology_state,
                position_scaling=position_scaling,
                entry_optimization=entry_optimization,
                reasoning_summary=self._generate_reasoning_summary(
                    inference_result, validation_result, psychology_state
                ),
                warnings=warnings
            )
            
            # Store decision
            self.decision_history.append(decision)
            self.last_analysis_time = datetime.now()
            
            # Record for neural evolution
            self.neural_evolution.record_trade_outcome({
                'decision_id': decision_id,
                'symbol': symbol,
                'action': final_action,
                'confidence': final_confidence,
                'pattern_id': inference_result.reasoning_chain.steps[1].output_data.get('market_structure', 'unknown')
            })
            
            self.status = SystemStatus.READY
            
            logger.info(f"Decision complete: {final_action} with {final_confidence:.2%} confidence")
            
            return decision
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            self.status = SystemStatus.READY
            return self._create_hold_decision(
                decision_id, symbol,
                f"Analysis error: {str(e)}",
                warnings=[f"ERROR: {str(e)}"]
            )
    
    async def start(self):
        """Start the orchestrator with background tasks"""
        if self.is_running:
            return
        
        self.is_running = True
        self.status = SystemStatus.READY
        
        # Start background evolution task
        evolution_task = asyncio.create_task(self._evolution_loop())
        self._background_tasks.append(evolution_task)
        
        logger.info("EliteTradingOrchestrator started")
    
    async def stop(self):
        """Stop the orchestrator"""
        self.is_running = False
        self.status = SystemStatus.SHUTDOWN
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        logger.info("EliteTradingOrchestrator stopped")
    
    async def _evolution_loop(self):
        """Background evolution loop"""
        while self.is_running:
            try:
                # Run evolution every 6 hours
                await asyncio.sleep(21600)
                
                if self.is_running and len(self.decision_history) > 10:
                    trade_history = [
                        {'pnl': d.expected_value, 'pattern_id': d.decision_id}
                        for d in self.decision_history
                    ]
                    await self.neural_evolution.run_evolution_cycle(trade_history, {})
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Evolution loop error: {e}")
    
    async def _handle_emergency(self, event):
        """Handle emergency events"""
        logger.warning(f"Emergency event: {event.event_type.value}")
        self.status = SystemStatus.EMERGENCY
        
        # Close all positions if critical
        if event.level in [EmergencyLevel.CRITICAL, EmergencyLevel.EMERGENCY]:
            positions = list(self.active_positions.values())
            await self.emergency_system.emergency_close_all(positions)
    
    def _create_hold_decision(
        self,
        decision_id: str,
        symbol: str,
        reason: str,
        inference_result: Optional[InferenceResult] = None,
        validation_result: Optional[ValidationResult] = None,
        psychology_state: Optional[PsychologyState] = None,
        warnings: Optional[List[str]] = None
    ) -> TradingDecision:
        """Create a HOLD decision"""
        return TradingDecision(
            decision_id=decision_id,
            symbol=symbol,
            action='HOLD',
            confidence=0.0,
            entry_price=None,
            stop_loss=None,
            take_profit=[],
            position_size=0,
            position_size_pct=0,
            risk_reward_ratio=0,
            expected_value=0,
            inference_result=inference_result,
            validation_result=validation_result,
            psychology_state=psychology_state,
            position_scaling=None,
            entry_optimization=None,
            reasoning_summary=reason,
            warnings=warnings or []
        )
    
    def _generate_reasoning_summary(
        self,
        inference: InferenceResult,
        validation: ValidationResult,
        psychology: PsychologyState
    ) -> str:
        """Generate human-readable reasoning summary"""
        parts = []
        
        # Inference summary
        parts.append(f"Analysis: {inference.action} signal with {inference.confidence:.1%} confidence")
        parts.append(f"Market regime: {inference.market_regime}")
        
        # Psychology summary
        parts.append(f"Psychology: {psychology.sentiment.psychology_phase.value}")
        parts.append(f"Institutional bias: {psychology.smart_money.institutional_bias.value}")
        
        # Validation summary
        parts.append(f"Validation: {validation.status.value} ({validation.overall_score:.1%})")
        
        # Risk/Reward
        if inference.risk_reward_ratio is not None and inference.risk_reward_ratio > 0:
            parts.append(f"R:R = {inference.risk_reward_ratio:.2f}, EV = {inference.expected_value:.3f}")
        
        return " | ".join(parts)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'status': self.status.value,
            'trading_mode': self.trading_mode.value,
            'is_running': self.is_running,
            'last_analysis': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
            'decisions_made': len(self.decision_history),
            'active_positions': len(self.active_positions),
            'emergency_level': self.emergency_system.current_level.value,
            'growth_status': self.growth_framework.get_growth_status(),
            'evolution_status': self.neural_evolution.get_evolution_status(),
            'validation_stats': self.signal_validation.get_validation_stats(),
            'execution_stats': self.execution_engine.get_execution_stats()
        }
    
    def update_position(self, symbol: str, position: Dict[str, Any]):
        """Update active position"""
        self.active_positions[symbol] = position
    
    def close_position(self, symbol: str, pnl: float):
        """Close position and update growth framework"""
        if symbol in self.active_positions:
            del self.active_positions[symbol]
        
        self.growth_framework.update_equity(pnl, {'symbol': symbol, 'pnl': pnl})
