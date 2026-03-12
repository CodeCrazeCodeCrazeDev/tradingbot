"""
Tests for Multi-Agent System (Phase 2)
"""

import unittest
import torch
import numpy as np
from agents.base_agent import BaseAgent, AgentType, AgentProposal
from agents.specialized_agents import (
    TrendFollowingAgent,
    MeanReversionAgent,
    VolatilityAgent,
    RiskManagerAgent
)
from agents.coordinator import MultiAgentCoordinator
import numpy


class TestBaseAgent(unittest.TestCase):
    """Test base agent functionality."""
    
    def setUp(self):
        class TestAgent(BaseAgent):
            def analyze_market(self, market_data):
                return AgentProposal(
                    agent_id=self.agent_id,
                    agent_type=self.agent_type,
                    action='BUY',
                    confidence=0.8,
                    reasoning='Test reasoning',
                    expected_return=0.01,
                    risk_score=0.3
                )
            
            def get_strategy_name(self):
                return "Test Strategy"
        
        self.agent = TestAgent("test_agent", AgentType.TREND_FOLLOWER)
    
    def test_performance_tracking(self):
        """Test performance tracking."""
        # Update with wins and losses
        self.agent.update_performance({'outcome': 'win', 'pnl': 100})
        self.agent.update_performance({'outcome': 'loss', 'pnl': -50})
        
        metrics = self.agent.get_performance_metrics()
        
        self.assertEqual(metrics['total_trades'], 2)
        self.assertEqual(metrics['win_rate'], 0.5)
        self.assertGreater(metrics['avg_return'], 0)
    
    def test_confidence_calculation(self):
        """Test confidence calculation."""
        confidence = self.agent.calculate_confidence(
            signal_strength=0.8,
            market_conditions={'volatility': 1.0}
        )
        
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_risk_assessment(self):
        """Test risk assessment."""
        risk = self.agent.get_risk_assessment({
            'volatility': 2.0,
            'trend': 1.0
        })
        
        self.assertIn('risk_level', risk)
        self.assertIn('risk_score', risk)
        self.assertGreaterEqual(risk['risk_score'], 0.0)
        self.assertLessEqual(risk['risk_score'], 1.0)


class TestSpecializedAgents(unittest.TestCase):
    """Test specialized trading agents."""
    
    def setUp(self):
        self.trend_agent = TrendFollowingAgent()
        self.mean_rev_agent = MeanReversionAgent()
        self.vol_agent = VolatilityAgent()
        self.risk_agent = RiskManagerAgent()
    
    def test_trend_following(self):
        """Test trend following agent."""
        market_data = {
            'price': 100,
            'sma_20': 95,
            'sma_50': 90,
            'macd': 0.5,
            'volatility': 1.0
        }
        
        proposal = self.trend_agent.analyze_market(market_data)
        
        self.assertEqual(proposal.agent_type, AgentType.TREND_FOLLOWER)
        self.assertIn(proposal.action, ['BUY', 'SELL', 'HOLD'])
        self.assertGreaterEqual(proposal.confidence, 0.0)
        self.assertLessEqual(proposal.confidence, 1.0)
    
    def test_mean_reversion(self):
        """Test mean reversion agent."""
        market_data = {
            'price': 100,
            'rsi': 25,  # Oversold
            'sma_20': 110,
            'volatility': 1.0
        }
        
        proposal = self.mean_rev_agent.analyze_market(market_data)
        
        self.assertEqual(proposal.agent_type, AgentType.MEAN_REVERTER)
        self.assertEqual(proposal.action, 'BUY')  # Should buy when oversold
    
    def test_volatility_trading(self):
        """Test volatility trading agent."""
        market_data = {
            'volatility': 3.0,  # High volatility
            'rsi': 60,
            'macd': 0.5
        }
        
        proposal = self.vol_agent.analyze_market(market_data)
        
        self.assertEqual(proposal.agent_type, AgentType.VOLATILITY_TRADER)
        self.assertGreater(proposal.risk_score, 0.5)  # Should indicate high risk
    
    def test_risk_management(self):
        """Test risk manager agent."""
        market_data = {
            'volatility': 2.5,
            'open_positions': 3,
            'total_pnl': -1000
        }
        
        proposal = self.risk_agent.analyze_market(market_data)
        
        self.assertEqual(proposal.agent_type, AgentType.RISK_MANAGER)
        self.assertEqual(proposal.action, 'HOLD')  # Should suggest holding in high risk
        self.assertGreater(proposal.risk_score, 0.4)  # Risk score should be elevated


class TestMultiAgentCoordinator(unittest.TestCase):
    """Test multi-agent coordination."""
    
    def setUp(self):
        self.agents = {
            'trend': TrendFollowingAgent(),
            'mean_rev': MeanReversionAgent(),
            'vol': VolatilityAgent(),
            'risk': RiskManagerAgent()
        }
        self.coordinator = MultiAgentCoordinator(self.agents)
    
    def test_proposal_collection(self):
        """Test collecting proposals from all agents."""
        market_data = {
            'price': 100,
            'sma_20': 95,
            'sma_50': 90,
            'rsi': 40,
            'macd': 0.5,
            'volatility': 1.0,
            'open_positions': 1,
            'total_pnl': 500
        }
        
        proposals = self.coordinator.get_proposals(market_data)
        
        self.assertEqual(len(proposals), len(self.agents))
        for proposal in proposals:
            self.assertIsInstance(proposal, AgentProposal)
    
    def test_weighted_voting(self):
        """Test weighted voting decision mechanism."""
        market_data = {
            'price': 100,
            'sma_20': 95,
            'sma_50': 90,
            'rsi': 40,
            'macd': 0.5,
            'volatility': 1.0
        }
        
        proposals = self.coordinator.get_proposals(market_data)
        decision = self.coordinator.aggregate_decisions(
            proposals,
            method='weighted_vote'
        )
        
        self.assertIn('action', decision)
        self.assertIn('confidence', decision)
        self.assertIn('reasoning', decision)
    
    def test_consensus_decision(self):
        """Test consensus-based decision mechanism."""
        market_data = {
            'price': 100,
            'sma_20': 95,
            'sma_50': 90,
            'rsi': 40,
            'macd': 0.5,
            'volatility': 1.0
        }
        
        proposals = self.coordinator.get_proposals(market_data)
        decision = self.coordinator.aggregate_decisions(
            proposals,
            method='consensus'
        )
        
        self.assertIn('action', decision)
        self.assertIn('confidence', decision)
        self.assertIn('method', decision)
    
    def test_agent_rankings(self):
        """Test agent performance ranking."""
        # Update agent performance
        for agent in self.agents.values():
            agent.update_performance({'outcome': 'win', 'pnl': 100})
            agent.update_performance({'outcome': 'loss', 'pnl': -50})
        
        rankings = self.coordinator.get_agent_rankings()
        
        self.assertEqual(len(rankings), len(self.agents))
        for ranking in rankings:
            self.assertIn('agent_id', ranking)
            self.assertIn('win_rate', ranking)
            self.assertIn('total_trades', ranking)
    
    def test_adaptive_weighting(self):
        """Test adaptive agent weighting."""
        weights = self.coordinator.adaptive_weighting()
        
        self.assertEqual(len(weights), len(self.agents))
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        for weight in weights.values():
            self.assertGreaterEqual(weight, 0.0)
            self.assertLessEqual(weight, 1.0)


if __name__ == '__main__':
    unittest.main()
