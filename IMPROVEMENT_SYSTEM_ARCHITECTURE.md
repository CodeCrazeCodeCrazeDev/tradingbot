# Architecture Design: Unified Self-Improvement Hub (USIH)

## 1. Core Philosophy
The USIH treats the entire trading system as a **Self-Optimizing Agent**. It moves beyond simple "self-play" (RL for weights) to "Structural Evolution" (RL for code, workflows, and reasoning).

## 2. High-Level Components

### 2.1 Unified Improvement Registry (UIR)
- **Role:** The "Source of Truth" for every proposed change.
- **Data Structure:**
  ```python
  {
      "improvement_id": "IMP-2026-001",
      "type": "META | TRADING | CODE",
      "domain": "reasoning | alpha | workflow",
      "source": "MultidimensionalAgent | SwarmController | SelfPlayLoop",
      "proposal": {...},
      "status": "candidate | shadow | production | rejected",
      "evidence": {
          "reasoning_score": 0.85,
          "backtest_sharpe": 2.1,
          "p_value": 0.01
      },
      "version_link": "git_commit_hash | model_v4"
  }
  ```

### 2.2 Hypothesis & Experiment Engine (HEE)
- **Role:** Translates abstract "Weaknesses" into concrete "Experiments".
- **Workflow:**
  1. **Weakness Detection:** Analyzes `MemorySystem` and `ReasoningTrace` for patterns of failure.
  2. **Hypothesis Generation:** Uses Multidimensional modules (Physics, Bio) to propose a fix.
  3. **Experiment Design:** Parameters for the `DockerVerificationSandbox` or `Backtester`.

### 2.3 Reasoning & Quality Evaluator (RQE)
- **Role:** Scores the "Meta-Intelligence" of the system.
- **Metrics:**
  - **Goal Alignment:** Did the agent's plan solve the original prompt?
  - **Tool Efficiency:** Were the minimum necessary tools used?
  - **Trace Coherence:** Is the reasoning logically sound?

### 2.4 Docker Verification Sandbox (DVS)
- **Role:** The "Executioner" of code-level changes.
- **Workflow:**
  1. Clones the current branch.
  2. Applies proposed patch.
  3. Runs `pytest` suite.
  4. Runs "Alpha Backtest".
  5. Returns a `ValidationReport`.

## 3. The Unified Loop (Standard Operating Procedure)

1. **Observe:** `MultidimensionalResearchAgent` detects a correlation between "Biological Circadian Rhythms" and FX market volatility.
2. **Identify:** `HEE` identifies that the current `VolatilityPlanner` ignores time-of-day dynamics.
3. **Hypothesize:** `HEE` poses: "Adding a circadian-weighting factor to the volatility model will reduce drawdown during NY-London overlap."
4. **Experiment:** `DVS` runs a backtest with the new factor.
5. **Evaluate:** `RQE` confirms the reasoning is sound; `Backtest` shows Sharpe +15%.
6. **Keep/Reject:** `ImprovementGatekeeper` promotes the improvement to `Shadow`.
7. **Update:** `UIR` updates the global system state; `MemorySystem` records the "Circadian Rule" in Semantic Memory.

## 4. Safety Boundaries

- **The Red Line:** No improvement can modify `AntiRewardHacking`, `ConstitutionalAI`, or `ImprovementGatekeeper`.
- **The Quarantine:** New code improvements must run in `Shadow` mode for 100 live market cycles before being considered for full production.
- **The Human Gate:** All `CODE` type improvements require an explicit `approve_improvement` signal from the user initially.

## 5. Affected Files (Target Architecture)

- `trading_bot/core_agent_system/improvement/registry.py` (New)
- `trading_bot/core_agent_system/improvement/orchestrator.py` (New)
- `trading_bot/core_agent_system/improvement/evaluator.py` (New)
- `trading_bot/core_agent_system/improvement/sandbox.py` (New)
- `trading_bot/core_agent_system/integrated_system.py` (Modified to hook the loop)
- `trading_bot/core_agent_system/master_orchestrator.py` (Modified for RQE feedback)
- `trading_bot/world_model/latent_dynamics.py` (Modified for Uncertainty integration)
