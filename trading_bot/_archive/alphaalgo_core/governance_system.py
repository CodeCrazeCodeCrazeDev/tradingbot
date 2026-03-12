"""
AlphaAlgo Governance System

Self-Improvement Rules:
1. Propose → Test → Human Approve → Deploy
2. Every change must be: reversible, logged, explainable
3. NO changes to risk modules without full explanation
4. NO changes to position sizing or order execution without approval
5. Improve slowly, safely, methodically — like a scientist, not a gambler
"""

import asyncio
import hashlib
import json
import logging
import os
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class GovernanceLevel(Enum):
    """Governance levels for actions"""
    HUMAN_REQUIRED = "human_required"      # G0 - Must have human approval
    CONTROLLER_ALLOWED = "controller"       # G1 - Controller can approve
    MINI_AI_ALLOWED = "mini_ai"            # G2 - Mini-AI can execute
    AUTOMATIC = "automatic"                 # Safe to auto-execute


class ChangeCategory(Enum):
    """Categories of changes"""
    RISK_MANAGEMENT = "risk"
    POSITION_SIZING = "position"
    ORDER_EXECUTION = "execution"
    STRATEGY_LOGIC = "strategy"
    DATA_PIPELINE = "data"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    MONITORING = "monitoring"
    DOCUMENTATION = "documentation"


@dataclass
class ProposedChange:
    """A proposed change to the system"""
    change_id: str
    category: ChangeCategory
    title: str
    description: str
    rationale: str
    expected_impact: str
    risk_assessment: str
    rollback_plan: str
    test_results: Optional[Dict[str, Any]] = None
    proposed_by: str = "AlphaAlgo"
    proposed_at: datetime = field(default_factory=datetime.now)
    status: str = "proposed"
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'change_id': self.change_id,
            'category': self.category.value,
            'title': self.title,
            'description': self.description,
            'rationale': self.rationale,
            'expected_impact': self.expected_impact,
            'risk_assessment': self.risk_assessment,
            'rollback_plan': self.rollback_plan,
            'test_results': self.test_results,
            'proposed_by': self.proposed_by,
            'proposed_at': self.proposed_at.isoformat(),
            'status': self.status,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None,
        }


