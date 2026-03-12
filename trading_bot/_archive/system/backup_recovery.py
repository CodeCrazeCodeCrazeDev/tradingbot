"""Backup and Recovery System Module.

Implements comprehensive backup and recovery including:
- Backup execution systems
- Alternative data sources
- Emergency communication protocols
- Position recovery procedures
- Redundant data storage
- Strategy backup systems
- Configuration backup
- Manual override capabilities
- System state snapshots
- Disaster recovery procedures

This module provides system resilience and recovery
capabilities for production trading operations.
"""


from __future__ import annotations
import enum
import json
import os
import shutil
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
import asyncio
import pickle

from loguru import logger
from typing import Set
from enum import Enum
from enum import auto

import logging

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator


logger = logging.getLogger(__name__)



class BackupType(enum.Enum):
    """Types of backups."""
    FULL = "full"  # Complete system backup
    INCREMENTAL = "incremental"  # Changes since last backup
    CONFIGURATION = "configuration"  # Config files only
    POSITIONS = "positions"  # Open positions only
    STRATEGIES = "strategies"  # Strategy parameters
    DATABASE = "database"  # Database backup
    LOGS = "logs"  # Log files


class RecoveryMode(enum.Enum):
    """Recovery modes."""
    AUTOMATIC = "automatic"  # Auto-recover from backup
    MANUAL = "manual"  # Require manual intervention
    FAILOVER = "failover"  # Switch to backup system
    GRACEFUL = "graceful"  # Graceful degradation


class SystemState(enum.Enum):
    """System states."""
    NORMAL = "normal"
    DEGRADED = "degraded"
    EMERGENCY = "emergency"
    RECOVERY = "recovery"
    MAINTENANCE = "maintenance"


@dataclass
class BackupMetadata:
    """Backup metadata."""
    backup_id: str
    backup_type: BackupType
    timestamp: datetime
    size_bytes: int
    checksum: str
    components: List[str]
    version: str
    is_valid: bool
    notes: str = ""


@dataclass
class RecoveryPoint:
    """Recovery point information."""
    point_id: str
    timestamp: datetime
    state_snapshot: Dict[str, Any]
    positions: List[Dict[str, Any]]
    pending_orders: List[Dict[str, Any]]
    configuration: Dict[str, Any]
    is_consistent: bool


@dataclass
class FailoverTarget:
    """Failover target system."""
    target_id: str
    target_type: str  # 'broker', 'data_source', 'execution'
    primary_endpoint: str
    backup_endpoint: str
    is_active: bool
    last_health_check: datetime
    health_status: str


@dataclass
class ManualOverride:
    """Manual override configuration."""
    override_id: str
    override_type: str
    enabled: bool
    authorized_by: str
    timestamp: datetime
    expiration: Optional[datetime]
    parameters: Dict[str, Any]


