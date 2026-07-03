# AlphaAlgo Redesign: Unified Cognitive Architecture (UCA)

## 1. Executive Summary
This redesign replaces the fragmented, task-based orchestration of AlphaAlgo with a **Unified Cognitive Architecture (UCA)**. Inspired by **Agents-A1** and **Einstein World Models**, the system shifts from *stateless execution* to *persistent autonomous cognition*.

Key shifts:
- **Agents**: From task-executors to **Persistent Cognitive Agents (PCA)** solving long-horizon problems (alpha discovery, risk adaptation).
- **World Model**: From next-step predictors to **Generative World Models (GWM)** providing "inspectable future rollouts" and counterfactual sandboxes.
- **Integration**: Tightly coupled "Thought-Simulation-Action" loops where simulation replaces guessing.

---

## 2. Agent Architecture Redesign: Persistent Cognitive Agents (PCA)

### 2.1 The "One Agent" Philosophy
All specialists (Macro, Risk, Execution) inherit from a single, generic `PersistentCognitiveAgent` base. Specialization is emergent, driven by unique **Objectives, Tools, and Memory Scopes**.

### 2.2 PCA Internal Components
- **Epistemic Core**: Maintains the agent's current "Belief State" about the market/task.
- **Goal Hierarchy**: A recursive tree of goals (e.g., "Maximize Sharpe" -> "Reduce Correlation" -> "Hedge JPY exposure").
- **Dynamic Plan Manager**: Generates and evolves long-horizon plans (days to months).
- **Verification Engine**: Self-monitors performance against predictions.
- **Continual Learner**: Updates local policies and "Lessons Learned" after every action.

### 2.3 The K-A-O (Knowledge-Action-Observation) Loop
Every PCA runs a continuous cycle:
1. **Observe**: Ingest raw data + agent messages.
2. **Retrieve**: Query Hierarchical Memory for relevant past context.
3. **Reason**: Perform chain-of-thought analysis on the delta between goals and state.
4. **Simulate**: Query the GWM to test plan branches (A, B, C).
5. **Decide**: Select the branch with the best risk-adjusted outcome.
6. **Act**: Execute via tool/broker.
7. **Verify**: Compare real outcome vs. simulation.
8. **Learn**: Update Epistemic State and Semantic Memory.

---

## 3. World Model Redesign: Generative World Model (GWM)

### 3.1 The "Dreamer" as a Sandbox
The GWM is no longer just a latent state transitioner. It is a **Future Simulator** that generates inspectable trajectories.

### 3.2 GWM Capabilities
- **Multi-Horizon Rollouts**:
    - *Tick-Level* (Execution): Microstructure/Slippage.
    - *Minute/Hour* (Market): Liquidity/Volatility regimes.
    - *Daily/Monthly* (Macro): Regime transitions/Causal interactions.
- **Counterfactual Engine**: Implements **Pearl’s Do-Calculus**. Agents ask: *"What if liquidity drops 50% during my rebalance?"*
- **Uncertainty Calibration**: Provides entropy-based confidence scores for every rollout branch.

---

## 4. Integration Architecture: The Unified Brain

### 4.1 Unified Orchestrator
Consolidates `MasterOrchestrator`, `IAS`, and `MetaOrchestrator` into a single **Cognitive System Controller**. It manages:
- **Registry**: Controlled objects and PCA lifecycle.
- **A2A Bus**: Asynchronous agent-to-agent communication.
- **Governance Gate**: Final safety check for all real-world actions.

### 4.2 Cognitive Workflow
- **Observation** → **PCA Reasoning** → **GWM Simulation (Sandboxing)** → **Debate (Verdict Engine)** → **Execution**.

---

## 5. Hierarchical Memory System (HMS)

Replaces fragmented JSON storage with a 6-tier hierarchy:
1. **Working Memory**: Real-time context (high churn).
2. **Episodic Memory**: Raw traces of specific trade/research sessions.
3. **Semantic Memory**: Distilled facts and market relationships.
4. **Procedural Memory**: "How-to" policies for execution and analysis.
5. **Research Memory**: Persistent hypotheses and experimental results.
6. **Institutional Knowledge**: Long-term strategic alpha and risk bounds.

---

## 6. Capability Comparison

| Feature | Current Implementation | Redesigned (UCA) |
| :--- | :--- | :--- |
| **Agent State** | Largely stateless; task-based. | Persistent; goal-oriented; long-lived. |
| **World Model** | Latent transition (DreamerV3 style). | Multi-path simulation (EWM style). |
| **Reasoning** | Heuristic ReAct templates. | Simulation-grounded counterfactuals. |
| **Planning** | Fixed search depth (MCTS). | Dynamic horizon scaling (Research/Strategy). |
| **Learning** | Simulated "Self-Play" (Random). | Grounded Continual Learning (Real Data). |
| **Memory** | JSON-based fragmented tiers. | 6-Tier Hierarchical Persistent Store. |

---

## 7. Mathematical Justification

### 7.1 Active Inference (Agents)
Agents minimize **Variational Free Energy** ($\mathcal{F}$). This unified framework combines:
- **Exploitation**: Maximizing expected utility.
- **Exploration**: Minimizing epistemic uncertainty (seeking information).

### 7.2 Causal Do-Calculus (World Model)
The World Model uses **Structural Causal Models (SCM)**. Interventions are modeled as:
$$P(Y | do(X=x))$$
Allowing the agent to simulate market impacts of its own actions or external shocks without confounding bias.

### 7.3 Information Bottleneck (Memory)
Memory distillation uses the **Information Bottleneck Principle**, preserving the most "predictive" information about future rewards while discarding noise.

---

## 8. Implementation Roadmap

### Phase 1: PCA & GWM Core (Foundation)
- Implement `PersistentCognitiveAgent` base class.
- Upgrade `FWM_DigitalTwin` to `GenerativeWorldModel` with multi-path rollouts.
- Establish the Hierarchical Memory persistent store (SQLite/PostgreSQL).

### Phase 2: Consolidation (The One Brain)
- Deprecate `MasterOrchestrator` and `MetaOrchestrator`.
- Re-route all logic through the `CognitiveSystemController`.
- Ground all RL/Self-Play in the `RigorousBacktest` environment.

### Phase 3: Horizon Scaling & Specialist Emergence
- Instantiate specialist PCAs (Macro, Liquidity, Risk).
- Enable long-running "Research Sessions" where agents share context over weeks.
- Implement the "Thought Sandbox" integration.

### Phase 4: Validation & Hardening
- Run the "System Validator" against intelligence/calibration metrics.
- Perform "Red Team" safety testing on PCA autonomous modifications.

---

## 9. Validation Framework

### Agent Metrics
- **Horizon Depth**: Max duration of a successful autonomous goal.
- **Reasoning Calibration**: Correlation between "Thought Confidence" and "Outcome Success".

### World Model Metrics
- **Rollout Fidelity**: Error between simulated branches and historical "Realized Path".
- **Counterfactual Accuracy**: Ability to predict regime shifts after interventions.

### Trading Metrics
- **Expectancy Ratio**: Profit per unit of risk.
- **Systematic Robustness**: Performance across unseen market regimes.
