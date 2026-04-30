# PHCE-D: Parallel Hypothesis Correction Engine with Decision Policy

## Executive Summary

PHCE-D should not be a new "AI trading brain". It should be a disciplined decision-quality layer that:

1. Generates a falsifiable hypothesis.
2. Verifies what can be verified with deterministic or statistical checks.
3. Converts contradictory evidence into scenario-conditioned uncertainty.
4. Produces a bounded decision outcome.
5. Forces every trade-related outcome through validation and paper trading before any capital is eligible.

If this system cannot produce enough validated edge after costs and slippage, the correct output is `NO_TRADE`, `NEEDS_MORE_EVIDENCE`, `RESEARCH_ONLY`, or `REJECTED`.

The word "parallel" only belongs in the research lane. It does not belong in the latency-sensitive execution lane unless measured quality improvement exceeds the latency and complexity penalty.

## Hard Rules

- No direct live execution.
- No forced convergence.
- No contradiction as final output.
- No LLM-only validation for high-trust claims.
- No parallel LLM reasoning for latency-sensitive execution.
- `UNKNOWN`, `HOLD`, and `NO_TRADE` are valid outputs.
- Every trade-related output must pass Validation Gateway and paper trading before capital use.

## Brutal Honesty

- Parallel hypotheses do not create alpha by themselves. They mostly create more ways to overfit, rationalize, and delay decisions.
- Contradiction handling is not intelligence. It is error containment.
- Credal probabilities are only useful if they change a decision boundary. If they do not affect the policy outcome, they are bookkeeping, not edge.
- LLMs are acceptable for hypothesis proposal, evidence summarization, and research drafting. They are not acceptable as sole validators for claims that would influence capital allocation.
- For MVP, one hypothesis with good verification beats five hypotheses with weak verification.

## Design Goal

Produce a decision object that is:

- auditable
- falsifiable
- cost-aware
- scenario-aware
- promotion-gated

The system must prefer refusing action over manufacturing confidence.

## Architecture

1. Evidence Intake
2. Hypothesis Generator
3. Deterministic / Statistical Verifier
4. Scenario Conditioner
5. Contradiction Classifier
6. Credal Probability Engine
7. Decision Policy Engine
8. Validation Gateway
9. Paper-Trade Promotion Layer
10. Decision Replay Debugger
11. Temporal Leakage Quarantine
12. Cost Stress Ladder
13. Trade Clustering Detector
14. Bypass Path Scanner

The first 9 modules are the core decision pipeline. Modules 10-14 are mandatory control modules. They exist to stop fake edge, invalid research, cost denial, path bypasses, and misleading paper-trade results.

Required research and promotion controls:

1. Pre-Registration Protocol
2. Hypothesis Complexity Penalty
3. Backtest Lockbox
4. Parameter Stability Map
5. Signal Decay Curve
6. Regime Coverage Matrix
7. Marginal Portfolio Risk Gate
8. Paper-to-Live Gap Estimator
9. Broker/Venue Health Gate
10. Decision Reason Code System

## Two Lanes

### Research Lane

Used for offline research, batch analysis, and non-urgent decisions.

- May use LLM-assisted hypothesis proposal.
- May evaluate multiple hypotheses in parallel.
- Must still require deterministic or statistical verification before any high-trust claim.
- Output is usually `RESEARCH_ONLY`, `NEEDS_MORE_EVIDENCE`, `PAPER_TRADE_CANDIDATE`, or `REJECTED`.

### Decision Lane

Used for bounded-latency decision support.

- No parallel LLM reasoning.
- No free-form debate loops.
- Only pre-registered hypothesis families.
- Deterministic verifiers first.
- Statistical checks only if they fit the latency budget.
- Output must be one of the allowed decision classes, not a prose contradiction.

## Canonical Decision Outputs

- `BUY`
- `SELL`
- `HOLD`
- `NO_TRADE`
- `RESEARCH_ONLY`
- `NEEDS_MORE_EVIDENCE`
- `PAPER_TRADE_CANDIDATE`
- `REJECTED`

## Module Contracts

### 1. Evidence Intake

Purpose:
Collect only point-in-time, permissioned, timestamped evidence needed to test the current hypothesis.

Inputs:
- market bars or quotes
- volume and liquidity measures
- spread, slippage, fee, and market impact inputs
- portfolio state
- regime labels or regime features
- data lineage metadata
- optional external research notes marked low-trust until verified

Outputs:
- normalized evidence packet
- freshness and completeness report
- lineage hash
- missing-field list
- trust labels per evidence source

Failure modes:
- stale data
- lookahead leakage
- survivorship bias
- missing timestamps
- inconsistent symbol mapping
- unsupported license or provenance
- regime features computed using future data

Latency budget:
- Decision lane: 5-20 ms from in-memory cache
- Research lane: 100-1000 ms if historical retrieval is required

Cost budget:
- Decision lane: zero LLM cost
- Research lane: near-zero compute cost relative to downstream analysis

Validation method:
- schema validation
- timestamp monotonicity checks
- point-in-time membership validation
- source license and provenance checks
- deterministic freshness thresholds

