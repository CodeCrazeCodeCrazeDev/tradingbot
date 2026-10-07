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

    _boot_id: Optional[str] = None  # class-level: survives instance reset()

    def __init__(self, seed: int = 42):
        if self._initialized:
            return
        self.seed = seed
        self._id_counter = 0
        self._run_id: Optional[str] = None
        self._enabled = False
        self._initialized = True

    @classmethod
    def _process_namespace(cls) -> str:
        """Per-process identity namespace for deterministic IDs.

        Fresh on every interpreter boot so two different sessions can never
        mint colliding durable IDs, while same-process re-seeding still
        reproduces ID sequences (legacy replay contract).
        """
        if cls._boot_id is None:
            cls._boot_id = uuid.uuid4().hex
        return f"proc-{cls._boot_id}"

    @classmethod
    def set_seed(cls, seed: int):
        """Set the deterministic seed (compat alias for ``enable``).

        Callable both on the class (``DeterministicManager.set_seed(42)``)
        and on an instance — the singleton is reseeded either way.
        """
        inst = cls()
        inst.seed = seed
        inst.enable(seed=seed)

    def enable(self, seed: Optional[int] = None, run_id: Optional[str] = None):
        """Enable deterministic mode with the given seed.

        ``run_id`` namespaces the ID sequence: an explicit value reproduces a
        named run across processes (replay tooling); omitted, the per-process
        namespace applies so unrelated sessions never share identity space.
        """
        if seed is not None:
            self.seed = seed

        self._id_counter = 0
        if run_id is not None:
            self._run_id = str(run_id)
        elif self._run_id is None:
            self._run_id = self._process_namespace()
        self._enabled = True

        # Standard Python seeds. NOTE: PYTHONHASHSEED must be set before the
        # interpreter starts — assigning it here has no effect on hash(), so
        # decision-affecting code must not rely on str hash ordering.
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

    def begin_run(self, run_id: str):
        """Switch the identity namespace to a named run (replay boundary)."""
        self._run_id = str(run_id)
        self._id_counter = 0

    def get_uuid(self) -> str:
        """Get a deterministic or random UUID.

        Deterministic IDs are scoped by (seed, run_id, counter): same seed in
        a different run namespace produces disjoint identities, so replays
        cannot collide with durable records from an earlier run.
        """
        if self._enabled:
            import hashlib
            namespace = self._run_id or self._process_namespace()
            h = hashlib.md5(
                f"{self.seed}|{namespace}|{self._id_counter}".encode()
            ).hexdigest()
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
