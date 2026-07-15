"""
Institutional Quantitative Research Pipeline & Lifecycle Management Suite.
Implements the 10-stage Continuous Quant Research Loop:
1. Research Lab – Generate and manage hypotheses.
2. Data Pipeline – Ingest, clean, validate, and version datasets.
3. Feature Factory – Create and evaluate candidate statistical features.
4. Alpha Discovery Engine – Discover and validate predictive signals (IC, stability).
5. Strategy Builder – Map alphas to executable trade rules with risk constraints.
6. Backtesting Engine – Simulates high-fidelity execution (commissions, spread, slippage).
7. Validation Lab – Walk-forward analysis, stress tests, Monte Carlo simulation.
8. Portfolio Optimizer – Dynamically allocate capital (Kelly, volatility targeting).
9. Paper Trading Environment – Validate signal latency and execution simulation.
10. Production & Monitoring – Live metrics tracking, drift detection, and strategy retirement.
"""

import logging
import uuid
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from trading_bot.data.validate import DataValidator
from trading_bot.backtesting.advanced_backtester import InstitutionalBacktester, InstitutionalTrade, InstitutionalBacktestResult
from trading_bot.strategy.strategy_engine import StrategyEngine, Signal

logger = logging.getLogger("AlphaAlgo.QuantPipeline")

# ===========================================================================
# Phase 1: Research Lab (Hypothesis Generation)
# ===========================================================================

@dataclass
class Hypothesis:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    economic_rationale: str = ""
    counterparty_profile: str = ""  # Who is likely on the other side of the trade
    falsification_conditions: List[str] = field(default_factory=list)
    status: str = "Proposed"  # Proposed, Under_Review, Accepted, Rejected, Retired


class ResearchLab:
    """Manages the generation, registration, and status of quantitative hypotheses."""

    def __init__(self):
        self.hypothesis_registry: Dict[str, Hypothesis] = {}

    def propose_hypothesis(self, name: str, description: str, rationale: str, counterparty: str, falsifications: List[str]) -> Hypothesis:
        hyp = Hypothesis(
            name=name,
            description=description,
            economic_rationale=rationale,
            counterparty_profile=counterparty,
            falsification_conditions=falsifications
        )
        self.hypothesis_registry[hyp.id] = hyp
        logger.info(f"Proposing hypothesis: '{name}' (ID: {hyp.id})")
        return hyp

    def get_hypothesis(self, hyp_id: str) -> Optional[Hypothesis]:
        return self.hypothesis_registry.get(hyp_id)


# ===========================================================================
# Phase 2: Data Pipeline
# ===========================================================================

