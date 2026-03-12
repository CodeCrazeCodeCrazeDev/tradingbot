"""
Internet-Based Learning System with Verification
Allows the bot to learn from verified online sources safely
"""

import asyncio
import aiohttp
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import re
from bs4 import BeautifulSoup
import feedparser
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Types of learning sources"""
    FINANCIAL_NEWS = "financial_news"
    RESEARCH_PAPER = "research_paper"
    MARKET_DATA = "market_data"
    ECONOMIC_INDICATOR = "economic_indicator"
    TRADING_STRATEGY = "trading_strategy"
    TECHNICAL_ANALYSIS = "technical_analysis"
    SOCIAL_SENTIMENT = "social_sentiment"


class VerificationStatus(Enum):
    """Verification status of learned information"""
    VERIFIED = "verified"
    PENDING = "pending"
    REJECTED = "rejected"
    CONFLICTING = "conflicting"


@dataclass
class LearnedKnowledge:
    """Represents a piece of learned knowledge"""
    id: str
    source_type: SourceType
    source_url: str
    content: str
    extracted_data: Dict[str, Any]
    timestamp: datetime
    verification_status: VerificationStatus
    confidence_score: float
    verification_sources: List[str]
    hash: str
    metadata: Dict[str, Any]


@dataclass
class TrustedSource:
    """Represents a trusted learning source"""
    name: str
    url: str
    source_type: SourceType
    reliability_score: float
    last_verified: datetime
    api_key: Optional[str] = None


class InternetLearningSystem:
    """
    Internet-based learning system with multi-source verification
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.knowledge_base: Dict[str, LearnedKnowledge] = {}
        self.trusted_sources: List[TrustedSource] = []
        self.verification_threshold = self.config.get('verification_threshold', 0.7)
        self.min_sources_for_verification = self.config.get('min_sources', 3)
        self.learning_history = deque(maxlen=10000)
        
        # Initialize trusted sources
        self._initialize_trusted_sources()
        
        # Knowledge storage
        self.storage_path = Path(self.config.get('storage_path', 'data/learned_knowledge'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("Internet Learning System initialized")
    
    def _initialize_trusted_sources(self):
        """Initialize list of trusted sources"""
        # Financial News
        self.trusted_sources.extend([
            TrustedSource(
                name="Bloomberg",
                url="https://www.bloomberg.com/feeds/markets/news.rss",
                source_type=SourceType.FINANCIAL_NEWS,
                reliability_score=0.95,
                last_verified=datetime.now()
            ),
            TrustedSource(
                name="Reuters",
                url="https://www.reuters.com/finance",
                source_type=SourceType.FINANCIAL_NEWS,
                reliability_score=0.95,
                last_verified=datetime.now()
            ),
            TrustedSource(
                name="Financial Times",
                url="https://www.ft.com/markets",
                source_type=SourceType.FINANCIAL_NEWS,
                reliability_score=0.90,
                last_verified=datetime.now()
            )
        ])
        
        # Economic Data
        self.trusted_sources.extend([
            TrustedSource(
                name="FRED",
                url="https://fred.stlouisfed.org/",
                source_type=SourceType.ECONOMIC_INDICATOR,
                reliability_score=1.0,
                last_verified=datetime.now()
            ),
            TrustedSource(
                name="World Bank",
                url="https://data.worldbank.org/",
                source_type=SourceType.ECONOMIC_INDICATOR,
                reliability_score=0.95,
                last_verified=datetime.now()
            )
        ])
        
        # Research Papers
        self.trusted_sources.extend([
            TrustedSource(
                name="arXiv Quantitative Finance",
                url="https://arxiv.org/list/q-fin/recent",
                source_type=SourceType.RESEARCH_PAPER,
                reliability_score=0.85,
                last_verified=datetime.now()
            ),
            TrustedSource(
                name="SSRN",
                url="https://www.ssrn.com/index.cfm/en/",
                source_type=SourceType.RESEARCH_PAPER,
                reliability_score=0.80,
                last_verified=datetime.now()
            )
        ])
    
    async def learn_from_internet(self, topic: str, max_sources: int = 5) -> List[LearnedKnowledge]:
        """
        Learn about a topic from multiple verified internet sources
        """
        logger.info(f"Learning about topic: {topic}")
        
        learned_items = []
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for source in self.trusted_sources[:max_sources]:
                tasks.append(self._fetch_from_source(session, source, topic))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error fetching from source: {result}")
                    continue
                
                if result:
                    learned_items.extend(result)
        
        # Cross-verify learned items
        verified_items = await self._cross_verify_knowledge(learned_items)
        
        # Store verified knowledge
        for item in verified_items:
            self.knowledge_base[item.id] = item
            self._save_knowledge(item)
        
        logger.info(f"Learned {len(verified_items)} verified items about {topic}")
        return verified_items
    
    async def _fetch_from_source(
        self, 
        session: aiohttp.ClientSession, 
        source: TrustedSource, 
        topic: str
    ) -> List[LearnedKnowledge]:
        """Fetch information from a specific source"""
        try:
            if source.source_type == SourceType.FINANCIAL_NEWS:
                return await self._fetch_news(session, source, topic)
            elif source.source_type == SourceType.RESEARCH_PAPER:
                return await self._fetch_research(session, source, topic)
            elif source.source_type == SourceType.ECONOMIC_INDICATOR:
                return await self._fetch_economic_data(session, source, topic)
            else:
                logger.warning(f"Unsupported source type: {source.source_type}")
                return []
        except Exception as e:
            logger.error(f"Error fetching from {source.name}: {e}")
            return []
    
    async def _fetch_news(
        self, 
        session: aiohttp.ClientSession, 
        source: TrustedSource, 
        topic: str
    ) -> List[LearnedKnowledge]:
        """Fetch news articles"""
        items = []
        
        try:
            # Try RSS feed first
            feed = feedparser.parse(source.url)
            
            for entry in feed.entries[:10]:  # Limit to 10 articles
                if topic.lower() in entry.title.lower() or topic.lower() in entry.get('summary', '').lower():
                    content = entry.get('summary', entry.get('description', ''))
                    
                    # Extract key information
                    extracted_data = self._extract_financial_data(content)
                    
                    knowledge = LearnedKnowledge(
                        id=self._generate_id(entry.link),
                        source_type=source.source_type,
                        source_url=entry.link,
                        content=content,
                        extracted_data=extracted_data,
                        timestamp=datetime.now(),
                        verification_status=VerificationStatus.PENDING,
                        confidence_score=source.reliability_score,
                        verification_sources=[source.name],
                        hash=self._hash_content(content),
                        metadata={
                            'title': entry.title,
                            'published': entry.get('published', ''),
                            'source': source.name
                        }
                    )
                    items.append(knowledge)
        
        except Exception as e:
            logger.error(f"Error fetching news from {source.name}: {e}")
        
        return items
    
    async def _fetch_research(
        self, 
        session: aiohttp.ClientSession, 
        source: TrustedSource, 
        topic: str
    ) -> List[LearnedKnowledge]:
        """Fetch research papers"""
        items = []
        
        try:
            # Search arXiv for relevant papers
            search_url = f"http://export.arxiv.org/api/query?search_query=all:{topic}&start=0&max_results=5"
            
            async with session.get(search_url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Parse XML response
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(content)
                    
                    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                        title = entry.find('{http://www.w3.org/2005/Atom}title').text
                        summary = entry.find('{http://www.w3.org/2005/Atom}summary').text
                        link = entry.find('{http://www.w3.org/2005/Atom}id').text
                        
                        # Extract trading strategies or insights
                        extracted_data = self._extract_strategy_data(summary)
                        
                        knowledge = LearnedKnowledge(
                            id=self._generate_id(link),
                            source_type=source.source_type,
                            source_url=link,
                            content=summary,
                            extracted_data=extracted_data,
                            timestamp=datetime.now(),
                            verification_status=VerificationStatus.PENDING,
                            confidence_score=source.reliability_score * 0.8,  # Research needs more verification
                            verification_sources=[source.name],
                            hash=self._hash_content(summary),
                            metadata={
                                'title': title,
                                'source': source.name,
                                'type': 'research_paper'
                            }
                        )
                        items.append(knowledge)
        
        except Exception as e:
            logger.error(f"Error fetching research from {source.name}: {e}")
        
        return items
    
    async def _fetch_economic_data(
        self, 
        session: aiohttp.ClientSession, 
        source: TrustedSource, 
        topic: str
    ) -> List[LearnedKnowledge]:
        """Fetch economic indicators"""
        items = []
        
        # This would integrate with FRED API or similar
        # For now, return empty list
        logger.info(f"Economic data fetching for {topic} - requires API key")
        
        return items
    
    async def _cross_verify_knowledge(self, items: List[LearnedKnowledge]) -> List[LearnedKnowledge]:
        """Cross-verify knowledge from multiple sources"""
        verified_items = []
        
        # Group items by content similarity
        groups = self._group_similar_items(items)
        
        for group in groups:
            if len(group) >= self.min_sources_for_verification:
                # Calculate consensus confidence
                avg_confidence = np.mean([item.confidence_score for item in group])
                
                if avg_confidence >= self.verification_threshold:
                    # Create verified knowledge item
                    primary_item = group[0]
                    primary_item.verification_status = VerificationStatus.VERIFIED
                    primary_item.confidence_score = avg_confidence
                    primary_item.verification_sources = [item.verification_sources[0] for item in group]
                    
                    verified_items.append(primary_item)
                    logger.info(f"Verified knowledge: {primary_item.metadata.get('title', 'Unknown')}")
                else:
                    # Mark as conflicting if confidence is low
                    primary_item.verification_status = VerificationStatus.CONFLICTING
                    verified_items.append(primary_item)
            else:
                # Single source - mark as pending
                group[0].verification_status = VerificationStatus.PENDING
                verified_items.append(group[0])
        
        return verified_items
    
    def _group_similar_items(self, items: List[LearnedKnowledge]) -> List[List[LearnedKnowledge]]:
        """Group similar knowledge items"""
        groups = []
        used_indices = set()
        
        for i, item1 in enumerate(items):
            if i in used_indices:
                continue
            
            group = [item1]
            used_indices.add(i)
            
            for j, item2 in enumerate(items[i+1:], start=i+1):
                if j in used_indices:
                    continue
                
                # Check similarity
                if self._calculate_similarity(item1, item2) > 0.7:
                    group.append(item2)
                    used_indices.add(j)
            
            groups.append(group)
        
        return groups
    
    def _calculate_similarity(self, item1: LearnedKnowledge, item2: LearnedKnowledge) -> float:
        """Calculate similarity between two knowledge items"""
        # Simple hash-based similarity
        if item1.hash == item2.hash:
            return 1.0
        
        # Check extracted data similarity
        common_keys = set(item1.extracted_data.keys()) & set(item2.extracted_data.keys())
        if not common_keys:
            return 0.0
        
        matches = sum(
            1 for key in common_keys 
            if item1.extracted_data[key] == item2.extracted_data[key]
        )
        
        return matches / len(common_keys)
    
    def _extract_financial_data(self, content: str) -> Dict[str, Any]:
        """Extract financial data from content"""
        data = {}
        
        # Extract numbers (prices, percentages, etc.)
        numbers = re.findall(r'\$?[\d,]+\.?\d*%?', content)
        if numbers:
            data['numbers'] = numbers
        
        # Extract currency pairs
        currency_pairs = re.findall(r'[A-Z]{3}/[A-Z]{3}', content)
        if currency_pairs:
            data['currency_pairs'] = currency_pairs
        
        # Extract sentiment keywords
        bullish_words = ['bullish', 'rally', 'surge', 'gain', 'rise', 'up']
        bearish_words = ['bearish', 'fall', 'drop', 'decline', 'down', 'crash']
        
        content_lower = content.lower()
        bullish_count = sum(1 for word in bullish_words if word in content_lower)
        bearish_count = sum(1 for word in bearish_words if word in content_lower)
        
        if bullish_count > 0 or bearish_count > 0:
            data['sentiment'] = {
                'bullish': bullish_count,
                'bearish': bearish_count,
                'score': (bullish_count - bearish_count) / max(bullish_count + bearish_count, 1)
            }
        
        return data
    
    def _extract_strategy_data(self, content: str) -> Dict[str, Any]:
        """Extract trading strategy information"""
        data = {}
        
        # Extract strategy keywords
        strategy_keywords = [
            'momentum', 'mean reversion', 'arbitrage', 'pairs trading',
            'trend following', 'breakout', 'support', 'resistance',
            'moving average', 'RSI', 'MACD', 'Bollinger'
        ]
        
        content_lower = content.lower()
        found_strategies = [kw for kw in strategy_keywords if kw in content_lower]
        
        if found_strategies:
            data['strategies'] = found_strategies
        
        # Extract performance metrics
        metrics = re.findall(r'sharpe ratio|win rate|drawdown|return', content_lower)
        if metrics:
            data['metrics'] = list(set(metrics))
        
        return data
    
    def _generate_id(self, url: str) -> str:
        """Generate unique ID for knowledge item"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _hash_content(self, content: str) -> str:
        """Hash content for similarity checking"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _save_knowledge(self, knowledge: LearnedKnowledge):
        """Save knowledge to disk"""
        try:
            file_path = self.storage_path / f"{knowledge.id}.json"
            
            # Convert to dict for JSON serialization
            data = asdict(knowledge)
            data['source_type'] = knowledge.source_type.value
            data['verification_status'] = knowledge.verification_status.value
            data['timestamp'] = knowledge.timestamp.isoformat()
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving knowledge: {e}")
    
    def get_verified_knowledge(self, topic: Optional[str] = None) -> List[LearnedKnowledge]:
        """Get verified knowledge, optionally filtered by topic"""
        verified = [
            k for k in self.knowledge_base.values()
            if k.verification_status == VerificationStatus.VERIFIED
        ]
        
        if topic:
            topic_lower = topic.lower()
            verified = [
                k for k in verified
                if topic_lower in k.content.lower() or 
                   topic_lower in k.metadata.get('title', '').lower()
            ]
        
        return verified
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        total = len(self.knowledge_base)
        verified = sum(1 for k in self.knowledge_base.values() 
                      if k.verification_status == VerificationStatus.VERIFIED)
        pending = sum(1 for k in self.knowledge_base.values() 
                     if k.verification_status == VerificationStatus.PENDING)
        rejected = sum(1 for k in self.knowledge_base.values() 
                      if k.verification_status == VerificationStatus.REJECTED)
        
        return {
            'total_items': total,
            'verified': verified,
            'pending': pending,
            'rejected': rejected,
            'verification_rate': verified / total if total > 0 else 0,
            'trusted_sources': len(self.trusted_sources),
            'avg_confidence': np.mean([k.confidence_score for k in self.knowledge_base.values()]) 
                            if self.knowledge_base else 0
        }


class AdaptiveLearningAgent:
    """
    Agent that uses internet learning to adapt trading strategies
    """
    
    def __init__(self, learning_system: InternetLearningSystem):
        self.learning_system = learning_system
        self.learned_strategies = []
        self.performance_history = deque(maxlen=1000)
    
    async def learn_new_strategy(self, market_condition: str) -> Optional[Dict[str, Any]]:
        """Learn new trading strategy based on market conditions"""
        logger.info(f"Learning strategy for market condition: {market_condition}")
        
        # Search for relevant strategies
        knowledge_items = await self.learning_system.learn_from_internet(
            topic=f"trading strategy {market_condition}",
            max_sources=5
        )
        
        # Extract verified strategies
        strategies = []
        for item in knowledge_items:
            if item.verification_status == VerificationStatus.VERIFIED:
                if 'strategies' in item.extracted_data:
                    strategies.extend(item.extracted_data['strategies'])
        
        if strategies:
            # Create strategy configuration
            strategy_config = {
                'name': f"Learned_{market_condition}_{datetime.now().strftime('%Y%m%d')}",
                'market_condition': market_condition,
                'techniques': strategies,
                'confidence': np.mean([k.confidence_score for k in knowledge_items]),
                'sources': [k.source_url for k in knowledge_items],
                'learned_at': datetime.now()
            }
            
            self.learned_strategies.append(strategy_config)
            logger.info(f"Learned new strategy: {strategy_config['name']}")
            return strategy_config
        
        return None
    
    async def update_market_knowledge(self):
        """Update knowledge about current market conditions"""
        topics = [
            "forex market trends",
            "economic indicators",
            "central bank policy",
            "market volatility",
            "trading signals"
        ]
        
        for topic in topics:
            await self.learning_system.learn_from_internet(topic, max_sources=3)
        
        stats = self.learning_system.get_learning_stats()
        logger.info(f"Market knowledge updated: {stats}")
    
    def get_strategy_recommendations(self, market_condition: str) -> List[Dict[str, Any]]:
        """Get strategy recommendations based on learned knowledge"""
        recommendations = []
        
        for strategy in self.learned_strategies:
            if market_condition.lower() in strategy['market_condition'].lower():
                recommendations.append(strategy)
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        return recommendations


# Example usage
async def main():
    """Example usage of Internet Learning System"""
    
    # Initialize learning system
    config = {
        'verification_threshold': 0.7,
        'min_sources': 2,
        'storage_path': 'data/learned_knowledge'
    }
    
    learning_system = InternetLearningSystem(config)
    
    # Create adaptive learning agent
    agent = AdaptiveLearningAgent(learning_system)
    
    # Learn about a topic
    logger.info("Learning about forex trading strategies...")
    knowledge = await learning_system.learn_from_internet("forex trading strategies", max_sources=5)
    
    logger.info(f"\nLearned {len(knowledge)} items")
    
    # Get verified knowledge
    verified = learning_system.get_verified_knowledge()
    logger.info(f"Verified items: {len(verified)}")
    
    # Learn new strategy
    strategy = await agent.learn_new_strategy("high volatility")
    if strategy:
        logger.info(f"\nLearned strategy: {strategy['name']}")
        logger.info(f"Techniques: {strategy['techniques']}")
        logger.info(f"Confidence: {strategy['confidence']:.2%}")
    
    # Get statistics
    stats = learning_system.get_learning_stats()
    logger.info(f"\nLearning Statistics:")
    logger.info(f"  Total items: {stats['total_items']}")
    logger.info(f"  Verified: {stats['verified']}")
    logger.info(f"  Verification rate: {stats['verification_rate']:.2%}")
    logger.info(f"  Average confidence: {stats['avg_confidence']:.2%}")


if __name__ == '__main__':
    asyncio.run(main())
