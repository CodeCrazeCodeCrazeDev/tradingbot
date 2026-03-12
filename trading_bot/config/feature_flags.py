"""
Feature Flags and Dynamic Runtime Configuration

Production-ready configuration management:
- Feature flags with rollout percentages
- Dynamic runtime configuration
- A/B testing support
- Configuration versioning
- Hot reload without restart
"""

import asyncio
import logging
import json
import hashlib
import os
from typing import Any, Callable, Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import threading

logger = logging.getLogger(__name__)

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class FeatureState(Enum):
    """Feature flag states"""
    DISABLED = "disabled"
    ENABLED = "enabled"
    ROLLOUT = "rollout"  # Percentage-based rollout
    AB_TEST = "ab_test"  # A/B testing


@dataclass
class FeatureFlag:
    """Feature flag definition"""
    name: str
    state: FeatureState
    description: str = ""
    rollout_percentage: float = 0.0  # 0-100
    ab_test_variant: Optional[str] = None
    allowed_users: Set[str] = field(default_factory=set)
    blocked_users: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'state': self.state.value,
            'description': self.description,
            'rollout_percentage': self.rollout_percentage,
            'ab_test_variant': self.ab_test_variant,
            'allowed_users': list(self.allowed_users),
            'blocked_users': list(self.blocked_users),
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FeatureFlag':
        return cls(
            name=data['name'],
            state=FeatureState(data.get('state', 'disabled')),
            description=data.get('description', ''),
            rollout_percentage=data.get('rollout_percentage', 0.0),
            ab_test_variant=data.get('ab_test_variant'),
            allowed_users=set(data.get('allowed_users', [])),
            blocked_users=set(data.get('blocked_users', [])),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now()
        )


@dataclass
class ConfigValue:
    """Configuration value with metadata"""
    key: str
    value: Any
    value_type: str  # string, int, float, bool, json
    description: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    secret: bool = False
    version: int = 1
    updated_at: datetime = field(default_factory=datetime.now)
    updated_by: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'key': self.key,
            'value': self.value if not self.secret else '***',
            'value_type': self.value_type,
            'description': self.description,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'allowed_values': self.allowed_values,
            'secret': self.secret,
            'version': self.version,
            'updated_at': self.updated_at.isoformat()
        }


