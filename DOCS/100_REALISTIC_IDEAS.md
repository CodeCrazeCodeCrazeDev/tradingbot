# 100 realistic ideas for AlphaAlgo

Every item maps to machinery that already exists in this repo. Each is
a bounded increment, gated the same way as everything else — measured
evidence, sealed evaluation, operator approval for promotion. None
assumes edge exists; most exist to *find out honestly* whether it does.

## Edge discovery & evaluation (1-15)

1. Invert `rate_diff_trend` — measured −32bps mean is a live candidate as
   a long-EUR-on-widening rule; flip sign and re-gate via `edge_gate`.
2. Run `edge_gate` on `dsc_data.db` EURUSD M15 once the candle sync
   completes — first real cross-venue FX verdict.
3. Add `usd_strength` hypothesis: DEXUSEU trend vs EURUSD M15 momentum
   interaction.
4. Add `cot_crowding_follow` (opposite of cot_fade) — crowd-following in
   trending regimes; test both, keep whichever survives.
5. Weekly-COT-freshness rule: fade positioning only in the first 3 days
   after publication (information decays).
6. Session sweep on NY (13:00-17:00 UTC) mirroring london_sweep.
7. Sweep variants: Asian-range sweep, prior-day-high/low sweep, sweep of
   the previous session's extreme.
8. Add realized-spread stress test: rerun london_sweep at p90 spread, not
   mean — does it die under realistic fills?
9. `--impacts High,Medium` sweep on blackout A/B to see if medium events
   dilute or help.
10. Test blackout pad 15/60/120min — is ±30 the right width?
11. Post-event drift hypothesis: M15 trend continuation in the 2h AFTER
    a high-impact release settles (the "second leg").
12. Event-surprise proxy: |move| in the release bar vs its trailing
    median — do big surprises predict follow-through or fade?
13. GBPUSD/USDJPY copies of every EURUSD hypothesis — cross-pair
    replication is the cheapest falsification there is.
14. `er_trend` only during London+NY overlap (12:00-16:00 UTC) — same
    rule, different regime filter.
15. rv16-quantile-gated variant of lowvol_trend — vol forecast already
    verified; use q95 to veto, not just size.

## Data & ingestion (16-30)

16. Resume the paced Dukascopy sync to 90+ days M15 — deeper eval window
    and more dsc_spread coverage.
17. `--sources releases` for UNRATE, RSAFS (retail sales), PCEPI —
    three more real release dates for the blackout set.
18. ICSA (initial claims) — weekly Thursday releases via the same
    ALFRED vintage discovery.
19. ECB rate decisions: same vintage trick is impossible (no ECB on
    FRED) — use `rule_seed` for the published GC schedule (~6/yr).
20. CFTC COT for silver, crude oil, Nasdaq — disaggregated markets are
    all in the same zip already; extend `COT_DISAGG_MARKETS`.
21. GDELT events feed — keyless; test whether FX-relevant event volume
    predicts next-day vol.
22. Binance aggTrades archive (`data.binance.vision`) — real trade flow
    for crypto hypotheses beyond candles.
23. Weekly accrual job for `faireconomy` calendar — history grows
    forward from now; schedule it Sunday nights.
24. FRED free API key → ALFRED direct vintage-date API (removes the
    binary-search request cost).
25. Stooq via a browser-driven fetch (JS PoW) — deep free FX/metals
    daily history if ever needed.
26. Persist Dukascopy raw ticks selectively (--keep-ticks for event
    windows only) — orderflow studies without the disk cost.
27. `dsc_spread` regime analysis: when does the real spread widen — is
    it a better blackout signal than the calendar?
28. Cross-venue divergence detector: MT5 vs Dukascopy price gap as a
    feed-quality metric.
29. market_data.db integrity: dedupe + re-gap check after the UTC fix
    (pre-utc-backup exists).
30. Off-grid splice audit for GBPUSD/USDJPY M15 (EURUSD already clean-
    verified).