Kill criteria:
- missing required fields
- stale or untrusted evidence for a high-trust claim
- lookahead or leakage suspicion
- cost inputs unavailable when evaluating a trade hypothesis

### 2. Hypothesis Generator

Purpose:
Produce a falsifiable market claim with explicit assumptions, horizon, trigger, and expected edge source.

Inputs:
- normalized evidence packet
- hypothesis templates
- optional research prompts
- historical failure memory

Outputs:
- one structured hypothesis for MVP
- hypothesis metadata:
  - direction
  - horizon
  - expected mechanism
  - invalidation conditions
  - minimum edge threshold
  - required verifier set

Failure modes:
- vague claim
- tautology disguised as insight
- untestable mechanism
- duplicate hypothesis under different wording
- hypothesis requires unavailable evidence
- LLM hallucination of nonexistent market structure

Latency budget:
- Decision lane MVP: 1-5 ms using deterministic templates only
- Research lane: up to 500 ms for optional LLM-assisted proposal

Cost budget:
- Decision lane: zero LLM cost
- Research lane: cap at one low-cost proposal pass per evidence packet

Validation method:
- template conformance
- falsifiability check
- duplicate check against active hypotheses
- invalidation rule presence
- explicit edge-above-cost requirement

Kill criteria:
- no falsifiable trigger
- no invalidation rule
- expected gross edge below likely transaction costs
- claim depends only on unverified LLM reasoning

### 3. Deterministic / Statistical Verifier

Purpose:
Test the hypothesis against reality, not narrative.

Inputs:
- structured hypothesis
- evidence packet
- transaction cost estimates
- historical sample or rolling window

Outputs:
- verification report
- pass/fail/unknown flags for each claim component
- effect size estimate
- uncertainty notes
- cost-adjusted edge estimate

Failure modes:
- sample too small
- leakage in feature construction
- p-hacking through repeated slicing
- deterministic rules too weak to discriminate noise
- verifier mismatch to hypothesis horizon
- cost model omitted or misapplied

Latency budget:
- Decision lane MVP: 10-50 ms
- Research lane: 100 ms to several seconds depending on sample

Cost budget:
- zero LLM cost
- bounded compute only

Validation method:
- deterministic invariants
- rolling out-of-sample checks
- bootstrap or simple confidence intervals where justified
- sign consistency checks
- cost/slippage subtraction before edge scoring

Kill criteria:
- unverifiable high-trust claim
- effect disappears after cost adjustment
- sign flips across nearby windows without scenario explanation
- sample size below configured minimum

### 4. Scenario Conditioner

Purpose:
Translate "it depends" into explicit conditions instead of vague contradiction.

Inputs:
- verification report
- regime features
- liquidity state
- volatility state
- market structure conditions

Outputs:
- scenario set
- per-scenario applicability conditions
- per-scenario directional effect
- scenario support weights

Failure modes:
- scenarios invented after seeing outcomes
- overlapping scenarios that double-count evidence
- regime labels too unstable to use
- too many scenarios for the amount of data

Latency budget:
- Decision lane: 5-15 ms
- Research lane: 20-100 ms

Cost budget:
- zero LLM cost in decision lane
- optional LLM summarization only in research reporting

Validation method:
- scenario partition sanity checks
- minimum support per scenario
- regime stability checks
- out-of-sample scenario consistency

Kill criteria:
- scenario support too low
- scenario partition unstable
- scenarioing increases complexity without improving discrimination

### 5. Contradiction Classifier

Purpose:
Classify why evidence conflicts and route to the right outcome.

Inputs:
- hypothesis
- verification report
- scenario set

Outputs:
- contradiction type:
  - measurement conflict
  - scenario conflict
  - model conflict
  - insufficient evidence
  - invalid hypothesis
- contradiction severity
- resolution path

Failure modes:
- treating noise as contradiction
- hiding invalidity inside "needs more evidence"
- forced averaging of opposing signals
- failure to separate scenario-specific truth from global falsity

Latency budget:
- 1-5 ms

Cost budget:
- zero LLM cost

Validation method:
- deterministic routing rules
- contradiction taxonomy coverage tests
- replay against known false-positive cases

Kill criteria:
- contradiction cannot be resolved into scenario conditions
- conflict arises from bad data
- hypothesis is internally inconsistent

### 6. Credal Probability Engine

Purpose:
Represent uncertainty as a bounded set of probabilities instead of fake point precision.

Inputs:
- scenario set
- contradiction classification
- verifier outputs
- prior reliability weights

Outputs:
- lower and upper probability bounds per outcome
- ambiguity score
- confidence class

Failure modes:
- fake precision
- arbitrary priors
- intervals so wide they are operationally useless
- complexity added without changing a decision

Latency budget:
- 1-10 ms

Cost budget:
- zero LLM cost

Validation method:
- calibration on historical decisions
- monotonicity checks
- sensitivity analysis on priors and scenario weights

Kill criteria:
- interval width exceeds actionability threshold
- credal bounds do not support a distinct policy action
- ambiguity remains too high after scenario conditioning

### 7. Decision Policy Engine

Purpose:
Map verified, cost-adjusted, scenario-conditioned uncertainty into an allowed action.

Inputs:
- cost-adjusted edge
- credal probability bounds
- ambiguity score
- contradiction class
- portfolio context
- latency class