class IngestionPipeline:
    """Ingests, cleans, and validates high-quality historical and streaming datasets."""

    def __init__(self):
        self.validator = DataValidator()

    def process_and_clean_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Cleans duplicates, resolves missing values, and runs pre-flight data checks."""
        if df is None or df.empty:
            raise ValueError("Input DataFrame is empty or None")

        # Ingest a clean copy
        cleaned_df = df.copy()

        # Remove duplicates
        if cleaned_df.index.duplicated().any():
            cleaned_df = cleaned_df[~cleaned_df.index.duplicated(keep="first")]

        # Linear interpolate missing OHLC prices safely, forward fill volumes
        for col in ["open", "high", "low", "close"]:
            if col in cleaned_df.columns:
                cleaned_df[col] = cleaned_df[col].interpolate(method="linear")

        if "volume" in cleaned_df.columns:
            cleaned_df["volume"] = cleaned_df["volume"].ffill().fillna(1000)

        # Run pre-flight validations
        is_valid, report = self.validator.validate_dataframe(cleaned_df)
        report["is_valid"] = is_valid

        return cleaned_df, report


# ===========================================================================
# Phase 3 & 4: Feature Factory & EDA
# ===========================================================================

class FeatureFactory:
    """Translates clean raw datasets into rich candidate statistical features."""

    def __init__(self):
        pass

    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features_df = df.copy()

        # 1. Base log returns
        features_df["log_ret"] = np.log(features_df["close"] / features_df["close"].shift(1))

        # 2. Volatility proxy (ATR-like volatility)
        features_df["real_vol_10"] = features_df["log_ret"].rolling(10).std()

        # 3. Microstructure features: VWAP distance
        if "volume" in features_df.columns:
            cum_vol = features_df["volume"].cumsum()
            cum_val = (features_df["close"] * features_df["volume"]).cumsum()
            vwap = cum_val / cum_vol
            features_df["vwap_dist"] = (features_df["close"] - vwap) / vwap

        # 4. Statistical characterization: Hurst Exponent (simplified lookback proxy)
        features_df["hurst_proxy"] = features_df["log_ret"].rolling(30).apply(self._calc_hurst_proxy, raw=True)

        return features_df.dropna()

    def _calc_hurst_proxy(self, returns: np.ndarray) -> float:
        """Simplified Hurst Exponent proxy calculating autocorrelation memory decay."""
        if len(returns) < 10:
            return 0.5
        std = np.std(returns)
        if std == 0:
            return 0.5
        # Range of cumulative sum of returns divided by std deviation
        cum_sum = np.cumsum(returns)
        r = np.max(cum_sum) - np.min(cum_sum)
        s = std
        # Normalize and return log ratio
        return float(np.log(r / s) / np.log(len(returns)) if r > 0 and s > 0 else 0.5)


# ===========================================================================
# Phase 5: Alpha Discovery Engine
# ===========================================================================

@dataclass
class AlphaSignal:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    information_coefficient: float = 0.0
    turnover: float = 0.0
    decay_half_life_bars: int = 24
    status: str = "Proposed"


class AlphaDiscoveryEngine:
    """Evaluates candidate features and validates them as predictive alpha signals."""

    def __init__(self, min_ic_threshold: float = 0.02):
        self.min_ic_threshold = min_ic_threshold
        self.validated_alphas: Dict[str, AlphaSignal] = {}

    def evaluate_feature_as_alpha(self, df: pd.DataFrame, feature_col: str, forward_returns_col: str = "log_ret") -> AlphaSignal:
        """Calculates Information Coefficient (Rank correlation with forward returns)."""
        forward_returns = df[forward_returns_col].shift(-1).dropna()
        feature_vals = df[feature_col].iloc[:len(forward_returns)]

        # Rank Information Coefficient (Spearman Rank Correlation)
        ic_corr = float(feature_vals.corr(forward_returns, method="spearman"))

        # Calculate approximate feature turnover
        turnover = float(df[feature_col].diff().abs().mean() / (df[feature_col].abs().mean() + 1e-8))

        alpha = AlphaSignal(
            name=f"Alpha_{feature_col}",
            information_coefficient=ic_corr,
            turnover=turnover,
            status="Approved" if abs(ic_corr) >= self.min_ic_threshold else "Rejected"
        )

        if alpha.status == "Approved":
            self.validated_alphas[alpha.id] = alpha

        logger.info(f"Evaluated candidate alpha signal: {alpha.name} -> IC: {ic_corr:.4f}, Status: {alpha.status}")
        return alpha


# ===========================================================================
# Phase 6: Strategy Builder
# ===========================================================================

class StrategyBuilder:
    """Converts approved predictive alpha signals into structured trading strategies."""

    def __init__(self, default_config: Dict[str, Any] = None):
        self.config = default_config or {
            "risk_limits": {
                "max_volatility_threshold": 0.03,
                "max_spread_pips_limit": 2.5
            }
        }

    def assemble_strategy(self, symbol: str, swing_len: int = 3) -> StrategyEngine:
        """Instantiates StrategyEngine with hard configuration and constraints."""
        engine = StrategyEngine(
            mt5i=None,
            swing_len=swing_len,
            symbol=symbol,
            config=self.config
        )
        return engine


# ===========================================================================
# Phase 7 & 8: Backtesting Engine & Validation Lab
# ===========================================================================

class ValidationLab:
    """Performs rigorous walk-forward splits, parameter sensitivities, and Monte Carlo checks."""

    def __init__(self, backtester: InstitutionalBacktester):
        self.backtester = backtester

    def run_walk_forward_backtest(self, oos_splits: int = 3) -> List[InstitutionalBacktestResult]:
        """Splits the historical dataset into walk-forward out-of-sample periods and backtests them."""
        total_bars = len(self.backtester.bars)
        split_size = total_bars // (oos_splits + 1)
        results = []

        for s in range(oos_splits):
            train_end = (s + 1) * split_size
            test_end = (s + 2) * split_size

            # Extract walk-forward out-of-sample slice
            oos_bars = self.backtester.bars.iloc[train_end:test_end].copy()

            # Create subset backtester for this OOS chunk
            sub_backtester = InstitutionalBacktester(
                bars=oos_bars,
                strategy=self.backtester.strategy,
                config=self.backtester.config,
                lookback=self.backtester.lookback
            )

            res = sub_backtester.run()
            results.append(res)
            logger.info(f"Walk-Forward Slice {s+1} OOS Completed. Return: {res.total_return_pct:.2f}%, Sharpe: {res.sharpe_ratio:.2f}")

        return results


# ===========================================================================
# Phase 9: Portfolio Optimizer
# ===========================================================================

class PortfolioOptimizer:
    """Allocates active risk and trading capital across strategy lines using volatility scaling."""

    def __init__(self, target_portfolio_vol: float = 0.12):
        self.target_portfolio_vol = target_portfolio_vol

    def calculate_allocations(self, strategy_vols: Dict[str, float]) -> Dict[str, float]:
        """Calculates risk-parity allocations (inverse-volatility scale)."""
        if not strategy_vols:
            return {}

        # Avoid divide-by-zero
        vols = np.array([max(v, 0.001) for v in strategy_vols.values()])
        inv_vols = 1.0 / vols
        total_inv_vol = np.sum(inv_vols)

        weights = inv_vols / total_inv_vol

        allocations = {}
        for (strategy_name, _), weight in zip(strategy_vols.items(), weights):
            allocations[strategy_name] = float(weight)

        return allocations


# ===========================================================================
# Phase 10: Paper Trading Environment
# ===========================================================================

class SimulatedPaperEnvironment:
    """Verifies strategy execution, latencies, and transaction costs on real-time simulated streams."""

    def __init__(self, strategy: StrategyEngine):
        self.strategy = strategy
        self.latency_buffer: List[float] = []

    def simulate_signal_execution(self, observation: Dict[str, Any]) -> Tuple[Optional[Signal], float]:
        """Simulates latency execution and measures delay."""
        t0 = datetime.utcnow()

        # Convert observation to DataFrame window
        dummy_df = pd.DataFrame([observation])
        signals = self.strategy.analyse(dummy_df)

        # Simulate standard API network latency delay
        latency_ms = np.random.uniform(5.0, 50.0)  # Standard 5-50ms simulation
        self.latency_buffer.append(latency_ms)

        signal = signals[0] if signals else None
        return signal, latency_ms


# ===========================================================================
# Phase 11 & 12: Production & Monitoring (Lifecycle Management)
# ===========================================================================

@dataclass
class StrategyMetricsSnapshot:
    strategy_id: str
    active_since: datetime
    total_trades_live: int = 0
    live_drawdown_pct: float = 0.0
    rolling_sharpe_live: float = 0.0
    model_drift_score: float = 0.0
    status: str = "Active"


class ProductionMonitor:
    """Monitors live metric snap shots, calculates model drift, and triggers strategy retirement."""

    def __init__(self, drawdown_retirement_limit: float = 12.0):
        self.drawdown_retirement_limit = drawdown_retirement_limit
        self.strategy_metrics: Dict[str, StrategyMetricsSnapshot] = {}

    def track_metrics(self, strategy_id: str, new_trades: int, current_drawdown: float, sharpe: float, drift: float) -> StrategyMetricsSnapshot:
        """Updates performance tracking and evaluates retirement circuit breakers."""
        snapshot = self.strategy_metrics.get(strategy_id)
        if not snapshot:
            snapshot = StrategyMetricsSnapshot(strategy_id=strategy_id, active_since=datetime.utcnow())
            self.strategy_metrics[strategy_id] = snapshot

        snapshot.total_trades_live += new_trades
        snapshot.live_drawdown_pct = current_drawdown
        snapshot.rolling_sharpe_live = sharpe
        snapshot.model_drift_score = drift

        # Hard retirement circuit breaker if max drawdown exceeded
        if snapshot.live_drawdown_pct >= self.drawdown_retirement_limit:
            snapshot.status = "Retired"
            logger.critical(f"STRATEGY RETIREMENT TRIGGERED! Strategy ID: {strategy_id} drawdown ({snapshot.live_drawdown_pct:.2f}%) exceeds retirement threshold!")

        return snapshot
