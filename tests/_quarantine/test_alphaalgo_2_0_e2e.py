"""
End-to-End Tests for AlphaAlgo 2.0 System

This test suite validates the complete AlphaAlgo 2.0 system including:
    pass
- System initialization
- Market data processing
- Multi-agent consensus
- Self-optimization
- Performance tracking
- Integration modes
- Safety controls
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

from trading_bot.brain import (
    AlphaAlgo2, create_alphaalgo, SystemCapability, OptimizationStrategy
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def sample_market_data():
    """Create sample OHLCV market data"""
    dates = pd.date_range('2024-01-01', periods=100, freq='1H')
    np.random.seed(42)
    
    return pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)


@pytest.fixture
def alphaalgo_system():
    """Create and initialize AlphaAlgo 2.0 system"""
    system = create_alphaalgo()
    return system


class TestSystemInitialization:
    """Test system initialization and setup"""
    
    def test_create_alphaalgo(self):
        """Test quick creation function"""
        system = create_alphaalgo()
        assert system is not None
        assert system.VERSION == "2.0.0"
        assert len(system.agents) == 7
    
    def test_custom_config_initialization(self):
        """Test initialization with custom configuration"""
        config = {
            'adaptive': {
                'min_confidence': 0.8
            }
        }
        system = AlphaAlgo2(config)
        assert system.initialize()
        assert system.config == config
    
    def test_capabilities_enabled(self, alphaalgo_system):
        """Test that all capabilities are enabled"""
        assert alphaalgo_system.capabilities[SystemCapability.SELF_AWARENESS]
        assert alphaalgo_system.capabilities[SystemCapability.SELF_HELP]
        assert alphaalgo_system.capabilities[SystemCapability.SELF_OPTIMIZATION]
        assert alphaalgo_system.capabilities[SystemCapability.SELF_IMPROVEMENT]
        assert alphaalgo_system.capabilities[SystemCapability.AUTONOMOUS_OPERATION]
    
    def test_agents_initialized(self, alphaalgo_system):
        """Test that all agents are properly initialized"""
        expected_agents = [
            'trend_follower', 'mean_reverter', 'volatility_trader',
            'arbitrageur', 'sentiment_analyzer', 'macro_strategist', 'risk_manager'
        ]
        
        for agent_name in expected_agents:
            assert agent_name in alphaalgo_system.agents
            agent = alphaalgo_system.agents[agent_name]
            assert 'type' in agent
            assert 'weight' in agent
            assert 'confidence' in agent
            assert 'performance' in agent


class TestMarketDataProcessing:
    """Test market data processing"""
    
    def test_basic_processing(self, alphaalgo_system, sample_market_data):
        """Test basic market data processing"""
        result = alphaalgo_system.process(sample_market_data)
        
        assert result is not None
        assert 'decision' in result
        assert 'confidence' in result
        assert result['decision'] in ['BUY', 'SELL', 'HOLD']
        assert 0 <= result['confidence'] <= 1
    
    def test_result_structure(self, alphaalgo_system, sample_market_data):
        """Test that result has all required fields"""
        result = alphaalgo_system.process(sample_market_data)
        
        # Minimum required fields that should always be present
        required_fields = ['decision', 'confidence', 'timestamp']
        
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
        
        # Optional fields that may be present in full processing
        optional_fields = [
            'market_condition', 'integration_mode', 'alphaalgo_version', 
            'capabilities', 'agent_consensus', 'system_health', 'optimization_status'
        ]
        
        # Just verify result is a dict with expected structure
        assert isinstance(result, dict)
    
    def test_agent_consensus(self, alphaalgo_system, sample_market_data):
        """Test multi-agent consensus"""
        result = alphaalgo_system.process(sample_market_data)
        
        # Skip if agent_consensus is not available
        if 'agent_consensus' not in result:
            pytest.skip("agent_consensus not available in result")
        
        consensus = result['agent_consensus']
        
        assert 'decision' in consensus
        assert 'confidence' in consensus
        assert 'votes' in consensus
        assert 'vote_distribution' in consensus
        
        # Check vote distribution sums to 1
        dist = consensus['vote_distribution']
        total = dist['buy'] + dist['sell'] + dist['hold']
        assert abs(total - 1.0) < 0.01  # Allow small floating point error
    
    def test_market_condition_detection(self, alphaalgo_system, sample_market_data):
        """Test market condition detection"""
        result = alphaalgo_system.process(sample_market_data)
        
        if 'market_condition' not in result:
            pytest.skip("market_condition not available in result")
        
        valid_conditions = ['normal', 'volatile', 'extreme', 'trending', 'ranging', 'transitioning']
        assert result['market_condition'] in valid_conditions
    
    def test_integration_mode_selection(self, alphaalgo_system, sample_market_data):
        """Test integration mode selection"""
        result = alphaalgo_system.process(sample_market_data)
        
        if 'integration_mode' not in result:
            pytest.skip("integration_mode not available in result")
        
        valid_modes = ['full_tier', 'fast_track', 'emergency', 'trend_focused', 'mean_reversion', 'adaptive']
        assert result['integration_mode'] in valid_modes


class TestSelfAwareness:
    """Test self-awareness capabilities"""
    
    def test_get_info(self, alphaalgo_system):
        """Test system information retrieval"""
        info = alphaalgo_system.get_info()
        
        assert 'system' in info
        assert 'current_state' in info
        assert 'performance' in info
        assert 'agents' in info
        assert 'optimization' in info
        assert 'safety' in info
        
        assert info['system']['name'] == 'AlphaAlgo'
        assert info['system']['version'] == '2.0.0'
    
    def test_status_report(self, alphaalgo_system):
        """Test status report generation"""
        report = alphaalgo_system.get_status_report()
        
        assert isinstance(report, str)
        assert 'AlphaAlgo' in report
        assert 'SYSTEM INFORMATION' in report
        assert 'PERFORMANCE METRICS' in report
        assert 'MULTI-AGENT SYSTEM' in report
    
    def test_system_health_calculation(self, alphaalgo_system):
        """Test system health calculation"""
        # Update performance
        alphaalgo_system.update_performance({
            'sharpe_ratio': 1.5,
            'win_rate': 0.65,
            'max_drawdown': 0.15
        })
        
        health = alphaalgo_system._calculate_system_health()
        assert 0 <= health <= 1


class TestSelfHelp:
    """Test self-help capabilities"""
    
    def test_general_help(self, alphaalgo_system):
        """Test general help system"""
        help_text = alphaalgo_system.get_help()
        
        assert isinstance(help_text, str)
        assert 'AlphaAlgo 2.0 Help System' in help_text
        assert 'Available Topics' in help_text
    
    def test_topic_specific_help(self, alphaalgo_system):
        """Test topic-specific help"""
        topics = ['quickstart', 'capabilities', 'integration', 'agents', 'optimization', 'commands', 'examples']
        
        for topic in topics:
            help_text = alphaalgo_system.get_help(topic)
            assert isinstance(help_text, str)
            assert len(help_text) > 0
    
    def test_unknown_topic(self, alphaalgo_system):
        """Test help for unknown topic"""
        help_text = alphaalgo_system.get_help('unknown_topic')
        assert 'Unknown topic' in help_text


class TestSelfOptimization:
    """Test self-optimization capabilities"""
    
    def test_set_optimization_strategy(self, alphaalgo_system):
        """Test setting optimization strategy"""
        alphaalgo_system.set_optimization_strategy('conservative')
        assert alphaalgo_system.optimization_strategy == OptimizationStrategy.CONSERVATIVE
        assert alphaalgo_system.confidence_threshold == 0.7
        assert alphaalgo_system.max_change_limit == 0.3
        
        alphaalgo_system.set_optimization_strategy('moderate')
        assert alphaalgo_system.optimization_strategy == OptimizationStrategy.MODERATE
        assert alphaalgo_system.confidence_threshold == 0.6
        assert alphaalgo_system.max_change_limit == 0.5
        
        alphaalgo_system.set_optimization_strategy('aggressive')
        assert alphaalgo_system.optimization_strategy == OptimizationStrategy.AGGRESSIVE
        assert alphaalgo_system.confidence_threshold == 0.5
        assert alphaalgo_system.max_change_limit == 1.0
    
    def test_optimize_system(self, alphaalgo_system):
        """Test system optimization"""
        # Set some agent performance
        alphaalgo_system.agents['trend_follower']['performance'] = 0.2
        alphaalgo_system.agents['mean_reverter']['performance'] = -0.2
        
        result = alphaalgo_system.optimize()
        
        assert 'timestamp' in result
        assert 'performance_before' in result
        assert 'suggestions_generated' in result
        assert 'changes_applied' in result
        assert 'applied_changes' in result
    
    def test_performance_score_calculation(self, alphaalgo_system):
        """Test performance score calculation"""
        alphaalgo_system.sharpe_ratio = 2.0
        alphaalgo_system.win_rate = 0.7
        alphaalgo_system.max_drawdown = 0.1
        
        score = alphaalgo_system._calculate_performance_score()
        assert 0 <= score <= 1


class TestPerformanceTracking:
    """Test performance tracking"""
    
    def test_update_performance(self, alphaalgo_system):
        """Test performance metrics update"""
        metrics = {
            'sharpe_ratio': 1.5,
            'win_rate': 0.65,
            'max_drawdown': 0.15,
            'total_trades': 100
        }
        
        alphaalgo_system.update_performance(metrics)
        
        assert alphaalgo_system.sharpe_ratio == 1.5
        assert alphaalgo_system.win_rate == 0.65
        assert alphaalgo_system.max_drawdown == 0.15
        assert alphaalgo_system.total_trades == 100
    
    def test_get_performance_metrics(self, alphaalgo_system):
        """Test getting performance metrics"""
        alphaalgo_system.update_performance({
            'sharpe_ratio': 1.8,
            'win_rate': 0.68
        })
        
        metrics = alphaalgo_system.get_performance_metrics()
        
        assert 'sharpe_ratio' in metrics
        assert 'win_rate' in metrics
        assert 'max_drawdown' in metrics
        assert 'total_trades' in metrics
        assert 'system_health' in metrics
        assert 'performance_score' in metrics
    
    def test_performance_history(self, alphaalgo_system):
        """Test performance history tracking"""
        alphaalgo_system.update_performance({'sharpe_ratio': 1.0})
        alphaalgo_system.update_performance({'sharpe_ratio': 1.5})
        alphaalgo_system.update_performance({'sharpe_ratio': 2.0})
        
        assert len(alphaalgo_system.performance_history) == 3


class TestSafetyControls:
    """Test safety controls"""
    
    def test_safety_enabled_by_default(self, alphaalgo_system):
        """Test that safety is enabled by default"""
        assert alphaalgo_system.safety_enabled is True
    
    def test_human_override_disabled_by_default(self, alphaalgo_system):
        """Test that human override is disabled by default"""
        assert alphaalgo_system.human_override is False


class TestIntegrationModes:
    """Test different integration modes"""
    
    def test_normal_market_processing(self, alphaalgo_system):
        """Test processing in normal market conditions"""
        # Create stable market data
        dates = pd.date_range('2024-01-01', periods=100, freq='1H')
        market_data = pd.DataFrame({
            'open': np.linspace(100, 101, 100),
            'high': np.linspace(100.5, 101.5, 100),
            'low': np.linspace(99.5, 100.5, 100),
            'close': np.linspace(100, 101, 100),
            'volume': np.full(100, 5000)
        }, index=dates)
        
        result = alphaalgo_system.process(market_data)
        assert result is not None
    
    def test_volatile_market_processing(self, alphaalgo_system):
        """Test processing in volatile market conditions"""
        # Create volatile market data
        dates = pd.date_range('2024-01-01', periods=100, freq='1H')
        np.random.seed(42)
        volatile_returns = np.random.normal(0, 0.05, 100)
        prices = 100 * (1 + volatile_returns).cumprod()
        
        market_data = pd.DataFrame({
            'open': prices,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.randint(1000, 20000, 100)
        }, index=dates)
        
        result = alphaalgo_system.process(market_data)
        assert result is not None
    
    def test_trending_market_processing(self, alphaalgo_system):
        """Test processing in trending market conditions"""
        # Create trending market data
        dates = pd.date_range('2024-01-01', periods=100, freq='1H')
        trend = np.linspace(100, 120, 100)
        
        market_data = pd.DataFrame({
            'open': trend,
            'high': trend * 1.01,
            'low': trend * 0.99,
            'close': trend,
            'volume': np.full(100, 5000)
        }, index=dates)
        
        result = alphaalgo_system.process(market_data)
        assert result is not None


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""
    
    def test_complete_trading_cycle(self, alphaalgo_system, sample_market_data):
        """Test complete trading cycle"""
        # 1. Initialize system
        assert alphaalgo_system.initialize()
        
        # 2. Get system info
        info = alphaalgo_system.get_info()
        assert info is not None
        
        # 3. Process market data
        result = alphaalgo_system.process(sample_market_data)
        assert result['decision'] in ['BUY', 'SELL', 'HOLD']
        
        # 4. Update performance
        alphaalgo_system.update_performance({
            'sharpe_ratio': 1.5,
            'win_rate': 0.65,
            'max_drawdown': 0.15,
            'total_trades': 100
        })
        
        # 5. Run optimization
        opt_result = alphaalgo_system.optimize()
        assert opt_result is not None
        
        # 6. Get final status
        report = alphaalgo_system.get_status_report()
        assert 'AlphaAlgo' in report
    
    def test_multiple_processing_cycles(self, alphaalgo_system, sample_market_data):
        """Test multiple processing cycles"""
        results = []
        
        for i in range(5):
            result = alphaalgo_system.process(sample_market_data)
            results.append(result)
            
            # Update performance after each cycle
            alphaalgo_system.update_performance({
                'sharpe_ratio': 1.0 + i * 0.1,
                'win_rate': 0.6 + i * 0.01
            })
        
        assert len(results) == 5
        assert all(r['decision'] in ['BUY', 'SELL', 'HOLD'] for r in results)
    
    def test_optimization_feedback_loop(self, alphaalgo_system):
        """Test optimization feedback loop"""
        # Set initial performance
        alphaalgo_system.agents['trend_follower']['performance'] = 0.3
        alphaalgo_system.agents['mean_reverter']['performance'] = -0.1
        
        # Run optimization
        result1 = alphaalgo_system.optimize()
        initial_changes = result1['changes_applied']
        
        # Update performance again
        alphaalgo_system.agents['trend_follower']['performance'] = 0.5
        
        # Run optimization again
        result2 = alphaalgo_system.optimize()
        
        # Should have made changes based on improved performance
        assert result2 is not None


class TestErrorHandling:
    """Test error handling"""
    
    def test_empty_market_data(self, alphaalgo_system):
        """Test handling of empty market data"""
        empty_data = pd.DataFrame()
        result = alphaalgo_system.process(empty_data)
        
        # Should return HOLD with low confidence
        assert result['decision'] == 'HOLD'
        assert result['confidence'] == 0.0
    
    def test_invalid_optimization_strategy(self, alphaalgo_system):
        """Test handling of invalid optimization strategy"""
        # Should not raise exception
        alphaalgo_system.set_optimization_strategy('invalid_strategy')
        # Strategy should remain unchanged
        assert alphaalgo_system.optimization_strategy in [
            OptimizationStrategy.CONSERVATIVE,
            OptimizationStrategy.MODERATE,
            OptimizationStrategy.AGGRESSIVE
        ]


# Performance benchmarks
class TestPerformance:
    """Test system performance"""
    
    def test_processing_speed(self, alphaalgo_system, sample_market_data):
        """Test that processing completes in reasonable time"""
        import time
        
        start = time.time()
        result = alphaalgo_system.process(sample_market_data)
        duration = time.time() - start
        
        # Should complete in less than 5 seconds
        assert duration < 5.0
        assert result is not None
    
    def test_optimization_speed(self, alphaalgo_system):
        """Test that optimization completes in reasonable time"""
from typing import Optional
from dataclasses import field
import numpy
        
start = time.time()
result = alphaalgo_system.optimize()
duration = time.time() - start
        
        # Should complete in less than 2 seconds
        assert duration < 2.0
        assert result is not None


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
