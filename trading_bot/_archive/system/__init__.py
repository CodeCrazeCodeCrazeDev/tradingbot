"""
system package
"""

try:
    from .backup_recovery import (
        BackupManager,
        BackupMetadata,
        BackupRecoverySystem,
        BackupType,
        EmergencyProtocol,
        FailoverTarget,
        ManualOverride,
        RecoveryManager,
        RecoveryMode,
        RecoveryPoint,
        SystemState,
        create_backup,
        restore_backup,
        retry
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in system: {e}')

__all__ = [
    'BackupManager',
    'BackupMetadata',
    'BackupRecoverySystem',
    'BackupType',
    'EmergencyProtocol',
    'FailoverTarget',
    'ManualOverride',
    'RecoveryManager',
    'RecoveryMode',
    'RecoveryPoint',
    'SystemState',
    'create_backup',
    'restore_backup',
    'retry',
]