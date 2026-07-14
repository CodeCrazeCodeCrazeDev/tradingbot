import pytest
import os
import shutil
from trading_bot.research.asrs.registry.manager import ExperimentRegistry
from trading_bot.research.asrs.scheduler.scheduler import ComputeResourceScheduler
from trading_bot.research.asrs.ledger.ledger import ResearchLedger
from trading_bot.research.asrs.discovery.knowledge_graph import ScientificKnowledgeGraph
from trading_bot.research.asrs.understanding.parser import ScientificPaperParser
from trading_bot.research.asrs.opportunity.detector import OpportunityDiscovery
from trading_bot.research.asrs.opportunity.carp import CostAwareResearchPlanner
from trading_bot.research.asrs.experiment.generator import ExperimentGenerator
from trading_bot.research.asrs.evolution.engine import SpeciatedEvolutionEngine
from trading_bot.research.asrs.harness.harness_evolution import HarnessEvolutionSystem
from trading_bot.research.asrs.strategy.laboratory import StrategyEvolutionLaboratory
from trading_bot.research.asrs.world_model.active_inference import ActiveInferenceWorldModel
from trading_bot.research.asrs.verification.lab import VerificationLaboratory
from trading_bot.research.asrs.benchmark.lab import BenchmarkLaboratory
from trading_bot.research.asrs.governance.gate import PromotionGate

@pytest.fixture
def clean_test_env():
    # Setup safe temporary database paths
    test_db_path = "alphaalgo_data/test_research_experiments.db"
    test_graph_path = "alphaalgo_data/test_scientific_knowledge_graph.json"
    test_schemas_dir = "alphaalgo_data/test_scientific_schemas/"
    test_ledger_dir = "alphaalgo_data/test_ledger/"

    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    if os.path.exists(test_graph_path):
        os.remove(test_graph_path)
    if os.path.exists(test_schemas_dir):
        shutil.rmtree(test_schemas_dir, ignore_errors=True)
    if os.path.exists(test_ledger_dir):
        shutil.rmtree(test_ledger_dir, ignore_errors=True)

    yield {
        "db": test_db_path,
        "graph": test_graph_path,
        "schemas": test_schemas_dir,
        "ledger": test_ledger_dir
    }

    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    if os.path.exists(test_graph_path):
        os.remove(test_graph_path)
    shutil.rmtree(test_schemas_dir, ignore_errors=True)
    shutil.rmtree(test_ledger_dir, ignore_errors=True)

def test_experiment_registry_state_transitions(clean_test_env):
    reg = ExperimentRegistry(clean_test_env["db"])
    exp_id = "exp-test-01"
    hyp_id = "hyp-test-01"

    # Register
    reg.register_experiment(
        experiment_id=exp_id,
        hypothesis_id=hyp_id,
        isolation_level=1,
        git_sha="12345",
        resources={"cores": [1, 2]},
        rollback_instructions={"revert": "none"}
    )

    exp = reg.get_experiment(exp_id)
    assert exp is not None
    assert exp["state"] == "QUEUED"
    assert exp["isolation_level"] == 1

    # Transition to Running
    reg.update_state(exp_id, "RUNNING")
    exp = reg.get_experiment(exp_id)
    assert exp["state"] == "RUNNING"

    # Transition to Completed
    reg.update_state(exp_id, "COMPLETED")
    exp = reg.get_experiment(exp_id)
    assert exp["state"] == "COMPLETED"

def test_compute_resource_scheduler_affinity():
    scheduler = ComputeResourceScheduler()
    res = scheduler.check_system_resources()
    assert "ram_pct" in res
    assert "system_safe" in res

    cores = scheduler.allocate_cores_for_experiment()
    assert isinstance(cores, list)
    assert len(cores) > 0

def test_scientific_knowledge_graph_traversal(clean_test_env):
    skg = ScientificKnowledgeGraph(clean_test_env["graph"])
    # Defaults should load SAGE, EKSFT, and DiscoLoop
    assert "paper:eksft_2026" in skg.nodes

    solutions = skg.find_solutions_for_domain("calibration_masking")
    assert len(solutions) > 0
    assert solutions[0]["id"] == "paper:eksft_2026"

def test_scientific_paper_parser_mass(clean_test_env):
    parser = ScientificPaperParser(clean_test_env["schemas"])
    mass = parser.parse_paper_to_mass("paper:eksft_2026")
    assert mass["paper_id"] == "paper:eksft_2026"
    assert "mathematical_formulation" in mass
    assert len(mass["algorithmic_definition"]["steps"]) > 0

def test_opportunity_discovery_breached_thresholds():
    odd = OpportunityDiscovery()

    # Simulated healthy metrics
    metrics_ok = {"calibration_error": 0.05, "execution_latency_ms": 110.0}
    hyp_ok = odd.inspect_system_diagnostics(metrics_ok)
    assert len(hyp_ok) == 0

    # Simulated breached metrics
    metrics_breached = {"calibration_error": 0.18, "execution_latency_ms": 110.0}
    hyp_breached = odd.inspect_system_diagnostics(metrics_breached)
    assert len(hyp_breached) == 1
    assert hyp_breached[0].trigger_metric == "calibration_error"
    assert hyp_breached[0].target_domain == "calibration_masking"

