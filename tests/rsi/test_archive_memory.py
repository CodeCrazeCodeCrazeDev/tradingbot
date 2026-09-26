"""Mission §7/§13: archive population semantics, lineage, append-only memory."""

from __future__ import annotations

import json
import sqlite3

import pytest

from trading_bot.recursive_self_improvement.archive import ParetoArchive
from trading_bot.recursive_self_improvement.memory import ImprovementMemory


def _rec(archive, gid, parent, net, dd, verdict="eligible_for_operator_review",
         role="challenger", cell="all", fingerprint=None):
    return archive.record_candidate(
        genome_id=gid, parent_id=parent, contract_hash="c1", dataset_hash="d1",
        strategy_family="mean_reversion",
        metric_vector={"net_return": net, "max_drawdown": dd, "cvar_95": dd,
                       "turnover": 1.0},
        delta={"net_return": net}, verdict=verdict, role=role,
        regime_cell=cell, extra={"fingerprint": fingerprint or gid})


def test_archive_append_and_frontier(tmp_path):
    a = ParetoArchive(tmp_path / "archive.jsonl")
    _rec(a, "g1", "baseline", 0.01, 0.02)
    _rec(a, "g2", "baseline", 0.02, 0.05)   # better net, worse dd -> frontier
    _rec(a, "g3", "baseline", 0.005, 0.06)  # dominated by both
    frontier = {r["genome_id"] for r in a.frontier(["net_return", "max_drawdown"])}
    assert frontier == {"g1", "g2"}


def test_archive_lineage_three_generations(tmp_path):
    a = ParetoArchive(tmp_path / "archive.jsonl")
    _rec(a, "g1", "baseline", 0.01, 0.01, fingerprint="fp1")
    _rec(a, "g2", "fp1", 0.02, 0.01, fingerprint="fp2")
    _rec(a, "g3", "fp2", 0.03, 0.02, fingerprint="fp3")
    chain = a.lineage("g3")
    assert [r["genome_id"] for r in chain] == ["g1", "g2", "g3"]


def test_failed_candidates_retained(tmp_path):
    a = ParetoArchive(tmp_path / "archive.jsonl")
    _rec(a, "bad", "baseline", -0.5, 0.9, verdict="rejected",
         role="failed_informative")
    assert a.by_id("bad")["verdict"] == "rejected"
    # and they are NOT live members
    assert all(m["genome_id"] != "bad" for m in a.live_members())


def test_champion_relabel_is_append_only(tmp_path):
    a = ParetoArchive(tmp_path / "archive.jsonl")
    _rec(a, "old", "baseline", 0.01, 0.01, role="champion")
    _rec(a, "new", "fp_old", 0.02, 0.01, role="champion")
    a.record_role("old", "ancestor", "superseded")
    assert a.champion()["genome_id"] == "new"
    # old record untouched on disk
    first = json.loads((tmp_path / "archive.jsonl").read_text().splitlines()[0])
    assert first["role"] == "champion"  # original record immutable


def test_archive_chain_detects_tampering(tmp_path):
    p = tmp_path / "archive.jsonl"
    a = ParetoArchive(p)
    _rec(a, "g1", "baseline", 0.01, 0.01)
    lines = p.read_text().splitlines()
    rec = json.loads(lines[0])
    rec["verdict"] = "rejected"  # tamper with stored payload
    p.write_text(json.dumps(rec) + "\n")
    with pytest.raises(ValueError):
        ParetoArchive(p)


def test_memory_evidence_ledger_append_only(tmp_path):
    m = ImprovementMemory(str(tmp_path / "mem.db"))
    h = m.append_evidence(trial_id="t1", nonce="n1",
                          payload={"ok": True}, status="eligible_for_operator_review")
    assert h and m.verify_evidence_chain()
    with sqlite3.connect(str(tmp_path / "mem.db")) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE evidence_ledger SET status='x' WHERE trial_id='t1'")
    with sqlite3.connect(str(tmp_path / "mem.db")) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("DELETE FROM evidence_ledger WHERE trial_id='t1'")
    # duplicates rejected
    with pytest.raises(sqlite3.IntegrityError):
        m.append_evidence(trial_id="t1", nonce="n2", payload={})
