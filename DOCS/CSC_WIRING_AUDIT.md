# CSC Wiring Audit — full inventory

Audit method: AST import-graph reachability from the canonical spine
(`main.py`, `unified_bot.py`, `foundation/`, plus everything reachable
through them) × `DEFAULT_ADVISORY_FACTORIES` (118 ids) ×
`UNWIRED_ORPHAN_MODULES` (240 entries) × AST scan for obs-callable
methods (`analyze|detect|classify|predict|assess|estimate|evaluate|scan|
identify|score|forecast|screen|generate_signal`) whose signatures take
market data (`df|data|market_data|bars|ohlcv|candles|ctx|...`).

Result: 225 dirs, 175 root files. Every root `.py` is already classified
(0 unmanifested). 100 dirs are unreachable from the canonical path and
neither wired nor manifested. Of those, **~15 contain genuinely
wireable analyzers**; the rest are external-data-dependent, authority
surfaces, infra/UI, or stubs.

---

## A. Should wire — real obs-callable analyzers

All self-contained (numpy/pandas only), parameterless constructors,
methods accept df/market_data/candles/observation — feedable from the
observation ctx + `_BarHistory` like the existing bucket-D/E adapters.

| File :: class | Surfaces | Why wire |
|---|---|---|
| `upgrades/core_upgrades_001_025.py` :: `VolatilityRegimeDetector`, `TradeClassifier`, `OrderBlockDetector`, `FairValueGapDetector`, `MarketStructureAnalyzer`, `PriceActionPatternDetector`, `LiquidityAnalyzer` | `detect(returns)`, `classify(price)`, `detect(candles)`, `analyze(highs,lows)`, `analyze(o,h,l,c)`, `analyze(bids,asks)` | Six real technical analyzers — pure numpy/dataclass code, candle-based |
| `upgrades/core_upgrades_026_050.py` :: `LiquiditySweepDetector`, `DivergenceDetector` | `detect(candles)` | Same pattern — real candle detectors |
| `institutional_entry/entry_signal_generator.py` :: `EntrySignalGenerator` | `generate_signals` | 743-line institutional entry logic, df-based |
| `institutional_entry/institutional_footprint.py` :: `InstitutionalFootprint`, `AbsorptionDetector` | `analyze_footprint(df, timeframe)`, `detect_absorption(df)`, `detect_institutional_sweep(df, levels)` | Order-flow evidence on real bars |
| `institutional_entry/wyckoff_ict_fusion.py` :: `WyckoffICTFusion` | `analyze_market_structure(df)` | 1237-line Wyckoff/ICT fusion — genuine analyzer |
| `analysis_unified/unified_analyzer.py` :: `UnifiedAnalyzer` | `analyze(symbol, market_data, analysis_types)` | Directly obs-callable composite analyzer |
| `advanced_analysis/hypernetwork_adaptation.py` :: `HypernetworkAdapter` | `detect_regime`, `predict` | Regime detection on accumulated state |
| `advanced_analysis/multi_agent_rl.py` :: `TradingAgent`, `MacroStrategist`, `TacticalExecutioner` | `analyze(ctx)` | Multi-agent analysis, obs-shaped input |
| `realtime/realtime_ml.py` :: `EnsembleModel` (+ Momentum/MeanReversion/Trend/Volatility) | `predict(features)` | Online ML models — features derivable from enriched obs (rsi/vol/trend) |
| `research/features/engine.py` :: `FeatureDiscoveryEngine` | `score_features` | sklearn-based feature scoring (needs sklearn → hermes or dep-skip) |
| `research/orchestration/quant_pipeline.py` :: `RegimeAndMicrostructureAnalyzer` | `classify_regime(df)` | df-based regime classification |
| `skills/ai_ml_enhancements/concept_drift.py` :: `ConceptDriftDetector` | `detect` | Drift evidence — feeds selection plane honestly |
| `skills/ai_ml_enhancements/counterfactual_analyzer.py` :: `CounterfactualAnalyzer` | `analyze` | Counterfactual evidence on decision quality |
| `profit_maximizer/market_regime_adapter.py` :: `MarketRegimeAdapter` | `analyze_regime(df)` | df-based regime adapter |
| `profit_maximizer/profit_maximizer_core.py` :: `SignalConfluenceScorer`, `SessionFilter` | `score_signal`, `assess_session` | Signal-quality scoring + session evidence |
| `ultimate_system/alpha_discovery_engine.py` :: `AlphaDiscoveryEngine` | `get_signals` | Alpha discovery — evidence output |
| `ultimate_system/deep_agent_system.py` :: `DeepAgentSystem` + agents | `analyze_market`, `analyze` | Multi-agent market analysis |
| `psychology/behavioral_features.py` :: `CognitiveBiasDetector`, `TiltDetector` | `detect_*`, `assess_tilt` | Behavioral evidence on the system's own trading pattern — inputs derivable from CSC trade history |
| `position/position_management.py` :: `CorrelationExposureMonitor`, `PositionAgingTracker` | `analyze(positions)` | Portfolio-state evidence — positions available from `csc._open_positions` |
| `hft/tick_data_handler.py` :: `OrderBookImbalanceDetector` | `analyze(order_book)` | Wireable only when LOB data present — the obs carries `microstructure` from `market_feeds.LOBFeed` |

