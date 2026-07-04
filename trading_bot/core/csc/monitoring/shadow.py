"""
Shadow Mode Monitor - UCA-2026 Validation

Runs the Cognitive System Controller (CSC) alongside legacy orchestrators.
Compares decisions, risk, and expected value (EV) in real-time without
affecting production traffic. Used to establish evidence for migration.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ShadowMonitor:
    """
    Validation engine for CSC vs. Legacy performance.
    UCA-2026 Principle: Evidence-Based Migration.
    """

    def __init__(self):
        self.comparisons: List[Dict[str, Any]] = []
        logger.info("UCA-2026 Shadow Monitor initialized.")

    def record_comparison(self, task: str, legacy_result: Any, csc_result: Any):
        """
        Records the output of both systems for a single task.
        """
        comparison = {
            'timestamp': datetime.now(),
            'task': task,
            'legacy': self._summarize(legacy_result),
            'csc': self._summarize(csc_result),
            'divergence': self._calculate_divergence(legacy_result, csc_result)
        }
        self.comparisons.append(comparison)

        # Log critical divergences
        if comparison['divergence'] > 0.5:
            logger.warning(f"SHADOW_DIVERGENCE: CSC and Legacy significantly disagree on task '{task}'.")
        else:
            logger.info(f"SHADOW_MATCH: CSC and Legacy consistent on task '{task}'.")

    def _summarize(self, result: Any) -> Dict[str, Any]:
        """Extracts key metrics from a decision/result."""
        if hasattr(result, 'expected_value'):
            return {
                'value': result.expected_value,
                'confidence': result.confidence,
                'safe': result.is_safe()
            }
        return {'raw': str(result)}

    def _calculate_divergence(self, legacy: Any, csc: Any) -> float:
        """Calculates a normalized divergence score [0, 1]."""
        # Simplistic divergence logic for bootstrap
        try:
            l_val = legacy.expected_value if hasattr(legacy, 'expected_value') else 0.5
            c_val = csc.expected_value if hasattr(csc, 'expected_value') else 0.5
            return abs(l_val - c_val)
        except Exception:
            return 1.0

    def get_migration_readiness(self) -> Dict[str, Any]:
        """Calculates readiness based on historical consistency."""
        if not self.comparisons:
            return {'status': 'no_data', 'readiness': 0.0}

        avg_divergence = sum(c['divergence'] for c in self.comparisons) / len(self.comparisons)
        readiness = 1.0 - avg_divergence

        return {
            'status': 'verified' if readiness > 0.9 else 'testing',
            'readiness': readiness,
            'total_samples': len(self.comparisons)
        }
