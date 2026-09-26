"""Human-guided recursive self-improvement foundation."""

from .evidence_boundaries import (
    CostModelRegistry,
    HoldoutAttestation,
    build_paired_envelope,
    load_key_file,
)
from .improvement_genome import (
    EvaluationEvidence,
    ImprovementDomain,
    ImprovementGenome,
    PromotionDecision,
)
from .rsi_loop import HumanGuidedRecursiveImprovementLoop, ImprovementPolicy

# Level-1 RSI v2 subsystem (research-only; no deployment authority).
from .archive import ParetoArchive
from .contracts import ContractError, contract_hash, load_signed_contract
from .engine_v2 import (
    CycleConfig,
    IndependentVerifier,
    OperatorAuthorization,
    PromotionLadder,
    RecursiveImprovementCycle,
)
from .meta_proposals import gate_meta, level2_proposal, level3_proposal
from .multi_objective import MultiObjectiveEvaluator
from .protected_control_plane import ProtectedPathGuard
from .scorecard import RSIScorecard
from .transfer import TransferEvaluator

__all__ = [
    "CostModelRegistry",
    "EvaluationEvidence",
    "HoldoutAttestation",
    "HumanGuidedRecursiveImprovementLoop",
    "ImprovementDomain",
    "ImprovementGenome",
    "ImprovementPolicy",
    "PromotionDecision",
    "build_paired_envelope",
    "load_key_file",
    "ParetoArchive",
    "ContractError",
    "contract_hash",
    "load_signed_contract",
    "CycleConfig",
    "IndependentVerifier",
    "OperatorAuthorization",
    "PromotionLadder",
    "RecursiveImprovementCycle",
    "gate_meta",
    "level2_proposal",
    "level3_proposal",
    "MultiObjectiveEvaluator",
    "ProtectedPathGuard",
    "RSIScorecard",
    "TransferEvaluator",
]
