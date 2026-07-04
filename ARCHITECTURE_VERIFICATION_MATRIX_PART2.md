# Architecture Verification Gate: Research Compatibility Matrix (Part 2)

---

## 9. RSEA (Recursive Self-Evolving Agents)
*   **Core contribution**: Monotone-safe recursive improvement via held-out selection.
*   **Mathematical assumptions**: Progress is measurable via a loss function; held-out data prevents overfitting.
*   **Required inputs**: Current strategy/skills, recent success/failure traces, validation data.
*   **Required outputs**: Mutated (improved) strategy/skills.
*   **Computational complexity**: High (requires extensive out-of-sample testing).
*   **Failure modes**: Evolution stagnation; local minima.
*   **Dependencies**: Immutable "Evolution Gate" (Safety layer).
*   **Conflicts**: Requires a "Held-out" environment, which may be difficult to maintain for live markets (requires high-fidelity simulation).
*   **Financial applicability**: Ensuring AlphaAlgo only "commits" strategy changes that pass strict backtests.
*   **Expected ROI**: Long-term self-healing and performance growth without human intervention.

## 10. Memory Survey (WMR Loop)
*   **Core contribution**: Formalizing the Write-Manage-Read loop and Hierarchical Memory architecture.
*   **Mathematical assumptions**: Utility-based retrieval ($U$); entropy-based consolidation.
*   **Required inputs**: Stream of observations/events.
*   **Required outputs**: Retrieved context, consolidated knowledge.
*   **Computational complexity**: $\mathcal{O}(N \log N)$ for management/indexing.
*   **Failure modes**: Memory drift (stale facts); Retrieval noise.
*   **Dependencies**: Persistence layer (HMS).
*   **Conflicts**: Integrates well with most architectures.
*   **Financial applicability**: Moving market events from "Working Memory" to "Institutional Knowledge."
*   **Expected ROI**: Improved relevance of retrieved context; reduced memory costs.

## 11. CWMI (Causal World Model Induction)
*   **Core contribution**: Inducing explicit Structural Causal Models (SCMs) for counterfactual reasoning.
*   **Mathematical assumptions**: Environment follows a DAG structure; Pearl's Do-Calculus is applicable.
*   **Required inputs**: Observational market data, interventional traces (e.g., historical large orders).
*   **Required outputs**: Causal DAG, predicted outcomes under intervention $do(X)$.
*   **Computational complexity**: Exponential in node count (requires heuristic/score-based approximation).
*   **Failure modes**: Unobserved confounders; incorrect causal directions.
*   **Dependencies**: Graph discovery algorithms.
*   **Conflicts**: May conflict with "Black-box" simulators; requires explicit causal assumptions.
*   **Financial applicability**: Simulating market impact and tail-risk interventions.
*   **Expected ROI**: Robust risk management; ability to simulate "What if" events never seen in history.

## 12. Active Inference (VFE Principle)
*   **Core contribution**: Variational Free Energy (VFE) as a unified objective for perception and action.
*   **Mathematical assumptions**: Variational approximation $q(s)$ is tractable; Markov Blankets define boundaries.
*   **Required inputs**: Stream of observations $o$, prior goals $C$.
*   **Required outputs**: Updated beliefs $q(s)$, policy selection $\pi$.
*   **Computational complexity**: Medium (with variational approximations).
*   **Failure modes**: Belief divergence; overly conservative behavior (surprise-avoidance).
*   **Dependencies**: Hierarchical Generative Model.
*   **Conflicts**: Fundamentally replaces standard Reward-maximization (RL) with Surprise-minimization (VFE).
*   **Financial applicability**: A system that "Acts to reduce Portfolio Surprise" while "Exploring for Alpha."
*   **Expected ROI**: Persistent, self-organizing behavior; natural balance of exploration/exploitation.

## 13. Reward Hacking Safety
*   **Core contribution**: Immutable Shield and Multi-Objective Red-Teaming for autonomous agents.
*   **Mathematical assumptions**: Proxy rewards $\hat{R}$ will inevitably diverge from true intent $R$ in complex spaces.
*   **Required inputs**: Agent action logs, independent risk/compliance oracles.
*   **Required outputs**: Pass/Fail gate decisions.
*   **Computational complexity**: Low.
*   **Failure modes**: False positives (blocking valid trades); Over-restriction.
*   **Dependencies**: Non-bypassable deterministic gates.
*   **Conflicts**: Directly restricts the "Self-Evolution" loop to prevent safety bypasses.
*   **Financial applicability**: Enforcing hard exposure limits regardless of what the LLM "reasons."
*   **Expected ROI**: Critical; prevents catastrophic losses due to "delusional" optimization.

## 14. PT-RAG (Parametric-Token RAG)
*   **Core contribution**: Hybrid parametric (activation-level) and token-level retrieval.
*   **Mathematical assumptions**: Knowledge can be efficiently encoded into lightweight adapters (parametric).
*   **Required inputs**: Retrieved evidence, base model hidden states.
*   **Required outputs**: Knowledge-augmented activations.
*   **Computational complexity**: Faster inference for long contexts; requires extra weight storage.
*   **Failure modes**: Interference with base model reasoning; implementation complexity.
*   **Dependencies**: Model-internal access (e.g., LoRA injection points).
*   **Conflicts**: Technical complexity conflicts with simple, platform-independent RAG.
*   **Financial applicability**: Providing real-time "Market Intuition" without context saturation.
*   **Expected ROI**: Faster, more stable reasoning in data-dense market environments.

## 15. Strategic Decision Intelligence (Bayesian DI)
*   **Core contribution**: Wrapping LLM reasoning in Bayesian Decision Theory.
*   **Mathematical assumptions**: LLM outputs can be calibrated into valid probability distributions.
*   **Required inputs**: LLM reasoning traces, statistical priors, utility function.
*   **Required outputs**: Calibrated Expected Value (EV), optimal decision $a^*$.
*   **Computational complexity**: Medium (sampling-heavy).
*   **Failure modes**: Mis-specified priors; poor probability calibration.
*   **Dependencies**: Calibration engine.
*   **Conflicts**: Conflicts with naive "Majority Vote" or "Single Pass" LLM decisions.
*   **Financial applicability**: Ensuring trade sizing and execution are driven by calibrated EV, not just "Sentiment."
*   **Expected ROI**: Institutional-grade risk-adjusted returns.

## 16. Effective Agents (Anthropic Patterns)
*   **Core contribution**: Prioritizing robust Workflows and Evaluator-Optimizer loops over free-form Swarms.
*   **Mathematical assumptions**: Sequential patterns are more reliable and converge faster for most tasks.
*   **Required inputs**: Task definition, tool schema.
*   **Required outputs**: Final task output.
*   **Computational complexity**: Low-Medium (deterministic).
*   **Failure modes**: Lack of flexibility in novel scenarios.
*   **Dependencies**: Composable workflow nodes.
*   **Conflicts**: Rejects the "Free-form Swarm" as a primary design pattern.
*   **Financial applicability**: Replacing mock swarms with strict Trading SOPs.
*   **Expected ROI**: Highest; dramatic improvement in system reliability and debuggability.
