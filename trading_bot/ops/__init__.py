"""Ops module - Emergency controls and Telegram commands."""

from .emergency_controls import (
    EmergencyAction,
    EmergencyEvent,
    EmergencyControls,
)
from .telegram_commands import UserRole, TelegramOpsCommands

__all__ = [
    "EmergencyAction",
    "EmergencyEvent",
    "EmergencyControls",
    "UserRole",
    "TelegramOpsCommands",
]


class OpsOrchestrator:
    """Auto-generated stub orchestrator for ops."""
    
    def __init__(self, config=None):
        self.config = config or {}
        import warnings
        warnings.warn(
            "OpsOrchestrator is a merge-generated stub and is deprecated. "
            "Route orchestration through CognitiveSystemController "
            "(trading_bot.core.csc.controller).",
            DeprecationWarning, stacklevel=2,
        )
        self.running = False
        self._initialized = True
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running, "initialized": self._initialized}
