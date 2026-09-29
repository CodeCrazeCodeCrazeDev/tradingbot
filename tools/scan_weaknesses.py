"""Weakness scanner: AST-based detection of confirmed weakness classes across
reachable trading_bot code.

Produces WEAKNESS_REGISTER.json — every row carries file:line evidence, a
detector name, and a severity class. The register is the campaign backlog; a
row means "flagged for human-visible verification", not "confirmed exploitable".

Usage: python tools/scan_weaknesses.py [--report]
"""
import ast
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PKG = REPO / "trading_bot"
SKIP_DIRS = {"__pycache__", "_archive", "node_modules", ".git", "venv", "tests"}

sys.path.insert(0, str(REPO))
from tools.scan_reachability import imports_in, module_file, seed_files  # noqa: E402

CAPITAL_DIRS = ("core/immutable_shield", "core/unified_event_bus", "risk/",
                "execution/", "governance/")
CANONICAL_DIRS = ("core/csc/", "cognition/", "foundation/runtime", "unified_bot")
EVIDENCE_DIRS = ("recursive_self_improvement/", "evaluation/")
DETERMINISM_DIRS = ("evaluation/", "recursive_self_improvement/")

GATE_NAME_PREFIXES = ("validate", "verify", "check", "approve", "authorize",
                      "permit", "allow", "ensure", "is_", "can_", "has_",
                      "safe", "sanitiz")


def reachable_files():
    seen, queue = set(), list(seed_files())
    while queue:
        f = queue.pop()
        if f in seen:
            continue
        seen.add(f)
        for mod in imports_in(f):
            if not mod.startswith("trading_bot"):
                continue
            m = module_file(mod)
            if m and m not in seen:
                queue.append(m)
    return {p.resolve() for p in seen}


def severity_for(relpath: str, detector: str) -> str:
    p = relpath.replace("\\", "/")
    if any(d in p for d in CAPITAL_DIRS):
        return "S0"
    if detector in ("sql_interpolation", "dangerous_call", "pickle_unsafe",
                    "yaml_unsafe"):
        return "S3"
    if any(d in p for d in EVIDENCE_DIRS):
        return "S2"
    if any(d in p for d in CANONICAL_DIRS):
        return "S1"
    return "S5"


def _returns_only_literal_true(fn: ast.AST) -> bool:
    returns = [n for n in ast.walk(fn) if isinstance(n, ast.Return)]
    if not returns:
        return False
    return all(isinstance(r.value, ast.Constant) and r.value.value is True
               for r in returns)


def _except_silent(handler: ast.ExceptHandler) -> str:
    body = handler.body
    if len(body) == 1:
        node = body[0]
        if isinstance(node, ast.Pass):
            return "except_pass"
        if isinstance(node, ast.Return) and (
                node.value is None or
                (isinstance(node.value, ast.Constant) and node.value.value in (None, False)) or
                isinstance(node.value, (ast.Dict, ast.List, ast.Tuple)) and not
                list(ast.walk(node.value))[1:]):
            return "except_swallow_default"
    if len(body) == 2 and isinstance(body[0], ast.Expr) and isinstance(body[1], ast.Pass):
        return "except_log_pass"
    return ""


def _call_name(call: ast.Call) -> str:
    f = call.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        parts = []
        node = f
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        return ".".join(reversed(parts))
    return ""


def scan_file(path: Path, relpath: str):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return
    fn_names = {n.name for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    abstract = {n.name for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and
                any(getattr(d, "id", getattr(d, "attr", "")) == "abstractmethod"
                    for d in n.decorator_list)}
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            kind = _except_silent(node)
            if kind:
                yield ("silent_" + kind, node.lineno, "silent exception handling")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            low = node.name.lower()
            if low.startswith(GATE_NAME_PREFIXES) and _returns_only_literal_true(node):
                yield ("always_true_gate", node.lineno, f"gate '{node.name}' always returns True")
            if node.name in fn_names and node.name not in abstract:
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Raise) and isinstance(sub.exc, ast.Call) and \
                            _call_name(sub.exc).endswith("NotImplementedError"):
                        yield ("not_implemented", sub.lineno,
                               f"raise NotImplementedError in {node.name}")
                    if isinstance(sub, ast.Assert) and low.startswith(GATE_NAME_PREFIXES):
                        yield ("assert_validation", sub.lineno,
                               "assert used inside a validation gate (stripped under -O)")
            for default in list(node.args.defaults) + [d for d in node.args.kw_defaults if d]:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    yield ("mutable_default", default.lineno,
                           f"mutable default argument in {node.name}")
        elif isinstance(node, ast.Call):
            name = _call_name(node)
            if name in ("eval", "exec"):
                yield ("dangerous_call", node.lineno, f"{name}() on dynamic input")
            elif name == "os.system":
                yield ("dangerous_call", node.lineno, "os.system()")
            elif name.startswith("subprocess.") and any(
                    k.arg == "shell" and isinstance(k.value, ast.Constant) and k.value.value
                    for k in node.keywords):
                yield ("dangerous_call", node.lineno, f"{name} shell=True")
            elif name in ("pickle.load", "pickle.loads"):
                arg_ok = node.args and isinstance(node.args[0], ast.Constant)
                if not arg_ok:
                    yield ("pickle_unsafe", node.lineno, "pickle on non-constant input")
            elif name == "yaml.load":
                loader = next((k for k in node.keywords if k.arg == "Loader"), None)
                safe = loader and "SafeLoader" in ast.dump(loader.value)
                if not safe:
                    yield ("yaml_unsafe", node.lineno, "yaml.load without SafeLoader")
            elif name.endswith(".execute") and node.args:
                first = node.args[0]
                if isinstance(first, ast.JoinedStr) or (
                        isinstance(first, ast.BinOp) and isinstance(first.op, ast.Mod)):
                    yield ("sql_interpolation", node.lineno, "SQL built by string interpolation")
            elif any(d in relpath.replace("\\", "/") for d in DETERMINISM_DIRS) and \
                    name.startswith(("random.", "np.random", "numpy.random")) and \
                    "seed" not in name:
                yield ("unseeded_random", node.lineno, f"unseeded {name} in deterministic path")


def main():
    reachable = reachable_files()
    rows = []
    for path in sorted(PKG.rglob("*.py")):
        if SKIP_DIRS & set(path.parts):
            continue
        relpath = str(path.relative_to(REPO))
        is_reachable = path.resolve() in reachable
        for detector, lineno, detail in scan_file(path, relpath):
            rows.append({
                "file": relpath, "line": lineno, "detector": detector,
                "detail": detail, "reachable": is_reachable,
                "severity": severity_for(relpath, detector) if is_reachable else "S5",
                "status": "open", "test": "", "commit": "",
            })
    rows.sort(key=lambda r: (r["severity"], r["file"], r["line"]))
    register = {
        "generated_by": "tools/scan_weaknesses.py",
        "note": "Rows are flagged candidates; verification + failing test precede any fix. "
                "_archive excluded. Reachability is best-effort AST analysis.",
        "counts": {
            "total": len(rows),
            "reachable": sum(1 for r in rows if r["reachable"]),
            "by_severity": {s: sum(1 for r in rows if r["severity"] == s)
                            for s in ("S0", "S1", "S2", "S3", "S4", "S5")},
            "by_detector": {d: sum(1 for r in rows if r["detector"] == d)
                            for d in sorted({r["detector"] for r in rows})},
        },
        "findings": rows,
    }
    out = REPO / "WEAKNESS_REGISTER.json"
    out.write_text(json.dumps(register, indent=2))
    print(json.dumps(register["counts"], indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
