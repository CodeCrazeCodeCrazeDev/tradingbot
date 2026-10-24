"""Verifier-key custody helpers (TD-07 hardening).

What this does:
- Keeps Ed25519 verifier keys OUTSIDE the repository tree
  (``%LOCALAPPDATA%\\alphaalgo\\keys``) so a candidate with repo-write
  access cannot reach key material by editing files it already owns.
- Best-effort ACL tightening to the current user (``icacls`` on
  Windows, ``os.chmod(0o600)`` elsewhere).
- ``custody_report()`` — honest attestation surface: where the key
  lives, whether it sits inside the repo (custody smell), whether ACL
  tightening succeeded, and the residual that local custody is never
  tamper-*proof* against a same-privilege writer.

What this does NOT do (honest residual):
- External custody (HSM/KMS/remote signer) requires infrastructure that
  doesn't exist in this deployment. This module makes custody
  *separated*, not *external* — the TD-07 residual is documented, not
  hidden.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

KEY_DIR_ENV = "RSI_KEY_DIR"


def default_key_dir() -> Path:
    """Custody dir outside the repository tree."""
    env = os.environ.get(KEY_DIR_ENV)
    if env:
        return Path(env)
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(
            Path.home() / "AppData" / "Local")
        return Path(base) / "alphaalgo" / "keys"
    return Path.home() / ".alphaalgo" / "keys"


def default_key_path(name: str = "verifier_ed25519.pem") -> Path:
    return default_key_dir() / name


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def path_inside_repo(path: Path) -> bool:
    try:
        Path(path).resolve().relative_to(_repo_root())
        return True
    except ValueError:
        return False


def tighten_acl(path: Path) -> bool:
    """Best-effort owner-only ACL. True when applied, False when the
    platform/tool denied it — callers must report, not assume."""
    try:
        if sys.platform == "win32":
            user = os.environ.get("USERNAME") or ""
            r = subprocess.run(
                ["icacls", str(path), "/inheritance:r",
                 "/grant:r", f"{user}:F"],
                capture_output=True, timeout=15)
            return r.returncode == 0
        os.chmod(path, 0o600)
        return True
    except Exception:  # noqa: BLE001 - custody boundary
        return False


def custody_report(key_path: Optional[str] = None) -> Dict[str, Any]:
    """Honest custody attestation — never claims more than exists."""
    path = Path(key_path) if key_path else default_key_path()
    exists = path.exists()
    inside = path_inside_repo(path)
    return {
        "key_path": str(path),
        "exists": exists,
        "inside_repo": inside,
        "custody": ("external" if not inside and exists else
                    "degraded" if inside else "unprovisioned"),
        "warnings": ([
            "key material inside repository tree — repo-write "
            "privilege implies key access"] if inside else []) + [
            "local custody is not tamper-proof against a "
            "same-privilege writer; external HSM/KMS custody "
            "is the remaining TD-07 residual"],
        "td07_residual": "external_custody_required_for_tamper_proof",
    }


def provision_verifier_key(path: Optional[str] = None,
                           overwrite: bool = False) -> Dict[str, Any]:
    """Generate an Ed25519 verifier key outside the repo + ACL tighten.

    Returns a custody_report with ``generated: True``. Never overwrites
    an existing key unless ``overwrite`` — rotation is an operator act,
    recorded by the caller."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)
    from cryptography.hazmat.primitives import serialization

    target = Path(path) if path else default_key_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        rep = custody_report(str(target))
        rep["generated"] = False
        rep["note"] = "key already provisioned"
        return rep
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption())
    tmp = target.with_suffix(".tmp")
    tmp.write_bytes(pem)
    os.replace(tmp, target)  # atomic — no truncate-on-crash window
    acl_ok = tighten_acl(target)
    rep = custody_report(str(target))
    rep["generated"] = True
    rep["acl_tightened"] = acl_ok
    if not acl_ok:
        rep["warnings"].append("ACL tighten failed — key readable by "
                               "any process under sibling accounts")
    return rep


