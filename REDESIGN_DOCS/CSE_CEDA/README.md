# Controlled Self-Evolution and Decision Architecture (CSE-CEDA) Study

This study details the scientific and engineering principles extracted from five pioneering 2026 paradigms in Evolvable AI (eAI) and defines their integration into AlphaAlgo:
1. **Introspection Fine-Tuning (IFT)** (arXiv:2607.14111): Self-reporting on internal state perturbations.
2. **Controlled Self-Evolution (CSE)** (arXiv:2601.07348): Sandboxed algorithmic optimization of strategy code.
3. **PEARL & Invariant-Gated Evolution (IGE)**: Governance layer restricting long-horizon self-modification via hard invariants.
4. **Controlled Evolution Decision Architecture (CEDA)**: Regime-aware champion-challenger tournament selection.

---

## 1. Transferable Engineering Principles

Rather than replicating the original papers verbatim (which would introduce massive computational bloat and duplicate code frameworks), AlphaAlgo distills the following transferable principles:

### A. Sandbox-Only Mutation (CSE)
* **Principle**: An AI system must never modify its own executing codebase online.
* **AlphaAlgo Mapping**: Mutations, parameter tunings, and model-head updates are executed purely inside isolated sandbox scopes. The live system remains immutable.

### B. Invariant-Gated Evolution (IGE)
* **Principle**: To prevent "delusion loops," reward hacking, and malicious architectural drifts, all self-evolution steps must pass through deterministic gates (Invariants) that can never be overridden by the AI agent itself.
* **AlphaAlgo Mapping**: We enforce four hardcoded **Runtime Invariants**:
  1. **Security Invariant**: No mutant code may import banned packages or execute dangerous functions (audited via AST parser).
  2. **Risk Invariant**: Mutant configurations must stay within strict risk thresholds (Max Drawdown ≤ 15%, Max Position Exposure ≤ 50%).
  3. **License Invariant**: Banned licenses (GPL, AGPL, LGPL) are completely rejected.
  4. **Validation Invariant**: Out-of-Sample (OOS) performance must exceed In-Sample (IS) baselines, ensuring no over-fitting.

### C. Champion-Challenger Tournaments (CEDA)
* **Principle**: Challenger mutations are systematically compared against active baseline Champions across a wide array of simulated market regimes.
* **AlphaAlgo Mapping**: The CEDA Decision Gate evaluates the mutant's Sharpe, win rate, and drawdown across trending, ranging, and volatile regimes before permitting promotion.

---

## 2. Integrated Architecture

EIP, ECIE, and the new **CSE-CEDA** engine cooperate inside the Research Operating System to provide an ultra-high ceiling, self-improving quantitative refinery:

```
+---------------------------------------------------------------------------------+
|                               External Intelligence                             |
|              (GitHub, arXiv, Hugging Face, Frontier Models, Creators)           |
+----------------------------------------+----------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
|                       EIP / ECIE Ingestion & Refinery                           |
|        (Discovery -> Evidence Quality Engine -> AST Security -> Distillation)   |
+----------------------------------------+----------------------------------------+
                                         | [Distilled Capability Pattern]
                                         v
+---------------------------------------------------------------------------------+
|                      CSE-CEDA Self-Evolution Sandbox                            |
|                                                                                 |
|        * InvariantGatedEvolutionEngine (Generates and audits mutations)         |
|        * CEDADecisionGate (Regime-aware tournament & validation checks)         |
+----------------------------------------+----------------------------------------+
                                         | [Approved Champion Skill]
                                         v
+---------------------------------------------------------------------------------+
|                        One Brain Production Environment                         |
|                     (Immutable, Highly-Governed Skill Router)                   |
+---------------------------------------------------------------------------------+
```

---

## 3. Validation Strategy

* **Invariant Violations**: Verifies that mutations violating security (AST check) or risk (Max Drawdown exceedance) are instantaneously purged.
* **Regime Consistency**: Assures that challenger mutations are validated over multi-regime datasets, eliminating regime-unaware optimization bias.
* **Zero Live Side-Effects**: Confirms that mutations remain sandboxed and never leak into the executing production state.
