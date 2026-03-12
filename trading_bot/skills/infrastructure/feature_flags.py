"""
Skill #91: Feature Flag Manager
===============================

Manages feature flags for controlled rollouts.
"""

from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class FeatureFlagResult:
    """Feature flag result."""
    flag_name: str
    enabled: bool
    percentage: float
    trading_signal: str


class FeatureFlagManager:
    """Manages feature flags."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.flags: Dict[str, Dict] = {}
            logger.info("FeatureFlagManager initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def create_flag(self, name: str, enabled: bool = False, percentage: float = 0.0):
        """Create a feature flag."""
        try:
            self.flags[name] = {'enabled': enabled, 'percentage': percentage}
        except Exception as e:
            logger.error(f"Error in create_flag: {e}")
            raise
    
    def is_enabled(self, name: str, user_id: str = "") -> FeatureFlagResult:
        """Check if flag is enabled."""
        try:
            if name not in self.flags:
                return FeatureFlagResult(name, False, 0, "Flag not found")
        
            flag = self.flags[name]
            enabled = flag['enabled']
            pct = flag['percentage']
        
            # Percentage-based rollout
            if pct > 0 and user_id:
                user_hash = hash(user_id) % 100
                enabled = enabled or user_hash < pct * 100
        
            return FeatureFlagResult(name, enabled, pct, f"FLAG {name}: {'ON' if enabled else 'OFF'}")
        except Exception as e:
            logger.error(f"Error in is_enabled: {e}")
            raise
    
    def toggle(self, name: str) -> FeatureFlagResult:
        """Toggle a flag."""
        try:
            if name in self.flags:
                self.flags[name]['enabled'] = not self.flags[name]['enabled']
                return self.is_enabled(name)
            return FeatureFlagResult(name, False, 0, "Flag not found")
        except Exception as e:
            logger.error(f"Error in toggle: {e}")
            raise
