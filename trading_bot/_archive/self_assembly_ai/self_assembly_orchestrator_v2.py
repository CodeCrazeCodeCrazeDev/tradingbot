"""
Self-Assembly AI Orchestrator V2 - Ultimate Self-Assembling System
===================================================================

The master orchestrator that coordinates all self-assembly systems:
- Code Genetics (DNA-like strategy evolution)
- Swarm Intelligence (collective optimization)
- Neural Architecture Search (auto-designing networks)
- Emergent Behavior (complex patterns from simple rules)
- Strategy Factory (self-replicating strategies)
- Component Auto-Wiring (self-configuring system)

This creates a truly autonomous AI that can:
1. Discover and wire its own components
2. Evolve its own trading strategies
3. Design its own neural architectures
4. Exhibit emergent intelligent behaviors
5. Self-replicate successful patterns
6. Optimize through collective intelligence
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import random
import json

from .code_genetics import CodeGenetics, Chromosome, create_code_genetics
from .swarm_intelligence import SwarmIntelligence, Position, create_swarm_intelligence
from .neural_architecture_search import NeuralArchitectureSearch, Architecture, create_nas_engine
from .emergent_behavior import EmergentBehaviorEngine, create_emergent_behavior_engine
from .strategy_factory import StrategyFactory, Strategy, create_strategy_factory
from .component_autowiring import AutoWiringContainer, create_autowiring_container

logger = logging.getLogger(__name__)


class AssemblyMode(Enum):
    """Modes of self-assembly operation"""
    BOOTSTRAP = "bootstrap"           # Initial assembly
    EVOLUTION = "evolution"           # Continuous evolution
    OPTIMIZATION = "optimization"     # Parameter optimization
    EXPLORATION = "exploration"       # Exploring new strategies
    EXPLOITATION = "exploitation"     # Exploiting known strategies
    MAINTENANCE = "maintenance"       # Self-maintenance
    EMERGENCY = "emergency"           # Emergency mode


class SystemHealth(Enum):
    """Overall system health status"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class AssemblyState:
    """Current state of the self-assembly system"""
    mode: AssemblyMode = AssemblyMode.BOOTSTRAP
    health: SystemHealth = SystemHealth.GOOD
    
    # Component states
    genetics_active: bool = False
    swarm_active: bool = False
    nas_active: bool = False
    emergent_active: bool = False
    factory_active: bool = False
    autowiring_active: bool = False
    
    # Metrics
    total_evolutions: int = 0
    total_optimizations: int = 0
    total_strategies_created: int = 0
    total_architectures_searched: int = 0
    
    # Performance
    best_fitness: float = 0.0
    current_fitness: float = 0.0
    fitness_trend: List[float] = field(default_factory=list)
    
    # Timestamps
    started_at: Optional[datetime] = None
    last_evolution: Optional[datetime] = None
    last_optimization: Optional[datetime] = None


@dataclass
class AssemblyConfig:
    """Configuration for self-assembly"""
    # Evolution settings
    evolution_interval_seconds: int = 300
    optimization_interval_seconds: int = 600
    
    # Population settings
    genetics_population_size: int = 50
    swarm_population_size: int = 30
    strategy_population_size: int = 20
    
    # Search settings
    nas_max_generations: int = 30
    nas_early_stopping: int = 10
    
    # Safety settings
    max_risk_per_trade: float = 0.02
    max_drawdown: float = 0.15
    min_fitness_threshold: float = 0.3
    
    # Auto-wiring settings
    auto_scan_packages: List[str] = field(default_factory=lambda: ["trading_bot"])
    hot_swap_enabled: bool = True


