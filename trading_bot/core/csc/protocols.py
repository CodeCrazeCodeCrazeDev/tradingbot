"""
Async interface contracts for Cognitive System Controller (CSC) dependencies.
Ensures strict conformity and eliminates runtime MagicMock await failures.
"""

from typing import Any, Dict, List, Protocol

class EvidenceStore(Protocol):
    """Protocol for Hierarchical Memory System (HMS) retrieval interfaces."""
    async def retrieve_evidence_chain(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve historical context-dependent evidence based on a query."""
        ...
