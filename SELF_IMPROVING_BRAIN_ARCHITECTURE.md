# SELF_IMPROVING_BRAIN_ARCHITECTURE.md

This document defines the conceptual and concrete target architecture of AlphaAlgo's self-improving cognitive system. It outlines the strict segregation between Runtime Intelligence and the Evolution/Research Layer, governed by an immutable safety layer.

---

## 1. Architectural Topology

The system is organized as a hierarchical, closed-loop cognitive structure where runtime decision execution is kept strictly isolated from the code modification and evolutionary search spaces.

```
                ┌────────────────────────────────────────────────────────┐
                │                     GOVERNANCE LAYER                   │
                │     - Validates and stores immutable safety cases      │
                │     - Governs overall promotion / rollback rules       │
                └───────────────────────────┬────────────────────────────┘
                                            │
                ┌───────────────────────────▼────────────────────────────┐
                │                     COGNITIVE BRAIN                    │
                │     - Active Inference Loop (Discrete & Continuous)    │
                │     - Information Folding Buffer (Context Slices)      │
                │     - Associative SAGE Graph Memory & AutoMem Schema   │
                └───────────────────────────┬────────────────────────────┘
                                            │
                ┌───────────────────────────▼────────────────────────────┐
                │                     EXECUTION / RISK                   │
                │     - Flat and Nested Program Functions (HASP Guard)   │
                │     - Immutable Shield Verification (Veto Power)       │
                └───────────────────────────┬────────────────────────────┘
                                            │
                ┌───────────────────────────▼────────────────────────────┐
                │                   OBSERVATION & AUDIT                  │
                │     - LogAct Shared-Log Backbone (Event Bus)           │
                │     - High-Resolution Latency and Entropy Tracing      │
                └───────────────────────────┬────────────────────────────┘
                                            │
                ┌───────────────────────────▼────────────────────────────┐
                │                   EVOLUTION / RESEARCH                 │
                │     - Diagnosis: Detects logic & calibration drop      │
                │     - Hypothesis: Formulates scientific solutions      │
                │     - Experimentation: Champion-Challenger validation  │
                │     - Evaluation & Promotion: Held-out performance     │
                └────────────────────────────────────────────────────────┘
```

---

## 2. Segregation of Concerns

### A. Runtime Intelligence Layer
The runtime engine executes in-context, real-time trading signals, portfolio optimizations, and risk mitigations. It operates with strict predictability, bounded compute constraints, and determinism.
- **Perception**: Ingests real-time tick and order-book snapshots from SQLite.
- **State Representation**: Couples continuous state latents with discrete quantized regime tokens (DiscoLoop).
- **Reasoning**: Multi-hop associative retrieval across the Evidence Graph.
- **Planning**: Bounded search and information folding to prevent strategic drift over long horizons.
- **Execution**: Direct trade placement routed through Mt5 and cTrader adapters.
- **Risk Gate**: Flat and nested executable guardrails (HASP Program Functions) that immediately veto dangerous orders.

### B. Evolution / Research Layer
The evolution engine operates completely offline or asynchronously in an isolated, multi-processed sandbox. It has zero direct access to the live execution adapters or portfolio books.
- **Diagnosis**: Monitored anomalies (prediction errors, calibration drift) trigger weak-state flags.
- **Hypothesis Generation**: Formulates mathematical and parameter adjustments.
- **Candidate Generation**: Spawns isolated code variants under a strictly limited Abstract Syntax Tree (AST) analyzer.
- **Experimentation**: Executes the Challenger in historical replay environments using real tick-data.
- **Falsification Gate**: subjects the challenger to adverse testing (volatility shocks, stale memory, corrupt parameters).
- **Promotion**: If and only if the Challenger beats the Champion on the hold-out dataset with statistical significance, the upgrade is staged for Governance approval.

---

## 3. Mathematical Formulation (Active Inference & Free Energy Minimization)

The Cognitive Brain's runtime is framed under Active Inference and the Free Energy Principle. The agent acts to minimize Variational Free Energy ($VFE$) to align its internal beliefs (generative model) with environmental observations, and minimizes Expected Free Energy ($EFE$) for future planning.

### A. Variational Free Energy (VFE)
The Variational Free Energy $F$ at time step $t$ given observation $o_t$ and internal state $s_t$ under variational belief $q(s_t)$ is:

$$F = \mathcal{D}_{KL}\left(q(s_t) \parallel p(s_t)\right) - \mathbb{E}_{q(s_t)}\left[\log p(o_t \mid s_t)\right]$$

To calculate surprise dynamically during market regime transitions:

$$VFE_{Surprise} = -\log \sum_{s} p(o_t \mid s) p(s \mid o_{t-1})$$

### B. Expected Free Energy (EFE)
For future planning, the agent evaluates the expected path $\pi$. The Expected Free Energy $G(\pi)$ is:

$$G(\pi) = \sum_{\tau} \mathbb{E}_{q(o_{\tau}, s_{\tau} \mid \pi)}\left[\log q(s_{\tau} \mid \pi) - \log p(o_{\tau}, s_{\tau})\right]$$

This decomposes into **Ambiguity Minimization** (epistemic value) and **Preference Satisfaction** (instrumental value):

$$G(\pi) \approx \underbrace{\mathbb{E}_{q(s_{\tau} \mid \pi)}\left[H(o_{\tau} \mid s_{\tau})\right]}_{\text{Ambiguity (Epistemic)}} - \underbrace{\mathbb{E}_{q(o_{\tau} \mid \pi)}\left[\log p(o_{\tau})\right]}_{\text{Preference (Instrumental)}}$$

The evolution engine uses VFE and surprise histories as primary diagnostic signals. An escalating VFE indicates structural failure of the current world model, invoking the recursive self-improvement pipeline.

---

## 4. Immutable Safety and Control Invariants

To avoid unconstrained self-modification and functional drift, the system enforces the following boundaries:
1. **Immutable Code Anchors**: The core state tracking loops, risk engines, and promotion validators cannot write to themselves or self-modify.
2. **Deterministic Veto (HASP Program Functions)**: Natural language directives are advisory. Safety checks are compiled as flat, fast, non-bypassable executable Python guardrails.
3. **AST Filtering**: Proposed candidate changes are parsed through an AST compiler. Any import of `os`, `sys` execution, raw `exec`, `eval`, or untrusted network calls is immediately blocked and rejected.
4. **Byzantine Isolation**: If a Challenger or child agent crashes or exhibits invalid behavior, the exception is caught, logged in the decision provenance, and the candidate is immediately dropped and blacklisted.
