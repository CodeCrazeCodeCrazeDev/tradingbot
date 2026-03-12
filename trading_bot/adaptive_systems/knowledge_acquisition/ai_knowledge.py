"""AI Knowledge Acquisition for Self-Improving Trading Bot.

from pathlib import Path
This module implements the acquisition of knowledge from external AI systems,
large language models, and specialized AI services.
"""

import uuid
import json
import logging
import asyncio
try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import requests
except ImportError:
    requests = None
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .knowledge_base import KnowledgeBase, KnowledgeItem, KnowledgeType, KnowledgeStatus
import pathlib
import numpy

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class AISource(Enum):
    """Types of AI knowledge sources."""
    LARGE_LANGUAGE_MODEL = "large_language_model"
    SPECIALIZED_AI = "specialized_ai"
    RESEARCH_AI = "research_ai"
    TRADING_AI = "trading_ai"
    MARKET_AI = "market_ai"
    RISK_AI = "risk_ai"


@dataclass
class AIKnowledge:
    """Knowledge acquired from AI sources."""
    content: str
    source: AISource
    prompt: str
    model_name: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_response: Optional[Dict[str, Any]] = None


class AIKnowledgeAcquisition:
    """System for acquiring knowledge from AI sources."""
    
    def __init__(self, knowledge_base: KnowledgeBase, api_keys: Optional[Dict[str, str]] = None):
        """Initialize the AI knowledge acquisition system.
        
        Args:
            knowledge_base: Knowledge base to store acquired knowledge
            api_keys: Dictionary of API keys for different AI services
        """
        self.knowledge_base = knowledge_base
        self.api_keys = api_keys or {}
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.query_history = []
        
        # Default prompts for different knowledge types
        self.default_prompts = {
            "trading_strategy": "Explain in detail the following trading strategy, including its strengths, weaknesses, optimal market conditions, and implementation details: {topic}",
            "market_analysis": "Provide a comprehensive analysis of {topic} in financial markets, including key factors, historical patterns, and predictive indicators.",
            "risk_management": "Explain advanced risk management techniques for {topic} in trading, including mathematical models, practical implementation, and common pitfalls.",
            "technical_indicator": "Provide a detailed explanation of the {topic} technical indicator, including its calculation, interpretation, strengths, weaknesses, and optimal usage scenarios.",
            "algorithm_explanation": "Explain the {topic} algorithm in detail, including its mathematical foundation, implementation steps, computational complexity, and application in trading systems."
        }
        
        logger.info("AI knowledge acquisition system initialized")
    
    async def query_openai(self, prompt: str, model: str = "gpt-4", 
                         temperature: float = 0.2, max_tokens: int = 1000,
                         knowledge_type: str = "trading_strategy", 
                         topic: str = "", tags: Optional[List[str]] = None) -> Optional[str]:
        """Query OpenAI API for knowledge.
        
        Args:
            prompt: Prompt to send to the API
            model: Model to use
            temperature: Temperature parameter
            max_tokens: Maximum tokens in response
            knowledge_type: Type of knowledge being requested
            topic: Topic of the knowledge
            tags: Optional tags for the knowledge
            
        Returns:
            ID of the stored knowledge item if successful, None otherwise
        """
        if "openai" not in self.api_keys:
            logger.error("OpenAI API key not provided")
            return None
        
        # Use default prompt if not provided
        if not prompt and knowledge_type in self.default_prompts and topic:
            prompt = self.default_prompts[knowledge_type].format(topic=topic)
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_keys['openai']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error: {response.status} - {error_text}")
                        return None
                    
                    result = await response.json()
            
            # Extract content
            content = result["choices"][0]["message"]["content"]
            
            # Calculate confidence based on response
            confidence = self._calculate_ai_confidence(result)
            
            # Create AI knowledge
            knowledge = AIKnowledge(
                content=content,
                source=AISource.LARGE_LANGUAGE_MODEL,
                prompt=prompt,
                model_name=model,
                confidence=confidence,
                tags=tags or self._extract_tags(content),
                metadata={
                    "knowledge_type": knowledge_type,
                    "topic": topic,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                raw_response=result
            )
            
            # Store in knowledge base
            return self._store_ai_knowledge(knowledge)
            
        except Exception as e:
            logger.error(f"Error querying OpenAI API: {e}")
            return None
    
    def query_local_model(self, prompt: str, model_path: str,
                        knowledge_type: str = "trading_strategy",
                        topic: str = "", tags: Optional[List[str]] = None) -> Optional[str]:
        """Query a local AI model for knowledge.
        
        Args:
            prompt: Prompt to send to the model
            model_path: Path to the local model
            knowledge_type: Type of knowledge being requested
            topic: Topic of the knowledge
            tags: Optional tags for the knowledge
            
        Returns:
            ID of the stored knowledge item if successful, None otherwise
        """
        try:
            # This is a placeholder for local model inference
            # In a real implementation, you would load and run the model here
            
            # Simulate model response for demonstration
            content = f"This is a simulated response from a local model about {topic}."
            confidence = 0.7  # Lower confidence for local model
            
            # Create AI knowledge
            knowledge = AIKnowledge(
                content=content,
                source=AISource.SPECIALIZED_AI,
                prompt=prompt,
                model_name=f"local:{model_path}",
                confidence=confidence,
                tags=tags or self._extract_tags(content),
                metadata={
                    "knowledge_type": knowledge_type,
                    "topic": topic,
                    "local_model": True
                }
            )
            
            # Store in knowledge base
            return self._store_ai_knowledge(knowledge)
            
        except Exception as e:
            logger.error(f"Error querying local model: {e}")
            return None
    
    async def query_specialized_api(self, api_name: str, endpoint: str, params: Dict[str, Any],
                                 knowledge_type: str, topic: str,
                                 tags: Optional[List[str]] = None) -> Optional[str]:
        """Query a specialized AI API for knowledge.
        
        Args:
            api_name: Name of the API
            endpoint: API endpoint
            params: API parameters
            knowledge_type: Type of knowledge being requested
            topic: Topic of the knowledge
            tags: Optional tags for the knowledge
            
        Returns:
            ID of the stored knowledge item if successful, None otherwise
        """
        if api_name not in self.api_keys:
            logger.error(f"{api_name} API key not provided")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_keys[api_name]}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    headers=headers,
                    json=params
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"{api_name} API error: {response.status} - {error_text}")
                        return None
                    
                    result = await response.json()
            
            # Extract content (this would depend on the specific API)
            content = self._extract_content_from_api_response(result, api_name)
            
            # Calculate confidence based on response
            confidence = self._calculate_api_confidence(result, api_name)
            
            # Create AI knowledge
            knowledge = AIKnowledge(
                content=content,
                source=AISource.SPECIALIZED_AI,
                prompt=json.dumps(params),
                model_name=f"{api_name}:{endpoint}",
                confidence=confidence,
                tags=tags or self._extract_tags(content),
                metadata={
                    "knowledge_type": knowledge_type,
                    "topic": topic,
                    "api_name": api_name,
                    "endpoint": endpoint
                },
                raw_response=result
            )
            
            # Store in knowledge base
            return self._store_ai_knowledge(knowledge)
            
        except Exception as e:
            logger.error(f"Error querying {api_name} API: {e}")
            return None
    
    async def query_trading_ai(self, market: str, timeframe: str, indicator: str,
                            params: Dict[str, Any], tags: Optional[List[str]] = None) -> Optional[str]:
        """Query a trading-specific AI for market analysis.
        
        Args:
            market: Market to analyze
            timeframe: Timeframe for analysis
            indicator: Technical indicator to use
            params: Additional parameters
            tags: Optional tags for the knowledge
            
        Returns:
            ID of the stored knowledge item if successful, None otherwise
        """
        # This is a specialized wrapper around query_specialized_api
        api_params = {
            "market": market,
            "timeframe": timeframe,
            "indicator": indicator,
            **params
        }
        
        return await self.query_specialized_api(
            api_name="trading_ai",
            endpoint="https://api.tradingai.example/analyze",
            params=api_params,
            knowledge_type="market_analysis",
            topic=f"{market} {timeframe} {indicator} analysis",
            tags=tags
        )
    
    def _store_ai_knowledge(self, knowledge: AIKnowledge) -> str:
        """Store AI knowledge in the knowledge base.
        
        Args:
            knowledge: AI knowledge to store
            
        Returns:
            ID of the stored knowledge item
        """
        # Generate a title
        title = self._generate_title(knowledge)
        
        # Create knowledge item
        item = KnowledgeItem(
            id=str(uuid.uuid4()),
            title=title,
            content=knowledge.content,
            knowledge_type=KnowledgeType.AI,
            source=f"{knowledge.source.value}:{knowledge.model_name}",
            tags=knowledge.tags,
            confidence=knowledge.confidence,
            acquisition_date=knowledge.timestamp,
            status=KnowledgeStatus.UNVERIFIED,
            metadata={
                "prompt": knowledge.prompt,
                "model_name": knowledge.model_name,
                **knowledge.metadata
            }
        )
        
        # Check for similar items before storing
        similar_items = self._find_similar_items(item)
        
        if similar_items:
            # Update existing item instead of creating a duplicate
            existing_item = similar_items[0]
            logger.info(f"Found similar item: {existing_item.title} (ID: {existing_item.id})")
            
            # Merge content and tags
            existing_item.content = f"{existing_item.content}\n\nAdditional information ({knowledge.timestamp}):\n{knowledge.content}"
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
        
        # Record in query history
        self.query_history.append({
            "timestamp": knowledge.timestamp,
            "source": knowledge.source.value,
            "model": knowledge.model_name,
            "topic": knowledge.metadata.get("topic", ""),
            "item_id": item_id
        })
        
        return item_id
    
    def _generate_title(self, knowledge: AIKnowledge) -> str:
        """Generate a title for AI knowledge.
        
        Args:
            knowledge: AI knowledge to generate title for
            
        Returns:
            Generated title
        """
        # Use topic if available
        topic = knowledge.metadata.get("topic")
        if topic:
            return f"{knowledge.metadata.get('knowledge_type', 'AI knowledge')}: {topic}"
        
        # Extract first line or sentence
        first_line = knowledge.content.split('\n')[0]
        if len(first_line) <= 100:
            return first_line
        
        # Truncate if too long
        if len(first_line) > 100:
            return first_line[:97] + "..."
        
        # Fall back to generic title
        return f"AI knowledge from {knowledge.model_name}"
    
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
            knowledge_type=KnowledgeType.AI,
            query=item.source,
            limit=5
        )
        
        for match in source_matches:
            similarity = self._calculate_text_similarity(item.content, match.content)
            if similarity > 0.7:  # High similarity threshold for AI content
                similar_items.append(match)
        
        if similar_items:
            return similar_items
        
        # If no source matches, check by tags
        if item.tags:
            tag_matches = self.knowledge_base.search(
                knowledge_type=KnowledgeType.AI,
                tags=item.tags[:3],
                limit=5
            )
            
            for match in tag_matches:
                similarity = self._calculate_text_similarity(item.content, match.content)
                if similarity > 0.6:  # Lower threshold for tag matches
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
    
    def _calculate_ai_confidence(self, response: Dict[str, Any]) -> float:
        """Calculate confidence score for AI response.
        
        Args:
            response: API response
            
        Returns:
            Confidence score (0-1)
        """
        # This is a placeholder for a more sophisticated confidence calculation
        # In a real implementation, you would analyze the response for indicators of confidence
        
        # Check if the model provides a logprobs or similar confidence indicator
        if "choices" in response and response["choices"]:
            choice = response["choices"][0]
            
            # Check for finish_reason
            if "finish_reason" in choice:
                if choice["finish_reason"] == "stop":
                    # Natural completion, higher confidence
                    base_confidence = 0.85
                else:
                    # Truncated or other reason, lower confidence
                    base_confidence = 0.7
            else:
                base_confidence = 0.75
            
            # Adjust based on model
            model = response.get("model", "")
            if "gpt-4" in model:
                base_confidence *= 1.1  # Boost confidence for GPT-4
            
            return min(1.0, base_confidence)  # Cap at 1.0
        
        return 0.75  # Default confidence
    
    def _calculate_api_confidence(self, response: Dict[str, Any], api_name: str) -> float:
        """Calculate confidence score for specialized API response.
        
        Args:
            response: API response
            api_name: Name of the API
            
        Returns:
            Confidence score (0-1)
        """
        # This would be customized based on the specific API
        if "confidence" in response:
            return float(response["confidence"])
        
        if "probability" in response:
            return float(response["probability"])
        
        if "score" in response:
            return min(1.0, float(response["score"]) / 100.0)
        
        return 0.7  # Default confidence for specialized APIs
    
    def _extract_content_from_api_response(self, response: Dict[str, Any], api_name: str) -> str:
        """Extract content from specialized API response.
        
        Args:
            response: API response
            api_name: Name of the API
            
        Returns:
            Extracted content
        """
        # This would be customized based on the specific API
        if "content" in response:
            return response["content"]
        
        if "result" in response:
            if isinstance(response["result"], str):
                return response["result"]
            return json.dumps(response["result"], indent=2)
        
        if "analysis" in response:
            return response["analysis"]
        
        # Fall back to full response
        return json.dumps(response, indent=2)
    
    def get_query_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get query history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of query history entries
        """
        return self.query_history[-limit:]
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get statistics about queries.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_queries": len(self.query_history),
            "by_source": {},
            "by_model": {},
            "recent_queries": len([q for q in self.query_history 
                                 if (datetime.now() - q["timestamp"]).days < 30])
        }
        
        # Count by source and model
        for query in self.query_history:
            source = query["source"]
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
            
            model = query["model"]
            stats["by_model"][model] = stats["by_model"].get(model, 0) + 1
        
        return stats
