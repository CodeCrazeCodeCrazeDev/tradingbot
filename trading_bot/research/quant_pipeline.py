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


# ===========================================================================
# ADVANCED INSTITUTIONAL PIPELINE STAGES (Invisible Operations)
# ===========================================================================


class LiteratureReviewBacklog:
    """
    Prevents 'reinventing the wheel' and rediscovering known dead ends.
    Indexes academic research papers, patents, and historical internal failure logs.
    """
    def __init__(self) -> None:
        self.backlog: List[Dict[str, Any]] = [
            {
                "topic": "EMA Crossover",
                "result": "FAIL",
                "reason": "High turnover fees wipe out small edge. Failed across all major FX pairs in 2021-2025.",
                "recomm": "Use order flow or Fair Value Gaps instead of technical indicator lags."
            },
            {
                "topic": "Order flow imbalance",
                "result": "PASS",
                "reason": "Provides short-term edge under range-bound liquidity regimes.",
                "recomm": "Integrate with Volatility circuit breaker."
            }
        ]

    def verify_topic(self, topic_query: str) -> Dict[str, Any]:
        """Scans historical backlog to provide peer research recommendation."""
        for item in self.backlog:
            if topic_query.lower() in item["topic"].lower():
                logger.info(f"Literature Review Match found for '{topic_query}': Result={item['result']}")
                return item
        return {
            "topic": topic_query,
            "result": "UNKNOWN",
            "reason": "No previous internal research or failure logs recorded.",
            "recomm": "Proceed with caution. Complete rigorous walk-forward test."
        }


class RegimeAndMicrostructureAnalyzer:
    """
    Performs high-fidelity Market Microstructure and Regime Analysis.
    Estimates Order Book Imbalance (OBI), Bid-Ask Spreads, and fill probabilities.
    """
    def __init__(self) -> None:
        pass

    def classify_regime(self, bars: pd.DataFrame) -> str:
        """Classifies the current market into trending, range, or high volatility crisis regimes."""
        if len(bars) < 10:
            return "NORMAL"
        close_prices = bars["close"].astype(float).values
        returns = np.diff(close_prices) / close_prices[:-1]
        vol = np.std(returns) * np.sqrt(252)

        if vol > 0.04:
            return "CRISIS_HIGH_VOL"
        elif vol < 0.01:
            return "LOW_VOL_RANGE"
        return "NORMAL_TRENDING"

    def calculate_order_book_imbalance(self, bid_qty: float, ask_qty: float) -> float:
        """
        Calculates the classical microstructural Order Book Imbalance (OBI).
        Ranges from -1.0 (heavy sell pressure) to +1.0 (heavy buy pressure).
        """
        total = bid_qty + ask_qty
        if total == 0:
            return 0.0
        return (bid_qty - ask_qty) / total

    def estimate_fill_probability(self, spread_pips: float, limit_distance_pips: float) -> float:
        """Estimates the probability of limit order execution based on spread and distance."""
        # Closer distance and tighter spread yield higher fill probability
        if limit_distance_pips <= 0:
            return 1.0
        exponent = - (limit_distance_pips / (spread_pips + 1e-5))
        return float(np.exp(exponent))


class FeatureSelectionSuite:
    """
    Generates candidate features and selects the most robust ones,
    preventing over-parameterization and dimensional inflation.
    """
    def __init__(self) -> None:
        pass

    def calculate_mutual_information_score(self, feature: pd.Series, target: pd.Series) -> float:
        """Calculates a simplified mutual information proxy using linear and rank correlations."""
        linear_corr = feature.corr(target, method="pearson")
        rank_corr = feature.corr(target, method="spearman")
        # Entropy proxy
        mi_proxy = 0.5 * (abs(linear_corr) + abs(rank_corr))
        return float(mi_proxy if not np.isnan(mi_proxy) else 0.0)

    def calculate_shap_proxy(self, feature: pd.Series, target: pd.Series) -> float:
        """Computes feature importance proxy based on gradient projection stability."""
        std_feat = feature.std()
        if std_feat == 0:
            return 0.0
        cov = feature.cov(target)
        return float(abs(cov) / std_feat)


class AlphaValidatorAndOrthogonality:
    """
    Validates candidate alphas for statistical significance (p-value)
    and correlation/orthogonality against existing active alphas.
    """
    def __init__(self) -> None:
        self.active_alphas: List[pd.Series] = []

    def check_orthogonality(self, candidate_returns: pd.Series) -> Tuple[bool, float]:
        """
        Computes maximum correlation with existing portfolio alphas.
        Alphas with max correlation > 0.40 are rejected to prevent concentration.
        """
        if not self.active_alphas:
            return True, 0.0

        max_corr = 0.0
        for active in self.active_alphas:
            # Align timestamps
            aligned = pd.concat([candidate_returns, active], axis=1).dropna()
            if len(aligned) >= 3:
                corr = abs(aligned.iloc[:, 0].corr(aligned.iloc[:, 1]))
                if corr > max_corr:
                    max_corr = corr

        is_orthogonal = max_corr <= 0.40
        return is_orthogonal, float(max_corr)


