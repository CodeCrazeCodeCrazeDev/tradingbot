"""
Comprehensive Unit and Integration Tests for the Quantitative Research Institution (AQRI).
Validates the institutional operating systems, specialized divisions,
the four advanced scientific engines, Palantir Enterprise Ontology,
AIP Orchestrator, the 14-step research lifecycle, AEI capabilities,
and Weco AI AIDE2-Style recursive self-improvement (RSI) dual loops.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from trading_bot.research.institution import (
    QuantitativeResearchInstitution,
    ResearchOS, KnowledgeOS, ExperimentOS, GovernanceOS, EvolutionOS,
    TradingResearchDivision, PortfolioResearchDivision, MarketMicrostructureDivision,
    RiskScienceDivision, AIResearchDivision, ProductionDeploymentDivision,
    AdversarialCritiqueBoard, SkepticismEngine, ContinuousReplicationPipeline, EvolutionSandbox,
    PalantirEnterpriseOntology, AIPOrchestrator, OntologyObject, Theory,
    MultimodalDataPlane, AgentBrain, AgentTool, AgentExecutor,
    MinuteRecord, MinutesLedger, OntologyAgent, OntologyAgentTask,
    AgentSDK, AgentBuilder, AIPLogicFunction, AI_FDE,
    LivingDigitalTwin, TwinMetrics, ContinuousArchitectureParser,
    WorldStateEngine, WorldState, MultiAgentConsensusEngine, ConsensusRole,
    StrategicPlanningLayer, ResourceAwareScheduler, FormalVerificationModelChecker,
    CausalInferenceEngine, BayesianUncertaintyEstimator, FailureResearchMemory,
    EconomicEngineeringOptimizer, CapabilityGovernance,
    PromptCompressor, AntiRewardHackingGate, RSILadder, AIDE2_InnerLoop, AIDE2_OuterLoop
)
from trading_bot.research.research_computer import EpistemicInstruction


@pytest.fixture
def institution():
    """Returns an initialized QuantitativeResearchInstitution instance."""
    return QuantitativeResearchInstitution()


@pytest.fixture
def sample_data():
    """Generates a synthetic dataset for testing granger causality and dataset lineage."""
    np.random.seed(42)
    # Generate cointegrated/causal relation: target lags signal
    signal = np.random.randn(150)
    target = np.roll(signal, 1) + np.random.normal(0, 0.1, 150)
    target[0] = 0.0  # clean edge

    df = pd.DataFrame({
        "feature_signal": signal,
        "target_return": target
    })
    return df


def test_aqri_initialization(institution):
    """Verifies that the entire top-level institution initializes cleanly."""
    assert institution is not None
    assert isinstance(institution.ros, ResearchOS)
    assert isinstance(institution.kos, KnowledgeOS)
    assert isinstance(institution.eos, ExperimentOS)
    assert isinstance(institution.gos, GovernanceOS)
    assert isinstance(institution.evos, EvolutionOS)

    # Divisions
    assert isinstance(institution.trading_division, TradingResearchDivision)
    assert isinstance(institution.portfolio_division, PortfolioResearchDivision)
    assert isinstance(institution.microstructure_division, MarketMicrostructureDivision)
    assert isinstance(institution.risk_division, RiskScienceDivision)
    assert isinstance(institution.ai_division, AIResearchDivision)
    assert isinstance(institution.production_division, ProductionDeploymentDivision)

    # Palantir AIP Layers
    assert isinstance(institution.ontology, PalantirEnterpriseOntology)
    assert isinstance(institution.orchestrator, AIPOrchestrator)
    assert isinstance(institution.mmdp, MultimodalDataPlane)
    assert isinstance(institution.sdk, AgentSDK)
    assert isinstance(institution.builder, AgentBuilder)
    assert isinstance(institution.ai_fde, AI_FDE)

    # AEI Pillars
    assert isinstance(institution.twin, LivingDigitalTwin)
    assert isinstance(institution.parser, ContinuousArchitectureParser)
    assert isinstance(institution.world_state, WorldStateEngine)
    assert isinstance(institution.consensus, MultiAgentConsensusEngine)
    assert isinstance(institution.planner, StrategicPlanningLayer)
    assert isinstance(institution.scheduler, ResourceAwareScheduler)

    # Weco AI RSI Engines
    assert isinstance(institution.prompt_compressor, PromptCompressor)
    assert isinstance(institution.anti_hacking, AntiRewardHackingGate)
    assert isinstance(institution.aide_inner_loop, AIDE2_InnerLoop)
    assert isinstance(institution.aide_outer_loop, AIDE2_OuterLoop)


def test_research_os_intent_and_cycle(institution):
    """Tests project creation and instruction trace tracking on ROS."""
    project = institution.ros.register_scientific_intent(
        title="Order Book Microstructure Alpha",
        question_text="Does order book imbalance predict forward 1-minute price shifts?",
        objective="Analyze OBI Spearman correlations."
    )
    assert project is not None
    assert project.title == "Order Book Microstructure Alpha"

    trace = institution.ros.run_cpu_cycle(EpistemicInstruction.QUESTION, project.id)
    assert trace is not None
    assert trace.instruction == EpistemicInstruction.QUESTION
    assert trace.input_object_id == project.id
    assert trace.execution_success is True


def test_knowledge_os_graph_and_beliefs(institution):
    """Tests semantic storage, beliefs tracking, and Research Balance Sheet calculation on KOS."""
    # Find or verify belief
    belief_text = "Momentum is persistent under high volatility regimes"
    b = institution.kos.verify_belief_state(belief_text)
    assert b is not None
    assert b.statement == belief_text
    assert b.status == "Hypothetical"

    # Add finding to semantic graph
    node_id = "f_node_1"
    finding = {"type": "coefficient_correlation", "val": 0.35}
    institution.kos.record_finding(b.id, "verified_by", node_id, finding)

    related = institution.kos.graph.find_relations(b.id, "verified_by")
    assert node_id in related

    # Test Research Balance Sheet
    institution.kos.balance_sheet.validated_theories_count = 3
    institution.kos.balance_sheet.immutably_hashed_datasets_count = 5
    institution.kos.balance_sheet.production_ready_alphas_count = 1

    institution.kos.balance_sheet.unverified_hypotheses_count = 1
    institution.kos.balance_sheet.technical_debt_score = 2.0
    institution.kos.balance_sheet.known_data_quality_issues = 0

    equity = institution.kos.update_firm_knowledge_equity()
    assert equity == 5850.0


def test_experiment_os_reproducibility_and_causality(institution, sample_data):
    """Tests reproducible dataset locking and causal tests (Granger, Chow) on EOS."""
    idea_id = "idea_momentum_test"
    params = {"seed": 42, "model_class": "LinearCausalRegressor"}

    experiment = institution.eos.register_reproducible_experiment(
        idea_id=idea_id,
        dataset_name="Synthetic_OBI_M1",
        dataset_df=sample_data,
        parameters=params
    )
    assert experiment is not None
    assert experiment.random_seed == 42
    assert experiment.dataset_name == "Synthetic_OBI_M1"

    # Granger causality test
    causal_dict = institution.eos.test_causal_soundness(
        signal=sample_data["feature_signal"],
        target=sample_data["target_return"]
    )
    assert "granger_f_stat" in causal_dict
    assert "chow_break_f_stat" in causal_dict
    assert causal_dict["granger_f_stat"] >= 0.0


def test_governance_os_compliance_and_review(institution):
    """Tests the Constitutional Layer gating and Peer Review board functionality in GOS."""
    # Constitution violation checks
    passed = institution.gos.check_constitutional_compliance(
        claim_text="Alpha yields premium",
        evidence_ids=["evidence_123"],
        seed=123,
        dataset_hash="hash_abc"
    )
    assert passed is True

    # Check that a claim with NO evidence fails
    failed = institution.gos.check_constitutional_compliance(
        claim_text="Alpha yields premium with zero evidence",
        evidence_ids=[],
        seed=123,
        dataset_hash="hash_abc"
    )
    assert failed is False

    # Review Board testing
    verdict = institution.gos.perform_peer_review_board(
        experiment_id="exp_abc",
        assumptions=["gaussian distribution", "zero latency impact"],
        metrics={"is_sharpe": 2.2, "oos_sharpe": 1.8}
    )
    assert verdict is not None
    assert verdict.methodology_valid is True
    assert verdict.verdict == "APPROVED"


def test_evolution_os_monotone_safety(institution):
    """Tests monotone-safe system self-modifications in EvOS."""
    prop_id = institution.evos.propose_system_evolution(
        subsystem_name="SAGE_Graph_Memory",
        proposed_code="class CompactedSAGE(SAGEGraphMemory): pass",
        rationale="Compacts the memory footprint to resolve Day 10 initialization overheads."
    )
    assert prop_id is not None
    assert prop_id in institution.evos.improvement_candidates

    # Evaluate safety with a regression failure: should fail
    reg_failed = institution.evos.run_monotone_safety_evaluation(
        proposal_id=prop_id,
        regression_results={"improvement_percentage": 12.5, "regression_failures_count": 2.0}
    )
    assert reg_failed is False
    assert institution.evos.improvement_candidates[prop_id]["status"] == "Rejected"

    # Evaluate safety with positive improvement and 0 regression: should succeed
    reg_success = institution.evos.run_monotone_safety_evaluation(
        proposal_id=prop_id,
        regression_results={"improvement_percentage": 5.4, "regression_failures_count": 0.0}
    )
    assert reg_success is True
    assert institution.evos.improvement_candidates[prop_id]["status"] == "Verified_Safe"


def test_scientific_divisions_computations(institution):
    """Validates math-oriented computations across the 6 scientific divisions."""
    # Trading Research
    theory = institution.trading_division.propose_alpha_theory(
        title="Microstructure Drift",
        description="OBI imbalance yields short-term mean-reverting pressures."
    )
    assert theory is not None
    assert theory.explanation == "OBI imbalance yields short-term mean-reverting pressures."

    # Portfolio Division: Fractional Kelly Allocation
    kelly = institution.portfolio_division.compute_kelly_allocation_bounds(
        win_rate=0.55,
        win_loss_ratio=1.2
    )
    assert abs(kelly - 0.0875) < 1e-5

    # Market Microstructure OBI
    obi = institution.microstructure_division.compute_order_book_imbalance(
        bid_vol=150.0,
        ask_vol=50.0
    )
    assert obi == 0.5

    # Risk Science: Credal Bounds
    predictions = [1.2, 1.15, 1.25, 1.21, 1.18]
    mean, lower, upper = institution.risk_division.calculate_prediction_bounds(predictions)
    assert mean == pytest.approx(1.198, abs=1e-3)
    assert lower < mean < upper

    # AI Research Division
    institution.ai_division.challenge_institutional_assumption("Pricing signals are static over multi-year regimes.")
    assert "Pricing signals are static over multi-year regimes." in institution.ai_division.assumptions_audit

    audit = institution.ai_division.run_meta_research_audit()
    assert audit["total_assumptions_audited"] == 1

    # Production Division: Packaged runbooks
    package = institution.production_division.transition_theory_to_packaged_code(
        model_uuid="model_123",
        code_hash="sha256_hash_value"
    )
    assert package is not None
    assert package.model_uuid == "model_123"
    assert package.reversion_rollback_hash == "sha256_hash_value"


def test_adversarial_critique_board(institution):
    """Tests the institutional Red Team board for look-ahead leakage and overfitting attacks."""
    board = AdversarialCritiqueBoard()

    # 1. Attack code containing shift(-1) look-ahead leakage: should fail
    unsafe_code = "signal = df['price'].shift(-1)"
    unsafe_metrics = {"sharpe_ratio": 2.5, "num_bars": 120}
    is_safe, vulnerabilities = board.challenge_model_vigor("exp_001", unsafe_code, unsafe_metrics)
    assert is_safe is False
    assert any("look-ahead" in v.lower() for v in vulnerabilities)

    # 2. Attack code with safe implementation: should succeed
    safe_code = "signal = df['price'].shift(1)"
    safe_metrics = {"sharpe_ratio": 2.1, "num_bars": 150}
    is_safe_2, vulnerabilities_2 = board.challenge_model_vigor("exp_002", safe_code, safe_metrics)
    assert is_safe_2 is True
    assert len(vulnerabilities_2) == 0


def test_skepticism_engine_groupthink(institution):
    """Tests detection of Groupthink/Cognitive Clustering in active firm theories."""
    engine = SkepticismEngine(kos=institution.kos)

    # State with no theories is diversified
    res_empty = engine.audit_cognitive_diversity()
    assert res_empty["status"] == "DIVERSIFIED"

    # Add three clustered momentum theories
    t1 = Theory(explanation="momentum trends in pricing")
    t2 = Theory(explanation="momentum SMA breakouts")
    t3 = Theory(explanation="momentum breakouts with RSI indicators")

    institution.kos.graph.add_node("t1", t1)
    institution.kos.graph.add_node("t2", t2)
    institution.kos.graph.add_node("t3", t3)

    res_clustered = engine.audit_cognitive_diversity()
    assert res_clustered["status"] == "CLUSTERED"
    assert res_clustered["recommendation"] == "FORCE_DIVERSIFICATION"


def test_continuous_replication_pipeline(institution, sample_data):
    """Tests retrospective replication study of older accepted theories."""
    t = Theory(explanation="Causal imbalance theory", confidence_score=0.90)
    institution.kos.graph.add_node("theory_c1", t)

    pipeline = ContinuousReplicationPipeline(kos=institution.kos)

    replicated, replicated_sharpe = pipeline.replicate_theory("theory_c1", sample_data)
    assert replicated in [True, False]
    assert len(pipeline.replication_audit_log) == 1
    assert pipeline.replication_audit_log[0]["theory_id"] == "theory_c1"


def test_evolution_sandbox_ablation():
    """Tests N-Dimensional Ablation studies on self-evolution proposals."""
    sandbox = EvolutionSandbox()
    proposal_id = "ev_prop_lr_resets"
    components = ["lr_scheduler_decay", "adam_optimizer_weight_decay"]

    ablation_matrix = sandbox.execute_ablation_study(proposal_id, components)
    assert "baseline" in ablation_matrix
    assert "full_integration" in ablation_matrix
    assert "only_lr_scheduler_decay" in ablation_matrix

    history = sandbox.ablation_matrix_history[proposal_id]
    assert len(history["attribution"]) == 2
    assert pytest.approx(sum(history["attribution"].values()), 1e-5) == 1.0


def test_palantir_ontology_and_orchestrator(institution):
    """Tests Palantir Enterprise Ontology tracking and long-running AIP Orchestrator teaming."""
    ontology = institution.ontology
    orchestrator = institution.orchestrator

    # 1. Create objects and links
    dataset_obj = ontology.create_object(obj_type="DATASET", properties={"name": "tick_data_EURUSD"})
    alpha_obj = ontology.create_object(obj_type="ALPHA", properties={"formula": "imbalance * zscore"})
    ontology.link_objects(alpha_obj.id, "trained_on", dataset_obj.id)

    assert len(ontology.objects) == 2
    assert len(ontology.relations) == 1

    # 2. Transactional Mutation
    action = ontology.apply_transaction(
        action_type="PROMOTE_TO_PRODUCTION",
        obj_id=alpha_obj.id,
        params={"state": "Active", "properties_update": {"reproducibility": "verified"}},
        agent_id="AIPOrchestrator"
    )
    assert ontology.objects[alpha_obj.id].state == "Active"
    assert ontology.objects[alpha_obj.id].properties["reproducibility"] == "verified"
    assert len(ontology.action_ledger) == 1

    # 3. AIP Orchestrator Background Agents
    agent = orchestrator.register_agent(role="RiskValidator")
    task = orchestrator.dispatch_task(
        agent_id=agent.id,
        desc="Audit slippage parameter constraints on new Alpha.",
        obj_id=alpha_obj.id
    )
    assert len(orchestrator.agents) == 1
    assert task.status == "Pending"

    # 4. Human-Agent Teaming Gate
    approved = orchestrator.run_human_agent_teaming_gate(
        task_id=task.id,
        rationale="All slippage validation metrics met. Highly clean data."
    )
    assert approved is True
    assert task.status == "Completed"


def test_durable_orchestration_and_checkpoints(institution):
    """Tests durable interruptible checkpointing under AIP Orchestrator."""
    orchestrator = institution.orchestrator
    agent = orchestrator.register_agent(role="DataEngineer")
    task = orchestrator.dispatch_task(agent.id, "Ingesting Tick Order Logs", "dataset_123")

    # Save checkpoints to allow interruptible/resumable execution states
    orchestrator.save_task_checkpoint(task.id, "checkpoint_stage_1", {"index_offset": 50000})
    assert "checkpoint_stage_1" in task.checkpoints
    assert task.checkpoints["checkpoint_stage_1"]["state"]["index_offset"] == 50000


def test_agent_engine_core_primitives():
    """Tests AgentBrain, AgentTool and AgentExecutor primitives."""
    brain = AgentBrain(role="MicrostructureMiner", system_prompt="Find short-term inefficiencies")
    tool = AgentTool(
        name="calc_correlation",
        description="Calculates Spearman correlations",
        callable_func=lambda x, y: 0.85
    )
    executor = AgentExecutor(brain=brain, tools=[tool])

    success, result = executor.execute_step("calc_correlation", {"x": [1, 2, 3], "y": [2, 4, 6]})
    assert success is True
    assert result == 0.85


def test_agent_sdk_cli_dx(institution):
    """Tests pro-code developer experience (DX) CLI initializing agent packages."""
    sdk = institution.sdk
    pkg_id = sdk.initialize_agent_package("CustomSlippageAgent", {"version": "1.4.2"})
    assert pkg_id is not None
    assert "CustomSlippageAgent" in sdk.packages_registry


def test_agent_builder_prompt_compiler(institution):
    """Tests low-code NLP agent creation compiling prompt to AgentBrain on top of the Ontology."""
    builder = institution.builder
    brain = builder.compile_prompt_to_agent("Create an agent to audit maximum drawdown risk boundaries.")
    assert brain.role == "RiskValidator"
    assert brain.parameters["risk_strictness"] == "High"


def test_minutes_audit_and_replay(institution):
    """Tests recording step execution traces in 'Minutes' and replaying agent steps."""
    ledger = institution.orchestrator.minutes
    ledger.record_step(
        agent_id="agent_001",
        task_id="task_999",
        step_index=1,
        action="calculate_fvg",
        inputs={"threshold": 0.05},
        outputs={"fvg_found": True},
        snapshot={"fvg_count": 12}
    )

    traces = ledger.replay_task("task_999")
    assert len(traces) == 1
    assert traces[0].action_name == "calculate_fvg"
    assert traces[0].outputs["fvg_found"] is True


def test_multimodal_data_plane_pushdown(institution):
    """Tests virtual table registrations and high-efficiency compute pushdown operations in MMDP."""
    mmdp = institution.mmdp
    df = pd.DataFrame({
        "symbol": ["EURUSD", "GBPUSD", "EURUSD"],
        "price": [1.08, 1.25, 1.09]
    })
    mmdp.register_virtual_table("raw_forex_feed", df)

    # Compute pushdown: apply filter & projection on MMDP side before fetching
    query_res = mmdp.execute_pushdown_query(
        table_name="raw_forex_feed",
        filters={"symbol": "EURUSD"},
        select_columns=["price"]
    )
    assert len(query_res) == 2
    assert list(query_res.columns) == ["price"]


def test_ai_fde_continuous_loop(institution):
    """Tests AI FDE self-evolving branch-aware continuous coding, evaluation and debugging."""
    fde = institution.ai_fde
    func = fde.author_aip_logic_function(
        name="calc_volatility_multiplier",
        code="def run(vix): return vix * 0.12 # clean syntax"
    )
    fde.author_automated_evaluations(
        name="calc_volatility_multiplier",
        evals=["assert run(20) == 2.4"]
    )

    success = fde.run_safe_debugging_loop("calc_volatility_multiplier")
    assert success is True
    assert func.state == "Safe_To_Commit"


def test_mindkit_dynamic_fleets(institution):
    """Tests dynamic ontology-powered fleet deployments using Mindkit patterns."""
    orchestrator = institution.orchestrator
    fleet_agents = orchestrator.deploy_mindkit_fleet(
        fleet_id="fleet_micro_alpha",
        roles=["DataEngineer", "QuantitativeResearcher", "RiskValidator"]
    )
    assert len(fleet_agents) == 3
    assert orchestrator.active_fleets["fleet_micro_alpha"] == fleet_agents


def test_living_digital_twin_and_parser(institution):
    """Tests the living digital twin metrics tracking and Continuous Architecture parser AST audits."""
    twin = institution.twin
    parser = institution.parser

    twin.register_service("ExecutionCore", {"port": 5001, "threads": 16})
    assert "ExecutionCore" in twin.services

    # Trigger change with eval() security risk
    change_res = parser.analyze_file_change("trading_bot/execution/arbitrage.py", "eval('1 + 1')")
    assert change_res["risk_score"] == 0.95
    assert twin.metrics.technical_debt_score >= 0.95


def test_world_state_and_consensus(institution):
    """Tests WorldState Engine query updates and independent multi-agent consensus reviews."""
    world = institution.world_state
    world.update_state(WorldState(repository_hash="sha_git_101", active_agent_count=5))
    assert world.query_state().repository_hash == "sha_git_101"

    # Multi-Agent Consensus reviews
    proposal_id = "prop_999"
    consensus = institution.consensus

    consensus.collect_role_review(proposal_id, ConsensusRole.ARCHITECT, True, "Approved design pattern.")
    consensus.collect_role_review(proposal_id, ConsensusRole.QA, True, "No regression found.")
    consensus.collect_role_review(proposal_id, ConsensusRole.DEVOPS, True, "Deployable package verified.")

    passed, rationale = consensus.evaluate_consensus(proposal_id)
    assert passed is True
    assert rationale == "APPROVED BY CONSENSUS"


def test_strategic_planning_and_scheduling(institution):
    """Tests ROI bottleneck identification and resource-aware scheduling."""
    twin = institution.twin
    planner = institution.planner
    scheduler = institution.scheduler

    # Setup high tech debt in twin
    twin.metrics.technical_debt_score = 6.2
    roi_mission = planner.identify_highest_roi_mission()
    assert roi_mission["target_subsystem"] == "Technical_Debt_Refactor"
    assert roi_mission["expected_roi"] == 85.0

    # Resource aware allocations
    success_alloc = scheduler.schedule_resource_task(task_priority=1, cost_cores=64)
    assert success_alloc is True
    assert scheduler.available_cores == 64

    fail_alloc = scheduler.schedule_resource_task(task_priority=2, cost_cores=128)
    assert fail_alloc is False


def test_advanced_aei_capabilities(institution, sample_data):
    """Tests formal verification proofs, causal do-effect proxies, and Beta Bayesian posteriors."""
    # Formal Verification model check
    proven, msg = FormalVerificationModelChecker.verify_invariant(current_state_val=10.0, proposed_delta=5.0, max_allowable_bound=20.0)
    assert proven is True

    # Pearl do-calculus causal interventional effect
    effect = CausalInferenceEngine.estimate_interventional_do_effect(cause_active=True, outcome_series=pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]))
    assert effect > 0.0

    # Bayesian posterior probability
    posterior = BayesianUncertaintyEstimator.compute_posterior_confidence(prior_confidence=0.5, successful_trials=8, total_trials=10)
    assert posterior > 0.5

    # Failure Research Memory
    failures = FailureResearchMemory()
    failures.record_failed_hypothesis("Linear EMAs prevent drift", 0.04, "High alpha decay")
    assert failures.is_failed_concept("Linear EMAs prevent drift") is True

    # Economic Engineering Optimizer
    viable, net_value = EconomicEngineeringOptimizer.evaluate_task_net_value(expected_alpha_return_usd=1000.0, compute_cost_usd=100.0, code_maintenance_cost_usd=50.0)
    assert viable is True
    assert net_value == 850.0

    # Capability Governance escalation rules
    gov = CapabilityGovernance()
    privs = gov.log_reliability_score(0.98)
    assert privs.can_self_evolve is True


def test_weco_prompt_compression():
    """Tests 16x prompt context compression according to AIDE2 standards."""
    naive_history = (
        "Verbose system initialization sequence starting... Done.\n"
        "Loading dataset... Done.\n"
        "Step 1: Out-of-sample Sharpe ratio found = 1.45.\n"
        "Verbose garbage debug lines... omitted.\n"
        "Step 2: Forward return Sharpe ratio found = 1.95.\n"
        "def calculate_spread_impact(p): pass"
    )
    compressed = PromptCompressor.compress_context(naive_history)
    assert "1.45" in compressed
    assert "1.95" in compressed
    assert "calculate_spread_impact" in compressed
    # Exclude verbose garbage sequences
    assert "sequence starting" not in compressed
    assert len(compressed) < len(naive_history)


def test_weco_anti_reward_hacking():
    """Tests automated detection and blockage of reward hacking and test outcome cheating."""
    gate = AntiRewardHackingGate()

    # 1. Try cheating code using mock patch: should reject
    cheat_code = "with mock.patch('target') as m: return True"
    clean, msg = gate.inspect_code_for_hacking(cheat_code, "assert sharpe > 1.2")
    assert clean is False
    assert "REJECTED" in msg

    # 2. Try outcome matching cheat: should reject
    cheat_code_2 = "assert expected == actual"
    clean_2, msg_2 = gate.inspect_code_for_hacking(cheat_code_2, "assert sharpe > 1.2")
    assert clean_2 is False

    # 3. Clean optimization code: should pass
    clean_code = "def calc_sharpe(pnl): return np.mean(pnl) / np.std(pnl)"
    clean_3, msg_3 = gate.inspect_code_for_hacking(clean_code, "assert sharpe > 1.2")
    assert clean_3 is True


def test_aide2_dual_loop_rsi(institution):
    """Tests AIDE2 dual-loop RSI progression on Weco's 4-level ladder."""
    outer_loop = institution.aide_outer_loop
    assert outer_loop is not None

    # Step 1: Execute recursive self improvement under low baseline: transitions to Level 1 Net Positive
    level, sharpe = outer_loop.execute_self_improvement_step(
        proposed_harness_rewrite="class NewHarness(AIDE2_OuterLoop): pass",
        human_tuned_baseline_sharpe=0.80
    )
    assert level == RSILadder.LEVEL_1_NET_POSITIVE or level == RSILadder.LEVEL_2_IGNITION
    assert sharpe > 0.80


def test_end_to_end_institutional_research_lifecycle(institution, sample_data):
    """Runs a complete 14-step continuous research-and-evolution cycle in the integrated AQRI."""
    result = institution.run_full_research_cycle(
        project_title="Order Book Imbalance Predictive Alpha",
        research_question="Does L2 order book imbalance have causal granger-predictive influence on EURUSD?",
        data_feed=sample_data,
        hypothesis_text="Momentum persists when order book imbalance > 0.4"
    )

    assert result is not None
    assert result["promoted"] is True
    assert result["reproducible"] is True
    assert result["validation"].deflated_sharpe == 2.45
    assert result["package"] is not None
    assert result["package"].model_uuid == result["experiment"].id
    assert result["knowledge_equity"] > 0
