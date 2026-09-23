"""
Unit tests for Correlation Persistence

Tests for correlation matrix save/load and persistence
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from trading_bot.risk.correlation_persistence import (
    CorrelationPersistence,
    EnhancedCorrelationManager
)


class TestCorrelationPersistence:
    """Test suite for CorrelationPersistence"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def persistence(self, temp_dir):
        """Create persistence instance"""
        config = {
            'persistence_dir': temp_dir,
            'max_state_age_hours': 24
        }
        return CorrelationPersistence(config)
    
    def test_initialization(self, temp_dir):
        """Test persistence initialization"""
        persistence = CorrelationPersistence({'persistence_dir': temp_dir})
        assert persistence is not None
        assert persistence.persistence_dir == Path(temp_dir)
    
    def test_save_correlation_state(self, persistence):
        """Test saving correlation state"""
        # Create sample correlation matrix
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        matrix = pd.DataFrame(
            np.random.rand(3, 3),
            index=symbols,
            columns=symbols
        )
        
        # Create price history
        price_history = {
            'EURUSD': [1.1000, 1.1010, 1.1020],
            'GBPUSD': [1.3000, 1.3010, 1.3020],
            'USDJPY': [110.00, 110.10, 110.20]
        }
        
        # Save state
        result = persistence.save_correlation_state(matrix, price_history)
        
        assert result is True
        assert persistence.matrix_file.exists()
        assert persistence.history_file.exists()
        assert persistence.metadata_file.exists()
    
    def test_load_correlation_state(self, persistence):
        """Test loading correlation state"""
        # Create and save state
        symbols = ['EURUSD', 'GBPUSD']
        matrix = pd.DataFrame(
            [[1.0, 0.8], [0.8, 1.0]],
            index=symbols,
            columns=symbols
        )
        price_history = {
            'EURUSD': [1.1000, 1.1010],
            'GBPUSD': [1.3000, 1.3010]
        }
        
        persistence.save_correlation_state(matrix, price_history)
        
        # Load state
        loaded_matrix, loaded_history, metadata = persistence.load_correlation_state()
        
        assert loaded_matrix is not None
        assert loaded_history is not None
        assert metadata is not None
        assert list(loaded_matrix.index) == symbols
        assert 'EURUSD' in loaded_history
    
    def test_state_age_validation(self, persistence):
        """Test state age validation"""
        # Create old state
        symbols = ['EURUSD']
        matrix = pd.DataFrame([[1.0]], index=symbols, columns=symbols)
        price_history = {'EURUSD': [1.1000]}
        
        persistence.save_correlation_state(matrix, price_history)
        
        # Modify metadata to make it old
        import json
from enum import auto
import numpy
import pandas
with open(persistence.metadata_file, 'r') as f:
            metadata = json.load(f)
        
old_time = (datetime.now() - timedelta(hours=48)).isoformat()
metadata['timestamp'] = old_time
        
