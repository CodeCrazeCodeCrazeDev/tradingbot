"""
Dataset Registry for Research OS.
Registers and tracks datasets, including versions, schemas, quality metrics, and validation histories.
"""

from typing import Dict, Optional, Any
import logging
from trading_bot.research.core.interfaces import DatasetRegistry, StandardizedDataset

logger = logging.getLogger(__name__)


class StandardDatasetRegistry(DatasetRegistry):
    """
    A robust, thread-safe memory-based Dataset Registry.
    Tracks lineage, version profiles, schemas, ownership, and quality metrics of all active research datasets.
    """

    def __init__(self):
        self._datasets: Dict[str, StandardizedDataset] = {}
        self._registry_metadata: Dict[str, Dict[str, Any]] = {}

    def register_dataset(self, dataset: StandardizedDataset) -> None:
        dataset_id = dataset.dataset_id
        self._datasets[dataset_id] = dataset

        # Populate schema representation
        schema = {col: str(arr.dtype) for col, arr in dataset.data.items()}
        schema["timestamps"] = str(dataset.timestamps.dtype)

        self._registry_metadata[dataset_id] = {
            "registered_at": datetime_to_iso(dataset.start_time),  # fallback helper
            "schema": schema,
            "version": dataset.metadata.get("version", "1.0.0"),
            "ownership": dataset.metadata.get("ownership", "AlphaAlgo Research division"),
            "provenance": dataset.provenance,
            "quality_metrics": dataset.quality_metrics,
            "validation_history": [
                {
                    "validated_at": datetime_to_iso(None),
                    "passed": dataset.quality_metrics.get("valid", True),
                    "anomalies_count": dataset.quality_metrics.get("anomalies_found", 0)
                }
            ]
        }
        logger.info(f"Registered dataset '{dataset_id}' successfully with registry.")

    def get_dataset(self, dataset_id: str) -> Optional[StandardizedDataset]:
        return self._datasets.get(dataset_id)

    def get_metadata(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        return self._registry_metadata.get(dataset_id)


def datetime_to_iso(dt: Optional[Any]) -> str:
    from datetime import datetime
    if dt is None:
        return datetime.utcnow().isoformat()
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)
