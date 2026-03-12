"""
AlphaAlgo Institutional - Master Orchestrator
==============================================

The Master Orchestrator integrates all 7 layers of the AlphaAlgo Institutional
system into a cohesive, institutional-grade quantitative research platform.

Architecture:
    Layer 1: Market Selection Layer
    Layer 2: Regime Detection Layer
    Layer 3: Quantitative Research Layer
    Layer 4: Strategic Portfolio Allocation Layer
    Layer 5: Risk Governance Layer
    Layer 6: Execution & Microstructure Layer
    Layer 7: Monitoring, Audit & Evolution Layer

Core Philosophy:
    - Markets are non-stationary, adversarial, and partially efficient
    - Prediction is unreliable; distribution control is superior
    - Capital preservation has veto power over opportunity
    - All models decay; systems must adapt or delete them
    - Portfolio behavior matters more than individual strategies
    - Risk is global, not local
    - No single model is ever trusted
    - Evolution is mostly subtraction, not addition
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import asyncio
import uuid

from .core_types import (
    MarketRegime, ModelStatus, RiskLevel, CommitteeType,
    CommitteeVote, CommitteeDecision, SystemConstants
)
from .layer1_market_selection import MarketSelectionLayer, MarketSelectionCommittee
from .layer2_regime_detection import RegimeDetectionLayer, RegimeIntelligenceUnit
from .layer3_quantitative_research import QuantitativeResearchLayer, QuantitativeResearchLab
from .layer4_portfolio_allocation import PortfolioAllocationLayer, PortfolioCapitalCommittee
from .layer5_risk_governance import RiskGovernanceLayer, ValidationKillCommittee
from .layer6_execution import ExecutionLayer, ExecutionIntelligenceUnit, ExecutionUrgency
from .layer7_monitoring_evolution import MonitoringEvolutionLayer, EvolutionAuditEngine
from .idea_vectors import IdeaVectorConstraints
from .research_loop import SelfEvolvingResearchLoop

logger = logging.getLogger(__name__)


# =============================================================================
# ORCHESTRATOR TYPES
# =============================================================================

class SystemState(Enum):
    """System operational states."""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    EMERGENCY = "emergency"
    SHUTDOWN = "shutdown"


class TradingMode(Enum):
    """Trading modes."""
    DISABLED = "disabled"
    PAPER = "paper"
    LIVE = "live"


@dataclass
class SystemStatus:
    """Current system status."""
    state: SystemState
    trading_mode: TradingMode
    current_regime: MarketRegime
    risk_level: RiskLevel
    active_strategies: int
    total_capital: float
    allocated_capital: float
    current_drawdown: float
    last_update: datetime


@dataclass
class TradingDecision:
    """A trading decision from the system."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: datetime = field(default_factory=datetime.utcnow)
    symbol: str = ""
    direction: str = ""  # 'buy', 'sell', 'hold'
    quantity: float = 0.0
    confidence: float = 0.0
    strategy_id: str = ""
    rationale: str = ""
    committee_votes: List[CommitteeVote] = field(default_factory=list)
    approved: bool = False
    executed: bool = False
    execution_price: Optional[float] = None


@dataclass
class SystemConfig:
    """System configuration."""
    trading_mode: TradingMode = TradingMode.PAPER
    initial_capital: float = 1000000.0
    max_strategies: int = 20
    research_cycle_hours: int = 24
    risk_check_minutes: int = 5
    rebalance_threshold: float = 0.05
    enable_auto_evolution: bool = True
    enable_auto_trading: bool = False


# =============================================================================
# INTERNAL COMMITTEES
# =============================================================================

