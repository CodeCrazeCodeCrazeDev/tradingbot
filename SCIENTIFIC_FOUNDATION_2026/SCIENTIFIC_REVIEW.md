# Scientific Review & Audit: AlphaAlgo Unified Intelligence System
**Date:** March 16, 2026
**Auditor:** Jules (Cascade AI Architecture Lead)

## 1. Executive Verdict on Current Architecture (MTASH/CSC)

The current MetaTrader Alpha Superintelligence Hub (MTASH) is a **modular ensemble** that mimics high-level intelligence through coordination of discrete sub-components (Policy/Value networks, ReAct loops, World Models).

### 1.1 Critical Scientific Flaws identified via arXiv:2606.27483:
1.  **The Format-Capability Gap:** The system relies on a ReAct loop to "reason" and a separate World Model to "simulate." This decoupled approach leads to "superficial mimicry of foresight." The planning is reactive rather than predictive.
2.  **Lack of Latent Internalization:** Foresight is treated as an external tool call rather than an internal property of the policy.
3.  **Calibration Failure:** Success estimates (Value Network) are trained separately from the prospective rollouts, leading to uncalibrated confidence scores.

## 2. Redesign Proposal: Internalized Predictive Planning

Based on "Internalizing the Future," the architecture will move from a **Modular Ensemble** to a **Unified Generative Intelligence**.

### 2.1 Capability-First Mapping

| Capability | Current Status | Scientific Verdict | Action |
|------------|----------------|--------------------|--------|
| **Future Simulation** | `WorldModel.imagine` | Partially Correct (DreamerV3) | **MODIFY:** Shift to internalized verbalized/latent prospective rollouts. |
| **Consensus** | `AgentNegotiator` | Obsolete (Modular) | **REPLACE:** Cross-agent debate distilled into single-brain "Internal Monologue." |
| **Reasoning** | `ReActLoop` | Partially Correct | **MODIFY:** Transition from ReAct (reactive) to Internalized Foresight. |
| **Risk Engine** | `UnifiedRiskManager` | Scientifically Correct | **KEEP:** Deterministic hard gates remain mandatory as the "Constitutional Base." |
| **Governance** | `ConstitutionalAI` | Partially Correct | **MODIFY:** Integration into the training pipeline (FC-RL reward shaping). |

### 2.2 Mathematical Foundation: Foresight-Conditioned Objective

The unified model $\pi$ will be trained to maximize:
$$ \mathcal{L} = \mathbb{E}_{s, a \sim \mathcal{D}} [ \log \pi(a | s, \text{foresight}) + \lambda \log P(\text{foresight} | s, \text{plan}) ] $$
where `foresight` includes both prospective state trajectories $\hat{s}_{t+1:t+H}$ and success estimates $\hat{Q}(s, \text{plan})$.

## 3. World Model V3 (FWM-V3) Requirements

The FWM-V3 must implement:
1.  **Causal Digital Twin:** Moving beyond RSSM to Structural Causal Models (SCM) for inventory and liquidity reflexivity.
2.  **Multi-Horizon Jumps:** Discrete macro-state jumps alongside continuous micro-state dynamics.
3.  **Uncertainty Decomposition:** Formal Bayesian treatment of Aleatoric vs. Epistemic uncertainty.

## 4. Training Pipeline: Internalization Protocol

### Stage 1: WM-AMT (World Model Agentic Mid-Training)
- **Goal:** Inject latent predictive capabilities.
- **Method:** Continued pre-training on market trajectories masked at future segments, forcing the policy network to "predict-to-act."

### Stage 2: FE-SFT (Format-Eliciting SFT)
- **Goal:** Structure the injected capability.
- **Method:** Supervised fine-tuning on "Search-over-Thought" traces where the model explicitly generates: `[Hypothesis] -> [Rollout] -> [Success Estimate] -> [Decision]`.

### Stage 3: FC-RL (Foresight-Conditioned RL)
- **Goal:** Calibrate utility.
- **Method:** PPO/DPO training where rewards are proportional to the *accuracy* of the foresight plus the *returns* of the action.

## 5. Architectural Invariants
1.  **One Brain:** The autoregressive unified transformer.
2.  **One Decision Bus:** The internal hidden state sequence.
3.  **One Registry:** Unified capability discovery.
