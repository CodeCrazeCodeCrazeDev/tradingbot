"""
Yield Farming Optimizer
============================================================

Scores and ranks DeFi yield opportunities with a conservative
risk adjustment (IL exposure, protocol age, TVL depth).
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class YieldOpportunity:
    pool_id: str
    protocol: str
    apy: float
    tvl_usd: float = 0.0
    il_risk: float = 0.0            # 0..1 impermanent-loss exposure
    protocol_age_days: int = 0
    risk_adjusted_score: float = 0.0


class YieldFarmingOptimizer:
    """Ranks yield opportunities by risk-adjusted return."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.min_tvl = float(self.config.get("min_tvl_usd", 1_000_000))
        self.min_age_days = int(self.config.get("min_protocol_age_days", 90))

    def score(self, opp: YieldOpportunity) -> float:
        """Risk-adjusted score: APY discounted by IL risk and maturity."""
        if opp.tvl_usd < self.min_tvl or opp.protocol_age_days < self.min_age_days:
            return 0.0
        maturity_bonus = min(1.0, opp.protocol_age_days / 365.0)
        tvl_bonus = min(1.0, opp.tvl_usd / 100_000_000)
        score = opp.apy * (1.0 - opp.il_risk) * (0.5 + 0.5 * maturity_bonus) * (0.5 + 0.5 * tvl_bonus)
        opp.risk_adjusted_score = score
        return score

    def rank(self, opportunities: List[YieldOpportunity]) -> List[YieldOpportunity]:
        for opp in opportunities:
            self.score(opp)
        return sorted(opportunities, key=lambda o: o.risk_adjusted_score, reverse=True)
