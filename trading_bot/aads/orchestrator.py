"""
AADS Orchestrator - Main Entry Point

The AADSOrchestrator is the unified control plane for the entire
Autonomous Alpha Discovery System. It coordinates all modules:

- Foundry: Data sovereignty layer
- Gotham: Market intelligence graph
- Sakana: Evolutionary engine
- Simulation: Monte Carlo, stress tests
- AlphaEvolve: Code evolution
- MicroFish: Swarm intelligence
- OpenClaw: Tool registry
- OpenCLIP: Visual intelligence
- Causal: World model
- AIP: Multi-agent core
- Maven: Decision intelligence
- Self-Improvement: Recursive enhancement

This is Level 6 Financial AI - fully autonomous alpha discovery.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import json
from pathlib import Path

from .core.strategy_genome import AADSStrategyGenome, GenomeStatus
from .core.sakana_engine import SakanaEvolutionEngine, EvolutionConfig
from .core.microfish_swarm import MicroFishSwarm
from .core.openclaw_registry import OpenClawRegistry, Tool, ToolCategory
from .core.causal_world_model import CausalWorldModel
from .core.openclip_vision import OpenCLIPPipeline
from .core.aip_agents import (
    ResearchAgent, BullAgent, BearAgent, RiskAgent,
    SimulationAgent, ExecutionAgent, AuditAgent, OntologyAgent
)
from .core.maven_decision import MavenDecisionEngine, DecisionBrief
from .core.self_improvement import SelfImprovementEngine, ComponentRegistry
from .core.alpha_discovery_loop import AutonomousAlphaDiscoveryLoop, OperationalConstraints

logger = logging.getLogger(__name__)


class AADSMode(Enum):
    """Operating modes for AADS"""
    DISCOVERY = "discovery"         # Full autonomous discovery
    PAPER_TRADING = "paper_trading" # Simulated execution
    LIVE_TRADING = "live_trading"   # Real execution
    BACKTEST = "backtest"           # Historical analysis
    RESEARCH = "research"           # Research only, no trading


@dataclass
class AADSConfig:
    """Configuration for the AADS system"""
    # Operating mode
    mode: AADSMode = AADSMode.PAPER_TRADING
    
    # Capital
    initial_capital: float = 1_000_000.0
    
    # Evolution
    population_size: int = 50
    max_generations: int = 100
    
    # Risk limits (non-negotiable)
    max_position_pct: float = 0.02
    max_sector_pct: float = 0.10
    max_drawdown_pct: float = 0.10
    
    # Execution
    enable_live_execution: bool = False
    paper_trade_slippage_bps: float = 5.0
    
    # Self-improvement
    enable_self_improvement: bool = True
    improvement_frequency_days: int = 7
    
    # Persistence
    save_directory: str = "aads_data"
    checkpoint_frequency: int = 10
    
    # Logging
    log_level: str = "INFO"
    audit_all_decisions: bool = True


class AADSOrchestrator:
    """
    Main orchestrator for the Autonomous Alpha Discovery System.
    
    Coordinates all AADS modules and provides a unified interface
    for autonomous alpha discovery and trading.
    """
    
    def __init__(self, config: Optional[AADSConfig] = None):
        """
        Initialize the AADS orchestrator.
        
        Args:
            config: AADS configuration (uses defaults if not provided)
        """
        self.config = config or AADSConfig()
        self.started_at: Optional[datetime] = None
        self.is_running = False
        
        # Setup logging
        logging.basicConfig(level=getattr(logging, self.config.log_level))
        
        # Setup directories
        self.save_dir = Path(self.config.save_directory)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize all modules
        self._initialize_modules()
        
        logger.info(f"AADSOrchestrator initialized in {self.config.mode.value} mode")
    
    def _initialize_modules(self) -> None:
        """Initialize all AADS modules"""
        
        # Core engines
        self.evolution_engine = SakanaEvolutionEngine(
            config=EvolutionConfig(
                population_size=self.config.population_size,
                max_generations=self.config.max_generations
            )
        )
        
        self.swarm = MicroFishSwarm()
        self.tool_registry = OpenClawRegistry()
        self.causal_model = CausalWorldModel()
        self.vision_pipeline = OpenCLIPPipeline()
        self.decision_engine = MavenDecisionEngine()
        self.component_registry = ComponentRegistry()
        self.self_improvement = SelfImprovementEngine(registry=self.component_registry)
        
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
        
        # Discovery loop
        self.discovery_loop = AutonomousAlphaDiscoveryLoop(
            initial_capital=self.config.initial_capital
        )
        
        logger.info("All AADS modules initialized")
    
    async def start(self) -> None:
        """Start the AADS system"""
        if self.is_running:
            logger.warning("AADS is already running")
            return
        
        self.started_at = datetime.now()
        self.is_running = True
        
        logger.info("=" * 60)
        logger.info("AADS - Autonomous Alpha Discovery System")
        logger.info("Level 6 Financial AI Infrastructure")
        logger.info("=" * 60)
        logger.info(f"Mode: {self.config.mode.value}")
        logger.info(f"Initial Capital: ${self.config.initial_capital:,.2f}")
        logger.info(f"Max Position: {self.config.max_position_pct:.1%}")
        logger.info(f"Circuit Breaker: {self.config.max_drawdown_pct:.1%} drawdown")
        logger.info("=" * 60)
        
        # Start based on mode
        if self.config.mode == AADSMode.DISCOVERY:
            await self._run_discovery_mode()
        elif self.config.mode == AADSMode.PAPER_TRADING:
            await self._run_paper_trading_mode()
        elif self.config.mode == AADSMode.LIVE_TRADING:
            await self._run_live_trading_mode()
        elif self.config.mode == AADSMode.BACKTEST:
            await self._run_backtest_mode()
        elif self.config.mode == AADSMode.RESEARCH:
            await self._run_research_mode()
    
    async def stop(self) -> None:
        """Stop the AADS system"""
        logger.info("Stopping AADS...")
        self.is_running = False
        
        # Save state
        self._save_state()
        
        logger.info("AADS stopped")
    
    async def _run_discovery_mode(self) -> None:
        """Run in full autonomous discovery mode"""
        logger.info("Starting autonomous discovery mode...")
        
        # Initialize evolution population
        self.evolution_engine.initialize_population()
        
        # Run continuous discovery loop
        await self.discovery_loop.run_continuous_loop()
    
    async def _run_paper_trading_mode(self) -> None:
        """Run in paper trading mode (simulated execution)"""
        logger.info("Starting paper trading mode...")
        
        # Run discovery with simulated execution
        iteration = 0
        while self.is_running:
            try:
                # Run one iteration
                await self.discovery_loop._run_iteration()
                
                iteration += 1
                
                # Log progress
                if iteration % 10 == 0:
                    status = self.discovery_loop.get_loop_status()
                    logger.info(f"Iteration {iteration}: "
                               f"Deployed={status['deployed_count']}, "
                               f"PnL=${sum(d.live_pnl for d in self.discovery_loop.deployed_discoveries.values()):,.2f}")
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Paper trading iteration failed: {e}")
                await asyncio.sleep(1)
    
    async def _run_live_trading_mode(self) -> None:
        """Run in live trading mode (real execution)"""
        if not self.config.enable_live_execution:
            logger.error("Live execution not enabled in config")
            return
        
        logger.warning("=" * 60)
        logger.warning("LIVE TRADING MODE - REAL MONEY AT RISK")
        logger.warning("=" * 60)
        
        # Additional safety checks for live trading
        await self._verify_live_trading_safety()
        
        # Run with real execution
        await self.discovery_loop.run_continuous_loop()
    
    async def _run_backtest_mode(self) -> None:
        """Run in backtest mode"""
        logger.info("Starting backtest mode...")
        
        # Run evolution for specified generations
        best_genome = self.evolution_engine.evolve(
            generations=self.config.max_generations
        )
        
        if best_genome:
            logger.info(f"Best genome found: {best_genome.genome_id[:8]}")
            logger.info(f"Fitness: {best_genome.fitness_score:.4f}")
            logger.info(f"Sharpe: {best_genome.sharpe_ratio:.2f}")
    
    async def _run_research_mode(self) -> None:
        """Run in research-only mode"""
        logger.info("Starting research mode...")
        
        # Generate hypotheses without trading
        while self.is_running:
            # Run research agent
            context = {'asset': 'SPY', 'market_state': {}}
            output = self.agents['research'].execute(context)
            
            logger.info(f"Research hypothesis: {output.data.get('hypothesis', {}).get('thesis', 'N/A')[:100]}")
            
            await asyncio.sleep(5)
    
    async def _verify_live_trading_safety(self) -> None:
        """Verify all safety checks before live trading"""
        checks = []
        
        # Check 1: Risk limits configured
        checks.append(('risk_limits', self.config.max_position_pct <= 0.02))
        
        # Check 2: Circuit breaker configured
        checks.append(('circuit_breaker', self.config.max_drawdown_pct <= 0.10))
        
        # Check 3: Audit enabled
        checks.append(('audit_enabled', self.config.audit_all_decisions))
        
        # Check 4: All agents operational
        all_agents_ok = all(
            agent.status.value != 'error'
            for agent in self.agents.values()
        )
        checks.append(('agents_operational', all_agents_ok))
        
        # Verify all checks pass
        failed = [name for name, passed in checks if not passed]
        
        if failed:
            raise RuntimeError(f"Live trading safety checks failed: {failed}")
        
        logger.info("All live trading safety checks passed")
    
    def _save_state(self) -> None:
        """Save current state to disk"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'mode': self.config.mode.value,
                'initial_capital': self.config.initial_capital
            },
            'evolution': self.evolution_engine.get_evolution_report(),
            'discovery_loop': self.discovery_loop.get_loop_status(),
            'swarm': self.swarm.get_swarm_stats(),
            'decision_engine': self.decision_engine.get_statistics()
        }
        
        filepath = self.save_dir / f"state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        logger.info(f"State saved to {filepath}")
    
    # ========================================================================
    # Public API Methods
    # ========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'is_running': self.is_running,
            'mode': self.config.mode.value,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'uptime_seconds': (datetime.now() - self.started_at).total_seconds() if self.started_at else 0,
            'discovery_loop': self.discovery_loop.get_loop_status(),
            'evolution': {
                'generation': self.evolution_engine.generation,
                'population_size': len(self.evolution_engine.population),
                'deployed_strategies': len(self.evolution_engine.deployed_genomes)
            },
            'swarm': self.swarm.get_swarm_stats(),
            'agents': {name: agent.get_stats() for name, agent in self.agents.items()}
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        return {
            'discovery_loop': self.discovery_loop.get_performance_report(),
            'evolution': self.evolution_engine.get_evolution_report(),
            'decision_engine': self.decision_engine.get_statistics(),
            'self_improvement': self.self_improvement.get_component_health_report()
        }
    
    def get_deployed_strategies(self) -> List[Dict[str, Any]]:
        """Get all deployed strategies"""
        strategies = []
        
        for genome in self.evolution_engine.get_deployed_strategies():
            strategies.append({
                'genome_id': genome.genome_id,
                'generation': genome.generation,
                'fitness_score': genome.fitness_score,
                'sharpe_ratio': genome.sharpe_ratio,
                'capital_allocation': genome.capital_allocation,
                'status': genome.status.value
            })
        
        return strategies
    
    def generate_decision_brief(self, asset: str, current_price: float) -> DecisionBrief:
        """Generate a decision brief for an asset"""
        # Run full agent pipeline
        context = {
            'asset': asset,
            'current_price': current_price,
            'market_state': {}
        }
        
        # Research
        research_output = self.agents['research'].execute(context)
        
        # Wargame
        bull_output = self.agents['bull'].execute({
            'hypothesis': research_output.data,
            'asset': asset,
            'current_price': current_price
        })
        
        bear_output = self.agents['bear'].execute({
            'bull_case': bull_output.data,
            'asset': asset,
            'current_price': current_price
        })
        
        wargame = self.decision_engine.run_wargame(bull_output.data, bear_output.data)
        
        # Simulation
        sim_output = self.agents['simulation'].execute({
            'asset': asset,
            'position_size': 0.01,
            'current_price': current_price
        })
        
        simulation = self.decision_engine.synthesize_simulation_results(
            sim_output.data.get('simulations', {})
        )
        
        # Swarm
        swarm_signal = self.swarm.get_consensus(asset, context['market_state'])
        
        # Risk
        risk_output = self.agents['risk'].execute({
            'trade': {'position_size': 0.01, 'sector': 'Unknown'},
            'portfolio': {},
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
            backtest_results={'sharpe_ratio': 1.5, 'max_drawdown': 0.10, 'win_rate': 0.55},
            genome_info={'genome_id': '', 'generation': 0, 'fitness_score': 0},
            risk_decision=risk_output.data
        )
        
        return brief
    
    def run_causal_analysis(self, variable: str, value: float, observe: List[str]) -> Dict[str, Any]:
        """Run causal intervention analysis"""
        result = self.causal_model.intervene(variable, value, observe)
        return result.to_dict()
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze an image for financial signals"""
        signal = self.vision_pipeline.analyze(image_path)
        return signal.to_dict()
    
    def discover_tools(self, task_description: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Discover relevant tools for a task"""
        tools = self.tool_registry.discover(task_description, top_k)
        return [tool.to_dict() for tool in tools]
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool from the registry"""
        result = self.tool_registry.execute(tool_name, **kwargs)
        return {
            'success': result.success,
            'data': result.data,
            'error': result.error,
            'execution_time_ms': result.execution_time_ms
        }
    
    def run_self_improvement_cycle(self) -> Dict[str, Any]:
        """Manually trigger a self-improvement cycle"""
        cycle = self.self_improvement.run_weekly_improvement_cycle()
        
        if cycle:
            return cycle.to_dict()
        else:
            return {'status': 'no_improvement_needed'}
    
    def get_component_health(self) -> Dict[str, Any]:
        """Get health status of all components"""
        return self.self_improvement.get_component_health_report()


# ============================================================================
# Convenience Functions
# ============================================================================

def create_aads(
    mode: str = "paper_trading",
    initial_capital: float = 1_000_000.0,
    **kwargs
) -> AADSOrchestrator:
    """
    Create an AADS instance with simplified configuration.
    
    Args:
        mode: Operating mode ("discovery", "paper_trading", "live_trading", "backtest", "research")
        initial_capital: Starting capital
        **kwargs: Additional configuration options
    
    Returns:
        Configured AADSOrchestrator instance
    """
    config = AADSConfig(
        mode=AADSMode(mode),
        initial_capital=initial_capital,
        **kwargs
    )
    
    return AADSOrchestrator(config)


async def run_aads_demo(iterations: int = 100) -> Dict[str, Any]:
    """
    Run a demo of the AADS system.
    
    Args:
        iterations: Number of discovery loop iterations
    
    Returns:
        Performance report
    """
    aads = create_aads(mode="paper_trading", initial_capital=1_000_000.0)
    
    # Run for specified iterations
    for i in range(iterations):
        await aads.discovery_loop._run_iteration()
        
        if i % 10 == 0:
            status = aads.get_status()
            logger.info(f"Demo iteration {i}: {status['discovery_loop']['deployed_count']} strategies deployed")
    
    return aads.get_performance_report()
