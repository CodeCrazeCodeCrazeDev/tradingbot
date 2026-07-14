import math
from typing import Dict, Any, List

class CostAwareResearchPlanner:
    """
    Cost-Aware Research Planner (CARP).
    Computes Expected Return on Engineering Investment (EROI) to prioritize
    which research pathways are most computationally and strategically cost-effective.
    """
    def __init__(self, compute_unit_rate: float = 1.20):
        # Dollar rate per compute hour (CPU/GPU)
        self.compute_unit_rate = compute_unit_rate

    def calculate_eroi(
        self,
        expected_improvement: float,
        probability_success: float,
        difficulty_score: float, # 1.0 to 10.0 scale
        estimated_compute_hours: float,
        systemic_risk_index: float # 1.0 to 5.0 scale
    ) -> float:
        """
        Calculates the exact Engineering ROI utilizing the CARP expected utility formula.

        EROI = (Expected Benefit * Probability Success - Compute Cost) / (Effort + Risk)
        """
        # Multi-attribute benefit scaling
        expected_benefit = expected_improvement * 100.0
        compute_cost = estimated_compute_hours * self.compute_unit_rate

        numerator = (expected_benefit * probability_success) - compute_cost
        denominator = difficulty_score + systemic_risk_index

        # Ensure division by zero safety
        if denominator <= 0:
            denominator = 1.0

        return numerator / denominator

    def prioritize_hypotheses(
        self,
        hypotheses: List[Any],
        paper_solutions_map: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Rank and order hypotheses mapped to papers based on EROI."""
        ranked_experiments = []
        for hyp in hypotheses:
            matched_papers = paper_solutions_map.get(hyp.target_domain, [])
            for paper in matched_papers:
                properties = paper.get("properties", {})

                # Retrieve parameters
                difficulty = properties.get("implementation_difficulty", 5.0)
                expected_roi = properties.get("expected_roi", 0.20)

                # Map compute bounds
                compute_req = properties.get("compute_requirements", "CPU_MED")
                comp_hours = 12.0 if "HIGH" in compute_req else (4.0 if "MED" in compute_req else 1.0)

                # Hardcoded systemic risk factor (csc core has higher impact risk than basic logs)
                risk_index = 4.0 if "core" in hyp.target_module else 2.0

                eroi = self.calculate_eroi(
                    expected_improvement=hyp.expected_improvement,
                    probability_success=0.80 if difficulty < 5.0 else 0.55,
                    difficulty_score=difficulty,
                    estimated_compute_hours=comp_hours,
                    systemic_risk_index=risk_index
                )

                ranked_experiments.append({
                    "hypothesis": hyp,
                    "target_paper": paper,
                    "eroi": eroi,
                    "estimated_compute_hours": comp_hours,
                    "difficulty_score": difficulty
                })

        # Sort in descending order of EROI
        ranked_experiments.sort(key=lambda x: x["eroi"], reverse=True)
        return ranked_experiments
