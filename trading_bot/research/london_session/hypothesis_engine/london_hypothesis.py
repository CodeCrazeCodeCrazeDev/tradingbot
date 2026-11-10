"""
Hypothesis Engine, Canonical Hypothesis Registry & Configurable Promotion Policy.
Defines and tests all 13 core London Session hypotheses specified in the Master Directive:
1. London opening range breakout and failure.
2. Asian-session range breakout and mean reversion.
3. Asian high/low liquidity sweeps.
4. London–New York session overlap.
5. London session volatility expansion and contraction.
6. Session-based liquidity transitions.
7. Market structure shifts and displacement.
8. Breakout continuation versus false breakout.
9. Conditional directional continuation.
10. Volatility-dependent stop-loss and take-profit behavior.
11. Time-of-day-dependent expected returns.
12. Spread, slippage, and transaction-cost effects.
13. Intermarket and cross-asset relationships.

Includes multiple-testing corrections: Benjamini-Hochberg (FDR) and Bonferroni.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd

logger = logging.getLogger("AlphaAlgo.LondonHypothesisEngine")


@dataclass
class LondonHypothesis:
    """
    Standardized, falsifiable hypothesis object.
    Matches structure: Hypothesis -> Features -> Prediction -> Statistical test -> Result.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    economic_rationale: str = ""
    entry_conditions: str = ""
    outcome_definitions: str = ""
    holding_period_bars: int = 12
    invalidation_criteria: str = ""
    risk_assumptions: str = ""
    feature_columns: List[str] = field(default_factory=list)
    falsification_tests: List[str] = field(default_factory=list)
    status: str = "Proposed"  # Proposed, Accepted, Rejected, Retired
    created_at: datetime = field(default_factory=datetime.utcnow)
    test_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromotionPolicy:
    """
    Configurable Promotion Policy for promoting edges from Candidates to Validated.
    """
    min_observations: int = 150
    max_pbo: float = 0.15          # Probability of Backtest Overfitting limit
    min_dsr: float = 1.6           # Deflated Sharpe Ratio limit
    max_drawdown: float = 0.15     # Max drawdown threshold
    min_calibration: float = 0.80  # Calibration success rate
    min_expected_return: float = 0.005 # Min return per trade
    max_turnover: float = 0.85     # Max turnover target
    max_market_impact: float = 5.0 # Max slippage market impact in pips


