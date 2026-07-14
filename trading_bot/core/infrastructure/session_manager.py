import logging
from datetime import datetime, time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MarketSessionManager:
    """Manages market sessions, holidays, and trading hours awareness."""
    def __init__(self):
        self.sessions = {
            "NYSE": {"open": time(9, 30), "close": time(16, 0), "timezone": "EST"},
            "LSE": {"open": time(8, 0), "close": time(16, 30), "timezone": "GMT"}
        }

    def is_market_open(self, exchange: str) -> bool:
        now = datetime.utcnow().time()
        session = self.sessions.get(exchange)
        if not session: return True
        return session["open"] <= now <= session["close"]

    def get_session_status(self) -> Dict[str, Any]:
        return {ex: self.is_market_open(ex) for ex in self.sessions}
