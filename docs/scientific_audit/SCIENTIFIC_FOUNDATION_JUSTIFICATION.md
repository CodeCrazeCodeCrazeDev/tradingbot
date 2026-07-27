# Scientific Foundation: Justification, Validation & Roadmap

## 1. Mathematical Justification

### 1.1 Variational Active Inference (VAI)
The global objective is the minimization of **Variational Free Energy (VFE)**, denoted as $F$.
A hypothesis $h$ is selected to minimize the expected free energy $G(h)$ for future observations:
$$G(h) \approx \sum_{\tau} E_{q(s_\tau, o_\tau | h)} [\ln q(s_\tau | h) - \ln p(s_\tau, o_\tau)]$$
This ensures the system balances **Epistemic Value** (searching for new information) and **Extrinsic Value** (expected utility/profit).

### 1.2 Recursive Bayesian Synthesis
We replace simple performance averaging with a **Recursive Bayesian Filter**. For each new evidence packet $E$, the posterior $P(H|E)$ is updated:
$$P(H|E) = \frac{P(E|H)P(H)}{P(E)}$$
We use **Credal Sets** to represent uncertainty, where the "Ambiguity" is the width of the interval $[\underline{P}, \overline{P}]$.

### 1.3 Causal Stability (Pearl's Do-Calculus)
To avoid "Correlation Hacking", we enforce interventional logic:
$$P(Y | do(X)) = P(Y | X, \text{mechanism stable})$$
Step 7 (Counterfactuals) uses the GWM to simulate $do(X)$ to ensure $X \rightarrow Y$ is not a spurious artifact of a common cause $Z$.

## 2. Validation Framework (Metrics of Success)

### 2.1 Hypothesis Quality (HQ)
$$HQ = \frac{Accuracy \times Robustness}{Uncertainty \times Ambiguity}$$
High HQ hypotheses are promoted to Level 4 (Production).

### 2.2 Research Efficiency (RE)
$$RE = \frac{\text{Confirmed Hypotheses}}{\text{Compute Hours} + \text{Failed Trials}}$$
Measures the "Return on Compute" for the discovery engines.

### 2.3 Economic Value (EV)
$$EV = \text{PnL}(h) - \text{CostOfDiscovery}(h) - \text{Slippage}(h)$$
Ensures that the scientific discovery remains economically viable.

### 2.4 Calibration Score (ECE)
Expected Calibration Error (ECE) measures how well predicted confidence matches realized accuracy. A system with ECE > 0.15 triggers an automated **Redesign Event** (Step 19).

## 3. Migration Roadmap (Shadow to Light)

### Phase 1: Foundation (Weeks 1-2)
*   Deploy unified `ScientificHypothesis` data model.
*   Initialize the global `InstitutionalRegistry`.
*   Connect SRE 19-step state machine to HMS for lineage logging.

### Phase 2: Orchestration (Weeks 3-6)
*   **Shadow Mode**: SRE observes existing `PHCE-D` and `AlphaMining` outputs.
*   Calculate "Shadow Decisions" and log VFE scores for current strategies.
*   Implement `FailureMemory` indexing for rejected legacy alphas.

### Phase 3: Authority (Weeks 7-10)
*   Enable **Gateway Veto**: SRE can block promotions if HQ < threshold.
*   Full integration of `CausalWorldModel` for Step 7.
*   Activate the **Verification Swarm** for Step 8 Adversarial Debate.

### Phase 4: Full Autonomy (Weeks 11+)
*   Enable Step 19: **Recursive Meta-Discovery**.
*   The system begins redesigning its own `HypothesisGenerator` search priors based on RE and HQ trends.
*   Complete decommissioning of legacy process-centric registries.
