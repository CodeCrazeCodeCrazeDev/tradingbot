import ast
import asyncio
import logging
import sys
import os
import multiprocessing
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class UnsafeCodeError(ValueError):
    """Exception raised when code violates security policies."""
    pass

class SecureASTVisitor(ast.NodeVisitor):
    """
    AST Visitor that checks python source code for dangerous statements,
    attributes, and function calls.
    """
    def __init__(self):
        # Whitelist of allowed modules to import (only if safe)
        self.allowed_modules = {"math", "numpy", "pandas"}

        # Blacklist of dangerous names/functions
        self.dangerous_names = {
            "eval", "exec", "compile", "globals", "locals", "open",
            "__import__", "getattr", "setattr", "delattr", "hasattr",
            "os", "sys", "subprocess", "socket", "builtins", "importlib",
            "shutil", "tempfile"
        }

    def visit_Import(self, node: ast.Import):
        for name in node.names:
            if name.name.split('.')[0] not in self.allowed_modules:
                raise UnsafeCodeError(f"Import of module '{name.name}' is blocked")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module and node.module.split('.')[0] not in self.allowed_modules:
            raise UnsafeCodeError(f"Import from module '{node.module}' is blocked")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if node.id in self.dangerous_names:
            raise UnsafeCodeError(f"Access to blocked name '{node.id}' is blocked")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        # Prevent access to double-underscore / private attributes
        if node.attr.startswith("__"):
            raise UnsafeCodeError("Access to private/dunder attributes is blocked")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Direct check of called name if it's a simple identifier
        if isinstance(node.func, ast.Name):
            if node.func.id in self.dangerous_names:
                raise UnsafeCodeError(f"Call to blocked function '{node.func.id}' is blocked")
        self.generic_visit(node)


def _worker_execute_code(code_str: str, entry_point: str, args_tuple: Tuple, seed: int) -> Tuple[bool, Any, str, str]:
    """
    Target worker function executed in an isolated process.
    Provides complete stdout/stderr capture, read-only environment limits,
    and deterministic RNG seeding.
    """
    import io
    import numpy as np
    import pandas as pd
    import random

    # Capture stdout and stderr
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    sys.stdout = stdout_buf
    sys.stderr = stderr_buf

    try:
        # Enforce deterministic seeding
        random.seed(seed)
        np.random.seed(seed)

        # Restricted environment
        allowed_globals = {
            "__builtins__": {
                "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
                "enumerate": enumerate, "filter": filter, "float": float, "int": int,
                "len": len, "list": list, "map": map, "max": max, "min": min,
                "range": range, "round": round, "set": set, "str": str, "sum": sum,
                "tuple": tuple, "zip": zip, "print": print
            },
            "np": np,
            "np_random": np.random,
            "pd": pd
        }
        local_scope = {}

        # Compile and run
        compiled = compile(code_str, "<sandbox>", "exec")
        exec(compiled, allowed_globals, local_scope)

        # Call the entry point function
        if entry_point not in local_scope:
            raise ValueError(f"Entry point function '{entry_point}' not found in executed code.")

        fn = local_scope[entry_point]
        result = fn(*args_tuple)

        sys.stdout = old_stdout
        sys.stderr = old_stderr
        return True, result, stdout_buf.getvalue(), stderr_buf.getvalue()

    except Exception as e:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        return False, str(e), stdout_buf.getvalue(), stderr_buf.getvalue()


def _process_target(queue: multiprocessing.Queue, code_str: str, entry_point: str, args_tuple: Tuple, seed: int):
    """Bridge wrapper to push worker execution outputs into a multiprocessing Queue."""
    try:
        res = _worker_execute_code(code_str, entry_point, args_tuple, seed)
        queue.put(res)
    except Exception as e:
        queue.put((False, str(e), "", ""))


class StrategySandbox:
    """
    Strategy Sandbox Environment.
    Enforces AST code verification and isolates dynamic code execution inside a
    disposable process pool to completely eliminate thread leaks and CPU/RAM starvation.
    """

    def __init__(self, wall_clock_timeout: float = 2.0, default_seed: int = 42):
        self.wall_clock_timeout = wall_clock_timeout
        self.default_seed = default_seed
        self.visitor = SecureASTVisitor()

    def verify_code_security(self, code_str: str) -> bool:
        """Parse and walk the AST to detect security policy violations."""
        try:
            tree = ast.parse(code_str)
            self.visitor.visit(tree)
            return True
        except (SyntaxError, UnsafeCodeError) as e:
            logger.warning(f"StrategySandbox: Security validation failed: {e}")
            raise UnsafeCodeError(f"Code security check failed: {e}")

    async def execute_secure(self, code_str: str, entry_point: str, args_tuple: Tuple = (), seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute code securely with AST checks and strict Process termination on timeouts.

        Returns a dict:
            {
                "success": bool,
                "result": Any or error message,
                "stdout": str,
                "stderr": str
            }
        """
        # 1. AST Validation
        self.verify_code_security(code_str)

        # 2. Process Isolation Execution
        seed_val = seed if seed is not None else self.default_seed

        queue = multiprocessing.Queue()
        p = multiprocessing.Process(
            target=_process_target,
            args=(queue, code_str, entry_point, args_tuple, seed_val)
        )
        p.start()

        loop = asyncio.get_running_loop()
        def wait_and_get():
            try:
                # Wait for queue up to the strict wall-clock timeout SLA
                res = queue.get(timeout=self.wall_clock_timeout)
                p.join()
                return res
            except Exception:
                # Terminate the process forcibly to reclaim CPU/RAM immediately
                p.terminate()
                p.join()
                try:
                    p.close()
                except ValueError:
                    pass
                raise asyncio.TimeoutError()

        try:
            success, result, stdout, stderr = await loop.run_in_executor(None, wait_and_get)
            return {
                "success": success,
                "result": result,
                "stdout": stdout,
                "stderr": stderr
            }
        except asyncio.TimeoutError:
            logger.error(f"StrategySandbox: Wall-clock timeout of {self.wall_clock_timeout}s exceeded.")
            return {
                "success": False,
                "result": f"Execution timed out (timeout: {self.wall_clock_timeout}s)",
                "stdout": "",
                "stderr": ""
            }
        except Exception as e:
            logger.error(f"StrategySandbox: Execution failed: {e}")
            return {
                "success": False,
                "result": f"Execution failed: {str(e)}",
                "stdout": "",
                "stderr": ""
            }
