"""
LogAct Shared-Log Backbone - UCA V5 Core Component
=============================================

The authoritative, totally ordered shared log for AlphaAlgo UCA V5.
Implements 'LogAct: Enabling Agentic Reliability via Shared Logs' (2026).
Maintains backward compatibility with the UCA-2026 UnifiedDecisionBus API.
"""

import asyncio
import logging
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Union
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
    EXECUTED = "executed"
    FAILED = "failed"

@dataclass
class LogAction:
    action_type: str
    payload: Dict[str, Any]
    agent_id: str
    action_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: ActionStatus = ActionStatus.PROPOSED
    correlation_id: Optional[str] = None
    voter_reports: Dict[str, Any] = field(default_factory=dict)
    sequence_number: Optional[int] = None
    priority: EventPriority = EventPriority.NORMAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_id': self.action_id,
            'action_type': self.action_type,
            'payload': self.payload,
            'agent_id': self.agent_id,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'correlation_id': self.correlation_id,
            'voter_reports': self.voter_reports,
            'sequence_number': self.sequence_number,
            'priority': self.priority.name
        }

class UnifiedDecisionBus:
    """
    LogAct Shared-Log Backbone - Authoritative Singleton for AlphaAlgo UCA V5.
    Provides a transactional shared log while maintaining backward compatibility.
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
        self._voters: Dict[str, Callable[[LogAction], Coroutine[Any, Any, Dict[str, Any]]]] = {}
        self._subscribers: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._running = False
        self._action_queue: Optional[asyncio.PriorityQueue] = None
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
        self._action_queue = asyncio.PriorityQueue()
        self._running = True
        self._processor_task = asyncio.create_task(self._process_log())
        logger.info("LogAct Backbone processing started")

    async def stop(self):
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
        logger.info("LogAct Backbone processing stopped")

    # --- UCA V5 API ---

    def register_voter(self, voter_id: str, voter_fn: Callable[[LogAction], Coroutine[Any, Any, Dict[str, Any]]]):
        """Register a decoupled voter for action verification."""
        self._voters[voter_id] = voter_fn
        logger.info(f"Registered LogAct Voter: {voter_id}")

    async def propose_action(self, action: LogAction):
        """Entry point for agents to propose an intervention."""
        if not self._running:
            logger.warning("Attempted to propose action to stopped LogAct Backbone")
            return
        action.status = ActionStatus.PROPOSED
        # PriorityQueue uses min-heap, so we use negative priority
        await self._action_queue.put((-action.priority.value, action.timestamp, action))
        logger.debug(f"Proposed action {action.action_id} from agent {action.agent_id}")

    # --- Legacy Compatibility API ---

    def subscribe(
        self,
        subscriber_id: str,
        event_types: Union[str, List[str]],
        handler: Callable[[Union[UnifiedEvent, LogAction]], Coroutine[Any, Any, None]] = None,
        priority: int = 0
    ):
        """
        Backward compatible subscribe method.
        If handler is None, it assumes the V5 signature: subscribe(action_type, handler)
        """
        # Support V5 signature: subscribe(action_type, handler)
        if handler is None and isinstance(subscriber_id, str) and callable(event_types):
            action_type = subscriber_id
            v5_handler = event_types
            self._subscribers[action_type].append({
                "id": "v5_sub",
                "handler": v5_handler,
                "priority": 0
            })
            return

        # Support Legacy signature
        if isinstance(event_types, str):
            event_types = [event_types]

        for etype in event_types:
            self._subscribers[etype].append({
                "id": subscriber_id,
                "handler": handler,
                "priority": priority
            })
            self._subscribers[etype].sort(key=lambda x: x["priority"], reverse=True)

    async def publish(self, event: UnifiedEvent):
        """Backward compatible publish method. Wraps event into a LogAction."""
        if not self._running:
            logger.warning("Attempted to publish to stopped UnifiedDecisionBus")
            return

        action = LogAction(
            action_type=event.event_type,
            payload=event.payload,
            agent_id=event.source,
            action_id=event.event_id,
            timestamp=event.timestamp,
            correlation_id=event.correlation_id,
            priority=event.priority
        )
        await self.propose_action(action)

    # --- Internal Logic ---

    async def _process_log(self):
        """Autoritative log processing and total ordering."""
        while self._running:
            try:
                _, _, action = await self._action_queue.get()

                # 1. Total Ordering
                action.sequence_number = len(self._log)
                self._log.append(action)

                # 2. Decoupled Voting (Audit Phase)
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
                            logger.error(f"Voter {vid} failed: {res}")
                            action.voter_reports[vid] = {"decision": "ERROR", "reason": str(res)}
                        else:
                            action.voter_reports[vid] = res

                # 3. Consensus Logic
                if self._verify_consensus(action):
                    action.status = ActionStatus.APPROVED
                    logger.info(f"Action {action.action_id} APPROVED [Seq: {action.sequence_number}]")
                    # 4. Dispatch to Consumers
                    await self._dispatch(action)
                else:
                    action.status = ActionStatus.VETOED
                    logger.warning(f"Action {action.action_id} VETOED by voters")

                self._action_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"LogAct Processor Critical Failure: {e}")

    def _verify_consensus(self, action: LogAction) -> bool:
        """Basic consensus: No 'REJECT' or 'VETO' from any registered voter."""
        for vid, report in action.voter_reports.items():
            decision = report.get("decision", "UNKNOWN")
            if decision in ["REJECT", "VETO", "FAIL"]:
                logger.warning(f"Consensus Veto: {vid} rejected {action.action_id}: {report.get('reason')}")
                return False
        return True

    async def _dispatch(self, action: LogAction):
        """Dispatch approved actions to subscribers."""
        handlers = self._subscribers.get(action.action_type, [])
        handlers.extend(self._subscribers.get("*", []))

        if not handlers:
            return

        # If it was a legacy event, pass it as UnifiedEvent if handler expects it?
        # For simplicity, we pass the LogAction, but we could wrap it.
        # Most handlers will just access .payload
        tasks = [h["handler"](action) for h in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)

# Shared Access Point
decision_bus = UnifiedDecisionBus()
