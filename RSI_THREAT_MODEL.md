# RSI threat model

**Protected assets:** capital, risk/kill-switch controls, independent datasets/holdout, evaluation contract/thresholds, baselines, attestation keys, experiment ledger, audit logs, rollback identity and existing capability suite. **Untrusted:** proposing/self-improvement agents, candidate code/config/data, self-reported confidence, proxy LLM judges, simulated fills, output from a candidate-modifiable evaluator and legacy mock tests.

| Failure/attack | How it appears here | Required control/test |
|---|---|---|
| Reward/metric gaming | `evaluation/runner.py` reports total return as Sharpe; weighted `evaluation.py` score can reward high gross gains while hiding downside. | Typed units, same-capital net bar series, full vector and hard risk gates; zero-trade/leverage/cost adversarial tests. |
| Evaluation tampering | Candidate edits thresholds, verifier, tests or baseline after looking at results; CSC heuristic returns `promoted=True`. | Operator-held signed contract, protected-path allowlist, contract/baseline hash and signature checks, explicit blocked-path event. |
| Leakage/repeated holdout | `walk_forward.py` calibrates on its test split and single EURUSD test reused across experiments. | Frozen final scoring, horizon purge/embargo, external holdout budget/rotation and trial ledger. |
| Manufactured evidence | Arbitrary injected `simulation_runner` dictionaries default promotion eligible; fabricated testnet/LOB fills or synthetic fallback. | Verify source/serialization and actual changed policy, independent verifier/attestation, reject synthetic/missing costs. |
| Specification gaming | Reduce trades to improve ratio; increase leverage; choose only favorable periods; conceal failed trials. | Include zero bars, exposure/turnover and min opportunity coverage; same sizing/costs and immutable experiment count. |
| Collusion/correlated judges | Same agent proposes and signs off, correlated LLM reviewers agree on invented claims. | Separate write privileges and operator custody; deterministic invariants/stat tests outrank LLM votes. |
| False safety or rollback | `EvolutionGate` default metrics imply no missing evidence; old RSI config apply returns success; rollback returns data without restoring runtime. | Missing values veto; disable old deploy; separately exercise rollback before any later canary. |
| Live execution bypass | RSI calls broker directly or disables shield, risk or approval; order duplicate/partial fills. | No execution imports or paper/live mutator in milestone; future canary only through canonical service with independent shield veto and signed human authorization. |
| Research recursion | Search revisits holdout, edits its own evaluator, consumes unbounded compute or forgets old regimes. | Hierarchical permissions, depth/trial/wall-time budgets, stop on drift, regression and failed-experiment memory. |

Report suspicious edits as security-relevant events without exposing credentials or sealed data. Repository commits and SHA-256 hashes give traceability, not tamper protection against a writer with the same privileges as the verifier. Fail closed when separation cannot be proved.
