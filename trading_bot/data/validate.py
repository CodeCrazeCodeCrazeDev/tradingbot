"""
Data Validator class.
Provides validation and sanitization checks for historical and streaming datasets.
"""

import pandas as pd
from typing import Dict, Any, Tuple

class DataValidator:
    """Validates Pandas DataFrames to ensure proper OHLCV and technical feature health."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def validate_dataframe(self, df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        """
        Validates structure, types, missing values, and logical boundaries on OHLCV columns.
        Returns a tuple: (is_valid, validation_report)
        """
        if df is None or df.empty:
            return False, {"error": "DataFrame is empty or None", "errors": ["DataFrame is empty or None"]}

        report = {
            "row_count": len(df),
            "total_records": len(df),
            "missing_values": 0,
            "corrupted_rows": 0,
            "logical_errors": 0,
            "bad_ticks_count": 0,
            "look_ahead_violations": 0,
            "errors": [],
            "warnings": []
        }

        # Check required columns
        required_cols = ["open", "high", "low", "close"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            msg = f"Missing required columns: {missing_cols}"
            report["errors"].append(msg)
            return False, report

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
        report["bad_ticks_count"] = violations_count
        if violations_count > 0:
            report["errors"].append(f"Detected {violations_count} bad ticks/logical errors")

        # Check look-ahead bias (any column indicating future data)
        look_ahead_count = 0
        for col in df.columns:
            if "future" in col or "next" in col or "target" in col:
                look_ahead_count += 1

        report["look_ahead_violations"] = look_ahead_count
        if look_ahead_count > 0:
            report["errors"].append(f"Possible look-ahead bias: columns indicate future data")

        is_valid = (nan_counts == 0) and (violations_count == 0) and (look_ahead_count == 0)
        return is_valid, report
