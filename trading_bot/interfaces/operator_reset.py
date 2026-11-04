"""Signed, offline recovery of a stopped paper runner.

The operator signs interactively; the consumer needs only a pinned public
key outside the repository. Approval is scoped to one database and incident.
The emergency flag, consumed nonce and audit receipt commit atomically.
Local DPAPI custody does not protect against another process as the same user.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
import time
import uuid

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class ResetApprovalError(ValueError):
    pass


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def database_path(state_dir: Path) -> Path:
    return (Path(state_dir).resolve() / "trading_state.db").resolve()


def key_directory(state_dir: Path) -> Path:
    resource = os.path.normcase(str(database_path(state_dir)))
    base = (Path(os.environ["LOCALAPPDATA"]) if sys.platform == "win32"
            else Path.home() / ".local" / "share")
    return base / "alphaalgo" / "operator_keys" / hashlib.sha256(
        resource.encode()).hexdigest()


@contextmanager
def runner_lock(state_dir: Path):
    """OS-owned lock: released even after a crash, never deleted while held."""
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    with (state_dir / "runner.lock").open("a+b") as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ResetApprovalError("Runner is active or another operator holds the lock.") from exc
        try:
            yield
        finally:
            handle.seek(0)
            if sys.platform == "win32":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _check_paper_state(state_dir: Path) -> None:
    snapshot = json.loads((Path(state_dir) / "snapshot.json").read_text(encoding="utf-8"))
    if snapshot.get("mode") != "paper":
        raise ResetApprovalError("This recovery interface is restricted to paper runs.")
    if any((Path(state_dir) / "control").glob("cmd-*.json")):
        raise ResetApprovalError("Pending operator commands must be resolved before reset.")


def _incident(connection: sqlite3.Connection) -> str:
    row = connection.execute(
        "SELECT value,updated_at FROM account_state WHERE key='control:emergency'"
    ).fetchone()
    if not row or row[0] != "1":
        raise ResetApprovalError("No persisted emergency stop is active.")
    return hashlib.sha256(canonical({"value": row[0], "updated_at": row[1]})).hexdigest()


def reset_request(state_dir: Path, user: str, reason: str) -> dict:
    _check_paper_state(state_dir)
    if not user.strip() or not reason.strip():
        raise ResetApprovalError("An operator identity and incident acknowledgement are required.")
    db = database_path(state_dir)
    with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True) as con:
        incident = _incident(con)
    now = time.time()
    return {
        "version": 1, "action": "reset_emergency", "mode": "paper",
        "database": os.path.normcase(str(db)), "incident": incident,
        "issued_by": user, "reason": reason, "issued_at": now,
        "expires_at": now + 900, "nonce": uuid.uuid4().hex,
    }


def sign_interactively(state_dir: Path, payload: dict) -> dict:
    """Only called by the operator CLI, never by the runner."""
    if not sys.stdin.isatty():
        raise ResetApprovalError("Signing requires an interactive operator terminal.")
    target = key_directory(state_dir)
    print(json.dumps(payload, indent=2))
    print("This clears only this paper run's emergency stop. Pause and risk gates remain.")
    print("Operator key:", target)
    print("If unprovisioned, a new Ed25519 key will be enrolled here, encrypted with Windows DPAPI.")
    if input("Type RESET PAPER to sign this approval: ").strip() != "RESET PAPER":
        raise ResetApprovalError("Approval cancelled; emergency stop unchanged.")
    if sys.platform != "win32":
        raise ResetApprovalError("Interactive custody requires Windows DPAPI; use an external signer.")
    from trading_bot.recursive_self_improvement.key_custody import (
        dpapi_decrypt, provision_verifier_key_dpapi, tighten_acl)

    private_path, public_path = target / "operator.dpapi", target / "operator.pub"
    repo = Path(__file__).resolve().parents[2]
    if target.resolve().is_relative_to(repo):
        raise ResetApprovalError("Operator keys must live outside the repository.")
    if public_path.exists() and not private_path.exists():
        raise ResetApprovalError("Pinned key has no local signer; use the existing external signer.")
    target.mkdir(parents=True, exist_ok=True)
    if not tighten_acl(target):
        raise ResetApprovalError("Cannot secure the operator key directory.")
    if not private_path.exists():
        report = provision_verifier_key_dpapi(str(private_path))
        if not report.get("acl_tightened"):
            raise ResetApprovalError("Cannot secure the operator private key.")
    key = serialization.load_pem_private_key(
        dpapi_decrypt(private_path.read_bytes()), password=None)
    public_bytes = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    if public_path.exists():
        if public_path.read_bytes() != public_bytes:
            raise ResetApprovalError("Signer does not match the pinned operator key.")
    else:
        with public_path.open("xb") as handle:
            handle.write(public_bytes)
    print("Operator public-key fingerprint:", hashlib.sha256(public_bytes).hexdigest())
    return {"payload": payload, "signature": key.sign(canonical(payload)).hex()}


def consume_reset(state_dir: Path, approval: dict) -> dict:
    """Caller holds runner_lock. Never accepts a public key from the approval."""
    _check_paper_state(state_dir)
    try:
        payload = approval["payload"]
        public_bytes = (key_directory(state_dir) / "operator.pub").read_bytes()
        Ed25519PublicKey.from_public_bytes(public_bytes).verify(
            bytes.fromhex(approval["signature"]), canonical(payload))
        now = time.time()
        issued, expires = payload["issued_at"], payload["expires_at"]
        if (not all(type(v) in (int, float) and math.isfinite(v) for v in (issued, expires))
                or not issued <= now < expires or not 0 < expires - issued <= 900):
            raise ResetApprovalError("Approval expired or has an invalid validity window.")
        if (payload["version"] != 1 or payload["action"] != "reset_emergency"
                or payload["mode"] != "paper"
                or payload["database"] != os.path.normcase(str(database_path(state_dir)))):
            raise ResetApprovalError("Approval does not match this paper database/action.")
        nonce = payload["nonce"]
        if not isinstance(nonce, str) or len(nonce) != 32 or uuid.UUID(hex=nonce).hex != nonce:
            raise ResetApprovalError("Invalid approval nonce.")
        if not isinstance(payload["issued_by"], str) or not payload["issued_by"].strip():
            raise ResetApprovalError("Missing operator identity.")
        if not isinstance(payload["reason"], str) or not payload["reason"].strip():
            raise ResetApprovalError("Missing incident acknowledgement.")
        if not isinstance(payload["incident"], str) or len(payload["incident"]) != 64:
            raise ResetApprovalError("Invalid incident binding.")
    except (KeyError, TypeError, ValueError, OSError, InvalidSignature) as exc:
        raise ResetApprovalError(f"Approval rejected: {exc}") from exc

    with sqlite3.connect(database_path(state_dir).as_uri() + "?mode=rw", uri=True) as con:
        con.execute("BEGIN IMMEDIATE")
        if payload["incident"] != _incident(con):
            raise ResetApprovalError("Emergency incident changed since approval.")
        consumed_key = "control:reset_used:" + nonce
        if con.execute("SELECT 1 FROM account_state WHERE key=?", (consumed_key,)).fetchone():
            raise ResetApprovalError("Approval has already been consumed.")
        now_iso = datetime.now(timezone.utc).isoformat()
        receipt = {
            "event_type": "operator_control", "actor": payload["issued_by"],
            "action": "reset_emergency", "outcome": "applied",
            "correlation_id": nonce, "occurred_at": now_iso,
            "details": {"approval": approval,
                        "key_fingerprint": hashlib.sha256(public_bytes).hexdigest(),
                        "emergency_cleared": True, "scope": "offline_paper"},
        }
        con.execute(
            "INSERT INTO account_state(key,value,updated_at) VALUES(?,?,?)",
            (consumed_key, payload["incident"], now_iso))
        con.execute(
            "INSERT INTO audit_events "
            "(audit_id,event_type,actor,action,outcome,correlation_id,event_json,occurred_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (uuid.uuid4().hex, "operator_control", payload["issued_by"],
             "reset_emergency", "applied", nonce, json.dumps(receipt), now_iso))
        con.execute(
            "UPDATE account_state SET value='0',updated_at=? WHERE key='control:emergency'",
            (now_iso,))
    return receipt
