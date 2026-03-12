"""
Data Normalizer
Ensures consistent data format across the pipeline
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime
from dataclasses import field

logger = logging.getLogger(__name__)

class DataNormalizer:
    """
    Normalizes data formats across the pipeline to ensure consistency
    Features:
    - Ensures price field is always present
    - Standardizes timestamp formats
    - Validates required fields
    - Adds missing fields with sensible defaults
    """
    
    @staticmethod
    def normalize_market_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize market data to ensure consistent format
        
        Args:
            data: Raw market data dictionary
            
        Returns:
            Normalized market data dictionary
        """
        try:
            if not data:
                return {}
        
            normalized = data.copy()
        
            # Ensure timestamp is present
            if 'timestamp' not in normalized:
                normalized['timestamp'] = datetime.now()
        
            # Ensure price is present
            if 'price' not in normalized:
                # Try to derive from OHLC
                if 'close' in normalized:
                    normalized['price'] = normalized['close']
                elif 'open' in normalized:
                    normalized['price'] = normalized['open']
                elif all(k in normalized for k in ['bid', 'ask']):
                    # Calculate mid price
                    normalized['price'] = (normalized['bid'] + normalized['ask']) / 2
                else:
                    logger.warning("Could not derive price from market data")
                    normalized['price'] = 0.0
        
            # Ensure symbol is present
            if 'symbol' not in normalized:
                normalized['symbol'] = normalized.get('instrument', 'UNKNOWN')
        
            # Ensure volume is present
            if 'volume' not in normalized:
                normalized['volume'] = normalized.get('tick_volume', normalized.get('real_volume', 0))
        
            return normalized
        except Exception as e:
            logger.error(f"Error in normalize_market_data: {e}")
            raise
    
    @staticmethod
    def normalize_ohlc_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize OHLC data to ensure consistent format
        
        Args:
            data: Raw OHLC data dictionary
            
        Returns:
            Normalized OHLC data dictionary
        """
        try:
            if not data:
                return {}
        
            normalized = data.copy()
        
            # Ensure all OHLC fields are present
            for field in ['open', 'high', 'low', 'close']:
                if field not in normalized:
                    if 'price' in normalized:
                        normalized[field] = normalized['price']
                    else:
                        normalized[field] = 0.0
        
            # Ensure price is present (use close)
            if 'price' not in normalized:
                normalized['price'] = normalized['close']
        
            # Ensure timestamp is present
            if 'timestamp' not in normalized:
                normalized['timestamp'] = datetime.now()
        
            # Ensure volume is present
            if 'volume' not in normalized:
                normalized['volume'] = normalized.get('tick_volume', normalized.get('real_volume', 0))
        
            return normalized
        except Exception as e:
            logger.error(f"Error in normalize_ohlc_data: {e}")
            raise
    
    @staticmethod
    def normalize_tick_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize tick data to ensure consistent format
        
        Args:
            data: Raw tick data dictionary
            
        Returns:
            Normalized tick data dictionary
        """
        try:
            if not data:
                return {}
        
            normalized = data.copy()
        
            # Ensure bid/ask are present
            if 'bid' not in normalized and 'ask' not in normalized:
                if 'price' in normalized:
                    normalized['bid'] = normalized['price']
                    normalized['ask'] = normalized['price']
            elif 'bid' in normalized and 'ask' not in normalized:
                normalized['ask'] = normalized['bid']
            elif 'ask' in normalized and 'bid' not in normalized:
                normalized['bid'] = normalized['ask']
        
            # Ensure price is present (use mid price)
            if 'price' not in normalized:
                normalized['price'] = (normalized['bid'] + normalized['ask']) / 2
        
            # Ensure timestamp is present
            if 'timestamp' not in normalized:
                normalized['timestamp'] = datetime.now()
        
            # Ensure volume is present
            if 'volume' not in normalized:
                normalized['volume'] = normalized.get('tick_volume', 0)
        
            return normalized
        except Exception as e:
            logger.error(f"Error in normalize_tick_data: {e}")
            raise