class SelfAssemblyOrchestratorV2:
    """
    Self-Assembly AI Orchestrator V2
    
    The ultimate self-assembling trading AI that can:
    - Automatically discover and wire components
    - Evolve trading strategies through genetic algorithms
    - Optimize parameters through swarm intelligence
    - Design neural architectures automatically
    - Generate emergent trading behaviors
    - Self-replicate successful strategies
    
    This is a living, breathing AI system that continuously
    improves itself without human intervention.
    """
    
    def __init__(self, workspace_path: str = ".", config: Optional[AssemblyConfig] = None):
        self.workspace_path = workspace_path
        self.config = config or AssemblyConfig()
        
        # State
        self.state = AssemblyState()
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        # Initialize subsystems (lazy)
        self._genetics: Optional[CodeGenetics] = None
        self._swarm: Optional[SwarmIntelligence] = None
        self._nas: Optional[NeuralArchitectureSearch] = None
        self._emergent: Optional[EmergentBehaviorEngine] = None
        self._factory: Optional[StrategyFactory] = None
        self._container: Optional[AutoWiringContainer] = None
        
        # Callbacks
        self.on_evolution_complete: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_strategy_created: Optional[Callable[[Strategy], None]] = None
        self.on_architecture_found: Optional[Callable[[Architecture], None]] = None
        
        # Fitness function (can be customized)
        self._fitness_func: Optional[Callable] = None
        
        logger.info("SelfAssemblyOrchestratorV2 initialized")
    
    # ==================== SUBSYSTEM INITIALIZATION ====================
    
    def _init_genetics(self) -> CodeGenetics:
        """Initialize code genetics system"""
        if self._genetics is None:
            self._genetics = create_code_genetics({
                'population_size': self.config.genetics_population_size,
                'mutation_rate': 0.1,
                'crossover_rate': 0.7,
            })
            self.state.genetics_active = True
            logger.info("Code Genetics initialized")
        return self._genetics
    
    def _init_swarm(self) -> SwarmIntelligence:
        """Initialize swarm intelligence system"""
        if self._swarm is None:
            # Define parameter bounds for optimization
            bounds = [
                (5, 50),    # RSI period
                (60, 90),   # RSI overbought
                (10, 40),   # RSI oversold
                (5, 50),    # MA fast
                (20, 200),  # MA slow
                (5, 30),    # ATR period
                (1.0, 5.0), # ATR multiplier
                (0.005, 0.05),  # Risk per trade
                (1, 10),    # Max positions
                (0.05, 0.30),   # Max drawdown
            ]
            
            self._swarm = create_swarm_intelligence(
                swarm_type="hybrid",
                dimensions=len(bounds),
                bounds=bounds,
                config={'max_iterations': 500}
            )
            self.state.swarm_active = True
            logger.info("Swarm Intelligence initialized")
        return self._swarm
    
    def _init_nas(self) -> NeuralArchitectureSearch:
        """Initialize neural architecture search"""
        if self._nas is None:
            self._nas = create_nas_engine(
                input_shape=(100, 10),  # 100 timesteps, 10 features
                output_shape=(3,),      # Buy, Hold, Sell
                config={
                    'population_size': 20,
                    'elite_size': 3,
                    'mutation_rate': 0.3,
                }
            )
            self.state.nas_active = True
            logger.info("Neural Architecture Search initialized")
        return self._nas
    
    def _init_emergent(self) -> EmergentBehaviorEngine:
        """Initialize emergent behavior engine"""
        if self._emergent is None:
            self._emergent = create_emergent_behavior_engine({
                'ca_width': 30,
                'ca_height': 30,
                'som_width': 10,
                'som_height': 10,
            })
            self.state.emergent_active = True
            logger.info("Emergent Behavior Engine initialized")
        return self._emergent
    
    def _init_factory(self) -> StrategyFactory:
        """Initialize strategy factory"""
        if self._factory is None:
            self._factory = create_strategy_factory({
                'max_population': self.config.strategy_population_size,
                'min_population': 5,
                'mutation_rate': 0.1,
            })
            self.state.factory_active = True
            logger.info("Strategy Factory initialized")
        return self._factory
    
    def _init_container(self) -> AutoWiringContainer:
        """Initialize auto-wiring container"""
        if self._container is None:
            self._container = create_autowiring_container(
                base_path=self.workspace_path,
                auto_scan=False,  # Manual control
            )
            self.state.autowiring_active = True
            logger.info("Auto-Wiring Container initialized")
        return self._container
    
    # ==================== MAIN OPERATIONS ====================
    
    async def start(self) -> None:
        """Start the self-assembly system"""
        if self._running:
            logger.warning("System already running")
            return
        
        self._running = True
        self.state.started_at = datetime.utcnow()
        self.state.mode = AssemblyMode.BOOTSTRAP
        
        logger.info("Starting Self-Assembly AI System...")
        
        # Bootstrap phase - initialize all subsystems
        await self._bootstrap()
        
        # Start background loops
        self._tasks.append(asyncio.create_task(self._evolution_loop()))
        self._tasks.append(asyncio.create_task(self._optimization_loop()))
        self._tasks.append(asyncio.create_task(self._emergent_loop()))
        self._tasks.append(asyncio.create_task(self._health_monitor_loop()))
        
        self.state.mode = AssemblyMode.EVOLUTION
        logger.info("Self-Assembly AI System started")
    
    async def stop(self) -> None:
        """Stop the self-assembly system"""
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        
        # Shutdown container
        if self._container:
            await self._container.shutdown()
        
        logger.info("Self-Assembly AI System stopped")
    
    async def _bootstrap(self) -> None:
        """Bootstrap phase - initialize all systems"""
        logger.info("Bootstrap phase started...")
        
        # Initialize all subsystems
        self._init_genetics()
        self._init_swarm()
        self._init_nas()
        self._init_emergent()
        self._init_factory()
        self._init_container()
        
        # Scan and register components
        container = self._init_container()
        for package in self.config.auto_scan_packages:
            try:
                count = container.scan_and_register(package)
                logger.info(f"Registered {count} components from {package}")
            except Exception as e:
                logger.warning(f"Could not scan {package}: {e}")
        
        # Initialize container
        try:
            await container.initialize()
        except Exception as e:
            logger.warning(f"Container initialization incomplete: {e}")
        
        logger.info("Bootstrap phase completed")
    
    # ==================== EVOLUTION LOOP ====================
    
    async def _evolution_loop(self) -> None:
        """Background loop for genetic evolution"""
        while self._running:
            try:
                await asyncio.sleep(self.config.evolution_interval_seconds)
                
                if self.state.mode == AssemblyMode.EMERGENCY:
                    continue
                
                logger.info("Starting evolution cycle...")
                
                # Evolve genetic strategies
                genetics = self._init_genetics()
                
                # Define fitness function
                def fitness_func(chromosome: Chromosome) -> float:
                    if self._fitness_func:
                        return self._fitness_func(chromosome)
                    return self._default_chromosome_fitness(chromosome)
                
                # Evolve one generation
                report = genetics.evolve_generation(fitness_func)
                
                self.state.total_evolutions += 1
                self.state.last_evolution = datetime.utcnow()
                
                # Update fitness tracking
                if report['best_fitness'] > self.state.best_fitness:
                    self.state.best_fitness = report['best_fitness']
                
                self.state.current_fitness = report['best_fitness']
                self.state.fitness_trend.append(report['best_fitness'])
                if len(self.state.fitness_trend) > 100:
                    self.state.fitness_trend.pop(0)
                
                # Evolve strategy factory
                factory = self._init_factory()
                factory.natural_selection()
                
                self.state.total_strategies_created = factory.total_created
                
                # Callback
                if self.on_evolution_complete:
                    self.on_evolution_complete(report)
                
                logger.info(f"Evolution cycle complete. Best fitness: {report['best_fitness']:.4f}")
                
            except Exception as e:
                logger.error(f"Error in evolution loop: {e}")
    
    async def _optimization_loop(self) -> None:
        """Background loop for swarm optimization"""
        while self._running:
            try:
                await asyncio.sleep(self.config.optimization_interval_seconds)
                
                if self.state.mode == AssemblyMode.EMERGENCY:
                    continue
                
                logger.info("Starting optimization cycle...")
                
                swarm = self._init_swarm()
                
                # Define fitness function for position
                def position_fitness(position: Position) -> float:
                    if self._fitness_func:
                        # Convert position to chromosome-like structure
                        return self._fitness_func(position)
                    return self._default_position_fitness(position)
                
                # Run optimization steps
                for _ in range(10):  # 10 steps per cycle
                    result = swarm.step(position_fitness)
                
                self.state.total_optimizations += 1
                self.state.last_optimization = datetime.utcnow()
                
                logger.info(f"Optimization cycle complete. Best: {result['global_best_fitness']:.4f}")
                
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
    
    async def _emergent_loop(self) -> None:
        """Background loop for emergent behavior"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Every minute
                
                emergent = self._init_emergent()
                
                # Run emergent systems
                for _ in range(10):
                    result = emergent.step()
                
                # Get emergent signal
                signal = emergent.get_emergent_signal()
                
                # Use signal to influence other systems
                if signal['confidence'] > 0.6:
                    # Adjust evolution based on emergent patterns
                    if signal['direction'] == 'bullish':
                        self.state.mode = AssemblyMode.EXPLOITATION
                    elif signal['direction'] == 'bearish':
                        self.state.mode = AssemblyMode.MAINTENANCE
                    elif signal['direction'] == 'avoid':
                        self.state.mode = AssemblyMode.MAINTENANCE
                
            except Exception as e:
                logger.error(f"Error in emergent loop: {e}")
    
    async def _health_monitor_loop(self) -> None:
        """Background loop for health monitoring"""
        while self._running:
            try:
                await asyncio.sleep(30)  # Every 30 seconds
                
                # Calculate health
                health_score = self._calculate_health_score()
                
                if health_score >= 0.8:
                    self.state.health = SystemHealth.EXCELLENT
                elif health_score >= 0.6:
                    self.state.health = SystemHealth.GOOD
                elif health_score >= 0.4:
                    self.state.health = SystemHealth.FAIR
                elif health_score >= 0.2:
                    self.state.health = SystemHealth.POOR
                else:
                    self.state.health = SystemHealth.CRITICAL
                    self.state.mode = AssemblyMode.EMERGENCY
                
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
    
    # ==================== FITNESS FUNCTIONS ====================
    
    def _default_chromosome_fitness(self, chromosome: Chromosome) -> float:
        """Default fitness function for chromosomes"""
        config = chromosome.express()
        
        fitness = 0.5  # Base fitness
        
        # Reward reasonable parameters
        if 'rsi_period' in config:
            if 10 <= config['rsi_period'] <= 20:
                fitness += 0.1
        
        if 'risk' in config:
            risk_per_trade = config['risk'].get('risk_per_trade', 0.02)
            if 0.01 <= risk_per_trade <= 0.03:
                fitness += 0.1
        
        if 'exits' in config:
            tp = config['exits'].get('take_profit_atr', 2)
            sl = config['exits'].get('stop_loss_atr', 1)
            if tp > sl:
                fitness += 0.1
        
        # Add some randomness to simulate backtesting
        fitness += random.gauss(0, 0.1)
        
        return max(0, min(1, fitness))
    
    def _default_position_fitness(self, position: Position) -> float:
        """Default fitness function for swarm positions"""
        dims = position.dimensions
        
        fitness = 0.5
        
        # Evaluate parameter combinations
        if len(dims) >= 10:
            rsi_period = dims[0]
            rsi_ob = dims[1]
            rsi_os = dims[2]
            ma_fast = dims[3]
            ma_slow = dims[4]
            
            # RSI parameters
            if 10 <= rsi_period <= 20:
                fitness += 0.05
            if rsi_ob > rsi_os + 30:
                fitness += 0.05
            
            # MA parameters
            if ma_fast < ma_slow:
                fitness += 0.1
            
            # Risk parameters
            risk = dims[7] if len(dims) > 7 else 0.02
            if 0.01 <= risk <= 0.03:
                fitness += 0.1
        
        fitness += random.gauss(0, 0.05)
        
        return max(0, min(1, fitness))
    
    def _calculate_health_score(self) -> float:
        """Calculate overall system health score"""
        score = 0.0
        checks = 0
        
        # Check subsystem health
        if self.state.genetics_active:
            score += 1.0
            checks += 1
        
        if self.state.swarm_active:
            score += 1.0
            checks += 1
        
        if self.state.factory_active:
            factory = self._init_factory()
            if len(factory.strategies) > 0:
                score += 1.0
            checks += 1
        
        if self.state.emergent_active:
            score += 1.0
            checks += 1
        
        # Check fitness trend
        if len(self.state.fitness_trend) >= 5:
            recent = self.state.fitness_trend[-5:]
            if recent[-1] >= recent[0]:  # Improving
                score += 1.0
            checks += 1
        
        return score / checks if checks > 0 else 0.5
    
    # ==================== PUBLIC API ====================
    
    def set_fitness_function(self, func: Callable) -> None:
        """Set custom fitness function"""
        self._fitness_func = func
    
    async def search_architecture(self, fitness_func: Optional[Callable] = None) -> Optional[Architecture]:
        """Search for optimal neural architecture"""
        nas = self._init_nas()
        
        if fitness_func is None:
            fitness_func = lambda arch: random.uniform(0.3, 0.9)  # Placeholder
        
        best_arch = await nas.search(
            fitness_func,
            max_generations=self.config.nas_max_generations,
            early_stopping_patience=self.config.nas_early_stopping,
        )
        
        self.state.total_architectures_searched += nas.evaluations
        
        if self.on_architecture_found and best_arch:
            self.on_architecture_found(best_arch)
        
        return best_arch
    
    def create_strategy(self, blueprint_id: str) -> Strategy:
        """Create a new strategy from blueprint"""
        factory = self._init_factory()
        strategy = factory.create_strategy(blueprint_id)
        
        if self.on_strategy_created:
            self.on_strategy_created(strategy)
        
        return strategy
    
    def get_best_strategy(self) -> Optional[Strategy]:
        """Get the best performing strategy"""
        factory = self._init_factory()
        return factory.get_best_strategy()
    
    def get_best_chromosome(self) -> Optional[Chromosome]:
        """Get the best evolved chromosome"""
        genetics = self._init_genetics()
        return genetics.gene_pool.get_best_chromosome()
    
    def get_swarm_best(self) -> Optional[Position]:
        """Get the best position from swarm optimization"""
        swarm = self._init_swarm()
        return swarm.get_best_solution()
    
    def get_emergent_signal(self) -> Dict[str, Any]:
        """Get current emergent trading signal"""
        emergent = self._init_emergent()
        return emergent.get_emergent_signal()
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive system report"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'state': {
                'mode': self.state.mode.value,
                'health': self.state.health.value,
                'running': self._running,
                'started_at': self.state.started_at.isoformat() if self.state.started_at else None,
            },
            'metrics': {
                'total_evolutions': self.state.total_evolutions,
                'total_optimizations': self.state.total_optimizations,
                'total_strategies_created': self.state.total_strategies_created,
                'total_architectures_searched': self.state.total_architectures_searched,
                'best_fitness': self.state.best_fitness,
                'current_fitness': self.state.current_fitness,
            },
            'subsystems': {
                'genetics_active': self.state.genetics_active,
                'swarm_active': self.state.swarm_active,
                'nas_active': self.state.nas_active,
                'emergent_active': self.state.emergent_active,
                'factory_active': self.state.factory_active,
                'autowiring_active': self.state.autowiring_active,
            },
        }
        
        # Add subsystem reports
        if self._genetics:
            report['genetics'] = self._genetics.gene_pool.get_report()
        
        if self._swarm:
            report['swarm'] = self._swarm.get_report()
        
        if self._nas:
            report['nas'] = self._nas.get_report()
        
        if self._emergent:
            report['emergent'] = self._emergent.get_report()
        
        if self._factory:
            report['factory'] = self._factory.get_report()
        
        if self._container:
            report['container'] = self._container.get_status()
        
        return report
    
    def human_override(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Human override - ALWAYS works"""
        params = params or {}
        result = {'action': action, 'success': True, 'message': ''}
        
        if action == "STOP":
            asyncio.create_task(self.stop())
            result['message'] = "System stopping"
        
        elif action == "SET_MODE":
            mode = params.get('mode', 'evolution')
            try:
                self.state.mode = AssemblyMode(mode)
                result['message'] = f"Mode set to {mode}"
            except ValueError:
                result['success'] = False
                result['message'] = f"Unknown mode: {mode}"
        
        elif action == "FORCE_EVOLUTION":
            genetics = self._init_genetics()
            def fitness_func(c): return self._default_chromosome_fitness(c)
            report = genetics.evolve_generation(fitness_func)
            result['message'] = f"Evolution forced. Best fitness: {report['best_fitness']:.4f}"
        
        elif action == "CREATE_STRATEGY":
            blueprint = params.get('blueprint', 'trend_following')
            strategy = self.create_strategy(blueprint)
            result['message'] = f"Created strategy: {strategy.strategy_id}"
            result['strategy_id'] = strategy.strategy_id
        
        elif action == "GET_STATUS":
            result['status'] = self.get_comprehensive_report()
            result['message'] = "Status retrieved"
        
        else:
            result['success'] = False
            result['message'] = f"Unknown action: {action}"
        
        logger.info(f"Human override: {action} - {result['message']}")
        return result


# Factory functions
def create_self_assembly_v2(
    workspace_path: str = ".",
    config: Optional[AssemblyConfig] = None
) -> SelfAssemblyOrchestratorV2:
    """Create self-assembly orchestrator V2"""
    return SelfAssemblyOrchestratorV2(workspace_path, config)


async def run_self_assembly_v2(
    workspace_path: str = ".",
    config: Optional[AssemblyConfig] = None,
    duration_seconds: Optional[float] = None
) -> None:
    """Run self-assembly system"""
    orchestrator = create_self_assembly_v2(workspace_path, config)
    await orchestrator.start()
    
    try:
        if duration_seconds:
            await asyncio.sleep(duration_seconds)
        else:
            while True:
                await asyncio.sleep(3600)
    finally:
        await orchestrator.stop()