## Hypothesis & strategy families (31-45)

31. `edge_hypotheses` placeholders — implement the timestamp/volume
    channels they document (hyp_time_of_day_momentum, weekend_effect).
32. Mean-reversion conditioned on RV-quantile: fade extremes only when
    q80 forecast is calm.
33. Donchian channel on D1 (H4 rollup) — slower breakout, cheaper cost
    ratio.
34. Carry-tilt hypothesis: long high-yield differential direction
    (DGS10−eu_aaa_10y sign) as a bias, not an entry.
35. Term-structure hypothesis: DGS10−DGS2 slope regime vs trend-following
    rules' performance.
36. Friday close / Monday open gap rule for FX — weekend risk premium.
37. Month-end rebalancing window (WMR-fix-style): last-2-days-of-month
    M15 drift hypothesis.
38. Vol-scaled variant of every baseline rule (the machinery exists in
    hyp_vol_scaled_momentum).
39. Time-in-market test: are all negative-LCB results concentrated in
    one session? A session mask is a legitimate declared filter.
40. Multi-horizon check: same rules at horizon 1/4/16 — does the sign
    flip (mean-rev vs trend) consistently?
41. Interaction test: momentum × blackout — is momentum specifically
    better OUTSIDE release windows (fewer whipsaws)?
42. Cot-fade on XAUUSD once gold bars are provisioned (disagg data is
    already collected).
43. Cross-asset FX lead-lag: GBPUSD leads EURUSD? edge_leadlag port
    from crypto to FX pairs.
44. Range-fade conditioned on EU session only — the quietest regime.
45. `pullback_long` with the er_trend gate instead of SMA50 — cleaner
    trend discriminator already proven as a feature.

## Architecture & discovery (46-60)

46. Convert existing advisory services to `CSC_MANIFEST` literals —
    they enter the dep-graph without code changes.
47. `provides`/`requires` naming convention doc so manifests share one
    interface vocabulary.
48. `discovery.plan.execute` smoke harness in tests — dry-run against a
    stub csc (no heavy import).
49. `dynamic` manifest probe: import-time sandbox for csc_manifest()
    modules that declare deps at runtime.
50. `conflict` resolution policy: prefer `status=verified` over
    candidate on duplicate ids.
51. Cycle-breaker suggestion: when a dep cycle is found, report the
    minimal edge to drop (feedback-arc).
52. `self_update.run` audit log to the evidence ledger — every wiring
    decision recorded with the plan hash.
53. Advisor-level provenance: stamp which manifest version a SHADOW
    node came from so a new file version re-probes.
54. Blocklist manifest key for discovered modules (opt-out without
    deletion).
55. Manifest `min_csc_version` — discovered modules declare the
    interface version they expect.
56. `kind="infrastructure"` path: wire to configure_* seams only —
    keep the second kind from becoming an authority side-door.
57. WiringPlan diff report between runs — what changed since last scan.
58. Manifest lint in CI: fail on unknown keys, missing id, id in
    INVARIANT_IDS.
59. Orphan-module sweeps: `UNWIRED_ORPHAN_MODULES` shrinks as manifests
    are written.
60. `plan.execute` budget guard: max N new SHADOW attachments per
    cycle (mirrors MAX_SHADOW).

## Self-improvement & governance (61-75)

61. `self_update` cycle report to snapshot.json — operator sees intent
    + outcome without log-diving.
62. Electorate entropy metric — diversity of attached advisors as a
    health signal (degenerate-electorate early warning).
63. Self_wiring telemetry: promotion/demotion rate per week — too many
    flips = unstable measurement.
64. SHADOW starvation alert: a shadow node that never graduates within
    its window should page attention, not sit.
65. Re-probe cooldown jitter — avoid dormant nodes re-failing in sync.
66. Electorate capacity test: does adding a genuinely noisy advisor
    measurably degrade branch ranking? (safety regression test).
