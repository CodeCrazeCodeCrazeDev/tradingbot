"""
Executor Agent - AI Core Component
Coordinates and executes trading actions in the AgentFlow architecture.
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ExecutorAgent:
    """Executor Agent for trade execution."""

    def __init__(self, agent_id: str = "executor_001", config: Optional[Dict[str, Any]] = None, **kwargs: Any):
        self.agent_id = agent_id
        self.config = config or kwargs.get("config", dict(kwargs))
        self.running = False
        self.initialized = False
        for k, v in kwargs.items():
            setattr(self, k, v)

    def initialize(self) -> bool:
        """Initialize the executor agent."""
        self.initialized = True
        self.running = True
        logger.info(f"ExecutorAgent {self.agent_id} initialized.")
        return True

    def process(self, data: Any = None) -> Dict[str, Any]:
        """Process input data and return execution result."""
        if not self.initialized:
            self.initialize()
        return {
            "status": "processed",
            "agent_id": self.agent_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "status": "operational",
            "running": self.running,
            "initialized": self.initialized,
            "agent_id": self.agent_id
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert status to dictionary."""
        return self.get_status()


_default_executor = ExecutorAgent()


def create_executor_agent(config: Optional[Dict[str, Any]] = None) -> ExecutorAgent:
    """Factory function to create an ExecutorAgent instance."""
    agent = ExecutorAgent(config=config)
    agent.initialize()
    return agent


def initialize() -> bool:
    """Module-level initialize helper."""
    return _default_executor.initialize()


def process(data: Any = None) -> Dict[str, Any]:
    """Module-level process helper."""
    return _default_executor.process(data)


def get_status() -> Dict[str, Any]:
    """Module-level get_status helper."""
    return _default_executor.get_status()
