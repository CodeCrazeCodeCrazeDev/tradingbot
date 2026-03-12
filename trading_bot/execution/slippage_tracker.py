import logging
"""
Slippage tracking and analysis for execution quality.
Monitors difference between expected and actual fill prices.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger
logger = logging.getLogger(__name__)


@dataclass
class SlippageRecord:
    """Record of slippage for a single trade."""
    timestamp: float
    symbol: str
    side: str  # 'buy' or 'sell'
    expected_price: float
    fill_price: float
    quantity: float
    slippage_bps: float  # Basis points
    slippage_cost: float  # Dollar cost


class SlippageTracker:
    """Track and analyze execution slippage."""
    
    def __init__(self, max_history: int = 10000):
        """
        Initialize slippage tracker.
        
        Args:
            max_history: Maximum number of records to keep
        """
        try:
            self.max_history = max_history
            self.records: List[SlippageRecord] = []
        
            logger.info(f"Slippage tracker initialized (max_history: {max_history})")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_fill(self, symbol: str, side: str, expected_price: float,
                   fill_price: float, quantity: float, timestamp: Optional[float] = None):
        """
        Record a trade fill and calculate slippage.
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            expected_price: Expected fill price
            fill_price: Actual fill price
            quantity: Trade quantity
            timestamp: Trade timestamp
        """
        try:
            import time

            if timestamp is None:
                timestamp = time.time()
        
            # Calculate slippage
            if side == 'buy':
                # For buys, positive slippage means paid more than expected
                slippage = fill_price - expected_price
            else:  # sell
                # For sells, positive slippage means received less than expected
                slippage = expected_price - fill_price
        
            # Convert to basis points
            slippage_bps = (slippage / expected_price) * 10000
        
            # Calculate dollar cost
            slippage_cost = slippage * quantity
        
            # Create record
            record = SlippageRecord(
                timestamp=timestamp,
                symbol=symbol,
                side=side,
                expected_price=expected_price,
                fill_price=fill_price,
                quantity=quantity,
                slippage_bps=slippage_bps,
                slippage_cost=slippage_cost
            )
        
            self.records.append(record)
        
            # Trim history
            if len(self.records) > self.max_history:
                self.records = self.records[-self.max_history:]
        
            # Log significant slippage
            if abs(slippage_bps) > 5.0:  # More than 5 bps
                logger.warning(f"High slippage: {symbol} {side} {slippage_bps:.2f} bps (${slippage_cost:.2f})")
        except Exception as e:
            logger.error(f"Error in record_fill: {e}")
            raise
    
    def get_statistics(self, symbol: Optional[str] = None, 
                      lookback: Optional[int] = None) -> Dict:
        """
        Get slippage statistics.
        
        Args:
            symbol: Filter by symbol (None for all)
            lookback: Number of recent trades to analyze
            
        Returns:
            Dictionary of statistics
        """
        # Filter records
        try:
            records = self.records
            if symbol:
                records = [r for r in records if r.symbol == symbol]
            if lookback:
                records = records[-lookback:]
        
            if not records:
                return {'error': 'No records found'}
        
            # Extract slippage values
            slippage_bps = [r.slippage_bps for r in records]
            slippage_costs = [r.slippage_cost for r in records]
        
            # Calculate statistics
            stats = {
                'count': len(records),
                'avg_slippage_bps': np.mean(slippage_bps),
                'median_slippage_bps': np.median(slippage_bps),
                'std_slippage_bps': np.std(slippage_bps),
                'max_slippage_bps': np.max(slippage_bps),
                'min_slippage_bps': np.min(slippage_bps),
                'total_cost': np.sum(slippage_costs),
                'avg_cost_per_trade': np.mean(slippage_costs),
                'positive_slippage_pct': (np.array(slippage_bps) > 0).mean() * 100
            }
        
            # Per-side statistics
            buy_records = [r for r in records if r.side == 'buy']
            sell_records = [r for r in records if r.side == 'sell']
        
            if buy_records:
                stats['buy_avg_slippage_bps'] = np.mean([r.slippage_bps for r in buy_records])
            if sell_records:
                stats['sell_avg_slippage_bps'] = np.mean([r.slippage_bps for r in sell_records])
        
            return stats
        except Exception as e:
            logger.error(f"Error in get_statistics: {e}")
            raise
    
    def get_slippage_by_symbol(self) -> Dict[str, Dict]:
        """Get slippage statistics grouped by symbol."""
        try:
            symbols = set(r.symbol for r in self.records)
        
            return {
                symbol: self.get_statistics(symbol=symbol)
                for symbol in symbols
            }
        except Exception as e:
            logger.error(f"Error in get_slippage_by_symbol: {e}")
            raise
    
    def get_recent_slippage(self, n: int = 10) -> List[Dict]:
        """Get N most recent slippage records."""
        try:
            recent = self.records[-n:]
        
            return [
                {
                    'timestamp': r.timestamp,
                    'symbol': r.symbol,
                    'side': r.side,
                    'expected_price': r.expected_price,
                    'fill_price': r.fill_price,
                    'slippage_bps': r.slippage_bps,
                    'slippage_cost': r.slippage_cost
                }
                for r in recent
            ]
        except Exception as e:
            logger.error(f"Error in get_recent_slippage: {e}")
            raise
    
    def export_to_dataframe(self) -> pd.DataFrame:
        """Export records to pandas DataFrame."""
        try:
            if not self.records:
                return pd.DataFrame()
        
            data = []
            for r in self.records:
                data.append({
                    'timestamp': pd.to_datetime(r.timestamp, unit='s'),
                    'symbol': r.symbol,
                    'side': r.side,
                    'expected_price': r.expected_price,
                    'fill_price': r.fill_price,
                    'quantity': r.quantity,
                    'slippage_bps': r.slippage_bps,
                    'slippage_cost': r.slippage_cost
                })
        
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error in export_to_dataframe: {e}")
            raise


class MarketImpactModel:
    """Model market impact of trades."""
    
    def __init__(self, model_type: str = 'linear'):
        """
        Initialize market impact model.
        
        Args:
            model_type: 'linear', 'sqrt', or 'power'
        """
        try:
            self.model_type = model_type
            self.calibrated = False
            self.params = {}
        
            logger.info(f"Market impact model initialized ({model_type})")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def estimate_impact(self, quantity: float, adv: float, 
                       volatility: float = 0.01) -> float:
        """
        Estimate market impact in basis points.
        
        Args:
            quantity: Trade quantity
            adv: Average daily volume
            volatility: Daily volatility
            
        Returns:
            Estimated impact in basis points
        """
        # Participation rate
        try:
            participation = quantity / adv
        
            if self.model_type == 'linear':
                # Simple linear model
                impact_bps = participation * volatility * 10000 * 0.5
        
            elif self.model_type == 'sqrt':
                # Square root model (more realistic)
                impact_bps = np.sqrt(participation) * volatility * 10000 * 0.3
        
            elif self.model_type == 'power':
                # Power law model
                impact_bps = (participation ** 0.6) * volatility * 10000 * 0.4
        
            else:
                impact_bps = 0.0
        
            return impact_bps
        except Exception as e:
            logger.error(f"Error in estimate_impact: {e}")
            raise
    
    def calibrate(self, slippage_tracker: SlippageTracker, 
                 volume_data: Dict[str, float]):
        """
        Calibrate model using historical slippage data.
        
        Args:
            slippage_tracker: SlippageTracker instance
            volume_data: Dict mapping symbols to ADV
        """
        # Get historical data
        try:
            df = slippage_tracker.export_to_dataframe()
        
            if df.empty:
                logger.warning("No data to calibrate market impact model")
                return
        
            # Add participation rates
            df['adv'] = df['symbol'].map(volume_data)
            df['participation'] = df['quantity'] / df['adv']
        
            # Fit model (simplified)
            # In production, use proper regression
            self.params['alpha'] = df['slippage_bps'].mean() / df['participation'].mean()
        
            self.calibrated = True
            logger.success("Market impact model calibrated")
        except Exception as e:
            logger.error(f"Error in calibrate: {e}")
            raise
    
    def get_optimal_execution_time(self, quantity: float, adv: float,
                                   max_participation: float = 0.1) -> float:
        """
        Calculate optimal execution time to minimize impact.
        
        Args:
            quantity: Total quantity to execute
            adv: Average daily volume
            max_participation: Maximum participation rate
            
        Returns:
            Optimal execution time in hours
        """
        # Simple calculation: spread execution to stay under max participation
        try:
            daily_quantity = adv * max_participation
            days_needed = quantity / daily_quantity
            hours_needed = days_needed * 24
        
            return max(0.1, hours_needed)  # At least 6 minutes
        except Exception as e:
            logger.error(f"Error in get_optimal_execution_time: {e}")
            raise
