"""
AlphaAlgo Institutional - Self-Evolving Research Loop
=====================================================

This module implements the Self-Evolving Research Loop that continuously:
1. Generates hypotheses
2. Constructs models
3. Validates models
4. Simulates performance
5. Approves capital allocation
6. Deploys models
7. Monitors performance
8. Retires or mutates models

The loop operates autonomously but with human oversight capability.

Key principles:
- Evolution is mostly subtraction, not addition
- All models decay
- Continuous improvement is mandatory
- No model is ever trusted completely
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import uuid
import asyncio

from .core_types import (
    ModelHypothesis, ModelStatus, ModelPerformance, MarketRegime,
    CommitteeVote, CommitteeDecision, SystemConstants
)

logger = logging.getLogger(__name__)


# =============================================================================
# RESEARCH LOOP TYPES
# =============================================================================

class LoopStage(Enum):
    """Stages of the research loop."""
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    MODEL_CONSTRUCTION = "model_construction"
    VALIDATION = "validation"
    SIMULATION = "simulation"
    CAPITAL_APPROVAL = "capital_approval"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    RETIREMENT_MUTATION = "retirement_mutation"


class ModelLifecycleState(Enum):
    """Model lifecycle states."""
    IDEA = "idea"
    HYPOTHESIS = "hypothesis"
    DEVELOPMENT = "development"
    VALIDATION = "validation"
    SIMULATION = "simulation"
    APPROVED = "approved"
    LIVE = "live"
    MONITORING = "monitoring"
    DEGRADED = "degraded"
    PAUSED = "paused"
    RETIRED = "retired"
    MUTATED = "mutated"


@dataclass
class ResearchCandidate:
    """A candidate in the research pipeline."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    hypothesis: Optional[ModelHypothesis] = None
    stage: LoopStage = LoopStage.HYPOTHESIS_GENERATION
    lifecycle_state: ModelLifecycleState = ModelLifecycleState.IDEA
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    simulation_results: Dict[str, Any] = field(default_factory=dict)
    approval_votes: List[CommitteeVote] = field(default_factory=list)
    performance: Optional[ModelPerformance] = None
    parent_id: Optional[str] = None  # For mutations
    generation: int = 1


