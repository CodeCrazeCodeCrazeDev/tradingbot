"""
Data Quarantine Pipeline
Implements HI-DAT-006: Data quarantine pipeline for bad bars

Isolates bad data from production pipeline to prevent contamination.
Critical for maintaining data quality.
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, List
from datetime import datetime
from pathlib import Path
import numpy
import pandas

logger = logging.getLogger(__name__)


class DataQuarantine:
    """
    Quarantines bad data and maintains clean pipeline
    
    Features:
    - NaN/Inf detection
    - Statistical outlier detection
    - Schema validation
    - Quarantine logging
    """
    
    def __init__(self, quarantine_dir: str = "quarantine", z_score_threshold: float = 5.0):
        self.quarantine_dir = Path(quarantine_dir)
        self.quarantine_dir.mkdir(exist_ok=True)
        self.z_score_threshold = z_score_threshold
        
        self.stats = {
            'total_processed': 0,
            'quarantined': 0,
            'clean': 0
        }
        
        logger.info(f"Data Quarantine initialized (dir: {quarantine_dir})")
    
    def validate_and_quarantine(self, data: pd.DataFrame, 
                                symbol: str = "UNKNOWN") -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Separate clean and bad data
        
        Args:
            data: Input DataFrame
            symbol: Trading symbol for logging
        
        Returns:
            Tuple of (clean_data, quarantined_data)
        """
        self.stats['total_processed'] += len(data)
        
        bad_mask = pd.Series(False, index=data.index)
        
        # Check 1: NaN values
        nan_mask = data.isnull().any(axis=1)
        if nan_mask.any():
            logger.warning(f"Found {nan_mask.sum()} rows with NaN for {symbol}")
            bad_mask |= nan_mask
        
        # Check 2: Infinite values
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        inf_mask = np.isinf(data[numeric_cols]).any(axis=1)
        if inf_mask.any():
            logger.warning(f"Found {inf_mask.sum()} rows with Inf for {symbol}")
            bad_mask |= inf_mask
        
        # Check 3: Statistical outliers (Z-score method)
        for col in numeric_cols:
            if col in data.columns and not data[col].empty:
                z_scores = np.abs((data[col] - data[col].mean()) / (data[col].std() + 1e-8))
                outlier_mask = z_scores > self.z_score_threshold
                if outlier_mask.any():
                    logger.warning(f"Found {outlier_mask.sum()} outliers in {col} for {symbol}")
                    bad_mask |= outlier_mask
        
        # Check 4: OHLC consistency
        if all(col in data.columns for col in ['open', 'high', 'low', 'close']):
            ohlc_invalid = (
                (data['high'] < data['low']) |
                (data['high'] < data['open']) |
                (data['high'] < data['close']) |
                (data['low'] > data['open']) |
                (data['low'] > data['close'])
            )
            if ohlc_invalid.any():
                logger.warning(f"Found {ohlc_invalid.sum()} OHLC inconsistencies for {symbol}")
                bad_mask |= ohlc_invalid
        
        # Separate data
        clean_data = data[~bad_mask].copy()
        quarantined_data = data[bad_mask].copy()
        
        self.stats['clean'] += len(clean_data)
        self.stats['quarantined'] += len(quarantined_data)
        
        # Log quarantined data
        if len(quarantined_data) > 0:
            self._save_quarantine(quarantined_data, symbol)
        
        logger.info(f"{symbol}: {len(clean_data)} clean, {len(quarantined_data)} quarantined")
        
        return clean_data, quarantined_data
    
    def _save_quarantine(self, data: pd.DataFrame, symbol: str):
        """Save quarantined data to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.quarantine_dir / f"{symbol}_{timestamp}.csv"
            data.to_csv(filename)
            logger.info(f"Quarantined data saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save quarantine: {e}")
    
    def get_statistics(self) -> dict:
        """Get quarantine statistics"""
        return {
            **self.stats,
            'quarantine_rate': (
                self.stats['quarantined'] / self.stats['total_processed'] * 100
                if self.stats['total_processed'] > 0 else 0
            )
        }


    def validate_data(self, data):
        """
        Validate data for quality issues
        
        Args:
            data: DataFrame or dict to validate
            
        Returns:
            tuple: (is_clean, issues) where issues is list of problems found
        """
        issues = []
        
        # Check for None/NaN values
        if hasattr(data, 'isnull'):
            if data.isnull().any().any():
                issues.append("Contains NaN values")
        
        # Check for negative prices
        if hasattr(data, 'columns') and 'price' in data.columns:
            if (data['price'] < 0).any():
                issues.append("Contains negative prices")
        
        is_clean = len(issues) == 0
        return is_clean, issues


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    quarantine = DataQuarantine()
    
    # Test data with issues
    data = pd.DataFrame({
        'open': [1.1, 1.2, np.nan, 1.4, 1.5],
        'high': [1.15, 1.25, 1.35, 1.3, 1.55],  # Row 3 has high < open
        'low': [1.05, 1.15, 1.25, 1.35, 1.45],
        'close': [1.12, np.inf, 1.32, 1.42, 1.52],
        'volume': [1000, 2000, 3000, 100000, 5000]  # Row 3 is outlier
    })
    
    clean, bad = quarantine.validate_and_quarantine(data, "EURUSD")
    logger.info(f"Clean rows: {len(clean)}")
    logger.info(f"Quarantined rows: {len(bad)}")
    logger.info(f"\nStats: {quarantine.get_statistics()}")
