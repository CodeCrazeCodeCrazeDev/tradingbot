"""Unit tests for ML components."""
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
import os
import tempfile

from trading_bot.ml.predictive_models import TransformerModel
from trading_bot.ml.reinforcement import PPOAgent
from typing import Set
import numpy
import pandas

import logging
import torch
logger = logging.getLogger(__name__)



class TestTransformerModel(unittest.TestCase):
    """Test cases for the TransformerModel."""

    def setUp(self):
        """Set up test fixtures."""
        # Create sample data
        self.df = pd.DataFrame({
            'time': pd.date_range(start='2023-01-01', periods=100),
            'open': np.random.normal(100, 1, 100),
            'high': np.random.normal(101, 1, 100),
            'low': np.random.normal(99, 1, 100),
            'close': np.random.normal(100, 1, 100),
            'volume': np.random.randint(1000, 10000, 100)
        })
        
        # Add some technical indicators
        self.df['sma_5'] = self.df['close'].rolling(5).mean()
        self.df['rsi_14'] = np.random.normal(50, 10, 100)  # Simulated RSI
        self.df = self.df.dropna()
        
        # Initialize model with test configuration
        self.model_config = {
            'window_size': 10,
            'hidden_size': 32,
            'num_layers': 2,
            'num_heads': 2,
            'dropout': 0.1,
            'learning_rate': 0.001,
            'batch_size': 16,
            'epochs': 2  # Small number for testing
        }
        self.model = TransformerModel(config=self.model_config)

    @patch('torch.cuda.is_available')
    def test_initialization(self, mock_cuda_available):
        """Test proper initialization of TransformerModel."""
        # Force CPU for testing
        mock_cuda_available.return_value = False
        
        model = TransformerModel(config=self.model_config)
        self.assertEqual(model.config['window_size'], 10)
        self.assertEqual(model.config['hidden_size'], 32)
        self.assertFalse(model.is_trained)

    def test_prepare_data(self):
        """Test data preparation method."""
        X, y = self.model.prepare_data(self.df, target_col='close')
        
        # Check shapes
        self.assertEqual(X.shape[1], self.model_config['window_size'])
        self.assertEqual(y.shape[0], X.shape[0])
        
        # Check that X contains sequences and y contains targets
        self.assertEqual(X.shape[0], len(self.df) - self.model_config['window_size'])
        self.assertEqual(y.shape[0], len(self.df) - self.model_config['window_size'])

    @patch('torch.nn.TransformerEncoder')
    @patch('torch.optim.Adam')
    @patch('torch.optim.lr_scheduler.ReduceLROnPlateau')
    def test_train_model(self, mock_scheduler, mock_optimizer, mock_transformer):
        """Test model training with mocked PyTorch components."""
        # Skip actual training, just test the interface
        result = self.model.train(
            df=self.df, 
            target_col='close',
            validation_split=0.2,
            early_stopping_patience=2
        )
        
        # Check that training returns expected metrics
        self.assertIn('train_loss', result)
        self.assertIn('val_loss', result)
        self.assertIn('epochs', result)
        self.assertTrue(self.model.is_trained)

    def test_predict(self):
        """Test prediction method."""
        # Mock the model as trained
        self.model.is_trained = True
        
        # Create a simple mock for the internal model
        self.model.model = MagicMock()
        self.model.model.eval.return_value = None
        self.model.model.return_value = np.array([[0.5]])
        self.model.scaler = MagicMock()
        self.model.scaler.transform.return_value = np.array([[0]])
        self.model.scaler.inverse_transform.return_value = np.array([[100]])
        
        # Test prediction
        with patch('torch.no_grad'):
            with patch('torch.from_numpy', return_value=MagicMock()):
                predictions = self.model.predict(self.df)
                self.assertIsInstance(predictions, np.ndarray)

    def test_save_load_model(self):
        """Test model saving and loading."""
        # Mock the model as trained
        self.model.is_trained = True
        self.model.model = MagicMock()
        self.model.scaler = MagicMock()
        
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as tmp:
            pass
        try:
            model_path = tmp.name
        
            # Test saving
            with patch('torch.save'):
                success = self.model.save_model(model_path)
                self.assertTrue(success)
            
            # Test loading
            with patch('torch.load', return_value={
                'model_state': {},
                'config': self.model_config,
                'scaler': MagicMock()
            }):
                new_model = TransformerModel()
                success = new_model.load_model(model_path)
                self.assertTrue(success)
                self.assertEqual(new_model.config, self.model_config)
        finally:
            # Clean up
            if os.path.exists(model_path):
                os.remove(model_path)


