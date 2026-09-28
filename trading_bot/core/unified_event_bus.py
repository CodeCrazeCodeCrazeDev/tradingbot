
from enum import Enum
from dataclasses import dataclass, field
import uuid, hashlib, hmac, time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

class CapabilityDomain(Enum):
    INTELLIGENCE = "INTELLIGENCE"
    RESEARCH = "RESEARCH"
    GOVERNANCE = "GOVERNANCE"
    RISK = "RISK"
    EXECUTION = "EXECUTION"
    DEPLOYMENT = "DEPLOYMENT"

@dataclass
class SignedInterAgentMessage:
    sender_id: str
    sender_version: str
    task_id: str
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
    causal_parent: Optional[str] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    payload_hash: str = ""
    capabilities: List[str] = field(default_factory=list)
    expiration: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp() + 300.0)
    signature: str = ""

    def __post_init__(self):
        if not self.payload_hash:
            self.payload_hash = hashlib.sha256(str(sorted(self.payload.items())).encode("utf-8")).hexdigest()
        if not self.signature:
            self.signature = self.compute_signature("SYSTEM_SECRET_KEY")

    def compute_signature(self, secret: str) -> str:
        data = f"{self.sender_id}:{self.sender_version}:{self.task_id}:{self.message_id}:{self.timestamp}:{self.payload_hash}"
        return hmac.new(secret.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify_signature(self, secret: str = "SYSTEM_SECRET_KEY") -> bool:
        if datetime.now(timezone.utc).timestamp() > self.expiration:
            return False
        current_hash = hashlib.sha256(str(sorted(self.payload.items())).encode("utf-8")).hexdigest()
        if current_hash != self.payload_hash:
            return False # Payload was tampered with!
        expected = self.compute_signature(secret)
        return hmac.compare_digest(self.signature, expected)

"""
LogAct Shared-Log Backbone - UCA V6 Core Component
=============================================

The authoritative, totally ordered shared log for AlphaAlgo UCA V6.
Implements 'LogAct: Enabling Agentic Reliability via Shared Logs' (Paper 1).
"""

import asyncio
import itertools
import time
import logging
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union, Callable
from uuid import uuid4
import threading
from .governance.determinism import determinism

logger = logging.getLogger(__name__)

# Action types that authorize capital movement. These are fail-closed: a
# shield voter must not merely fail to veto — it must return an explicit
# affirmative decision inside the voter timeout.
SHIELDED_ACTION_TYPES = {"TRADE_PROPOSAL", "TRADE_EXECUTION", "ORDER", "EXECUTE"}
_AFFIRMATIVE_DECISIONS = {"APPROVE", "APPROVED", "ALLOW", "PASS"}
_VETO_DECISIONS = {"REJECT", "VETO", "FAIL", "BLOCKED"}


def _is_shield_voter(voter_id: str) -> bool:
    return voter_id in ("ImmutableShield", "shield") or "shield" in voter_id.lower()


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
    def action_id(self) -> str:
        return self.event_id

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
    _instance: Optional['UnifiedDecisionBus'] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(UnifiedDecisionBus, cls).__new__(cls)
            return cls._instance

    def __init__(self, config: Optional[Dict] = None):
        if getattr(self, "_initialized", False):
            # Singleton: re-apply an explicitly passed config (e.g. a fresh
            # log_path after reset) without re-running full construction.
            if config:
                self.config.update(config)
                if "log_path" in config:
                    self._log_path = config["log_path"]
            return
        self.config = config or {}
        self._log_path = self.config.get("log_path")
        self._log: List[Union[LogAction, UnifiedEvent]] = []
        self._voters: Dict[str, Callable] = {}
        self._subscribers: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._action_queue = asyncio.PriorityQueue()
        self._action_seq = itertools.count()
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        self._tasks: Set[asyncio.Task] = set()
        self._initialized = True
        logger.info("LogAct Shared-Log Backbone initialized")

    @classmethod
    def reset(cls):
        """Resets the global decision bus instance state in-place."""
        global decision_bus
        with cls._lock:
            if decision_bus is not None:
                decision_bus._running = False
                task = getattr(decision_bus, '_processor_task', None)
                if task and not task.done():
                    task.cancel()
                    decision_bus._processor_task = None
                decision_bus._log.clear()
                decision_bus._voters.clear()
                decision_bus._subscribers.clear()
                try:
                    decision_bus._action_queue = asyncio.PriorityQueue()
                    decision_bus._action_seq = itertools.count()
                except Exception:
                    logger.debug("UnifiedDecisionBus: action queue rebuild skipped", exc_info=True)
            else:
                decision_bus = UnifiedDecisionBus()
                cls._instance = decision_bus
        logger.info("UnifiedDecisionBus reset complete.")

    async def start(self):
        if getattr(self, '_processor_task', None) and not self._processor_task.done():
            return
        self._running = True
        task = asyncio.create_task(self._process_log())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        self._processor_task = task
        logger.info("LogAct Backbone processing started")

    async def stop(self):
        self._running = False
        task = getattr(self, '_processor_task', None)
        if task is not None:
            task.cancel()
            try:
                if task.get_loop() is asyncio.get_running_loop():
                    await task
            except (asyncio.CancelledError, RuntimeError):
                pass
            self._processor_task = None

    def register_voter(self, voter_id: str, voter_fn: Callable):
        self._voters[voter_id] = voter_fn

    def _migrate_queue_to_loop(self, running_loop) -> None:
        """Rebuild ``_action_queue`` when it is bound to a different loop.

        ``asyncio.Queue`` lazily binds to the first loop that blocks on it.
        If the bus was started on one loop (e.g. a fixture/setup loop or a
        restarted runtime) and actions are later proposed from another, every
        ``get()``/``put()`` on the stale queue raises "bound to a different
        event loop". Rebuilding on the current loop and migrating pending
        items lets the running processor recover on its next poll.
        """
        old_q = self._action_queue
        if old_q is None or getattr(old_q, "_loop", None) in (None, running_loop):
            return
        self._action_queue = asyncio.PriorityQueue()
        while True:
            try:
                self._action_queue.put_nowait(old_q.get_nowait())
            except asyncio.QueueEmpty:
                break

    async def propose_action(self, action: LogAction):
        """Proposes an action to the shared log."""
        running_loop = asyncio.get_running_loop()
        self._migrate_queue_to_loop(running_loop)
        processor = getattr(self, "_processor_task", None)
        if self._running and processor is not None and not processor.done():
            try:
                stale_loop = processor.get_loop() is not running_loop
            except Exception:
                stale_loop = True
            if stale_loop:
                logger.warning(
                    "LogAct: processor task bound to a different event loop; "
                    "restarting on the current loop so actions are not dropped."
                )
                processor.cancel()
                self._processor_task = None
        if not self._running or getattr(self, "_processor_task", None) is None:
            logger.warning(f"LogAct: Attempted to propose action {action.action_id} while bus is not running. Starting bus...")
            await self.start()

        action.status = ActionStatus.PROPOSED
        if self._action_queue is None:
            self._action_queue = asyncio.PriorityQueue()
        if getattr(self, "_action_seq", None) is None:
            self._action_seq = itertools.count()
        # seq is the final tiebreaker: equal priorities+timestamps must never
        # fall through to comparing LogAction instances (unorderable).
        await self._action_queue.put((-action.priority.value, action.timestamp, next(self._action_seq), action))
        logger.debug(f"LogAct: Action {action.action_id} queued for auditing (Priority: {action.priority.name})")

    async def publish(self, event: Any):
        if isinstance(event, UnifiedEvent):
            # Events dispatch directly to subscribers; only LogActions go
            # through voter consensus (an event has no audit fields).
            await self._dispatch(event)
        elif isinstance(event, LogAction) or hasattr(event, "priority"):
            await self.propose_action(event)
        else:
            action = LogAction(
                action_type=getattr(event, "event_type", "EVENT"),
                payload=getattr(event, "payload", {}),
                agent_id=getattr(event, "source", "anon")
            )
            await self.propose_action(action)

    async def publish_contract(
        self,
        action_type: str,
        contract: Any,
        source: str = "foundation",
        priority: EventPriority = EventPriority.NORMAL,
    ) -> LogAction:
        """Publish a typed foundation contract through the shared audit bus.

        The bus remains backward-compatible with dictionary payloads while this
        bridge makes the contract boundary explicit for new data and execution
        paths. Contracts must expose ``to_dict`` so secrets and serialization
        policy stay outside the bus implementation.
        """
        serializer = getattr(contract, "to_dict", None)
        if serializer is None or not callable(serializer):
            raise TypeError("publish_contract requires a contract with to_dict()")
        payload = serializer()
        if not isinstance(payload, dict):
            raise TypeError("contract.to_dict() must return a dictionary")
        action = LogAction(
            action_type=action_type,
            payload=payload,
            agent_id=source,
            priority=priority,
        )
        await self.propose_action(action)
        return action

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
        Instrumented with UCA V6 high-resolution tracing.
        """
        max_log_size = self.config.get("max_log_size", 10000)
        while self._running:
            action = None
            start_time = time.time()
            try:
                # 1. Queue Retrieval
                _, _, _, action = await self._action_queue.get()
                t_start = datetime.utcnow()
                action.sequence_number = len(self._log)
                self._log.append(action)
                if len(self._log) > max_log_size:
                    self._log.pop(0)

                logger.debug(f"LogAct [{action.sequence_number}]: Processing action {action.action_id} ({action.action_type})")

                # 2. Audit Phase (Voter Execution)
                action.status = ActionStatus.AUDITING
                voter_ids = list(self._voters.keys())

                # UCA V6: Mandatory voter verification
                # Fail-closed: if no shield voter is registered, an action that
                # authorizes capital movement is vetoed rather than silently
                # auto-approved. Internal/non-execution actions (telemetry,
                # test, diagnostics) are not shield-gated.
                requires_shield = getattr(action, "action_type", "") in SHIELDED_ACTION_TYPES
                has_shield = any(_is_shield_voter(k) for k in voter_ids)
                if requires_shield and not has_shield:
                    logger.warning(f"LogAct: No shield voter registered. VETOING action {action.action_id} (fail-closed).")
                    action.voter_reports["__missing_shield__"] = {
                        "decision": "VETO",
                        "reason": "Mandatory shield voter missing; consensus fails closed",
                    }
                    if not self._check_consensus(action):
                        action.status = ActionStatus.VETOED
                        continue

                vote_tasks = []
                voter_timeout = float(self.config.get("voter_timeout", 0) or 0)
                for v_id, vfn in self._voters.items():
                    try:
                        if asyncio.iscoroutinefunction(vfn):
                            vote_coro = vfn(action)
                        else:
                            loop = asyncio.get_event_loop()
                            vote_coro = loop.run_in_executor(None, vfn, action)
                        if voter_timeout > 0:
                            vote_coro = asyncio.wait_for(vote_coro, timeout=voter_timeout)
                        vote_tasks.append(vote_coro)
                    except Exception as e:
                        logger.error(f"LogAct: Error preparing voter {v_id}: {e}")

                if vote_tasks:
                    v_start = datetime.utcnow()
                    results = await asyncio.gather(*vote_tasks, return_exceptions=True)
                    v_end = datetime.utcnow()

                    for i, res in enumerate(results):
                        vid = voter_ids[i]
                        if isinstance(res, (asyncio.TimeoutError, TimeoutError)):
                            # Voter timeout is an ERROR report, not a veto — the
                            # remaining voters still decide consensus.
                            action.voter_reports[vid] = {
                                "decision": "ERROR",
                                "reason": f"Timeout after {voter_timeout}s",
                            }
                        elif isinstance(res, Exception):
                            action.voter_reports[vid] = {"decision": "FAIL", "reason": str(res)}
                        else:
                            action.voter_reports[vid] = res

                    logger.debug(f"LogAct [{action.sequence_number}]: Voter phase complete in {(v_end - v_start).total_seconds():.3f}s")

                # 3. Consensus Phase
                c_start = datetime.utcnow()
                if self._check_consensus(action):
                    action.status = ActionStatus.APPROVED
                    logger.info(f"LogAct [{action.sequence_number}]: Action {action.action_id} APPROVED")

                    # 4. Dispatch Phase — the bus approves and fans out; the
                    # execution layer (e.g. PaperExecutionBridge) owns EXECUTED.
                    await self._dispatch(action)
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
                if action is None:
                    # Avoid a hot spin when queue polling itself keeps failing.
                    await asyncio.sleep(0.05)
                if action:
                    action.status = ActionStatus.FAILED
            finally:
                if action:
                    action._completed_event.set()
                    self._action_queue.task_done()
                    if self._log_path:
                        try:
                            with open(self._log_path, "a", encoding="utf-8") as f:
                                f.write(json.dumps(action.to_dict(), default=str) + "\n")
                        except Exception as e:
                            logger.error(f"LogAct: persistence write failed: {e}")

    def _check_consensus(self, action: LogAction) -> bool:
        """
        UCA V6 Consensus Logic.
        Hardened: Case-insensitive and supports multiple result formats.

        For shielded (capital-moving) action types the shield voter must return
        an explicit affirmative decision. An ERROR/FAIL/timeout report, an
        abstention, or a missing shield report vetoes the action — absence of a
        veto is not approval when safety evidence is unavailable.
        """
        requires_shield = getattr(action, "action_type", "") in SHIELDED_ACTION_TYPES
        shield_affirmed = not requires_shield
        for vid, report in action.voter_reports.items():
            decision = ""
            if isinstance(report, dict):
                decision = str(report.get("decision", "FAIL")).upper()
            elif isinstance(report, str):
                decision = report.upper()
            if decision in _VETO_DECISIONS:
                logger.warning(f"LogAct: Action {action.action_id} VETOED by {vid}: "
                               f"{report.get('reason', 'No reason') if isinstance(report, dict) else report}")
                return False
            if requires_shield and _is_shield_voter(str(vid)):
                if decision in _AFFIRMATIVE_DECISIONS:
                    shield_affirmed = True
                else:
                    logger.warning(
                        f"LogAct: Action {action.action_id} VETOED — shield voter "
                        f"'{vid}' returned non-affirmative '{decision or 'no decision'}' "
                        f"(fail-closed)."
                    )
                    return False
        if requires_shield and not shield_affirmed:
            logger.warning(f"LogAct: Action {action.action_id} VETOED — no affirmative shield report")
            return False
        return True

    async def _dispatch(self, action: LogAction):
        key = getattr(action, "action_type", None) or getattr(action, "event_type", "")
        handlers = self._subscribers.get(key, []) + self._subscribers.get("*", [])
        tasks = [h["handler"](action) for h in handlers]
        if not tasks:
            return
        results = await asyncio.gather(*tasks, return_exceptions=True)
        failures = []
        for h, res in zip(handlers, results):
            if isinstance(res, Exception):
                failures.append(f"{h['id']}: {res!r}")
            elif isinstance(res, dict) and str(res.get("status", "")).lower() in ("rejected", "failed"):
                failures.append(f"{h['id']}: {res.get('status')} ({res.get('reason', '')})")
        if failures:
            logger.error(f"LogAct: subscriber failures for {action.action_id}: {failures}")
            # A shielded action whose handler failed was never carried out —
            # mark FAILED so the audit trail and waiters see a terminal
            # failure, not an APPROVED that only looks executed. An action
            # already flipped to EXECUTED by the execution bridge stays EXECUTED:
            # the fill happened; the secondary handler failure is logged.
            if (getattr(action, "action_type", "") in SHIELDED_ACTION_TYPES
                    and action.status is not ActionStatus.EXECUTED):
                action.status = ActionStatus.FAILED

    def get_action_by_id(self, action_id: str) -> Optional[LogAction]:
        """Look up a processed action in the shared audit log by id."""
        for entry in self._log:
            if getattr(entry, "action_id", None) == action_id:
                return entry
        return None

# Global instance for production path (authoritative)
decision_bus = UnifiedDecisionBus()
