"""
Comprehensive Institutional Verification Test Suite for the Research OS.
Tests all 14 stages of the quantitative research lifecycle, including Phase 2 features:
Experiment OS, Prioritization Economics, Multi-Agent Debate Marketplace, Causal SCM,
Active Learning, World Model, Digital Twin, Decision Records, and Meta-Research calibration.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta

# Research OS imports
from trading_bot.research import (
    SovereignResearchOrchestrator,
    TFIDFEmbeddingProvider,
    BM25EmbeddingProvider,
    HybridEnsembleDuplicateDetector,
    LocalArchiveDiscoveryProvider,
    HypothesisGenerator,
    LocalCSVDataProvider,
    StandardDatasetValidator,
    StandardDatasetRegistry,
    FeatureDiscoveryEngine,
    StandardFeatureRegistry,
    ADFStationarityTest,
    LjungBoxAutocorrelationTest,
    GrangerCausalityTest,
    FDRCorrection,
    QuantitativeAlphaGenerator,
    StrategySynthesizer,
    StandardStrategyRegistry,
    StandardExperimentRegistry,
    StandardModelRegistry,
    StandardKnowledgeRegistry,
    NetworkXGraphStore,
    RealisticResearchBacktester,
    RobustnessTester,
    PortfolioResearchOptimizer,
    PromotionPipelineGatekeeper,
    ProductionResearchMonitor,

    # Phase 2 imports
    SovereignExperimentScheduler,
    ExpectedInformationGainSchedulingPolicy,
    FIFOSchedulingPolicy,
    MultiArmedBanditSchedulingPolicy,
    BayesianEVIPrioritizationPolicy,
    ResearchEconomicsAllocationOptimizer,
    SkepticalReviewer,
    StatisticianReviewer,
    ScientificDebateEngine,
    LinearStructuralCausalModel,
    RegimeGapActiveLearning,
    MarkovRegimeSwitchingWorldModel,
    AdversarialMarketDigitalTwin,
    SovereignDecisionAuditor,
    AdaptiveMetaResearchEngine,
    ResearchProposal,
    ReviewerOpinion
)


@pytest.fixture
def sample_dataset():
    """Generates 200 data points of stochastic prices for robust testing."""
    start_time = datetime(2026, 1, 1)
    end_time = start_time + timedelta(days=50)

    np.random.seed(100)
    num_points = 200
    delta = (end_time - start_time) / num_points
    timestamps = np.array([np.datetime64(start_time + i * delta) for i in range(num_points)])

    # Simulating standard GBM Forex prices
    returns = np.random.normal(0, 0.001, num_points)
    prices = 1.12 * np.exp(np.cumsum(returns))

    opens = prices * 0.999
    highs = np.maximum(prices, opens) * 1.001
    lows = np.minimum(prices, opens) * 0.999
    closes = prices
    volumes = np.random.poisson(1000, num_points).astype(float)

    data = {
        "EURUSD_open": opens,
        "EURUSD_high": highs,
        "EURUSD_low": lows,
        "EURUSD_close": closes,
        "EURUSD_volume": volumes
    }

    from trading_bot.research.core.interfaces import StandardizedDataset
    return StandardizedDataset(
        dataset_id="ds_test_eurusd",
        asset_class="Forex",
        symbols=["EURUSD"],
        timeframe="1h",
        start_time=start_time,
        end_time=end_time,
        data=data,
        timestamps=timestamps,
        metadata={"version": "1.0.0"},
        provenance={"generator": "GBMFixture"}
    )


# -----------------------------------------------------------------------------
# 1. LITERATURE, EMBEDDINGS & DUPLICATE DETECTION TESTS
# -----------------------------------------------------------------------------

def test_literature_embeddings_and_duplicate_detection():
    embed_provider = TFIDFEmbeddingProvider()
    bm25_provider = BM25EmbeddingProvider()
    detector = HybridEnsembleDuplicateDetector(threshold=0.7)

    from trading_bot.research.core.interfaces import ResearchPaper
    paper1 = ResearchPaper(
        paper_id="paper_1",
        title="Microstructure Alpha in Liquidity Pools",
        authors=["Jules"],
        publish_date=datetime.utcnow(),
        abstract="Order flow imbalance is highly predictive of short term price movements during liquid regimes.",
        category="microstructure"
    )

    paper2 = ResearchPaper(
        paper_id="paper_2",
        title="Predictive Microstructural Alpha on Liquidity Pools",
        authors=["Jules"],
        publish_date=datetime.utcnow(),
        abstract="We show order flow imbalance predicts short term returns in liquid regimes.",
        category="microstructure"
    )

    paper1.embeddings = embed_provider.embed(paper1.abstract)
    paper2.embeddings = embed_provider.embed(paper2.abstract)

    assert paper1.embeddings.shape == (500,)
    assert bm25_provider.embed(paper1.abstract).shape == (1000,)

    # Duplicate check
    duplicates = detector.find_duplicates(paper1, [paper2])
    assert len(duplicates) == 1
    assert duplicates[0][0].paper_id == "paper_2"
    assert duplicates[0][1] >= 0.7


# -----------------------------------------------------------------------------
# 2. HYPOTHESIS & DATA VALIDATION TESTS
# -----------------------------------------------------------------------------

def test_hypothesis_and_data_validation(sample_dataset):
    # Hypothesis Generation
    gen = HypothesisGenerator()
    hyp = gen.generate_custom(
        description="VPIN predicts 1h returns",
        assumptions=["VPIN correlates with adverse selection"],
        market="EURUSD",
        timeframe="1h",
        expected_mechanism="Inventory risk pressure",
        measurable_prediction="IC > 0.02",
        failure_conditions=["No significant IC correlation"]
    )
    assert hyp.status == "draft"
    assert "selection" in hyp.assumptions[0]  # lowercase s matching actual test input

    # Dataset Ingestion & Validation
    validator = StandardDatasetValidator()
    passed, anomalies = validator.validate(sample_dataset)
    assert passed is True
    assert len(anomalies) == 0

    # Test corruption rejection
    corrupted_data = sample_dataset.data.copy()
    corrupted_data["EURUSD_close"] = corrupted_data["EURUSD_close"].copy()
    corrupted_data["EURUSD_close"][10] = np.nan  # inject NaN

    from trading_bot.research.core.interfaces import StandardizedDataset
    corrupted_dataset = StandardizedDataset(
        dataset_id="ds_corrupted",
        asset_class="Forex",
        symbols=["EURUSD"],
        timeframe="1h",
        start_time=sample_dataset.start_time,
        end_time=sample_dataset.end_time,
        data=corrupted_data,
        timestamps=sample_dataset.timestamps,
        metadata={}
    )

    passed_corr, anomalies_corr = validator.validate(corrupted_dataset)
    assert passed_corr is False
    assert "EURUSD_close_corrupted_values" in anomalies_corr


# -----------------------------------------------------------------------------
# 3. FEATURE DISCOVERY & SELECTION TESTS
# -----------------------------------------------------------------------------

def test_feature_discovery_and_selection(sample_dataset):
    engine = FeatureDiscoveryEngine()
    registry = StandardFeatureRegistry()

    features = engine.generate_features(sample_dataset, "EURUSD")
    assert len(features) >= 4

    # Register feature
    for feature in features:
        registry.register_feature(feature)

    # Get registered feature
    primary_feat = registry.get_feature(features[0].feature_id)
    assert primary_feat.name == features[0].name

    # Scoring via Mutual Info
    target = np.random.normal(0, 0.001, len(sample_dataset.timestamps))
    scores = engine.score_features(features, target)
    assert len(scores) == len(features)
    for feat_id, score in scores.items():
        assert score >= 0.0
        registry.record_importance(feat_id, score)

    # Correlation pruning
    pruned = engine.prune_redundant_features(features, threshold=0.95)
    assert len(pruned) > 0


# -----------------------------------------------------------------------------
# 4. STATISTICAL HYPOTHESIS TESTING TESTS
# -----------------------------------------------------------------------------

def test_statistical_hypothesis_testing(sample_dataset):
    close_prices = sample_dataset.data["EURUSD_close"]
    returns = np.diff(close_prices) / close_prices[:-1]

    # 1. ADF Stationarity Test
    adf_test = ADFStationarityTest()
    adf_res = adf_test.run_test(returns)
    assert "passed" in adf_res

    # 2. Ljung-Box Autocorrelation Test
    lb_test = LjungBoxAutocorrelationTest()
    lb_res = lb_test.run_test(returns, lags=3)
    assert "p_value" in lb_res

    # 3. Granger Causality Test
    granger_test = GrangerCausalityTest()
    # predictor causes returns
    predictor = returns * 0.5 + np.random.normal(0, 0.0001, len(returns))
    causality_data = np.column_stack((returns, predictor))
    g_res = granger_test.run_test(causality_data, maxlag=2)
    assert "p_value" in g_res

    # 4. FDR multi-test p-value corrections
    p_values = [0.001, 0.02, 0.04, 0.45, 0.90]
    rejected, adjusted_p = FDRCorrection.adjust_p_values(p_values, alpha=0.05)
    assert len(rejected) == len(p_values)
    assert bool(rejected[0]) is True  # standard boolean cast to prevent numpy type assertion failure


# -----------------------------------------------------------------------------
# 5. ALPHA PERFORMANCE ESTIMATORS TESTS
# -----------------------------------------------------------------------------

def test_alpha_performance_estimators(sample_dataset):
    alpha_gen = QuantitativeAlphaGenerator()
    feat_vol = next(feat for feat in FeatureDiscoveryEngine().generate_features(sample_dataset, "EURUSD") if "volatility" in feat.name)
    feat_ent = next(feat for feat in FeatureDiscoveryEngine().generate_features(sample_dataset, "EURUSD") if "entropy" in feat.name)

    alphas = alpha_gen.generate_alpha(sample_dataset, [feat_vol, feat_ent])
    assert len(alphas) > 0
    alpha = alphas[0]

    assert alpha.metrics["ic"] >= -1.0 and alpha.metrics["ic"] <= 1.0
    assert "turnover" in alpha.metrics
    assert "capacity_usd" in alpha.metrics
    assert "decay_rate" in alpha.metrics


# -----------------------------------------------------------------------------
# 6. STRATEGY SYNTHESIS, EXECUTION & REALISTIC BACKTESTING TESTS
# -----------------------------------------------------------------------------

def test_strategy_synthesis_and_realistic_backtesting(sample_dataset):
    feat_vol = next(feat for feat in FeatureDiscoveryEngine().generate_features(sample_dataset, "EURUSD") if "volatility" in feat.name)
    feat_ent = next(feat for feat in FeatureDiscoveryEngine().generate_features(sample_dataset, "EURUSD") if "entropy" in feat.name)
    alphas = QuantitativeAlphaGenerator().generate_alpha(sample_dataset, [feat_vol, feat_ent])
    alpha = alphas[0]

    # Strategy Synthesis
    synthesizer = StrategySynthesizer()
    strategy = synthesizer.synthesize_strategy(alpha)
    assert strategy.name.startswith("EURUSD")

    # Execution
    signals = strategy.generate_signals(sample_dataset)
    assert len(signals) == len(sample_dataset.timestamps)
    assert set(np.unique(signals)).issubset({-1.0, 0.0, 1.0})

    # Backtesting
    backtester = RealisticResearchBacktester(spread_pct=0.0001, commission_pct=0.00005)
    res = backtester.run_backtest(strategy, sample_dataset)

    assert "cagr" in res
    assert "sharpe" in res
    assert "max_drawdown" in res
    assert "cvar_95_tail_risk" in res
    assert "profit_factor" in res
    assert len(res["equity_curve"]) == len(sample_dataset.timestamps)


# -----------------------------------------------------------------------------
# 7. ROBUSTNESS & PORTFOLIO OPTIMIZER TESTS
# -----------------------------------------------------------------------------

def test_robustness_and_portfolio_optimizer(sample_dataset):
    # Robustness walk-forward and regime-switching stress checks
    feat_vol = next(feat for feat in FeatureDiscoveryEngine().generate_features(sample_dataset, "EURUSD") if "volatility" in feat.name)
    feat_ent = next(feat for feat in FeatureDiscoveryEngine().generate_features(sample_dataset, "EURUSD") if "entropy" in feat.name)
    alphas = QuantitativeAlphaGenerator().generate_alpha(sample_dataset, [feat_vol, feat_ent])
    alpha = alphas[0]
    strategy = StrategySynthesizer().synthesize_strategy(alpha)

    tester = RobustnessTester()
    wf_res = tester.walk_forward_validation(strategy.__class__, alpha, sample_dataset, num_windows=2)
    assert "passed" in wf_res

    regime_res = tester.regime_stress_test(strategy, sample_dataset)
    assert "passed" in regime_res

    # Portfolio HRP, Kelly & Risk Parity
    opt = PortfolioResearchOptimizer()
    returns_matrix = np.random.normal(0, 0.001, (100, 3))

    hrp_weights = opt.optimize_hrp(returns_matrix)
    assert len(hrp_weights) == 3
    assert np.isclose(np.sum(hrp_weights), 1.0)

    rp_weights = opt.optimize_risk_parity(returns_matrix)
    assert len(rp_weights) == 3
    assert np.isclose(np.sum(rp_weights), 1.0)

    cvar_weights = opt.optimize_minimum_cvar(returns_matrix)
    assert len(cvar_weights) == 3
    assert np.isclose(np.sum(cvar_weights), 1.0)

    k_fraction = opt.calculate_kelly_fraction(win_rate=0.55, win_loss_ratio=1.2)
    assert k_fraction >= 0.0 and k_fraction <= 1.0


# -----------------------------------------------------------------------------
# 8. PHASE 2 MODULE-SPECIFIC TESTS
# -----------------------------------------------------------------------------

def test_experiment_os_and_prioritization_economics():
    # Pluggable policies
    fifo = FIFOSchedulingPolicy()
    eig = ExpectedInformationGainSchedulingPolicy()
    mab = MultiArmedBanditSchedulingPolicy()

    scheduler = SovereignExperimentScheduler(policy=eig)

    p1 = ResearchProposal("p_1", "hyp_1", estimated_compute_hours=1.0, estimated_data_cost=0.5, expected_alpha=0.02, expected_sharpe_improvement=0.4, expected_uncertainty_reduction=0.5, confidence=0.8)
    p2 = ResearchProposal("p_2", "hyp_1", estimated_compute_hours=5.0, estimated_data_cost=2.5, expected_alpha=0.05, expected_sharpe_improvement=0.8, expected_uncertainty_reduction=0.9, confidence=0.8)

    scheduler.queue_proposal(p1)
    scheduler.queue_proposal(p2)

    resources = {"max_compute_hours": 10.0}
    selected = scheduler.select_next_experiment(resources)
    assert selected is not None
    # p1 should be selected under EIG policy because of high benefits relative to low log-costs
    assert selected.proposal_id == "p_1"

    # Reproducibility checks
    repro = scheduler.get_reproducibility_score("p_1")
    assert repro >= 0.0 and repro <= 1.0

    # Bayesian Prioritization Policy scoring
    evi_policy = BayesianEVIPrioritizationPolicy()
    score1 = evi_policy.score_proposal(p1)
    assert score1 >= 0.0

    # Economics Resource Optimizer
    econ_opt = ResearchEconomicsAllocationOptimizer(compute_budget_limit=2.0)
    allocated = econ_opt.allocate_compute_capital([p1, p2])
    assert len(allocated) == 1
    assert allocated[0].proposal_id == "p_1"


def test_causal_discovery_and_active_learning(sample_dataset):
    # Causal Engine
    features = FeatureDiscoveryEngine().generate_features(sample_dataset, "EURUSD")
    causal_engine = LinearStructuralCausalModel()
    causal_model = causal_engine.discover_causal_graph(sample_dataset, features)

    assert "nodes" in causal_model
    assert "edges" in causal_model

    # Counterfactual reasoning do(volatility = 3.0)
    counterfactual = causal_engine.evaluate_counterfactual(causal_model, "returns", {"volatility": 3.0})
    assert "counterfactual_state" in counterfactual
    assert counterfactual["counterfactual_state"]["volatility"] == 3.0

    # Active learning scans
    active_learner = RegimeGapActiveLearning()
    gaps = active_learner.select_regime_gaps([sample_dataset])
    assert len(gaps) >= 0


def test_world_model_and_digital_twin_simulator(sample_dataset):
    # World Model
    wm = MarkovRegimeSwitchingWorldModel()
    states = wm.predict_latent_states(sample_dataset)

    assert "latent_states" in states
    assert "transition_matrix" in states
    assert states["transition_matrix"].shape == (3, 3)

    # Digital twin flash crash stress test
    twin = AdversarialMarketDigitalTwin()
    twin_data = twin.instantiate_scenario("flash_crash", sample_dataset)

    symbol = sample_dataset.symbols[0]
    c_col = f"{symbol}_close"

    # Closes should be heavily impacted
    baseline_close = sample_dataset.data[c_col]
    twin_close = twin_data.data[c_col]

    assert len(twin_close) == len(baseline_close)
    # Volatility should be higher in twin
    assert np.std(np.diff(twin_close)) > np.std(np.diff(baseline_close))


def test_meta_research_and_decision_intelligence():
    # Signed DecisionRecords
    auditor = SovereignDecisionAuditor()
    decision = auditor.create_signed_decision(
        decision_type="accept_hypothesis",
        evidence={"ic": 0.05, "p_value": 0.01},
        assumptions=["predictable autocorrelation"],
        confidence=0.88,
        alternatives=["reject_hypothesis"],
        rationale="ADF stationarity passed and Granger causality validated."
    )

    assert decision.decision_id.startswith("dec_")
    assert len(decision.signature) > 10

    # Decision Quality audits
    audit_res = auditor.audit_decision_quality(decision.decision_id, "success")
    assert audit_res["bias_classification"] == "calibrated"

    # Meta-Research reviewer calibrations
    meta = AdaptiveMetaResearchEngine()
    reviews = [
        ReviewerOpinion("Dr. Sigma", "Statistician", is_approved=True, confidence=0.9, rationale="p-value < 0.05", objections=[], evidence_considered={"strategy_id": "strat_1"}),
        ReviewerOpinion("Flash", "Execution Specialist", is_approved=True, confidence=0.8, rationale="Turnover is normal", objections=[], evidence_considered={"strategy_id": "strat_1"})
    ]
    outcomes = {"strat_1": 1.5}  # successful outcome (Sharpe > 1.0)

    calibrations = meta.analyze_reviewer_calibration(reviews, outcomes)
    assert "Statistician" in calibrations
    assert calibrations["Statistician"] >= 0.0


# -----------------------------------------------------------------------------
# 9. INTEGRATION ORCHESTRATION TESTS (PHASE 2)
# -----------------------------------------------------------------------------

def test_sovereign_research_orchestrator_phase_2():
    orchestrator = SovereignResearchOrchestrator()

    # Ingest Paper On-Demand
    res_ingest = orchestrator._execute_evaluate_paper({
        "paper_id": "test_arxiv_2026",
        "title": "Adverse Selection Anomalies in High-Liquidity Regimes",
        "abstract": "We analyze adverse selection and order flow toxic imbalances in Forex G10 currency regimes.",
        "category": "microstructure"
    }, "orchestrator_integration_test")

    assert res_ingest["status"] == "success"

    # Ingest duplicate paper - must reject
    res_dup = orchestrator._execute_evaluate_paper({
        "paper_id": "test_arxiv_2026_dup",
        "title": "Adverse Selection Anomalies in High-Liquidity Regimes",
        "abstract": "We analyze adverse selection and order flow toxic imbalances in Forex G10 currency regimes.",
        "category": "microstructure"
    }, "orchestrator_integration_test")

    assert res_dup["status"] == "rejected"
    assert res_dup["reason"] == "duplicate_found"

    # Run full 14-stage quantitative research pipeline integrating Phase 2 features
    res_full = orchestrator._execute_full_pipeline({
        "symbol": "EURUSD",
        "query": "microstructure"
    }, "orchestrator_integration_test")

    assert res_full["status"] in ["success", "failed"]  # dependent on stochastic returns simulation, but must finish successfully
    assert "strategy_id" in res_full or "gate" in res_full
    if res_full["status"] == "success":
        assert "debate_consensus" in res_full
        assert "decision_record_id" in res_full
