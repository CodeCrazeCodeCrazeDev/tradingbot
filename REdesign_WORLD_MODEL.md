# Redesign: Institutional-Grade Predictive Planning World Model (WM-V2)

## 1. Executive Summary
This document outlines the transition from the current JEPA-based latent transition model to a **Predictive Planning World Model** (WM-V2). Inspired by the "Internalizing the Future" (arXiv:2606.27483) paradigm, WM-V2 is designed as a capability-first architecture that reasons about multiple future market trajectories, execution dynamics, and causal interventions before recommending trading actions.

## 2. Architecture: The "Hybrid Forethought" Paradigm

The architecture separates **Numerical Prediction** from **Semantic Reasoning**, ensuring institutional-grade precision while maintaining agentic flexibility.

### 2.1. Neural Predictive Core (The Engine)
- **Backbone:** A hybrid **Transformer-Mamba (SSM)** architecture.
  - **Mamba/SSM Layers:** Handle high-frequency tick data and order book dynamics with linear scaling, capturing long-range temporal dependencies without the quadratic cost of self-attention.
  - **Transformer Blocks:** Model complex cross-asset correlations (e.g., how a 10Y Treasury move propagates through FX to Equities) using multi-head global attention.
- **Unified Cross-Asset Encoder:** A shared embedding space for Equities, Futures, FX, Commodities, Macro, and Microstructure data.
- **Multimodal Perception (L1-V2):** Processes numerical price streams, order book snapshots, and structured news events (encoded as vector primitives).

### 2.2. Internalized Capabilities (Native World Dynamics)
Unlike the legacy JEPA model, which predicted abstract latent transitions, WM-V2 "internalizes" specific market mechanics:
- **Execution Simulator:** Predicts slippage, market impact, and fill probability ($P_{fill}$) as a function of order size and current liquidity.
- **Regime Transition Model:** Explicitly models transitions between volatility (Low/Normal/High/Extreme) and liquidity (Deep/Thin/Illiquid) states.
- **Causal Dynamics Model:** Implements native `do-calculus` operators. It can simulate "What if central bank rates rise by 50bps?" or "What if our order size doubles?" by perturbing the causal graph in latent space.

### 2.3. Reasoning Interface (The Auditor)
- **LLM Layer:** A Large Language/Action Model (e.g., GPT-4o, Claude 3.5, or a specialized financial LLM) acts as the high-level planner.
- **Function:** It does NOT predict prices. It receives structured summaries (Scenarios, Uncertainty, Risks) from the Neural Core and performs:
  - **Critique:** "Scenario B assumes high liquidity, but the macro schedule suggests a gap."
  - **Strategy Selection:** Choosing the plan with the best risk-adjusted expected utility.
  - **Explanation:** Generating the reasoning trace for human/governance review.

---

## 3. Comparison: JEPA vs. Predictive Planning

| Feature | Legacy JEPA World Model | New Predictive Planning (WM-V2) |
| :--- | :--- | :--- |
| **Primary Goal** | Latent state consistency | Multi-horizon future simulation |
| **Architecture** | Joint-Embedding Encoder/Predictor | Hybrid Transformer-SSM + LLM Reasoning |
| **Foresight** | Passive next-step prediction | Active "what-if" trajectory evaluation |
| **Execution** | External/Post-hoc estimation | Internalized market-impact simulation |
| **Causality** | Correlational transitions | Native causal interventions (do-calculus) |
| **Output** | Latent vector $z_{t+1}$ | Probabilistic Scenario Set {A, B, C} + Reasoning |

---

## 4. Mathematical Justification

### 4.1. Transition from Latent Matching to Trajectory Planning
In the JEPA model, we minimized:
$$\mathcal{L}_{JEPA} = \| \text{Enc}(x_{t+1}) - \text{Pred}(z_t, a_t) \|^2 + \text{Reg}$$

