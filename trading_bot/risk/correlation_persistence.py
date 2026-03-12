"""
Correlation Matrix Persistence

Saves and loads correlation matrices to/from disk to preserve state across restarts.
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Tuple
import numpy
import pandas

logger = logging.getLogger(__name__)


class CorrelationPersistence:
    """Handle persistence of correlation data"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # Support both 'storage_dir' and 'persistence_dir' keys
        dir_path = self.config.get('persistence_dir') or self.config.get('storage_dir', 'data/correlation')
        self.storage_dir = Path(dir_path)
        self.persistence_dir = self.storage_dir  # Alias for backward compatibility
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.max_state_age_hours = self.config.get('max_state_age_hours', 24)
        
        # File paths
        self.matrix_file = self.storage_dir / 'correlation_matrix.pkl'
        self.history_file = self.storage_dir / 'price_history.json'
        self.metadata_file = self.storage_dir / 'metadata.json'
        
    def save_correlation_state(
        self,
        correlation_matrix: Optional[pd.DataFrame],
        price_history: Dict[str, list],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save correlation state to disk
        
        Args:
            correlation_matrix: Correlation matrix DataFrame
            price_history: Dictionary of symbol -> price history
            metadata: Additional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Save correlation matrix (pickle for DataFrame)
            if correlation_matrix is not None:
                with open(self.matrix_file, 'wb') as f:
                    pickle.dump(correlation_matrix, f)
                logger.info(f"Saved correlation matrix to {self.matrix_file}")
            
            # Save price history (JSON)
            history_data = {
                symbol: list(prices) for symbol, prices in price_history.items()
            }
            with open(self.history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
            logger.info(f"Saved price history to {self.history_file}")
            
            # Save metadata
            meta = metadata or {}
            meta['last_save'] = datetime.now().isoformat()
            meta['symbols'] = list(price_history.keys())
            meta['matrix_shape'] = list(correlation_matrix.shape) if correlation_matrix is not None else None
            
            with open(self.metadata_file, 'w') as f:
                json.dump(meta, f, indent=2)
            logger.info(f"Saved metadata to {self.metadata_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving correlation state: {e}")
            return False
    
    def load_correlation_state(self, max_age_hours: Optional[float] = None):
        """
        Load correlation state from disk
        
        Args:
            max_age_hours: Maximum age in hours (None = use config default)
        
        Returns:
            Tuple of (matrix, history, metadata) or (None, None, None) if failed or too old
        """
        try:
            # Check if history file exists (matrix file is optional)
            if not self.history_file.exists():
                logger.warning("Correlation state files not found")
                return None, None, None
            
            # Load metadata first to check age
            metadata = {}
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
            
            # Use provided max_age_hours or fall back to config
            age_limit = max_age_hours if max_age_hours is not None else self.max_state_age_hours
            
            # Check age
            timestamp_str = metadata.get('timestamp') or metadata.get('last_save')
            if timestamp_str and age_limit:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    age_hours = (datetime.now() - timestamp).total_seconds() / 3600
                    if age_hours > age_limit:
                        logger.warning(f"Correlation state is {age_hours:.1f} hours old (max: {age_limit}), rejecting")
                        return None, None, None
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse timestamp: {e}")
            
            # Load correlation matrix (if exists)
            correlation_matrix = None
            if self.matrix_file.exists():
                with open(self.matrix_file, 'rb') as f:
                    correlation_matrix = pickle.load(f)
                logger.info(f"Loaded correlation matrix from {self.matrix_file}")
            
            # Load price history
            with open(self.history_file, 'r') as f:
                price_history = json.load(f)
            logger.info(f"Loaded price history from {self.history_file}")
            
            return correlation_matrix, price_history, metadata
            
        except Exception as e:
            logger.error(f"Error loading correlation state: {e}")
            return None, None, None
    
    def clear_correlation_state(self) -> bool:
        """Clear saved correlation state"""
        try:
            if self.matrix_file.exists():
                self.matrix_file.unlink()
            if self.history_file.exists():
                self.history_file.unlink()
            if self.metadata_file.exists():
                self.metadata_file.unlink()
            
            logger.info("Cleared correlation state")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing correlation state: {e}")
            return False
    
    def get_state_age(self) -> Optional[float]:
        """
        Get age of saved state in hours
        
        Returns:
            Age in hours, or None if no state exists
        """
        try:
            if not self.metadata_file.exists():
                return None
            
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            last_save = datetime.fromisoformat(metadata.get('last_save', ''))
            age_hours = (datetime.now() - last_save).total_seconds() / 3600
            
            return age_hours
            
        except Exception as e:
            logger.error(f"Error getting state age: {e}")
            return None


class EnhancedCorrelationManager:
    """Correlation manager with persistence"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # Pass config with storage_dir key for compatibility
        persistence_config = dict(self.config)
        if 'persistence_dir' in persistence_config and 'storage_dir' not in persistence_config:
            persistence_config['storage_dir'] = persistence_config['persistence_dir']
        self.persistence = CorrelationPersistence(persistence_config)
        
        # Correlation data
        self.correlation_matrix: Optional[pd.DataFrame] = None
        self.price_history: Dict[str, list] = {}
        self.last_update: Optional[datetime] = None
        
        # Configuration
        self.max_history_length = self.config.get('max_history_length', 100)
        self.auto_save_interval = self.config.get('auto_save_interval', 300)  # 5 minutes
        self.max_state_age_hours = self.config.get('max_state_age_hours', 24)
        
        # Try to load existing state
        self._load_state()
    
    def _load_state(self):
        """Load correlation state from disk"""
        matrix, history, metadata = self.persistence.load_correlation_state()
        
        # Load if we have history, even if matrix is None
        if history:
            # Check if state is too old
            age = self.persistence.get_state_age()
            if age and age > self.max_state_age_hours:
                logger.warning(f"Correlation state is {age:.1f} hours old, discarding")
                return
            
            self.correlation_matrix = matrix  # Can be None
            self.price_history = history
            # Support both timestamp keys
            timestamp_str = metadata.get('last_update') or metadata.get('timestamp') or metadata.get('last_save')
            if timestamp_str:
                self.last_update = datetime.fromisoformat(timestamp_str)
            else:
                self.last_update = datetime.now()
            
            age_str = f"{age:.1f} hours" if age else "unknown"
            logger.info(
                f"Loaded correlation state: {len(self.price_history)} symbols, "
                f"age: {age_str}"
            )
    
    def update_price(self, symbol: str, price: float):
        """Update price history for symbol"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append(price)
        
        # Trim history
        if len(self.price_history[symbol]) > self.max_history_length:
            self.price_history[symbol] = self.price_history[symbol][-self.max_history_length:]
    
    def calculate_correlation_matrix(self, symbols: list) -> Optional[pd.DataFrame]:
        """Calculate correlation matrix for symbols"""
        try:
            # Build price DataFrame
            data = {}
            for symbol in symbols:
                if symbol in self.price_history and len(self.price_history[symbol]) > 10:
                    data[symbol] = self.price_history[symbol]
            
            if len(data) < 2:
                logger.warning("Not enough data to calculate correlation")
                return None
            
            df = pd.DataFrame(data)
            self.correlation_matrix = df.corr()
            self.last_update = datetime.now()
            
            return self.correlation_matrix
            
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {e}")
            return None
    
    def save_state(self) -> bool:
        """Save current state to disk"""
        timestamp = self.last_update.isoformat() if self.last_update else datetime.now().isoformat()
        return self.persistence.save_correlation_state(
            self.correlation_matrix,
            self.price_history,
            {'last_update': timestamp, 'timestamp': timestamp}  # Support both keys
        )
    
    def get_correlation(self, symbol1: str, symbol2: str) -> Optional[float]:
        """Get correlation between two symbols"""
        # Auto-calculate matrix if not present
        if self.correlation_matrix is None:
            symbols = list(self.price_history.keys())
            if symbol1 in symbols and symbol2 in symbols:
                self.calculate_correlation_matrix(symbols)
        
        if self.correlation_matrix is None:
            return None
        try:
        
            return self.correlation_matrix.loc[symbol1, symbol2]
        except (KeyError, IndexError):
            return None
