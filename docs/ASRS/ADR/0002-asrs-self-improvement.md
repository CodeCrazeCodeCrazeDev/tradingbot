# ADR 0002: Self-Referential Optimization of ASRS
## Status: Approved

### Context
To achieve long-term continuous capability scaling, the ASRS itself must not be static. If the R&D platform's own search parameters (such as mutation rates, population sizes, TextGrad prompts, or scheduling priorities) are fixed, the system may plateau or fail to discover more complex optimizations over time.

### Decision
We will design ASRS to be a self-referential, self-improving platform. The ASRS itself will be modeled as an evolvable component inside the Scientific Knowledge Graph.

* The Opportunity Discovery Division can audit ASRS metrics (such as average search generation convergence time, or experiment evaluation costs).
* The Evolution Engine can propose mutations to ASRS parameters (such as the weights in the Cost-Aware Research Planner utility formula, or the TextGrad Critic prompts).
* Mutated ASRS configurations are subjected to a meta-verification phase, running synthetic benchmark suites of historical experiments to confirm they discover high-quality improvements faster than the baseline ASRS setup.

### Consequences
* **Extensibility**: Permits the research platform to autonomously adapt to changes in hardware resources or API limits.
* **Optimized Efficiency**: Ensures that the evolution parameters (e.g. mutation rates) dynamically scale down as the search space approaches convergence.
* **Infinite Loops Prevention**: Meta-evolution is tightly constrained. ASRS parameter changes can only be evaluated on static historical benchmarks to prevent recursive divergence or unstable nested evolutionary loops.
