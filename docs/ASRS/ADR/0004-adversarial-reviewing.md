# ADR 0004: Adversarial Auditing via Autonomous Reviewer Agent
## Status: Approved

### Context
In automated code evolution systems, there is a strong tendency toward "optimizing for the metric" rather than solving the underlying scientific problem. A strategy or prompt might achieve a perfect score by exploiting dataset leakage, overfitting to a specific historical segment, or introducing hidden assumptions that are unstable in production.

### Decision
We will separate the "Candidate Generation" (Evolution Engine) from the "Candidate Assessment" (Promotion Gate). Before any candidate is promoted to production, the Promotion Gate instantiates an independent **Autonomous Reviewer Agent (ARA)** whose sole mandate is to find reasons to reject the candidate.

The ARA executes a zero-trust check suite:
* **Feature Leakage Check**: Ensures that future rolling variables or test-set labels are not leaking into the model features.
* **Overfitting Sensitivity Check**: Perturbs parameters by $+/- 1\%$ to ensure that performance does not collapse. A fragile, overfitted parameter spike will instantly fail.
* **Systemic Side-Effect Scan**: Confirms that improving the target module does not degrade performance or increase latency in adjacent modules.

### Consequences
* **Extreme Robustness**: Prevents overfitted, fragile, or lucky mutations from contaminating production systems.
* **Intellectual Rigor**: Ensures that every promoted system has been challenged by an adversarial critic, mimicking peer-review processes in elite academic journals.
* **Increased Rejection Rates**: The majority of proposed self-improvements will be rejected by the ARA, resulting in a clean, high-conviction pipeline where only truly robust improvements survive.
