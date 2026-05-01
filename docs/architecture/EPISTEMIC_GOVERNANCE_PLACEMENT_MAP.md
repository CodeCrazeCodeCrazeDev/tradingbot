# Epistemically Governed Autonomous System Placement Map

## Meaning

An epistemically governed autonomous system is a self-auditing decision system that can:

1. generate options
2. attack its own conclusions
3. formalize claims
4. verify critical reasoning
5. refuse weak claims
6. log proof traces
7. allow action only when the reasoning graph is sufficient

Mature pipeline:

`claim -> evidence -> proof -> action`

This should not become another "AI brain". In AlphaAlgo, it belongs as a governance plane that wraps every decision-producing subsystem.

## Primary Home

The primary implementation home is:

- `trading_bot/decision_governance/`

Reason:

- It already defines the exact epistemic stack: claim graph, evidence audit, adversarial analyst, regime fit, counterfactuals, uncertainty, arbiter, memory, audit logging, and operational planes.
- It already describes itself as a self-auditing epistemic governance system.
- It already has real-time, offline, and evolution planes, which match the maturity path from decision-time refusal to deeper proof and system learning.

Do not duplicate this as a separate top-level "epistemic brain". Strengthen and connect the existing governance plane.

## System Placement

| Area | Existing files | Fit | Role in claim -> evidence -> proof -> action |
| --- | --- | --- | --- |
| Decision Governance System | `trading_bot/decision_governance/` | Primary home | Owns claim graph, evidence audit, adversarial challenge, uncertainty, arbiter, abstention, audit trail |
| Epistemic proof trace engine | `trading_bot/decision_governance/epistemic_governance.py` | Core implementation | Standardizes proof traces, refuses insufficient reasoning graphs, and emits `APPROVE`, `PAPER_ONLY`, `ABSTAIN`, `DEFER`, `REJECT`, or `MANUAL_REVIEW` |
| Claim graph | `decision_governance/layer1_claim_graph.py` | Core | Converts options and agent outputs into structured claims, assumptions, predicted outcomes, and invalidation conditions |
| Evidence auditor | `decision_governance/layer2_evidence_auditor.py` | Core | Checks evidence presence, freshness, insufficiency, and contradictions |
| Adversarial analyst | `decision_governance/layer3_adversarial_analyst.py` | Core | Attacks claims with rival explanations, hidden assumptions, base-rate objections, regime mismatch, and execution objections |
| Counterfactual and robustness | `decision_governance/layer5_counterfactual.py`, `advanced_ai/safety_verification.py`, `world_model/` | Proof support | Tests whether the claim survives perturbations, scenario changes, and formal safety checks |
| Uncertainty and refusal | `decision_governance/layer6_uncertainty.py`, `layer7_arbiter.py` | Core | Converts weak reasoning into `ABSTAIN`, `DEFER`, `REJECT`, `PAPER_ONLY`, or manual review |
| PHCE-D | `trading_bot/core/phce_d_engine.py` | Trade decision consumer and producer | Produces structured hypotheses and trade candidates; should emit proof inputs and consume governance verdicts before paper-trade candidacy |
| Governed Hivemind | `trading_bot/hivemind/governed_hivemind.py`, `trading_bot/hivemind/coordinator.py` | Swarm-governance layer | Registers advanced hivemind patterns, rejects fake-democracy/groupthink outputs, measures signal independence, and downgrades trade-like hive decisions without proof traces |
| Unified Decision Gate | `trading_bot/core/unified_decision_gate.py` | Final enforcement gate | Blocks action when claims, confidence, market hostility, catastrophic risk, or portfolio impact fail |
| Claim decomposition | `trading_bot/core/explicit_claim_decomposition.py`, `trading_bot/core/alphaalgo_core_engine.py` | Adapter/source | Decomposes trade proposals into falsifiable claims before DGS and PHCE-D use them |
| Adversarial failure analysis | `trading_bot/core/adversarial_failure_analysis.py`, `trading_bot/adversarial_decision/` | Attack layer | Attempts to break a signal before it reaches the final gate |
| COS | `trading_bot/cos/system_cognitive_os.py` | Memory and evolution substrate | Stores typed knowledge, strategies, failures, and decision outcomes; feeds retrieval and learning, not direct approval |
| Evidence lineage and research substrate | `trading_bot/core/research_mvp_pipeline.py` | Evidence backbone | Provides point-in-time data, lineage hashes, cost model, and paper ledger records needed for proof traces |
| Verified research | `trading_bot/core/aletheia_browser_research.py`, `autonomous_financial_intelligence/verified_reasoning/`, `autonomous_financial_intelligence/evidence_verification/` | Research proof support | Turns external research into cited, verified, non-LLM-only evidence; should not directly authorize trades |
| Reverse engineering and creator intelligence | `trading_bot/intelligence/reverse_engineering_engine.py` | Research/intelligence input | Acts as a capability distillation and verification layer: formalizes external claims, builds claim/evidence/mechanism/test graphs, rejects hype/honeypots/dangerous ideas, generates sandbox experiments, and prevents direct live-code modification |
| Risk and validation | `trading_bot/validation/risk_validation_gate.py`, `trading_bot/core/unified_market_hostility_gate.py` | Safety proof | Validates risk limits, hostile market states, drawdown, liquidity, and event conditions |
| Cost and execution feasibility | `trading_bot/core/transaction_cost_model.py`, `decision_governance/cost_expectancy.py`, `decision_governance/execution_engine*.py` | Execution proof | Shows whether expected edge survives spread, slippage, fees, impact, fills, and venue conditions |
| Paper trading and shadow mode | `trading_bot/validation/paper_trading_validator.py`, `research_mvp_pipeline.py` | Outcome proof | Converts proof-approved candidates into paper evidence before any capital eligibility |
| Autonomy governance | `trading_bot/core/autonomy_control_plane.py`, `decision_governance/plane_evolution.py` | System-change governance | Requires proof traces, approvals, backtests, and paper reports for strategy promotion or risk-control changes |
| Audit logging | `trading_bot/audit/`, `decision_governance/audit_logger.py`, `advanced_features/blockchain_trade_verification.py` | Proof trace storage | Stores immutable or tamper-evident records of claim, evidence, proof, decision, and outcome |
| Execution and broker layers | `trading_bot/execution/`, `trading_bot/broker/`, `trading_bot/brokers/` | Downstream only | Must only receive action after DGS, PHCE-D, validation gateway, and paper/live promotion rules pass |
| Agents and orchestrators | `trading_bot/agents*/`, `hivemind/`, `autonomous_superintelligence/`, `radar_ai/` | Claim sources | May generate options, but their outputs must be converted into claim graphs and verified before action |
| Monitoring and metrics | `decision_governance/monitoring.py`, `decision_governance/benchmarking.py`, `metrics/`, `reports/` | Calibration layer | Measures proof sufficiency, adversarial precision, abstention cost, false positives, and calibration error |

