# Research Architecture Audit and Pre-Mortem Report

## 1. Architecture Audit

### Current Components
- **Orchestration**: `MasterOrchestrator` (MCTS, Decision Fusion), `SelfCoordinatingCore` (Task Decomposition, Multi-agent Teamwork).
- **Agents**: Standard roles (Planner, Executor, Evaluator, Researcher, Safety) and Legacy specialized agents.
- **Loops**: `IntegratedAgentSystem` main loop, `SelfPlayLoop` (RL-lite), `ReActLoop` (Reasoning).
- **Safety**: `ConstitutionalAI` (Principle-based critique/revision).

### Identified Duplication/Conflicts
- `MasterOrchestrator` and `SelfCoordinatingCore` both attempt to manage execution.
- Reasoning traces are generated in multiple formats across `ReActLoop`, `MasterOrchestrator`, and `IntegratedAgentSystem`.
- `SelfPlayLoop` is currently limited to Policy/Value network updates and lacks a multi-objective reward system.

### Proposed Migration
- **Meta-Orchestrator**: Positioned at the top of `IntegratedAgentSystem`. It will manage "Workflow Policies" rather than just tasks.
- **Unified Reasoning**: Standardize on a single `ReasoningTrace` format compatible with major providers.
- **RL Expansion**: Transform `SelfPlayLoop` into `SelfImprovingRLFramework` with PPO/DPO support and a Multi-Objective Reward Model.

---

## 2. Pre-Mortem Analysis

**Scenario**: The architecture failed to achieve its goals, leading to system instability or financial loss.

### Failure Paths and Mitigations

| Failure Path | Description | Mitigation |
|--------------|-------------|------------|
| **Reward Hacking** | Model generates "sophisticated" reasoning to get high quality scores without actual trading success. | **Deterministic Monitor**: Cross-reference reasoning quality with actual PnL and consistency. |
| **Runaway Complexity** | Meta-orchestrator creates excessive sub-tasks and agents, exhausting resources. | **Resource Guardrails**: Hard limits on decomposition depth and agent count in `SelfCoordinatingCore`. |
| **Policy Instability** | RL updates cause erratic behavior. | **Fixed Trust Boundary**: Immutable risk limits enforced at the execution layer, independent of the RL policy. |
| **Judge Bias** | Frozen LLM Judge shares biases with the agent. | **Cross-Model Validation**: Use different model families for the agent and the judge. |
| **Compute Bottleneck** | Layered thinking takes too long for real-time market response. | **Hierarchical Latency**: Use fast-path heuristics for execution while "deep thinking" happens asynchronously. |

---

## 3. Implementation Priorities
1. **Anti-Reward Hacking**: Establish the ground truth and boundaries.
2. **Meta-Orchestrator**: Enable self-scaffolding workflows.
3. **RL Training**: Implement the self-improvement loop.
4. **Tool/Reasoning Adapters**: Ensure cross-provider compatibility.
