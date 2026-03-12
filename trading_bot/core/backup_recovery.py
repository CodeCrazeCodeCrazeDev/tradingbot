"""
Backup and Recovery System
Provides state persistence and recovery for the trading bot.
"""

import asyncio
import json
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import hashlib
import gzip

logger = logging.getLogger(__name__)


@dataclass
class BackupMetadata:
    """Metadata for a backup."""
    backup_id: str
    timestamp: str
    version: str
    components: List[str]
    size_bytes: int
    checksum: str
    compressed: bool


@dataclass
class RecoveryPoint:
    """A point-in-time recovery snapshot."""
    timestamp: datetime
    positions: List[Dict]
    pending_orders: List[Dict]
    account_state: Dict
    config: Dict
    metrics: Dict


class BackupManager:
    """
    Manages backup and recovery of trading bot state.
    
    Features:
    - Automatic periodic backups
    - State persistence
    - Point-in-time recovery
    - Backup rotation
    - Compression
    """
    
    def __init__(
        self,
        backup_dir: str = "backups",
        max_backups: int = 100,
        backup_interval_seconds: int = 300,  # 5 minutes
        compress: bool = True
    ):
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.backup_interval = backup_interval_seconds
        self.compress = compress
        
        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # State
        self._running = False
        self._last_backup: Optional[datetime] = None
        self._backup_history: List[BackupMetadata] = []
        
        # Components to backup
        self._components: Dict[str, Any] = {}
        
        logger.info(f"BackupManager initialized: dir={backup_dir}, interval={backup_interval_seconds}s")
    
    def register_component(self, name: str, component: Any):
        """Register a component for backup."""
        self._components[name] = component
        logger.debug(f"Registered component for backup: {name}")
    
    async def start(self):
        """Start automatic backup loop."""
        self._running = True
        logger.info("Starting automatic backup loop")
        
        while self._running:
            try:
                await self.create_backup()
                await asyncio.sleep(self.backup_interval)
            except Exception as e:
                logger.error(f"Error in backup loop: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    async def stop(self):
        """Stop backup loop and create final backup."""
        self._running = False
        await self.create_backup("shutdown")
        logger.info("Backup loop stopped")
    
    async def create_backup(self, reason: str = "scheduled") -> Optional[BackupMetadata]:
        """
        Create a backup of current state.
        
        Args:
            reason: Reason for backup (scheduled, shutdown, manual, etc.)
            
        Returns:
            BackupMetadata if successful
        """
        try:
            timestamp = datetime.now()
            backup_id = f"backup_{timestamp.strftime('%Y%m%d_%H%M%S')}_{reason}"
            
            # Collect state from all components
            state = {
                'backup_id': backup_id,
                'timestamp': timestamp.isoformat(),
                'reason': reason,
                'version': '2.0.0',
                'components': {}
            }
            
            component_names = []
            
            for name, component in self._components.items():
                try:
                    component_state = await self._get_component_state(name, component)
                    if component_state:
                        state['components'][name] = component_state
                        component_names.append(name)
                except Exception as e:
                    logger.error(f"Error backing up component {name}: {e}")
            
            # Serialize state
            state_json = json.dumps(state, default=str, indent=2)
            
            # Calculate checksum
            checksum = hashlib.sha256(state_json.encode()).hexdigest()[:16]
            
            # Write backup file
            if self.compress:
                backup_file = self.backup_dir / f"{backup_id}.json.gz"
                with gzip.open(backup_file, 'wt', encoding='utf-8') as f:
                    f.write(state_json)
            else:
                backup_file = self.backup_dir / f"{backup_id}.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(state_json)
            
            # Create metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                timestamp=timestamp.isoformat(),
                version='2.0.0',
                components=component_names,
                size_bytes=backup_file.stat().st_size,
                checksum=checksum,
                compressed=self.compress
            )
            
            self._backup_history.append(metadata)
            self._last_backup = timestamp
            
            # Rotate old backups
            await self._rotate_backups()
            
            logger.info(f"Backup created: {backup_id} ({len(component_names)} components, "
                       f"{metadata.size_bytes} bytes)")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    async def _get_component_state(self, name: str, component: Any) -> Optional[Dict]:
        """Get state from a component."""
        # Try various methods to get state
        if hasattr(component, 'get_state'):
            state = component.get_state()
            if asyncio.iscoroutine(state):
                state = await state
            return state
        
        if hasattr(component, 'to_dict'):
            return component.to_dict()
        
        if hasattr(component, '__dict__'):
            # Filter out non-serializable attributes
            state = {}
            for key, value in component.__dict__.items():
                if not key.startswith('_') and self._is_serializable(value):
                    state[key] = value
            return state
        
        return None
    
    def _is_serializable(self, value: Any) -> bool:
        """Check if a value is JSON serializable."""
        try:
            json.dumps(value, default=str)
            return True
        except (TypeError, ValueError):
            return False
    
    async def _rotate_backups(self):
        """Remove old backups to stay within limit."""
        backup_files = sorted(self.backup_dir.glob("backup_*.json*"))
        
        while len(backup_files) > self.max_backups:
            oldest = backup_files.pop(0)
            try:
                oldest.unlink()
                logger.debug(f"Rotated old backup: {oldest.name}")
            except Exception as e:
                logger.error(f"Error removing old backup: {e}")
    
    async def restore(self, backup_id: Optional[str] = None) -> bool:
        """
        Restore state from a backup.
        
        Args:
            backup_id: Specific backup to restore, or None for latest
            
        Returns:
            True if successful
        """
        try:
            # Find backup file
            if backup_id:
                backup_file = self.backup_dir / f"{backup_id}.json"
                if not backup_file.exists():
                    backup_file = self.backup_dir / f"{backup_id}.json.gz"
            else:
                # Get latest backup
                backup_files = sorted(self.backup_dir.glob("backup_*.json*"), reverse=True)
                if not backup_files:
                    logger.error("No backups found")
                    return False
                backup_file = backup_files[0]
            
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False
            
            # Read backup
            if backup_file.suffix == '.gz':
                with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                    state = json.load(f)
            else:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
            
            # Restore components
            restored_count = 0
            for name, component_state in state.get('components', {}).items():
                if name in self._components:
                    try:
                        await self._restore_component(name, self._components[name], component_state)
                        restored_count += 1
                    except Exception as e:
                        logger.error(f"Error restoring component {name}: {e}")
            
            logger.info(f"Restored from backup: {backup_file.name} ({restored_count} components)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False
    
    async def _restore_component(self, name: str, component: Any, state: Dict):
        """Restore state to a component."""
        if hasattr(component, 'restore_state'):
            result = component.restore_state(state)
            if asyncio.iscoroutine(result):
                await result
        elif hasattr(component, 'from_dict'):
            component.from_dict(state)
        else:
            # Direct attribute assignment
            for key, value in state.items():
                if hasattr(component, key):
                    setattr(component, key, value)
    
    def list_backups(self) -> List[BackupMetadata]:
        """List all available backups."""
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("backup_*.json*"), reverse=True):
            try:
                # Parse metadata from filename
                name = backup_file.stem
                if name.endswith('.json'):
                    name = name[:-5]
                
                parts = name.split('_')
                if len(parts) >= 3:
                    backup_id = name
                    
                    backups.append(BackupMetadata(
                        backup_id=backup_id,
                        timestamp=f"{parts[1]}_{parts[2]}",
                        version='unknown',
                        components=[],
                        size_bytes=backup_file.stat().st_size,
                        checksum='',
                        compressed=backup_file.suffix == '.gz'
                    ))
            except Exception as e:
                logger.debug(f"Error parsing backup file {backup_file}: {e}")
        
        return backups
    
    def get_status(self) -> Dict:
        """Get backup manager status."""
        backups = self.list_backups()
        total_size = sum(b.size_bytes for b in backups)
        
        return {
            'running': self._running,
            'backup_count': len(backups),
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'last_backup': self._last_backup.isoformat() if self._last_backup else None,
            'backup_interval_seconds': self.backup_interval,
            'max_backups': self.max_backups,
            'registered_components': list(self._components.keys())
        }


