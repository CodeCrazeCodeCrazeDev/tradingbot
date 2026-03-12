"""
Configuration Integrity Monitor - Answers Q781-Q800
===================================================

Critical Question Q781: How do you manage configuration across environments?
Critical Question Q791: How do you ensure parameter values are valid?
Critical Question Q789: How do you detect when configuration is being tampered with?

This module provides:
1. Configuration validation
2. Drift detection
3. Tampering detection via checksums
4. Parameter bounds enforcement
5. Configuration versioning
6. Audit trail
"""

import logging
import threading
import hashlib
import json
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class ConfigValidationResult(Enum):
    """Configuration validation result"""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    TAMPERED = "tampered"


class ParameterType(Enum):
    """Parameter types for validation"""
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    ENUM = "enum"
    PATH = "path"
    URL = "url"
    PERCENTAGE = "percentage"  # 0-1 or 0-100


@dataclass
class ParameterSpec:
    """Specification for a configuration parameter"""
    name: str
    param_type: ParameterType
    required: bool = True
    default: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None  # Regex pattern for strings
    description: str = ""
    immutable: bool = False  # Cannot be changed at runtime
    sensitive: bool = False  # Should be masked in logs


@dataclass
class ConfigValidationError:
    """Configuration validation error"""
    parameter: str
    error_type: str
    expected: Any
    actual: Any
    message: str
    severity: str  # 'critical', 'warning', 'info'
    
    def to_dict(self) -> Dict:
        return {
            'parameter': self.parameter,
            'error_type': self.error_type,
            'expected': str(self.expected),
            'actual': str(self.actual),
            'message': self.message,
            'severity': self.severity
        }


@dataclass
class ConfigSnapshot:
    """Snapshot of configuration state"""
    timestamp: datetime
    config_hash: str
    config_data: Dict
    version: int
    source: str  # 'file', 'api', 'env', 'default'
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'config_hash': self.config_hash,
            'version': self.version,
            'source': self.source
        }


