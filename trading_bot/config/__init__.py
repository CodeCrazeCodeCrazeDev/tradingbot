"""
Config Module
============================================================

Auto-generated integration file.
"""

# centralized_config
try:
    from .centralized_config import (
        ConfigManager,
    )
except ImportError as e:
    # centralized_config not available
    pass

# config_manager
try:
    from .config_manager import (
        ConfigManager,
    )
except ImportError as e:
    # config_manager not available
    pass

# feature_flags
try:
    from .feature_flags import (
        DynamicConfigManager,
        FeatureFlagManager,
    )
except ImportError as e:
    # feature_flags not available
    pass

# legacy config API
try:
    from .config import (
        Config,
        DEFAULT_CONFIG,
        get,
        get_config,
        load_config,
    )
except ImportError as e:
    # config not available
    pass

__all__ = [
    'ConfigManager',
    'DynamicConfigManager',
    'FeatureFlagManager',
    'Config',
    'DEFAULT_CONFIG',
    'get',
    'get_config',
    'load_config',
]
