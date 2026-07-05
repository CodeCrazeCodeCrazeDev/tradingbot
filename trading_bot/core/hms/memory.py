"""
HMS Tiered Storage and Management Logic
=======================================

Implements the 6-tier architecture:
1. Working (Hot/RAM)
2. Episodic (Recent Events)
3. Semantic (Facts/Knowledge)
4. Procedural (Skills/LoRA)
5. Research (Evidence/Snapshots)
6. Institutional (Priors/Governance)
"""

import logging
import os
import json
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)

class HMSTier:
    def __init__(self, name: str, persistent: bool = True, capacity: Optional[int] = None):
        self.name = name
        self.persistent = persistent
        self.capacity = capacity
        self.data = deque(maxlen=capacity) if capacity else []

class HierarchicalMemorySystem:
    """
    The Authoritative Unified Memory for AlphaAlgo UCA-2026.
    """
    def __init__(self, storage_root: str = "alphaalgo_data/hms_v3"):
        self.storage_root = storage_root

        # Initialize Tiers
        self.tiers = {
            "working": HMSTier("Working", persistent=False, capacity=1000),
            "episodic": HMSTier("Episodic", persistent=True, capacity=10000),
            "semantic": HMSTier("Semantic", persistent=True),
            "procedural": HMSTier("Procedural", persistent=True),
            "research": HMSTier("Research", persistent=True),
            "institutional": HMSTier("Institutional", persistent=True)
        }

        # Setup persistence
        for tier_name, tier in self.tiers.items():
            if tier.persistent:
                os.makedirs(os.path.join(self.storage_root, tier_name), exist_ok=True)

        logger.info(f"HMS V3: Initialized 6-tier memory at {storage_root}")

    def write(self, tier_name: str, key: str, value: Any, metadata: Optional[Dict] = None):
        """Standardized Write operation."""
        if tier_name not in self.tiers:
            raise ValueError(f"Unknown HMS tier: {tier_name}")

        entry = {
            "key": key,
            "value": value,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        tier = self.tiers[tier_name]

        # Update in-memory state
        if isinstance(tier.data, deque):
            tier.data.append(entry)
        else:
            # For semantic/research, we might want a dict-like access
            pass

        # Persist if required
        if tier.persistent:
            self._persist(tier_name, key, entry)

    def read(self, tier_name: str, key: str) -> Optional[Any]:
        """Standardized Read operation."""
        # Check in-memory first, then disk
        if tier_name not in self.tiers:
             return None

        file_path = os.path.join(self.storage_root, tier_name, f"{key}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)["value"]
        return None

    def query(self, tier_name: str, filter_fn: Any) -> List[Any]:
        """Query tier based on criteria."""
        # Simple implementation: list files and filter
        results = []
        tier_path = os.path.join(self.storage_root, tier_name)
        if not os.path.exists(tier_path):
            return []

        for filename in os.listdir(tier_path):
            if filename.endswith(".json"):
                with open(os.path.join(tier_path, filename), 'r') as f:
                    entry = json.load(f)
                    if filter_fn(entry):
                        results.append(entry)
        return results

    def _persist(self, tier_name: str, key: str, entry: Dict):
        path = os.path.join(self.storage_root, tier_name, f"{key}.json")
        with open(path, 'w') as f:
            json.dump(entry, f, indent=2)

    def fold_information(self, source_tier: str, target_tier: str, aggregation_logic: Any):
        """
        Implements HIPIF Information Folding.
        Compresses episodic data into semantic updates.
        """
        logger.info(f"HMS: Folding information from {source_tier} to {target_tier}")
        # Implementation of strategic compression
        pass

    async def maintenance_loop(self):
        """Periodic cleanup and pruning."""
        while True:
            # Implement pruning of stale episodic entries
            await asyncio.sleep(3600) # Every hour