class ConfigIntegrityMonitor:
    """
    Monitors configuration integrity and detects drift/tampering.
    
    Addresses critical questions:
    - Q781: Configuration management across environments
    - Q791: Parameter validation
    - Q789: Tampering detection
    
    Features:
    - Schema-based validation
    - Checksum verification
    - Drift detection
    - Immutable parameter protection
    - Audit trail
    """
    
    # IMMUTABLE: Critical trading parameters that should never be auto-modified
    PROTECTED_PARAMETERS = {
        'max_risk_per_trade',
        'max_drawdown',
        'max_leverage',
        'emergency_shutdown_drawdown',
        'max_position_size',
        'kill_switch_enabled'
    }
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        schema: Optional[Dict[str, ParameterSpec]] = None,
        check_interval: float = 60.0,
        on_drift_detected: Optional[Callable] = None,
        on_tampering_detected: Optional[Callable] = None,
        on_validation_error: Optional[Callable] = None
    ):
        """
        Initialize configuration integrity monitor.
        
        Args:
            config_path: Path to configuration file
            schema: Parameter specifications
            check_interval: Seconds between integrity checks
            on_drift_detected: Callback when config drift detected
            on_tampering_detected: Callback when tampering detected
            on_validation_error: Callback when validation fails
        """
        self.config_path = Path(config_path) if config_path else None
        self.schema = schema or self._get_default_schema()
        self.check_interval = check_interval
        self.on_drift_detected = on_drift_detected
        self.on_tampering_detected = on_tampering_detected
        self.on_validation_error = on_validation_error
        
        # State
        self._lock = threading.RLock()
        self._current_config: Dict = {}
        self._baseline_hash: Optional[str] = None
        self._snapshots: List[ConfigSnapshot] = []
        self._version = 0
        
        # Audit trail
        self._audit_log: List[Dict] = []
        
        # Statistics
        self.stats = {
            'validations': 0,
            'validation_errors': 0,
            'drift_detections': 0,
            'tampering_detections': 0
        }
        
        logger.info("ConfigIntegrityMonitor initialized")
    
    def _get_default_schema(self) -> Dict[str, ParameterSpec]:
        """Get default schema for trading bot configuration"""
        return {
            # Risk parameters
            'max_risk_per_trade': ParameterSpec(
                name='max_risk_per_trade',
                param_type=ParameterType.PERCENTAGE,
                required=True,
                default=0.02,
                min_value=0.001,
                max_value=0.05,
                description='Maximum risk per trade as decimal',
                immutable=False
            ),
            'max_drawdown': ParameterSpec(
                name='max_drawdown',
                param_type=ParameterType.PERCENTAGE,
                required=True,
                default=0.20,
                min_value=0.05,
                max_value=0.30,
                description='Maximum allowed drawdown',
                immutable=False
            ),
            'max_leverage': ParameterSpec(
                name='max_leverage',
                param_type=ParameterType.FLOAT,
                required=True,
                default=1.0,
                min_value=1.0,
                max_value=10.0,
                description='Maximum leverage',
                immutable=False
            ),
            'emergency_shutdown_drawdown': ParameterSpec(
                name='emergency_shutdown_drawdown',
                param_type=ParameterType.PERCENTAGE,
                required=True,
                default=0.25,
                min_value=0.10,
                max_value=0.35,
                description='Drawdown that triggers emergency shutdown',
                immutable=True
            ),
            'max_position_size': ParameterSpec(
                name='max_position_size',
                param_type=ParameterType.PERCENTAGE,
                required=True,
                default=0.10,
                min_value=0.01,
                max_value=0.25,
                description='Maximum position size as % of portfolio',
                immutable=False
            ),
            'max_open_positions': ParameterSpec(
                name='max_open_positions',
                param_type=ParameterType.INTEGER,
                required=True,
                default=10,
                min_value=1,
                max_value=50,
                description='Maximum concurrent positions',
                immutable=False
            ),
            # Trading parameters
            'trading_enabled': ParameterSpec(
                name='trading_enabled',
                param_type=ParameterType.BOOLEAN,
                required=True,
                default=False,
                description='Whether trading is enabled',
                immutable=False
            ),
            'trading_mode': ParameterSpec(
                name='trading_mode',
                param_type=ParameterType.ENUM,
                required=True,
                default='paper',
                allowed_values=['live', 'paper', 'simulation', 'backtest'],
                description='Trading mode',
                immutable=False
            ),
            # Kill switch
            'kill_switch_enabled': ParameterSpec(
                name='kill_switch_enabled',
                param_type=ParameterType.BOOLEAN,
                required=True,
                default=True,
                description='Whether kill switch is enabled',
                immutable=True
            ),
            # Data parameters
            'data_staleness_threshold': ParameterSpec(
                name='data_staleness_threshold',
                param_type=ParameterType.FLOAT,
                required=False,
                default=5.0,
                min_value=1.0,
                max_value=60.0,
                description='Max data age in seconds',
                immutable=False
            ),
            # API keys (sensitive)
            'broker_api_key': ParameterSpec(
                name='broker_api_key',
                param_type=ParameterType.STRING,
                required=False,
                default='',
                description='Broker API key',
                sensitive=True,
                immutable=False
            ),
            'broker_api_secret': ParameterSpec(
                name='broker_api_secret',
                param_type=ParameterType.STRING,
                required=False,
                default='',
                description='Broker API secret',
                sensitive=True,
                immutable=False
            )
        }
    
    def load_config(self, config_path: Optional[str] = None) -> Tuple[Dict, List[ConfigValidationError]]:
        """
        Load and validate configuration from file.
        
        Args:
            config_path: Optional path override
            
        Returns:
            Tuple of (config_dict, validation_errors)
        """
        path = Path(config_path) if config_path else self.config_path
        
        if not path or not path.exists():
            try:
                logger.warning(f"Config file not found: {path}")
                return {}, [ConfigValidationError(
                    parameter='config_file',
                    error_type='missing',
                    expected='file exists',
                    actual='file not found',
                    message=f"Configuration file not found: {path}",
                    severity='critical'
                )]

                with open(path, 'r') as f:
                    if path.suffix in ('.yaml', '.yml'):
                        config = yaml.safe_load(f) or {}
                    elif path.suffix == '.json':
                        config = json.load(f)
                    else:
                        logger.error(f"Unsupported config format: {path.suffix}")
                        return {}, []

                # Validate
                errors = self.validate_config(config)

                # Store if valid
                if not any(e.severity == 'critical' for e in errors):
                    with self._lock:
                        self._current_config = config
                        self._baseline_hash = self._compute_hash(config)
                        self._version += 1

                        # Create snapshot
                        snapshot = ConfigSnapshot(
                            timestamp=datetime.now(),
                            config_hash=self._baseline_hash,
                            config_data=self._mask_sensitive(config),
                            version=self._version,
                            source='file'
                        )
                        self._snapshots.append(snapshot)

                        self._log_audit('load', 'config_loaded', {'path': str(path), 'version': self._version})

                return config, errors

            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return {}, [ConfigValidationError(
                    parameter='config_file',
                    error_type='parse_error',
                    expected='valid format',
                    actual=str(e),
                    message=f"Failed to parse configuration: {e}",
                    severity='critical'
                )]

    def validate_config(self, config: Dict) -> List[ConfigValidationError]:
        """
        Validate configuration against schema.
        
        This is the answer to Q791: How do you ensure parameter values are valid?
        
        Args:
            config: Configuration dictionary
            
        Returns:
            List of validation errors
        """
        self.stats['validations'] += 1
        errors = []
        
        for param_name, spec in self.schema.items():
            value = config.get(param_name)
            
            # Check required
            if spec.required and value is None:
                if spec.default is not None:
                    continue  # Will use default
                errors.append(ConfigValidationError(
                    parameter=param_name,
                    error_type='missing_required',
                    expected='value present',
                    actual='missing',
                    message=f"Required parameter '{param_name}' is missing",
                    severity='critical'
                ))
                continue
            
            if value is None:
                continue
            
            # Type validation
            type_error = self._validate_type(param_name, value, spec)
            if type_error:
                errors.append(type_error)
                continue
            
            # Range validation
            if spec.min_value is not None and value < spec.min_value:
                errors.append(ConfigValidationError(
                    parameter=param_name,
                    error_type='below_minimum',
                    expected=f'>= {spec.min_value}',
                    actual=value,
                    message=f"'{param_name}' value {value} is below minimum {spec.min_value}",
                    severity='critical'
                ))
            
            if spec.max_value is not None and value > spec.max_value:
                errors.append(ConfigValidationError(
                    parameter=param_name,
                    error_type='above_maximum',
                    expected=f'<= {spec.max_value}',
                    actual=value,
                    message=f"'{param_name}' value {value} is above maximum {spec.max_value}",
                    severity='critical'
                ))
            
            # Allowed values
            if spec.allowed_values and value not in spec.allowed_values:
                errors.append(ConfigValidationError(
                    parameter=param_name,
                    error_type='invalid_value',
                    expected=f'one of {spec.allowed_values}',
                    actual=value,
                    message=f"'{param_name}' value '{value}' not in allowed values",
                    severity='critical'
                ))
        
        # Check for unknown parameters (warning only)
        known_params = set(self.schema.keys())
        for param in config.keys():
            if param not in known_params:
                errors.append(ConfigValidationError(
                    parameter=param,
                    error_type='unknown_parameter',
                    expected='known parameter',
                    actual=param,
                    message=f"Unknown parameter '{param}' in configuration",
                    severity='warning'
                ))
        
        if errors:
            self.stats['validation_errors'] += len(errors)
            if self.on_validation_error:
                for error in errors:
                    try:
                        self.on_validation_error(error)
                    except Exception as e:
                        logger.error(f"Validation error callback failed: {e}")
        
        return errors
    
    def _validate_type(
        self,
        param_name: str,
        value: Any,
        spec: ParameterSpec
    ) -> Optional[ConfigValidationError]:
        """Validate parameter type"""
        expected_type = spec.param_type
        
        type_checks = {
            ParameterType.INTEGER: lambda v: isinstance(v, int) and not isinstance(v, bool),
            ParameterType.FLOAT: lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            ParameterType.STRING: lambda v: isinstance(v, str),
            ParameterType.BOOLEAN: lambda v: isinstance(v, bool),
            ParameterType.LIST: lambda v: isinstance(v, list),
            ParameterType.DICT: lambda v: isinstance(v, dict),
            ParameterType.ENUM: lambda v: isinstance(v, str),
            ParameterType.PATH: lambda v: isinstance(v, str),
            ParameterType.URL: lambda v: isinstance(v, str) and ('://' in v or v.startswith('/')),
            ParameterType.PERCENTAGE: lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)
        }
        
        check_func = type_checks.get(expected_type, lambda v: True)
        
        if not check_func(value):
            return ConfigValidationError(
                parameter=param_name,
                error_type='type_mismatch',
                expected=expected_type.value,
                actual=type(value).__name__,
                message=f"'{param_name}' expected {expected_type.value}, got {type(value).__name__}",
                severity='critical'
            )
        
        return None
    
    def check_integrity(self) -> Tuple[bool, List[str]]:
        """
        Check configuration integrity.
        
        This is the answer to Q789: How do you detect when configuration is being tampered with?
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        with self._lock:
            if not self._current_config:
                return True, []
            
            # Compute current hash
            current_hash = self._compute_hash(self._current_config)
            
            # Compare with baseline
            if self._baseline_hash and current_hash != self._baseline_hash:
                issues.append(f"Configuration hash mismatch: expected {self._baseline_hash[:8]}, got {current_hash[:8]}")
                self.stats['tampering_detections'] += 1
                
                if self.on_tampering_detected:
                    try:
                        self.on_tampering_detected(self._baseline_hash, current_hash)
                    except Exception as e:
                        logger.error(f"Tampering callback failed: {e}")
            
            # Check file modification if path exists
            if self.config_path and self.config_path.exists():
                try:
                    with open(self.config_path, 'r') as f:
                        if self.config_path.suffix in ('.yaml', '.yml'):
                            file_config = yaml.safe_load(f) or {}
                        else:
                            file_config = json.load(f)
                    
                    file_hash = self._compute_hash(file_config)
                    
                    if file_hash != current_hash:
                        issues.append("Configuration file differs from loaded config")
                        self.stats['drift_detections'] += 1
                        
                        if self.on_drift_detected:
                            try:
                                self.on_drift_detected(self._current_config, file_config)
                            except Exception as e:
                                logger.error(f"Drift callback failed: {e}")
                                
                except Exception as e:
                    issues.append(f"Failed to read config file: {e}")
        
        return len(issues) == 0, issues
    
    def update_parameter(
        self,
        param_name: str,
        value: Any,
        source: str = 'api'
    ) -> Tuple[bool, Optional[str]]:
        """
        Update a configuration parameter.
        
        Args:
            param_name: Parameter name
            value: New value
            source: Source of update
            
        Returns:
            Tuple of (success, error_message)
        """
        with self._lock:
            # Check if parameter exists in schema
            spec = self.schema.get(param_name)
            if not spec:
                return False, f"Unknown parameter: {param_name}"
            
            # Check if immutable
            if spec.immutable:
                self._log_audit('update_blocked', param_name, {
                    'reason': 'immutable',
                    'attempted_value': str(value)
                })
                return False, f"Parameter '{param_name}' is immutable and cannot be changed"
            
            # Check if protected
            if param_name in self.PROTECTED_PARAMETERS:
                logger.warning(f"Updating protected parameter: {param_name}")
            
            # Validate new value
            test_config = {**self._current_config, param_name: value}
            errors = self.validate_config(test_config)
            
            param_errors = [e for e in errors if e.parameter == param_name and e.severity == 'critical']
            if param_errors:
                return False, param_errors[0].message
            
            # Store old value for audit
            old_value = self._current_config.get(param_name)
            
            # Update
            self._current_config[param_name] = value
            self._version += 1
            
            # Update baseline hash
            self._baseline_hash = self._compute_hash(self._current_config)
            
            # Create snapshot
            snapshot = ConfigSnapshot(
                timestamp=datetime.now(),
                config_hash=self._baseline_hash,
                config_data=self._mask_sensitive(self._current_config),
                version=self._version,
                source=source
            )
            self._snapshots.append(snapshot)
            
            # Audit
            self._log_audit('update', param_name, {
                'old_value': str(old_value) if not spec.sensitive else '***',
                'new_value': str(value) if not spec.sensitive else '***',
                'source': source
            })
            
            logger.info(f"Configuration updated: {param_name} = {value if not spec.sensitive else '***'}")
            
            return True, None
    
    def get_parameter(self, param_name: str, default: Any = None) -> Any:
        """Get a configuration parameter value"""
        with self._lock:
            value = self._current_config.get(param_name)
            if value is None:
                spec = self.schema.get(param_name)
                if spec and spec.default is not None:
                    return spec.default
                return default
            return value
    
    def get_config(self, mask_sensitive: bool = True) -> Dict:
        """Get current configuration"""
        with self._lock:
            if mask_sensitive:
                return self._mask_sensitive(self._current_config)
            return dict(self._current_config)
    
    def _compute_hash(self, config: Dict) -> str:
        """Compute hash of configuration"""
        # Sort keys for consistent hashing
        sorted_config = json.dumps(config, sort_keys=True, default=str)
        return hashlib.sha256(sorted_config.encode()).hexdigest()
    
    def _mask_sensitive(self, config: Dict) -> Dict:
        """Mask sensitive values in configuration"""
        masked = dict(config)
        for param_name, spec in self.schema.items():
            if spec.sensitive and param_name in masked and masked[param_name]:
                masked[param_name] = '***MASKED***'
        return masked
    
    def _log_audit(self, action: str, target: str, details: Dict):
        """Log audit entry"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'target': target,
            'details': details,
            'version': self._version
        }
        self._audit_log.append(entry)
        
        # Limit audit log size
        if len(self._audit_log) > 10000:
            self._audit_log = self._audit_log[-5000:]
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get recent audit log entries"""
        return self._audit_log[-limit:]
    
    def get_snapshots(self, limit: int = 10) -> List[Dict]:
        """Get recent configuration snapshots"""
        return [s.to_dict() for s in self._snapshots[-limit:]]
    
    def rollback_to_version(self, version: int) -> Tuple[bool, Optional[str]]:
        """Rollback to a previous configuration version"""
        with self._lock:
            # Find snapshot
            target_snapshot = None
            for snapshot in self._snapshots:
                if snapshot.version == version:
                    target_snapshot = snapshot
                    break
            
            if not target_snapshot:
                return False, f"Version {version} not found"
            
            # Validate
            errors = self.validate_config(target_snapshot.config_data)
            if any(e.severity == 'critical' for e in errors):
                return False, "Snapshot configuration is no longer valid"
            
            # Rollback
            old_version = self._version
            self._current_config = dict(target_snapshot.config_data)
            self._version += 1
            self._baseline_hash = self._compute_hash(self._current_config)
            
            self._log_audit('rollback', 'config', {
                'from_version': old_version,
                'to_version': version
            })
            
            logger.info(f"Configuration rolled back from v{old_version} to v{version}")
            
            return True, None
    
    def get_status(self) -> Dict:
        """Get monitor status"""
        is_valid, issues = self.check_integrity()
        
        return {
            'current_version': self._version,
            'baseline_hash': self._baseline_hash[:16] if self._baseline_hash else None,
            'is_valid': is_valid,
            'issues': issues,
            'parameters_count': len(self._current_config),
            'snapshots_count': len(self._snapshots),
            'audit_log_count': len(self._audit_log),
            'statistics': self.stats
        }