Outputs:
- one final classification:
  - `BUY`
  - `SELL`
  - `HOLD`
  - `NO_TRADE`
  - `RESEARCH_ONLY`
  - `NEEDS_MORE_EVIDENCE`
  - `PAPER_TRADE_CANDIDATE`
  - `REJECTED`
- decision rationale
- required next step

Failure modes:
- rewarding weak positive expectancy with action
- ignoring uncertainty width
- collapsing unknown into hold
- using policy thresholds not tied to realized outcomes

Latency budget:
- 1-5 ms

Cost budget:
- zero LLM cost

Validation method:
- backtest of policy decisions versus naive baselines
- abstention-quality measurement
- threshold sweep on false-positive reduction

Kill criteria:
- no measurable uplift versus simpler gating baseline
- policy approves trades that fail cost-adjusted expectancy thresholds
- policy cannot explain abstentions and approvals in rule form

#### Policy Rules

`BUY`:
- only if direction is long
- deterministic/statistical verification passed
- net edge remains positive after costs and slippage
- credal lower bound exceeds buy threshold
- ambiguity below action threshold
- validation gateway passes

`SELL`:
- same as `BUY`, but short or exit direction

`HOLD`:
- existing position context says do not add, reduce, or reverse
- evidence does not justify state change

`NO_TRADE`:
- no actionable edge
- uncertainty too high
- transaction costs absorb expected edge
- scenario split too wide to justify action

`RESEARCH_ONLY`:
- interesting hypothesis with incomplete validation
- useful for offline study, not for trade consideration

`NEEDS_MORE_EVIDENCE`:
- hypothesis might be valid, but current sample, freshness, or support is insufficient

`PAPER_TRADE_CANDIDATE`:
- research and decision criteria passed
- safe enough to shadow or paper trade
- still not eligible for live capital

`REJECTED`:
- invalid hypothesis
- failed verification
- failed validation gateway
- prohibited source or method

### 8. Validation Gateway

Purpose:
Apply hard safety and risk gates after the decision policy, before any promotion.

Inputs:
- decision object
- portfolio state
- risk limits
- market hostility indicators
- catastrophic risk indicators
- claim verification status

Outputs:
- gateway-approved or gateway-rejected status
- rejection reasons
- residual risk score

Failure modes:
- bypass paths
- soft warnings where hard rejection is required
- inconsistent treatment across strategies
- cost-aware alpha approved but portfolio risk ignored

Latency budget:
- 5-30 ms

Cost budget:
- zero LLM cost

Validation method:
- deterministic rule tests
- adversarial replay
- red-team path coverage
- invariant tests that no trade skips the gateway

Kill criteria:
- any bypass path exists
- catastrophic risk flag present
- failed-claims or low-confidence gate hit
- portfolio or drawdown limits exceeded

### 9. Paper-Trade Promotion Layer

Purpose:
Turn validated candidates into paper-traded evidence before any capital eligibility.

Inputs:
- gateway-approved `PAPER_TRADE_CANDIDATE`
- order intent
- transaction cost assumptions
- paper execution logs
- realized paper performance metrics

Outputs:
- paper-trade record
- stage status:
  - accumulating evidence
  - failed
  - passed threshold for next governance review
- promotion recommendation

Failure modes:
- paper fills too idealized
- no benchmark comparison
- not enough trades
- regime mismatch between research and paper-trade window
- manual cherry-picking of promotion windows

Latency budget:
- synchronous logging: 1-10 ms
- evaluation: asynchronous batch

Cost budget:
- compute/storage only

Validation method:
- realized paper PnL and drawdown
- Sharpe and hit-rate thresholds
- cost-adjusted benchmark delta
- minimum trade count and day count
- promotion audit trail

Kill criteria:
- weak-signal strategy fails to outperform no-trade baseline
- negative paper-trade Sharpe delta
- unstable edge after realistic cost assumptions
- insufficient sample size for promotion

### 10. Decision Replay Debugger

Purpose:
Reconstruct an exact past decision from stored evidence, configuration, and gate outputs so failures can be debugged without story-making.

Inputs:
- decision ID
- evidence packet snapshot
- hypothesis snapshot
- verifier outputs
- scenario and credal outputs
- policy thresholds
- gateway results
- paper-trade outcome if available
- code version and config hash

Outputs:
- replay decision trace
- divergence report versus original decision
- deterministic step log
- root-cause candidate list

Failure modes:
- non-deterministic code path
- missing snapshot data
- hidden dependency on mutable state
- config drift with no version trace
- inability to reproduce historical cost estimates

Latency budget:
- not on the decision critical path
- offline replay: 100 ms to 5 s

Cost budget:
- zero LLM cost
- bounded compute and storage cost only

Validation method:
- exact input hashing
- deterministic replay against stored decision records
- tolerance-bounded comparison for floating-point outputs
- replay regression suite on known incidents

Kill criteria:
- historical decisions cannot be reproduced within configured tolerance
- key decision inputs are missing from the audit record
- replay reveals hidden state dependence or nondeterminism

### 11. Temporal Leakage Quarantine

