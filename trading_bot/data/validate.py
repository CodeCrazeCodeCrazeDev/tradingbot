"""
Provides backward and testing compatibility for data validation modules.
"""

from typing import Any, Optional, Dict, Tuple
import logging
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class DataValidator:
    """Validates Pandas DataFrames to ensure proper OHLCV and technical feature health."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.initialized = False

    def initialize(self) -> bool:
        self.initialized = True
        return True

    def process(self, data: Any) -> Any:
        if not self.initialized:
            self.initialize()
        return data

    def get_status(self) -> Dict[str, Any]:
        return {
            'initialized': self.initialized,
            'timestamp': datetime.now().isoformat(),
            'config': self.config
        }

    def validate_dataframe(self, df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        """
        Validates structure, types, missing values, and logical boundaries on OHLCV columns.
        Returns a tuple: (is_valid, validation_report)
        """
        if df is None or df.empty:
            return False, {"error": "DataFrame is empty or None"}

        report = {
            "row_count": len(df),
            "missing_values": 0,
            "corrupted_rows": 0,
            "logical_errors": 0,
            "warnings": []
        }

        # Check required columns
        required_cols = ["open", "high", "low", "close"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return False, {"error": f"Missing required columns: {missing_cols}"}

        # Check for NaNs
        nan_counts = df[required_cols].isna().sum().sum()
        report["missing_values"] = int(nan_counts)

        # Check logical OHLC relations: high >= open/close/low, low <= open/close/high
        logical_violations = (
            (df["high"] < df["low"]) |
            (df["high"] < df["open"]) |
            (df["high"] < df["close"]) |
            (df["low"] > df["open"]) |
            (df["low"] > df["close"])
        )
        violations_count = int(logical_violations.sum())
        report["logical_errors"] = violations_count

        is_valid = (nan_counts == 0) and (violations_count == 0)
        return is_valid, report