## B. Cannot wire honestly — inputs not in the observation

| Dir | Reason |
|---|---|
| `arbitrage` | `detect_opportunities` needs cross-exchange prices — no second venue in ctx |
| `internet_access`, `sentiment`, `alternative_data`, `macro`, `multimodal` | External feeds (news/social/ESG/alt-data) absent from obs ctx — wiring would fabricate inputs |
| `wealth` | `FreeESGScorer.score_asset` needs ESG data |
| `research_ingestion` | `score_paper`/`score_repo`/`analyze_repo` operate on papers/repos, not market obs |
| `surveillance` | `detect(account_id, symbol)` needs the order tape, not bar data — evidence exists but lives in the execution ledger, not the observation seam |
| `quantum` | `QuantumMachineLearning.predict(X)` needs a trained model + feature matrix — no honest obs mapping |
| `market_student` | `evaluate_behavior` needs behavior metrics not present in ctx |

## C. Must NOT wire — authority/parallel-capital surfaces

| Dir | Reason |
|---|---|
| `approval`, `unified_approval`, `ultimate_approval` | Approval = veto authority — never advisory |
| `portfolio`, `position` (management methods), `profit_maximizer` (execution parts) | Sizing/allocation authority — risk service owns this |
| `reality_gates`, `stealth_safety`, `safety`, `risk_management`, `risk_unified`, `hedging` | Parallel gate/safety stacks — superseded by immutable_shield + CanonicalRiskService; a second veto path violates single-authority |
| `trading`, `production` (orchestration), `deployment`, `autonomous_pipeline`, `system_supervisor`, `ultimate_bot`, `ultimate_architecture`, `unified_system` (orchestrator layers), `institutional`, `realtime` (engine parts), `crypto`, `ctrader`, `derivatives`, `bridges`, `broker`, `connectors`, `market_making`, `hedge_fund` (execution parts), `arbitrage` (executor) | Parallel bots/executors — wiring gives a second decision path |
| `recursive_improvement`, `eternal_evolution`, `auto_optimizer`, `optimization`, `critical_fixes`, `upgrades` (non-analyzer parts) | Deprecated RSI duplicates per AGENTS.md — no improvement authority (analyzer classes in `upgrades/` are still evidence-wireable, see A) |
| `security`, `compliance`, `surveillance` (screening parts) | Compliance authority is a boundary, not evidence |

## D. Not wireable — infra / UI / stubs / empty

