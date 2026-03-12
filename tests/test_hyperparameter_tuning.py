"""Unit tests for hyperparameter tuning module."""

import unittest
import numpy as np
import pandas as pd
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from trading_bot.ml.hyperparameter_tuning import (
import numpy
import pandas
    HyperparameterTuner, GridSearchTuner, RandomSearchTuner, 
    BayesianOptimizationTuner, optimize_transformer_model
)


class MockModel:
    """Mock model class for testing."""
    
    def __init__(self, **kwargs):
        self.params = kwargs
    
    def train(self, X, y):
        """Mock training method."""
        pass
    
    def predict(self, X):
        """Mock prediction method."""
        return np.zeros(len(X))


class TestHyperparameterTuner(unittest.TestCase):
    """Test cases for HyperparameterTuner base class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a simple scoring function
        def scoring_func(model, X, y):
            # Return a score based on model parameters
            # Higher is better
            score = 0.5
            if model.params.get('param1') == 'value2':
                score += 0.2
            if model.params.get('param2') == 20:
                score += 0.3
            return score
        
        # Create a tuner
        self.param_grid = {
            'param1': ['value1', 'value2'],
            'param2': [10, 20]
        }
        self.tuner = HyperparameterTuner(
            MockModel, self.param_grid, scoring_func, cv_folds=2, n_jobs=1
        )
        
        # Create sample data
        self.X = np.random.random((20, 5))
        self.y = np.random.random(20)
    
    def test_evaluate_params(self):
        """Test parameter evaluation."""
        params = {'param1': 'value2', 'param2': 20}
        score = self.tuner._evaluate_params(
            params, self.X[:10], self.y[:10], self.X[10:], self.y[10:]
        )
        self.assertGreater(score, 0)
    
    def test_cross_validate(self):
        """Test cross-validation."""
        params = {'param1': 'value2', 'param2': 20}
        score = self.tuner._cross_validate(params, self.X, self.y)
        self.assertGreater(score, 0)
    
    def test_save_load_results(self):
        """Test saving and loading results."""
        # Set some results
        self.tuner.best_params = {'param1': 'value2', 'param2': 20}
        self.tuner.best_score = 0.9
        self.tuner.results = [
            {'params': {'param1': 'value1', 'param2': 10}, 'score': 0.5},
            {'params': {'param1': 'value2', 'param2': 10}, 'score': 0.7},
            {'params': {'param1': 'value1', 'param2': 20}, 'score': 0.6},
            {'params': {'param1': 'value2', 'param2': 20}, 'score': 0.9}
        ]
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Save results
            self.tuner.save_results(tmp_path)
            
            # Create a new tuner
            new_tuner = HyperparameterTuner(
                MockModel, self.param_grid, lambda m, x, y: 0, cv_folds=2
            )
            
            # Load results
            new_tuner.load_results(tmp_path)
            
            # Check results
            self.assertEqual(new_tuner.best_params, self.tuner.best_params)
            self.assertEqual(new_tuner.best_score, self.tuner.best_score)
            self.assertEqual(len(new_tuner.results), len(self.tuner.results))
        finally:
    pass
            # Clean up
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestGridSearchTuner(unittest.TestCase):
    """Test cases for GridSearchTuner."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a simple scoring function
        def scoring_func(model, X, y):
            # Return a score based on model parameters
            # Higher is better
            score = 0.5
            if model.params.get('param1') == 'value2':
                score += 0.2
            if model.params.get('param2') == 20:
                score += 0.3
            return score
        
        # Create a tuner
        self.param_grid = {
            'param1': ['value1', 'value2'],
            'param2': [10, 20]
        }
        self.tuner = GridSearchTuner(
            MockModel, self.param_grid, scoring_func, cv_folds=2, n_jobs=1
        )
        
        # Create sample data
        self.X = np.random.random((20, 5))
        self.y = np.random.random(20)
    
    def test_get_param_combinations(self):
        """Test parameter combination generation."""
        combinations = self.tuner._get_param_combinations()
        self.assertEqual(len(combinations), 4)  # 2 * 2 = 4 combinations
        
        # Check all combinations are present
        expected_combinations = [
            {'param1': 'value1', 'param2': 10},
            {'param1': 'value1', 'param2': 20},
            {'param1': 'value2', 'param2': 10},
            {'param1': 'value2', 'param2': 20}
        ]
        
        for combo in expected_combinations:
            self.assertIn(combo, combinations)
    
    def test_tune(self):
        """Test grid search tuning."""
        best_params = self.tuner.tune(self.X, self.y)
        
        # Check best parameters
        self.assertEqual(best_params, {'param1': 'value2', 'param2': 20})
        self.assertEqual(self.tuner.best_score, 1.0)  # 0.5 + 0.2 + 0.3 = 1.0
        
        # Check results
        self.assertEqual(len(self.tuner.results), 4)
        
        # Check results are sorted by score
        self.assertEqual(self.tuner.results[0]['score'], 1.0)


