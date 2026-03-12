"""
AlphaAlgo Core Integration Layer

Integrates the AlphaAlgo Core Engine with existing systems:
- MSOS (Market Survival Operating System)
- SurvivalCore
- Risk Managers
- Signal Validators
- Execution Systems

Author: AlphaAlgo Core
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from .alphaalgo_core_engine import (
    AlphaAlgoCoreEngine,
    TradeProposal,
    CoreDecision,
    DecisionOutcome,
    MarketHostility,
    create_alphaalgo_core
)

logger = logging.getLogger(__name__)


@dataclass
class IntegratedTradeRequest:
    """Unified trade request from any system"""
    # Core identification
    request_id: str
    symbol: str
    direction: str  # 'long' or 'short'
    quantity: float
    
    # Pricing
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Signal context
    signal_strength: float = 0.0
    signal_source: str = ""  # 'msos', 'survival_core', 'strategy', etc.
    strategy_id: str = ""
    
    # Market context
    regime: Optional[str] = None
    volatility: float = 0.0
    liquidity_score: float = 0.5
    
    # Portfolio context
    current_equity: float = 0.0
    current_drawdown: float = 0.0
    correlation_exposure: float = 0.0
    
    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class IntegratedDecision:
    """Unified decision output"""
    approved: bool
    request_id: str
    symbol: str
    
    # Decision details
    outcome: DecisionOutcome
    approved_quantity: float = 0.0
    rejection_reason: Optional[str] = None
    
    # Confidence metrics
    min_confidence: float = 0.0
    confidence_breakdown: Dict[str, float] = field(default_factory=dict)
    
    # Risk metrics
    market_hostility: Optional[str] = None
    risk_score: float = 0.0
    
    # Audit trail
    evaluation_time_ms: float = 0.0
    stage_results: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class AlphaAlgoCoreIntegration:
    """
    Integration layer for AlphaAlgo Core Engine
    
    Provides unified interface for all trading systems to use
    the hostile capital-preserving decision engine.
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.6,
        enable_strict_mode: bool = True,
        enable_msos_integration: bool = True,
        enable_survival_core_integration: bool = True
    ):
        self.confidence_threshold = confidence_threshold
        self.enable_strict_mode = enable_strict_mode
        self.enable_msos_integration = enable_msos_integration
        self.enable_survival_core_integration = enable_survival_core_integration
        
        # Initialize core engine
        self.core_engine = create_alphaalgo_core(
            required_confidence_threshold=confidence_threshold,
            enable_strict_mode=enable_strict_mode
        )
        
        # Integration components (lazy loaded)
        self._msos_orchestrator = None
        self._survival_core = None
        self._risk_manager = None
        
        logger.info("AlphaAlgo Core Integration initialized")
    
    async def evaluate_trade_request(
        self,
        request: IntegratedTradeRequest,
        market_context: Optional[Dict[str, Any]] = None
    ) -> IntegratedDecision:
        """
        Evaluate a trade request through AlphaAlgo Core
        
        Args:
            request: Unified trade request
            market_context: Optional market context data
            
        Returns:
            IntegratedDecision with approval/rejection
        """
        start_time = datetime.utcnow()
        
        # Convert to TradeProposal
        proposal = self._convert_to_proposal(request)
        
        # Enhance market context with integrated systems
        enhanced_context = await self._enhance_market_context(
            request, market_context or {}
        )
        
        # Evaluate through core engine
        core_decision = await self.core_engine.evaluate_trade(
            proposal, enhanced_context
        )
        
        # Convert to integrated decision
        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        integrated_decision = self._convert_to_integrated_decision(
            request, core_decision, elapsed_ms
        )
        
        # Log decision
        self._log_decision(integrated_decision)
        
        return integrated_decision
    
    def _convert_to_proposal(self, request: IntegratedTradeRequest) -> TradeProposal:
        """Convert IntegratedTradeRequest to TradeProposal"""
        return TradeProposal(
            trade_id=request.request_id,
            symbol=request.symbol,
            direction=request.direction,
            quantity=request.quantity,
            entry_price=request.entry_price,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            signal_strength=request.signal_strength,
            strategy_id=request.strategy_id,
            timestamp=request.timestamp,
            regime=request.regime,
            volatility=request.volatility,
            liquidity_score=request.liquidity_score,
            current_equity=request.current_equity,
            current_drawdown=request.current_drawdown,
            correlation_exposure=request.correlation_exposure
        )
    
    async def _enhance_market_context(
        self,
        request: IntegratedTradeRequest,
        base_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance market context with data from integrated systems"""
        enhanced = base_context.copy()
        
        # Add MSOS data if available
        if self.enable_msos_integration and self._msos_orchestrator:
            try:
                msos_data = await self._get_msos_context(request)
                enhanced.update(msos_data)
            except Exception as e:
                logger.warning(f"Failed to get MSOS context: {e}")
        
        # Add SurvivalCore data if available
        if self.enable_survival_core_integration and self._survival_core:
            try:
                survival_data = await self._get_survival_core_context(request)
                enhanced.update(survival_data)
            except Exception as e:
                logger.warning(f"Failed to get SurvivalCore context: {e}")
        
        # Ensure required fields exist
        enhanced.setdefault('recent_performance', [])
        enhanced.setdefault('regime_stability', 0.7)
        enhanced.setdefault('liquidity_stress', 0.2)
        enhanced.setdefault('cross_strategy_dispersion', 0.3)
        
        return enhanced
    
    async def _get_msos_context(self, request: IntegratedTradeRequest) -> Dict[str, Any]:
        """Get context from MSOS orchestrator"""
        # Lazy load MSOS
        if not self._msos_orchestrator:
            try:
                from trading_bot.msos import MSOSOrchestrator
                self._msos_orchestrator = MSOSOrchestrator()
            except ImportError:
                logger.warning("MSOS not available")
                return {}
        
        # Get MSOS state
        context = {}
        
        # Add regime stability from MSOS
        # (This would integrate with actual MSOS regime detector)
        context['regime_stability'] = 0.7  # Placeholder
        
        return context
    
    async def _get_survival_core_context(self, request: IntegratedTradeRequest) -> Dict[str, Any]:
        """Get context from SurvivalCore"""
        # Lazy load SurvivalCore
        if not self._survival_core:
            try:
                from trading_bot.core.survival_core import SurvivalCore
                self._survival_core = SurvivalCore()
            except ImportError:
                logger.warning("SurvivalCore not available")
                return {}
        
        context = {}
        
        # Add recent performance
        # (This would integrate with actual SurvivalCore performance tracking)
        context['recent_performance'] = []  # Placeholder
        
        return context
    
    def _convert_to_integrated_decision(
        self,
        request: IntegratedTradeRequest,
        core_decision: CoreDecision,
        elapsed_ms: float
    ) -> IntegratedDecision:
        """Convert CoreDecision to IntegratedDecision"""
        approved = (core_decision.outcome == DecisionOutcome.TRADE_APPROVED)
        
        # Extract confidence breakdown
        confidence_breakdown = {}
        if core_decision.confidence_vector:
            cv = core_decision.confidence_vector
            confidence_breakdown = {
                'statistical': cv.statistical,
                'regime': cv.regime,
                'execution': cv.execution,
                'tail_risk': cv.tail_risk,
                'model_stability': cv.model_stability,
                'minimum': cv.min_confidence()
            }
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(core_decision)
        
        # Build stage results
        stage_results = {
            'market_hostility': core_decision.market_hostility.name if core_decision.market_hostility else None,
            'failed_claims': [c.name for c in core_decision.failed_claims],
            'killer_verdict': core_decision.killer_verdict.reason if core_decision.killer_verdict else None,
            'agent_verdicts': [
                {'agent': v.agent.name, 'approved': v.approved, 'reason': v.reason}
                for v in core_decision.all_verdicts
            ]
        }
        
        return IntegratedDecision(
            approved=approved,
            request_id=request.request_id,
            symbol=request.symbol,
            outcome=core_decision.outcome,
            approved_quantity=core_decision.approved_position_size if approved else 0.0,
            rejection_reason=core_decision.dominant_rejection_reason,
            min_confidence=confidence_breakdown.get('minimum', 0.0),
            confidence_breakdown=confidence_breakdown,
            market_hostility=core_decision.market_hostility.name if core_decision.market_hostility else None,
            risk_score=risk_score,
            evaluation_time_ms=elapsed_ms,
            stage_results=stage_results
        )
    
    def _calculate_risk_score(self, core_decision: CoreDecision) -> float:
        """Calculate overall risk score (0-1, higher = riskier)"""
        if core_decision.outcome == DecisionOutcome.TRADE_APPROVED:
            # Low risk if approved
            if core_decision.confidence_vector:
                return 1.0 - core_decision.confidence_vector.min_confidence()
            return 0.5
        elif core_decision.outcome == DecisionOutcome.NO_TRADE_MARKET_HOSTILE:
            # High risk if market hostile
            return 0.9
        else:
            # Medium-high risk if rejected
            return 0.7
    
    def _log_decision(self, decision: IntegratedDecision):
        """Log decision for audit trail"""
        if decision.approved:
            logger.info(
                f"APPROVED: {decision.symbol} {decision.request_id} "
                f"(qty={decision.approved_quantity:.3f}, "
                f"conf={decision.min_confidence:.3f}, "
                f"time={decision.evaluation_time_ms:.1f}ms)"
            )
        else:
            logger.warning(
                f"REJECTED: {decision.symbol} {decision.request_id} "
                f"({decision.outcome.value}) - {decision.rejection_reason}"
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get integration statistics"""
        core_stats = self.core_engine.get_statistics()
        
        return {
            'core_engine': core_stats,
            'integration': {
                'msos_enabled': self.enable_msos_integration,
                'survival_core_enabled': self.enable_survival_core_integration,
                'confidence_threshold': self.confidence_threshold,
                'strict_mode': self.enable_strict_mode
            }
        }


class MSOSAdapter:
    """Adapter for MSOS integration"""
    
    def __init__(self, core_integration: AlphaAlgoCoreIntegration):
        self.core_integration = core_integration
        
    async def evaluate_msos_signal(
        self,
        symbol: str,
        signal_data: Dict[str, Any],
        strategy_config: Dict[str, Any],
        equity: float
    ) -> Tuple[bool, Optional[float], str]:
        """
        Evaluate MSOS signal through AlphaAlgo Core
        
        Returns:
            (approved, position_size, reason)
        """
        # Convert MSOS signal to IntegratedTradeRequest
        request = IntegratedTradeRequest(
            request_id=f"msos_{symbol}_{datetime.utcnow().timestamp()}",
            symbol=symbol,
            direction=signal_data.get('direction', 'long'),
            quantity=signal_data.get('quantity', 1.0),
            entry_price=signal_data.get('price', 0.0),
            stop_loss=signal_data.get('stop_loss'),
            take_profit=signal_data.get('take_profit'),
            signal_strength=signal_data.get('confidence', 0.5),
            signal_source='msos',
            strategy_id=strategy_config.get('strategy_id', 'unknown'),
            regime=signal_data.get('regime'),
            volatility=signal_data.get('volatility', 0.2),
            liquidity_score=signal_data.get('liquidity_score', 0.5),
            current_equity=equity,
            current_drawdown=signal_data.get('drawdown', 0.0),
            correlation_exposure=signal_data.get('correlation', 0.0)
        )
        
        # Evaluate
        decision = await self.core_integration.evaluate_trade_request(request)
        
        return (
            decision.approved,
            decision.approved_quantity if decision.approved else None,
            decision.rejection_reason or "Approved"
        )


class SurvivalCoreAdapter:
    """Adapter for SurvivalCore integration"""
    
    def __init__(self, core_integration: AlphaAlgoCoreIntegration):
        self.core_integration = core_integration
        
    async def validate_survival_signal(
        self,
        signal: Dict[str, Any],
        portfolio_state: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validate SurvivalCore signal through AlphaAlgo Core
        
        Returns:
            (approved, reason)
        """
        # Convert to IntegratedTradeRequest
        request = IntegratedTradeRequest(
            request_id=signal.get('signal_id', 'unknown'),
            symbol=signal.get('symbol', ''),
            direction=signal.get('direction', 'long'),
            quantity=signal.get('quantity', 1.0),
            entry_price=signal.get('price', 0.0),
            stop_loss=signal.get('stop_loss'),
            signal_strength=signal.get('confidence', 0.5),
            signal_source='survival_core',
            strategy_id=signal.get('strategy', 'unknown'),
            current_equity=portfolio_state.get('equity', 0.0),
            current_drawdown=portfolio_state.get('drawdown', 0.0)
        )
        
        # Evaluate
        decision = await self.core_integration.evaluate_trade_request(request)
        
        return (
            decision.approved,
            decision.rejection_reason or "Approved"
        )


class RiskManagerAdapter:
    """Adapter for Risk Manager integration"""
    
    def __init__(self, core_integration: AlphaAlgoCoreIntegration):
        self.core_integration = core_integration
        
    async def validate_risk_limits(
        self,
        trade_request: Dict[str, Any],
        portfolio: Dict[str, Any]
    ) -> Tuple[bool, Optional[float], str]:
        """
        Validate trade against risk limits through AlphaAlgo Core
        
        Returns:
            (approved, adjusted_size, reason)
        """
        # Convert to IntegratedTradeRequest
        request = IntegratedTradeRequest(
            request_id=trade_request.get('id', 'unknown'),
            symbol=trade_request.get('symbol', ''),
            direction=trade_request.get('direction', 'long'),
            quantity=trade_request.get('quantity', 1.0),
            entry_price=trade_request.get('price', 0.0),
            stop_loss=trade_request.get('stop_loss'),
            signal_source='risk_manager',
            current_equity=portfolio.get('equity', 0.0),
            current_drawdown=portfolio.get('drawdown', 0.0),
            correlation_exposure=portfolio.get('correlation', 0.0)
        )
        
        # Evaluate
        decision = await self.core_integration.evaluate_trade_request(request)
        
        return (
            decision.approved,
            decision.approved_quantity if decision.approved else None,
            decision.rejection_reason or "Approved"
        )


# Factory functions
def create_core_integration(
    confidence_threshold: float = 0.6,
    enable_strict_mode: bool = True,
    enable_msos: bool = True,
    enable_survival_core: bool = True
) -> AlphaAlgoCoreIntegration:
    """Create AlphaAlgo Core Integration instance"""
    return AlphaAlgoCoreIntegration(
        confidence_threshold=confidence_threshold,
        enable_strict_mode=enable_strict_mode,
        enable_msos_integration=enable_msos,
        enable_survival_core_integration=enable_survival_core
    )


def create_msos_adapter(
    core_integration: Optional[AlphaAlgoCoreIntegration] = None
) -> MSOSAdapter:
    """Create MSOS adapter"""
    if core_integration is None:
        core_integration = create_core_integration()
    return MSOSAdapter(core_integration)


def create_survival_core_adapter(
    core_integration: Optional[AlphaAlgoCoreIntegration] = None
) -> SurvivalCoreAdapter:
    """Create SurvivalCore adapter"""
    if core_integration is None:
        core_integration = create_core_integration()
    return SurvivalCoreAdapter(core_integration)


def create_risk_manager_adapter(
    core_integration: Optional[AlphaAlgoCoreIntegration] = None
) -> RiskManagerAdapter:
    """Create Risk Manager adapter"""
    if core_integration is None:
        core_integration = create_core_integration()
    return RiskManagerAdapter(core_integration)
