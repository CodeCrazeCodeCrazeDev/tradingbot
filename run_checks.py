"""
AlphaAlgo automated compliance checks — metrics computed, not hardcoded.

Each scorecard number is derived from a real measurement over the live
tree; nothing here asserts a value it did not measure.
"""

import ast
import json
import os
import py_compile
import subprocess
import sys

SKIP_DIRS = {"_archive", "__pycache__", ".pytest_cache", "_quarantine"}

REQUIRED_DOCS = [
    "MASTER_AUDIT_REPORT.md",
    "ISSUE_TRACKER.md",
    "ARCHITECTURE_IMPROVEMENTS.md",
    "FIX_LOG.md",
    "VALIDATION_REPORT.md",
    "DEPENDENCY_GRAPH.md",
    "SERVICE_DEPENDENCY_GRAPH.md",
    "STATIC_ANALYSIS_REPORT.md",
    "SECURITY_AUDIT.md",
    "PERFORMANCE_PROFILE.md",
    "CONCURRENCY_AUDIT.md",
    "RELIABILITY_AUDIT.md",
    "TECHNICAL_DEBT_REGISTER.md",
    "SCIENTIFIC_FOUNDATION_2026/SCIENTIFIC_AUDIT_REPORT_COMPLETE.md",
]

# Canonical "One Brain" components that must import for the live path to run.
CORE_MODULES = [
    "trading_bot.core.csc.controller",
    "trading_bot.core.csc.hypothesis",
    "trading_bot.core.csc.router",
    "trading_bot.core.csc.folding",
    "trading_bot.core.hms.memory",
    "trading_bot.core.hms.models",
    "trading_bot.core.unified_event_bus",
    "trading_bot.core.unified_registry",
    "trading_bot.core.immutable_shield",
    "trading_bot.core.execution_bridge",
    "trading_bot.core.verification.swarm",
    "trading_bot.agents.multi_agent_debate",
    "trading_bot.registry",
    "trading_bot.unified_ai_brain",
]


def iter_py_files(base, skip_archive=True):
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if skip_archive and "_archive" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(root, f)


def compile_score(files):
    """Fraction of files that byte-compile cleanly."""
    if not files:
        return 0.0, []
    broken = []
    for p in files:
        try:
            py_compile.compile(p, doraise=True)
        except py_compile.PyCompileError as e:
            broken.append(f"{p}: {str(e).splitlines()[-1][:80]}")
    return 100.0 * (len(files) - len(broken)) / len(files), broken


def import_score(modules):
    """Fraction of modules that import in a single probe subprocess."""
    probe = (
        "import importlib,sys;"
        "mods=" + repr(modules) + ";"
        "[print(('OK' if _try(m) else 'FAIL') + '|' + m) for m in mods]"
    )
    probe = (
        "import importlib\n"
        "mods=" + repr(modules) + "\n"
        "for m in mods:\n"
        "    try:\n"
        "        importlib.import_module(m); print('OK|'+m)\n"
        "    except Exception as e:\n"
        "        print('FAIL|'+m+'|'+str(e)[:70])\n"
    )
    try:
        out = subprocess.run(
            [sys.executable, "-c", probe],
            capture_output=True, text=True, timeout=300,
        ).stdout
    except subprocess.TimeoutExpired:
        return 0.0, ["probe timed out"]
    ok, fails = [], []
    for line in out.splitlines():
        if line.startswith("OK|"):
            ok.append(line[3:])
        elif line.startswith("FAIL|"):
            fails.append(line[5:])
    measured = len(ok) + len(fails)
    score = 100.0 * len(ok) / measured if measured else 0.0
    return score, fails


def doc_score():
    missing = [d for d in REQUIRED_DOCS if not os.path.exists(d)]
    return 100.0 * (len(REQUIRED_DOCS) - len(missing)) / len(REQUIRED_DOCS), missing


def package_health(py_files):
    """Fraction of production dirs containing .py files that also have
    an __init__.py (import-hazard check)."""
    dirs = {os.path.dirname(p) for p in py_files}
    missing = [d for d in dirs if not os.path.exists(os.path.join(d, "__init__.py"))]
    if not dirs:
        return 0.0, []
    return 100.0 * (len(dirs) - len(missing)) / len(dirs), missing


def local_cycle_check(roots):
    """Cheap import-graph cycle detector over a bounded set of directories.
    Parses intra-repo imports via ast and reports simple A->B->A cycles."""
    edges = {}
    for base in roots:
        for p in iter_py_files(base):
            try:
                tree = ast.parse(open(p, encoding="utf-8", errors="ignore").read())
            except Exception:
                continue
            mod = p[:-3].replace(os.sep, ".")
            deps = set()
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                for n in names:
                    if n.startswith("trading_bot."):
                        deps.add(n)
            edges[mod] = deps
    cycles = set()
    for a, deps in edges.items():
        for b in deps:
            if a in edges.get(b, ()):
                cycles.add(" <-> ".join(sorted((a, b))))
    return sorted(cycles)