Purpose:
Detect and block lookahead leakage, revised-data leakage, and label contamination before any hypothesis is trusted.

Inputs:
- feature timestamps
- label timestamps
- join and resample rules
- point-in-time universe membership
- source revision metadata
- dataset lineage and preprocessing graph

Outputs:
- quarantine status
- blocked feature or dataset list
- leakage findings with exact offending transformation
- approved feature registry for downstream use

Failure modes:
- future bars included in feature windows
- revised macro or fundamentals used as-if known earlier
- target labels leaking into feature engineering
- split logic that lets future regime labels bleed backward
- late-arriving data treated as contemporaneous

Latency budget:
- research lane batch checks: 50 ms to several seconds depending on dataset size
- decision lane approved-feature check: 1-5 ms

Cost budget:
- zero LLM cost
- bounded compute only

Validation method:
- timestamp monotonicity and as-of checks
- synthetic leakage probes
- train/validation split discipline tests
- point-in-time reconstruction tests
- feature approval allowlist enforcement

Kill criteria:
- any unresolved lookahead or label leakage
- any feature without a validated as-of timestamp
- any dataset revision used without point-in-time handling

### 12. Cost Stress Ladder

Purpose:
Test whether expected edge survives worse-than-base execution conditions instead of only surviving in optimistic cost assumptions.

Inputs:
- base transaction cost estimate
- spread inputs
- slippage inputs
- market impact inputs
- liquidity regime
- expected gross edge
- target size

Outputs:
- stress ladder report
- edge-after-cost at each stress rung
- break-even rung
- stress survival score

Failure modes:
- cost model calibrated only to median conditions
- use of midpoint fantasy fills
- ignoring spread widening in volatility spikes
- no size sensitivity
- stress ladder so mild it never changes a decision

Latency budget:
- decision lane: 2-10 ms for a small fixed ladder
- research lane: 20-100 ms for richer scenario ladders

Cost budget:
- zero LLM cost
- bounded compute only

Validation method:
- replay against realized paper-trade costs
- worst-decile spread and slippage comparisons
- regime-conditioned stress calibration
- monotonicity tests that harsher costs never improve edge

Kill criteria:
- edge turns negative under moderate stress
- decision only survives the base case and fails the first stress rung
- size cannot be reduced enough to fit the cost budget without destroying expectancy

### 13. Trade Clustering Detector

Purpose:
Detect when many trades are really one repeated bet in disguise, which makes paper-trade evidence look stronger than it is.

Inputs:
- candidate decisions
- order timestamps
- symbol and sector identifiers
- factor and regime tags
- holding periods
- portfolio exposures

Outputs:
- clustering flags
- effective independent trade count
- cluster concentration score
- clustering penalty or block recommendation

Failure modes:
- treating highly correlated trades as independent evidence
- bursty entries around the same event counted as many wins
- repeated same-regime trades dominating validation
- pyramiding or duplicate entries hidden inside separate IDs

Latency budget:
- decision lane recent-window check: 1-10 ms
- paper-trade evaluation: asynchronous batch allowed

Cost budget:
- zero LLM cost
- bounded compute only

Validation method:
- rolling burst detection
- correlation and regime overlap checks
- effective sample size estimation
- paper-trade replay with clustered trades collapsed

Kill criteria:
- effective independent trade count falls below the minimum evidence threshold
- cluster concentration exceeds configured exposure limits
- paper-trade success disappears when clustered trades are collapsed to independent bets

### 14. Bypass Path Scanner

Purpose:
Prove that no trade-related output can reach execution, promotion, or approval-sensitive code without going through the intended PHCE-D gates.

Inputs:
- code path graph
- action schemas
- event logs
- approval records
- deployment and promotion endpoints
- integration tests and runtime invariants

Outputs:
- bypass findings
- path coverage report
- blocked endpoint list
- fail-closed certification status

Failure modes:
- hidden direct broker or order path
- manual override without signed approval
- separate code path that writes paper-trade promotions directly
- logging-only gates with no enforcement
- test coverage that misses the real execution path

Latency budget:
- CI and pre-deploy only
- seconds to minutes is acceptable

Cost budget:
- zero LLM cost
- engineering and CI compute only

Validation method:
- static path scanning
- runtime invariant tests
- fail-closed integration tests
- approval-envelope verification
- red-team attempts to route around the gateway

Kill criteria:
- any reachable bypass path exists
- any trade-related action can occur without a logged gateway decision
- any promotion path skips paper-trade evidence requirements
- any override path lacks explicit signed approval and audit trail

## Research Discipline And Promotion Controls

These controls are not alpha modules. They are discipline, audit, and promotion filters. If they make fewer trades eligible, they are doing their job.

### 1. Pre-Registration Protocol

Purpose:
Freeze the hypothesis, thresholds, feature set, validation window, and kill criteria before looking at holdout or paper-trade outcomes.

Enforced at:
- before verifier execution
- before any backtest lockbox access
- before paper-trade candidacy

Outputs:
- pre-registration ID
- immutable hypothesis card
- allowed parameter ranges
- allowed data windows
- disallowed post-hoc edits

Kill criteria:
- hypothesis changed after outcome inspection
- thresholds tuned on the evaluation window
- feature list modified without a new registration

