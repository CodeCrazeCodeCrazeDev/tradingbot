---
name: edge-reverse-engineering
description: Reconstruct a claimed trading edge (paper, repo, rumor, P&L claim) into a testable signal spec and falsify it on real data at real costs
---

# Strategy / Edge Reverse-Engineering

Given a claimed edge — an arXiv paper, a GitHub strategy, a screenshot P&L, a
"what if X leads Y" rumor — decompose it into its minimal testable mechanism and
falsify it honestly on this repo's real data.

## Workflow

1. **Extract the mechanism, not the narrative.** What is the claimed primitive?
   (cross-venue lag, funding carry, depth imbalance, premium convergence, ...).
   Write it as: *signal definition, horizon, direction, required data*. If the
   claim is vague, formalize the strongest charitable version.
2. **Map to data we actually have.** Check `var/data_catalog.json` /
   `var/l2data` first. If the mechanism needs data we lack (L3 order flow,
   options chains, real queue fills), say so — do not approximate silently.
3. **Implement the replay in `scripts/edge_research.py`** as an `--only` path
   (H5–H8 are the pattern). Reuse `_um_file`/`_get` caching; stream large
   archives, keep bounded resamples under `var/l2data`.
4. **Evaluate correctly — the three mandatory checks:**
   - **Per-day/per-regime splits**, never pooled alone. Overlapping windows
     inside episodes fake statistical significance (3 episodes of 300
     correlated points ≠ 300 independent samples). This fooled us 3× already.
   - **Real costs**: taker fees + spread + slippage; maker path needs an
     explicit fill model (see maker-reverse engineering below). Use measured
     bookTicker spreads where available, not assumed.
   - **Selection accounting**: if the edge implies execution (limits, expiry),
     count expired orders' subsequent move — missed-fills are part of the
     economics (`paper_maker_fx` proved expired buys were not "saves").
5. **Ledger the verdict** into `var/methods/ledger.jsonl` via
   `scripts/research_ledger.py`. FAIL is a fine result — it is the working
   output of the pipeline. A structural anomaly that survives everything but
   costs (premium basis: 93/93 days, sub-cost at standard tiers) gets
   `FAIL` + a caveat documenting the fee regime where it would flip.

## Hard rules

- Never promote a gross-of-cost positive to a trading rule.
- Never weaken gates to force a PASS; abstention under real costs is correct.
- No live/broker execution. Paper replay only.
- Maker-side tests: entries passive LIMIT, exits MARKET, TTL expiry,
  maker fee ≠ taker fee (closes must pay taker — see maker_fee caveat in
  `trading_bot/brokers/maker_paper_adapter.py`).
- HF-gated or credentialed data stays GATED — never fabricate tokens.