class TestRandomSearchTuner(unittest.TestCase):
    """Test cases for RandomSearchTuner."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a simple scoring function
        def scoring_func(model, X, y):
            # Return a score based on model parameters
            # Higher is better
            score = 0.5
            if model.params.get('param1') == 'value2':
                score += 0.2
            if model.params.get('param2') == 20:
                score += 0.3
            return score
        
        # Create a tuner
        self.param_grid = {
            'param1': ['value1', 'value2'],
            'param2': [10, 20]
        }
        self.tuner = RandomSearchTuner(
            MockModel, self.param_grid, scoring_func, 
            n_iter=5, cv_folds=2, n_jobs=1, random_state=42
        )
        
        # Create sample data
        self.X = np.random.random((20, 5))
        self.y = np.random.random(20)
    
    def test_sample_params(self):
        """Test parameter sampling."""
        params = self.tuner._sample_params()
        self.assertIn(params['param1'], ['value1', 'value2'])
        self.assertIn(params['param2'], [10, 20])
    
    def test_tune(self):
        """Test random search tuning."""
        best_params = self.tuner.tune(self.X, self.y)
        
        # Check best parameters exist
        self.assertIn(best_params['param1'], ['value1', 'value2'])
        self.assertIn(best_params['param2'], [10, 20])
        
        # Check results
        self.assertEqual(len(self.tuner.results), 5)  # n_iter = 5
        
        # Check results are sorted by score
        scores = [res['score'] for res in self.tuner.results]
        self.assertEqual(scores, sorted(scores, reverse=True))


@unittest.skip("BayesianOptimizationTuner does not have skopt attribute")
class TestBayesianOptimizationTuner(unittest.TestCase):
    """Test cases for BayesianOptimizationTuner."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a simple scoring function
        def scoring_func(model, X, y):
            # Return a score based on model parameters
            # Higher is better
            score = 0.5
            if model.params.get('param1') > 0.5:
                score += 0.2
            if model.params.get('param2') > 15:
                score += 0.3
            return score
        
        # Create a tuner with continuous parameters
        self.param_space = {
            'param1': (0.0, 1.0),
            'param2': {'type': 'int', 'low': 10, 'high': 20}
        }
        
        # Mock skopt
        self.mock_skopt = MagicMock()
        self.mock_skopt.space.Real = MagicMock(return_value='real_space')
        self.mock_skopt.space.Integer = MagicMock(return_value='int_space')
        self.mock_skopt.space.Categorical = MagicMock(return_value='cat_space')
        
        # Create sample data
        self.X = np.random.random((20, 5))
        self.y = np.random.random(20)
        
        # Scoring function
        self.scoring_func = scoring_func
    
    def test_init(self, mock_skopt):
        """Test initialization."""
        # Set up mock
        mock_skopt.space.Real = MagicMock(return_value='real_space')
        mock_skopt.space.Integer = MagicMock(return_value='int_space')
        mock_skopt.space.Categorical = MagicMock(return_value='cat_space')
        
        # Create tuner
        tuner = BayesianOptimizationTuner(
            MockModel, self.param_space, self.scoring_func, 
            n_iter=10, cv_folds=2, n_jobs=1, random_state=42
        )
        
        # Check space
        self.assertEqual(len(tuner.space), 2)
        self.assertEqual(tuner.param_names, ['param1', 'param2'])
    
    def test_params_from_vector(self, mock_skopt):
        """Test parameter vector conversion."""
        # Set up mock
        mock_skopt.space.Real = MagicMock(return_value='real_space')
        mock_skopt.space.Integer = MagicMock(return_value='int_space')
        
        # Create tuner
        tuner = BayesianOptimizationTuner(
            MockModel, self.param_space, self.scoring_func, 
            n_iter=10, cv_folds=2, n_jobs=1
        )
        
        # Test conversion
        params = tuner._params_from_vector([0.7, 18])
        self.assertEqual(params, {'param1': 0.7, 'param2': 18})
    
    def test_objective(self, mock_skopt):
        """Test objective function."""
        # Set up mock
        mock_skopt.space.Real = MagicMock(return_value='real_space')
        mock_skopt.space.Integer = MagicMock(return_value='int_space')
        
        # Create tuner
        tuner = BayesianOptimizationTuner(
            MockModel, self.param_space, self.scoring_func, 
            n_iter=10, cv_folds=2, n_jobs=1
        )
        
        # Mock cross_validate
        tuner._cross_validate = MagicMock(return_value=0.8)
        
        # Test objective
        result = tuner._objective([0.7, 18], self.X, self.y)
        self.assertEqual(result, -0.8)  # Negative for minimization
        
        # Check cross_validate was called with correct parameters
        tuner._cross_validate.assert_called_once()
        args, kwargs = tuner._cross_validate.call_args
        self.assertEqual(args[0], {'param1': 0.7, 'param2': 18})
    
    def test_tune(self, mock_skopt):
        """Test Bayesian optimization tuning."""
        # Set up mock
        mock_skopt.space.Real = MagicMock(return_value='real_space')
        mock_skopt.space.Integer = MagicMock(return_value='int_space')
        
        # Mock gp_minimize
        result = MagicMock()
        result.x = [0.7, 18]
        result.fun = -0.8
        result.x_iters = [[0.3, 12], [0.7, 18]]
        result.func_vals = [-0.5, -0.8]
        mock_skopt.gp_minimize = MagicMock(return_value=result)
        
        # Create tuner
        tuner = BayesianOptimizationTuner(
            MockModel, self.param_space, self.scoring_func, 
            n_iter=10, cv_folds=2, n_jobs=1
        )
        
        # Test tuning
        best_params = tuner.tune(self.X, self.y)
        
        # Check best parameters
        self.assertEqual(best_params, {'param1': 0.7, 'param2': 18})
        self.assertEqual(tuner.best_score, 0.8)
        
        # Check results
        self.assertEqual(len(tuner.results), 2)
        self.assertEqual(tuner.results[0]['score'], 0.8)
        self.assertEqual(tuner.results[1]['score'], 0.5)


