# World Model V5: Conditional Causal Induction

The GWM (Generative World Model) V5 moves from "Latent Dynamics" to **Conditional Structural Causal Models (C-SCM)**.

## 1. Mathematical Core: C-SCM
A World Model state is defined by a triplet $(\mathcal{G}, \mathcal{F}, \mathcal{P})$:
*   $\mathcal{G}$: The DAG representing causal relationships (e.g., Rates $\to$ Equities).
*   $\mathcal{F}$: The set of functions $f_i$ determining node values.
*   $\mathcal{P}$: The context-validity distribution from the QKG.

The V5 World Model evaluates:
$$P(Y | do(X), Context)$$
Instead of $P(Y | X)$.

## 2. Causal Induction (CWMI)
The GWM background process continuously induces causal structure from the Shared Log (market data + agent actions).
*   **Constraint-based Search**: Identifies the DAG structure.
*   **Context Conditioning**: The GWM identifies that the relationship $Oil \to CAD$ has high validity $(>0.9)$ in "Stagflation" context but low validity $(<0.2)$ in "Deflationary Recession" context.

## 3. Imagination Engine: Interventional Planning
When the `PlannerAgent` asks "What if?", the GWM V5 performs a **Structural Intervention**.

1.  **Context Alignment**: Align the current GWM state with the QKG Market Context.
2.  **Intervention**: Set $X = trade\_intent$ (e.g., $do(Buy\_500\_Lots)$).
3.  **Propagation**: Use the C-SCM to propagate the causal effect through the DAG.
4.  **Counterfactual**: Generate "What would have happened if we *hadn't* traded?" vs "What will happen if we *do*?".
5.  **Risk Verification**: If the propagation hits a "Safety Node" (e.g., Max Drawdown) with $P > 0.05$, the Verification Swarm issues a Veto.

## 4. World Model Self-Refinement
Using the **Hyperagent** Meta-Agent, the GWM refines its own structure.
*   *Mechanism*: Error Attribution. If a prediction $P(Y | do(X))$ differs from the actual outcome, the Meta-Agent investigates:
    *   Was the DAG structure incorrect?
    *   Was the Context Validity (QKG) wrong?
    *   Was there a missing Latent Variable?
*   *Action*: Propose a DAG modification or a QKG update.