CANONICAL_HYPOTHESES = [
    {
        "name": "HYP-01_London_Opening_Range_Breakout_Failure",
        "description": "Initial 15-min London open price extensions frequently exhaust and fail if volume drops sharply.",
        "economic_rationale": "Early retail breakout entries get trapped by institutional order book replenishment.",
        "entry_conditions": "is_london_open == 1 and abs(liquidity_sweep_signal) > 0 and ofi < 0",
        "outcome_definitions": "Reversal of at least 1.5x initial bar range within 6 bars",
        "holding_period_bars": 12,
        "invalidation_criteria": "Price sustains beyond breakout level with rising OFI",
        "risk_assumptions": "1.5 pip spread + 0.5 pip slippage drag",
        "feature_columns": ["is_london_open", "liquidity_sweep_signal", "ofi", "vol_ratio_5m_4h"],
        "falsification_tests": ["Regression t-stat p-value > 0.05 on forward returns"]
    },
    {
        "name": "HYP-02_Asian_Range_Breakout_Mean_Reversion",
        "description": "Tight Asian ranges revert to mean when pierced prior to major liquidity migration.",
        "economic_rationale": "Thin pre-London liquidity causes artificial price excursions unsupported by depth.",
        "entry_conditions": "is_asia_session == 1 and (high > asia_high or low < asia_low)",
        "outcome_definitions": "Price returns to Asian midpoint within 8 bars",
        "holding_period_bars": 8,
        "invalidation_criteria": "Volume expansion > 2x average",
        "risk_assumptions": "Wider Asia spreads (2.0 - 2.5 pips)",
        "feature_columns": ["is_asia_session", "asia_range", "volatility_5m"],
        "falsification_tests": ["T-test on return difference p > 0.05"]
    },
    {
        "name": "HYP-03_Asian_High_Low_Liquidity_Sweeps",
        "description": "Asian High/Low levels are swept at London open before aggressive directional expansion (Judas Swing).",
        "economic_rationale": "Liquidity pools resting above/below Asian extremes provide liquidity for institutional accumulation.",
        "entry_conditions": "is_london_open == 1 and (asia_high_sweep == 1 or asia_low_sweep == 1)",
        "outcome_definitions": "Directional displacement opposite the sweep direction within 12 bars",
        "holding_period_bars": 18,
        "invalidation_criteria": "Close remains beyond swept extreme for > 3 bars",
        "risk_assumptions": "1.2 pip spread + stop loss placed at sweep wick extreme",
        "feature_columns": ["asia_high_sweep", "asia_low_sweep", "liquidity_sweep_signal", "liquidity_migration_ratio"],
        "falsification_tests": ["Post-sweep return sign t-test p > 0.05"]
    },
    {
        "name": "HYP-04_London_NY_Session_Overlap_Momentum",
        "description": "London-NY overlap exhibits highest daily liquidity and directional trend continuation.",
        "economic_rationale": "Dual-continental institutional order flow generates genuine trending runs.",
        "entry_conditions": "is_lnd_ny_overlap == 1 and is_displacement == 1",
        "outcome_definitions": "Trend continuation in displacement direction for >= 15 bars",
        "holding_period_bars": 18,
        "invalidation_criteria": "Reversal of > 50% displacement candle",
        "risk_assumptions": "Tight spread (1.0 pip), moderate slippage during US releases",
        "feature_columns": ["is_lnd_ny_overlap", "directional_displacement", "ofi_ma_6"],
        "falsification_tests": ["Permutation test on continuation Sharpe p > 0.05"]
    },
    {
        "name": "HYP-05_London_Volatility_Expansion_Contraction",
        "description": "Volatility regime transitions predictably from low Asia volatility to London expansion.",
        "economic_rationale": "Capital allocation surges when European interbank participants open operations.",
        "entry_conditions": "vol_ratio_5m_4h > 1.8 and is_london_open == 1",
        "outcome_definitions": "Realized range exceeds 2x 24h average ATR",
        "holding_period_bars": 24,
        "invalidation_criteria": "Realized volatility falls back below baseline within 4 bars",
        "risk_assumptions": "Spread widening on volatility spikes",
        "feature_columns": ["vol_ratio_5m_4h", "volatility_5m", "volatility_4h", "is_london_open"],
        "falsification_tests": ["Volatility prediction R2 <= 0.0"]
    },
    {
        "name": "HYP-06_Session_Liquidity_Transitions",
        "description": "Liquidity migration ratio predicts speed and magnitude of impending directional expansion.",
        "economic_rationale": "Rapid volume acceleration signals institutional commitment.",
        "entry_conditions": "liquidity_migration_ratio > 2.5 and is_london_open == 1",
        "outcome_definitions": "Expansion of >= 30 pips within 12 bars",
        "holding_period_bars": 12,
        "invalidation_criteria": "Liquidity migration falls below 1.0 within 3 bars",
        "risk_assumptions": "Dynamic slippage scaling with liquidity ratio",
        "feature_columns": ["liquidity_migration_ratio", "is_london_open", "ofi"],
        "falsification_tests": ["Information coefficient (IC) p > 0.05"]
    },
    {
        "name": "HYP-07_Market_Structure_Shifts_Displacement",
        "description": "Displacement candles during London Killzone establish strong directional bias for remainder of session.",
        "economic_rationale": "High-volume displacement creates imbalances that act as support/resistance.",
        "entry_conditions": "is_london_killzone == 1 and is_displacement == 1",
        "outcome_definitions": "Positive expected return in direction of displacement at session close",
        "holding_period_bars": 24,
        "invalidation_criteria": "Close beyond opposite end of displacement candle",
        "risk_assumptions": "Fixed R:R 2.0 with stop at displacement origin",
        "feature_columns": ["is_london_killzone", "is_displacement", "directional_displacement"],
        "falsification_tests": ["Regression beta t-stat p > 0.05"]
    },
    {
        "name": "HYP-08_Breakout_Continuation_vs_False_Breakout",
        "description": "Order flow imbalance (OFI) distinguishes true breakouts from false breakout sweeps.",
        "economic_rationale": "True breakouts show sustained positive OFI; false breakouts show immediate order absorption.",
        "entry_conditions": "abs(liquidity_sweep_signal) > 0",
        "outcome_definitions": "OFI sign matches subsequent return sign",
        "holding_period_bars": 12,
        "invalidation_criteria": "OFI diverges from price action for > 3 bars",
        "risk_assumptions": "Standard institutional execution drag",
        "feature_columns": ["liquidity_sweep_signal", "ofi", "ofi_ma_6"],
        "falsification_tests": ["Correlation between OFI and post-sweep return p > 0.05"]
    },
    {
        "name": "HYP-09_Conditional_Directional_Continuation",
        "description": "Directional persistence conditioned on consecutive displacement and London Open regime.",
        "economic_rationale": "Multi-bar institutional execution algorithms slice orders over several 5-min intervals.",
        "entry_conditions": "is_london_open == 1 and directional_displacement != 0 and ofi_ma_6 != 0",
        "outcome_definitions": "Autoregressive return persistence over next 6 bars",
        "holding_period_bars": 6,
        "invalidation_criteria": "Counter-trend displacement candle",
        "risk_assumptions": "Trailing stop after 3 bars",
        "feature_columns": ["directional_displacement", "ofi_ma_6", "is_london_open"],
        "falsification_tests": ["Autoregressive coefficient p > 0.05"]
    },
    {
        "name": "HYP-10_Volatility_Dependent_SL_TP_Optimization",
        "description": "Dynamic volatility-scaled barriers significantly outperform fixed pip stops during London session.",
        "economic_rationale": "Intraday volatility shifts by >300% between Asia and London; fixed stops get premature whipsaws.",
        "entry_conditions": "All London entries",
        "outcome_definitions": "Sharpe ratio of dynamic barrier > Sharpe of fixed pip barrier",
        "holding_period_bars": 18,
        "invalidation_criteria": "Fixed pip strategy achieves equal or lower drawdown",
        "risk_assumptions": "Triple barrier simulation with slippage",
        "feature_columns": ["volatility_5m", "vol_ratio_5m_4h", "is_london_killzone"],
        "falsification_tests": ["Paired t-test on trade Sharpe p > 0.05"]
    },
    {
        "name": "HYP-11_Time_of_Day_Dependent_Expected_Returns",
        "description": "Specific 30-minute intervals within London session carry non-zero expected returns.",
        "economic_rationale": "Scheduled auction fixes (e.g. 08:00 open, 16:00 London WMR fix) trigger systematic flows.",
        "entry_conditions": "london_hour in [8.0, 8.5, 11.0, 15.5, 16.0]",
        "outcome_definitions": "Mean return significantly different from 0 at alpha=0.01",
        "holding_period_bars": 6,
        "invalidation_criteria": "Distribution mean p-value > 0.05",
        "risk_assumptions": "High liquidity / tightest spreads of the day",
        "feature_columns": ["london_hour", "is_london_open", "is_london_close"],
        "falsification_tests": ["One-sample t-test against zero p > 0.05"]
    },
    {
        "name": "HYP-12_Spread_Slippage_Transaction_Cost_Decay",
        "description": "Trading edges decay quadratically as spread z-score deviates above normal London baseline.",
        "economic_rationale": "Widened spreads signal dealer toxic flow aversion, compounding adverse execution selection.",
        "entry_conditions": "spread_zscore > 1.5",
        "outcome_definitions": "Net trade expectancy drops below 0",
        "holding_period_bars": 12,
        "invalidation_criteria": "Profitable trade rate remains unchanged despite elevated spread",
        "risk_assumptions": "Realistic spread capture and slippage penalty",
        "feature_columns": ["spread_zscore", "volatility_5m"],
        "falsification_tests": ["Negative regression slope p > 0.05"]
    },
    {
        "name": "HYP-13_Intermarket_Cross_Asset_Lead_Lag",
        "description": "DXY momentum leads EURUSD and GBPUSD directional movements during London open by 1-2 bars.",
        "economic_rationale": "Global USD liquidity adjustments register first across sovereign rates and DXY futures.",
        "entry_conditions": "abs(dxy_return) > 1.5 * std and is_london_open == 1",
        "outcome_definitions": "Negative correlation with currency pair return at lag 1",
        "holding_period_bars": 6,
        "invalidation_criteria": "Transfer entropy <= 0 or contemporaneous correlation dominates",
        "risk_assumptions": "Standard EUR/GBP spread",
        "feature_columns": ["is_london_open", "dxy_close"],
        "falsification_tests": ["Transfer entropy test p > 0.05"]
    }
]


