"""
Comprehensive Audit Logger

Immutable audit trail for all governance decisions and actions.
Records complete provenance for regulatory compliance and debugging.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of auditable events"""
    SIGNAL_RECEIVED = "signal_received"
    SIGNAL_VALIDATED = "signal_validated"
    CLAIM_CONSTRUCTED = "claim_constructed"
    EVIDENCE_AUDITED = "evidence_audited"
    ADVERSARIAL_CHALLENGE = "adversarial_challenge"
    REGIME_EVALUATED = "regime_evaluated"
    COUNTERFACTUAL_RUN = "counterfactual_run"
    UNCERTAINTY_COMPUTED = "uncertainty_computed"
    RISK_CHECKED = "risk_checked"
    EXECUTION_ASSESSED = "execution_assessed"
    DECISION_RENDERED = "decision_rendered"
    DECISION_OVERRIDDEN = "decision_overridden"
    TRADE_EXECUTED = "trade_executed"
    OUTCOME_RECORDED = "outcome_recorded"
    FAILURE_ANALYZED = "failure_analyzed"
    CAPABILITY_PROMOTED = "capability_promoted"
    SAFETY_VIOLATION = "safety_violation"


@dataclass
class AuditEntry:
    """Single audit log entry"""
    timestamp: datetime
    event_type: AuditEventType
    decision_id: Optional[str]
    component: str  # Which component generated this
    description: str
    data: Dict[str, Any]  # Structured event data
    hash_chain: str  # Hash linking to previous entry
    severity: str = "INFO"  # INFO, WARNING, ERROR, CRITICAL


