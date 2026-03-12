"""
Skill #88: Time Travel Debugger
===============================

Enables replaying historical states for debugging.
"""

from dataclasses import dataclass
from typing import Dict, Optional, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Snapshot:
    """State snapshot."""
    timestamp: datetime
    state: Dict[str, Any]
    event: str


@dataclass
class TimeTravelResult:
    """Time travel result."""
    current_time: datetime
    snapshots_available: int
    current_state: Dict[str, Any]
    trading_signal: str


class TimeTravelDebugger:
    """Time travel debugging for state replay."""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.snapshots: List[Snapshot] = []
            self.current_index = -1
            logger.info("TimeTravelDebugger initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def snapshot(self, state: Dict[str, Any], event: str = ""):
        """Take a snapshot."""
        try:
            self.snapshots.append(Snapshot(datetime.now(), state.copy(), event))
            self.current_index = len(self.snapshots) - 1
        except Exception as e:
            logger.error(f"Error in snapshot: {e}")
            raise
    
    def travel_to(self, index: int) -> TimeTravelResult:
        """Travel to specific snapshot."""
        try:
            if 0 <= index < len(self.snapshots):
                self.current_index = index
                snap = self.snapshots[index]
                return TimeTravelResult(snap.timestamp, len(self.snapshots), snap.state, f"TRAVELED: {snap.event}")
            return TimeTravelResult(datetime.now(), len(self.snapshots), {}, "Invalid index")
        except Exception as e:
            logger.error(f"Error in travel_to: {e}")
            raise
    
    def step_back(self) -> TimeTravelResult:
        """Step back one snapshot."""
        return self.travel_to(self.current_index - 1)
    
    def step_forward(self) -> TimeTravelResult:
        """Step forward one snapshot."""
        return self.travel_to(self.current_index + 1)
