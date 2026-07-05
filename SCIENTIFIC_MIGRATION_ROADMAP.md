# Scientific Reasoning Engine: Migration Roadmap

## Phase 1: Model Unification (Week 1)
- **Action:** Consolidate `Hypothesis` classes.
- **Source:** `trading_bot/intelligence_core/hypothesis_engine.py`, `trading_bot/core/csc/hypothesis.py`.
- **Target:** `trading_bot/core_agent_system/scientific_reasoning/core.py`.
- **Outcome:** Single authoritative `ScientificHypothesis` object.

## Phase 2: Bridge Implementation (Week 2)
- **Action:** Create adapters for existing generators.
- **Source:** `MarketBehaviorGenerator`, `CuriosityEngine`.
- **Target:** SRE `propose()` method.
- **Outcome:** Existing systems feed into the new 18-step loop without logic changes.

## Phase 3: Loop Orchestration (Week 3)
- **Action:** Replace `HypothesisEngine.test_hypothesis` with `SRE.run_cycle()`.
- **Outcome:** Formalized 18-step loop becomes the default investigator for all research.

## Phase 4: HMS Integration (Week 4)
- **Action:** Link `ScientificMemoryObject` to SRE `institutionalize()`.
- **Outcome:** Successful hypotheses automatically become part of global institutional knowledge.

## Phase 5: Legacy Decommissioning (Week 5)
- **Action:** Move `trading_bot/intelligence_core/hypothesis_engine.py` to `_archive/`.
- **Outcome:** Full transition to UCA-2026 Scientific Architecture.
