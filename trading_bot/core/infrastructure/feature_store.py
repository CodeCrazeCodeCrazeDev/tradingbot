import logging
import pandas as pd
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class InstitutionalFeatureStore:
    """Centralized, versioned repository for all features used in trading models."""
    def __init__(self):
        self.store = {}
        self.versions = {}

    def push_features(self, name: str, data: pd.DataFrame, version: str = "v1"):
        self.store[name] = data
        self.versions[name] = version
        logger.info(f"FeatureStore: Pushed {name} ({version})")

    def pull_features(self, name: str) -> Optional[pd.DataFrame]:
        return self.store.get(name)
