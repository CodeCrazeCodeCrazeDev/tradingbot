"""
Intelligent & Social Delegation - Task Decomposition Engine
Based on Google DeepMind "Intelligent AI Delegation" (2026, arXiv:2602.11865)

Section 4.1: Task Decomposition
- Contract-first decomposition (verifiability constraint)
- Hybrid human-AI market awareness
- Iterative proposal generation
- Parallel vs sequential execution planning
- Recursive decomposition until verifiable granularity

RISK MITIGATIONS IMPLEMENTED:
- Decomposition Explosion: Max depth limit, complexity floor bypass
- Verification Gap: Contract-first — tasks decomposed until verifiable
- Latency Asymmetry: Human vs AI speed-aware scheduling
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .delegation_types import (
    AgentProfile,
    AgentSpecialization,
    AutonomyLevel,
    DelegationTask,
    DelegationGranularity,
    TaskCharacteristics,
    TaskComplexity,
    TaskCriticality,
    TaskReversibility,
    TaskUncertainty,
    TaskVerifiability,
    TradingTaskType,
    get_task_template,
)

logger = logging.getLogger(__name__)


# ============================================================================
# DECOMPOSITION STRATEGIES
# ============================================================================

@dataclass
class DecompositionProposal:
    """A proposed decomposition of a complex task into sub-tasks."""
    proposal_id: str = ""
    parent_task: Optional[DelegationTask] = None
    sub_tasks: List[DelegationTask] = field(default_factory=list)
    execution_order: str = "sequential"  # sequential, parallel, dag
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    estimated_total_duration: float = 0.0
    estimated_total_cost: float = 0.0
    estimated_success_rate: float = 0.0
    requires_human_nodes: bool = False
    human_node_count: int = 0
    max_depth: int = 0
    score: float = 0.0
    rationale: str = ""

    @property
    def task_count(self) -> int:
        return len(self.sub_tasks)


@dataclass
class DecompositionConfig:
    """Configuration for the decomposition engine."""
    max_depth: int = 5
    max_sub_tasks: int = 20
    min_verifiability: TaskVerifiability = TaskVerifiability.MODERATELY_VERIFIABLE
    complexity_floor: TaskComplexity = TaskComplexity.LOW
    prefer_parallel: bool = True
    human_latency_factor: float = 60.0  # humans are ~60x slower than AI
    max_proposals: int = 3
    enable_recursive_decomposition: bool = True


class TaskDecompositionEngine:
    """
    Decomposes complex trading tasks into manageable, verifiable sub-tasks.

    Implements Section 4.1 of the paper:
    - Contract-first decomposition: tasks must be verifiable
    - Hybrid human-AI awareness: accounts for speed/cost asymmetries
    - Iterative proposal generation: multiple decomposition strategies
    - Recursive decomposition: until verifiable granularity reached

    RISK MITIGATIONS:
    - Decomposition Explosion (Section 4.1): max_depth + complexity_floor
    - Verification Gap (Section 4.1): contract-first constraint
    - Latency Asymmetry (Section 4.1): human_latency_factor weighting
    """

    def __init__(self, config: Optional[DecompositionConfig] = None):
        self.config = config or DecompositionConfig()
        self._decomposition_rules: Dict[TradingTaskType, Callable] = {}
        self._register_trading_decompositions()
        self._decomposition_count = 0
        logger.info("TaskDecompositionEngine initialized (max_depth=%d)", self.config.max_depth)

    def _register_trading_decompositions(self):
        """Register domain-specific decomposition rules for trading tasks."""
        self._decomposition_rules = {
            TradingTaskType.GENERATE_SIGNAL: self._decompose_signal_generation,
            TradingTaskType.EXECUTE_ORDER: self._decompose_order_execution,
            TradingTaskType.OPTIMIZE_PORTFOLIO: self._decompose_portfolio_optimization,
            TradingTaskType.REBALANCE_PORTFOLIO: self._decompose_rebalance,
            TradingTaskType.EMERGENCY_EXIT: self._decompose_emergency_exit,
            TradingTaskType.HEDGE_POSITION: self._decompose_hedge,
        }

    def decompose(
        self,
        task: DelegationTask,
        available_agents: Optional[List[AgentProfile]] = None,
        depth: int = 0,
    ) -> DecompositionProposal:
        """
        Decompose a task into sub-tasks.

        Section 4.1 Contract-First: If a sub-task's output is too subjective
        or complex to verify, recursively decompose further until verifiable.

        Section 4.3 Complexity Floor: Tasks below the floor bypass delegation.
        """
        self._decomposition_count += 1

        # RISK MITIGATION: Complexity floor — trivial tasks skip decomposition
        if task.characteristics.bypass_delegation:
            logger.debug("Task %s bypasses delegation (complexity floor)", task.task_id)
            return DecompositionProposal(
                proposal_id=f"bypass_{task.task_id}",
                parent_task=task,
                sub_tasks=[task],
                execution_order="atomic",
                estimated_success_rate=0.95,
                score=1.0,
                rationale="Task below complexity floor — direct execution",
            )

        # RISK MITIGATION: Decomposition explosion — enforce max depth
        if depth >= self.config.max_depth:
            logger.warning(
                "Max decomposition depth %d reached for task %s",
                self.config.max_depth, task.task_id,
            )
            return DecompositionProposal(
                proposal_id=f"maxdepth_{task.task_id}",
                parent_task=task,
                sub_tasks=[task],
                execution_order="atomic",
                score=0.5,
                rationale="Max decomposition depth reached — executing as-is",
            )

        # Generate multiple proposals (Section 4.1: iterative proposal generation)
        proposals = self._generate_proposals(task, available_agents, depth)

        if not proposals:
            return DecompositionProposal(
                proposal_id=f"atomic_{task.task_id}",
                parent_task=task,
                sub_tasks=[task],
                execution_order="atomic",
                score=0.7,
                rationale="No decomposition applicable — atomic execution",
            )

        # Score and select best proposal
        best = max(proposals, key=lambda p: p.score)

        # CONTRACT-FIRST: Recursively decompose any sub-task that isn't verifiable enough
        if self.config.enable_recursive_decomposition:
            best = self._enforce_verifiability(best, available_agents, depth)

        logger.info(
            "Decomposed task %s into %d sub-tasks (depth=%d, strategy=%s)",
            task.task_id, best.task_count, depth, best.execution_order,
        )
        return best

    def _generate_proposals(
        self,
        task: DelegationTask,
        available_agents: Optional[List[AgentProfile]],
        depth: int,
    ) -> List[DecompositionProposal]:
        """Generate multiple decomposition proposals for a task."""
        proposals = []

        # Strategy 1: Domain-specific decomposition
        if task.task_type in self._decomposition_rules:
            domain_proposal = self._decomposition_rules[task.task_type](task, depth)
            if domain_proposal:
                domain_proposal.score = self._score_proposal(domain_proposal, available_agents)
                proposals.append(domain_proposal)

        # Strategy 2: Parallel fan-out (for independent sub-analyses)
        if task.characteristics.complexity >= TaskComplexity.HIGH:
            parallel_proposal = self._parallel_decomposition(task, depth)
            if parallel_proposal:
                parallel_proposal.score = self._score_proposal(parallel_proposal, available_agents)
                proposals.append(parallel_proposal)

        # Strategy 3: Sequential pipeline (for dependent steps)
        if task.characteristics.criticality >= TaskCriticality.HIGH:
            sequential_proposal = self._sequential_decomposition(task, depth)
            if sequential_proposal:
                sequential_proposal.score = self._score_proposal(sequential_proposal, available_agents)
                proposals.append(sequential_proposal)

        return proposals[:self.config.max_proposals]

    def _score_proposal(
        self,
        proposal: DecompositionProposal,
        available_agents: Optional[List[AgentProfile]],
    ) -> float:
        """Score a decomposition proposal based on multiple objectives (Section 4.3)."""
        score = 0.5

        # Verifiability bonus: more verifiable sub-tasks = better
        avg_verifiability = 0.0
        for st in proposal.sub_tasks:
            avg_verifiability += (5 - st.characteristics.verifiability.value) / 4.0
        if proposal.sub_tasks:
            avg_verifiability /= len(proposal.sub_tasks)
        score += avg_verifiability * 0.3

        # Parallelism bonus
        if proposal.execution_order == "parallel" and self.config.prefer_parallel:
            score += 0.1

        # Agent availability bonus
        if available_agents:
            matched = 0
            for st in proposal.sub_tasks:
                for agent in available_agents:
                    if agent.supports_task(st.task_type) and not agent.is_overloaded:
                        matched += 1
                        break
            if proposal.sub_tasks:
                score += (matched / len(proposal.sub_tasks)) * 0.2

        # Penalty for too many sub-tasks (overhead)
        if len(proposal.sub_tasks) > 10:
            score -= 0.1
        if len(proposal.sub_tasks) > self.config.max_sub_tasks:
            score -= 0.3

        # Penalty for human nodes (latency)
        if proposal.requires_human_nodes:
            score -= 0.05 * proposal.human_node_count

        return max(0.0, min(1.0, score))

    def _enforce_verifiability(
        self,
        proposal: DecompositionProposal,
        available_agents: Optional[List[AgentProfile]],
        depth: int,
    ) -> DecompositionProposal:
        """
        CONTRACT-FIRST DECOMPOSITION (Section 4.1):
        Recursively decompose sub-tasks that don't meet verifiability threshold.
        """
        refined_sub_tasks = []
        for st in proposal.sub_tasks:
            if st.characteristics.verifiability > self.config.min_verifiability:
                # Not verifiable enough — decompose further
                sub_proposal = self.decompose(st, available_agents, depth + 1)
                refined_sub_tasks.extend(sub_proposal.sub_tasks)
            else:
                refined_sub_tasks.append(st)

        proposal.sub_tasks = refined_sub_tasks
        return proposal

    # ========================================================================
    # DOMAIN-SPECIFIC DECOMPOSITIONS (Trading)
    # ========================================================================

    def _decompose_signal_generation(
        self, task: DelegationTask, depth: int
    ) -> DecompositionProposal:
        """Decompose signal generation into analysis → validation → sizing pipeline."""
        symbol = task.input_data.get('symbol', 'UNKNOWN')

        sub_tasks = [
            DelegationTask(
                task_type=TradingTaskType.VALIDATE_DATA,
                description=f"Validate market data for {symbol}",
                characteristics=get_task_template(TradingTaskType.VALIDATE_DATA),
                input_data={'symbol': symbol},
                parent_task_id=task.task_id,
            ),
            DelegationTask(
                task_type=TradingTaskType.DETECT_REGIME,
                description=f"Detect market regime for {symbol}",
                characteristics=get_task_template(TradingTaskType.DETECT_REGIME),
                input_data={'symbol': symbol},
                parent_task_id=task.task_id,
            ),
            DelegationTask(
                task_type=TradingTaskType.ANALYZE_MARKET,
                description=f"Technical analysis for {symbol}",
                characteristics=get_task_template(TradingTaskType.ANALYZE_MARKET),
                input_data={'symbol': symbol, 'analysis_type': 'technical'},
                parent_task_id=task.task_id,
            ),
            DelegationTask(
                task_type=TradingTaskType.ANALYZE_MARKET,
                description=f"Fundamental analysis for {symbol}",
                characteristics=get_task_template(TradingTaskType.ANALYZE_MARKET),
                input_data={'symbol': symbol, 'analysis_type': 'fundamental'},
                parent_task_id=task.task_id,
            ),
            DelegationTask(
                task_type=TradingTaskType.PROCESS_NEWS,
                description=f"Process news sentiment for {symbol}",
                characteristics=get_task_template(TradingTaskType.ANALYZE_MARKET),
                input_data={'symbol': symbol},
                parent_task_id=task.task_id,
            ),
            DelegationTask(
                task_type=TradingTaskType.VALIDATE_SIGNAL,
                description=f"Validate generated signal for {symbol}",
                characteristics=TaskCharacteristics(
                    complexity=TaskComplexity.MODERATE,
                    criticality=TaskCriticality.HIGH,
                    verifiability=TaskVerifiability.EASILY_VERIFIABLE,
                    reversibility=TaskReversibility.FULLY_REVERSIBLE,
                ),
                input_data={'symbol': symbol},
                parent_task_id=task.task_id,
            ),
            DelegationTask(
                task_type=TradingTaskType.ASSESS_RISK,
                description=f"Risk assessment for signal on {symbol}",
                characteristics=get_task_template(TradingTaskType.ASSESS_RISK),
                input_data={'symbol': symbol},
                parent_task_id=task.task_id,
            ),
            DelegationTask(
                task_type=TradingTaskType.CALCULATE_POSITION_SIZE,
                description=f"Calculate position size for {symbol}",
                characteristics=get_task_template(TradingTaskType.CALCULATE_POSITION_SIZE),
                input_data={'symbol': symbol},
                parent_task_id=task.task_id,
            ),
        ]

        # Build dependency graph: validate → [regime, tech, fund, news] → validate_signal → risk → size
        deps = {
            sub_tasks[1].task_id: [sub_tasks[0].task_id],  # regime after data validation
            sub_tasks[2].task_id: [sub_tasks[0].task_id],  # tech after data validation
            sub_tasks[3].task_id: [sub_tasks[0].task_id],  # fund after data validation
            sub_tasks[4].task_id: [sub_tasks[0].task_id],  # news after data validation
            sub_tasks[5].task_id: [sub_tasks[1].task_id, sub_tasks[2].task_id,
                                   sub_tasks[3].task_id, sub_tasks[4].task_id],
            sub_tasks[6].task_id: [sub_tasks[5].task_id],  # risk after validation
            sub_tasks[7].task_id: [sub_tasks[6].task_id],  # size after risk
        }

        return DecompositionProposal(
            proposal_id=f"signal_gen_{task.task_id}",
            parent_task=task,
            sub_tasks=sub_tasks,
            execution_order="dag",
            dependency_graph=deps,
            estimated_total_duration=15.0,
            estimated_success_rate=0.85,
            requires_human_nodes=False,
            max_depth=depth + 1,
            rationale="Signal generation pipeline: validate → parallel analysis → signal validation → risk → sizing",
        )

    def _decompose_order_execution(
        self, task: DelegationTask, depth: int
    ) -> DecompositionProposal:
        """Decompose order execution into compliance → execution → monitoring."""
        symbol = task.input_data.get('symbol', 'UNKNOWN')

        sub_tasks = [
            DelegationTask(
                task_type=TradingTaskType.CHECK_COMPLIANCE,
                description=f"Pre-trade compliance check for {symbol}",
                characteristics=TaskCharacteristics(
                    complexity=TaskComplexity.LOW,
                    criticality=TaskCriticality.CRITICAL,
                    verifiability=TaskVerifiability.AUTO_VERIFIABLE,
                    reversibility=TaskReversibility.FULLY_REVERSIBLE,
                ),
                input_data=task.input_data,
                parent_task_id=task.task_id,
            ),
            DelegationTask(
                task_type=TradingTaskType.ASSESS_RISK,
                description=f"Final risk check before execution on {symbol}",
                characteristics=get_task_template(TradingTaskType.ASSESS_RISK),
                input_data=task.input_data,
                parent_task_id=task.task_id,
            ),
            DelegationTask(
                task_type=TradingTaskType.EXECUTE_ORDER,
                description=f"Execute order for {symbol}",
                characteristics=get_task_template(TradingTaskType.EXECUTE_ORDER),
                input_data=task.input_data,
                parent_task_id=task.task_id,
            ),
            DelegationTask(
                task_type=TradingTaskType.MONITOR_POSITION,
                description=f"Monitor position after execution on {symbol}",
                characteristics=get_task_template(TradingTaskType.MONITOR_POSITION),
                input_data=task.input_data,
                parent_task_id=task.task_id,
            ),
        ]

        # Strict sequential: compliance → risk → execute → monitor
        deps = {
            sub_tasks[1].task_id: [sub_tasks[0].task_id],
            sub_tasks[2].task_id: [sub_tasks[1].task_id],
            sub_tasks[3].task_id: [sub_tasks[2].task_id],
        }

        # PAPER: Irreversible tasks require human escalation
        requires_human = task.characteristics.requires_human_oversight
        if requires_human:
            human_task = DelegationTask(
                task_type=TradingTaskType.HUMAN_APPROVAL,
                description=f"Human approval required for {symbol} order (irreversible, critical)",
                characteristics=get_task_template(TradingTaskType.HUMAN_APPROVAL),
                input_data=task.input_data,
                parent_task_id=task.task_id,
            )
            # Insert human approval between risk and execution
            sub_tasks.insert(2, human_task)
            deps[human_task.task_id] = [sub_tasks[1].task_id]
            deps[sub_tasks[3].task_id] = [human_task.task_id]

        return DecompositionProposal(
            proposal_id=f"exec_{task.task_id}",
            parent_task=task,
            sub_tasks=sub_tasks,
            execution_order="sequential",
            dependency_graph=deps,
            estimated_total_duration=10.0 + (300.0 if requires_human else 0.0),
            estimated_success_rate=0.90,
            requires_human_nodes=requires_human,
            human_node_count=1 if requires_human else 0,
            max_depth=depth + 1,
            rationale="Order execution pipeline: compliance → risk → [human?] → execute → monitor",
        )

    def _decompose_portfolio_optimization(
        self, task: DelegationTask, depth: int
    ) -> DecompositionProposal:
        """Decompose portfolio optimization into analysis → optimize → rebalance."""
        symbols = task.input_data.get('symbols', [])

        sub_tasks = []
        # Parallel: analyze each symbol
        for sym in symbols[:10]:
            sub_tasks.append(DelegationTask(
                task_type=TradingTaskType.ANALYZE_MARKET,
                description=f"Analyze {sym} for portfolio optimization",
                characteristics=get_task_template(TradingTaskType.ANALYZE_MARKET),
                input_data={'symbol': sym},
                parent_task_id=task.task_id,
            ))

        # Correlation analysis
        corr_task = DelegationTask(
            task_type=TradingTaskType.ASSESS_RISK,
            description="Cross-asset correlation analysis",
            characteristics=TaskCharacteristics(
                complexity=TaskComplexity.HIGH,
                criticality=TaskCriticality.HIGH,
                verifiability=TaskVerifiability.EASILY_VERIFIABLE,
                reversibility=TaskReversibility.FULLY_REVERSIBLE,
            ),
            input_data={'symbols': symbols},
            parent_task_id=task.task_id,
        )
        sub_tasks.append(corr_task)

        # Optimization
        opt_task = DelegationTask(
            task_type=TradingTaskType.OPTIMIZE_PORTFOLIO,
            description="Run portfolio optimization",
            characteristics=TaskCharacteristics(
                complexity=TaskComplexity.HIGH,
                criticality=TaskCriticality.HIGH,
                verifiability=TaskVerifiability.EASILY_VERIFIABLE,
                reversibility=TaskReversibility.FULLY_REVERSIBLE,
            ),
            input_data={'symbols': symbols},
            parent_task_id=task.task_id,
        )
        sub_tasks.append(opt_task)

        # Human review for large portfolios
        human_task = DelegationTask(
            task_type=TradingTaskType.HUMAN_REVIEW,
            description="Human review of portfolio optimization results",
            characteristics=get_task_template(TradingTaskType.HUMAN_APPROVAL),
            input_data={'symbols': symbols},
            parent_task_id=task.task_id,
        )
        sub_tasks.append(human_task)

        return DecompositionProposal(
            proposal_id=f"portfolio_{task.task_id}",
            parent_task=task,
            sub_tasks=sub_tasks,
            execution_order="dag",
            estimated_total_duration=30.0 + 300.0,
            estimated_success_rate=0.80,
            requires_human_nodes=True,
            human_node_count=1,
            max_depth=depth + 1,
            rationale="Portfolio optimization: parallel analysis → correlation → optimize → human review",
        )

    def _decompose_emergency_exit(
        self, task: DelegationTask, depth: int
    ) -> DecompositionProposal:
        """Emergency exit: minimal decomposition, maximum speed."""
        sub_tasks = [
            DelegationTask(
                task_type=TradingTaskType.EMERGENCY_EXIT,
                description="Close all positions immediately",
                characteristics=get_task_template(TradingTaskType.EMERGENCY_EXIT),
                input_data=task.input_data,
                parent_task_id=task.task_id,
            ),
            DelegationTask(
                task_type=TradingTaskType.TRACK_PERFORMANCE,
                description="Log emergency exit results",
                characteristics=TaskCharacteristics(
                    complexity=TaskComplexity.LOW,
                    criticality=TaskCriticality.LOW,
                    verifiability=TaskVerifiability.AUTO_VERIFIABLE,
                    reversibility=TaskReversibility.FULLY_REVERSIBLE,
                ),
                input_data=task.input_data,
                parent_task_id=task.task_id,
            ),
        ]

        return DecompositionProposal(
            proposal_id=f"emergency_{task.task_id}",
            parent_task=task,
            sub_tasks=sub_tasks,
            execution_order="sequential",
            estimated_total_duration=2.0,
            estimated_success_rate=0.95,
            requires_human_nodes=False,
            max_depth=depth + 1,
            rationale="Emergency exit: immediate close → log results",
        )

    def _decompose_rebalance(
        self, task: DelegationTask, depth: int
    ) -> DecompositionProposal:
        """Decompose rebalancing into analysis → plan → execute."""
        return self._decompose_portfolio_optimization(task, depth)

    def _decompose_hedge(
        self, task: DelegationTask, depth: int
    ) -> DecompositionProposal:
        """Decompose hedging into risk analysis → hedge calculation → execution."""
        symbol = task.input_data.get('symbol', 'UNKNOWN')

        sub_tasks = [
            DelegationTask(
                task_type=TradingTaskType.ASSESS_RISK,
                description=f"Assess exposure for {symbol}",
                characteristics=get_task_template(TradingTaskType.ASSESS_RISK),
                input_data=task.input_data,
                parent_task_id=task.task_id,
            ),
            DelegationTask(
                task_type=TradingTaskType.CALCULATE_POSITION_SIZE,
                description=f"Calculate hedge size for {symbol}",
                characteristics=get_task_template(TradingTaskType.CALCULATE_POSITION_SIZE),
                input_data=task.input_data,
                parent_task_id=task.task_id,
            ),
            DelegationTask(
                task_type=TradingTaskType.EXECUTE_ORDER,
                description=f"Execute hedge order for {symbol}",
                characteristics=get_task_template(TradingTaskType.EXECUTE_ORDER),
                input_data=task.input_data,
                parent_task_id=task.task_id,
            ),
        ]

        return DecompositionProposal(
            proposal_id=f"hedge_{task.task_id}",
            parent_task=task,
            sub_tasks=sub_tasks,
            execution_order="sequential",
            estimated_total_duration=8.0,
            estimated_success_rate=0.88,
            requires_human_nodes=False,
            max_depth=depth + 1,
            rationale="Hedge pipeline: risk assessment → size calculation → execution",
        )

    # ========================================================================
    # GENERIC DECOMPOSITION STRATEGIES
    # ========================================================================

    def _parallel_decomposition(
        self, task: DelegationTask, depth: int
    ) -> Optional[DecompositionProposal]:
        """Fan-out: split analysis into parallel independent sub-tasks."""
        if task.task_type not in (
            TradingTaskType.ANALYZE_MARKET,
            TradingTaskType.GENERATE_SIGNAL,
            TradingTaskType.OPTIMIZE_PORTFOLIO,
        ):
            return None

        symbol = task.input_data.get('symbol', 'UNKNOWN')
        analysis_types = ['technical', 'fundamental', 'sentiment', 'regime']

        sub_tasks = [
            DelegationTask(
                task_type=TradingTaskType.ANALYZE_MARKET,
                description=f"{atype.title()} analysis for {symbol}",
                characteristics=TaskCharacteristics(
                    complexity=TaskComplexity.MODERATE,
                    criticality=task.characteristics.criticality,
                    verifiability=TaskVerifiability.MODERATELY_VERIFIABLE,
                    reversibility=TaskReversibility.FULLY_REVERSIBLE,
                ),
                input_data={'symbol': symbol, 'analysis_type': atype},
                parent_task_id=task.task_id,
            )
            for atype in analysis_types
        ]

        return DecompositionProposal(
            proposal_id=f"parallel_{task.task_id}",
            parent_task=task,
            sub_tasks=sub_tasks,
            execution_order="parallel",
            estimated_total_duration=max(
                st.characteristics.duration_seconds for st in sub_tasks
            ),
            estimated_success_rate=0.85,
            max_depth=depth + 1,
            rationale="Parallel fan-out: independent analyses run concurrently",
        )

    def _sequential_decomposition(
        self, task: DelegationTask, depth: int
    ) -> Optional[DecompositionProposal]:
        """Pipeline: sequential steps with verification gates."""
        if task.task_type == TradingTaskType.EMERGENCY_EXIT:
            return None

        symbol = task.input_data.get('symbol', 'UNKNOWN')

        sub_tasks = [
            DelegationTask(
                task_type=TradingTaskType.VALIDATE_DATA,
                description=f"Validate input data for {symbol}",
                characteristics=get_task_template(TradingTaskType.VALIDATE_DATA),
                input_data=task.input_data,
                parent_task_id=task.task_id,
            ),
            DelegationTask(
                task_type=task.task_type,
                description=f"Core execution: {task.description}",
                characteristics=task.characteristics,
                input_data=task.input_data,
                parent_task_id=task.task_id,
            ),
            DelegationTask(
                task_type=TradingTaskType.CHECK_COMPLIANCE,
                description=f"Post-execution compliance check for {symbol}",
                characteristics=TaskCharacteristics(
                    complexity=TaskComplexity.LOW,
                    criticality=TaskCriticality.HIGH,
                    verifiability=TaskVerifiability.AUTO_VERIFIABLE,
                    reversibility=TaskReversibility.FULLY_REVERSIBLE,
                ),
                input_data=task.input_data,
                parent_task_id=task.task_id,
            ),
        ]

        return DecompositionProposal(
            proposal_id=f"sequential_{task.task_id}",
            parent_task=task,
            sub_tasks=sub_tasks,
            execution_order="sequential",
            estimated_total_duration=sum(
                st.characteristics.duration_seconds for st in sub_tasks
            ),
            estimated_success_rate=0.88,
            max_depth=depth + 1,
            rationale="Sequential pipeline: validate → execute → compliance check",
        )

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        return {
            'total_decompositions': self._decomposition_count,
            'max_depth': self.config.max_depth,
            'registered_rules': len(self._decomposition_rules),
        }
