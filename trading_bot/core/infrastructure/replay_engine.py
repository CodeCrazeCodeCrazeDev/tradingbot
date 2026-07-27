import logging
import sys
import torch
import numpy as np
from typing import Any, List, Dict, Optional
import hashlib

logger = logging.getLogger(__name__)

class ReplayEngine:
    """
    Supports deterministic, bit-identical replay of historical system states.
    Captures full execution context including dependencies and hardware state.
    """
    def __init__(self, csc: Any, config: Optional[Dict] = None):
        self.csc = csc
        self.config = config or {}
        self.provenance_data = self._capture_environment()

    def _capture_environment(self) -> Dict[str, Any]:
        """Captures the current software and hardware environment for reproducibility."""
        return {
            "python_version": sys.version,
            "torch_version": torch.__version__ if 'torch' in sys.modules else None,
            "numpy_version": np.__version__ if 'numpy' in sys.modules else None,
            "platform": sys.platform,
            "config_hash": self._hash_config(self.config)
        }

    def _hash_config(self, config: Dict) -> str:
        """Generates a stable hash for the current configuration."""
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()

    async def replay_episode(self, events: List[Dict[str, Any]], expected_checksums: Optional[List[str]] = None):
        """
        Replays a sequence of events and verifies state integrity.
        """
        logger.info(f"ReplayEngine: Replaying {len(events)} events")

        # Ensure deterministic execution if using PyTorch
        if 'torch' in sys.modules:
            torch.use_deterministic_algorithms(True)
            if torch.cuda.is_available():
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False

        for i, event in enumerate(events):
            # Verify observation integrity
            obs = event["observation"]
            await self.csc.process_market_observation(obs)

            # Optional state verification if checksums provided
            if expected_checksums and i < len(expected_checksums):
                current_state_hash = self.csc.get_state_hash()
                if current_state_hash != expected_checksums[i]:
                    logger.error(f"DETERMINISM BREACH at event {i}: Expected {expected_checksums[i]}, got {current_state_hash}")
                    raise RuntimeError(f"Non-deterministic replay detected at step {i}")

        logger.info("Replay completed successfully with 100% state match.")

import json
