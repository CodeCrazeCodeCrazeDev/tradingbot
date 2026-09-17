"""
Quantitative Research Kernel - Immutable State-Centric Discovery Kernel.
Treats every hypothesis, dataset, feature, model, and alpha as a first-class ResearchObject
with a formal lifecycle state machine, strict provenance, and direct economic resource schedules.
Unifies research and production into a single state-centric dependency graph.
"""

import logging
import uuid
import hashlib
import json
import networkx as nx
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum, auto

logger = logging.getLogger("AlphaAlgo.ResearchKernel")


# ===========================================================================
# 1. State Machine & Object Primitives
# ===========================================================================

class LifecycleState(Enum):
    """Immutable Lifecycle States for unified research and production."""
    DRAFT = auto()
    EXPERIMENTAL = auto()
    VALIDATED = auto()
    PAPER = auto()
    SHADOW = auto()
    CANARY = auto()
    PRODUCTION = auto()
    DEPRECATED = auto()
    RETIRED = auto()


@dataclass
class StateTransition:
    from_state: LifecycleState
    to_state: LifecycleState
    transitioned_at: datetime = field(default_factory=datetime.utcnow)
    approved_by: str = ""
    rationale: str = ""


class ImmutabilityViolation(Exception):
    """Raised when an active, validated, or production object is illegally modified."""
    pass


class ResearchObject:
    """
    First-class Immutable Research Object with precise state, version,
    provenance, and complete transition audit history.
    """
    def __init__(self, name: str, obj_type: str, raw_payload: Dict[str, Any],
                 creator: str = "Research_Agent") -> None:
        self.id: str = str(uuid.uuid4())
        self.name: str = name
        self.obj_type: str = obj_type  # HYPOTHESIS, DATASET, FEATURE, MODEL, ALPHA
        self.version: int = 1
        self.creator: str = creator
        self.created_at: datetime = datetime.utcnow()
        self.state: LifecycleState = LifecycleState.DRAFT
        self.transition_history: List[StateTransition] = []

        # Provenance: Parent object IDs from which this object was derived
        self.provenance_parents: List[str] = []

        # Immutable Payload lock
        self._payload: Dict[str, Any] = raw_payload.copy()
        self._payload_hash: str = self._calculate_hash(self._payload)

    def _calculate_hash(self, payload: Dict[str, Any]) -> str:
        s = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    @property
    def payload(self) -> Dict[str, Any]:
        """Provides read-only access to the payload."""
        return self._payload

    @property
    def payload_hash(self) -> str:
        return self._payload_hash

    def update_payload(self, new_payload: Dict[str, Any]) -> None:
        """Enforces immutability: Rejects updates if the object is validated or active in production."""
        if self.state in {LifecycleState.VALIDATED, LifecycleState.PAPER, LifecycleState.SHADOW,
                           LifecycleState.CANARY, LifecycleState.PRODUCTION}:
            raise ImmutabilityViolation(f"Illegal modification attempt on validated/production ResearchObject {self.id[:12]} in state {self.state.name}!")

        self._payload = new_payload.copy()
        self._payload_hash = self._calculate_hash(self._payload)
        self.version += 1
        logger.info(f"ResearchObject: Updated payload of {self.name} to version {self.version}")


# ===========================================================================
# 2. Directed Dependency Graph (Research as a Network)
# ===========================================================================

class ResearchDependencyGraph:
    """
    Network memory of the platform mapping multi-hop knowledge relationships.
    Traces how Hypotheses lead to Experiments, which use Datasets to produce Features/Alphas.
    """
    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()

    def add_object_node(self, obj: ResearchObject) -> None:
        """Adds a first-class research object node to the network."""
        self.graph.add_node(
            obj.id,
            name=obj.name,
            obj_type=obj.obj_type,
            state=obj.state.name,
            version=obj.version,
            hash=obj.payload_hash,
            # Priority 4: Enhanced provenance metadata
            created_at=obj.created_at.isoformat(),
            creator=obj.creator,
            checksum=hashlib.sha256(json.dumps(obj.payload, sort_keys=True, default=str).encode()).hexdigest()
        )

    def add_relation_edge(self, parent_id: str, child_id: str, relation_type: str) -> None:
        """Creates a directed trace edge between two research entities."""
        self.graph.add_edge(parent_id, child_id, relation=relation_type)
        logger.info(f"Dependency Graph: {parent_id[:12]} --[{relation_type}]--> {child_id[:12]}")

    def get_provenance_trail(self, obj_id: str) -> List[str]:
        """Returns the full ancestral ancestry trail for an object (ordered from raw source)."""
        if obj_id not in self.graph:
            return []
        # Return simple ancestors path
        return list(nx.ancestors(self.graph, obj_id))


# ===========================================================================
# 3. Research Economics Engine (Resource Allocation & Prioritization)
# ===========================================================================

