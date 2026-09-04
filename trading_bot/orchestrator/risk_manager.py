"""
Risk Manager module alias in orchestrator package.
"""
from typing import Any, Dict, Optional

class RiskManager:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

__all__ = ['RiskManager']
