"""
Master Orchestrator Module
"""
from enum import Enum
from typing import Dict, List, Any, Optional

class TradingMode(Enum):
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"

class MasterOrchestrator:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.total_capital = self.config.get('capital', 100000)
        self.max_risk_per_trade = self.config.get('max_risk_per_trade', 0.02)
        self.trading_mode = TradingMode.BALANCED

    def filter_opportunities_by_mode(self, opps: List[Dict], mode: TradingMode) -> List[Dict]:
        min_conf = 0.8 if mode == TradingMode.CONSERVATIVE else 0.6 if mode == TradingMode.BALANCED else 0.4
        return [o for o in opps if o.get('confidence', 0) >= min_conf]

    def calculate_kelly_fraction(self, win_rate: float, win_loss_ratio: float) -> float:
        return (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio if win_loss_ratio > 0 else 0.0

    def determine_action(self, opp: Dict) -> str:
        return opp.get('direction', 'BUY') if opp.get('confidence', 0) >= 0.5 else 'HOLD'

    def extract_symbols(self, opps: List[Dict]) -> List[str]:
        return list(set(o['symbol'] for o in opps if 'symbol' in o))

    def adjust_trading_mode(self, perf_summary: Dict) -> TradingMode:
        win_rate = perf_summary.get('win_rate', 0.5)
        if win_rate > 0.7:
            self.trading_mode = TradingMode.AGGRESSIVE
        elif win_rate < 0.4:
            self.trading_mode = TradingMode.CONSERVATIVE
        else:
            self.trading_mode = TradingMode.BALANCED
        return self.trading_mode

    def get_performance_summary(self) -> Dict[str, Any]:
        return {'total_trades': 10, 'win_rate': 0.6, 'total_pnl': 1500}
