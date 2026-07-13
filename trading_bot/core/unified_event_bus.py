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
from datetime import datetime, timedelta
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
    TIMED_OUT = "timed_out"
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

    # Synchronization for consensus
    _completed_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)

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
    Provides a transactional shared log with explicit state machine transitions.
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

        self.config = config or {
            "voter_timeout": 5.0,
            "max_log_size": 10000
        }
        self._log: List[LogAction] = []
        self._voters: Dict[str, Callable[[LogAction], Coroutine[Any, Any, Dict[str, Any]]]] = {}
        self._subscribers: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._running = False
        self._action_queue: Optional[asyncio.PriorityQueue] = None
        self._processor_task: Optional[asyncio.Task] = None
        self._initialized = True

        # Auto-register ImmutableShield as a voter
        try:
            from .immutable_shield import shield, GovernanceDecision
            async def shield_voter(action: LogAction) -> Dict[str, Any]:
                report = shield.validate_action(action.action_type, action.payload, action.payload.get("context", {}))
                return {
                    "decision": "APPROVED" if report.decision == GovernanceDecision.APPROVED else "VETO",
                    "reason": report.reason,
                    "audit_id": report.audit_id
                }
            self.register_voter("ImmutableShield", shield_voter)
        except ImportError:
            logger.warning("ImmutableShield not found during LogAct initialization")

        logger.info("LogAct Shared-Log Backbone initialized with Explicit State Machine")

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
            try:
                await self.start()
            except RuntimeError:
                logger.error("Attempted to propose action without running event loop")
                return

        action.status = ActionStatus.PROPOSED
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
        """Backward compatible subscribe method."""
        if handler is None and isinstance(subscriber_id, str) and callable(event_types):
            action_type = subscriber_id
            v5_handler = event_types
            self._subscribers[action_type].append({
                "id": "v5_sub",
                "handler": v5_handler,
                "priority": 0
            })
            return

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
        """Backward compatible publish method."""
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
        """Authoritative log processing with explicit state transitions."""
        while self._running:
            try:
                _, _, action = await self._action_queue.get()

                # 1. Total Ordering & Log Persistence
                action.sequence_number = len(self._log)
                self._log.append(action)
                if len(self._log) > self.config.get("max_log_size", 10000):
                    self._log.pop(0)

                # 2. Audit Phase (Explicit Transition: AUDITING)
                action.status = ActionStatus.AUDITING
                voter_timeout = self.config.get("voter_timeout", 5.0)

                voter_ids = list(self._voters.keys())
                if voter_ids:
                    tasks = [self._run_voter(vid, action) for vid in voter_ids]
                    try:
                        # Use asyncio.wait_for as a secondary safety, but _run_voter handles internal timeouts
                        await asyncio.gather(*tasks)
                    except Exception as e:
                        logger.error(f"Error during parallel voting for {action.action_id}: {e}")

                # 3. Consensus Phase (Explicit Transition: APPROVED or VETOED)
                if self._verify_consensus(action):
                    action.status = ActionStatus.APPROVED
                    logger.info(f"Action {action.action_id} APPROVED [Seq: {action.sequence_number}]")
                    # 4. Dispatch to Consumers
                    await self._dispatch(action)
                    action.status = ActionStatus.EXECUTED
                else:
                    action.status = ActionStatus.VETOED
                    logger.warning(f"Action {action.action_id} VETOED by voters")

                # Signal completion for wait_for_decision
                action._completed_event.set()
                self._action_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"LogAct Processor Critical Failure: {e}")

    async def _run_voter(self, voter_id: str, action: LogAction):
        """Runs a single voter with timeout handling."""
        voter_fn = self._voters.get(voter_id)
        if not voter_fn: return

        timeout = self.config.get("voter_timeout", 5.0)
        try:
            result = await asyncio.wait_for(voter_fn(action), timeout=timeout)
            action.voter_reports[voter_id] = result
        except asyncio.TimeoutError:
            logger.warning(f"Voter {voter_id} TIMED OUT for action {action.action_id}")
            action.voter_reports[voter_id] = {"decision": "TIMEOUT", "reason": "Voter exceeded time limit"}
        except Exception as e:
            logger.error(f"Voter {voter_id} FAILED for action {action.action_id}: {e}")
            action.voter_reports[voter_id] = {"decision": "ERROR", "reason": str(e)}

    def _verify_consensus(self, action: LogAction) -> bool:
        """Consensus logic: reject on any VETO, BLOCKED, or FAIL."""
        for vid, report in action.voter_reports.items():
            decision = str(report.get("decision", "UNKNOWN")).upper()
            if decision in ["REJECT", "VETO", "FAIL", "BLOCKED"]:
                return False
        return True

    async def _dispatch(self, action: LogAction):
        """Dispatch approved actions to subscribers."""
        handlers = self._subscribers.get(action.action_type, [])
        handlers.extend(self._subscribers.get("*", []))

        if handlers:
            tasks = [h["handler"](action) for h in handlers]
            await asyncio.gather(*tasks, return_exceptions=True)

# Shared Access Point
decision_bus = UnifiedDecisionBus()
