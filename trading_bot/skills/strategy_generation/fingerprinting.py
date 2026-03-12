"""
Skill #75: Strategy Fingerprinting
==================================

Creates unique fingerprints for strategies to detect similarities.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class FingerprintResult:
    """Strategy fingerprinting result."""
    fingerprint: np.ndarray
    similar_strategies: List[str]
    uniqueness_score: float
    trading_signal: str


class StrategyFingerprinting:
    """Creates strategy fingerprints."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.fingerprint_db: Dict[str, np.ndarray] = {}
            logger.info("StrategyFingerprinting initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def create_fingerprint(self, strategy_returns: np.ndarray, name: str) -> FingerprintResult:
        """Create fingerprint for strategy."""
        try:
            if len(strategy_returns) < 20:
                return self._create_empty_result()
        
            # Create fingerprint from statistical properties
            fingerprint = np.array([
                np.mean(strategy_returns),
                np.std(strategy_returns),
                np.min(strategy_returns),
                np.max(strategy_returns),
                np.percentile(strategy_returns, 25),
                np.percentile(strategy_returns, 75),
                self._autocorr(strategy_returns, 1),
                self._autocorr(strategy_returns, 5),
                np.mean(strategy_returns > 0),
                np.mean(np.abs(strategy_returns)),
            ])
        
            # Find similar strategies
            similar = []
            for db_name, db_fp in self.fingerprint_db.items():
                similarity = 1 - np.linalg.norm(fingerprint - db_fp) / (np.linalg.norm(fingerprint) + 1e-10)
                if similarity > 0.8:
                    similar.append(db_name)
        
            # Store fingerprint
            self.fingerprint_db[name] = fingerprint
        
            uniqueness = 1 - len(similar) / (len(self.fingerprint_db) + 1e-10)
        
            return FingerprintResult(
                fingerprint=fingerprint, similar_strategies=similar,
                uniqueness_score=uniqueness,
                trading_signal=f"FINGERPRINT: {len(similar)} similar strategies, uniqueness {uniqueness:.0%}"
            )
        except Exception as e:
            logger.error(f"Error in create_fingerprint: {e}")
            raise
    
    def _autocorr(self, x: np.ndarray, lag: int) -> float:
        """Calculate autocorrelation."""
        try:
            if len(x) <= lag:
                return 0
            return np.corrcoef(x[:-lag], x[lag:])[0, 1]
        except Exception as e:
            logger.error(f"Error in _autocorr: {e}")
            raise
    
    def _create_empty_result(self) -> FingerprintResult:
        return FingerprintResult(np.array([]), [], 0, "Insufficient data")
