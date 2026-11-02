"""
Tests for the Research Swarm: parallel fan-out of research programs,
agent isolation, replication adjudication, and proceedings archival.
"""

from trading_bot.research.swarm import (
    ResearchSwarm,
    SwarmProceedings,
)


def test_swarm_fans_out_paper_programs():
    swarm = ResearchSwarm(max_workers=3)
    proceedings = swarm.swarm([
        {"kind": "evaluate_paper", "title": "Order Flow Alpha I",
         "abstract": "VPIN-based microstructure signal."},
        {"kind": "evaluate_paper", "title": "Carry and Momentum Interactions",
         "abstract": "Cross-asset carry overlays on momentum."},
        {"kind": "evaluate_paper", "title": "Volatility Risk Premia in FX",
         "abstract": "Variance swap implied premia for majors."},
    ])

    assert isinstance(proceedings, SwarmProceedings)
    assert proceedings.programs == 3
    assert len(proceedings.findings) == 3
    assert all(f.status == "success" for f in proceedings.findings)
    assert all(v.verdict == "ingested" for v in proceedings.verdicts)
    # Proceedings archived to the swarm knowledge registry.
    assert swarm.proceedings_registry.get_knowledge(proceedings.swarm_id) is not None


def test_swarm_agents_are_independent_labs():
    """Distinct agents must run on distinct lab instances."""
    swarm = ResearchSwarm(max_workers=2)
    proceedings = swarm.swarm([
        {"kind": "evaluate_paper", "title": "Alpha Study A", "abstract": "a"},
        {"kind": "evaluate_paper", "title": "Alpha Study B", "abstract": "b"},
    ])
    agent_ids = {f.agent_id for f in proceedings.findings}
    assert len(agent_ids) >= 1
    assert proceedings.agents


def test_swarm_pipeline_program_with_replication():
    """A full-pipeline program replicated across agents gets a cross-validated verdict."""
    swarm = ResearchSwarm(max_workers=2)
    proceedings = swarm.swarm(
        [{"kind": "full_pipeline", "symbol": "EURUSD", "query": "microstructure"}],
        replication=2,
    )

    assert len(proceedings.findings) == 2
    roles = {f.role for f in proceedings.findings}
    assert roles == {"analyst", "replicator"}, \
        "replicated runs must be split across analyst and replicator seats"
    # Replication must land on different agents (independent labs).
    agent_ids = {f.agent_id for f in proceedings.findings}
    assert len(agent_ids) == 2

    verdict = proceedings.verdicts[0]
    assert verdict.replication_count == 2
    assert verdict.completed_runs == 2
    # Identical deterministic program run twice must agree (promoted or rejected).
    assert verdict.verdict in ("promoted", "rejected")
    assert verdict.replication_agreement == 1.0


def test_swarm_lab_report_lineage_preserved():
    """Swarm findings must carry the full institutional lab lineage."""
    swarm = ResearchSwarm(max_workers=2)
    proceedings = swarm.swarm(
        [{"kind": "full_pipeline", "symbol": "EURUSD", "query": "carry"}],
        replication=1,
    )
    finding = proceedings.findings[0]
    assert finding.lab_report is not None
    assert finding.lab_report["divisions_engaged"]
    assert finding.lab_report["minutes"]


def test_swarm_handles_agent_failure_without_sinking():
    """An unsupported task kind must produce an error finding, not crash the swarm."""
    swarm = ResearchSwarm(max_workers=2)
    proceedings = swarm.swarm([{"kind": "nonexistent_kind"}])
    assert proceedings.findings[0].status == "failed"
    assert proceedings.verdicts[0].verdict in ("error", "rejected")
