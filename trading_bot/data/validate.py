import pandas as pd
import numpy as np

class DataValidator:
    """Pre-flight data validator that identifies anomalies, bad ticks, and look-ahead leaks."""
    def validate_dataframe(self, df: pd.DataFrame):
        report = {
            "total_records": len(df),
            "bad_ticks_count": 0,
            "look_ahead_violations": 0,
            "errors": []
        }
        is_valid = True

        # Check for bad ticks: negative values or high < low
        bad_ticks = 0
        if "high" in df.columns and "low" in df.columns:
            bad_ticks_mask = (df["high"] < df["low"])
            for col in ["open", "high", "low", "close"]:
                if col in df.columns:
                    bad_ticks_mask = bad_ticks_mask | (df[col] < 0)
            bad_ticks = int(bad_ticks_mask.sum())

        report["bad_ticks_count"] = bad_ticks
        if bad_ticks > 0:
            is_valid = False
            report["errors"].append(f"Detected {bad_ticks} bad ticks.")

        # Check for look-ahead violations
        look_ahead_cols = [c for c in df.columns if any(k in str(c).lower() for k in ["future", "next", "leaky", "lookahead", "look_ahead"])]
        if look_ahead_cols:
            is_valid = False
            report["look_ahead_violations"] = len(look_ahead_cols)
            report["errors"].append(f"Possible look-ahead bias: {look_ahead_cols}")

        return is_valid, report
