"""
Safety Validator for AI Core
Performs real-time safety and risk validation for agent decisions.
"""

import logging
from typing import Any, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class SafetyValidator:
    """
    Safety Validator - Real-time safety validation sentinel for AI Core agent system.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, *args: Any, **kwargs: Any):
        if config is None:
            config = kwargs.get("config", dict(kwargs))
        self.config = config or {}
        self.running = False
        self.initialized = False
        for k, v in kwargs.items():
            setattr(self, k, v)
        logger.info(f"{self.__class__.__name__} initialized")

    def initialize(self) -> bool:
        """Initialize the safety validator."""
        try:
            self.initialized = True
            self.running = True
            logger.info("SafetyValidator successfully initialized")
            return True
        except Exception as e:
            logger.error(f"SafetyValidator initialization failed: {e}")
            return False

    def process(self, data: Any = None) -> Any:
        """
        Process data for safety validation.
        """
        if not self.initialized:
            self.initialize()

        try:
            if isinstance(data, dict):
                return self.validate_safety(data)
            return {
                "status": "processed",
                "timestamp": datetime.now().isoformat(),
                "data": data,
            }
        except Exception as e:
            logger.error(f"SafetyValidator processing error: {e}")
            return None

    def validate_safety(self, proposal: Any, context: Any = None) -> Tuple[bool, str]:
        """
        Validate safety of a trade proposal or context.
        """
        try:
            confidence = getattr(proposal, "confidence", None) or (
                proposal.get("confidence", 0.7) if isinstance(proposal, dict) else 0.7
            )
            if confidence < 0.5:
                return False, "Confidence too low for safe execution"
            return True, "All safety checks passed"
        except Exception as e:
            logger.error(f"Safety validation failed: {e}")
            return False, f"Validation error: {e}"

    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "status": "operational",
            "initialized": self.initialized,
            "running": self.running,
            "config": self.config,
            "timestamp": datetime.now().isoformat(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert status to dictionary representation."""
        return self.get_status()


def create_safety_validator(config: Optional[Dict[str, Any]] = None) -> SafetyValidator:
    """Factory function to create a SafetyValidator instance."""
    validator = SafetyValidator(config=config)
    validator.initialize()
    return validator
