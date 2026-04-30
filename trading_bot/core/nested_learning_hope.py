"""HOPE-inspired nested learning memory for AlphaAlgo.

This module adapts the Nested Learning / Hope ideas into AlphaAlgo's security
model: multi-timescale associative memory, surprise-weighted updates, signed
read-only snapshots, and no production self-modification.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from trading_bot.core.signal_counterintelligence import (
    AppendOnlyJsonlAuditLedger,
    DataPassportValidationResult,
    ImmutableAuditLedger,
    IntelligenceDecision,
    IntelligenceRole,
    IntelligenceZone,
)


@dataclass
class HopeMemoryTier:
    """One nested optimization level with its own context flow and update rate."""

    name: str
    update_every: int
    decay: float
    capacity: int
    surprise_threshold: float = 0.15

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HopeObservation:
    """One supervised market outcome entering the research/staging memory loop."""

    observation_id: str
    signal_id: str
    asset: str
    timestamp: float
    features: Dict[str, float]
    prediction: float
    realized_outcome: float
    regime: str
    lineage_hashes: List[str]
    passport_id: str = ""
    source_quality: float = 1.0

    @property
    def surprise(self) -> float:
        return abs(float(self.realized_outcome) - float(self.prediction))

    def vector(self) -> Dict[str, float]:
        payload = {str(key): float(value) for key, value in self.features.items()}
        payload["prediction"] = float(self.prediction)
        payload["realized_outcome"] = float(self.realized_outcome)
        payload["surprise"] = self.surprise
        payload["source_quality"] = float(self.source_quality)
        return payload

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HopeMemoryEntry:
    """Associative-memory entry compressed from one or more observations."""

    entry_id: str
    tier: str
    signal_id: str
    asset: str
    regime: str
    key_hash: str
    value_vector: Dict[str, float]
    surprise_score: float
    weight: float
    lineage_hashes: List[str]
    created_at: float
    updated_at: float
    update_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HopeUpdateReport:
    """Result of a nested-learning update attempt."""

    accepted: bool
    observation_id: str
    zone: IntelligenceZone
    role: IntelligenceRole
    updated_tiers: List[str]
    blocked_reasons: List[str]
    surprise: float
    audit_digest: str

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["zone"] = self.zone.value
        data["role"] = self.role.value
        return data


@dataclass
class HopeRecommendation:
    """Read-side inference from nested memory."""

    signal_id: str
    asset: str
    regime: str
    memory_score: float
    confidence_adjustment: float
    matched_entries: List[str]
    context_flow_digests: Dict[str, str]
    snapshot_digest: str = ""
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HopeMemorySnapshot:
    """Signed read-only artifact carrying nested memory into production."""

    snapshot_id: str
    created_at: float
    source_zone: IntelligenceZone
    tiers: Dict[str, List[Dict[str, Any]]]
    digest: str
    signer: str
    signature: str
    read_only: bool = True

    def signing_payload(self) -> Dict[str, Any]:
        data = asdict(self)
        data["source_zone"] = self.source_zone.value
        data.pop("signature", None)
        return data

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["source_zone"] = self.source_zone.value
        return data


class NestedLearningHopeEngine:
    """Security-bounded Hope-style memory hierarchy.

    The engine updates only in research/staging zones. Production receives signed
    snapshots and can read recommendations, but cannot mutate memory.
    """

    default_tiers = (
        HopeMemoryTier("short_term", update_every=1, decay=0.85, capacity=64, surprise_threshold=0.05),
        HopeMemoryTier("episodic", update_every=3, decay=0.92, capacity=128, surprise_threshold=0.10),
        HopeMemoryTier("regime", update_every=5, decay=0.97, capacity=128, surprise_threshold=0.12),
        HopeMemoryTier("strategy", update_every=8, decay=0.985, capacity=256, surprise_threshold=0.18),
    )

    update_roles = {
        IntelligenceRole.RESEARCH_ANALYST,
        IntelligenceRole.STAGING_SYSTEM,
        IntelligenceRole.AI_ENGINEERING_AGENT,
    }

    def __init__(
        self,
        tiers: Optional[Sequence[HopeMemoryTier]] = None,
        audit_ledger: Optional[ImmutableAuditLedger] = None,
        signing_secret: str = "alphaalgo-nested-learning-hope",
    ):
        self.tiers = list(tiers or self.default_tiers)
        self.audit_ledger = audit_ledger or AppendOnlyJsonlAuditLedger()
        self.signing_secret = signing_secret
        self.memories: Dict[str, List[HopeMemoryEntry]] = {tier.name: [] for tier in self.tiers}
        self.update_clock = 0
        self.production_snapshot: Optional[HopeMemorySnapshot] = None

    def observe(
        self,
        observation: HopeObservation,
        role: IntelligenceRole,
        zone: IntelligenceZone,
        passport_validation: Optional[DataPassportValidationResult] = None,
    ) -> HopeUpdateReport:
        zone = self._coerce_zone(zone)
        reasons = self._update_reasons(observation, role, zone, passport_validation)
        updated_tiers: List[str] = []

        if not reasons:
            self.update_clock += 1
            for tier in self.tiers:
                if self._should_update_tier(tier, observation):
                    self._upsert_memory(tier, observation)
                    updated_tiers.append(tier.name)

        payload = {
            "observation": observation.to_dict(),
            "zone": zone.value,
            "role": role.value,
            "updated_tiers": updated_tiers,
            "blocked_reasons": reasons,
            "surprise": observation.surprise,
        }
        audit_record = self.audit_ledger.append(
            "hope_nested_learning_observation",
            payload,
            actor=role.value,
            action="observe",
            input_hash=self._hash_payload(observation.to_dict()),
            output_hash=self._hash_payload({"updated_tiers": updated_tiers, "reasons": reasons}),
        )
        return HopeUpdateReport(
            accepted=not reasons,
            observation_id=observation.observation_id,
            zone=zone,
            role=role,
            updated_tiers=updated_tiers,
            blocked_reasons=reasons,
            surprise=observation.surprise,
            audit_digest=audit_record.record_hash,
        )

    def recommend(
        self,
        signal_id: str,
        asset: str,
        regime: str,
        features: Mapping[str, float],
        zone: IntelligenceZone = IntelligenceZone.RESEARCH,
    ) -> HopeRecommendation:
        zone = self._coerce_zone(zone)
        memories = self._snapshot_entries() if zone == IntelligenceZone.PRODUCTION and self.production_snapshot else self.memories
        query = {str(key): float(value) for key, value in features.items()}
        matched: List[Tuple[HopeMemoryEntry, float]] = []
        context_digests: Dict[str, str] = {}

        for tier_name, entries in memories.items():
            context_digests[tier_name] = self._hash_payload([entry.to_dict() for entry in entries])
            for entry in entries:
                if entry.asset != asset:
                    continue
                regime_multiplier = 1.0 if entry.regime == regime else 0.6
                score = self._cosine_similarity(query, entry.value_vector) * regime_multiplier * entry.weight
                if score > 0:
                    matched.append((entry, score))

        matched.sort(key=lambda pair: pair[1], reverse=True)
        top = matched[:8]
        if not top:
            return HopeRecommendation(
                signal_id=signal_id,
                asset=asset,
                regime=regime,
                memory_score=0.0,
                confidence_adjustment=0.0,
                matched_entries=[],
                context_flow_digests=context_digests,
                snapshot_digest=self.production_snapshot.digest if self.production_snapshot else "",
                reasons=["no relevant nested memory"],
            )

        total_weight = sum(score for _, score in top) or 1.0
        outcome_bias = sum(entry.value_vector.get("realized_outcome", 0.0) * score for entry, score in top) / total_weight
        surprise_penalty = sum(entry.surprise_score * score for entry, score in top) / total_weight
        memory_score = max(-1.0, min(1.0, outcome_bias - surprise_penalty * 0.25))
        confidence_adjustment = max(-0.25, min(0.25, memory_score * 0.10 - surprise_penalty * 0.05))
        return HopeRecommendation(
            signal_id=signal_id,
            asset=asset,
            regime=regime,
            memory_score=round(memory_score, 6),
            confidence_adjustment=round(confidence_adjustment, 6),
            matched_entries=[entry.entry_id for entry, _ in top],
            context_flow_digests=context_digests,
            snapshot_digest=self.production_snapshot.digest if self.production_snapshot else "",
            reasons=["nested memory retrieved across " + str(len(context_digests)) + " context flows"],
        )

    def export_snapshot(
        self,
        signer: str,
        zone: IntelligenceZone = IntelligenceZone.STAGING,
    ) -> HopeMemorySnapshot:
        zone = self._coerce_zone(zone)
        if zone != IntelligenceZone.STAGING:
            raise PermissionError("HOPE memory snapshots must be signed from staging")
        tiers_payload = {
            tier_name: [entry.to_dict() for entry in entries]
            for tier_name, entries in sorted(self.memories.items())
        }
        digest = self._hash_payload(tiers_payload)
        created_at = time.time()
        snapshot_id = hashlib.sha256(f"{digest}:{created_at:.6f}:{signer}".encode("utf-8")).hexdigest()[:16]
        snapshot = HopeMemorySnapshot(
            snapshot_id=snapshot_id,
            created_at=created_at,
            source_zone=zone,
            tiers=tiers_payload,
            digest=digest,
            signer=signer,
            signature="",
            read_only=True,
        )
        snapshot.signature = self._sign_snapshot(snapshot)
        self.audit_ledger.append(
            "hope_memory_snapshot_exported",
            snapshot.to_dict(),
            actor=signer,
            action="export_snapshot",
            artifact_hash=digest,
        )
        return snapshot

    def load_production_snapshot(self, snapshot: HopeMemorySnapshot) -> bool:
        if not self.verify_snapshot(snapshot):
            return False
        if snapshot.source_zone != IntelligenceZone.STAGING or not snapshot.read_only:
            return False
        self.production_snapshot = snapshot
        return True

    def verify_snapshot(self, snapshot: HopeMemorySnapshot) -> bool:
        if snapshot.digest != self._hash_payload(snapshot.tiers):
            return False
        return hmac.compare_digest(snapshot.signature, self._sign_snapshot(snapshot))

    def attempt_production_update(self, observation: HopeObservation) -> HopeUpdateReport:
        return self.observe(
            observation,
            role=IntelligenceRole.PRODUCTION_RUNTIME,
            zone=IntelligenceZone.PRODUCTION,
        )

    def _update_reasons(
        self,
        observation: HopeObservation,
        role: IntelligenceRole,
        zone: IntelligenceZone,
        passport_validation: Optional[DataPassportValidationResult],
    ) -> List[str]:
        reasons: List[str] = []
        if zone == IntelligenceZone.PRODUCTION:
            reasons.append("production nested memory is read-only")
        if zone not in {IntelligenceZone.RESEARCH, IntelligenceZone.STAGING}:
            reasons.append("updates are only allowed in research or staging")
        if role not in self.update_roles:
            reasons.append(f"role {role.value} cannot update HOPE memory")
        if not observation.lineage_hashes:
            reasons.append("observation requires provenance lineage hashes")
        if observation.source_quality < 0.80:
            reasons.append("source quality below nested-learning threshold")
        if passport_validation is not None and not passport_validation.accepted:
            reasons.extend(passport_validation.reasons)
        return reasons

    def _should_update_tier(self, tier: HopeMemoryTier, observation: HopeObservation) -> bool:
        return (
            self.update_clock % max(1, tier.update_every) == 0
            or observation.surprise >= tier.surprise_threshold
        )

    def _upsert_memory(self, tier: HopeMemoryTier, observation: HopeObservation) -> None:
        key_hash = self._memory_key_hash(tier.name, observation)
        entries = self.memories.setdefault(tier.name, [])
        existing = next((entry for entry in entries if entry.key_hash == key_hash), None)
        vector = observation.vector()
        surprise = observation.surprise
        if existing is None:
            entry_id = hashlib.sha256(f"{tier.name}:{key_hash}:{time.time():.6f}".encode("utf-8")).hexdigest()[:16]
            entries.append(
                HopeMemoryEntry(
                    entry_id=entry_id,
                    tier=tier.name,
                    signal_id=observation.signal_id,
                    asset=observation.asset,
                    regime=observation.regime,
                    key_hash=key_hash,
                    value_vector=vector,
                    surprise_score=surprise,
                    weight=max(0.05, min(2.0, surprise + observation.source_quality)),
                    lineage_hashes=list(observation.lineage_hashes),
                    created_at=time.time(),
                    updated_at=time.time(),
                )
            )
        else:
            existing.value_vector = self._decayed_average(existing.value_vector, vector, tier.decay)
            existing.surprise_score = tier.decay * existing.surprise_score + (1.0 - tier.decay) * surprise
            existing.weight = max(0.05, min(2.0, tier.decay * existing.weight + (1.0 - tier.decay) * (surprise + observation.source_quality)))
            existing.updated_at = time.time()
            existing.update_count += 1
            existing.lineage_hashes = sorted(set(existing.lineage_hashes) | set(observation.lineage_hashes))
        entries.sort(key=lambda entry: (entry.weight, entry.updated_at), reverse=True)
        del entries[tier.capacity:]

    def _memory_key_hash(self, tier_name: str, observation: HopeObservation) -> str:
        if tier_name == "short_term":
            key = f"{observation.asset}:{observation.signal_id}"
        elif tier_name == "episodic":
            key = f"{observation.asset}:{observation.regime}:{observation.signal_id}"
        elif tier_name == "regime":
            key = f"{observation.asset}:{observation.regime}"
        else:
            key = f"{observation.signal_id}:{observation.asset}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _snapshot_entries(self) -> Dict[str, List[HopeMemoryEntry]]:
        if not self.production_snapshot:
            return {}
        return {
            tier_name: [self._entry_from_dict(item) for item in items]
            for tier_name, items in self.production_snapshot.tiers.items()
        }

    def _entry_from_dict(self, data: Mapping[str, Any]) -> HopeMemoryEntry:
        return HopeMemoryEntry(
            entry_id=str(data["entry_id"]),
            tier=str(data["tier"]),
            signal_id=str(data["signal_id"]),
            asset=str(data["asset"]),
            regime=str(data["regime"]),
            key_hash=str(data["key_hash"]),
            value_vector={str(key): float(value) for key, value in dict(data["value_vector"]).items()},
            surprise_score=float(data["surprise_score"]),
            weight=float(data["weight"]),
            lineage_hashes=list(data.get("lineage_hashes") or []),
            created_at=float(data["created_at"]),
            updated_at=float(data["updated_at"]),
            update_count=int(data.get("update_count", 1)),
        )

    def _sign_snapshot(self, snapshot: HopeMemorySnapshot) -> str:
        payload = json.dumps(snapshot.signing_payload(), sort_keys=True, default=str).encode("utf-8")
        return hmac.new(self.signing_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    def _decayed_average(
        self,
        current: Mapping[str, float],
        new: Mapping[str, float],
        decay: float,
    ) -> Dict[str, float]:
        keys = set(current) | set(new)
        return {
            key: float(current.get(key, 0.0)) * decay + float(new.get(key, 0.0)) * (1.0 - decay)
            for key in keys
        }

    def _cosine_similarity(self, left: Mapping[str, float], right: Mapping[str, float]) -> float:
        keys = set(left) & set(right)
        if not keys:
            return 0.0
        numerator = sum(float(left[key]) * float(right[key]) for key in keys)
        left_norm = math.sqrt(sum(float(left[key]) ** 2 for key in keys))
        right_norm = math.sqrt(sum(float(right[key]) ** 2 for key in keys))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return numerator / (left_norm * right_norm)

    def _hash_payload(self, payload: Any) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()

    def _coerce_zone(self, zone: IntelligenceZone) -> IntelligenceZone:
        if isinstance(zone, IntelligenceZone):
            return zone
        return IntelligenceZone(str(zone))


__all__ = [
    "HopeMemoryEntry",
    "HopeMemorySnapshot",
    "HopeMemoryTier",
    "HopeObservation",
    "HopeRecommendation",
    "HopeUpdateReport",
    "NestedLearningHopeEngine",
]
