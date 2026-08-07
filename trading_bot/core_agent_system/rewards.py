"""
Institutional Reward Function - AlphaAlgo UCA V5
Computes risk-adjusted, execution-aware rewards for RL.
"""

from typing import Dict, Any, List
import numpy as np

class InstitutionalRewardFunction:
    """
    Calculates institutional-grade rewards incorporating risk,
    drawdown, and execution quality.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.risk_free_rate = self.config.get('risk_free_rate', 0.02)
        self.dd_penalty_factor = self.config.get('drawdown_penalty', 2.0)
        self.turnover_penalty = self.config.get('turnover_penalty', 0.0001)

    def calculate(self,
                  step_pnl_bps: float,
                  portfolio_state: Dict[str, Any],
                  execution_details: Dict[str, Any]) -> float:
        """
        Calculate step reward.

        Args:
            step_pnl_bps: PnL from this step in basis points.
            portfolio_state: Current equity, drawdown, etc.
            execution_details: Slippage and spread incurred.
        """
        # 1. Base PnL
        reward = step_pnl_bps

        # 2. Drawdown Penalty (Exponential)
        drawdown = portfolio_state.get('drawdown', 0.0)
        if drawdown > 0.05: # Threshold for high penalty
            reward -= (np.exp(drawdown * 10) * self.dd_penalty_factor)

        # 3. Execution Quality Penalty
        slippage = execution_details.get('slippage', 0.0)
        if slippage > 0:
            reward -= slippage * 1000 # Penalize poor execution

        # 4. Consistency Reward (Sharpe-like)
        # In a single step we can't calculate Sharpe, but we can penalize volatility
        # of the returns if we had historical steps.

        # 5. Constraint Violations
        if portfolio_state.get('equity', 0) < self.config.get('min_equity', 5000):
            reward -= 1000 # Critical failure penalty

        return reward
