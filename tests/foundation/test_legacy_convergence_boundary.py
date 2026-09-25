"""Boundary tests for the Wave-0 legacy convergence manifest.

The scanner (trading_bot.foundation.legacy_convergence) classifies every live
module and records which are reachable from the canonical composition root.
These tests make the manifest actionable: a module only counts as converged if
no *reachable* module is quarantined and no reachable module holds an
undeclared capital path.
"""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "ARCHITECTURE_LEGACY_CLASSIFICATION.json"

EXECUTION_BOUNDARY_PARTS = (
    "trading_bot/execution/",
    "trading_bot/broker/",
    "trading_bot/brokers/",
)


@pytest.fixture(scope="module")
def manifest() -> dict:
    if not MANIFEST.exists():
        pytest.skip("legacy convergence manifest not generated")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _execution_boundary_allowed(path: str) -> bool:
    from trading_bot.foundation.legacy_convergence import EXECUTION_BOUNDARY_PATHS

    return path in EXECUTION_BOUNDARY_PATHS or any(
        part in path for part in EXECUTION_BOUNDARY_PARTS
    )


def test_no_reachable_module_is_quarantined(manifest: dict) -> None:
    reachable_quarantined = [
        m["path"]
        for m in manifest["modules"]
        if m["runtime_reachable"] and m["classification"] == "quarantine"
    ]
    assert reachable_quarantined == []


def test_no_reachable_module_has_undeclared_capital_path(manifest: dict) -> None:
    offenders = [
        m["path"]
        for m in manifest["modules"]
        if m["runtime_reachable"]
        and m["direct_capital_path"]
        and not _execution_boundary_allowed(m["path"])
    ]
    assert offenders == []


def test_declared_canonical_authorities_exist_on_disk(manifest: dict) -> None:
    missing = [
        path
        for path in manifest["canonical_authorities"]
        if not (ROOT / path).exists()
    ]
    assert missing == []


def test_manifest_is_fresh_against_source_tree(manifest: dict) -> None:
    """Every file the manifest calls reachable must still exist."""
    missing = [
        m["path"]
        for m in manifest["modules"]
        if m["runtime_reachable"] and not (ROOT / m["path"]).exists()
    ]
    assert missing == []
