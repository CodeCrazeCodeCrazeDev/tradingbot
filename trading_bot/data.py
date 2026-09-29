"""
MT5 Interface Mock and Data Module
"""
from typing import Any, Dict, List, Optional

class MT5Interface:
    def __init__(self, *args, **kwargs):
        pass

    def get_positions(self) -> List[Any]:
        return []

    def account_info(self) -> Optional[Any]:
        return None

    def place_order(self, *args, **kwargs) -> Optional[int]:
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class MarketDataStream:
    pass

class TimeSeriesDB:
    pass
