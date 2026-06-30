"""
Prediction Market - USIS Advanced Research Frontier
Agents 'bet' AlphaCredits on their predictions to improve consensus calibration.
"""

import logging
from typing import Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MarketBet:
    agent_id: str
    direction: float
    confidence: float
    amount: float

class AlphaPredictionMarket:
    """
    Internal market where agents stake reputation (AlphaCredits).
    """
    def __init__(self):
        self.credits: Dict[str, float] = {}
        self.active_bets: List[MarketBet] = []

    def place_bet(self, agent_id: str, direction: float, confidence: float):
        if agent_id not in self.credits:
            self.credits[agent_id] = 100.0 # Starting credits

        # Amount staked is proportional to confidence
        amount = self.credits[agent_id] * 0.1 * confidence
        self.credits[agent_id] -= amount

        self.active_bets.append(MarketBet(agent_id, direction, confidence, amount))
        logger.info(f"Agent {agent_id} placed bet of {amount:.2f} AlphaCredits")

    def resolve_market(self, actual_outcome: float):
        """
        Pay out rewards based on direction accuracy.
        """
        for bet in self.active_bets:
            # Simple binary payout: correct direction gets 2x stake
            if (bet.direction > 0 and actual_outcome > 0) or (bet.direction < 0 and actual_outcome < 0):
                payout = bet.amount * 2
                self.credits[bet.agent_id] += payout
                logger.info(f"Agent {bet.agent_id} won {payout:.2f} AlphaCredits")
            else:
                logger.info(f"Agent {bet.agent_id} lost stake of {bet.amount:.2f}")

        self.active_bets = []

    def get_weighted_signal(self) -> float:
        """
        Aggregate signals weighted by the agent's current credit balance (wealth).
        Successful agents carry more weight in the swarm.
        """
        total_wealth = sum(self.credits.values())
        if total_wealth == 0: return 0.0

        weighted_sum = 0.0
        for bet in self.active_bets:
            weight = self.credits[bet.agent_id] / total_wealth
            weighted_sum += bet.direction * weight

        return weighted_sum
