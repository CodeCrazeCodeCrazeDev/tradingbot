"""
Elite Data Validation & Quality System
Ensures data integrity and quality before trading decisions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import numpy
import pandas

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of data validation"""
    passed: bool
    level: ValidationLevel
    message: str
    details: Dict = None


class DataQualityValidator:
    """
    Elite Data Quality Validator
    
    Validates:
    - Missing data
    - Outliers
    - Data gaps
    - Price anomalies
    - Volume anomalies
    - Timestamp consistency
    """
    
    def __init__(self, strict_mode: bool = True):
        try:
            self.strict_mode = strict_mode
            self.validation_results: List[ValidationResult] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def validate_ohlcv(self, df: pd.DataFrame) -> Tuple[bool, List[ValidationResult]]:
        """
        Comprehensive OHLCV data validation
        
        Returns:
            (is_valid, validation_results)
        """
        try:
            self.validation_results = []
        
            # Required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                self.validation_results.append(ValidationResult(
                    passed=False,
                    level=ValidationLevel.CRITICAL,
                    message="Missing required OHLCV columns",
                    details={'missing': [c for c in required_cols if c not in df.columns]}
                ))
                return False, self.validation_results
        
            # Run all validations
            validations = [
                self._check_missing_values(df),
                self._check_ohlc_consistency(df),
                self._check_price_outliers(df),
                self._check_volume_anomalies(df),
                self._check_data_gaps(df),
                self._check_timestamp_order(df),
                self._check_zero_values(df),
                self._check_negative_values(df)
            ]
        
            # Aggregate results
            critical_failures = [v for v in validations if not v.passed and v.level == ValidationLevel.CRITICAL]
        
            if critical_failures:
                logger.error(f"Data validation failed: {len(critical_failures)} critical issues")
                return False, self.validation_results
        
            error_failures = [v for v in validations if not v.passed and v.level == ValidationLevel.ERROR]
            if error_failures and self.strict_mode:
                logger.warning(f"Data validation failed in strict mode: {len(error_failures)} errors")
                return False, self.validation_results
        
            logger.info("✅ Data validation passed")
            return True, self.validation_results
        except Exception as e:
            logger.error(f"Error in validate_ohlcv: {e}")
            raise
    
    def _check_missing_values(self, df: pd.DataFrame) -> ValidationResult:
        """Check for missing values"""
        try:
            missing = df.isnull().sum()
            total_missing = missing.sum()
        
            if total_missing > 0:
                missing_pct = (total_missing / (len(df) * len(df.columns))) * 100
            
                if missing_pct > 5:  # More than 5% missing
                    result = ValidationResult(
                        passed=False,
                        level=ValidationLevel.CRITICAL,
                        message=f"High missing data: {missing_pct:.2f}%",
                        details={'missing_counts': missing.to_dict()}
                    )
                else:
                    result = ValidationResult(
                        passed=False,
                        level=ValidationLevel.WARNING,
                        message=f"Some missing data: {missing_pct:.2f}%",
                        details={'missing_counts': missing.to_dict()}
                    )
            else:
                result = ValidationResult(
                    passed=True,
                    level=ValidationLevel.INFO,
                    message="No missing values"
                )
        
            self.validation_results.append(result)
            return result
        except Exception as e:
            logger.error(f"Error in _check_missing_values: {e}")
            raise
    
    def _check_ohlc_consistency(self, df: pd.DataFrame) -> ValidationResult:
        """Check OHLC price consistency"""
        # High should be >= max(open, close)
        # Low should be <= min(open, close)
        
        try:
            invalid_high = (df['high'] < df[['open', 'close']].max(axis=1)).sum()
            invalid_low = (df['low'] > df[['open', 'close']].min(axis=1)).sum()
        
            total_invalid = invalid_high + invalid_low
        
            if total_invalid > 0:
                result = ValidationResult(
                    passed=False,
                    level=ValidationLevel.CRITICAL,
                    message=f"OHLC consistency violations: {total_invalid} bars",
                    details={'invalid_high': int(invalid_high), 'invalid_low': int(invalid_low)}
                )
            else:
                result = ValidationResult(
                    passed=True,
                    level=ValidationLevel.INFO,
                    message="OHLC consistency validated"
                )
        
            self.validation_results.append(result)
            return result
        except Exception as e:
            logger.error(f"Error in _check_ohlc_consistency: {e}")
            raise
    
    def _check_price_outliers(self, df: pd.DataFrame) -> ValidationResult:
        """Detect price outliers using IQR method"""
        try:
            close_prices = df['close']
        
            Q1 = close_prices.quantile(0.25)
            Q3 = close_prices.quantile(0.75)
            IQR = Q3 - Q1
        
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR
        
            outliers = ((close_prices < lower_bound) | (close_prices > upper_bound)).sum()
            outlier_pct = (outliers / len(df)) * 100
        
            if outlier_pct > 1:  # More than 1% outliers
                result = ValidationResult(
                    passed=False,
                    level=ValidationLevel.WARNING,
                    message=f"Price outliers detected: {outlier_pct:.2f}%",
                    details={'outlier_count': int(outliers), 'bounds': (float(lower_bound), float(upper_bound))}
                )
            else:
                result = ValidationResult(
                    passed=True,
                    level=ValidationLevel.INFO,
                    message="No significant price outliers"
                )
        
            self.validation_results.append(result)
            return result
        except Exception as e:
            logger.error(f"Error in _check_price_outliers: {e}")
            raise
    
    def _check_volume_anomalies(self, df: pd.DataFrame) -> ValidationResult:
        """Check for volume anomalies"""
        try:
            volumes = df['volume']
        
            # Check for zero volume
            zero_volume = (volumes == 0).sum()
        
            # Check for volume spikes
            volume_mean = volumes.mean()
            volume_std = volumes.std()
            volume_spikes = (volumes > volume_mean + 5 * volume_std).sum()
        
            if zero_volume > len(df) * 0.1:  # More than 10% zero volume
                result = ValidationResult(
                    passed=False,
                    level=ValidationLevel.ERROR,
                    message=f"High zero volume bars: {zero_volume}",
                    details={'zero_volume_count': int(zero_volume)}
                )
            elif volume_spikes > 0:
                result = ValidationResult(
                    passed=True,
                    level=ValidationLevel.WARNING,
                    message=f"Volume spikes detected: {volume_spikes}",
                    details={'spike_count': int(volume_spikes)}
                )
            else:
                result = ValidationResult(
                    passed=True,
                    level=ValidationLevel.INFO,
                    message="Volume data looks normal"
                )
        
            self.validation_results.append(result)
            return result
        except Exception as e:
            logger.error(f"Error in _check_volume_anomalies: {e}")
            raise
    
    def _check_data_gaps(self, df: pd.DataFrame) -> ValidationResult:
        """Check for gaps in time series"""
        try:
            if not isinstance(df.index, pd.DatetimeIndex):
                result = ValidationResult(
                    passed=True,
                    level=ValidationLevel.WARNING,
                    message="Cannot check gaps: index is not datetime"
                )
                self.validation_results.append(result)
                return result
        
            # Calculate expected frequency
            time_diffs = df.index.to_series().diff()
            median_diff = time_diffs.median()
        
            # Find gaps (more than 2x median)
            gaps = time_diffs > (median_diff * 2)
            gap_count = gaps.sum()
        
            if gap_count > 0:
                result = ValidationResult(
                    passed=False,
                    level=ValidationLevel.WARNING,
                    message=f"Data gaps detected: {gap_count}",
                    details={'gap_count': int(gap_count), 'median_interval': str(median_diff)}
                )
            else:
                result = ValidationResult(
                    passed=True,
                    level=ValidationLevel.INFO,
                    message="No data gaps detected"
                )
        
            self.validation_results.append(result)
            return result
        except Exception as e:
            logger.error(f"Error in _check_data_gaps: {e}")
            raise
    
    def _check_timestamp_order(self, df: pd.DataFrame) -> ValidationResult:
        """Check if timestamps are in order"""
        try:
            if not isinstance(df.index, pd.DatetimeIndex):
                result = ValidationResult(
                    passed=True,
                    level=ValidationLevel.WARNING,
                    message="Cannot check order: index is not datetime"
                )
                self.validation_results.append(result)
                return result
        
            is_sorted = df.index.is_monotonic_increasing
        
            if not is_sorted:
                result = ValidationResult(
                    passed=False,
                    level=ValidationLevel.CRITICAL,
                    message="Timestamps are not in order",
                    details={'is_sorted': is_sorted}
                )
            else:
                result = ValidationResult(
                    passed=True,
                    level=ValidationLevel.INFO,
                    message="Timestamps are properly ordered"
                )
        
            self.validation_results.append(result)
            return result
        except Exception as e:
            logger.error(f"Error in _check_timestamp_order: {e}")
            raise
    
    def _check_zero_values(self, df: pd.DataFrame) -> ValidationResult:
        """Check for zero values in OHLC"""
        try:
            zero_counts = {
                'open': (df['open'] == 0).sum(),
                'high': (df['high'] == 0).sum(),
                'low': (df['low'] == 0).sum(),
                'close': (df['close'] == 0).sum()
            }
        
            total_zeros = sum(zero_counts.values())
        
            if total_zeros > 0:
                result = ValidationResult(
                    passed=False,
                    level=ValidationLevel.ERROR,
                    message=f"Zero values in OHLC: {total_zeros}",
                    details=zero_counts
                )
            else:
                result = ValidationResult(
                    passed=True,
                    level=ValidationLevel.INFO,
                    message="No zero values in OHLC"
                )
        
            self.validation_results.append(result)
            return result
        except Exception as e:
            logger.error(f"Error in _check_zero_values: {e}")
            raise
    
    def _check_negative_values(self, df: pd.DataFrame) -> ValidationResult:
        """Check for negative values"""
        try:
            negative_counts = {
                'open': (df['open'] < 0).sum(),
                'high': (df['high'] < 0).sum(),
                'low': (df['low'] < 0).sum(),
                'close': (df['close'] < 0).sum(),
                'volume': (df['volume'] < 0).sum()
            }
        
            total_negative = sum(negative_counts.values())
        
            if total_negative > 0:
                result = ValidationResult(
                    passed=False,
                    level=ValidationLevel.CRITICAL,
                    message=f"Negative values detected: {total_negative}",
                    details=negative_counts
                )
            else:
                result = ValidationResult(
                    passed=True,
                    level=ValidationLevel.INFO,
                    message="No negative values"
                )
        
            self.validation_results.append(result)
            return result
        except Exception as e:
            logger.error(f"Error in _check_negative_values: {e}")
            raise
    
    def get_validation_summary(self) -> Dict:
        """Get summary of validation results"""
        return {
            'total_checks': len(self.validation_results),
            'passed': sum(1 for v in self.validation_results if v.passed),
            'failed': sum(1 for v in self.validation_results if not v.passed),
            'critical': sum(1 for v in self.validation_results if v.level == ValidationLevel.CRITICAL),
            'errors': sum(1 for v in self.validation_results if v.level == ValidationLevel.ERROR),
            'warnings': sum(1 for v in self.validation_results if v.level == ValidationLevel.WARNING),
            'results': [
                {
                    'passed': v.passed,
                    'level': v.level.value,
                    'message': v.message,
                    'details': v.details
                }
                for v in self.validation_results
            ]
        }


# Export
__all__ = ['DataQualityValidator', 'ValidationResult', 'ValidationLevel']
