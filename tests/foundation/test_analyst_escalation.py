"""Analyst->hunter escalation: WATCH near-miss specs earn a harder
second look; everything else stays parked."""

from scripts.autonomous_cycle import watch_escalation_specs


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
