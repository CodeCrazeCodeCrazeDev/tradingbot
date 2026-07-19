"""
Machine-Readable Scientific Research Schemas.
=============================================
Provides strictly typed schemas and serialized representations for core entities in the
Quantitative Research System, enabling trace-reproducibility and unified knowledge management.
"""

import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class HypothesisSchema:
    """Rigorous scientific hypothesis representation."""
    id: str
    statement: str
    economic_foundation: str
    counterparty_profile: str
    falsification_tests: List[str]
    state: str = "PROPOSED"  # PROPOSED, REVIEW, ACCEPTED, REJECTED, RETIRED
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass
class DatasetSchema:
    """Verifiable dataset metadata trace schema."""
    id: str
    source_name: str
    dataset_hash: str
    record_count: int
    data_quality_score: float  # 0.0 to 1.0
    lineage_parent_ids: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    column_definitions: Dict[str, str] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass
class FeatureSchema:
    """Candidate statistical feature metadata schema."""
    id: str
    name: str
    expression: str
    dataset_version_id: str
    information_coefficient: float
    turnover_rate: float
    p_value: float
    status: str = "DRAFT"  # DRAFT, EXCLUDED, APPROVED
    ablation_marginal_gain: float = 0.0
    fdr_adjusted_p_value: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass
class ExperimentSchema:
    """Trace-reproducible quantitative experiment schema."""
    id: str
    hypothesis_id: str
    dataset_hash: str
    random_seed: int
    parameters: Dict[str, Any]
    code_version: str  # Git commit hash
    outcome_metrics: Dict[str, float] = field(default_factory=dict)
    status: str = "REGISTERED"  # REGISTERED, RUNNING, COMPLETED, FAILED
    purged_cv_parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass
class ModelSchema:
    """Scientific model specification registry schema."""
    id: str
    experiment_id: str
    model_class: str
    parameter_count: int
    in_sample_sharpe: float
    out_of_sample_sharpe: float
    decay_half_life_bars: int
    artifact_path: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass
class BenchmarkSchema:
    """Regime-aware institutional backtest baseline schema."""
    id: str
    benchmark_name: str
    regime_classified: str  # TRENDING, RANGING, CRISIS_HIGH_VOL, LOW_VOL
    sample_size_bars: int
    realized_sharpe: float
    max_drawdown_pct: float
    sortino_ratio: float
    information_ratio: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass
class EvidenceSchema:
    """Empirical statistical evidence used to support/refute beliefs."""
    id: str
    experiment_id: str
    claim_text: str
    observed_metric_value: float
    p_value: float
    is_reproducible: bool
    verdict: str  # ACCEPTED, REJECTED_SIGNIFICANCE, REJECTED_REPRODUCIBILITY
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass
class DecisionSchema:
    """Formal, auditable strategic decision ledger schema."""
    id: str
    experiment_id: str
    policy_action: str  # REJECT, ARCHIVE, IMPROVE, MERGE, DEPLOY, REPEAT
    approver_signature: str
    rationale: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)
