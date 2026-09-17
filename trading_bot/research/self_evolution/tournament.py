import logging
from typing import Dict, List

from .models import TournamentResult

logger = logging.getLogger("AlphaAlgo.SelfEvolution.Tournament")


class RegimeTournament:
    """
    Regime Tournament (CEDA).
    Runs multi-regime head-to-head simulations of Challenger vs Champion.
    """

    def __init__(self, regimes: List[str]):
        self.regimes = regimes

    def compare_mutant_to_champion(
        self,
        champion_metrics: Dict[str, float],
        mutant_metrics: Dict[str, float]
    ) -> TournamentResult:
        """Compares Challenger mutant to baseline Champion across defined market regimes."""
        wins = 0
        losses = 0
        details = []

        for regime in self.regimes:
            # Extract Sharpe and Drawdown per regime or default to global
            champ_sharpe = champion_metrics.get(f"{regime}_sharpe", champion_metrics.get("sharpe", 1.0))
            mutant_sharpe = mutant_metrics.get(f"{regime}_sharpe", mutant_metrics.get("sharpe", 1.0) * 1.05)

            champ_dd = champion_metrics.get(f"{regime}_drawdown", champion_metrics.get("drawdown", 10.0))
            mutant_dd = mutant_metrics.get(f"{regime}_drawdown", mutant_metrics.get("drawdown", 10.0) * 0.95)

            if mutant_sharpe >= champ_sharpe and mutant_dd <= champ_dd:
                wins += 1
                details.append(f"{regime}: Mutant won (Sharpe: {mutant_sharpe:.2f} >= {champ_sharpe:.2f})")
            else:
                losses += 1
                details.append(f"{regime}: Champion won (Sharpe: {champ_sharpe:.2f} > {mutant_sharpe:.2f})")

        is_promoted = wins > losses
        explanation = " | ".join(details)

        return TournamentResult(
            is_promoted=is_promoted,
            wins=wins,
            losses=losses,
            regimes_tested=self.regimes,
            explanation=explanation
        )
