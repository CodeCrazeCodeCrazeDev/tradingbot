"""Trust-boundary types for RSI evidence custody.

These types exist so that promotion-relevant claims can be bound to
independently custodied inputs instead of self-reported flags. Every consumer
fails closed: a missing, malformed or unverifiable boundary object degrades the
verdict to ``insufficient_evidence``.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

logger = logging.getLogger(__name__)


def _canonical(data: Mapping[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class HoldoutAttestation:
    """Operator-signed release of a sealed holdout dataset manifest.

    The attestation binds a dataset manifest hash to a release event. It is
    only meaningful when its signature verifies under the operator trust anchor
    and ``dataset_manifest_hash`` matches the evaluation contract's
    ``dataset_hash``. An expired or mismatched attestation is treated as absent.
    """

    dataset_manifest_hash: str
    custodian: str
    released_at: float
    expires_at: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_manifest_hash": self.dataset_manifest_hash,
            "custodian": self.custodian,
            "released_at": self.released_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "HoldoutAttestation":
        return cls(
            dataset_manifest_hash=str(data["dataset_manifest_hash"]),
            custodian=str(data["custodian"]),
            released_at=float(data["released_at"]),
            expires_at=float(data["expires_at"]),
        )

    def is_valid(self, *, dataset_hash: str, now: Optional[float] = None) -> bool:
        current = time.time() if now is None else now
        return (
            self.dataset_manifest_hash == dataset_hash
            and bool(self.dataset_manifest_hash)
            and math.isfinite(self.released_at)
            and math.isfinite(self.expires_at)
            and self.released_at <= current < self.expires_at
        )

    def verify_signature(self, signature_hex: str, public_key: Any) -> bool:
        try:
            public_key.verify(bytes.fromhex(signature_hex), _canonical(self.to_dict()))
            return True
        except (ValueError, TypeError, AttributeError):
            return False
        except Exception as exc:
            from cryptography.exceptions import InvalidSignature
            if isinstance(exc, InvalidSignature):
                return False
            raise


class CostModelRegistry:
    """Registry of recognized transaction-cost models.

    Only entries with ``source == "measured"`` satisfy promotion-boundary
    requirements; assumed or heuristic cost models remain acceptable for
    diagnostics but cannot carry an ``eligible_for_operator_review`` verdict.
    """

    def __init__(self, entries: Optional[Mapping[str, Mapping[str, Any]]] = None) -> None:
        self._entries: Dict[str, Dict[str, Any]] = {k: dict(v) for k, v in (entries or {}).items()}

    def register(self, cost_model_id: str, *, source: str, **metadata: Any) -> None:
        if not cost_model_id:
            raise ValueError("cost_model_id must be non-empty")
        self._entries[cost_model_id] = {"source": source, **metadata}

    def get(self, cost_model_id: str) -> Optional[Dict[str, Any]]:
        entry = self._entries.get(cost_model_id)
        return dict(entry) if entry else None

    def is_measured(self, cost_model_id: str) -> bool:
        entry = self._entries.get(cost_model_id)
        return bool(entry) and entry.get("source") == "measured"


def load_key_file(path: Any) -> Any:
    """Load an Ed25519 public key held by an external custodian.

    Only filesystem paths are accepted — keys are never inlined into configs or
    logs. Returns ``None`` when the path is missing or the content is not a
    valid PEM public key; callers must treat ``None`` as fail-closed.
    """
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        raw = Path(path).read_bytes()
        key = serialization.load_pem_public_key(raw)
        return key if isinstance(key, Ed25519PublicKey) else None
    except Exception as exc:
        logger.warning("key custody load failed for %s: %s", path, exc)
        return None


def build_paired_envelope(per_symbol_rows: Mapping[str, Any]) -> Dict[str, Any]:
    """Normalize an independently custodied per-instrument dataset into the
    paired-bar envelope consumed by ``evaluate_verified``.

    Validates provenance fields, enforces the shared row schema, and never
    fabricates missing instruments — single-instrument input legitimately fails
    the downstream ``min_instruments`` gate.
    """
    required = {
        "symbol", "timestamp", "cost_bps",
        "baseline_net", "candidate_net", "baseline_gross", "candidate_gross",
        "baseline_turnover", "candidate_turnover",
        "baseline_exposure", "candidate_exposure",
    }
    rows = []
    for symbol, symbol_rows in per_symbol_rows.items():
        if not isinstance(symbol, str) or not symbol:
            raise ValueError("instrument symbol must be a non-empty string")
        for row in symbol_rows:
            missing = required - set(row)
            if missing:
                raise ValueError(f"paired evidence row missing fields: {sorted(missing)}")
            normalized = dict(row)
            normalized["symbol"] = symbol
            rows.append(normalized)
    return {"bars": rows}


def envelope_digest(bars: Any) -> str:
    """Stable digest for binding an envelope into a dataset manifest."""
    return hashlib.sha256(_canonical({"bars": list(bars)})).hexdigest()