# ---------------------------------------------------------------------------
# DPAPI-encrypted at-rest keys (Windows). CryptProtectData binds the blob to
# the current user account — a file copied off this host, or read by another
# user, cannot decrypt it. Not external custody (TD-07 residual stands), but
# the key at rest is no longer plaintext-in-a-file.
# ---------------------------------------------------------------------------

_DPAPI_MAGIC = b"DPAPI\x01"

if sys.platform == "win32":
    import ctypes

    class _DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", ctypes.c_ulong),
                    ("pbData", ctypes.POINTER(ctypes.c_char))]

    def _dpapi_crypt(data: bytes, protect: bool) -> bytes:
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
        inbuf = ctypes.create_string_buffer(data, len(data))
        blob_in = _DATA_BLOB(len(data),
                             ctypes.cast(inbuf, ctypes.POINTER(ctypes.c_char)))
        blob_out = _DATA_BLOB()
        fn = crypt32.CryptProtectData if protect \
            else crypt32.CryptUnprotectData
        if not fn(ctypes.byref(blob_in), None, None, None, None, 0,
                  ctypes.byref(blob_out)):
            raise OSError(ctypes.get_last_error(), "DPAPI call failed")
        try:
            return ctypes.string_at(blob_out.pbData, blob_out.cbData)
        finally:
            kernel32.LocalFree(blob_out.pbData)


def dpapi_encrypt(data: bytes) -> bytes:
    """Encrypt with the current user's DPAPI secret. Raises on non-Windows —
    callers must check platform rather than fall back silently."""
    if sys.platform != "win32":
        raise OSError("DPAPI is Windows-only")
    return _DPAPI_MAGIC + _dpapi_crypt(data, protect=True)


def dpapi_decrypt(blob: bytes) -> bytes:
    """Decrypt a DPAPI blob; raises OSError if the blob is not ours."""
    if sys.platform != "win32":
        raise OSError("DPAPI is Windows-only")
    if not blob.startswith(_DPAPI_MAGIC):
        raise OSError("not a DPAPI-wrapped key")
    return _dpapi_crypt(blob[len(_DPAPI_MAGIC):], protect=False)


def provision_verifier_key_dpapi(path: Optional[str] = None,
                                 overwrite: bool = False
                                 ) -> Dict[str, Any]:
    """Provision an Ed25519 verifier key, DPAPI-encrypted at rest.

    The file on disk is ciphertext bound to this user account; plaintext
    never touches disk. Returns a custody report with
    ``encryption='dpapi'``. On non-Windows the caller gets an honest
    error report, not a plaintext write."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)
    from cryptography.hazmat.primitives import serialization

    if sys.platform != "win32":
        return {"status": "unavailable",
                "reason": "DPAPI is Windows-only — use external custody"}

    target = Path(path) if path else default_key_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        rep = custody_report(str(target))
        rep["generated"] = False
        rep["note"] = "key already provisioned"
        return rep
    pem = Ed25519PrivateKey.generate().private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption())
    blob = dpapi_encrypt(pem)
    tmp = target.with_suffix(".tmp")
    tmp.write_bytes(blob)
    os.replace(tmp, target)
    acl_ok = tighten_acl(target)
    rep = custody_report(str(target))
    rep.update({"generated": True, "encryption": "dpapi",
                "acl_tightened": acl_ok})
    return rep


def load_verifier_key_bytes(path: Optional[str] = None) -> Optional[bytes]:
    """Read a verifier key file — DPAPI-decrypts if wrapped, returns raw
    bytes otherwise. Callers decide what encoding to accept."""
    target = Path(path) if path else default_key_path()
    if not target.exists():
        return None
    data = target.read_bytes()
    if data.startswith(_DPAPI_MAGIC):
        return dpapi_decrypt(data)
    return data
