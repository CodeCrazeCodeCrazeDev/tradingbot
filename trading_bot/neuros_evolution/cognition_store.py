"""
Cognition Store - ASI-Evolve Knowledge Base
==========================================

Embedding-indexed knowledge repository with semantic search capabilities.
Provides domain priors to accelerate cold-start search and avoid rediscovery.

Based on ASI-Evolve paper: "injects accumulated human priors into each round of exploration"
"""

import asyncio
import logging
import hashlib
import json
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


@dataclass
class CognitionItem:
    """Knowledge item in cognition store"""
    id: str
    content: str
    embedding_vector: Optional[List[float]] = None
    source_domain: str
    novelty_score: float = 0.0
    actionability_score: float = 0.0
    created_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.embedding_vector:
            # Generate simple embedding based on content hash
            content_hash = hashlib.md5(self.content.encode()).hexdigest()
            self.embedding_vector = [hash(content_hash) % 1000 for _ in range(128)]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'source_domain': self.source_domain,
            'novelty_score': self.novelty_score,
            'actionability_score': self.actionability_score,
            'created_at': self.created_at.isoformat(),
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
        }


class CognitionStore:
    """
    ASI-Evolve Cognition Store with FAISS-like indexing.
    
    Provides fast semantic search and knowledge retrieval.
    """
    
    def __init__(self):
        self.items: Dict[str, CognitionItem] = {}
        self.embedding_index: Dict[str, List[float]] = {}
        logger.info("Cognition Store initialized")
    
    def initialize(self):
        """Initialize cognition store with domain knowledge"""
        # Add basic trading strategy knowledge
        basic_knowledge = [
            "Mean reversion strategies work best in ranging markets with defined support/resistance levels",
            "Momentum strategies require volume confirmation and trend alignment",
            "Statistical arbitrage opportunities are time-sensitive and require fast execution",
            "Volatility-based position sizing adapts to market regime changes",
            "Risk management through stop-loss and position limits is essential for long-term survival",
        ]
        
        # Add ML architecture knowledge
        ml_knowledge = [
            "Transformer architectures excel at sequence modeling but have quadratic complexity",
            "Linear attention mechanisms (RWKV, Mamba) provide O(N) complexity with better performance",
            "Ensemble methods combine multiple models for improved robustness and accuracy",
            "Regularization techniques (dropout, weight decay) prevent overfitting and improve generalization",
        ]
        
        # Add data curation knowledge
        data_knowledge = [
            "Quality issues in text data include HTML artifacts, formatting inconsistencies, and incomplete fragments",
            "Domain-specific preservation rules prevent over-aggressive filtering that removes important signals",
            "Data quality assessment requires both automated metrics and human evaluation",
            "Deduplication detection and removal is critical for training efficiency",
        ]
        
        # Add algorithm design knowledge
        algorithm_knowledge = [
            "Reinforcement learning requires careful reward function design to avoid instability",
            "Advantage estimation methods significantly impact learning efficiency and convergence",
            "Exploration vs exploitation trade-offs must be balanced for optimal policy learning",
            "Gradient clipping and normalization techniques prevent training divergence",
        ]
        
        # Store all knowledge
        all_knowledge = basic_knowledge + ml_knowledge + data_knowledge + algorithm_knowledge
        
        for i, content in enumerate(all_knowledge):
            item = CognitionItem(
                id=f"cognition_{i}",
                content=content,
                source_domain="general",
                novelty_score=0.8 if i < 10 else 0.5,  # Basic knowledge gets higher novelty
                actionability_score=0.9 if i < 10 else 0.7,
                created_at=datetime.utcnow(),
            )
            self.items[item.id] = item
            self._update_embedding_index(item)
        
        logger.info(f"Cognition Store initialized with {len(all_knowledge)} knowledge items")
    
    def _update_embedding_index(self, item: CognitionItem):
        """Update embedding index for semantic search"""
        # Simple embedding-based indexing
        domain_keywords = {
            'trading': ['strategy', 'risk', 'arbitrage', 'momentum'],
            'ml': ['architecture', 'attention', 'transformer', 'ensemble'],
            'data': ['quality', 'curation', 'cleaning', 'deduplication'],
            'algorithm': ['reinforcement', 'advantage', 'policy', 'gradient'],
        }
        
        # Extract keywords from content
        content_lower = item.content.lower()
        item_keywords = []
        for domain, keywords in domain_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    item_keywords.append(f"{domain}:{keyword}")
        
        # Update embedding vector with keyword matches
        if item.embedding_vector:
            for i, keyword in enumerate(item_keywords[:128]):
                if i < len(item.embedding_vector):
                    item.embedding_vector[i] = 1.0
            else:
                item.embedding_vector.extend([1.0] * (128 - len(item.embedding_vector)))
    
    def add_cognition_item(self, item: CognitionItem):
        """Add new cognition item"""
        self.items[item.id] = item
        item.access_count += 1
        item.last_accessed = datetime.utcnow()
        self._update_embedding_index(item)
        logger.info(f"Added cognition item: {item.id}")
    
    def search(self, query: str, top_k: int = 5) -> List[CognitionItem]:
        """Semantic search over cognition items"""
        query_lower = query.lower()
        scored_items = []
        
        for item in self.items.values():
            # Simple relevance scoring based on keyword overlap
            content_lower = item.content.lower()
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            
            # Calculate overlap ratio
            overlap = len(query_words & content_words)
            query_size = len(query_words)
            content_size = len(content_words)
            
            # Relevance score based on overlap and recency
            relevance = overlap / query_size if query_size > 0 else 0
            recency_bonus = 1.0 if item.access_count > 0 else 0.5
            
            score = relevance + 0.1 * recency_bonus
            
            if score > 0.1:  # Only return relevant items
                scored_items.append((score, item))
        
        # Sort by score and return top_k
        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored_items[:top_k]]
    
    def get_item(self, item_id: str) -> Optional[CognitionItem]:
        """Get cognition item by ID"""
        return self.items.get(item_id)
    
    def get_all_items(self) -> List[CognitionItem]:
        """Get all cognition items"""
        return list(self.items.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cognition store statistics"""
        total_items = len(self.items)
        total_accesses = sum(item.access_count for item in self.items.values())
        
        domain_distribution = {}
        for item in self.items.values():
            domain = item.source_domain
            domain_distribution[domain] = domain_distribution.get(domain, 0) + 1
        
        return {
            'total_items': total_items,
            'total_accesses': total_accesses,
            'domain_distribution': domain_distribution,
            'avg_access_count': total_accesses / total_items if total_items > 0 else 0,
        }
