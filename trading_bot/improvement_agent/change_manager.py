"""
Change Manager
==============

Manages the lifecycle of proposed changes from creation to application.
Tracks all changes, maintains history, and handles approval workflow.

Capabilities:
- Track change requests
- Manage approval workflow
- Apply approved changes
- Rollback failed changes
- Maintain change history
"""

import os
import json
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Callable, Tuple
from enum import Enum
from datetime import datetime
import logging
import hashlib

from .improvement_proposer import Improvement, ImprovementProposal, FileDiff

logger = logging.getLogger(__name__)


class ChangeStatus(Enum):
    """Status of a change request."""
    PENDING = "pending"           # Awaiting review
    APPROVED = "approved"         # Approved, ready to apply
    REJECTED = "rejected"         # Rejected by reviewer
    APPLIED = "applied"           # Successfully applied
    FAILED = "failed"             # Application failed
    ROLLED_BACK = "rolled_back"   # Changes were rolled back


class ChangeType(Enum):
    """Type of change."""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"


@dataclass
class FileBackup:
    """Backup of a file before modification."""
    file_path: str
    original_content: str
    backup_path: str
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ChangeRequest:
    """A request to change the codebase."""
    id: str
    improvement_id: str
    change_type: ChangeType
    file_path: str
    description: str
    
    # The change
    diff: Optional[FileDiff] = None
    
    # Status
    status: ChangeStatus = ChangeStatus.PENDING
    
    # Review
    reviewed_by: str = ""
    review_notes: str = ""
    reviewed_at: Optional[datetime] = None
    
    # Application
    applied_at: Optional[datetime] = None
    backup: Optional[FileBackup] = None
    error_message: str = ""
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "improvement_id": self.improvement_id,
            "change_type": self.change_type.value,
            "file_path": self.file_path,
            "status": self.status.value,
            "description": self.description,
            "reviewed_by": self.reviewed_by,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ChangeHistory:
    """History of all changes."""
    changes: List[ChangeRequest] = field(default_factory=list)
    
    # Statistics
    total_applied: int = 0
    total_rejected: int = 0
    total_rolled_back: int = 0
    
    def add(self, change: ChangeRequest):
        self.changes.append(change)
    
    def get_pending(self) -> List[ChangeRequest]:
        return [c for c in self.changes if c.status == ChangeStatus.PENDING]
    
    def get_approved(self) -> List[ChangeRequest]:
        return [c for c in self.changes if c.status == ChangeStatus.APPROVED]
    
    def get_by_improvement(self, improvement_id: str) -> List[ChangeRequest]:
        return [c for c in self.changes if c.improvement_id == improvement_id]
    
    def to_dict(self) -> Dict:
        return {
            "total_changes": len(self.changes),
            "total_applied": self.total_applied,
            "total_rejected": self.total_rejected,
            "total_rolled_back": self.total_rolled_back,
            "pending": len(self.get_pending()),
            "approved": len(self.get_approved()),
        }


