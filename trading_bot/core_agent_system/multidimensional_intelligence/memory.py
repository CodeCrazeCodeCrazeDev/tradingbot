"""
Knowledge Memory for Multidimensional Intelligence.
Persists validated insights and links domain concepts to performance results.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class MultidimensionalKnowledgeMemory:
    """
    Knowledge Memory
    Stores: Domain Concept -> Mathematical Representation -> Trading Application -> Performance Result
    """

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.knowledge_file = storage_path / "multidimensional_knowledge.json"
        self.knowledge_graph: Dict[str, Any] = {}

    def load(self):
        """Load knowledge from disk."""
        if self.knowledge_file.exists():
            try:
                with open(self.knowledge_file, 'r') as f:
                    self.knowledge_graph = json.load(f)
                logger.info(f"Loaded {len(self.knowledge_graph)} insights from knowledge memory")
            except Exception as e:
                logger.error(f"Error loading knowledge memory: {e}")

    def save(self):
        """Save knowledge to disk."""
        try:
            with open(self.knowledge_file, 'w') as f:
                json.dump(self.knowledge_graph, f, indent=2)
            logger.info("Saved multidimensional knowledge memory")
        except Exception as e:
            logger.error(f"Error saving knowledge memory: {e}")

    def add_insight(
        self,
        domain: str,
        concept: str,
        math_rep: str,
        application: str,
        result: Dict[str, Any],
        performance: Dict[str, float]
    ):
        """Add a new validated insight to the memory."""
        insight_id = f"{domain}_{concept.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.knowledge_graph[insight_id] = {
            "domain": domain,
            "concept": concept,
            "mathematical_representation": math_rep,
            "trading_application": application,
            "result": result,
            "performance_metrics": performance,
            "timestamp": datetime.now().isoformat()
        }
        self.save()

    def get_all_insights(self) -> List[Dict[str, Any]]:
        """Return all stored insights."""
        return list(self.knowledge_graph.values())

    def get_insights_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Filter insights by domain."""
        return [i for i in self.knowledge_graph.values() if i['domain'] == domain]
