import random
from typing import List, Dict, Any, Tuple

class SpeciatedEvolutionEngine:
    """
    Speciated Evolution Engine (SEE).
    Implements continuous CMA-ES style distribution adaptation and discrete NSGA-II
    Pareto non-dominated sorting.
    """
    def __init__(self, population_size: int = 10):
        self.population_size = population_size

    def cma_es_step(
        self,
        mean: float,
        step_size: float,
        best_candidates: List[float]
    ) -> Tuple[float, float]:
        """
        Lightweight mathematical CMA-ES mean and step size update.
        Adjusts parameters dynamically toward high-performing elites.
        """
        if not best_candidates:
            return mean, step_size

        # 1. Update Mean (average of elite candidates)
        new_mean = sum(best_candidates) / len(best_candidates)

        # 2. Update Step Size (shrink if variance is small, expand if scattered)
        variance = sum((x - new_mean) ** 2 for x in best_candidates) / len(best_candidates)
        new_step_size = step_size * 0.95 + math_std(variance) * 0.05

        return new_mean, max(new_step_size, 0.01)

    def sort_pareto_fronts(
        self,
        candidates: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        NSGA-II Non-dominated Sorting.
        Groups candidates into Pareto fronts based on two objectives:
        Objective 1: Expected Return (maximize)
        Objective 2: Latency / Resource Overheads (minimize)
        """
        fronts: List[List[Dict[str, Any]]] = [[]]

        for p in candidates:
            p["domination_count"] = 0
            p["dominated_set"] = []

            for q in candidates:
                # Objectives: [return_val, latency_val]
                p_ret, p_lat = p["objectives"]
                q_ret, q_lat = q["objectives"]

                # Check if p dominates q
                # p dominates q if p has higher return and lower latency
                if (p_ret >= q_ret and p_lat <= q_lat) and (p_ret > q_ret or p_lat < q_lat):
                    p["dominated_set"].append(q)
                elif (q_ret >= p_ret and q_lat <= p_lat) and (q_ret > p_ret or q_lat < p_lat):
                    p["domination_count"] += 1

            if p["domination_count"] == 0:
                p["rank"] = 0
                fronts[0].append(p)

        i = 0
        while len(fronts[i]) > 0:
            next_front = []
            for p in fronts[i]:
                for q in p["dominated_set"]:
                    q["domination_count"] -= 1
                    if q["domination_count"] == 0:
                        q["rank"] = i + 1
                        next_front.append(q)
            i += 1
            fronts.append(next_front)

        return [f for f in fronts if len(f) > 0]

def math_std(variance: float) -> float:
    return variance ** 0.5
