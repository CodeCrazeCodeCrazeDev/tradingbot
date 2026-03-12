"""
Adversarial Curriculum Learning Demo

Demonstrates the complete adversarial curriculum learning system for training
robust trading agents through progressively harder market conditions.

This demo shows:
1. Level progression from clean to adversarial environments
2. Promotion evaluation with statistical rigor
3. Anti-cheat detection and hardening
4. Failure analysis and regression handling
5. Out-of-distribution testing
"""

import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import random
from datetime import datetime
from typing import Dict, Any, List

from trading_bot.adversarial_curriculum import (
    CurriculumOrchestrator,
    CurriculumLevel,
    AdversarialMarketEnvironment,
    PromotionEvaluator,
    AntiCheatSystem,
    FailureAnalyzer,
    AgentAction,
    MarketState,
    AgentState,
    EpisodeResult,
    get_level_config,
    get_promotion_gate,
)
from trading_bot.adversarial_curriculum.curriculum_orchestrator import (
    AgentInterface,
    SimpleRuleAgent,
    RandomAgent,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# CUSTOM AGENTS FOR DEMO
# =============================================================================

class MomentumAgent(AgentInterface):
    """
    Momentum-based trading agent.
    Buys when price is trending up, sells when trending down.
    """
    
    def __init__(self, lookback: int = 20, threshold: float = 0.005):
        self.lookback = lookback
        self.threshold = threshold
        self.position_limit = 1.0
    
    def act(self, state: MarketState, agent_state: AgentState) -> AgentAction:
        # Need enough history
        if len(state.price_history) < self.lookback:
            return AgentAction.HOLD
        
        # Risk management first
        if agent_state.current_drawdown > 0.15:
            if agent_state.position != 0:
                return AgentAction.CLOSE_ALL
            return AgentAction.HOLD
        
        # Calculate momentum
        recent_prices = state.price_history[-self.lookback:]
        momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        # Volatility adjustment
        vol_adjustment = 1.0 / (1.0 + state.volatility * 10)
        adjusted_threshold = self.threshold / vol_adjustment
        
        # Position sizing based on confidence
        if momentum > adjusted_threshold:
            if agent_state.position < self.position_limit:
                if abs(momentum) > adjusted_threshold * 2:
                    return AgentAction.BUY_LARGE
                elif abs(momentum) > adjusted_threshold * 1.5:
                    return AgentAction.BUY_MEDIUM
                else:
                    return AgentAction.BUY_SMALL
        elif momentum < -adjusted_threshold:
            if agent_state.position > -self.position_limit:
                if abs(momentum) > adjusted_threshold * 2:
                    return AgentAction.SELL_LARGE
                elif abs(momentum) > adjusted_threshold * 1.5:
                    return AgentAction.SELL_MEDIUM
                else:
                    return AgentAction.SELL_SMALL
        
        return AgentAction.HOLD
    
    def reset(self):
        pass


class MeanReversionAgent(AgentInterface):
    """
    Mean reversion trading agent.
    Buys when price is below moving average, sells when above.
    """
    
    def __init__(self, lookback: int = 50, std_threshold: float = 1.5):
        self.lookback = lookback
        self.std_threshold = std_threshold
    
    def act(self, state: MarketState, agent_state: AgentState) -> AgentAction:
        if len(state.price_history) < self.lookback:
            return AgentAction.HOLD
        
        # Risk management
        if agent_state.current_drawdown > 0.12:
            if agent_state.position != 0:
                return AgentAction.REDUCE_EXPOSURE
            return AgentAction.HOLD
        
        # Calculate z-score
        prices = state.price_history[-self.lookback:]
        mean_price = np.mean(prices)
        std_price = np.std(prices)
        
        if std_price == 0:
            return AgentAction.HOLD
        
        z_score = (state.price - mean_price) / std_price
        
        # Mean reversion logic
        if z_score < -self.std_threshold:
            # Price is low - buy
            if agent_state.position <= 0:
                return AgentAction.BUY_MEDIUM
        elif z_score > self.std_threshold:
            # Price is high - sell
            if agent_state.position >= 0:
                return AgentAction.SELL_MEDIUM
        elif abs(z_score) < 0.5:
            # Close to mean - close position
            if agent_state.position > 0:
                return AgentAction.SELL_SMALL
            elif agent_state.position < 0:
                return AgentAction.BUY_SMALL
        
        return AgentAction.HOLD
    
    def reset(self):
        pass


class AdaptiveAgent(AgentInterface):
    """
    Adaptive agent that switches between momentum and mean reversion
    based on detected market regime.
    """
    
    def __init__(self):
        self.momentum_agent = MomentumAgent()
        self.mean_reversion_agent = MeanReversionAgent()
        self.regime_lookback = 100
    
    def act(self, state: MarketState, agent_state: AgentState) -> AgentAction:
        # Determine regime
        regime = self._detect_regime(state)
        
        # Select strategy based on regime
        if regime == 'trending':
            return self.momentum_agent.act(state, agent_state)
        else:
            return self.mean_reversion_agent.act(state, agent_state)
    
    def _detect_regime(self, state: MarketState) -> str:
        """Simple regime detection based on price action."""
        if len(state.price_history) < self.regime_lookback:
            return 'ranging'
        
        prices = state.price_history[-self.regime_lookback:]
        
        # Calculate trend strength
        returns = np.diff(prices) / prices[:-1]
        
        # Hurst exponent approximation
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 'ranging'
        
        # If returns are autocorrelated, it's trending
        autocorr = np.corrcoef(returns[:-1], returns[1:])[0, 1]
        
        if autocorr > 0.1:
            return 'trending'
        elif autocorr < -0.1:
            return 'mean_reverting'
        else:
            return 'ranging'
    
    def reset(self):
        self.momentum_agent.reset()
        self.mean_reversion_agent.reset()


# =============================================================================
# DEMO FUNCTIONS
# =============================================================================

def demo_level_progression():
    """Demonstrate level progression and hardening."""
    print("\n" + "=" * 80)
    print("DEMO 1: LEVEL PROGRESSION AND HARDENING")
    print("=" * 80)
    
    print("\nLevel configurations showing progressive hardening:\n")
    
    for level in [CurriculumLevel.LEVEL_0, CurriculumLevel.LEVEL_3, 
                  CurriculumLevel.LEVEL_5, CurriculumLevel.LEVEL_7, 
                  CurriculumLevel.LEVEL_10]:
        config = get_level_config(level)
        gate = get_promotion_gate(level)
        
        print(f"LEVEL {level.value}: {level.description}")
        print(f"  Noise: price_std={config.price_noise_std:.4f}, volume_std={config.volume_noise_std:.2f}")
        print(f"  Execution: slippage={config.base_slippage_bps:.1f}bps, latency={config.latency_mean_ms:.0f}ms")
        print(f"  Adversarial: fake_signals={config.fake_signal_probability:.1%}, stop_hunt={config.stop_hunt_probability:.1%}")
        print(f"  Crisis: flash_crash={config.flash_crash_probability:.2%}, liquidity_crisis={config.liquidity_crisis_probability:.2%}")
        print(f"  Promotion: min_sharpe={gate.min_sharpe:.2f}, max_dd={gate.max_drawdown:.0%}, min_episodes={gate.min_episodes}")
        print()


def demo_environment_simulation():
    """Demonstrate environment simulation at different levels."""
    print("\n" + "=" * 80)
    print("DEMO 2: ENVIRONMENT SIMULATION")
    print("=" * 80)
    
    agent = MomentumAgent()
    
    for level in [CurriculumLevel.LEVEL_0, CurriculumLevel.LEVEL_5, CurriculumLevel.LEVEL_10]:
        print(f"\n--- Level {level.value}: {level.description} ---")
        
        env = AdversarialMarketEnvironment(
            level=level,
            initial_capital=100000,
            episode_length=200,
            seed=42
        )
        
        state = env.reset()
        done = False
        step = 0
        
        while not done:
            action = agent.act(state, env.agent_state)
            state, reward, done, info = env.step(action)
            step += 1
        
        result = env.get_episode_result()
        
        print(f"  Episodes steps: {step}")
        print(f"  Total return: {result.total_return:.2%}")
        print(f"  Sharpe ratio: {result.sharpe_ratio:.2f}")
        print(f"  Max drawdown: {result.max_drawdown:.2%}")
        print(f"  Win rate: {result.win_rate:.1%}")
        print(f"  Total trades: {result.total_trades}")
        print(f"  Regimes encountered: {[r.name for r in result.regimes_encountered]}")
        print(f"  Hardening events: {[h.name for h in result.hardening_events]}")


def demo_anti_cheat_system():
    """Demonstrate anti-cheat detection."""
    print("\n" + "=" * 80)
    print("DEMO 3: ANTI-CHEAT SYSTEM")
    print("=" * 80)
    
    # Create a "cheating" agent that exploits patterns
    class ExploitingAgent(AgentInterface):
        """Agent that tries to exploit deterministic patterns."""
        def __init__(self):
            self.step_count = 0
        
        def act(self, state: MarketState, agent_state: AgentState) -> AgentAction:
            self.step_count += 1
            # Always buy at step 10, 20, 30, etc. (exploiting timing)
            if self.step_count % 10 == 0:
                return AgentAction.BUY_LARGE
            # Always sell at step 15, 25, 35, etc.
            if self.step_count % 10 == 5:
                return AgentAction.SELL_LARGE
            return AgentAction.HOLD
        
        def reset(self):
            self.step_count = 0
    
    print("\nTesting exploiting agent against anti-cheat system...")
    
    env = AdversarialMarketEnvironment(
        level=CurriculumLevel.LEVEL_5,
        initial_capital=100000,
        episode_length=500,
    )
    
    anti_cheat = AntiCheatSystem(CurriculumLevel.LEVEL_5)
    agent = ExploitingAgent()
    
    state = env.reset()
    done = False
    step = 0
    
    while not done:
        action = agent.act(state, env.agent_state)
        
        # Record for anti-cheat
        anti_cheat.record_step(state, action, env.agent_state, step)
        
        state, _, done, _ = env.step(action)
        step += 1
    
    # Run anti-cheat checks
    violations = anti_cheat.run_checks(500)
    
    print(f"\nViolations detected: {len(violations)}")
    for v in violations:
        print(f"  - {v.violation_type.name}: {v.severity} (confidence: {v.confidence:.1%})")
        print(f"    {v.evidence.get('explanation', 'No details')}")
    
    print(f"\nPenalty multiplier: {anti_cheat.penalty_multiplier:.2f}")
    print(f"Hardening active: {anti_cheat.hardening_active}")
    
    if anti_cheat.hardening_active:
        mods = anti_cheat.get_hardening_modifications()
        print(f"Hardening modifications: {list(mods.keys())}")


def demo_promotion_evaluation():
    """Demonstrate promotion evaluation."""
    print("\n" + "=" * 80)
    print("DEMO 4: PROMOTION EVALUATION")
    print("=" * 80)
    
    orchestrator = CurriculumOrchestrator({
        'initial_capital': 100000,
        'episode_length': 300,
        'num_seeds': 3,
        'ood_test_episodes': 5,
    })
    
    # Use adaptive agent
    agent = AdaptiveAgent()
    orchestrator.set_agent(agent)
    
    print("\nRunning training session at Level 0...")
    
    # Start training
    session = orchestrator.start_training(CurriculumLevel.LEVEL_0)
    
    # Run episodes
    for i in range(20):
        result = orchestrator.run_episode()
        if (i + 1) % 5 == 0:
            print(f"  Episode {i+1}: Return={result.total_return:.2%}, Sharpe={result.sharpe_ratio:.2f}")
    
    print("\nEvaluating promotion...")
    
    # Note: Full promotion requires more episodes and OOD tests
    # This is a simplified demo
    print("\n(Note: Full promotion requires meeting all statistical criteria)")
    print("Current session summary:")
    
    summary = session.get_summary()
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")


def demo_failure_analysis():
    """Demonstrate failure analysis and regression."""
    print("\n" + "=" * 80)
    print("DEMO 5: FAILURE ANALYSIS AND REGRESSION")
    print("=" * 80)
    
    # Create a risky agent that will fail
    class RiskyAgent(AgentInterface):
        """Agent that takes excessive risks."""
        def act(self, state: MarketState, agent_state: AgentState) -> AgentAction:
            # Always go all-in
            if agent_state.position == 0:
                return AgentAction.BUY_LARGE
            elif agent_state.current_drawdown > 0.05:
                # Double down on losses (martingale)
                return AgentAction.BUY_LARGE
            return AgentAction.HOLD
        
        def reset(self):
            pass
    
    print("\nTesting risky agent that exhibits martingale behavior...")
    
    env = AdversarialMarketEnvironment(
        level=CurriculumLevel.LEVEL_5,
        initial_capital=100000,
        episode_length=300,
    )
    
    agent = RiskyAgent()
    failure_analyzer = FailureAnalyzer()
    
    state = env.reset()
    done = False
    
    while not done:
        action = agent.act(state, env.agent_state)
        state, _, done, _ = env.step(action)
    
    result = env.get_episode_result()
    
    print(f"\nEpisode result:")
    print(f"  Return: {result.total_return:.2%}")
    print(f"  Max drawdown: {result.max_drawdown:.2%}")
    print(f"  Max leverage: {result.max_leverage_used:.2f}x")
    
    # Analyze failure
    diagnostic = failure_analyzer.analyze_episode_failure(
        result=result,
        agent_state=env.agent_state,
        market_conditions={
            'regimes': result.regimes_encountered,
            'hardening_events': result.hardening_events,
        }
    )
    
    if diagnostic:
        print(f"\nFailure Diagnostic:")
        print(f"  Mode: {diagnostic.failure_mode.name}")
        print(f"  Severity: {diagnostic.severity}")
        print(f"  Description: {diagnostic.description}")
        print(f"  Contributing factors: {diagnostic.contributing_factors}")
        print(f"  Recommended action: {diagnostic.recommended_action}")
        print(f"  Retrain from level: {diagnostic.retrain_from_level.value if diagnostic.retrain_from_level else 'N/A'}")
        print(f"  Training focus: {diagnostic.targeted_training_focus}")


def demo_full_curriculum():
    """Demonstrate full curriculum training (abbreviated)."""
    print("\n" + "=" * 80)
    print("DEMO 6: FULL CURRICULUM TRAINING (ABBREVIATED)")
    print("=" * 80)
    
    orchestrator = CurriculumOrchestrator({
        'initial_capital': 100000,
        'episode_length': 200,
        'num_seeds': 2,
        'ood_test_episodes': 3,
    })
    
    agent = AdaptiveAgent()
    orchestrator.set_agent(agent)
    
    print("\nRunning abbreviated curriculum (Level 0 -> Level 2)...")
    print("(Full training would run many more episodes per level)\n")
    
    # Track progress
    def on_episode(result):
        pass  # Silent
    
    def on_promotion(result):
        print(f"  PROMOTED to Level {result.next_level.value if result.next_level else 'MAX'}")
    
    def on_failure(diagnostic):
        print(f"  FAILURE: {diagnostic.failure_mode.name}")
    
    orchestrator.on_episode_complete = on_episode
    orchestrator.on_promotion = on_promotion
    orchestrator.on_failure = on_failure
    
    # Run a few levels
    for target_level in range(3):
        if orchestrator.current_level.value >= target_level:
            continue
        
        print(f"\nTraining at Level {orchestrator.current_level.value}...")
        session = orchestrator.start_training()
        
        # Run minimal episodes for demo
        for i in range(15):
            result = orchestrator.run_episode()
        
        print(f"  Completed {session.completed_episodes} episodes")
        print(f"  Best Sharpe: {session.best_sharpe:.2f}")
        print(f"  Best Return: {session.best_return:.2%}")
    
    # Print final report
    print("\n" + orchestrator.generate_curriculum_report())


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all demos."""
    print("=" * 80)
    print("ADVERSARIAL CURRICULUM LEARNING SYSTEM - DEMONSTRATION")
    print("=" * 80)
    print("""
This demonstration shows the complete adversarial curriculum learning system
for training robust trading agents through progressively harder conditions.

CORE PRINCIPLES:
- Capital preservation > Profit
- Statistical dominance, not perfection
- No shortcuts, no overfitting, no reward hacking
- Every level is strictly harder than the previous
- Out-of-distribution tests are mandatory
    """)
    
    # Run demos
    demo_level_progression()
    demo_environment_simulation()
    demo_anti_cheat_system()
    demo_promotion_evaluation()
    demo_failure_analysis()
    demo_full_curriculum()
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("""
KEY TAKEAWAYS:

1. LEVEL HARDENING: Each level introduces new complexity
   - Level 0-1: Clean environment
   - Level 2-3: Noise and execution uncertainty
   - Level 4-5: Regime switching and adversarial behavior
   - Level 6-7: Multi-asset shocks and black swans
   - Level 8+: Non-stationary rules

2. PROMOTION GATES: Statistical rigor required
   - Positive expectancy with confidence
   - Sharpe ratio above threshold
   - Drawdown bounded
   - Consistent across seeds
   - OOD tests passed

3. ANTI-CHEAT: No shortcuts allowed
   - Pattern memorization detected
   - Deterministic exploitation blocked
   - Excessive trading penalized
   - Reward hacking prevented

4. FAILURE HANDLING: Learn from mistakes
   - Root cause analysis
   - Targeted retraining
   - Level regression when needed

The agent must SURVIVE reality, not just win in simulation.
    """)


if __name__ == "__main__":
    main()