`api`, `core_api` (interfaces only — `I*`, no impl), `audit`, `automation`,
`blockchain`, `cloud_deployer`, `connectivity_unified`, `data_feeds`,
`data_sources`, `deployment`, `devops`, `diagnostics`, `distributed`,
`documentation`, `error_handling`, `event_monitoring`, `event_pipeline`,
`exits`, `filters`, `features` (helpers, no analyzers), `global_expansion`,
`infrastructure`, `ingestion`, `integration`, `integrations` (`Mock*`
classes), `log_system`, `mobile`, `mobile_app`, `notifications`,
`observability`, `ops`, `profiling`, `quality`, `reporting`,
`risk_unified` (stub), `simulation`, `backtesting` (offline harnesses,
need history not obs), `social`, `streaming`, `system`,
`trading_calendar`, `validation`, `verification` (dir shim — canonical
swarm is `core/verification`), `visualization` (`AnomalyDetector` needs
plotly — dep absent in .venv; wireable under hermes if wanted),
`voice_assistant`, `wealth`, `testing`, `tools`, `trade_journal`,
`unified_approval` (listed above), `upgrades` (non-analyzer parts).

## E. Borderline — wireable but flagged

- `skills/` — 109 files; beyond the two candidates above, most are ML
  tooling (embeddings, federated, RL gym) needing trained models — treat
  remaining files as conditional: wire only ones that accept raw obs
  fields.
- `production/profitable_strategies.py` — `generate_signals` is
  obs-callable and real, but the file imports `tick_level_backtester`
  (a top-level module); wire only if that import resolves.
- `hedge_fund/multi_strategy.py` — `generate_signals(market_data)` is
  wireable evidence; the rest of `hedge_fund/` is capital-path.
- `unified_system/layers/layer4_intelligence.py` /
  `layer5_signal.py` — real `predict`/`detect_regime`/`generate_signals`
  impls, but the package is a parallel orchestrator; extracting the
  layer impls as advisors is safe, the orchestrator is not.
- `psychology` — listed in A, but inputs (trade history, pnl) come from
  the ledger not the raw bar — adapter must pull from `csc._open_positions`
  or pending-prediction history rather than ctx fields.

## Recommendation

Wire bucket A (~20 analyzers across ~15 files) through
`AdvisoryModuleAdapter` + `_BarHistory`, same idiom as bucket D/E.
Manifest everything in B/C/D with concrete reasons so the audit map
stays total. The contract tests then enforce every new adapter emits
`{capability_id, direction, confidence, evidence, advisory_only}` with
authority fields stripped.

---

## Bucket F — wiring result (implemented)

14 new advisory services attached via `DEFAULT_ADVISORY_FACTORIES`
(`trading_bot/core/csc/advisory.py`, "Bucket F" block). All probe-tested
with 80 synthetic EURUSD observations; evidence emits
`{capability_id, direction, confidence, evidence, advisory_only}` with
authority fields stripped. `.venv` probe: 11/14 green, 0 field leaks.

