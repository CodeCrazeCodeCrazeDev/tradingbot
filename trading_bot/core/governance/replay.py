import random
import logging
import json
from typing import Any, Dict, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class DeterministicReplayError(ValueError):
    """Exception raised when a replayed decision path deviates from the original outcome."""
    pass

class ReplayManager:
    """
    Deterministic Replay Manager.
    Re-seeds and re-runs historical decision paths from captured provenance metadata
    to ensure 100% reproducible execution traces.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def enforce_determinism(self, seed: int):
        """Force exact seed alignment across standard libraries, numpy, and torch."""
        random.seed(seed)
        np.random.seed(seed)
        try:
            import torch
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
        except ImportError:
            pass

    def replay_decision(self, snapshot: Dict[str, Any], execute_fn: Any) -> Tuple[bool, Dict[str, Any]]:
        """
        Replay a historical decision path given its captured state metadata and a callable execute function.

        Args:
            snapshot: Dictionary containing captured state:
                {
                    "decision_id": str,
                    "seed": int,
                    "market_snapshot": dict,
                    "expected_outcome": dict
                }
            execute_fn: A function that takes (market_snapshot) and returns the computed outcome.

        Returns:
            A tuple of (success, replayed_outcome)
        """
        decision_id = snapshot.get("decision_id", "unknown")
        seed = snapshot.get("seed", 42)
        market_snapshot = snapshot.get("market_snapshot", {})
        expected_outcome = snapshot.get("expected_outcome", {})

        logger.info(f"ReplayManager: Replaying decision {decision_id} (Seed: {seed})")

        # 1. Align determinism seeds
        self.enforce_determinism(seed)

        # 2. Execute decision pipeline
        replayed_outcome = execute_fn(market_snapshot)

        # 3. Compare outcomes for exact equivalence
        for key, expected_val in expected_outcome.items():
            if key not in replayed_outcome:
                raise DeterministicReplayError(
                    f"Replay Deviation for decision {decision_id}: missing key '{key}' in replayed outcome"
                )
            replayed_val = replayed_outcome[key]
            if replayed_val != expected_val:
                raise DeterministicReplayError(
                    f"Replay Deviation for decision {decision_id} on key '{key}': "
                    f"expected '{expected_val}', got '{replayed_val}'"
                )

        logger.info(f"ReplayManager: Decision {decision_id} replayed successfully with 100% determinism!")
        return True, replayed_outcome
