"""
AgentFlow Orchestration System

Implements Stanford's AgentFlow architecture with planner-verifier-executor pattern.
Coordinates multi-agent workflow for safe, explainable trading decisions.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import numpy as np
import pandas as pd
import numpy
import pandas

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent roles in the system."""
    PLANNER = "planner"
    VERIFIER = "verifier"
    EXECUTOR = "executor"
    SAFETY_VALIDATOR = "safety_validator"
    MONITOR = "monitor"


class DecisionStatus(Enum):
    """Status of trading decisions."""
    PROPOSED = "proposed"
    VALIDATED = "validated"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


@dataclass
class TradingContext:
    """Context for trading decisions."""
    timestamp: datetime
    market_data: pd.DataFrame
    portfolio_state: Dict[str, Any]
    risk_metrics: Dict[str, float]
    forecasts: Dict[str, Any]
    regime: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradingProposal:
    """Proposed trading action."""
    proposal_id: str
    timestamp: datetime
    action: str  # 'buy', 'sell', 'hold', 'close'
    symbol: str
    size: float
    price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    
    # Reasoning
    rationale: str
    confidence: float
    expected_return: float
    expected_risk: float
    
    # Attribution
    features: Dict[str, float]
    model_version: str
    agent_id: str
    
    # Status
    status: DecisionStatus = DecisionStatus.PROPOSED
    validation_results: Dict[str, Any] = field(default_factory=dict)
    execution_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of proposal validation."""
    is_valid: bool
    validator_id: str
    checks_passed: List[str]
    checks_failed: List[str]
    risk_score: float
    confidence_adjustment: float
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradingDecision:
    """
    Trading decision output from agents.
    
    Simplified version of TradingProposal for agent communication.
    """
    action: str  # 'buy', 'sell', 'hold', 'close'
    confidence: float
    reasoning: str
    symbol: Optional[str] = None
    size: Optional[float] = None
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_actionable(self) -> bool:
        """Check if decision requires action."""
        return self.action in ('buy', 'sell', 'close') and self.confidence > 0.5


class BaseAgent:
    """Base class for all agents."""
    
    def __init__(self, agent_id: str, role: AgentRole, config: Optional[Dict] = None):
        self.agent_id = agent_id
        self.role = role
        self.config = config or {}
        self.is_active = True
        self.performance_history = []
        
        logger.info(f"Initialized {role.value} agent: {agent_id}")
    
    async def process(self, context: TradingContext) -> Any:
        """Process trading context. Override in subclasses."""
        # Default implementation - log and return context
        logger.info(f"{self.role.value} agent processing context for {context.symbol}")
        
        # Basic processing - can be overridden
        return {
            'agent_id': self.agent_id,
            'role': self.role.value,
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'status': 'processed'
        }
    
    def update_performance(self, metric: float):
        """Update agent performance metrics."""
        self.performance_history.append({
            'timestamp': datetime.now(),
            'metric': metric
        })
        
        # Keep last 1000 records
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]


class PlannerAgent(BaseAgent):
    """
    Planner Agent - Analyzes market and proposes trading actions.
    
    Uses:
    - RL policies (CQL, BCQ, BEAR, MBOP, MAGIC)
    - Forecasting models (TFT, Informer, N-BEATS, DeepAR)
    - Technical analysis
    - Sentiment analysis
    """
    
    def __init__(self, agent_id: str = "planner_001", config: Optional[Dict] = None):
        super().__init__(agent_id, AgentRole.PLANNER, config)
        
        self.rl_agents = []  # Will be populated with RL agents
        self.forecasters = []  # Will be populated with forecasting models
        self.min_confidence = config.get('min_confidence', 0.6)
    
    async def process(self, context: TradingContext) -> List[TradingProposal]:
        """
        Generate trading proposals based on analysis.
        
        Args:
            context: Current trading context
        
        Returns:
            List of trading proposals
        """
        proposals = []
        
        try:
            # 1. Get RL policy recommendations
            rl_actions = await self._get_rl_recommendations(context)
            
            # 2. Get forecast-based signals
            forecast_signals = await self._get_forecast_signals(context)
            
            # 3. Combine and rank proposals
            combined_proposals = self._combine_signals(
                rl_actions, 
                forecast_signals, 
                context
            )
            
            # 4. Filter by confidence
            filtered_proposals = [
                p for p in combined_proposals 
                if p.confidence >= self.min_confidence
            ]
            
            logger.info(
                f"Planner generated {len(filtered_proposals)} proposals "
                f"(filtered from {len(combined_proposals)})"
            )
            
            return filtered_proposals
            
        except Exception as e:
            logger.error(f"Planner error: {e}", exc_info=True)
            return []
    
    async def _get_rl_recommendations(self, context: TradingContext) -> List[Dict]:
        """Get recommendations from RL agents."""
        recommendations = []
        
        for agent in self.rl_agents:
            try:
                action = await agent.get_action(context)
                recommendations.append({
                    'source': 'rl',
                    'agent': agent.name,
                    'action': action,
                    'confidence': action.get('confidence', 0.5)
                })
            except Exception as e:
                logger.error(f"RL agent {agent.name} error: {e}")
        
        return recommendations
    
    async def _get_forecast_signals(self, context: TradingContext) -> List[Dict]:
        """Get signals from forecasting models."""
        signals = []
        
        for forecaster in self.forecasters:
            try:
                forecast = await forecaster.predict(context.market_data)
                signal = self._forecast_to_signal(forecast)
                signals.append({
                    'source': 'forecast',
                    'model': forecaster.name,
                    'signal': signal,
                    'confidence': forecast.get('confidence', 0.5)
                })
            except Exception as e:
                logger.error(f"Forecaster {forecaster.name} error: {e}")
        
        return signals
    
    def _forecast_to_signal(self, forecast: Dict) -> str:
        """Convert forecast to trading signal."""
        predicted_return = forecast.get('predicted_return', 0)
        
        if predicted_return > 0.001:
            return 'buy'
        elif predicted_return < -0.001:
            return 'sell'
        else:
            return 'hold'
    
    def _combine_signals(
        self, 
        rl_actions: List[Dict], 
        forecast_signals: List[Dict],
        context: TradingContext
    ) -> List[TradingProposal]:
        """Combine signals from different sources into proposals."""
        proposals = []
        
        # Aggregate signals
        buy_confidence = 0.0
        sell_confidence = 0.0
        hold_confidence = 0.0
        
        all_signals = rl_actions + forecast_signals
        
        for signal in all_signals:
            action = signal.get('action', signal.get('signal', 'hold'))
            confidence = signal.get('confidence', 0.5)
            
            if action == 'buy':
                buy_confidence += confidence
            elif action == 'sell':
                sell_confidence += confidence
            else:
                hold_confidence += confidence
        
        # Normalize
        total = buy_confidence + sell_confidence + hold_confidence
        if total > 0:
            buy_confidence /= total
            sell_confidence /= total
            hold_confidence /= total
        
        # Create proposal for strongest signal
        max_confidence = max(buy_confidence, sell_confidence, hold_confidence)
        
        if max_confidence == buy_confidence and buy_confidence > 0.5:
            action = 'buy'
            confidence = buy_confidence
        elif max_confidence == sell_confidence and sell_confidence > 0.5:
            action = 'sell'
            confidence = sell_confidence
        else:
            action = 'hold'
            confidence = hold_confidence
        
        if action != 'hold':
            proposal = TradingProposal(
                proposal_id=f"prop_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                action=action,
                symbol=context.market_data.get('symbol', 'UNKNOWN'),
                size=self._calculate_position_size(context, confidence),
                price=None,  # Will be filled by executor
                stop_loss=None,
                take_profit=None,
                rationale=f"Combined signal from {len(all_signals)} sources",
                confidence=confidence,
                expected_return=0.01 if action == 'buy' else -0.01,
                expected_risk=0.005,
                features={},
                model_version="ensemble_v1",
                agent_id=self.agent_id
            )
            proposals.append(proposal)
        
        return proposals
    
    def _calculate_position_size(self, context: TradingContext, confidence: float) -> float:
        """Calculate position size based on confidence and risk."""
        # Simple Kelly-like sizing
        base_size = 0.1  # 10% of portfolio
        adjusted_size = base_size * confidence
        
        # Apply risk limits
        max_size = context.risk_metrics.get('max_position_size', 0.2)
        return min(adjusted_size, max_size)


class VerifierAgent(BaseAgent):
    """
    Verifier Agent - Validates trading proposals.
    
    Checks:
    - Risk limits (exposure, drawdown, concentration)
    - Market conditions (liquidity, volatility)
    - Model confidence and uncertainty
    - Historical performance patterns
    """
    
    def __init__(self, agent_id: str = "verifier_001", config: Optional[Dict] = None):
        super().__init__(agent_id, AgentRole.VERIFIER, config)
        
        self.max_exposure = config.get('max_exposure', 1.0)
        self.max_drawdown = config.get('max_drawdown', 0.2)
        self.min_liquidity = config.get('min_liquidity', 1000000)
        self.max_volatility = config.get('max_volatility', 0.05)
    
    async def process(
        self, 
        proposal: TradingProposal, 
        context: TradingContext
    ) -> ValidationResult:
        """
        Validate trading proposal.
        
        Args:
            proposal: Trading proposal to validate
            context: Current trading context
        
        Returns:
            Validation result
        """
        checks_passed = []
        checks_failed = []
        risk_score = 0.0
        
        try:
            # 1. Check exposure limits
            if self._check_exposure(proposal, context):
                checks_passed.append("exposure_limit")
            else:
                checks_failed.append("exposure_limit")
                risk_score += 0.3
            
            # 2. Check drawdown
            if self._check_drawdown(context):
                checks_passed.append("drawdown_limit")
            else:
                checks_failed.append("drawdown_limit")
                risk_score += 0.4
            
            # 3. Check liquidity
            if self._check_liquidity(context):
                checks_passed.append("liquidity")
            else:
                checks_failed.append("liquidity")
                risk_score += 0.2
            
            # 4. Check volatility
            if self._check_volatility(context):
                checks_passed.append("volatility")
            else:
                checks_failed.append("volatility")
                risk_score += 0.1
            
            # 5. Check confidence
            if proposal.confidence >= 0.6:
                checks_passed.append("confidence")
            else:
                checks_failed.append("confidence")
                risk_score += 0.2
            
            is_valid = len(checks_failed) == 0
            
            # Adjust confidence based on checks
            confidence_adjustment = 1.0 - (risk_score * 0.5)
            
            recommendations = []
            if not is_valid:
                recommendations.append(f"Failed checks: {', '.join(checks_failed)}")
                if 'exposure_limit' in checks_failed:
                    recommendations.append("Reduce position size")
                if 'drawdown_limit' in checks_failed:
                    recommendations.append("Wait for recovery")
            
            return ValidationResult(
                is_valid=is_valid,
                validator_id=self.agent_id,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                risk_score=risk_score,
                confidence_adjustment=confidence_adjustment,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Verifier error: {e}", exc_info=True)
            return ValidationResult(
                is_valid=False,
                validator_id=self.agent_id,
                checks_passed=[],
                checks_failed=["validation_error"],
                risk_score=1.0,
                confidence_adjustment=0.0,
                recommendations=["Validation failed due to error"]
            )
    
    def _check_exposure(self, proposal: TradingProposal, context: TradingContext) -> bool:
        """Check if proposal exceeds exposure limits."""
        current_exposure = context.portfolio_state.get('total_exposure', 0.0)
        new_exposure = current_exposure + proposal.size
        return new_exposure <= self.max_exposure
    
    def _check_drawdown(self, context: TradingContext) -> bool:
        """Check if current drawdown is within limits."""
        current_drawdown = context.risk_metrics.get('current_drawdown', 0.0)
        return abs(current_drawdown) <= self.max_drawdown
    
    def _check_liquidity(self, context: TradingContext) -> bool:
        """Check if market has sufficient liquidity."""
        liquidity = context.market_data.get('volume', 0) * context.market_data.get('close', 0)
        return liquidity >= self.min_liquidity
    
    def _check_volatility(self, context: TradingContext) -> bool:
        """Check if volatility is within acceptable range."""
        volatility = context.risk_metrics.get('volatility', 0.0)
        return volatility <= self.max_volatility


class SafetyValidatorAgent(BaseAgent):
    """
    Safety Validator Agent - Final safety check before execution.
    
    Can veto trades based on:
    - Extreme market conditions
    - Model uncertainty
    - Anomaly detection
    - Circuit breaker triggers
    """
    
    def __init__(self, agent_id: str = "safety_001", config: Optional[Dict] = None):
        super().__init__(agent_id, AgentRole.SAFETY_VALIDATOR, config)
        
        self.circuit_breaker_threshold = config.get('circuit_breaker_threshold', 0.1)
        self.max_uncertainty = config.get('max_uncertainty', 0.5)
    
    async def process(
        self, 
        proposal: TradingProposal, 
        context: TradingContext
    ) -> Tuple[bool, str]:
        """
        Final safety check.
        
        Args:
            proposal: Validated proposal
            context: Current context
        
        Returns:
            (approved, reason)
        """
        try:
            # 1. Check circuit breaker
            if self._circuit_breaker_triggered(context):
                return False, "Circuit breaker triggered - extreme market conditions"
            
            # 2. Check model uncertainty
            if proposal.confidence < (1.0 - self.max_uncertainty):
                return False, f"Model uncertainty too high: {1.0 - proposal.confidence:.2f}"
            
            # 3. Check for anomalies
            if self._detect_anomaly(context):
                return False, "Market anomaly detected"
            
            # 4. Check regime compatibility
            if not self._check_regime_compatibility(proposal, context):
                return False, "Proposal incompatible with current market regime"
            
            return True, "All safety checks passed"
            
        except Exception as e:
            logger.error(f"Safety validator error: {e}", exc_info=True)
            return False, f"Safety validation error: {str(e)}"
    
    def _circuit_breaker_triggered(self, context: TradingContext) -> bool:
        """Check if circuit breaker should trigger."""
        recent_pnl = context.portfolio_state.get('recent_pnl', 0.0)
        return abs(recent_pnl) > self.circuit_breaker_threshold
    
    def _detect_anomaly(self, context: TradingContext) -> bool:
        """Detect market anomalies."""
        # Simple anomaly detection based on z-score
        if 'price_zscore' in context.risk_metrics:
            return abs(context.risk_metrics['price_zscore']) > 3.0
        return False
    
    def _check_regime_compatibility(
        self, 
        proposal: TradingProposal, 
        context: TradingContext
    ) -> bool:
        """Check if proposal is compatible with current regime."""
        regime = context.regime
        
        # Example: Don't trade aggressively in high volatility regime
        if regime == 'high_volatility' and proposal.size > 0.05:
            return False
        
        return True


class ExecutorAgent(BaseAgent):
    """
    Executor Agent - Executes approved trades.
    
    Uses:
    - Almgren-Chriss optimal execution
    - RL-based adaptive execution
    - Market impact models
    - Smart order routing
    """
    
    def __init__(self, agent_id: str = "executor_001", config: Optional[Dict] = None):
        super().__init__(agent_id, AgentRole.EXECUTOR, config)
        
        self.execution_algorithm = config.get('execution_algorithm', 'almgren_chriss')
        self.max_slippage = config.get('max_slippage', 0.001)
    
    async def process(
        self, 
        proposal: TradingProposal, 
        context: TradingContext
    ) -> Dict[str, Any]:
        """
        Execute approved proposal.
        
        Args:
            proposal: Approved proposal
            context: Current context
        
        Returns:
            Execution results
        """
        try:
            # 1. Determine execution strategy
            strategy = self._select_execution_strategy(proposal, context)
            
            # 2. Execute trade
            result = await self._execute_trade(proposal, strategy, context)
            
            # 3. Record execution
            self._record_execution(proposal, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Executor error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'proposal_id': proposal.proposal_id
            }
    
    def _select_execution_strategy(
        self, 
        proposal: TradingProposal, 
        context: TradingContext
    ) -> str:
        """Select optimal execution strategy."""
        # Large orders use Almgren-Chriss
        if proposal.size > 0.1:
            return 'almgren_chriss'
        
        # High urgency uses aggressive execution
        if proposal.confidence > 0.9:
            return 'aggressive'
        
        # Default to adaptive
        return 'adaptive'
    
    async def _execute_trade(
        self, 
        proposal: TradingProposal, 
        strategy: str,
        context: TradingContext
    ) -> Dict[str, Any]:
        """Execute trade using selected strategy."""
        # Placeholder - actual execution would interface with broker
        return {
            'success': True,
            'proposal_id': proposal.proposal_id,
            'executed_size': proposal.size,
            'executed_price': context.market_data.get('close', 0),
            'slippage': 0.0001,
            'commission': 0.0005,
            'strategy': strategy,
            'timestamp': datetime.now()
        }
    
    def _record_execution(self, proposal: TradingProposal, result: Dict):
        """Record execution for analysis."""
        proposal.execution_results = result
        proposal.status = DecisionStatus.EXECUTED if result['success'] else DecisionStatus.FAILED


class AgentOrchestrator:
    """
    Agent Orchestrator - Coordinates multi-agent workflow.
    
    Implements AgentFlow pattern:
    1. Planner proposes actions
    2. Verifier validates proposals
    3. Safety Validator performs final check
    4. Executor executes approved trades
    5. Monitor tracks performance
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize agents
        self.planner = PlannerAgent(config=config.get('planner', {}))
        self.verifier = VerifierAgent(config=config.get('verifier', {}))
        self.safety_validator = SafetyValidatorAgent(config=config.get('safety', {}))
        self.executor = ExecutorAgent(config=config.get('executor', {}))
        
        # Tracking
        self.decision_history = []
        self.performance_metrics = {
            'total_proposals': 0,
            'validated_proposals': 0,
            'executed_trades': 0,
            'rejected_trades': 0,
            'failed_trades': 0
        }
        
        logger.info("AgentOrchestrator initialized")
    
    async def process_trading_cycle(self, context: TradingContext) -> List[Dict[str, Any]]:
        """
        Execute complete trading cycle.
        
        Args:
            context: Current trading context
        
        Returns:
            List of execution results
        """
        results = []
        
        try:
            # 1. Planning phase
            logger.info("=== Planning Phase ===")
            proposals = await self.planner.process(context)
            self.performance_metrics['total_proposals'] += len(proposals)
            
            if not proposals:
                logger.info("No proposals generated")
                return results
            
            # 2. Verification phase
            logger.info(f"=== Verification Phase ({len(proposals)} proposals) ===")
            for proposal in proposals:
                # Verify
                validation = await self.verifier.process(proposal, context)
                proposal.validation_results = validation.__dict__
                
                if not validation.is_valid:
                    proposal.status = DecisionStatus.REJECTED
                    self.performance_metrics['rejected_trades'] += 1
                    logger.info(
                        f"Proposal {proposal.proposal_id} rejected: "
                        f"{', '.join(validation.checks_failed)}"
                    )
                    continue
                
                proposal.status = DecisionStatus.VALIDATED
                self.performance_metrics['validated_proposals'] += 1
                
                # 3. Safety validation phase
                logger.info(f"=== Safety Validation ({proposal.proposal_id}) ===")
                approved, reason = await self.safety_validator.process(proposal, context)
                
                if not approved:
                    proposal.status = DecisionStatus.REJECTED
                    self.performance_metrics['rejected_trades'] += 1
                    logger.warning(f"Safety veto: {reason}")
                    continue
                
                # 4. Execution phase
                logger.info(f"=== Execution Phase ({proposal.proposal_id}) ===")
                execution_result = await self.executor.process(proposal, context)
                
                if execution_result['success']:
                    self.performance_metrics['executed_trades'] += 1
                else:
                    self.performance_metrics['failed_trades'] += 1
                
                results.append(execution_result)
                
                # Record decision
                self.decision_history.append({
                    'timestamp': datetime.now(),
                    'proposal': proposal,
                    'validation': validation,
                    'execution': execution_result
                })
            
            logger.info(f"=== Cycle Complete: {len(results)} trades executed ===")
            
        except Exception as e:
            logger.error(f"Orchestrator error: {e}", exc_info=True)
        
        return results
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        total = self.performance_metrics['total_proposals']
        executed = self.performance_metrics['executed_trades']
        
        return {
            **self.performance_metrics,
            'execution_rate': executed / total if total > 0 else 0.0,
            'rejection_rate': self.performance_metrics['rejected_trades'] / total if total > 0 else 0.0,
            'success_rate': executed / (executed + self.performance_metrics['failed_trades']) if (executed + self.performance_metrics['failed_trades']) > 0 else 0.0
        }


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.INFO)
    
    async def demo():
        print("\n" + "="*80)
        logger.info("AGENTFLOW ORCHESTRATION DEMO")
        print("="*80)
        
        # Create orchestrator
        orchestrator = AgentOrchestrator()
        
        # Create mock context
        context = TradingContext(
            timestamp=datetime.now(),
            market_data=pd.DataFrame({
                'close': [1.1000],
                'volume': [1000000],
                'symbol': ['EURUSD']
            }).iloc[0],
            portfolio_state={'total_exposure': 0.3},
            risk_metrics={'current_drawdown': 0.05, 'volatility': 0.02},
            forecasts={},
            regime='normal',
            confidence=0.8
        )
        
        # Run trading cycle
        results = await orchestrator.process_trading_cycle(context)
        
        logger.info(f"\nResults: {len(results)} trades executed")
        logger.info("\nPerformance Summary:")
        summary = orchestrator.get_performance_summary()
        for key, value in summary.items():
            logger.info(f"  {key}: {value}")
    
    asyncio.run(demo())
