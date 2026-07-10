# Hypothesis Evaluation Points (Verified Audit 2026)

## Core Evaluation
1. **`trading_bot/core/phce_d_engine.py`**: `ParallelHypothesisCorrectionEngine.process()` - Main evaluation pipeline using EvidencePackets.
2. **`trading_bot/core_agent_system/scientific_reasoning/core.py`**: `ScientificReasoningEngine.evaluate_results()` / `bayesian_update()`.

## Specialized Evaluation
1. **`trading_bot/apex_fi/alpha_mining.py`**: `LivingFactorLibrary` - Decay-based validation.
2. **`trading_bot/core/verification/swarm.py`**: `VerificationSwarm` - Peer-review based evaluation.
