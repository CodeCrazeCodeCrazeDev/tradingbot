# Paper Synthesis: Reasoning with Insight (DeepInsight)

## Paper Information
* **Title**: Learning to Reason with Insight for Informal Theorem Proving
* **Authors**: Yunhe Li, et al.
* **Publication**: arXiv:2604.16278
* **Year**: 2026
* **Link**: https://arxiv.org/abs/2604.16278

## Core Scientific Contribution
Identifies "lack of insight" (recognizing core techniques) as a bottleneck in reasoning. Proposes **DeepInsight**, a framework that structures informal proofs by explicitly extracting core techniques and proof sketches.

## Reusable Algorithms & Engineering Principles
* **Proof Sketching**: Generating a high-level roadmap before low-level execution.
* **Insight Identification**: Training models to flag "Core Techniques" used in a solution.
* **Progressive Multi-Stage SFT**: Teaching models proof writing $\to$ planning $\to$ insight.

## Architectural Patterns
* **Hierarchical Reasoning**: Insight $\to$ Sketch $\to$ Final Output.
* **InsightPO**: Policy optimization with structured rewards over the insight hierarchy.

## Mathematical Foundations
* **Hierarchical Reward Structuring**: $R = w_1 R_{insight} + w_2 R_{sketch} + w_3 R_{final}$.

## Failure Modes & Complexity
* **Failure Modes**: Insight-plan mismatch; "insight-washing" (claiming an insight not used in the proof).
* **Computational Complexity**: Moderate (hierarchical generation).
* **Scalability Limits**: Quality depends on the "DeepInsightTheorem" dataset quality.

## Comparison against AlphaAlgo (UCA-2026)
* **Status**: AlphaAlgo uses "HIPIF" for planning.
* **Improvement**: HIPIF folds history; DeepInsight generates the *forward* roadmap with "Insight".
* **Synergy**: DeepInsight provides the *Strategic Anchor* for HIPIF's folding.

## Decision: EXTEND
* **Justification**: "Insight" is exactly what institutional trade research lacks (it's often just indicator-dumping).
* **Implementation**: Upgrade `PlannerAgent` to use "DeepInsight" (Insight $\to$ Sketch $\to$ Research).

---

# Paper Synthesis: HyEvo

## Paper Information
* **Title**: HyEvo: Self-Evolving Hybrid Agentic Workflows for Efficient Reasoning
* **Authors**: Beibei Xu, et al.
* **Publication**: arXiv:2603.19639
* **Year**: 2026
* **Link**: https://arxiv.org/abs/2603.19639

## Core Scientific Contribution
Introduces **heterogeneous atomic synthesis**—combining probabilistic LLM nodes with deterministic code nodes. HyEvo autonomously evolves both workflow topology and node logic.

## Reusable Algorithms & Engineering Principles
* **Heterogeneous Atomic Synthesis**: Mixing neural and symbolic nodes.
* **Multi-Island Evolutionary Strategy**: Parallel populations exploring the hybrid search space.
* **Reflect-then-Generate**: Feedback-driven topology refinement.

## Architectural Patterns
* **Hybrid Workflows**: LLM for "Why", Code for "How".
* **Topology Evolution**: Dynamically adding/removing nodes and edges based on performance.

## Mathematical Foundations
* **Program Synthesis**: Evolution over a graph of neural-symbolic primitives.

## Failure Modes & Complexity
* **Failure Modes**: Symbolic node errors; logic cycles; excessive cost of evolutionary search.
* **Computational Complexity**: Moderate to High (evolutionary loops).
* **Scalability Limits**: Limited by the size of the atomic operator library.

## Comparison against AlphaAlgo (UCA-2026)
* **Status**: AlphaAlgo has `SkillRouter` and `HASP` (Hybrid Agentic Skill Programs).
* **Improvement**: HyEvo provides a formal framework for evolving the *entire* workflow topology, not just selecting skills.

## Decision: MODIFY
* **Justification**: AlphaAlgo's HASP is a subset of HyEvo's capabilities.
* **Implementation**: Transition `IntegratedAgentSystem` to a HyEvo-inspired "Evolving Graph" architecture.