class TestPPOAgent(unittest.TestCase):
    """Test cases for the PPOAgent."""

    def setUp(self):
        """Set up test fixtures."""
        # Create sample data
        self.df = pd.DataFrame({
            'time': pd.date_range(start='2023-01-01', periods=100),
            'open': np.random.normal(100, 1, 100),
            'high': np.random.normal(101, 1, 100),
            'low': np.random.normal(99, 1, 100),
            'close': np.random.normal(100, 1, 100),
            'volume': np.random.randint(1000, 10000, 100)
        })
        
        # Add some technical indicators that PPOAgent expects
        self.df['sma_5'] = self.df['close'].rolling(5).mean()
        self.df['sma_20'] = self.df['close'].rolling(20).mean()
        self.df['rsi_14'] = np.random.normal(50, 10, 100)
        self.df['macd'] = np.random.normal(0, 0.5, 100)
        self.df['macd_signal'] = np.random.normal(0, 0.5, 100)
        self.df['atr_14'] = np.random.normal(1, 0.2, 100)
        self.df = self.df.dropna()
        
        # Initialize agent with test configuration
        self.agent_config = {
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
        self.agent = PPOAgent(config=self.agent_config)

    def test_initialization(self):
        """Test proper initialization of PPOAgent."""
        self.assertEqual(self.agent.config['learning_rate'], 0.001)
        self.assertEqual(self.agent.config['gamma'], 0.99)
        self.assertFalse(self.agent.is_trained)
        self.assertEqual(len(self.agent.training_history), 0)

    def test_preprocess_state(self):
        """Test state preprocessing."""
        states = self.agent.preprocess_state(self.df)
        
        # Check that states have the expected shape
        self.assertIsInstance(states, np.ndarray)
        self.assertEqual(states.shape[0], len(self.df))
        
        # Check that states contain features
        self.assertGreater(states.shape[1], 5)  # Should have multiple features

    @patch('torch.nn.Module')
    @patch('torch.optim.Adam')
    def test_build_networks(self, mock_optimizer, mock_module):
        """Test network building with mocked PyTorch components."""
        with patch('torch.device'):
            self.agent.build_networks(state_dim=20, action_dim=3)
            
            # Check that networks were built
            self.assertIsNotNone(self.agent.policy_network)
            self.assertIsNotNone(self.agent.value_network)
            self.assertIsNotNone(self.agent.optimizer)

    @patch('torch.FloatTensor')
    @patch('torch.LongTensor')
    @patch('torch.distributions.Categorical')
    def test_train(self, mock_categorical, mock_long_tensor, mock_float_tensor):
        """Test training method with mocked PyTorch components."""
        # Mock the networks and optimizer
        self.agent.policy_network = MagicMock()
        self.agent.value_network = MagicMock()
        self.agent.optimizer = MagicMock()
        self.agent.device = 'cpu'
        
        # Test training
        with patch('numpy.random.choice'):
            with patch('numpy.random.randint'):
                result = self.agent.train(self.df, n_iterations=2)
                
                # Check that training returns expected metrics
                self.assertIn('success', result)
                self.assertTrue(result['success'])
                self.assertIn('final_mean_reward', result)
                self.assertIn('metrics', result)
                self.assertTrue(self.agent.is_trained)

    def test_get_action(self):
        """Test action selection."""
        # Mock the agent as trained
        self.agent.is_trained = True
        self.agent.policy_network = MagicMock()
        self.agent.device = 'cpu'
        
        # Mock the policy network output
        action_probs = np.array([0.2, 0.5, 0.3])  # hold, buy, sell probs
        self.agent.policy_network.eval.return_value = None
        
        with patch('torch.FloatTensor'):
            with patch('torch.no_grad'):
                with patch('numpy.random.random', return_value=0.9):  # Use greedy selection
                    with patch('numpy.argmax', return_value=1):  # Select buy action
                        with patch.object(self.agent.policy_network, '__call__', return_value=MagicMock(cpu=MagicMock(numpy=MagicMock(return_value=np.array([action_probs]))))):
                            action, probs = self.agent.get_action(np.random.random(20))
                            
                            # Check that action and probabilities are returned
                            self.assertEqual(action, 1)  # buy action
                            self.assertIn('buy', probs)
                            self.assertIn('sell', probs)
                            self.assertIn('hold', probs)

    def test_save_load_model(self):
        """Test model saving and loading."""
        # Mock the agent as trained
        self.agent.is_trained = True
        self.agent.policy_network = MagicMock()
        self.agent.policy_network.state_dict.return_value = {'fc1.weight': torch.randn(32, 20)}
        self.agent.value_network = MagicMock()
        self.agent.value_network.state_dict.return_value = {'fc1.weight': torch.randn(32, 20)}
        
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as tmp:
            pass
        try:
            model_path = tmp.name
        
            # Test saving
            with patch('torch.save'):
                success = self.agent.save_model(model_path)
                self.assertTrue(success)
            
            # Test loading
            mock_state_dict = {
                'fc1.weight': torch.randn(32, 20),
                'fc3.weight': torch.randn(3, 32)
            }
            
            with patch('torch.load', return_value={
                'policy_network': mock_state_dict,
                'value_network': mock_state_dict,
                'config': self.agent_config,
                'training_history': [],
                'metadata': {'version': '1.0', 'framework': 'pytorch'}
            }):
                with patch('os.path.exists', return_value=True):
                    new_agent = PPOAgent()
                    
                    # Mock build_networks to avoid actual network creation
                    new_agent.build_networks = MagicMock()
                    new_agent.policy_network = MagicMock()
                    new_agent.value_network = MagicMock()
                    
                    success = new_agent.load_model(model_path)
                    self.assertTrue(success)
                    self.assertEqual(new_agent.config, self.agent_config)
                    self.assertTrue(new_agent.is_trained)
        finally:
            # Clean up
            if os.path.exists(model_path):
                os.remove(model_path)


if __name__ == '__main__':
    unittest.main()
