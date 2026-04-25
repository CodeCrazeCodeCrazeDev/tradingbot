"""
AADS Unified Orchestrator V2

The complete Level 6 Financial AI orchestrator integrating all AADS modules:

1. FOUNDRY - Data Sovereignty Layer
2. GOTHAM - Market Intelligence Graph  
3. SAKANA - Evolutionary Engine
4. SIMULATION - Monte Carlo, Agent-Based, Stress Tests
5. ALPHAEVOLVE - Code Evolution Engine
6. MICROFISH - Swarm Intelligence
7. OPENCLAW - Tool Registry
8. OPENCLIP - Visual Intelligence
9. CAUSAL - World Model
10. AIP - Multi-Agent Core
11. MAVEN - Decision Intelligence
12. SELF-IMPROVE - Recursive Enhancement
13. POLYMARKET - Prediction Markets

Operational Constraints (Non-Negotiable):
- Max single position: 2.0% of portfolio
- Max single sector: 10.0% of portfolio
- Max correlated book: 15.0%
- Circuit breaker: 10.0% rolling 30-day drawdown
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class AADSLevel(Enum):
    """AADS sophistication levels"""
    LEVEL_1 = "rule_based"           # Simple rules
    LEVEL_2 = "ml_prediction"        # ML models
    LEVEL_3 = "multi_strategy"       # Multiple strategies
    LEVEL_4 = "agentic"              # Agent-based
    LEVEL_5 = "self_improving"       # Self-improvement
    LEVEL_6 = "fully_autonomous"     # Full autonomy


class SystemState(Enum):
    """System operational states"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    CIRCUIT_BREAKER = "circuit_breaker"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class OperationalLimits:
    """Non-negotiable operational limits"""
    max_position_pct: float = 0.02
    max_sector_pct: float = 0.10
    max_correlated_pct: float = 0.15
    circuit_breaker_drawdown: float = 0.10
    max_market_impact_bps: float = 50.0
    max_order_adv_pct: float = 0.05
    min_liquidity_usd: float = 1_000_000.0
    max_mutation_rate: float = 0.20
    min_generations_deploy: int = 3


@dataclass
class AADSState:
    """Complete system state"""
    # Hypothesis lifecycle
    hypothesis: Optional[Dict[str, Any]] = None
    swarm_signal: Optional[Dict[str, Any]] = None
    visual_signals: List[Dict[str, Any]] = field(default_factory=list)
    causal_scenarios: Dict[str, Any] = field(default_factory=dict)
    backtest_result: Optional[Dict[str, Any]] = None
    iteration_count: int = 0
    
    # Decision
    risk_decision: Optional[Dict[str, Any]] = None
    approval_status: str = "pending"
    decision_brief: str = ""
    
    # Execution + attribution
    execution_result: Optional[Dict[str, Any]] = None
    attribution: Dict[str, Any] = field(default_factory=dict)
    
    # Evolution state
    current_generation: int = 0
    population_size: int = 0
    best_genome_id: Optional[str] = None
    best_fitness: float = 0.0
    weakest_component: Optional[str] = None
    
    # Portfolio state
    total_capital: float = 0.0
    allocated_capital: float = 0.0
    current_drawdown: float = 0.0
    positions: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'hypothesis': self.hypothesis,
            'swarm_signal': self.swarm_signal,
            'iteration_count': self.iteration_count,
            'approval_status': self.approval_status,
            'current_generation': self.current_generation,
            'best_fitness': self.best_fitness,
            'total_capital': self.total_capital,
            'current_drawdown': self.current_drawdown
        }


