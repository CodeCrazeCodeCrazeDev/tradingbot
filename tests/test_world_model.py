"""
Tests for World Models and Simulation (Phase 4)
"""

import unittest
import torch
import numpy as np
from trading_bot.world_model.latent_dynamics import (
    WorldModel,
    MarketStateEncoder,
    MarketStateDecoder,
    LatentDynamicsModel
)
from trading_bot.world_model.imagination import ImaginationPlanner
from trading_bot.world_model.synthetic_data import (
    SyntheticMarketGenerator,
    MarketScenario,
    MarketRegime
)
from trading_bot.world_model.unified_world_model import UnifiedWorldModel, TrainingCoordinator


class TestWorldModel(unittest.TestCase):
    """Test world model components."""
    
    def setUp(self):
        self.world_model = WorldModel(
            input_dim=20,
            latent_dim=20,
            hidden_dim=64,
            option_dim=5,
            graph_dim=20
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
        
        next_state, reward, hidden, info = self.world_model.predict_next(latent)
        
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


class TestUnifiedWorldModel(unittest.TestCase):
    """Test the newly redesigned UnifiedWorldModel and its training coordinator."""

    def setUp(self):
        # Initialize target UnifiedWorldModel
        self.model = UnifiedWorldModel(
            num_assets=5,
            num_timeframes=5,
            sequence_len=20,
            num_features=10,
            latent_dim=128,
            action_dim=3,
            hidden_dim=128
        )
        self.coordinator = TrainingCoordinator(self.model)

    def test_end_to_end_prediction(self):
        """Test standard predict() forward pass yielding a strongly-typed WorldModelPrediction."""
        x = torch.randn(2, 5, 5, 20, 10)  # batch=2, assets=5, timeframes=5, seq=20, features=10
        pred = self.model.predict(x)

        # 1. Verify structured traces and recommendation fields
        self.assertIsNotNone(pred.recommended_action)
        self.assertIn(pred.recommended_action, ["BUY", "SELL", "HOLD"])
        self.assertIsNotNone(pred.reasoning_trace)
        self.assertEqual(pred.reasoning_trace.chosen_policy, f"Formally recommended {pred.recommended_action} policy based on highest expected utility.")

        # 2. Verify Scenarios A, B, and C are simulated
        self.assertIn("Scenario_Normal", pred.predicted_states)
        self.assertIn("Scenario_Bull", pred.predicted_states)
        self.assertIn("Scenario_Bear", pred.predicted_states)

        normal_rollout = pred.predicted_states["Scenario_Normal"]
        self.assertEqual(len(normal_rollout.predicted_states), 5) # horizon=5
        self.assertIn("EURUSD", normal_rollout.predicted_prices)

        # 3. Verify uncertainty estimates
        self.assertTrue(0.0 <= pred.epistemic_uncertainty <= 1.0)
        self.assertTrue(0.0 <= pred.aleatoric_uncertainty <= 1.0)
        self.assertTrue(0.0 <= pred.calibration_score <= 1.0)

        # 4. Verify counterfactual reasoning questions are answered
        self.assertIn("no_trade", pred.counterfactuals)
        self.assertIn("double_volatility", pred.counterfactuals)
        self.assertIn("wide_spread", pred.counterfactuals)
        self.assertIn("illiquid", pred.counterfactuals)

        cf_vol = pred.counterfactuals["double_volatility"]
        self.assertEqual(cf_vol.question, "What if volatility doubles?")
        self.assertEqual(cf_vol.intervention, {"volatility_multiplier": 2.0})

    def test_causal_interventions(self):
        """Test Pearl's do-calculus node intervention and topological SCM propagation."""
        node_values = torch.zeros(2, 5)
        node_values[:, 0] = 3.5  # Fed_Rate 3.5%
        node_values[:, 1] = 1.0  # Volatility 1.0

        # Intervene and force Volatility (index 1) to be high (5.0)
        intervened = self.model.causal_engine.intervene(node_values, target_idx=1, value=5.0)

        # SCM propagation guarantees descendants like spreads and returns are updated
        self.assertEqual(float(intervened[0, 1].item()), 5.0)
        self.assertNotEqual(float(intervened[0, 4].item()), 0.0)  # Return index 4 is non-zero due to propagation

    def test_training_pipeline(self):
        """Test multi-objective joint optimization via TrainingCoordinator."""
        x_t = torch.randn(2, 5, 5, 20, 10)
        x_next = torch.randn(2, 5, 5, 20, 10)
        action = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        actual_reward = torch.tensor([0.05, -0.01])
        actual_causal_nodes = torch.randn(2, 5)
        target_policy_logits = torch.tensor([[0.8, 0.1, 0.1], [0.1, 0.8, 0.1]])

        losses = self.coordinator.train_step(
            x_t=x_t,
            x_next=x_next,
            action=action,
            actual_reward=actual_reward,
            actual_causal_nodes=actual_causal_nodes,
            target_policy_logits=target_policy_logits
        )

        # Ensure all optimization terms are calculated and updated
        self.assertIn("loss_total", losses)
        self.assertIn("loss_seq", losses)
        self.assertIn("loss_latent", losses)
        self.assertIn("loss_reward", losses)
        self.assertIn("loss_causal", losses)
        self.assertIn("loss_calibration", losses)
        self.assertIn("loss_policy", losses)

        self.assertTrue(losses["loss_total"] > 0.0)


if __name__ == '__main__':
    unittest.main()
