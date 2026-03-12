"""
intel package
"""

try:
    from .fundamental_analyzer import (
        CentralBankEvent,
        CompanyFinancials,
        FundamentalAnalyzer,
        FundamentalSignal,
        GeopoliticalEvent,
        MacroIndicator,
        OnChainData
    )
    from .news_pipeline import NewsArticle, NewsPipeline, NewsSignal
    from .strategy_researcher import CandidateStrategy, StrategyResearcher, StrategySource
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in intel: {e}')

__all__ = [
    'CandidateStrategy',
    'CentralBankEvent',
    'CompanyFinancials',
    'FundamentalAnalyzer',
    'FundamentalSignal',
    'GeopoliticalEvent',
    'MacroIndicator',
    'NewsArticle',
    'NewsPipeline',
    'NewsSignal',
    'OnChainData',
    'StrategyResearcher',
    'StrategySource',
]

class IntelOrchestrator:
    """Auto-generated stub orchestrator for intel."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.running = False
        self._initialized = True
    
    async def start(self):
        self.running = True
    
    async def stop(self):
        self.running = False
    
    def get_status(self):
        return {"running": self.running, "initialized": self._initialized}
