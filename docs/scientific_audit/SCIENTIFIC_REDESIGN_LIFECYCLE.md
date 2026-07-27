# Scientific Redesign: Unified Hypothesis Lifecycle (AlphaAlgo 2026)

## 1. The Scientific Reasoning Engine (SRE) Core
The SRE is the central authority for the **19-Stage Reasoning Loop**. It replaces process-centric pipelines with a state-centric knowledge operating system.

### 19-Stage Reasoning Loop Implementation
1.  **Observation**: Ingests multi-modal data (Market, Sentiment, Geopolitical) via `SRE.observe()`.
2.  **Anomaly Detection**: Calculates "Surprise" (VFE) relative to GWM predictions.
3.  **Question Generation**: Formulates "Why" questions for detected anomalies.
4.  **Hypothesis Generation**: Proposes testable claims (Causal, Predictive, or Structural).
5.  **Evidence Collection**: Traces data lineage and gathers supporting/contradicting "Packets".
6.  **World Model Simulation**: Imagines trajectories in the Global World Model (GWM).
7.  **Counterfactual Generation**: Pearl's **Do-Calculus** interventions to verify causal stability.
8.  **Adversarial Debate**: Specialized agents in the **Verification Swarm** attempt to falsify.
9.  **Experiment Design**: Defines formal falsification triggers and boundary conditions.
10. **Execution**: Runs backtests, paper trades, or synthetic stress tests.
11. **Evaluation**: Computes Sharpe, DSR (Deflated Sharpe), and PSI (Population Stability Index).
12. **Bayesian Update**: Formal refinement of posterior $P(H|E)$.
13. **Confidence Calibration**: Adjusts Credal Bounds $[\underline{P}, \overline{P}]$ based on historical ECE.
14. **Knowledge Integration**: Synthesizes verified claims into the **Knowledge Graph**.
15. **Memory Consolidation**: Stores lineage in **HMS/SAGE** and indices "Lessons Learned".
16. **Policy Improvement**: Updates capital allocation, search priors, and risk weights.
17. **Continuous Monitoring**: Tracks alpha decay and drift via the **Death Clock**.
18. **Hypothesis Retirement**: Transitions to terminal states (Never deleted).
19. **Meta-Discovery**: Real-time VFE-triggered redesign of the generation logic.

## 2. Authoritative End-States (The Immutable Ledger)
Hypotheses are permanent objects in the institutional ledger. They must end in one of these states:

*   **Confirmed**: High posterior, low ambiguity, survives adversarial debate.
*   **Rejected**: Falsified by evidence or adversarial stress; moved to **Failure Memory**.
*   **Inconclusive**: Insufficient sample size or contradictory evidence; triggers Step 5.
*   **Merged**: Combined with other hypotheses to form a stronger "Theory".
*   **Split**: Broken into sub-hypotheses for specific regimes.
*   **Dormant**: Valid but currently lacks market regime support.
*   **Reactivated**: Moved from Dormant to Active when regime conditions match.
*   **Deprecated**: Superseded by better models or structural market changes.
*   **Superseded**: Replaced by a more granular or accurate hypothesis.
*   **Institutionalized**: Accepted as a core "Law" in the firm's Scientific Philosophy.

## 3. Mandatory Lineage & Provenance
Every `ScientificHypothesis` object must maintain a `HypothesisLineage` record:
*   `parent_ids`: The ancestors (e.g., academic paper ID, anomaly ID).
*   `child_ids`: Descendants created through splitting or mutation.
*   `derivation_path`: A trace of the logic (e.g., "Observation -> Surprise -> Question -> Causal Claim").
*   `immutable_hash`: A SHA-256 hash of the initial formulation to prevent "moving the goalposts".

## 4. Institutional Registry (The "Single Brain")
All sub-registries (Alpha Mining, Curiosity, PHCE-D) are replaced by a unified `InstitutionalRegistry`.
*   **Consistency**: A single UUID for a claim across its entire life.
*   **Transparency**: Any module can query the state of any hypothesis.
*   **Efficiency**: No redundant testing of the same causal structure.
