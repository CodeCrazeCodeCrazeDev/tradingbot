from pathlib import Path
import importlib.util

import numpy as np
import pandas as pd


def load_market_analysis_module():
    module_path = Path(__file__).parent / "trading_bot" / "elite_system" / "market_analysis.py"
    spec = importlib.util.spec_from_file_location("elite_market_analysis_local", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def synthetic_market_data(rows: int = 240) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    idx = pd.date_range("2024-01-01", periods=rows, freq="h")
    base = 1.10 + np.cumsum(rng.normal(0, 0.0008, size=rows))
    open_ = base + rng.normal(0, 0.0002, size=rows)
    close = base + rng.normal(0, 0.0002, size=rows)
    high = np.maximum(open_, close) + np.abs(rng.normal(0, 0.0003, size=rows))
    low = np.minimum(open_, close) - np.abs(rng.normal(0, 0.0003, size=rows))
    volume = rng.integers(500, 2500, size=rows)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=idx,
    )


def main() -> None:
    module = load_market_analysis_module()
    EliteMarketAnalyzer = module.EliteMarketAnalyzer
    TimeFrame = module.TimeFrame

    analyzer = EliteMarketAnalyzer(symbol="EURUSD", primary_timeframe=TimeFrame.H1)
    analyzer.load_data(TimeFrame.H1, synthetic_market_data())

    pa = analyzer.analyze_price_action(TimeFrame.H1)
    direction = pa["trend"].get("direction", "neutral")
    strength = pa["trend"].get("strength", "unknown")
    confidence = 0.80 if strength == "strong" else 0.60

    print(f"Direction: {direction}")
    print(f"Strength: {strength}")
    print(f"Confidence: {confidence:.2f}")


if __name__ == "__main__":
    main()
