"""
London Session Microstructure Feature Engine.
Computes high-fidelity features specifically for London trading session behaviors,
market structure breaks, Asian range sweeps, displacement, order flow replenishment,
and information-theoretic / causal metrics.
"""

import zoneinfo
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple


class LondonFeatureEngine:
    """
    Computes indicators and microstructure states specifically for the London session:
    - Opening auction behavior
    - Asian Session High/Low levels and Range
    - Liquidity sweeps of Asian boundaries before directional expansion
    - Market Structure Shifts (MSS) & Displacement
    - Volatility regimes (expansion vs. contraction)
    - Microstructure imbalances, spread dynamics, and order-flow replenishment
    - Cross-asset relationships (e.g. DXY lead-lag)
    - Transfer Entropy, Conditional Mutual Information, and Backdoor do-calculus.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        # Session times in Europe/London local hours
        self.asia_start_hour = self.config.get("asia_start_hour", 0.0)
        self.asia_end_hour = self.config.get("asia_end_hour", 7.0)
        self.london_open_start = self.config.get("london_open_start", 7.5)
        self.london_open_end = self.config.get("london_open_end", 9.5)
        self.london_killzone_start = self.config.get("london_killzone_start", 8.0)
        self.london_killzone_end = self.config.get("london_killzone_end", 11.0)
        self.overlap_start = self.config.get("overlap_start", 13.0)
        self.overlap_end = self.config.get("overlap_end", 16.5)
        self.london_close_start = self.config.get("london_close_start", 15.5)
        self.london_close_end = self.config.get("london_close_end", 16.5)

    def compute_session_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes high-fidelity features on historical intraday DataFrame.
        Expected columns: open, high, low, close, volume.
        Optional columns: spread, bid_qty, ask_qty, dxy_close.
        """
        features_df = df.copy()

        # Ensure index is datetime
        if not isinstance(features_df.index, pd.DatetimeIndex):
            features_df.index = pd.to_datetime(features_df.index)

        # Ensure UTC timezone
        if features_df.index.tz is None:
            features_df.index = features_df.index.tz_localize("UTC")
        else:
            features_df.index = features_df.index.tz_convert("UTC")

        # Compute Europe/London hour to accurately respect BST/GMT daylight saving transitions
        london_tz = zoneinfo.ZoneInfo("Europe/London")
        london_index = features_df.index.tz_convert(london_tz)
        hours = london_index.hour + london_index.minute / 60.0
        features_df["london_hour"] = hours

        # 1. Base log returns & multi-window volatility
        features_df["log_ret"] = np.log(features_df["close"] / features_df["close"].shift(1))
        features_df["volatility_5m"] = features_df["log_ret"].rolling(12).std() * np.sqrt(288)
        features_df["volatility_1h"] = features_df["log_ret"].rolling(12).std()
        features_df["volatility_4h"] = features_df["log_ret"].rolling(48).std()
        features_df["vol_ratio_5m_4h"] = features_df["volatility_5m"] / (features_df["volatility_4h"] + 1e-8)

        # 2. Extract Session Regime Indicators (in local London time)
        features_df["is_asia_session"] = ((hours >= self.asia_start_hour) & (hours < self.asia_end_hour)).astype(int)
        features_df["is_london_open"] = ((hours >= self.london_open_start) & (hours <= self.london_open_end)).astype(int)
        features_df["is_london_killzone"] = ((hours >= self.london_killzone_start) & (hours <= self.london_killzone_end)).astype(int)
        features_df["is_london_close"] = ((hours >= self.london_close_start) & (hours <= self.london_close_end)).astype(int)
        features_df["is_lnd_ny_overlap"] = ((hours >= self.overlap_start) & (hours <= self.overlap_end)).astype(int)

        # 3. Asian Session Range Calculation (00:00 - 07:00 London)
        # We compute rolling daily Asian High and Low
        features_df["date"] = london_index.date
        asia_mask = features_df["is_asia_session"] == 1

        asia_highs = features_df.loc[asia_mask].groupby("date")["high"].max()
        asia_lows = features_df.loc[asia_mask].groupby("date")["low"].min()

        features_df["asia_high"] = features_df["date"].map(asia_highs)
        features_df["asia_low"] = features_df["date"].map(asia_lows)
        features_df["asia_range"] = features_df["asia_high"] - features_df["asia_low"]

        # Forward fill for intraday bars after Asia closes
        features_df["asia_high"] = features_df["asia_high"].ffill()
        features_df["asia_low"] = features_df["asia_low"].ffill()
        features_df["asia_range"] = features_df["asia_range"].ffill()

        # 4. Asian Range Sweeps (Judas Swing / Liquidity Sweep)
        # Price spikes above Asia High or below Asia Low and rejects back inside
        sweep_high = (features_df["high"] > features_df["asia_high"]) & (features_df["close"] < features_df["asia_high"])
        sweep_low = (features_df["low"] < features_df["asia_low"]) & (features_df["close"] > features_df["asia_low"])
        features_df["asia_high_sweep"] = sweep_high.astype(float)
        features_df["asia_low_sweep"] = sweep_low.astype(float)
        features_df["liquidity_sweep_signal"] = features_df["asia_high_sweep"] - features_df["asia_low_sweep"]

        # 5. Market Structure Shift (MSS) and Displacement
        # Displacement: exceptionally large body candle relative to ATR
        candle_body = (features_df["close"] - features_df["open"]).abs()
        atr_14 = (features_df["high"] - features_df["low"]).rolling(14).mean()
        features_df["is_displacement"] = (candle_body > (atr_14 * 1.5)).astype(int)

        # Directional displacement
        features_df["directional_displacement"] = np.where(
            features_df["close"] > features_df["open"],
            features_df["is_displacement"],
            np.where(features_df["close"] < features_df["open"], -features_df["is_displacement"], 0)
        )

        # 6. Liquidity Migration from Asia to London (Cumulative Volume and Volatility shifts)
        features_df["asia_vol_proxy"] = features_df["volume"].rolling(48).mean()  # 4 hours
        features_df["london_vol_proxy"] = features_df["volume"].rolling(12).mean() # 1 hour
        features_df["liquidity_migration_ratio"] = features_df["london_vol_proxy"] / (features_df["asia_vol_proxy"] + 1e-8)

        # 7. Microstructure Order Flow Imbalance (OFI) & Replenishment
        if "bid_qty" in features_df.columns and "ask_qty" in features_df.columns:
            features_df["ofi"] = (features_df["bid_qty"] - features_df["ask_qty"]) / (features_df["bid_qty"] + features_df["ask_qty"] + 1e-8)
        else:
            price_change = features_df["close"].diff()
            features_df["ofi"] = np.where(price_change > 0, features_df["volume"], np.where(price_change < 0, -features_df["volume"], 0)) / (features_df["volume"] + 1e-8)

        features_df["ofi_ma_6"] = features_df["ofi"].rolling(6).mean()

        # 8. Spread Dynamics & Execution Quality
        if "spread" in features_df.columns:
            features_df["spread_ma_12"] = features_df["spread"].rolling(12).mean()
            features_df["spread_zscore"] = (features_df["spread"] - features_df["spread_ma_12"]) / (features_df["spread"].rolling(12).std() + 1e-8)
        else:
            features_df["spread_zscore"] = 0.0

        # 9. Clean intermediate date column
        if "date" in features_df.columns:
            features_df = features_df.drop(columns=["date"])

        return features_df.dropna()

    def estimate_transfer_entropy(self, source: pd.Series, target: pd.Series, lag: int = 1, bins: int = 5) -> float:
        """
        Estimates Transfer Entropy (TE) from source series to target series.
        TE measures directional information flow: H(Y_t | Y_{t-1}) - H(Y_t | Y_{t-1}, X_{t-lag}).
        Returns value in bits (>= 0).
        """
        aligned = pd.concat([source, target], axis=1).dropna()
        if len(aligned) < (lag + 10):
            return 0.0

        x = pd.qcut(aligned.iloc[:, 0], q=bins, labels=False, duplicates="drop").values
        y = pd.qcut(aligned.iloc[:, 1], q=bins, labels=False, duplicates="drop").values

        y_t = y[lag:]
        y_lag = y[:-lag]
        x_lag = x[:-lag]

        p_y_joint = self._compute_joint_prob_2d(y_t, y_lag, bins)
        h_y_joint = -np.sum(p_y_joint * np.log2(p_y_joint + 1e-12))

        p_y_lag = self._compute_prob_1d(y_lag, bins)
        h_y_lag = -np.sum(p_y_lag * np.log2(p_y_lag + 1e-12))
        h_cond_base = h_y_joint - h_y_lag

        p_3d = self._compute_joint_prob_3d(y_t, y_lag, x_lag, bins)
        h_3d = -np.sum(p_3d * np.log2(p_3d + 1e-12))

        p_2d_cond = self._compute_joint_prob_2d(y_lag, x_lag, bins)
        h_2d_cond = -np.sum(p_2d_cond * np.log2(p_2d_cond + 1e-12))
        h_cond_full = h_3d - h_2d_cond

        te = max(0.0, h_cond_base - h_cond_full)
        return float(te)

    def estimate_conditional_mutual_information(self, x: pd.Series, y: pd.Series, z: pd.Series, bins: int = 5) -> float:
        """
        Estimates Conditional Mutual Information (CMI): I(X; Y | Z) = H(X, Z) + H(Y, Z) - H(X, Y, Z) - H(Z).
        """
        aligned = pd.concat([x, y, z], axis=1).dropna()
        if len(aligned) < 15:
            return 0.0

        xd = pd.qcut(aligned.iloc[:, 0], q=bins, labels=False, duplicates="drop").values
        yd = pd.qcut(aligned.iloc[:, 1], q=bins, labels=False, duplicates="drop").values
        zd = pd.qcut(aligned.iloc[:, 2], q=bins, labels=False, duplicates="drop").values

        p_xz = self._compute_joint_prob_2d(xd, zd, bins)
        h_xz = -np.sum(p_xz * np.log2(p_xz + 1e-12))

        p_yz = self._compute_joint_prob_2d(yd, zd, bins)
        h_yz = -np.sum(p_yz * np.log2(p_yz + 1e-12))

        p_xyz = self._compute_joint_prob_3d(xd, yd, zd, bins)
        h_xyz = -np.sum(p_xyz * np.log2(p_xyz + 1e-12))

        p_z = self._compute_prob_1d(zd, bins)
        h_z = -np.sum(p_z * np.log2(p_z + 1e-12))

        cmi = max(0.0, h_xz + h_yz - h_xyz - h_z)
        return float(cmi)

    def estimate_causal_do_calculus(self, cause: pd.Series, effect: pd.Series, confounder: pd.Series, bins: int = 3) -> Dict[str, Any]:
        """
        Estimates interventional causal effect using backdoor adjustment: P(Y | do(X)).
        """
        aligned = pd.concat([cause, effect, confounder], axis=1).dropna()
        if len(aligned) < 20:
            return {"ace": 0.0, "p_do": {}}

        x = pd.qcut(aligned.iloc[:, 0], q=bins, labels=False, duplicates="drop").values
        y = pd.qcut(aligned.iloc[:, 1], q=bins, labels=False, duplicates="drop").values
        z = pd.qcut(aligned.iloc[:, 2], q=bins, labels=False, duplicates="drop").values

        u_x = np.unique(x)
        u_y = np.unique(y)
        u_z = np.unique(z)

        p_z = {}
        for state_z in u_z:
            p_z[state_z] = np.mean(z == state_z)

        p_do = {}
        for state_x in u_x:
            for state_y in u_y:
                p_y_given_do = 0.0
                for state_z in u_z:
                    sub_xz = (x == state_x) & (z == state_z)
                    if np.sum(sub_xz) > 0:
                        p_cond_y = np.mean(y[sub_xz] == state_y)
                        p_y_given_do += p_cond_y * p_z[state_z]
                p_do[(int(state_x), int(state_y))] = float(p_y_given_do)

        ace = 0.0
        if len(u_x) >= 2 and len(u_y) >= 2:
            max_x = int(np.max(u_x))
            min_x = int(np.min(u_x))
            high_y = int(np.max(u_y))
            p_y_high_do_max = p_do.get((max_x, high_y), 0.0)
            p_y_high_do_min = p_do.get((min_x, high_y), 0.0)
            ace = float(p_y_high_do_max - p_y_high_do_min)

        return {
            "ace": ace,
            "p_do": {f"do(X={k[0]},Y={k[1]})": v for k, v in p_do.items()}
        }

    def _compute_prob_1d(self, arr: np.ndarray, num_bins: int) -> np.ndarray:
        counts = np.bincount(arr, minlength=num_bins)
        return counts / (np.sum(counts) + 1e-12)

    def _compute_joint_prob_2d(self, a: np.ndarray, b: np.ndarray, num_bins: int) -> np.ndarray:
        joint_hist, _, _ = np.histogram2d(a, b, bins=(num_bins, num_bins))
        return joint_hist / (np.sum(joint_hist) + 1e-12)

    def _compute_joint_prob_3d(self, a: np.ndarray, b: np.ndarray, c: np.ndarray, num_bins: int) -> np.ndarray:
        indices = a * (num_bins**2) + b * num_bins + c
        counts = np.bincount(indices, minlength=num_bins**3)
        return counts / (np.sum(counts) + 1e-12)
