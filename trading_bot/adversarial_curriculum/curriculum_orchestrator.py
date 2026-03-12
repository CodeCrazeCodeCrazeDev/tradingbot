"""
Curriculum Orchestrator for Adversarial Training

Master controller that coordinates:
- Level progression
- Training sessions
- Promotion evaluation
- Anti-cheat monitoring
- Failure handling
- Environment hardening

This is the main entry point for the adversarial curriculum learning system.
"""

import asyncio
import logging
import random
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

from .core_types import (
    AgentAction,
    AgentState,
    AntiCheatViolation,
    CurriculumLevel,
    EpisodeResult,
    FailureDiagnostic,
    FailureMode,
    HardeningMechanism,
    LevelConfig,
    MarketRegime,
    MarketState,
    PromotionGate,
    PromotionResult,
    get_level_config,
    get_promotion_gate,
)
from .market_environment import AdversarialMarketEnvironment
from .promotion_system import PromotionEvaluator, OODTester
from .anti_cheat import AntiCheatSystem
from .failure_handler import FailureAnalyzer, RetrainingScheduler, RegressionManager

logger = logging.getLogger(__name__)


# =============================================================================
# TRAINING SESSION
# =============================================================================

@dataclass
class TrainingSession:
    """Represents a training session at a specific level."""
    session_id: str
    level: CurriculumLevel
    started_at: datetime
    
    # Configuration
    target_episodes: int = 100
    seeds: List[int] = field(default_factory=list)
    
    # Results
    episode_results: List[EpisodeResult] = field(default_factory=list)
    ood_results: Dict[str, List[EpisodeResult]] = field(default_factory=dict)
    
    # Status
    completed_episodes: int = 0
    current_seed_idx: int = 0
    status: str = 'running'  # 'running', 'evaluating', 'completed', 'failed'
    
    # Metrics
    best_sharpe: float = float('-inf')
    best_return: float = float('-inf')
    lowest_drawdown: float = float('inf')
    
    # Timestamps
    ended_at: Optional[datetime] = None
    
    def add_result(self, result: EpisodeResult):
        """Add episode result and update metrics."""
        try:
            self.episode_results.append(result)
            self.completed_episodes += 1
        
            if result.sharpe_ratio > self.best_sharpe:
                self.best_sharpe = result.sharpe_ratio
            if result.total_return > self.best_return:
                self.best_return = result.total_return
            if result.max_drawdown < self.lowest_drawdown:
                self.lowest_drawdown = result.max_drawdown
        except Exception as e:
            logger.error(f"Error in add_result: {e}")
            raise
    
    def get_progress(self) -> float:
        """Get training progress as percentage."""
        return self.completed_episodes / self.target_episodes if self.target_episodes > 0 else 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get session summary."""
        try:
            if not self.episode_results:
                return {'status': self.status, 'episodes': 0}
        
            returns = [r.total_return for r in self.episode_results]
            sharpes = [r.sharpe_ratio for r in self.episode_results]
            drawdowns = [r.max_drawdown for r in self.episode_results]
        
            return {
                'session_id': self.session_id,
                'level': self.level.value,
                'status': self.status,
                'episodes': self.completed_episodes,
                'target_episodes': self.target_episodes,
                'progress': f"{self.get_progress():.1%}",
                'avg_return': np.mean(returns),
                'avg_sharpe': np.mean(sharpes),
                'avg_drawdown': np.mean(drawdowns),
                'best_sharpe': self.best_sharpe,
                'best_return': self.best_return,
                'lowest_drawdown': self.lowest_drawdown,
                'duration': str(datetime.now() - self.started_at),
            }
        except Exception as e:
            logger.error(f"Error in get_summary: {e}")
            raise


# =============================================================================
# AGENT INTERFACE
# =============================================================================

class AgentInterface:
    """
    Interface for trading agents to implement.
    Agents must implement the act() method.
    """
    
    def act(self, state: MarketState, agent_state: AgentState) -> AgentAction:
        """
        Select action based on current state.
        
        Args:
            state: Current market state
            agent_state: Current agent state
            
        Returns:
            Selected action
        """
    
    def learn(self, experience: Dict[str, Any]):
        """
        Learn from experience (optional).
        
        Args:
            experience: Dictionary containing state, action, reward, next_state, done
        """
        pass
    
    def reset(self):
        """Reset agent state for new episode."""
        pass
    
    def save(self, path: str):
        """Save agent to file."""
        pass
    
    def load(self, path: str):
        """Load agent from file."""
        pass


class RandomAgent(AgentInterface):
    """Simple random agent for testing."""
    
    def __init__(self, action_space: List[AgentAction]):
        try:
            self.action_space = action_space
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def act(self, state: MarketState, agent_state: AgentState) -> AgentAction:
        """
        act function.

    Args:
        state: Description
        agent_state: Description

    Returns:
        Result of operation
        """
        return random.choice(self.action_space)


class SimpleRuleAgent(AgentInterface):
    """Simple rule-based agent for testing."""
    
    def __init__(self):
        try:
            self.position_target = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def act(self, state: MarketState, agent_state: AgentState) -> AgentAction:
        """
        act function.

    Args:
        state: Description
        agent_state: Description

    Returns:
        Result of operation
        """
        # Simple momentum strategy
        try:
            if len(state.price_history) < 20:
                return AgentAction.HOLD
        
            # Calculate simple momentum
            recent_return = (state.price_history[-1] - state.price_history[-20]) / state.price_history[-20]
        
            # Risk management
            if agent_state.current_drawdown > 0.1:
                if agent_state.position != 0:
                    return AgentAction.CLOSE_ALL
                return AgentAction.HOLD
        
            # Position management
            if recent_return > 0.01 and agent_state.position <= 0:
                return AgentAction.BUY_SMALL
            elif recent_return < -0.01 and agent_state.position >= 0:
                return AgentAction.SELL_SMALL
        
            return AgentAction.HOLD
        except Exception as e:
            logger.error(f"Error in act: {e}")
            raise


# =============================================================================
# CURRICULUM ORCHESTRATOR
# =============================================================================

class CurriculumOrchestrator:
    """
    Main orchestrator for adversarial curriculum learning.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Components
            self.promotion_evaluator = PromotionEvaluator()
            self.ood_tester = OODTester()
            self.failure_analyzer = FailureAnalyzer()
            self.retraining_scheduler = RetrainingScheduler()
            self.regression_manager = RegressionManager()
        
            # State
            self.current_level = CurriculumLevel.LEVEL_0
            self.current_session: Optional[TrainingSession] = None
            self.session_history: List[TrainingSession] = []
        
            # Agent
            self.agent: Optional[AgentInterface] = None
        
            # Anti-cheat
            self.anti_cheat: Optional[AntiCheatSystem] = None
        
            # Environment
            self.environment: Optional[AdversarialMarketEnvironment] = None
        
            # Configuration
            self.initial_capital = self.config.get('initial_capital', 100000.0)
            self.episode_length = self.config.get('episode_length', 1000)
            self.num_seeds = self.config.get('num_seeds', 5)
            self.ood_test_episodes = self.config.get('ood_test_episodes', 20)
        
            # Callbacks
            self.on_episode_complete: Optional[Callable] = None
            self.on_level_complete: Optional[Callable] = None
            self.on_promotion: Optional[Callable] = None
            self.on_failure: Optional[Callable] = None
        
            logger.info("CurriculumOrchestrator initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def set_agent(self, agent: AgentInterface):
        """Set the agent to train."""
        try:
            self.agent = agent
            logger.info(f"Agent set: {type(agent).__name__}")
        except Exception as e:
            logger.error(f"Error in set_agent: {e}")
            raise
    
    def start_training(self, from_level: Optional[CurriculumLevel] = None) -> TrainingSession:
        """
        Start a new training session.
        
        Args:
            from_level: Level to start from (default: current level)
            
        Returns:
            New training session
        """
        try:
            if from_level is not None:
                self.current_level = from_level
        
            level_config = get_level_config(self.current_level)
        
            # Generate seeds
            seeds = [random.randint(0, 2**32 - 1) for _ in range(self.num_seeds)]
        
            # Create session
            self.current_session = TrainingSession(
                session_id=f"session_{self.current_level.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                level=self.current_level,
                started_at=datetime.now(),
                target_episodes=level_config.min_episodes,
                seeds=seeds,
            )
        
            # Initialize anti-cheat
            self.anti_cheat = AntiCheatSystem(self.current_level)
        
            logger.info(f"Training session started: {self.current_session.session_id}")
            logger.info(f"Level: {self.current_level.value} - {self.current_level.description}")
            logger.info(f"Target episodes: {level_config.min_episodes}, Seeds: {len(seeds)}")
        
            return self.current_session
        except Exception as e:
            logger.error(f"Error in start_training: {e}")
            raise
    
    def run_episode(self, seed: Optional[int] = None) -> EpisodeResult:
        """
        Run a single training episode.
        
        Args:
            seed: Random seed for reproducibility
            
        Returns:
            Episode result
        """
        try:
            if self.agent is None:
                raise ValueError("No agent set. Call set_agent() first.")
        
            if self.current_session is None:
                raise ValueError("No active session. Call start_training() first.")
        
            # Select seed
            if seed is None:
                seed_idx = self.current_session.current_seed_idx % len(self.current_session.seeds)
                seed = self.current_session.seeds[seed_idx]
                self.current_session.current_seed_idx += 1
        
            # Create environment
            self.environment = AdversarialMarketEnvironment(
                level=self.current_level,
                initial_capital=self.initial_capital,
                episode_length=self.episode_length,
                seed=seed,
            )
        
            # Apply anti-cheat hardening if needed
            if self.anti_cheat and self.anti_cheat.hardening_active:
                modifications = self.anti_cheat.get_hardening_modifications()
                self._apply_hardening(modifications)
        
            # Reset agent
            self.agent.reset()
        
            # Run episode
            state = self.environment.reset()
            done = False
            total_reward = 0
            step = 0
        
            while not done:
                # Get action from agent
                action = self.agent.act(state, self.environment.agent_state)
            
                # Record for anti-cheat
                if self.anti_cheat:
                    self.anti_cheat.record_step(
                        state=state,
                        action=action,
                        agent_state=self.environment.agent_state,
                        step=step
                    )
            
                # Take step
                next_state, reward, done, info = self.environment.step(action)
            
                # Learn (if agent supports it)
                experience = {
                    'state': state,
                    'action': action,
                    'reward': reward,
                    'next_state': next_state,
                    'done': done,
                    'info': info,
                }
                self.agent.learn(experience)
            
                state = next_state
                total_reward += reward
                step += 1
        
            # Get episode result
            result = self.environment.get_episode_result()
        
            # Run anti-cheat checks
            if self.anti_cheat:
                violations = self.anti_cheat.run_checks(self.episode_length)
                result.anti_cheat_flags = [v.violation_type for v in violations]
        
            # Add to session
            self.current_session.add_result(result)
        
            # Check for failures
            if not result.passed_basic_checks or result.max_drawdown > 0.3:
                self._handle_failure(result)
        
            # Callback
            if self.on_episode_complete:
                self.on_episode_complete(result)
        
            logger.debug(
                f"Episode {result.episode_id} complete: "
                f"Return={result.total_return:.2%}, Sharpe={result.sharpe_ratio:.2f}, "
                f"DD={result.max_drawdown:.2%}"
            )
        
            return result
        except Exception as e:
            logger.error(f"Error in run_episode: {e}")
            raise
    
    def _apply_hardening(self, modifications: Dict[str, Any]):
        """Apply hardening modifications to environment."""
        try:
            if not self.environment:
                return
        
            config = self.environment.config
        
            if 'noise_multiplier' in modifications:
                config.price_noise_std *= modifications['noise_multiplier']
                config.volume_noise_std *= modifications['noise_multiplier']
        
            if 'regime_switch_multiplier' in modifications:
                config.regime_switch_probability *= modifications['regime_switch_multiplier']
        
            if 'transaction_cost_multiplier' in modifications:
                config.base_slippage_bps *= modifications['transaction_cost_multiplier']
        
            if 'tail_risk_penalty_multiplier' in modifications:
                config.tail_risk_penalty *= modifications['tail_risk_penalty_multiplier']
        
            logger.info(f"Applied hardening modifications: {list(modifications.keys())}")
        except Exception as e:
            logger.error(f"Error in _apply_hardening: {e}")
            raise
    
    def _handle_failure(self, result: EpisodeResult):
        """Handle episode failure."""
        # Analyze failure
        try:
            diagnostic = self.failure_analyzer.analyze_episode_failure(
                result=result,
                agent_state=self.environment.agent_state if self.environment else AgentState(
                    capital=0, position=0, avg_entry_price=0, unrealized_pnl=0,
                    realized_pnl=0, trade_count=0, win_count=0, loss_count=0,
                    max_drawdown=result.max_drawdown, current_drawdown=result.max_drawdown,
                    peak_capital=self.initial_capital, leverage=0
                ),
                market_conditions={
                    'regimes': result.regimes_encountered,
                    'hardening_events': result.hardening_events,
                }
            )
        
            if diagnostic:
                logger.warning(f"Failure detected: {diagnostic.failure_mode.name}")
            
                # Check for regression
                regression_level = self.regression_manager.record_failure(self.current_level)
            
                if regression_level:
                    logger.warning(f"REGRESSION triggered: Level {self.current_level.value} -> {regression_level.value}")
                    self.current_level = regression_level
                
                    # Schedule retraining
                    self.retraining_scheduler.schedule_retraining(
                        diagnostic,
                        priority='critical' if diagnostic.severity == 'critical' else 'high'
                    )
            
                # Callback
                if self.on_failure:
                    self.on_failure(diagnostic)
        except Exception as e:
            logger.error(f"Error in _handle_failure: {e}")
            raise
    
    def run_ood_tests(self) -> Dict[str, List[EpisodeResult]]:
        """
        Run out-of-distribution tests.
        
        Returns:
            Dictionary of scenario name -> results
        """
        try:
            if self.agent is None:
                raise ValueError("No agent set")
        
            scenarios = self.ood_tester.generate_ood_scenarios(self.current_level)
            ood_results = {}
        
            for scenario in scenarios:
                logger.info(f"Running OOD test: {scenario['name']}")
            
                scenario_results = []
                for _ in range(self.ood_test_episodes):
                    # Create modified environment
                    env = AdversarialMarketEnvironment(
                        level=self.current_level,
                        initial_capital=self.initial_capital,
                        episode_length=self.episode_length,
                    )
                
                    # Apply scenario modifications
                    self._apply_scenario_modifications(env, scenario['modifications'])
                
                    # Run episode
                    self.agent.reset()
                    state = env.reset()
                    done = False
                
                    while not done:
                        action = self.agent.act(state, env.agent_state)
                        state, _, done, _ = env.step(action)
                
                    result = env.get_episode_result()
                    scenario_results.append(result)
            
                ood_results[scenario['name']] = scenario_results
            
                # Log results
                avg_sharpe = np.mean([r.sharpe_ratio for r in scenario_results])
                avg_return = np.mean([r.total_return for r in scenario_results])
                logger.info(f"  {scenario['name']}: Sharpe={avg_sharpe:.2f}, Return={avg_return:.2%}")
        
            return ood_results
        except Exception as e:
            logger.error(f"Error in run_ood_tests: {e}")
            raise
    
    def _apply_scenario_modifications(self, env: AdversarialMarketEnvironment, modifications: Dict[str, Any]):
        """Apply OOD scenario modifications to environment."""
        try:
            config = env.config
        
            if modifications.get('volatility_multiplier'):
                config.price_noise_std *= modifications['volatility_multiplier']
        
            if modifications.get('spread_multiplier'):
                config.base_spread_bps *= modifications['spread_multiplier']
        
            if modifications.get('liquidity_multiplier'):
                # Reduce liquidity
                pass  # Would modify liquidity in environment
        
            if modifications.get('slippage_multiplier'):
                config.base_slippage_bps *= modifications['slippage_multiplier']
        
            if modifications.get('fake_signal_multiplier'):
                config.fake_signal_probability *= modifications['fake_signal_multiplier']
        
            if modifications.get('stop_hunt_multiplier'):
                config.stop_hunt_probability *= modifications['stop_hunt_multiplier']
        except Exception as e:
            logger.error(f"Error in _apply_scenario_modifications: {e}")
            raise
    
    def evaluate_promotion(self) -> PromotionResult:
        """
        Evaluate if agent should be promoted to next level.
        
        Returns:
            Promotion result
        """
        try:
            if self.current_session is None:
                raise ValueError("No active session")
        
            logger.info(f"Evaluating promotion for Level {self.current_level.value}")
        
            # Run OOD tests
            ood_results = self.run_ood_tests()
            self.current_session.ood_results = ood_results
        
            # Evaluate promotion
            result = self.promotion_evaluator.evaluate_promotion(
                level=self.current_level,
                results=self.current_session.episode_results,
                ood_results=ood_results,
            )
        
            # Log report
            report = self.promotion_evaluator.generate_promotion_report(result)
            logger.info(f"\n{report}")
        
            # Handle promotion
            if result.promoted:
                self.regression_manager.record_success(self.current_level)
            
                if result.next_level:
                    self.current_level = result.next_level
                    logger.info(f"PROMOTED to Level {self.current_level.value}")
            
                if self.on_promotion:
                    self.on_promotion(result)
            else:
                logger.warning(f"Promotion DENIED. Failures: {len(result.failure_reasons)}")
        
            # Complete session
            self.current_session.status = 'completed'
            self.current_session.ended_at = datetime.now()
            self.session_history.append(self.current_session)
        
            if self.on_level_complete:
                self.on_level_complete(self.current_session)
        
            return result
        except Exception as e:
            logger.error(f"Error in evaluate_promotion: {e}")
            raise
    
    def run_full_training(
        self,
        target_level: CurriculumLevel = CurriculumLevel.LEVEL_10,
        max_sessions: int = 100
    ) -> Dict[str, Any]:
        """
        Run full training curriculum until target level or max sessions.
        
        Args:
            target_level: Target level to reach
            max_sessions: Maximum training sessions
            
        Returns:
            Training summary
        """
        try:
            if self.agent is None:
                raise ValueError("No agent set")
        
            logger.info(f"Starting full training. Target: Level {target_level.value}")
        
            sessions_completed = 0
            promotions = 0
            regressions = 0
        
            while self.current_level.value < target_level.value and sessions_completed < max_sessions:
                # Start session
                session = self.start_training()
            
                # Run episodes
                level_config = get_level_config(self.current_level)
                for _ in range(level_config.min_episodes):
                    self.run_episode()
            
                # Evaluate promotion
                result = self.evaluate_promotion()
            
                if result.promoted:
                    promotions += 1
                else:
                    # Check if we regressed
                    if self.current_level.value < session.level.value:
                        regressions += 1
            
                sessions_completed += 1
            
                logger.info(
                    f"Session {sessions_completed} complete. "
                    f"Current level: {self.current_level.value}, "
                    f"Promotions: {promotions}, Regressions: {regressions}"
                )
        
            # Generate summary
            summary = {
                'final_level': self.current_level.value,
                'target_level': target_level.value,
                'reached_target': self.current_level.value >= target_level.value,
                'sessions_completed': sessions_completed,
                'promotions': promotions,
                'regressions': regressions,
                'total_episodes': sum(s.completed_episodes for s in self.session_history),
                'session_history': [s.get_summary() for s in self.session_history],
            }
        
            logger.info(f"Training complete. Final level: {self.current_level.value}")
        
            return summary
        except Exception as e:
            logger.error(f"Error in run_full_training: {e}")
            raise
    
    def get_curriculum_status(self) -> Dict[str, Any]:
        """Get current curriculum status."""
        return {
            'current_level': self.current_level.value,
            'level_description': self.current_level.description,
            'active_session': self.current_session.get_summary() if self.current_session else None,
            'sessions_completed': len(self.session_history),
            'total_episodes': sum(s.completed_episodes for s in self.session_history),
            'failure_summary': self.failure_analyzer.get_failure_summary(),
            'regression_summary': self.regression_manager.get_regression_summary(),
            'anti_cheat_summary': self.anti_cheat.get_violation_summary() if self.anti_cheat else "N/A",
        }
    
    def generate_curriculum_report(self) -> str:
        """Generate comprehensive curriculum report."""
        try:
            lines = [
                "=" * 80,
                "ADVERSARIAL CURRICULUM LEARNING REPORT",
                "=" * 80,
                "",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "CURRENT STATUS",
                "-" * 40,
                f"Current Level: {self.current_level.value} - {self.current_level.description}",
                f"Sessions Completed: {len(self.session_history)}",
                f"Total Episodes: {sum(s.completed_episodes for s in self.session_history)}",
                "",
            ]
        
            # Level progression
            lines.append("LEVEL PROGRESSION")
            lines.append("-" * 40)
        
            for session in self.session_history:
                summary = session.get_summary()
                lines.append(
                    f"Level {summary['level']}: "
                    f"Episodes={summary['episodes']}, "
                    f"Sharpe={summary['avg_sharpe']:.2f}, "
                    f"Return={summary['avg_return']:.2%}, "
                    f"DD={summary['avg_drawdown']:.2%}"
                )
        
            lines.append("")
        
            # Failure analysis
            lines.append("FAILURE ANALYSIS")
            lines.append("-" * 40)
            lines.append(self.failure_analyzer.get_failure_summary())
            lines.append("")
        
            # Regression history
            lines.append("REGRESSION HISTORY")
            lines.append("-" * 40)
            lines.append(self.regression_manager.get_regression_summary())
            lines.append("")
        
            # Anti-cheat summary
            if self.anti_cheat:
                lines.append("ANTI-CHEAT SUMMARY")
                lines.append("-" * 40)
                lines.append(self.anti_cheat.get_violation_summary())
                lines.append("")
        
            lines.append("=" * 80)
        
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Error in generate_curriculum_report: {e}")
            raise


# =============================================================================
# QUICK START
# =============================================================================

def quick_start(config: Optional[Dict[str, Any]] = None) -> CurriculumOrchestrator:
    """
    Quick start function to create and configure orchestrator.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured CurriculumOrchestrator
    """
    try:
        orchestrator = CurriculumOrchestrator(config)
    
        # Set default agent if none provided
        level_config = get_level_config(CurriculumLevel.LEVEL_0)
        default_agent = SimpleRuleAgent()
        orchestrator.set_agent(default_agent)
    
        return orchestrator
    except Exception as e:
        logger.error(f"Error in quick_start: {e}")
        raise


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 80)
    print("ADVERSARIAL CURRICULUM LEARNING SYSTEM")
    print("=" * 80)
    
    # Create orchestrator
    orchestrator = quick_start({
        'initial_capital': 100000,
        'episode_length': 500,
        'num_seeds': 3,
    })
    
    # Start training at Level 0
    session = orchestrator.start_training(CurriculumLevel.LEVEL_0)
    
    print(f"\nStarted session: {session.session_id}")
    print(f"Level: {orchestrator.current_level.value} - {orchestrator.current_level.description}")
    
    # Run some episodes
    print("\nRunning episodes...")
    for i in range(10):
        result = orchestrator.run_episode()
        print(f"  Episode {i+1}: Return={result.total_return:.2%}, Sharpe={result.sharpe_ratio:.2f}")
    
    # Get status
    print("\n" + "=" * 80)
    print("CURRICULUM STATUS")
    print("=" * 80)
    
    status = orchestrator.get_curriculum_status()
    print(f"Current Level: {status['current_level']}")
    print(f"Sessions Completed: {status['sessions_completed']}")
    print(f"Total Episodes: {status['total_episodes']}")
    
    print("\n" + orchestrator.generate_curriculum_report())
