"""Unit tests for online learning module."""

import unittest
import numpy as np
import pandas as pd
import os
import sys
import tempfile
import time
import threading
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from trading_bot.ml.online_learning import (
import numpy
import pandas
    OnlineLearner, IncrementalLearner, EnsembleOnlineLearner,
    ConceptDriftDetector, AsyncOnlineLearner
)


class MockModel:
    """Mock model class for testing."""
    
    def __init__(self, **kwargs):
        self.params = kwargs
        self.partial_fit_called = 0
        self.predict_called = 0
    
    def predict(self, X):
        """Mock prediction method."""
        self.predict_called += 1
        return np.zeros(len(X))
    
    def partial_fit(self, X, y):
        """Mock partial fit method."""
        self.partial_fit_called += 1
        return self


class TestOnlineLearner(unittest.TestCase):
    """Test cases for OnlineLearner base class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock model
        self.model = MockModel()
        
        # Create a subclass that implements abstract methods
        class ConcreteOnlineLearner(OnlineLearner):
            def _evaluate_performance(self, data):
                return 0.8
            
            def _update_model(self):
                self.model.partial_fit_called += 1
        
        # Create a learner
        self.learner = ConcreteOnlineLearner(
            self.model, window_size=10, update_frequency=5,
            performance_threshold=0.1, target_col='close'
        )
        
        # Create sample data
        self.sample = pd.Series({
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000.0
        })
    
    def test_add_sample(self):
        """Test adding samples to the buffer."""
        # Add a sample
        self.learner.add_sample(self.sample)
        
        # Check buffer
        self.assertEqual(len(self.learner.data_buffer), 1)
        self.assertEqual(self.learner.samples_since_update, 1)
        
        # Add more samples
        for _ in range(4):
            self.learner.add_sample(self.sample)
        
        # Check buffer and counter
        self.assertEqual(len(self.learner.data_buffer), 5)
        self.assertEqual(self.learner.samples_since_update, 0)  # Reset after update
        
        # Check that _check_performance was called
        self.assertIsNotNone(self.learner.current_performance)
    
    def test_detect_performance_degradation(self):
        """Test performance degradation detection."""
        # Set baseline and current performance
        self.learner.baseline_performance = 0.8
        self.learner.current_performance = 0.7
        
        # Check degradation
        self.assertTrue(self.learner._detect_performance_degradation())
        
        # Set current performance higher
        self.learner.current_performance = 0.75
        
        # Check degradation
        self.assertFalse(self.learner._detect_performance_degradation())
    
    @unittest.skip("Pickle cannot serialize local class ConcreteOnlineLearner")
    def test_save_load(self):
        """Test saving and loading."""
        # Add some samples
        for _ in range(5):
            self.learner.add_sample(self.sample)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Save learner
            self.learner.save(tmp_path)
            
            # Load learner
            loaded_learner = OnlineLearner.load(tmp_path)
            
            # Check attributes
            self.assertEqual(len(loaded_learner.data_buffer), len(self.learner.data_buffer))
            self.assertEqual(loaded_learner.window_size, self.learner.window_size)
            self.assertEqual(loaded_learner.update_frequency, self.learner.update_frequency)
        finally:
    pass
            # Clean up
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestIncrementalLearner(unittest.TestCase):
    """Test cases for IncrementalLearner."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock model
        self.model = MockModel()
        
        # Create a learner
        self.learner = IncrementalLearner(
            self.model, window_size=10, update_frequency=5,
            performance_threshold=0.1, target_col='close',
            batch_size=2
        )
        
        # Create sample data
        self.sample = pd.Series({
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000.0
        })
    
    def test_evaluate_performance(self):
        """Test performance evaluation."""
        # Create a DataFrame
        df = pd.DataFrame([self.sample.to_dict() for _ in range(5)])
        
        # Evaluate performance
        performance = self.learner._evaluate_performance(df)
        
        # Check performance
        self.assertLess(performance, 0)  # Negative error
        
        # Check that predict was called
        self.assertEqual(self.model.predict_called, 1)
    
    def test_update_model(self):
        """Test model update."""
        # Add samples
        for _ in range(5):
            self.learner.add_sample(self.sample)
        
        # Check that partial_fit was called
        self.assertEqual(self.model.partial_fit_called, 3)  # 5 samples / 2 batch_size = 3 batches
        
        # Check update history
        self.assertEqual(len(self.learner.update_history), 1)
    
    def test_error_metrics(self):
        """Test different error metrics."""
        # Create learners with different metrics
        metrics = ['mse', 'mae', 'rmse']
        
        for metric in metrics:
            learner = IncrementalLearner(
                MockModel(), window_size=10, update_frequency=5,
                performance_threshold=0.1, target_col='close',
                error_metric=metric
            )
            
            # Create a DataFrame
            df = pd.DataFrame([self.sample.to_dict() for _ in range(5)])
            
            # Evaluate performance
            performance = learner._evaluate_performance(df)
            
            # Check performance
            self.assertLess(performance, 0)  # Negative error


