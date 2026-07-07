# ADR 006: Consolidation of Fragmented Risk Subsystems

## Status
Proposed

## Context
The `trading_bot/risk` directory contains 50+ fragmented files with overlapping responsibilities. There is no single authoritative source of truth for risk calculation, leading to inconsistent enforcement and high maintenance overhead. Institutional grade requires a deterministic, audited, and unified risk engine.

## Decision
We will consolidate all risk logic into a single, high-performance `Immutable Risk Engine`.
1. **Core Engine**: A unified class `UnifiedRiskEngine` will handle all calculations (VaR, CVaR, Kelly, etc.).
2. **Safety Enforcement**: The engine will be the sole backend for the `ImmutableShield`.
3. **Skill-to-LoRA**: Dynamic risk parameters will be managed as CSC Skills.
4. **Decommissioning**: All 50+ legacy risk files will be moved to `_archive/risk_legacy`.

## Consequences
- **Positive**: Reduced complexity, deterministic risk enforcement, improved auditability.
- **Negative**: Initial migration effort, potential for temporary regression in specialized metrics until ported.
