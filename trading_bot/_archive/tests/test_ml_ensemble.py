"""Integration tests for ML ensemble components."""
import json
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
import os
import tempfile
try:
    import torch
except ImportError:
    torch = None

from trading_bot.ml.predictive_models import TransformerModel
from trading_bot.ml.reinforcement import PPOAgent
from trading_bot.ml.ensemble_models import ModelEnsemble, AdaptiveEnsemble, HierarchicalEnsemble
from typing import Set
import numpy
import pandas

import logging
logger = logging.getLogger(__name__)



class TestMLEnsemble(unittest.TestCase):
    """Test cases for ML ensemble components."""

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
        
        self.ensemble_config = {
            'ensemble_method': 'weighted_average',
            'initial_weights': [0.6, 0.4],
            'meta_model_epochs': 5,
            'meta_model_batch_size': 16
        }
        
        self.adaptive_config = {
            'ensemble_method': 'weighted_average',
            'initial_weights': [0.5, 0.5],
            'adaptation_window': 20,
            'adaptation_rate': 0.1
        }
        
        self.hierarchical_config = {
            'timeframes': ['short', 'medium', 'long'],
            'timeframe_weights': {'short': 0.3, 'medium': 0.4, 'long': 0.3},
            'short_config': {'ensemble_method': 'weighted_average', 'adaptive': True},
            'medium_config': {'ensemble_method': 'weighted_average', 'adaptive': True},
            'long_config': {'ensemble_method': 'weighted_average', 'adaptive': True}
        }
        
        # Create mock models
        self.transformer_model1 = MagicMock(spec=TransformerModel)
        self.transformer_model1.is_trained = True
        self.transformer_model1.predict.return_value = np.array([101.0])
        
        self.transformer_model2 = MagicMock(spec=TransformerModel)
        self.transformer_model2.is_trained = True
        self.transformer_model2.predict.return_value = np.array([102.0])
        
        self.ppo_agent1 = MagicMock(spec=PPOAgent)
        self.ppo_agent1.is_trained = True
        self.ppo_agent1.preprocess_state.return_value = np.array([[1.0, 2.0, 3.0]])
        self.ppo_agent1.get_action.return_value = (1, {'hold': 0.2, 'buy': 0.7, 'sell': 0.1})
        
        self.ppo_agent2 = MagicMock(spec=PPOAgent)
        self.ppo_agent2.is_trained = True
        self.ppo_agent2.preprocess_state.return_value = np.array([[1.0, 2.0, 3.0]])
        self.ppo_agent2.get_action.return_value = (0, {'hold': 0.6, 'buy': 0.3, 'sell': 0.1})

    def test_model_ensemble_initialization(self):
        """Test ModelEnsemble initialization."""
        ensemble = ModelEnsemble(self.ensemble_config)
        self.assertEqual(ensemble.ensemble_method, 'weighted_average')
        self.assertEqual(ensemble.model_weights, [0.6, 0.4])
        self.assertFalse(ensemble.is_trained)
        self.assertEqual(len(ensemble.models), 0)

    def test_model_ensemble_add_model(self):
        """Test adding models to ModelEnsemble."""
        ensemble = ModelEnsemble(self.ensemble_config)
        ensemble.add_model(self.transformer_model1, weight=0.7)
        ensemble.add_model(self.transformer_model2, weight=0.3)
        
        self.assertEqual(len(ensemble.models), 2)
        self.assertEqual(len(ensemble.model_weights), 2)
        self.assertAlmostEqual(sum(ensemble.model_weights), 1.0)

    def test_model_ensemble_predict_price(self):
        """Test price prediction with ModelEnsemble."""
        ensemble = ModelEnsemble(self.ensemble_config)
        ensemble.add_model(self.transformer_model1, weight=0.7)
        ensemble.add_model(self.transformer_model2, weight=0.3)
        
        prediction = ensemble.predict_price(self.df)
        
        # Expected: 0.7 * 101.0 + 0.3 * 102.0 = 101.3
        self.assertAlmostEqual(prediction[0], 101.3)
        
        # Test with simple average
        ensemble.ensemble_method = 'simple_average'
        prediction = ensemble.predict_price(self.df)
        
        # Expected: (101.0 + 102.0) / 2 = 101.5
        self.assertAlmostEqual(prediction[0], 101.5)

    def test_model_ensemble_get_trading_action(self):
        """Test trading action selection with ModelEnsemble."""
        ensemble = ModelEnsemble(self.ensemble_config)
        ensemble.add_model(self.ppo_agent1, weight=0.6)
        ensemble.add_model(self.ppo_agent2, weight=0.4)
        
        action, probs = ensemble.get_trading_action(self.df)
        
        # Expected probabilities: 
        # hold: 0.6*0.2 + 0.4*0.6 = 0.12 + 0.24 = 0.36
        # buy: 0.6*0.7 + 0.4*0.3 = 0.42 + 0.12 = 0.54
        # sell: 0.6*0.1 + 0.4*0.1 = 0.06 + 0.04 = 0.10
        # So action should be 1 (buy)
        self.assertEqual(action, 1)
        self.assertAlmostEqual(probs['hold'], 0.36)
        self.assertAlmostEqual(probs['buy'], 0.54)
        self.assertAlmostEqual(probs['sell'], 0.10)

    @patch('torch.nn.Linear')
    @patch('torch.optim.Adam')
    @patch('torch.FloatTensor')
    def test_model_ensemble_train_meta_model(self, mock_tensor, mock_adam, mock_linear):
        """Test training meta-model for stacking ensemble."""
        # Setup mocks
        mock_linear_instance = MagicMock()
        mock_linear.return_value = mock_linear_instance
        mock_linear_instance.weight = MagicMock()
        mock_linear_instance.weight.cpu.return_value.numpy.return_value.flatten.return_value.tolist.return_value = [0.7, 0.3]
        
        # Create ensemble with real TransformerModel mocks
        ensemble = ModelEnsemble(self.ensemble_config)
        
        # Add mocked transformer models
        transformer1 = MagicMock(spec=TransformerModel)
        transformer1.is_trained = True
        transformer1.predict.return_value = np.array([101.0])
        
        transformer2 = MagicMock(spec=TransformerModel)
        transformer2.is_trained = True
        transformer2.predict.return_value = np.array([102.0])
        
        ensemble.add_model(transformer1)
        ensemble.add_model(transformer2)
        
        # Train meta-model
        with patch('torch.nn.MSELoss'):
            history = ensemble.train_meta_model(self.df)
        
        # Check results
        self.assertTrue(ensemble.is_trained)
        self.assertIsNotNone(history)
        self.assertIn('train_loss', history)
        self.assertIn('val_loss', history)
        self.assertEqual(len(ensemble.model_weights), 2)
        self.assertAlmostEqual(sum(ensemble.model_weights), 1.0)

    def test_adaptive_ensemble(self):
        """Test AdaptiveEnsemble functionality."""
        ensemble = AdaptiveEnsemble(self.adaptive_config)
        ensemble.add_model(self.transformer_model1)
        ensemble.add_model(self.transformer_model2)
        
        # Test weight adaptation
        original_weights = ensemble.model_weights.copy()
        
        # Mock update_weights to avoid actual computation
        with patch.object(ensemble, 'update_weights'):
            prediction = ensemble.predict_price(self.df, adapt=True)
            self.assertEqual(prediction.shape, (1,))
            
            # Weights should remain unchanged since update_weights was mocked
            self.assertEqual(ensemble.model_weights, original_weights)

    def test_hierarchical_ensemble(self):
        """Test HierarchicalEnsemble functionality."""
        ensemble = HierarchicalEnsemble(self.hierarchical_config)
        
        # Add models to different timeframes
        ensemble.add_model(self.transformer_model1, 'short')
        ensemble.add_model(self.transformer_model2, 'medium')
        ensemble.add_model(self.ppo_agent1, 'short')
        ensemble.add_model(self.ppo_agent2, 'medium')
        
        # Test price prediction
        with patch.object(AdaptiveEnsemble, 'predict_price') as mock_predict:
            mock_predict.side_effect = [np.array([101.0]), np.array([102.0]), np.array([103.0])]
            prediction = ensemble.predict_price(self.df)
            
            # Expected: 0.3*101.0 + 0.4*102.0 + 0.3*103.0 = 30.3 + 40.8 + 30.9 = 102.0
            self.assertEqual(prediction.shape, (1,))
        
        # Test trading action
        with patch.object(AdaptiveEnsemble, 'get_trading_action') as mock_action:
            mock_action.side_effect = [
                (1, {'hold': 0.2, 'buy': 0.7, 'sell': 0.1}),  # short
                (0, {'hold': 0.6, 'buy': 0.3, 'sell': 0.1}),  # medium
                (2, {'hold': 0.3, 'buy': 0.2, 'sell': 0.5})   # long
            ]
            action, probs = ensemble.get_trading_action(self.df)
            
            # Expected probabilities:
            # hold: 0.3*0.2 + 0.4*0.6 + 0.3*0.3 = 0.06 + 0.24 + 0.09 = 0.39
            # buy: 0.3*0.7 + 0.4*0.3 + 0.3*0.2 = 0.21 + 0.12 + 0.06 = 0.39
            # sell: 0.3*0.1 + 0.4*0.1 + 0.3*0.5 = 0.03 + 0.04 + 0.15 = 0.22
            # So action should be either 0 (hold) or 1 (buy) since they tie at 0.39
            self.assertIn(action, [0, 1])
            self.assertAlmostEqual(probs['hold'] + probs['buy'] + probs['sell'], 1.0, places=5)

    def test_model_persistence(self):
        """Test model saving and loading for ensemble models."""
        # Create ensemble with mock models
        ensemble = ModelEnsemble(self.ensemble_config)
        ensemble.add_model(self.transformer_model1)
        ensemble.add_model(self.transformer_model2)
        ensemble.is_trained = True
        
        # Create temporary files for testing
        with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as tmp:
            pass
        try:
            model_path = tmp.name.replace('.pt', '')
        
            # Test saving
            with patch('json.dump'), \
                 patch.object(self.transformer_model1, 'save_model', return_value=True), \
                 patch.object(self.transformer_model2, 'save_model', return_value=True):
                success = ensemble.save_model(model_path)
                self.assertTrue(success)
            
            # Test loading
            new_ensemble = ModelEnsemble()
            
            with patch('json.load', return_value={
                'ensemble_method': 'weighted_average',
                'model_weights': [0.6, 0.4],
                'is_trained': True,
                'training_history': [],
                'config': self.ensemble_config,
                'metadata': {'version': '1.0', 'timestamp': '2023-01-01T00:00:00', 'num_models': 2}
            }), \
                 patch('os.path.exists', return_value=True), \
                 patch.object(TransformerModel, 'load_model', return_value=True):
                success = new_ensemble.load_model(model_path)
                self.assertTrue(success)
                self.assertEqual(new_ensemble.ensemble_method, 'weighted_average')
                self.assertEqual(new_ensemble.model_weights, [0.6, 0.4])
                self.assertTrue(new_ensemble.is_trained)
        
        finally:
            # Clean up
            for ext in ['.json', '.meta', '_model_0_transformer.pt', '_model_1_transformer.pt']:
                path = f"{model_path}{ext}"
                if os.path.exists(path):
                    os.remove(path)

    def test_hierarchical_ensemble_persistence(self):
        """Test model saving and loading for hierarchical ensemble."""
        # Create hierarchical ensemble
        ensemble = HierarchicalEnsemble(self.hierarchical_config)
        
        # Add mock models to timeframes
        for timeframe in ['short', 'medium', 'long']:
            ensemble.ensembles[timeframe] = MagicMock(spec=AdaptiveEnsemble)
            ensemble.ensembles[timeframe].save_model.return_value = True
        
        # Create temporary files for testing
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            pass
        try:
            model_path = tmp.name.replace('.json', '')
        
            # Test saving
            with patch('json.dump'):
                success = ensemble.save_model(model_path)
                self.assertTrue(success)
                
                # Verify each timeframe ensemble was saved
                for timeframe in ['short', 'medium', 'long']:
                    ensemble.ensembles[timeframe].save_model.assert_called_once_with(
                        f"{model_path}_{timeframe}"
                    )
            
            # Test loading
            new_ensemble = HierarchicalEnsemble()
            
            with patch('json.load', return_value={
                'timeframes': ['short', 'medium', 'long'],
                'timeframe_weights': {'short': 0.3, 'medium': 0.4, 'long': 0.3},
                'config': self.hierarchical_config,
                'metadata': {'version': '1.0', 'timestamp': '2023-01-01T00:00:00'}
            }), \
                 patch('os.path.exists', return_value=True), \
                 patch.object(AdaptiveEnsemble, 'load_model', return_value=True):
                success = new_ensemble.load_model(model_path)
                self.assertTrue(success)
                self.assertEqual(new_ensemble.timeframes, ['short', 'medium', 'long'])
                self.assertEqual(new_ensemble.timeframe_weights, 
                                {'short': 0.3, 'medium': 0.4, 'long': 0.3})
        
        finally:
            # Clean up
            if os.path.exists(f"{model_path}.json"):
                os.remove(f"{model_path}.json")


if __name__ == '__main__':
    unittest.main()
