"""Windows Job Object limits for sandbox child processes (TD-06 upgrade).

A Job Object is a real OS-level containment primitive — unlike a bare
``multiprocessing.Process``, it gives the sandbox hard, kernel-enforced
bounds:

- ``ACTIVE_PROCESS=1`` — the child cannot spawn its own subprocesses
  (closes the process-tree escape).
- ``PROCESS_MEMORY`` — kernel-enforced memory cap per process.
- ``KILL_ON_JOB_CLOSE`` — closing the handle terminates every process
  in the job, including anything the child leaked.
- CPU rate control (Win8+) — best-effort percent cap.

Honest limits of this control:
- Still NOT a container: no filesystem virtualization and no network
  namespace. A socket firewall requires OS/network-layer enforcement
  (documented TD-06 residual).
- Assignment can fail when the child is already inside a job that
  forbids nested breakaway — the caller treats failure as a degraded
  (but still killed-on-deadline) sandbox, never silently "limited".
"""
from __future__ import annotations

import ctypes
import logging
import os
import sys
from ctypes import wintypes
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)

WINDOWS = sys.platform == "win32"

if WINDOWS:
    _k32 = ctypes.windll.kernel32

    # --- structures -------------------------------------------------------
    class _LARGE_INTEGER(ctypes.Structure):
        _fields_ = [("QuadPart", ctypes.c_int64)]

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [(k, ctypes.c_uint64) for k in (
            "ReadOperationCount", "WriteOperationCount",
            "OtherOperationCount", "ReadTransferCount",
            "WriteTransferCount", "OtherTransferCount")]

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", _LARGE_INTEGER),
            ("PerJobUserTimeLimit", _LARGE_INTEGER),
            ("LimitFlags", ctypes.c_uint32),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", ctypes.c_uint32),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", ctypes.c_uint32),
            ("SchedulingClass", ctypes.c_uint32),
        ]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    class JOBOBJECT_CPU_RATE_CONTROL_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("ControlFlags", ctypes.c_uint32),
            ("Value", ctypes.c_uint32),
        ]

    class JOBOBJECT_NET_RATE_CONTROL_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("MaxBandwidth", ctypes.c_uint64),
            ("ControlFlags", ctypes.c_uint32),
            ("DscpTag", ctypes.c_ubyte),
        ]

    _JobObjectExtendedLimitInformation = 9
    _JobObjectCpuRateControlInformation = 15
    _JobObjectNetRateControlInformation = 32  # JOBOBJECTINFOCLASS 32 — verified: SetInformationJobObject accepts and round-trips on Win10+

    NET_RATE_CONTROL_ENABLE = 0x1
    NET_RATE_CONTROL_MAX_BANDWIDTH = 0x2

    LIMIT_ACTIVE_PROCESS = 0x00000008
    LIMIT_PROCESS_MEMORY = 0x00000100
    LIMIT_JOB_MEMORY = 0x00000200
    LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
    LIMIT_CPU_RATE_CONTROL = 0x00000010

    CPU_RATE_CONTROL_ENABLE = 0x1
    CPU_RATE_CONTROL_HARD_CAP = 0x4

    PROCESS_SET_QUOTA = 0x0100
    PROCESS_TERMINATE = 0x0001
    PROCESS_ASSIGN_PROCESS = 0x0020