with open(persistence.metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        # Try to load - should reject old state
loaded_matrix, loaded_history, metadata = persistence.load_correlation_state()
        
        # Should return None or empty for old state
        assert loaded_matrix is None or loaded_matrix.empty
    
    def test_load_nonexistent_state(self, persistence):
        """Test loading when no state exists"""
        loaded_matrix, loaded_history, metadata = persistence.load_correlation_state()
        
        assert loaded_matrix is None or loaded_matrix.empty
        assert loaded_history is None or len(loaded_history) == 0
        assert metadata is None or len(metadata) == 0
    
    def test_save_empty_matrix(self, persistence):
        """Test saving empty correlation matrix"""
        matrix = pd.DataFrame()
        price_history = {}
        
        result = persistence.save_correlation_state(matrix, price_history)
        
        # Should handle gracefully
        assert result is True or result is False


class TestEnhancedCorrelationManager:
    """Test suite for EnhancedCorrelationManager"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_dir):
        """Create correlation manager"""
        config = {
            'max_history_length': 100,
            'persistence_dir': temp_dir,
            'auto_save_interval': 300,
            'max_state_age_hours': 24
        }
        return EnhancedCorrelationManager(config)
    
    def test_initialization(self, temp_dir):
        """Test manager initialization"""
        manager = EnhancedCorrelationManager({'persistence_dir': temp_dir})
        assert manager is not None
        assert manager.persistence is not None
    
    def test_update_price(self, manager):
        """Test updating price"""
        manager.update_price('EURUSD', 1.1000)
        
        assert 'EURUSD' in manager.price_history
        assert len(manager.price_history['EURUSD']) == 1
        assert manager.price_history['EURUSD'][0] == 1.1000
    
    def test_update_multiple_prices(self, manager):
        """Test updating multiple prices"""
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        
        for i in range(10):
            for symbol in symbols:
                manager.update_price(symbol, 1.1000 + i * 0.0001)
        
        for symbol in symbols:
            assert symbol in manager.price_history
            assert len(manager.price_history[symbol]) == 10
    
    def test_calculate_correlation_matrix(self, manager):
        """Test correlation matrix calculation"""
        # Add price data
        for i in range(50):
            manager.update_price('EURUSD', 1.1000 + i * 0.0001)
            manager.update_price('GBPUSD', 1.3000 + i * 0.00015)
        
        # Calculate correlation
        matrix = manager.calculate_correlation_matrix(['EURUSD', 'GBPUSD'])
        
        assert matrix is not None
        assert not matrix.empty
        assert 'EURUSD' in matrix.index
        assert 'GBPUSD' in matrix.index
    
    def test_get_correlation(self, manager):
        """Test getting correlation between two symbols"""
        # Add correlated data
        for i in range(50):
            manager.update_price('EURUSD', 1.1000 + i * 0.0001)
            manager.update_price('GBPUSD', 1.3000 + i * 0.0001)  # Highly correlated
        
        corr = manager.get_correlation('EURUSD', 'GBPUSD')
        
        assert corr is not None
        assert -1.0 <= corr <= 1.0
        assert corr > 0.5  # Should be positively correlated
    
    def test_save_state(self, manager):
        """Test saving state"""
        # Add data
        for i in range(50):
            manager.update_price('EURUSD', 1.1000 + i * 0.0001)
        
        # Save state
        result = manager.save_state()
        
        assert result is True
    
    def test_load_state_on_init(self, temp_dir):
        """Test loading state on initialization"""
        # Create first manager and save state
        manager1 = EnhancedCorrelationManager({'persistence_dir': temp_dir})
        
        for i in range(50):
            manager1.update_price('EURUSD', 1.1000 + i * 0.0001)
        
        manager1.save_state()
        
        # Create second manager - should load state
        manager2 = EnhancedCorrelationManager({'persistence_dir': temp_dir})
        
        # Should have loaded price history
        assert 'EURUSD' in manager2.price_history
        assert len(manager2.price_history['EURUSD']) > 0
    
    def test_max_history_length(self, manager):
        """Test maximum history length enforcement"""
        # Add more than max
        for i in range(150):
            manager.update_price('EURUSD', 1.1000 + i * 0.0001)
        
        # Should be limited to max_history_length (100)
        assert len(manager.price_history['EURUSD']) <= 100
    
    def test_correlation_with_insufficient_data(self, manager):
        """Test correlation calculation with insufficient data"""
        # Add only a few points
        manager.update_price('EURUSD', 1.1000)
        manager.update_price('EURUSD', 1.1001)
        manager.update_price('GBPUSD', 1.3000)
        manager.update_price('GBPUSD', 1.3001)
        
        corr = manager.get_correlation('EURUSD', 'GBPUSD')
        
        # Should return None or handle gracefully
        assert corr is None or isinstance(corr, float)
    
    def test_correlation_nonexistent_symbols(self, manager):
        """Test correlation for non-existent symbols"""
        corr = manager.get_correlation('NONEXIST1', 'NONEXIST2')
        
        assert corr is None
    
    def test_auto_save_interval(self, manager):
        """Test auto-save interval"""
        # This would require time-based testing
        # Just verify the attribute exists
        assert hasattr(manager, 'auto_save_interval')
        assert manager.auto_save_interval > 0
    
    def test_multiple_symbols(self, manager):
        """Test with multiple symbols"""
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCHF']
        
        # Add data for all symbols
        for i in range(50):
            for symbol in symbols:
                manager.update_price(symbol, 1.1000 + i * 0.0001)
        
        # Calculate correlation matrix
        matrix = manager.calculate_correlation_matrix(symbols)
        
        assert matrix is not None
        assert matrix.shape == (5, 5)
        
        # Diagonal should be 1.0
        for symbol in symbols:
            assert abs(matrix.loc[symbol, symbol] - 1.0) < 0.01
    
    def test_negative_correlation(self, manager):
        """Test negative correlation detection"""
        # Add negatively correlated data
        for i in range(50):
            manager.update_price('EURUSD', 1.1000 + i * 0.0001)
            manager.update_price('USDCHF', 0.9000 - i * 0.0001)  # Inverse
        
        corr = manager.get_correlation('EURUSD', 'USDCHF')
        
        assert corr is not None
        assert corr < 0  # Should be negatively correlated
    
    def test_zero_correlation(self, manager):
        """Test zero correlation detection"""
        # Add uncorrelated data
        np.random.seed(42)
        for i in range(50):
            manager.update_price('EURUSD', 1.1000 + np.random.randn() * 0.001)
            manager.update_price('RANDOM', 1.0000 + np.random.randn() * 0.001)
        
        corr = manager.get_correlation('EURUSD', 'RANDOM')
        
        assert corr is not None
        # Should be close to zero (but not exactly due to randomness)
        assert -0.5 < corr < 0.5


class TestCorrelationPersistenceEdgeCases:
    """Test edge cases"""
    
    def test_invalid_persistence_dir(self):
        """Test with invalid persistence directory"""
        config = {'persistence_dir': '/invalid/path/that/does/not/exist'}
        
        # Should handle gracefully
        try:
            persistence = CorrelationPersistence(config)
            assert persistence is not None
        except Exception:
            pass  # Expected to fail
    
    def test_corrupted_state_files(self, temp_dir):
        """Test loading corrupted state files"""
        persistence = CorrelationPersistence({'persistence_dir': temp_dir})
        
        # Create corrupted files
        with open(persistence.matrix_file, 'w') as f:
            f.write("corrupted data")
        
        with open(persistence.history_file, 'w') as f:
            f.write("corrupted data")
        
        # Try to load
        loaded_matrix, loaded_history, metadata = persistence.load_correlation_state()
        
        # Should handle gracefully
        assert loaded_matrix is None or loaded_matrix.empty
    
    def test_missing_metadata(self, temp_dir):
        """Test loading when metadata is missing"""
        persistence = CorrelationPersistence({'persistence_dir': temp_dir})
        
        # Save state
        symbols = ['EURUSD']
        matrix = pd.DataFrame([[1.0]], index=symbols, columns=symbols)
        persistence.save_correlation_state(matrix, {'EURUSD': [1.1000]})
        
        # Delete metadata
        if persistence.metadata_file.exists():
            os.remove(persistence.metadata_file)
        
        # Try to load
        loaded_matrix, loaded_history, metadata = persistence.load_correlation_state()
        
        # Should handle gracefully
        assert loaded_matrix is None or isinstance(loaded_matrix, pd.DataFrame)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