67. `run_self_update` dry-run mode — plan only, no execute, for the
    dashboard.
68. Quarterly manifest-review audit: stale factories, dead provides.
69. Approval-channel UX: pending shadow candidates listed in
    snapshot.json for one-file operator sign-off.
70. Rollback drill: attach a known-bad candidate in a test env, verify
    the quarantine path end-to-end (it exists — exercise it).
71. Electorate vote-abstention report: advisors that never vote are
    measurement overhead, prune candidates.
72. Duplicate-signal detection: two advisors emitting correlated calls
    should count as one vote (collinearity guard).
73. `self_wiring` policy version in reports — threshold changes are
    themselves auditable events.
74. Advisor sandbox timeout: discovered callables get a wall-clock
    budget before they stall the consult loop.
75. Advisor input contract check: discovered emit signature must match
    the electorate protocol before SHADOW entry.

## Edge-to-production pipeline (76-88)

76. Qualified-candidate → hypothesis → sealed-eval handoff: automate the
    edge_gate pass into the proposal queue.
77. Walk-forward segment count sweep on edge_gate — is 3 enough, or do
    candidates need 5?
78. `--min-venues 3` once Binance/Dukascopy/MT5 all carry a pair.
79. Paper-fill reconciliation: feed paper fills back into the cost model
    (measured, not flat 5bps).
80. `--cost-bps` sensitivity table per candidate — edge that only lives
    under 2bps is not real edge.
81. `edge_features` report → falsification ledger entries (rejections
    recorded, not just JSON).
82. Multiplicity budget: track hypotheses-tested-per-quarter; adjust
    required margin by Benjamini-Hochberg.
83. `--embargo` sensitivity: 20 vs 100 bars — do candidate verdicts hold
    under wider purges?
84. Discovery-window honesty check: rules must never see eval-window
    data; add a leakage assertion to edge_features.
85. Bootstrap block-length robustness: LCB at blocks 4/8/16 — verdicts
    that depend on block size are suspect.
86. Candidate decay rule: a qualified candidate that stops working in
    new data gets auto-flagged for re-review (not auto-killed).
87. `edge_gate` cross-venue p-value: same rule, independent feeds —
    correlated-venue caveat reported.
88. Score-paper-run → edge_baseline bridge: convert live paper results
    into the same net-bps units.

## Operations & reliability (89-100)

89. Scheduled `collect_macro` job — weekly refresh keeps calendar/COT
    current without re-discovery cost.
90. `dsc_data.db` freshness monitor: alert if the venue feed goes
    stale mid-run.
91. `news_events` coverage dashboard: which currencies/impacts are
    populated vs sparse.
92. `collect_macro` failure-mode: per-source retry budget so one dead
    host can't stall the others (already bounded; monitor).
93. manifest `status` audit — verified modules that stop being loadable
    flag themselves.
94. `edge_features` runtime budget: the O(window) rules need
    vectorization or a documented --rules split for CI use.
95. Pre-merge integrity check: git status + file-hash of advisory.py
    before long agent sessions (the truncation hazard is documented).
96. macro_data.db backup cadence — the ALFRED discovery cost is
    one-time; don't re-pay it on a corrupted db.
97. `var/` artifact rotation — reports are append-heavy; compact old
    jsonl files.
98. `self_update` simulation mode in tests — full plan→execute→report
    on a stub csc (fast CI).
99. `DOCS/DATA_SOURCES.md` freshness check — wired sources verified
    monthly (endpoints drift; bls.ics already proved that).
100. Operator-readable weekly digest: edges tested, verdicts, advisors
    promoted/demoted, calendar accrual — one page, no jargon.

## Honest scope statement

Ideas 1-60 are implementable now with existing machinery and testable
data. 61-100 are instrumentation on the same systems. What is *not*
on this list: unverifiable capability claims, autonomous self-modifying
code, unlicensed data sources, and any promotion path that skips the
operator gate — those are architectural invariants, not ideas.
