"""Reachability scan: which top-level trading_bot subpackages are actually
reachable from live entry points?

Seeds: trading_bot/__init__.py, main.py, all tests/*.py, root-level *.py scripts.
Follows: AST import statements (with correct package-relative resolution for
__init__.py files) + string literals passed to importlib.import_module().

Usage: python tools/scan_reachability.py [--json]
"""
import ast
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PKG = REPO / "trading_bot"
SKIP_DIRS = {"__pycache__", "_archive", "node_modules", ".git", "venv"}


def module_file(mod: str):
    """dotted module name -> file path, or None."""
    parts = mod.split(".")
    p = REPO / Path(*parts)
    if (p.with_suffix(".py")).exists():
        return p.with_suffix(".py")
    if (p / "__init__.py").exists():
        return p / "__init__.py"
    return None


def resolve_relative(base_file: Path, level: int, module: str) -> str:
    """Resolve `from .x import y` inside base_file to a dotted module."""
    # base_file is e.g. trading_bot/sub/pkg/__init__.py or trading_bot/sub/mod.py
    if base_file.name == "__init__.py":
        base_parts = list(base_file.parent.relative_to(REPO).parts)
    else:
        base_parts = list(base_file.parent.relative_to(REPO).parts)
    # level=1 means "current package"; go up level-1 dirs
    root = base_parts[: max(0, len(base_parts) - (level - 1))]
    return ".".join(root + ([module] if module else []))


def imports_in(path: Path):
    """Yield dotted module names imported by path (best-effort)."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                yield a.name
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                yield resolve_relative(path, node.level, node.module or "")
            elif node.module:
                yield node.module
        elif isinstance(node, ast.Call):
            # importlib.import_module("a.b.c")
            fn = node.func
            name = getattr(fn, "attr", getattr(fn, "id", ""))
            if name == "import_module" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    yield arg.value


def seed_files():
    seeds = [PKG / "__init__.py", REPO / "main.py"]
    tests = REPO / "tests"
    if tests.exists():
        seeds += [p for p in tests.rglob("*.py") if "_quarantine" not in p.parts]
    seeds += [p for p in REPO.glob("*.py")]
    return [p for p in seeds if p.exists()]


def main():
    seen_files = set()
    queue = list(seed_files())
    reachable_pkgs = set()
    while queue:
        f = queue.pop()
        if f in seen_files:
            continue
        seen_files.add(f)
        for mod in imports_in(f):
            if not mod.startswith("trading_bot"):
                continue
            top = mod.split(".")[1] if "." in mod else None
            if top:
                reachable_pkgs.add(top)
            m = module_file(mod)
            if m and m not in seen_files:
                queue.append(m)
            # `import a.b` may target package a.b whose __init__ was already
            # queued; also queue a.b.c when `from a.b import c` names a submodule
    all_pkgs = sorted(
        d.name for d in PKG.iterdir()
        if d.is_dir() and d.name not in SKIP_DIRS and (d / "__init__.py").exists()
    )
    unreachable = sorted(set(all_pkgs) - reachable_pkgs)
    print(f"top-level packages: {len(all_pkgs)}")
    print(f"reachable:          {len(reachable_pkgs & set(all_pkgs))}")
    print(f"unreachable:        {len(unreachable)}")
    for name in unreachable:
        has_main = any(p.name == "__main__.py" for p in (PKG / name).rglob("__main__.py"))
        print(f"  {name}{'  [has __main__]' if has_main else ''}")
    if "--json" in sys.argv:
        (REPO / "reachability_report.json").write_text(json.dumps({
            "reachable": sorted(reachable_pkgs), "unreachable": unreachable}, indent=2))


if __name__ == "__main__":
    main()
