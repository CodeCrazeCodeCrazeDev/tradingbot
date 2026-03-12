"""Unit tests for ML model visualization tools."""

import unittest
import pandas as pd
import numpy as np
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from trading_bot.ml.visualization import ModelVisualizer
from typing import Set
import numpy
import pandas


class TestModelVisualizer(unittest.TestCase):
    """Test cases for ModelVisualizer class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
        self.visualizer = ModelVisualizer(output_dir=self.temp_dir)
        
        # Create sample data
        dates = pd.date_range(start='2022-01-01', periods=100)
        self.df = pd.DataFrame({
            'open': np.random.normal(100, 5, 100),
            'high': np.random.normal(105, 5, 100),
            'low': np.random.normal(95, 5, 100),
            'close': np.random.normal(102, 5, 100),
            'volume': np.random.normal(1000, 200, 100)
        }, index=dates)
        
        # Sample predictions
        self.predictions = {
            't+1': 103.5,
            't+2': 104.2,
            't+3': 103.8,
            't+4': 105.1,
            't+5': 106.3
        }
        
        # Sample feature importance scores
        self.feature_scores = {
            'rsi_14': 0.25,
            'macd': 0.20,
            'volume': 0.15,
            'close': 0.10,
            'adx_14': 0.08,
            'bb_width_20': 0.07,
            'atr_percent': 0.05,
            'momentum_10': 0.05,
            'ema_20': 0.03,
            'stoch_k_14': 0.02
        }
        
        # Sample performance metrics
        self.metrics = {
            'mse': 0.0025,
            'rmse': 0.05,
            'mae': 0.04,
            'mape': 0.8,
            'r2': 0.85
        }
        
        # Sample training history
        self.history = {
            'loss': [0.05, 0.04, 0.035, 0.032, 0.03],
            'val_loss': [0.055, 0.045, 0.04, 0.038, 0.037]
        }
        
        # Sample attention weights
        self.attention_weights = np.random.random((5, 5))
        self.feature_names = ['close', 'volume', 'rsi_14', 'macd', 'bb_width_20']
        
        # Sample confusion matrix
        self.confusion_matrix = np.array([
            [45, 5, 0],
            [3, 40, 7],
            [2, 8, 40]
        ])
        self.class_names = ['Buy', 'Hold', 'Sell']
        
        # Sample ROC data
        self.fpr = np.array([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
        self.tpr = np.array([0, 0.4, 0.5, 0.7, 0.8, 0.85, 0.9, 0.92, 0.95, 0.98, 1.0])
        self.auc = 0.85
        
        # Sample ensemble predictions
        self.ensemble_predictions = {
            'Model 1': list(np.random.normal(102, 1, 30)),
            'Model 2': list(np.random.normal(103, 1.5, 30)),
            'Ensemble': list(np.random.normal(102.5, 0.8, 30))
        }
        self.actual_values = list(np.random.normal(102.2, 1, 30))
        self.dates_list = pd.date_range(start='2022-01-01', periods=30)
        
        # Sample model weights
        self.model_weights = {
            'Model 1': 0.4,
            'Model 2': 0.35,
            'Model 3': 0.25
        }

    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary files
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    def test_plot_price_predictions(self, mock_figure, mock_savefig):
        """Test plotting price predictions."""
        # Call the method
        fig = self.visualizer.plot_price_predictions(
            self.df, self.predictions, lookback_periods=20,
            title="Test Price Predictions"
        )
        
        # Check that the figure was created
        self.assertIsNotNone(fig)
        
        # Test with save_path
        save_path = os.path.join(self.temp_dir, "test_price_pred.png")
        fig = self.visualizer.plot_price_predictions(
            self.df, self.predictions, save_path=save_path
        )
        self.assertIsNotNone(fig)

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    def test_plot_feature_importance(self, mock_figure, mock_savefig):
        """Test plotting feature importance."""
        # Call the method
        fig = self.visualizer.plot_feature_importance(
            self.feature_scores, top_n=5,
            title="Test Feature Importance"
        )
        
        # Check that the figure was created
        self.assertIsNotNone(fig)
        
        # Test with save_path
        save_path = os.path.join(self.temp_dir, "test_feature_imp.png")
        fig = self.visualizer.plot_feature_importance(
            self.feature_scores, save_path=save_path
        )
        self.assertIsNotNone(fig)

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    def test_plot_performance_metrics(self, mock_figure, mock_savefig):
        """Test plotting performance metrics."""
        # Call the method
        fig = self.visualizer.plot_performance_metrics(
            self.metrics, title="Test Performance Metrics"
        )
        
        # Check that the figure was created
        self.assertIsNotNone(fig)
        
        # Test with save_path
        save_path = os.path.join(self.temp_dir, "test_metrics.png")
        fig = self.visualizer.plot_performance_metrics(
            self.metrics, save_path=save_path
        )
        self.assertIsNotNone(fig)

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    def test_plot_training_history(self, mock_figure, mock_savefig):
        """Test plotting training history."""
        # Call the method
        fig = self.visualizer.plot_training_history(
            self.history, title="Test Training History"
        )
        
        # Check that the figure was created
        self.assertIsNotNone(fig)
        
        # Test with save_path
        save_path = os.path.join(self.temp_dir, "test_history.png")
        fig = self.visualizer.plot_training_history(
            self.history, save_path=save_path
        )
        self.assertIsNotNone(fig)

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    def test_plot_attention_heatmap(self, mock_figure, mock_savefig):
        """Test plotting attention heatmap."""
        # Call the method
        fig = self.visualizer.plot_attention_heatmap(
            self.attention_weights, self.feature_names,
            title="Test Attention Heatmap"
        )
        
        # Check that the figure was created
        self.assertIsNotNone(fig)
        
        # Test with save_path
        save_path = os.path.join(self.temp_dir, "test_attention.png")
        fig = self.visualizer.plot_attention_heatmap(
            self.attention_weights, self.feature_names, save_path=save_path
        )
        self.assertIsNotNone(fig)

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    def test_plot_confusion_matrix(self, mock_figure, mock_savefig):
        """Test plotting confusion matrix."""
        # Call the method
        fig = self.visualizer.plot_confusion_matrix(
            self.confusion_matrix, self.class_names,
            title="Test Confusion Matrix"
        )
        
        # Check that the figure was created
        self.assertIsNotNone(fig)
        
        # Test with save_path
        save_path = os.path.join(self.temp_dir, "test_confusion.png")
        fig = self.visualizer.plot_confusion_matrix(
            self.confusion_matrix, self.class_names, save_path=save_path
        )
        self.assertIsNotNone(fig)

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    def test_plot_roc_curve(self, mock_figure, mock_savefig):
        """Test plotting ROC curve."""
        # Call the method
        fig = self.visualizer.plot_roc_curve(
            self.fpr, self.tpr, self.auc,
            title="Test ROC Curve"
        )
        
        # Check that the figure was created
        self.assertIsNotNone(fig)
        
        # Test with save_path
        save_path = os.path.join(self.temp_dir, "test_roc.png")
        fig = self.visualizer.plot_roc_curve(
            self.fpr, self.tpr, self.auc, save_path=save_path
        )
        self.assertIsNotNone(fig)

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    def test_plot_ensemble_comparison(self, mock_figure, mock_savefig):
        """Test plotting ensemble comparison."""
        # Call the method
        fig = self.visualizer.plot_ensemble_comparison(
            self.ensemble_predictions, self.actual_values, self.dates_list,
            title="Test Ensemble Comparison"
        )
        
        # Check that the figure was created
        self.assertIsNotNone(fig)
        
        # Test with save_path
        save_path = os.path.join(self.temp_dir, "test_ensemble.png")
        fig = self.visualizer.plot_ensemble_comparison(
            self.ensemble_predictions, self.actual_values, self.dates_list,
            save_path=save_path
        )
        self.assertIsNotNone(fig)

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    def test_plot_model_weights(self, mock_figure, mock_savefig):
        """Test plotting model weights."""
        # Call the method
        fig = self.visualizer.plot_model_weights(
            self.model_weights, title="Test Model Weights"
        )
        
        # Check that the figure was created
        self.assertIsNotNone(fig)
        
        # Test with save_path
        save_path = os.path.join(self.temp_dir, "test_weights.png")
        fig = self.visualizer.plot_model_weights(
            self.model_weights, save_path=save_path
        )
        self.assertIsNotNone(fig)

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    def test_create_dashboard(self, mock_figure, mock_savefig):
        """Test creating dashboard."""
        # Create mock figures
        mock_figs = {
            'Price Predictions': MagicMock(),
            'Feature Importance': MagicMock(),
            'Performance Metrics': MagicMock()
        }
        
        # Mock canvas and renderer for each figure
        for fig in mock_figs.values():
            fig.canvas = MagicMock()
            fig.canvas.draw = MagicMock()
            fig.canvas.renderer = MagicMock()
            fig.canvas.renderer.buffer_rgba = MagicMock(return_value=np.zeros((100, 100, 4), dtype=np.uint8))
        
        # Call the method
        fig = self.visualizer.create_dashboard(
            mock_figs, layout=(2, 2),
            title="Test Dashboard"
        )
        
        # Check that the figure was created
        self.assertIsNotNone(fig)
        
        # Test with save_path
        save_path = os.path.join(self.temp_dir, "test_dashboard.png")
        fig = self.visualizer.create_dashboard(
            mock_figs, save_path=save_path
        )
        self.assertIsNotNone(fig)

    def test_error_handling(self):
        """Test error handling in visualization methods."""
        # Test with invalid data
        fig = self.visualizer.plot_price_predictions(
            pd.DataFrame(), {}  # Empty data
        )
        self.assertIsNotNone(fig)
        
        # Test with invalid feature scores
        fig = self.visualizer.plot_feature_importance({})
        self.assertIsNotNone(fig)


if __name__ == '__main__':
    unittest.main()
