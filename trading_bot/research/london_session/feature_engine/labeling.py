"""
Triple-Barrier Event Labeling and Meta-Labeling for London Session.
Applies Marcos Lopez de Prado's triple barrier method with:
- Volatility-dependent take-profit and stop-loss barriers
- Maximum holding period horizon (vertical barrier)
- Realistic transaction costs (spreads, slippage drag, commissions)
- Meta-labeling for secondary sizing/filtering models (whether trade is net profitable).
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple


class TripleBarrierLabeler:
    """
    Computes triple-barrier outcomes and meta-labels on intraday session data.
    """

    def __init__(
        self,
        volatility_col: str = "volatility_5m",
        tp_multiple: float = 2.0,
        sl_multiple: float = 1.0,
        max_horizon_bars: int = 18,
        cost_drag_pips: float = 1.5,
        pip_size: float = 0.0001
    ) -> None:
        self.volatility_col = volatility_col
        self.tp_multiple = tp_multiple
        self.sl_multiple = sl_multiple
        self.max_horizon_bars = max_horizon_bars
        self.cost_drag_pips = cost_drag_pips
        self.pip_size = pip_size

    def compute_labels(
        self,
        df: pd.DataFrame,
        signal_col: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Applies triple barrier labeling.
        If signal_col is provided (e.g. +1 for long, -1 for short), barriers are evaluated
        in the signal direction. Otherwise, directional barriers are evaluated for both directions.
        Returns DataFrame with:
        - 'barrier_hit': +1 (TP), -1 (SL), 0 (Vertical horizon / timeout)
        - 'gross_return': Price change at barrier exit
        - 'net_return': Price change minus estimated transaction cost
        - 'meta_label': 1 if net_return > 0 else 0
        """
        labeled_df = df.copy()
        n = len(labeled_df)

        closes = labeled_df["close"].values
        highs = labeled_df["high"].values
        lows = labeled_df["low"].values

        # Dynamic daily volatility estimate
        if self.volatility_col in labeled_df.columns:
            vols = labeled_df[self.volatility_col].values
        else:
            vols = np.full(n, 0.001)

        # Baseline directional signals if not specified
        if signal_col and signal_col in labeled_df.columns:
            signals = labeled_df[signal_col].values
        else:
            # Default to sign of liquidity_sweep_signal or displacement
            if "liquidity_sweep_signal" in labeled_df.columns:
                signals = np.sign(labeled_df["liquidity_sweep_signal"].values)
            else:
                signals = np.ones(n)

        cost_fraction = self.cost_drag_pips * self.pip_size

        barrier_hit = np.zeros(n, dtype=int)
        gross_returns = np.zeros(n, dtype=float)
        net_returns = np.zeros(n, dtype=float)
        exit_bars = np.zeros(n, dtype=int)

        for i in range(n - self.max_horizon_bars):
            sig = signals[i]
            if sig == 0:
                continue

            entry_px = closes[i]
            vol = max(vols[i], 0.0002)

            tp_dist = vol * self.tp_multiple
            sl_dist = vol * self.sl_multiple

            hit = 0
            exit_px = entry_px
            bars_held = self.max_horizon_bars

            for step in range(1, self.max_horizon_bars + 1):
                idx = i + step
                curr_high = highs[idx]
                curr_low = lows[idx]

                if sig > 0: # LONG
                    if curr_high >= (entry_px + tp_dist):
                        hit = 1
                        exit_px = entry_px + tp_dist
                        bars_held = step
                        break
                    elif curr_low <= (entry_px - sl_dist):
                        hit = -1
                        exit_px = entry_px - sl_dist
                        bars_held = step
                        break
                elif sig < 0: # SHORT
                    if curr_low <= (entry_px - tp_dist):
                        hit = 1 # Profitable short
                        exit_px = entry_px - tp_dist
                        bars_held = step
                        break
                    elif curr_high >= (entry_px + sl_dist):
                        hit = -1 # Stopped out short
                        exit_px = entry_px + sl_dist
                        bars_held = step
                        break

            # Vertical barrier exit if neither touched
            if hit == 0:
                exit_px = closes[i + self.max_horizon_bars]

            gross_ret = (exit_px - entry_px) / entry_px if sig > 0 else (entry_px - exit_px) / entry_px
            net_ret = gross_ret - cost_fraction

            barrier_hit[i] = hit
            gross_returns[i] = gross_ret
            net_returns[i] = net_ret
            exit_bars[i] = bars_held

        labeled_df["barrier_hit"] = barrier_hit
        labeled_df["gross_return"] = gross_returns
        labeled_df["net_return"] = net_returns
        labeled_df["bars_held"] = exit_bars
        # Meta-label: 1 if trade made money after drag, 0 otherwise
        labeled_df["meta_label"] = (net_returns > 0.0).astype(int)

        return labeled_df