class FeatureFlagManager:
    """
    Feature flag management system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Feature flags storage
        self.flags: Dict[str, FeatureFlag] = {}
        
        # Persistence
        self.storage_path = self.config.get('storage_path', 'config/feature_flags.json')
        
        # Callbacks
        self.on_flag_change: Optional[Callable] = None
        
        # Load existing flags
        self._load_flags()
        
        logger.info("FeatureFlagManager initialized")
    
    def _load_flags(self):
        """Load flags from storage"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for flag_data in data.get('flags', []):
                        flag = FeatureFlag.from_dict(flag_data)
                        self.flags[flag.name] = flag
                logger.info(f"Loaded {len(self.flags)} feature flags")
        except Exception as e:
            logger.error(f"Failed to load feature flags: {e}")
    
    def _save_flags(self):
        """Save flags to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'flags': [flag.to_dict() for flag in self.flags.values()],
                    'updated_at': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save feature flags: {e}")
    
    def create_flag(
        self,
        name: str,
        state: FeatureState = FeatureState.DISABLED,
        description: str = "",
        rollout_percentage: float = 0.0,
        **kwargs
    ) -> FeatureFlag:
        """Create a new feature flag"""
        flag = FeatureFlag(
            name=name,
            state=state,
            description=description,
            rollout_percentage=rollout_percentage,
            **kwargs
        )
        
        self.flags[name] = flag
        self._save_flags()
        
        logger.info(f"Feature flag created: {name}")
        return flag
    
    def update_flag(self, name: str, **updates) -> Optional[FeatureFlag]:
        """Update a feature flag"""
        flag = self.flags.get(name)
        if not flag:
            return None
        
        for key, value in updates.items():
            if hasattr(flag, key):
                setattr(flag, key, value)
        
        flag.updated_at = datetime.now()
        self._save_flags()
        
        if self.on_flag_change:
            try:
                self.on_flag_change(flag)
            except Exception as e:
                logger.error(f"Flag change callback error: {e}")
        
        logger.info(f"Feature flag updated: {name}")
        return flag
    
    def delete_flag(self, name: str) -> bool:
        """Delete a feature flag"""
        if name in self.flags:
            del self.flags[name]
            self._save_flags()
            logger.info(f"Feature flag deleted: {name}")
            return True
        return False
    
    def is_enabled(
        self,
        name: str,
        user_id: Optional[str] = None,
        default: bool = False
    ) -> bool:
        """Check if feature is enabled for user"""
        flag = self.flags.get(name)
        
        if not flag:
            return default
        
        # Check blocked users
        if user_id and user_id in flag.blocked_users:
            return False
        
        # Check allowed users
        if user_id and user_id in flag.allowed_users:
            return True
        
        # Check state
        if flag.state == FeatureState.DISABLED:
            return False
        
        if flag.state == FeatureState.ENABLED:
            return True
        
        if flag.state == FeatureState.ROLLOUT:
            # Deterministic rollout based on user_id
            if user_id:
                hash_value = int(hashlib.md5(f"{name}:{user_id}".encode()).hexdigest(), 16)
                return (hash_value % 100) < flag.rollout_percentage
            return False
        
        if flag.state == FeatureState.AB_TEST:
            # A/B test - return True for variant A
            if user_id:
                hash_value = int(hashlib.md5(f"{name}:{user_id}".encode()).hexdigest(), 16)
                return (hash_value % 2) == 0
            return False
        
        return default
    
    def get_variant(
        self,
        name: str,
        user_id: Optional[str] = None,
        variants: List[str] = None
    ) -> Optional[str]:
        """Get A/B test variant for user"""
        flag = self.flags.get(name)
        
        if not flag or flag.state != FeatureState.AB_TEST:
            return None
        
        variants = variants or ['A', 'B']
        
        if user_id:
            hash_value = int(hashlib.md5(f"{name}:{user_id}".encode()).hexdigest(), 16)
            variant_index = hash_value % len(variants)
            return variants[variant_index]
        
        return variants[0]
    
    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        """Get feature flag by name"""
        return self.flags.get(name)
    
    def get_all_flags(self) -> List[FeatureFlag]:
        """Get all feature flags"""
        return list(self.flags.values())
    
    def enable(self, name: str) -> bool:
        """Enable a feature flag"""
        flag = self.update_flag(name, state=FeatureState.ENABLED)
        return flag is not None
    
    def disable(self, name: str) -> bool:
        """Disable a feature flag"""
        flag = self.update_flag(name, state=FeatureState.DISABLED)
        return flag is not None
    
    def set_rollout(self, name: str, percentage: float) -> bool:
        """Set rollout percentage"""
        flag = self.update_flag(
            name,
            state=FeatureState.ROLLOUT,
            rollout_percentage=min(100, max(0, percentage))
        )
        return flag is not None


class DynamicConfigManager:
    """
    Dynamic runtime configuration management.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Configuration storage
        self.values: Dict[str, ConfigValue] = {}
        
        # Persistence
        self.storage_path = self.config.get('storage_path', 'config/runtime_config.json')
        
        # Watch for file changes
        self.watch_interval = self.config.get('watch_interval', 30)
        self._watch_task: Optional[asyncio.Task] = None
        self._last_modified: Optional[float] = None
        
        # Callbacks
        self.on_config_change: Optional[Callable] = None
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Load existing config
        self._load_config()
        
        logger.info("DynamicConfigManager initialized")
    
    def _load_config(self):
        """Load configuration from storage"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for key, value_data in data.get('values', {}).items():
                        self.values[key] = ConfigValue(
                            key=key,
                            value=value_data.get('value'),
                            value_type=value_data.get('value_type', 'string'),
                            description=value_data.get('description', ''),
                            min_value=value_data.get('min_value'),
                            max_value=value_data.get('max_value'),
                            allowed_values=value_data.get('allowed_values'),
                            secret=value_data.get('secret', False),
                            version=value_data.get('version', 1)
                        )
                self._last_modified = os.path.getmtime(self.storage_path)
                logger.info(f"Loaded {len(self.values)} config values")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
    
    def _save_config(self):
        """Save configuration to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'values': {
                        key: {
                            'value': cv.value,
                            'value_type': cv.value_type,
                            'description': cv.description,
                            'min_value': cv.min_value,
                            'max_value': cv.max_value,
                            'allowed_values': cv.allowed_values,
                            'secret': cv.secret,
                            'version': cv.version
                        }
                        for key, cv in self.values.items()
                    },
                    'updated_at': datetime.now().isoformat()
                }, f, indent=2)
            self._last_modified = os.path.getmtime(self.storage_path)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def set(
        self,
        key: str,
        value: Any,
        value_type: str = "string",
        description: str = "",
        **kwargs
    ) -> ConfigValue:
        """Set configuration value"""
        with self._lock:
            # Validate value
            validated_value = self._validate_value(value, value_type, kwargs)
            
            if key in self.values:
                cv = self.values[key]
                old_value = cv.value
                cv.value = validated_value
                cv.version += 1
                cv.updated_at = datetime.now()
            else:
                cv = ConfigValue(
                    key=key,
                    value=validated_value,
                    value_type=value_type,
                    description=description,
                    **kwargs
                )
                self.values[key] = cv
                old_value = None
            
            self._save_config()
            
            if self.on_config_change and old_value != validated_value:
                try:
                    self.on_config_change(key, old_value, validated_value)
                except Exception as e:
                    logger.error(f"Config change callback error: {e}")
            
            logger.info(f"Config set: {key}")
            return cv
    
    def _validate_value(
        self,
        value: Any,
        value_type: str,
        constraints: Dict
    ) -> Any:
        """Validate and convert value"""
        # Type conversion
        if value_type == 'int':
            value = int(value)
        elif value_type == 'float':
            value = float(value)
        elif value_type == 'bool':
            if isinstance(value, str):
                value = value.lower() in ('true', '1', 'yes')
            else:
                value = bool(value)
        elif value_type == 'json':
            if isinstance(value, str):
                value = json.loads(value)
        
        # Range validation
        min_value = constraints.get('min_value')
        max_value = constraints.get('max_value')
        
        if min_value is not None and value < min_value:
            raise ValueError(f"Value {value} is below minimum {min_value}")
        if max_value is not None and value > max_value:
            raise ValueError(f"Value {value} is above maximum {max_value}")
        
        # Allowed values validation
        allowed_values = constraints.get('allowed_values')
        if allowed_values and value not in allowed_values:
            raise ValueError(f"Value {value} not in allowed values {allowed_values}")
        
        return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        with self._lock:
            cv = self.values.get(key)
            if cv:
                return cv.value
            return default
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value"""
        value = self.get(key, default)
        return int(value) if value is not None else default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value"""
        value = self.get(key, default)
        return float(value) if value is not None else default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value"""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value) if value is not None else default
    
    def get_json(self, key: str, default: Any = None) -> Any:
        """Get JSON configuration value"""
        value = self.get(key, default)
        if isinstance(value, str):
            return json.loads(value)
        return value
    
    def delete(self, key: str) -> bool:
        """Delete configuration value"""
        with self._lock:
            if key in self.values:
                del self.values[key]
                self._save_config()
                logger.info(f"Config deleted: {key}")
                return True
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        with self._lock:
            return {key: cv.to_dict() for key, cv in self.values.items()}
    
    async def start_watching(self):
        """Start watching for config file changes"""
        self._watch_task = asyncio.create_task(self._watch_loop())
        logger.info("Config file watching started")
    
    async def stop_watching(self):
        """Stop watching for config file changes"""
        if self._watch_task:
            self._watch_task.cancel()
        logger.info("Config file watching stopped")
    
    async def _watch_loop(self):
        """Watch for file changes"""
        while True:
            try:
                await asyncio.sleep(self.watch_interval)
                
                if os.path.exists(self.storage_path):
                    current_modified = os.path.getmtime(self.storage_path)
                    
                    if self._last_modified and current_modified > self._last_modified:
                        logger.info("Config file changed, reloading...")
                        self._load_config()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Config watch error: {e}")


class ConfigurationService:
    """
    Unified configuration service.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self.feature_flags = FeatureFlagManager(
            self.config.get('feature_flags', {})
        )
        
        self.dynamic_config = DynamicConfigManager(
            self.config.get('dynamic_config', {})
        )
        
        logger.info("ConfigurationService initialized")
    
    async def start(self):
        """Start configuration service"""
        await self.dynamic_config.start_watching()
    
    async def stop(self):
        """Stop configuration service"""
        await self.dynamic_config.stop_watching()
    
    def is_feature_enabled(self, name: str, user_id: Optional[str] = None) -> bool:
        """Check if feature is enabled"""
        return self.feature_flags.is_enabled(name, user_id)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.dynamic_config.get(key, default)
    
    def set_config(self, key: str, value: Any, **kwargs):
        """Set configuration value"""
        return self.dynamic_config.set(key, value, **kwargs)
    
    def get_status(self) -> Dict[str, Any]:
        """Get configuration status"""
        return {
            'feature_flags': {
                'count': len(self.feature_flags.flags),
                'enabled': sum(1 for f in self.feature_flags.flags.values() 
                              if f.state == FeatureState.ENABLED)
            },
            'config_values': {
                'count': len(self.dynamic_config.values)
            }
        }


# Export
__all__ = [
    'ConfigurationService',
    'FeatureFlagManager',
    'DynamicConfigManager',
    'FeatureFlag',
    'FeatureState',
    'ConfigValue'
]
