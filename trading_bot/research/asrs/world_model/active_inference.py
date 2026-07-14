import math
from typing import Dict, Any, List

class ActiveInferenceWorldModel:
    """
    Active Inference World Model (AIWM).
    Calculates Variational Free Energy (VFE) to update perception states,
    and Expected Free Energy (EFE) to guide optimal planning trajectories.
    """
    def __init__(self):
        pass

    def calculate_variational_free_energy(
        self,
        predicted_mean: float,
        predicted_variance: float,
        observed_value: float,
        prior_entropy: float
    ) -> float:
        """
        Calculates Variational Free Energy (VFE).
        F = D_KL(Q || P) - ln P(y)
        Represents surprise / model deviation.
        """
        if predicted_variance <= 0:
            predicted_variance = 1e-5

        # Surprisal (negative log likelihood of observed data)
        surprisal = 0.5 * math.log(2 * math.pi * predicted_variance) + ((observed_value - predicted_mean) ** 2) / (2 * predicted_variance)

        # Simple KL-divergence mapping
        kl_divergence = 0.5 * (((observed_value - predicted_mean) ** 2) / predicted_variance - 1.0 + math.log(predicted_variance) + prior_entropy)

        return kl_divergence + surprisal

    def calculate_expected_free_energy(
        self,
        epistemic_value: float, # Information gain (maximize)
        pragmatic_value: float # Preference satisfaction (maximize)
    ) -> float:
        """
        Calculates Expected Free Energy (EFE) for policy selection.
        G = - Epistemic_Value - Pragmatic_Value
        Optimal policies minimize EFE.
        """
        return -epistemic_value - pragmatic_value

    def filter_world_belief_update(
        self,
        observations: List[float],
        transition_prior: float
    ) -> Dict[str, float]:
        """Update continuous world trajectory beliefs."""
        if not observations:
            return {"mean": 0.0, "entropy": 1.0}

        avg_obs = sum(observations) / len(observations)
        variance = sum((x - avg_obs) ** 2 for x in observations) / len(observations) if len(observations) > 1 else 1.0

        # Bayesian update combining observations with transition priors
        updated_mean = 0.7 * avg_obs + 0.3 * transition_prior
        entropy = 0.5 * math.log(2 * math.pi * math.e * max(variance, 1e-5))

        return {
            "mean": updated_mean,
            "entropy": entropy
        }
