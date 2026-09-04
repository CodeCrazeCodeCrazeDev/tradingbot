"""
Agent Orchestrator module alias.
"""
from typing import Any, Dict, Optional

class AgentOrchestrator:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

__all__ = ['AgentOrchestrator']
