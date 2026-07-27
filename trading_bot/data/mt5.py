import pandas as pd
import numpy as np

class MT5Interface:
    """Interface for MetaTrader 5 (MT5)."""
    def __init__(self, *args, **kwargs):
        pass

    def get_rates(self, symbol: str, timeframe: str, bars: int) -> pd.DataFrame:
        """Returns dummy rates DataFrame for the given symbol."""
        dates = pd.date_range(end=pd.Timestamp.now(), periods=bars, freq='h')
        return pd.DataFrame({
            'open': np.random.uniform(1.0, 1.2, bars),
            'high': np.random.uniform(1.2, 1.3, bars),
            'low': np.random.uniform(0.9, 1.0, bars),
            'close': np.random.uniform(1.0, 1.2, bars),
            'volume': np.random.randint(100, 1000, bars)
        }, index=dates)