### 2. Hypothesis Complexity Penalty

Purpose:
Penalize hypotheses that use too many parameters, branches, scenarios, or exceptions relative to available evidence.

Enforced at:
- hypothesis generation
- verifier scoring
- decision policy thresholding

Outputs:
- complexity score
- effective degrees-of-freedom estimate
- adjusted confidence or edge haircut
- rejection reason when complexity overwhelms evidence

Kill criteria:
- parameter count is too high for sample size
- added complexity does not improve out-of-sample usefulness
- exception rules explain only past failures

### 3. Backtest Lockbox

Purpose:
Protect final evaluation data from repeated peeking and accidental tuning.

Enforced at:
- research evaluation
- strategy promotion review
- benchmark reporting

Outputs:
- lockbox access record
- holdout evaluation result
- access count
- lockbox contamination status

Kill criteria:
- lockbox accessed before pre-registration
- more than the allowed number of evaluations
- any parameter change after lockbox inspection

### 4. Parameter Stability Map

Purpose:
Show whether the hypothesis only works at one fragile parameter point or across a reasonable neighborhood.

Enforced at:
- verifier review
- research promotion
- paper-trade candidacy

Outputs:
- parameter sensitivity grid
- stable region score
- cliff-risk flags
- recommended conservative parameter set

Kill criteria:
- edge appears only at one narrow parameter value
- small parameter changes flip sign after costs
- stability region fails across nearby regimes

### 5. Signal Decay Curve

Purpose:
Measure how quickly the signal loses predictive value after detection.

Enforced at:
- horizon selection
- paper-trade candidate sizing
- latency policy review

Outputs:
- edge by holding horizon
- half-life estimate
- stale-signal threshold
- allowed decision latency class

Kill criteria:
- signal decays faster than the system can act
- profitable horizon disappears after cost stress
- delayed decisions behave like noise

### 6. Regime Coverage Matrix

Purpose:
Prevent a strategy from claiming broad validity when it has only been tested in one market condition.

Enforced at:
- scenario conditioning
- verifier review
- promotion review

Outputs:
- regime-by-regime support matrix
- missing-regime list
- per-regime edge and drawdown
- allowed deployment regimes

Kill criteria:
- target regime lacks evidence
- performance depends on a single favorable regime
- regime classifier is too unstable to gate decisions

### 7. Marginal Portfolio Risk Gate

Purpose:
Evaluate the incremental portfolio risk of a candidate, not just the standalone trade quality.

Enforced at:
- after decision policy
- before validation gateway approval
- before paper-trade promotion scoring

Outputs:
- marginal VaR or drawdown contribution
- correlation and concentration delta
- exposure overlap score
- allow, reduce-size, or reject recommendation

Kill criteria:
- marginal risk breaches portfolio limits
- candidate duplicates existing exposure
- expected edge is too small for the added portfolio risk

### 8. Paper-to-Live Gap Estimator

Purpose:
Estimate how much paper performance may degrade under real execution, partial fills, queue position, latency, fees, and venue behavior.

Enforced at:
- paper-trade review
- live-readiness governance
- promotion reporting

Outputs:
- expected live slippage gap
- fill-quality degradation estimate
- latency sensitivity score
- live-readiness haircut

Kill criteria:
- paper edge disappears after realistic live gap adjustment
- paper fills depend on unrealistic prices or liquidity
- live venue assumptions are unverified

### 9. Broker/Venue Health Gate

Purpose:
Block candidates when execution infrastructure, venue liquidity, broker status, or data/execution connectivity is unhealthy.

Enforced at:
- decision lane preflight
- paper-trade logging
- live-readiness governance

Outputs:
- venue health status
- broker connectivity status
- spread and depth warnings
- action block or degradation reason

Kill criteria:
- broker connection is degraded or unauthenticated
- venue spread or depth violates execution assumptions
- recent rejects, stale quotes, or abnormal latency exceed thresholds

### 10. Decision Reason Code System

Purpose:
Make every output machine-auditable by assigning stable reason codes instead of relying on prose explanations.

Enforced at:
- every final decision output
- replay debugger
- benchmark aggregation
- incident review

Outputs:
- primary reason code
- secondary reason codes
- blocking gate ID
- stable human-readable rationale

Kill criteria:
- decision has no reason code
- reason code does not map to an enforced rule
- final decision cannot be grouped for benchmark review

## Decision State Machine

1. Intake evidence.
2. Run Temporal Leakage Quarantine.
3. Load or create a pre-registered hypothesis card.
4. Apply the Hypothesis Complexity Penalty.
5. Verify deterministically and statistically where justified.
6. Use Backtest Lockbox only under pre-registered access rules.
7. Build Parameter Stability Map and Signal Decay Curve.
8. Run Cost Stress Ladder before allowing any positive action.
9. If evidence conflicts, classify the conflict.
10. Convert conflict into scenario-conditioned credal bounds and Regime Coverage Matrix.
11. Apply decision policy and assign Decision Reason Codes.
12. Run Trade Clustering Detector on candidate actions and evidence accumulation.
13. Run Marginal Portfolio Risk Gate.
14. If output is trade-related, pass Validation Gateway, including market hostility and event-risk embargo inputs, plus Broker/Venue Health Gate.
15. If gateway passes, output `PAPER_TRADE_CANDIDATE`.
16. Promote only after paper-trade evidence clears thresholds and Paper-to-Live Gap Estimator haircuts.
17. Use Decision Replay Debugger for incidents, regressions, and disputed outcomes.
18. Run Bypass Path Scanner continuously in CI and pre-deploy governance.

