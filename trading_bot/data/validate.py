import pandas as pd
from typing import Dict, Tuple, Any

class DataValidator:
    """Rigorous pre-flight data quality and integrity validator."""

    def validate_dataframe(self, df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        report = {
            "total_records": len(df),
            "bad_ticks_count": 0,
            "look_ahead_violations": 0,
            "errors": []
        }

        if df.empty:
            report["errors"].append("DataFrame is empty")
            return False, report

        # Check for bad ticks (negative values, open/high/low/close consistency)
        bad_ticks = 0
        for col in ["open", "high", "low", "close"]:
            if col in df.columns:
                if (df[col] < 0).any():
                    bad_ticks += (df[col] < 0).sum()

        if "high" in df.columns and "low" in df.columns:
            inconsistent_ticks = (df["high"] < df["low"]).sum()
            bad_ticks += inconsistent_ticks

        report["bad_ticks_count"] = int(bad_ticks)
        if bad_ticks > 0:
            report["errors"].append(f"Found {bad_ticks} bad ticks (negative prices or high < low)")

        # Check for look-ahead violations
        look_ahead_cols = []
        for col in df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in ["future", "target", "next", "lead", "prediction"]):
                look_ahead_cols.append(col)

        report["look_ahead_violations"] = len(look_ahead_cols)
        if len(look_ahead_cols) > 0:
            report["errors"].append(f"Possible look-ahead bias detected in columns: {', '.join(look_ahead_cols)}")

        is_valid = (report["bad_ticks_count"] == 0) and (report["look_ahead_violations"] == 0)
        return is_valid, report