class TestEnsembleOnlineLearner(unittest.TestCase):
    """Test cases for EnsembleOnlineLearner."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock models
        self.models = [MockModel() for _ in range(3)]
        
        # Create a learner
        self.learner = EnsembleOnlineLearner(
            self.models, weights=[0.5, 0.3, 0.2],
            window_size=10, update_frequency=5,
            performance_threshold=0.1, target_col='close'
        )
        
        # Create sample data
        self.sample = pd.Series({
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000.0
        })
    
    def test_evaluate_performance(self):
        """Test performance evaluation."""
        # Create a DataFrame
        df = pd.DataFrame([self.sample.to_dict() for _ in range(5)])
        
        # Evaluate performance
        performance = self.learner._evaluate_performance(df)
        
        # Check performance
        self.assertLess(performance, 0)  # Negative error
        
        # Check that predict was called for each model
        for model in self.models:
            self.assertEqual(model.predict_called, 1)
        
        # Check model performances
        for perf in self.learner.model_performances:
            self.assertIsNotNone(perf)
    
    def test_update_model(self):
        """Test model update."""
        # Add samples
        for _ in range(5):
            self.learner.add_sample(self.sample)
        
        # Check that partial_fit was called for each model
        for model in self.models:
            self.assertEqual(model.partial_fit_called, 1)
        
        # Check update history
        self.assertEqual(len(self.learner.update_history), 1)
    
    def test_predict(self):
        """Test ensemble prediction."""
        # Create features
        X = np.random.random((5, 4))
        
        # Make prediction
        y_pred = self.learner.predict(X)
        
        # Check prediction shape
        self.assertEqual(y_pred.shape, (5,))
        
        # Check that predict was called for each model
        for model in self.models:
            self.assertEqual(model.predict_called, 1)


class TestConceptDriftDetector(unittest.TestCase):
    """Test cases for ConceptDriftDetector."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a detector
        self.detector = ConceptDriftDetector(
            window_size=5, alpha=0.05, drift_threshold=0.1
        )
    
    def test_initialize_reference(self):
        """Test reference window initialization."""
        # Initialize reference
        self.detector._initialize_reference(10.0)
        
        # Check reference window
        self.assertEqual(len(self.detector.reference_window), 1)
        self.assertEqual(self.detector.reference_mean, 10.0)
        self.assertEqual(self.detector.reference_std, 1.0)
    
    def test_add_sample_no_drift(self):
        """Test adding samples with no drift."""
        # Add initial sample
        drift = self.detector.add_sample(10.0)
        self.assertFalse(drift)
        
        # Add more samples with similar values
        for i in range(1, 5):
            drift = self.detector.add_sample(10.0 + i * 0.1)
            self.assertFalse(drift)
        
        # Check windows
        self.assertEqual(len(self.detector.reference_window), 1)
        self.assertEqual(len(self.detector.current_window), 4)
        
        # Add one more sample to fill current window
        drift = self.detector.add_sample(10.5)
        
        # Check drift detection
        self.assertFalse(drift)
        
        # Check that current window was cleared
        self.assertEqual(len(self.detector.current_window), 0)
    
    def test_add_sample_with_drift(self):
        """Test adding samples with drift."""
        # Add initial sample
        drift = self.detector.add_sample(10.0)
        self.assertFalse(drift)
        
        # Fill reference window
        for i in range(1, 5):
            drift = self.detector.add_sample(10.0 + i * 0.1)
            self.assertFalse(drift)
        
        # Add samples with significant drift
        drift_detected = False
        for i in range(5):
            drift = self.detector.add_sample(20.0 + i * 0.1)
            if drift:
                drift_detected = True
        
        # Drift should be detected at some point
        self.assertTrue(drift_detected)
        
        # Check drift history
        self.assertGreaterEqual(len(self.detector.drift_history), 1)
        self.assertTrue(self.detector.drift_history[0]['drift_detected'])


