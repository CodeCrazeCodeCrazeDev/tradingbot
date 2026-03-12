"""
Code Rewriter
Applies approved proposals by actually modifying the code files.
Creates backups and supports rollback.
"""

import os
import shutil
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import hashlib

from .proposal_engine import Proposal, ProposalStatus, CodeChange, ChangeType

logger = logging.getLogger(__name__)


@dataclass
class FileBackup:
    """Record of a file backup."""
    file_path: str
    backup_path: str
    original_hash: str
    backed_up_at: datetime
    proposal_id: str
    
    def to_dict(self) -> Dict:
        return {
            'file_path': self.file_path,
            'backup_path': self.backup_path,
            'original_hash': self.original_hash,
            'backed_up_at': self.backed_up_at.isoformat(),
            'proposal_id': self.proposal_id
        }


@dataclass
class ApplyResult:
    """Result of applying a proposal."""
    proposal_id: str
    success: bool
    changes_applied: int
    changes_failed: int
    error_message: Optional[str] = None
    backup_created: bool = False
    files_modified: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'proposal_id': self.proposal_id,
            'success': self.success,
            'changes_applied': self.changes_applied,
            'changes_failed': self.changes_failed,
            'error_message': self.error_message,
            'backup_created': self.backup_created,
            'files_modified': self.files_modified
        }