No stage is allowed to output "contradiction" as the final answer. It must resolve to:

- `NO_TRADE`
- `NEEDS_MORE_EVIDENCE`
- `RESEARCH_ONLY`
- `REJECTED`
- or a scenario-conditioned trade candidate

## MVP

The MVP should be deliberately small.

Scope:
- one hypothesis at a time
- deterministic checks first
- basic statistical sanity only if cheap
- mandatory cost/slippage filter
- paper-trade logging
- no live execution path

Mandatory components:
- Evidence Intake from point-in-time market and portfolio data
- Temporal Leakage Quarantine
- Pre-Registration Protocol for the single active hypothesis
- Hypothesis template library with one active hypothesis
- Hypothesis Complexity Penalty with a simple parameter-count and branch-count score
- Deterministic verifier
- Backtest Lockbox rules, even if the first MVP only records locked holdout access
- Parameter Stability Map over a small fixed threshold neighborhood
- Signal Decay Curve for the selected horizon
- Cost model integration
- Cost Stress Ladder with at least `base`, `moderate`, and `harsh` rungs
- Regime Coverage Matrix with explicit missing-regime labels
- Decision policy with abstention outputs
- Trade Clustering Detector with a simple recent-window burst rule
- Marginal Portfolio Risk Gate
- Validation gateway
- Broker/Venue Health Gate in block-only mode
- Paper-trade candidate logging
- Paper-to-Live Gap Estimator as a conservative haircut on paper results
- Decision Replay Debugger with exact input and config hashes
- Decision Reason Code System
- Bypass Path Scanner in CI and promotion checks

Explicit non-goals for MVP:
- multi-agent debate
- free-form parallel LLM reasoning
- self-modifying policy thresholds
- broad credal algebra if simple probability bounds are enough
- production capital deployment

## Recommended MVP Hypothesis

Start with one hypothesis family such as:

"If short-horizon directional signal strength exceeds threshold X, and estimated edge after fees, slippage, and market impact remains above threshold Y, then the trade is eligible for paper-trade candidacy. Otherwise abstain."

Why this is the right MVP:

- easy to falsify
- easy to cost-adjust
- easy to benchmark against a simpler gate
- hard to hide behind narrative

## Benchmark Framework

PHCE-D should be judged against a simpler baseline gate, not against aspiration.

### Primary benchmarks

- weak-signal promotion reduction
- false positive signal rate
- refusal precision, refusal recall, and abstention cost
- paper-trade Sharpe delta
- cost-adjusted edge
- stress-survival rate under the Cost Stress Ladder
- pre-registration violation count
- complexity-adjusted edge
- lockbox access count and contamination rate
- parameter stability score
- signal half-life versus decision latency
- regime coverage ratio
- marginal portfolio risk added per candidate
- paper-to-live gap estimate
- broker or venue health block rate
- event embargo block rate
- calibration error by confidence bucket
- config diff risk review coverage
- decision reason-code coverage
- decision usefulness
- latency per decision
- cost per useful hypothesis
- percentage of outputs that become validated paper-trade candidates
- replay reproducibility rate
- temporal leakage catch rate before promotion
- cluster-adjusted paper-trade performance
- bypass scan finding count

### Definitions

Weak-signal promotion reduction:
- reduction in candidates promoted to paper trade whose realized paper performance later fails thresholds

False positive signal rate:
- fraction of approved or promoted signals with negative realized edge after cost

Refusal precision, refusal recall, and abstention cost:
- measures whether `NO_TRADE`, `REJECTED`, and `NEEDS_MORE_EVIDENCE` decisions avoided bad candidates or incorrectly blocked useful ones

Paper-trade Sharpe delta:
- difference between PHCE-D-filtered paper basket and baseline paper basket

Cost-adjusted edge:
- expected return minus spread, slippage, fees, and market impact

Pre-registration violation count:
- number of hypotheses, thresholds, or feature definitions changed after evaluation data was inspected

Complexity-adjusted edge:
- cost-adjusted edge after subtracting the Hypothesis Complexity Penalty

Lockbox access count and contamination rate:
- number of final-holdout evaluations and percentage of evaluations invalidated by premature or repeated access

Parameter stability score:
- percentage of nearby parameter settings that preserve the same decision class and positive edge after costs

Signal half-life versus decision latency:
- comparison of signal decay speed against measured p95 decision and execution latency

Regime coverage ratio:
- percentage of intended deployment regimes with enough verified evidence for use

Marginal portfolio risk added per candidate:
- incremental risk contribution from each approved candidate relative to current portfolio state

Paper-to-live gap estimate:
- expected degradation from paper-trade performance to plausible live execution performance

Broker or venue health block rate:
- percentage of otherwise-valid candidates blocked because infrastructure or venue conditions were unhealthy

