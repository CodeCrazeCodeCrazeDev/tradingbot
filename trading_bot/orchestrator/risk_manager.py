"""
Risk Manager Module
"""
from typing import Dict, List, Tuple, Any, Optional

class RiskManager:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def calculate_position_weights(self, positions: Dict[str, Dict]) -> Dict[str, float]:
        tot = sum(p.get('value', 0) for p in positions.values())
        return {k: p.get('value', 0) / tot for k, p in positions.items()} if tot > 0 else {}

    def check_concentration_risk(self, weights: Dict[str, float], max_weight: float = 0.3) -> bool:
        return any(w > max_weight for w in weights.values())

    def stress_test(self, positions: Dict[str, Dict], market_shock: float = -0.1) -> float:
        tot_val = sum(p.get('value', 0) for p in positions.values())
        return tot_val * market_shock

    def validate_trade(self, trade: Dict, current_positions: Dict) -> Tuple[bool, str]:
        return True, "Trade approved"

class PositionSizer:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def calculate_kelly_fraction(self, win_rate: float, win_loss_ratio: float) -> float:
        return (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio if win_loss_ratio > 0 else 0.0

    def fixed_fractional(self, account_size: float, risk_pct: float) -> float:
        return account_size * risk_pct

    def risk_parity(self, volatilities: List[float], target_risk: float = 0.1) -> List[float]:
        inv_vols = [1 / v if v > 0 else 0 for v in volatilities]
        tot = sum(inv_vols)
        return [iv / tot for iv in inv_vols] if tot > 0 else [1 / len(volatilities)] * len(volatilities)

class DrawdownController:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.equity_peak = 100000.0

    def check_drawdown(self, current_equity: float) -> Tuple[str, Dict[str, Any]]:
        if current_equity > self.equity_peak:
            self.equity_peak = current_equity
        dd = (self.equity_peak - current_equity) / self.equity_peak if self.equity_peak > 0 else 0.0
        if dd >= 0.20:
            return "stop", {"drawdown": dd, "action": "stop_all_trading", "emergency_exit": True, "new_trades_allowed": False}
        elif dd >= 0.05:
            return "warning", {"drawdown": dd, "action": "warning", "new_trades_allowed": True}
        return "normal", {"drawdown": dd, "action": "none", "new_trades_allowed": True}
