"""
Tests for World Models and Simulation (Phase 4)
"""

import unittest
import torch
import numpy as np
from world_model.latent_dynamics import (
    WorldModel,
    MarketStateEncoder,
    MarketStateDecoder,
    LatentDynamicsModel
)
from world_model.imagination import ImaginationPlanner
from world_model.synthetic_data import (
    SyntheticMarketGenerator,
    MarketScenario,
    MarketRegime
)


class TestWorldModel(unittest.TestCase):
    """Test world model components."""
    
    def setUp(self):
        self.world_model = WorldModel(
            input_dim=20,
            latent_dim=32,
            hidden_dim=64
        )
    
    def test_encode_decode(self):
        """Test encoding and decoding market states."""
        # Create dummy market state
        state = torch.randn(1, 20)
        
        # Encode
        latent = self.world_model.encode(state)
        
        # Decode
        reconstructed = self.world_model.decode(latent)
        
        self.assertEqual(state.shape, reconstructed.shape)
        # Just verify the reconstruction is finite and has correct shape
        # Reconstruction quality depends on training
        self.assertTrue(torch.isfinite(reconstructed).all())
    
    def test_prediction(self):
        """Test next state prediction."""
        state = torch.randn(1, 20)
        latent = self.world_model.encode(state)
        
        next_state, reward, hidden = self.world_model.predict_next(latent)
        
        self.assertEqual(next_state.shape, latent.shape)
        self.assertIsInstance(reward.item(), float)
    
    def test_imagination(self):
        """Test trajectory imagination."""
        state = torch.randn(1, 20)
        
        trajectory = self.world_model.imagine_trajectory(
            state,
            horizon=50
        )
        
        self.assertIn('latent_states', trajectory)
        self.assertIn('decoded_states', trajectory)
        self.assertIn('predicted_rewards', trajectory)
        
        self.assertEqual(len(trajectory['predicted_rewards']), 50)
    
    def test_training(self):
        """Test world model training."""
        # Create dummy training data
        states = torch.randn(10, 100, 20)  # [batch, time, features]
        rewards = torch.randn(10, 100)  # [batch, time]
        
        losses = self.world_model.train_step(states, rewards)
        
        self.assertIn('total_loss', losses)
        self.assertIn('recon_loss', losses)
        self.assertIn('kl_loss', losses)
        self.assertIn('dynamics_loss', losses)
        self.assertIn('reward_loss', losses)


class TestImaginationPlanner(unittest.TestCase):
    """Test imagination-based planning."""
    
    def setUp(self):
        self.world_model = WorldModel(
            input_dim=20,
            latent_dim=32,
            hidden_dim=64
        )
        self.planner = ImaginationPlanner(
            world_model=self.world_model,
            num_simulations=10,
            horizon=50
        )
    
    def test_plan_action(self):
        """Test action planning."""
        current_state = torch.randn(1, 20)
        possible_actions = ['BUY', 'SELL', 'HOLD']
        
        plan = self.planner.plan_action(
            current_state,
            possible_actions
        )
        
        self.assertIn('action', plan)
        self.assertIn('analysis', plan)
        self.assertIn('all_results', plan)
        self.assertEqual(plan['num_simulations'], 10)
        self.assertEqual(plan['horizon'], 50)
    
    def test_simulate_futures(self):
        """Test future simulation."""
        current_state = torch.randn(1, 20)
        
        futures = self.planner.simulate_futures(
            current_state,
            action='BUY'
        )
        
        self.assertEqual(len(futures), 10)  # num_simulations
        for future in futures:
            self.assertIn('trajectory', future)
            self.assertIn('cumulative_reward', future)
            self.assertIn('final_state', future)
            self.assertIn('rewards', future)
            self.assertIn('simulation_id', future)


class TestSyntheticData(unittest.TestCase):
    """Test synthetic data generation."""
    
    def setUp(self):
        self.generator = SyntheticMarketGenerator(
            base_volatility=0.01,
            dt=1.0/252.0
        )
    
    def test_scenario_generation(self):
        """Test market scenario generation."""
        scenario = MarketScenario(
            regime=MarketRegime.TRENDING_UP,
            duration=1000,
            volatility=1.0,
            trend_strength=0.2
        )
        
        data = self.generator.generate_scenario(
            scenario,
            initial_price=100.0
        )
        
        self.assertIn('prices', data)
        self.assertIn('returns', data)
        self.assertIn('indicators', data)
        self.assertIn('metadata', data)
        
        self.assertEqual(len(data['prices']), 1000)
        self.assertEqual(len(data['returns']), 999)  # n-1 returns
    
    def test_regime_transition(self):
        """Test regime transition generation."""
        data = self.generator.generate_regime_transition(
            initial_regime=MarketRegime.RANGING,
            final_regime=MarketRegime.TRENDING_UP,
            transition_duration=100,
            total_duration=500
        )
        
        self.assertIn('prices', data)
        self.assertIn('metadata', data)
        self.assertEqual(len(data['prices']), 500)
    
    def test_market_cycle(self):
        """Test complete market cycle generation."""
        data = self.generator.generate_market_cycle(
            cycle_duration=1000,
            num_regimes=4
        )
        
        self.assertIn('prices', data)
        self.assertIn('metadata', data)
        self.assertEqual(len(data['prices']), 1000)
        self.assertEqual(
            len(data['metadata']['regime_sequence']),
            4
        )
    
    def test_technical_indicators(self):
        """Test technical indicator calculation."""
        scenario = MarketScenario(
            regime=MarketRegime.TRENDING_UP,
            duration=1000,
            volatility=1.0
        )
        
        data = self.generator.generate_scenario(scenario)
        indicators = data['indicators']
        
        self.assertIn('sma_20', indicators)
        self.assertIn('sma_50', indicators)
        self.assertIn('rsi', indicators)
        self.assertIn('macd', indicators)
        self.assertIn('volatility', indicators)
        
        # Check indicator lengths
        self.assertEqual(len(indicators['sma_20']), 1000)
        self.assertEqual(len(indicators['rsi']), 1000)


if __name__ == '__main__':
    unittest.main()
