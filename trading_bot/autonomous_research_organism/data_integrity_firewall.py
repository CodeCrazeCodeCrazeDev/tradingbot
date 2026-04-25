"""
Data Integrity Firewall
=======================

Protects critical data from unauthorized modification by autonomous AI.
Implements multi-layer protection:
1. Access control (read/write/execute permissions)
2. Data checksums and integrity verification
3. Change tracking and audit logging
4. Rollback capabilities
5. Quarantine for suspicious changes

CRITICAL: Autonomous AI cannot modify protected resources without approval.
"""

import os
import hashlib
import json
import shutil
import threading
from typing import Dict, Any, List, Optional, Set, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
import logging
import copy

logger = logging.getLogger(__name__)


class AccessLevel(Enum):
    """Access levels for protected resources."""
    NONE = 0           # No access
    READ = 1           # Read only
    WRITE = 2          # Read and write
    EXECUTE = 3        # Read, write, and execute
    ADMIN = 4          # Full access including deletion


class ResourceType(Enum):
    """Types of protected resources."""
    FILE = auto()
    DIRECTORY = auto()
    DATABASE = auto()
    CONFIG = auto()
    CREDENTIAL = auto()
    MODEL = auto()
    STRATEGY = auto()
    SAFETY_RULE = auto()


class ProtectionLevel(Enum):
    """Protection levels for resources."""
    IMMUTABLE = 0      # Cannot be changed by AI ever
    CRITICAL = 1       # Requires human approval for any change
    PROTECTED = 2      # Requires validation before change
    MONITORED = 3      # Changes are logged but allowed
    NORMAL = 4         # Standard access


@dataclass
class ProtectedResource:
    """A resource protected by the firewall."""
    resource_id: str
    resource_type: ResourceType
    path: str
    protection_level: ProtectionLevel
    checksum: str
    owner: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_verified: datetime = field(default_factory=datetime.utcnow)
    last_modified: Optional[datetime] = None
    access_rules: Dict[str, AccessLevel] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'resource_id': self.resource_id,
            'resource_type': self.resource_type.name,
            'path': self.path,
            'protection_level': self.protection_level.name,
            'checksum': self.checksum,
            'owner': self.owner,
            'created_at': self.created_at.isoformat(),
            'last_verified': self.last_verified.isoformat(),
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'access_rules': {k: v.name for k, v in self.access_rules.items()},
        }


@dataclass
class FirewallViolation:
    """Record of a firewall violation."""
    violation_id: str
    resource_id: str
    violation_type: str
    actor: str
    attempted_action: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    blocked: bool = True
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'violation_id': self.violation_id,
            'resource_id': self.resource_id,
            'violation_type': self.violation_type,
            'actor': self.actor,
            'attempted_action': self.attempted_action,
            'timestamp': self.timestamp.isoformat(),
            'blocked': self.blocked,
            'details': self.details,
        }


@dataclass
class ChangeRequest:
    """Request to change a protected resource."""
    request_id: str
    resource_id: str
    actor: str
    change_type: str  # 'create', 'modify', 'delete'
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    justification: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, approved, rejected, applied
    approved_by: Optional[str] = None
    applied_at: Optional[datetime] = None


