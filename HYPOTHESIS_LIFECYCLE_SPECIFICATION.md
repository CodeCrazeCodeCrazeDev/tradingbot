# Hypothesis Lifecycle & Scientific State Machine Specification (UCA V6)

## Executive Summary

This specification governs the lifetime, state machine dynamics, cryptographic provenance, and 19-stage Scientific Reasoning Engine (SRE) execution pipeline for all hypotheses (alphas, strategies, beliefs, forecasts, causal models, world model representations) across AlphaAlgo.

Every claim or model in AlphaAlgo is treated as a hypothesis until empirically validated. Under no circumstances is any hypothesis or historical record allowed to be silently deleted. Every hypothesis resides in a fully deterministic lifecycle state machine with non-lossy historical tracking.

---

## 1. Complete 19-Stage Scientific Reasoning Engine (SRE) Pipeline

The SRE executes a continuous, autonomous scientific discovery loop:

```
[1. Observation]
       │
[2. Anomaly Detection]
       │
[3. Question Generation]
       │
[4. Hypothesis Generation] ◄── [Failure Ledger Constraints]
       │
[5. Evidence Collection]
       │
[6. World Model Simulation]
       │
[7. Counterfactual Generation (do-calculus)]
       │
[8. Adversarial Debate (Verification Swarm)]
       │
[9. Experiment Design & Falsification Trigger Setup]
       │
[10. Execution (Backtesting & Paper Trading)]
       │
[11. Statistical & Empirical Evaluation]
       │
[12. Bayesian Posterior Update]
       │
[13. Confidence Calibration (ECE Verification)]
       │
[14. Knowledge Integration]
       │
[15. Memory Consolidation (HMS Graph Persist)]
       │
[16. Policy Improvement & Strategy Synthesis]
       │
[17. Continuous Monitoring (Alpha Death Clock)]
       │
[18. Hypothesis Retirement / State Transition]
       │
[19. Automatic Discovery of New Hypotheses]
```

---

## 2. Deterministic State Machine & Transition Rules

Every hypothesis must exist in exactly one of the following 10 canonical operational and terminal states:

```
                      ┌─────────────────── [CREATED / CANDIDATE] ──────────────────┐
                      │                                                            │
                      ▼                                                            ▼
               [INCONCLUSIVE] ◄───────────────────────────────────────────── [UNDER EVALUATION]
                      │                                                            │
         ┌────────────┴────────────┐                           ┌───────────────────┼───────────────────┐
         ▼                         ▼                           ▼                   ▼                   ▼
    [DORMANT]               [REACTIVATED]                 [CONFIRMED]         [REJECTED]            [MERGED]
         │                         │                           │                   │                   │
         └─────────────────────────┴────────────┬──────────────┘                   │                   │
                                                ▼                                  ▼                   ▼
                                       [INSTITUTIONALIZED]                   [DEPRECATED]           [SPLIT]
                                                │                                  │
                                                └─────────────────┬────────────────┘
                                                                  ▼
                                                             [SUPERSEDED]
```

### State Definitions & Transition Criteria

1. **CREATED (Candidate)**:
   - *Criteria*: Initial instantiation by an origination engine (Alpha Mining, Curiosity, Extraction, Symbolic Discovery). SHA-256 genesis hash generated.
   - *Next States*: `UNDER_EVALUATION`.

2. **UNDER_EVALUATION**:
   - *Criteria*: Active execution through World Model counterfactual simulation, Adversarial Debate, and Out-of-Sample backtesting.
   - *Next States*: `CONFIRMED`, `REJECTED`, `INCONCLUSIVE`, `MERGED`, `SPLIT`.

3. **CONFIRMED**:
   - *Criteria*: $P(\mathcal{H} \mid \mathcal{E}) \ge 0.85$, $DSR > 1.5$, $ECE < 0.05$, and passed all risk verifiers.
   - *Next States*: `INSTITUTIONALIZED`, `DORMANT`, `DEPRECATED`.

4. **REJECTED**:
   - *Criteria*: $P(\mathcal{H} \mid \mathcal{E}) < 0.20$, or hard falsification by Risk Verifier or Red-Team Swarm.
   - *Next States*: Terminal (persisted in HMS `FailureLedger` for negative constraint queries).

5. **INCONCLUSIVE**:
   - *Criteria*: Statistical power insufficient ($p > 0.05$ or credal interval span $> 0.50$).
   - *Next States*: `UNDER_EVALUATION` (with higher sample size), `DORMANT`.

6. **MERGED**:
   - *Criteria*: Combined with a complementary hypothesis to improve Sharpe and reduce drawdown ($I(\mathcal{H}_1; \mathcal{H}_2) > \tau$).
   - *Next States*: Genesis state for new merged candidate hypothesis.

7. **SPLIT**:
   - *Criteria*: Bimodal performance across regimes requiring decomposition into regime-specific sub-hypotheses.
   - *Next States*: Genesis states for $N$ regime-bound sub-hypotheses.

8. **DORMANT**:
   - *Criteria*: Strategy parked due to unfavorable market regime (e.g. low-volatility model during high-VIX shock).
   - *Next States*: `REACTIVATED`, `DEPRECATED`.

9. **REACTIVATED**:
   - *Criteria*: Re-entered active evaluation/execution when market regime aligns with strategy boundary conditions.
   - *Next States*: `CONFIRMED`, `UNDER_EVALUATION`.

10. **DEPRECATED / SUPERSEDED**:
    - *Criteria*: Retired due to continuous alpha decay (Death Clock exhaustion) or replaced by a superior evolved model.
    - *Next States*: Terminal archive in HMS Knowledge Graph.

11. **INSTITUTIONALIZED**:
    - *Criteria*: Promoted to Level 5 production execution with automated portfolio capital allocation.
    - *Next States*: `DORMANT`, `DEPRECATED`, `SUPERSEDED`.

---

## 3. Cryptographic Provenance & Lineage Data Schema

Every hypothesis record enforces strict lineage and provenance schema (`ProvenanceDataSchema` v1.0.0):

```json
{
  "hypothesis_id": "hyp_2026_09f83a1c2d",
  "parent_ids": ["hyp_2026_01a02b", "hyp_2026_04c05d"],
  "genesis_engine": "ApexAlphaMining_v4",
  "genesis_timestamp": "2026-03-31T12:00:00Z",
  "state": "CONFIRMED",
  "sha256_code_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "sha256_state_hash": "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4",
  "p_value": 0.0021,
  "deflated_sharpe_ratio": 2.14,
  "expected_calibration_error": 0.032,
  "bayes_factor": 18.4,
  "evidence_lineage": [
    {
      "source": "LSE_Market_Data_Feeds",
      "timestamp": "2026-03-31T12:05:00Z",
      "signature": "hmac_sha256_proof..."
    }
  ],
  "regime_boundary_mask": ["HIGH_VOLATILITY", "TRENDING_BEAR"],
  "last_updated": "2026-03-31T12:30:00Z"
}
```

---

## 4. HMS Knowledge Integration & Failure Recovery

1. **Non-Lossy Failure Ledger**:
   - All `REJECTED` hypotheses are archived into `HMS.FailureLedger`.
   - When SRE Stage 4 generates new hypotheses, it performs vector similarity lookups against `FailureLedger` to instantly prune known failure topologies.

2. **Graph Consistency**:
   - The HMS graph updates edges upon `MERGE`, `SPLIT`, and `SUPERSEDE` operations, preserving parent-child relationships back to root market observations.
