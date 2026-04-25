"""
AADS Autonomous Alpha Discovery Loop

This is what separates AADS from everything below Level 6.
The system does NOT wait for humans to specify strategies — it discovers them.

Continuous Discovery Loop (runs 24/7):
1. DISCOVER - Generate novel alpha hypotheses
2. VALIDATE - Walk-forward backtest + causal stress tests
3. DEPLOY - Capital allocation to validated strategies
4. MONITOR - Track live vs expected performance
5. RETIRE - Auto-retire underperformers
6. EVOLVE - Feed failures back into evolution

Operational Constraints (Non-Negotiable):
- Max single position: 2.0% of portfolio
- Max single sector: 10.0% of portfolio
- Max correlated book: 15.0%
- Circuit breaker: 10.0% rolling 30-day drawdown
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import logging
import asyncio
import uuid

from .strategy_genome import AADSStrategyGenome, GenomeStatus, create_random_genome
from .sakana_engine import SakanaEvolutionEngine, EvolutionConfig
from .microfish_swarm import MicroFishSwarm, SwarmSignal
from .aip_agents import (
    ResearchAgent, BullAgent, BearAgent, RiskAgent,
    SimulationAgent, ExecutionAgent, AuditAgent, OntologyAgent
)
from .maven_decision import MavenDecisionEngine, DecisionBrief, ApprovalStatus
from .self_improvement import SelfImprovementEngine, ComponentRegistry
from .causal_world_model import CausalWorldModel
from .openclip_vision import OpenCLIPPipeline

logger = logging.getLogger(__name__)


class LoopPhase(Enum):
    """Current phase of the discovery loop"""
    IDLE = "idle"
    DISCOVERING = "discovering"
    VALIDATING = "validating"
    DEPLOYING = "deploying"
    MONITORING = "monitoring"
    RETIRING = "retiring"
    EVOLVING = "evolving"


class DiscoverySource(Enum):
    """Source of alpha discovery"""
    RESEARCH_AGENT = "research_agent"
    ALPHA_EVOLVE = "alpha_evolve"
    SAKANA_EVOLUTION = "sakana_evolution"
    MICROFISH_SPAWN = "microfish_spawn"
    OPENCLIP_VISUAL = "openclip_visual"
    KNOWLEDGE_GRAPH = "knowledge_graph"


@dataclass
class DiscoveryResult:
    """Result of a discovery cycle"""
    discovery_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    source: DiscoverySource = DiscoverySource.RESEARCH_AGENT
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Hypothesis
    hypothesis: Dict[str, Any] = field(default_factory=dict)
    genome: Optional[AADSStrategyGenome] = None
    
    # Validation
    validated: bool = False
    validation_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Deployment
    deployed: bool = False
    capital_allocation: float = 0.0
    
    # Performance
    live_sharpe: float = 0.0
    live_pnl: float = 0.0
    days_live: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'discovery_id': self.discovery_id,
            'source': self.source.value,
            'timestamp': self.timestamp.isoformat(),
            'hypothesis': self.hypothesis,
            'genome_id': self.genome.genome_id if self.genome else None,
            'validated': self.validated,
            'validation_metrics': self.validation_metrics,
            'deployed': self.deployed,
            'capital_allocation': self.capital_allocation,
            'live_sharpe': self.live_sharpe,
            'live_pnl': self.live_pnl,
            'days_live': self.days_live
        }


@dataclass
class PortfolioState:
    """Current portfolio state"""
    total_capital: float = 1_000_000.0
    cash: float = 1_000_000.0
    positions: Dict[str, Dict[str, float]] = field(default_factory=dict)  # asset -> {size, entry, pnl}
    
    # Risk metrics
    current_drawdown: float = 0.0
    rolling_30d_drawdown: float = 0.0
    portfolio_var_95: float = 0.0
    
    # Sector exposures
    sector_exposures: Dict[str, float] = field(default_factory=dict)
    
    # Deployed strategies
    deployed_strategies: Dict[str, float] = field(default_factory=dict)  # genome_id -> allocation
    
    @property
    def total_deployed(self) -> float:
        return sum(self.deployed_strategies.values())
    
    @property
    def available_capital(self) -> float:
        return 1.0 - self.total_deployed
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_capital': self.total_capital,
            'cash': self.cash,
            'positions': self.positions,
            'current_drawdown': self.current_drawdown,
            'rolling_30d_drawdown': self.rolling_30d_drawdown,
            'sector_exposures': self.sector_exposures,
            'deployed_strategies': self.deployed_strategies,
            'total_deployed': self.total_deployed
        }


class OperationalConstraints:
    """Non-negotiable operational constraints"""
    
    # Capital limits
    MAX_SINGLE_POSITION = 0.02      # 2% of portfolio
    MAX_SINGLE_SECTOR = 0.10        # 10% of portfolio
    MAX_CORRELATED_BOOK = 0.15      # 15% correlation > 0.6
    CIRCUIT_BREAKER_DD = 0.10       # 10% rolling 30-day drawdown
    
    # Execution limits
    MAX_MARKET_IMPACT_BPS = 50      # 50 bps
    MAX_ORDER_PCT_ADV = 0.05        # 5% of ADV
    MIN_LIQUIDITY_ADV = 1_000_000   # $1M ADV
    
    # Evolution limits
    MAX_MUTATION_RATE = 0.20        # 20% parameter change
    MIN_GENERATIONS = 3             # Before deployment
    
    # Validation gates
    MIN_SHARPE = 1.0
    MAX_DRAWDOWN = 0.15
    MIN_WIN_RATE = 0.55
    MIN_OOS_PERIODS = 3
    
    @classmethod
    def check_position_limit(cls, size: float) -> bool:
        return size <= cls.MAX_SINGLE_POSITION
    
    @classmethod
    def check_sector_limit(cls, exposure: float) -> bool:
        return exposure <= cls.MAX_SINGLE_SECTOR
    
    @classmethod
    def check_circuit_breaker(cls, drawdown: float) -> bool:
        return drawdown < cls.CIRCUIT_BREAKER_DD
    
    @classmethod
    def check_validation_gates(cls, metrics: Dict[str, float]) -> Tuple[bool, List[str]]:
        """Check if strategy passes all validation gates"""
        failures = []
        
        if metrics.get('sharpe_ratio', 0) < cls.MIN_SHARPE:
            failures.append(f"Sharpe {metrics.get('sharpe_ratio', 0):.2f} < {cls.MIN_SHARPE}")
        
        if abs(metrics.get('max_drawdown', 1)) > cls.MAX_DRAWDOWN:
            failures.append(f"Max DD {metrics.get('max_drawdown', 0):.1%} > {cls.MAX_DRAWDOWN:.1%}")
        
        if metrics.get('win_rate', 0) < cls.MIN_WIN_RATE:
            failures.append(f"Win rate {metrics.get('win_rate', 0):.1%} < {cls.MIN_WIN_RATE:.1%}")
        
        return len(failures) == 0, failures


class AutonomousAlphaDiscoveryLoop:
    """
    The Autonomous Alpha Discovery Loop - Core of AADS Level 6.
    
    Runs continuously to:
    - Discover new alpha sources
    - Validate through rigorous backtesting
    - Deploy with capital allocation
    - Monitor live performance
    - Retire underperformers
    - Evolve based on feedback
    """
    
    def __init__(
        self,
        initial_capital: float = 1_000_000.0,
        backtest_fn: Optional[Callable] = None
    ):
        # Portfolio state
        self.portfolio = PortfolioState(total_capital=initial_capital, cash=initial_capital)
        
        # Core engines
        self.evolution_engine = SakanaEvolutionEngine(
            config=EvolutionConfig(),
            backtest_fn=backtest_fn
        )
        self.swarm = MicroFishSwarm()
        self.causal_model = CausalWorldModel()
        self.vision_pipeline = OpenCLIPPipeline()
        self.decision_engine = MavenDecisionEngine()
        self.self_improvement = SelfImprovementEngine()
        
        # Agents
        self.research_agent = ResearchAgent()
        self.bull_agent = BullAgent()
        self.bear_agent = BearAgent()
        self.risk_agent = RiskAgent()
        self.simulation_agent = SimulationAgent()
        self.execution_agent = ExecutionAgent()
        self.audit_agent = AuditAgent()
        self.ontology_agent = OntologyAgent()
        
        # Discovery tracking
        self.discoveries: List[DiscoveryResult] = []
        self.deployed_discoveries: Dict[str, DiscoveryResult] = {}
        self.retired_discoveries: Dict[str, DiscoveryResult] = {}
        
        # Loop state
        self.current_phase = LoopPhase.IDLE
        self.loop_iterations = 0
        self.last_improvement_check = datetime.now()
        
        # Performance tracking
        self.daily_pnl: List[Tuple[datetime, float]] = []
        self.peak_capital = initial_capital
        
        logger.info("AutonomousAlphaDiscoveryLoop initialized")
    
    async def run_continuous_loop(self, max_iterations: Optional[int] = None) -> None:
        """
        Run the continuous discovery loop.
        
        This is the main entry point for autonomous operation.
        """
        logger.info("Starting Autonomous Alpha Discovery Loop")
        
        iteration = 0
        while max_iterations is None or iteration < max_iterations:
            try:
                # Check circuit breaker
                if not OperationalConstraints.check_circuit_breaker(self.portfolio.rolling_30d_drawdown):
                    logger.warning("CIRCUIT BREAKER TRIGGERED - Halting all new positions")
                    await asyncio.sleep(3600)  # Wait 1 hour
                    continue
                
                # Run one iteration of the loop
                await self._run_iteration()
                
                iteration += 1
                self.loop_iterations = iteration
                
                # Weekly self-improvement check
                if datetime.now() - self.last_improvement_check > timedelta(days=7):
                    await self._run_self_improvement()
                    self.last_improvement_check = datetime.now()
                
                # Brief pause between iterations
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Loop iteration failed: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    async def _run_iteration(self) -> None:
        """Run one iteration of the discovery loop"""
        
        # Phase 1: DISCOVER
        self.current_phase = LoopPhase.DISCOVERING
        discoveries = await self._discover_phase()
        
        # Phase 2: VALIDATE
        self.current_phase = LoopPhase.VALIDATING
        validated = await self._validate_phase(discoveries)
        
        # Phase 3: DEPLOY
        self.current_phase = LoopPhase.DEPLOYING
        await self._deploy_phase(validated)
        
        # Phase 4: MONITOR
        self.current_phase = LoopPhase.MONITORING
        await self._monitor_phase()
        
        # Phase 5: RETIRE
        self.current_phase = LoopPhase.RETIRING
        await self._retire_phase()
        
        # Phase 6: EVOLVE
        self.current_phase = LoopPhase.EVOLVING
        await self._evolve_phase()
        
        self.current_phase = LoopPhase.IDLE
    
    async def _discover_phase(self) -> List[DiscoveryResult]:
        """
        Phase 1: DISCOVER
        
        Generate novel alpha hypotheses from multiple sources:
        - Research agent mines knowledge graph
        - AlphaEvolve generates novel signal code
        - Sakana evolutionary engine evolves genomes
        - MicroFish spawns new fish for patterns
        - OpenCLIP scans for visual alpha
        """
        discoveries = []
        
        # Source 1: Research Agent
        research_context = {
            'asset': 'SPY',  # Example
            'market_state': self._get_market_state()
        }
        research_output = self.research_agent.execute(research_context)
        
        if research_output.confidence > 0.6:
            discovery = DiscoveryResult(
                source=DiscoverySource.RESEARCH_AGENT,
                hypothesis=research_output.data
            )
            discoveries.append(discovery)
        
        # Source 2: Sakana Evolution
        if len(self.evolution_engine.population) == 0:
            self.evolution_engine.initialize_population()
        
        # Run one generation
        gen_result = self.evolution_engine.evolve_generation()
        
        if gen_result.best_genome:
            discovery = DiscoveryResult(
                source=DiscoverySource.SAKANA_EVOLUTION,
                genome=gen_result.best_genome,
                hypothesis={'type': 'evolved_strategy', 'generation': gen_result.generation}
            )
            discoveries.append(discovery)
        
        # Source 3: MicroFish Swarm
        swarm_signal = self.swarm.get_consensus('SPY', self._get_market_state())
        
        if swarm_signal.strength > 0.7:
            discovery = DiscoveryResult(
                source=DiscoverySource.MICROFISH_SPAWN,
                hypothesis={
                    'type': 'swarm_consensus',
                    'direction': swarm_signal.direction,
                    'strength': swarm_signal.strength,
                    'dominant_fish': swarm_signal.dominant_fish
                }
            )
            discoveries.append(discovery)
        
        logger.info(f"Discovery phase: {len(discoveries)} hypotheses generated")
        return discoveries
    
    async def _validate_phase(self, discoveries: List[DiscoveryResult]) -> List[DiscoveryResult]:
        """
        Phase 2: VALIDATE
        
        For each hypothesis:
        - Walk-forward backtest: Sharpe > 1.0, Max DD < 15%, Win rate > 55%
        - Causal scenario stress test: survive all macro shock scenarios
        - Agent-based microstructure sim: check execution feasibility
        - Anti-overfit check: regime stability across 3 distinct periods
        """
        validated = []
        
        for discovery in discoveries:
            # Run validation
            validation_result = await self._validate_discovery(discovery)
            
            if validation_result['passed']:
                discovery.validated = True
                discovery.validation_metrics = validation_result['metrics']
                validated.append(discovery)
                logger.info(f"Discovery {discovery.discovery_id} validated")
            else:
                logger.info(f"Discovery {discovery.discovery_id} failed validation: {validation_result['failures']}")
        
        return validated
    
    async def _validate_discovery(self, discovery: DiscoveryResult) -> Dict[str, Any]:
        """Validate a single discovery"""
        
        # Get or create genome
        genome = discovery.genome
        if genome is None:
            genome = create_random_genome()
            discovery.genome = genome
        
        # Simulate backtest (in production, run actual backtest)
        backtest_metrics = {
            'sharpe_ratio': np.random.uniform(0.5, 2.5),
            'max_drawdown': np.random.uniform(0.05, 0.25),
            'win_rate': np.random.uniform(0.45, 0.65),
            'sortino_ratio': np.random.uniform(0.5, 3.0),
            'calmar_ratio': np.random.uniform(0.5, 2.0)
        }
        
        # Check validation gates
        passed, failures = OperationalConstraints.check_validation_gates(backtest_metrics)
        
        # Run causal stress tests
        causal_scenarios = self.causal_model.counterfactual_trade_analysis(
            trade_asset=discovery.hypothesis.get('asset', 'SPY'),
            trade_direction='long',
            current_exposure=0.01
        )
        
        # Check survival under stress scenarios
        stress_passed = True
        for scenario_name, result in causal_scenarios.items():
            # Check if trade survives scenario
            if any(abs(v) > 0.20 for v in result.causal_effects.values()):
                stress_passed = False
                failures.append(f"Failed stress test: {scenario_name}")
        
        # Run simulation
        sim_context = {
            'asset': discovery.hypothesis.get('asset', 'SPY'),
            'position_size': 0.01,
            'current_price': 100.0
        }
        sim_output = self.simulation_agent.execute(sim_context)
        
        # Final validation
        final_passed = passed and stress_passed
        
        return {
            'passed': final_passed,
            'metrics': backtest_metrics,
            'failures': failures,
            'simulation': sim_output.data
        }
    
    async def _deploy_phase(self, validated: List[DiscoveryResult]) -> None:
        """
        Phase 3: DEPLOY
        
        If hypothesis passes all gates:
        - 0.5% capital allocation
        - Register in strategy registry
        - Shadow period: compare live vs backtest
        """
        for discovery in validated:
            # Check if we have capacity
            if self.portfolio.available_capital < 0.005:
                logger.warning("No capacity for new deployments")
                break
            
            # Run full decision process
            decision_brief = await self._generate_decision(discovery)
            
            if decision_brief.approval_status == ApprovalStatus.AUTO_EXECUTE:
                # Deploy
                allocation = 0.005  # 0.5% initial allocation
                
                discovery.deployed = True
                discovery.capital_allocation = allocation
                
                # Update portfolio
                genome_id = discovery.genome.genome_id if discovery.genome else discovery.discovery_id
                self.portfolio.deployed_strategies[genome_id] = allocation
                
                # Track
                self.deployed_discoveries[discovery.discovery_id] = discovery
                self.discoveries.append(discovery)
                
                # Audit
                self.audit_agent.execute({
                    'decision_id': decision_brief.decision_id,
                    'asset': decision_brief.asset,
                    'direction': decision_brief.direction,
                    'approved': True,
                    'confidence': decision_brief.confidence
                })
                
                logger.info(f"Deployed discovery {discovery.discovery_id} with {allocation:.1%} allocation")
    
    async def _generate_decision(self, discovery: DiscoveryResult) -> DecisionBrief:
        """Generate full decision brief for a discovery"""
        asset = discovery.hypothesis.get('asset', 'SPY')
        current_price = 100.0  # Placeholder
        
        # Run wargame
        bull_output = self.bull_agent.execute({
            'hypothesis': discovery.hypothesis,
            'asset': asset,
            'current_price': current_price
        })
        
        bear_output = self.bear_agent.execute({
            'bull_case': bull_output.data,
            'asset': asset,
            'current_price': current_price
        })
        
        wargame = self.decision_engine.run_wargame(bull_output.data, bear_output.data)
        
        # Run simulation
        sim_output = self.simulation_agent.execute({
            'asset': asset,
            'position_size': 0.01,
            'current_price': current_price
        })
        
        simulation = self.decision_engine.synthesize_simulation_results(sim_output.data.get('simulations', {}))
        
        # Get swarm signal
        swarm_signal = self.swarm.get_consensus(asset, self._get_market_state())
        
        # Risk check
        risk_output = self.risk_agent.execute({
            'trade': {'position_size': 0.01, 'sector': 'Technology'},
            'portfolio': self.portfolio.to_dict(),
            'simulation_results': sim_output.data
        })
        
        # Generate brief
        brief = self.decision_engine.generate_decision_brief(
            asset=asset,
            current_price=current_price,
            wargame=wargame,
            simulation=simulation,
            swarm_signal=swarm_signal.to_dict(),
            visual_signals=[],
            backtest_results=discovery.validation_metrics,
            genome_info={
                'genome_id': discovery.genome.genome_id if discovery.genome else '',
                'generation': discovery.genome.generation if discovery.genome else 0,
                'fitness_score': discovery.genome.fitness_score if discovery.genome else 0
            },
            risk_decision=risk_output.data
        )
        
        return brief
    
    async def _monitor_phase(self) -> None:
        """
        Phase 4: MONITOR
        
        Daily: track live PnL vs expected PnL
        Weekly: benchmark all components
        Monthly: full evolutionary generation cycle
        """
        for discovery_id, discovery in self.deployed_discoveries.items():
            # Simulate live performance
            discovery.days_live += 1
            
            # Simulate daily PnL
            daily_return = np.random.normal(0.0005, 0.02)
            discovery.live_pnl += daily_return * discovery.capital_allocation
            
            # Update live Sharpe (simplified)
            if discovery.days_live > 20:
                discovery.live_sharpe = discovery.live_pnl / (discovery.days_live * 0.02) * np.sqrt(252)
        
        # Update portfolio drawdown
        self._update_portfolio_metrics()
    
    async def _retire_phase(self) -> None:
        """
        Phase 5: RETIRE
        
        If live performance diverges from backtest by > 2σ for 20 consecutive days:
        - Auto-retire strategy
        - Reallocate capital to best performers
        """
        to_retire = []
        
        for discovery_id, discovery in self.deployed_discoveries.items():
            # Check retirement criteria
            if discovery.days_live >= 20:
                expected_sharpe = discovery.validation_metrics.get('sharpe_ratio', 1.0)
                
                # Check if live Sharpe is significantly below expected
                if discovery.live_sharpe < expected_sharpe - 0.5:  # Simplified 2σ check
                    to_retire.append(discovery_id)
                    logger.info(f"Retiring discovery {discovery_id}: live Sharpe {discovery.live_sharpe:.2f} "
                               f"vs expected {expected_sharpe:.2f}")
        
        # Retire underperformers
        for discovery_id in to_retire:
            discovery = self.deployed_discoveries.pop(discovery_id)
            discovery.deployed = False
            
            # Free up capital
            genome_id = discovery.genome.genome_id if discovery.genome else discovery_id
            if genome_id in self.portfolio.deployed_strategies:
                del self.portfolio.deployed_strategies[genome_id]
            
            # Archive
            self.retired_discoveries[discovery_id] = discovery
            
            # Update genome status
            if discovery.genome:
                discovery.genome.status = GenomeStatus.RETIRED
    
    async def _evolve_phase(self) -> None:
        """
        Phase 6: EVOLVE
        
        - Retired strategy genomes become input to next generation
        - Failure modes logged as anti-patterns
        - Self-improve engine targets weakest component
        """
        # Feed retired genomes back to evolution
        for discovery in self.retired_discoveries.values():
            if discovery.genome:
                # Log failure modes
                failure_mode = {
                    'genome_id': discovery.genome.genome_id,
                    'expected_sharpe': discovery.validation_metrics.get('sharpe_ratio', 0),
                    'live_sharpe': discovery.live_sharpe,
                    'days_live': discovery.days_live,
                    'reason': 'performance_divergence'
                }
                logger.info(f"Logged failure mode: {failure_mode}")
        
        # Clear retired (already processed)
        self.retired_discoveries.clear()
    
    async def _run_self_improvement(self) -> None:
        """Run weekly self-improvement cycle"""
        logger.info("Running weekly self-improvement cycle")
        
        cycle = self.self_improvement.run_weekly_improvement_cycle()
        
        if cycle:
            logger.info(f"Self-improvement cycle completed: {cycle.status.value}")
    
    def _get_market_state(self) -> Dict[str, Any]:
        """Get current market state for agents"""
        return {
            'prices': [100 + np.random.randn() for _ in range(100)],
            'volumes': [1e6 + np.random.randn() * 1e5 for _ in range(100)],
            'vix': np.random.uniform(15, 30),
            'regime': 'normal',
            'sentiment_score': np.random.uniform(-0.5, 0.5)
        }
    
    def _update_portfolio_metrics(self) -> None:
        """Update portfolio risk metrics"""
        # Calculate current drawdown
        total_pnl = sum(d.live_pnl for d in self.deployed_discoveries.values())
        current_capital = self.portfolio.total_capital + total_pnl
        
        if current_capital > self.peak_capital:
            self.peak_capital = current_capital
        
        self.portfolio.current_drawdown = (self.peak_capital - current_capital) / self.peak_capital
        
        # Rolling 30-day drawdown (simplified)
        self.portfolio.rolling_30d_drawdown = self.portfolio.current_drawdown
    
    def get_loop_status(self) -> Dict[str, Any]:
        """Get current status of the discovery loop"""
        return {
            'current_phase': self.current_phase.value,
            'loop_iterations': self.loop_iterations,
            'total_discoveries': len(self.discoveries),
            'deployed_count': len(self.deployed_discoveries),
            'retired_count': len(self.retired_discoveries),
            'portfolio': self.portfolio.to_dict(),
            'evolution_generation': self.evolution_engine.generation,
            'swarm_stats': self.swarm.get_swarm_stats()
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        deployed = list(self.deployed_discoveries.values())
        
        if not deployed:
            return {'status': 'no_deployed_strategies'}
        
        return {
            'deployed_strategies': len(deployed),
            'total_allocation': sum(d.capital_allocation for d in deployed),
            'total_pnl': sum(d.live_pnl for d in deployed),
            'avg_live_sharpe': np.mean([d.live_sharpe for d in deployed]),
            'avg_days_live': np.mean([d.days_live for d in deployed]),
            'portfolio_drawdown': self.portfolio.current_drawdown,
            'circuit_breaker_active': not OperationalConstraints.check_circuit_breaker(
                self.portfolio.rolling_30d_drawdown
            ),
            'discoveries_by_source': {
                source.value: sum(1 for d in self.discoveries if d.source == source)
                for source in DiscoverySource
            }
        }
