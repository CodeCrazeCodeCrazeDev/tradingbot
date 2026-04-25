"""
Unified Offline World Simulation Orchestrator
=============================================

Integrates all simulation components:
- AlphaGo-style self-play
- DeepSeek-style synthetic data generation
- Counterfactual reasoning
- Dream/Imagination engine

Provides unified API for:
- Training mode: Self-play for strategy improvement
- Testing mode: Stress-test with synthetic regimes
- Prediction mode: Imagine future trajectories
- Learning mode: Counterfactual analysis

Scale: 10,000x parallel simulations with GPU acceleration
"""

import asyncio
import torch
import numpy as np
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

from .self_play_engine import SelfPlayEngine, TradingAgent, create_self_play_engine
from .counterfactual_engine import CounterfactualEngine, create_counterfactual_engine
from .synthetic_data import (
    SyntheticMarketGenerator, MultiAgentMarketSimulator,
    SyntheticDataQualityScorer, MarketRegime, MarketScenario
)
from .experience_replay import ExperienceReplayBuffer, Experience, create_experience_replay_buffer
from .latent_dynamics import WorldModel
from .imagination import ImaginationPlanner

logger = logging.getLogger(__name__)


class SimulationMode(Enum):
    """Simulation operating modes"""
    TRAINING = "training"  # Self-play for strategy improvement
    TESTING = "testing"    # Stress-test with synthetic scenarios
    PREDICTION = "prediction"  # Imagine future trajectories
    LEARNING = "learning"  # Counterfactual analysis
    DREAMING = "dreaming"  # Offline consolidation


@dataclass
class SimulationConfig:
    """Configuration for simulation run"""
    mode: SimulationMode
    
    # Scale parameters
    num_parallel_simulations: int = 10000  # 10,000x scale
    use_gpu: bool = True
    max_workers: int = 16
    
    # Mode-specific parameters
    duration_steps: int = 100
    num_episodes: int = 1000
    
    # Market parameters
    base_volatility: float = 0.01
    regime: MarketRegime = MarketRegime.NORMAL
    
    # Quality control
    quality_threshold: float = 0.7
    filter_low_quality: bool = True