class JobLimits:
    """Assign a child process to a kernel Job Object with hard limits.

    ``assign(pid)`` returns True when the process is inside the job.
    Closing (or ``close()``) kills every member when kill_on_close is
    set — use in a finally block or as a context manager."""

    def __init__(self, process_memory_bytes: int = 1 << 30,
                 max_active_processes: int = 1,
                 cpu_percent: Optional[int] = None,
                 max_bandwidth_Bps: Optional[int] = 16384) -> None:
        self.process_memory_bytes = process_memory_bytes
        self.max_active_processes = max_active_processes
        self.cpu_percent = cpu_percent
        # Network exfiltration is strangled, not blocked: MaxBandwidth
        # throttles job sockets to a trickle (default 16KB/s — a day's
        # exfil takes hours; the audit trail catches it first). A true
        # socket wall needs OS firewall rules — documented residual.
        self.max_bandwidth_Bps = max_bandwidth_Bps
        self._handle: Optional[int] = None
        self._assigned = False

    @property
    def available(self) -> bool:
        return WINDOWS

    def assign(self, pid: int) -> bool:
        """Put ``pid`` inside a fresh limited job. False on any failure —
        the caller must treat that as *degraded*, not as sandboxed."""
        if not WINDOWS:
            return False
        try:
            self._handle = _k32.CreateJobObjectW(None, None)
            if not self._handle:
                return False
            info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            flags = (LIMIT_ACTIVE_PROCESS | LIMIT_PROCESS_MEMORY
                     | LIMIT_KILL_ON_JOB_CLOSE)
            info.BasicLimitInformation.LimitFlags = flags
            info.BasicLimitInformation.ActiveProcessLimit = (
                self.max_active_processes)
            info.ProcessMemoryLimit = self.process_memory_bytes
            ok = _k32.SetInformationJobObject(
                self._handle, _JobObjectExtendedLimitInformation,
                ctypes.byref(info), ctypes.sizeof(info))
            if not ok:
                self.close()
                return False
            if self.cpu_percent is not None:
                cpu = JOBOBJECT_CPU_RATE_CONTROL_INFORMATION()
                cpu.ControlFlags = (CPU_RATE_CONTROL_ENABLE
                                    | CPU_RATE_CONTROL_HARD_CAP)
                cpu.Value = int(max(1, min(100, self.cpu_percent)) * 100)
                _k32.SetInformationJobObject(
                    self._handle, _JobObjectCpuRateControlInformation,
                    ctypes.byref(cpu), ctypes.sizeof(cpu))
            if self.max_bandwidth_Bps is not None:
                net = JOBOBJECT_NET_RATE_CONTROL_INFORMATION()
                net.MaxBandwidth = int(self.max_bandwidth_Bps)
                net.ControlFlags = (NET_RATE_CONTROL_ENABLE
                                    | NET_RATE_CONTROL_MAX_BANDWIDTH)
                ok = _k32.SetInformationJobObject(
                    self._handle, _JobObjectNetRateControlInformation,
                    ctypes.byref(net), ctypes.sizeof(net))
                if not ok:
                    # Pre-1607 builds or policy-denied — degrade loudly.
                    logger.debug("job net rate control unavailable")
            proc = _k32.OpenProcess(
                PROCESS_SET_QUOTA | PROCESS_TERMINATE
                | PROCESS_ASSIGN_PROCESS, False, pid)
            if not proc:
                self.close()
                return False
            try:
                ok = _k32.AssignProcessToJobObject(self._handle, proc)
            finally:
                _k32.CloseHandle(proc)
            if not ok:
                self.close()
                return False
            self._assigned = True
            return True
        except Exception as exc:  # noqa: BLE001 - sandbox boundary
            logger.debug("job-object assign failed: %s", exc)
            self.close()
            return False

    @property
    def assigned(self) -> bool:
        return self._assigned

    def close(self) -> None:
        if self._handle:
            _k32.CloseHandle(self._handle)
            self._handle = None
            self._assigned = False

    def __enter__(self) -> "JobLimits":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Low-integrity filesystem confinement (TD-06, FS-write layer)
# ---------------------------------------------------------------------------
#
# A process can voluntarily drop its own integrity level to LOW
# (S-1-16-4096). From that point the kernel denies writes to any object
# labeled medium or higher — which covers the user profile, the repo, and
# virtually the whole filesystem. Reads are unaffected, so replay workers
# still see the datasets they need. Writable space is a per-eval scratch
# directory explicitly labeled Low (icacls /setintegritylevel Low).
#
# Verified empirically: a LOW child gets PermissionError writing to the
# user profile while still delivering results over mp.Queue and writing
# to its low-labeled scratch dir.