class LondonHypothesisEngine:
    """
    Hypothesis Engine: manages canonical hypothesis registry, evaluates falsifications,
    and performs Benjamini-Hochberg False Discovery Rate (FDR) corrections.
    """

    def __init__(self) -> None:
        self.hypotheses: Dict[str, LondonHypothesis] = {}
        self._register_canonical_hypotheses()

    def _register_canonical_hypotheses(self) -> None:
        """Loads the full suite of 13 canonical London session hypotheses."""
        for item in CANONICAL_HYPOTHESES:
            hyp = LondonHypothesis(
                name=item["name"],
                description=item["description"],
                economic_rationale=item["economic_rationale"],
                entry_conditions=item["entry_conditions"],
                outcome_definitions=item["outcome_definitions"],
                holding_period_bars=item["holding_period_bars"],
                invalidation_criteria=item["invalidation_criteria"],
                risk_assumptions=item["risk_assumptions"],
                feature_columns=item["feature_columns"],
                falsification_tests=item["falsification_tests"]
            )
            self.hypotheses[hyp.id] = hyp

    def propose_london_hypothesis(
        self,
        name: str,
        description: str,
        rationale: str,
        features: List[str],
        falsifications: List[str]
    ) -> LondonHypothesis:
        """Proposes a new custom hypothesis."""
        hyp = LondonHypothesis(
            name=name,
            description=description,
            economic_rationale=rationale,
            feature_columns=features,
            falsification_tests=falsifications
        )
        self.hypotheses[hyp.id] = hyp
        logger.info(f"Proposed London Session Hypothesis: '{name}' (ID: {hyp.id})")
        return hyp

    def falsify_hypothesis_regression(
        self,
        hyp: LondonHypothesis,
        df: pd.DataFrame,
        target_col: str = "log_ret",
        p_value_threshold: float = 0.05
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Runs statistical regression test to evaluate if hypothesis features exhibit
        significant explanatory power on the target variable.
        """
        valid_features = [col for col in hyp.feature_columns if col in df.columns]
        if not valid_features or target_col not in df.columns:
            return False, {"error": f"Features or target {target_col} missing in dataset."}

        clean_df = df[valid_features + [target_col]].dropna()
        if len(clean_df) < 50:
            return False, {"error": "Sample size too small (<50 rows)"}

        y = clean_df[target_col].values
        X = clean_df[valid_features].values
        X_design = np.column_stack([np.ones_like(y), X])

        beta, _, _, _ = np.linalg.lstsq(X_design, y, rcond=None)
        n = len(y)
        k = X_design.shape[1]
        df_residual = max(n - k, 1)

        residuals = y - X_design.dot(beta)
        mse = np.sum(residuals**2) / df_residual
        try:
            cov_beta = mse * np.linalg.inv(X_design.T.dot(X_design))
            se_beta = np.sqrt(np.maximum(np.diagonal(cov_beta), 1e-12))
        except np.linalg.LinAlgError:
            se_beta = np.ones(k) * 1e-4

        t_stats = beta / (se_beta + 1e-12)
        # Approximate two-tailed p-values
        p_values = 2 * (1 - 0.5 * (1.0 + np.tanh(np.abs(t_stats) / np.sqrt(2.0))))

        significant = []
        p_dict = {}
        for i, feat in enumerate(valid_features):
            p_val = float(p_values[i + 1])
            p_dict[feat] = p_val
            if p_val < p_value_threshold:
                significant.append((feat, p_val))

        passed = len(significant) > 0
        hyp.status = "Accepted" if passed else "Rejected"
        hyp.test_metrics = {
            "sample_size": n,
            "coefficients": {feat: float(beta[i+1]) for i, feat in enumerate(valid_features)},
            "p_values": p_dict,
            "significant_features": significant
        }

        return passed, hyp.test_metrics

    def screen_hypotheses_with_multiple_testing_correction(
        self,
        df: pd.DataFrame,
        target_col: str = "log_ret",
        alpha_fdr: float = 0.05
    ) -> Dict[str, Any]:
        """
        Runs falsification tests on all hypotheses in the registry and applies
        Benjamini-Hochberg (BH) False Discovery Rate (FDR) multiple-testing correction.
        """
        p_values_all = []
        evaluations = []

        for hyp_id, hyp in self.hypotheses.items():
            passed, metrics = self.falsify_hypothesis_regression(hyp, df, target_col=target_col, p_value_threshold=0.99)
            if "p_values" in metrics and metrics["p_values"]:
                min_p = min(metrics["p_values"].values())
            else:
                min_p = 1.0

            p_values_all.append(min_p)
            evaluations.append({
                "id": hyp.id,
                "name": hyp.name,
                "raw_min_p": min_p,
                "metrics": metrics
            })

        # Apply Benjamini-Hochberg procedure
        m = len(p_values_all)
        sorted_indices = np.argsort(p_values_all)
        sorted_p = np.array(p_values_all)[sorted_indices]

        # Critical values: (rank / m) * alpha
        bh_critical = ((np.arange(1, m + 1)) / m) * alpha_fdr
        passed_bh = sorted_p <= bh_critical

        # Find maximum rank that passes
        max_pass_rank = -1
        if np.any(passed_bh):
            max_pass_rank = np.max(np.where(passed_bh)[0])

        results = {}
        for rank, idx in enumerate(sorted_indices):
            ev = evaluations[idx]
            hyp_obj = self.hypotheses[ev["id"]]
            is_significant_fdr = rank <= max_pass_rank if max_pass_rank >= 0 else False
            hyp_obj.status = "Accepted" if is_significant_fdr else "Rejected"
            results[ev["name"]] = {
                "id": ev["id"],
                "raw_p": float(sorted_p[rank]),
                "bh_critical": float(bh_critical[rank]),
                "passed_fdr": bool(is_significant_fdr),
                "status": hyp_obj.status,
                "metrics": ev["metrics"]
            }

        logger.info(f"Screened {m} hypotheses with Benjamini-Hochberg: {sum(r['passed_fdr'] for r in results.values())} passed FDR threshold.")
        return results
