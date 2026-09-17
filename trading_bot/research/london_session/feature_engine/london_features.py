"""
London Session Microstructure Feature Engine.
Computes high-fidelity features specifically for London trading session behaviors,
as well as advanced information-theoretic and causal metrics.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple


class LondonFeatureEngine:
    """
    Computes indicators and microstructure states specifically for the London session:
    - Opening auction behavior
    - Liquidity migration from Asia to London
    - Liquidity sweeps before directional expansion
    - Volatility regimes
    - Microstructure imbalances, spread dynamics, and order-flow replenishment
    - Cross-asset relationships
    - Transfer Entropy, Conditional Mutual Information, and SCM do-calculus.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        # Session times in UTC/GMT
        self.asia_end_hour = self.config.get("asia_end_hour", 7)
        self.london_start_hour = self.config.get("london_start_hour", 8)
        self.london_end_hour = self.config.get("london_end_hour", 16.5)

    def compute_session_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes high-fidelity features on a historical high-frequency DataFrame.
        Expected columns: open, high, low, close, volume, spread, bid_qty, ask_qty.
        And optional cross-asset columns like: dxy_close, bond_yield_close.
        """
        features_df = df.copy()

        # Ensure index is datetime
        if not isinstance(features_df.index, pd.DatetimeIndex):
            features_df.index = pd.to_datetime(features_df.index)

        # 1. Base log returns & volatility
        features_df["log_ret"] = np.log(features_df["close"] / features_df["close"].shift(1))
        features_df["volatility_5m"] = features_df["log_ret"].rolling(12).std() * np.sqrt(288)

        # 2. Extract Session Regime Indicators
        hours = features_df.index.hour + features_df.index.minute / 60.0

        # 3. Opening Auction & London Open behavior (07:30 - 08:30 GMT)
        features_df["is_london_open"] = ((hours >= 7.5) & (hours <= 8.5)).astype(int)

        # 4. London Kill Zone (08:00 - 11:00 GMT)
        features_df["is_london_killzone"] = ((hours >= 8.0) & (hours <= 11.0)).astype(int)

        # 5. London Close (15:30 - 16:30 GMT)
        features_df["is_london_close"] = ((hours >= 15.5) & (hours <= 16.5)).astype(int)

        # 6. London-New York Overlap (13:00 - 16:30 GMT)
        features_df["is_lnd_ny_overlap"] = ((hours >= 13.0) & (hours <= 16.5)).astype(int)

        # 7. Liquidity Migration from Asia (Cumulative Volume and Volatility shifts)
        # Compute rolling volume of the last 4 hours (representing late Asia) vs. London opening
        features_df["asia_vol_proxy"] = features_df["volume"].rolling(48).mean()  # 4 hours of 5-min candles
        features_df["london_vol_proxy"] = features_df["volume"].rolling(12).mean() # 1 hour
        features_df["liquidity_migration_ratio"] = features_df["london_vol_proxy"] / (features_df["asia_vol_proxy"] + 1e-8)

        # 8. Liquidity Sweep Indicator (H/L Sweeps before expansion)
        # Identify if high/low is broken briefly and price reverses (rejection pinbar/wick behavior)
        rolling_high_20 = features_df["high"].shift(1).rolling(20).max()
        rolling_low_20 = features_df["low"].shift(1).rolling(20).min()

        features_df["high_sweep"] = ((features_df["high"] > rolling_high_20) & (features_df["close"] < rolling_high_20)).astype(float)
        features_df["low_sweep"] = ((features_df["low"] < rolling_low_20) & (features_df["close"] > rolling_low_20)).astype(float)
        features_df["liquidity_sweep_signal"] = features_df["high_sweep"] - features_df["low_sweep"]

        # 9. Microstructure Order Flow Imbalance (OFI) & Replenishment
        # Standard bid/ask volume imbalance
        if "bid_qty" in features_df.columns and "ask_qty" in features_df.columns:
            features_df["ofi"] = (features_df["bid_qty"] - features_df["ask_qty"]) / (features_df["bid_qty"] + features_df["ask_qty"] + 1e-8)
        else:
            # Fallback to volume-weighted direction proxy
            price_change = features_df["close"].diff()
            features_df["ofi"] = np.where(price_change > 0, features_df["volume"], np.where(price_change < 0, -features_df["volume"], 0)) / (features_df["volume"] + 1e-8)

        # 10. Spread Dynamics & Execution Quality
        if "spread" in features_df.columns:
            features_df["spread_ma_12"] = features_df["spread"].rolling(12).mean()
            features_df["spread_zscore"] = (features_df["spread"] - features_df["spread_ma_12"]) / (features_df["spread"].rolling(12).std() + 1e-8)
        else:
            features_df["spread_zscore"] = 0.0

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

        # Discretize into quantile bins to compute probabilities
        x = pd.qcut(aligned.iloc[:, 0], q=bins, labels=False, duplicates="drop").values
        y = pd.qcut(aligned.iloc[:, 1], q=bins, labels=False, duplicates="drop").values

        # Construct vectors
        # Y_t, Y_{t-1}, X_{t-lag}
        y_t = y[lag:]
        y_lag = y[:-lag]
        x_lag = x[:-lag]

        # 1. Joint entropy of (Y_t, Y_lag)
        p_y_joint = self._compute_joint_prob_2d(y_t, y_lag, bins)
        h_y_joint = -np.sum(p_y_joint * np.log2(p_y_joint + 1e-12))

        # 2. Entropy of Y_lag
        p_y_lag = self._compute_prob_1d(y_lag, bins)
        h_y_lag = -np.sum(p_y_lag * np.log2(p_y_lag + 1e-12))

        # H(Y_t | Y_{t-1}) = H(Y_t, Y_{t-1}) - H(Y_{t-1})
        h_cond_base = h_y_joint - h_y_lag

        # 3. Joint entropy of (Y_t, Y_lag, X_lag)
        p_3d = self._compute_joint_prob_3d(y_t, y_lag, x_lag, bins)
        h_3d = -np.sum(p_3d * np.log2(p_3d + 1e-12))

        # 4. Joint entropy of (Y_lag, X_lag)
        p_2d_cond = self._compute_joint_prob_2d(y_lag, x_lag, bins)
        h_2d_cond = -np.sum(p_2d_cond * np.log2(p_2d_cond + 1e-12))

        # H(Y_t | Y_{t-1}, X_{t-lag}) = H(Y_t, Y_{t-1}, X_{t-lag}) - H(Y_{t-1}, X_{t-lag})
        h_cond_full = h_3d - h_2d_cond

        # TE = H(Y_t | Y_{t-1}) - H(Y_t | Y_{t-1}, X_{t-lag})
        te = max(0.0, h_cond_base - h_cond_full)
        return float(te)

    def estimate_conditional_mutual_information(self, x: pd.Series, y: pd.Series, z: pd.Series, bins: int = 5) -> float:
        """
        Estimates Conditional Mutual Information (CMI): I(X; Y | Z)
        CMI = H(X, Z) + H(Y, Z) - H(X, Y, Z) - H(Z)
        Returns CMI value (>= 0).
        """
        aligned = pd.concat([x, y, z], axis=1).dropna()
        if len(aligned) < 15:
            return 0.0

        # Discretize
        xd = pd.qcut(aligned.iloc[:, 0], q=bins, labels=False, duplicates="drop").values
        yd = pd.qcut(aligned.iloc[:, 1], q=bins, labels=False, duplicates="drop").values
        zd = pd.qcut(aligned.iloc[:, 2], q=bins, labels=False, duplicates="drop").values

        # Compute probabilities
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
        P(Y=y | do(X=x)) = sum_z P(Y=y | X=x, Z=z) * P(Z=z)
        Also returns causal confidence / average causal effect (ACE) proxy.
        """
        aligned = pd.concat([cause, effect, confounder], axis=1).dropna()
        if len(aligned) < 20:
            return {"ace": 0.0, "p_do": {}}

        # Discretize for clean probability calculations
        x = pd.qcut(aligned.iloc[:, 0], q=bins, labels=False, duplicates="drop").values
        y = pd.qcut(aligned.iloc[:, 1], q=bins, labels=False, duplicates="drop").values
        z = pd.qcut(aligned.iloc[:, 2], q=bins, labels=False, duplicates="drop").values

        # Unique state counts
        u_x = np.unique(x)
        u_y = np.unique(y)
        u_z = np.unique(z)

        # 1. Compute marginal P(Z=z)
        p_z = {}
        for state_z in u_z:
            p_z[state_z] = np.mean(z == state_z)

        # 2. Compute conditional joint probabilities P(Y=y | X=x, Z=z)
        p_do = {} # Map (x, y) -> P(Y=y | do(X=x))
        for state_x in u_x:
            for state_y in u_y:
                p_y_given_do = 0.0
                for state_z in u_z:
                    # Subset where X=x, Z=z
                    sub_xz = (x == state_x) & (z == state_z)
                    if np.sum(sub_xz) > 0:
                        p_cond_y = np.mean(y[sub_xz] == state_y)
                        p_y_given_do += p_cond_y * p_z[state_z]
                p_do[(int(state_x), int(state_y))] = float(p_y_given_do)

        # 3. Compute Average Causal Effect (ACE) proxy as difference between extreme causes
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

    # =======================================================================
    # Probability helper methods
    # =======================================================================

    def _compute_prob_1d(self, arr: np.ndarray, num_bins: int) -> np.ndarray:
        counts = np.bincount(arr, minlength=num_bins)
        return counts / (np.sum(counts) + 1e-12)

    def _compute_joint_prob_2d(self, a: np.ndarray, b: np.ndarray, num_bins: int) -> np.ndarray:
        joint_hist, _, _ = np.histogram2d(a, b, bins=(num_bins, num_bins))
        return joint_hist / (np.sum(joint_hist) + 1e-12)

    def _compute_joint_prob_3d(self, a: np.ndarray, b: np.ndarray, c: np.ndarray, num_bins: int) -> np.ndarray:
        # Standardized 3D joint histogram flat array
        indices = a * (num_bins**2) + b * num_bins + c
        counts = np.bincount(indices, minlength=num_bins**3)
        return counts / (np.sum(counts) + 1e-12)
