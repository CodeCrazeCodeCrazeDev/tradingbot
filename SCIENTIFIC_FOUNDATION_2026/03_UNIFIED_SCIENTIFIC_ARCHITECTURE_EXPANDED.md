# Phase 3 — Unified Superior Scientific Architecture for AlphaAlgo UCA V6

## Executive Overview
This document specifies the unified superior architecture for AlphaAlgo UCA V6. Rather than implementing individual research papers verbatim or operating disconnected sub-systems, AlphaAlgo synthesizes the strongest principles from all eight mandatory research papers (arXiv:2605.29303, arXiv:2607.00341, arXiv:2607.01224, arXiv:2605.12061, arXiv:2605.10813, arXiv:2605.20025, arXiv:2605.17734, arXiv:2605.21482) into one seamless, non-overlapping active inference engine.

---

## 1. Unified Architecture Principles
1. **Single Authoritative Subsystem Ownership**:
   - `CognitiveSystemController` (CSC) is the **sole** active inference orchestrator.
   - `SkillRouter` is the **sole** capability router and HASP program pre-emptor.
   - `HierarchicalMemorySystem` (HMS) is the **sole** memory substrate integrating SAGE graphs and AutoMem schema migrations.
   - `MultiAgentDebateSystem` is the **sole** consensus and debate synthesis engine.
   - `EvolutionGate` is the **sole** monotone-safe evolution gatekeeper.
   - `UnifiedDecisionBus` is the **sole** shared-log backbone (`LogAct`).

2. **Contradiction Resolution & Superiority Integration**:
   - **Contradiction 1 (Exploration vs. Safety Invariants)**: Dynamic hypothesis exploration (AutoResearchClaw / DiscoLoop) is strictly bounded by deterministic pre-emptive guardrails (HASP). When market volatility $V > 0.3$, HASP pre-empts all agent reasoning and overrides the proposal to `HOLD`.
   - **Contradiction 2 (Overconfidence vs. Speed)**: Multi-agent debate consensus (NanoResearch) can produce overconfident agreement under trend alignment. DeepWeb-Bench Expected Calibration Error (ECE) bounds and post-hoc Bayesian calibration scale down agent confidence vectors whenever epistemic variance across agent votes exceeds $\sigma^2 > 0.05$.
   - **Contradiction 3 (Memory Evolution vs. Schema Stability)**: Dynamic edge weight adaptation (SAGE) is decoupled from structural schema changes (AutoMem). Schema modifications are serialized through stepwise version migrations (`v1.0` $\leftrightarrow$ `v1.1` $\leftrightarrow$ `v1.2`) with SHA-256 integrity hash verification before graph compaction.

---

## 2. Integrated 12-Stage Active Inference Pipeline

```
[Observation]
     │
     ▼
[Stage 0: Normalization & Trade ID Resolution]
     │
     ▼
[Stage 1: Perception & VFE Surprise Calculation]
     │
     ▼
[Stage 2: HMS Multi-Hop Evidence Chain Retrieval (SAGE)]
     │
     ▼
[Stage 3: HASP Volatility Pre-Emption Guardrail Check]
     │ (Vol > 0.3 ? Override to HOLD : Pass)
     ▼
[Stage 4: DiscoLoop Recurrence & Transactive Memory Internalization]
     │
     ▼
[Stage 5/6: Competing Branch Generation & Causal Simulation]
     │
     ▼
[Stage 7: AutoResearchClaw Pivot/Refine Hypothesis Selection]
     │
     ▼
[Stage 8: Optimal Decision Proposal Synthesis]
     │
     ▼
[Stage 8.5/8.6: Canonical Portfolio Risk & Governance Gates]
     │
     ▼
[Stage 9: LogAct Trade Proposal on UnifiedDecisionBus]
     │
     ▼
[Stage 10: Verification Swarm & Bounded Strategy Refinement]
     │
     ▼
[Stage 11: Immutable Shield Validation]
     │
     ▼
[Stage 12: Ledger Persistence, Shared-Log Consensus & Execution]
```

---

## 3. Subsystem Functional Architecture

### A. Strategic Brain — CognitiveSystemController (CSC)
- Implements the 12-stage active inference pipeline above.
- Integrates `DiscoLoopCell` for alternating continuous vector embeddings and discrete entity tokens.
- Manages persistent cognitive agent populations (`AlphaAgent`, `MacroAgent`, `RiskAgent`).

### B. Capability Router — SkillRouter & HASPExecutor
- Evaluates incoming market context prior to agent routing.
- Hard pre-emption on volatility $V > 0.3 \implies$ `override_to_hold`.
- Executes versioned skill programs under HASP safety invariants.

### C. Memory Substrate — HierarchicalMemorySystem (HMS) & SAGE
- Multi-hop subgraph retrieval ($R(q, n) = \text{Sim}(q, n) + \sum w_{nm} \text{Sim}(q, m)$).
- Autonomous weight evolution ($w \gets \text{clip}(w + \eta \Delta, 0.0, 1.0)$) and orphan node compaction.
- Stepwise schema migrations (`1.0` $\leftrightarrow$ `1.1` $\leftrightarrow$ `1.2`) with cryptographic checksums.

### D. Consensus & Debate — MultiAgentDebateSystem
- Multi-role adversarial debate (`MacroStrategist`, `TacticalExecutioner`, `RiskSentinel`, `DevilsAdvocate`, `RiskProsecutor`).
- Regime-aware scorecard weighting across `UP`, `DOWN`, and `SIDEWAYS` trends.
- Bayesian decision engine with epistemic uncertainty dampening.
- Falsification gate executing multi-verifier challenge evaluations.

### E. Self-Evolution — EvolutionGate
- CL-Bench Gain Metric ($G = P_{\text{cand}} - P_{\text{base}} \ge \tau_g$) for monotone update commitment.
- EKSFT compliance checking ($\tau_h = 0.8, \tau_{\text{kl}} = 0.5$).
- Automated red-teaming scenario synthesis against code diffs.
- ECE calibration drift auditing ($\Delta \text{ECE} \le 0.05$).

---

## 4. Superiority Guarantee
By integrating all eight mandatory research papers into a single closed loop, AlphaAlgo achieves:
1. Zero unhandled high-volatility tail risk (guaranteed by HASP).
2. Zero mode-collapse policy regressions (guaranteed by EKSFT & EvolutionGate).
3. Sub-quadratic multi-hop memory retrieval speed (guaranteed by SAGE).
4. Calibrated, non-overconfident decision confidence (guaranteed by DeepWeb-Bench ECE).
5. Immutable, fail-closed auditability across all capital-moving operations (guaranteed by LogAct).