class InternalCommittees:
    """
    The 7 Internal Committees that govern the system.
    
    1. Market Selection Committee
    2. Regime Intelligence Unit
    3. Quantitative Research Lab
    4. Validation & Kill Committee
    5. Portfolio & Capital Committee
    6. Execution Intelligence Unit
    7. Evolution & Audit Engine
    """
    
    def __init__(
        self,
        market_selection: MarketSelectionCommittee,
        regime_intelligence: RegimeIntelligenceUnit,
        research_lab: QuantitativeResearchLab,
        validation_kill: ValidationKillCommittee,
        portfolio_capital: PortfolioCapitalCommittee,
        execution_intelligence: ExecutionIntelligenceUnit,
        evolution_audit: EvolutionAuditEngine
    ):
        self.market_selection = market_selection
        self.regime_intelligence = regime_intelligence
        self.research_lab = research_lab
        self.validation_kill = validation_kill
        self.portfolio_capital = portfolio_capital
        self.execution_intelligence = execution_intelligence
        self.evolution_audit = evolution_audit
    
    def vote_on_trade(self, trade_proposal: Dict[str, Any]) -> List[CommitteeVote]:
        """
        All committees vote on a trade proposal.
        
        Returns:
            List of committee votes
        """
        votes = []
        
        # Risk committee has veto power
        risk_vote = self.validation_kill.vote(trade_proposal)
        votes.append(risk_vote)
        
        # If risk rejects, no need for other votes
        if risk_vote.decision == CommitteeDecision.REJECT:
            return votes
        
        # Regime intelligence vote
        regime_vote = self.regime_intelligence.vote(trade_proposal.get('action', 'hold'))
        votes.append(regime_vote)
        
        # Portfolio committee vote
        # Create a rebalance proposal for voting
        from .layer4_portfolio_allocation import RebalanceProposal, RebalanceReason
        rebalance = RebalanceProposal(
            reason=RebalanceReason.MANUAL,
            proposed_allocations={trade_proposal.get('symbol', ''): trade_proposal.get('weight', 0)}
        )
        portfolio_vote = self.portfolio_capital.vote(rebalance)
        votes.append(portfolio_vote)
        
        # Execution intelligence vote
        from .layer6_execution import ExecutionPlan
        exec_plan = ExecutionPlan(
            symbol=trade_proposal.get('symbol', ''),
            direction=trade_proposal.get('direction', ''),
            quantity=trade_proposal.get('size', 0),
            algorithm='adaptive',
            urgency='medium',
            expected_slippage=5.0,
            max_participation_rate=0.10,
            time_horizon_minutes=60
        )
        exec_vote = self.execution_intelligence.vote(exec_plan)
        votes.append(exec_vote)
        
        return votes
    
    def aggregate_votes(self, votes: List[CommitteeVote]) -> Tuple[bool, float, str]:
        """
        Aggregate committee votes into final decision.
        
        Returns:
            Tuple of (approved, confidence, rationale)
        """
        if not votes:
            return False, 0.0, "No votes received"
        
        # Check for any rejections (veto power)
        rejections = [v for v in votes if v.decision == CommitteeDecision.REJECT]
        if rejections:
            return False, 0.9, f"Rejected by: {rejections[0].rationale}"
        
        # Count approvals and conditionals
        approvals = [v for v in votes if v.decision == CommitteeDecision.APPROVE]
        conditionals = [v for v in votes if v.decision == CommitteeDecision.CONDITIONAL]
        
        # Need majority approval
        approval_rate = len(approvals) / len(votes)
        
        if approval_rate >= 0.5:
            avg_confidence = sum(v.confidence for v in approvals) / len(approvals)
            return True, avg_confidence, f"Approved by {len(approvals)}/{len(votes)} committees"
        elif len(conditionals) > 0:
            conditions = []
            for v in conditionals:
                conditions.extend(v.conditions)
            return False, 0.5, f"Conditional: {', '.join(conditions[:3])}"
        else:
            return False, 0.8, "Insufficient approval"


# =============================================================================
# MASTER ORCHESTRATOR
# =============================================================================

