"""
Data Quality Validation for OHLCV data.
Ensures data integrity before trading decisions.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class DataQualityValidator:
    """Comprehensive data quality validation for trading data."""
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize data quality validator.
        
        Args:
            strict_mode: If True, raise errors on validation failures
        """
        try:
            self.strict_mode = strict_mode
            self.validation_results = []
        
            logger.info(f"Data quality validator initialized (strict: {strict_mode})")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate_ohlcv(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate OHLCV data integrity.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            (is_valid, list_of_errors)
        """
        try:
            errors = []
        
            # Check required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                errors.append(f"Missing columns: {missing_cols}")
        
            if errors:
                return False, errors
        
            # Check for NaN values
            nan_counts = df[required_cols].isna().sum()
            if nan_counts.any():
                errors.append(f"NaN values found: {nan_counts[nan_counts > 0].to_dict()}")
        
            # Check for infinite values
            inf_counts = np.isinf(df[required_cols]).sum()
            if inf_counts.any():
                errors.append(f"Infinite values found: {inf_counts[inf_counts > 0].to_dict()}")
        
            # Check for negative prices
            for col in ['open', 'high', 'low', 'close']:
                if (df[col] < 0).any():
                    errors.append(f"Negative prices in {col}")
        
            # Check for negative volume
            if (df['volume'] < 0).any():
                errors.append("Negative volume detected")
        
            # Check OHLC relationships
            if not (df['high'] >= df['low']).all():
                errors.append("High < Low detected")
        
            if not (df['high'] >= df['open']).all():
                errors.append("High < Open detected")
        
            if not (df['high'] >= df['close']).all():
                errors.append("High < Close detected")
        
            if not (df['low'] <= df['open']).all():
                errors.append("Low > Open detected")
        
            if not (df['low'] <= df['close']).all():
                errors.append("Low > Close detected")
        
            # Check for zero prices
            for col in ['open', 'high', 'low', 'close']:
                if (df[col] == 0).any():
                    errors.append(f"Zero prices in {col}")
        
            # Check for duplicate timestamps
            if 'timestamp' in df.columns:
                if df['timestamp'].duplicated().any():
                    errors.append("Duplicate timestamps detected")
        
            # Check for gaps in time series
            if 'timestamp' in df.columns and len(df) > 1:
                time_diffs = df['timestamp'].diff()
                if time_diffs.std() / time_diffs.mean() > 0.5:  # High variance
                    errors.append("Irregular time intervals detected")
        
            # Check for outliers (price spikes)
            returns = df['close'].pct_change()
            if (abs(returns) > 0.2).any():  # 20% single-bar move
                outlier_count = (abs(returns) > 0.2).sum()
                errors.append(f"Extreme price movements detected: {outlier_count} bars")
        
            # Check volume outliers
            if len(df) > 20:
                volume_zscore = (df['volume'] - df['volume'].mean()) / df['volume'].std()
                if (abs(volume_zscore) > 5).any():
                    errors.append("Extreme volume outliers detected")
        
            is_valid = len(errors) == 0
        
            if not is_valid:
                logger.warning(f"Data quality validation failed: {len(errors)} errors")
                for error in errors:
                    logger.warning(f"  - {error}")
            
                if self.strict_mode:
                    raise ValueError(f"Data quality validation failed: {errors}")
            else:
                logger.success("Data quality validation passed")
        
            return is_valid, errors
        except Exception as e:
            logger.error(f"Error in validate_ohlcv: {e}")
            raise
    
    def fix_common_issues(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Attempt to fix common data quality issues.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Cleaned DataFrame
        """
        try:
            df = df.copy()
        
            # Forward fill NaN values
            df = df.fillna(method='ffill')
        
            # Remove infinite values
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.fillna(method='ffill')
        
            # Fix OHLC relationships
            df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
            df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
        
            # Remove duplicate timestamps
            if 'timestamp' in df.columns:
                df = df.drop_duplicates(subset=['timestamp'], keep='first')
        
            # Cap extreme returns
            returns = df['close'].pct_change()
            extreme_mask = abs(returns) > 0.2
            if extreme_mask.any():
                logger.warning(f"Capping {extreme_mask.sum()} extreme returns")
                # Replace with median return
                median_return = returns.median()
                df.loc[extreme_mask, 'close'] = df.loc[extreme_mask, 'close'].shift(1) * (1 + median_return)
        
            logger.info("Data quality fixes applied")
            return df
        except Exception as e:
            logger.error(f"Error in fix_common_issues: {e}")
            raise
    
    def get_data_statistics(self, df: pd.DataFrame) -> Dict:
        """Get data quality statistics."""
        try:
            stats = {
                'total_rows': len(df),
                'date_range': (df.index[0], df.index[-1]) if len(df) > 0 else (None, None),
                'missing_values': df.isna().sum().to_dict(),
                'price_range': {
                    'min': float(df['close'].min()),
                    'max': float(df['close'].max()),
                    'mean': float(df['close'].mean())
                },
                'volume_stats': {
                    'min': float(df['volume'].min()),
                    'max': float(df['volume'].max()),
                    'mean': float(df['volume'].mean())
                }
            }
        
            return stats
        except Exception as e:
            logger.error(f"Error in get_data_statistics: {e}")
            raise


class DataAnomalyDetector:
    """Detect anomalies in trading data."""
    
    def __init__(self, sensitivity: float = 3.0):
        """
        Initialize anomaly detector.
        
        Args:
            sensitivity: Z-score threshold for anomalies
        """
        try:
            self.sensitivity = sensitivity
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def detect_price_anomalies(self, df: pd.DataFrame) -> pd.Series:
        """Detect price anomalies using Z-score."""
        try:
            returns = df['close'].pct_change()
            z_scores = (returns - returns.mean()) / returns.std()
        
            anomalies = abs(z_scores) > self.sensitivity
        
            if anomalies.any():
                logger.warning(f"Detected {anomalies.sum()} price anomalies")
        
            return anomalies
        except Exception as e:
            logger.error(f"Error in detect_price_anomalies: {e}")
            raise
    
    def detect_volume_anomalies(self, df: pd.DataFrame) -> pd.Series:
        """Detect volume anomalies."""
        try:
            log_volume = np.log(df['volume'] + 1)
            z_scores = (log_volume - log_volume.mean()) / log_volume.std()
        
            anomalies = abs(z_scores) > self.sensitivity
        
            if anomalies.any():
                logger.warning(f"Detected {anomalies.sum()} volume anomalies")
        
            return anomalies
        except Exception as e:
            logger.error(f"Error in detect_volume_anomalies: {e}")
            raise
