# AlphaAlgo Recursive Self-Improvement Architecture

## Purpose

AlphaAlgo's recursive self-improvement (RSI) system improves research hypotheses,
strategies, policies, models, tools, and architecture proposals through a
closed evidence loop. It does **not** permit an agent to rewrite live trading
code, risk limits, approval policy, credentials, or execution paths directly.
Every candidate is versioned, replay-tested, evaluated out of sample, red
teamed, archived, and promoted only through explicit human approval.

## Research comparison

The design was compared against the following public approaches:

- [AlphaEvolve — Google DeepMind](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/): candidate generation is separated from automated evaluators; promising programs are retained in a programs database and evolved against objective metrics. AlphaAlgo adopts the frozen-evaluator boundary, candidate archive, evaluator insights, bounded mutations, and resource budgets. Unlike AlphaEvolve, the first AlphaAlgo implementation evolves configuration/strategy artifacts rather than arbitrary executable code because trading safety and reproducibility are stricter requirements.
- [Darwin Gödel Machine](https://arxiv.org/html/2505.22954v2): maintains an archive/tree of self-improving agents, samples parents, creates mutations, empirically validates candidates, and uses sandboxing/human oversight. AlphaAlgo adopts lineage, diversity-preserving archives, parent IDs, rollback snapshots, and human oversight. It deliberately excludes unrestricted self-modifying production code.
- [Dream-RSI](https://arxiv.org/abs/2609.14858): uses online discovery traces to construct a replay simulator, improves the exploration policy through cheap offline dreaming, then redeploys the improved policy online. AlphaAlgo adds this as the dream/replay stage: historical market data, experiment traces, fills, slippage, failures, and research outcomes form the simulator pool; no synthetic reward is accepted as production evidence.
- [MONA — Google DeepMind](https://deepmind.google/research/publications/148850/): separates myopic optimization from non-myopic approval to reduce multi-step reward hacking. AlphaAlgo applies this by allowing bounded local candidate optimization while requiring non-myopic human approval and long-horizon OOS, drawdown, robustness, and safety checks before promotion.

## Existing AlphaAlgo strengths

- `EvolutionGate` already provides monotone-gain, calibration, robustness,
  replay, EKSFT, and adversarial checks.
- `WalkForwardEvaluator` provides chronological OOS evaluation.
- `ImmutableShield` provides deterministic runtime vetoes.
- `HumanApprovalGate` provides request/history infrastructure.
- `RollbackManager` provides configuration snapshots.
- HMS and RSI memory provide experiment/lesson persistence.

## Gaps closed by the new foundation

1. Existing `ExperimentManager` falls back to random metrics when simulation
   integrations are unavailable; the new RSI contract requires evaluator-owned,
   provenance-bearing evidence and rejects missing replay evidence.
2. Existing RSI deployment can apply configuration after a score check; the new
   loop is dry-run by default and requires an explicit human approver for every
   promotion.
3. Existing domain loops are open-ended but have no common genome, lineage,
   diversity archive, or immutable promotion record; `ImprovementGenome`,
   `EvaluationEvidence`, and `PromotionDecision` add those boundaries.
4. Existing human approval labels some strategy actions as auto-approved; RSI
   promotion uses its own hard policy and cannot downgrade its approval level.
5. Existing rollback is available but not coupled to candidate approval; the
   new loop records a rollback snapshot before a staged promotion.
6. Existing improvement state is separate from trading accounting; typed
   trading repositories now provide authoritative orders, fills, positions,
   audit events, and reconciliation records.

## RSI lifecycle

```text
Observe current system and market state
  -> generate bounded ImprovementGenome candidates
  -> select parents from the lineage archive
  -> dream in replay/simulation using immutable historical inputs
  -> run chronological train/OOS, stress, regime, cost, and slippage evaluation
  -> run safety/adversarial/reward-hacking checks
  -> compare candidate vs baseline with calibration and drawdown constraints
  -> EvolutionGate validation
  -> HumanApprovalGate approval (required for all promotions)
  -> create rollback snapshot and signed/staged artifact
  -> paper deployment and monitoring
  -> only then separately approve production promotion
  -> record outcome and lessons into memory/archive
```

## Domain coverage

The improvement genome supports the requested domains:

- World model; alpha/strategy discovery; trading policy; risk intelligence;
  market analysis; sentiment intelligence; research intelligence;
  hypothesis generation; experiment design; evaluation intelligence;
  agent intelligence; planning; memory; feature engineering; model architecture;
  model selection/routing; uncertainty estimation; execution intelligence;
  portfolio intelligence; data intelligence; simulation environment;
  backtesting/validation; strategy lifecycle; failure diagnosis;
  root-cause analysis; governance; self-debugging; resource optimization;
  tool selection; knowledge graph/institutional knowledge;
  research-to-engineering transfer; research prioritization; meta-learning;
  architecture; and reasoning.

## Safety invariants

- No candidate without a parent, objective, bounded change set, evaluation plan,
  and safety constraints.
- No candidate is accepted without immutable data provenance.
- No candidate is promoted without deterministic replay and OOS evidence.
- No candidate may increase permitted drawdown by default.
- No missing evaluator, missing safety result, failed replay, or missing human
  approver is interpreted as approval.
- No RSI candidate directly changes live code, risk limits, credentials,
  governance, broker selection, or execution semantics.
- Every staged change has a rollback snapshot and a human-readable audit record.
- Paper/staging promotion is distinct from live production promotion.
