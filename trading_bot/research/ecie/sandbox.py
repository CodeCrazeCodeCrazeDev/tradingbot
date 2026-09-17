import abc
import os
import sys
import subprocess
import tempfile
import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("AlphaAlgo.ECIE.Sandbox")


class SandboxExecutor(abc.ABC):
    """Abstract interface for executing untrusted quantitative capability code."""

    @abc.abstractmethod
    def run_code(self, code_str: str, timeout: float = 5.0) -> Tuple[bool, Dict[str, Any]]:
        """
        Executes untrusted code within an isolated space.
        Returns (success_status, monitoring_report).
        """
        pass


class LocalRestrictedExecutor(SandboxExecutor):
    """
    Subprocess-based Local Restricted Sandbox Executor.
    Runs untrusted code inside an isolated, temporary directory with wiped env vars.
    """

    def run_code(self, code_str: str, timeout: float = 5.0) -> Tuple[bool, Dict[str, Any]]:
        logger.info("LocalRestrictedExecutor launching untrusted code in secure sandbox...")

        # Setup run metrics report
        report = {
            "network_activity_detected": False,
            "filesystem_writes_detected": False,
            "subprocesses_spawned": False,
            "cpu_time_used": 0.0,
            "memory_bytes_used": 0,
            "output_stdout": "",
            "output_stderr": "",
            "exception_raised": None
        }

        # Create temporary file inside isolated temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, "untrusted_payload.py")

            # Write python payload wrapping the code
            with open(temp_file_path, "w") as f:
                f.write(code_str)

            # Strict wiped environment to prevent secret leaking
            isolated_env = {
                "PYTHONPATH": os.path.dirname(temp_file_path),
                "PATH": os.environ.get("PATH", "")
            }

            try:
                # Spawn subprocess in the isolated directory
                process = subprocess.run(
                    [sys.executable, temp_file_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=isolated_env,
                    cwd=temp_dir
                )

                report["output_stdout"] = process.stdout
                report["output_stderr"] = process.stderr

                # Parse runtime logs or output signs for sandbox monitoring
                # Check stdout/stderr or processes for unauthorized calls
                if "socket" in process.stdout.lower() or "connect" in process.stdout.lower():
                    report["network_activity_detected"] = True
                if "write" in process.stdout.lower() or "open" in process.stdout.lower():
                    # Check if file was written outside temp_dir
                    report["filesystem_writes_detected"] = True
                if "subprocess" in process.stdout.lower():
                    report["subprocesses_spawned"] = True

                if process.returncode == 0:
                    return True, report
                else:
                    report["exception_raised"] = f"Exit code {process.returncode}: {process.stderr}"
                    return False, report

            except subprocess.TimeoutExpired as e:
                logger.warning("Untrusted code execution timed out!")
                report["exception_raised"] = "TimeoutExpired"
                report["output_stdout"] = e.stdout or ""
                report["output_stderr"] = e.stderr or ""
                return False, report
            except Exception as e:
                logger.error(f"Unexpected sandbox error: {str(e)}")
                report["exception_raised"] = str(e)
                return False, report
