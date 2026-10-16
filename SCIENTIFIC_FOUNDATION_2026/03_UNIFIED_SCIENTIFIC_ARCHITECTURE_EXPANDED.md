# 03 Unified Scientific Architecture (2026 Baseline Specification)

This document presents the consolidated, unified scientific architecture for the AlphaAlgo Autonomous Financial Intelligence System. Synthesized from eight mandatory post-2025 research specifications (arXiv:2605.29303 [EKSFT], arXiv:2607.00341 [DiscoLoop], arXiv:2607.01224 [CORAL/AutoMem], arXiv:2605.12061 [Search-R1/SAGE], arXiv:2605.10813 [NanoResearch], arXiv:2605.20025 [S2L/AutoResearchClaw], arXiv:2605.17734 [HASP], and arXiv:2605.21482 [DeepWeb-Bench]), this architecture outperforms any individual paper through tight cross-layer integration.

---

## Unified Multi-Layer Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                        LAYER 5: GOVERNANCE & SELF-EVOLUTION                      |
|   [EvolutionGate] (Monotone-Safe M_t+1 >= M_t)  <--->  [ImmutableShield] (Hard Veto) |
|   - EKSFT Entropy/KL Compliance                  - Real-Time Trade Veto Gate     |
|   - DeepWeb-Bench ECE Calibration Audit           - Audit Trail Signing          |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                         LAYER 1: STRATEGIC BRAIN & CSC                            |
|   [CognitiveSystemController] (12-Step Recursive Active Inference Engine)         |
|   - Sensory Surprise Minimization (VFE)          - DiscoLoop Multi-Hop Recurrence  |
|   - AutoResearchClaw Pivot/Refine Loops           - LogAct Trajectory Replay      |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                   LAYER 3: MULTI-AGENT ADVISORY & CONSENSUS                       |
|   [MultiAgentDebateSystem] (Tri-Level Specialized Debate + Adversaries)           |
|   - Macro / Tactical / Risk Agents               - 6 Adversarial Prosecutors      |
|   - Bayesian Posterior Calibrator                - SRE Falsification Gate         |
+-----------------------------------------------------------------------------------+
                       /                  |                  \
                      v                   v                   v