@dataclass
class LoopIteration:
    """A single iteration of the research loop."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    stage: LoopStage = LoopStage.HYPOTHESIS_GENERATION
    candidates_processed: int = 0
    candidates_advanced: int = 0
    candidates_rejected: int = 0
    candidates_retired: int = 0
    notes: str = ""


@dataclass
class LoopMetrics:
    """Metrics for the research loop."""
    total_iterations: int = 0
    total_hypotheses_generated: int = 0
    total_models_validated: int = 0
    total_models_deployed: int = 0
    total_models_retired: int = 0
    avg_time_to_deployment_days: float = 0.0
    survival_rate: float = 0.0
    mutation_success_rate: float = 0.0


# =============================================================================
# VALIDATION ENGINE
# =============================================================================

class ValidationEngine:
    """Validates model candidates."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Validation thresholds
        self.min_sharpe = self.config.get('min_sharpe', 0.5)
        self.max_drawdown = self.config.get('max_drawdown', 0.15)
        self.min_win_rate = self.config.get('min_win_rate', 0.45)
        self.min_profit_factor = self.config.get('min_profit_factor', 1.2)
        self.min_sample_size = self.config.get('min_sample_size', 100)
    
    def validate(self, candidate: ResearchCandidate, historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a research candidate.
        
        Args:
            candidate: Candidate to validate
            historical_data: Historical data for validation
            
        Returns:
            Validation results
        """
        results = {
            'passed': False,
            'checks': {},
            'score': 0.0,
            'issues': []
        }
        
        # Check hypothesis quality
        if candidate.hypothesis:
            hyp = candidate.hypothesis
            
            # Expected edge check
            if hyp.expected_edge >= self.min_sharpe:
                results['checks']['expected_edge'] = True
            else:
                results['checks']['expected_edge'] = False
                results['issues'].append(f"Expected edge {hyp.expected_edge:.2f} below minimum {self.min_sharpe}")
            
            # Failure mode awareness
            if len(hyp.failure_modes) >= 2:
                results['checks']['failure_modes'] = True
            else:
                results['checks']['failure_modes'] = False
                results['issues'].append("Insufficient failure mode analysis")
            
            # Data requirements
            if hyp.data_requirements:
                results['checks']['data_requirements'] = True
            else:
                results['checks']['data_requirements'] = False
                results['issues'].append("No data requirements specified")
            
            # Mathematical basis
            if hyp.mathematical_basis:
                results['checks']['mathematical_basis'] = True
            else:
                results['checks']['mathematical_basis'] = False
                results['issues'].append("No mathematical basis specified")
        
        # Calculate overall score
        checks_passed = sum(1 for v in results['checks'].values() if v)
        total_checks = len(results['checks'])
        results['score'] = checks_passed / max(1, total_checks)
        
        # Determine if passed
        results['passed'] = results['score'] >= 0.7 and len(results['issues']) <= 1
        
        return results


# =============================================================================
# SIMULATION ENGINE
# =============================================================================

class SimulationEngine:
    """Simulates model performance."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Simulation parameters
        self.n_simulations = self.config.get('n_simulations', 1000)
        self.simulation_periods = self.config.get('simulation_periods', 252)
    
    def simulate(
        self,
        candidate: ResearchCandidate,
        market_scenarios: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Simulate candidate performance.
        
        Args:
            candidate: Candidate to simulate
            market_scenarios: Market scenarios to test
            
        Returns:
            Simulation results
        """
        import numpy as np
        
        results = {
            'passed': False,
            'metrics': {},
            'scenario_results': [],
            'confidence': 0.0
        }
        
        if not candidate.hypothesis:
            results['metrics']['error'] = "No hypothesis"
            return results
        
        # Simulate returns based on expected edge
        expected_sharpe = candidate.hypothesis.expected_edge
        expected_vol = 0.15  # Assume 15% volatility
        expected_return = expected_sharpe * expected_vol
        
        # Monte Carlo simulation
        simulated_returns = []
        simulated_drawdowns = []
        
        for _ in range(self.n_simulations):
            # Generate random returns
            returns = np.random.normal(
                expected_return / 252,
                expected_vol / np.sqrt(252),
                self.simulation_periods
            )
            
            # Calculate cumulative return
            cum_return = np.prod(1 + returns) - 1
            simulated_returns.append(cum_return)
            
            # Calculate max drawdown
            cum_wealth = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cum_wealth)
            drawdowns = (running_max - cum_wealth) / running_max
            max_dd = np.max(drawdowns)
            simulated_drawdowns.append(max_dd)
        
        # Calculate metrics
        results['metrics'] = {
            'mean_return': np.mean(simulated_returns),
            'median_return': np.median(simulated_returns),
            'std_return': np.std(simulated_returns),
            'prob_positive': np.mean(np.array(simulated_returns) > 0),
            'mean_max_drawdown': np.mean(simulated_drawdowns),
            'worst_drawdown': np.max(simulated_drawdowns),
            'var_95': np.percentile(simulated_returns, 5),
            'cvar_95': np.mean([r for r in simulated_returns if r <= np.percentile(simulated_returns, 5)])
        }
        
        # Test against scenarios
        for scenario in market_scenarios:
            scenario_result = self._simulate_scenario(candidate, scenario)
            results['scenario_results'].append(scenario_result)
        
        # Determine if passed
        results['passed'] = (
            results['metrics']['prob_positive'] > 0.6 and
            results['metrics']['mean_max_drawdown'] < 0.20 and
            results['metrics']['mean_return'] > 0
        )
        
        results['confidence'] = results['metrics']['prob_positive']
        
        return results
    
    def _simulate_scenario(
        self,
        candidate: ResearchCandidate,
        scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate a specific scenario."""
        
        scenario_name = scenario.get('name', 'Unknown')
        shock = scenario.get('shock', 0.0)
        
        # Adjust expected return for scenario
        base_return = candidate.hypothesis.expected_edge * 0.15 if candidate.hypothesis else 0
        scenario_return = base_return + shock
        
        return {
            'scenario': scenario_name,
            'expected_return': scenario_return,
            'survives': scenario_return > -0.20
        }


# =============================================================================
# CAPITAL APPROVAL ENGINE
# =============================================================================

class CapitalApprovalEngine:
    """Manages capital approval for models."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Approval thresholds
        self.min_validation_score = self.config.get('min_validation_score', 0.7)
        self.min_simulation_confidence = self.config.get('min_simulation_confidence', 0.6)
        self.max_initial_allocation = self.config.get('max_initial_allocation', 0.05)
    
    def request_approval(
        self,
        candidate: ResearchCandidate,
        requested_allocation: float
    ) -> CommitteeVote:
        """
        Request capital approval for a candidate.
        
        Args:
            candidate: Candidate requesting approval
            requested_allocation: Requested allocation percentage
            
        Returns:
            CommitteeVote
        """
        issues = []
        
        # Check validation results
        val_score = candidate.validation_results.get('score', 0)
        if val_score < self.min_validation_score:
            issues.append(f"Validation score {val_score:.2f} below minimum {self.min_validation_score}")
        
        # Check simulation results
        sim_confidence = candidate.simulation_results.get('confidence', 0)
        if sim_confidence < self.min_simulation_confidence:
            issues.append(f"Simulation confidence {sim_confidence:.2f} below minimum {self.min_simulation_confidence}")
        
        # Check allocation request
        if requested_allocation > self.max_initial_allocation:
            issues.append(f"Requested allocation {requested_allocation:.2%} exceeds maximum {self.max_initial_allocation:.2%}")
        
        # Make decision
        if not issues:
            decision = CommitteeDecision.APPROVE
            confidence = min(val_score, sim_confidence)
            rationale = f"Approved for {requested_allocation:.2%} allocation"
        elif len(issues) == 1:
            decision = CommitteeDecision.CONDITIONAL
            confidence = 0.5
            rationale = f"Conditional approval: {issues[0]}"
        else:
            decision = CommitteeDecision.REJECT
            confidence = 0.8
            rationale = f"Rejected: {', '.join(issues)}"
        
        return CommitteeVote(
            committee=None,  # Would be set by committee
            decision=decision,
            confidence=confidence,
            rationale=rationale,
            conditions=issues if decision == CommitteeDecision.CONDITIONAL else []
        )


# =============================================================================
# RETIREMENT ENGINE
# =============================================================================

class RetirementEngine:
    """Manages model retirement and mutation."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Retirement thresholds
        self.min_sharpe_for_survival = self.config.get('min_sharpe_for_survival', 0.3)
        self.max_drawdown_for_survival = self.config.get('max_drawdown_for_survival', 0.20)
        self.decay_threshold = self.config.get('decay_threshold', 0.5)
    
    def evaluate_for_retirement(
        self,
        candidate: ResearchCandidate,
        recent_performance: Dict[str, float]
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Evaluate if a candidate should be retired.
        
        Args:
            candidate: Candidate to evaluate
            recent_performance: Recent performance metrics
            
        Returns:
            Tuple of (should_retire, reason, mutation_suggestion)
        """
        sharpe = recent_performance.get('sharpe', 0)
        drawdown = recent_performance.get('max_drawdown', 0)
        decay_score = recent_performance.get('decay_score', 0)
        
        # Check survival criteria
        if drawdown > self.max_drawdown_for_survival:
            return True, f"Drawdown {drawdown:.2%} exceeds survival limit", None
        
        if sharpe < self.min_sharpe_for_survival:
            # Consider mutation instead of retirement
            if decay_score < self.decay_threshold:
                mutation = self._suggest_mutation(candidate, recent_performance)
                return False, "Consider mutation", mutation
            return True, f"Sharpe {sharpe:.2f} below survival threshold", None
        
        if decay_score > self.decay_threshold:
            mutation = self._suggest_mutation(candidate, recent_performance)
            return False, "Performance decaying, mutation suggested", mutation
        
        return False, "Meets survival criteria", None
    
    def _suggest_mutation(
        self,
        candidate: ResearchCandidate,
        performance: Dict[str, float]
    ) -> Dict[str, Any]:
        """Suggest a mutation for the candidate."""
        return {
            'type': 'parameter_adjustment',
            'reason': 'Performance decay detected',
            'suggestions': [
                'Reduce position size',
                'Tighten stop loss',
                'Adjust regime filter',
                'Recalibrate parameters'
            ],
            'priority': 'high' if performance.get('decay_score', 0) > 0.7 else 'medium'
        }


# =============================================================================
# SELF-EVOLVING RESEARCH LOOP
# =============================================================================

class SelfEvolvingResearchLoop:
    """
    The Self-Evolving Research Loop.
    
    Continuously:
    1. Generates hypotheses
    2. Constructs models
    3. Validates models
    4. Simulates performance
    5. Approves capital allocation
    6. Deploys models
    7. Monitors performance
    8. Retires or mutates models
    
    Key principles:
    - Evolution is mostly subtraction
    - All models decay
    - Continuous improvement
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize engines
        self.validation_engine = ValidationEngine(self.config)
        self.simulation_engine = SimulationEngine(self.config)
        self.approval_engine = CapitalApprovalEngine(self.config)
        self.retirement_engine = RetirementEngine(self.config)
        
        # Pipeline state
        self.candidates: Dict[str, ResearchCandidate] = {}
        self.live_models: Dict[str, ResearchCandidate] = {}
        self.retired_models: List[str] = []
        
        # Loop state
        self.iterations: List[LoopIteration] = []
        self.metrics = LoopMetrics()
        self.is_running = False
        self.last_iteration: Optional[datetime] = None
        
        # Callbacks
        self.hypothesis_generator: Optional[Callable] = None
        self.model_constructor: Optional[Callable] = None
        self.deployer: Optional[Callable] = None
        self.monitor: Optional[Callable] = None
        
        logger.info("SelfEvolvingResearchLoop initialized")
    
    def register_hypothesis_generator(self, generator: Callable):
        """Register hypothesis generation function."""
        self.hypothesis_generator = generator
    
    def register_model_constructor(self, constructor: Callable):
        """Register model construction function."""
        self.model_constructor = constructor
    
    def register_deployer(self, deployer: Callable):
        """Register deployment function."""
        self.deployer = deployer
    
    def register_monitor(self, monitor: Callable):
        """Register monitoring function."""
        self.monitor = monitor
    
    async def run_iteration(self, market_conditions: Dict[str, Any]) -> LoopIteration:
        """
        Run a single iteration of the research loop.
        
        Args:
            market_conditions: Current market conditions
            
        Returns:
            LoopIteration results
        """
        iteration = LoopIteration()
        
        try:
            # Stage 1: Hypothesis Generation
            await self._stage_hypothesis_generation(iteration, market_conditions)
            
            # Stage 2: Model Construction
            await self._stage_model_construction(iteration)
            
            # Stage 3: Validation
            await self._stage_validation(iteration, market_conditions)
            
            # Stage 4: Simulation
            await self._stage_simulation(iteration, market_conditions)
            
            # Stage 5: Capital Approval
            await self._stage_capital_approval(iteration)
            
            # Stage 6: Deployment
            await self._stage_deployment(iteration)
            
            # Stage 7: Monitoring
            await self._stage_monitoring(iteration)
            
            # Stage 8: Retirement/Mutation
            await self._stage_retirement_mutation(iteration)
            
            iteration.completed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error in research loop iteration: {e}")
            iteration.notes = f"Error: {str(e)}"
        
        self.iterations.append(iteration)
        self.metrics.total_iterations += 1
        self.last_iteration = datetime.utcnow()
        
        return iteration
    
    async def _stage_hypothesis_generation(
        self,
        iteration: LoopIteration,
        market_conditions: Dict[str, Any]
    ):
        """Stage 1: Generate hypotheses."""
        iteration.stage = LoopStage.HYPOTHESIS_GENERATION
        
        if self.hypothesis_generator:
            hypotheses = self.hypothesis_generator(market_conditions)
            
            for hypothesis in hypotheses:
                candidate = ResearchCandidate(
                    hypothesis=hypothesis,
                    stage=LoopStage.HYPOTHESIS_GENERATION,
                    lifecycle_state=ModelLifecycleState.HYPOTHESIS
                )
                self.candidates[candidate.id] = candidate
                iteration.candidates_processed += 1
                self.metrics.total_hypotheses_generated += 1
    
    async def _stage_model_construction(self, iteration: LoopIteration):
        """Stage 2: Construct models from hypotheses."""
        iteration.stage = LoopStage.MODEL_CONSTRUCTION
        
        hypothesis_candidates = [
            c for c in self.candidates.values()
            if c.lifecycle_state == ModelLifecycleState.HYPOTHESIS
        ]
        
        for candidate in hypothesis_candidates:
            if self.model_constructor:
                # Construct model
                success = self.model_constructor(candidate)
                if success:
                    candidate.lifecycle_state = ModelLifecycleState.DEVELOPMENT
                    candidate.stage = LoopStage.VALIDATION
                    iteration.candidates_advanced += 1
                else:
                    iteration.candidates_rejected += 1
            else:
                # Default: advance to validation
                candidate.lifecycle_state = ModelLifecycleState.DEVELOPMENT
                candidate.stage = LoopStage.VALIDATION
                iteration.candidates_advanced += 1
    
    async def _stage_validation(
        self,
        iteration: LoopIteration,
        market_conditions: Dict[str, Any]
    ):
        """Stage 3: Validate models."""
        iteration.stage = LoopStage.VALIDATION
        
        development_candidates = [
            c for c in self.candidates.values()
            if c.lifecycle_state == ModelLifecycleState.DEVELOPMENT
        ]
        
        for candidate in development_candidates:
            results = self.validation_engine.validate(candidate, market_conditions)
            candidate.validation_results = results
            
            if results['passed']:
                candidate.lifecycle_state = ModelLifecycleState.VALIDATION
                candidate.stage = LoopStage.SIMULATION
                iteration.candidates_advanced += 1
                self.metrics.total_models_validated += 1
            else:
                candidate.lifecycle_state = ModelLifecycleState.RETIRED
                iteration.candidates_rejected += 1
    
    async def _stage_simulation(
        self,
        iteration: LoopIteration,
        market_conditions: Dict[str, Any]
    ):
        """Stage 4: Simulate model performance."""
        iteration.stage = LoopStage.SIMULATION
        
        # Define market scenarios
        scenarios = [
            {'name': 'Normal', 'shock': 0.0},
            {'name': 'Bull', 'shock': 0.10},
            {'name': 'Bear', 'shock': -0.15},
            {'name': 'Crisis', 'shock': -0.30},
            {'name': 'Volatility Spike', 'shock': -0.05}
        ]
        
        validation_candidates = [
            c for c in self.candidates.values()
            if c.lifecycle_state == ModelLifecycleState.VALIDATION
        ]
        
        for candidate in validation_candidates:
            results = self.simulation_engine.simulate(candidate, scenarios)
            candidate.simulation_results = results
            
            if results['passed']:
                candidate.lifecycle_state = ModelLifecycleState.SIMULATION
                candidate.stage = LoopStage.CAPITAL_APPROVAL
                iteration.candidates_advanced += 1
            else:
                candidate.lifecycle_state = ModelLifecycleState.RETIRED
                iteration.candidates_rejected += 1
    
    async def _stage_capital_approval(self, iteration: LoopIteration):
        """Stage 5: Request capital approval."""
        iteration.stage = LoopStage.CAPITAL_APPROVAL
        
        simulation_candidates = [
            c for c in self.candidates.values()
            if c.lifecycle_state == ModelLifecycleState.SIMULATION
        ]
        
        for candidate in simulation_candidates:
            # Request initial allocation
            vote = self.approval_engine.request_approval(candidate, 0.02)
            candidate.approval_votes.append(vote)
            
            if vote.decision == CommitteeDecision.APPROVE:
                candidate.lifecycle_state = ModelLifecycleState.APPROVED
                candidate.stage = LoopStage.DEPLOYMENT
                iteration.candidates_advanced += 1
            elif vote.decision == CommitteeDecision.CONDITIONAL:
                # Keep in simulation for now
                pass
            else:
                candidate.lifecycle_state = ModelLifecycleState.RETIRED
                iteration.candidates_rejected += 1
    
    async def _stage_deployment(self, iteration: LoopIteration):
        """Stage 6: Deploy approved models."""
        iteration.stage = LoopStage.DEPLOYMENT
        
        approved_candidates = [
            c for c in self.candidates.values()
            if c.lifecycle_state == ModelLifecycleState.APPROVED
        ]
        
        for candidate in approved_candidates:
            if self.deployer:
                success = self.deployer(candidate)
                if success:
                    candidate.lifecycle_state = ModelLifecycleState.LIVE
                    candidate.stage = LoopStage.MONITORING
                    self.live_models[candidate.id] = candidate
                    del self.candidates[candidate.id]
                    iteration.candidates_advanced += 1
                    self.metrics.total_models_deployed += 1
            else:
                # Default: mark as live
                candidate.lifecycle_state = ModelLifecycleState.LIVE
                candidate.stage = LoopStage.MONITORING
                self.live_models[candidate.id] = candidate
                del self.candidates[candidate.id]
                iteration.candidates_advanced += 1
                self.metrics.total_models_deployed += 1
    
    async def _stage_monitoring(self, iteration: LoopIteration):
        """Stage 7: Monitor live models."""
        iteration.stage = LoopStage.MONITORING
        
        for model_id, model in list(self.live_models.items()):
            if self.monitor:
                performance = self.monitor(model)
                model.performance = performance
            
            model.last_updated = datetime.utcnow()
    
    async def _stage_retirement_mutation(self, iteration: LoopIteration):
        """Stage 8: Retire or mutate underperforming models."""
        iteration.stage = LoopStage.RETIREMENT_MUTATION
        
        for model_id, model in list(self.live_models.items()):
            # Get recent performance
            recent_perf = {
                'sharpe': 0.5,  # Would come from actual monitoring
                'max_drawdown': 0.10,
                'decay_score': 0.3
            }
            
            should_retire, reason, mutation = self.retirement_engine.evaluate_for_retirement(
                model, recent_perf
            )
            
            if should_retire:
                model.lifecycle_state = ModelLifecycleState.RETIRED
                self.retired_models.append(model_id)
                del self.live_models[model_id]
                iteration.candidates_retired += 1
                self.metrics.total_models_retired += 1
                logger.info(f"Retired model {model_id}: {reason}")
            
            elif mutation:
                # Create mutated version
                mutated = ResearchCandidate(
                    hypothesis=model.hypothesis,
                    stage=LoopStage.VALIDATION,
                    lifecycle_state=ModelLifecycleState.DEVELOPMENT,
                    parent_id=model_id,
                    generation=model.generation + 1
                )
                self.candidates[mutated.id] = mutated
                logger.info(f"Created mutation {mutated.id} from {model_id}")
    
    async def run_continuous(
        self,
        market_conditions_provider: Callable[[], Dict[str, Any]],
        interval_seconds: int = 3600
    ):
        """
        Run the research loop continuously.
        
        Args:
            market_conditions_provider: Function that returns current market conditions
            interval_seconds: Seconds between iterations
        """
        self.is_running = True
        
        while self.is_running:
            try:
                market_conditions = market_conditions_provider()
                await self.run_iteration(market_conditions)
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in continuous loop: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    def stop(self):
        """Stop the continuous loop."""
        self.is_running = False
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status."""
        stage_counts = {}
        for candidate in self.candidates.values():
            stage = candidate.lifecycle_state.value
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
        
        return {
            'candidates_in_pipeline': len(self.candidates),
            'live_models': len(self.live_models),
            'retired_models': len(self.retired_models),
            'stage_distribution': stage_counts,
            'last_iteration': self.last_iteration.isoformat() if self.last_iteration else None,
            'is_running': self.is_running
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get loop metrics."""
        # Calculate survival rate
        total_processed = self.metrics.total_hypotheses_generated
        if total_processed > 0:
            self.metrics.survival_rate = self.metrics.total_models_deployed / total_processed
        
        return {
            'total_iterations': self.metrics.total_iterations,
            'total_hypotheses_generated': self.metrics.total_hypotheses_generated,
            'total_models_validated': self.metrics.total_models_validated,
            'total_models_deployed': self.metrics.total_models_deployed,
            'total_models_retired': self.metrics.total_models_retired,
            'survival_rate': self.metrics.survival_rate,
            'current_live_models': len(self.live_models)
        }


