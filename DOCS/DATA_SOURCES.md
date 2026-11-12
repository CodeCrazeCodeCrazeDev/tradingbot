# Data sources for edge research

Status map for the external data sources evaluated for AlphaAlgo.
Three statuses: **wired** (script + table, verified working),
**keyless-planned** (free/public, connector feasible), and
**licensed** (paid/permissioned — listed so nobody re-researches
whether they're free).

## Wired (verified 2026-11-09)

| Source | Data | Where | Notes |
|---|---|---|---|
| Dukascopy `.bi5` tick feed | Bid/ask ticks, hour files | `scripts/collect_fx_ticks.py` → `var/orderflow/fx_ticks.db` | Pre-existing; real bid/ask from one LP aggregator, not a consolidated FX book |
| Dukascopy → candles | Mid OHLC + measured spread per bar | `scripts/dsc_candles.py` → `dsc_data.db` (`market_data` schema + `dsc_spread`) | Second FX venue for `edge_gate` cross-venue checks; spread = real cost model. Pace ≥1s/request or the feed 429s |
| MT5 broker history | OHLCV bars (65k+ per tf) | `scripts/mt5_data_sync.py` → `market_data.db` | Requires running terminal; `market_data.db` now holds 66k EURUSD M15 / 30k H4 (2007→) — AGENTS.md's "1,000 bars" note is stale. 1,000 off-grid splice rows remain; `edge_features.py` drops them automatically |
| FRED (`fredgraph.csv`) | DGS2, DGS10, SOFR, DEXUSEU, DEXUSUK, DEXJPUS daily | `scripts/collect_macro.py --sources fred` → `macro_data.db.macro_series` | Keyless, no API key needed for the CSV endpoint. Caveat: Akamai drops custom User-Agents and python-TLS reads — collector falls back to Git-for-Windows curl with default UA |
| ECB SDW | EUR ref FX (USD/GBP/JPY per EUR) + euro AAA 10y | `scripts/collect_macro.py --sources ecb` → `macro_series` | Keyless `format=csvdata`. Independent second daily FX fix for cross-checking |
| CFTC COT | TFF managed-money positioning (6 FX) + disaggregated gold | `scripts/collect_macro.py --sources cot` → `cot_positions` | Annual zips, keyless. Positions Tuesday, published Friday → `published_at` = +3d, joined point-in-time. `XRATE`/cross contracts excluded (they're not the pair's own positioning) |
| Economic calendar | Weekly scheduled events w/ impact | `scripts/collect_macro.py --sources calendar` → `news_events` | faireconomy mirror of a retail calendar (not BLS/BEA primary). ET→UTC with explicit DST rules. **Forward-looking only** — history accrues by re-running weekly; nothing is backfilled |
| FOMC calendar | Real published meeting + minutes dates, 2021–2027 | `scripts/collect_macro.py --sources official` → `news_events` | Parsed from federalreserve.gov `fomccalendars.htm`; statement 14:00 ET on last meeting day, minutes on the recorded release date. ~96 real events covering the backtest window |
| NFP rule seed | Employment Situation dates, first-Friday 08:30 ET | `scripts/collect_macro.py --sources official` → `news_events` | `source=rule_seed:nfp_1st_friday` — the documented standing schedule rule, NOT scraped actuals; rare holiday shifts may be off one week. Honest for ±30min blackout testing |
| ICS release calendars | Agency schedules (BLS, ECB GC) | `scripts/collect_macro.py --sources ics` → `news_events` | Generic VEVENT parser (TZID/UTC/date-only). bls.ics exists but bot-blocks this client — reports `not a calendar response`, never faked. Works from any environment where the host serves the file |
| ALFRED vintage discovery | REAL historical release dates for NFP, CPI, PPI, GDP | `scripts/collect_macro.py --sources releases` → `news_events` | `alfredgraph.csv?vintage_date=D` is keyless: binary-searches the first vintage where each obs appears (= release date) plus value revisions (GDP 2nd/3rd estimates). ~5-15 requests/release, opt-in. Verified: NFP dates land on first Fridays, GDP yields all 3 estimates |
| Hyperliquid / Kraken / Binance candles | Crypto OHLCV, 3 venues | `scripts/data_scout.py` → `hl/kraken/binance_data.db` | Pre-existing |
| Binance USDⓈ-M + Hyperliquid funding | Settled funding prints (8h BN / 1h HL) + mark/index premiumIndex snapshots | `scripts/collect_funding.py` → `funding_data.db` (`funding_rates`, `premium_snapshots`) | Keyless. Fulfils the `scout_claims` data request (var/data_requests.json). Idempotent on (source,symbol,funding_time); failures reported, never faked. Verified 2026-11-12: 270 BN + 1,500 HL prints over 30d |

## Evaluation layer

| Script | What it answers |
|---|---|
| `scripts/edge_baseline.py` | 8 fixed rules, bootstrap LCB on one eval window |
| `scripts/edge_gate.py` | Same rules across walk-forward segments AND ≥2 venues — now satisfiable for FX via `dsc_data.db` |
| `scripts/edge_leadlag.py` | Cross-asset lead-lag (crypto) |
| `scripts/edge_features.py` | Feature-conditioned hypotheses the price-only gate can't express: news-blackout A/B delta on all baseline rules, London session-sweep fade (real measured spread as cost), COT crowded-positioning fade, US–EU rate-differential trend. Point-in-time joins on `published_at` |
| `scripts/funding_carry_eval.py` | Funding-signed fade on `funding_data.db` × spot closes — first non-price-data consumer. Decomposes funding income vs drift; unhedged, spot-as-perp-proxy caveat stamped. Binance 8h PASSes were drift-dominated; Hyperliquid 1h FAILed segment-consistency |

## Keyless-planned (not yet wired)

| Source | Why it's still out |
|---|---|
| Treasury daily par-yield CSV | Endpoint is flaky/blocked from this host; DGS2/DGS10 via FRED covers the same data |
| ALFRED vintages | **Wired** — see "ALFRED vintage discovery" above (`vintage_date` param on the graph CSV, no key needed) |
| OANDA order/position book | Snapshot only, no public history — would need prospective collection |
| EIA Open Data | Needs free API key |
| GDELT | Feasible keyless; no hypothesis proposed yet that needs it |
| Binance public archive (trades/aggTrades) | `data.binance.vision` zips — deeper microstructure than klines |

## Licensed / permissioned (do not assume free)

CME DataMine, Databento, Nasdaq TotalView, NYSE TAQ/Pillar Depth, OPRA,
CRSP, CLSMarketData, WMR FX Benchmarks, CME CVOL history, DTCC DDR full
feed, Trading Economics calendar API (paid), Bloomberg/LSEG/RavenPack,
Kenneth French library is free for benchmarking factor exposure (CSV,
keyless — worth wiring if equity factors are ever tested), AQR datasets,
Deribit (keyless public API for crypto options — feasible if needed).

## Honest caveats carried from the source review

- Spot FX is OTC: the MT5 feed, Dukascopy feed, and ECB fix measure
  different parts of the same market — disagreement between venues is
  itself information, not an error.
- COT is weekly with a Tuesday→Friday lag; it's a slow feature, never
  an intraday trigger.
- The calendar mirror is third-party and forward-looking; primary BLS/
  BEA schedules are the correct source but block non-browser clients,
  and Wayback archives are IP-throttled here. Historical coverage
  currently rests on FOMC (real dates) + NFP (rule-derived); CPI/PPI/
  GDP release times still have no keyless historical feed — measured
  blackout deltas exclude them.
- Measured result (EURUSD M15 eval 2025-09→2026-10): 199 high-impact
  events (FOMC + ALFRED-discovered NFP/CPI/PPI/GDP + NFP seed), 250
  bars removed at ±30min, LCB deltas ±0.03bps across the six fast
  baseline rules — the scheduled-release filter neither helps nor
  hurts these rules. Honest, not a null artifact.
- ALFRED-discovery caveat: `vintage_date` marks when ALFRED recorded
  the publication — can lag the actual print by ~1 day on weekend
  releases (PAYEMS 2025-08-02 Saturday = the Friday Aug 1 report).
  For ±30min blackouts the day is right ~always; for surprise-vs-
  actual work the time field (08:30 ET) is the standing rule, not
  measured.
- Mid-price candles are not executable prices; `dsc_spread` supplies
  the measured cost half of that gap.