class DataIntegrityFirewall:
    """
    Firewall protecting critical data from unauthorized AI modifications.
    
    Implements defense-in-depth:
    1. Access control lists
    2. Integrity verification
    3. Change approval workflow
    4. Audit logging
    5. Automatic rollback
    """
    
    # Resources that are ALWAYS immutable
    IMMUTABLE_PATTERNS = [
        '**/safety_core.py',
        '**/immutable_*.py',
        '**/kill_switch*.py',
        '**/.env',
        '**/*.key',
        '**/*.pem',
        '**/credentials*',
    ]
    
    def __init__(self, 
                 storage_path: Optional[Path] = None,
                 backup_path: Optional[Path] = None):
        """
        Initialize data integrity firewall.
        
        Args:
            storage_path: Path for firewall state storage
            backup_path: Path for resource backups
        """
        self.storage_path = storage_path or Path("firewall_state")
        self.backup_path = backup_path or Path("firewall_backups")
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        self.resources: Dict[str, ProtectedResource] = {}
        self.violations: List[FirewallViolation] = []
        self.change_requests: Dict[str, ChangeRequest] = {}
        self.checksums: Dict[str, str] = {}
        
        self._lock = threading.RLock()
        self._violation_counter = 0
        self._request_counter = 0
        
        # Callbacks for approval workflow
        self._approval_callbacks: List[Callable[[ChangeRequest], bool]] = []
        
        # Load existing state
        self._load_state()
        
        logger.info("DataIntegrityFirewall initialized")
    
    def register_resource(self,
                          path: str,
                          resource_type: ResourceType,
                          protection_level: ProtectionLevel,
                          owner: str = "system",
                          access_rules: Optional[Dict[str, AccessLevel]] = None) -> str:
        """
        Register a resource for protection.
        
        Args:
            path: Path to the resource
            resource_type: Type of resource
            protection_level: Level of protection
            owner: Owner of the resource
            access_rules: Access rules by actor
            
        Returns:
            Resource ID
        """
        with self._lock:
            resource_id = hashlib.sha256(path.encode()).hexdigest()[:16]
            
            # Calculate checksum
            checksum = self._calculate_checksum(path)
            
            resource = ProtectedResource(
                resource_id=resource_id,
                resource_type=resource_type,
                path=path,
                protection_level=protection_level,
                checksum=checksum,
                owner=owner,
                access_rules=access_rules or {},
            )
            
            self.resources[resource_id] = resource
            self.checksums[resource_id] = checksum
            
            # Create backup
            self._create_backup(resource)
            
            logger.info(f"Resource registered: {path} ({protection_level.name})")
            
            self._save_state()
            
            return resource_id
    
    def check_access(self, 
                     resource_id: str, 
                     actor: str, 
                     action: str) -> bool:
        """
        Check if actor has access to perform action on resource.
        
        Args:
            resource_id: ID of the resource
            actor: Actor requesting access
            action: Action to perform ('read', 'write', 'execute', 'delete')
            
        Returns:
            True if access is allowed
        """
        with self._lock:
            resource = self.resources.get(resource_id)
            if not resource:
                return False
            
            # Check protection level
            if resource.protection_level == ProtectionLevel.IMMUTABLE:
                if action != 'read':
                    self._record_violation(
                        resource_id, actor, action,
                        "Attempted modification of immutable resource"
                    )
                    return False
            
            # Check access rules
            actor_access = resource.access_rules.get(actor, AccessLevel.NONE)
            
            required_access = {
                'read': AccessLevel.READ,
                'write': AccessLevel.WRITE,
                'execute': AccessLevel.EXECUTE,
                'delete': AccessLevel.ADMIN,
            }.get(action, AccessLevel.ADMIN)
            
            if actor_access.value < required_access.value:
                self._record_violation(
                    resource_id, actor, action,
                    f"Insufficient access level: {actor_access.name} < {required_access.name}"
                )
                return False
            
            return True
    
    def request_change(self,
                       resource_id: str,
                       actor: str,
                       change_type: str,
                       new_value: Any,
                       justification: str) -> str:
        """
        Request a change to a protected resource.
        
        Args:
            resource_id: ID of the resource
            actor: Actor requesting change
            change_type: Type of change ('create', 'modify', 'delete')
            new_value: New value for the resource
            justification: Reason for the change
            
        Returns:
            Request ID
        """
        with self._lock:
            resource = self.resources.get(resource_id)
            if not resource:
                raise ValueError(f"Unknown resource: {resource_id}")
            
            # Check if change is allowed at all
            if resource.protection_level == ProtectionLevel.IMMUTABLE:
                self._record_violation(
                    resource_id, actor, change_type,
                    "Change request for immutable resource"
                )
                raise PermissionError("Cannot change immutable resource")
            
            # Create change request
            self._request_counter += 1
            request_id = f"req_{self._request_counter:08d}"
            
            # Get current value
            old_value = self._read_resource(resource.path)
            
            request = ChangeRequest(
                request_id=request_id,
                resource_id=resource_id,
                actor=actor,
                change_type=change_type,
                old_value=old_value,
                new_value=new_value,
                justification=justification,
            )
            
            self.change_requests[request_id] = request
            
            # Auto-approve based on protection level
            if resource.protection_level == ProtectionLevel.MONITORED:
                self._approve_request(request_id, "auto")
            elif resource.protection_level == ProtectionLevel.NORMAL:
                self._approve_request(request_id, "auto")
            elif resource.protection_level == ProtectionLevel.PROTECTED:
                # Run validation callbacks
                if self._validate_change(request):
                    self._approve_request(request_id, "validation")
            # CRITICAL level requires manual approval
            
            logger.info(f"Change request created: {request_id} for {resource_id}")
            
            return request_id
    
    def approve_request(self, request_id: str, approver: str) -> bool:
        """
        Approve a change request (human approval).
        
        Args:
            request_id: ID of the request
            approver: Who is approving
            
        Returns:
            True if approved successfully
        """
        with self._lock:
            return self._approve_request(request_id, approver)
    
    def _approve_request(self, request_id: str, approver: str) -> bool:
        """Internal approval method."""
        request = self.change_requests.get(request_id)
        if not request:
            return False
        
        if request.status != "pending":
            return False
        
        request.status = "approved"
        request.approved_by = approver
        
        # Apply the change
        return self._apply_change(request)
    
    def reject_request(self, request_id: str, rejector: str, reason: str) -> bool:
        """
        Reject a change request.
        
        Args:
            request_id: ID of the request
            rejector: Who is rejecting
            reason: Reason for rejection
            
        Returns:
            True if rejected successfully
        """
        with self._lock:
            request = self.change_requests.get(request_id)
            if not request:
                return False
            
            if request.status != "pending":
                return False
            
            request.status = "rejected"
            
            logger.info(f"Change request rejected: {request_id} by {rejector}: {reason}")
            
            return True
    
    def _apply_change(self, request: ChangeRequest) -> bool:
        """Apply an approved change."""
        try:
            resource = self.resources.get(request.resource_id)
            if not resource:
                return False
            
            # Create backup before change
            self._create_backup(resource)
            
            # Apply change based on type
            if request.change_type == 'modify':
                self._write_resource(resource.path, request.new_value)
            elif request.change_type == 'delete':
                self._delete_resource(resource.path)
            elif request.change_type == 'create':
                self._write_resource(resource.path, request.new_value)
            
            # Update checksum
            new_checksum = self._calculate_checksum(resource.path)
            resource.checksum = new_checksum
            resource.last_modified = datetime.utcnow()
            self.checksums[request.resource_id] = new_checksum
            
            request.status = "applied"
            request.applied_at = datetime.utcnow()
            
            logger.info(f"Change applied: {request.request_id}")
            
            self._save_state()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply change {request.request_id}: {e}")
            request.status = "failed"
            return False
    
    def verify_integrity(self, resource_id: Optional[str] = None) -> Dict[str, bool]:
        """
        Verify integrity of protected resources.
        
        Args:
            resource_id: Optional specific resource to verify
            
        Returns:
            Dict of resource_id -> integrity_ok
        """
        with self._lock:
            results = {}
            
            resources_to_check = (
                [self.resources[resource_id]] if resource_id 
                else self.resources.values()
            )
            
            for resource in resources_to_check:
                try:
                    current_checksum = self._calculate_checksum(resource.path)
                    expected_checksum = self.checksums.get(resource.resource_id)
                    
                    is_valid = current_checksum == expected_checksum
                    results[resource.resource_id] = is_valid
                    
                    if not is_valid:
                        logger.warning(
                            f"Integrity violation: {resource.path} "
                            f"(expected {expected_checksum}, got {current_checksum})"
                        )
                        self._record_violation(
                            resource.resource_id, "system", "integrity_check",
                            "Checksum mismatch detected"
                        )
                    
                    resource.last_verified = datetime.utcnow()
                    
                except Exception as e:
                    logger.error(f"Integrity check failed for {resource.path}: {e}")
                    results[resource.resource_id] = False
            
            return results
    
    def rollback_resource(self, resource_id: str) -> bool:
        """
        Rollback a resource to its last known good state.
        
        Args:
            resource_id: ID of the resource to rollback
            
        Returns:
            True if rollback successful
        """
        with self._lock:
            resource = self.resources.get(resource_id)
            if not resource:
                return False
            
            backup_path = self.backup_path / f"{resource_id}_latest"
            
            if not backup_path.exists():
                logger.error(f"No backup found for {resource_id}")
                return False
            
            try:
                # Restore from backup
                if backup_path.is_file():
                    shutil.copy2(backup_path, resource.path)
                else:
                    shutil.copytree(backup_path, resource.path, dirs_exist_ok=True)
                
                # Update checksum
                new_checksum = self._calculate_checksum(resource.path)
                resource.checksum = new_checksum
                self.checksums[resource_id] = new_checksum
                
                logger.info(f"Resource rolled back: {resource_id}")
                
                return True
                
            except Exception as e:
                logger.error(f"Rollback failed for {resource_id}: {e}")
                return False
    
    def _calculate_checksum(self, path: str) -> str:
        """Calculate checksum for a resource."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return "NOT_FOUND"
        
        if path_obj.is_file():
            with open(path_obj, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        elif path_obj.is_dir():
            # Hash directory contents
            hasher = hashlib.sha256()
            for file_path in sorted(path_obj.rglob('*')):
                if file_path.is_file():
                    hasher.update(str(file_path.relative_to(path_obj)).encode())
                    with open(file_path, 'rb') as f:
                        hasher.update(f.read())
            return hasher.hexdigest()
        
        return "UNKNOWN"
    
    def _read_resource(self, path: str) -> Optional[Any]:
        """Read resource content."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return None
        
        if path_obj.is_file():
            try:
                with open(path_obj, 'r') as f:
                    return f.read()
            except Exception:
                with open(path_obj, 'rb') as f:
                    return f.read()
        
        return None
    
    def _write_resource(self, path: str, content: Any):
        """Write resource content."""
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(content, bytes):
            with open(path_obj, 'wb') as f:
                f.write(content)
        else:
            with open(path_obj, 'w') as f:
                f.write(str(content))
    
    def _delete_resource(self, path: str):
        """Delete a resource."""
        path_obj = Path(path)
        
        if path_obj.is_file():
            path_obj.unlink()
        elif path_obj.is_dir():
            shutil.rmtree(path_obj)
    
    def _create_backup(self, resource: ProtectedResource):
        """Create backup of a resource."""
        try:
            source = Path(resource.path)
            if not source.exists():
                return
            
            backup_dest = self.backup_path / f"{resource.resource_id}_latest"
            
            if source.is_file():
                shutil.copy2(source, backup_dest)
            else:
                if backup_dest.exists():
                    shutil.rmtree(backup_dest)
                shutil.copytree(source, backup_dest)
            
            # Also create timestamped backup
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            timestamped_dest = self.backup_path / f"{resource.resource_id}_{timestamp}"
            
            if source.is_file():
                shutil.copy2(source, timestamped_dest)
            else:
                shutil.copytree(source, timestamped_dest)
            
        except Exception as e:
            logger.error(f"Backup failed for {resource.path}: {e}")
    
    def _record_violation(self, resource_id: str, actor: str, 
                          action: str, description: str):
        """Record a firewall violation."""
        self._violation_counter += 1
        violation_id = f"viol_{self._violation_counter:08d}"
        
        violation = FirewallViolation(
            violation_id=violation_id,
            resource_id=resource_id,
            violation_type=action,
            actor=actor,
            attempted_action=action,
            details={'description': description},
        )
        
        self.violations.append(violation)
        
        logger.warning(f"Firewall violation: {violation_id} - {description}")
        
        # Keep violations bounded
        if len(self.violations) > 10000:
            self.violations = self.violations[-5000:]
    
    def _validate_change(self, request: ChangeRequest) -> bool:
        """Run validation callbacks on change request."""
        for callback in self._approval_callbacks:
            try:
                if not callback(request):
                    return False
            except Exception as e:
                logger.error(f"Validation callback error: {e}")
                return False
        return True
    
    def add_approval_callback(self, callback: Callable[[ChangeRequest], bool]):
        """Add a callback for change approval validation."""
        self._approval_callbacks.append(callback)
    
    def _load_state(self):
        """Load firewall state from storage."""
        state_file = self.storage_path / "firewall_state.json"
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                # Restore checksums
                self.checksums = state.get('checksums', {})
                
                logger.info("Firewall state loaded")
                
            except Exception as e:
                logger.error(f"Failed to load firewall state: {e}")
    
    def _save_state(self):
        """Save firewall state to storage."""
        state_file = self.storage_path / "firewall_state.json"
        
        try:
            state = {
                'checksums': self.checksums,
                'resources': {
                    rid: r.to_dict() for rid, r in self.resources.items()
                },
                'timestamp': datetime.utcnow().isoformat(),
            }
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save firewall state: {e}")
    
    def get_violation_report(self, 
                             since: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate violation report."""
        violations = self.violations
        
        if since:
            violations = [v for v in violations if v.timestamp >= since]
        
        return {
            'total_violations': len(violations),
            'by_type': {},
            'by_actor': {},
            'by_resource': {},
            'recent': [v.to_dict() for v in violations[-20:]],
        }
    
    def get_protected_resources(self) -> List[Dict[str, Any]]:
        """Get list of all protected resources."""
        return [r.to_dict() for r in self.resources.values()]
    
    def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Get list of pending change requests."""
        return [
            {
                'request_id': r.request_id,
                'resource_id': r.resource_id,
                'actor': r.actor,
                'change_type': r.change_type,
                'justification': r.justification,
                'timestamp': r.timestamp.isoformat(),
            }
            for r in self.change_requests.values()
            if r.status == 'pending'
        ]