In WM-V2, we maximize the **Expected Utility of Foresight**:
$$J(\theta) = \mathbb{E}_{\tau \sim P_\theta(\cdot|s_t, a_{1:H})} \left[ \sum_{h=1}^H \gamma^h R(s_{t+h}, a_{t+h}) - \beta \cdot \text{Uncertainty}(\tau) \right]$$

Where $\tau$ is a generated future trajectory. The model is trained not just to "match" the next state, but to ensure that its internal simulations $\tau$ lead to better decisions under real market rewards.

### 4.2. Uncertainty Calibration
We use **Ensemble Disagreement** and **Evidential Deep Learning** to decompose uncertainty:
- **Aleatoric (Market Noise):** Modeled as the variance of the predicted distribution.
- **Epistemic (Model Ignorance):** Modeled as the disagreement between internal heads (WM-AMT).

---

## 5. Training Pipeline: Three-Stage Specialization

### Phase 1: World Model Agentic Mid-Training (WM-AMT)
- **Goal:** Inject "market intuition."
- **Data:** 10+ years of high-frequency tick data across 50+ assets.
- **Objective:** Self-supervised prediction of market transitions, regime shifts, and execution outcomes. The model learns to internalize "if I sell $X$ units here, the price will likely move $Y$ due to order book depth."

### Phase 2: Format-Eliciting SFT (FE-SFT)
- **Goal:** Teach the model to communicate foresight.
- **Data:** Curated trajectories with "expert" reasoning summaries.
- **Output:** The model learns to produce structured JSON/DSL outputs containing `Scenario_A`, `Scenario_B`, `Risk_Assessment`, and `Confidence_Score`.

### Phase 3: Foresight-Conditioned RL (FC-RL)
- **Goal:** Align simulation with PnL.
- **Optimization:** Proximal Policy Optimization (PPO) where the policy is conditioned on the World Model's generated futures.
- **Reward:** Governance-approved Risk-Adjusted Returns (Sharpe/Sortino) penalized by calibration error (if the model's "Scenario A" was highly confident but failed to occur, it receives a heavy penalty).

---

## 6. Validation Framework

### 6.1. Simulation Fidelity (Institutional Grade)
- **Calibration Error:** Is a "90% confidence" move actually occurring 90% of the time?
- **Scenario Diversity:** Does the model generate distinct, plausible futures (Bull, Bear, Volatile) or does it collapse to the mean?
- **Causal Consistency:** If we simulate a rate hike, does the model correctly propagate the effect to bond prices and FX?

### 6.2. Financial Performance
- **Risk-Adjusted Returns:** Sharpe > 3.0, Sortino > 4.5.
- **Max Drawdown:** < 10% on institutional capital.
- **Execution Quality:** Difference between predicted slippage and actual realized slippage.

### 6.3. Engineering
- **Inference Latency:** < 50ms for multi-scenario generation.
- **Throughput:** 10,000+ simulations per second.

---

## 7. Migration Strategy

1. **Side-by-Side Shadowing:** Deploy WM-V2 in "Shadow Mode" alongside the JEPA model. Compare prediction accuracy for 1 week.
2. **Component Swap:** Replace the L1/L3 Perception/Ensemble in the `IntegratedAgentSystem` with the WM-V2 Core.
3. **Reasoning Integration:** Enable the `ReasoningTrace` capability in IAS to consume WM-V2 outputs.
4. **Governance Cutover:** Transition the `DecisionLayerService` to utilize WM-V2 scenarios for final trade validation.
5. **Sunset JEPA:** Decommission legacy JEPA modules after verification of superior V2 performance.

---

## 8. Risks and Mitigations

- **Risk:** Over-reliance on simulation (model hallucination).
- **Mitigation:** Mandatory L10 Runtime Shield checks and Uncertainty Gating. If the World Model's confidence is low, the system reverts to "Observe Only" mode.
- **Risk:** Computational Latency of multi-scenario rollouts.
- **Mitigation:** Mamba/SSM backbone for linear-time complexity and quantized inference on GPU clusters.
