"""AST gate tests — the non-bypassable scan for agent-generated code."""
import pytest

from trading_bot.recursive_self_improvement.ast_gate import (
    scan_code, verify_code_safety)


def test_clean_math_code_passes():
    assert verify_code_safety(
        "import numpy as np\nx = np.array([1, 2, 3])\ny = np.mean(x)\n")


def test_eval_exec_blocked():
    assert not verify_code_safety("x = eval('1+1')")
    assert not verify_code_safety("exec('print(1)')")
    assert not verify_code_safety("compile('x', 'f', 'exec')")


def test_forbidden_imports_blocked():
    assert not verify_code_safety("import os")
    assert not verify_code_safety("import subprocess")
    assert not verify_code_safety("from os import system")
    assert not verify_code_safety("import socket")
    # Dotted forms too.
    assert not verify_code_safety("import os.path")


def test_attr_calls_on_forbidden_roots_blocked():
    assert not verify_code_safety("os.system('rm -rf /')")
    assert not verify_code_safety("subprocess.run('x')")


def test_dunder_traversal_blocked():
    # The classic sandbox-escape idiom.
    assert not verify_code_safety("x = ().__class__.__bases__")
    assert not verify_code_safety("x.__globals__['os'].system('x')")


def test_smuggled_builtins_blocked():
    assert not verify_code_safety("getattr(x, 'evil')()")
    assert not verify_code_safety("globals()['os']")
    assert not verify_code_safety("open('/etc/passwd')")
    assert not verify_code_safety("__import__('os')")


def test_syntax_error_rejected():
    ok, violations = scan_code("def broken(:")
    assert not ok
    assert violations and violations[0].startswith("syntax_error")


def test_unlisted_import_flagged():
    ok, violations = scan_code("import requests")
    assert not ok
    assert any("unlisted" in v for v in violations)


def test_scan_reports_violations():
    ok, violations = scan_code("import os\nx = eval('y')")
    assert not ok
    assert len(violations) == 2