Event embargo block rate:
- percentage of otherwise-valid candidates blocked because known event risk invalidated normal cost, liquidity, or volatility assumptions

Calibration error by confidence bucket:
- observed outcome error grouped by declared confidence or credal interval bucket

Config diff risk review coverage:
- percentage of threshold, gate, cost-model, and hypothesis-template changes that received governance review before deployment

Decision reason-code coverage:
- percentage of final outputs with valid primary and secondary reason codes

Decision usefulness:
- proportion of outputs that lead to a better next action than always-trade or always-hold baselines

Latency per decision:
- p50, p95, p99 end-to-end latency from evidence-ready to decision-issued

Cost per useful hypothesis:
- compute and model cost divided by hypotheses that improve downstream decisions

Percentage of outputs that become validated paper-trade candidates:
- how often the system generates something strong enough to survive gating

Stress-survival rate:
- percentage of candidates that remain positive after moderate and harsh cost assumptions

Replay reproducibility rate:
- percentage of historical PHCE-D decisions that can be replayed to the same outcome within tolerance

Temporal leakage catch rate before promotion:
- fraction of contaminated features or datasets blocked before they affect candidate decisions

Cluster-adjusted paper-trade performance:
- paper-trade performance recomputed after collapsing clustered trades to effective independent bets

Bypass scan finding count:
- number of reachable bypass paths discovered by static and runtime enforcement tests

### Success criterion

Parallel hypotheses should only be enabled if they produce a measurable improvement in at least:

- false positive reduction
- cost-adjusted edge
- or paper-trade Sharpe delta

without breaking:

- latency budget
- operational simplicity
- auditability

If not, keep PHCE-D single-hypothesis.

## Adjacent Control Placement Decisions

These items are useful, but they should not all become PHCE-D core modules. A good architecture says where a control belongs and refuses duplicate machinery.

| Item | Placement | Verdict |
| --- | --- | --- |
| Shadow-Mode Replay Engine | Paper-Trade Promotion Layer | Already covered by running on live data without execution. Keep the name as an implementation mode, not a new module. |
| Feature Availability Calendar | Evidence Intake | Implement as a point-in-time availability calendar for freshness and as-of checks. It is not a separate idea from evidence discipline. |
| Data Vendor Disagreement Resolver | Contradiction Classifier | Treat vendor disagreement as measurement conflict. Route to scenario conditioning, `NO_TRADE`, or `REJECTED`. |
| No-Trade Baseline Ledger | Benchmark and research evaluation store | Required for refusal precision, recall, and abstention-cost measurement. Not a decision-time module. |
| Confidence Calibration Registry | Metrics and research evaluation store | Required later for calibration governance. Not MVP and not a standalone PHCE-D module. |
| Market Hostility Detector | Validation Gateway input | Implement as `market_hostility_score` consumed by the gateway. Do not duplicate the gateway. |
| Correlated Exposure Compressor | Portfolio risk and Validation Gateway logic | Implement through portfolio correlation, concentration, and marginal-risk gates. Not a separate PHCE-D module. |
| Decision Dissent Record | Decision Reason Code System | Useful as "best reason to reject" or strongest dissent, but it supports auditability rather than changing the core pipeline. |
| Promotion Decay Timer | Paper-Trade Promotion Layer | Implement as hypothesis expiration and renewal. A candidate should decay if paper evidence goes stale. |
| Config Diff Risk Scorer | Deployment, CI, and governance pipeline | Not PHCE-D decision-time logic. Keep it as an AlphaAlgo deployment control for threshold, cost model, validation gate, and template changes. |
| Event-Risk Embargo System | Validation Gateway input | Do not add as a standalone PHCE-D module. Implement embargo windows for FOMC, CPI, NFP, earnings, rate decisions, broker maintenance, and other known execution-risk events. |

Hard placement rule:

- If a control changes whether a specific candidate can proceed, it belongs in Decision Policy, Validation Gateway, or Paper-Trade Promotion.
- If a control validates the research process, it belongs in research evaluation, replay, lockbox, or calibration storage.
- If a control protects production behavior after code or config changes, it belongs in CI, deployment, and governance.

## Integration with Existing AlphaAlgo Components

PHCE-D should reuse the existing substrate instead of inventing parallel infrastructure.

Recommended anchors:

- PHCE-D MVP AI:
  - `trading_bot/core/phce_d_engine.py`
  - implements the conservative one-hypothesis engine, deterministic verifier, cost stress ladder, gateway validation, and paper-only promotion path

- Evidence Intake:
  - `trading_bot/core/research_mvp_pipeline.py`
  - use clean data, point-in-time membership, lineage hashing, and the paper ledger substrate
  - Feature Availability Calendar belongs here as an implementation of as-of availability and freshness checks

- Decision Replay Debugger and Temporal Leakage Quarantine:
  - `trading_bot/core/research_mvp_pipeline.py`
  - use lineage hashes, point-in-time reconstruction, and paper ledger records as the replay substrate

- Pre-Registration Protocol, Backtest Lockbox, and Decision Reason Code System:
  - `trading_bot/core/research_mvp_pipeline.py`
  - `trading_bot/core/autonomy_control_plane.py`
  - store immutable hypothesis cards, lockbox access records, and stable reason codes with every decision record

