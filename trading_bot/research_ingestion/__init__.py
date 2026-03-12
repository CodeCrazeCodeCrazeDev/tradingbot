"""
Research Ingestion Module
============================================================

Auto-generated integration file.
"""

# paper_ingestion
try:
    from .paper_ingestion import (
        PaperIngestionEngine,
    )
except ImportError as e:
    # paper_ingestion not available
    pass

# research_pipeline_orchestrator
try:
    from .research_pipeline_orchestrator import (
        ResearchPipelineOrchestrator,
    )
except ImportError as e:
    # research_pipeline_orchestrator not available
    pass

__all__ = [
    'PaperIngestionEngine',
    'ResearchPipelineOrchestrator',
]