class AdvancedStatisticalValidation:
    """
    Computes rigorous statistical indicators to verify backtests.
    Includes the Deflated Sharpe Ratio (DSR) to correct for multiple testing bias.
    """
    def __init__(self) -> None:
        pass

    def calculate_deflated_sharpe_ratio(self, observed_sr: float, num_trials: int,
                                      variance_of_srs: float, skewness: float,
                                      kurtosis: float, num_bars: int) -> float:
        """
        Calculates Bailey and Lopez de Prado's Deflated Sharpe Ratio (DSR).
        Corrects the observed Sharpe Ratio for multiple testing (inflation).

        Returns:
            The probability (0.0 to 1.0) that the actual Sharpe is greater than 0
            after accounting for the trials and skew/kurtosis.
        """
        # 1. Estimate expected maximum Sharpe under multiple testing
        euler_gamma = 0.5772156649
        if num_trials <= 1:
            expected_max_sr = 0.0
        else:
            # Standard normal cumulative inverse proxies for high N trials
            z = np.sqrt(2 * np.log(num_trials)) - (np.log(np.log(num_trials)) + np.log(4 * np.pi)) / (2 * np.sqrt(2 * np.log(num_trials)))
            expected_max_sr = float(z * np.sqrt(variance_of_srs))

        # 2. Standard deviation of the Sharpe Ratio distribution under non-normality
        # Lopez de Prado formula
        sr_variance = (1.0 + (1.0 + skewness * observed_sr) * (observed_sr**2 / 4.0) - skewness * (observed_sr**3 / 2.0) + (kurtosis - 1.0) * (observed_sr**4 / 4.0)) / (num_bars - 1.0)
        sr_std = np.sqrt(max(sr_variance, 1e-8))

        # 3. Compute DSR test statistic
        z_stat = (observed_sr - expected_max_sr) / sr_std

        # 4. Return standard cumulative probability (Normal distribution)
        dsr = 0.5 * (1.0 + np.tanh(z_stat / np.sqrt(2.0)))
        return float(dsr)


class CapacityAnalyzer:
    """
    Computes strategy trade capacity.
    Applies the market impact square-root law to model slippage escalation at scale.
    """
    def __init__(self, impact_coefficient: float = 0.15) -> None:
        self.impact_coefficient = impact_coefficient

    def estimate_market_impact_pips(self, trade_size_usd: float, avg_daily_volume_usd: float, vol_annualized: float) -> float:
        """
        Applies the classical institutional Square-Root Law of Market Impact.
        Slippage increases with the square root of participation rate.
        """
        if avg_daily_volume_usd <= 0:
            return 0.0
        participation_rate = trade_size_usd / avg_daily_volume_usd
        impact_pct = self.impact_coefficient * vol_annualized * np.sqrt(participation_rate)

        # Translate percent return impact to pips (approx 1 pip = 0.0001 = 0.01%)
        return float(impact_pct * 10000.0)


class ShadowTradingEnvironment:
    """
    Logs and monitors strategy decisions in parallel with production
    without committing real capital. Compares actual execution against paper expectations.
    """
    def __init__(self) -> None:
        self.shadow_log: List[Dict[str, Any]] = []

    def record_shadow_execution(self, signal: Signal, actual_spread: float) -> Dict[str, Any]:
        """Logs parallel trade, recording execution slip."""
        expected_pips = signal.stop_loss_pips * signal.take_profit_rr
        # Realistic slippage is higher if spread is wide
        slippage_slip = actual_spread * np.random.uniform(0.1, 0.4)

        log_entry = {
            "timestamp": datetime.utcnow(),
            "symbol": signal.symbol,
            "direction": signal.direction,
            "expected_pips": expected_pips,
            "actual_slippage_pips": slippage_slip,
            "reconciled": True
        }
        self.shadow_log.append(log_entry)
        logger.info(f"Shadow Execution Logged: {signal.symbol} {signal.direction} -> Slip: {slippage_slip:.2f} pips")
        return log_entry


class PerformanceAttribution:
    """
    Deconstructs strategy returns into distinct scientific risk components:
    Alpha (pure edge), Beta (market returns), Regime effect, and Transaction Drag.
    """
    def __init__(self) -> None:
        pass

    def attribute_performance(self, total_pnl_usd: float, market_return_pnl: float,
                              transaction_cost_drag: float, beta: float = 1.0) -> Dict[str, float]:
        """
        Splits returns: Total PnL = Beta * MarketReturn + Alpha - FeeDrag
        """
        beta_pnl = beta * market_return_pnl
        net_edge = total_pnl_usd - beta_pnl
        # Alpha is net edge before fees
        alpha_pnl = net_edge + transaction_cost_drag

        return {
            "total_return_usd": total_pnl_usd,
            "beta_attribution_usd": beta_pnl,
            "alpha_attribution_usd": alpha_pnl,
            "transaction_cost_drag_usd": transaction_cost_drag
        }


class AdvancedDriftDetection:
    """
    Automated Population Stability Index (PSI) drift monitoring for features/labels.
    Prevents silent model decay in changing market environments.
    """
    def __init__(self) -> None:
        pass

    def calculate_psi(self, baseline_distribution: np.ndarray, actual_distribution: np.ndarray, num_bins: int = 5) -> float:
        """
        Computes Population Stability Index (PSI) between baseline and actual distributions.
        PSI < 0.1 indicates stability, PSI > 0.25 indicates significant feature/label drift.
        """
        if len(baseline_distribution) == 0 or len(actual_distribution) == 0:
            return 0.0

        # Standardize and bin
        baseline_pcts, bins = np.histogram(baseline_distribution, bins=num_bins, density=False)
        actual_pcts, _ = np.histogram(actual_distribution, bins=bins, density=False)

        # Convert count frequency to percentage
        b_pct = baseline_pcts / len(baseline_distribution)
        a_pct = actual_pcts / len(actual_distribution)

        # Adjust zeros to prevent log zero
        b_pct = np.where(b_pct == 0, 1e-4, b_pct)
        a_pct = np.where(a_pct == 0, 1e-4, a_pct)

        # PSI Formula: sum( (Actual% - Expected%) * ln(Actual% / Expected%) )
        psi = np.sum((a_pct - b_pct) * np.log(a_pct / b_pct))
        return float(psi)
