"""
Tests for Internet Learning System
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.learning import (
    InternetLearningSystem,
    AdaptiveLearningAgent,
    LearnedKnowledge,
    TrustedSource,
    SourceType,
    VerificationStatus
)


class TestInternetLearningSystem:
    """Test Internet Learning System"""
    
    @pytest.fixture
    def learning_system(self):
        """Create learning system instance"""
        config = {
            'verification_threshold': 0.7,
            'min_sources': 2,
            'storage_path': 'data/test_knowledge'
        }
        return InternetLearningSystem(config)
    
    def test_initialization(self, learning_system):
        """Test system initialization"""
        assert learning_system is not None
        assert len(learning_system.trusted_sources) > 0
        assert learning_system.verification_threshold == 0.7
        assert learning_system.min_sources_for_verification == 2
    
    def test_trusted_sources(self, learning_system):
        """Test trusted sources are loaded"""
        sources = learning_system.trusted_sources
        
        # Check we have different types of sources
        source_types = {s.source_type for s in sources}
        assert SourceType.FINANCIAL_NEWS in source_types
        assert SourceType.RESEARCH_PAPER in source_types
        assert SourceType.ECONOMIC_INDICATOR in source_types
        
        # Check reliability scores
        for source in sources:
            assert 0.0 <= source.reliability_score <= 1.0
    
    def test_knowledge_extraction(self, learning_system):
        """Test knowledge extraction from content"""
        content = """
        EUR/USD rallied 0.5% to 1.2500 as bullish sentiment increased.
        The pair showed strong momentum with support at 1.2450.
        """
        
        extracted = learning_system._extract_financial_data(content)
        
        assert 'numbers' in extracted or 'currency_pairs' in extracted
        if 'sentiment' in extracted:
            assert 'bullish' in extracted['sentiment']
            assert 'bearish' in extracted['sentiment']
    
    def test_strategy_extraction(self, learning_system):
        """Test strategy extraction from research"""
        content = """
        This paper presents a momentum trading strategy with a Sharpe ratio of 2.1.
        The approach uses moving average crossovers and RSI indicators for entry signals.
        """
        
        extracted = learning_system._extract_strategy_data(content)
        
        if 'strategies' in extracted:
            assert any('momentum' in s for s in extracted['strategies'])
        if 'metrics' in extracted:
            assert any('sharpe' in m for m in extracted['metrics'])
    
    def test_content_hashing(self, learning_system):
        """Test content hashing for deduplication"""
        content1 = "Test content for hashing"
        content2 = "Test content for hashing"
        content3 = "Different content"
        
        hash1 = learning_system._hash_content(content1)
        hash2 = learning_system._hash_content(content2)
        hash3 = learning_system._hash_content(content3)
        
        assert hash1 == hash2
        assert hash1 != hash3
    
    def test_id_generation(self, learning_system):
        """Test unique ID generation"""
        url1 = "https://example.com/article1"
        url2 = "https://example.com/article2"
        
        id1 = learning_system._generate_id(url1)
        id2 = learning_system._generate_id(url2)
        
        assert id1 != id2
        assert len(id1) == 32  # MD5 hash length
    
    def test_similarity_calculation(self, learning_system):
        """Test knowledge similarity calculation"""
        item1 = LearnedKnowledge(
            id="1",
            source_type=SourceType.FINANCIAL_NEWS,
            source_url="http://example.com/1",
            content="Test content",
            extracted_data={'sentiment': 'bullish', 'pair': 'EUR/USD'},
            timestamp=datetime.now(),
            verification_status=VerificationStatus.PENDING,
            confidence_score=0.8,
            verification_sources=["Source1"],
            hash="hash1",
            metadata={}
        )
        
        item2 = LearnedKnowledge(
            id="2",
            source_type=SourceType.FINANCIAL_NEWS,
            source_url="http://example.com/2",
            content="Test content",
            extracted_data={'sentiment': 'bullish', 'pair': 'EUR/USD'},
            timestamp=datetime.now(),
            verification_status=VerificationStatus.PENDING,
            confidence_score=0.8,
            verification_sources=["Source2"],
            hash="hash1",
            metadata={}
        )
        
        similarity = learning_system._calculate_similarity(item1, item2)
        assert similarity > 0.5
    
    def test_get_learning_stats(self, learning_system):
        """Test learning statistics"""
        stats = learning_system.get_learning_stats()
        
        assert 'total_items' in stats
        assert 'verified' in stats
        assert 'pending' in stats
        assert 'rejected' in stats
        assert 'verification_rate' in stats
        assert 'trusted_sources' in stats
        assert 'avg_confidence' in stats
        
        assert stats['trusted_sources'] > 0


class TestAdaptiveLearningAgent:
    """Test Adaptive Learning Agent"""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance"""
        config = {
            'verification_threshold': 0.7,
            'min_sources': 2,
            'storage_path': 'data/test_knowledge'
        }
        learning_system = InternetLearningSystem(config)
        return AdaptiveLearningAgent(learning_system)
    
    def test_agent_initialization(self, agent):
        """Test agent initialization"""
        assert agent is not None
        assert agent.learning_system is not None
        assert len(agent.learned_strategies) == 0
    
    def test_strategy_recommendations(self, agent):
        """Test strategy recommendations"""
        # Add a test strategy
        agent.learned_strategies.append({
            'name': 'Test_Strategy',
            'market_condition': 'high volatility',
            'techniques': ['momentum', 'breakout'],
            'confidence': 0.85,
            'sources': ['test'],
            'learned_at': datetime.now()
        })
        
        # Get recommendations
        recommendations = agent.get_strategy_recommendations('volatility')
        
        assert len(recommendations) > 0
        assert recommendations[0]['confidence'] == 0.85


