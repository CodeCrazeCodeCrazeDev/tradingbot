# ADR 001: Unified Component Registry Consolidation

## Status
Proposed

## Context
The AlphaAlgo system currently suffers from "Registry Fragmentation," with multiple disjoint registries for agents (`AgentRegistry`), tools (`ToolRegistry`), and services (`ServiceRegistry`). This fragmentation leads to:
- Duplicate component instantiation.
- Hidden dependencies.
- Inconsistent lifecycle management.
- Architectural drift.

## Problem
How can we ensure that every system component is uniquely identified, correctly instantiated, and globally accessible through a single authoritative source?

## Alternatives Considered
1.  **Global Dictionary**: Simple but lacks typing, lifecycle hooks, and validation.
2.  **Dependency Injection (DI) Container**: Powerful but can add significant overhead and complexity for simpler components.
3.  **Singleton Unified Registry**: Provides a single point of truth with minimal overhead, suitable for a centralized "One Brain" architecture.

## Decision
We will implement a **Singleton Unified Component Registry**.

### Key Features:
- **Singleton Pattern**: Ensures exactly one registry exists in the runtime.
- **Type-Safe Registration**: Specific methods for agents, tools, services, and models.
- **Lifecycle Management**: Support for `initialize()` and `shutdown()` hooks for all registered components.
- **Dependency Tracking**: Explicitly recording which components depend on others.

## Expected Benefits
- **Architecture Consistency**: Exactly one source of truth for component discovery.
- **Elimination of Duplication**: Prevents multiple instances of the same orchestrator or tool.
- **Simplified Lifecycle**: Centralized startup and shutdown sequence.
- **Observability**: Clear visibility into all active system components.

## Trade-offs
- **Centralization**: The registry becomes a critical single point of failure (mitigated by high-reliability design and FMEA).
- **Global State**: Singletons introduce global state, which must be carefully managed to avoid testing interference.

## Rollback Strategy
1.  Maintain legacy registry adapters that wrap the new Unified Registry.
2.  In case of failure, revert individual component registrations back to legacy files.
3.  Full git revert of the registry module.

## Success Metrics
- **Uniqueness**: Exactly 1 registry instance detected by fitness tests.
- **Coverage**: 100% of agents and tools migrated to the unified registry.
- **Latency**: < 1ms for component retrieval.
- **Registry Fragmentation**: Zero redundant registry files remaining after Phase 5.
