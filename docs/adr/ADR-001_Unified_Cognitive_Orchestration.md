# ADR-001: Unified Cognitive Orchestration (UCO)

## Problem Definition
Current AlphaAlgo implementation suffers from "agentic fragmentation" where multiple controllers (`MasterOrchestrator`, `MetaOrchestrator`, `SelfCoordinatingCore`, `USIS`) run overlapping decision loops. This leads to high communication overhead, goal misalignment, and difficult-to-trace failures.

## Existing Implementation
An 8-layer SOA where Level 7 (Orchestration) delegates to Level 10 (Swarm) and Level 6 (Agent System) independently, creating non-linear and sometimes circular dependencies.

## Research Evidence
- **Building Effective Agents (Anthropic):** Advocates for simple, stateful, and composable agents over complex multi-agent swarms.
- **The Long-Horizon Task Mirage (Wang et al., 2026):** Identifies that complex orchestration often fails at long horizons due to compounding errors in coordination.

## Selected Decision
Consolidate all Level 6-10 orchestration logic into a single **Unified Cognitive Orchestrator (UCO)**. The UCO acts as the system's "Prefrontal Cortex," maintaining a unified state tensor and executing interleaved reasoning/tool-use steps.

## Competing Alternatives
1. **Hierarchical Swarms:** (Rejected) - Too much "agentic drift" and noise for institutional risk standards.
2. **Stateless ReAct Agents:** (Rejected) - Fails to maintain long-horizon coherence required for financial missions.

## Mathematical Justification
The UCO optimizes a single objective function $J(\theta)$ across all sub-tasks, ensuring that local actions $a_t$ are always aligned with the global mission $G$:
$$\nabla_\theta J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta} \left[ \sum_{t=0}^H \nabla_\theta \log \pi_\theta(a_t | s_t, G) \cdot A(s_t, a_t, G) \right]$$
Consolidation reduces the variance of the gradient by eliminating conflicting policy updates from sub-orchestrators.

## Engineering Justification
- **Centralized State:** Eliminates the need for expensive JSON-based synchronization between orchestrators.
- **Atomic Operations:** Ensures that risk gates are checked exactly once per decision cycle.

## Implementation Strategy
1. Create `UnifiedCognitiveOrchestrator` class.
2. Port keyword-based routing from `MetaOrchestrator`.
3. Wrap legacy Swarm and Master logic as "Skills" accessible by the UCO.

## Validation Strategy
- **Baseline:** Decision latency of legacy hierarchy.
- **Test:** UCO decision latency on identical market scenarios.
- **Success Criteria:** >30% reduction in latency; 100% parity in risk-gate compliance.

## Risks & Rollback
- **Risk:** Bottlenecking on single-threaded reasoning.
- **Rollback:** Preserve legacy orchestrators as deprecated services for 2 cycles.

## Confidence Level
**High** (Supported by large-scale institutional deployment patterns and Anthropic's production findings).
