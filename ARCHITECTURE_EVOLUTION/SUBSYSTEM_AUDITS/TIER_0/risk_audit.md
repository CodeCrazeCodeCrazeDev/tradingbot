# Subsystem Audit: risk

## 1. Scientific Audit
- **Purpose**: Comprehensive risk management, VaR, CVaR, Kelly, etc.
- **Architecture**: Extremely fragmented (50+ files).
- **Algorithms**: VaR, CVaR, Monte Carlo, Black-Litterman, Kelly Criterion.
- **Strengths**: Wide range of risk metrics and protectors.
- **Weaknesses**: Unmanageable fragmentation, duplicate managers (`MASTER_risk_manager.py`, `RiskManager.py`, `unified_risk_manager.py`, etc.).
- **Technical Debt**: High complexity, difficult to maintain or audit.
- **Duplication**: Massive internal duplication of risk calculation logic.
- **Scientific Gaps**: Risk estimates are not tied to the World Model V3 uncertainty engine.

## 2. One Brain Compliance
- **CSC Integration**: NO.
- **HMS Integration**: NO.
- **Decision Bus Integration**: NO.
- **Immutable Shield Integration**: NO (separate from `ImmutableShield`).

## 3. Decision
- **Decision**: HARD CONSOLIDATION & REPLACE
- **Justification**: Collapse all 50+ files into a single `Immutable Risk Engine` governed by the CSC and enforced via the `ImmutableShield`.
