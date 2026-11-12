"""Network-free tests for csc.discovery — AST manifest scan, dep-graph
topo wiring, blocked/conflict/cycle/invariant handling. No imports of
scanned code ever happen — manifests are literals read from source."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from trading_bot.core.csc.discovery import scan_packages  # noqa: E402


def _write(root: Path, rel: str, text: str):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _manifest(mid, kind="advisory", provides=(), requires=(),
              factory="m:f", status="candidate"):
    return (
        "CSC_MANIFEST = {\n"
        f'    "id": "{mid}",\n'
        f'    "kind": "{kind}",\n'
        f'    "provides": {list(provides)!r},\n'
        f'    "requires": {list(requires)!r},\n'
        f'    "factory": "{factory}",\n'
        f'    "status": "{status}",\n'
        "}\n")


def test_scan_orders_by_dependency(tmp_path):
    _write(tmp_path, "pkg/b.py", _manifest(
        "b", provides=["market_data"], factory="pkg.b:make"))
    _write(tmp_path, "pkg/a.py", _manifest(
        "a", provides=["regime"], requires=["market_data"],
        factory="pkg.a:make"))
    _write(tmp_path, "pkg/c.py", _manifest(
        "c", requires=["regime"], factory="pkg.c:make"))
    plan = scan_packages([tmp_path])
    ids = [m.id for m in plan.ordered]
    assert ids == ["b", "a", "c"]
    assert not plan.blocked and not plan.cycles


def test_missing_require_is_blocked_not_wired(tmp_path):
    _write(tmp_path, "pkg/x.py", _manifest(
        "x", requires=["nonexistent_iface"], factory="pkg.x:make"))
    plan = scan_packages([tmp_path])
    assert plan.ordered == []
    assert plan.blocked[0].reason == "missing:nonexistent_iface"


def test_cycle_reported_not_wired(tmp_path):
    _write(tmp_path, "pkg/a.py", _manifest(
        "a", provides=["p_a"], requires=["p_b"]))
    _write(tmp_path, "pkg/b.py", _manifest(
        "b", provides=["p_b"], requires=["p_a"]))
    plan = scan_packages([tmp_path])
    assert sorted(plan.cycles[0]) == ["a", "b"]
    assert plan.ordered == []


def test_invariant_and_protected_rejected(tmp_path):
    _write(tmp_path, "pkg/evil.py", _manifest("risk", factory="pkg.evil:make"))
    _write(tmp_path, "trading_bot/risk/x.py", _manifest("legit_looking"))
    plan = scan_packages([tmp_path])
    assert plan.ordered == []
    assert not plan.blocked  # silently excluded, not an error


def test_duplicate_id_conflicts(tmp_path):
    _write(tmp_path, "pkg/a.py", _manifest("dup", provides=["i1"]))
    _write(tmp_path, "pkg/b.py", _manifest("dup", provides=["i2"]))
    plan = scan_packages([tmp_path])
    assert len(plan.conflicts) == 1
    assert len(plan.ordered) == 1  # first wins


def test_dynamic_manifest_deferred_not_imported(tmp_path):
    _write(tmp_path, "pkg/dyn.py",
           "def csc_manifest():\n    return {'id': 'dyn'}\n")
    plan = scan_packages([tmp_path])
    assert plan.ordered == []
    assert plan.dynamic == ["pkg/dyn.py"]


def test_broken_source_never_raises(tmp_path):
    _write(tmp_path, "pkg/bad.py", "def broken(:\n")
    _write(tmp_path, "pkg/good.py", _manifest("good"))
    plan = scan_packages([tmp_path])
    assert [m.id for m in plan.ordered] == ["good"]


def test_factoryless_manifest_is_declaration_only(tmp_path):
    _write(tmp_path, "pkg/spec.py", _manifest("spec", factory=""))
    plan = scan_packages([tmp_path])
    assert plan.ordered == []
