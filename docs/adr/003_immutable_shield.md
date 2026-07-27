# ADR 003: Immutable Shield Governance Consolidation

## Status
Proposed

## Context
The system currently has dozens of fragmented "Governance" layers, often overlapping or soft-coded within individual agents. This makes it impossible to guarantee that all actions (trades, self-modifications) comply with institutional risk limits.

## Problem
How can we ensure that every system intervention passes through a non-bypassable, deterministic safety gate that is independent of the reasoning agents?

## Alternatives Considered
1.  **Agent-level Self-Checks**: Unreliable; agents can "reason" their way around limits (Reward Hacking).
2.  **Middleware Validators**: Good, but can be bypassed if the middleware is not enforced at the lowest execution level.
3.  **Immutable Shield (Governance Gate)**: A singleton interceptor that sits between the CSC/Agents and the Execution/Evolution layers.

## Decision
We will implement the **Immutable Shield** as the authoritative governance singleton.

### Key Features:
- **Mandatory Interception**: No trade or code change can reach the environment without a cryptographic signature from the Shield.
- **Deterministic Logic**: While agents use probabilistic reasoning, the Shield uses hard-coded, verifiable risk and compliance rules.
- **Multi-Stage Validation**:
    1.  **Compliance**: Regulatory and internal policy checks.
    2.  **Risk**: Exposure, VaR, and drawdown limits.
    3.  **Safety**: Out-of-distribution (OOD) detection for anomalous market conditions.
- **Audit Immutability**: Every decision (Pass/Fail) is logged to a write-once audit trail.

## Expected Benefits
- **Zero Bypass**: Prevents "Delusional Optimization" or "Reward Hacking" from impacting the live portfolio.
- **Institutional Compliance**: Guaranteed enforcement of risk mandates.
- **Explainability**: Clear, deterministic reasons for why an action was blocked.

## Trade-offs
- **Rigidity**: Hard limits might block profitable but unusual trades (intended behavior for safety).
- **Single Point of Failure**: System shuts down if the Shield fails (intended behavior).

## Rollback Strategy
1.  Bypass mode (admin-only, logged) for emergency recovery.
2.  Parallel legacy governance checks for verification.

## Success Metrics
- **Zero Violations**: 0 instances of risk limits being exceeded in production.
- **Detection Rate**: 100% of anomalous/high-risk actions intercepted during testing.
- **Overhead**: < 10ms processing latency per check.