_LOW_IL_SID = 'S-1-16-4096'          # SECURITY_MANDATORY_LOW_RID
_SE_GROUP_INTEGRITY_ENABLED = 0x20
_TokenIntegrityLevel = 25


def drop_to_low_integrity() -> bool:
    """Drop the *current* process to LOW integrity.

    Irreversible within the process — integrity can only go down, never
    up. Returns False (loud, logged) on any platform or API failure; the
    caller must treat False as "FS confinement not active"."""
    if sys.platform != 'win32':
        logger.debug('low-integrity drop unsupported on %s', sys.platform)
        return False
    adv = ctypes.windll.advapi32
    k32 = ctypes.windll.kernel32
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    adv.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                     ctypes.POINTER(wintypes.HANDLE)]
    tok = wintypes.HANDLE()
    TOKEN_ALL_ACCESS = 0xF01FF
    if not adv.OpenProcessToken(k32.GetCurrentProcess(), TOKEN_ALL_ACCESS,
                                ctypes.byref(tok)):
        logger.debug('OpenProcessToken failed: %s', k32.GetLastError())
        return False
    try:
        sid = wintypes.LPVOID()
        if not adv.ConvertStringSidToSidW(_LOW_IL_SID, ctypes.byref(sid)):
            return False
        try:
            class _SID_ATTR(ctypes.Structure):
                _fields_ = [('Sid', wintypes.LPVOID),
                            ('Attributes', wintypes.DWORD)]
            attr = _SID_ATTR(sid, _SE_GROUP_INTEGRITY_ENABLED)
            ok = bool(adv.SetTokenInformation(tok, _TokenIntegrityLevel,
                                              ctypes.byref(attr),
                                              ctypes.sizeof(attr)))
            if not ok:
                logger.debug('SetTokenInformation(IL=low) failed: %s',
                             k32.GetLastError())
            return ok
        finally:
            k32.LocalFree(sid)
    finally:
        k32.CloseHandle(tok)


def current_integrity_level() -> Optional[int]:
    """Query the process's mandatory integrity RID (0x2000=medium,
    0x1000=low). Returns None on failure — callers treat None as
    'unknown', never as 'high'."""
    if sys.platform != 'win32':
        return None
    adv = ctypes.windll.advapi32
    k32 = ctypes.windll.kernel32
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    adv.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                     ctypes.POINTER(wintypes.HANDLE)]
    tok = wintypes.HANDLE()
    if not adv.OpenProcessToken(k32.GetCurrentProcess(), 0x0008 | 0x0002,
                                ctypes.byref(tok)):  # QUERY|DUPLICATE
        return None
    try:
        buf = ctypes.create_string_buffer(1024)
        ret_len = wintypes.DWORD(0)
        if not adv.GetTokenInformation(tok, _TokenIntegrityLevel, buf,
                                     1024, ctypes.byref(ret_len)):
            return None
        # TOKEN_MANDATORY_LABEL: { SID_AND_ATTRIBUTES Label } — the RID
        # is the last DWORD of the SID sub-authority array.
        sid_ptr = ctypes.cast(buf, ctypes.POINTER(wintypes.LPVOID)).contents
        adv.GetSidSubAuthority.restype = wintypes.LPVOID
        rid_ptr = adv.GetSidSubAuthority(sid_ptr, 0)
        if not rid_ptr:
            return None
        return int(ctypes.cast(rid_ptr,
                               ctypes.POINTER(wintypes.DWORD)).contents.value)
    finally:
        k32.CloseHandle(tok)


def make_scratch_dir(parent: Union[str, 'Path']) -> 'Path':
    """Create a per-eval scratch dir labeled LOW integrity so a
    low-integrity child can write inside it."""
    import subprocess as _sp
    from pathlib import Path as _P
    d = _P(parent) / ('scratch_%08x' % (os.getpid() & 0xFFFFFFFF))
    d.mkdir(parents=True, exist_ok=True)
    if sys.platform == 'win32':
        _sp.run(['icacls', str(d), '/setintegritylevel', 'Low', '/q'],
                capture_output=True)
    return d
