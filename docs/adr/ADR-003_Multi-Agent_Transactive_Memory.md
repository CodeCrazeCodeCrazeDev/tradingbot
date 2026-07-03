# ADR-003: Multi-Agent Transactive Memory (MATM)

## Problem Definition
Current AlphaAlgo agents operate in relative memory isolation or query a global noisy vector database. This leads to "redundant rediscovery" where multiple agents spend compute and time learning the same market patterns (e.g., a specific liquidity trap) instead of sharing the solution.

## Existing Implementation
A multi-tier memory system (Working, Episodic, Semantic, Procedural) where each agent maintains its own instances or shares a global, unstructured `episodic` store.

## Research Evidence
- **Multi-Agent Transactive Memory (arXiv:2606.19911):** Proposes a framework for population-level storage and retrieval of agent-generated trajectories.
- **Organize then Retrieve: Hierarchical Memory Navigation (arXiv:2606.11680):** Advocates for structured memory organization (Grounded Workspace) to improve efficiency.

## Selected Decision
Adopt a **Multi-Agent Transactive Memory (MATM)** architecture. Agents will contribute successful execution trajectories to a shared `Procedural Artifact Store`. A centralized `Transactive Index` will map specific knowledge domains to the agents that produced them, enabling "who knows what" routing.

## Competing Alternatives
1. **Unified Global RAG:** (Rejected) - High signal-to-noise ratio issues and lack of procedural structure.
2. **Individual Agent Memory:** (Rejected) - Extreme redundancy and slow collective learning.

## Mathematical Justification
We model the system's "Discovery Cost" $C_{sys}$. In MATM, for a new task $T$ belonging to domain $D$, the cost is:
$$C_{sys}(T) = C_{index} + \min_{a \in \mathcal{A}} [ \text{dist}(D, \text{index}(a)) \cdot C_{query} + (1 - \text{hit}(a)) \cdot C_{explore} ]$$
Where $C_{index}$ is the lookup cost and $hit(a)$ is the probability agent $a$ already has the solution. MATM maximizes $hit(a)$ across the population, reducing total exploration cost $C_{explore}$ compared to independent learning.

## Engineering Justification
- **Storage Efficiency:** Only "Gold Standard" trajectories (high reward) are indexed globally.
- **Collaboration:** Enables agents to "outsource" reasoning to specialists identified in the index.

## Implementation Strategy
1. Implement the `TransactiveIndex` registry.
2. Create the `ProceduralArtifactStore` for high-confidence trajectory sharing.
3. Update agent retrieval logic to query the Transactive Index before initiating new research.

## Validation Strategy
- **Benchmark:** "Cold Start" vs. "Accumulated Experience" phases in CL-Bench.
- **Success Criteria:** >25% reduction in steps-to-solution for recurring market patterns.

## Risks & Rollback
- **Risk:** Stale Transactive Index leading to incorrect routing.
- **Rollback:** Fall back to individual local memory if index confidence drops.

## Confidence Level
**High** (Directly supported by CMU and UC Berkeley evidence in interactive environments).
