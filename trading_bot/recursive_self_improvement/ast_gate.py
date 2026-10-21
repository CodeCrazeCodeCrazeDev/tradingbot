"""AST-level code safety gate — non-bypassable scan for agent-generated
code before any execution path.

Implements the SAFE_SELF_MODIFICATION spec, hardened: forbidden calls,
forbidden modules (including dotted forms like ``os.path``), dunder
attribute traversal (``__class__.__bases__`` escapes), attribute calls
on forbidden roots (``os.system``), and smuggled builtins
(``getattr``, ``vars``).
"""
from __future__ import annotations

import ast
from typing import List, Optional, Tuple

FORBIDDEN_CALLS = frozenset({
    "eval", "exec", "compile", "__import__", "input", "breakpoint",
    "globals", "locals", "vars", "dir", "memoryview", "open",
    "getattr", "setattr", "delattr", "execfile",
})
FORBIDDEN_MODULES = frozenset({
    "os", "sys", "subprocess", "shutil", "socket", "ctypes",
    "importlib", "pickle", "shelve", "marshal", "multiprocessing",
    "signal", "builtins", "io", "code", "codeop", "pty", "tty",
    "pathlib", "tempfile", "zipfile", "tarfile",
})
ALLOWED_MODULES = frozenset({
    "numpy", "pandas", "scipy", "sklearn", "statsmodels", "math",
    "statistics", "itertools", "functools", "collections",
})
# Dunder traversal is the classic sandbox-escape idiom.
_FORBIDDEN_ATTR_PREFIXES = ("__",)


def _root_name(node: ast.AST) -> Optional[str]:
    cur = node
    while isinstance(cur, ast.Attribute):
        cur = cur.value
    return cur.id if isinstance(cur, ast.Name) else None


def verify_code_safety(code_string: str) -> bool:
    """True only if the source parses and contains no forbidden call,
    import, attribute traversal, or smuggled builtin access."""
    ok, _ = scan_code(code_string)
    return ok


def scan_code(code_string: str) -> Tuple[bool, List[str]]:
    """Structured variant: returns (safe, violations)."""
    violations: List[str] = []
    try:
        tree = ast.parse(code_string)
    except SyntaxError as exc:
        return False, [f"syntax_error:{exc}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                violations.append(f"forbidden_call:{node.func.id}")
        if isinstance(node, ast.Call) and isinstance(node.func,
                                                      ast.Attribute):
            root = _root_name(node.func.value)
            if root in FORBIDDEN_MODULES:
                violations.append(
                    f"forbidden_attr_call:{root}.{node.func.attr}")
            if node.func.attr.startswith(_FORBIDDEN_ATTR_PREFIXES):
                violations.append(f"dunder_call:{node.func.attr}")
        if isinstance(node, ast.Attribute):
            if node.attr.startswith(_FORBIDDEN_ATTR_PREFIXES):
                violations.append(f"dunder_access:{node.attr}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_MODULES:
                    violations.append(f"forbidden_import:{alias.name}")
                elif (root not in ALLOWED_MODULES
                      and not alias.name.startswith(("numpy", "pandas"))):
                    violations.append(f"unlisted_import:{alias.name}")
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            root = mod.split(".")[0]
            if root in FORBIDDEN_MODULES:
                violations.append(f"forbidden_import_from:{mod}")
            elif root not in ALLOWED_MODULES:
                violations.append(f"unlisted_import_from:{mod}")
    return not violations, violations