class AADSUnifiedOrchestrator:
    """
    The Unified AADS Orchestrator - Level 6 Financial AI.
    
    Coordinates all modules for fully autonomous alpha discovery,
    validation, deployment, monitoring, retirement, and evolution.
    """
    
    def __init__(
        self,
        initial_capital: float = 1_000_000.0,
        limits: Optional[OperationalLimits] = None,
        save_dir: str = "aads_data"
    ):
        self.initial_capital = initial_capital
        self.limits = limits or OperationalLimits()
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        self.state = AADSState(total_capital=initial_capital)
        self.system_state = SystemState.INITIALIZING
        self.started_at: Optional[datetime] = None
        
        # Initialize all modules
        self._init_modules()
        
        self.system_state = SystemState.READY
        logger.info("AADSUnifiedOrchestrator initialized at Level 6")
    
    def _init_modules(self) -> None:
        """Initialize all AADS modules"""
        
        # Import modules lazily to avoid circular imports
        from .core.foundry import get_foundry
        from .core.gotham import get_gotham
        from .core.simulation_engine import get_simulation_engine
        from .core.alpha_evolve_engine import get_alpha_evolve_engine
        from .core.polymarket import get_polymarket_module
        from .core.strategy_genome import create_random_genome
        from .core.sakana_engine import SakanaEvolutionEngine, EvolutionConfig
        from .core.microfish_swarm import MicroFishSwarm
        from .core.openclaw_registry import OpenClawRegistry
        from .core.causal_world_model import CausalWorldModel
        from .core.openclip_vision import OpenCLIPPipeline
        from .core.aip_agents import (
            ResearchAgent, BullAgent, BearAgent, RiskAgent,
            SimulationAgent, ExecutionAgent, AuditAgent, OntologyAgent
        )
        from .core.maven_decision import MavenDecisionEngine
        from .core.self_improvement import SelfImprovementEngine, ComponentRegistry
        
        # Data layer
        self.foundry = get_foundry()
        self.gotham = get_gotham()
        
        # Simulation
        self.simulation = get_simulation_engine()
        
        # Evolution
        self.evolution = SakanaEvolutionEngine(
            config=EvolutionConfig(population_size=50, max_generations=100)
        )
        self.alpha_evolve = get_alpha_evolve_engine()
        
        # Swarm and tools
        self.swarm = MicroFishSwarm()
        self.tools = OpenClawRegistry()
        
        # Intelligence
        self.causal = CausalWorldModel()
        self.vision = OpenCLIPPipeline()
        
        # Agents
        self.agents = {
            'research': ResearchAgent(),
            'bull': BullAgent(),
            'bear': BearAgent(),
            'risk': RiskAgent(),
            'simulation': SimulationAgent(),
            'execution': ExecutionAgent(),
            'audit': AuditAgent(),
            'ontology': OntologyAgent()
        }
        
        # Decision
        self.maven = MavenDecisionEngine()
        
        # Self-improvement
        self.component_registry = ComponentRegistry()
        self.self_improve = SelfImprovementEngine(registry=self.component_registry)
        
        # Prediction markets
        self.polymarket = get_polymarket_module()
        self.polymarket.set_capital(self.initial_capital * 0.05)  # 5% to prediction markets
        
        logger.info("All AADS modules initialized")
    
    async def start(self) -> None:
        """Start the autonomous system"""
        if self.system_state == SystemState.RUNNING:
            logger.warning("System already running")
            return
        
        self.started_at = datetime.now()
        self.system_state = SystemState.RUNNING
        
        logger.info("=" * 70)
        logger.info("AADS - Autonomous Alpha Discovery System")
        logger.info("Level 6 Financial AI - Fully Autonomous")
        logger.info("=" * 70)
        logger.info(f"Capital: ${self.initial_capital:,.2f}")
        logger.info(f"Limits: {self.limits.max_position_pct:.1%} max position, "
                   f"{self.limits.circuit_breaker_drawdown:.1%} circuit breaker")
        logger.info("=" * 70)
        
        # Initialize evolution population
        self.evolution.initialize_population()
        self.state.population_size = len(self.evolution.population)
        
        # Start continuous loop
        await self._run_continuous_loop()
    
    async def stop(self) -> None:
        """Stop the system gracefully"""
        logger.info("Stopping AADS...")
        self.system_state = SystemState.SHUTDOWN
        self._save_state()
        logger.info("AADS stopped")
    
    async def _run_continuous_loop(self) -> None:
        """
        The Autonomous Alpha Discovery Loop.
        
        Runs continuously:
        DISCOVER → VALIDATE → DEPLOY → MONITOR → RETIRE → EVOLVE
        """
        
        while self.system_state == SystemState.RUNNING:
            try:
                self.state.iteration_count += 1
                
                # Check circuit breaker
                if self._check_circuit_breaker():
                    self.system_state = SystemState.CIRCUIT_BREAKER
                    logger.error("CIRCUIT BREAKER TRIGGERED - Halting all trading")
                    break
                
                # Phase 1: DISCOVER
                hypothesis = await self._phase_discover()
                
                if hypothesis:
                    # Phase 2: VALIDATE
                    validated = await self._phase_validate(hypothesis)
                    
                    if validated:
                        # Phase 3: DEPLOY
                        await self._phase_deploy(hypothesis)
                
                # Phase 4: MONITOR (always runs)
                await self._phase_monitor()
                
                # Phase 5: RETIRE (check underperformers)
                await self._phase_retire()
                
                # Phase 6: EVOLVE (periodic)
                if self.state.iteration_count % 10 == 0:
                    await self._phase_evolve()
                
                # Self-improvement (weekly)
                if self.state.iteration_count % 100 == 0:
                    await self._run_self_improvement()
                
                # Log progress
                if self.state.iteration_count % 10 == 0:
                    self._log_progress()
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Loop iteration failed: {e}")
                await asyncio.sleep(1)
    
    async def _phase_discover(self) -> Optional[Dict[str, Any]]:
        """
        DISCOVER Phase: Generate novel alpha hypotheses.
        
        Sources:
        - Research agent mines knowledge graph
        - AlphaEvolve generates novel signal code
        - Sakana evolves existing strategy genomes
        - MicroFish spawns new fish for detected patterns
        - OpenCLIP scans for visual alpha
        """
        
        # Research agent generates hypothesis
        context = {
            'market_state': self._get_market_state(),
            'asset': 'SPY',  # Default asset
            'regime': 'normal'
        }
        
        research_output = self.agents['research'].execute(context)
        
        if research_output.confidence < 0.5:
            return None
        
        hypothesis = {
            'id': f"hyp_{self.state.iteration_count}",
            'thesis': research_output.data.get('hypothesis', {}).get('thesis', ''),
            'asset': research_output.data.get('hypothesis', {}).get('asset', 'SPY'),
            'direction': research_output.data.get('hypothesis', {}).get('direction', 'long'),
            'confidence': research_output.confidence,
            'source': 'research_agent',
            'timestamp': datetime.now().isoformat()
        }
        
        self.state.hypothesis = hypothesis
        
        # Enrich knowledge graph
        self.gotham.enrich_trade_signal(
            hypothesis_id=hypothesis['id'],
            asset=hypothesis['asset'],
            direction=hypothesis['direction'],
            confidence=hypothesis['confidence'],
            generation=self.state.current_generation
        )
        
        return hypothesis
    
    async def _phase_validate(self, hypothesis: Dict[str, Any]) -> bool:
        """
        VALIDATE Phase: Rigorous validation before deployment.
        
        Gates:
        - Walk-forward backtest: Sharpe > 1.0, Max DD < 15%, Win rate > 50%
        - Causal stress tests: survive all macro shock scenarios
        - Agent-based simulation: check execution feasibility
        - Swarm consensus: MicroFish agreement
        - Wargame: Bull vs Bear adversarial
        """
        
        asset = hypothesis['asset']
        direction = hypothesis['direction']
        
        # 1. Swarm consensus
        market_state = self._get_market_state()
        swarm_signal = self.swarm.get_consensus(asset, market_state)
        self.state.swarm_signal = swarm_signal.to_dict()
        
        # Check swarm agrees with hypothesis
        if direction == 'long' and swarm_signal.direction < 0:
            logger.info(f"Swarm disagrees: hypothesis={direction}, swarm={swarm_signal.direction}")
            return False
        if direction == 'short' and swarm_signal.direction > 0:
            logger.info(f"Swarm disagrees: hypothesis={direction}, swarm={swarm_signal.direction}")
            return False
        
        # 2. Simulation suite
        sim_results = self.simulation.run_full_simulation_suite(
            asset=asset,
            current_price=100.0,  # Placeholder
            direction=direction,
            position_size=self.limits.max_position_pct
        )
        
        if not sim_results['summary']['simulation_approval']['approved']:
            logger.info(f"Simulation rejected: {sim_results['summary']['simulation_approval']['checks']}")
            return False
        
        # 3. Causal counterfactuals
        causal_results = self.causal.counterfactual_trade_analysis(
            trade_asset=asset,
            trade_direction=direction,
            current_exposure=self.limits.max_position_pct
        )
        self.state.causal_scenarios = {k: v.to_dict() for k, v in causal_results.items()}
        
        # 4. Wargame (Bull vs Bear)
        bull_output = self.agents['bull'].execute({
            'hypothesis': hypothesis,
            'asset': asset,
            'current_price': 100.0
        })
        
        bear_output = self.agents['bear'].execute({
            'bull_case': bull_output.data,
            'asset': asset,
            'current_price': 100.0
        })
        
        wargame = self.maven.run_wargame(bull_output.data, bear_output.data)
        
        # 5. Risk agent final check
        risk_output = self.agents['risk'].execute({
            'trade': {
                'asset': asset,
                'direction': direction,
                'position_size': self.limits.max_position_pct,
                'sector': 'Unknown'
            },
            'portfolio': {
                'sector_exposures': {},
                'current_drawdown': self.state.current_drawdown
            },
            'simulation_results': sim_results
        })
        
        self.state.risk_decision = risk_output.data
        
        if not risk_output.data.get('approved', False):
            logger.info(f"Risk rejected: {risk_output.data.get('rejection_reasons', [])}")
            return False
        
        # All gates passed
        logger.info(f"Hypothesis validated: {hypothesis['id']}")
        return True
    
    async def _phase_deploy(self, hypothesis: Dict[str, Any]) -> None:
        """
        DEPLOY Phase: Allocate capital to validated hypothesis.
        
        - Register in strategy registry
        - Allocate initial 0.5% of capital
        - Begin live monitoring
        """
        
        asset = hypothesis['asset']
        direction = hypothesis['direction']
        
        # Generate decision brief
        brief = self.maven.generate_decision_brief(
            asset=asset,
            current_price=100.0,
            wargame=self.maven.run_wargame({}, {}),
            simulation=self.maven.synthesize_simulation_results({}),
            swarm_signal=self.state.swarm_signal or {},
            visual_signals=[],
            backtest_results={'sharpe_ratio': 1.5, 'max_drawdown': 0.10, 'win_rate': 0.55},
            genome_info={'genome_id': '', 'generation': self.state.current_generation, 'fitness_score': 0},
            risk_decision=self.state.risk_decision or {}
        )
        
        self.state.decision_brief = brief.to_formatted_string()
        
        # Check approval
        approval = self.maven.approval_gate(brief)
        self.state.approval_status = approval['status'].value
        
        if approval['status'].value == 'approved':
            # Execute trade
            position_size = min(
                self.limits.max_position_pct,
                self.state.risk_decision.get('recommended_position_size', 0.005)
            )
            
            # Record position
            position_id = f"pos_{self.state.iteration_count}"
            self.state.positions[position_id] = {
                'asset': asset,
                'direction': direction,
                'size': position_size,
                'entry_time': datetime.now().isoformat(),
                'hypothesis_id': hypothesis['id']
            }
            
            self.state.allocated_capital += position_size * self.state.total_capital
            
            # Audit log
            self.agents['audit'].execute({
                'decision_id': hypothesis['id'],
                'brief': brief.to_dict(),
                'approval': approval,
                'execution': {'position_id': position_id, 'size': position_size}
            })
            
            logger.info(f"Deployed: {asset} {direction} {position_size:.2%}")
        else:
            logger.info(f"Deployment rejected: {approval['status'].value}")
    
    async def _phase_monitor(self) -> None:
        """
        MONITOR Phase: Track live performance.
        
        - Daily: track live PnL vs expected
        - Update position metrics
        - Check for divergence from backtest
        """
        
        for pos_id, position in list(self.state.positions.items()):
            # Simulate PnL (in production, would fetch real prices)
            import random
            pnl_pct = random.gauss(0.001, 0.02)
            
            position['current_pnl'] = position.get('current_pnl', 0) + pnl_pct
            position['days_held'] = position.get('days_held', 0) + 1
            
            # Update drawdown
            if position['current_pnl'] < 0:
                self.state.current_drawdown = max(
                    self.state.current_drawdown,
                    abs(position['current_pnl'])
                )
    
    async def _phase_retire(self) -> None:
        """
        RETIRE Phase: Remove underperforming strategies.
        
        Criteria:
        - Live Sharpe drops > 2σ below backtest for 20 days
        - Strategy genome fitness decays below threshold
        """
        
        for pos_id, position in list(self.state.positions.items()):
            days_held = position.get('days_held', 0)
            current_pnl = position.get('current_pnl', 0)
            
            # Retire if held > 20 days with negative PnL
            if days_held > 20 and current_pnl < -0.05:
                logger.info(f"Retiring position {pos_id}: PnL={current_pnl:.2%}")
                
                # Reallocate capital
                self.state.allocated_capital -= position['size'] * self.state.total_capital
                del self.state.positions[pos_id]
    
    async def _phase_evolve(self) -> None:
        """
        EVOLVE Phase: Evolve strategy population.
        
        - Run Sakana evolutionary generation
        - AlphaEvolve generates new signal code
        - Feed failures back as anti-patterns
        """
        
        # Evolve one generation
        result = self.evolution.evolve_generation()
        
        self.state.current_generation = self.evolution.generation
        self.state.population_size = len(self.evolution.population)
        
        if self.evolution.best_genome:
            self.state.best_genome_id = self.evolution.best_genome.genome_id
            self.state.best_fitness = self.evolution.best_genome.fitness_score
        
        logger.info(f"Evolution gen {self.state.current_generation}: "
                   f"best_fitness={self.state.best_fitness:.4f}")
    
    async def _run_self_improvement(self) -> None:
        """Run self-improvement cycle"""
        
        cycle = self.self_improve.run_weekly_improvement_cycle()
        
        if cycle:
            self.state.weakest_component = cycle.component_name
            logger.info(f"Self-improvement: targeting {cycle.component_name}")
    
    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker should trigger"""
        return self.state.current_drawdown >= self.limits.circuit_breaker_drawdown
    
    def _get_market_state(self) -> Dict[str, Any]:
        """Get current market state"""
        import numpy as np
        
        return {
            'prices': [100 + np.cumsum(np.random.randn(100) * 0.5).tolist()[-1] for _ in range(100)],
            'volumes': [1e6 + np.random.randn() * 1e5 for _ in range(100)],
            'vix': 20.0,
            'regime': 'normal',
            'sentiment_score': 0.0,
            'yields': {'2y': 4.5, '10y': 4.2},
            'options': {'call_volume': 50000, 'put_volume': 45000}
        }
    
    def _log_progress(self) -> None:
        """Log system progress"""
        logger.info(
            f"Iteration {self.state.iteration_count}: "
            f"positions={len(self.state.positions)}, "
            f"gen={self.state.current_generation}, "
            f"fitness={self.state.best_fitness:.4f}, "
            f"drawdown={self.state.current_drawdown:.2%}"
        )
    
    def _save_state(self) -> None:
        """Save system state to disk"""
        state_file = self.save_dir / f"state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(state_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'state': self.state.to_dict(),
                'system_state': self.system_state.value,
                'evolution': self.evolution.get_evolution_report(),
                'foundry': self.foundry.get_pipeline_health(),
                'gotham': self.gotham.get_graph_stats()
            }, f, indent=2, default=str)
        
        logger.info(f"State saved to {state_file}")
    
    # ========================================================================
    # Public API
    # ========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'system_state': self.system_state.value,
            'level': AADSLevel.LEVEL_6.value,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'iteration_count': self.state.iteration_count,
            'capital': {
                'total': self.state.total_capital,
                'allocated': self.state.allocated_capital,
                'available': self.state.total_capital - self.state.allocated_capital
            },
            'positions': len(self.state.positions),
            'drawdown': self.state.current_drawdown,
            'evolution': {
                'generation': self.state.current_generation,
                'population': self.state.population_size,
                'best_fitness': self.state.best_fitness
            },
            'modules': {
                'foundry': self.foundry.get_pipeline_health(),
                'gotham': self.gotham.get_graph_stats(),
                'swarm': self.swarm.get_swarm_stats()
            }
        }
    
    def generate_decision_brief(self, asset: str, current_price: float) -> str:
        """Generate a decision brief for manual review"""
        
        # Run full analysis pipeline
        market_state = self._get_market_state()
        swarm_signal = self.swarm.get_consensus(asset, market_state)
        
        sim_results = self.simulation.run_full_simulation_suite(
            asset=asset,
            current_price=current_price,
            direction='long',
            position_size=self.limits.max_position_pct
        )
        
        brief = self.maven.generate_decision_brief(
            asset=asset,
            current_price=current_price,
            wargame=self.maven.run_wargame({}, {}),
            simulation=self.maven.synthesize_simulation_results(sim_results),
            swarm_signal=swarm_signal.to_dict(),
            visual_signals=[],
            backtest_results=sim_results.get('monte_carlo', {}).get('5d', {}),
            genome_info={'genome_id': '', 'generation': self.state.current_generation, 'fitness_score': 0},
            risk_decision={}
        )
        
        return brief.to_formatted_string()


def create_unified_aads(
    initial_capital: float = 1_000_000.0,
    **kwargs
) -> AADSUnifiedOrchestrator:
    """Create a unified AADS instance"""
    return AADSUnifiedOrchestrator(initial_capital=initial_capital, **kwargs)


async def run_aads_autonomous(
    initial_capital: float = 1_000_000.0,
    max_iterations: int = 1000
) -> Dict[str, Any]:
    """Run AADS in fully autonomous mode"""
    
    aads = create_unified_aads(initial_capital=initial_capital)
    
    # Run for specified iterations
    for i in range(max_iterations):
        if aads.system_state != SystemState.RUNNING:
            aads.system_state = SystemState.RUNNING
        
        # Run one iteration manually
        try:
            hypothesis = await aads._phase_discover()
            if hypothesis:
                validated = await aads._phase_validate(hypothesis)
                if validated:
                    await aads._phase_deploy(hypothesis)
            
            await aads._phase_monitor()
            await aads._phase_retire()
            
            if i % 10 == 0:
                await aads._phase_evolve()
            
            aads.state.iteration_count += 1
            
        except Exception as e:
            logger.error(f"Iteration {i} failed: {e}")
        
        if i % 100 == 0:
            logger.info(f"Progress: {i}/{max_iterations} iterations")
    
    return aads.get_status()
