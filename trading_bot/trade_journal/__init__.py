"""
Automatic Trade Journal
Records all trades with screenshots, notes, and analysis
"""

from .journal_manager import (
    TradeJournal,
    JournalEntry,
    TradeNote,
    ScreenshotCapture,
    PerformanceAnalyzer
)

__all__ = [
    'TradeJournalOrchestrator',
    'TradeJournal',
    'JournalEntry',
    'TradeNote',
    'ScreenshotCapture',
    'PerformanceAnalyzer'
]


class TradeJournalOrchestrator:
    """Stub for TradeJournalOrchestrator."""
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', {})
        import warnings
        warnings.warn(
            "TradeJournalOrchestrator is a merge-generated stub and is deprecated. "
            "Route orchestration through CognitiveSystemController "
            "(trading_bot.core.csc.controller).",
            DeprecationWarning, stacklevel=2,
        )
        self.running = False
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running}
