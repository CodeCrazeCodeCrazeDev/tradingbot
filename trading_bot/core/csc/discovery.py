"""Interface/dependency-driven module discovery and wiring plan.

The existing advisory manifest (``advisory.py``) is a static audit map
and ``discover_advisory_callables`` probes orphans by convention. This
module adds the missing layer: modules *declare* what they provide and
what they need, and the wiring order is computed from the dependency
graph — discovered by scanning source, never by importing it.

Contract: a module opts in by assigning a top-level literal

    CSC_MANIFEST = {
        "id": "my_service",            # required, unique
        "kind": "advisory",            # advisory | infrastructure
        "provides": ["regime"],        # interface names it implements
        "requires": ["market_data"],   # interfaces it needs wired first
        "factory": "pkg.mod:make",     # dotted path to a 0-arg factory
        "status": "candidate",         # candidate | verified
    }

Rules — same governance as the rest of the CSC:

- Scanning is AST-only. ``trading_bot/__init__`` costs minutes to
  import and concurrent-edit hazards are documented; a manifest is
  data, and data can be read without executing the module.
- A manifest must be a ``ast.literal_eval``-able dict. A
  ``def csc_manifest()`` (dynamic) is reported as ``dynamic`` and
  deferred to the existing runtime probe — never imported by the scan.
- ``kind=advisory`` nodes wire into the advisory electorate (they
  start SHADOW under self_wiring). ``kind=infrastructure`` wires to
  ``configure_*`` seams only. The authority chain is unreachable:
  ids in ``self_wiring.INVARIANT_IDS`` and factories under the
  protected paths are rejected at plan time, not at attach time.
- Missing requires -> node marked ``blocked`` with the gap recorded.
  Cycles -> all members reported, none wired. Duplicated ids -> the
  second is ``conflict``. The plan is always constructible — nothing
  raises on bad input.

Usage:
    plan = scan_packages([ROOT / "trading_bot"])
    plan.execute(csc)   # imports ONLY resolved factories, in dep order
"""

from __future__ import annotations

import ast
import importlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .self_wiring import INVARIANT_IDS

logger = logging.getLogger(__name__)

_MANIFEST_KEYS = ("CSC_MANIFEST", "AGENT_MANIFEST")
_PROTECTED_PREFIXES = (
    "trading_bot/risk", "trading_bot/core/immutable_shield",
    "trading_bot/execution", "trading_bot/unified_bot", "main.py",
    "trading_bot/recursive_self_improvement",
)


@dataclass
class Manifest:
    id: str
    kind: str
    provides: Tuple[str, ...]
    requires: Tuple[str, ...]
    factory: str
    status: str
    source: str                       # file the manifest was read from


@dataclass
class PlanNode:
    manifest: Manifest
    state: str = "pending"            # pending|ready|blocked|conflict
    reason: str = ""


@dataclass
class WiringPlan:
    ordered: List[Manifest] = field(default_factory=list)
    blocked: List[PlanNode] = field(default_factory=list)
    conflicts: List[PlanNode] = field(default_factory=list)
    cycles: List[List[str]] = field(default_factory=list)
    dynamic: List[str] = field(default_factory=list)
    scanned: int = 0

    def execute(self, csc: Any, attach_fn=None) -> Dict[str, Any]:
        """Import resolved factories in dependency order and attach.
        Every callable error is recorded, never raised — one bad
        module cannot break the loop."""
        attached, failed = [], {}
        for m in self.ordered:
            try:
                mod_name, _, attr = m.factory.partition(":")
                mod = importlib.import_module(mod_name)
                factory = getattr(mod, attr or "csc_manifest")
                svc = factory()
                (attach_fn or csc.configure_cognition)(svc)
                attached.append(m.id)
            except Exception as exc:  # noqa: BLE001
                failed[m.id] = str(exc)
                logger.warning("wire %s failed: %s", m.id, exc)
        return {"attached": attached, "failed": failed}


