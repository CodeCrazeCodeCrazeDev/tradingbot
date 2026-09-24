"""YourTradingBot - flat-path shim with minimal deleted-class shims."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class YourTradingBotConfig:
    """User-facing trading bot configuration."""

    mode: str = "paper"
    symbol: str = "EURUSD"
    risk_per_trade: float = 0.02
    max_positions: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)


class YourTradingBot:
    """Minimal user-facing trading bot wrapper."""

    def __init__(self, config: YourTradingBotConfig = None):
        self.config = config or YourTradingBotConfig()
        self.initialized = False
        self.running = False

    def initialize(self) -> bool:
        self.initialized = True
        return True

    def process(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {"processed": True, "symbol": self.config.symbol, "data": data}

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": "operational",
            "initialized": self.initialized,
            "running": self.running,
        }
