# Scientific Redesign: UCA-2026 Hypothesis Lifecycle

## 1. Unified Architectural Specification

The redesign unifies PHCE-D, SRE, and CSC into a single, cohesive **Scientific Reasoning Engine (SRE)**. The core philosophy is that "every prediction is a hypothesis, and every hypothesis must survive a 19-step gauntlet."

### The 19-Step Autonomous Scientific Lifecycle

| Step | Operation | Primary Actor | Output |
|------|-----------|---------------|--------|
| 1 | **Observation** | Data Ingestion | Raw Signal/Anomaly |
| 2 | **Anomaly Detection** | World Model | Surprise Vector ($\nabla VFE$) |
| 3 | **Question Generation** | Meta-Reasoning | Research Question |
| 4 | **Hypothesis Gen** | Hypothesis Engine | Falsifiable Claim (ScientificHypothesis) |
| 5 | **Evidence Collection** | Evidence Intake | Cross-Domain Evidence Packet |
| 6 | **World Model Sim** | GWM | Simulated Futures |
| 7 | **Counterfactual Gen** | Causal Engine | Intervention Results (Do-calculus) |
| 8 | **Adversarial Debate** | Verifier Swarm | Multi-Agent Critique |
| 9 | **Experiment Design** | Researcher | Test Methodology (Scenario Set) |
| 10| **Execution** | Backtester/Paper | Performance Metrics |
| 11| **Evaluation** | Epistemology | Credal Bounds / Belief Score |
| 12| **Bayesian Update** | Bayesian Core | Updated Posterior $P(H\|E)$ |
| 13| **Confidence Calib** | Calibration Mon | ECE-Adjusted Confidence |
| 14| **Knowledge Integ** | Semantic Memory | HMS Tier 2/3 Nodes |
| 15| **Memory Consolid** | Institutional Mem | HMS Tier 5 Permanence |
| 16| **Policy Improv** | SkillRouter | Execution Policy Update |
| 17| **Continuous Mon** | Drift Monitor | Drift Assessment |
| 18| **Hypothesis Retire** | Governance Gate | End-State Assignment |
| 19| **Auto-Discovery** | Discovery Engine | New Research Objectives |

## 2. Mandatory End-States

No hypothesis simply "disappears." Every entity must terminate in one of these 10 states:

1.  **Confirmed**: Passed all 17 steps with $P(H\|E) > 0.95$.
2.  **Rejected**: Falsified by evidence or adversarial debate.
3.  **Inconclusive**: Insufficient evidence to decide; kept for future observation.
4.  **Merged**: Found to be a subset or duplicate of another hypothesis.
5.  **Split**: Refined into two or more specialized hypotheses (e.g., regime-specific).
6.  **Dormant**: Valid but regime is not currently active.
7.  **Reactivated**: Moved from Dormant/Inconclusive back to Active.
8.  **Deprecated**: Superseded by a more accurate model/hypothesis.
9.  **Superseded**: Replaced by a hypothesis with higher explanatory power.
10. **Institutionalized**: Promoted to core system invariant (Production).

## 3. Provenance and Lineage

Every `ScientificHypothesis` carries an immutable `HypothesisLineage` object containing:
- **Parent IDs**: Link to previous versions or related hypotheses.
- **Data Provenance**: Hashes of all evidence packets used for evaluation.
- **Actor Trace**: IDs of all agents/modules that modified or evaluated it.
- **Regime Fingerprint**: Market conditions at each lifecycle transition.
