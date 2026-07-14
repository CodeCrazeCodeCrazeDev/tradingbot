"""
Market Replay Engine - AlphaAlgo UCA V5
Implements grounded historical data replay with dataset splitting.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class DatasetSplit(Enum):
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"
    PAPER = "paper"
    LIVE = "live"

class MarketReplay:
    """
    Grounded market replay engine that enforces dataset separation
    and realistic execution modeling.
    """

    def __init__(self,
                 data: Dict[str, pd.DataFrame],
                 split_ratios: Dict[DatasetSplit, float] = None,
                 initial_capital: float = 100000.0):
        self.data = data
        self.initial_capital = initial_capital
        self.split_ratios = split_ratios or {
            DatasetSplit.TRAIN: 0.7,
            DatasetSplit.VALIDATION: 0.15,
            DatasetSplit.TEST: 0.15
        }
        self._validate_splits()
        self.splits = self._perform_splits()

    def _validate_splits(self):
        total = sum(self.split_ratios.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Split ratios must sum to 1.0, got {total}")

    def _perform_splits(self) -> Dict[DatasetSplit, Dict[str, pd.DataFrame]]:
        splits = {split: {} for split in DatasetSplit}

        for symbol, df in self.data.items():
            n = len(df)
            train_end = int(n * self.split_ratios.get(DatasetSplit.TRAIN, 0))
            val_end = train_end + int(n * self.split_ratios.get(DatasetSplit.VALIDATION, 0))

            splits[DatasetSplit.TRAIN][symbol] = df.iloc[:train_end]
            splits[DatasetSplit.VALIDATION][symbol] = df.iloc[train_end:val_end]
            splits[DatasetSplit.TEST][symbol] = df.iloc[val_end:]

        return splits

    def get_data(self, split: DatasetSplit) -> Dict[str, pd.DataFrame]:
        """Retrieve data for a specific split."""
        return self.splits.get(split, {})

    def get_market_state(self, symbol: str, timestamp: datetime, split: DatasetSplit) -> Optional[Dict]:
        """Realistic market state snapshot."""
        df = self.splits[split].get(symbol)
        if df is None: return None

        # Grounding: Use actual historical index
        mask = df.index <= timestamp
        if not any(mask): return None

        row = df.loc[mask].iloc[-1]

        # Model realistic spreads and volatility
        volatility = (row['high'] - row['low']) / row['close']
        base_spread = 0.0002 # 2 pips
        variable_spread = base_spread + (volatility * 0.1)

        return {
            'price': row['close'],
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'volume': row['volume'],
            'spread': variable_spread,
            'volatility': volatility,
            'timestamp': row.name
        }
