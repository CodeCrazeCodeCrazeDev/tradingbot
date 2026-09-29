"""Level-2 / Level-3 meta proposals (mission sections 5-6, 15).

Level 1 improves trading components. Level 2 proposes changes to *how* the
system discovers improvements (hypothesis rules, prioritizer weights,
search parameters). Level 3 proposes changes to *how it evaluates* (contract
thresholds, panels, evaluator config). Meta proposals are recorded as
ImprovementGenomes with ``recursion_level`` in metadata — and the cycle
always refuses to evaluate them in-process; they require a signed
out-of-band operator authorization path that does not exist in this code.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from .improvement_genome import ImprovementDomain, ImprovementGenome
from .protected_control_plane import GOVERNED_DOMAINS


def _meta_genome(level: int, domain: ImprovementDomain, objective: str,
                 change_set: Mapping[str, Any], rationale: str,
                 baseline_hash: str) -> ImprovementGenome:
    return ImprovementGenome(
        domain=domain,
        objective=objective,
        change_set=dict(change_set),
        evaluation_plan={"contract_id": "meta", "recursion_level": level},
        safety_constraints={"requires_out_of_band_authorization": True},
        parent_id=baseline_hash,
        metadata={"recursion_level": level, "rationale": rationale},
    )


def level2_proposal(target_rule: str, suggestion: Mapping[str, Any],
                    rationale: str, baseline_hash: str) -> ImprovementGenome:
    """Propose an improvement to the improvement-discovery machinery."""
    return _meta_genome(
        2, ImprovementDomain.META_LEARNING,
        f"improve search: {target_rule}",
        {target_rule: dict(suggestion)}, rationale, baseline_hash)


def level3_proposal(target_contract_field: str, suggestion: Any,
                    rationale: str, baseline_hash: str) -> ImprovementGenome:
    """Propose an improvement to evaluation/governance itself."""
    return _meta_genome(
        3, ImprovementDomain.EVALUATION_INTELLIGENCE,
        f"improve evaluation: {target_contract_field}",
        {target_contract_field: suggestion}, rationale, baseline_hash)


def recursion_level(genome: ImprovementGenome) -> int:
    meta_level = genome.metadata.get("recursion_level")
    plan_level = genome.evaluation_plan.get("recursion_level")
    for v in (meta_level, plan_level):
        if isinstance(v, int) and v >= 1:
            return v
    if genome.domain.value in GOVERNED_DOMAINS:
        return 2
    return 1


def gate_meta(genome: ImprovementGenome, contract: Mapping[str, Any]) -> Optional[str]:
    """None -> may proceed as level-1. str -> rejection reason."""
    level = recursion_level(genome)
    if level > int(contract.get("max_recursion_depth", 1)):
        return "candidate exceeds contract max_recursion_depth"
    if level > 1 or genome.safety_constraints.get("requires_out_of_band_authorization"):
        return "level_requires_out_of_band_authorization"
    return None
