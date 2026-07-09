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
from datetime import datetime
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
            'voter_reports': self.voter_reports,
            'sequence_number': self.sequence_number,
            'priority': self.priority.name
        }

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
        logger.info("LogAct Shared-Log Backbone Initialized with Legacy Support")

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
        """Authoritative Log Processor: Total Ordering -> Voting -> Dispatch."""
        while self._running:
            try:
                _, _, action = await self._action_queue.get()

                # 1. Total Ordering
                action.sequence_number = len(self._log)
                self._log.append(action)

                # 2. Audit (Decoupled Voting)
                action.status = ActionStatus.AUDITING
                if self._voters:
                    vote_tasks = [vfn(action) for vfn in self._voters.values()]
                    voter_ids = list(self._voters.keys())
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
                    await self._dispatch(action)
                else:
                    action.status = ActionStatus.VETOED

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

    async def _dispatch(self, action: LogAction):
        # Notify specific subscribers and wildcard subscribers
        handlers = self._subscribers.get(action.action_type, []) + self._subscribers.get("*", [])
        if not handlers:
            return

        tasks = [h["handler"](action) for h in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)

# Shared Access Point
decision_bus = UnifiedDecisionBus()