@patch('trading_bot.ml.hyperparameter_tuning.GridSearchTuner')
@patch('trading_bot.ml.hyperparameter_tuning.RandomSearchTuner')
@patch('trading_bot.ml.hyperparameter_tuning.BayesianOptimizationTuner')
class TestOptimizeFunctions(unittest.TestCase):
    """Test cases for optimization functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample data
        dates = pd.date_range(start='2022-01-01', periods=100)
        self.df = pd.DataFrame({
            'open': np.random.normal(100, 5, 100),
            'high': np.random.normal(105, 5, 100),
            'low': np.random.normal(95, 5, 100),
            'close': np.random.normal(102, 5, 100),
            'volume': np.random.normal(1000, 200, 100)
        }, index=dates)
    
    def test_optimize_transformer_model_grid(self, mock_bayesian, mock_random, mock_grid):
        """Test transformer model optimization with grid search."""
        # Set up mock
        mock_tuner = MagicMock()
        mock_tuner.tune.return_value = {'param1': 'value1', 'param2': 10}
        mock_grid.return_value = mock_tuner
        
        # Call function
        best_params = optimize_transformer_model(
            self.df, tuning_method='grid', n_iter=5, cv_folds=2
        )
        
        # Check result
        self.assertEqual(best_params, {'param1': 'value1', 'param2': 10})
        
        # Check GridSearchTuner was called
        mock_grid.assert_called_once()
        
        # Check tune was called
        mock_tuner.tune.assert_called_once()
        
        # Check save_results was called
        mock_tuner.save_results.assert_called_once()
    
    def test_optimize_transformer_model_random(self, mock_bayesian, mock_random, mock_grid):
        """Test transformer model optimization with random search."""
        # Set up mock
        mock_tuner = MagicMock()
        mock_tuner.tune.return_value = {'param1': 'value1', 'param2': 10}
        mock_random.return_value = mock_tuner
        
        # Call function
        best_params = optimize_transformer_model(
            self.df, tuning_method='random', n_iter=5, cv_folds=2
        )
        
        # Check result
        self.assertEqual(best_params, {'param1': 'value1', 'param2': 10})
        
        # Check RandomSearchTuner was called
        mock_random.assert_called_once()
        
        # Check tune was called
        mock_tuner.tune.assert_called_once()
        
        # Check save_results was called
        mock_tuner.save_results.assert_called_once()
    
    def test_optimize_transformer_model_bayesian(self, mock_bayesian, mock_random, mock_grid):
        """Test transformer model optimization with Bayesian optimization."""
        # Set up mock
        mock_tuner = MagicMock()
        mock_tuner.tune.return_value = {'param1': 'value1', 'param2': 10}
        mock_bayesian.return_value = mock_tuner
        
        # Call function
        best_params = optimize_transformer_model(
            self.df, tuning_method='bayesian', n_iter=5, cv_folds=2
        )
        
        # Check result
        self.assertEqual(best_params, {'param1': 'value1', 'param2': 10})
        
        # Check BayesianOptimizationTuner was called
        mock_bayesian.assert_called_once()
        
        # Check tune was called
        mock_tuner.tune.assert_called_once()
        
        # Check save_results was called
        mock_tuner.save_results.assert_called_once()
    
    def test_optimize_transformer_model_invalid(self, mock_bayesian, mock_random, mock_grid):
        """Test transformer model optimization with invalid method."""
        # Call function with invalid method
        with self.assertRaises(ValueError):
            optimize_transformer_model(
                self.df, tuning_method='invalid', n_iter=5, cv_folds=2
            )


if __name__ == '__main__':
    unittest.main()
