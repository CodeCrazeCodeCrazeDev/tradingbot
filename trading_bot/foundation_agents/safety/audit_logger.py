"""
Audit Logger - Complete Audit Trail
========================================

Provides comprehensive audit logging for:
1. All trading decisions
2. Research activities
3. System changes
4. Safety interventions
5. Human overrides

Ensures complete accountability and traceability.
"""

import logging
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import deque
import uuid

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""
    TRADE_DECISION = "trade_decision"
    RESEARCH_ACTION = "research_action"
    SYSTEM_CHANGE = "system_change"
    SAFETY_INTERVENTION = "safety_intervention"
    HUMAN_OVERRIDE = "human_override"
    CONFIGURATION_CHANGE = "configuration_change"
    KNOWLEDGE_UPDATE = "knowledge_update"
    AGENT_ACTION = "agent_action"
    EXTERNAL_INPUT = "external_input"
    ERROR = "error"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFO = 1


@dataclass
class AuditEntry:
    """A single audit log entry"""
    entry_id: str
    timestamp: datetime
    event_type: AuditEventType
    
    # Actor
    actor_id: str  # agent_id, user_id, or "system"
    actor_type: str  # "agent", "human", "system"
    
    # Action
    action: str
    action_description: str
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Data
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    
    # State
    before_state: Optional[Dict] = None
    after_state: Optional[Dict] = None
    
    # Safety
    safety_checks: List[Dict] = field(default_factory=list)
    ethical_assessment: Optional[Dict] = None
    
    # Outcome
    success: bool = True
    error_message: Optional[str] = None
    
    # Metadata
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    parent_entry_id: Optional[str] = None
    
    # Integrity
    hash_value: Optional[str] = None
    
    def calculate_hash(self) -> str:
        """Calculate integrity hash for entry"""
        data = {
            'entry_id': self.entry_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'actor_id': self.actor_id,
            'action': self.action,
            'context': self.context
        }
        
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            'entry_id': self.entry_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'actor': self.actor_id,
            'action': self.action,
            'success': self.success
        }