class AuditLogger:
    """
    Immutable audit logging system for complete decision provenance.
    
    Features:
    - Tamper-evident log chain
    - Structured event data
    - Queryable by decision, component, or time
    - Export for compliance
    """
    
    def __init__(
        self,
        log_path: Optional[str] = None,
        enable_hash_chain: bool = True
    ):
        self.log_path = log_path or "audit_log.jsonl"
        self.enable_hash_chain = enable_hash_chain
        
        self.entries: List[AuditEntry] = []
        self.last_hash: str = "0" * 64
        
        # Decision index
        self.decision_entries: Dict[str, List[int]] = {}
        
        # Component index
        self.component_entries: Dict[str, List[int]] = {}
        
        # Load existing if file exists
        self._load_existing()
        
    def _load_existing(self) -> None:
        """Load existing audit log if present"""
        path = Path(self.log_path)
        if path.exists():
            try:
                with open(path, 'r') as f:
                    for line in f:
                        entry_dict = json.loads(line.strip())
                        entry = self._dict_to_entry(entry_dict)
                        self.entries.append(entry)
                        self._index_entry(entry, len(self.entries) - 1)
                        if self.enable_hash_chain:
                            self.last_hash = entry.hash_chain
            except Exception as e:
                logger.error(f"Error loading audit log: {e}")
                
    def _index_entry(self, entry: AuditEntry, index: int) -> None:
        """Index entry for fast lookup"""
        
        if entry.decision_id:
            if entry.decision_id not in self.decision_entries:
                self.decision_entries[entry.decision_id] = []
            self.decision_entries[entry.decision_id].append(index)
            
        if entry.component:
            if entry.component not in self.component_entries:
                self.component_entries[entry.component] = []
            self.component_entries[entry.component].append(index)
            
    def log(
        self,
        event_type: AuditEventType,
        component: str,
        description: str,
        decision_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        severity: str = "INFO"
    ) -> AuditEntry:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            component: Component that generated this
            description: Human-readable description
            decision_id: Associated decision if any
            data: Structured event data
            severity: Event severity
            
        Returns:
            Created AuditEntry
        """
        # Calculate hash chain
        if self.enable_hash_chain:
            hash_content = f"{self.last_hash}:{datetime.utcnow().isoformat()}:{component}:{description}"
            current_hash = hashlib.sha256(hash_content.encode()).hexdigest()
        else:
            current_hash = ""
            
        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            decision_id=decision_id,
            component=component,
            description=description,
            data=data or {},
            hash_chain=current_hash,
            severity=severity
        )
        
        self.entries.append(entry)
        self._index_entry(entry, len(self.entries) - 1)
        
        if self.enable_hash_chain:
            self.last_hash = current_hash
            
        # Persist immediately for durability
        self._persist_entry(entry)
        
        return entry
    
    def _persist_entry(self, entry: AuditEntry) -> None:
        """Persist entry to disk"""
        try:
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(self._entry_to_dict(entry), default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to persist audit entry: {e}")
            
    def _entry_to_dict(self, entry: AuditEntry) -> Dict:
        """Convert entry to dictionary"""
        return {
            'timestamp': entry.timestamp.isoformat(),
            'event_type': entry.event_type.value,
            'decision_id': entry.decision_id,
            'component': entry.component,
            'description': entry.description,
            'data': entry.data,
            'hash_chain': entry.hash_chain,
            'severity': entry.severity
        }
        
    def _dict_to_entry(self, d: Dict) -> AuditEntry:
        """Convert dictionary to entry"""
        return AuditEntry(
            timestamp=datetime.fromisoformat(d['timestamp']),
            event_type=AuditEventType(d['event_type']),
            decision_id=d.get('decision_id'),
            component=d['component'],
            description=d['description'],
            data=d.get('data', {}),
            hash_chain=d.get('hash_chain', ''),
            severity=d.get('severity', 'INFO')
        )
        
    def get_decision_audit_trail(
        self,
        decision_id: str
    ) -> List[AuditEntry]:
        """
        Get complete audit trail for a decision.
        
        Returns:
            List of audit entries in chronological order
        """
        indices = self.decision_entries.get(decision_id, [])
        return [self.entries[i] for i in sorted(indices)]
        
    def get_component_logs(
        self,
        component: str,
        since: Optional[datetime] = None
    ) -> List[AuditEntry]:
        """Get all logs from a component"""
        
        indices = self.component_entries.get(component, [])
        entries = [self.entries[i] for i in indices]
        
        if since:
            entries = [e for e in entries if e.timestamp >= since]
            
        return entries
        
    def get_safety_violations(
        self,
        since: Optional[datetime] = None
    ) -> List[AuditEntry]:
        """Get all safety violations"""
        
        violations = [
            e for e in self.entries
            if e.event_type == AuditEventType.SAFETY_VIOLATION
        ]
        
        if since:
            violations = [e for e in violations if e.timestamp >= since]
            
        return violations
        
    def verify_integrity(self) -> Tuple[bool, List[str]]:
        """
        Verify audit log integrity (hash chain validation).
        
        Returns:
            Tuple of (is_valid, list of violations)
        """
        if not self.enable_hash_chain:
            return True, []
            
        violations = []
        
        for i in range(1, len(self.entries)):
            prev_entry = self.entries[i - 1]
            curr_entry = self.entries[i]
            
            # Verify hash chain
            expected_content = f"{prev_entry.hash_chain}:{curr_entry.timestamp.isoformat()}:{curr_entry.component}:{curr_entry.description}"
            expected_hash = hashlib.sha256(expected_content.encode()).hexdigest()
            
            if curr_entry.hash_chain != expected_hash:
                violations.append(
                    f"Hash chain violation at entry {i}: {curr_entry.hash_chain} != {expected_hash}"
                )
                
        return len(violations) == 0, violations
        
    def generate_decision_report(
        self,
        decision_id: str
    ) -> Dict[str, Any]:
        """Generate comprehensive audit report for a decision"""
        
        entries = self.get_decision_audit_trail(decision_id)
        
        if not entries:
            return {'error': 'No audit trail found for decision'}
            
        # Group by phase
        phases = {
            'input': [],
            'validation': [],
            'analysis': [],
            'decision': [],
            'execution': [],
            'outcome': []
        }
        
        phase_mapping = {
            AuditEventType.SIGNAL_RECEIVED: 'input',
            AuditEventType.SIGNAL_VALIDATED: 'validation',
            AuditEventType.CLAIM_CONSTRUCTED: 'analysis',
            AuditEventType.EVIDENCE_AUDITED: 'analysis',
            AuditEventType.ADVERSARIAL_CHALLENGE: 'analysis',
            AuditEventType.REGIME_EVALUATED: 'analysis',
            AuditEventType.COUNTERFACTUAL_RUN: 'analysis',
            AuditEventType.UNCERTAINTY_COMPUTED: 'analysis',
            AuditEventType.RISK_CHECKED: 'analysis',
            AuditEventType.EXECUTION_ASSESSED: 'analysis',
            AuditEventType.DECISION_RENDERED: 'decision',
            AuditEventType.TRADE_EXECUTED: 'execution',
            AuditEventType.OUTCOME_RECORDED: 'outcome'
        }
        
        for entry in entries:
            phase = phase_mapping.get(entry.event_type, 'other')
            phases[phase].append({
                'timestamp': entry.timestamp.isoformat(),
                'component': entry.component,
                'event': entry.event_type.value,
                'description': entry.description,
                'data': entry.data
            })
            
        return {
            'decision_id': decision_id,
            'total_events': len(entries),
            'start_time': entries[0].timestamp.isoformat() if entries else None,
            'end_time': entries[-1].timestamp.isoformat() if entries else None,
            'phases': phases,
            'safety_violations': sum(
                1 for e in entries if e.event_type == AuditEventType.SAFETY_VIOLATION
            )
        }
        
    def export_for_compliance(
        self,
        start_date: datetime,
        end_date: datetime,
        output_path: str
    ) -> Dict[str, Any]:
        """Export audit log for regulatory compliance"""
        
        entries = [
            e for e in self.entries
            if start_date <= e.timestamp <= end_date
        ]
        
        # Verify integrity first
        is_valid, violations = self.verify_integrity()
        
        export_data = {
            'export_metadata': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_entries': len(entries),
                'integrity_verified': is_valid,
                'integrity_violations': violations,
                'generated_at': datetime.utcnow().isoformat()
            },
            'entries': [self._entry_to_dict(e) for e in entries]
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
            
        return {
            'success': True,
            'entries_exported': len(entries),
            'output_path': output_path,
            'integrity_status': 'VERIFIED' if is_valid else 'VIOLATIONS_DETECTED'
        }
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit log statistics"""
        
        return {
            'total_entries': len(self.entries),
            'unique_decisions': len(self.decision_entries),
            'unique_components': len(self.component_entries),
            'entries_by_type': {
                et.value: sum(1 for e in self.entries if e.event_type == et)
                for et in AuditEventType
            },
            'safety_violations': sum(
                1 for e in self.entries
                if e.event_type == AuditEventType.SAFETY_VIOLATION
            ),
            'integrity_verified': self.verify_integrity()[0]
        }
