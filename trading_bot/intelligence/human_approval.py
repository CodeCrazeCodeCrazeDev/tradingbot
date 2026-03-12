"""
Human Approval Gate (#1)
=========================
Requires human confirmation for trades above a configurable threshold.
Default: $10,000,000 notional value.

The gate:
    - Blocks execution until human approves or rejects
    - Times out after configurable period (default 5 minutes)
    - Logs all approval requests and decisions
    - Supports auto-approve for paper mode
    - Persists approval history to SQLite
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"
    AUTO_APPROVED = "auto_approved"


@dataclass
class ApprovalRequest:
    request_id: str
    symbol: str
    direction: str          # "BUY" or "SELL"
    lots: float
    notional_value: float   # USD value of the trade
    price: float
    strategy: str
    confidence: float
    risk_reward: float
    reason: str             # Why the AI wants this trade
    status: ApprovalStatus = ApprovalStatus.PENDING
    human_comment: str = ""
    requested_at: datetime = field(default_factory=datetime.now)
    decided_at: Optional[datetime] = None
    timeout_seconds: float = 300.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "symbol": self.symbol,
            "direction": self.direction,
            "lots": self.lots,
            "notional_value": self.notional_value,
            "price": self.price,
            "strategy": self.strategy,
            "confidence": self.confidence,
            "risk_reward": self.risk_reward,
            "reason": self.reason,
            "status": self.status.value,
            "human_comment": self.human_comment,
            "requested_at": self.requested_at.isoformat(),
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
        }


class HumanApprovalGate:
    """
    Blocks trade execution for large trades until human approves.
    
    Usage:
        gate = HumanApprovalGate(threshold_usd=10_000_000)
        
        # Check if trade needs approval
        if gate.needs_approval(notional_value=15_000_000):
            request = gate.create_request(symbol, direction, lots, ...)
            approved = await gate.wait_for_approval(request)
            if not approved:
                return  # Don't execute
        
        # Execute trade...
    """

    def __init__(
        self,
        threshold_usd: float = 10_000_000.0,
        timeout_seconds: float = 300.0,
        auto_approve_paper: bool = True,
        db_path: Optional[str] = None,
        on_approval_needed: Optional[Callable] = None,
    ):
        self._threshold = threshold_usd
        self._timeout = timeout_seconds
        self._auto_approve_paper = auto_approve_paper
        self._is_paper_mode = False
        self._on_approval_needed = on_approval_needed

        # Pending approvals
        self._pending: Dict[str, ApprovalRequest] = {}
        self._approval_events: Dict[str, asyncio.Event] = {}

        # Stats
        self._total_requests = 0
        self._total_approved = 0
        self._total_rejected = 0
        self._total_timed_out = 0

        # Persistence
        if db_path is None:
            root = Path(__file__).resolve().parent.parent.parent
            db_path = str(root / "data" / "human_approvals.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db_path = db_path
        self._init_db()

        logger.info(
            f"[APPROVAL GATE] Initialized: threshold=${self._threshold:,.0f}, "
            f"timeout={self._timeout}s, auto_paper={self._auto_approve_paper}"
        )

    def set_paper_mode(self, is_paper: bool) -> None:
        self._is_paper_mode = is_paper

    @property
    def threshold(self) -> float:
        return self._threshold

    def needs_approval(self, notional_value: float) -> bool:
        return notional_value >= self._threshold

    def create_request(
        self,
        symbol: str,
        direction: str,
        lots: float,
        notional_value: float,
        price: float,
        strategy: str = "",
        confidence: float = 0.0,
        risk_reward: float = 0.0,
        reason: str = "",
    ) -> ApprovalRequest:
        self._total_requests += 1
        request_id = f"APR-{self._total_requests:06d}-{int(time.time())}"

        request = ApprovalRequest(
            request_id=request_id,
            symbol=symbol,
            direction=direction,
            lots=lots,
            notional_value=notional_value,
            price=price,
            strategy=strategy,
            confidence=confidence,
            risk_reward=risk_reward,
            reason=reason,
            timeout_seconds=self._timeout,
        )

        self._pending[request_id] = request
        self._approval_events[request_id] = asyncio.Event()
        self._save_request(request)

        logger.warning(
            f"[APPROVAL GATE] 🔔 HUMAN APPROVAL REQUIRED\n"
            f"  Request ID : {request_id}\n"
            f"  Symbol     : {symbol}\n"
            f"  Direction  : {direction}\n"
            f"  Lots       : {lots}\n"
            f"  Notional   : ${notional_value:,.2f}\n"
            f"  Price      : {price}\n"
            f"  Strategy   : {strategy}\n"
            f"  Confidence : {confidence:.1%}\n"
            f"  R:R        : {risk_reward:.1f}\n"
            f"  Reason     : {reason}\n"
            f"  Timeout    : {self._timeout}s\n"
            f"  ➡️  Call gate.approve('{request_id}') or gate.reject('{request_id}')"
        )

        if self._on_approval_needed:
            try:
                self._on_approval_needed(request)
            except Exception as e:
                logger.warning(f"Approval callback error: {e}")

        return request

    async def wait_for_approval(self, request: ApprovalRequest) -> bool:
        """Wait for human decision. Returns True if approved."""
        # Auto-approve in paper mode
        if self._auto_approve_paper and self._is_paper_mode:
            request.status = ApprovalStatus.AUTO_APPROVED
            request.decided_at = datetime.now()
            request.human_comment = "Auto-approved (paper mode)"
            self._total_approved += 1
            self._save_request(request)
            self._cleanup(request.request_id)
            logger.info(f"[APPROVAL GATE] ✅ Auto-approved {request.request_id} (paper mode)")
            return True

        # Wait for human decision with timeout
        event = self._approval_events.get(request.request_id)
        if not event:
            return False

        try:
            await asyncio.wait_for(event.wait(), timeout=request.timeout_seconds)
        except asyncio.TimeoutError:
            request.status = ApprovalStatus.TIMED_OUT
            request.decided_at = datetime.now()
            self._total_timed_out += 1
            self._save_request(request)
            self._cleanup(request.request_id)
            logger.warning(f"[APPROVAL GATE] ⏰ TIMED OUT {request.request_id} — trade BLOCKED")
            return False

        # Check final status
        approved = request.status == ApprovalStatus.APPROVED
        self._save_request(request)
        self._cleanup(request.request_id)
        return approved

    def approve(self, request_id: str, comment: str = "") -> bool:
        """Human approves a trade."""
        request = self._pending.get(request_id)
        if not request:
            logger.warning(f"[APPROVAL GATE] Request {request_id} not found or already decided")
            return False

        request.status = ApprovalStatus.APPROVED
        request.decided_at = datetime.now()
        request.human_comment = comment
        self._total_approved += 1

        event = self._approval_events.get(request_id)
        if event:
            event.set()

        logger.info(f"[APPROVAL GATE] ✅ APPROVED {request_id} by human. Comment: {comment}")
        return True

    def reject(self, request_id: str, comment: str = "") -> bool:
        """Human rejects a trade."""
        request = self._pending.get(request_id)
        if not request:
            logger.warning(f"[APPROVAL GATE] Request {request_id} not found or already decided")
            return False

        request.status = ApprovalStatus.REJECTED
        request.decided_at = datetime.now()
        request.human_comment = comment
        self._total_rejected += 1

        event = self._approval_events.get(request_id)
        if event:
            event.set()

        logger.info(f"[APPROVAL GATE] ❌ REJECTED {request_id} by human. Comment: {comment}")
        return True

    def get_pending(self) -> list:
        return [r.to_dict() for r in self._pending.values()]

    def stats(self) -> Dict[str, Any]:
        return {
            "threshold_usd": self._threshold,
            "total_requests": self._total_requests,
            "approved": self._total_approved,
            "rejected": self._total_rejected,
            "timed_out": self._total_timed_out,
            "pending": len(self._pending),
        }

    def _cleanup(self, request_id: str) -> None:
        self._pending.pop(request_id, None)
        self._approval_events.pop(request_id, None)

    # -- Persistence --

    def _init_db(self) -> None:
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute("""CREATE TABLE IF NOT EXISTS approval_history (
                request_id TEXT PRIMARY KEY,
                symbol TEXT, direction TEXT, lots REAL,
                notional_value REAL, price REAL,
                strategy TEXT, confidence REAL, risk_reward REAL,
                reason TEXT, status TEXT,
                human_comment TEXT,
                requested_at TEXT, decided_at TEXT
            )""")
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Approval DB init error: {e}")

    def _save_request(self, req: ApprovalRequest) -> None:
        try:
            conn = sqlite3.connect(self._db_path)
            conn.execute("""INSERT OR REPLACE INTO approval_history
                (request_id, symbol, direction, lots, notional_value, price,
                 strategy, confidence, risk_reward, reason, status,
                 human_comment, requested_at, decided_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (req.request_id, req.symbol, req.direction, req.lots,
                 req.notional_value, req.price, req.strategy, req.confidence,
                 req.risk_reward, req.reason, req.status.value,
                 req.human_comment, req.requested_at.isoformat(),
                 req.decided_at.isoformat() if req.decided_at else None))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Approval save error: {e}")
