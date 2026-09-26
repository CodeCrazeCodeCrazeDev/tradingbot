"""RSI reachability inventory (read-only audit tool).

Proves which self-improvement/evolution/learning modules are actually
importable from the live entry points, rather than assuming that a file or
class implies functionality. Uses `git ls-files` / `git grep` (fast on this
tree; plain recursive grep times out) and a lazy AST import-BFS starting at
the proven runtime entry points.

Outputs RSI_REACHABILITY_INVENTORY.json at the repo root and prints a
markdown classification table.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Modules being audited (dotted names -> repo path stems).
TARGETS = {
    "trading_bot.recursive_self_improvement": "trading_bot/recursive_self_improvement",
    "trading_bot.recursive_improvement": "trading_bot/recursive_improvement",
    "trading_bot.eternal_evolution": "trading_bot/eternal_evolution",
    "trading_bot.alpha_evolve": "trading_bot/alpha_evolve",
    "trading_bot.autonomous_learner": "trading_bot/autonomous_learner",
    "trading_bot.adaptive_systems": "trading_bot/adaptive_systems",
    "trading_bot.meta_learning": "trading_bot/meta_learning",
    "trading_bot.evolution_layer": "trading_bot/evolution_layer",
    "trading_bot.evaluation": "trading_bot/evaluation",
    "trading_bot.code_evolver": "trading_bot/code_evolver.py",
    "trading_bot.auto_optimizer": "trading_bot/auto_optimizer.py",
    "trading_bot.auto_rollback": "trading_bot/auto_rollback.py",
    "trading_bot.continual_learner": "trading_bot/continual_learner.py",
    "trading_bot.self_learning": "trading_bot/self_learning.py",
    "trading_bot.ai_learner": "trading_bot/ai_learner.py",
    "trading_bot.experiment_tracker": "trading_bot/experiment_tracker.py",
    "trading_bot.optimization": "trading_bot/optimization.py",
    "trading_bot.performance_optimizer": "trading_bot/performance_optimizer.py",
    "trading_bot.governance.evolution_gate": "trading_bot/governance/evolution_gate.py",
}

ENTRY_POINTS = ["main.py", "bot_cli.py", "trading_bot/unified_bot.py",
                "trading_bot/foundation/runtime.py"]

PLACEHOLDER_RE = re.compile(
    r"NotImplementedError|TODO|placeholder|mock_|synthetic|fake_|hard.?coded|pass\s*(#.*)?$",
    re.IGNORECASE | re.MULTILINE,
)
CAPITAL_RE = re.compile(r"place_order|order_send|execute_trade|submit_order|send_order")
DEPLOY_RE = re.compile(r"deploy|promote|production|live_", re.IGNORECASE)


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT)] + list(args),
        capture_output=True, text=True, check=True,
    ).stdout


def list_py_files() -> list[str]:
    return [f for f in git("ls-files", "*.py").splitlines() if f.strip()]


def module_of(path: str) -> str:
    if path.endswith("/__init__.py"):
        return path[: -len("/__init__.py")].replace("/", ".")
    return path[: -len(".py")].replace("/", ".")


def file_for_module(mod: str, files_set: set[str]) -> str | None:
    path = mod.replace(".", "/")
    if path + ".py" in files_set:
        return path + ".py"
    if path + "/__init__.py" in files_set:
        return path + "/__init__.py"
    return None


def parse_imports(path: str) -> list[str]:
    """Return dotted module names imported by a repo-relative .py file."""
    try:
        tree = ast.parse(Path(ROOT, path).read_bytes(), filename=path)
    except (SyntaxError, ValueError, OSError, UnicodeDecodeError):
        return []
    mods: list[str] = []
    pkg = module_of(path)
    base = pkg if path.endswith("/__init__.py") else pkg.rpartition(".")[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            level = node.level or 0
            if level == 0:
                mods.append(node.module or "")
            else:
                parts = base.split(".")
                anchor = ".".join(parts[: max(0, len(parts) - level + 1)])
                mods.append(f"{anchor}.{node.module}" if node.module else anchor)
                # `from . import sub` needs the anchor itself recorded too.
                if not node.module:
                    for alias in node.names:
                        mods.append(f"{anchor}.{alias.name}")
    return mods


def reachable_from(entries: list[str], files_set: set[str]) -> set[str]:
    """BFS over in-repo import edges starting at the entry files."""
    seen: set[str] = set()
    queue: deque[str] = deque()
    for entry in entries:
        if entry in files_set:
            queue.append(module_of(entry))
            seen.add(module_of(entry))
    while queue:
        mod = queue.popleft()
        f = file_for_module(mod, files_set)
        if f is None:
            continue
        for imported in parse_imports(f):
            if not imported.startswith("trading_bot"):
                continue
            # Resolve the deepest resolvable prefix (e.g. `trading_bot.a.b`
            # may be a class inside `trading_bot/a.py`).
            parts = imported.split(".")
            for i in range(len(parts), 1, -1):
                cand = ".".join(parts[:i])
                if file_for_module(cand, files_set):
                    if cand not in seen:
                        seen.add(cand)
                        queue.append(cand)
                    break
    return seen


def importers_of(needle: str, py_files: list[str]) -> dict[str, list[str]]:
    """Map repo file -> matched import strings, for files mentioning needle."""
    pat = re.escape(needle.replace("trading_bot.", "").replace(".", r"[./]"))
    grep_pat = rf"(trading_bot[. ]{pat}|from \.\S*{needle.rpartition('.')[-1]}|import {needle.rpartition('.')[-1]})"
    try:
        out = git("grep", "-l", "-E", grep_pat, "--", "*.py")
    except subprocess.CalledProcessError:
        return {}
    result: dict[str, list[str]] = {}
    for f in out.splitlines():
        if f.strip() and f in py_files:
            result.setdefault(f, [])
    for f in list(result):
        for mod in parse_imports(f):
            if mod == needle or mod.startswith(needle + "."):
                result[f].append(mod)
    return {k: v for k, v in result.items() if v}


def classify(path_exists: bool, runtime_reachable: bool, test_reachable: bool,
             cli_entrypoint: bool, importers: dict, content: str) -> str:
    if not path_exists:
        return "MISSING"
    if runtime_reachable:
        if CAPITAL_RE.search(content) and DEPLOY_RE.search(content):
            return "UNSAFE"
        return "ACTIVE"
    if not importers:
        return "DEAD"
    if test_reachable:
        return "DISCONNECTED"
    if len(PLACEHOLDER_RE.findall(content)) > len(content.splitlines()) * 0.05:
        return "PLACEHOLDER"
    return "DISCONNECTED"


def main() -> int:
    py_files = list_py_files()
    files_set = set(py_files)
    modules = {module_of(f): f for f in py_files}
    tests = {m: f for m, f in modules.items() if f.startswith("tests/")}

    runtime_reach = reachable_from(ENTRY_POINTS, files_set)
    test_reach: dict[str, set[str]] = {}
    # Which target modules any test file imports (direct, cheap check).
    for tmod, tfile in tests.items():
        for imported in parse_imports(tfile):
            for target in TARGETS:
                if imported == target or imported.startswith(target + "."):
                    test_reach.setdefault(target, set()).add(tfile)

    report = {"generated_by": "scripts/rsi_reachability_inventory.py",
              "entry_points": ENTRY_POINTS,
              "runtime_reachable_module_count": len(runtime_reach),
              "targets": {}}

    rows = []
    for dotted, stem in sorted(TARGETS.items()):
        exists = stem in files_set or (stem + "/__init__.py") in files_set
        init_file = (stem + "/__init__.py") if stem.endswith(".py") is False else stem
        importers = importers_of(dotted, files_set)
        content = ""
        for candidate in (stem, init_file):
            if candidate in files_set:
                try:
                    content = Path(ROOT, candidate).read_text(
                        encoding="utf-8", errors="replace")
                except OSError:
                    content = ""
                break
        # Package: concatenate all member file contents for heuristics.
        if exists and not stem.endswith(".py"):
            content = "".join(
                Path(ROOT, f).read_text(encoding="utf-8", errors="replace")
                for f in py_files if f.startswith(stem + "/") and f.endswith(".py")
            )
        in_runtime = any(m == dotted or m.startswith(dotted + ".")
                         for m in runtime_reach)
        test_hit = dotted in test_reach
        cli = any(f.rsplit("/", 1)[-1] in ("main.py", "bot_cli.py", "run.py")
                  for f in importers)
        cls = classify(exists, in_runtime, test_hit, cli, importers, content)
        entry = {
            "path": stem,
            "exists": exists,
            "classification": cls,
            "runtime_reachable": in_runtime,
            "test_reachable": test_hit,
            "test_files": sorted(test_reach.get(dotted, ())),
            "importers": sorted(importers),
            "importer_count": len(importers),
        }
        report["targets"][dotted] = entry
        rows.append((dotted, cls, in_runtime, len(importers),
                     ", ".join(sorted(os.path.basename(t) for t in
                                      test_reach.get(dotted, ()))[:3])))

    out = ROOT / "RSI_REACHABILITY_INVENTORY.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("| Module | Classification | Runtime-reachable | Importers | Tests |")
    print("|---|---|---|---|---|")
    for dotted, cls, reach, n, t in rows:
        print(f"| `{dotted}` | {cls} | {'yes' if reach else 'no'} | {n} | {t or '—'} |")
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
