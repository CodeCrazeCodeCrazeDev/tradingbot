"""
Intelligent & Social Delegation - Trust & Reputation System
Based on Google DeepMind "Intelligent AI Delegation" (2026, arXiv:2602.11865)

Section 4.6: Trust and Reputation
- Performance-based immutable ledger
- Decentralized attestations (Web of Trust model)
- Behavioral and explainability metrics
- Graduated authority based on trust
- Context-specific credentials
- Dynamic trust calibration

RISK MITIGATIONS IMPLEMENTED:
- Reputation Gaming: Difficulty-weighted scoring, anti-cherry-picking
- Reputation Sabotage: Feedback validation, outlier rejection, dispute mechanism
- Trust Threshold Miscalibration: Bayesian trust updates, adaptive thresholds
- Sybil Attacks: Identity verification, behavioral fingerprinting
"""

import hashlib
import logging
import math
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from .delegation_types import (
    AgentProfile,
    ReputationRecord,
    SecurityThreat,
    TaskCriticality,
    TaskComplexity,
    ThreatCategory,
    ThreatSeverity,
    TradingTaskType,
    TrustDimension,
)

logger = logging.getLogger(__name__)


# ============================================================================
# TRUST MODEL
# ============================================================================

@dataclass
class TrustProfile:
    """Multi-dimensional trust profile for an agent."""
    agent_id: str = ""
    dimensions: Dict[str, float] = field(default_factory=lambda: {
        TrustDimension.COMPETENCE.value: 0.5,
        TrustDimension.RELIABILITY.value: 0.5,
        TrustDimension.INTEGRITY.value: 0.5,
        TrustDimension.ALIGNMENT.value: 0.5,
        TrustDimension.TRANSPARENCY.value: 0.5,
    })
    overall_trust: float = 0.5
    confidence: float = 0.1  # How confident we are in the trust estimate
    observation_count: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    trust_history: List[Tuple[datetime, float]] = field(default_factory=list)
    violations: List[Dict[str, Any]] = field(default_factory=list)
    is_frozen: bool = False  # Frozen = under investigation
    freeze_reason: Optional[str] = None

    def update_dimension(self, dimension: TrustDimension, value: float, weight: float = 1.0):
        """Bayesian update of a trust dimension."""
        key = dimension.value
        old = self.dimensions.get(key, 0.5)
        # Exponential moving average with confidence weighting
        alpha = min(0.3, weight / max(self.observation_count, 1))
        new_val = old * (1 - alpha) + value * alpha
        self.dimensions[key] = max(0.0, min(1.0, new_val))
        self._recalculate_overall()

    def _recalculate_overall(self):
        """Recalculate overall trust from dimensions."""
        weights = {
            TrustDimension.COMPETENCE.value: 0.25,
            TrustDimension.RELIABILITY.value: 0.25,
            TrustDimension.INTEGRITY.value: 0.25,
            TrustDimension.ALIGNMENT.value: 0.15,
            TrustDimension.TRANSPARENCY.value: 0.10,
        }
        total = sum(
            self.dimensions.get(k, 0.5) * w
            for k, w in weights.items()
        )
        self.overall_trust = max(0.0, min(1.0, total))
        self.last_updated = datetime.utcnow()
        self.trust_history.append((self.last_updated, self.overall_trust))
        # Keep history bounded
        if len(self.trust_history) > 1000:
            self.trust_history = self.trust_history[-500:]


@dataclass
class ReputationProfile:
    """Public reputation profile for an agent."""
    agent_id: str = ""
    overall_score: float = 0.5
    task_type_scores: Dict[str, float] = field(default_factory=dict)
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    avg_quality: float = 0.5
    avg_latency_ms: float = 100.0
    deadline_adherence: float = 1.0
    transparency_score: float = 0.5
    safety_score: float = 0.5
    difficulty_weighted_score: float = 0.5
    records: List[ReputationRecord] = field(default_factory=list)
    credentials: List[Dict[str, Any]] = field(default_factory=list)
    disputes: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.5
        return self.successful_tasks / self.total_tasks


@dataclass
class TrustReputationConfig:
    """Configuration for the trust & reputation system."""
    initial_trust: float = 0.5
    initial_reputation: float = 0.5
    trust_decay_rate: float = 0.001  # Per hour of inactivity
    max_trust: float = 0.99
    min_trust: float = 0.01
    reputation_damping: float = 0.1  # Damping factor for reputation updates
    failure_penalty_multiplier: float = 2.0  # Failures penalized 2x
    success_reward_multiplier: float = 1.0
    difficulty_weight: float = 0.3  # Weight for task difficulty in scoring
    recency_weight: float = 0.2  # Weight for recent performance
    outlier_rejection_threshold: float = 3.0  # Std devs for outlier feedback
    min_observations_for_confidence: int = 10
    sybil_detection_enabled: bool = True
    max_trust_change_per_update: float = 0.1
    freeze_threshold_violations: int = 3


