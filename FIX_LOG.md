# FIX LOG

| Date | Issue ID | Developer | Description | Solution Implemented | Verification |
|---|---|---|---|---|---|
| July 2026 | **SEC-001** | Jules | Unsafe Pickle Deserialization | Created `ArtifactManager` to enforce non-executable JSON serialization for cache, and `RestrictedUnpickler` for ML models. | Static scan and unit tests. |
| July 2026 | **SEC-002** | Jules | `shell=True` in subprocess calls | Refactored command invocations to lists using `shlex.split`. | CI-enforced security check. |
| July 2026 | **SEC-003** | Jules | Hardcoded credentials | Retrieved credentials from environmental lookups (`os.getenv`). | Confirmed secure lookup. |
| July 2026 | **REL-001** | Jules | Naked `except:` blocks | Replaced raw blocks with `except Exception as e:` and appropriate warning logs. | Ran full UCA test suite. |
| July 2026 | **CONC-001**| Jules | Race conditions in Event Bus | Integrated a fine-grained `self._sub_lock` threading lock in `EventBus`. | Run concurrency stress chaos tests. |
| July 2026 | **INT-001** | Jules | "Delusion Loop" random walks | Replaced `np.random.randn()` with SQLite `market_data` or Geometric Brownian Motion. | Run self-play test. |
| July 2026 | **INT-002** | Jules | Simulated Superintelligence Stubs | Connected `DiscoveryEngine`'s evaluation to the backtester math formulas. | Run strategy discovery tests. |
| July 2026 | **TEST-001**| Jules | Singleton mock contamination | Updated `CognitiveSystemController` and `SkillRouter` to re-bind properties. | Ran repeated test runs. |
| July 2026 | **TEST-002**| Jules | Spell/Logic Participle Mismatch | Expanded SkillRouter's task checking to match both `"hedge"` and `"hedg"`. | `test_router_s2l_routing` passed. |