- Hypothesis Complexity Penalty, Parameter Stability Map, Signal Decay Curve, and Regime Coverage Matrix:
  - `trading_bot/core/research_mvp_pipeline.py`
  - these should attach verifier diagnostics to the decision record instead of living only in research notebooks

- Cost / slippage filter:
  - `trading_bot/core/transaction_cost_model.py`
  - `trading_bot/core/research_mvp_pipeline.py`

- Cost Stress Ladder:
  - `trading_bot/core/transaction_cost_model.py`
  - `trading_bot/core/research_mvp_pipeline.py`
  - ladder logic should wrap, not replace, the base transaction cost estimator

- Trade Clustering Detector:
  - `trading_bot/validation/paper_trading_validator.py`
  - `trading_bot/validation/risk_validation_gate.py`
  - use paper-trade history and portfolio exposure state to penalize pseudo-independent trades

- Marginal Portfolio Risk Gate:
  - `trading_bot/core/unified_decision_gate.py`
  - `trading_bot/validation/risk_validation_gate.py`
  - evaluate incremental concentration, correlation, and drawdown contribution before a candidate can move forward

- Validation Gateway:
  - `trading_bot/core/unified_decision_gate.py`
  - `trading_bot/validation/risk_validation_gate.py`
  - Market Hostility Detector and Event-Risk Embargo System belong here as gateway inputs and rules
  - Correlated Exposure Compressor belongs here as portfolio-level risk compression, not a separate decision module

- Paper-trade promotion:
  - `trading_bot/validation/paper_trading_validator.py`
  - `trading_bot/core/autonomy_control_plane.py`
  - Shadow-Mode Replay Engine, No-Trade Baseline Ledger, Decision Dissent Record, and Promotion Decay Timer belong here or in the associated evaluation store

- Paper-to-Live Gap Estimator and Broker/Venue Health Gate:
  - `trading_bot/validation/paper_trading_validator.py`
  - `trading_bot/core/transaction_cost_model.py`
  - `broker/`
  - paper performance should be haircut by realistic execution degradation and blocked when broker or venue health is poor

- Bypass Path Scanner:
  - `trading_bot/core/unified_decision_gate.py`
  - `trading_bot/core/autonomy_control_plane.py`
  - scanner should verify that all promotion and execution-sensitive paths remain fail-closed

- Config Diff Risk Scorer and Confidence Calibration Registry:
  - `trading_bot/core/autonomy_control_plane.py`
  - CI/deployment governance
  - research metrics store
  - config risk scoring is deployment control, while calibration registry is research governance

Integration rule:

PHCE-D should produce a structured decision record that these gates can consume. It should not bypass them, duplicate them, or replace them with prose reasoning.

## What To Reject

Reject the following immediately:

- any design that lets an LLM certify its own market claim
- any design that outputs a contradiction instead of an action class
- any design that treats "more agents agreed" as evidence
- any design that ignores transaction costs until after approval
- any design that adds parallel hypotheses before proving benchmark uplift
- any design that calls something "high confidence" without calibration

## Implementation Order

1. Build the PHCE-D decision schema and enum outputs.
2. Wire Evidence Intake to the research MVP substrate.
3. Add Temporal Leakage Quarantine before any verifier is trusted.
4. Add Pre-Registration Protocol and Backtest Lockbox records.
5. Add one deterministic hypothesis template.
6. Add Hypothesis Complexity Penalty before verifier scoring.
7. Add Parameter Stability Map and Signal Decay Curve diagnostics.
8. Add Regime Coverage Matrix to scenario conditioning.
9. Add base cost rejection plus the Cost Stress Ladder before any positive action.
10. Add Decision Reason Code System for every output.
11. Add a minimal Trade Clustering Detector for recent-window burst control.
12. Add Marginal Portfolio Risk Gate.
13. Route every trade-related output through the existing validation gate, with market hostility and event-risk embargo inputs.
14. Add Broker/Venue Health Gate before candidate promotion.
15. Add Shadow-Mode Replay Engine behavior through the paper-trading pipeline.
16. Add No-Trade Baseline Ledger, Decision Dissent Record, and Promotion Decay Timer to the evaluation store.
17. Log approved candidates into the paper-trading pipeline.
18. Add Paper-to-Live Gap Estimator to promotion review.
19. Add Confidence Calibration Registry after enough paper and replay outcomes exist.
20. Add Config Diff Risk Scorer to CI and deployment governance.
21. Add Decision Replay Debugger with exact input and config hashing.
22. Add Bypass Path Scanner to CI and promotion governance.
23. Benchmark against a simpler baseline.
24. Only then test whether a second hypothesis improves decisions enough to justify the extra latency.

## Final Recommendation

PHCE-D is worth building only as a refusal-capable decision-quality layer.

If implemented honestly, its first job is not to find more trades. Its first job is to prevent bad trades from being promoted by weak evidence, hidden contradictions, and unpriced execution costs.

If the MVP cannot clearly beat a simpler baseline on false positives, cost-adjusted edge, and paper-trade promotion quality, stop there. Do not add more hypotheses, more agents, or more probabilistic machinery.