class GovernanceSystem:
    """
    The AlphaAlgo Governance System
    
    Enforces the self-improvement rules:
    - Propose → Test → Human Approve → Deploy
    - All changes must be reversible, logged, explainable
    - Risk/position/execution changes require human approval
    """
    
    # Categories that ALWAYS require human approval
    HUMAN_REQUIRED_CATEGORIES = {
        ChangeCategory.RISK_MANAGEMENT,
        ChangeCategory.POSITION_SIZING,
        ChangeCategory.ORDER_EXECUTION,
        ChangeCategory.SECURITY,
    }
    
    def __init__(self, db_path: str = "alphaalgo_data/governance.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        self._proposed_changes: Dict[str, ProposedChange] = {}
        self._deployed_changes: List[str] = []
        self._rollback_stack: List[Tuple[str, Callable]] = []
        self._lock = threading.Lock()
        
        logger.info("[Governance] System initialized")
    
    def _init_database(self):
        """Initialize governance database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS proposed_changes (
                    change_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    expected_impact TEXT NOT NULL,
                    risk_assessment TEXT NOT NULL,
                    rollback_plan TEXT NOT NULL,
                    test_results TEXT,
                    proposed_by TEXT NOT NULL,
                    proposed_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    approved_by TEXT,
                    approved_at TEXT,
                    deployed_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS change_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    change_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT
                )
            """)
            conn.commit()
    
    def propose_change(
        self,
        category: ChangeCategory,
        title: str,
        description: str,
        rationale: str,
        expected_impact: str,
        risk_assessment: str,
        rollback_plan: str,
    ) -> ProposedChange:
        """
        Propose a change to the system.
        
        This is step 1 of: Propose → Test → Human Approve → Deploy
        """
        import uuid
        change_id = f"CHG-{uuid.uuid4().hex[:8].upper()}"
        
        change = ProposedChange(
            change_id=change_id,
            category=category,
            title=title,
            description=description,
            rationale=rationale,
            expected_impact=expected_impact,
            risk_assessment=risk_assessment,
            rollback_plan=rollback_plan,
        )
        
        with self._lock:
            self._proposed_changes[change_id] = change
            self._save_change(change)
            self._log_audit(change_id, "PROPOSED", "AlphaAlgo", description)
        
        logger.info(f"[Governance] Change proposed: {change_id} - {title}")
        return change
    
    def record_test_results(
        self,
        change_id: str,
        test_results: Dict[str, Any]
    ) -> bool:
        """
        Record test results for a proposed change.
        
        This is step 2 of: Propose → Test → Human Approve → Deploy
        """
        with self._lock:
            if change_id not in self._proposed_changes:
                logger.warning(f"[Governance] Change {change_id} not found")
                return False
            
            change = self._proposed_changes[change_id]
            change.test_results = test_results
            change.status = "tested"
            
            self._save_change(change)
            self._log_audit(change_id, "TESTED", "AlphaAlgo", json.dumps(test_results))
        
        logger.info(f"[Governance] Test results recorded for {change_id}")
        return True
    
    def approve_change(
        self,
        change_id: str,
        approved_by: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Human approves a change.
        
        This is step 3 of: Propose → Test → Human Approve → Deploy
        """
        with self._lock:
            if change_id not in self._proposed_changes:
                logger.warning(f"[Governance] Change {change_id} not found")
                return False
            
            change = self._proposed_changes[change_id]
            
            # Verify test results exist for critical changes
            if change.category in self.HUMAN_REQUIRED_CATEGORIES:
                if not change.test_results:
                    logger.warning(f"[Governance] Change {change_id} requires test results")
                    return False
            
            change.status = "approved"
            change.approved_by = approved_by
            change.approved_at = datetime.now()
            
            self._save_change(change)
            self._log_audit(change_id, "APPROVED", approved_by, notes or "")
        
        logger.info(f"[Governance] Change {change_id} APPROVED by {approved_by}")
        return True
    
    def reject_change(
        self,
        change_id: str,
        rejected_by: str,
        reason: str
    ) -> bool:
        """Human rejects a change"""
        with self._lock:
            if change_id not in self._proposed_changes:
                return False
            
            change = self._proposed_changes[change_id]
            change.status = "rejected"
            
            self._save_change(change)
            self._log_audit(change_id, "REJECTED", rejected_by, reason)
        
        logger.info(f"[Governance] Change {change_id} REJECTED: {reason}")
        return True
    
    def deploy_change(
        self,
        change_id: str,
        deploy_function: Callable,
        rollback_function: Callable
    ) -> Tuple[bool, str]:
        """
        Deploy an approved change.
        
        This is step 4 of: Propose → Test → Human Approve → Deploy
        """
        with self._lock:
            pass
        try:
            if change_id not in self._proposed_changes:
                return (False, "Change not found")
            
            change = self._proposed_changes[change_id]
            
            if change.status != "approved":
                return (False, f"Change not approved (status: {change.status})")
        
            # Execute deployment
            deploy_function()
            
            with self._lock:
                change.status = "deployed"
                change.deployed_at = datetime.now()
                self._deployed_changes.append(change_id)
                self._rollback_stack.append((change_id, rollback_function))
                
                self._save_change(change)
                self._log_audit(change_id, "DEPLOYED", "AlphaAlgo", "")
            
            logger.info(f"[Governance] Change {change_id} DEPLOYED successfully")
            return (True, "Deployed successfully")
            
        except Exception as e:
            logger.error(f"[Governance] Deployment failed for {change_id}: {e}")
            self._log_audit(change_id, "DEPLOY_FAILED", "AlphaAlgo", str(e))
            return (False, f"Deployment failed: {e}")
    
    def rollback_change(self, change_id: str) -> Tuple[bool, str]:
        """Rollback a deployed change"""
        with self._lock:
            pass
        try:
            # Find rollback function
            rollback_func = None
            for cid, func in self._rollback_stack:
                if cid == change_id:
                    rollback_func = func
                    break
            
            if not rollback_func:
                return (False, "No rollback function found")
        
            rollback_func()
            
            with self._lock:
                if change_id in self._proposed_changes:
                    self._proposed_changes[change_id].status = "rolled_back"
                    self._save_change(self._proposed_changes[change_id])
                
                self._rollback_stack = [(c, f) for c, f in self._rollback_stack if c != change_id]
                self._log_audit(change_id, "ROLLED_BACK", "AlphaAlgo", "")
            
            logger.info(f"[Governance] Change {change_id} ROLLED BACK")
            return (True, "Rolled back successfully")
            
        except Exception as e:
            logger.error(f"[Governance] Rollback failed for {change_id}: {e}")
            return (False, f"Rollback failed: {e}")
    
    def requires_human_approval(self, category: ChangeCategory) -> bool:
        """Check if a category requires human approval"""
        return category in self.HUMAN_REQUIRED_CATEGORIES
    
    def get_governance_level(self, category: ChangeCategory) -> GovernanceLevel:
        """Get the governance level for a category"""
        if category in self.HUMAN_REQUIRED_CATEGORIES:
            return GovernanceLevel.HUMAN_REQUIRED
        elif category in {ChangeCategory.STRATEGY_LOGIC, ChangeCategory.DATA_PIPELINE}:
            return GovernanceLevel.CONTROLLER_ALLOWED
        elif category in {ChangeCategory.MONITORING, ChangeCategory.DOCUMENTATION}:
            return GovernanceLevel.AUTOMATIC
        else:
            return GovernanceLevel.MINI_AI_ALLOWED
    
    def get_pending_changes(self) -> List[ProposedChange]:
        """Get all changes pending approval"""
        with self._lock:
            return [c for c in self._proposed_changes.values() 
                    if c.status in ('proposed', 'tested')]
    
    def get_change_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get change history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM proposed_changes
                ORDER BY proposed_at DESC
                LIMIT ?
            """, (limit,))
            
            columns = [d[0] for d in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def _save_change(self, change: ProposedChange):
        """Save change to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO proposed_changes
                (change_id, category, title, description, rationale,
                 expected_impact, risk_assessment, rollback_plan,
                 test_results, proposed_by, proposed_at, status,
                 approved_by, approved_at, deployed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                change.change_id,
                change.category.value,
                change.title,
                change.description,
                change.rationale,
                change.expected_impact,
                change.risk_assessment,
                change.rollback_plan,
                json.dumps(change.test_results) if change.test_results else None,
                change.proposed_by,
                change.proposed_at.isoformat(),
                change.status,
                change.approved_by,
                change.approved_at.isoformat() if change.approved_at else None,
                change.deployed_at.isoformat() if change.deployed_at else None,
            ))
            conn.commit()
    
    def _log_audit(self, change_id: str, action: str, actor: str, details: str):
        """Log audit trail"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO change_audit_log
                (change_id, action, actor, timestamp, details)
                VALUES (?, ?, ?, ?, ?)
            """, (change_id, action, actor, datetime.now().isoformat(), details))
            conn.commit()
    
    def generate_change_report(self) -> str:
        """Generate a human-readable change report"""
        pending = self.get_pending_changes()
        
        report = ["=" * 60]
        report.append("ALPHAALGO GOVERNANCE - PENDING CHANGES REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Total Pending: {len(pending)}")
        report.append("")
        
        for change in pending:
            report.append("-" * 40)
            report.append(f"ID: {change.change_id}")
            report.append(f"Category: {change.category.value}")
            report.append(f"Title: {change.title}")
            report.append(f"Status: {change.status}")
            report.append(f"Requires Human Approval: {self.requires_human_approval(change.category)}")
            report.append(f"Description: {change.description}")
            report.append(f"Rationale: {change.rationale}")
            report.append(f"Expected Impact: {change.expected_impact}")
            report.append(f"Risk Assessment: {change.risk_assessment}")
            report.append(f"Rollback Plan: {change.rollback_plan}")
            if change.test_results:
                report.append(f"Test Results: {json.dumps(change.test_results, indent=2)}")
            report.append("")
        
        report.append("=" * 60)
        return "\n".join(report)
