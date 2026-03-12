"""
tools package
"""

try:
    from .backup import (
        BACKUP_ITEMS,
        create_backup,
        main,
        restore_backup
    )
    from .encrypt_api_keys import (
        encrypt_value,
        generate_key,
        load_or_create_key,
        main
    )
    from .system_check import (
        OPTIONAL_PACKAGES,
        REQUIRED_CONFIG_FILES,
        REQUIRED_DIRECTORIES,
        REQUIRED_PACKAGES,
        check_config_files,
        check_directories,
        check_mt5,
        check_network,
        check_packages,
        check_python_version,
        check_system_resources,
        main
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in tools: {e}')

__all__ = [
    'BACKUP_ITEMS',
    'OPTIONAL_PACKAGES',
    'REQUIRED_CONFIG_FILES',
    'REQUIRED_DIRECTORIES',
    'REQUIRED_PACKAGES',
    'check_config_files',
    'check_directories',
    'check_mt5',
    'check_network',
    'check_packages',
    'check_python_version',
    'check_system_resources',
    'create_backup',
    'encrypt_value',
    'generate_key',
    'load_or_create_key',
    'main',
    'restore_backup',
]