"""
Lightweight agent-to-agent interoperability primitives.

This module provides a small in-process A2A transport that different agent
systems in the trading bot can share without introducing external dependencies.
"""

from __future__ import annotations

import copy
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence


def _utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class A2AMessage:
    """Portable envelope for agent-to-agent communication."""

    message_id: str
    sender: str
    recipients: List[str]
    intent: str
    payload: Dict[str, Any]
    channel: str = "default"
    conversation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_utc_now_iso)
    protocol_version: str = "a2a/v1"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the message into a plain dictionary."""
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "recipients": list(self.recipients),
            "intent": self.intent,
            "payload": copy.deepcopy(self.payload),
            "channel": self.channel,
            "conversation_id": self.conversation_id,
            "metadata": copy.deepcopy(self.metadata),
            "timestamp": self.timestamp,
            "protocol_version": self.protocol_version,
        }


class A2AMessageBus:
    """
    Simple in-memory A2A transport shared across agent systems.

    The implementation is intentionally minimal: it supports agent registration,
    direct messages, broadcasts, and recent message lookup. That is enough to
    unify the currently disconnected agent layers in this repository.
    """

    def __init__(self, protocol_version: str = "a2a/v1"):
        self.protocol_version = protocol_version
        self._messages: List[A2AMessage] = []
        self._registrations: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def register_agent(
        self,
        agent_id: str,
        capabilities: Optional[Sequence[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Register or update an agent on the bus."""
        with self._lock:
            registration = {
                "agent_id": agent_id,
                "capabilities": list(capabilities or []),
                "metadata": copy.deepcopy(metadata or {}),
                "registered_at": _utc_now_iso(),
            }
            self._registrations[agent_id] = registration
            return copy.deepcopy(registration)

    def list_agents(self) -> List[str]:
        """Return all registered agent identifiers."""
        with self._lock:
            return list(self._registrations.keys())

    def get_agent_registration(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Return the registration for one agent, if available."""
        with self._lock:
            registration = self._registrations.get(agent_id)
            return copy.deepcopy(registration) if registration else None

    def send(
        self,
        sender: str,
        recipients: Sequence[str],
        intent: str,
        payload: Dict[str, Any],
        *,
        channel: str = "default",
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> A2AMessage:
        """Send a direct message to one or more recipients."""
        with self._lock:
            message = A2AMessage(
                message_id=f"msg-{uuid.uuid4().hex[:12]}",
                sender=sender,
                recipients=list(recipients),
                intent=intent,
                payload=copy.deepcopy(payload),
                channel=channel,
                conversation_id=conversation_id,
                metadata=copy.deepcopy(metadata or {}),
                protocol_version=self.protocol_version,
            )
            self._messages.append(message)
            return message

    def broadcast(
        self,
        sender: str,
        intent: str,
        payload: Dict[str, Any],
        *,
        recipients: Optional[Sequence[str]] = None,
        channel: str = "broadcast",
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> A2AMessage:
        """Broadcast a message to all registered agents or a target subset."""
        if recipients is None:
            recipients = [agent_id for agent_id in self.list_agents() if agent_id != sender]
        return self.send(
            sender=sender,
            recipients=recipients,
            intent=intent,
            payload=payload,
            channel=channel,
            conversation_id=conversation_id,
            metadata=metadata,
        )

    def get_messages(
        self,
        agent_id: str,
        *,
        intent: Optional[str] = None,
        channel: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[A2AMessage]:
        """Fetch messages addressed to the given agent."""
        with self._lock:
            filtered = [
                message
                for message in self._messages
                if agent_id in message.recipients
                and (intent is None or message.intent == intent)
                and (channel is None or message.channel == channel)
            ]
            if limit is not None:
                filtered = filtered[-limit:]
            return list(filtered)

    def get_recent_messages(self, limit: int = 50) -> List[A2AMessage]:
        """Return the most recent messages on the bus."""
        with self._lock:
            return list(self._messages[-limit:])

    def message_count(self) -> int:
        """Return the total number of messages sent through the bus."""
        with self._lock:
            return len(self._messages)
