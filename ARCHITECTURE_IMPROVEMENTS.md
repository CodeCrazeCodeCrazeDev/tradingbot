# AlphaAlgo Elite System — Architecture Improvements

This document outlines the major architectural consolidations and improvements introduced to stabilize and enhance the structural integrity of the AlphaAlgo system.

---

### 1. Unified Dynamic Import Redirection Layer
- **Component**: `UtilityImportRedirector` inside `trading_bot/__init__.py`.
- **Description**: Replaced static, fragile symlinks and sys.path manipulation with a dynamic, hook-based import interception layer (`sys.meta_path`).
- **Safety Measures**:
  - Automatically redirects imports of any of the 16 refactored utility submodules (e.g., `trading_bot.api_cache`) to their new canonical package structure (`trading_bot.utils.api_cache`).
  - Emits explicit, traceable `DeprecationWarning`s to notify developers of outdated paths.
  - Automatically logs usage counts of legacy imports to assist in auditing which active modules still need refactoring before eventually deprecating the redirector entirely.

---

### 2. Explicit Operating Mode Enforcement for `MT5Interface`
- **Component**: `MT5Interface` inside `trading_bot/data/mt5_interface.py`.
- **Description**: Introduced an explicit `OperatingMode` Enum to categorize the running mode of the system:
  - `Production MT5`: Direct, live connection to MetaTrader 5 server. Requires MT5 libraries to be present on disk. Blocking check prevents any silent degradation to mock fallback in production.
  - `Simulation`: Realistic local paper-trading simulation.
  - `Mock`: Minimal static testing mock.
  - `Historical Replay`: Deterministic historical bar playback.
- **Safety Measures**: Throws an `ImportError` instantly if initialized in `Production MT5` mode without the MetaTrader 5 library, preventing silent fallbacks that could hide connection failures.

---

### 3. Dynamic Async Lock Binding (Event Loop Isolation)
- **Component**: `UnifiedRiskEngine` inside `trading_bot/core/risk/unified_risk_engine.py`.
- **Description**: Refactored resource locking to use a lazy-instantiation class helper `_get_lock()`.
- **Safety Measures**: Completely eliminates loop-closed or loop-closed-on-import exceptions. Locks are only constructed when the engine is actively executing within a running asyncio event loop, isolating test environments and preventing runtime deadlocks.

---

### 4. Consolidated Component Singletons
Verified that the system holds exactly one authoritative:
- **Cognitive System Controller (CSC)**: `CognitiveSystemController` (UCA V6 July 2026 Core).
- **Event Bus**: `UnifiedDecisionBus` (LogAct Shared-Log Backbone).
- **Component Registry**: `UnifiedComponentRegistry` (Single point of truth).
- **Risk Engine**: `UnifiedRiskEngine` (Compositional Bayesian-Calibrated).
