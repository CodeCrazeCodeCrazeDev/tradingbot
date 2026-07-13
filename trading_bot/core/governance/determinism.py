import random
import numpy as np
import torch
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

class DeterministicManager:
    """
    Enforces global seeds and state consistency across the system.
    """
    @staticmethod
    def set_seed(seed: int = 42):
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        # torch.use_deterministic_algorithms(True) # Can cause issues with some ops
        logger.info(f"DeterministicManager: Global seed set to {seed}")

    @staticmethod
    def get_state_hash(config: dict, code_revision: str) -> str:
        state_str = json.dumps(config, sort_keys=True) + code_revision
        return hashlib.sha256(state_str.encode()).hexdigest()