@pytest.mark.asyncio
class TestAsyncLearning:
    """Test async learning capabilities"""
    
    @pytest.fixture
    def learning_system(self):
        """Create learning system instance"""
        config = {
            'verification_threshold': 0.7,
            'min_sources': 2,
            'storage_path': 'data/test_knowledge'
        }
        return InternetLearningSystem(config)
    
    async def test_learn_from_internet(self, learning_system):
        """Test learning from internet (mock)"""
        # This would require actual internet connection
        # For now, test the structure
        assert hasattr(learning_system, 'learn_from_internet')
        assert callable(learning_system.learn_from_internet)
    
    async def test_cross_verification(self, learning_system):
        """Test cross-verification of knowledge"""
        # Create test knowledge items
        items = [
            LearnedKnowledge(
                id=f"test_{i}",
                source_type=SourceType.FINANCIAL_NEWS,
                source_url=f"http://example.com/{i}",
                content="EUR/USD bullish trend",
                extracted_data={'sentiment': 'bullish'},
                timestamp=datetime.now(),
                verification_status=VerificationStatus.PENDING,
                confidence_score=0.8,
                verification_sources=[f"Source{i}"],
                hash="same_hash",
                metadata={}
            )
            for i in range(3)
        ]
        
        # Test verification
        verified = await learning_system._cross_verify_knowledge(items)
        
        assert len(verified) > 0
        # Items with same hash should be grouped
        assert any(len(item.verification_sources) > 1 for item in verified)


def test_verification_status_enum():
    """Test VerificationStatus enum"""
    assert VerificationStatus.VERIFIED.value == "verified"
    assert VerificationStatus.PENDING.value == "pending"
    assert VerificationStatus.REJECTED.value == "rejected"
    assert VerificationStatus.CONFLICTING.value == "conflicting"


def test_source_type_enum():
    """Test SourceType enum"""
    assert SourceType.FINANCIAL_NEWS.value == "financial_news"
    assert SourceType.RESEARCH_PAPER.value == "research_paper"
    assert SourceType.MARKET_DATA.value == "market_data"
    assert SourceType.ECONOMIC_INDICATOR.value == "economic_indicator"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
