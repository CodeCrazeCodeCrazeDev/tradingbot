# Adversarial Curriculum Learning System

## Complete Documentation

A multi-level curriculum learning environment that trains AI trading agents from fundamentals to advanced market mastery under increasingly hostile conditions.

**Priority: Robustness, Generalization, and Capital Preservation - NOT short-term profit.**

---

## Table of Contents

1. [Core Principles](#core-principles)
2. [Architecture Overview](#architecture-overview)
3. [Level Progression](#level-progression)
4. [Promotion Gates](#promotion-gates)
5. [Anti-Cheat System](#anti-cheat-system)
6. [Failure Handling](#failure-handling)
7. [Usage Guide](#usage-guide)
8. [API Reference](#api-reference)

---

## Core Principles

### Non-Negotiable Rules

1. **No "100% accuracy" criteria** - Use statistical confidence, robustness, and risk metrics only
2. **Every level must harden the environment** - More noise, more regime shifts, less signal-to-noise, higher penalties
3. **Capital survival > Profit** - Any strategy that wins by accepting catastrophic tail risk is rejected
4. **Out-of-distribution tests are mandatory** - Promotion is invalid without unseen regimes
5. **No shortcuts, no overfitting, no reward hacking** - Detected exploits trigger penalties and retraining

---

## Architecture Overview

```
trading_bot/adversarial_curriculum/
├── __init__.py                 # Module exports
├── core_types.py               # Data structures, enums, level configs
├── market_environment.py       # Adversarial market simulation
├── promotion_system.py         # Statistical validation for promotion
├── anti_cheat.py               # Exploit detection and hardening
├── failure_handler.py          # Failure analysis and regression
└── curriculum_orchestrator.py  # Main training controller
```

### Components

| Component | Purpose |
|-----------|---------|
| `AdversarialMarketEnvironment` | Simulates market with progressive hardening |
| `PromotionEvaluator` | Validates promotion with statistical rigor |
| `AntiCheatSystem` | Detects and punishes exploits |
| `FailureAnalyzer` | Diagnoses failure modes |
| `RegressionManager` | Handles level regression |
| `CurriculumOrchestrator` | Coordinates all components |

---

## Level Progression

### Level 0-1: Foundation (Clean Environment)
- **What's tested**: Basic market mechanics, simple execution
- **Noise**: Minimal (price_std=0.0001)
- **Execution**: Near-perfect (slippage=0.5bps, latency=10ms)
- **Promotion**: Sharpe ≥ 0.3, Drawdown ≤ 15%

### Level 2-3: Noise Injection
- **What breaks**: Strategies dependent on clean signals
- **New challenges**:
  - Price noise (std=0.001)
  - Volume noise (std=15%)
  - Slippage variance
  - Latency variance (25-50ms)
  - Partial fills (10-15%)
- **Promotion**: Sharpe ≥ 0.5, Drawdown ≤ 20%

### Level 4-5: Regime Switching & Adversarial Behavior
- **What breaks**: Single-regime strategies
- **New challenges**:
  - Regime switching (1-2% per step)
  - Fake signals (5-8%)
  - Stop hunting (3-5%)
  - Market manipulation (2-3%)
  - Spread widening
- **Promotion**: Sharpe ≥ 0.7, Drawdown ≤ 25%, OOD degradation ≤ 25%

### Level 6-7: Multi-Asset Shocks & Black Swans
- **What breaks**: Correlation-dependent strategies
- **New challenges**:
  - Correlation breakdowns (2-3%)
  - Flash crashes (0.5-1%)
  - Liquidity crises (1-2%)
  - Multi-asset exposure
- **Promotion**: Sharpe ≥ 0.9, Drawdown ≤ 25%, OOD degradation ≤ 15%

### Level 8-10: Non-Stationary & Full Adversarial
- **What breaks**: Everything that isn't truly robust
- **New challenges**:
  - Non-stationary reward functions
  - Rule changes mid-episode
  - All mechanisms active at maximum intensity
- **Promotion**: Sharpe ≥ 1.5, Drawdown ≤ 25%, OOD degradation ≤ 5%

---

## Promotion Gates

### Statistical Requirements

Each level requires ALL conditions to pass:

| Metric | Description | Validation Method |
|--------|-------------|-------------------|
| Positive Expectancy | Returns > 0 with confidence | One-sample t-test |
| Sharpe Ratio | Above threshold | t-test against threshold |
| Max Drawdown | Below threshold | Bootstrap confidence interval |
| Seed Consistency | Low variance across seeds | Coefficient of variation |
| Regime Independence | No single-regime dependence | ANOVA test |
| OOD Performance | Acceptable degradation | Comparison with in-distribution |

### OOD Test Scenarios

1. **Inverted Regimes** - Regime patterns opposite to training
2. **Extreme Volatility** - 3x normal volatility
3. **Liquidity Drought** - 80% liquidity reduction
4. **Correlation Flip** - All correlations flip sign
5. **Adversarial Patterns** - 3x fake signals and stop hunting
6. **Non-Stationary** - Mid-episode rule changes

### Promotion Denied If:

- Insufficient episodes
- Failed statistical tests
- High seed variance
- OOD degradation > threshold
- Any rule violations
- Anti-cheat flags

---

## Anti-Cheat System

### Detection Mechanisms

| Detector | What It Catches |
|----------|-----------------|
| `OverfitDetector` | Pattern memorization, deterministic behavior, low action entropy |
| `ExploitDetector` | Timing exploits, regime exploitation, leverage abuse, reward hacking |
| `BehaviorAnalyzer` | Panic behavior, overtrading, position oscillation |

### Violation Types

```python
class AntiCheatViolationType(Enum):
    PATTERN_MEMORIZATION = auto()
    DETERMINISTIC_EXPLOITATION = auto()
    SINGLE_REGIME_DEPENDENCE = auto()
    EXCESSIVE_TRADING = auto()
    UNREALISTIC_EXECUTION = auto()
    REWARD_HACKING = auto()
    TAIL_RISK_HIDING = auto()
```

### Responses to Violations

1. **Penalty Multiplier** - Increases with severity (1.2x to 2x)
2. **Environment Hardening** - Inject more noise, increase regime switching
3. **Forced Retraining** - Schedule targeted retraining
4. **Promotion Block** - Cannot advance with violations

---

## Failure Handling

### Failure Modes

| Mode | Description | Typical Cause |
|------|-------------|---------------|
| `RISK_MISMANAGEMENT` | Excessive risk, blown accounts | Poor position sizing |
| `REGIME_BLINDNESS` | Failed to adapt to regime change | Single-strategy dependence |
| `OVERFITTING` | Memorized patterns, failed OOD | Insufficient regularization |
| `LATENCY_SENSITIVITY` | Broke under execution delays | Unrealistic assumptions |
| `DRAWDOWN_EXCEEDED` | Max drawdown breached | No drawdown management |
| `TAIL_RISK_EXPOSURE` | Catastrophic loss from tail event | No tail hedging |
| `MARTINGALE_BEHAVIOR` | Doubling down on losses | Flawed position sizing |
| `LEVERAGE_ABUSE` | Excessive leverage | No leverage limits |

### Failure Response

1. **Diagnose** - Identify root cause and contributing factors
2. **Recommend** - Generate targeted training focus
3. **Regress** - Move to earlier level if repeated failures
4. **Retrain** - Schedule retraining with specific focus

### Regression Rules

- 3 failures at same level → Regress 1-2 levels
- Multiple regressions from same level → Regress further
- Critical failures (martingale, leverage abuse) → Regress to Level 0

---

## Usage Guide

### Quick Start

```python
from trading_bot.adversarial_curriculum import (
    CurriculumOrchestrator,
    CurriculumLevel,
    quick_start,
)

# Create orchestrator
orchestrator = quick_start({
    'initial_capital': 100000,
    'episode_length': 1000,
    'num_seeds': 5,
})

# Set your agent
orchestrator.set_agent(your_agent)

# Start training
session = orchestrator.start_training(CurriculumLevel.LEVEL_0)

# Run episodes
for _ in range(100):
    result = orchestrator.run_episode()

# Evaluate promotion
promotion_result = orchestrator.evaluate_promotion()
```

### Implementing an Agent

```python
from trading_bot.adversarial_curriculum.curriculum_orchestrator import AgentInterface

class MyAgent(AgentInterface):
    def act(self, state: MarketState, agent_state: AgentState) -> AgentAction:
        # Your trading logic here
        # Must return an AgentAction
        
        # Risk management first
        if agent_state.current_drawdown > 0.15:
            return AgentAction.CLOSE_ALL
        
        # Your strategy
        if should_buy:
            return AgentAction.BUY_MEDIUM
        elif should_sell:
            return AgentAction.SELL_MEDIUM
        
        return AgentAction.HOLD
    
    def learn(self, experience: Dict[str, Any]):
        # Optional: Learn from experience
        pass
    
    def reset(self):
        # Reset state for new episode
        pass
```

### Full Training Run

```python
# Run full curriculum
summary = orchestrator.run_full_training(
    target_level=CurriculumLevel.LEVEL_10,
    max_sessions=100
)

print(f"Final level: {summary['final_level']}")
print(f"Reached target: {summary['reached_target']}")
print(f"Total episodes: {summary['total_episodes']}")
```

### Callbacks

```python
def on_episode_complete(result: EpisodeResult):
    print(f"Episode: Return={result.total_return:.2%}")

def on_promotion(result: PromotionResult):
    print(f"PROMOTED to Level {result.next_level.value}")

def on_failure(diagnostic: FailureDiagnostic):
    print(f"FAILURE: {diagnostic.failure_mode.name}")

orchestrator.on_episode_complete = on_episode_complete
orchestrator.on_promotion = on_promotion
orchestrator.on_failure = on_failure
```

---

## API Reference

### CurriculumOrchestrator

```python
class CurriculumOrchestrator:
    def set_agent(self, agent: AgentInterface)
    def start_training(self, from_level: Optional[CurriculumLevel] = None) -> TrainingSession
    def run_episode(self, seed: Optional[int] = None) -> EpisodeResult
    def run_ood_tests(self) -> Dict[str, List[EpisodeResult]]
    def evaluate_promotion(self) -> PromotionResult
    def run_full_training(self, target_level, max_sessions) -> Dict[str, Any]
    def get_curriculum_status(self) -> Dict[str, Any]
    def generate_curriculum_report(self) -> str
```

### AdversarialMarketEnvironment

```python
class AdversarialMarketEnvironment:
    def reset(self) -> MarketState
    def step(self, action: AgentAction) -> Tuple[MarketState, float, bool, Dict]
    def get_episode_result(self) -> EpisodeResult
```

### Key Data Classes

```python
@dataclass
class MarketState:
    timestamp: datetime
    price: float
    bid: float
    ask: float
    volume: float
    volatility: float
    regime: MarketRegime
    spread: float
    liquidity_depth: float
    price_history: np.ndarray
    correlated_assets: Dict[str, float]

@dataclass
class AgentState:
    capital: float
    position: float
    avg_entry_price: float
    unrealized_pnl: float
    realized_pnl: float
    max_drawdown: float
    current_drawdown: float
    leverage: float

@dataclass
class EpisodeResult:
    total_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    # ... and more
```

---

## Files Created

| File | Lines | Description |
|------|-------|-------------|
| `core_types.py` | ~650 | Data structures, enums, level configs |
| `market_environment.py` | ~750 | Adversarial market simulation |
| `promotion_system.py` | ~500 | Statistical validation |
| `anti_cheat.py` | ~550 | Exploit detection |
| `failure_handler.py` | ~450 | Failure analysis |
| `curriculum_orchestrator.py` | ~600 | Main controller |
| `adversarial_curriculum_demo.py` | ~500 | Demo script |
| **TOTAL** | **~4,000** | Complete system |

---

## Running the Demo

```bash
cd "c:\Users\peterson\trading bot"
python examples/adversarial_curriculum_demo.py
```

The demo shows:
1. Level progression and hardening configurations
2. Environment simulation at different levels
3. Anti-cheat detection in action
4. Promotion evaluation process
5. Failure analysis and diagnostics
6. Abbreviated full curriculum training

---

## Final Notes

### The Agent Must Survive Reality

This system is designed to produce agents that can handle real market conditions, not agents that look good on paper. Key principles:

1. **No vanity metrics** - Only statistical significance matters
2. **No shortcuts** - Exploits are detected and punished
3. **No overfitting** - OOD tests are mandatory
4. **No tail risk hiding** - Catastrophic strategies are rejected
5. **Capital preservation first** - Survival trumps profit

### If the Agent Cannot Survive Hardened Conditions, It Does Not Advance

The job of this system is not to make the agent win — it's to make the agent survive reality.

---

**Status: 100% COMPLETE - Production Ready**

*Generated: December 2024*
