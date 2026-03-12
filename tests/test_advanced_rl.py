"""
Tests for Advanced RL components (Phase 1)
"""

import unittest
import torch
import numpy as np
from learning.distributional_rl import DistributionalQLearning
from learning.multi_objective_rl import MultiObjectiveRL, TradeMetrics
import numpy

class TestDistributionalRL(unittest.TestCase):
    """Test Distributional RL implementation."""
    
    def setUp(self):
        self.drl = DistributionalQLearning(
            state_dim=10,
            action_dim=3,
            num_quantiles=51
        )
    
    def test_distribution_shape(self):
        """Test shape of predicted distributions."""
        state = torch.randn(1, 10)
        distribution = self.drl.predict_distribution(state)
        
        self.assertEqual(distribution.shape, (3, 51))  # [actions, quantiles]
    
    def test_cvar_calculation(self):
        """Test CVaR calculation."""
        distribution = np.random.normal(0, 1, 1000)
        cvar = self.drl.calculate_cvar(distribution, alpha=0.05)
        
        self.assertLess(cvar, np.mean(distribution))  # CVaR should be lower than mean
    
    def test_risk_metrics(self):
        """Test comprehensive risk metrics."""
        state = torch.randn(1, 10)
        metrics = self.drl.get_risk_metrics(state, action=0)
        
        required_metrics = [
            'expected_return', 'var_5%', 'cvar_5%',
            'var_1%', 'cvar_1%', 'std', 'skewness',
            'kurtosis', 'downside_risk'
        ]
        
        for metric in required_metrics:
            self.assertIn(metric, metrics)
            self.assertIsInstance(metrics[metric], (float, np.floating))
    
    def test_risk_aware_action(self):
        """Test risk-aware action selection."""
        state = torch.randn(1, 10)
        
        # Risk-neutral
        action1 = self.drl.select_action(state, risk_aversion=0.0)
        
        # Risk-averse
        action2 = self.drl.select_action(state, risk_aversion=1.0)
        
        self.assertIsInstance(action1, int)
        self.assertIsInstance(action2, int)
        self.assertIn(action1, [0, 1, 2])
        self.assertIn(action2, [0, 1, 2])
    
    def test_model_update(self):
        """Test model update with experience."""
        state = torch.randn(1, 10)
        next_state = torch.randn(1, 10)
        
        loss = self.drl.update(
            state=state,
            action=0,
            reward=1.0,
            next_state=next_state,
            done=False
        )
        
        self.assertIsInstance(loss, float)
        self.assertGreaterEqual(loss, 0.0)


class TestMultiObjectiveRL(unittest.TestCase):
    """Test Multi-Objective RL implementation."""
    
    def setUp(self):
        self.morl = MultiObjectiveRL()
    
    def test_reward_calculation(self):
        """Test multi-objective reward calculation."""
        metrics = TradeMetrics(
            pnl=100.0,
            sharpe_contribution=0.5,
            drawdown_impact=-0.02,
            volatility_score=0.3,
            execution_quality=0.9
        )
        
        reward = self.morl.compute_reward(metrics)
        self.assertIsInstance(reward, float)
        self.assertGreaterEqual(reward, -1.0)
        self.assertLessEqual(reward, 1.0)
    
    def test_regime_adaptation(self):
        """Test adaptation to market regimes."""
        # Initial weights
        initial_weights = self.morl.objectives.to_dict()
        
        # Adapt to high volatility
        self.morl.adapt_objectives('high_volatility')
        high_vol_weights = self.morl.objectives.to_dict()
        
        # Weights should change
        self.assertNotEqual(initial_weights, high_vol_weights)
        
        # Risk weight should increase
        self.assertGreater(
            high_vol_weights['drawdown'],
            initial_weights['drawdown']
        )
    
    def test_pareto_optimization(self):
        """Test Pareto front identification."""
        policies = [
            ('policy1', {'profit': 0.8, 'risk': 0.3}),
            ('policy2', {'profit': 0.6, 'risk': 0.2}),
            ('policy3', {'profit': 0.7, 'risk': 0.1})
        ]
        
        pareto_front = self.morl.pareto_optimization(policies)
        
        # Non-dominated solutions
        self.assertGreater(len(pareto_front), 0)
        self.assertLess(len(pareto_front), len(policies))
    
    def test_auto_tuning(self):
        """Test automatic objective tuning."""
        # Add some performance history
        for _ in range(20):
            metrics = TradeMetrics(
                pnl=np.random.normal(100, 20),
                sharpe_contribution=np.random.normal(0.5, 0.1),
                drawdown_impact=np.random.normal(-0.02, 0.01),
                volatility_score=np.random.normal(0.3, 0.1),
                execution_quality=np.random.normal(0.9, 0.05)
            )
            self.morl.compute_reward(metrics)
        
        # Initial weights
        initial_weights = self.morl.objectives.to_dict()
        
        # Auto-tune
        self.morl.auto_tune_objectives()
        tuned_weights = self.morl.objectives.to_dict()
        
        # Weights should be updated
        self.assertNotEqual(initial_weights, tuned_weights)
        
        # Weights should still sum to 1
        self.assertAlmostEqual(
            sum(tuned_weights.values()),
            1.0,
            places=6
        )


if __name__ == '__main__':
    unittest.main()
