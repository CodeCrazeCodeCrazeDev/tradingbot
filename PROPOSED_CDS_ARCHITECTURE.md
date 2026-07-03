# Proposed Architecture: Unified Cognitive Decision System (CDS)

This document outlines the redesign of AlphaAlgo's decision architecture into a single, evidence-driven cognitive system.

## 1. The Unified Pipeline

The CDS operates as a single, immutable pipeline. No decision bypasses any stage.

1.  **Market Data**: Raw ingest of price, volume, order book, and alternative data.
2.  **Evidence Collection (TALOS)**: Strategic coordination of data gathering, identifying missing info, and maintaining provenance.
3.  **Evidence Validation**: Deterministic and statistical checks on data integrity and "taint" status.
4.  **Hypothesis Generation (PHCE-D)**: Creation of one or more falsifiable market hypotheses based on validated evidence.
5.  **Adversarial Challenge (Adversarial Epistemology)**: Engine that attacks the hypothesis, identifying assumptions and contradictory evidence.
6.  **Epistemic Evaluation**: Hybrid mathematical framework (Bayesian, Dempster-Shafer, Info Theory) to calculate belief and uncertainty.
7.  **World Model Consistency**: Check against the latent dynamics world model to ensure the hypothesis doesn't violate known market physics.
8.  **Risk Evaluation**: Multi-dimensional risk check (Concentration, VaR, Liquidity, Catastrophic failure modes).
9.  **Governance**: Immutable validation of compliance and safety thresholds.
10. **Final Verdict (Verdict Engine)**: Synthesis of structured debate from specialist adversarial agents.
11. **Execution**: Controlled entry into the market.

## 2. Mathematical Frameworks

The CDS uses a hybrid approach:
*   **Bayesian Inference**: For recursive belief updating as new evidence arrives.
*   **Dempster-Shafer Theory**: For handling "ignorance" and conflicting evidence where Bayesian priors are unknown.
*   **Information Theory**: To measure Evidence Quality (Mutual Information) and Reasoning Entropy.
*   **Causal Inference**: To ensure the hypothesis is based on structural drivers, not just spurious correlations.
*   **Game Theory**: For the Adversarial Verdict Engine's debate synthesis (Nash Equilibrium of arguments).

## 3. Core Components Redesign

### TALOS (The Strategic Coordinator)
TALOS shifts from a "research tool" to the **Strategic Coordinator** of the decision flow. It manages the `EvidenceGraph` and triggers the adversarial reviewers.

### PHCE-D (The Evidence Graph)
PHCE-D is upgraded into a two-layer Evidence Graph:
1.  **Short-Term (Real-Time)**: In-memory `networkx` graph for active decisions.
2.  **Long-Term (Persistent)**: Knowledge graph storing decision lineage, failure modes, and provenance for self-improvement.

### Adversarial Epistemology Engine
A dedicated engine that asks 10+ critical questions for every hypothesis (e.g., "What information is missing?", "How would an adversary exploit this reasoning?").

### Adversarial Verdict Engine (The Swarm Debate)
Instead of voting, specialist agents (Bull, Bear, Risk, Macro, etc.) conduct a structured debate. The engine synthesizes disagreements using calibration scores for each agent.

## 4. Data Structures

### Unified Evidence Graph
`Evidence` -> `Claims` -> `Counterclaims` -> `Proofs` -> `Verdicts`

### Final Verdict Object
Every decision must include:
*   `belief_score`: 0.0 to 1.0
*   `uncertainty`: 0.0 to 1.0 (Entropy/Ambiguity)
*   `explanation`: Natural language reasoning trace.
*   `failure_reason`: Specific check that failed (if rejected).
*   `traceability_id`: Hash-linked proof-trace.
*   `debate_summary`: Synthesis of adversarial reviewer disagreements.

## 5. Deployment Structure
`trading_bot/core_agent_system/cds/`
*   `orchestrator.py`
*   `evidence_graph.py`
*   `epistemology_engine.py`
*   `verdict_engine.py`
*   `governance_gate.py`
*   `reviewers/` (Specialist Agents)
