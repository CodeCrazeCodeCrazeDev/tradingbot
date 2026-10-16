# Phase 4: Refactoring and Migration Plan (2026)

## Dependency Graph
```
[SkillRouter / HASP] ──> [CognitiveSystemController] <── [SAGE / AutoMem / HMS]
                                  │
                                  ▼
                     [MultiAgentDebateSystem]
                                  │
                                  ▼
                          [EvolutionGate]
```

## Migration Graph
1. Core Singletons Verification -> 2. Paper Traceability Docstring Checks -> 3. Unified Integration Testing -> 4. Monotone-Safe Verification.

## Risk Analysis
- **Risk**: Over-pruning of graph edges in `SAGEGraphMemory`.
  - **Mitigation**: Edge weight decay rate is capped at $\eta=0.1$ and minimum weight threshold is enforced at $0.1$.
- **Risk**: Latency overhead during multi-step `DiscoLoop` recurrence.
  - **Mitigation**: Loop iterations $k$ are default-bounded to 2 loops during market observation ingestion.

## Rollback Strategy
All changes are protected by deterministic class-level `reset()` methods on core singletons (`CognitiveSystemController.reset()`, `SkillRouter.reset()`, `HierarchicalMemorySystem.reset()`). Automated regression test suites under `tests/` ensure instantaneous rollback detection.

## Benchmark & Validation Plan
Validation is performed via `tests/test_scientific_architecture_uca2026.py`, `tests/uca_v5/`, `tests/agents/test_multi_agent_debate.py`, and `tests/governance/test_evolution_gate_v5.py`.
