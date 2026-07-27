"""
Knowledge Registry for Research OS.
Archives quantitative discoveries, failed hypothesis post-mortems, and mathematical findings.
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
from trading_bot.research.core.interfaces import KnowledgeRegistry

logger = logging.getLogger(__name__)


class StandardKnowledgeRegistry(KnowledgeRegistry):
    """
    Standard in-memory Knowledge Registry archiving insights and lessons learned.
    """

    def __init__(self):
        self._archive: Dict[str, Dict[str, Any]] = {}

    def archive_knowledge(self, key: str, knowledge: Dict[str, Any]) -> None:
        record = {
            "key": key,
            "title": knowledge.get("title", "Untitled Discovery"),
            "content": knowledge.get("content", ""),
            "author": knowledge.get("author", "AlphaAlgo Core Researcher"),
            "category": knowledge.get("category", "general"),
            "evidence": knowledge.get("evidence", {}),
            "tags": knowledge.get("tags", []),
            "archived_at": datetime.utcnow().isoformat()
        }
        self._archive[key] = record
        logger.info(f"Knowledge successfully archived under key '{key}'.")

    def get_knowledge(self, key: str) -> Optional[Dict[str, Any]]:
        return self._archive.get(key)

    def query_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """
        Simple text match query search across archived knowledge title, content, and tags.
        """
        q = query.lower()
        results = []
        for record in self._archive.values():
            if (q in record["title"].lower() or
                q in record["content"].lower() or
                any(q in tag.lower() for tag in record["tags"])):
                results.append(record)
        return results
