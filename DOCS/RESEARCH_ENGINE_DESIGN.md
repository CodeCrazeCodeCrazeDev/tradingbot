# Research Engine — unified design against REDESIGN_DOCS

Maps the live `trading_bot/core/csc/research/` engine onto the EIP /
ECIE / CSE-CEDA / RESEARCH_OS_V2 specs. Each spec service names the
existing code that carries it, or marks the gap.

## Pipeline

```
fetchers.py + fetchers_extra.py   (14 keyless source adapters)
        |
        v
evidence_quality.py  (EQE — weighted claim scoring, cross-source
        |            corroboration, provenance labels)
        v
sources.py extract_claims  (declared vs heuristic, polarity, hedged)
        |
        v
engine.py ingest_literature  -> KG nodes @ EvidenceTier.THEORETICAL
        |                      + unvalidated_assumption entries
        v
engine.py research_question  (hypothesis -> adversarial debate ->
        |                       falsification experiment -> KG)
        v
policy_lifecycle.py  (champion-challenger deploy gate + rollback)
harness_rl.py        (HPO harness evolution, GRPO ranking)
```

## Spec-to-code map

| Spec service (ECIE/EIP) | Existing code | Status |
|---|---|---|
| Scout adapters | `research/fetchers*.py` (14 sources) | wired |
| Evidence Quality Engine | `research/evidence_quality.py` | **this doc's build** |
| Claim extraction | `sources.py:extract_claims` | wired |
| Security/AST scanner | RSI `ProtectedPathGuard` + sandbox | wired (code path) |
| Disposable sandbox | `SandboxManager` subprocess backend | wired |
| Governance gate | canonical governance + `OperatorAuthorization` | wired |
| Rollout/Rollback | `PolicyLifecycle` deploy + auto-rollback | wired |
| Champion-challenger (CEDA) | lifecycle candidate-vs-incumbent OPE gate | wired |
| Invariant-gated evolution (IGE) | RSI invariants + protected-path hashing | wired |
| Introspection (IFT) | RLSF self-report fields (`rlsf`, `hpo`, `policy_lifecycle` in payloads) | wired |
| Skill compiler / registry | `UniversalCapabilityRegistry` + advisory adapter seam | partial |
| Weakness inversion | not built | gap |
| Creator/frontier adapters | need API keys | gap |

## Authority boundary

Research output is THEORETICAL evidence only. Promotion to any
decision authority requires the gated deploy path (OPE-improved
candidate, CVaR/DD floors, operator signature for live).
