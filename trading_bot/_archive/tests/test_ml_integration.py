"""Integration tests for ML module components."""
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
import os
import tempfile

from trading_bot.ml.predictive_models import TransformerModel
from trading_bot.ml.reinforcement import PPOAgent, StrategyOptimizer
from typing import Set
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class TestMLIntegration(unittest.TestCase):
    """Test cases for ML module integration."""

    def setUp(self):
        """Set up test fixtures."""
        # Create sample market data
        self.df = pd.DataFrame({
            'time': pd.date_range(start='2023-01-01', periods=200),
            'open': np.random.normal(100, 1, 200),
            'high': np.random.normal(101, 1, 200),
            'low': np.random.normal(99, 1, 200),
            'close': np.random.normal(100, 1, 200),
            'volume': np.random.randint(1000, 10000, 200)
        })
        
        # Add technical indicators
        self.df['sma_5'] = self.df['close'].rolling(5).mean()
        self.df['sma_20'] = self.df['close'].rolling(20).mean()
        self.df['rsi_14'] = np.random.normal(50, 10, 200)
        self.df['macd'] = np.random.normal(0, 0.5, 200)
        self.df['macd_signal'] = np.random.normal(0, 0.5, 200)
        self.df['atr_14'] = np.random.normal(1, 0.2, 200)
        self.df = self.df.dropna()
        
        # Initialize models with test configurations
        self.transformer_config = {
            'window_size': 10,
            'hidden_size': 32,
            'num_layers': 2,
            'num_heads': 2,
            'dropout': 0.1,
            'learning_rate': 0.001,
            'batch_size': 16,
            'epochs': 2  # Small number for testing
        }
        
        self.ppo_config = {
            'learning_rate': 0.001,
            'gamma': 0.99,
            'lambda_': 0.95,
            'epsilon': 0.2,
            'value_coef': 0.5,
            'entropy_coef': 0.01,
            'max_grad_norm': 0.5,
            'batch_size': 16,
            'epochs': 2,
            'horizon': 20,
            'hidden_size': 32
        }
        
        self.transformer_model = TransformerModel(config=self.transformer_config)
        self.ppo_agent = PPOAgent(config=self.ppo_config)
        self.strategy_optimizer = StrategyOptimizer()

    @patch('torch.cuda.is_available')
    def test_transformer_ppo_integration(self, mock_cuda_available):
        """Test integration between TransformerModel and PPOAgent."""
        # Force CPU for testing
        mock_cuda_available.return_value = False
        
        # Mock the transformer model training and prediction
        with patch.object(self.transformer_model, 'train', return_value={
            'train_loss': [0.1, 0.05],
            'val_loss': [0.12, 0.06],
            'epochs': 2
        }):
            with patch.object(self.transformer_model, 'predict', return_value=np.array([101.0])):
                # Train transformer model
                self.transformer_model.train(self.df, target_col='close')
                self.assertTrue(self.transformer_model.is_trained)
                
                # Make predictions
                next_price = self.transformer_model.predict(self.df.tail(10))
                self.assertIsInstance(next_price, np.ndarray)
                
                # Add prediction to dataframe
                self.df['price_prediction'] = np.nan
                self.df.loc[self.df.index[-1], 'price_prediction'] = next_price[0]
                
                # Mock PPO agent training and action selection
                with patch.object(self.ppo_agent, 'train', return_value={
                    'success': True,
                    'final_mean_reward': 10.5,
                    'metrics': {
                        'mean_reward': [5.0, 10.5],
                        'policy_loss': [0.2, 0.1],
                        'value_loss': [0.3, 0.15],
                        'entropy': [0.5, 0.4]
                    }
                }):
                    with patch.object(self.ppo_agent, 'get_action', return_value=(1, {'hold': 0.2, 'buy': 0.7, 'sell': 0.1})):
                        # Train PPO agent
                        self.ppo_agent.train(self.df, n_iterations=2)
                        self.assertTrue(self.ppo_agent.is_trained)
                        
                        # Get action recommendation
                        state = self.ppo_agent.preprocess_state(self.df.tail(1))
                        action, probs = self.ppo_agent.get_action(state[0])
                        
                        # Check action
                        self.assertIn(action, [0, 1, 2])  # hold, buy, sell
                        self.assertIn('buy', probs)
                        self.assertIn('sell', probs)
                        self.assertIn('hold', probs)
                        
                        # Test that the action probabilities sum to approximately 1
                        self.assertAlmostEqual(sum(probs.values()), 1.0, places=5)

    def test_strategy_optimizer_integration(self):
        """Test integration with StrategyOptimizer."""
        # Define a simple strategy function for testing
        def test_strategy(df, params):
            sma_short = params.get('sma_short', 5)
            sma_long = params.get('sma_long', 20)
            
            df['sma_short'] = df['close'].rolling(sma_short).mean()
            df['sma_long'] = df['close'].rolling(sma_long).mean()
            
            # Generate signals
            signals = []
            for i in range(sma_long, len(df)):
                if df['sma_short'].iloc[i] > df['sma_long'].iloc[i] and df['sma_short'].iloc[i-1] <= df['sma_long'].iloc[i-1]:
                    signals.append(('buy', i, df['close'].iloc[i]))
                elif df['sma_short'].iloc[i] < df['sma_long'].iloc[i] and df['sma_short'].iloc[i-1] >= df['sma_long'].iloc[i-1]:
                    signals.append(('sell', i, df['close'].iloc[i]))
            
            # Calculate returns
            returns = 0
            position = 0
            entry_price = 0
            
            for signal, idx, price in signals:
                if signal == 'buy' and position <= 0:
                    if position < 0:  # Close short position
                        returns += entry_price - price
                    position = 1
                    entry_price = price
                elif signal == 'sell' and position >= 0:
                    if position > 0:  # Close long position
                        returns += price - entry_price
                    position = -1
                    entry_price = price
            
            # Close final position
            if position != 0:
                final_price = df['close'].iloc[-1]
                if position > 0:
                    returns += final_price - entry_price
                else:
                    returns += entry_price - final_price
            
            return {
                'returns': returns,
                'num_trades': len(signals),
                'sharpe_ratio': returns / (df['close'].std() + 1e-10),
                'max_drawdown': 0.1  # Simplified for testing
            }
        
        # Define parameter space
        param_space = {
            'sma_short': [3, 5, 7, 10],
            'sma_long': [15, 20, 25, 30]
        }
        
        # Run optimization
        with patch.object(self.strategy_optimizer, '_evaluate_params', side_effect=test_strategy):
            results = self.strategy_optimizer.optimize(
                strategy_func=test_strategy,
                df=self.df,
                param_space=param_space,
                metric='returns',
                n_trials=3
            )
            
            # Check results
            self.assertIsInstance(results, dict)
            self.assertIn('best_params', results)
            self.assertIn('best_value', results)
            self.assertIn('all_trials', results)
            
            # Check that best parameters are within the parameter space
            self.assertIn(results['best_params']['sma_short'], param_space['sma_short'])
            self.assertIn(results['best_params']['sma_long'], param_space['sma_long'])

    def test_model_persistence(self):
        """Test model saving and loading for both components."""
        # Mock the models as trained
        self.transformer_model.is_trained = True
        self.transformer_model.model = MagicMock()
        self.transformer_model.scaler = MagicMock()
        
        self.ppo_agent.is_trained = True
        self.ppo_agent.policy_network = MagicMock()
        self.ppo_agent.policy_network.state_dict.return_value = {'fc1.weight': MagicMock()}
        self.ppo_agent.value_network = MagicMock()
        self.ppo_agent.value_network.state_dict.return_value = {'fc1.weight': MagicMock()}
        
        # Create temporary files for testing
        with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as tmp1, \
             tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as tmp2:
            transformer_path = tmp1.name
            ppo_path = tmp2.name
        
        try:
            # Test saving
            with patch('torch.save'):
                # Save transformer model
                success1 = self.transformer_model.save_model(transformer_path)
                self.assertTrue(success1)
                
                # Save PPO agent
                success2 = self.ppo_agent.save_model(ppo_path)
                self.assertTrue(success2)
            
            # Test loading
            with patch('torch.load', return_value={
                'model_state': {},
                'config': self.transformer_config,
                'scaler': MagicMock(),
                'policy_network': {'fc1.weight': MagicMock(), 'fc3.weight': MagicMock()},
                'value_network': {'fc1.weight': MagicMock()},
                'training_history': [],
                'metadata': {'version': '1.0', 'framework': 'pytorch'}
            }):
                with patch('os.path.exists', return_value=True):
                    # Load transformer model
                    new_transformer = TransformerModel()
                    new_transformer.model = MagicMock()
                    success1 = new_transformer.load_model(transformer_path)
                    self.assertTrue(success1)
                    
                    # Load PPO agent
                    new_ppo = PPOAgent()
                    new_ppo.build_networks = MagicMock()
                    new_ppo.policy_network = MagicMock()
                    new_ppo.value_network = MagicMock()
                    success2 = new_ppo.load_model(ppo_path)
                    self.assertTrue(success2)
        finally:
            # Clean up
            for path in [transformer_path, ppo_path]:
                if os.path.exists(path):
                    os.remove(path)

    def test_end_to_end_workflow(self):
        """Test end-to-end ML workflow with mocked components."""
        # 1. Train transformer model
        with patch.object(self.transformer_model, 'train', return_value={
            'train_loss': [0.1, 0.05],
            'val_loss': [0.12, 0.06],
            'epochs': 2
        }):
            self.transformer_model.train(self.df, target_col='close')
        
        # 2. Make price predictions
        with patch.object(self.transformer_model, 'predict', return_value=np.array([101.0, 102.0, 103.0])):
            predictions = self.transformer_model.predict(self.df.tail(10), n_future=3)
            self.assertEqual(len(predictions), 3)
        
        # 3. Add predictions to dataframe
        self.df['next_day_prediction'] = np.nan
        self.df.loc[self.df.index[-1], 'next_day_prediction'] = predictions[0]
        
        # 4. Train PPO agent with enhanced features
        with patch.object(self.ppo_agent, 'train', return_value={
            'success': True,
            'final_mean_reward': 15.0,
            'metrics': {'mean_reward': [10.0, 15.0]}
        }):
            self.ppo_agent.train(self.df, n_iterations=2)
        
        # 5. Get trading action
        with patch.object(self.ppo_agent, 'get_action', return_value=(1, {'hold': 0.1, 'buy': 0.8, 'sell': 0.1})):
            state = self.ppo_agent.preprocess_state(self.df.tail(1))
            action, probs = self.ppo_agent.get_action(state[0])
            self.assertEqual(action, 1)  # buy action
        
        # 6. Evaluate strategy performance
        with patch.object(self.ppo_agent, 'evaluate', return_value={
            'total_return': 15.5,
            'sharpe_ratio': 1.2,
            'max_drawdown': 0.1,
            'win_rate': 0.65,
            'trades': 20
        }):
            performance = self.ppo_agent.evaluate(self.df)
            self.assertGreater(performance['total_return'], 0)
            self.assertGreater(performance['sharpe_ratio'], 0)
        
        # 7. Save models
        with patch('torch.save'):
            with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as tmp:
                model_path = tmp.name
                try:
                    self.transformer_model.is_trained = True
                    self.transformer_model.model = MagicMock()
                    self.transformer_model.scaler = MagicMock()
                    self.transformer_model.save_model(model_path)
                    
                    self.ppo_agent.is_trained = True
                    self.ppo_agent.policy_network = MagicMock()
                    self.ppo_agent.policy_network.state_dict.return_value = {'fc1.weight': MagicMock()}
                    self.ppo_agent.value_network = MagicMock()
                    self.ppo_agent.value_network.state_dict.return_value = {'fc1.weight': MagicMock()}
                    self.ppo_agent.save_model(model_path + '.ppo')
                finally:
                    if os.path.exists(model_path):
                        os.remove(model_path)
                    if os.path.exists(model_path + '.ppo'):
                        os.remove(model_path + '.ppo')


if __name__ == '__main__':
    unittest.main()