+-----------------------------+ +-------------------+ +-----------------------------+
| LAYER 2: ROUTING & EXEC     | | LAYER 4: MEMORY   | | LAYER 2: HASP GUARDRAILS    |
| [SkillRouter]               | | [HMS / SAGE]    | | [HASPExecutor]              |
| - S2L Latent LoRA Selection | | - Multi-Hop Graph| | - Hard Volatility Override|
| - Program Skill Mapping     | | - AutoMem Schema  | | - Invariant Checking      |
+-----------------------------+ +-------------------+ +-----------------------------+
```

---

## Detailed Architectural Layers

### Layer 1: Strategic Brain & Cognitive System Controller (`CognitiveSystemController`)
- **Primary Responsibility**: Authoritative strategic coordinator executing the 12-stage Active Inference pipeline.
- **Synthesized Mechanisms**:
  1. **Sensory Surprise Minimization**: Computes Variational Free Energy (VFE) surprise from incoming market observations.
  2. **DiscoLoop Recurrence**: Alternates continuous latent representation updates with discrete symbolic bridge tokens ($h_{k+1}, e_{k+1} = \text{DiscoLoop}(h_k, e_k, x_t)$).
  3. **AutoResearchClaw Pivot/Refine**: Evaluates competing hypotheses under causal simulation; pivots away from failure-prone branches before decision synthesis.
  4. **LogAct Decision Consensus**: Logs proposed actions as `LogAction` events onto `decision_bus` with Byzantine fault tolerance.

---

### Layer 2: Capability Routing & Execution (`SkillRouter` & `HASPExecutor`)
- **Primary Responsibility**: Maps specialized tasks to executable programs, LoRA adapters, or safety guardrails.
- **Synthesized Mechanisms**:
  1. **S2L Latent Skill Routing**: Resolves tasks to specialized Low-Rank Adaptation (LoRA) adapters using latent skill vector similarity.
  2. **HASP Program Pre-emption**: Evaluates hard safety invariants before model execution. Puts high volatility ($\text{Vol} > 0.3$) through immediate `override_to_hold` pre-emption.
  3. **Capability Conflict Resolution**: Resolves overlapping skill requests using capability taxonomy matching.

---

### Layer 3: Multi-Agent Advisory & Consensus (`MultiAgentDebateSystem` & `HeadAI`)
- **Primary Responsibility**: Evidence-first multi-perspective debate and Bayesian confidence aggregation.
- **Synthesized Mechanisms**:
  1. **Tri-Level Agent Debate**: Macro Strategist, Tactical Executioner, and Risk Sentinel engage in structured evidence-first debate.
  2. **6 Adversarial Prosecutors**: Devil's Advocate, Risk Prosecutor, Overfitting Prosecutor, Liquidity Prosecutor, Execution Prosecutor, and Data Prosecutor actively challenge proposed trades.
  3. **Correlation-Aware Bayesian Synthesis**: Computes posterior winning probability adjusted for agent correlations and epistemic variance penalties.
  4. **Falsification Gate**: Subject proposed decisions to causal, liquidity, regime, and risk verification checks before consensus finalization.

---

### Layer 4: Authoritative Memory Substrate (`HierarchicalMemorySystem` & `SAGEGraphMemory`)
- **Primary Responsibility**: Single source of truth for working, episodic, semantic graph, and transactive memory.
- **Synthesized Mechanisms**:
  1. **SAGE Self-Evolving Graph**: Dynamic MultiDiGraph storing evidence triplets with autonomous edge weight evolution ($w \leftarrow w + \eta \Delta$) and low-utility edge pruning ($w < 0.1$).
  2. **AutoMem Metamemory Schema Migration**: Sequential versioned schema migrations ($v \rightarrow v+0.1$) driven by task performance feedback without data loss.
  3. **Dynamic Memory Window**: Adaptive window sizing ($N_{\text{window}} \in [10, 500]$) balancing context retention against retrieval latency.

---

### Layer 5: Governance & Monotone Self-Evolution (`EvolutionGate` & `ImmutableShield`)
- **Primary Responsibility**: Enforces monotone-safe system self-improvement and real-time trade vetoing.
- **Synthesized Mechanisms**:
  1. **RSEA Monotone Safety Gate**: Promotes candidate code rewrites or parameter updates only when Gain $G \ge \tau$ and zero safety/latency regressions occur.
  2. **EKSFT Compliance Gating**: Verifies candidates maintain update entropy $H \ge \tau_h$ (0.8) and KL divergence drift $D_{\text{KL}} \le \tau_{\text{kl}}$ (0.5).
  3. **DeepWeb-Bench Calibration Auditing**: Verifies Expected Calibration Error (ECE) drift stays within $\le 0.05$.
  4. **Immutable Shield Veto**: Synchronous final-gate trade vetoing with cryptographic signing.

---

## Structural Principles & Guiding Invariants

1. **Strict Single Ownership**:
   - `CognitiveSystemController` is the **only** active strategic controller.
   - `SkillRouter` is the **only** capability router.
   - `HierarchicalMemorySystem` is the **only** memory substrate.
   - `EvolutionGate` is the **only** self-improvement gatekeeper.
   - `UnifiedComponentRegistry` is the **only** component registry.

2. **12-Stage Active Inference Pipeline**:
   - Stage 0: Observation Normalization & UUID Generation
   - Stage 1: Sensory Perception & VFE Surprise Minimization
   - Stage 2: HMS Evidence Chain Multi-Hop Retrieval
   - Stage 3: HASP Volatility & Skill Guardrails Check
   - Stage 4: DiscoLoop Discrete-Continuous Internalization
   - Stage 4.5: Transactive PCA Population Consultation
   - Stage 5: Competing Hypothesis Generation
   - Stage 6: Causal World Model Counterfactual Simulation
   - Stage 7: AutoResearchClaw Pivot/Refine Loop Selection
   - Stage 8: Decision Proposal Synthesis
   - Stage 8.5: Canonical Portfolio Risk Boundary Evaluation
   - Stage 8.6: Human-Layer Governance Authorization
   - Stage 9: LogAct Proposal on Unified Decision Bus
   - Stage 10: Verification Swarm Evaluation & Refinement Pass
   - Stage 11: Immutable Shield Final Veto Check
   - Stage 12: Ledger Persistence, Consensus Finalization & Order Dispatch

---

## Mathematical Safety Guarantees

1. **Monotone Safety Condition**:
   $$\text{Promote}(\text{Cand}) \iff \left( \text{Gain}(\text{Cand}) \ge \tau \right) \land \left( S_{\text{safety}} = 1.0 \right) \land \left( \Delta_{\text{latency}} \le 1.2 \times \text{Base} \right)$$

2. **EKSFT Information Bounds**:
   $$H(\theta_{\text{cand}}) \ge 0.8, \quad D_{\text{KL}}(\theta_{\text{cand}} \,||\, \theta_{\text{base}}) \le 0.5$$

3. **Calibration Drift Bound**:
   $$|\text{ECE}(\text{Cand}) - \text{ECE}(\text{Base})| \le 0.05$$