def test_carp_roi_calculation():
    carp = CostAwareResearchPlanner()
    eroi = carp.calculate_eroi(
        expected_improvement=0.25,
        probability_success=0.80,
        difficulty_score=4.0,
        estimated_compute_hours=4.0,
        systemic_risk_index=2.0
    )
    # EROI = (25 * 0.8 - 4 * 1.2) / 6 = (20 - 4.8) / 6 = 15.2 / 6 = 2.533
    assert abs(eroi - 2.533) < 0.01

def test_experiment_generator_sandbox_isolation():
    eg = ExperimentGenerator()
    sandbox = eg.prepare_sandbox("test-exp-01", 1)
    assert sandbox["isolation_level"] == 1
    assert sandbox["workspace_path"] == "memory"

    sandbox_l2 = eg.prepare_sandbox("test-exp-02", 2)
    assert sandbox_l2["isolation_level"] == 2
    assert "l2-test-exp-02" in sandbox_l2["workspace_path"]

    # Cleanup
    eg.cleanup_sandbox(sandbox_l2)
    assert not os.path.exists(sandbox_l2["workspace_path"])

def test_speciated_evolution_and_pareto():
    engine = SpeciatedEvolutionEngine()
    candidates = [
        {"id": "cand_a", "objectives": [0.45, 120.0]}, # high return, high latency
        {"id": "cand_b", "objectives": [0.12, 12.0]},   # low return, low latency
        {"id": "cand_c", "objectives": [0.45, 150.0]}  # dominated by cand_a (same return, higher latency)
    ]
    fronts = engine.sort_pareto_fronts(candidates)
    assert len(fronts) > 0
    # First front should contain cand_a and cand_b
    first_front_ids = [p["id"] for p in fronts[0]]
    assert "cand_a" in first_front_ids
    assert "cand_b" in first_front_ids
    assert "cand_c" not in first_front_ids

def test_harness_evolution_textgrad():
    hes = HarnessEvolutionSystem()
    prompt = "Task: Decide trade size based on volatility parameters."
    mutated = hes.perform_textgrad_mutation(prompt, "Latency is too high.")
    assert "Respond concisely" in mutated

def test_strategy_evolution_metrics():
    sel = StrategyEvolutionLaboratory(risk_free_rate=0.0)
    rets = [0.01, 0.02, -0.015, 0.03, -0.005, 0.01]

    sharpe = sel.calculate_sharpe(rets)
    sortino = sel.calculate_sortino(rets)
    cvar = sel.calculate_cvar_95(rets)

    assert sharpe > 0.0
    assert sortino > 0.0
    assert cvar == 0.015 # 5th percentile is -0.015 loss

def test_active_inference_vfe():
    wm = ActiveInferenceWorldModel()
    vfe = wm.calculate_variational_free_energy(
        predicted_mean=0.5,
        predicted_variance=0.1,
        observed_value=0.52,
        prior_entropy=1.2
    )
    assert isinstance(vfe, float)

def test_verification_lab_security_integrity():
    vl = VerificationLaboratory()
    safe_code = "def f(x):\n    return x * 2"
    unsafe_code = "import os\nos.system('rm -rf /')"

    assert vl.verify_pipeline_integrity(safe_code) is True
    assert vl.verify_pipeline_integrity(unsafe_code) is False

def test_benchmark_lab_ece_and_percentiles():
    sbl = BenchmarkLaboratory()
    latencies = [12.0, 14.0, 45.0, 110.0, 420.0]
    p = sbl.calculate_percentiles(latencies)
    assert p["P50"] == 45.0
    assert p["P99"] == 420.0

    confidences = [0.9, 0.8, 0.3, 0.6]
    outcomes = [1, 1, 0, 1]
    ece = sbl.calculate_ece(confidences, outcomes, num_bins=2)
    assert 0.0 <= ece <= 1.0

def test_promotion_gate_bootstrap(clean_test_env):
    gate = PromotionGate()
    cand = [0.02, 0.03, 0.01, 0.04, 0.02]
    base = [0.001, 0.002, -0.003, 0.001, 0.002]

    passed, ci = gate.run_bootstrap_sharpe_test(cand, base, iterations=50)
    assert isinstance(passed, bool)
    assert isinstance(ci, list)
    assert len(ci) == 2

def test_research_ledger_immutability(clean_test_env):
    ledger = ResearchLedger(clean_test_env["ledger"])

    # Commit Record 1
    h1 = ledger.commit_record(
        record_uuid="rl-test-01",
        hypothesis_id="hyp-test-01",
        git_context={"base_sha": "abc", "experiment_sha": "def"},
        configuration_hash="hash1",
        verification_report={"ok": True},
        benchmark_metrics={"latency": 112.0},
        statistical_tests={"p_val": 0.01},
        adversarial_audit_log="ARA passed",
        decision_rationale="reproducible",
        promotion_outcome="APPROVED",
        rollback_instructions={"cmd": "revert"}
    )
    assert h1 != "0" * 64
    assert ledger.scan_integrity() is True

    # Commit Record 2 - should be linked via Merkle parent
    h2 = ledger.commit_record(
        record_uuid="rl-test-02",
        hypothesis_id="hyp-test-02",
        git_context={"base_sha": "def", "experiment_sha": "ghi"},
        configuration_hash="hash2",
        verification_report={"ok": True},
        benchmark_metrics={"latency": 105.0},
        statistical_tests={"p_val": 0.02},
        adversarial_audit_log="ARA passed",
        decision_rationale="faster",
        promotion_outcome="APPROVED",
        rollback_instructions={"cmd": "revert"}
    )
    assert h2 != h1
    assert ledger.scan_integrity() is True
