"""
Deterministic Manager - UCA V5 Core Component
=============================================

Enforces deterministic seeds and non-random ID generation for reproducibility.
Implements the Institutional Reproducibility Policy (2026).
"""

import random
import os
import logging
import threading
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

class DeterministicManager:
    """
    Authoritative manager for system-wide determinism.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DeterministicManager, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, seed: int = 42):
        if self._initialized:
            return
        self.seed = seed
        self._id_counter = 0
        self._enabled = False
        self._initialized = True

    def enable(self, seed: Optional[int] = None):
        """Enable deterministic mode with the given seed."""
        if seed is not None:
            self.seed = seed

        self._id_counter = 0
        self._enabled = True

        # Standard Python seeds
        random.seed(self.seed)
        os.environ['PYTHONHASHSEED'] = str(self.seed)

        try:
            import numpy as np
            np.random.seed(self.seed)
        except ImportError:
            pass

        try:
            import torch
            torch.manual_seed(self.seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(self.seed)
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
        except ImportError:
            pass

        logger.info(f"Deterministic mode ENABLED (Seed: {self.seed})")

    def disable(self):
        """Disable deterministic mode."""
        self._enabled = False
        logger.info("Deterministic mode DISABLED")

    def get_uuid(self) -> str:
        """Get a deterministic or random UUID."""
        if self._enabled:
            # Generate a deterministic UUID based on seed and counter
            import hashlib
            h = hashlib.md5(f"{self.seed}-{self._id_counter}".encode()).hexdigest()
            self._id_counter += 1
            return str(uuid.UUID(h))
        return str(uuid.uuid4())

    @classmethod
    def reset(cls):
        """Reset the singleton instance."""
        with cls._lock:
            cls._instance = None

# Global access point
determinism = DeterministicManager()