class AuditLogger:
    """
    Audit Logger
    
    Provides complete audit trail for all system activities,
    ensuring accountability and regulatory compliance.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Storage
        self.entries: deque = deque(maxlen=self.config.get('max_entries', 10000))
        self.entries_by_type: Dict[AuditEventType, deque] = {
            t: deque(maxlen=1000) for t in AuditEventType
        }
        
        # Session tracking
        self.current_session: Optional[str] = None
        self.session_start: Optional[datetime] = None
        
        # Indexing
        self.entries_by_actor: Dict[str, List[str]] = {}
        self.entries_by_correlation: Dict[str, List[str]] = {}
        
        # Integrity chain
        self.last_hash: Optional[str] = None
        
        # Statistics
        self.stats = {
            'total_entries': 0,
            'by_type': {t.value: 0 for t in AuditEventType},
            'by_severity': {s.value: 0 for s in AuditSeverity}
        }
        
        logger.info("Audit Logger initialized")
    
    def start_session(self, session_id: str, metadata: Optional[Dict] = None):
        """Start a new audit session"""
        self.current_session = session_id
        self.session_start = datetime.utcnow()
        
        self.log_event(
            event_type=AuditEventType.SYSTEM_CHANGE,
            actor_id="system",
            actor_type="system",
            action="session_start",
            action_description=f"Session {session_id} started",
            context=metadata or {}
        )
        
        logger.info(f"Audit session started: {session_id}")
    
    def log_event(
        self,
        event_type: AuditEventType,
        actor_id: str,
        actor_type: str,
        action: str,
        action_description: str = "",
        context: Optional[Dict] = None,
        input_data: Optional[Dict] = None,
        output_data: Optional[Dict] = None,
        before_state: Optional[Dict] = None,
        after_state: Optional[Dict] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        correlation_id: Optional[str] = None,
        parent_entry_id: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO
    ) -> AuditEntry:
        """Log an audit event"""
        entry = AuditEntry(
            entry_id=str(uuid.uuid4())[:12],
            timestamp=datetime.utcnow(),
            event_type=event_type,
            actor_id=actor_id,
            actor_type=actor_type,
            action=action,
            action_description=action_description,
            context=context or {},
            input_data=input_data or {},
            output_data=output_data or {},
            before_state=before_state,
            after_state=after_state,
            success=success,
            error_message=error_message,
            session_id=self.current_session,
            correlation_id=correlation_id,
            parent_entry_id=parent_entry_id
        )
        
        # Calculate hash for integrity
        entry.hash_value = entry.calculate_hash()
        
        # Chain with previous entry
        if self.last_hash:
            entry.context['_prev_hash'] = self.last_hash
        self.last_hash = entry.hash_value
        
        # Store entry
        self.entries.append(entry)
        self.entries_by_type[event_type].append(entry)
        
        # Index by actor
        if actor_id not in self.entries_by_actor:
            self.entries_by_actor[actor_id] = []
        self.entries_by_actor[actor_id].append(entry.entry_id)
        
        # Index by correlation
        if correlation_id:
            if correlation_id not in self.entries_by_correlation:
                self.entries_by_correlation[correlation_id] = []
            self.entries_by_correlation[correlation_id].append(entry.entry_id)
        
        # Update statistics
        self.stats['total_entries'] += 1
        self.stats['by_type'][event_type.value] += 1
        self.stats['by_severity'][severity.value] += 1
        
        return entry
    
    def log_trade_decision(
        self,
        agent_id: str,
        symbol: str,
        decision: str,  # "buy", "sell", "hold"
        quantity: float,
        price: float,
        rationale: str,
        confidence: float,
        safety_checks: Optional[List[Dict]] = None
    ) -> AuditEntry:
        """Log a trading decision"""
        return self.log_event(
            event_type=AuditEventType.TRADE_DECISION,
            actor_id=agent_id,
            actor_type="agent",
            action=decision,
            action_description=f"{decision.upper()} {quantity} {symbol} @ {price}",
            context={
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'rationale': rationale,
                'confidence': confidence
            },
            output_data={'safety_checks': safety_checks or []},
            severity=AuditSeverity.HIGH if decision != "hold" else AuditSeverity.INFO
        )
    
    def log_research_action(
        self,
        agent_id: str,
        action: str,
        hypothesis_id: Optional[str] = None,
        experiment_id: Optional[str] = None,
        result: Optional[str] = None
    ) -> AuditEntry:
        """Log a research action"""
        return self.log_event(
            event_type=AuditEventType.RESEARCH_ACTION,
            actor_id=agent_id,
            actor_type="agent",
            action=action,
            action_description=f"Research action: {action}",
            context={
                'hypothesis_id': hypothesis_id,
                'experiment_id': experiment_id,
                'result': result
            }
        )
    
    def log_safety_intervention(
        self,
        intervention_type: str,
        trigger: str,
        action_taken: str,
        affected_components: List[str],
        severity: AuditSeverity = AuditSeverity.HIGH
    ) -> AuditEntry:
        """Log a safety system intervention"""
        return self.log_event(
            event_type=AuditEventType.SAFETY_INTERVENTION,
            actor_id="safety_system",
            actor_type="system",
            action=intervention_type,
            action_description=f"Safety intervention: {intervention_type}",
            context={
                'trigger': trigger,
                'action_taken': action_taken,
                'affected_components': affected_components
            },
            severity=severity
        )
    
    def log_human_override(
        self,
        human_id: str,
        override_type: str,
        target_action: str,
        reason: str,
        previous_state: Optional[Dict] = None,
        new_state: Optional[Dict] = None
    ) -> AuditEntry:
        """Log a human override action"""
        return self.log_event(
            event_type=AuditEventType.HUMAN_OVERRIDE,
            actor_id=human_id,
            actor_type="human",
            action=override_type,
            action_description=f"Human override: {override_type} on {target_action}",
            context={'reason': reason},
            before_state=previous_state,
            after_state=new_state,
            severity=AuditSeverity.CRITICAL
        )
    
    def log_configuration_change(
        self,
        actor_id: str,
        actor_type: str,
        parameter: str,
        old_value: Any,
        new_value: Any,
        reason: str
    ) -> AuditEntry:
        """Log a configuration change"""
        return self.log_event(
            event_type=AuditEventType.CONFIGURATION_CHANGE,
            actor_id=actor_id,
            actor_type=actor_type,
            action="config_change",
            action_description=f"Changed {parameter}",
            context={'reason': reason},
            before_state={parameter: old_value},
            after_state={parameter: new_value},
            severity=AuditSeverity.MEDIUM
        )
    
    def get_entries(
        self,
        event_type: Optional[AuditEventType] = None,
        actor_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Query audit entries"""
        entries = list(self.entries)
        
        if event_type:
            entries = [e for e in entries if e.event_type == event_type]
        
        if actor_id:
            entries = [e for e in entries if e.actor_id == actor_id]
        
        if since:
            entries = [e for e in entries if e.timestamp >= since]
        
        if until:
            entries = [e for e in entries if e.timestamp <= until]
        
        # Sort by timestamp descending
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        
        return entries[:limit]
    
    def get_entry_chain(self, entry_id: str) -> List[AuditEntry]:
        """Get chain of related entries"""
        chain = []
        
        # Find entry
        entry = None
        for e in self.entries:
            if e.entry_id == entry_id:
                entry = e
                break
        
        if not entry:
            return chain
        
        chain.append(entry)
        
        # Follow parent links
        current = entry
        while current.parent_entry_id:
            for e in self.entries:
                if e.entry_id == current.parent_entry_id:
                    chain.append(e)
                    current = e
                    break
            else:
                break
        
        # Follow correlation links
        if entry.correlation_id:
            correlated = [
                e for e in self.entries
                if e.correlation_id == entry.correlation_id
                and e.entry_id != entry_id
            ]
            chain.extend(correlated)
        
        return chain
    
    def verify_integrity(self, entry_id: Optional[str] = None) -> bool:
        """Verify integrity of audit log or specific entry"""
        if entry_id:
            # Verify specific entry
            for entry in self.entries:
                if entry.entry_id == entry_id:
                    expected_hash = entry.calculate_hash()
                    return entry.hash_value == expected_hash
            return False
        else:
            # Verify entire chain
            for i, entry in enumerate(self.entries):
                if entry.hash_value != entry.calculate_hash():
                    return False
                
                # Check chain link (except for first entry)
                if i > 0:
                    prev_entry = self.entries[i-1]
                    if entry.context.get('_prev_hash') != prev_entry.hash_value:
                        return False
            
            return True
    
    def export_to_json(self, filepath: str, since: Optional[datetime] = None):
        """Export audit log to JSON file"""
        entries = self.get_entries(since=since, limit=10000)
        
        data = {
            'export_timestamp': datetime.utcnow().isoformat(),
            'entry_count': len(entries),
            'entries': [
                {
                    'entry_id': e.entry_id,
                    'timestamp': e.timestamp.isoformat(),
                    'event_type': e.event_type.value,
                    'actor': {
                        'id': e.actor_id,
                        'type': e.actor_type
                    },
                    'action': e.action,
                    'description': e.action_description,
                    'context': e.context,
                    'success': e.success,
                    'hash': e.hash_value
                }
                for e in entries
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Audit log exported to {filepath}")
    
    def generate_summary_report(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> Dict:
        """Generate summary report of audit activity"""
        entries = self.get_entries(since=since, until=until, limit=10000)
        
        # Count by type
        by_type = defaultdict(int)
        by_actor = defaultdict(int)
        by_success = {'success': 0, 'failure': 0}
        
        for entry in entries:
            by_type[entry.event_type.value] += 1
            by_actor[entry.actor_id] += 1
            by_success['success' if entry.success else 'failure'] += 1
        
        return {
            'period': {
                'since': since.isoformat() if since else 'all',
                'until': until.isoformat() if until else 'now'
            },
            'total_entries': len(entries),
            'by_type': dict(by_type),
            'by_actor': dict(by_actor),
            'by_success': by_success,
            'most_active_actor': max(by_actor.items(), key=lambda x: x[1])[0] if by_actor else None,
            'integrity_verified': self.verify_integrity()
        }
    
    def get_statistics(self) -> Dict:
        """Get logger statistics"""
        return {
            **self.stats,
            'current_session': self.current_session,
            'storage_utilization': len(self.entries) / self.entries.maxlen,
            'integrity_verified': self.verify_integrity()
        }
