# Algory (algory.app) — Deep Technical Investigation

**Date:** 2026-11-13
**Scope:** evolutionary algorithms, architecture, strategy generation, validation
methodology, profitability evidence, security, and lessons for this repo's RSI
subsystem (`trading_bot/recursive_self_improvement/`).
**Method:** public sources only — algory.app pages, guide pages, release notes,
legal/privacy text, UK Companies House. The engine is closed-source; anything
marked *(inferred)* is deduction from observable behavior, not confirmed fact.

---

## 1. Executive summary

Algory is a Windows desktop "strategy factory" by **VagaFX Ltd** (UK company
14261308, inc. 28 Jul 2022; sole director Tomas Edgar Rees, b. Jul 1995 — a
 forex educator behind the Vaga Academy). It breeds thousands of rule-based
trading strategy variants with a genetic algorithm on the user's own CPU,
backtests them on M1-OHLC data with broker-realistic costs, subjects survivors
to a five-part out-of-sample gauntlet, verifies the compiled MetaTrader 5 EA
trade-by-trade against MT5's own Strategy Tester ("parity", graded A–F), and
exports survivors as MT5 expert advisors. Post-deploy it runs a daily
decay/health check and a 25%→50%→100% "incubation" risk ladder driven by live
trade evidence.

The genuinely notable part is **not** the GA (operators unpublished) but the
**validation pipeline**: held-out slice, beat-a-field-of-100-random-strategies,
1,000× trade-order shuffle for drawdown fragility, parameter-nudge robustness,
per-broker cost model, and venue parity gating what may breed. That gate stack
is better than most retail tooling and maps cleanly onto gaps in our RSI
evaluator. The profitability evidence, however, is **self-reported and
unverified** — no audited track record exists, and the headline vault numbers
on the homepage are animated demo figures the site itself declares "randomly
generated."

Our RSI stack is already statistically *stricter* than Algory's (signed
evidence, embargoed splits, block bootstrap + multiplicity correction, DSR,
CSCV/PBO, anti-gaming battery). What we should take from Algory is the parts we
lack: **venue-parity grading, a random-field benchmark gate, trade-order/path
fragility checks, perturbation robustness, graduated risk-ramp promotion, and
a scheduled decay-reassessment loop.**

---

## 2. Company and product

| Fact | Detail |
|---|---|
| Legal entity | VagaFX Ltd, England & Wales, company no. 14261308, inc. 28 Jul 2022, SIC 62012 (software development). Registered office on Companies House is a London virtual office (East Ham); site lists 71-75 Shelton St, Covent Garden. |
| Founder | Tomas Edgar Rees (Director + Secretary, appointed 28 Jul 2022, b. Jul 1995, British). Public face: @vagafx on Threads/Instagram (~89K followers), Vaga Academy forex-education business (~6K Discord, Trustpilot 4.5/5 on 71 reviews per third-party profile). |
| Product | "Algory Engine" — closed-source Windows desktop app (`Algory.exe`), first public archive capture May 2026; release train v1.3 (Jun 2026) → v1.4 "Boadicea" UI (Jul 2026) → v1.5.3.1.7 (25 Oct 2026). Codename "CRIMSON PROTOCOL". |
| Business model | Freemium: Free ($0, Eco/Medium power, 3 markets H1/H2, built-in history) / $97 mo / $197 qtr / $487 yr. Second device +$29/mo etc. Whitelabel and partner programs (50% revenue share, Stripe billing). infra: DigitalOcean, Stripe, Brevo, Discord. |
| Positioning | "Strategy factory, not auto-trader": breeds/tests strategies, user deploys resulting EAs to MT5. Explicit, repeated disclaimers that it never places trades itself. |

Not to be confused with the unrelated 2017 Polish "Algory Project" crypto ICO —
different company, different product.

---

## 3. Architecture

Observed/inferred from docs, patch notes, and legal text:

