"""
Knowledge Pipeline - External Knowledge Integration
====================================================

Implements real-time knowledge acquisition:
- ArXiv Connector: Academic paper ingestion
- SSRN Connector: Financial research papers
- Cross-Domain Mapper: Physics/biology/psychology analogies
- Knowledge Synthesizer: Combine insights from multiple sources
- Citation Network: Track research influence
- Theory Validator: Test academic theories in markets
"""

from .arxiv_connector import ArxivConnector, Paper, PaperMetadata
from .cross_domain_mapper import CrossDomainMapper, DomainAnalogy, DomainType
from .knowledge_synthesizer import KnowledgeSynthesizer, SynthesizedInsight
from .theory_validator import TheoryValidator, TheoryValidationResult

__all__ = [
    "ArxivConnector",
    "Paper",
    "PaperMetadata",
    "CrossDomainMapper",
    "DomainAnalogy",
    "DomainType",
    "KnowledgeSynthesizer",
    "SynthesizedInsight",
    "TheoryValidator",
    "TheoryValidationResult",
]
