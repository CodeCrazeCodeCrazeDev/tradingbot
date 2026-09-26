"""Context classifier for WEAKNESS_REGISTER.json silent-except rows.

Re-parses each flagged file and classifies every open silent_except* finding
by surrounding context:

  benign_optional_import - module-level or lazy optional-dependency guard
  benign_shutdown        - except asyncio.CancelledError / KeyboardInterrupt
  benign_cleanup         - except in finally/destructor/close paths
  review                 - bare swallow inside logic; needs human audit

Also rescans for bare `raise NotImplementedError` (exc as ast.Name) which the
main scanner's Call-only check missed. Writes results back into the register.
"""
import ast
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REG = REPO / "WEAKNESS_REGISTER.json"


def norm(p):
    return p.replace("\\", "/")


def context_of(path: Path, lineno: int):
    """Return (except_type_names, module_level, in_finally_or_close, func_name)."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.lineno == lineno:
            names = []
            t = node.type
            if t is None:
                names.append("<bare>")
            elif isinstance(t, ast.Tuple):
                names += [getattr(e, "id", getattr(e, "attr", "")) for e in t.elts]
            else:
                names.append(getattr(t, "id", getattr(t, "attr", "")))
            parent = getattr(node, "_parent", None)
            return names
    return None


def build_parents(tree):
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child._parent = node


def classify_file(path: Path, target_lines: set):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {}
    build_parents(tree)
    out = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler) or node.lineno not in target_lines:
            continue
        t = node.type
        names = set()
        if t is None:
            names.add("<bare>")
        elif isinstance(t, ast.Tuple):
            names |= {getattr(e, "id", getattr(e, "attr", "")) for e in t.elts}
        else:
            names.add(getattr(t, "id", getattr(t, "attr", "")))
        # walk ancestors: module-level? inside function? finally/close?
        anc = getattr(node, "_parent", None)
        module_level = True
        fname = ""
        in_cleanup = False
        while anc is not None:
            if isinstance(anc, (ast.FunctionDef, ast.AsyncFunctionDef)):
                module_level = False
                fname = anc.name
                if fname.lower() in {"close", "disconnect", "stop", "shutdown",
                                     "__del__", "__exit__", "cleanup", "release"}:
                    in_cleanup = True
                break
            anc = getattr(anc, "_parent", None)
        try_block = getattr(node, "_parent", None)
        if isinstance(try_block, ast.Try) and try_block.finalbody:
            if any(h is node for h in try_block.handlers) is False:
                pass
        if names & {"CancelledError", "KeyboardInterrupt", "GeneratorExit"}:
            out[node.lineno] = "classified: CancelledError/KeyboardInterrupt shutdown pattern"
        elif module_level and "ImportError" in names:
            out[node.lineno] = "classified: optional-import guard at module level"
        elif not module_level and "ImportError" in names:
            out[node.lineno] = "classified: lazy optional-import fallback"
        elif in_cleanup:
            out[node.lineno] = "classified: best-effort cleanup/close path"
        else:
            out[node.lineno] = None  # review
    return out


def find_bare_notimplemented(path: Path):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return []
    hits = []
    abstract_fns = {n.name for n in ast.walk(tree)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and
                    any("abstract" in ast.dump(d) for d in n.decorator_list)}
    current_fn = [None]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            current_fn[0] = node.name
        if isinstance(node, ast.Raise):
            exc = node.exc
            name = ""
            if isinstance(exc, ast.Name):
                name = exc.id
            elif isinstance(exc, ast.Call):
                f = exc.func
                name = getattr(f, "id", getattr(f, "attr", ""))
            if name == "NotImplementedError" and current_fn[0] not in abstract_fns:
                hits.append((node.lineno, current_fn[0] or "<module>"))
    return hits


def main():
    d = json.loads(REG.read_text())
    by_file = {}
    for r in d["findings"]:
        if r["status"] == "open" and r["detector"].startswith("silent_except"):
            by_file.setdefault(r["file"], set()).add(r["line"])
    n_auto = 0
    for rel, lines in by_file.items():
        path = REPO / rel
        if not path.exists():
            continue
        verdicts = classify_file(path, lines)
        for r in d["findings"]:
            if r["file"] == rel and r["line"] in verdicts and verdicts[r["line"]]:
                r["status"] = verdicts[r["line"]]
                n_auto += 1
    # bare NotImplementedError rescan across reachable files
    for r in d["findings"]:
        rel = r["file"]
        if r["status"] != "open" or not r["reachable"]:
            continue
    added = 0
    seen = {(norm(r["file"]), r["line"], r["detector"]) for r in d["findings"]}
    for path in REPO.joinpath("trading_bot").rglob("*.py"):
        rel = str(path.relative_to(REPO))
        if "_archive" in rel or "__pycache__" in rel:
            continue
        for lineno, fn in find_bare_notimplemented(path):
            if (norm(rel), lineno, "not_implemented") in seen:
                continue
            d["findings"].append({
                "file": rel, "line": lineno, "detector": "not_implemented",
                "detail": f"raise NotImplementedError in {fn}",
                "reachable": True, "severity": "S5", "status": "open",
                "test": "", "commit": "",
            })
            added += 1
    remaining = sum(1 for r in d["findings"] if r["status"] == "open" and r["reachable"])
    d["counts"]["classified_s5_context"] = n_auto
    d["counts"]["not_implemented_added"] = added
    d["counts"]["open_reachable_remaining"] = remaining
    REG.write_text(json.dumps(d, indent=2))
    print(f"auto-classified: {n_auto}  not_implemented added: {added}  open reachable: {remaining}")


if __name__ == "__main__":
    main()
