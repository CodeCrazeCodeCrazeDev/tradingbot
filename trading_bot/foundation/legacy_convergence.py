"""Wave-0 legacy convergence inventory and architecture boundary scanner.

The scanner is intentionally read-mostly: it classifies active code and emits a
manifest, but never moves, deletes, imports, or executes legacy modules.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".merge_backup",
    ".venv",
    "venv",
    "node_modules",
    "_archive",
    "_quarantine",
    "examples",
    "generated",
}

CAPITAL_CALLS = {
    "place_order",
    "order_send",
    "execute_trade",
    "submit_order",
    "send_order",
    "close_position",
    # camelCase broker APIs (ibapi et al.)
    "placeOrder",
    "cancelOrder",
}
LOOP_CALLS = {
    "create_task",
    "run_forever",
    "Process",
    "Thread",
    "multiprocessing.Process",
    "asyncio.create_task",
}
# Import edges the static `imports` list cannot see: runtime module loading.
# Files using these get a `dynamic_import` tag so reviewers know reachability
# is undercounted for them.
# Credential/secret access markers. Tagged for review: secrets may only be
# resolved inside declared security/broker-adapter boundaries; everywhere else
# these calls are candidates to route through the canonical credential
# provider.
CREDENTIAL_IMPORTS = {
    "getpass",
    "keyring",
    "trading_bot.security.credential_vault",
    "trading_bot.security.credentials",
}
CREDENTIAL_CALLS = {
    "getenv",
    "environ.get",
    "os.getenv",
    "os.environ.get",
    "get_password",
    "decrypt",
}
DYNAMIC_LOADERS = {
    "importlib.import_module",
    "import_module",
    "__import__",
    "runpy.run_module",
    "runpy.run_path",
    "spec_from_file_location",
    "module_from_spec",
}
# Directories outside trading_bot/ that still contain executable Python the
# package scanner cannot reach. Root *.py and scripts/ are handled separately.
EXTERNAL_SCAN_DIRS = ("scripts", "perfect_bot", "SCIENTIFIC_FOUNDATION_V5")
# Reviewed exceptions: capital-named calls inside these paths target in-memory
# simulators, not broker adapters (e.g. ``backtester.execute_trade(...)`` on a
# Backtester instance in strategy_backtester.py). Verified non-live; do NOT add
# entries without confirming the receiver is a simulator.
SIMULATED_CAPITAL_PATHS = {
    "trading_bot/backtesting/strategy_backtester.py",
    # In-memory paper broker: fills and close_position operate on
    # self._positions only; no network or live broker calls.
    "trading_bot/alphaalgo_v2/execution/brokers/paper.py",
}

# Declared execution adapters living outside the execution/|broker(s)/ trees.
# Mirrors ARCHITECTURE_COMPONENT_MANIFEST.json -> execution_service
# .compatibility_paths: the bridge delegates to an injected broker adapter and
# is itself the typed execution surface, not an uncontrolled capital path.
EXECUTION_BOUNDARY_PATHS = {
    "trading_bot/core/execution_bridge.py",
}

# Reviewed connection-plumbing workers inside declared adapter boundaries:
# heartbeat loops, websocket pump handlers, reconnect tasks, and ibapi
# client.run threads are adapter internals, not independent trading
# lifecycles. Exempt from the loop violation only — direct-capital and
# archive rules still apply. Do NOT add entries without confirming the spawn
# is connection plumbing, not a trading/decision loop.
ADAPTER_WORKER_PATHS = {
    "trading_bot/broker/binance_broker.py",
    "trading_bot/brokers/connection_manager.py",
    "trading_bot/brokers/live_order_router.py",
    "trading_bot/brokers/multi_broker_adapter.py",
    "trading_bot/brokers/real_broker_integration.py",
    "trading_bot/connectors/binance_connector.py",
    "trading_bot/connectors/interactive_brokers_connector.py",
    "trading_bot/production/interactive_brokers_live.py",
}

# Modules that preserve imports while delegating to canonical services. They
# are one-wave shims rather than authorities.
COMPATIBILITY_FACADE_PATHS = {
    "trading_bot/api.py",
    "trading_bot/api/__init__.py",
    "trading_bot/core/event_bus.py",
    "trading_bot/unified_main.py",
    "trading_bot/unified_architecture/unified_trading_system.py",
}

CANONICAL_FILES = {
    "trading_bot/foundation/runtime.py": ("canonical", "composition", "ModularMonolithRuntime"),
    "trading_bot/unified_bot.py": ("canonical", "composition", "UnifiedTradingBot"),
    "trading_bot/core/csc/controller.py": ("canonical", "orchestration", "CognitiveSystemController"),
    "trading_bot/cognition/orchestrator.py": ("canonical", "cognition", "AlphaAlgoCognitiveBrain"),
    "trading_bot/core/unified_registry.py": ("canonical", "infrastructure", "UnifiedComponentRegistry"),
    "trading_bot/core/unified_event_bus.py": ("canonical", "infrastructure", "UnifiedDecisionBus"),
    "trading_bot/data/normalizer.py": ("canonical", "data", "MarketDataNormalizer"),
    "trading_bot/risk/service.py": ("canonical", "risk", "CanonicalRiskService"),
    "trading_bot/core/immutable_shield.py": ("canonical", "governance", "ImmutableShield"),
    "trading_bot/execution/service.py": ("canonical", "execution", "CanonicalExecutionService"),
    "trading_bot/persistence/repositories.py": ("canonical", "persistence", "SqliteTradingRepository"),
    "trading_bot/recursive_self_improvement/rsi_loop.py": (
        "canonical", "research", "HumanGuidedRecursiveImprovementLoop"
    ),
}


@dataclass
class ModuleRecord:
    path: str
    module: str
    classification: str
    owner: str
    canonical_port: str
    runtime_reachable: bool = False
    cli_entrypoint: bool = False
    direct_capital_path: bool = False
    starts_loop: bool = False
    parse_status: str = "pass"
    parse_error: Optional[str] = None
    secondary_tags: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    importers: List[str] = field(default_factory=list)
    tests: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    migration_wave: int = 0
    shim_status: str = "not_applicable"
    quarantine_reason: Optional[str] = None
    removal_ready: bool = False

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def _rel_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _module_name(relative: str) -> str:
    if relative.endswith("/__init__.py"):
        relative = relative[: -len("/__init__.py")]
    elif relative.endswith(".py"):
        relative = relative[:-3]
    return relative.replace("/", ".")


def iter_python_files(root: Path) -> Iterable[Path]:
    for directory, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
        for filename in sorted(files):
            if filename.endswith(".py"):
                yield Path(directory) / filename


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        parts = []
        current: ast.AST = node.func
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    return ""


def _parse_source(source: str) -> Tuple[Optional[ast.Module], Optional[str]]:
    try:
        return ast.parse(source), None
    except SyntaxError as exc:
        return None, f"{exc.msg} (line {exc.lineno})"


def scan_source(source: str, path: str) -> Dict[str, object]:
    """Scan one source string without importing or executing it."""
    tree, parse_error = _parse_source(source)
    calls: Set[str] = set()
    imports: Set[str] = set()
    classes: List[str] = []
    functions: List[str] = []
    has_cli = False

    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)
            elif isinstance(node, ast.Call):
                calls.add(_call_name(node))
            elif isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
            elif isinstance(node, ast.If):
                if isinstance(node.test, ast.Compare):
                    left = node.test.left
                    if isinstance(left, ast.Name) and left.id == "__name__":
                        has_cli = True

    terminal_calls = {call.rsplit(".", 1)[-1] for call in calls}
    direct_capital = bool(terminal_calls & CAPITAL_CALLS)
    starts_loop = bool(calls & LOOP_CALLS or terminal_calls & {"create_task", "run_forever", "Process", "Thread"})
    dynamic = bool(calls & DYNAMIC_LOADERS)
    tags: List[str] = []
    if direct_capital:
        tags.append("direct_broker_access")
    if starts_loop:
        tags.append("starts_loop")
    if dynamic:
        tags.append("dynamic_import")
    if imports & CREDENTIAL_IMPORTS or terminal_calls & CREDENTIAL_CALLS or calls & CREDENTIAL_CALLS:
        tags.append("credential_access")
    if any("_archive" in item for item in imports):
        tags.append("archive_import")
    return {
        "parse_status": "error" if parse_error else "pass",
        "parse_error": parse_error,
        "classes": sorted(classes),
        "functions": sorted(functions),
        "imports": sorted(imports),
        "calls": sorted(calls),
        "cli_entrypoint": has_cli,
        "direct_capital_path": direct_capital,
        "starts_loop": starts_loop,
        "secondary_tags": tags,
    }


def _owner_for_path(path: str, classes: Sequence[str]) -> Tuple[str, str, int]:
    canonical = CANONICAL_FILES.get(path)
    if canonical:
        return canonical[1], canonical[2], 0
    lowered = path.lower()
    if any(part in lowered for part in ("research", "backtest", "evaluation", "experiment")):
        return "research", "ResearchCapability", 6
    if any(part in lowered for part in ("broker", "venue", "exchange", "mt5", "binance", "ib_")):
        return "execution", "BrokerAdapter", 3
    if any(part in lowered for part in ("risk", "safety", "governance", "approval", "compliance")):
        return "risk", "RiskService/GovernanceGate", 2
    if any(part in lowered for part in ("strategy", "signal", "alpha", "portfolio", "position")):
        return "strategy", "StrategyPort/SignalPort", 4
    if any(part in lowered for part in ("agent", "brain", "intelligence", "model", "reasoning", "cognition")):
        return "cognition", "CapabilityPort", 5
    if "orchestrator" in lowered or "controller" in lowered or "master_" in lowered:
        return "orchestration", "ModularMonolithRuntime", 1
    if path.endswith("main.py") or "__main__" in classes:
        return "interfaces", "ModularMonolithRuntime", 7
    return "infrastructure", "ComponentLifecycle", 1


def _classification(path: str, scan: Mapping[str, object]) -> Tuple[str, Optional[str]]:
    if scan["parse_status"] == "error":
        return "quarantine", "parse_error"
    canonical = CANONICAL_FILES.get(path)
    if canonical:
        return "canonical", None
    if path in COMPATIBILITY_FACADE_PATHS:
        return "compatibility_facade", None
    if (
        scan["direct_capital_path"]
        and path not in SIMULATED_CAPITAL_PATHS
        and path not in EXECUTION_BOUNDARY_PATHS
        and not any(
            allowed in path for allowed in ("trading_bot/execution/", "trading_bot/broker/", "trading_bot/brokers/")
        )
    ):
        return "quarantine", "direct_capital_path_outside_execution_boundary"
    lowered = path.lower()
    if any(part in lowered for part in ("research", "backtest", "evaluation", "experiment")):
        return "research_only", None
    if any(part in lowered for part in ("orchestrator", "master_", "controller", "registry")):
        return "compatibility_facade", None
    return "adapter", None


def build_manifest(root: Path) -> Dict[str, object]:
    root = root.resolve()
    paths = sorted(iter_python_files(root / "trading_bot"))
    scans: Dict[str, Dict[str, object]] = {}
    module_paths: Dict[str, str] = {}
    for path in paths:
        relative = _rel_path(path, root)
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            continue
        scans[relative] = scan_source(source, relative)
        module_paths[_module_name(relative)] = relative

    importers: Dict[str, Set[str]] = {path: set() for path in scans}
    imports_by_path: Dict[str, Set[str]] = {path: set() for path in scans}
    for path, scan in scans.items():
        for imported in scan["imports"]:
            if not isinstance(imported, str):
                continue
            candidates = [imported]
            while candidates:
                candidate = candidates.pop()
                target = module_paths.get(candidate)
                if target:
                    importers[target].add(path)
                    imports_by_path[path].add(target)
                    break
                if "." in candidate:
                    candidates.append(candidate.rsplit(".", 1)[0])

    # Evidence mapping: which test files import each module. Covers both
    # in-package test modules and the top-level tests/ tree, which the module
    # scan cannot reach because it lives outside trading_bot/.
    tests_map: Dict[str, Set[str]] = {path: set() for path in scans}

    def _resolve_import(module_name: str) -> Optional[str]:
        candidate = module_name
        while candidate:
            target = module_paths.get(candidate)
            if target:
                return target
            if "." not in candidate:
                return None
            candidate = candidate.rsplit(".", 1)[0]
        return None

    def _record_test_imports(test_path: str, imports: Iterable[object]) -> None:
        for imported in imports:
            if not isinstance(imported, str):
                continue
            target = _resolve_import(imported)
            if target and target != test_path and target in tests_map:
                tests_map[target].add(test_path)

    for path, scan in scans.items():
        name = path.rsplit("/", 1)[-1]
        if name.startswith("test_") or "/tests/" in path or "/test_" in path:
            _record_test_imports(path, scan["imports"])

    tests_root = root / "tests"
    if tests_root.exists():
        for directory, dirs, files in os.walk(tests_root):
            dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
            for filename in sorted(files):
                if not filename.endswith(".py"):
                    continue
                tpath = Path(directory) / filename
                try:
                    tsource = tpath.read_text(encoding="utf-8", errors="replace")
                except (FileNotFoundError, OSError):
                    continue
                trel = _rel_path(tpath, root)
                _record_test_imports(trel, scan_source(tsource, trel)["imports"])

    seeds = {
        "trading_bot/__init__.py",
        "trading_bot/unified_bot.py",
        "trading_bot/foundation/runtime.py",
    }
    root_main = root / "main.py"
    if root_main.exists():
        root_main_scan = scan_source(root_main.read_text(encoding="utf-8", errors="replace"), "main.py")
        for imported in root_main_scan["imports"]:
            if isinstance(imported, str):
                target = module_paths.get(imported)
                if target:
                    seeds.add(target)
    for path, scan in scans.items():
        if scan["cli_entrypoint"] and path.endswith("/__main__.py"):
            seeds.add(path)
    reachable = set(seeds)
    queue = list(seeds)
    while queue:
        current = queue.pop()
        for target in imports_by_path.get(current, set()):
            if target not in reachable:
                reachable.add(target)
                queue.append(target)

    records: List[Dict[str, object]] = []
    for path in sorted(scans):
        scan = scans[path]
        owner, port, wave = _owner_for_path(path, scan["classes"])
        classification, quarantine_reason = _classification(path, scan)
        tags = list(scan["secondary_tags"])
        if scan["cli_entrypoint"]:
            tags.append("cli_entrypoint")
        if path.startswith("trading_bot/") and "/" not in path[len("trading_bot/") :]:
            tags.append("top_level_module")
        record = ModuleRecord(
            path=path,
            module=_module_name(path),
            classification=classification,
            owner=owner,
            canonical_port=port,
            runtime_reachable=path in reachable,
            cli_entrypoint=bool(scan["cli_entrypoint"]),
            direct_capital_path=bool(scan["direct_capital_path"]),
            starts_loop=bool(scan["starts_loop"]),
            parse_status=str(scan["parse_status"]),
            parse_error=scan["parse_error"],
            secondary_tags=sorted(set(tags)),
            classes=list(scan["classes"]),
            functions=list(scan["functions"]),
            imports=list(scan["imports"]),
            importers=sorted(importers[path]),
            tests=sorted(tests_map[path]),
            migration_wave=wave,
            shim_status="active_one_wave" if classification == "compatibility_facade" else "not_applicable",
            quarantine_reason=quarantine_reason,
        )
        records.append(record.to_dict())

    # Authority-review status for every flagged (capital/loop) record.
    # "canonical_authority" = sanctioned owner inside the boundary;
    # "warned_non_authority" = source carries an explicit no-authority
    # marker; "catalogued_non_reachable" = flagged backlog, no live path;
    # "reachable_review_required" = flagged AND reachable non-canonical —
    # must be zero after each wave.
    for record in records:
        if not (record["direct_capital_path"] or record["starts_loop"]):
            continue
        if record["classification"] == "canonical":
            record["review_status"] = "canonical_authority"
            continue
        if record["path"] in EXECUTION_BOUNDARY_PATHS:
            record["review_status"] = "sanctioned_boundary_adapter"
            continue
        if record["runtime_reachable"]:
            record["review_status"] = "reachable_review_required"
            continue
        try:
            text = (root / record["path"]).read_text(
                encoding="utf-8", errors="replace"
            )
        except OSError:
            text = ""
        record["review_status"] = (
            "warned_non_authority"
            if "DeprecationWarning" in text or "QUARANTINED" in text
            else "catalogued_non_reachable"
        )

    # Non-package executable surfaces the module scan cannot reach: root
    # *.py launchers, scripts/, and bundled standalone packages. They are
    # recorded separately (not as modules) and default to unreviewed/quarantine
    # for production purposes until individually classified.
    surfaces: List[Dict[str, object]] = []
    surface_paths: List[Path] = [
        p for p in sorted(root.glob("*.py"))
        if p.name != "__init__.py"
    ]
    for dirname in EXTERNAL_SCAN_DIRS:
        directory = root / dirname
        if not directory.exists():
            continue
        for directory_walk, dirs, files in os.walk(directory):
            dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
            for filename in sorted(files):
                if filename.endswith(".py"):
                    surface_paths.append(Path(directory_walk) / filename)
    for path in sorted(set(surface_paths)):
        relative = _rel_path(path, root)
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except (FileNotFoundError, OSError):
            continue
        scan = scan_source(source, relative)
        tags = list(scan["secondary_tags"])
        if scan["cli_entrypoint"]:
            tags.append("cli_entrypoint")
        tb_imports = [
            imp for imp in scan["imports"]
            if imp == "trading_bot" or imp.startswith("trading_bot.")
        ]
        # Entry-point triage: a capital-capable surface is only "contained" if
        # it refuses at __main__ (QUARANTINED/SystemExit marker) or delegates
        # to a canonical entry point (main/foundation runtime/unified_bot).
        delegates_to_runtime = bool(
            {"main", "trading_bot.foundation.runtime",
             "trading_bot.unified_bot"} & set(scan["imports"])
        )
        guarded_at_entry = (
            ("QUARANTINED" in source and "SystemExit" in source)
            or delegates_to_runtime
            or "ModularMonolithRuntime" in source
        )
        if scan["parse_status"] == "error" or scan["direct_capital_path"]:
            surface_class = "quarantine"
            reason = (
                "parse_error" if scan["parse_status"] == "error"
                else "direct_capital_path_outside_execution_boundary"
            )
        elif delegates_to_runtime:
            surface_class = "runtime_facade"
            reason = None
        elif not tb_imports:
            surface_class = "standalone_tool"
            reason = None
        else:
            surface_class = "unreviewed_surface"
            reason = None
        surfaces.append({
            "path": relative,
            "classification": surface_class,
            "quarantine_reason": reason,
            "guarded_at_entry": guarded_at_entry,
            "delegates_to_runtime": delegates_to_runtime,
            "cli_entrypoint": bool(scan["cli_entrypoint"]),
            "direct_capital_path": bool(scan["direct_capital_path"]),
            "starts_loop": bool(scan["starts_loop"]),
            "parse_status": str(scan["parse_status"]),
            "secondary_tags": sorted(set(tags)),
            "imports": list(scan["imports"]),
            "classes": list(scan["classes"]),
        })

    return {
        "schema_version": "1.0",
        "generator": "trading_bot.foundation.legacy_convergence",
        "scope": {
            "included": "live runtime modules and standalone CLI entry points",
            "excluded": sorted(EXCLUDED_DIRS),
            "physical_moves_performed": False,
        },
        "canonical_authorities": {
            path: {"owner": data[1], "implementation": data[2]}
            for path, data in sorted(CANONICAL_FILES.items())
        },
        "summary": {
            "modules": len(records),
            "runtime_reachable": sum(1 for row in records if row["runtime_reachable"]),
            "quarantined": sum(1 for row in records if row["classification"] == "quarantine"),
            "compatibility_facades": sum(1 for row in records if row["classification"] == "compatibility_facade"),
            "direct_capital_paths": sum(1 for row in records if row["direct_capital_path"]),
            "parse_errors": sum(1 for row in records if row["parse_status"] == "error"),
            "external_surfaces": len(surfaces),
            "external_capital_paths": sum(1 for row in surfaces if row["direct_capital_path"]),
            "external_loop_starters": sum(1 for row in surfaces if row["starts_loop"]),
            "unguarded_capital_surfaces": sum(
                1 for row in surfaces
                if row["direct_capital_path"] and not row["guarded_at_entry"]
            ),
            "unguarded_loop_surfaces": sum(
                1 for row in surfaces
                if row["starts_loop"] and row["cli_entrypoint"]
                and not row["guarded_at_entry"]
            ),
            "external_surface_classes": {
                cls: sum(1 for row in surfaces if row["classification"] == cls)
                for cls in (
                    "quarantine", "runtime_facade", "standalone_tool",
                    "unreviewed_surface",
                )
            },
            "dynamic_import_modules": sum(
                1 for row in records if "dynamic_import" in row["secondary_tags"]
            ),
            "flagged_review_status": {
                status: sum(1 for row in records if row.get("review_status") == status)
                for status in (
                    "canonical_authority",
                    "sanctioned_boundary_adapter",
                    "warned_non_authority",
                    "catalogued_non_reachable",
                    "reachable_review_required",
                )
            },
            "credential_access_modules": sum(
                1 for row in records if "credential_access" in row["secondary_tags"]
            ) + sum(
                1 for row in surfaces if "credential_access" in row["secondary_tags"]
            ),
            "modules_with_test_evidence": sum(1 for row in records if row["tests"]),
            "adapters_without_tests": sum(
                1 for row in records
                if row["classification"] == "adapter" and not row["tests"]
            ),
        },
        "modules": records,
        "external_surfaces": surfaces,
    }


def boundary_violations(source: str, path: str) -> List[str]:
    """Return violations for one source unit, suitable for CI tests."""
    scan = scan_source(source, path)
    violations: List[str] = []
    if any(tag == "archive_import" for tag in scan["secondary_tags"]):
        violations.append("active module imports from _archive")
    if (
        scan["direct_capital_path"]
        and path not in SIMULATED_CAPITAL_PATHS
        and path not in EXECUTION_BOUNDARY_PATHS
        and not any(
            allowed in path for allowed in ("trading_bot/execution/", "trading_bot/broker/", "trading_bot/brokers/")
        )
    ):
        violations.append("direct capital call outside execution/broker adapter")
    if (
        scan["starts_loop"]
        and path not in CANONICAL_FILES
        and path not in ADAPTER_WORKER_PATHS
        and "foundation/runtime.py" not in path
    ):
        violations.append("independent lifecycle/worker loop")
    return violations


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate AlphaAlgo legacy convergence manifest")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="ARCHITECTURE_LEGACY_CLASSIFICATION.json")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = root / output
    output.write_text(json.dumps(build_manifest(root), indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