- **Local-first desktop engine.** Breeding is CPU-bound and runs on the user's
  machine; "Power" modes Eco→Extreme map to core counts, with free-RAM-aware
  scheduling (campaigns degrade gracefully under memory pressure). Signed
  binaries; auto-update every few hours, deferred while jobs run.
- **Two dashboards.** "Legacy" dashboard plus **Boadicea** (v1.4+): a
  GPU-accelerated "neural map" visualization of the vault and live evolution
  field, with FX quality modes (FULL/LITE/OFF) for weak GPUs. Visualization is
  real engine telemetry, not mock — but the homepage hero figures are declared
  randomly generated.
- **Data plane.** Market data comes from the user's MT5 terminal (broker
  history, "downloads your broker's full available price history before a
  campaign") or a built-in history (Dukascopy-sourced) when no broker is
  connected. Strategies bred on built-in history must be **REFRESH**ed on the
  broker's own data before deploy — a data-provenance gate.
- **MT5 is the execution boundary.** Algory never sees broker credentials;
  MT5 holds the login. Algory reads account metadata through MT5 (e.g., infers
  per-lot commission from the account's closed trades), compiles each strategy
  into an MT5 Expert Advisor dropped into the Experts folder, and a companion
  "Chart Manager" EA on a chart records live trades for health checks and the
  incubation ladder.
- **Parity harness.** Parity tests replay the strategy inside the MT5 Strategy
  Tester (Single mode, **1-minute OHLC** modelling — matching Algory's own fill
  resolution, which is M1 sub-bars, not ticks). Algory can spawn a dedicated
  test MT5 instance so parity never disturbs the trading terminal; deploys/
  restarts are scheduled at "quiet minutes" away from bar opens and news.
- **Licensing/sync.** Licence key + hardware fingerprint enforced per device;
  optional second-device sync replicates portfolios, strategy files,
  incubation/decay records, deploy ledger, and live trade log through their
  server (DigitalOcean). Automation steps (CAMPAIGN, PORTFOLIO, REASSESS,
  PARITY, deploy/replace) can run on a schedule or non-stop, chained, with
  cross-device STOP propagation.

---

## 4. The evolutionary algorithm (what is public)

The engine internals are proprietary; this is the documented shape:

- **Campaign** = one breeding run scoped to chosen markets × timeframes. The
  "Proving Grounds" screens ~3,000 starting candidates (reduced from 4,000 in
  v1.5.3 for speed) split across **four execution modes** (~750 each).
- **Two tribes** — *Consistency* and *Growth* — each breed ~20 generations,
  then a **"Final War"** merges the pools. Fitness drives selection; weak lines
  die, strong lines breed on. *(Island-model GA with two niches; selection,
  crossover, and mutation operators are not published.)*
- **Smart Mode** (paid): half the starting pool is seeded with "genes that won
  before on that market" (elite archive per market), the other half stays
  random **as an explicit control** — built-in explore/exploit ablation.
- **Parity-gated breeding**: only genes/strategies that passed MT5 parity
  validation may enter the breeding pool.
- **Genome** = a structured vector across gene categories shown in the UI:
  **signals, bias, filters, execution, management**. Named signal genes carry
  ICT-flavoured labels (v1.5.3 renamed them: OTE/FIB, BOS/STRUCTURE,
  REJECTION BLOCK, DISPLACEMENT, EQUILIBRIUM; plus fair value gaps, momentum
  breaks, Donchian mid, etc.). Management genes include ATR trailing,
  partial TP, breakeven/stop-to-entry, time-of-day/session closes, Friday
  close, range-day filter. **8 archetypes** cluster the vault (trend follower,
  mean reverter, breakout, etc.). Campaign guardrails (news filter, daily DD
  limit, Friday close, symbol lock, max aggregate risk) are **baked into the
  genome at breeding time**, not applied post-hoc.
- **Composite score 0–100**, eight weighted parts: persistence 20, recovery 15,
  Sharpe 15, trade count 15, held-out linearity 12, max drawdown 10, profit
  factor 10, IS linearity 3. "Persistence" = fraction of in-sample edge
  surviving per trade out-of-sample; <55 = WEAK, ≥55 = GOOD.

---

## 5. Validation methodology — the core of the product

### 5.1 Backtester

- Fill resolution: **M1 OHLC sub-bars**, no tick simulation (deliberate —
  matches MT5's 1-min-OHLC tester mode so parity is meaningful).
- Costs stamped at training time, per asset class: spread measured **per hour
  from real tick bid/ask** (not a daily average; rollover-spread widening
  handled), broker commission inferred from the account's own closed trades,
  swaps with triple-night on the broker's rollover day, contract sizes and
  volume grids per instrument, broker daily-break minutes excluded, DST
  handling for New York-close brokers, Friday-close semantics mirrored in the
  backtest, limit orders fill only when price actually reaches them.
- Split: breed on first **70%** of history; last **30%** is held out and never
  touched by breeding. Equity curves mark the boundary.

### 5.2 Promotion gates ("four gates" per marketing; five checks documented)

1. **Composite score** (above) with persistence weighted highest.
2. **Held-out slice** performance on the untouched 30%.
3. **Beat random**: must beat most of a field of **100 random strategies** on
   the held-out slice; the bar rises when the slice is thin.
4. **Trade-order shuffle**: trade sequence shuffled 1,000×, drawdown
   re-measured; orderings with bad drawdown >40% reject the candidate —
   path-dependence/fragility check.
5. **Parameter nudges**: perturb parameters; ≥50% of nudges must stay
   profitable, and <15 held-out trades is an automatic refusal.

### 5.3 Venue parity (the differentiator)

- Every vaulted strategy gets a **passport**: equity curve with held-out region
  marked, trade stats, exact genes, score, grade — "nothing deploys as a black
  box."
- **Parity test**: replay the compiled EA inside the user's own MT5 Strategy
  Tester on the broker's data, same symbol/timeframe/start date, 1-min OHLC;
  trade-by-trade match vs the simulation graded **A (≥85%) / B (70–84) /
  C (55–69) / D (40–54) / F (<40)**. "The same gene can grade A on gold and F
  on an index" — parity is per market, not global. Parity-passed genes are the
  only ones allowed to breed.

### 5.4 Portfolio level

- **Diversity grade** = worst of ~5 axes (correlation, exposure, health,
  concentration, size; guides mention seven axes), with pairwise return
  correlations computed from actual equity curves — not label variety.
- **TRUE SIM**: account-level simulation of the whole portfolio applying
  symbol lock, max aggregate risk, and pending orders the way live bots do.
- **Account heat** guidance: total open risk if every trade stops at once;
  <3.5% for prop accounts, ≤10% personal; symbol lock (one trade per symbol)
  on by default, max aggregate risk default 5%.

### 5.5 Post-deploy lifecycle

- **Daily health check**: re-simulates each live bot's strategy on market data
  since training, reconciles simulated vs live trades (via Chart Manager),
  verdicts HOLDING / DECAYED / TOO EARLY / NO VERDICT with retry backoff
  (1d → 3d → weekly).
- **Incubation ladder**: deploy starts at **25%** of target risk → **50%**
  (PROVING) → **100%** (FULL). Climb on ~10 healthy live trades to 50%, ~30
  profitable trades to full; time-based fallback (~2 clean weeks / ~6 weeks);
  "hot start" for statistically remarkable opening runs. Risk changes apply to
  new trades only; verdicts REPLACE/WATCH/EARLY/OK drive auto-replace
  automation.
- **Reassess/Refresh**: re-score strategies on new data since training
  (HOLDING/DECAYED/TOO EARLY); strategies bred on built-in history get
  NEEDS REFRESH until re-validated on broker data.

---

## 6. Profitability evidence — honest assessment

**What exists:**

- Marketing vault stats (3,975 bred, vault avg score 74.2, avg return +14.8%,
  avg DD 3.1%, best +38.2%) — but the site footer states figures in animated
  app scenes are **randomly generated**. Treat as illustrative, not evidence.
- A community "challenge passes / payouts" wall (FTMO, FundingPips, etc.)
  spanning 2022–2026. Entries are tagged "Before Algory" (the user's prior
  trading history) vs post-Algory; self-reported screenshots, unverified, and
  subject to selection bias (people post wins).
- The free tier lets users verify the pipeline themselves; Discord community
  exists for support.

**What does not exist:**

- No audited track record, no Myfxbook/FX Blue-style verified live statements,
  no published vault-wide *live* performance. Algory collects live trade
  results via telemetry (see §7) — they have the data to publish real stats
  but do not (yet).
- No disclosed detail on GA operators, fitness internals, or the 8 archetype
  definitions.

**Structural caveats even if methodology is sound:**

- GA on a backtest score is still selection over ~3,000 candidates/campaign;
  the gates mitigate but no formal multiplicity correction (DSR/PBO/CSCV) is
  disclosed. Single 70/30 chronological split = one partition.
- M1-OHLC is better than bar-close but still an approximation: intra-minute
  stop-vs-target ordering ambiguity remains, and parity measures agreement
  with MT5's *tester* (itself a model), not real fills.
- Vault shows survivors only — classic selection bias in what the user sees.
- Young single-founder company, closed source, bus factor ~1.

**Verdict:** the *process* is unusually rigorous for retail; the *claims* are
unproven. Their own disclaimers are honest about this.

---

## 7. Security and privacy

**Positives:**

- Signed binaries (installer + apps carry verified signatures); components
  signed after a Windows-security block issue.
- Credential boundary is clean: Algory never handles broker logins/passwords —
  MT5 terminal owns them; Algory reads market/account metadata locally.
- Local compute for the expensive part (breeding); licence checks are the main
  phone-home, plus optional 2-device sync.
- Privacy policy (UK GDPR) is unusually thorough and honest: enumerates every
  upload, names processors (DigitalOcean, Stripe, Brevo, Meta, Discord,
  Google, ipapi.co), states retention, provides objection path.
- Telemetry minimization claims: uploads "never contain your trading account
  number or login, balance or equity, profit or costs in money, lot sizes,
  order comments, licence key, machine identifiers or email."

**Concerns:**

- **Live trade results upload is ON by default with no in-app switch**
  (objection requires emailing support with install id). It includes per-trade
  entry/exit prices/times, exit reason, broker server name — fine-grained
  trading telemetry tied to a persistent install id + IP.
- Vault summaries + hourly MT5 setup report are default-on (one toggle covers
  both).
- Two-device sync stores full strategy files + live trade logs on their
  server — user's strategy IP lives in their cloud.
- Licence server = revocation/kill-switch surface; hardware fingerprinting.
- Closed-source engine **and** compiled EAs: "inspect every expert advisor"
  notwithstanding, .ex5 binaries are not meaningfully auditable; ToS bans
  reverse engineering. An EA runs with full account privileges — a malicious
  or compromised update path is the highest-impact risk (though auto-updates
  are deferred during jobs and signed).
- ToS caps liability at 12 months' fees and excludes trading losses; updates
  "may change how backtests, scores and parity grades are calculated" —
  scoring is a moving target.

---

## 8. What our AI should learn from it

Mapped to `trading_bot/recursive_self_improvement/` and the wider runtime.
Our stack is already stronger on *statistical evidence* (Ed25519-signed
contract+verifier reports, embargoed chronological splits, holdout
attestation, block bootstrap with trial-count-corrected alpha, Holm, deflated
Sharpe, CSCV/PBO, anti-gaming battery, hash-chained archive + ledger). The
gaps Algory exposes are in **venue fidelity, gate diversity, lifecycle, and
promotion staging** — not in math we already do better.

### Adopt (concrete, ranked by leverage)

1. **Venue-parity grade as a first-class passport metric.** Algory's best idea:
   grade how well the *simulator* matches the *execution venue*, per market,
   A–F, and gate breeding on it. Our analog: replay candidate parameter sets
   through the same fill/cost path the paper runner and MT5 adapter use and
   grade divergence (we already have `scripts/mt5_demo_runner.py`,
   measured-cost frictions, and documented MT5 venue quirks in AGENTS.md).
   "Same gene grades A on gold, F on index" ⇒ evaluate parity **per
   instrument**, matching our existing per-instrument no-regression rule in
   `evaluation.py` (`instrument_delta` check).

2. **Beat-a-random-field gate.** Require candidates to beat a field of ~100
   random parameter draws on the held-out slice, with the bar rising on thin
   slices. Cheap to add alongside the paired baseline comparison; directly
   counters "candidate beats incumbent by luck of the draw" and complements
   our block-bootstrap bound.

3. **Trade-order/path fragility check.** Shuffle trade order 1,000× and
   re-measure drawdown; reject if >40% of orderings breach a DD threshold.
   Our bootstrap preserves return dependence but ignores *path*
   dependence — drawdown is path-dependent, so this is a genuinely different
   failure mode worth a `robustness_metrics` entry.

4. **Parameter-perturbation robustness gate.** ≥50% of local nudges must stay
   profitable; refuse when held-out trade count <15. Adjacent to our bounded
   `allowed_parameters` scope but as an explicit *stability* test — a
   candidate sitting on a fitness spike should fail. Fits naturally into
   `EvaluationEvidence.robustness_metrics`.

5. **Graduated promotion ("incubation" analog).** Our
   `PromotionDecision` → `OperatorAuthorization` → staged config is binary at
   each stage. Algory's 25→50→100% ladder says: let *accrued live/paper
   evidence* raise authority gradually. Concretely: after
   `eligible_for_operator_review`, require a paper-runner soak window whose
   simulated-vs-expected trade stats feed the next stage gate before full
   parameters go live — "size follows proof." `engine_v2.py` already has a
   `STAGES`/`AUTH_REQUIRED` ladder to hang this on.

6. **Scheduled decay reassessment ("REASSESS" analog).** Algory re-simulates
   each deployed strategy on post-training data daily and flags
   HOLDING/DECAYED. Our archive/rollback exists but promotion is one-shot.
   A periodic job that re-scores *deployed* parameters on data since their
   evaluation window — writing verdicts to the evidence ledger — would close
   the strategy lifecycle (deploy → monitor → rotate) we currently lack.
   `paper_runner` + the evaluation harness already produce the inputs.

7. **Elite-seeding with a random control arm ("Smart Mode").** Half the
   proposal pool seeded from per-market/regime archive winners, half random —
   and *measure which arm produces eligible candidates*. Our
   `select_diverse_hypotheses` spends budget across distinct parameters; adding
   an archive-conditioned seed fraction **with a logged control arm** turns
   seeding into an experiment rather than an assumption.

8. **Niching/tribes → island models.** Two fitness niches (Consistency /
   Growth) merged after 20 generations is a simple island-model GA. We have
   `ParetoArchive` + `multi_objective.py`; per-regime or per-family islands
   with periodic migration would diversify `HypothesisEngine` output beyond
   the current single ranking.

9. **"Parity-passed genes may breed" → gate the proposal prior.** Restrict
   hypothesis generation to parameter regions/families with prior
   `eligible_for_operator_review` evidence (or explicitly explore outside it
   as a control). Our archive already stores this; wiring it into
   `ExperimentPrioritizer` as a prior — with exploration budget preserved —
   mirrors their rule without losing novelty.

10. **Cost-model fidelity details worth stealing for `synthetic_market` /
    paper fills:** per-hour spread from tick-level bid/ask rather than a daily
    scalar; commission inferred from the venue's own fills; session-break and
    DST/rollover handling; limit-order fill only at reachable price;
    Friday/weekend-hold semantics explicit. These are exactly the
    "measured-cost frictions" our paper path already aspires to — Algory's
    changelog is a checklist of edge cases that bite in production.

### Architectural patterns worth noting (secondary)

- **Venue as credential boundary**: keep broker auth inside MT5, never in the
  app — matches our "localhost/paper-only" posture and MT5 demo runner design.
- **Companion telemetry EA** ("Chart Manager"): a minimal on-chart agent
  recording live fills is how they get ground truth for health checks — an
  analog for us would be reading `account_state`/decision-bus records rather
  than trusting backtest re-runs alone.
- **Dedicated test instance**: parity on a separate MT5 so validation never
  disturbs the trading terminal; our fault-gate/synthetic separation is the
  same instinct.
- **Quiet-minute scheduling**: never restart/redeploy near bar opens or news —
  directly applicable to any future live-runner automation here.
- **Per-bot magic numbers + orphan-trade detection + deploy ledger**:
  idempotent, auditable deployment bookkeeping — parallels our execution
  idempotency fault gate.

### Do NOT copy / be wary of

- **The composite score.** Opacity is the problem: weights (20/15/15/15/12/10/
  10/3) are arbitrary and unauditable. Copy the *gate structure* (held-out,
  random-field, shuffle, nudge), not a single blended number — our
  contract-declared thresholds are more honest.
- **Single 70/30 split.** We already do embargoed multi-window splits +
  holdout attestation + CSCV/PBO. Keep ours.
- **Telemetry defaults.** Their always-on live-trade upload with no in-app
  opt-out is a cautionary example; our evidence ledger is local and
  hash-chained — keep it that way and prefer explicit consent for any future
  outcome-sharing.
- **Marketing ≠ evidence.** Prop-pass walls and vault averages are
  self-reported; the site's own disclaimer says demo figures are random.
  Their live-trade telemetry means they *could* publish verified stats —
  absence of that is itself informative.
- **Closed-source trust.** Signed binaries + licence server + compiled EAs is
  a trust model we deliberately avoid (our operator-signed authorization +
  protected-path guard is stricter and inspectable).

---

## 9. Sources

- https://algory.app/ (homepage: tribes, gates, score weights, parity grades,
  incubation, guardrails, pricing, disclaimer that demo figures are random)
- https://algory.app/g/algory-how-to-use.html (+ .pdf) — operating procedure
- https://algory.app/g/algory-parity-test.html — M1-OHLC parity setup
- https://algory.app/g/algory-portfolio-risk.html — heat, diversity, TRUE SIM
- https://algory.app/g/more-strategies.html — portfolio/diversification guide
- https://algory.app/g/algory-incubation.html — 25/50/100 ladder, Pilot/Chart
  Manager, health verdicts
- https://algory.app/g/algory-mt5-basics.html, algory-mac-android.html
- https://algory.app/g/new-ui.html — Boadicea UI, gene categories, archetypes
- https://algory.app/g/patch-notes-latest.html — v1.5.3.1.7 (25 Oct 2026):
  gene names, Proving Grounds 3000/4 modes, REASSESS, sync, cost-model fixes
- https://algory.app/guides.html, partners.html, whitelabel.html
- https://algory.app/?legal=1 — Terms, Privacy Policy (uploads, sync, GDPR),
  Refund Policy
- UK Companies House, company 14261308 (VAGAFX LTD; officer Tomas Edgar Rees)
- https://www.threads.com/@vagafx — founder statements
- Wayback Machine: earliest algory.app capture 10 May 2026

*Internal references: `improvement_genome.py`, `rsi_loop.py`, `evaluation.py`,
`anti_gaming.py`, `multiplicity.py`, `scorecard.py`, `engine_v2.py`,
`sleep_cycle.py`; AGENTS.md RSI rules and MT5 venue quirks.*
