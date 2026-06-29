import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import numpy as np
from .memory import ImprovementMemory

logger = logging.getLogger(__name__)

class ImprovementOptimizer:
    """
    Meta-improvement layer that learns from historical experiments.
    Optimizes hypothesis generation and experiment ranking.
    """

    def __init__(self, memory: ImprovementMemory, config: Optional[Dict[str, Any]] = None):
        self.memory = memory
        self.config = config or {}

    async def analyze_meta_performance(self) -> Dict[str, Any]:
        """
        Analyze which types of experiments have the highest success rates.
        """
        history = self.memory.get_recent_experiments(limit=500)
        if not history:
            return {"status": "insufficient_data"}

        domain_performance = {}
        for exp in history:
            domain = exp["domain"]
            if domain not in domain_performance:
                domain_performance[domain] = {"total": 0, "success": 0, "total_score": 0.0}

            domain_performance[domain]["total"] += 1
            if exp["status"] == "completed":
                domain_performance[domain]["success"] += 1
                domain_performance[domain]["total_score"] += exp["result_score"] or 0

        # Calculate success rates and average scores
        report = {}
        for domain, stats in domain_performance.items():
            report[domain] = {
                "success_rate": stats["success"] / stats["total"],
                "avg_score": stats["total_score"] / stats["success"] if stats["success"] > 0 else 0,
                "total_experiments": stats["total"]
            }

        return report

    def rank_proposals(self, domain: str, proposals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank improvement proposals based on meta-learned priors.
        """
        if not proposals:
            return []

        # For now, a simple heuristic: rank by estimated impact and prior domain success
        # In a more advanced version, this would use a model trained on ImprovementMemory
        for prop in proposals:
            prop["meta_rank"] = prop.get("estimated_impact", 0.5)

        return sorted(proposals, key=lambda x: x["meta_rank"], reverse=True)

    async def generate_meta_hypothesis(self) -> str:
        """
        Generate a hypothesis about how to improve the improvement process itself.
        """
        analysis = await self.analyze_meta_performance()

        if analysis.get("status") == "insufficient_data":
            return "Meta-Hypothesis: Continuous diversification of hypothesis generation methods will prevent local optima in system evolution."

        # Simple rule-based meta-discovery
        weakest_domain = None
        min_success = 1.0

        for domain, stats in analysis.items():
            if not isinstance(stats, dict): continue
            if stats.get("success_rate", 1.0) < min_success:
                min_success = stats["success_rate"]
                weakest_domain = domain

        if weakest_domain:
            return f"Meta-Hypothesis: Increasing the rigor of pre-simulation filters in {weakest_domain} will increase deployment success rate."

        return "Meta-Hypothesis: Continuous diversification of hypothesis generation methods will prevent local optima in system evolution."