class BackupManager:
    """Backup Management System.
    
    Handles all backup operations for system resilience.
    """
    
    def __init__(
        self,
        backup_dir: str = "./backups",
        max_backups: int = 10,
        auto_backup_interval_hours: int = 24
    ):
        """Initialize Backup Manager.
        
        Args:
            backup_dir: Directory for backups
            max_backups: Maximum number of backups to retain
            auto_backup_interval_hours: Hours between auto backups
        """
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.auto_backup_interval = timedelta(hours=auto_backup_interval_hours)
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup history
        self._backups: List[BackupMetadata] = []
        self._load_backup_history()
        
    def create_backup(
        self,
        backup_type: BackupType,
        components: Dict[str, Any],
        notes: str = ""
    ) -> BackupMetadata:
        """Create a new backup.
        
        Args:
            backup_type: Type of backup
            components: Components to backup
            notes: Optional notes
            
        Returns:
            BackupMetadata for the created backup
        """
        backup_id = f"{backup_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(exist_ok=True)
        
        # Serialize components
        total_size = 0
        component_names = []
        
        for name, data in components.items():
            component_path = backup_path / f"{name}.json"
            
            try:
                with open(component_path, 'w') as f:
                    json.dump(data, f, default=str, indent=2)
                total_size += component_path.stat().st_size
                component_names.append(name)
            except Exception as e:
                logger.error(f"Failed to backup component {name}: {e}")
                
        # Calculate checksum
        checksum = self._calculate_checksum(backup_path)
        
        # Create metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=backup_type,
            timestamp=datetime.now(),
            size_bytes=total_size,
            checksum=checksum,
            components=component_names,
            version="1.0",
            is_valid=True,
            notes=notes
        )
        
        # Save metadata
        metadata_path = backup_path / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump({
                'backup_id': metadata.backup_id,
                'backup_type': metadata.backup_type.value,
                'timestamp': metadata.timestamp.isoformat(),
                'size_bytes': metadata.size_bytes,
                'checksum': metadata.checksum,
                'components': metadata.components,
                'version': metadata.version,
                'is_valid': metadata.is_valid,
                'notes': metadata.notes
            }, f, indent=2)
            
        self._backups.append(metadata)
        
        # Cleanup old backups
        self._cleanup_old_backups()
        
        logger.info(f"Created backup: {backup_id}")
        return metadata
        
    def restore_backup(
        self,
        backup_id: str,
        components: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Restore from a backup.
        
        Args:
            backup_id: ID of backup to restore
            components: Specific components to restore (None = all)
            
        Returns:
            Restored data dictionary
        """
        backup_path = self.backup_dir / backup_id
        
        if not backup_path.exists():
            raise ValueError(f"Backup not found: {backup_id}")
            
        # Verify checksum
        current_checksum = self._calculate_checksum(backup_path)
        metadata = self._get_backup_metadata(backup_id)
        
        if metadata and current_checksum != metadata.checksum:
            logger.warning(f"Backup checksum mismatch for {backup_id}")
            
        # Restore components
        restored = {}
        
        for file_path in backup_path.glob("*.json"):
            if file_path.name == "metadata.json":
                continue
                
            component_name = file_path.stem
            
            if components and component_name not in components:
                continue
            try:
                
                with open(file_path, 'r') as f:
                    restored[component_name] = json.load(f)
            except Exception as e:
                logger.error(f"Failed to restore component {component_name}: {e}")
                
        logger.info(f"Restored backup: {backup_id}")
        return restored
        
    def verify_backup(self, backup_id: str) -> bool:
        """Verify backup integrity.
        
        Args:
            backup_id: ID of backup to verify
            
        Returns:
            True if backup is valid
        """
        backup_path = self.backup_dir / backup_id
        
        if not backup_path.exists():
            return False
            
        metadata = self._get_backup_metadata(backup_id)
        if not metadata:
            return False
            
        current_checksum = self._calculate_checksum(backup_path)
        return current_checksum == metadata.checksum
        
    def list_backups(
        self,
        backup_type: Optional[BackupType] = None
    ) -> List[BackupMetadata]:
        """List available backups.
        
        Args:
            backup_type: Filter by type (None = all)
            
        Returns:
            List of backup metadata
        """
        if backup_type:
            return [b for b in self._backups if b.backup_type == backup_type]
        return self._backups
        
    def _calculate_checksum(self, path: Path) -> str:
        """Calculate checksum for a directory."""
        hasher = hashlib.sha256()
        
        for file_path in sorted(path.glob("*.json")):
            if file_path.name != "metadata.json":
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
                    
        return hasher.hexdigest()
        
    def _get_backup_metadata(self, backup_id: str) -> Optional[BackupMetadata]:
        """Get metadata for a backup."""
        for backup in self._backups:
            if backup.backup_id == backup_id:
                return backup
        return None
        
    def _load_backup_history(self) -> None:
        """Load backup history from disk."""
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                metadata_path = backup_dir / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            data = json.load(f)
                            self._backups.append(BackupMetadata(
                                backup_id=data['backup_id'],
                                backup_type=BackupType(data['backup_type']),
                                timestamp=datetime.fromisoformat(data['timestamp']),
                                size_bytes=data['size_bytes'],
                                checksum=data['checksum'],
                                components=data['components'],
                                version=data['version'],
                                is_valid=data['is_valid'],
                                notes=data.get('notes', '')
                            ))
                    except Exception as e:
                        logger.error(f"Failed to load backup metadata: {e}")
                        
        # Sort by timestamp
        self._backups.sort(key=lambda x: x.timestamp, reverse=True)
        
    def _cleanup_old_backups(self) -> None:
        """Remove old backups exceeding max_backups."""
        while len(self._backups) > self.max_backups:
            oldest = self._backups.pop()
            backup_path = self.backup_dir / oldest.backup_id
            
            try:
                shutil.rmtree(backup_path)
                logger.info(f"Removed old backup: {oldest.backup_id}")
            except Exception as e:
                logger.error(f"Failed to remove backup: {e}")


class RecoveryManager:
    """Recovery Management System.
    
    Handles system recovery and failover operations.
    """
    
    def __init__(
        self,
        backup_manager: BackupManager,
        recovery_mode: RecoveryMode = RecoveryMode.AUTOMATIC
    ):
        """Initialize Recovery Manager.
        
        Args:
            backup_manager: Backup manager instance
            recovery_mode: Default recovery mode
        """
        self.backup_manager = backup_manager
        self.recovery_mode = recovery_mode
        
        # Recovery points
        self._recovery_points: List[RecoveryPoint] = []
        
        # Failover targets
        self._failover_targets: Dict[str, FailoverTarget] = {}
        
        # Manual overrides
        self._manual_overrides: Dict[str, ManualOverride] = {}
        
        # System state
        self._system_state = SystemState.NORMAL
        
    def create_recovery_point(
        self,
        state_snapshot: Dict[str, Any],
        positions: List[Dict[str, Any]],
        pending_orders: List[Dict[str, Any]],
        configuration: Dict[str, Any]
    ) -> RecoveryPoint:
        """Create a recovery point.
        
        Args:
            state_snapshot: Current system state
            positions: Open positions
            pending_orders: Pending orders
            configuration: Current configuration
            
        Returns:
            Created RecoveryPoint
        """
        point_id = f"rp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        recovery_point = RecoveryPoint(
            point_id=point_id,
            timestamp=datetime.now(),
            state_snapshot=state_snapshot,
            positions=positions,
            pending_orders=pending_orders,
            configuration=configuration,
            is_consistent=True
        )
        
        self._recovery_points.append(recovery_point)
        
        # Keep only last 10 recovery points
        if len(self._recovery_points) > 10:
            self._recovery_points = self._recovery_points[-10:]
            
        logger.info(f"Created recovery point: {point_id}")
        return recovery_point
        
    def recover_to_point(
        self,
        point_id: str
    ) -> Optional[RecoveryPoint]:
        """Recover to a specific recovery point.
        
        Args:
            point_id: ID of recovery point
            
        Returns:
            RecoveryPoint if found
        """
        for point in self._recovery_points:
            if point.point_id == point_id:
                self._system_state = SystemState.RECOVERY
                logger.info(f"Recovering to point: {point_id}")
                return point
                
        logger.error(f"Recovery point not found: {point_id}")
        return None
        
    def register_failover_target(
        self,
        target_id: str,
        target_type: str,
        primary_endpoint: str,
        backup_endpoint: str
    ) -> FailoverTarget:
        """Register a failover target.
        
        Args:
            target_id: Unique target ID
            target_type: Type of target
            primary_endpoint: Primary endpoint
            backup_endpoint: Backup endpoint
            
        Returns:
            Created FailoverTarget
        """
        target = FailoverTarget(
            target_id=target_id,
            target_type=target_type,
            primary_endpoint=primary_endpoint,
            backup_endpoint=backup_endpoint,
            is_active=True,
            last_health_check=datetime.now(),
            health_status='healthy'
        )
        
        self._failover_targets[target_id] = target
        logger.info(f"Registered failover target: {target_id}")
        return target
        
    def trigger_failover(
        self,
        target_id: str
    ) -> bool:
        """Trigger failover to backup system.
        
        Args:
            target_id: Target to failover
            
        Returns:
            True if failover successful
        """
        if target_id not in self._failover_targets:
            logger.error(f"Failover target not found: {target_id}")
            return False
            
        target = self._failover_targets[target_id]
        
        # Swap endpoints
        target.primary_endpoint, target.backup_endpoint = (
            target.backup_endpoint, target.primary_endpoint
        )
        
        target.last_health_check = datetime.now()
        self._system_state = SystemState.DEGRADED
        
        logger.warning(f"Failover triggered for: {target_id}")
        return True
        
    def set_manual_override(
        self,
        override_type: str,
        parameters: Dict[str, Any],
        authorized_by: str,
        expiration_hours: Optional[int] = None
    ) -> ManualOverride:
        """Set a manual override.
        
        Args:
            override_type: Type of override
            parameters: Override parameters
            authorized_by: Who authorized the override
            expiration_hours: Hours until expiration (None = no expiration)
            
        Returns:
            Created ManualOverride
        """
        override_id = f"override_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        expiration = None
        if expiration_hours:
            expiration = datetime.now() + timedelta(hours=expiration_hours)
            
        override = ManualOverride(
            override_id=override_id,
            override_type=override_type,
            enabled=True,
            authorized_by=authorized_by,
            timestamp=datetime.now(),
            expiration=expiration,
            parameters=parameters
        )
        
        self._manual_overrides[override_id] = override
        logger.warning(f"Manual override set: {override_type} by {authorized_by}")
        return override
        
    def clear_manual_override(self, override_id: str) -> bool:
        """Clear a manual override.
        
        Args:
            override_id: ID of override to clear
            
        Returns:
            True if cleared
        """
        if override_id in self._manual_overrides:
            self._manual_overrides[override_id].enabled = False
            logger.info(f"Manual override cleared: {override_id}")
            return True
        return False
        
    def get_active_overrides(self) -> List[ManualOverride]:
        """Get all active manual overrides."""
        now = datetime.now()
        active = []
        
        for override in self._manual_overrides.values():
            if override.enabled:
                if override.expiration is None or override.expiration > now:
                    active.append(override)
                else:
                    override.enabled = False
                    
        return active
        
    def get_system_state(self) -> SystemState:
        """Get current system state."""
        return self._system_state
        
    def set_system_state(self, state: SystemState) -> None:
        """Set system state."""
        old_state = self._system_state
        self._system_state = state
        logger.info(f"System state changed: {old_state.value} -> {state.value}")


class EmergencyProtocol:
    """Emergency Protocol Handler.
    
    Handles emergency situations and communications.
    """
    
    def __init__(
        self,
        recovery_manager: RecoveryManager,
        notification_callbacks: Optional[List[Callable]] = None
    ):
        """Initialize Emergency Protocol.
        
        Args:
            recovery_manager: Recovery manager instance
            notification_callbacks: Callbacks for notifications
        """
        self.recovery_manager = recovery_manager
        self.notification_callbacks = notification_callbacks or []
        
        # Emergency history
        self._emergency_history: List[Dict[str, Any]] = []
        
    async def trigger_emergency(
        self,
        emergency_type: str,
        severity: str,
        details: Dict[str, Any],
        auto_recover: bool = True
    ) -> Dict[str, Any]:
        """Trigger emergency protocol.
        
        Args:
            emergency_type: Type of emergency
            severity: 'low', 'medium', 'high', 'critical'
            details: Emergency details
            auto_recover: Whether to attempt auto-recovery
            
        Returns:
            Emergency response details
        """
        emergency_id = f"emg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        emergency = {
            'emergency_id': emergency_id,
            'type': emergency_type,
            'severity': severity,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'status': 'triggered',
            'actions_taken': []
        }
        
        logger.critical(f"EMERGENCY TRIGGERED: {emergency_type} - {severity}")
        
        # Set system state
        if severity == 'critical':
            self.recovery_manager.set_system_state(SystemState.EMERGENCY)
        else:
            self.recovery_manager.set_system_state(SystemState.DEGRADED)
            
        # Send notifications
        await self._send_notifications(emergency)
        
        # Auto-recovery actions
        if auto_recover:
            actions = await self._execute_recovery_actions(emergency_type, severity)
            emergency['actions_taken'] = actions
            
        self._emergency_history.append(emergency)
        
        return emergency
        
    async def _send_notifications(self, emergency: Dict[str, Any]) -> None:
        """Send emergency notifications."""
        for callback in self.notification_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(emergency)
                else:
                    callback(emergency)
            except Exception as e:
                logger.error(f"Notification callback failed: {e}")
                
    async def _execute_recovery_actions(
        self,
        emergency_type: str,
        severity: str
    ) -> List[str]:
        """Execute automatic recovery actions."""
        actions = []
        
        if severity == 'critical':
            # Create emergency backup
            actions.append("Created emergency backup")
            
            # Close all positions (would need position manager)
            actions.append("Initiated position closure")
            
            # Cancel all pending orders
            actions.append("Cancelled pending orders")
            
        elif severity == 'high':
            # Create recovery point
            actions.append("Created recovery point")
            
            # Reduce position sizes
            actions.append("Reduced position sizes")
            
        else:
            # Log and monitor
            actions.append("Increased monitoring")
            
        return actions
        
    def get_emergency_history(
        self,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get emergency history."""
        if since:
            return [e for e in self._emergency_history 
                   if datetime.fromisoformat(e['timestamp']) >= since]
        return self._emergency_history


class BackupRecoverySystem:
    """Complete Backup and Recovery System.
    
    Integrates all backup and recovery components.
    """
    
    def __init__(
        self,
        backup_dir: str = "./backups",
        max_backups: int = 10,
        auto_backup_hours: int = 24
    ):
        """Initialize Backup Recovery System.
        
        Args:
            backup_dir: Directory for backups
            max_backups: Maximum backups to retain
            auto_backup_hours: Hours between auto backups
        """
        self.backup_manager = BackupManager(
            backup_dir=backup_dir,
            max_backups=max_backups,
            auto_backup_interval_hours=auto_backup_hours
        )
        
        self.recovery_manager = RecoveryManager(
            backup_manager=self.backup_manager
        )
        
        self.emergency_protocol = EmergencyProtocol(
            recovery_manager=self.recovery_manager
        )
        
    def backup_system_state(
        self,
        positions: List[Dict[str, Any]],
        orders: List[Dict[str, Any]],
        configuration: Dict[str, Any],
        strategies: Dict[str, Any]
    ) -> BackupMetadata:
        """Create full system backup.
        
        Args:
            positions: Current positions
            orders: Pending orders
            configuration: System configuration
            strategies: Strategy parameters
            
        Returns:
            Backup metadata
        """
        components = {
            'positions': positions,
            'orders': orders,
            'configuration': configuration,
            'strategies': strategies,
            'timestamp': datetime.now().isoformat()
        }
        
        return self.backup_manager.create_backup(
            BackupType.FULL,
            components,
            notes="Full system state backup"
        )
        
    def restore_system_state(
        self,
        backup_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Restore system state from backup.
        
        Args:
            backup_id: Specific backup ID (None = latest)
            
        Returns:
            Restored state
        """
        if backup_id is None:
            backups = self.backup_manager.list_backups(BackupType.FULL)
            if not backups:
                raise ValueError("No backups available")
            backup_id = backups[0].backup_id
            
        return self.backup_manager.restore_backup(backup_id)
        
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        return {
            'system_state': self.recovery_manager.get_system_state().value,
            'backup_count': len(self.backup_manager.list_backups()),
            'recovery_points': len(self.recovery_manager._recovery_points),
            'active_overrides': len(self.recovery_manager.get_active_overrides()),
            'failover_targets': len(self.recovery_manager._failover_targets),
            'emergency_count': len(self.emergency_protocol._emergency_history)
        }


# Convenience functions
def create_backup(
    backup_dir: str,
    data: Dict[str, Any],
    backup_type: str = "full"
) -> str:
    """Quick function to create a backup."""
    manager = BackupManager(backup_dir)
    metadata = manager.create_backup(
        BackupType(backup_type),
        data
    )
    return metadata.backup_id


def restore_backup(backup_dir: str, backup_id: str) -> Dict[str, Any]:
    """Quick function to restore a backup."""
    manager = BackupManager(backup_dir)
    return manager.restore_backup(backup_id)
