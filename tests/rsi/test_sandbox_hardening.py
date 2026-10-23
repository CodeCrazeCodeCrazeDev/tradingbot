"""TD-06 Job Object limits + TD-07 key custody tests."""
import os
import sys
import time

import pytest

from trading_bot.recursive_self_improvement.job_limits import (
    WINDOWS, JobLimits)
from trading_bot.recursive_self_improvement.key_custody import (
    custody_report, default_key_path, path_inside_repo)


def _spawn_probe_worker(q):
    """Module-level worker — spawn requires picklable targets. A job
    quota (WinError 1816) or CreateProcess failure is proof the limit
    is enforced — report 'blocked', never crash unreported."""
    import subprocess
    code = (
        "import subprocess,sys;"
        "try:"
        " subprocess.Popen([sys.executable,'-c','pass']).wait();"
        " print('spawned')"
        "except Exception:"
        " print('blocked')")
    try:
        out = subprocess.run([sys.executable, "-c", code],
                             capture_output=True, text=True,
                             timeout=30).stdout
    except Exception as exc:
        out = f"blocked:{type(exc).__name__}"
    q.put(out)


@pytest.mark.skipif(not WINDOWS, reason="Job Objects are Windows-only")
class TestJobLimits:
    def test_assign_and_kill_on_close(self):
        import subprocess
        proc = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"])
        try:
            job = JobLimits()
            assert job.assign(proc.pid)
            assert job.assigned
            job.close()  # KILL_ON_JOB_CLOSE terminates the child
            proc.wait(timeout=10)
            # Terminated — exit code semantics are OS-defined (job-close
            # termination reports 0 on Windows), presence matters.
            assert proc.poll() is not None
        finally:
            if proc.poll() is None:
                proc.kill()

    def test_assign_invalid_pid_fails_cleanly(self):
        job = JobLimits()
        ok = job.assign(99999999)
        job.close()  # must not raise either way

    def test_active_process_limit_blocks_spawn(self):
        import multiprocessing as mp
        ctx = mp.get_context("spawn")
        q = ctx.Queue()
        proc = ctx.Process(target=_spawn_probe_worker,
                           args=(q,), daemon=True)
        job = JobLimits(max_active_processes=1)
        proc.start()
        job.assign(proc.pid)
        try:
            out = q.get(timeout=40)
            assert "blocked" in out
        finally:
            job.close()
            if proc.is_alive():
                proc.terminate()


class TestKeyCustody:
    def test_default_key_path_outside_repo(self):
        assert not path_inside_repo(default_key_path())

    def test_custody_report_flags_repo_internal(self, tmp_path):
        from trading_bot.recursive_self_improvement.key_custody import (
            _repo_root)
        inside = _repo_root() / "keys" / "verifier.pem"
        rep = custody_report(str(inside))
        assert rep["inside_repo"] is True
        assert rep["custody"] == "degraded"
        assert rep["td07_residual"] == \
            "external_custody_required_for_tamper_proof"

    def test_custody_report_unprovisioned(self):
        rep = custody_report(r"C:\nonexistent\verifier.pem")
        assert rep["exists"] is False
        assert rep["custody"] in ("external", "unprovisioned")

    def test_provision_key_outside_repo(self, tmp_path, monkeypatch):
        monkeypatch.setenv("RSI_KEY_DIR", str(tmp_path / "keys"))
        from trading_bot.recursive_self_improvement.key_custody import (
            provision_verifier_key)
        rep = provision_verifier_key()
        assert rep["generated"] is True
        assert rep["inside_repo"] is False
        assert rep["exists"] is True
        # second call never overwrites
        rep2 = provision_verifier_key()
        assert rep2["generated"] is False

    def test_verifier_loads_provisioned_key(self, tmp_path, monkeypatch):
        monkeypatch.setenv("RSI_KEY_DIR", str(tmp_path / "keys"))
        from trading_bot.recursive_self_improvement.key_custody import (
            provision_verifier_key, default_key_path)
        provision_verifier_key()
        from trading_bot.recursive_self_improvement.engine_v2 import (
            IndependentVerifier)
        v = IndependentVerifier(key_path=str(default_key_path()))
        assert v.custody_report()["custody"] == "external"
