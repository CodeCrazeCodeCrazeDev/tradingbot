"""Analyst->hunter escalation + data-need queue tests."""

import json

from scripts.autonomous_cycle import (
    merge_data_requests, watch_escalation_specs)


def _spec(sid="s1", family="momentum"):
    return {"spec_id": sid, "family": family,
            "params": {"lookback": 10}, "hypothesis": "h"}


def _entry(sid, klass, near_miss, spec=None):
    return {"spec_id": sid, "classification": klass,
            "near_miss_datasets": near_miss, "spec": spec}


def test_near_miss_watch_escalates():
    q = {"specs": [_entry("s1", "WATCH", ["db:EURUSD:D1"], _spec())]}
    out = watch_escalation_specs(q, 3)
    assert len(out) == 1 and out[0]["spec_id"] == "s1"


def test_watch_without_near_miss_stays_parked():
    # fragile/dead-ish WATCH (like ext_momentum_0) must NOT burn eval
    # budget — only genuine near-misses escalate
    q = {"specs": [_entry("s1", "WATCH", [], _spec())]}
    assert watch_escalation_specs(q, 3) == []


def test_dead_and_promote_do_not_escalate():
    q = {"specs": [
        _entry("d1", "DEAD", ["x"], _spec("d1")),
        _entry("p1", "PROMOTE_CANDIDATE", ["x"], _spec("p1")),
    ]}
    assert watch_escalation_specs(q, 3) == []


def test_cap_and_missing_spec():
    q = {"specs": [
        _entry("s1", "WATCH", ["x"], _spec("s1")),
        _entry("s2", "WATCH", ["x"], _spec("s2")),
        _entry("s3", "WATCH", ["x"], None),  # no spec dict -> skip
        _entry("s4", "WATCH", ["x"], _spec("s4")),
    ]}
    out = watch_escalation_specs(q, 2)
    assert [s["spec_id"] for s in out] == ["s1", "s2"]


def test_zero_cap_disables():
    q = {"specs": [_entry("s1", "WATCH", ["x"], _spec())]}
    assert watch_escalation_specs(q, 0) == []


def _eval(sid, fam, datasets):
    return {"spec_id": sid, "family": fam, "datasets": datasets}


def test_data_requests_needs_pair_and_data(tmp_path):
    qpath = tmp_path / "data_requests.json"
    evals = [
        _eval("p1", "stat_arb", [{"status": "needs_pair",
                                  "reason": "spec.pair required"}]),
        _eval("m1", "momentum", [{"dataset": "fx_data.db:EURUSD:D1",
                                  "status": "insufficient_bars",
                                  "bars": 30}]),
        _eval("ok", "meanrev", [{"dataset": "a.db:X:M15",
                                 "verdict": "rejected"}]),
    ]
    n = merge_data_requests(evals, qpath)
    assert n == 2  # rejected eval emits nothing
    q = json.loads(qpath.read_text())
    kinds = {r["kind"] for r in q["requests"].values()}
    assert kinds == {"spec_completion", "data"}


def test_data_requests_dedup_and_count(tmp_path):
    qpath = tmp_path / "data_requests.json"
    e = _eval("m1", "momentum", [{"dataset": "d.db:X:D1",
                                  "status": "load_error",
                                  "reason": "missing table"}])
    merge_data_requests([e], qpath)
    merge_data_requests([e], qpath)
    q = json.loads(qpath.read_text())
    assert len(q["requests"]) == 1
    r = next(iter(q["requests"].values()))
    assert r["count"] == 2 and r["kind"] == "data"