## Operational Flow

1. Option generator creates a possible action.
2. Claim graph formalizes the option into claims, assumptions, causal links, predicted outcomes, and invalidation conditions.
3. Evidence auditor attaches and checks evidence.
4. Adversarial analyst attacks the reasoning graph.
5. Verifiers test critical logic with deterministic, statistical, counterfactual, cost, risk, and execution checks.
6. Uncertainty layer estimates confidence and ambiguity.
7. Arbiter refuses, defers, paper-only approves, or escalates.
8. PHCE-D and Unified Decision Gate enforce trade-specific validation.
9. Paper-trade layer records shadow outcomes.
10. COS and DGS memory update beliefs, strategies, failures, and future retrieval.

## Where It Must Be Enforced

### Before Any Trade Candidate

Use:

- `trading_bot/core/phce_d_engine.py`
- `trading_bot/decision_governance/layer1_claim_graph.py`
- `trading_bot/decision_governance/layer2_evidence_auditor.py`
- `trading_bot/decision_governance/layer3_adversarial_analyst.py`
- `trading_bot/decision_governance/layer7_arbiter.py`

Rule:

- no `BUY`, `SELL`, or `PAPER_TRADE_CANDIDATE` without a claim/evidence/proof trace.

### Before Any Paper Promotion

Use:

