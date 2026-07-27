"""
High-Fidelity Realistic Backtester for Research OS.
Incorporates spread, commission, slippage, latency drag, and square-root market impact.
Calculates CAGR, Sharpe, Sortino, Calmar, drawdowns, Expected Value, and CVaR tail risk.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
from trading_bot.research.core.interfaces import StandardizedDataset, ResearchStrategy

import logging
logger = logging.getLogger(__name__)


class RealisticResearchBacktester:
    """
    Simulates reality by applying detailed transaction cost models to executable strategies.
    Produces comprehensive scientific risk and return attribution tables.
    """

    def __init__(
        self,
        initial_capital: float = 1000000.0,
        spread_pct: float = 0.0001,       # 1 pip spread for Forex (0.01% of base price)
        commission_pct: float = 0.00005,  # 0.005% commission
        slippage_pct: float = 0.00005,    # 0.005% execution slippage
        latency_drag_secs: float = 0.1,   # 100ms average latency execution delay
        market_impact_coefficient: float = 0.1  # square-root market impact multiplier
    ):
        self.initial_capital = initial_capital
        self.spread_pct = spread_pct
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        self.latency_drag_secs = latency_drag_secs
        self.market_impact_coef = market_impact_coefficient

    def run_backtest(self, strategy: ResearchStrategy, dataset: StandardizedDataset) -> Dict[str, Any]:
        symbol = dataset.symbols[0]
        close_col = f"{symbol}_close"
        if close_col not in dataset.data:
            raise KeyError(f"Close prices '{close_col}' not found in dataset.")

        prices = dataset.data[close_col]
        signals = strategy.generate_signals(dataset)

        capital = self.initial_capital
        position = 0.0
        equity_curve = [self.initial_capital]
        trades = []

        # We model latency drag: strategy signal is generated at T, but executed at T+1
        # For an array of size N, we shift signal by 1 index to simulate latency execution delay
        latency_signals = np.zeros_like(signals)
        latency_signals[1:] = signals[:-1]

        for i in range(1, len(prices)):
            current_price = prices[i]
            prev_signal = latency_signals[i-1]
            current_signal = latency_signals[i]

            # Position changes
            if current_signal != prev_signal:
                # 1. Close out existing position
                if position != 0.0:
                    # Model bid/ask spread and slippage on exit
                    exit_cost_factor = (self.spread_pct / 2.0) + self.slippage_pct
                    exit_price = current_price * (1.0 - exit_cost_factor if position > 0 else 1.0 + exit_cost_factor)

                    # Model commission
                    commission = abs(position) * exit_price * self.commission_pct

                    # Model square-root market impact based on transaction size relative to normal volume
                    # Square-root impact = Daily volatility * coefficient * sqrt(order_size / avg_volume)
                    market_impact = current_price * self.market_impact_coef * np.sqrt(abs(position) / 100000.0)
                    exit_price = exit_price - market_impact if position > 0 else exit_price + market_impact

                    proceeds = position * exit_price - commission
                    capital += proceeds

                    trades.append({
                        "type": "sell" if position > 0 else "buy_to_cover",
                        "price": exit_price,
                        "shares": abs(position),
                        "pnl": proceeds - (position * trades[-1]["price"] if trades else 0),
                        "timestamp": str(dataset.timestamps[i])
                    })
                    position = 0.0

                # 2. Enter new position
                if current_signal != 0.0:
                    # Leverage: allocate 95% of capital to limit margin calls
                    allocated_capital = capital * 0.95
                    # Apply bid/ask spread, commission, slippage and market impact on entry
                    entry_cost_factor = (self.spread_pct / 2.0) + self.slippage_pct
                    entry_price = current_price * (1.0 + entry_cost_factor if current_signal > 0 else 1.0 - entry_cost_factor)

                    shares_to_buy = allocated_capital / entry_price
                    commission = shares_to_buy * entry_price * self.commission_pct

                    # Square-root entry impact
                    market_impact = current_price * self.market_impact_coef * np.sqrt(shares_to_buy / 100000.0)
                    entry_price = entry_price + market_impact if current_signal > 0 else entry_price - market_impact

                    position = shares_to_buy * current_signal
                    capital -= (allocated_capital + commission)

                    trades.append({
                        "type": "buy" if current_signal > 0 else "sell_short",
                        "price": entry_price,
                        "shares": shares_to_buy,
                        "timestamp": str(dataset.timestamps[i])
                    })

            # Calculate current equity
            current_equity = capital + (position * current_price if position != 0.0 else 0.0)
            equity_curve.append(current_equity)

        equity_curve = np.array(equity_curve)
        returns = np.diff(equity_curve) / equity_curve[:-1]

        # Compute advanced metrics
        metrics = self._calculate_metrics(equity_curve, returns, dataset.timestamps, trades)
        metrics["equity_curve"] = equity_curve.tolist()
        metrics["trades_count"] = len(trades)

        return metrics

    def _calculate_metrics(self, equity_curve: np.ndarray, returns: np.ndarray, timestamps: np.ndarray, trades: List[Dict]) -> Dict[str, Any]:
        if len(returns) == 0:
            return {}

        final_equity = float(equity_curve[-1])
        total_return = float((final_equity - self.initial_capital) / self.initial_capital)

        # CAGR (assuming daily/timeframe scaling)
        days = max(1.0, float((timestamps[-1] - timestamps[0]) / np.timedelta64(1, 'D')))
        cagr = float(((final_equity / self.initial_capital) ** (365.25 / days)) - 1.0) if final_equity > 0 else -1.0

        # Volatility
        daily_vol = float(np.std(returns))
        ann_vol = float(daily_vol * np.sqrt(252))

        # Sharpe ratio
        sharpe = float((np.mean(returns) / daily_vol) * np.sqrt(252)) if daily_vol > 0 else 0.0

        # Sortino ratio (downside risk only)
        downside_returns = returns[returns < 0]
        downside_vol = float(np.std(downside_returns)) if len(downside_returns) > 0 else 0.0
        sortino = float((np.mean(returns) / downside_vol) * np.sqrt(252)) if downside_vol > 0 else 0.0

        # Max Drawdown
        peak = np.maximum.accumulate(equity_curve)
        drawdowns = (equity_curve - peak) / peak
        max_dd = float(np.min(drawdowns))

        # Calmar ratio
        calmar = float(cagr / abs(max_dd)) if max_dd != 0 else 0.0

        # Profit Factor
        pnls = [t.get("pnl", 0.0) for t in trades if "pnl" in t]
        gross_profits = sum(p for p in pnls if p > 0)
        gross_losses = sum(abs(p) for p in pnls if p < 0)
        profit_factor = float(gross_profits / gross_losses) if gross_losses > 0 else (float('inf') if gross_profits > 0 else 1.0)

        # Expected Value
        expected_value = float(np.mean(pnls)) if pnls else 0.0

        # CVaR (Conditional Value at Risk at 95% confidence)
        var_95 = float(np.percentile(returns, 5))
        cvar_95 = float(np.mean(returns[returns <= var_95])) if np.sum(returns <= var_95) > 0 else var_95

        return {
            "total_return": total_return,
            "cagr": cagr,
            "sharpe": sharpe,
            "sortino": sortino,
            "max_drawdown": max_dd,
            "calmar": calmar,
            "profit_factor": profit_factor,
            "expected_value": expected_value,
            "cvar_95_tail_risk": cvar_95,
            "exposure_ratio": float(np.sum(np.array(returns) != 0) / len(returns)),
            "turnover_rate": float(len(trades) / days)
        }