| Adapter id | Source :: surfaces | Input mapping |
|---|---|---|
| `upgrades_price_structure` | `OrderBlockDetector.detect`, `FairValueGapDetector.detect`, `MarketStructureAnalyzer.analyze`, `PriceActionPatternDetector.analyze`, `LiquiditySweepDetector.detect` | `_BarHistory` bars → candle dicts + derived swing levels |
| `upgrades_regime_divergence` | `VolatilityRegimeDetector.detect`, `TradeClassifier.classify`, `DivergenceDetector.detect` | real returns + computed RSI series as the indicator |
| `institutional_entry_footprint` | `AbsorptionDetector.detect_absorption`, `InstitutionalFootprint.analyze_footprint`/`detect_institutional_sweep`, `WyckoffICTFusion.analyze_market_structure` | bar DataFrame; module timeframe labels mapped onto the single feed; swing levels derived from bars |
| `analysis_unified_analyzer` | `UnifiedAnalyzer.analyze` | symbol + obs fields + OHLCV frame |
| `hypernetwork_regime` | `HypernetworkAdapter.detect_regime` | real prices/volatility (`predict()` dropped — expects a fixed-width model input the obs can't honestly supply) |
| `marl_strategists` | `MacroStrategist.analyze`, `TacticalExecutioner.analyze` | obs numeric fields + price window; per-agent error isolation |
| `realtime_ensemble` | `EnsembleModel.predict` over Momentum/MeanReversion/Trend/Volatility online models | `_numeric_fields` → `FeatureVector` |
| `feature_discovery` | `FeatureDiscoveryEngine.generate_features` + `score_features` | bar window → `StandardizedDataset`; target = realized next-bar return (needs `sklearn` — attaches under hermes, skips in `.venv`) |
| `quant_regime_microstructure` | `RegimeAndMicrostructureAnalyzer.classify_regime` + `calculate_order_book_imbalance` | bar frame; OBI only when bid/ask sizes present (needs `sklearn` — hermes) |
| `concept_drift` | `ConceptDriftDetector.detect` | accumulated prices + volumes |
| `profit_max_market_regime` | `MarketRegimeAdapter.analyze_regime` | bar frame; sizing/stop adjustment fields stripped by the extended `AUTHORITY_FIELDS` |
| `confluence_session` | `SignalConfluenceScorer.score_signal`, `SessionFilter.assess_session` | obs trend label + bar frame / numeric fields |
| `deep_agent_market` | `DeepAgentSystem.analyze_market` (async) | obs + price window; needs `aiohttp` — skips in `.venv`, attaches under hermes |
| `hft_orderbook_imbalance` | `OrderBookImbalanceDetector.analyze`, `LiquidityAnalyzer.analyze` | conditional — emits `no_order_book_in_observation` unless `order_book`/`bids`/`asks` present |

### Candidates dropped after deeper inspection

- `EntrySignalGenerator` — needs upstream `EntryTrigger` objects the
  observation channel never produces; wiring would fabricate triggers.
- `AlphaDiscoveryEngine.get_signals` — emits `np.random.uniform` noise
  (stub); wiring it would fabricate evidence.
- `CounterfactualAnalyzer` — needs realized action/outcome pairs; route
  through HMS failure memory instead of the obs seam.
- `CognitiveBiasDetector`/`TiltDetector` (psychology) — need realized
  trade history/PnL, which is CSC-internal, not in the obs contract.
- `CorrelationExposureMonitor`/`PositionAgingTracker` (position) — need
  position state; same boundary.
- `MultiStrategyEngine` (hedge_fund) — empty strategy registry by
  default; would emit vacuous evidence.
- `IntelligenceLayerImpl`/`SignalLayerImpl` (unified_system) — literal
  stubs returning constants/empty lists.
- `production/profitable_strategies` — Signal objects carry
  entry/stop/sizing; authority-adjacent lane.

All of the above plus the partial-package remainders are manifested in
`UNWIRED_ORPHAN_MODULES` with concrete reasons — the audit map is total.

### Verification

- `tests/foundation/test_orphan_ai_quarantine.py` + `test_ai_stack.py`:
  248 passed, 17 skipped (`.venv`)
- Per-adapter probe: 11/14 construct and emit clean evidence in
  `.venv`; `feature_discovery`, `quant_regime_microstructure` (sklearn)
  and `deep_agent_market` (aiohttp) skip at factory time by design and
  attach under hermes.
- `AUTHORITY_FIELDS` extended in `cognition/advisory_adapter.py` with
  sizing/trade-parameter vocabulary (`position_size`, `size_adj`,
  `stop_loss`, `take_profit`, `entry_price`, `risk_per_trade`,
  `leverage`, ...) so regime-adapter outputs can't smuggle sizing.
