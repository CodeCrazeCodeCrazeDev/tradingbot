"""
LogAct Shared-Log Backbone - UCA V5 Core Component
=============================================

The authoritative, totally ordered shared log for AlphaAlgo UCA V5.
Implements 'LogAct: Enabling Agentic Reliability via Shared Logs' (Paper 1).
"""

import asyncio
import logging
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from uuid import uuid4
import threading

logger = logging.getLogger(__name__)

class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

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
    voter_reports: Dict[str, Any] = field(default_factory=dict)
    sequence_number: Optional[int] = None
    priority: EventPriority = EventPriority.NORMAL

    _completed_event: asyncio.Event = field(default_factory=asyncio.Event, init=False)

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
        try:
            await asyncio.wait_for(self._completed_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            if self.status in [ActionStatus.PROPOSED, ActionStatus.AUDITING]:
                self.status = ActionStatus.TIMED_OUT
        return self.status

class UnifiedDecisionBus:
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
        logger.info("LogAct Shared-Log Backbone initialized")

    async def start(self):
        if self._running: return
        # Re-initialize the queue to bind to the current running event loop
        self._action_queue = asyncio.PriorityQueue()
        self._running = True
        self._processor_task = asyncio.create_task(self._process_log())

    async def stop(self):
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()

    def register_voter(self, voter_id: str, voter_fn: Callable):
        self._voters[voter_id] = voter_fn

    async def propose_action(self, action: LogAction):
        action.status = ActionStatus.PROPOSED
        await self._action_queue.put((-action.priority.value, action.timestamp, action))

    def subscribe(self, action_type: str, handler: Callable, subscriber_id: str = "anon", priority: int = 0):
        self._subscribers[action_type].append({"id": subscriber_id, "handler": handler, "priority": priority})
        self._subscribers[action_type].sort(key=lambda x: x["priority"], reverse=True)

    async def _process_log(self):
        max_log_size = self.config.get("max_log_size", 1000)
        while self._running:
            try:
                _, _, action = await self._action_queue.get()
                action.sequence_number = len(self._log)
                self._log.append(action)
                if len(self._log) > max_log_size:
                    self._log.pop(0)

                action.status = ActionStatus.AUDITING
                voter_ids = list(self._voters.keys())
                vote_tasks = [vfn(action) for vfn in self._voters.values()]

                if vote_tasks:
                    results = await asyncio.gather(*vote_tasks, return_exceptions=True)
                    for i, res in enumerate(results):
                        vid = voter_ids[i]
                        action.voter_reports[vid] = res if not isinstance(res, Exception) else {"decision": "FAIL", "reason": str(res)}

                if self._check_consensus(action):
                    action.status = ActionStatus.APPROVED
                    await self._dispatch(action)
                    action.status = ActionStatus.EXECUTED
                else:
                    action.status = ActionStatus.VETOED

                action._completed_event.set()
                self._action_queue.task_done()
            except asyncio.CancelledError: break
            except Exception as e: logger.error(f"LogAct Error: {e}")

    def _check_consensus(self, action: LogAction) -> bool:
        for vid, report in action.voter_reports.items():
            if isinstance(report, dict) and report.get("decision") in ["REJECT", "VETO", "FAIL", "BLOCKED"]:
                return False
        return True

    async def _dispatch(self, action: LogAction):
        handlers = self._subscribers.get(action.action_type, []) + self._subscribers.get("*", [])
        tasks = [h["handler"](action) for h in handlers]
        if tasks: await asyncio.gather(*tasks, return_exceptions=True)

decision_bus = UnifiedDecisionBus()
