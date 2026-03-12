"""
knowledge_acquisition package
"""

try:
    from .ai_knowledge import (
        AIKnowledge,
        AIKnowledgeAcquisition,
        AISource,
        retry
    )
    from .algorithm_knowledge import AlgorithmKnowledge, AlgorithmKnowledgeAcquisition, AlgorithmSource
    from .book_knowledge import BookKnowledge, BookKnowledgeAcquisition, BookSource
    from .human_knowledge import FeedbackSource, HumanKnowledge, HumanKnowledgeAcquisition
    from .knowledge_base import (
        KnowledgeBase,
        KnowledgeItem,
        KnowledgeStatus,
        KnowledgeType
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in knowledge_acquisition: {e}')

__all__ = [
    'AIKnowledge',
    'AIKnowledgeAcquisition',
    'AISource',
    'AlgorithmKnowledge',
    'AlgorithmKnowledgeAcquisition',
    'AlgorithmSource',
    'BookKnowledge',
    'BookKnowledgeAcquisition',
    'BookSource',
    'FeedbackSource',
    'HumanKnowledge',
    'HumanKnowledgeAcquisition',
    'KnowledgeBase',
    'KnowledgeItem',
    'KnowledgeStatus',
    'KnowledgeType',
    'retry',
]