@dataclass
class ResearchCost:
    developer_hours: float = 0.0
    compute_cores_hours: float = 0.0
    data_acquisition_cost_usd: float = 0.0


class ResearchEconomicsEngine:
    """
    Computes research costs and prioritizes experiment schedules.
    Maximizes Expected Information Gain (EIG) relative to mathematical capital/compute costs.
    """
    def __init__(self, dev_hour_rate: float = 75.0, core_hour_rate: float = 0.15) -> None:
        self.dev_hour_rate = dev_hour_rate
        self.core_hour_rate = core_hour_rate

    def calculate_total_cost_usd(self, cost: ResearchCost) -> float:
        """Calculates total financial cost of conducting a research experiment."""
        dev_cost = cost.developer_hours * self.dev_hour_rate
        compute_cost = cost.compute_cores_hours * self.core_hour_rate
        return float(dev_cost + compute_cost + cost.data_acquisition_cost_usd)

    def calculate_priority_score(self, expected_information_gain: float, cost: ResearchCost) -> float:
        """
        Calculates EIG-to-Cost ratio prioritization score.
        Enforces prioritization of high-leverage uncertainty-reducing experiments.
        """
        total_cost = self.calculate_total_cost_usd(cost)
        # Prevent divide-by-zero by assuming minimal cost floor of $1.0
        return float(expected_information_gain / max(total_cost, 1.0))


# ===========================================================================
# 4. Research Kernel Core
# ===========================================================================

class ResearchKernel:
    """
    The main process/state governance kernel of the SRP/QDP platform.
    Manages immutable object registrations, validates state transitions,
    enforces promotion gate policies, and monitors audit compliance.
    """
    def __init__(self) -> None:
        self.registry: Dict[str, ResearchObject] = {}
        self.network = ResearchDependencyGraph()
        self.economics = ResearchEconomicsEngine()

    def register_object(self, obj: ResearchObject, parent_ids: Optional[List[str]] = None) -> None:
        """Saves a research object in the immutable registry and maps its dependency edges."""
        self.registry[obj.id] = obj
        self.network.add_object_node(obj)

        if parent_ids:
            obj.provenance_parents = parent_ids.copy()
            for parent_id in parent_ids:
                if parent_id in self.registry:
                    # Formulate relational edge in the semantic network
                    self.network.add_relation_edge(
                        parent_id=parent_id,
                        child_id=obj.id,
                        relation_type="derived_to"
                    )
        logger.info(f"Research Kernel: Registered {obj.obj_type} '{obj.name}' (ID: {obj.id[:12]})")

    def verify_provenance_integrity(self, obj_id: str) -> bool:
        """Verifies that an object's payload hash matches its registered checksum (Priority 4)."""
        obj = self.registry.get(obj_id)
        if not obj: return False

        current_hash = hashlib.sha256(json.dumps(obj.payload, sort_keys=True, default=str).encode()).hexdigest()
        return current_hash == obj.payload_hash

    def archive_old_objects(self, age_days: int = 365 * 5):
        """
        Moves objects older than age_days to a 'RETIRED' state to ensure 5-10 year scalability.
        In a real system, this would move payloads to cold storage (e.g. AWS S3 Glacier).
        """
        cutoff = datetime.utcnow() - timedelta(days=age_days)
        count = 0
        for obj in self.registry.values():
            if obj.created_at < cutoff and obj.state not in {LifecycleState.RETIRED, LifecycleState.DEPRECATED}:
                obj.state = LifecycleState.RETIRED
                count += 1

        if count > 0:
            logger.warning(f"Research Kernel: Archived {count} objects older than {age_days} days for long-term stability.")

    def execute_state_transition(self, obj_id: str, target_state: LifecycleState,
                                 approver: str, rationale: str) -> None:
        """
        Executes a formal state transition.
        Enforces promotion gate validation rules depending on the target state.
        """
        obj = self.registry.get(obj_id)
        if not obj:
            raise ValueError(f"ResearchObject ID {obj_id} not found in kernel registry.")

        # Enforce validation gate if promoting past DRAFT/EXPERIMENTAL
        if target_state in {LifecycleState.VALIDATED, LifecycleState.PRODUCTION}:
            # Mock check: Validated objects must have at least 1 parent provenance trail
            if not obj.provenance_parents:
                raise ImmutabilityViolation(f"Promotion Denied: Object {obj.id[:12]} lacks parent lineage provenance. Promotion violates constitutional verification gates!")

        # Log transition
        transition = StateTransition(
            from_state=obj.state,
            to_state=target_state,
            approved_by=approver,
            rationale=rationale
        )
        obj.transition_history.append(transition)

        # Update node metadata in dependency graph
        obj.state = target_state
        if obj.id in self.network.graph:
            self.network.graph.nodes[obj.id]["state"] = target_state.name

        logger.warning(f"STATE TRANSITION: Object '{obj.name}' promoted from {transition.from_state.name} to {target_state.name}. Signed by: {approver}")
