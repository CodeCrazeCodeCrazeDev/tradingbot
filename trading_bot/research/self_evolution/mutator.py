import logging
import numpy as np
from typing import Any, Dict, Optional

logger = logging.getLogger("AlphaAlgo.SelfEvolution.Mutator")


class ControlledMutator:
    """
    Controlled Mutator.
    Handles guided mutations and compositional crossovers inside the sandbox.
    """

    def __init__(self, mutation_scale: float = 0.15):
        self.mutation_scale = mutation_scale

    def mutate_parameters(self, base_params: Dict[str, Any], adaptive_scale: Optional[float] = None) -> Dict[str, Any]:
        """Applies guided perturbation mutations on strategy parameters (CEUO style)."""
        scale = adaptive_scale if adaptive_scale is not None else self.mutation_scale
        mutated = base_params.copy()

        for key, val in base_params.items():
            if isinstance(val, (int, float)):
                # Guided Gaussian mutation
                noise = np.random.normal(0, scale * abs(val))
                new_val = val + noise
                if isinstance(val, int):
                    new_val = int(round(new_val))
                mutated[key] = new_val

        return mutated

    def compositional_crossover(self, parent_a: Dict[str, Any], parent_b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs functional component crossover.
        Structurally integrates complementary strengths rather than text/parameter averaging.
        """
        child = {}

        # Determine functional components (e.g. feature indicators vs. sizing risk limits)
        for key in set(parent_a.keys()) | set(parent_b.keys()):
            if key in parent_a and key in parent_b:
                # Alternate components structurally or pick the best performing parent's component
                # For demo, alternate keys to simulate structural composition
                if hash(key) % 2 == 0:
                    child[key] = parent_a[key]
                else:
                    child[key] = parent_b[key]
            elif key in parent_a:
                child[key] = parent_a[key]
            else:
                child[key] = parent_b[key]

        return child
