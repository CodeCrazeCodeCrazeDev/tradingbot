"""Human Knowledge Acquisition for Self-Improving Trading Bot.

This module implements the acquisition of knowledge from human experts,
user feedback, and interactive learning sessions.
"""

import uuid
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .knowledge_base import KnowledgeBase, KnowledgeItem, KnowledgeType, KnowledgeStatus
import numpy

logger = logging.getLogger(__name__)


class FeedbackSource(Enum):
    """Types of human feedback sources."""
    USER_FEEDBACK = "user_feedback"
    EXPERT_CONSULTATION = "expert_consultation"
    PERFORMANCE_REVIEW = "performance_review"
    TRADING_JOURNAL = "trading_journal"
    INTERVIEW = "interview"
    SURVEY = "survey"


@dataclass
class HumanKnowledge:
    """Knowledge acquired from human sources."""
    content: str
    source: FeedbackSource
    contributor: str
    context: str
    timestamp: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.9  # Higher default confidence for human knowledge
    metadata: Dict[str, Any] = field(default_factory=dict)
    verification_status: str = "unverified"


class HumanKnowledgeAcquisition:
    """System for acquiring knowledge from human sources."""
    
    def __init__(self, knowledge_base: KnowledgeBase):
        """Initialize the human knowledge acquisition system.
        
        Args:
            knowledge_base: Knowledge base to store acquired knowledge
        """
        self.knowledge_base = knowledge_base
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.feedback_handlers = {}
        self.feedback_history = []
        
        logger.info("Human knowledge acquisition system initialized")
    
    def register_feedback_handler(self, source: FeedbackSource, handler: Callable):
        """Register a handler for a specific feedback source.
        
        Args:
            source: Feedback source type
            handler: Callback function to handle feedback
        """
        self.feedback_handlers[source] = handler
        logger.info(f"Registered feedback handler for {source.value}")
    
    def process_feedback(self, feedback: HumanKnowledge) -> str:
        """Process human feedback and store as knowledge.
        
        Args:
            feedback: Human feedback to process
            
        Returns:
            ID of the stored knowledge item
        """
        logger.info(f"Processing feedback from {feedback.contributor} via {feedback.source.value}")
        
        # Extract tags if not provided
        if not feedback.tags:
            feedback.tags = self._extract_tags(feedback.content)
        
        # Create knowledge item
        item = KnowledgeItem(
            id=str(uuid.uuid4()),
            title=self._generate_title(feedback),
            content=feedback.content,
            knowledge_type=KnowledgeType.HUMAN,
            source=f"{feedback.source.value}:{feedback.contributor}",
            tags=feedback.tags,
            confidence=feedback.confidence,
            acquisition_date=feedback.timestamp,
            status=KnowledgeStatus.UNVERIFIED,
            metadata={
                "contributor": feedback.contributor,
                "context": feedback.context,
                "verification_status": feedback.verification_status,
                **feedback.metadata
            }
        )
        
        # Check for similar items before storing
        similar_items = self._find_similar_items(item)
        
        if similar_items:
            # Update existing item instead of creating a duplicate
            existing_item = similar_items[0]
            logger.info(f"Found similar item: {existing_item.title} (ID: {existing_item.id})")
            
            # Merge content and tags
            existing_item.content = f"{existing_item.content}\n\nAdditional feedback ({feedback.timestamp}):\n{feedback.content}"
            existing_item.tags = list(set(existing_item.tags + item.tags))
            
            # Update confidence if new item has higher confidence
            if item.confidence > existing_item.confidence:
                existing_item.confidence = item.confidence
            
            # Update metadata
            existing_item.metadata.update(item.metadata)
            
            # Store updated item
            self.knowledge_base.update_item(existing_item)
            item_id = existing_item.id
            
        else:
            # Store new item
            item_id = self.knowledge_base.add_item(item)
        
        # Record in feedback history
        self.feedback_history.append({
            "timestamp": feedback.timestamp,
            "source": feedback.source.value,
            "contributor": feedback.contributor,
            "item_id": item_id
        })
        
        # Call appropriate handler if registered
        if feedback.source in self.feedback_handlers:
            try:
                self.feedback_handlers[feedback.source](feedback, item_id)
            except Exception as e:
                logger.error(f"Error in feedback handler: {e}")
        
        return item_id
    
    def record_user_feedback(self, content: str, contributor: str, context: str, 
                           tags: Optional[List[str]] = None, confidence: float = 0.9,
                           metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record feedback from a user.
        
        Args:
            content: Feedback content
            contributor: Name or ID of the contributor
            context: Context in which the feedback was given
            tags: Optional tags for the feedback
            confidence: Confidence score (0-1)
            metadata: Additional metadata
            
        Returns:
            ID of the stored knowledge item
        """
        feedback = HumanKnowledge(
            content=content,
            source=FeedbackSource.USER_FEEDBACK,
            contributor=contributor,
            context=context,
            tags=tags or [],
            confidence=confidence,
            metadata=metadata or {}
        )
        
        return self.process_feedback(feedback)
    
    def record_expert_consultation(self, content: str, expert_name: str, expertise_area: str,
                                 tags: Optional[List[str]] = None, confidence: float = 0.95,
                                 metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record consultation with an expert.
        
        Args:
            content: Consultation content
            expert_name: Name of the expert
            expertise_area: Area of expertise
            tags: Optional tags for the consultation
            confidence: Confidence score (0-1)
            metadata: Additional metadata
            
        Returns:
            ID of the stored knowledge item
        """
        feedback = HumanKnowledge(
            content=content,
            source=FeedbackSource.EXPERT_CONSULTATION,
            contributor=expert_name,
            context=f"Expert consultation in {expertise_area}",
            tags=tags or [],
            confidence=confidence,
            metadata={
                "expertise_area": expertise_area,
                **(metadata or {})
            }
        )
        
        return self.process_feedback(feedback)
    
    def record_performance_review(self, content: str, reviewer: str, performance_metrics: Dict[str, Any],
                                tags: Optional[List[str]] = None, confidence: float = 0.9,
                                metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record a performance review.
        
        Args:
            content: Review content
            reviewer: Name of the reviewer
            performance_metrics: Performance metrics
            tags: Optional tags for the review
            confidence: Confidence score (0-1)
            metadata: Additional metadata
            
        Returns:
            ID of the stored knowledge item
        """
        feedback = HumanKnowledge(
            content=content,
            source=FeedbackSource.PERFORMANCE_REVIEW,
            contributor=reviewer,
            context="Performance review",
            tags=tags or [],
            confidence=confidence,
            metadata={
                "performance_metrics": performance_metrics,
                **(metadata or {})
            }
        )
        
        return self.process_feedback(feedback)
    
    def record_trading_journal(self, content: str, trader: str, trade_details: Dict[str, Any],
                             tags: Optional[List[str]] = None, confidence: float = 0.85,
                             metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record a trading journal entry.
        
        Args:
            content: Journal content
            trader: Name of the trader
            trade_details: Details of the trade
            tags: Optional tags for the journal entry
            confidence: Confidence score (0-1)
            metadata: Additional metadata
            
        Returns:
            ID of the stored knowledge item
        """
        feedback = HumanKnowledge(
            content=content,
            source=FeedbackSource.TRADING_JOURNAL,
            contributor=trader,
            context="Trading journal entry",
            tags=tags or [],
            confidence=confidence,
            metadata={
                "trade_details": trade_details,
                **(metadata or {})
            }
        )
        
        return self.process_feedback(feedback)
    
    def get_feedback_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get feedback history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of feedback history entries
        """
        return self.feedback_history[-limit:]
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get statistics about feedback.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_feedback": len(self.feedback_history),
            "by_source": {},
            "by_contributor": {},
            "recent_feedback": len([f for f in self.feedback_history 
                                  if (datetime.now() - f["timestamp"]).days < 30])
        }
        
        # Count by source
        for feedback in self.feedback_history:
            source = feedback["source"]
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
            
            contributor = feedback["contributor"]
            stats["by_contributor"][contributor] = stats["by_contributor"].get(contributor, 0) + 1
        
        return stats
    
    def _generate_title(self, feedback: HumanKnowledge) -> str:
        """Generate a title for feedback.
        
        Args:
            feedback: Feedback to generate title for
            
        Returns:
            Generated title
        """
        # Extract first line or sentence
        first_line = feedback.content.split('\n')[0]
        if len(first_line) <= 100:
            return first_line
        
        # Truncate if too long
        if len(first_line) > 100:
            return first_line[:97] + "..."
        
        # Fall back to generic title
        return f"{feedback.source.value} from {feedback.contributor}"
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract relevant tags from content.
        
        Args:
            content: Content to extract tags from
            
        Returns:
            List of tags
        """
        # Use TF-IDF to find important terms
        tfidf_matrix = self.vectorizer.fit_transform([content])
        feature_names = self.vectorizer.get_feature_names_out()
        
        # Get top TF-IDF scores
        scores = zip(feature_names, tfidf_matrix.toarray()[0])
        sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
        
        # Extract top terms as tags
        tags = [word for word, score in sorted_scores[:10] if len(word) > 3]
        
        # Add trading-specific tags if they appear in the content
        trading_terms = [
            "trading", "market", "stock", "forex", "cryptocurrency", "technical", "fundamental",
            "analysis", "indicator", "strategy", "risk", "volatility", "trend", "momentum",
            "arbitrage", "algorithm", "backtest", "optimization", "machine learning", "ai"
        ]
        
        for term in trading_terms:
            if term in content.lower() and term not in tags:
                tags.append(term)
        
        return tags[:15]  # Limit to 15 tags
    
    def _find_similar_items(self, item: KnowledgeItem) -> List[KnowledgeItem]:
        """Find similar items in the knowledge base.
        
        Args:
            item: Knowledge item to find similar items for
            
        Returns:
            List of similar knowledge items
        """
        # Search by content similarity
        similar_items = []
        
        # First check for items with the same source
        source_matches = self.knowledge_base.search(
            knowledge_type=KnowledgeType.HUMAN,
            query=item.source,
            limit=5
        )
        
        for match in source_matches:
            similarity = self._calculate_text_similarity(item.content, match.content)
            if similarity > 0.6:  # Moderate similarity threshold
                similar_items.append(match)
        
        if similar_items:
            return similar_items
        
        # If no source matches, check by tags
        if item.tags:
            tag_matches = self.knowledge_base.search(
                knowledge_type=KnowledgeType.HUMAN,
                tags=item.tags[:3],
                limit=5
            )
            
            for match in tag_matches:
                similarity = self._calculate_text_similarity(item.content, match.content)
                if similarity > 0.5:  # Lower threshold for tag matches
                    similar_items.append(match)
        
        return similar_items
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate TF-IDF cosine similarity between texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
        return (tfidf_matrix * tfidf_matrix.T).toarray()[0, 1]
