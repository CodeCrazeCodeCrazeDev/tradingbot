"""
Research & Knowledge Ingestion Pipeline

Full pipeline for ingesting, filtering, and deploying ideas from:
- Academic research papers (arXiv, SSRN, etc.)
- GitHub repositories (quantitative finance, ML trading)
- Blog posts, forums, and community knowledge

Pipeline: Ingestion → Relevance Filtering → Claim Extraction → Feasibility Scoring
         → Sandbox Implementation → Backtest & Stress Test → Capital Impact Estimation
         → Human/Policy Gate → Production Deployment
"""

from .paper_ingestion import PaperIngestionEngine, ResearchPaper, PaperSource
from .github_ingestion import GitHubRepoIngestion, RepoAnalysis
from .relevance_filter import RelevanceFilter, RelevanceScore
from .claim_extractor import ClaimExtractor, ExtractedClaim
from .feasibility_scorer import FeasibilityScorer, FeasibilityReport
from .sandbox_implementer import SandboxImplementer, SandboxResult
from .research_pipeline_orchestrator import ResearchPipelineOrchestrator

__all__ = [
    'PaperIngestionEngine', 'ResearchPaper', 'PaperSource',
    'GitHubRepoIngestion', 'RepoAnalysis',
    'RelevanceFilter', 'RelevanceScore',
    'ClaimExtractor', 'ExtractedClaim',
    'FeasibilityScorer', 'FeasibilityReport',
    'SandboxImplementer', 'SandboxResult',
    'ResearchPipelineOrchestrator',
]