class AlphaAlgoInstitutional:
    """
    AlphaAlgo Institutional Master Orchestrator.
    
    A multi-disciplinary institutional quantitative research system that operates as:
    - Hedge fund research desk
    - Proprietary trading firm
    - Quantitative asset manager
    - Risk committee
    - Portfolio manager
    - Systems engineer
    
    Primary objective: Long-term capital compounding under uncertainty.
    
    Hierarchy of priorities:
    1. Survival
    2. Capital preservation
    3. Risk-adjusted returns
    4. Absolute returns
    """
    
    def __init__(self, config: SystemConfig = None):
        self.config = config or SystemConfig()
        
        # System state
        self.state = SystemState.INITIALIZING
        self.trading_mode = self.config.trading_mode
        self.started_at: Optional[datetime] = None
        
        # Initialize all layers
        self._initialize_layers()
        
        # Initialize internal committees
        self._initialize_committees()
        
        # Initialize idea vectors
        self.idea_vectors = IdeaVectorConstraints()
        
        # Initialize research loop
        self.research_loop = SelfEvolvingResearchLoop()
        self._configure_research_loop()
        
        # Trading state
        self.current_regime = MarketRegime.NORMAL
        self.risk_level = RiskLevel.LOW
        self.total_capital = self.config.initial_capital
        self.allocated_capital = 0.0
        
        # Decision history
        self.decisions: List[TradingDecision] = []
        
        # Mark as ready
        self.state = SystemState.READY
        
        logger.info("AlphaAlgoInstitutional initialized")
        logger.info(f"Trading mode: {self.trading_mode.value}")
        logger.info(f"Initial capital: ${self.total_capital:,.2f}")
    
    def _initialize_layers(self):
        """Initialize all 7 layers."""
        layer_config = {
            'initial_capital': self.config.initial_capital,
            'max_strategies': self.config.max_strategies
        }
        
        # Layer 1: Market Selection
        self.layer1_market_selection = MarketSelectionLayer(layer_config)
        
        # Layer 2: Regime Detection
        self.layer2_regime_detection = RegimeDetectionLayer(layer_config)
        
        # Layer 3: Quantitative Research
        self.layer3_research = QuantitativeResearchLayer(layer_config)
        
        # Layer 4: Portfolio Allocation
        self.layer4_allocation = PortfolioAllocationLayer(layer_config)
        
        # Layer 5: Risk Governance
        self.layer5_risk = RiskGovernanceLayer(layer_config)
        
        # Layer 6: Execution
        self.layer6_execution = ExecutionLayer(layer_config)
        
        # Layer 7: Monitoring & Evolution
        self.layer7_monitoring = MonitoringEvolutionLayer(layer_config)
        
        logger.info("All 7 layers initialized")
    
    def _initialize_committees(self):
        """Initialize internal committees."""
        self.committees = InternalCommittees(
            market_selection=self.layer1_market_selection.committee,
            regime_intelligence=self.layer2_regime_detection.regime_unit,
            research_lab=self.layer3_research.research_lab,
            validation_kill=self.layer5_risk.committee,
            portfolio_capital=self.layer4_allocation.committee,
            execution_intelligence=self.layer6_execution.execution_unit,
            evolution_audit=self.layer7_monitoring.engine
        )
        
        logger.info("All 7 internal committees initialized")
    
    def _configure_research_loop(self):
        """Configure the self-evolving research loop."""
        # Register hypothesis generator
        def generate_hypotheses(market_conditions):
            return self.layer3_research.run_research_cycle(market_conditions)
        
        self.research_loop.register_hypothesis_generator(generate_hypotheses)
        
        # Register monitor
        def monitor_model(candidate):
            # Would return actual performance
            return None
        
        self.research_loop.register_monitor(monitor_model)
    
    # =========================================================================
    # CORE OPERATIONS
    # =========================================================================
    
    async def start(self):
        """Start the system."""
        if self.state != SystemState.READY:
            logger.warning(f"Cannot start from state {self.state}")
            return
        
        self.state = SystemState.RUNNING
        self.started_at = datetime.utcnow()
        
        # Log startup
        self.layer7_monitoring.log_audit(
            event_type="system",
            component="orchestrator",
            action="started",
            details={'trading_mode': self.trading_mode.value}
        )
        
        logger.info("AlphaAlgoInstitutional started")
    
    async def stop(self):
        """Stop the system."""
        self.state = SystemState.SHUTDOWN
        self.research_loop.stop()
        
        # Log shutdown
        self.layer7_monitoring.log_audit(
            event_type="system",
            component="orchestrator",
            action="stopped"
        )
        
        logger.info("AlphaAlgoInstitutional stopped")
    
    async def pause(self):
        """Pause the system."""
        self.state = SystemState.PAUSED
        logger.info("AlphaAlgoInstitutional paused")
    
    async def resume(self):
        """Resume the system."""
        if self.state == SystemState.PAUSED:
            self.state = SystemState.RUNNING
            logger.info("AlphaAlgoInstitutional resumed")
    
    async def emergency_stop(self, reason: str):
        """Emergency stop - halt all trading immediately."""
        self.state = SystemState.EMERGENCY
        self.layer5_risk.halt_trading(reason)
        
        # Log emergency
        self.layer7_monitoring.log_audit(
            event_type="emergency",
            component="orchestrator",
            action="emergency_stop",
            details={'reason': reason}
        )
        
        logger.critical(f"EMERGENCY STOP: {reason}")
    
    # =========================================================================
    # MARKET ANALYSIS
    # =========================================================================
    
    def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze current market conditions.
        
        Args:
            market_data: Market data including prices, volumes, etc.
            
        Returns:
            Market analysis results
        """
        analysis = {}
        
        # Layer 1: Market Selection
        selected_markets = self.layer1_market_selection.select_markets(
            market_data.get('available_markets', [])
        )
        analysis['selected_markets'] = selected_markets
        
        # Layer 2: Regime Detection
        import numpy as np
        returns = market_data.get('returns', np.array([]))
        volatility = market_data.get('volatility', 0.0)
        
        regime_state = self.layer2_regime_detection.detect_regime(returns, volatility)
        self.current_regime = regime_state.primary_regime
        analysis['regime'] = {
            'primary': regime_state.primary_regime.value,
            'confidence': regime_state.confidence,
            'volatility_regime': regime_state.volatility_regime.value,
            'trend_regime': regime_state.trend_regime.value
        }
        
        # Update allocation layer with regime
        self.layer4_allocation.update_regime(self.current_regime)
        
        return analysis
    
    # =========================================================================
    # RESEARCH & MODEL MANAGEMENT
    # =========================================================================
    
    async def run_research_cycle(self, market_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a research cycle to generate and evaluate new models.
        
        Args:
            market_conditions: Current market conditions
            
        Returns:
            Research cycle results
        """
        # Generate hypotheses
        hypotheses = self.layer3_research.run_research_cycle(market_conditions)
        
        # Run research loop iteration
        iteration = await self.research_loop.run_iteration(market_conditions)
        
        return {
            'hypotheses_generated': len(hypotheses),
            'candidates_processed': iteration.candidates_processed,
            'candidates_advanced': iteration.candidates_advanced,
            'candidates_rejected': iteration.candidates_rejected,
            'pipeline_status': self.research_loop.get_pipeline_status()
        }
    
    def get_active_models(self) -> List[Dict[str, Any]]:
        """Get all active models."""
        models = []
        
        # From research layer
        for model in self.layer3_research.get_live_models():
            models.append({
                'id': model.id,
                'name': model.template.name if model.template else 'Unknown',
                'status': model.status.value,
                'family': model.template.family.value if model.template else 'Unknown'
            })
        
        # From research loop
        for model_id, model in self.research_loop.live_models.items():
            models.append({
                'id': model_id,
                'name': model.hypothesis.name if model.hypothesis else 'Unknown',
                'status': model.lifecycle_state.value,
                'generation': model.generation
            })
        
        return models
    
    # =========================================================================
    # TRADING DECISIONS
    # =========================================================================
    
    async def make_trading_decision(
        self,
        symbol: str,
        signal: Dict[str, Any],
        strategy_id: str
    ) -> TradingDecision:
        """
        Make a trading decision through the full committee process.
        
        Args:
            symbol: Trading symbol
            signal: Trading signal from strategy
            strategy_id: Strategy that generated the signal
            
        Returns:
            TradingDecision
        """
        decision = TradingDecision(
            symbol=symbol,
            direction=signal.get('direction', 'hold'),
            quantity=signal.get('quantity', 0),
            confidence=signal.get('confidence', 0),
            strategy_id=strategy_id
        )
        
        # Check if trading is allowed
        trading_allowed, reason = self.layer5_risk.is_trading_allowed()
        if not trading_allowed:
            decision.approved = False
            decision.rationale = f"Trading not allowed: {reason}"
            self.decisions.append(decision)
            return decision
        
        # Create trade proposal for committees
        trade_proposal = {
            'symbol': symbol,
            'direction': signal.get('direction', 'hold'),
            'size': signal.get('quantity', 0),
            'portfolio_value': self.total_capital,
            'current_positions': {},  # Would come from actual positions
            'weight': signal.get('quantity', 0) / self.total_capital if self.total_capital > 0 else 0
        }
        
        # Get committee votes
        votes = self.committees.vote_on_trade(trade_proposal)
        decision.committee_votes = votes
        
        # Aggregate votes
        approved, confidence, rationale = self.committees.aggregate_votes(votes)
        decision.approved = approved
        decision.confidence = confidence
        decision.rationale = rationale
        
        # If approved and auto-trading enabled, execute
        if approved and self.config.enable_auto_trading and self.trading_mode == TradingMode.LIVE:
            await self._execute_decision(decision)
        
        # Log decision
        self.layer7_monitoring.log_audit(
            event_type="trading",
            component="orchestrator",
            action="decision_made",
            details={
                'symbol': symbol,
                'direction': decision.direction,
                'approved': approved,
                'confidence': confidence
            }
        )
        
        self.decisions.append(decision)
        return decision
    
    async def _execute_decision(self, decision: TradingDecision):
        """Execute an approved trading decision."""
        # Create execution plan
        plan = self.layer6_execution.create_execution_plan(
            symbol=decision.symbol,
            direction=decision.direction,
            quantity=decision.quantity,
            urgency=ExecutionUrgency.MEDIUM,
            regime=self.current_regime
        )
        
        # Submit order
        order = self.layer6_execution.submit_order(plan)
        
        # Mark as executed (in practice, would wait for fill)
        decision.executed = True
        
        logger.info(f"Executed decision {decision.id}: {decision.direction} {decision.quantity} {decision.symbol}")
    
    # =========================================================================
    # RISK MANAGEMENT
    # =========================================================================
    
    async def run_risk_check(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run comprehensive risk check.
        
        Args:
            portfolio_data: Current portfolio data
            
        Returns:
            Risk check results
        """
        
        portfolio_value = portfolio_data.get('value', self.total_capital)
        returns = portfolio_data.get('returns', np.array([]))
        positions = portfolio_data.get('positions', {})
        leverage = portfolio_data.get('leverage', 1.0)
        
        # Update risk state
        alerts = self.layer5_risk.update_risk_state(
            portfolio_value, returns, positions, leverage
        )
        
        # Run stress tests
        stress_results = self.layer5_risk.run_stress_tests(
            portfolio_value,
            portfolio_data.get('beta', 1.0),
            leverage,
            portfolio_data.get('liquidity_buffer', portfolio_value * 0.1)
        )
        
        # Get risk metrics
        risk_metrics = self.layer5_risk.get_risk_metrics()
        
        # Update risk level
        if risk_metrics.current_drawdown > 0.15:
            self.risk_level = RiskLevel.CRITICAL
        elif risk_metrics.current_drawdown > 0.10:
            self.risk_level = RiskLevel.HIGH
        elif risk_metrics.current_drawdown > 0.05:
            self.risk_level = RiskLevel.MEDIUM
        else:
            self.risk_level = RiskLevel.LOW
        
        return {
            'risk_level': self.risk_level.value,
            'alerts': len(alerts),
            'current_drawdown': risk_metrics.current_drawdown,
            'max_drawdown': risk_metrics.max_drawdown,
            'stress_test_results': [
                {
                    'scenario': r.scenario.name,
                    'portfolio_loss': r.portfolio_loss,
                    'survival_probability': r.survival_probability
                }
                for r in stress_results
            ]
        }
    
    # =========================================================================
    # PORTFOLIO MANAGEMENT
    # =========================================================================
    
    def initialize_portfolio(self, strategy_ids: List[str]) -> Dict[str, Any]:
        """
        Initialize portfolio with strategies.
        
        Args:
            strategy_ids: List of strategy IDs to include
            
        Returns:
            Portfolio state
        """
        portfolio_state = self.layer4_allocation.initialize(
            self.total_capital, strategy_ids
        )
        
        self.allocated_capital = portfolio_state.allocated_capital
        
        return {
            'total_capital': portfolio_state.total_capital,
            'allocated_capital': portfolio_state.allocated_capital,
            'cash_reserve': portfolio_state.cash_reserve,
            'n_strategies': len(portfolio_state.strategy_allocations)
        }
    
    async def rebalance_portfolio(
        self,
        expected_returns: Dict[str, float],
        covariance_matrix: Any,
        strategy_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Rebalance portfolio.
        
        Args:
            expected_returns: Expected returns by strategy
            covariance_matrix: Covariance matrix
            strategy_ids: Strategy IDs
            
        Returns:
            Rebalance results
        """
        from .layer4_portfolio_allocation import RebalanceReason
        
        # Compute optimal allocation
        new_allocation = self.layer4_allocation.compute_allocation(
            expected_returns, covariance_matrix, strategy_ids
        )
        
        # Propose rebalance
        proposal = self.layer4_allocation.propose_rebalance(
            RebalanceReason.SCHEDULED, new_allocation
        )
        
        # Get approval
        vote = self.layer4_allocation.approve_rebalance(proposal)
        
        if vote.decision == CommitteeDecision.APPROVE:
            # Execute rebalance
            success = self.layer4_allocation.execute_rebalance(proposal)
            
            return {
                'approved': True,
                'executed': success,
                'new_allocation': new_allocation,
                'turnover': proposal.expected_turnover,
                'cost': proposal.expected_cost
            }
        else:
            return {
                'approved': False,
                'reason': vote.rationale
            }
    
    # =========================================================================
    # MONITORING & EVOLUTION
    # =========================================================================
    
    async def run_evolution_cycle(self) -> Dict[str, Any]:
        """
        Run evolution cycle to analyze and evolve strategies.
        
        Returns:
            Evolution cycle results
        """
        
        results = {
            'strategies_analyzed': 0,
            'decay_signals': 0,
            'evolution_events': 0
        }
        
        # Analyze each live model
        for model in self.layer3_research.get_live_models():
            # Get performance data (would come from actual monitoring)
            returns = np.random.normal(0.0005, 0.02, 60)  # Placeholder
            signal_accuracy = [0.55] * 60  # Placeholder
            
            analysis = self.layer7_monitoring.analyze_strategy(
                strategy_id=model.id,
                returns=returns,
                signal_accuracy=signal_accuracy,
                current_regime=self.current_regime,
                strategy_regime=MarketRegime.NORMAL,
                regime_performance={MarketRegime.NORMAL: 0.5}
            )
            
            results['strategies_analyzed'] += 1
            
            if analysis['decay_signals']:
                results['decay_signals'] += len(analysis['decay_signals'])
            
            if analysis['evolution_event']:
                results['evolution_events'] += 1
        
        return results
    
    def run_health_check(self) -> Dict[str, Any]:
        """
        Run system health check.
        
        Returns:
            Health check results
        """
        def check_layer(layer, name):
            try:
                state = layer.get_layer_state()
                return True, f"{name} operational", state
            except Exception as e:
                return False, f"{name} error: {str(e)}", {}
        
        components = {
            'layer1_market_selection': lambda: check_layer(self.layer1_market_selection, "Market Selection"),
            'layer2_regime_detection': lambda: check_layer(self.layer2_regime_detection, "Regime Detection"),
            'layer3_research': lambda: check_layer(self.layer3_research, "Research"),
            'layer4_allocation': lambda: check_layer(self.layer4_allocation, "Allocation"),
            'layer5_risk': lambda: check_layer(self.layer5_risk, "Risk"),
            'layer6_execution': lambda: check_layer(self.layer6_execution, "Execution"),
            'layer7_monitoring': lambda: check_layer(self.layer7_monitoring, "Monitoring")
        }
        
        results = self.layer7_monitoring.run_health_check(components)
        
        return {
            'overall_status': 'healthy' if all(r.status.value == 'healthy' for r in results.values()) else 'degraded',
            'components': {k: v.status.value for k, v in results.items()}
        }
    
    # =========================================================================
    # STATUS & REPORTING
    # =========================================================================
    
    def get_status(self) -> SystemStatus:
        """Get current system status."""
        risk_metrics = self.layer5_risk.get_risk_metrics()
        
        return SystemStatus(
            state=self.state,
            trading_mode=self.trading_mode,
            current_regime=self.current_regime,
            risk_level=self.risk_level,
            active_strategies=len(self.get_active_models()),
            total_capital=self.total_capital,
            allocated_capital=self.allocated_capital,
            current_drawdown=risk_metrics.current_drawdown,
            last_update=datetime.utcnow()
        )
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive system report."""
        status = self.get_status()
        
        return {
            'system': {
                'state': status.state.value,
                'trading_mode': status.trading_mode.value,
                'uptime_hours': (datetime.utcnow() - self.started_at).total_seconds() / 3600 if self.started_at else 0
            },
            'market': {
                'regime': status.current_regime.value,
                'risk_level': status.risk_level.value
            },
            'portfolio': {
                'total_capital': status.total_capital,
                'allocated_capital': status.allocated_capital,
                'current_drawdown': status.current_drawdown,
                'active_strategies': status.active_strategies
            },
            'research': {
                'pipeline_status': self.research_loop.get_pipeline_status(),
                'metrics': self.research_loop.get_metrics()
            },
            'risk': self.layer5_risk.get_layer_state(),
            'execution': self.layer6_execution.get_layer_state(),
            'monitoring': self.layer7_monitoring.get_layer_state(),
            'idea_vectors': self.idea_vectors.get_summary(),
            'audit_chain_valid': self.layer7_monitoring.verify_audit_chain()[0]
        }
    
    def explain_system(self) -> str:
        """
        Explain the system's approach to trading.
        
        Returns a comprehensive explanation covering:
        - Market selection
        - Model families
        - Uncertainty handling
        - Model evolution
        - Risk dominance
        - Long-term survivability
        """
        explanation = """
# AlphaAlgo Institutional System Explanation

## Market Selection
Markets are selected based on quantitative criteria, not narrative or convenience:
- Liquidity analysis (bid-ask spread, depth, volume)
- Inefficiency detection (autocorrelation, variance ratio, Hurst exponent)
- Structural analysis (market hours, participants, regulations)
- Data quality assessment
- Execution feasibility
- Capacity constraints

Only markets that pass all criteria are traded. Markets are continuously re-evaluated.

## Model Families
Models are inspired by multiple scientific disciplines:

**Mathematics**: Stochastic calculus (Ornstein-Uhlenbeck, jump-diffusion), optimization 
(mean-variance, risk parity, CVaR), probability theory

**Physics**: Entropy-based state detection, phase transitions, chaos theory (Lyapunov 
exponents), resonance patterns

**Biology**: Evolutionary algorithms, predator-prey dynamics (Lotka-Volterra), neural 
adaptation, ecosystem balance, swarm intelligence

**Chemistry**: Reaction kinetics, equilibrium models, catalyst detection

**Complex Systems**: Fractals, power laws, feedback loops, emergence

**AI (Conservative)**: Ensemble methods, Bayesian model averaging, anomaly detection, 
meta-learning

## Uncertainty Handling
Uncertainty is embraced, not ignored:
- All predictions come with confidence intervals
- Models output distributions, not point estimates
- Position sizing scales with uncertainty
- Multiple models vote on decisions
- Regime detection adjusts behavior
- Tail risk is explicitly modeled

## Model Evolution
Models follow a strict lifecycle:
1. Hypothesis generation from research
2. Mathematical formulation
3. Validation against historical data
4. Simulation under multiple scenarios
5. Capital approval by committee
6. Deployment with monitoring
7. Continuous performance tracking
8. Retirement or mutation when decaying

Evolution is mostly subtraction - removing what doesn't work.

## Risk Dominance
Risk has veto power over all decisions:
- Maximum drawdown limits are absolute (20%)
- Position limits prevent concentration (10% max)
- Leverage is strictly controlled (3x max)
- Correlation risk is monitored
- Stress tests run continuously
- Circuit breakers halt trading automatically

Capital preservation > opportunity capture.

## Long-Term Survivability
The system is designed for survival:
- No single trade can threaten the system
- No single model is ever fully trusted
- Diversification across strategies, assets, and time
- Continuous adaptation to changing markets
- Audit trails for all decisions
- Human oversight capability maintained

The goal is not to maximize returns, but to compound capital over the long term
while surviving all market conditions.

## Absolute Prohibitions
The system will NEVER:
- Blindly predict prices
- Stack indicators without rationale
- Depend on a single strategy
- Ignore execution costs
- Ignore regime shifts
- Chase recent performance
- Use narrative to explain losses
- Use uncontrolled leverage
- Execute unexplained trades

Violation of any prohibition triggers system failure.
"""
        return explanation


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_alphaalgo_institutional(
    trading_mode: str = "paper",
    initial_capital: float = 1000000.0,
    **kwargs
) -> AlphaAlgoInstitutional:
    """
    Factory function to create AlphaAlgo Institutional system.
    
    Args:
        trading_mode: 'disabled', 'paper', or 'live'
        initial_capital: Initial capital amount
        **kwargs: Additional configuration
        
    Returns:
        Configured AlphaAlgoInstitutional instance
    """
    config = SystemConfig(
        trading_mode=TradingMode(trading_mode),
        initial_capital=initial_capital,
        **{k: v for k, v in kwargs.items() if hasattr(SystemConfig, k)}
    )
    
    return AlphaAlgoInstitutional(config)
