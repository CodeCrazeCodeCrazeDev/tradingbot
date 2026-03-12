"""
research package
"""

try:
    from .free_research_lab import (
        FreeABTesting,
        FreeBacktester,
        FreePaperTrading,
        FreeResearchLab,
        FreeStrategy,
        FreeStrategyLibrary
    )
    from .innovation_lab import (
        ABTestVariant,
        ABTestingFramework,
        AdvancedBacktester,
        BacktestResult,
        ExperimentalStrategy,
        ExperimentalStrategyLab,
        PaperTrade,
        PaperTradingSimulator,
        ResearchInnovationHub,
        retry
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in research: {e}')

try:
    from .research_ingestion_pipeline import (
        ResearchIngestionPipeline,
        PipelineStage,
        SourceType,
        RelevanceCategory,
        FeasibilityLevel,
        ResearchSource,
        ExtractedClaim,
        BoundedExperiment,
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in research.research_ingestion_pipeline: {e}')

__all__ = [
    'ABTestVariant',
    'ABTestingFramework',
    'AdvancedBacktester',
    'BacktestResult',
    'BoundedExperiment',
    'ExtractedClaim',
    'ExperimentalStrategy',
    'ExperimentalStrategyLab',
    'FreeABTesting',
    'FreeBacktester',
    'FreePaperTrading',
    'FreeResearchLab',
    'FreeStrategy',
    'FreeStrategyLibrary',
    'PaperTrade',
    'PaperTradingSimulator',
    'ResearchInnovationHub',
    'ResearchIngestionPipeline',
    'PipelineStage',
    'SourceType',
    'RelevanceCategory',
    'FeasibilityLevel',
    'ResearchSource',
    'retry',
]

class ResearchOrchestrator:
    """Auto-generated stub orchestrator for research."""
    
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
