"""
Data Validator - Validates incoming data quality
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    score: float  # 0-1


class DataValidator:
    """Validates data quality"""
    
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
            self._running = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        try:
            logger.info("DataValidator initialized")
            return True
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    async def start(self) -> bool:
        try:
            self._running = True
            return True
        except Exception as e:
            logger.error(f"Error in start: {e}")
            raise
    
    async def stop(self) -> bool:
        try:
            self._running = False
            return True
        except Exception as e:
            logger.error(f"Error in stop: {e}")
            raise
    
    def validate(self, data: pd.DataFrame) -> ValidationResult:
        try:
            errors, warnings = [], []
            if data.empty:
                errors.append("Empty dataframe")
            if data.isnull().any().any():
                warnings.append("Contains null values")
            score = 1.0 - (len(errors) * 0.3 + len(warnings) * 0.1)
            return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings, score=max(0, score))
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


_validator: Optional[DataValidator] = None
def get_validator() -> DataValidator:
    try:
        global _validator
        if _validator is None:
            _validator = DataValidator()
        return _validator
    except Exception as e:
        logger.error(f"Error in get_validator: {e}")
        raise

async def initialize(config: Dict[str, Any] = None) -> bool:
    return await get_validator().initialize(config)
async def start() -> bool:
    return await get_validator().start()
async def stop() -> bool:
    return await get_validator().stop()
