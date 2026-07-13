# ARCHITECTURE_IMPROVEMENTS.md - UCA V5 Evolution

## 1. "One Brain" Enforcement
*   **Consolidation of Registries:** Fragmented `SystemRegistry` and `AgentRegistry` have been bridged to the authoritative `UnifiedComponentRegistry` (Singleton). This prevents multi-instance hallucinations where different parts of the system use different versions of the same agent.
*   **Consolidation of Decision Bus:** The legacy `EventBus` now serves as a thin wrapper around the `UnifiedDecisionBus` (LogAct Backbone). This ensures all system events are totally ordered and audited by the LogAct consensus processor.

## 2. Risk Management Hardening
*   **Unified Risk Engine:** Consolidated 6 disparate risk implementations into a single `MasterRiskManager`. This eliminates conflicting position sizing logic and ensures drawdown protection is enforced globally.
*   **Immutable Shield Integration:** The `CognitiveSystemController` now passes every approved trade through the `ImmutableShield` as a final, non-bypassable governance gate.

## 3. Modularization of Autonomy
*   **Refactored Control Plane:** The 142KB `autonomy_control_plane.py` God-file has been decomposed into a cohesive package structure:
    *   `autonomy/models.py`: All Pydantic/Dataclass schemas.
    *   `autonomy/services.py`: Sandbox, Credential, and Approval services.
    *   `autonomy/factory.py`: The Controlled Software Factory logic.
*   **Benefit:** Reduced circular dependency risk and improved unit-testability of the safety primitives.

## 4. Scientific Reasoning Upgrades
*   **World Model V3 (WM-V3):** Replaced simplistic prediction stubs with a hybrid Transformer-Mamba architecture capable ofRelational Attention and Linear-time temporal scanning.
*   **Evidence-First Gating:** Implemented the `EvidenceGraphGate` which prevents the system from acting on reasoning that cannot be traced back to the research ledger.

## 5. Persistence Integrity
*   **Security layer:** Implemented a canonical `SafeEvaluator` to replace raw `eval()` in feature engineering, and transitioned from `pickle` to `json`/`joblib` to mitigate arbitrary code execution risks.
*   **Deterministic Governance:** Added `DeterministicManager` to ensure all AI-driven decisions are 100% reproducible across institutional environments.
