# RSI Traceability Matrix — Research → Principle → AlphaAlgo Mechanism → Test

Every mechanism that entered the v2 RSI subsystem traces to a research
principle. "Design-only" rows are documented but not implemented (marked
accordingly). Nothing was cargo-culted: each row ends in a concrete file,
function, or explicit non-implementation rationale.

| Source (year, venue) | Problem | Transferable principle | AlphaAlgo mechanism | Test |
|---|---|---|---|---|
| Darwin Gödel Machine (Zhang et al. 2025, preprint) | Agents improve by editing themselves but lose diversity to greedy hill climbing | Keep an open-ended archive of agents; any archived ancestor may be a parent | `archive.py::ParetoArchive` — hash-chained, lineage-preserving; `sample_parent()` | `test_archive_memory.py` (lineage, frontier, tamper) |
| STOP — Self-Taught Optimizer (Zelikman et al. 2023, preprint) | Improver can improve the improver | Recursive improvement is legitimate but the scaffold must be held to the same evidence bar | `meta_proposals.py` — L2/L3 genomes recorded + gated; scorecard measures the improver, not its output only | `test_cycle.py::test_meta_proposals_rejected_in_cycle` |
| AIDE / AI Scientist (2024-25, preprints) | Automated research loops need tree search and reviewer separation | Competing hypotheses as a tree; independent reviewing | `engine_v2::HypothesisEngine` (≥2 competing falsifiable hypotheses, failure memory), `IndependentVerifier` (own key, own replay) | `test_cycle.py::test_run_cycle_produces_gated_decisions` |
| HyperAgents (2025, preprint) | Unbounded self-modification recursion | Bound recursion depth explicitly | contract `max_recursion_depth`; `meta_proposals.recursion_level` | same as above |
| MAP-Elites / QD (Mouret & Clune 2015) | Converging to one optimum loses stepping stones | Behaviour-descriptor cells retain specialists | archive `regime_cell` + `specialist`/`stepping_stone` roles; dominated-but-novel retained | `test_transfer.py`, `test_archive_memory.py` |
| Population-Based Training (Jaderberg 2017) | Exploit+explore over populations | Population with lineage, not serial mutation | archive lineage + `sample_parent(frontier/novelty/uniform)` | `test_archive_memory.py::test_archive_lineage_three_generations` |
| NSGA-II (Deb 2002) | Multi-objective selection without scalarisation | Constrained non-dominated sorting; never collapse to one score | `multi_objective.pareto_relation` + `archive.frontier` | `test_multi_objective_gates.py::test_pareto_*` |
| Bayesian optimisation / EI (Snoek 2012) | Which experiment next | Expected value of information for prioritisation | `ExperimentPrioritizer` — bootstrap-CI-width × family prior ÷ compute; **no GP dependency** | exercised in `test_cycle.py` (ordering affects which hyps run first) |
| Sequential testing / alpha-spending (Lan-DeMets; Johari et al. 2017) | Repeated looks consume error budget | Explicit budgets for holdout queries and trials | contract `max_trials`, `holdout_query_budget`; `bonferroni_alpha` | `test_trial_budget_rejected`, `test_holdout_query_budget_rejected` |
| Holm / BH correction (Holm 1979; Benjamini-Hochberg 1995) | Many trials → inflated significance | Family-wise/step-up control | `multiplicity.holm_rejections`, `bonferroni_alpha` in evaluator | `test_multi_objective_gates` (budget + CI gates) |
| Deflated Sharpe Ratio (Bailey & López de Prado 2014) | Best-of-N backtests are overfit | Compare observed SR to E[max SR] across trial family | `multiplicity.deflated_sharpe_ratio` — returns `None` below preconditions, never fabricated | — (helper; wired as `unavailable` reporting) |
| Probability of Backtest Overfitting / CSCV (Bailey et al. 2016) | Selection bias across configurations | CSCV over fold combinations | `multiplicity.pbo_cscv` — `None` below 4 folds/4 candidates | — (helper) |
| Safe policy improvement (Laroche et al. 2019); constrained RL (Achiam 2017 CPO) | New policy may be worse under weak evidence | Fall back to incumbent unless lower bound clears threshold | paired CI lower bound > 0 required; `insufficient_evidence` otherwise | `test_insignificant_improvement_insufficient` |
| Offline RL eval pitfalls (D4RL, Fu et al. 2021) | Off-policy estimates overestimate | RL reward ≠ raw PnL; L1 excludes RL candidates entirely | adapter allowlist covers only interpretable param strategies | adapter `check_params` tests |
| Curriculum & continual learning (Bengio 2009; Kirkpatrick 2017) | Improvements must not forget past regimes | Regression panel over past regimes | `TransferEvaluator` regime panel × seeds × cost multipliers | `test_transfer.py` |
| Causal attribution (Pearl; Athey-Imbens 2017) | Correlation ≠ effect | One factor changed at a time; paired design | contract enforces `len(change_set)==1`; paired per-bar replay | `test_rsi_replay_causality.py` (existing) + v2 binding checks |
| Goodhart / reward hacking (Gao et al. 2023; Skalse et al. 2022) | Metrics get gamed | Proxy divergence detection | `anti_gaming.py` — 7 checks incl. foresight, cost floor, cherry-pick, risk hiding | `test_anti_gaming.py` (11 tests) |
| Calibration (Guo et al. 2017; Brier 1950) | Probabilities must be calibrated OOS | Brier/ECE in metric vector | `metric_registry` fields; `not_applicable` for direction-only strategies | metric registry validated in contract tests |
| Champion/challenger, shadow, canary (industry deployment practice) | Stage-ladder promotion with kill thresholds | Separate stages, human authorization between research and capital | `PromotionLadder` + `OperatorAuthorization` (Ed25519, expiring) | `test_promotion_ladder_authorization` |
| Paper→production traceability (AIDE/mission §6) | Research jumps to prod without evidence chain | Claim→principle→hypothesis→prototype→experiment→evidence→decision | this document + `ImprovementGenome.evaluation_plan` binding | binding checks in `evaluate` |

## What did NOT transfer (and why)

| Mechanism | Reason rejected for AlphaAlgo |
|---|---|
| Darwin Gödel Machine code-level self-editing | A candidate that rewrites its own code or its evaluator is the threat model; L1 is bounded-parameter only. |
| RL reward = PnL | Mission §6 prohibits; paired cost-adjusted net used instead. |
| GP-based Bayesian optimization | Adds sklearn/scipy GP cost + failure modes; VOI proxy adequate at current scale. |
| Nash/self-play training | No adversary population; markets are not self-play games. |
| Meta-gradient / learned optimizers (Andrychowicz 2016) | Requires differentiable inner loop; L1 strategies aren't differentiable and dataset is tiny. |
| Automated architecture search on models | Model candidates are out of L1 scope (design-only, documented debt). |
