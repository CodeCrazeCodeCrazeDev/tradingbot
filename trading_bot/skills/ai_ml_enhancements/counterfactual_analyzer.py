"""
Skill #26: Counterfactual Analyzer
==================================

Analyzes "what-if" scenarios to understand potential
alternative outcomes and decision impacts.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class Counterfactual:
    """Single counterfactual scenario."""
    scenario_name: str
    original_value: float
    counterfactual_value: float
    outcome_change: float
    probability: float


@dataclass
class CounterfactualResult:
    """Counterfactual analysis result."""
    counterfactuals: List[Counterfactual]
    most_impactful: Counterfactual
    regret_analysis: Dict[str, float]
    optimal_action: str
    trading_signal: str


class CounterfactualAnalyzer:
    """Counterfactual analysis for trading decisions."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            logger.info("CounterfactualAnalyzer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(
        self,
        prices: np.ndarray,
        actions_taken: List[str],
        outcomes: List[float]
    ) -> CounterfactualResult:
        """Analyze counterfactual scenarios."""
        try:
            if len(prices) < 10:
                return self._create_empty_result()
        
            counterfactuals = []
        
            # What if we had bought instead of sold (and vice versa)
            for i, (action, outcome) in enumerate(zip(actions_taken, outcomes)):
                cf_outcome = -outcome  # Opposite action
                counterfactuals.append(Counterfactual(
                    scenario_name=f"opposite_action_{i}",
                    original_value=outcome,
                    counterfactual_value=cf_outcome,
                    outcome_change=cf_outcome - outcome,
                    probability=0.5
                ))
        
            # What if we had waited
            for i in range(len(outcomes) - 1):
                wait_outcome = outcomes[i + 1] - outcomes[i]
                counterfactuals.append(Counterfactual(
                    scenario_name=f"wait_one_period_{i}",
                    original_value=outcomes[i],
                    counterfactual_value=wait_outcome,
                    outcome_change=wait_outcome - outcomes[i],
                    probability=0.3
                ))
        
            # Find most impactful
            most_impactful = max(counterfactuals, key=lambda c: abs(c.outcome_change)) if counterfactuals else None
        
            # Regret analysis
            regret = self._calculate_regret(counterfactuals)
        
            # Optimal action
            optimal = self._determine_optimal_action(counterfactuals, prices)
        
            signal = self._generate_signal(most_impactful, regret)
        
            return CounterfactualResult(
                counterfactuals=counterfactuals[:10],
                most_impactful=most_impactful,
                regret_analysis=regret,
                optimal_action=optimal,
                trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
    
    def _calculate_regret(self, counterfactuals: List[Counterfactual]) -> Dict[str, float]:
        """Calculate regret for different action types."""
        try:
            regret = {'buy': 0, 'sell': 0, 'hold': 0}
        
            for cf in counterfactuals:
                if cf.outcome_change > 0:
                    if 'opposite' in cf.scenario_name:
                        regret['hold'] += cf.outcome_change
                    elif 'wait' in cf.scenario_name:
                        regret['buy'] += cf.outcome_change
        
            return regret
        except Exception as e:
            logger.error(f"Error in _calculate_regret: {e}")
            raise
    
    def _determine_optimal_action(
        self,
        counterfactuals: List[Counterfactual],
        prices: np.ndarray
    ) -> str:
        """Determine optimal action based on counterfactuals."""
        try:
            if not counterfactuals:
                return "hold"
        
            avg_change = np.mean([cf.outcome_change for cf in counterfactuals])
            if avg_change > 0.01:
                return "buy"
            elif avg_change < -0.01:
                return "sell"
            return "hold"
        except Exception as e:
            logger.error(f"Error in _determine_optimal_action: {e}")
            raise
    
    def _generate_signal(
        self,
        most_impactful: Optional[Counterfactual],
        regret: Dict[str, float]
    ) -> str:
        """Generate trading signal."""
        try:
            if not most_impactful:
                return "NEUTRAL: No counterfactual data"
        
            min_regret_action = min(regret, key=regret.get)
            return f"OPTIMAL: {min_regret_action.upper()} (lowest regret: {regret[min_regret_action]:.2f})"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _create_empty_result(self) -> CounterfactualResult:
        """Create empty result."""
        return CounterfactualResult(
            counterfactuals=[],
            most_impactful=None,
            regret_analysis={},
            optimal_action="hold",
            trading_signal="Insufficient data"
        )