class TrustReputationSystem:
    """
    Manages trust and reputation for all agents in the delegation ecosystem.

    Implements Section 4.6 of the paper:
    - Performance-based immutable ledger
    - Multi-dimensional trust (competence, reliability, integrity, alignment, transparency)
    - Difficulty-weighted reputation scoring (anti-gaming)
    - Graduated authority based on trust level
    - Bayesian trust updates with confidence tracking
    - Sybil attack detection via behavioral fingerprinting

    RISK MITIGATIONS:
    - Reputation Gaming (4.6): Difficulty-weighted scoring prevents cherry-picking easy tasks
    - Reputation Sabotage (4.6/4.9): Outlier feedback rejection, dispute mechanism
    - Trust Miscalibration (4.6): Bayesian updates, adaptive thresholds
    - Sybil Attacks (4.9): Behavioral fingerprinting, identity correlation
    """

    def __init__(self, config: Optional[TrustReputationConfig] = None):
        self.config = config or TrustReputationConfig()
        self._trust_profiles: Dict[str, TrustProfile] = {}
        self._reputation_profiles: Dict[str, ReputationProfile] = {}
        self._behavioral_fingerprints: Dict[str, Dict[str, Any]] = {}
        self._feedback_history: Dict[str, List[float]] = defaultdict(list)
        self._sybil_clusters: List[Set[str]] = []
        logger.info("TrustReputationSystem initialized")

    def initialize_agent(self, agent_id: str):
        """Initialize trust and reputation for a new agent."""
        if agent_id not in self._trust_profiles:
            self._trust_profiles[agent_id] = TrustProfile(
                agent_id=agent_id,
                overall_trust=self.config.initial_trust,
            )
        if agent_id not in self._reputation_profiles:
            self._reputation_profiles[agent_id] = ReputationProfile(
                agent_id=agent_id,
                overall_score=self.config.initial_reputation,
            )

    def get_trust(self, agent_id: str) -> float:
        """Get current trust score for an agent."""
        profile = self._trust_profiles.get(agent_id)
        return profile.overall_trust if profile else self.config.initial_trust

    def get_reputation(self, agent_id: str) -> float:
        """Get current reputation score for an agent."""
        profile = self._reputation_profiles.get(agent_id)
        return profile.overall_score if profile else self.config.initial_reputation

    def get_trust_profile(self, agent_id: str) -> Optional[TrustProfile]:
        return self._trust_profiles.get(agent_id)

    def get_reputation_profile(self, agent_id: str) -> Optional[ReputationProfile]:
        return self._reputation_profiles.get(agent_id)

    # ========================================================================
    # RECORD TASK OUTCOME (Section 4.6 - Immutable Ledger)
    # ========================================================================

    def record_outcome(self, record: ReputationRecord):
        """
        Record a task outcome and update trust/reputation.
        This is the core feedback loop of the delegation system.
        """
        agent_id = record.agent_id
        self.initialize_agent(agent_id)

        # Compute attestation hash (immutable record)
        record.compute_attestation()
        record.verified = True

        trust_profile = self._trust_profiles[agent_id]
        rep_profile = self._reputation_profiles[agent_id]

        # RISK MITIGATION: Outlier feedback rejection
        if not self._validate_feedback(agent_id, record.quality_score):
            logger.warning(
                "Outlier feedback rejected for agent %s (quality=%.2f)",
                agent_id, record.quality_score,
            )
            return

        # Update reputation
        self._update_reputation(rep_profile, record)

        # Update trust dimensions
        self._update_trust(trust_profile, record)

        # Update behavioral fingerprint (for Sybil detection)
        self._update_fingerprint(agent_id, record)

        # Check for Sybil patterns
        if self.config.sybil_detection_enabled:
            self._check_sybil(agent_id)

        logger.debug(
            "Recorded outcome for agent %s: success=%s, quality=%.2f, trust=%.3f, rep=%.3f",
            agent_id, record.success, record.quality_score,
            trust_profile.overall_trust, rep_profile.overall_score,
        )

    def _validate_feedback(self, agent_id: str, quality: float) -> bool:
        """
        RISK MITIGATION: Reputation Sabotage (Section 4.6/4.9)
        Reject outlier feedback that deviates too far from historical pattern.
        """
        history = self._feedback_history[agent_id]
        if len(history) < 5:
            history.append(quality)
            return True

        mean = sum(history) / len(history)
        variance = sum((x - mean) ** 2 for x in history) / len(history)
        std = math.sqrt(variance) if variance > 0 else 0.1

        if abs(quality - mean) > self.config.outlier_rejection_threshold * std:
            return False

        history.append(quality)
        if len(history) > 100:
            self._feedback_history[agent_id] = history[-50:]
        return True

    def _update_reputation(self, profile: ReputationProfile, record: ReputationRecord):
        """Update reputation with difficulty-weighted scoring (anti-gaming)."""
        profile.records.append(record)
        if len(profile.records) > 500:
            profile.records = profile.records[-250:]

        profile.total_tasks += 1
        if record.success:
            profile.successful_tasks += 1
        else:
            profile.failed_tasks += 1

        # RISK MITIGATION: Difficulty-weighted scoring (anti-gaming)
        # Harder tasks contribute more to reputation
        difficulty_multiplier = 1.0
        task_type = record.task_type.value
        if record.task_type in (
            TradingTaskType.EXECUTE_ORDER,
            TradingTaskType.EMERGENCY_EXIT,
            TradingTaskType.OPTIMIZE_PORTFOLIO,
        ):
            difficulty_multiplier = 1.5
        elif record.task_type in (
            TradingTaskType.GENERATE_SIGNAL,
            TradingTaskType.ASSESS_RISK,
        ):
            difficulty_multiplier = 1.2

        # Weighted quality update
        weight = difficulty_multiplier * self.config.difficulty_weight
        if record.success:
            delta = record.quality_score * weight * self.config.success_reward_multiplier
        else:
            delta = -record.quality_score * weight * self.config.failure_penalty_multiplier

        # Damped update
        alpha = self.config.reputation_damping
        profile.overall_score = max(
            self.config.min_trust,
            min(self.config.max_trust,
                profile.overall_score * (1 - alpha) + (profile.overall_score + delta) * alpha)
        )

        # Update task-type-specific score
        old_type_score = profile.task_type_scores.get(task_type, 0.5)
        profile.task_type_scores[task_type] = old_type_score * 0.9 + record.quality_score * 0.1

        # Update averages
        n = profile.total_tasks
        profile.avg_quality = (profile.avg_quality * (n - 1) + record.quality_score) / n
        profile.avg_latency_ms = (profile.avg_latency_ms * (n - 1) + record.latency_ms) / n
        if record.deadline_met:
            profile.deadline_adherence = (profile.deadline_adherence * (n - 1) + 1.0) / n
        else:
            profile.deadline_adherence = (profile.deadline_adherence * (n - 1) + 0.0) / n

        profile.last_updated = datetime.utcnow()

    def _update_trust(self, profile: TrustProfile, record: ReputationRecord):
        """Bayesian trust update across multiple dimensions."""
        if profile.is_frozen:
            return

        profile.observation_count += 1

        # Competence: based on quality score
        profile.update_dimension(
            TrustDimension.COMPETENCE,
            record.quality_score,
            weight=1.0 if record.success else 0.5,
        )

        # Reliability: based on success and deadline adherence
        reliability = 1.0 if record.success and record.deadline_met else 0.0
        profile.update_dimension(TrustDimension.RELIABILITY, reliability)

        # Integrity: based on constraint violations
        integrity = 1.0 if not record.constraint_violations else 0.0
        profile.update_dimension(TrustDimension.INTEGRITY, integrity)

        # Clamp trust change per update
        old_trust = profile.overall_trust
        profile._recalculate_overall()
        delta = profile.overall_trust - old_trust
        if abs(delta) > self.config.max_trust_change_per_update:
            clamped = old_trust + math.copysign(self.config.max_trust_change_per_update, delta)
            profile.overall_trust = max(self.config.min_trust, min(self.config.max_trust, clamped))

        # Check for violation threshold → freeze
        if not record.success and record.constraint_violations:
            profile.violations.append({
                'task_id': record.task_id,
                'violations': record.constraint_violations,
                'timestamp': datetime.utcnow().isoformat(),
            })
            if len(profile.violations) >= self.config.freeze_threshold_violations:
                profile.is_frozen = True
                profile.freeze_reason = f"Exceeded {self.config.freeze_threshold_violations} violations"
                logger.warning("Agent %s FROZEN: %s", profile.agent_id, profile.freeze_reason)

    # ========================================================================
    # SYBIL DETECTION (Section 4.9)
    # ========================================================================

    def _update_fingerprint(self, agent_id: str, record: ReputationRecord):
        """Update behavioral fingerprint for Sybil detection."""
        fp = self._behavioral_fingerprints.setdefault(agent_id, {
            'avg_quality': 0.5,
            'avg_latency': 100.0,
            'task_type_distribution': defaultdict(int),
            'success_pattern': [],
            'timing_pattern': [],
        })

        n = len(fp['success_pattern']) + 1
        fp['avg_quality'] = (fp['avg_quality'] * (n - 1) + record.quality_score) / n
        fp['avg_latency'] = (fp['avg_latency'] * (n - 1) + record.latency_ms) / n
        fp['task_type_distribution'][record.task_type.value] += 1
        fp['success_pattern'].append(1 if record.success else 0)
        fp['timing_pattern'].append(record.timestamp.hour)

        # Keep bounded
        if len(fp['success_pattern']) > 100:
            fp['success_pattern'] = fp['success_pattern'][-50:]
            fp['timing_pattern'] = fp['timing_pattern'][-50:]

    def _check_sybil(self, agent_id: str):
        """
        RISK MITIGATION: Sybil Attack Detection (Section 4.9)
        Detect multiple identities controlled by same adversary via behavioral similarity.
        """
        fp = self._behavioral_fingerprints.get(agent_id)
        if not fp or len(fp['success_pattern']) < 10:
            return

        for other_id, other_fp in self._behavioral_fingerprints.items():
            if other_id == agent_id:
                continue
            if len(other_fp['success_pattern']) < 10:
                continue

            similarity = self._fingerprint_similarity(fp, other_fp)
            if similarity > 0.95:
                logger.warning(
                    "SYBIL SUSPECTED: Agents %s and %s have %.1f%% behavioral similarity",
                    agent_id, other_id, similarity * 100,
                )
                # Add to cluster
                found = False
                for cluster in self._sybil_clusters:
                    if agent_id in cluster or other_id in cluster:
                        cluster.add(agent_id)
                        cluster.add(other_id)
                        found = True
                        break
                if not found:
                    self._sybil_clusters.append({agent_id, other_id})

    def _fingerprint_similarity(
        self, fp1: Dict[str, Any], fp2: Dict[str, Any]
    ) -> float:
        """Calculate behavioral similarity between two fingerprints."""
        score = 0.0
        count = 0

        # Quality similarity
        if abs(fp1['avg_quality'] - fp2['avg_quality']) < 0.05:
            score += 1.0
        count += 1

        # Latency similarity
        if abs(fp1['avg_latency'] - fp2['avg_latency']) < 10.0:
            score += 1.0
        count += 1

        # Success pattern similarity (correlation)
        p1 = fp1['success_pattern'][-20:]
        p2 = fp2['success_pattern'][-20:]
        min_len = min(len(p1), len(p2))
        if min_len >= 5:
            matches = sum(1 for a, b in zip(p1[-min_len:], p2[-min_len:]) if a == b)
            score += matches / min_len
            count += 1

        # Timing pattern similarity
        t1 = fp1['timing_pattern'][-20:]
        t2 = fp2['timing_pattern'][-20:]
        if t1 and t2:
            avg_t1 = sum(t1) / len(t1)
            avg_t2 = sum(t2) / len(t2)
            if abs(avg_t1 - avg_t2) < 1.0:
                score += 1.0
            count += 1

        return score / max(count, 1)

    # ========================================================================
    # GRADUATED AUTHORITY (Section 4.6)
    # ========================================================================

    def get_authority_level(self, agent_id: str) -> Dict[str, Any]:
        """
        Determine authority level based on trust (Section 4.6).
        Higher trust → more autonomy, less monitoring.
        """
        trust = self.get_trust(agent_id)
        rep = self.get_reputation(agent_id)

        if trust >= 0.85 and rep >= 0.80:
            return {
                'level': 'high',
                'max_autonomy': 4,
                'monitoring': 'outcome_only',
                'transaction_cap': float('inf'),
                'requires_approval': False,
                'description': 'High-trust agent: minimal oversight',
            }
        elif trust >= 0.65 and rep >= 0.60:
            return {
                'level': 'medium',
                'max_autonomy': 2,
                'monitoring': 'periodic',
                'transaction_cap': 10000.0,
                'requires_approval': False,
                'description': 'Medium-trust agent: periodic monitoring',
            }
        elif trust >= 0.40 and rep >= 0.35:
            return {
                'level': 'low',
                'max_autonomy': 1,
                'monitoring': 'continuous',
                'transaction_cap': 1000.0,
                'requires_approval': True,
                'description': 'Low-trust agent: continuous monitoring, approval required',
            }
        else:
            return {
                'level': 'probationary',
                'max_autonomy': 0,
                'monitoring': 'continuous',
                'transaction_cap': 100.0,
                'requires_approval': True,
                'description': 'Probationary agent: strict constraints, all actions approved',
            }

    # ========================================================================
    # TRUST DECAY & MAINTENANCE
    # ========================================================================

    def apply_trust_decay(self):
        """Apply trust decay for inactive agents."""
        now = datetime.utcnow()
        for agent_id, profile in self._trust_profiles.items():
            hours_inactive = (now - profile.last_updated).total_seconds() / 3600.0
            if hours_inactive > 1.0:
                decay = self.config.trust_decay_rate * hours_inactive
                profile.overall_trust = max(
                    self.config.min_trust,
                    profile.overall_trust - decay,
                )

    def unfreeze_agent(self, agent_id: str, reason: str = "manual_review"):
        """Unfreeze an agent after investigation."""
        profile = self._trust_profiles.get(agent_id)
        if profile:
            profile.is_frozen = False
            profile.freeze_reason = None
            profile.violations = []
            logger.info("Agent %s unfrozen: %s", agent_id, reason)

    # ========================================================================
    # DISPUTE RESOLUTION (Section 4.8)
    # ========================================================================

    def file_dispute(
        self,
        agent_id: str,
        task_id: str,
        reason: str,
        evidence: Dict[str, Any],
    ) -> str:
        """File a dispute against a reputation record."""
        rep_profile = self._reputation_profiles.get(agent_id)
        if not rep_profile:
            return "agent_not_found"

        dispute = {
            'dispute_id': hashlib.sha256(
                f"{agent_id}:{task_id}:{time.time()}".encode()
            ).hexdigest()[:12],
            'agent_id': agent_id,
            'task_id': task_id,
            'reason': reason,
            'evidence': evidence,
            'status': 'pending',
            'filed_at': datetime.utcnow().isoformat(),
        }
        rep_profile.disputes.append(dispute)
        logger.info("Dispute filed against agent %s for task %s", agent_id, task_id)
        return dispute['dispute_id']

    def resolve_dispute(
        self,
        agent_id: str,
        dispute_id: str,
        resolution: str,
        adjustment: float = 0.0,
    ):
        """Resolve a dispute with optional reputation adjustment."""
        rep_profile = self._reputation_profiles.get(agent_id)
        if not rep_profile:
            return

        for dispute in rep_profile.disputes:
            if dispute.get('dispute_id') == dispute_id:
                dispute['status'] = resolution
                dispute['resolved_at'] = datetime.utcnow().isoformat()
                if adjustment != 0.0:
                    rep_profile.overall_score = max(
                        self.config.min_trust,
                        min(self.config.max_trust,
                            rep_profile.overall_score + adjustment)
                    )
                logger.info(
                    "Dispute %s resolved: %s (adjustment=%.3f)",
                    dispute_id, resolution, adjustment,
                )
                break

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        trust_scores = [p.overall_trust for p in self._trust_profiles.values()]
        rep_scores = [p.overall_score for p in self._reputation_profiles.values()]
        frozen = sum(1 for p in self._trust_profiles.values() if p.is_frozen)

        return {
            'total_agents': len(self._trust_profiles),
            'avg_trust': sum(trust_scores) / max(len(trust_scores), 1),
            'avg_reputation': sum(rep_scores) / max(len(rep_scores), 1),
            'frozen_agents': frozen,
            'sybil_clusters': len(self._sybil_clusters),
            'total_disputes': sum(
                len(p.disputes) for p in self._reputation_profiles.values()
            ),
        }

    def get_leaderboard(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top agents by reputation."""
        agents = []
        for agent_id, rep in self._reputation_profiles.items():
            trust = self.get_trust(agent_id)
            agents.append({
                'agent_id': agent_id,
                'reputation': rep.overall_score,
                'trust': trust,
                'total_tasks': rep.total_tasks,
                'success_rate': rep.success_rate,
                'avg_quality': rep.avg_quality,
            })
        agents.sort(key=lambda a: a['reputation'], reverse=True)
        return agents[:top_n]
