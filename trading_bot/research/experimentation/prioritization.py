"""
Research Economics and Bayesian Research Prioritization Engine for Research OS.
Calculates Bayesian Expected Value of Information (EVI) and scores proposals under compute budget constraints.
Formulates prioritization as a constrained portfolio allocation problem.
"""

from typing import Dict, Any, List
import numpy as np
import logging
from trading_bot.research.core.interfaces import ResearchPrioritizationPolicy, ResearchProposal

logger = logging.getLogger(__name__)


class BayesianEVIPrioritizationPolicy(ResearchPrioritizationPolicy):
    """
    Computes prior scores based on Bayesian Expected Value of Information (EVI).
    Prioritizes experiments with high expected uncertainty reduction relative to their financial and computational costs.
    """

    def __init__(self, target_sharpe: float = 2.5):
        self.target_sharpe = target_sharpe

    def score_proposal(self, proposal: ResearchProposal) -> float:
        """
        Bayesian EVI score = (Expected alpha * expected_sharpe_improvement) / (Estimated compute + data costs)
        """
        expected_returns = proposal.expected_alpha
        sharpe_improvement = proposal.expected_sharpe_improvement
        uncertainty_reduction = proposal.expected_uncertainty_reduction

        # Total cost is compute cost plus external data acquisition cost
        total_cost = proposal.estimated_compute_hours + proposal.estimated_data_cost
        total_cost = max(0.1, total_cost)

        # Bayesian expected value of knowledge gain
        expected_value_of_info = (expected_returns * sharpe_improvement) + (0.5 * uncertainty_reduction)

        # ROI score = EVI / total_cost
        roi_score = expected_value_of_info / total_cost
        return float(roi_score)


class ResearchEconomicsAllocationOptimizer:
    """
    Optimizes compute and research budget allocations.
    Formulates research pipeline execution as a literal constrained portfolio optimization problem.
    """

    def __init__(self, compute_budget_limit: float = 100.0):
        self.compute_budget_limit = compute_budget_limit

    def allocate_compute_capital(self, proposals: List[ResearchProposal]) -> List[ResearchProposal]:
        """
        Selects a subset of research proposals that maximizes total Expected Information Gain (EIG)
        subject to the total compute budget constraint.
        This solves a 0-1 Knapsack resource-prioritization problem.
        """
        if not proposals:
            return []

        # We can implement a clean greedy approximation of the Knapsack problem:
        # Sort by (EIG / compute_hours) ratio and pack until budget is exhausted.
        def _cost_benefit_ratio(p: ResearchProposal) -> float:
            cost = max(0.1, p.estimated_compute_hours)
            return float(p.expected_uncertainty_reduction / cost)

        sorted_proposals = sorted(proposals, key=_cost_benefit_ratio, reverse=True)

        allocated = []
        accumulated_compute = 0.0

        for prop in sorted_proposals:
            if accumulated_compute + prop.estimated_compute_hours <= self.compute_budget_limit:
                allocated.append(prop)
                accumulated_compute += prop.estimated_compute_hours
            else:
                logger.info(f"Budget limit reached. Postponing proposal '{prop.proposal_id}' (Requires {prop.estimated_compute_hours} hrs).")

        return allocated
