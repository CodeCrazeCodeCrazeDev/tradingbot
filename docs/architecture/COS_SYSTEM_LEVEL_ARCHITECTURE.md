# AlphaAlgo Cognitive Operating System

## Purpose

The COS is not notes and not chat memory. It is a system-level loop that structures knowledge, evaluates ideas, supports decisions, feeds execution systems, and evolves from feedback.

Loop:

1. observe
2. think
3. test
4. learn

The strict implementation lives in `trading_bot/cos/system_cognitive_os.py`.

The COS is memory and learning substrate for the broader claim -> evidence -> proof -> action governance plane documented in `docs/architecture/EPISTEMIC_GOVERNANCE_PLACEMENT_MAP.md`.

## Layers

### 1. Knowledge Graph

Stores typed property-graph knowledge only.

Allowed node types:
- `Concept`
- `Entity`
- `Strategy`
- `Outcome`
- `Assumption`
- `Belief`

Allowed edge types:
- `causes`
- `contradicts`
- `supports`
- `precedes`
- `is_a`
- `used_in`
- `led_to`

Anti-pattern:
- no markdown notes
- no raw text logs
- no untyped memory blobs

### 2. Decision Memory

Stores every decision with context, chosen strategy, expected outcome, actual outcome, and confidence before and after feedback. This is the audit backbone.

### 3. Failure Memory

Stores what failed, under which structured conditions, which assumptions were invalid, and what constraint should block future repeats.

### 4. Strategy Library

Stores reusable, versioned decision recipes with preconditions, action schema, success metrics, playbook steps, provenance, and performance.

### 5. Retrieval Engine

Retrieves knowledge, past decisions, failures, and matching strategies together. It combines graph traversal with lightweight semantic scoring and freshness.

### 6. Integration Layer

Accepts observations, routes plans to action connectors, and receives feedback. Default mode is `shadow`, so no external execution is required or assumed.

### 7. Evolution Layer

Updates belief confidence, strategy performance, failure records, and graph relations from actual outcomes.

## Engineering Stance

This COS is allowed to influence decisions, but it should not bypass PHCE-D, Validation Gateway, paper-trading promotion, or deployment governance.

It is useful only if it makes decisions more auditable, less repetitive in failure, and more calibrated after feedback. If it becomes a pile of stored prose, it has failed its job.
