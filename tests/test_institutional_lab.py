"""
Tests for the Institutional Research Lab layer over the
SovereignResearchOrchestrator kernel: org chart integrity, stage->division
attribution, minutes ledger, and program reporting.
"""

from trading_bot.research.lab import (
    InstitutionalResearchLab,
    LabMinutesLedger,
    STAGE_TO_DIVISION,
    build_org_chart,
    division_for_stage,
)
from trading_bot.research.orchestration.kernel import SovereignResearchOrchestrator


def test_org_chart_covers_every_emitted_stage():
    """Every stage the kernel emits must be owned by a declared division."""
    chart = build_org_chart()
    declared_keys = {d.key for d in chart}
    assert len(declared_keys) == len(chart), "duplicate division keys in org chart"

    for stage, division in STAGE_TO_DIVISION.items():
        assert division in declared_keys, f"stage '{stage}' maps to undeclared division '{division}'"

    for division in chart:
        assert division.stages, f"division '{division.key}' owns no stages"
        for stage in division.stages:
            assert STAGE_TO_DIVISION[stage] == division.key, (
                f"division '{division.key}' claims stage '{stage}' "
                f"mapped to '{STAGE_TO_DIVISION[stage]}'"
            )


def test_minutes_ledger_replay_and_failures():
    ledger = LabMinutesLedger()
    ledger.record("t1", "alpha_lab", "alpha_generation", "completed", {"ic": 0.05})
    ledger.record("t1", "governance_office", "promotion_governance", "failed", {"gate": "gate_2"})
    ledger.record("t2", "literature_desk", "literature_intake", "completed")

    t1 = ledger.replay_task("t1")
    assert len(t1) == 2
    assert ledger.divisions_engaged("t1") == ["alpha_lab", "governance_office"]
    failed = ledger.failed_stages("t1")
    assert len(failed) == 1 and failed[0].stage == "promotion_governance"
    assert len(ledger) == 3


def test_kernel_emits_stage_events_to_observer():
    """The kernel must emit stage events a lab observer can attribute."""
    orch = SovereignResearchOrchestrator()
    events = []
    orch.register_stage_observer(events.append)

    orch._execute_evaluate_paper(
        {"title": "Test Paper Alpha", "abstract": "Testing the desk pipeline."},
        "obs_test",
    )

    stages = [e["stage"] for e in events]
    assert "literature_intake" in stages
    assert "duplicate_check" in stages
    assert "graph_persistence" in stages
    for e in events:
        assert e["task_id"] == "obs_test"
        assert e["status"] == "completed"
        assert division_for_stage(e["stage"]) == "literature_desk"


def test_lab_evaluate_paper_records_literature_desk_minutes():
    lab = InstitutionalResearchLab()
    res = lab.evaluate_paper_submission(
        title="Market Impact of Limit Order Book Imbalance",
        abstract="Empirical study of short-horizon imbalance alpha in FX majors.",
    )
    assert res["status"] == "success"

    desk_stages = {m.stage for m in lab.minutes._minutes if m.division == "literature_desk"}
    assert {"literature_intake", "duplicate_check", "graph_persistence"} <= desk_stages


def test_lab_run_research_program_produces_institutional_report():
    """A full program must engage the pipeline divisions and produce minutes."""
    lab = InstitutionalResearchLab()
    report = lab.run_research_program(symbol="EURUSD", query="microstructure")

    assert report.program_id.startswith("prog_")
    assert report.status in ("success", "failed")
    assert report.decision
    assert report.divisions_engaged, "no divisions recorded any activity"

    # A gated run should still traverse upstream divisions.
    for key in ("literature_desk", "hypothesis_lab", "data_operations",
                "statistics_office", "alpha_lab", "validation_desk",
                "peer_review_board", "governance_office"):
        assert key in report.divisions_engaged, f"division '{key}' did not engage"

    engaged = {d.division_key for d in report.division_reports if d.stages_run > 0}
    assert engaged == set(report.divisions_engaged)

    # Every division-owned stage of the lifecycle must have recorded a minute.
    stages_run = {m.stage for m in report.minutes}
    assert {"feature_engineering", "feature_selection",
            "strategy_synthesis", "experiment_registration"} <= stages_run

    # Proceedings archived to the institutional knowledge base.
    archived = lab.orchestrator.knowledge_registry.get_knowledge(report.program_id)
    assert archived is not None
    assert archived["category"] == "lab_proceedings"


def test_dispatch_swarm_archives_proceedings_to_lab_knowledge_base():
    """Swarm proceedings dispatched by the lab must land in the lab's own
    knowledge registry — the institutional KB is incomplete otherwise."""
    lab = InstitutionalResearchLab()
    proceedings = lab.dispatch_swarm(
        [{"kind": "full_pipeline", "symbol": "EURUSD", "query": "microstructure"}],
        max_workers=1, replication=1,
    )

    archived = lab.orchestrator.knowledge_registry.get_knowledge(proceedings.swarm_id)
    assert archived is not None
    assert archived["category"] == "swarm_proceedings"


def test_lab_minutes_replay_isolated_per_task():
    lab = InstitutionalResearchLab()
    task_a = "lab_task_a"
    lab.evaluate_paper_submission(
        title="Volatility Clustering Revisited",
        abstract="GARCH-family persistence across FX regimes.",
        task_id=task_a,
    )
    a_minutes = lab.get_minutes(task_a)
    assert a_minutes and all(m.task_id == task_a for m in a_minutes)
    assert all(m["minute_id"] for m in lab.export_minutes())