class CodeRewriter:
    """
    Applies approved proposals by modifying actual code files.
    
    Features:
    - Creates backups before any changes
    - Validates changes before applying
    - Supports rollback
    - Maintains audit trail
    """
    
    def __init__(self, base_path: str, backup_path: str = None):
        """
        Initialize code rewriter.
        
        Args:
            base_path: Root path of the trading bot codebase
            backup_path: Path to store backups (default: base_path/backups)
        """
        self.base_path = Path(base_path)
        self.backup_path = Path(backup_path) if backup_path else self.base_path / "code_backups"
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        self.backups: Dict[str, FileBackup] = {}
        self.apply_history: List[ApplyResult] = []
        
        # Load existing backups
        self._load_backup_index()
        
        logger.info(f"CodeRewriter initialized. Backups at {self.backup_path}")
    
    def _load_backup_index(self) -> None:
        """Load backup index."""
        index_file = self.backup_path / "backup_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data.get('backups', {}))} backup records")
            except Exception as e:
                logger.warning(f"Could not load backup index: {e}")
    
    def _save_backup_index(self) -> None:
        """Save backup index."""
        index_file = self.backup_path / "backup_index.json"
        data = {
            'updated_at': datetime.now().isoformat(),
            'backups': {k: v.to_dict() for k, v in self.backups.items()}
        }
        with open(index_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _compute_hash(self, content: str) -> str:
        """Compute hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _create_backup(self, file_path: str, proposal_id: str) -> Optional[FileBackup]:
        """Create backup of a file before modification."""
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return None
        try:
        
            # Read original content
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{file_path.replace('/', '_').replace(os.sep, '_')}_{timestamp}.bak"
            backup_full_path = self.backup_path / backup_name
            
            # Write backup
            with open(backup_full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Create backup record
            backup = FileBackup(
                file_path=file_path,
                backup_path=str(backup_full_path),
                original_hash=self._compute_hash(content),
                backed_up_at=datetime.now(),
                proposal_id=proposal_id
            )
            
            self.backups[file_path] = backup
            self._save_backup_index()
            
            logger.info(f"Created backup: {backup_name}")
            return backup
            
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return None
    
    def _read_file(self, file_path: str) -> Optional[List[str]]:
        """Read file and return lines."""
        full_path = self.base_path / file_path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.readlines()
        except Exception as e:
            logger.error(f"Could not read {file_path}: {e}")
            return None
    
    def _write_file(self, file_path: str, lines: List[str]) -> bool:
        """Write lines to file."""
        full_path = self.base_path / file_path
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True
        except Exception as e:
            logger.error(f"Could not write {file_path}: {e}")
            return False
    
    def _apply_change(self, change: CodeChange) -> Tuple[bool, str]:
        """
        Apply a single code change.
        
        Returns:
            Tuple of (success, error_message)
        """
        lines = self._read_file(change.file_path)
        if lines is None:
            return False, f"Could not read file: {change.file_path}"
        try:
        
            if change.change_type == ChangeType.REPLACE_CODE:
                # Replace lines
                start_idx = change.line_start - 1
                end_idx = change.line_end
                
                if start_idx < 0 or end_idx > len(lines):
                    return False, f"Line range out of bounds: {change.line_start}-{change.line_end}"
                
                # Get indentation from original line
                original_line = lines[start_idx] if start_idx < len(lines) else ""
                indent = len(original_line) - len(original_line.lstrip())
                indent_str = ' ' * indent
                
                # Apply new code with proper indentation
                new_lines = []
                for new_line in change.new_code.split('\n'):
                    if new_line.strip():
                        new_lines.append(indent_str + new_line.strip() + '\n')
                    else:
                        new_lines.append('\n')
                
                # Replace the lines
                lines = lines[:start_idx] + new_lines + lines[end_idx:]
                
            elif change.change_type == ChangeType.ADD_CODE:
                # Insert new lines
                insert_idx = change.line_start - 1
                
                if insert_idx < 0:
                    insert_idx = 0
                if insert_idx > len(lines):
                    insert_idx = len(lines)
                
                new_lines = [line + '\n' for line in change.new_code.split('\n')]
                lines = lines[:insert_idx] + new_lines + lines[insert_idx:]
                
            elif change.change_type == ChangeType.REMOVE_CODE:
                # Remove lines
                start_idx = change.line_start - 1
                end_idx = change.line_end
                
                if start_idx < 0 or end_idx > len(lines):
                    return False, f"Line range out of bounds"
                
                lines = lines[:start_idx] + lines[end_idx:]
            
            else:
                return False, f"Unsupported change type: {change.change_type}"
            
            # Write the modified file
            if self._write_file(change.file_path, lines):
                return True, ""
            else:
                return False, "Failed to write file"
                
        except Exception as e:
            return False, str(e)
    
    def apply_proposal(self, proposal: Proposal, dry_run: bool = False) -> ApplyResult:
        """
        Apply a proposal's changes to the codebase.
        
        Args:
            proposal: The proposal to apply
            dry_run: If True, only validate without making changes
            
        Returns:
            ApplyResult with details of what was done
        """
        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Applying proposal {proposal.proposal_id}")
        
        if proposal.status != ProposalStatus.APPROVED:
            return ApplyResult(
                proposal_id=proposal.proposal_id,
                success=False,
                changes_applied=0,
                changes_failed=0,
                error_message=f"Proposal is not approved (status: {proposal.status})"
            )
        
        if not proposal.changes:
            return ApplyResult(
                proposal_id=proposal.proposal_id,
                success=True,
                changes_applied=0,
                changes_failed=0,
                error_message="No automatic changes to apply"
            )
        
        # Group changes by file
        files_to_modify = set(c.file_path for c in proposal.changes)
        
        # Create backups first (unless dry run)
        if not dry_run:
            for file_path in files_to_modify:
                backup = self._create_backup(file_path, proposal.proposal_id)
                if not backup:
                    return ApplyResult(
                        proposal_id=proposal.proposal_id,
                        success=False,
                        changes_applied=0,
                        changes_failed=0,
                        error_message=f"Failed to create backup for {file_path}",
                        backup_created=False
                    )
        
        # Apply changes
        changes_applied = 0
        changes_failed = 0
        errors = []
        
        for change in proposal.changes:
            if dry_run:
                # Just validate
                lines = self._read_file(change.file_path)
                if lines is None:
                    changes_failed += 1
                    errors.append(f"Cannot read {change.file_path}")
                else:
                    changes_applied += 1
            else:
                success, error = self._apply_change(change)
                if success:
                    changes_applied += 1
                    logger.info(f"  ✓ Applied change to {change.file_path}:{change.line_start}")
                else:
                    changes_failed += 1
                    errors.append(f"{change.file_path}: {error}")
                    logger.error(f"  ✗ Failed: {error}")
        
        # Update proposal status
        if not dry_run:
            if changes_failed == 0:
                proposal.status = ProposalStatus.APPLIED
            else:
                proposal.status = ProposalStatus.FAILED
        
        result = ApplyResult(
            proposal_id=proposal.proposal_id,
            success=changes_failed == 0,
            changes_applied=changes_applied,
            changes_failed=changes_failed,
            error_message='; '.join(errors) if errors else None,
            backup_created=not dry_run,
            files_modified=list(files_to_modify)
        )
        
        self.apply_history.append(result)
        
        if result.success:
            logger.info(f"✓ Proposal {proposal.proposal_id} applied successfully ({changes_applied} changes)")
        else:
            logger.error(f"✗ Proposal {proposal.proposal_id} failed ({changes_failed} failures)")
        
        return result
    
    def apply_all_approved(self, proposals: List[Proposal], dry_run: bool = False) -> List[ApplyResult]:
        """
        Apply all approved proposals.
        
        Args:
            proposals: List of proposals
            dry_run: If True, only validate
            
        Returns:
            List of ApplyResults
        """
        approved = [p for p in proposals if p.status == ProposalStatus.APPROVED]
        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Applying {len(approved)} approved proposals")
        
        results = []
        for proposal in approved:
            result = self.apply_proposal(proposal, dry_run)
            results.append(result)
        
        # Summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        logger.info(f"Application complete: {successful} successful, {failed} failed")
        return results
    
    def rollback_proposal(self, proposal_id: str) -> bool:
        """
        Rollback changes from a proposal.
        
        Args:
            proposal_id: ID of proposal to rollback
            
        Returns:
            True if rollback successful
        """
        logger.info(f"Rolling back proposal {proposal_id}")
        
        # Find backups for this proposal
        backups_to_restore = [
            b for b in self.backups.values() 
            if b.proposal_id == proposal_id
        ]
        
        if not backups_to_restore:
            logger.warning(f"No backups found for proposal {proposal_id}")
            return False
        
        success = True
        for backup in backups_to_restore:
            try:
                # Read backup content
                with open(backup.backup_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Restore to original location
                full_path = self.base_path / backup.file_path
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"  ✓ Restored {backup.file_path}")
                
            except Exception as e:
                logger.error(f"  ✗ Failed to restore {backup.file_path}: {e}")
                success = False
        
        if success:
            logger.info(f"✓ Rollback of {proposal_id} complete")
        else:
            logger.error(f"✗ Rollback of {proposal_id} had errors")
        
        return success
    
    def get_apply_history(self) -> List[ApplyResult]:
        """Get history of applied proposals."""
        return self.apply_history
    
    def save_history(self, output_path: str) -> None:
        """Save application history."""
        data = {
            'saved_at': datetime.now().isoformat(),
            'history': [r.to_dict() for r in self.apply_history]
        }
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"History saved to {output_path}")