def _literal_manifest(tree: ast.Module) -> Optional[dict]:
    for node in tree.body:
        tgt = None
        if isinstance(node, ast.Assign):
            tgt = node.targets[0] if len(node.targets) == 1 else None
            val = node.value
        elif isinstance(node, ast.AnnAssign):
            tgt, val = node.target, node.value
        else:
            continue
        if (isinstance(tgt, ast.Name) and tgt.id in _MANIFEST_KEYS
                and isinstance(val, ast.Dict)):
            try:
                return ast.literal_eval(val)
            except (ValueError, SyntaxError):
                return {"_unparseable": True}
    return None


def _has_dynamic(tree: ast.Module) -> bool:
    return any(isinstance(n, ast.FunctionDef)
               and n.name == "csc_manifest" for n in tree.body)


def _protected_source(rel: str) -> bool:
    """Match a protected path anywhere in the relative path — scan
    roots vary (repo root, tmp dirs) but 'trading_bot/risk' is
    protected wherever it appears."""
    rel = rel.replace("\\", "/")
    tail = "/" + rel
    for p in _PROTECTED_PREFIXES:
        if (tail.startswith("/" + p + "/") or tail.endswith("/" + p)
                or rel == p):
            return True
    return False


def _manifest_from(d: dict, source: str) -> Optional[Manifest]:
    mid = d.get("id")
    if not isinstance(mid, str) or not mid:
        return None
    if mid in INVARIANT_IDS or _protected_source(source):
        return None
    kind = d.get("kind", "advisory")
    if kind not in ("advisory", "infrastructure"):
        kind = "advisory"
    return Manifest(
        id=mid, kind=kind,
        provides=tuple(d.get("provides") or ()),
        requires=tuple(d.get("requires") or ()),
        factory=str(d.get("factory", "")),
        status=str(d.get("status", "candidate")),
        source=source)


def scan_packages(roots, glob: str = "**/*.py") -> WiringPlan:
    """AST-scan roots for CSC_MANIFEST literals -> WiringPlan."""
    nodes: Dict[str, PlanNode] = {}
    plan = WiringPlan()
    for root in roots:
        root = Path(root)
        if not root.exists():
            continue
        for f in root.rglob(glob):
            if "__pycache__" in f.parts or f.name.startswith("test_"):
                continue
            plan.scanned += 1
            try:
                tree = ast.parse(f.read_text(encoding="utf-8",
                                             errors="replace"))
            except SyntaxError:
                continue
            rel = str(f.relative_to(root)).replace("\\", "/")
            if _protected_source(rel):
                continue
            d = _literal_manifest(tree)
            if d is None:
                if _has_dynamic(tree):
                    plan.dynamic.append(rel)
                continue
            if d.get("_unparseable"):
                plan.dynamic.append(rel)
                continue
            m = _manifest_from(d, rel)
            if m is None:
                continue
            node = PlanNode(manifest=m)
            if m.id in nodes:
                node.state, node.reason = "conflict", m.id
                plan.conflicts.append(node)
                continue
            nodes[m.id] = node

    # topological order over provides/requires (Kahn)
    provided_by: Dict[str, str] = {}
    for nid, n in nodes.items():
        for p in n.manifest.provides:
            provided_by.setdefault(p, nid)
    deps: Dict[str, List[str]] = {}
    for nid, n in nodes.items():
        deps[nid] = []
        for req in n.manifest.requires:
            src = provided_by.get(req)
            if src is None:
                n.state, n.reason = "blocked", f"missing:{req}"
                plan.blocked.append(n)
                break
            if src != nid:
                deps[nid].append(src)

    indeg = {nid: len(deps[nid]) for nid in nodes
             if nodes[nid].state != "blocked"}
    ready = sorted(n for n, d in indeg.items() if d == 0)
    order: List[str] = []
    while ready:
        nid = ready.pop(0)
        order.append(nid)
        for other, ds in deps.items():
            if nid in ds:
                indeg[other] -= 1
                if indeg[other] == 0:
                    ready.append(other)
    cyclic = [n for n in indeg if indeg[n] > 0]
    if cyclic:
        plan.cycles.append(sorted(cyclic))
    # topo order already respects deps — manifests without a factory
    # are declarations only (report, nothing to instantiate)
    plan.ordered = [nodes[n].manifest for n in order
                    if nodes[n].manifest.factory]
    return plan