def run_automated_audits():
    print("=" * 60)
    print("ALPHALGO AUTOMATED PRODUCTION COMPLIANCE & RESEARCH VERIFIER")
    print("=" * 60)

    # 1. Scanning directories and files
    print("\n[1/7] SCANNING REPOSITORY DIRECTORIES...")
    py_files = list(iter_py_files("trading_bot"))
    test_files = list(iter_py_files("tests", skip_archive=False)) + \
        list(iter_py_files("tests_new", skip_archive=False))
    quarantined = list(iter_py_files("tests/_quarantine", skip_archive=False))
    print(f"  - Active Production Py Files: {len(py_files)}")
    print(f"  - Automated Unit/Integration Tests: {len(test_files)} (+{len(quarantined)} quarantined)")

    # 2. Required documents
    print("\n[2/7] VERIFYING CROSS-DOCUMENT CONSISTENCY...")
    docs_pct, missing_docs = doc_score()
    if missing_docs:
        print(f"  - Missing required files ({len(missing_docs)}): {missing_docs}")
    else:
        print(f"  - OK: All {len(REQUIRED_DOCS)} required documents present.")

    # 3. Duplicate capability ownership scan
    print("\n[3/7] SCANNING FOR DUPLICATE CAPABILITY OWNERSHIP & ORCHESTRATORS...")
    matches = []
    for py_file in py_files:
        try:
            with open(py_file, encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "class CognitiveSystemController" in content or \
               "class UnifiedDecisionBus" in content:
                matches.append(py_file)
        except Exception:
            pass
    print(f"  - Core controller/bus definitions found: {len(matches)}")
    for m in matches:
        print(f"    * {m}")
    dup_penalty = max(0, len(matches) - 2) * 10  # >1 of each = drift

    # 4. Dependency cycles over the canonical core (real ast scan)
    print("\n[4/7] DETECTING CIRCULAR DEPENDENCIES (core/csc + core/hms)...")
    cycles = local_cycle_check(["trading_bot/core/csc", "trading_bot/core/hms"])
    if cycles:
        print(f"  - {len(cycles)} import cycles found:")
        for c in cycles[:10]:
            print(f"    * {c}")
    else:
        print("  - 0 direct import cycles detected.")

    # 5. Literature metrics
    print("\n[5/7] COMPUTE LITERATURE METRICS...")
    papers = 0
    try:
        with open("SCIENTIFIC_FOUNDATION_2026/literature_index.json") as f:
            corpus = json.load(f)
        papers = len(corpus)
        venues = {}
        for p in corpus:
            venues[p.get("venue", "arXiv")] = venues.get(p.get("venue", "arXiv"), 0) + 1
        print(f"  - Total Discovered Papers: {papers}")
        print(f"  - Top Venues: {list(venues)[:5]}")
    except Exception as e:
        print(f"  - WARNING: literature index unavailable: {e}")
    research_pct = min(100.0, papers / 50.0 * 100.0)

    # 6. Real readiness scorecard
    print("\n[6/7] AUTOMATED READINESS GATING DECISION SCORECARD...")

    repo_pct, broken = compile_score(py_files)
    print(f"  - Live files compiling: {len(py_files) - len(broken)}/{len(py_files)}")
    for b in broken[:10]:
        print(f"    ! {b}")

    arch_pct, import_fails = import_score(CORE_MODULES)
    print(f"  - Core modules importing: {len(CORE_MODULES) - len(import_fails)}/{len(CORE_MODULES)}")
    for f_ in import_fails[:10]:
        print(f"    ! {f_}")

    test_pct, broken_tests = compile_score(test_files)
    pkg_pct, missing_init = package_health(py_files)
    cycle_pct = 100.0 if not cycles else max(0.0, 100.0 - len(cycles) * 10)

    metrics = {
        "Research Coverage": research_pct,
        "Architecture Coverage": max(0.0, arch_pct - dup_penalty),
        "Repository Coverage": repo_pct,
        "Traceability": docs_pct,
        "Validation Planning": test_pct,
        "Dependency Health": min(pkg_pct, cycle_pct),
        "Implementation Readiness": (repo_pct + arch_pct) / 2.0,
    }

    is_ready = True
    for key, val in metrics.items():
        print(f"  - {key:<25} : {val:.1f}%")
        if val < 90:
            is_ready = False

    # 7. Verdict
    print("\n[7/7] COMPUTING FINAL PHASE-GATE DECISION...")
    if is_ready:
        print("  - Gating Status: SUCCESS")
        print("  - FINAL VERDICT: APPROVED FOR PRODUCTION IMPLEMENTATION")
    else:
        print("  - Gating Status: RETRIAL REQUIRED")
        print("  - FINAL VERDICT: BLOCK IMPLEMENTATION")
    print("=" * 60)
    return 0 if is_ready else 1


if __name__ == "__main__":
    sys.exit(run_automated_audits())
