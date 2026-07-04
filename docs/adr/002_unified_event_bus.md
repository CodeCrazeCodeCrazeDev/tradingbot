# ADR 002: Unified Decision Bus Consolidation

## Status
Proposed

## Context
The system currently has multiple event bus implementations (`EventBus`, `MessageBus`, `RealTimeEventBus`, etc.) used for different purposes (service comms, real-time trading, distributed learning). This fragmentation results in:
- Inconsistent event delivery guarantees.
- Difficulty in tracing cross-system logic.
- Redundant message overhead.
- Obscure system state transitions.

## Problem
How can we unify all internal system communication into a single, high-reliability event substrate that supports the UCA-2026 "One Brain" philosophy?

## Alternatives Considered
1.  **Direct Function Calls**: Simple but tight coupling and lacks async benefits.
2.  **Distributed Broker (Redis/RabbitMQ)**: Robust but adds operational complexity and latency for intra-process comms.
3.  **Singleton Unified Decision Bus**: In-memory async bus for low latency, with bridge capability for distributed nodes.

## Decision
We will implement the **Unified Decision Bus** as the authoritative communication substrate.

### Key Features:
- **Singleton Implementation**: Ensures exactly one bus exists.
- **Priority Queuing**: Essential for critical trading and risk events.
- **Correlation IDs**: Mandatory for tracing reasoning chains across agents.
- **Dead Letter Queue (DLQ)**: Mandatory for handling and auditing failed events.
- **Event Replay**: For world-model grounding and debugging.

## Expected Benefits
- **Observability**: Single point for logging all system interactions.
- **Decoupling**: Services interact via events, not direct references.
- **Reliability**: Standardized retry and failure handling logic.
- **Grounding Support**: Event replay allows for high-fidelity state reconstruction.

## Trade-offs
- **Latency**: Async processing adds minor overhead (mitigated by optimized asyncio implementation).
- **Complexity**: Debugging event-driven systems can be harder (mitigated by Correlation IDs and Tracing).

## Rollback Strategy
1.  Individual legacy bus wrappers that proxy to the Unified Decision Bus.
2.  Maintain legacy bus files until Phase 5 decommissioning.
3.  Full git revert of the bus module.

## Success Metrics
- **Uniqueness**: Exactly 1 event bus instance detected by fitness tests.
- **Coverage**: 100% of inter-service messages migrated to the unified bus.
- **Throughput**: > 10,000 events/sec.
- **Latency**: < 5ms for dispatch-to-handler.