class StateManager:
    """
    Manages persistent state for quick recovery.
    Saves state to disk on every change.
    """
    
    def __init__(self, state_file: str = "state/trading_state.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._state: Dict[str, Any] = {}
        self._dirty = False
        self._lock = asyncio.Lock()
        
        # Load existing state
        self._load_state()
        
        logger.info(f"StateManager initialized: {state_file}")
    
    def _load_state(self):
        """Load state from disk."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    self._state = json.load(f)
                logger.info(f"Loaded state: {len(self._state)} keys")
            except Exception as e:
                logger.error(f"Error loading state: {e}")
                self._state = {}
    
    async def save(self):
        """Save state to disk."""
        async with self._lock:
            if not self._dirty:
                return
            try:
            
                # Write to temp file first
                temp_file = self.state_file.with_suffix('.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(self._state, f, default=str, indent=2)
                
                # Atomic rename
                temp_file.replace(self.state_file)
                self._dirty = False
                
            except Exception as e:
                logger.error(f"Error saving state: {e}")
    
    async def set(self, key: str, value: Any):
        """Set a state value."""
        async with self._lock:
            self._state[key] = value
            self._dirty = True
        await self.save()
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        return self._state.get(key, default)
    
    async def delete(self, key: str):
        """Delete a state value."""
        async with self._lock:
            if key in self._state:
                del self._state[key]
                self._dirty = True
        await self.save()
    
    async def update(self, updates: Dict[str, Any]):
        """Update multiple state values."""
        async with self._lock:
            self._state.update(updates)
            self._dirty = True
        await self.save()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all state."""
        return self._state.copy()


# Singleton instances
_backup_manager: Optional[BackupManager] = None
_state_manager: Optional[StateManager] = None


def get_backup_manager(**kwargs) -> BackupManager:
    """Get or create the backup manager singleton."""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager(**kwargs)
    return _backup_manager


def get_state_manager(state_file: str = "state/trading_state.json") -> StateManager:
    """Get or create the state manager singleton."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager(state_file)
    return _state_manager


__all__ = [
    'BackupManager',
    'BackupMetadata',
    'RecoveryPoint',
    'StateManager',
    'get_backup_manager',
    'get_state_manager'
]
