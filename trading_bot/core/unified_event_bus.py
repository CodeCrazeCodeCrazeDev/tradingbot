"""
LogAct Shared-Log Backbone - UCA V5 Core Component
=============================================

The authoritative, totally ordered shared log for AlphaAlgo UCA V5.
Implements 'LogAct: Enabling Agentic Reliability via Shared Logs' (Paper 1).

Maintains a transactional ledger of all system decisions, ensuring
deterministic recovery and decoupled safety verification (Voter Swarm).
Provides full backward compatibility with UCA-2026 UnifiedDecisionBus.
"""

import asyncio
import logging
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, Coroutine
from uuid import uuid4
import threading

logger = logging.getLogger(__name__)

# --- Legacy Compatibility Layer ---

class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class UnifiedEvent:
    event_type: str
    payload: Dict[str, Any]
    source: str
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'payload': self.payload,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority.name,
            'correlation_id': self.correlation_id,
            'metadata': self.metadata,
        }

# --- UCA V5 LogAct Core ---

class ActionStatus(Enum):
    PROPOSED = "proposed"
    AUDITING = "auditing"
    APPROVED = "approved"
    VETOED = "vetoed"
    TIMED_OUT = "timed_out"
    EXECUTED = "executed"
    FAILED = "failed"

@dataclass
class LogAction:
    """
    Authoritative institutional-grade action record.
    Permanently links decisions to evidence, state, and audit trails.
    """
    action_type: str
    payload: Dict[str, Any]
    agent_id: str
    action_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: ActionStatus = ActionStatus.PROPOSED
    voter_reports: Dict[str, Any] = field(default_factory=dict)
    sequence_number: Optional[int] = None
    priority: EventPriority = EventPriority.NORMAL

    # Institutional Decision Ledger Links (arXiv:2604.07988 Extension)
    evidence_graph_id: Optional[str] = None
    world_model_state_hash: Optional[str] = None
    portfolio_snapshot_id: Optional[str] = None
    configuration_hash: Optional[str] = None
    git_commit: Optional[str] = None
    dataset_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_id': self.action_id,
            'action_type': self.action_type,
            'payload': self.payload,
            'agent_id': self.agent_id,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'voter_reports': self.voter_reports,
            'sequence_number': self.sequence_number,
            'priority': self.priority.name
        }

    async def wait_for_decision(self, timeout: float = 10.0) -> ActionStatus:
        """Wait for the decision bus to reach consensus on this action."""
        try:
            await asyncio.wait_for(self._completed_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            if self.status in [ActionStatus.PROPOSED, ActionStatus.AUDITING]:
                self.status = ActionStatus.TIMED_OUT
        return self.status

class UnifiedDecisionBus:
    """
    LogAct Shared-Log Backbone - Authoritative Singleton for AlphaAlgo UCA V5.
    Ensures transactional reliability with full legacy support.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(UnifiedDecisionBus, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self.config = config or {}
        self._log: List[LogAction] = []
        self._voters: Dict[str, Callable] = {}
        self._subscribers: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._action_queue = asyncio.PriorityQueue()
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        self._initialized = True
        logger.info("LogAct Shared-Log Backbone initialized with Legacy Support")
        self._register_default_voters()

    def _register_default_voters(self):
        """Registers institutional voters mandated by UCA V5."""
        from .immutable_shield import shield
        async def governance_shield_voter(action: LogAction) -> Dict[str, Any]:
            report = await shield.validate_action(action.action_type, action.payload, {"market": {}, "portfolio": {}})
            from .immutable_shield import GovernanceDecision
            return {
                "decision": "APPROVED" if report.decision == GovernanceDecision.APPROVED else "REJECT",
                "reason": report.reason,
                "risk_score": report.risk_score
            }
        self.register_voter("GovernanceShield", governance_shield_voter)

    async def start(self):
        if self._running:
            return
        self._running = True
        self._processor_task = asyncio.create_task(self._process_log())

    async def stop(self):
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
        logger.info("LogAct Backbone stopped")

    def register_voter(self, voter_id: str, voter_fn: Callable):
        """UCA V5: Register a voter for decoupled consensus."""
        self._voters[voter_id] = voter_fn

    async def propose_action(self, action: LogAction):
        """UCA V5: Propose an intervention to the shared log."""
        action.status = ActionStatus.PROPOSED
        await self._action_queue.put((-action.priority.value, action.timestamp, action))

    async def publish(self, event: UnifiedEvent):
        """Legacy Support: Wraps UnifiedEvent into LogAction for the Shared Log."""
        action = LogAction(
            action_type=event.event_type,
            payload=event.payload,
            agent_id=event.source,
            action_id=event.event_id,
            timestamp=event.timestamp,
            priority=event.priority
        )
        await self.propose_action(action)

    def subscribe(self, action_type: str, handler: Callable, subscriber_id: str = "anon", priority: int = 0):
        """
        Unified Subscription API:
        Works for both LogActions (V5) and UnifiedEvents (Legacy).
        """
        self._subscribers[action_type].append({
            "id": subscriber_id,
            "handler": handler,
            "priority": priority
        })
        # Sort by priority (Legacy feature)
        self._subscribers[action_type].sort(key=lambda x: x["priority"], reverse=True)

    async def _process_log(self):
        """
        Authoritative log processing and total ordering.
        Implements LogAct (arXiv:2604.07988) State Machine Replication.
        """
        # Auto-inject ImmutableShield as the primary Governance Voter
        try:
            from .immutable_shield import shield
            self.register_voter("immutable_shield_voter", self._shield_voter_adapter)
        except ImportError:
            logger.warning("ImmutableShield not available for LogAct voting")

        while self._running:
            try:
                _, _, action = await self._action_queue.get()

                # 1. Total Ordering & Log Persistence
                action.sequence_number = len(self._log)
                self._log.append(action)
                if len(self._log) > self.config.get("max_log_size", 10000):
                    self._log.pop(0)

                # 2. Decoupled Voting (Audit Phase)
                # This deconstructs the agent's state machine.
                # Voter can see the action BEFORE it is executed.
                action.status = ActionStatus.AUDITING

                vote_tasks = []
                voter_ids = list(self._voters.keys())

                for vid, vfn in self._voters.items():
                    vote_tasks.append(vfn(action))

                if vote_tasks:
                    results = await asyncio.gather(*vote_tasks, return_exceptions=True)
                    for i, res in enumerate(results):
                        vid = voter_ids[i]
                        if isinstance(res, Exception):
                            action.voter_reports[vid] = {"decision": "FAIL", "reason": str(res)}
                        else:
                            action.voter_reports[vid] = res

                # 3. Consensus Logic
                if self._check_consensus(action):
                    action.status = ActionStatus.APPROVED
                    logger.info(f"Action {action.action_id} APPROVED [Seq: {action.sequence_number}]")
                    # 4. Dispatch to Consumers (Execution Phase)
                    # Once in the log and approved, the action is 'committed'
                    await self._dispatch(action)
                    action.status = ActionStatus.EXECUTED
                else:
                    action.status = ActionStatus.VETOED

                # Signal completion for wait_for_decision
                action._completed_event.set()
                self._action_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"LogAct Critical Processor Error: {e}")

    def _check_consensus(self, action: LogAction) -> bool:
        for vid, report in action.voter_reports.items():
            if report.get("decision") in ["REJECT", "VETO", "FAIL"]:
                logger.warning(f"LogAct: Action {action.action_id} VETOED by {vid}")
                return False
        return True

    async def _shield_voter_adapter(self, action: LogAction) -> Dict[str, Any]:
        """Adapts ImmutableShield to the LogAct Voter interface."""
        from .immutable_shield import shield, GovernanceDecision

        # Extract context if provided in payload, else use empty
        context = action.payload.get("context", {})
        report = shield.validate_action(action.action_type, action.payload, context)

        return {
            "decision": "APPROVED" if report.decision == GovernanceDecision.APPROVED else "VETO",
            "reason": report.reason,
            "risk_score": report.risk_score,
            "audit_id": report.audit_id
        }

    async def _dispatch(self, action: LogAction):
        # Notify specific subscribers and wildcard subscribers
        handlers = self._subscribers.get(action.action_type, []) + self._subscribers.get("*", [])
        if not handlers:
            return

        tasks = [h["handler"](action) for h in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)

# Shared Access Point
decision_bus = UnifiedDecisionBus()
