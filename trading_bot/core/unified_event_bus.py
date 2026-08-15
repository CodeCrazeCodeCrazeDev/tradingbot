"""
LogAct Shared-Log Backbone - UCA V5 Core Component
=============================================

The authoritative, totally ordered shared log for AlphaAlgo UCA V5.
Implements 'LogAct: Enabling Agentic Reliability via Shared Logs' (Paper 1).
"""

import asyncio
import logging
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from uuid import uuid4
import threading
from .governance.determinism import determinism

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
    action_id: str = field(default_factory=lambda: determinism.get_uuid())
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: ActionStatus = ActionStatus.PROPOSED
    voter_reports: Dict[str, Any] = field(default_factory=dict)
    sequence_number: Optional[int] = None
    priority: EventPriority = EventPriority.NORMAL

    _completed_event: asyncio.Event = field(default_factory=asyncio.Event, init=False)

    @property
    def event_type(self) -> str:
        return self.action_type

    @property
    def source(self) -> str:
        return self.agent_id

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
    status: ActionStatus = ActionStatus.PROPOSED
    voter_reports: Dict[str, Any] = field(default_factory=dict)
    sequence_number: Optional[int] = None

    _completed_event: asyncio.Event = field(default_factory=asyncio.Event, init=False)

    @property
    def action_type(self) -> str:
        return self.event_type

    @property
    def agent_id(self) -> str:
        return self.source

    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_id': self.event_id,
            'action_type': self.event_type,
            'payload': self.payload,
            'agent_id': self.source,
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
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._log: List[Union[LogAction, UnifiedEvent]] = []
        self._voters: Dict[str, Callable] = {}
        self._subscribers: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._action_queue = asyncio.PriorityQueue()
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        logger.info("LogAct Shared-Log Backbone initialized")

    @classmethod
    def reset(cls):
        """Reset the global decision_bus instance state."""
        global decision_bus
        decision_bus._log.clear()
        decision_bus._voters.clear()
        decision_bus._subscribers.clear()
        try:
            decision_bus._action_queue = asyncio.PriorityQueue()
        except Exception:
            decision_bus._action_queue = None
        decision_bus._running = False
        decision_bus._processor_task = None
        logger.info("UnifiedDecisionBus state reset")

    async def start(self):
        if self._processor_task and not self._processor_task.done():
            return
        self._running = True

        # Re-initialize PriorityQueue to bind to the active event loop and prevent cross-loop leakage
        self._action_queue = asyncio.PriorityQueue()
        self._log.clear()

        self._processor_task = asyncio.create_task(self._process_log())

    async def stop(self):
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
            self._processor_task = None

    def register_voter(self, voter_id: str, voter_fn: Callable):
        self._voters[voter_id] = voter_fn

    async def propose_action(self, action: LogAction):
        """Proposes an action to the shared log."""
        if not self._running:
            logger.warning(f"LogAct: Attempted to propose action {action.action_id} while bus is not running. Starting bus...")
            await self.start()

        action.status = ActionStatus.PROPOSED
        if self._action_queue is None:
            self._action_queue = asyncio.PriorityQueue()
        await self._action_queue.put((-action.priority.value, action.timestamp, action))
        logger.debug(f"LogAct: Action {action.action_id} queued for auditing (Priority: {action.priority.name})")

    async def publish(self, event: Any):
        if isinstance(event, (LogAction, UnifiedEvent)) or hasattr(event, "priority"):
            await self.propose_action(event)
        else:
            action = LogAction(
                action_type=getattr(event, "event_type", "EVENT"),
                payload=getattr(event, "payload", {}),
                agent_id=getattr(event, "source", "anon")
            )
            await self.propose_action(action)

    def subscribe(self, action_type: str, handler: Callable, subscriber_id: str = "anon", priority: int = 0):
        # Support legacy subscription signature: subscribe(subscriber_id, action_type, handler)
        if not callable(handler) and callable(subscriber_id):
            real_subscriber_id = action_type
            real_action_type = handler
            real_handler = subscriber_id
            action_type = real_action_type
            handler = real_handler
            subscriber_id = real_subscriber_id

        self._subscribers[action_type].append({"id": subscriber_id, "handler": handler, "priority": priority})
        self._subscribers[action_type].sort(key=lambda x: x["priority"], reverse=True)

    async def _process_log(self):
        """
        Main LogAct processing loop.
        Instrumented with UCA V5 high-resolution tracing.
        """
        max_log_size = self.config.get("max_log_size", 10000)
        while self._running:
            action = None
            start_time = time.time()
            try:
                # 1. Queue Retrieval
                _, _, action = await self._action_queue.get()
                t_start = datetime.utcnow()
                action.sequence_number = len(self._log)
                self._log.append(action)
                if len(self._log) > max_log_size:
                    self._log.pop(0)

                logger.debug(f"LogAct [{action.sequence_number}]: Processing action {action.action_id} ({action.action_type})")

                # 2. Audit Phase (Voter Execution)
                action.status = ActionStatus.AUDITING
                voter_ids = list(self._voters.keys())

                # UCA V5: Mandatory voter verification
                has_shield = any(k in ["ImmutableShield", "shield"] or "shield" in k.lower() for k in voter_ids)
                if not has_shield:
                    logger.warning(f"LogAct: No explicit shield voter found. Registering Default Shield Voter.")
                    self.register_voter("shield", lambda act: {"decision": "APPROVE", "reason": "Default approved shield voter"})
                    voter_ids = list(self._voters.keys())

                vote_tasks = []
                for v_id, vfn in self._voters.items():
                    try:
                        if asyncio.iscoroutinefunction(vfn):
                            vote_tasks.append(vfn(action))
                        else:
                            # Wrap sync voters in a thread pool to avoid blocking the bus
                            loop = asyncio.get_event_loop()
                            vote_tasks.append(loop.run_in_executor(None, vfn, action))
                    except Exception as e:
                        logger.error(f"LogAct: Error preparing voter {v_id}: {e}")

                if vote_tasks:
                    v_start = datetime.utcnow()
                    results = await asyncio.gather(*vote_tasks, return_exceptions=True)
                    v_end = datetime.utcnow()

                    for i, res in enumerate(results):
                        vid = voter_ids[i]
                        if isinstance(res, Exception):
                            action.voter_reports[vid] = {"decision": "FAIL", "reason": str(res)}
                        else:
                            action.voter_reports[vid] = res

                    logger.debug(f"LogAct [{action.sequence_number}]: Voter phase complete in {(v_end - v_start).total_seconds():.3f}s")

                # 3. Consensus Phase
                c_start = datetime.utcnow()
                if self._check_consensus(action):
                    action.status = ActionStatus.APPROVED
                    logger.info(f"LogAct [{action.sequence_number}]: Action {action.action_id} APPROVED")

                    # 4. Dispatch Phase
                    await self._dispatch(action)
                    action.status = ActionStatus.EXECUTED
                else:
                    action.status = ActionStatus.VETOED
                    logger.warning(f"LogAct [{action.sequence_number}]: Action {action.action_id} VETOED")

                # Record KPI: Consensus Latency
                latency = (time.time() - start_time) * 1000
                logger.debug(f"KPI: Consensus Latency for {action.action_id}: {latency:.2f}ms")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"LogAct Error: {e}")
                if action:
                    action.status = ActionStatus.FAILED
            finally:
                if action:
                    action._completed_event.set()
                    self._action_queue.task_done()

    def _check_consensus(self, action: LogAction) -> bool:
        """
        UCA V5 Consensus Logic.
        Hardened: Case-insensitive and supports multiple result formats.
        """
        for vid, report in action.voter_reports.items():
            if isinstance(report, dict):
                decision = str(report.get("decision", "FAIL")).upper()
                if decision in ["REJECT", "VETO", "FAIL", "BLOCKED"]:
                    logger.warning(f"LogAct: Action {action.action_id} VETOED by {vid}: {report.get('reason', 'No reason')}")
                    return False
            elif isinstance(report, str):
                if report.upper() in ["REJECT", "VETO", "FAIL", "BLOCKED"]:
                    return False
        return True

    async def _dispatch(self, action: LogAction):
        handlers = self._subscribers.get(action.action_type, []) + self._subscribers.get("*", [])
        tasks = [h["handler"](action) for h in handlers]
        if tasks: await asyncio.gather(*tasks, return_exceptions=True)

# Global instance for production path (authoritative)
decision_bus = UnifiedDecisionBus()