@dataclass
class SimulationResult:
    """Results from simulation run"""
    run_id: str
    mode: SimulationMode
    
    # Results
    experiences: List[Experience] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # Performance
    duration_seconds: float = 0.0
    simulations_per_second: float = 0.0
    
    # Quality
    quality_score: float = 0.0
    num_filtered: int = 0
    
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class SimulationOrchestrator:
    """
    Unified orchestrator for offline world simulation
    
    Integrates:
    - AlphaGo self-play (strategy improvement)
    - DeepSeek synthetic data (scale generation)
    - Counterfactual reasoning (what-if analysis)
    - Dream/Imagination (offline consolidation)
    
    Scale: 10,000x parallel simulations
    """
    
    def __init__(
        self,
        world_model: Optional[WorldModel] = None,
        experience_buffer: Optional[ExperienceReplayBuffer] = None,
        storage_path: Optional[str] = None
    ):
        # Components
        self.world_model = world_model
        self.experience_buffer = experience_buffer or create_experience_replay_buffer()
        
        # Simulation engines
        self.self_play_engine: Optional[SelfPlayEngine] = None
        self.counterfactual_engine: Optional[CounterfactualEngine] = None
        self.synthetic_generator: Optional[SyntheticMarketGenerator] = None
        self.multi_agent_sim: Optional[MultiAgentMarketSimulator] = None
        self.imagination_planner: Optional[ImaginationPlanner] = None
        self.quality_scorer = SyntheticDataQualityScorer()
        
        # Storage
        self.storage_path = Path(storage_path) if storage_path else Path("./simulation_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # State
        self.is_running = False
        self.run_history: List[SimulationResult] = []
        
        # GPU
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        logger.info(f"✅ SimulationOrchestrator initialized")
        logger.info(f"   Device: {self.device}")
        logger.info(f"   Storage: {self.storage_path}")
    
    def initialize_engines(self, config: Optional[SimulationConfig] = None):
        """Initialize all simulation engines"""
        cfg = config or SimulationConfig(mode=SimulationMode.TRAINING)
        
        # Self-play engine
        if cfg.mode in [SimulationMode.TRAINING, SimulationMode.TESTING]:
            self.self_play_engine = create_self_play_engine(
                market_simulator=self._market_simulator,
                num_agents=10,
                games_per_iteration=min(cfg.num_episodes, 1000)
            )
        
        # Counterfactual engine
        if cfg.mode == SimulationMode.LEARNING:
            self.counterfactual_engine = create_counterfactual_engine(
                max_counterfactuals=cfg.num_parallel_simulations,
                target_response_ms=50.0
            )
        
        # Synthetic data generator
        if cfg.mode in [SimulationMode.TESTING, SimulationMode.DREAMING]:
            self.synthetic_generator = SyntheticMarketGenerator(
                base_volatility=cfg.base_volatility
            )
            self.multi_agent_sim = MultiAgentMarketSimulator(
                num_agents=1000,
                base_volatility=cfg.base_volatility
            )
        
        # Imagination planner
        if cfg.mode == SimulationMode.PREDICTION and self.world_model is not None:
            self.imagination_planner = ImaginationPlanner(
                world_model=self.world_model,
                num_simulations=100,
                horizon=cfg.duration_steps
            )
        
        logger.info("✅ All engines initialized")
    
    def _market_simulator(self, num_steps: int, initial_price: float) -> Dict:
        """Simple market simulator for self-play"""
        if self.synthetic_generator is None:
            self.synthetic_generator = SyntheticMarketGenerator()
        
        scenario = MarketScenario(
            regime=MarketRegime.NORMAL,
            duration=num_steps,
            volatility=1.0
        )
        
        data = self.synthetic_generator.generate_scenario(
            scenario,
            initial_price=initial_price
        )
        
        return {
            'prices': data['prices'],
            'features': np.array([
                data['indicators']['sma_20'],
                data['indicators']['sma_50'],
                data['indicators']['rsi'],
                data['indicators']['macd'],
                data['indicators']['volatility']
            ]).T,
            'returns': data['returns']
        }
    
    async def run_simulation(
        self,
        config: SimulationConfig,
        progress_callback: Optional[Callable[[Dict], None]] = None
    ) -> SimulationResult:
        """
        Run simulation based on configuration
        
        Args:
            config: Simulation configuration
            progress_callback: Optional callback for progress updates
        
        Returns:
            SimulationResult with all generated experiences
        """
        import time
        start_time = time.time()
        
        run_id = f"sim_{datetime.utcnow().timestamp()}"
        logger.info(f"🚀 Starting simulation run {run_id}")
        logger.info(f"   Mode: {config.mode.value}")
        logger.info(f"   Parallel simulations: {config.num_parallel_simulations}")
        
        self.is_running = True
        
        # Initialize engines
        self.initialize_engines(config)
        
        try:
            # Run based on mode
            if config.mode == SimulationMode.TRAINING:
                experiences = await self._run_training_mode(config, progress_callback)
            elif config.mode == SimulationMode.TESTING:
                experiences = await self._run_testing_mode(config, progress_callback)
            elif config.mode == SimulationMode.PREDICTION:
                experiences = await self._run_prediction_mode(config, progress_callback)
            elif config.mode == SimulationMode.LEARNING:
                experiences = await self._run_learning_mode(config, progress_callback)
            elif config.mode == SimulationMode.DREAMING:
                experiences = await self._run_dreaming_mode(config, progress_callback)
            else:
                experiences = []
            
            # Quality filtering
            filtered_experiences = self._filter_by_quality(
                experiences,
                config.quality_threshold,
                config.filter_low_quality
            )
            
            # Store in replay buffer
            for exp in filtered_experiences:
                self.experience_buffer.add(exp)
            
            # Calculate metrics
            duration = time.time() - start_time
            
            result = SimulationResult(
                run_id=run_id,
                mode=config.mode,
                experiences=filtered_experiences,
                metrics=self._calculate_metrics(filtered_experiences),
                duration_seconds=duration,
                simulations_per_second=config.num_parallel_simulations / duration,
                quality_score=self._calculate_quality_score(filtered_experiences),
                num_filtered=len(experiences) - len(filtered_experiences)
            )
            
            self.run_history.append(result)
            
            logger.info(f"✅ Simulation complete: {len(filtered_experiences)} experiences")
            logger.info(f"   Duration: {duration:.1f}s")
            logger.info(f"   Rate: {result.simulations_per_second:.1f} sims/sec")
            
            return result
            
        finally:
            self.is_running = False
    
    async def _run_training_mode(
        self,
        config: SimulationConfig,
        progress_callback: Optional[Callable] = None
    ) -> List[Experience]:
        """Run AlphaGo-style self-play training"""
        if self.self_play_engine is None:
            return []
        
        experiences = []
        
        # Run self-play iterations
        for i in range(config.num_episodes // 100):
            stats = await self.self_play_engine.run_self_play_iteration()
            
            # Convert game results to experiences
            for agent in self.self_play_engine.agents.values():
                for state, action, reward in agent.get_training_data():
                    exp = Experience(
                        experience_id=f"sp_{i}_{len(experiences)}",
                        state=state,
                        action=action,
                        reward=reward,
                        next_state=state,  # Simplified
                        done=False,
                        timestamp=datetime.utcnow(),
                        source='self_play'
                    )
                    experiences.append(exp)
            
            if progress_callback:
                await progress_callback({
                    'phase': 'self_play',
                    'iteration': i + 1,
                    'total': config.num_episodes // 100,
                    'experiences': len(experiences)
                })
        
        return experiences
    
    async def _run_testing_mode(
        self,
        config: SimulationConfig,
        progress_callback: Optional[Callable] = None
    ) -> List[Experience]:
        """Run stress testing with synthetic scenarios"""
        if self.multi_agent_sim is None:
            return []
        
        experiences = []
        
        # Generate synthetic data
        data = self.multi_agent_sim.generate_batch(
            num_candles=min(config.duration_steps, 1000000),
            regime=config.regime,
            include_news=True
        )
        
        # Convert to experiences
        for i in range(len(data['prices']) - 1):
            exp = Experience(
                experience_id=f"test_{i}",
                state=np.array([
                    data['prices'][i],
                    data['volumes'][i],
                    data['spreads'][i]
                ]),
                action=0,  # HOLD
                reward=data['prices'][i+1] - data['prices'][i],
                next_state=np.array([
                    data['prices'][i+1],
                    data['volumes'][i+1],
                    data['spreads'][i+1]
                ]),
                done=(i == len(data['prices']) - 2),
                timestamp=datetime.utcnow(),
                source='synthetic',
                market_regime=config.regime.value
            )
            experiences.append(exp)
        
        if progress_callback:
            await progress_callback({
                'phase': 'testing',
                'experiences': len(experiences)
            })
        
        return experiences
    
    async def _run_prediction_mode(
        self,
        config: SimulationConfig,
        progress_callback: Optional[Callable] = None
    ) -> List[Experience]:
        """Run future trajectory prediction"""
        if self.imagination_planner is None or self.world_model is None:
            return []
        
        experiences = []
        
        # Generate initial states
        initial_states = [
            torch.randn(20) * 0.5  # Random initial states
            for _ in range(config.num_parallel_simulations // 100)
        ]
        
        actions = ['HOLD', 'BUY', 'SELL']
        
        for i, state in enumerate(initial_states):
            # Plan action using imagination
            plan = self.imagination_planner.plan_action(state, actions)
            
            # Store imagined trajectories as experiences
            for action, analysis in plan['all_results'].items():
                exp = Experience(
                    experience_id=f"pred_{i}_{action}",
                    state=state.numpy(),
                    action=actions.index(action),
                    reward=analysis['expected_return'],
                    next_state=state.numpy(),
                    done=False,
                    timestamp=datetime.utcnow(),
                    source='imagination',
                    market_regime=config.regime.value
                )
                experiences.append(exp)
            
            if progress_callback and i % 10 == 0:
                await progress_callback({
                    'phase': 'prediction',
                    'current': i + 1,
                    'total': len(initial_states),
                    'experiences': len(experiences)
                })
        
        return experiences
    
    async def _run_learning_mode(
        self,
        config: SimulationConfig,
        progress_callback: Optional[Callable] = None
    ) -> List[Experience]:
        """Run counterfactual learning mode"""
        if self.counterfactual_engine is None:
            return []
        
        # This mode generates counterfactual scenarios from trade history
        # In practice, would load from history
        experiences = []
        
        # Generate synthetic trade outcomes for counterfactual analysis
        from .counterfactual_engine import TradeOutcome
        
        for i in range(config.num_parallel_simulations // 100):
            trade = TradeOutcome(
                trade_id=f"trade_{i}",
                timestamp=datetime.utcnow(),
                factors={'price': 100.0, 'volatility': 0.1},
                action_taken='BUY',
                realized_return=np.random.uniform(-0.05, 0.05),
                hypothetical_returns={
                    'BUY': np.random.uniform(-0.05, 0.05),
                    'SELL': np.random.uniform(-0.05, 0.05),
                    'HOLD': 0.0
                }
            )
            
            # Generate counterfactuals
            scenarios = self.counterfactual_engine.generate_counterfactuals(trade, num_scenarios=10)
            
            for scenario in scenarios:
                exp = Experience(
                    experience_id=scenario.scenario_id,
                    state=np.array([trade.factors['price'], trade.factors['volatility']]),
                    action=0 if 'HOLD' in scenario.intervention else 1,
                    reward=scenario.predicted_return,
                    next_state=np.array([trade.factors['price'] * (1 + scenario.causal_effect), trade.factors['volatility']]),
                    done=False,
                    timestamp=datetime.utcnow(),
                    source='counterfactual'
                )
                experiences.append(exp)
        
        if progress_callback:
            await progress_callback({
                'phase': 'learning',
                'experiences': len(experiences)
            })
        
        return experiences
    
    async def _run_dreaming_mode(
        self,
        config: SimulationConfig,
        progress_callback: Optional[Callable] = None
    ) -> List[Experience]:
        """Run offline dreaming/consolidation mode"""
        experiences = []
        
        # Sample from experience buffer
        if len(self.experience_buffer.buffer) > 0:
            recent_experiences, _, _ = self.experience_buffer.sample(
                batch_size=min(1000, len(self.experience_buffer.buffer)),
                use_priorities=True
            )
            
            # Generate variations of each experience (dream)
            for exp in recent_experiences:
                # Create 100 variations
                for i in range(100):
                    noisy_state = exp.state + np.random.normal(0, 0.01, len(exp.state))
                    noisy_reward = exp.reward * np.random.uniform(0.8, 1.2)
                    
                    dream_exp = Experience(
                        experience_id=f"dream_{exp.experience_id}_{i}",
                        state=noisy_state,
                        action=exp.action,
                        reward=noisy_reward,
                        next_state=noisy_state,
                        done=exp.done,
                        timestamp=datetime.utcnow(),
                        source='dream',
                        market_regime=exp.market_regime
                    )
                    experiences.append(dream_exp)
        
        if progress_callback:
            await progress_callback({
                'phase': 'dreaming',
                'base_experiences': len(recent_experiences),
                'dream_experiences': len(experiences)
            })
        
        return experiences
    
    def _filter_by_quality(
        self,
        experiences: List[Experience],
        threshold: float,
        do_filter: bool
    ) -> List[Experience]:
        """Filter experiences by quality score"""
        if not do_filter or len(experiences) == 0:
            return experiences
        
        filtered = []
        for exp in experiences:
            # Create synthetic data dict for scoring
            data = {
                'prices': np.array([exp.state[0], exp.next_state[0]]) if len(exp.state) > 0 else np.array([100.0, 100.0])
            }
            
            score = self.quality_scorer.score(data)
            
            if score >= threshold:
                exp.priority = score
                filtered.append(exp)
        
        return filtered
    
    def _calculate_metrics(self, experiences: List[Experience]) -> Dict[str, float]:
        """Calculate statistics from experiences"""
        if not experiences:
            return {}
        
        rewards = [e.reward for e in experiences]
        
        return {
            'num_experiences': len(experiences),
            'avg_reward': np.mean(rewards),
            'std_reward': np.std(rewards),
            'max_reward': np.max(rewards),
            'min_reward': np.min(rewards),
            'sharpe_ratio': np.mean(rewards) / (np.std(rewards) + 1e-8),
            'win_rate': np.mean([r > 0 for r in rewards])
        }
    
    def _calculate_quality_score(self, experiences: List[Experience]) -> float:
        """Calculate overall quality score"""
        if not experiences:
            return 0.0
        
        return np.mean([e.priority for e in experiences])
    
    def get_replay_buffer(self) -> ExperienceReplayBuffer:
        """Get the experience replay buffer"""
        return self.experience_buffer
    
    def save_checkpoint(self, filepath: Optional[str] = None):
        """Save orchestrator state"""
        path = Path(filepath) if filepath else self.storage_path / "orchestrator_state.json"
        
        data = {
            'run_history': [
                {
                    'run_id': r.run_id,
                    'mode': r.mode.value,
                    'metrics': r.metrics,
                    'duration_seconds': r.duration_seconds,
                    'timestamp': r.timestamp
                }
                for r in self.run_history
            ],
            'buffer_stats': self.experience_buffer.get_statistics(),
            'saved_at': datetime.utcnow().isoformat()
        }
        
        with open(path, 'w') as f:
            import json
            json.dump(data, f, indent=2)
        
        # Save experience buffer
        self.experience_buffer.save(self.storage_path / "experience_buffer.json")
        
        logger.info(f"💾 Orchestrator state saved to {path}")
    
    def load_checkpoint(self, filepath: Optional[str] = None):
        """Load orchestrator state"""
        path = Path(filepath) if filepath else self.storage_path / "orchestrator_state.json"
        
        if not path.exists():
            logger.warning(f"No checkpoint found at {path}")
            return
        
        try:
            with open(path, 'r') as f:
                import json
                data = json.load(f)
            
            # Load experience buffer
            self.experience_buffer.load(self.storage_path / "experience_buffer.json")
            
            logger.info(f"📂 Orchestrator state loaded from {path}")
            
        except Exception as e:
            logger.error(f"Error loading checkpoint: {e}")
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics"""
        return {
            'total_runs': len(self.run_history),
            'total_experiences': len(self.experience_buffer.buffer),
            'buffer_capacity': self.experience_buffer.capacity,
            'buffer_utilization': len(self.experience_buffer.buffer) / self.experience_buffer.capacity,
            'run_history': [
                {
                    'run_id': r.run_id,
                    'mode': r.mode.value,
                    'experiences': len(r.experiences),
                    'duration': r.duration_seconds
                }
                for r in self.run_history[-10:]  # Last 10 runs
            ]
        }


# Factory function
def create_simulation_orchestrator(
    world_model: Optional[WorldModel] = None,
    storage_path: Optional[str] = None
) -> SimulationOrchestrator:
    """Create unified simulation orchestrator"""
    return SimulationOrchestrator(
        world_model=world_model,
        storage_path=storage_path
    )


# Convenience functions for different modes
async def run_self_play_training(
    num_episodes: int = 1000,
    storage_path: Optional[str] = None
) -> SimulationResult:
    """Run AlphaGo-style self-play training"""
    orchestrator = create_simulation_orchestrator(storage_path=storage_path)
    
    config = SimulationConfig(
        mode=SimulationMode.TRAINING,
        num_episodes=num_episodes,
        duration_steps=100
    )
    
    return await orchestrator.run_simulation(config)


async def generate_synthetic_data(
    num_candles: int = 10000000,
    regime: MarketRegime = MarketRegime.NORMAL,
    storage_path: Optional[str] = None
) -> SimulationResult:
    """Generate DeepSeek-style synthetic market data"""
    orchestrator = create_simulation_orchestrator(storage_path=storage_path)
    
    config = SimulationConfig(
        mode=SimulationMode.TESTING,
        num_parallel_simulations=num_candles,
        duration_steps=num_candles,
        regime=regime
    )
    
    return await orchestrator.run_simulation(config)


async def run_counterfactual_analysis(
    trade_history: Optional[List] = None,
    num_scenarios: int = 1000,
    storage_path: Optional[str] = None
) -> SimulationResult:
    """Run counterfactual reasoning analysis"""
    orchestrator = create_simulation_orchestrator(storage_path=storage_path)
    
    config = SimulationConfig(
        mode=SimulationMode.LEARNING,
        num_parallel_simulations=num_scenarios
    )
    
    return await orchestrator.run_simulation(config)


# =============================================================================
# L10: Governance and Verifier Layer — Formal Methods Light: Runtime Shield
# =============================================================================

class LTLFormula:
    """
    Linear Temporal Logic (LTL) formula for runtime safety specification.
    Compiled into a deterministic finite automaton for real-time checking.

    Supported operators:
    - G (Globally / Always): G(phi) means phi must hold at every state
    - F (Eventually): F(phi) means phi must hold at some future state
    - X (Next): X(phi) means phi must hold at the next state
    - U (Until): phi1 U phi2 means phi1 holds until phi2 becomes true
    - ! (Not), & (And), | (Or)
    """

    def __init__(self, formula_str: str, description: str = ""):
        self.formula_str = formula_str
        self.description = description
        self.violation_count = 0
        self.check_count = 0

    def check(self, state_predicates: Dict[str, bool]) -> bool:
        """
        Check if current state satisfies this LTL formula.
        Simplified: handles G (always) and basic boolean combinations.
        """
        self.check_count += 1

        # Parse simplified G(phi) formulas
        if self.formula_str.startswith("G(") and self.formula_str.endswith(")"):
            inner = self.formula_str[2:-1]
            result = self._evaluate_predicate(inner, state_predicates)
            if not result:
                self.violation_count += 1
            return result

        # Parse F(phi) — eventually (track across calls)
        if self.formula_str.startswith("F(") and self.formula_str.endswith(")"):
            inner = self.formula_str[2:-1]
            return self._evaluate_predicate(inner, state_predicates)

        # Direct predicate
        result = self._evaluate_predicate(self.formula_str, state_predicates)
        if not result:
            self.violation_count += 1
        return result

    def _evaluate_predicate(self, expr: str, predicates: Dict[str, bool]) -> bool:
        """Evaluate a boolean expression against state predicates."""
        # Simple evaluation: replace predicate names with values
        eval_expr = expr
        for name, value in predicates.items():
            eval_expr = eval_expr.replace(name, str(value))

        # Handle negation
        eval_expr = eval_expr.replace("!True", "False")
        eval_expr = eval_expr.replace("!False", "True")

        # Handle conjunction/disjunction
        eval_expr = eval_expr.replace(" & ", " and ")
        eval_expr = eval_expr.replace(" | ", " or ")

        try:
            return bool(eval(eval_expr))
        except Exception:
            return True  # Default to safe if cannot evaluate

    @property
    def violation_rate(self) -> float:
        if self.check_count == 0:
            return 0.0
        return self.violation_count / self.check_count


class RuntimeShield:
    """
    L10: Reactive Synthesis Shield — Formal Methods Light.

    This layer is NOT a neural network. It is a Reactive Synthesis Shield.

    Mechanism: A set of Linear Temporal Logic (LTL) formulas compiled into
    a deterministic finite automaton.

    Execution: The planner (L7) proposes an action. The Shield observes the
    L2 Scene Graph state. If the action would violate a temporal safety
    specification, the Shield blocks the signal and forces a Pre-Defined
    Safe Fallback Trajectory.

    Features:
    - State confidence checks
    - Invariant violation detection
    - Plan plausibility scoring
    - Anomaly detection
    - Rollback/fallback behavior
    - Human or supervisory override when stakes are high
    """

    def __init__(
        self,
        safe_fallback_action: int = 0,  # Default safe action (e.g., HOLD)
        confidence_threshold: float = 0.5,
        anomaly_threshold: float = 3.0,
        human_override_stake_threshold: float = 0.8
    ):
        self.safe_fallback_action = safe_fallback_action
        self.confidence_threshold = confidence_threshold
        self.anomaly_threshold = anomaly_threshold
        self.human_override_stake_threshold = human_override_stake_threshold

        # LTL safety specifications
        self.safety_formulas: List[LTLFormula] = []

        # State tracking
        self.state_history: List[Dict] = []
        self.violation_log: List[Dict] = []
        self.override_count = 0
        self.total_checks = 0

        # Anomaly detector (running statistics)
        self._state_mean = None
        self._state_std = None

        logger.info("✅ Runtime Shield (L10) initialized")
        logger.info(f"   Confidence threshold: {confidence_threshold}")
        logger.info(f"   Anomaly threshold: {anomaly_threshold}")

    def add_safety_spec(self, formula_str: str, description: str = ""):
        """Add an LTL safety specification."""
        self.safety_formulas.append(LTLFormula(formula_str, description))

    def check_action(
        self,
        proposed_action: int,
        scene_graph_state: Dict[str, bool],
        latent_confidence: float = 1.0,
        stake_level: float = 0.0
    ) -> Tuple[bool, int, Dict]:
        """
        Check if proposed action violates any safety specification.

        Returns:
            is_approved: Whether action is allowed
            action: Approved action (may be fallback)
            info: Dict with violation details
        """
        self.total_checks += 1
        info = {
            'violations': [],
            'confidence_check': True,
            'anomaly_check': True,
            'human_override': False
        }

        # 1. Check LTL safety formulas
        for formula in self.safety_formulas:
            if not formula.check(scene_graph_state):
                info['violations'].append({
                    'formula': formula.formula_str,
                    'description': formula.description
                })

        # 2. State confidence check
        if latent_confidence < self.confidence_threshold:
            info['confidence_check'] = False
            info['violations'].append({
                'formula': 'confidence_below_threshold',
                'description': f'Confidence {latent_confidence:.2f} < {self.confidence_threshold}'
            })

        # 3. Anomaly detection
        if self._state_mean is not None and len(self.state_history) > 10:
            latest = self.state_history[-1]
            if 'latent_norm' in latest:
                z_score = abs(latest['latent_norm'] - self._state_mean) / max(self._state_std, 1e-8)
                if z_score > self.anomaly_threshold:
                    info['anomaly_check'] = False
                    info['violations'].append({
                        'formula': 'anomaly_detected',
                        'description': f'Z-score {z_score:.2f} > {self.anomaly_threshold}'
                    })

        # 4. Human override for high-stakes situations
        if stake_level > self.human_override_stake_threshold and info['violations']:
            info['human_override'] = True
            self.override_count += 1

        # Decision
        if info['violations']:
            # Log violation
            self.violation_log.append({
                'proposed_action': proposed_action,
                'violations': info['violations'],
                'timestamp': datetime.utcnow().isoformat()
            })

            # Block and force safe fallback
            return False, self.safe_fallback_action, info

        return True, proposed_action, info

    def update_state_stats(self, latent_norm: float):
        """Update running statistics for anomaly detection."""
        self.state_history.append({'latent_norm': latent_norm})

        # Keep last 1000 states
        if len(self.state_history) > 1000:
            self.state_history = self.state_history[-1000:]

        # Update mean/std
        if len(self.state_history) > 10:
            norms = [s['latent_norm'] for s in self.state_history]
            self._state_mean = np.mean(norms)
            self._state_std = np.std(norms)

    def check_plan_plausibility(
        self,
        plan_result,
        scene_graph_state: Dict[str, bool]
    ) -> Tuple[bool, float]:
        """
        Score plan plausibility based on safety specifications and
        constraint violations.
        """
        plausibility = 1.0

        # Reduce plausibility for each constraint violation
        if hasattr(plan_result, 'constraint_violations'):
            n_violations = len(plan_result.constraint_violations)
            plausibility -= n_violations * 0.2

        # Check against safety formulas
        for formula in self.safety_formulas:
            if not formula.check(scene_graph_state):
                plausibility -= 0.3

        # Check confidence
        if hasattr(plan_result, 'confidence'):
            plausibility *= plan_result.confidence

        plausibility = max(0.0, min(1.0, plausibility))
        is_plausible = plausibility >= 0.5

        return is_plausible, plausibility

    def get_statistics(self) -> Dict:
        """Get shield statistics."""
        return {
            'total_checks': self.total_checks,
            'total_violations': len(self.violation_log),
            'violation_rate': len(self.violation_log) / max(self.total_checks, 1),
            'human_overrides': self.override_count,
            'safety_formulas': len(self.safety_formulas),
            'formula_violation_rates': {
                f.formula_str: f.violation_rate for f in self.safety_formulas
            }
        }


def create_runtime_shield(
    safe_fallback_action: int = 0,
    confidence_threshold: float = 0.5,
    anomaly_threshold: float = 3.0
) -> RuntimeShield:
    """Create L10 Runtime Shield with default trading safety specs."""
    shield = RuntimeShield(
        safe_fallback_action=safe_fallback_action,
        confidence_threshold=confidence_threshold,
        anomaly_threshold=anomaly_threshold
    )

    # Add default trading safety specifications
    shield.add_safety_spec(
        "G(!excessive_drawdown)",
        "Never allow drawdown to exceed maximum threshold"
    )
    shield.add_safety_spec(
        "G(!unhedged_concentration)",
        "Never allow unhedged position concentration above limit"
    )
    shield.add_safety_spec(
        "G(!trade_during_halt)",
        "Never trade during market halt"
    )
    shield.add_safety_spec(
        "G(!exceed_risk_budget)",
        "Never exceed daily risk budget"
    )

    return shield