class ChangeManager:
    """
    Manages the complete lifecycle of code changes.
    
    This is the "hands" of the improvement agent - it applies
    approved changes to the codebase safely.
    """
    
    # Protected paths that require extra confirmation
    PROTECTED_PATHS = [
        "core/risk",
        "core/execution",
        "core/security",
        "trading/",
        "broker/",
        ".env",
        "credentials",
        "secrets",
    ]
    
    def __init__(self, root_path: str, backup_dir: str = None):
        self.root_path = Path(root_path)
        self.backup_dir = Path(backup_dir) if backup_dir else self.root_path / ".improvement_backups"
        self.history = ChangeHistory()
        self._change_counter = 0
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_change_requests(self, proposal: ImprovementProposal) -> List[ChangeRequest]:
        """Create change requests from a proposal."""
        requests = []
        
        for improvement in proposal.improvements:
            for diff in improvement.diffs:
                change_type = ChangeType.CREATE if diff.is_new_file else ChangeType.MODIFY
                
                request = ChangeRequest(
                    id=self._generate_change_id(),
                    improvement_id=improvement.id,
                    change_type=change_type,
                    file_path=diff.file_path,
                    description=diff.changes_description,
                    diff=diff,
                )
                
                requests.append(request)
                self.history.add(request)
        
        logger.info(f"Created {len(requests)} change requests from proposal {proposal.id}")
        return requests
    
    def _generate_change_id(self) -> str:
        """Generate unique change ID."""
        self._change_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"CHG_{timestamp}_{self._change_counter:04d}"
    
    def is_protected_path(self, file_path: str) -> bool:
        """Check if a path is protected."""
        for protected in self.PROTECTED_PATHS:
            if protected in file_path.lower():
                return True
        return False
    
    def approve_change(self, change_id: str, reviewer: str, notes: str = "") -> bool:
        """Approve a change request."""
        change = self._find_change(change_id)
        if not change:
            logger.error(f"Change not found: {change_id}")
            return False
        
        if change.status != ChangeStatus.PENDING:
            logger.warning(f"Change {change_id} is not pending (status: {change.status})")
            return False
        
        change.status = ChangeStatus.APPROVED
        change.reviewed_by = reviewer
        change.review_notes = notes
        change.reviewed_at = datetime.now()
        
        logger.info(f"Change {change_id} approved by {reviewer}")
        return True
    
    def reject_change(self, change_id: str, reviewer: str, reason: str) -> bool:
        """Reject a change request."""
        change = self._find_change(change_id)
        if not change:
            logger.error(f"Change not found: {change_id}")
            return False
        
        change.status = ChangeStatus.REJECTED
        change.reviewed_by = reviewer
        change.review_notes = reason
        change.reviewed_at = datetime.now()
        
        self.history.total_rejected += 1
        
        logger.info(f"Change {change_id} rejected by {reviewer}: {reason}")
        return True
    
    def approve_all_for_improvement(self, improvement_id: str, reviewer: str) -> int:
        """Approve all changes for an improvement."""
        changes = self.history.get_by_improvement(improvement_id)
        approved = 0
        
        for change in changes:
            if change.status == ChangeStatus.PENDING:
                if self.approve_change(change.id, reviewer):
                    approved += 1
        
        return approved
    
    def apply_change(self, change_id: str) -> Tuple[bool, str]:
        """Apply an approved change to the codebase."""
        change = self._find_change(change_id)
        if not change:
            return False, f"Change not found: {change_id}"
        
        if change.status != ChangeStatus.APPROVED:
            return False, f"Change {change_id} is not approved (status: {change.status})"
        try:
        
            # Create backup
            backup = self._create_backup(change)
            change.backup = backup
            
            # Apply the change
            if change.change_type == ChangeType.CREATE:
                self._apply_create(change)
            elif change.change_type == ChangeType.MODIFY:
                self._apply_modify(change)
            elif change.change_type == ChangeType.DELETE:
                self._apply_delete(change)
            
            change.status = ChangeStatus.APPLIED
            change.applied_at = datetime.now()
            self.history.total_applied += 1
            
            logger.info(f"Change {change_id} applied successfully")
            return True, "Change applied successfully"
            
        except Exception as e:
            change.status = ChangeStatus.FAILED
            change.error_message = str(e)
            logger.error(f"Failed to apply change {change_id}: {e}")
            return False, str(e)
    
    def apply_all_approved(self) -> Tuple[int, int, List[str]]:
        """Apply all approved changes."""
        approved = self.history.get_approved()
        applied = 0
        failed = 0
        errors = []
        
        for change in approved:
            success, message = self.apply_change(change.id)
            if success:
                applied += 1
            else:
                failed += 1
                errors.append(f"{change.id}: {message}")
        
        return applied, failed, errors
    
    def rollback_change(self, change_id: str) -> Tuple[bool, str]:
        """Rollback an applied change."""
        change = self._find_change(change_id)
        if not change:
            return False, f"Change not found: {change_id}"
        
        if change.status != ChangeStatus.APPLIED:
            return False, f"Change {change_id} is not applied (status: {change.status})"
        
        if not change.backup:
            return False, f"No backup available for change {change_id}"
        try:
        
            file_path = self.root_path / change.file_path
            
            if change.change_type == ChangeType.CREATE:
                # Delete the created file
                if file_path.exists():
                    file_path.unlink()
            else:
                # Restore from backup
                file_path.write_text(change.backup.original_content, encoding='utf-8')
            
            change.status = ChangeStatus.ROLLED_BACK
            self.history.total_rolled_back += 1
            
            logger.info(f"Change {change_id} rolled back successfully")
            return True, "Change rolled back successfully"
            
        except Exception as e:
            logger.error(f"Failed to rollback change {change_id}: {e}")
            return False, str(e)
    
    def _find_change(self, change_id: str) -> Optional[ChangeRequest]:
        """Find a change by ID."""
        for change in self.history.changes:
            if change.id == change_id:
                return change
        return None
    
    def _create_backup(self, change: ChangeRequest) -> Optional[FileBackup]:
        """Create a backup of a file before modification."""
        file_path = self.root_path / change.file_path
        
        if not file_path.exists():
            return None
        try:
        
            original_content = file_path.read_text(encoding='utf-8')
            
            # Create backup file
            backup_name = f"{change.id}_{file_path.name}"
            backup_path = self.backup_dir / backup_name
            backup_path.write_text(original_content, encoding='utf-8')
            
            return FileBackup(
                file_path=str(file_path),
                original_content=original_content,
                backup_path=str(backup_path),
            )
        except Exception as e:
            logger.warning(f"Failed to create backup for {file_path}: {e}")
            return None
    
    def _apply_create(self, change: ChangeRequest):
        """Apply a file creation change."""
        file_path = self.root_path / change.file_path
        
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write new file
        file_path.write_text(change.diff.new_content, encoding='utf-8')
        
        logger.debug(f"Created file: {file_path}")
    
    def _apply_modify(self, change: ChangeRequest):
        """Apply a file modification change."""
        file_path = self.root_path / change.file_path
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Write modified content
        file_path.write_text(change.diff.new_content, encoding='utf-8')
        
        logger.debug(f"Modified file: {file_path}")
    
    def _apply_delete(self, change: ChangeRequest):
        """Apply a file deletion change."""
        file_path = self.root_path / change.file_path
        
        if file_path.exists():
            file_path.unlink()
            logger.debug(f"Deleted file: {file_path}")
    
    def get_pending_review(self) -> List[Dict]:
        """Get all changes pending review."""
        pending = self.history.get_pending()
        return [
            {
                "id": c.id,
                "file": c.file_path,
                "type": c.change_type.value,
                "description": c.description,
                "protected": self.is_protected_path(c.file_path),
                "diff_preview": c.diff.get_unified_diff()[:500] if c.diff else "",
            }
            for c in pending
        ]
    
    def get_status_summary(self) -> Dict:
        """Get a summary of change status."""
        return {
            "total": len(self.history.changes),
            "pending": len(self.history.get_pending()),
            "approved": len(self.history.get_approved()),
            "applied": self.history.total_applied,
            "rejected": self.history.total_rejected,
            "rolled_back": self.history.total_rolled_back,
        }
    
    def save_history(self, file_path: str = None):
        """Save change history to file."""
        if not file_path:
            file_path = self.backup_dir / "change_history.json"
        
        data = {
            "saved_at": datetime.now().isoformat(),
            "summary": self.history.to_dict(),
            "changes": [c.to_dict() for c in self.history.changes],
        }
        
        Path(file_path).write_text(json.dumps(data, indent=2), encoding='utf-8')
        logger.info(f"Saved change history to {file_path}")
    
    def load_history(self, file_path: str = None):
        """Load change history from file."""
        if not file_path:
            file_path = self.backup_dir / "change_history.json"
        
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"History file not found: {file_path}")
            return
        
        data = json.loads(path.read_text(encoding='utf-8'))
        
        # Restore statistics
        summary = data.get("summary", {})
        self.history.total_applied = summary.get("total_applied", 0)
        self.history.total_rejected = summary.get("total_rejected", 0)
        self.history.total_rolled_back = summary.get("total_rolled_back", 0)
        
        logger.info(f"Loaded change history from {file_path}")


# End of module
