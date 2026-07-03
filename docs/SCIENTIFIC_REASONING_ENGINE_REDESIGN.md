# AlphaAlgo Scientific Reasoning Engine: Architectural Redesign

## 1. Unified Scientific Architecture
The redesign replaces fragmented modules with a **Unified Scientific Reasoning Engine (SRE)**. Every subsystem (World Model, Research, Strategy, Risk) is now a participant in a single, circular scientific process.

### **The 11-Stage Scientific Pipeline**
1.  **Observation & Anomaly Detection**: Proactive monitoring of "Surprisal" (World Model prediction error) and "Evidential Entropy" (contradictory data in TALOS).
2.  **Question & Hypothesis Generation**: Automated conversion of anomalies into falsifiable claims (PHCE-D).
3.  **Proactive Probing (Simulation)**: Using the **V2 World Model** for latent counterfactual rollouts *before* any code or data is fetched.
4.  **Adversarial Red-Teaming**: Active generation of "Counter-Hypotheses" to find paths to failure early.
5.  **Evidence-Graph Synthesis**: Building a Bayesian evidence graph where every node is a piece of evidence and edges are probabilistic dependencies.
6.  **Experiment Design (SCM-based)**: Defining specific Structural Causal Model interventions to test.
7.  **Rigorous Validation**: Execution in the **AlphaAlgo Rigorous Backtester** (Historical) and **Paper Trade Sandbox** (Live).
8.  **Bayesian Belief Update**: Formal posterior update: $P(H|E) = \frac{P(E|H)P(H)}{P(E)}$.
9.  **Knowledge Consolidation**: Promoting validated hypotheses to the **Institutional Knowledge Graph**.
10. **Policy/Prior Injection**: Injecting new knowledge into the **Policy-Value Networks** and **World Model Priors**.
11. **Regime-Aware Monitoring**: Continuous validation of assumptions (MSOS) with automated transition to "Dormant" or "Revived" states.

---

## 2. The Unified Scientific State Machine
Hypotheses transition through 16 states based on evidence quality ($Q_e$), confidence ($C$), and uncertainty ($\sigma$).

| State | Transition Criteria |
| :--- | :--- |
| **Proposed** | $Q_e > 0$, Novelty $> 0.7$ |
| **Prioritized** | Expected Value $(EV) \times \text{Novelty}$ ranking |
| **Under Investigation** | Research Agent assigned |
| **Evidence Gathering** | TALOS active retrieval |
| **Simulated** | Latent rollout success rate $> 0.6$ |
| **Experiment Running** | Backtest/Sandbox active |
| **Supported** | Posterior $P(H|E) > 0.8$, $p\text{-value} < 0.01$ |
| **Contradicted** | Posterior $P(H|E) < 0.3$ |
| **Uncertain** | $0.3 < P(H|E) < 0.8$ or High Entropy |
| **Dormant** | Supported but Regime $R_{current} \neq R_{required}$ |
| **Revived** | Dormant and Regime $R_{current} \in R_{required}$ |
| **Merged** | Correlation $\rho(H_1, H_2) > 0.9$ and causal overlap |
| **Split** | Performance variance across regimes $> \tau$ |
| **Rejected** | Falsification condition met or $EV < \text{Cost}$ |
| **Archived** | Rejected/Superseded with immutable lineage |
| **Institutionalized** | $P(H|E) > 0.95$ over multiple regimes; integrated into Priors |

---

## 3. Promotion Hierarchy
- **Level 0 (Raw Observation)**: Transient signals and prediction errors.
- **Level 1 (Candidate)**: Formally proposed hypotheses.
- **Level 2 (Validated)**: Passed backtesting and simulation.
- **Level 3 (Research)**: High-conviction ideas undergoing refinement.
- **Level 4 (Production)**: Strategies running with real capital.
- **Level 5 (Institutional Knowledge)**: Core axioms of the World Model.

---

## 4. Persistence & Data Architecture
- **Source of Truth**: **Hypothesis Registry Service**.
- **Metadata Store (SQL)**: Tracks state, scores, and basic lineage.
- **Evidence Graph (Graph DB)**: Tracks complex relationships, dependencies, and "Merge/Split" history.
- **Event Store (Immutable JSONL)**: Every state transition and piece of evidence is an immutable event for auditability and playback.

---

## 5. Mathematical Foundation
- **Belief Update**: Recursive Bayesian Filters for real-time confidence.
- **Anomaly Detection**: Variational Free Energy (Surprisal) minimization.
- **Merge/Split**: Information-theoretic similarity (KL Divergence) and Causal Discovery (PC algorithm).
- **Uncertainty**: Epistemic (model) vs. Aleatoric (noise) decomposition.

---

## 6. Proactive Discovery & Anomaly Detection
The system monitors the **World Model's Latent State Entropy**. When entropy spikes (indicating the world model is "confused"), the **Scientific Reasoning Engine** triggers a "Question Generation" cycle:
1.  Identify the latent dimension with highest variance.
2.  Retrieve historical anomalies with similar latent signatures.
3.  Propose a "Regime Shift" or "Structural Break" hypothesis.
4.  Test via Counterfactual Intervention.
