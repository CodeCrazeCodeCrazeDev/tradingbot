# CSC modular architecture — discovery, interfaces, wiring, self-update

How modules are discovered, wired, and orchestrated in the Cognitive
System Controller — and what "self-updating AI" honestly means in this
repository. Written 2026-11-10; verified against the code.

## The authority chain (invariant — cannot be rewired)

```
CSC (sole decision authority)
  -> risk service (sizing authority)
  -> immutable_shield
  -> governance gate
  -> decision bus
  -> execution service
```

These components are listed in `self_wiring.INVARIANT_IDS` and
`discovery._PROTECTED_PREFIXES`. No discovery scan, advisory vote, or
self-update cycle may attach, replace, or modify them. Deployment and
promotion additionally require signed `OperatorAuthorization`.

## The layers

| Layer | Component | Role |
|---|---|---|
| Interfaces | `core/csc/protocols.py` | Async Protocol contracts (EvidenceStore etc.) — runtime-checked conformity |
| Manifest | `CSC_MANIFEST` literal in a module | Declares `id`, `kind`, `provides`, `requires`, `factory`, `status` |
| Discovery | `core/csc/discovery.py` | AST-scans source for manifests (never imports), builds dep graph, topo-orders wiring, reports blocked/cycles/conflicts |
| Wiring | `advisory.attach_advisory_modules` + `discovery.WiringPlan.execute` | Static manifest attach + dynamic discovered factories; everything lands in the advisory channel |
| Electorate lifecycle | `core/csc/self_wiring.py` | SHADOW → ATTACHED → DORMANT → QUARANTINED by *measured* emits only |
| Promotion pipeline | `controller.py` | propose_model → validate_model (OOS) → operator flag → attach_engineered_model (SHADOW) |
| Self-update seam | `core/csc/self_update.py` | Composes the above into one declared loop — plan reported before execution |
| Research/falsification | `research/`, edge gates, RSI cycle | Where new hypotheses come from and die |

## Manifest contract

```python
CSC_MANIFEST = {
    "id": "my_service",
    "kind": "advisory",          # advisory | infrastructure
    "provides": ["regime"],      # interfaces implemented
    "requires": ["market_data"], # interfaces needed first
    "factory": "pkg.mod:make",   # dotted path to 0-arg factory
    "status": "candidate",
}
```

AST-read only — a `def csc_manifest()` (dynamic) is deferred to the
existing runtime probe (`discover_advisory_callables`), never imported
by the scanner. This keeps `trading_bot/__init__`'s multi-minute import
and the concurrent-edit hazard out of the discovery path.

## What "self-update" means (and cannot mean)

Allowed — the system rewrites *what it consults*:

1. `plan_self_update()` scans manifests → WiringPlan (audited before run)
2. `plan.execute(csc)` wires resolved factories in dep order → SHADOW
3. `self_wiring` promotes to ATTACHED on measured substantive emits
4. Model candidates flow propose→validate→**operator flag**→shadow-attach

Never allowed — the system rewrites *itself*:

- No code self-modification (ProtectedPathGuard hashes the control
  plane; the sandbox eval channel exists for generated code)
- No deployment, sizing, or promotion without signed operator approval
- No authority for discovered modules — advisory evidence only, by
  construction (the electorate votes; the CSC decides)

"Self-improving" = the electorate composition + engineered-model pool
improves under measured evidence. "Self-evolving" = the
evolution_supervisor + RSI cycle mutate *candidate parameters* through
sealed evaluation. Both are real today; both are bounded.

## Wiring it up

```python
from trading_bot.core.csc.discovery import scan_packages
from trading_bot.core.csc.self_update import plan_self_update

plan = plan_self_update()          # scan repo, dep-order, report
report = plan.to_report()          # audit BEFORE wiring
# plan.execute(csc) attaches resolved advisory factories in dep order
```
