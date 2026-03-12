"""
Skill #58: Contagion Risk Monitor
=================================

Monitors for contagion risk spreading across assets.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class ContagionResult:
    """Contagion risk result."""
    contagion_score: float
    affected_assets: List[str]
    spillover_probability: float
    safe_havens: List[str]
    trading_signal: str


class ContagionRiskMonitor:
    """Monitors contagion risk across assets."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            logger.info("ContagionRiskMonitor initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def monitor(self, returns_dict: Dict[str, np.ndarray]) -> ContagionResult:
        """Monitor for contagion risk."""
        try:
            if len(returns_dict) < 2:
                return self._create_empty_result()
        
            names = list(returns_dict.keys())
            returns = np.array([returns_dict[n][-20:] for n in names])
        
            # Check for synchronized drops
            negative_days = returns < 0
            sync_drops = np.mean(np.all(negative_days, axis=0))
        
            # Contagion score
            corr_matrix = np.corrcoef(returns)
            avg_corr = np.mean(corr_matrix[np.triu_indices_from(corr_matrix, k=1)])
            contagion_score = sync_drops * avg_corr
        
            # Affected assets (those with high correlation to others)
            affected = [names[i] for i in range(len(names)) if np.mean(corr_matrix[i]) > 0.5]
        
            # Safe havens (low correlation)
            safe = [names[i] for i in range(len(names)) if np.mean(corr_matrix[i]) < 0.2]
        
            spillover = min(0.9, contagion_score * 2)
            signal = self._generate_signal(contagion_score, len(affected))
        
            return ContagionResult(
                contagion_score=contagion_score, affected_assets=affected,
                spillover_probability=spillover, safe_havens=safe, trading_signal=signal
            )
        except Exception as e:
            logger.error(f"Error in monitor: {e}")
            raise
    
    def _generate_signal(self, score: float, affected: int) -> str:
        try:
            if score > 0.5:
                return f"HIGH CONTAGION: Score {score:.2f}, {affected} assets affected"
            return f"LOW CONTAGION: Score {score:.2f}"
        except Exception as e:
            logger.error(f"Error in _generate_signal: {e}")
            raise
    
    def _create_empty_result(self) -> ContagionResult:
        return ContagionResult(0, [], 0, [], "Insufficient data")
