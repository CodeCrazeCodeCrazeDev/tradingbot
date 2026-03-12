"""
Configuration Validation System
Schema-based validation for trading bot configuration
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Configuration validation error"""
    pass


class FieldType(Enum):
    """Configuration field types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    ENUM = "enum"


@dataclass
class FieldSchema:
    """Field validation schema"""
    name: str
    field_type: FieldType
    required: bool = True
    default: Any = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    description: str = ""


class ConfigValidator:
    """
    Configuration Validator
    
    Validates trading bot configuration against schema.
    Ensures all required fields are present and valid.
    """
    
    def __init__(self):
        """Initialize configuration validator"""
        self.schema = self._build_schema()
        logger.info("ConfigValidator initialized")
    
    def _build_schema(self) -> Dict[str, List[FieldSchema]]:
        """Build configuration schema"""
        return {
            'trading': [
                FieldSchema(
                    name='symbols',
                    field_type=FieldType.LIST,
                    required=True,
                    min_length=1,
                    description='List of trading symbols'
                ),
                FieldSchema(
                    name='interval_seconds',
                    field_type=FieldType.INTEGER,
                    required=True,
                    min_value=1,
                    max_value=3600,
                    default=60,
                    description='Trading loop interval in seconds'
                ),
                FieldSchema(
                    name='mode',
                    field_type=FieldType.ENUM,
                    required=True,
                    allowed_values=['paper', 'live', 'simulation'],
                    default='paper',
                    description='Trading mode'
                ),
                FieldSchema(
                    name='max_positions',
                    field_type=FieldType.INTEGER,
                    required=False,
                    min_value=1,
                    max_value=100,
                    default=10,
                    description='Maximum concurrent positions'
                )
            ],
            'risk': [
                FieldSchema(
                    name='max_risk_per_trade',
                    field_type=FieldType.FLOAT,
                    required=True,
                    min_value=0.001,
                    max_value=0.1,
                    default=0.02,
                    description='Maximum risk per trade (fraction)'
                ),
                FieldSchema(
                    name='max_daily_loss',
                    field_type=FieldType.FLOAT,
                    required=True,
                    min_value=0.01,
                    max_value=0.5,
                    default=0.05,
                    description='Maximum daily loss (fraction)'
                ),
                FieldSchema(
                    name='max_drawdown',
                    field_type=FieldType.FLOAT,
                    required=True,
                    min_value=0.05,
                    max_value=0.5,
                    default=0.20,
                    description='Maximum drawdown (fraction)'
                ),
                FieldSchema(
                    name='position_size_method',
                    field_type=FieldType.ENUM,
                    required=False,
                    allowed_values=['fixed', 'kelly', 'volatility'],
                    default='fixed',
                    description='Position sizing method'
                )
            ],
            'account': [
                FieldSchema(
                    name='initial_capital',
                    field_type=FieldType.FLOAT,
                    required=True,
                    min_value=100,
                    description='Initial account capital'
                ),
                FieldSchema(
                    name='currency',
                    field_type=FieldType.STRING,
                    required=False,
                    default='USD',
                    description='Account currency'
                )
            ],
            'broker': [
                FieldSchema(
                    name='name',
                    field_type=FieldType.ENUM,
                    required=True,
                    allowed_values=['alpaca', 'interactive_brokers', 'binance', 'mt5', 'simulation'],
                    description='Broker name'
                ),
                FieldSchema(
                    name='api_key',
                    field_type=FieldType.STRING,
                    required=False,
                    description='Broker API key'
                ),
                FieldSchema(
                    name='api_secret',
                    field_type=FieldType.STRING,
                    required=False,
                    description='Broker API secret'
                )
            ],
            'execution': [
                FieldSchema(
                    name='order_type',
                    field_type=FieldType.ENUM,
                    required=False,
                    allowed_values=['market', 'limit', 'stop', 'stop_limit'],
                    default='market',
                    description='Default order type'
                ),
                FieldSchema(
                    name='max_slippage',
                    field_type=FieldType.FLOAT,
                    required=False,
                    min_value=0.0,
                    max_value=0.1,
                    default=0.001,
                    description='Maximum allowed slippage'
                ),
                FieldSchema(
                    name='fill_timeout_seconds',
                    field_type=FieldType.INTEGER,
                    required=False,
                    min_value=1,
                    max_value=600,
                    default=60,
                    description='Order fill timeout'
                )
            ],
            'logging': [
                FieldSchema(
                    name='level',
                    field_type=FieldType.ENUM,
                    required=False,
                    allowed_values=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    default='INFO',
                    description='Logging level'
                ),
                FieldSchema(
                    name='file',
                    field_type=FieldType.STRING,
                    required=False,
                    description='Log file path'
                ),
                FieldSchema(
                    name='max_bytes',
                    field_type=FieldType.INTEGER,
                    required=False,
                    min_value=1024,
                    default=10485760,
                    description='Max log file size in bytes'
                ),
                FieldSchema(
                    name='backup_count',
                    field_type=FieldType.INTEGER,
                    required=False,
                    min_value=1,
                    max_value=100,
                    default=5,
                    description='Number of backup log files'
                )
            ],
            'database': [
                FieldSchema(
                    name='path',
                    field_type=FieldType.STRING,
                    required=False,
                    default='trading_bot.db',
                    description='Database file path'
                ),
                FieldSchema(
                    name='pool_size',
                    field_type=FieldType.INTEGER,
                    required=False,
                    min_value=1,
                    max_value=100,
                    default=5,
                    description='Connection pool size'
                )
            ],
            'monitoring': [
                FieldSchema(
                    name='enabled',
                    field_type=FieldType.BOOLEAN,
                    required=False,
                    default=True,
                    description='Enable monitoring'
                ),
                FieldSchema(
                    name='metrics_port',
                    field_type=FieldType.INTEGER,
                    required=False,
                    min_value=1024,
                    max_value=65535,
                    default=9090,
                    description='Metrics export port'
                ),
                FieldSchema(
                    name='health_check_port',
                    field_type=FieldType.INTEGER,
                    required=False,
                    min_value=1024,
                    max_value=65535,
                    default=8080,
                    description='Health check port'
                )
            ]
        }
    
    def validate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Validated configuration with defaults applied
            
        Raises:
            ValidationError: If configuration is invalid
        """
        validated = {}
        errors = []
        
        # Validate each section
        for section_name, fields in self.schema.items():
            section_config = config.get(section_name, {})
            validated[section_name] = {}
            
            for field in fields:
                try:
                    value = self._validate_field(field, section_config, section_name)
                    validated[section_name][field.name] = value
                except ValidationError as e:
                    errors.append(str(e))
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(errors)
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        logger.info("Configuration validated successfully")
        return validated
    
    def _validate_field(
        self,
        field: FieldSchema,
        section_config: Dict[str, Any],
        section_name: str
    ) -> Any:
        """Validate a single field"""
        value = section_config.get(field.name)
        
        # Check required
        if value is None:
            if field.required:
                raise ValidationError(
                    f"{section_name}.{field.name}: Required field missing"
                )
            return field.default
        
        # Validate type
        if field.field_type == FieldType.STRING:
            if not isinstance(value, str):
                raise ValidationError(
                    f"{section_name}.{field.name}: Must be string, got {type(value).__name__}"
                )
            
            if field.min_length and len(value) < field.min_length:
                raise ValidationError(
                    f"{section_name}.{field.name}: Length must be >= {field.min_length}"
                )
            
            if field.max_length and len(value) > field.max_length:
                raise ValidationError(
                    f"{section_name}.{field.name}: Length must be <= {field.max_length}"
                )
            
            if field.pattern:
                import re
                if not re.match(field.pattern, value):
                    raise ValidationError(
                        f"{section_name}.{field.name}: Does not match pattern {field.pattern}"
                    )
        
        elif field.field_type == FieldType.INTEGER:
            if not isinstance(value, int):
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    raise ValidationError(
                        f"{section_name}.{field.name}: Must be integer, got {type(value).__name__}"
                    )
            
            if field.min_value is not None and value < field.min_value:
                raise ValidationError(
                    f"{section_name}.{field.name}: Must be >= {field.min_value}"
                )
            
            if field.max_value is not None and value > field.max_value:
                raise ValidationError(
                    f"{section_name}.{field.name}: Must be <= {field.max_value}"
                )
        
        elif field.field_type == FieldType.FLOAT:
            if not isinstance(value, (int, float)):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    raise ValidationError(
                        f"{section_name}.{field.name}: Must be float, got {type(value).__name__}"
                    )
            
            value = float(value)
            
            if field.min_value is not None and value < field.min_value:
                raise ValidationError(
                    f"{section_name}.{field.name}: Must be >= {field.min_value}"
                )
            
            if field.max_value is not None and value > field.max_value:
                raise ValidationError(
                    f"{section_name}.{field.name}: Must be <= {field.max_value}"
                )
        
        elif field.field_type == FieldType.BOOLEAN:
            if not isinstance(value, bool):
                if isinstance(value, str):
                    value = value.lower() in ['true', '1', 'yes', 'on']
                else:
                    raise ValidationError(
                        f"{section_name}.{field.name}: Must be boolean, got {type(value).__name__}"
                    )
        
        elif field.field_type == FieldType.LIST:
            if not isinstance(value, list):
                raise ValidationError(
                    f"{section_name}.{field.name}: Must be list, got {type(value).__name__}"
                )
            
            if field.min_length and len(value) < field.min_length:
                raise ValidationError(
                    f"{section_name}.{field.name}: List length must be >= {field.min_length}"
                )
            
            if field.max_length and len(value) > field.max_length:
                raise ValidationError(
                    f"{section_name}.{field.name}: List length must be <= {field.max_length}"
                )
        
        elif field.field_type == FieldType.DICT:
            if not isinstance(value, dict):
                raise ValidationError(
                    f"{section_name}.{field.name}: Must be dict, got {type(value).__name__}"
                )
        
        elif field.field_type == FieldType.ENUM:
            if field.allowed_values and value not in field.allowed_values:
                raise ValidationError(
                    f"{section_name}.{field.name}: Must be one of {field.allowed_values}, got '{value}'"
                )
        
        return value
    
    def get_schema_documentation(self) -> str:
        """Generate schema documentation"""
        lines = ["# Trading Bot Configuration Schema\n"]
        
        for section_name, fields in self.schema.items():
            lines.append(f"\n## {section_name}\n")
            
            for field in fields:
                lines.append(f"### {field.name}")
                lines.append(f"- **Type**: {field.field_type.value}")
                lines.append(f"- **Required**: {'Yes' if field.required else 'No'}")
                
                if field.default is not None:
                    lines.append(f"- **Default**: {field.default}")
                
                if field.min_value is not None:
                    lines.append(f"- **Min**: {field.min_value}")
                
                if field.max_value is not None:
                    lines.append(f"- **Max**: {field.max_value}")
                
                if field.allowed_values:
                    lines.append(f"- **Allowed**: {', '.join(map(str, field.allowed_values))}")
                
                if field.description:
                    lines.append(f"- **Description**: {field.description}")
                
                lines.append("")
        
        return "\n".join(lines)
    
    def generate_example_config(self) -> Dict[str, Any]:
        """Generate example configuration with defaults"""
        example = {}
        
        for section_name, fields in self.schema.items():
            example[section_name] = {}
            
            for field in fields:
                if field.default is not None:
                    example[section_name][field.name] = field.default
                elif field.required:
                    # Provide example values for required fields
                    if field.field_type == FieldType.STRING:
                        example[section_name][field.name] = f"<{field.name}>"
                    elif field.field_type == FieldType.INTEGER:
                        example[section_name][field.name] = field.min_value or 0
                    elif field.field_type == FieldType.FLOAT:
                        example[section_name][field.name] = field.min_value or 0.0
                    elif field.field_type == FieldType.BOOLEAN:
                        example[section_name][field.name] = False
                    elif field.field_type == FieldType.LIST:
                        example[section_name][field.name] = []
                    elif field.field_type == FieldType.DICT:
                        example[section_name][field.name] = {}
                    elif field.field_type == FieldType.ENUM and field.allowed_values:
                        example[section_name][field.name] = field.allowed_values[0]
        
        return example


# Singleton instance
_config_validator: Optional[ConfigValidator] = None


def get_config_validator() -> ConfigValidator:
    """Get or create config validator singleton"""
    global _config_validator
    
    if _config_validator is None:
        _config_validator = ConfigValidator()
    
    return _config_validator


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to validate configuration"""
    validator = get_config_validator()
    return validator.validate(config)
