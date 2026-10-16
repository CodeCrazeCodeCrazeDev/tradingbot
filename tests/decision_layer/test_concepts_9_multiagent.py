"""
Comprehensive tests for concepts_9_multiagent
"""

import pytest
import logging
from pathlib import Path

try:
    from trading_bot.decision_layer.concepts_9_multiagent import *
    from trading_bot.decision_layer.core_types import DecisionContext
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from trading_bot.decision_layer.concepts_9_multiagent import *
    from trading_bot.decision_layer.core_types import DecisionContext

logger = logging.getLogger(__name__)


@pytest.fixture
def sample_context():
    return DecisionContext(
        symbol="BTC/USD",
        price=100.0,
        volume=1000.0,
        volatility=0.1,
        trend=0.1,
        momentum=0.1,
        sentiment=0.1,
        regime="normal",
        timeframe="1h",
        portfolio_value=10000.0,
        current_position=0.0,
        drawdown=0.01,
        win_rate=0.55
    )


class TestVotingEnsembleDecision:
    @pytest.fixture
    def instance(self):
        return VotingEnsembleDecision()

    def test_initialization(self, instance):
        assert instance is not None

    def test_decide(self, instance, sample_context):
        result = instance.decide(sample_context)
        assert result is not None


class TestWeightedExpertsDecision:
    @pytest.fixture
    def instance(self):
        return WeightedExpertsDecision()

    def test_initialization(self, instance):
        assert instance is not None

    def test_decide(self, instance, sample_context):
        result = instance.decide(sample_context)
        assert result is not None


class TestDebateDecision:
    @pytest.fixture
    def instance(self):
        return DebateDecision()

    def test_initialization(self, instance):
        assert instance is not None

    def test_decide(self, instance, sample_context):
        result = instance.decide(sample_context)
        assert result is not None


class TestConsensusDecision:
    @pytest.fixture
    def instance(self):
        return ConsensusDecision()

    def test_initialization(self, instance):
        assert instance is not None

    def test_decide(self, instance, sample_context):
        result = instance.decide(sample_context)
        assert result is not None


class TestHierarchicalDecision:
    @pytest.fixture
    def instance(self):
        return HierarchicalDecision()

    def test_initialization(self, instance):
        assert instance is not None

    def test_decide(self, instance, sample_context):
        result = instance.decide(sample_context)
        assert result is not None


class TestSwarmIntelligenceDecision:
    @pytest.fixture
    def instance(self):
        return SwarmIntelligenceDecision()

    def test_initialization(self, instance):
        assert instance is not None

    def test_decide(self, instance, sample_context):
        result = instance.decide(sample_context)
        assert result is not None


class TestAdversarialDecision:
    @pytest.fixture
    def instance(self):
        return AdversarialDecision()

    def test_initialization(self, instance):
        assert instance is not None

    def test_decide(self, instance, sample_context):
        result = instance.decide(sample_context)
        assert result is not None


class TestSpecialistCommitteeDecision:
    @pytest.fixture
    def instance(self):
        return SpecialistCommitteeDecision()

    def test_initialization(self, instance):
        assert instance is not None

    def test_decide(self, instance, sample_context):
        result = instance.decide(sample_context)
        assert result is not None


class TestMarketMakingAgentDecision:
    @pytest.fixture
    def instance(self):
        return MarketMakingAgentDecision()

    def test_initialization(self, instance):
        assert instance is not None

    def test_decide(self, instance, sample_context):
        result = instance.decide(sample_context)
        assert result is not None


class TestArbitrageAgentDecision:
    @pytest.fixture
    def instance(self):
        return ArbitrageAgentDecision()

    def test_initialization(self, instance):
        assert instance is not None

    def test_decide(self, instance, sample_context):
        result = instance.decide(sample_context)
        assert result is not None


def test_concepts_registry(sample_context):
    for cls in MULTIAGENT_CONCEPTS:
        obj = cls()
        res = obj.decide(sample_context)
        assert res is not None


def test_module_integration():
    assert len(MULTIAGENT_CONCEPTS) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
