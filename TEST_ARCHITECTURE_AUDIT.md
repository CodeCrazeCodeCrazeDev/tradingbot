# TEST_ARCHITECTURE_AUDIT.md
## Deconstruction and Analysis of AlphaAlgo's Test Architecture

This audit deconstructs the AlphaAlgo test suite as a potentially contaminated legacy artifact, identifying tests that validate genuine invariants versus those that enforce obsolete interface contracts or introduce technical debt.

### 1. The `validate_evolution()` Interface Contradiction
*   **Test**: `tests/test_scientific_modules.py::test_rsea_monotone_safe_gate` & `test_rsea_multi_metric_protected_gate`
*   **Intended Invariant**: Verify that the `EvolutionGate` correctly filters self-evolving candidates based on the Monotone-Safe rule and Gain Metric.
*   **Current Implementation**: The test invokes `await gate.validate_evolution(...)`, which expects an asynchronous coroutine or an awaitable object.
*   **Is Invariant Still Valid?**: Yes, the monotone safety filter is a Tier-0 invariant.
*   **The Problem**: The production method `validate_evolution()` is conceptually and syntactically synchronous in 95% of active callers across the repository. Introducing a hybrid `AwaitableBool` or `async` wrapper solely to satisfy this single test violates clean API boundaries and leaks test-only complexity into production.
*   **Decision**: Maintain `validate_evolution()` as a strictly synchronous method returning a standard `bool`. Redesign the contract in `tests/test_scientific_modules.py` to remove the obsolete `await` keyword.

### 2. Parameterless Singleton Instantiation
*   **Test**: `tests/test_scientific_modules.py::test_discoloop_internalization` & `test_pivot_refine_logic`
*   **Intended Invariant**: Verify DiscoLoop reasoning internalization and strategic pivot refinement on the active brain.
*   **Current Implementation**: Instantiates the central controller via `csc = CognitiveSystemController()` without passing required dependency injections (`world_model` and `hms`).
*   **Is Invariant Still Valid?**: Yes, reasoning depth and confidence decay must be verifiable.
*   **The Problem**: If a previous test or fixtures run `CognitiveSystemController.reset()`, the next parameterless instantiation fails with missing positional arguments in `__init__`.
*   **Decision**: Update `CognitiveSystemController`'s constructor to make its dependency arguments optional (`world_model=None`, `hms=None`) so that it can be cleanly constructed as a parameterless singleton in isolated unit tests while still accepting full injections in integration runs.

### 3. LogAct Await Timeout Hacking
*   **Test**: `tests/conftest.py::mock_wait_for_decision`
*   **Intended Invariant**: Avoid hanging during test runs when waiting for consensus on proposals.
*   **Current Implementation**: Automatically patches `LogAction.wait_for_decision` to immediately approve proposals.
*   **Is Invariant Still Valid?**: Yes, we must prevent test hang-ups.
*   **Decision**: Maintain this mock logic as a designated test fixture, but explicitly document that production runs require actual asynchronous voter execution over the `UnifiedDecisionBus`.