- `trading_bot/validation/paper_trading_validator.py`
- `trading_bot/core/research_mvp_pipeline.py`
- `trading_bot/decision_governance/memory_system.py`
- `trading_bot/cos/system_cognitive_os.py`

Rule:

- no promotion if proof succeeds only in backtest but fails paper evidence, clustered-trade adjustment, cost stress, or calibration.

### Before Any Live Capital

Use:

- `trading_bot/core/unified_decision_gate.py`
- `trading_bot/validation/risk_validation_gate.py`
- `trading_bot/core/autonomy_control_plane.py`

Rule:

- live capital requires validated paper evidence, risk gate approval, governance approval, and an auditable proof trace.

### Before Any Autonomous Code, Config, Strategy, or Risk Change

Use:

- `trading_bot/core/autonomy_control_plane.py`
- `trading_bot/decision_governance/plane_evolution.py`
- `trading_bot/decision_governance/safety_enforcer.py`

Rule:

- changes to thresholds, risk limits, cost models, strategy templates, execution logic, or validation gates require a proof trace and approval path.

## Required Proof Trace Shape

Every governed decision should be able to emit:

```text
ProofTrace {
  trace_id
  action_candidate
  claims[]
  assumptions[]
  evidence_refs[]
  missing_evidence[]
  contradictions[]
  adversarial_challenges[]
  verifier_results[]
  uncertainty_profile
  refusal_or_approval_reason
  final_decision
  downstream_action
  outcome_ref
}
```

This trace belongs in DGS audit logging and should be referenced by PHCE-D, COS decision memory, paper-trade records, and autonomy-control approvals.

## Refusal Rules

The system must refuse when:

- a critical claim has missing, stale, conflicting, or weak evidence
- the adversarial analyst finds an unresolved severe objection
- deterministic verification fails
- cost-adjusted expectancy turns negative
- execution feasibility fails
- uncertainty or ambiguity exceeds threshold
- the reasoning graph has unsupported causal links
- proof trace cannot be reproduced
- outcome history shows repeated failure under current conditions

Valid refusal outputs:

- `ABSTAIN`
- `DEFER`
- `REJECT`
- `PAPER_ONLY`
- `MANUAL_REVIEW`
- `NO_TRADE`
- `NEEDS_MORE_EVIDENCE`
- `RESEARCH_ONLY`

## Maturity Roadmap

1. Standardize proof trace schema across DGS, PHCE-D, COS, and validation gates.
2. Make PHCE-D emit claim graph inputs for every hypothesis.
3. Make DGS arbiter produce a proof-trace reference for every decision.
4. Require proof-trace references in paper-trade records.
5. Require proof-trace references in autonomy-control strategy promotion.
6. Add replay tests that verify `claim -> evidence -> proof -> action` is reproducible.
7. Add bypass scanner checks so no execution-sensitive path can skip proof governance.

## Brutal Placement Verdict

This system does not belong mainly in the agent layer. Agents can generate options and objections, but the authority must live in deterministic governance, validation, paper-trade evidence, audit logs, and autonomy-control promotion gates.

The best implementation path is to strengthen `trading_bot/decision_governance` as the epistemic authority, then wire PHCE-D, COS, paper trading, unified decision gate, and autonomy control into it with shared proof trace IDs.

Current implementation anchor:

- `trading_bot/decision_governance/epistemic_governance.py` provides the standalone proof-trace authority.
- `trading_bot/core/phce_d_engine.py` now emits proof traces on every PHCE-D decision record.
- `trading_bot/intelligence/reverse_engineering_engine.py` extracts external patterns but keeps them subordinate to proof governance.
