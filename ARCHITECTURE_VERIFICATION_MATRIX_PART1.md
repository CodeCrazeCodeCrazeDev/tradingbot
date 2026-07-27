# Architecture Verification Gate: Research Compatibility Matrix (Part 1)

This document provides a detailed compatibility analysis for the 16 foundational research papers/topics.

---

## 1. HIPIF (Hierarchical Planning and Information Folding)
*   **Core contribution**: Information Folding (IF) for context-window management in long-horizon tasks.
*   **Mathematical assumptions**: Markov property holds for the "folded" (compressed) state; Information Bottleneck (IB) principle for compression.
*   **Required inputs**: Raw execution history (observations, actions, rewards), subgoal definitions.
*   **Required outputs**: Folded state representation (Semantic Update), next subgoal.
*   **Computational complexity**: $\mathcal{O}(L \log L)$ for folding; reduces downstream inference costs.
*   **Failure modes**: Information loss during folding; Strategic drift if folding is too aggressive.
*   **Dependencies**: Subgoal decomposer (Planner).
*   **Conflicts**: May conflict with "Flat Memory" approaches; requires careful integration with multi-tier memory (HMS).
*   **Financial applicability**: Compressing tick-level market data into regime-level strategic anchors.
*   **Expected ROI**: Significant reduction in token costs for 24h+ trading sessions; improved long-term goal coherence.

## 2. SocraticPO (Policy Optimization via Interactive Guidance)
*   **Core contribution**: Interactive diagnostic feedback and reward decay for reasoning-heavy RL.
*   **Mathematical assumptions**: Access to an optimal/near-optimal Teacher or Oracle; Reward $R$ is decomposable.
*   **Required inputs**: Reasoning traces, environment feedback, Teacher diagnostics.
*   **Required outputs**: Improved policy weights (or LoRA), diagnostic logs.
*   **Computational complexity**: High (multi-pass training); Inference is $\mathcal{O}(1)$ (standard forward pass).
*   **Failure modes**: Over-reliance on the Teacher; Reward hacking the decay function.
*   **Dependencies**: Strong Teacher model or Deterministic Oracle (Backtester).
*   **Conflicts**: Requires "Interactive" training, which conflicts with standard "Batch" RL unless carefully staged.
*   **Financial applicability**: Learning to trade by "diagnosing" backtest failures (e.g., SL hit due to ATR mismatch).
*   **Expected ROI**: Faster convergence of trading policies; reduced "delusional" behavior.

## 3. Skill-to-LoRA (S2L)
*   **Core contribution**: Moving procedural skills from prompts to dynamically loadable LoRA weights.
*   **Mathematical assumptions**: LoRA adapters are additive and non-interfering; Behavioral distillation matches teacher performance.
*   **Required inputs**: Skill documents (SKILL.md), behavioral demonstrations.
*   **Required outputs**: LoRA adapters, adapter router.
*   **Computational complexity**: $\mathcal{O}(1)$ for adapter switching; significantly reduces per-step token overhead.
*   **Failure modes**: Adapter interference (if multiple are active); Out-of-distribution skill failure.
*   **Dependencies**: Multi-LoRA inference engine (vLLM/LoRAX).
*   **Conflicts**: Conflicts with "Prompt-only" architectures; requires standardized skill definitions.
*   **Financial applicability**: Internalizing execution archetypes (VWAP, Arbitrage) into model weights.
*   **Expected ROI**: 50-70% reduction in per-step latency and token cost.

## 4. Agents-K1 (Knowledge Orchestration)
*   **Core contribution**: Agent-native Knowledge Graphs (Scholar-KG) for multi-hop scientific reasoning.
*   **Mathematical assumptions**: Knowledge can be represented as a directed graph of typed entities and relations.
*   **Required inputs**: Unstructured text, multimodal evidence (charts), graph schema.
*   **Required outputs**: Structured Knowledge Graph, causal linkages.
*   **Computational complexity**: $\mathcal{O}(|V| + |E|)$ for traversal; higher extraction cost.
*   **Failure modes**: Graph pollution; Entity resolution errors in sparse data.
*   **Dependencies**: Graph database (Neo4j/FalkorDB), specialized IE models.
*   **Conflicts**: Requires structured storage, conflicting with "Pure RAG" (vector-only) systems.
*   **Financial applicability**: Mapping macro indicators to market hypotheses and trade evidence.
*   **Expected ROI**: Improved reasoning provenance; ability to explain *why* a trade was taken across multiple news events.

## 5. MATM (Multi-Agent Transactive Memory)
*   **Core contribution**: Population-level artifact reuse (trajectories) for heterogeneous agents.
*   **Mathematical assumptions**: Success in one task/agent is transferable to others via trajectory demonstration.
*   **Required inputs**: Agent trajectories (observation, action, outcome).
*   **Required outputs**: Retrieved trajectory demonstrations.
*   **Computational complexity**: $\mathcal{O}(\log N)$ for retrieval.
*   **Failure modes**: Policy contagion (bad habits); retrieval noise.
*   **Dependencies**: Shared vector/KV store.
*   **Conflicts**: May conflict with "Private/Isolated" agent designs.
*   **Financial applicability**: Sharing "Lessons Learned" from a Macro agent to an Execution agent.
*   **Expected ROI**: Reduced "Discovery" time for new market regimes or strategies.

## 6. HORIZON (Failure Attribution)
*   **Core contribution**: Systematic benchmark for attributing long-horizon failures (Planning vs. Memory).
*   **Mathematical assumptions**: Failure is attributable to a discrete taxonomy; human-judge agreement is high.
*   **Required inputs**: Execution trajectories, Intrinsic Horizon $(H^*)$.
*   **Required outputs**: Failure classification, breakdown level.
*   **Computational complexity**: Low (offline scoring).
*   **Failure modes**: Judge bias; Incomplete taxonomy.
*   **Dependencies**: High-capability "Judge" model.
*   **Conflicts**: None (Diagnostic tool).
*   **Financial applicability**: Determining if a strategy failed because the "Plan" was bad or the "Market Data" was stale.
*   **Expected ROI**: Targeted engineering improvements based on quantified failure data.

## 7. CL-Bench (Continual Learning Bench)
*   **Core contribution**: Gain Metric for isolating online learning from pre-trained knowledge.
*   **Mathematical assumptions**: Stateless vs. Stateful performance comparison is a valid proxy for learning.
*   **Required inputs**: Sequential task instances, system state.
*   **Required outputs**: Gain Metric ($G$).
*   **Computational complexity**: Low.
*   **Failure modes**: Stability-Plasticity dilemma; Overfitting.
*   **Dependencies**: Evaluation harness with task schedules.
*   **Conflicts**: None.
*   **Financial applicability**: Measuring if the "Market Student" is actually learning from today's trades.
*   **Expected ROI**: Protection against "Lucky" performance; verification of genuine adaptation.

## 8. Self-Harness (Framework Optimization)
*   **Core contribution**: Self-optimizing agent scaffolding (tools, prompts, checklists).
*   **Mathematical assumptions**: Local harness changes can lead to global performance improvements.
*   **Required inputs**: Failure logs, current harness definition.
*   **Required outputs**: Optimized harness (revised tool schema, new checklists).
*   **Computational complexity**: High (requires parallel validation of candidate harnesses).
*   **Failure modes**: Over-complexity; Security/Safety regressions.
*   **Dependencies**: Validation set of "Held-out" task instances.
*   **Conflicts**: Requires write-access to its own "Rules," which must be guarded by Governance.
*   **Financial applicability**: Autonomously refining pre-trade verification checklists.
*   **Expected ROI**: 15-50% performance gain on fixed models.