class TestAsyncOnlineLearner(unittest.TestCase):
    """Test cases for AsyncOnlineLearner."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock model
        self.model = MockModel()
        
        # Create a learner
        self.learner = AsyncOnlineLearner(
            self.model, window_size=10, update_frequency=5,
            target_col='close'
        )
        
        # Create sample data
        self.sample = pd.Series({
            'open': 100.0,
            'high': 105.0,
            'low': 95.0,
            'close': 102.0,
            'volume': 1000.0
        })
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop the update thread if running
        if self.learner.update_thread is not None and self.learner.update_thread.is_alive():
            self.learner.stop()
    
    def test_start_stop(self):
        """Test starting and stopping the update thread."""
        # Start the thread
        self.learner.start()
        
        # Check that thread is running
        self.assertIsNotNone(self.learner.update_thread)
        self.assertTrue(self.learner.update_thread.is_alive())
        
        # Stop the thread
        self.learner.stop()
        
        # Check that thread is stopped
        self.assertFalse(self.learner.update_thread.is_alive())
    
    def test_add_sample(self):
        """Test adding samples."""
        # Start the thread
        self.learner.start()
        
        # Add samples
        for _ in range(5):
            self.learner.add_sample(self.sample)
        
        # Check buffer
        self.assertEqual(len(self.learner.data_buffer), 5)
        self.assertEqual(self.learner.samples_since_update, 0)  # Reset after update
        
        # Wait for update to complete
        time.sleep(0.1)
        
        # Check that update was queued
        self.assertEqual(self.learner.update_queue.qsize(), 0)  # Queue should be empty after processing
    
    def test_update_model(self):
        """Test model update."""
        # Create a DataFrame
        df = pd.DataFrame([self.sample.to_dict() for _ in range(5)])
        
        # Update model
        self.learner._update_model(df)
        
        # Check that partial_fit was called
        self.assertEqual(self.model.partial_fit_called, 1)
        
        # Check update history
        self.assertEqual(len(self.learner.update_history), 1)
    
    def test_predict(self):
        """Test prediction."""
        # Create features
        X = np.random.random((5, 4))
        
        # Make prediction
        y_pred = self.learner.predict(X)
        
        # Check prediction shape
        self.assertEqual(y_pred.shape, (5,))
        
        # Check that predict was called
        self.assertEqual(self.model.predict_called, 1)
    
    def test_save_load(self):
        """Test saving and loading."""
        # Add some samples
        for _ in range(5):
            self.learner.add_sample(self.sample)
        
        # Start the thread
        self.learner.start()
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Save learner
            self.learner.save(tmp_path)
            
            # Load learner
            loaded_learner = AsyncOnlineLearner.load(tmp_path)
            
            # Check attributes
            self.assertEqual(len(loaded_learner.data_buffer), len(self.learner.data_buffer))
            self.assertEqual(loaded_learner.window_size, self.learner.window_size)
            self.assertEqual(loaded_learner.update_frequency, self.learner.update_frequency)
        finally:
    pass
            # Clean up
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == '__main__':
    unittest.main()
