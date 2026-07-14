import math
from typing import List, Dict, Any

class StrategyEvolutionLaboratory:
    """
    Strategy Evolution Laboratory (SEL).
    Provides core financial telemetry engines calculating Sharpe, Sortino,
    Calmar, CVaR, Turnover, and Slippage costs.
    """
    def __init__(self, risk_free_rate: float = 0.04):
        self.risk_free_rate = risk_free_rate

    def calculate_sharpe(self, returns: List[float]) -> float:
        if not returns or len(returns) < 2:
            return 0.0
        avg_ret = sum(returns) / len(returns)
        variance = sum((r - avg_ret) ** 2 for r in returns) / (len(returns) - 1)
        if variance <= 0:
            return 0.0
        annualized_ret = avg_ret * 252 - self.risk_free_rate
        annualized_vol = (variance ** 0.5) * (252 ** 0.5)
        return annualized_ret / annualized_vol

    def calculate_sortino(self, returns: List[float]) -> float:
        if not returns or len(returns) < 2:
            return 0.0
        avg_ret = sum(returns) / len(returns)
        downside_returns = [min(0.0, r) for r in returns]
        downside_variance = sum(r ** 2 for r in downside_returns) / len(returns)
        if downside_variance <= 0:
            return 0.0
        annualized_ret = avg_ret * 252 - self.risk_free_rate
        downside_deviation = (downside_variance ** 0.5) * (252 ** 0.5)
        return annualized_ret / downside_deviation

    def calculate_cvar_95(self, returns: List[float]) -> float:
        if not returns:
            return 0.0
        sorted_rets = sorted(returns)
        # Find 5th percentile index
        cutoff_idx = max(1, int(len(sorted_rets) * 0.05))
        tail_losses = sorted_rets[:cutoff_idx]
        return -sum(tail_losses) / len(tail_losses)

    def calculate_turnover_penalty(self, weights: List[float], prev_weights: List[float]) -> float:
        if not weights or not prev_weights or len(weights) != len(prev_weights):
            return 0.0
        total_delta = sum(abs(w - pw) for w, pw in zip(weights, prev_weights))
        return total_delta / len(weights)

    def compute_portfolio_fitness(
        self,
        returns: List[float],
        weights_history: List[List[float]],
        slippage_bps: float
    ) -> Dict[str, float]:
        """Unified Portfolio Fitness Score calculation."""
        sharpe = self.calculate_sharpe(returns)
        sortino = self.calculate_sortino(returns)
        cvar = self.calculate_cvar_95(returns)

        # Calculate average turnover
        turnovers = []
        for i in range(1, len(weights_history)):
            turnovers.append(self.calculate_turnover_penalty(weights_history[i], weights_history[i-1]))
        avg_turnover = sum(turnovers) / len(turnovers) if turnovers else 0.0

        # Scale fitness down based on turnover churn and slippage
        fitness = (sharpe * 0.35 + sortino * 0.35) - (cvar * 0.15) - (avg_turnover * 0.10) - (slippage_bps * 0.05)

        return {
            "sharpe": sharpe,
            "sortino": sortino,
            "cvar": cvar,
            "turnover": avg_turnover,
            "fitness": max(fitness, -10.0)
        }
