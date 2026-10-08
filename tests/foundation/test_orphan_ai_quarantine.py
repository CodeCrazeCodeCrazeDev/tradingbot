"""Orphan-AI quarantine boundary — the structural form of "one AI".

Physical relocation of the ~40 orphan AI directories is unsafe: they are
referenced by dozens of test files, sibling orphans, the legacy
``main_v1`` entrypoint, and even live imports (``unified_bot`` ->
``world_model``). Quarantine-in-place is the established convention
(``test_brain_quarantine.py``): files stay for research, but the
canonical one-brain path may not reach them except through the advisory
seam, where authority fields are stripped.

This test enforces exactly that, against the manifest that is the audit
map — ``advisory.UNWIRED_ORPHAN_MODULES`` and the attached factories.
"""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

CANONICAL_GLOBS = (
    "trading_bot/foundation/**/*.py",
    "trading_bot/core/csc/**/*.py",
    "trading_bot/cognition/**/*.py",
    "trading_bot/interfaces/**/*.py",
)
CANONICAL_FILES = (
    "main.py",
    "trading_bot/unified_bot.py",
    "trading_bot/foundation/runtime.py",
)

# The advisory seam is the sanctioned place to import orphan/legacy AI
# modules — AdvisoryModuleAdapter strips authority fields before any
# output reaches the evidence channel.
ADVISORY_SEAM = {
    "trading_bot/core/csc/advisory.py",
    "trading_bot/core/csc/assembly.py",
}

# Attached orphans are legitimately reachable through the seam — every
# directory with at least one DEFAULT_ADVISORY_FACTORIES adapter.
ATTACHED_ORPHAN_ROOTS = {
    "agents", "market_intelligence", "agents2", "core_agent_system",
    "intelligence_core", "adversarial_decision", "alphaalgo_core",
    "alpha_research", "alphaalgo_institutional", "brain",
    "cognitive_architecture", "elite_ai_system", "adaptive_systems",
    "intelligence", "self_learning", "signal_discovery", "tamic",
    "self_diagnostic", "aletheia_autonomous", "superintelligence",
    "systems_ai", "advanced_intelligence", "improvement_agent",
    "neural_integration", "radar_ai", "self_concepts", "self_healing_ai",
    "self_mastery", "sentient_core", "superpowerful_ai", "ai", "ai_core",
    "aads", "aamis_v3", "autonomous_learner", "explainability",
}

from trading_bot.core.csc.advisory import (  # noqa: E402
    LIVE_IMPORTED_NON_ADVISORY, UNWIRED_ORPHAN_MODULES)

QUARANTINED_ORPHAN_ROOTS = {name for name, _ in UNWIRED_ORPHAN_MODULES}
LIVE_NON_ADVISORY_ROOTS = {name for name, _ in LIVE_IMPORTED_NON_ADVISORY}


def _iter_canonical_files():
    seen = set()
    for rel in CANONICAL_FILES:
        p = ROOT / rel
        if p.exists():
            seen.add(p)
    for pattern in CANONICAL_GLOBS:
        for p in ROOT.glob(pattern):
            if p.is_file() and "__pycache__" not in str(p):
                seen.add(p)
    return sorted(seen)


def _imported_modules(path: Path):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _orphan_root(mod: str):
    parts = mod.split(".")
    if len(parts) >= 2 and parts[0] == "trading_bot":
        return parts[1]
    return None


@pytest.mark.parametrize("quarantined", sorted(QUARANTINED_ORPHAN_ROOTS))
def test_canonical_path_never_imports_quarantined_orphan(quarantined):
    if quarantined in ATTACHED_ORPHAN_ROOTS:
        pytest.skip("attached via the advisory seam")
    offenders = []
    for path in _iter_canonical_files():
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        if rel in ADVISORY_SEAM:
            continue
        for mod in _imported_modules(path):
            if _orphan_root(mod) == quarantined:
                offenders.append(f"{rel} imports {mod}")
    assert offenders == [], (
        f"canonical one-brain path reaches quarantined orphan "
        f"{quarantined!r} outside the advisory seam: {offenders}")


def test_manifest_covers_every_ai_named_dir():
    """Every AI-named top-level dir under trading_bot/ is either attached,
    live-imported, or declared unwired — no silent gaps in the audit map."""
    classified = (
        QUARANTINED_ORPHAN_ROOTS
        | LIVE_NON_ADVISORY_ROOTS
        | ATTACHED_ORPHAN_ROOTS
        | {"cognition", "alpha_algo"}  # canonical advisory stack
    )
    canonical = {"core", "cognition", "evolution_layer", "verification",
                 "research", "recursive_self_improvement", "foundation",
                 "execution", "risk", "evaluation", "persistence"}
    # Name-heuristic false positives: not AI modules.
    not_ai = {"blockchain", "meta_governance"}
    classified |= not_ai
    ai_markers = ("ai", "intelligen", "cognit", "agent", "brain",
                  "learn", "neural", "sentien", "meta_")
    uncovered = []
    for d in sorted((ROOT / "trading_bot").iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        name = d.name
        if name in classified or name in canonical:
            continue
        if any(m in name for m in ai_markers):
            uncovered.append(name)
    assert uncovered == [], (
        f"AI-named dirs missing from the quarantine manifest: {uncovered}")


def test_manifest_covers_every_root_file():
    """Every loose ``trading_bot/*.py`` module is classified — wired
    through the advisory seam (declared with an 'attached' reason),
    explicitly unwired with a concrete reason, or canonical. No silent
    gaps at file granularity."""
    canonical_files = {"__init__.py", "unified_bot.py", "main.py",
                       # canonical read-model facade over the CSC
                       "ai_stack.py"}
    uncovered = []
    for p in sorted((ROOT / "trading_bot").glob("*.py")):
        if p.name in canonical_files:
            continue
        if p.name not in QUARANTINED_ORPHAN_ROOTS:
            uncovered.append(p.name)
    assert uncovered == [], (
        f"root modules missing from the quarantine manifest: {uncovered}")
