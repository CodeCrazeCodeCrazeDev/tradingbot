"""
Dark Pool Data Analyzer
Advanced analysis of dark pool trading data for alpha generation
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import aiohttp
try:
    import requests
except ImportError:
    requests = None
import json
from datetime import datetime, timedelta
import logging
import asyncio
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
import numpy
import pandas

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



# Initialize logging
logger = logging.getLogger(__name__)


@dataclass
class DarkPoolSignal:
    """Signal generated from dark pool data analysis"""
    ticker: str
    timestamp: datetime
    signal_type: str  # 'bullish', 'bearish', 'neutral'
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    volume: float
    price: float
    premium_discount: float  # % premium/discount to NBBO
    block_count: int
    unusual_activity: bool
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'ticker': self.ticker,
            'timestamp': self.timestamp.isoformat(),
            'signal_type': self.signal_type,
            'strength': self.strength,
            'confidence': self.confidence,
            'volume': self.volume,
            'price': self.price,
            'premium_discount': self.premium_discount,
            'block_count': self.block_count,
            'unusual_activity': self.unusual_activity,
            'metadata': self.metadata
        }


class DarkPoolAnalyzer:
    """
    Advanced analysis of dark pool trading data for alpha generation
    
    Features:
    - Block trade detection and analysis
    - Unusual volume detection
    - Price impact analysis
    - Institutional activity tracking
    - Liquidity imbalance detection
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # API configuration
        self.api_key = self.config.get('api_key', '')
        self.base_url = self.config.get('base_url', 'https://api.darkpooldata.com/v1/')
        
        # Analysis parameters
        self.volume_threshold = self.config.get('volume_threshold', 0.05)  # 5% of ADV
        self.block_size_threshold = self.config.get('block_size_threshold', 10000)  # shares
        self.lookback_days = self.config.get('lookback_days', 20)
        self.unusual_volume_z_score = self.config.get('unusual_volume_z_score', 2.0)
        self.price_impact_threshold = self.config.get('price_impact_threshold', 0.5)  # % price move
        
        # Historical data cache
        self.historical_data = {}
        self.baseline_metrics = {}
        self.last_update = {}
        
        logger.info("Dark Pool Analyzer initialized")
    
    async def get_signals(self, tickers: List[str]) -> List[DarkPoolSignal]:
        """
        Get dark pool trading signals for a list of tickers
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            List of dark pool signals
        """
        signals = []
        
        for ticker in tickers:
            try:
                # Get dark pool data
                dark_pool_data = await self._get_dark_pool_data(ticker)
                if not dark_pool_data:
                    continue
                
                # Update historical data
                self._update_historical_data(ticker, dark_pool_data)
                
                # Calculate baseline metrics if needed
                if ticker not in self.baseline_metrics:
                    self._calculate_baseline_metrics(ticker)
                
                # Analyze for signals
                ticker_signals = self._analyze_for_signals(ticker, dark_pool_data)
                signals.extend(ticker_signals)
                
            except Exception as e:
                logger.error(f"Error analyzing dark pool data for {ticker}: {e}")
        
        return signals
    
    async def _get_dark_pool_data(self, ticker: str) -> List[Dict[str, Any]]:
        """
        Get dark pool data for a ticker
        
        In a real implementation, this would call an API service
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            List of dark pool trades
        """
        # This is a simulated implementation
        # In a real system, this would call a dark pool data provider API
        
        # Check if we should simulate data
        if not self.config.get('simulate_data', True):
            try:
                # Make API request
                url = f"{self.base_url}trades/{ticker}"
                headers = {'Authorization': f'Bearer {self.api_key}'}
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            logger.error(f"API error: {response.status}")
                            return []
            except Exception as e:
                logger.error(f"Error fetching dark pool data: {e}")
                return []
        
        # Simulate realistic dark pool data
        return self._simulate_dark_pool_data(ticker)
    
    def _simulate_dark_pool_data(self, ticker: str) -> List[Dict[str, Any]]:
        """Simulate realistic dark pool data for testing"""
        # Get base price for the ticker (would be real in production)
        base_price = self._get_simulated_price(ticker)
        
        # Generate random number of trades (more for liquid stocks)
        num_trades = np.random.randint(5, 30)
        
        # Generate trades over the past day
        now = datetime.now()
        trades = []
        
        for _ in range(num_trades):
            # Random time in the past 24 hours
            trade_time = now - timedelta(minutes=np.random.randint(1, 1440))
            
            # Random price with slight variation
            price = base_price * (1 + np.random.normal(0, 0.005))
            
            # Random volume (log-normal distribution for realistic sizes)
            volume = int(np.random.lognormal(10, 1))
            
            # Random venue
            venue = np.random.choice([
                'UBS ATS', 'SIGMA X', 'MS POOL', 'JPM-X', 'BARX',
                'CITADEL CONNECT', 'VIRTU MATCHIT', 'INSTINCT X'
            ])
            
            # Premium/discount to NBBO
            premium_discount = np.random.normal(0, 0.001)
            
            trades.append({
                'ticker': ticker,
                'timestamp': trade_time.isoformat(),
                'price': price,
                'volume': volume,
                'venue': venue,
                'premium_discount': premium_discount,
                'block_trade': volume > self.block_size_threshold,
                'notional_value': price * volume
            })
        
        # Add a few block trades with higher probability for certain tickers
        if ticker in ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META']:
            num_blocks = np.random.randint(1, 5)
            for _ in range(num_blocks):
                # Random time in the past 24 hours
                trade_time = now - timedelta(minutes=np.random.randint(1, 1440))
                
                # Block trades often execute at slight discount
                price = base_price * (1 - np.random.uniform(0.001, 0.005))
                
                # Large block size
                volume = int(np.random.uniform(50000, 500000))
                
                # Random venue
                venue = np.random.choice([
                    'UBS ATS', 'SIGMA X', 'MS POOL', 'JPM-X', 'BARX'
                ])
                
                # Premium/discount to NBBO (blocks often trade at discount)
                premium_discount = -np.random.uniform(0.001, 0.003)
                
                trades.append({
                    'ticker': ticker,
                    'timestamp': trade_time.isoformat(),
                    'price': price,
                    'volume': volume,
                    'venue': venue,
                    'premium_discount': premium_discount,
                    'block_trade': True,
                    'notional_value': price * volume
                })
        
        # Sort by timestamp
        trades.sort(key=lambda x: x['timestamp'])
        
        return trades
    
    def _get_simulated_price(self, ticker: str) -> float:
        """Get simulated price for a ticker"""
        # Map common tickers to realistic prices
        price_map = {
            'AAPL': 175.0,
            'MSFT': 330.0,
            'AMZN': 130.0,
            'GOOGL': 140.0,
            'META': 300.0,
            'TSLA': 250.0,
            'NVDA': 450.0,
            'JPM': 150.0,
            'V': 240.0,
            'JNJ': 160.0
        }
        
        # Return mapped price or random price
        return price_map.get(ticker, np.random.uniform(50, 200))
    
    def _update_historical_data(self, ticker: str, new_data: List[Dict[str, Any]]):
        """Update historical data cache with new data"""
        if ticker not in self.historical_data:
            self.historical_data[ticker] = []
        
        # Add new data
        self.historical_data[ticker].extend(new_data)
        
        # Convert timestamps to datetime objects for easier processing
        for trade in self.historical_data[ticker]:
            if isinstance(trade.get('timestamp'), str):
                trade['timestamp'] = datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00'))
        
        # Keep only recent data
        cutoff = datetime.now() - timedelta(days=self.lookback_days)
        self.historical_data[ticker] = [
            trade for trade in self.historical_data[ticker]
            if trade['timestamp'] > cutoff
        ]
        
        # Sort by timestamp
        self.historical_data[ticker].sort(key=lambda x: x['timestamp'])
        
        # Update last update time
        self.last_update[ticker] = datetime.now()
    
    def _calculate_baseline_metrics(self, ticker: str):
        """Calculate baseline metrics for a ticker"""
        if ticker not in self.historical_data or not self.historical_data[ticker]:
            return
        
        data = self.historical_data[ticker]
        
        # Group by day
        daily_data = defaultdict(list)
        for trade in data:
            day = trade['timestamp'].date()
            daily_data[day].append(trade)
        
        # Calculate daily metrics
        daily_volumes = []
        daily_block_counts = []
        daily_price_impacts = []
        
        for day, trades in daily_data.items():
            # Daily volume
            volume = sum(trade['volume'] for trade in trades)
            daily_volumes.append(volume)
            
            # Block trade count
            block_count = sum(1 for trade in trades if trade.get('block_trade', False))
            daily_block_counts.append(block_count)
            
            # Price impact (max - min) / avg
            if len(trades) > 1:
                prices = [trade['price'] for trade in trades]
                avg_price = np.mean(prices)
                price_range = max(prices) - min(prices)
                price_impact = price_range / avg_price if avg_price > 0 else 0
                daily_price_impacts.append(price_impact)
        
        # Calculate baseline metrics
        self.baseline_metrics[ticker] = {
            'avg_daily_volume': np.mean(daily_volumes) if daily_volumes else 0,
            'std_daily_volume': np.std(daily_volumes) if len(daily_volumes) > 1 else 0,
            'avg_block_count': np.mean(daily_block_counts) if daily_block_counts else 0,
            'std_block_count': np.std(daily_block_counts) if len(daily_block_counts) > 1 else 0,
            'avg_price_impact': np.mean(daily_price_impacts) if daily_price_impacts else 0,
            'std_price_impact': np.std(daily_price_impacts) if len(daily_price_impacts) > 1 else 0
        }
    
    def _analyze_for_signals(self, ticker: str, recent_data: List[Dict[str, Any]]) -> List[DarkPoolSignal]:
        """Analyze dark pool data for trading signals"""
        signals = []
        
        if not recent_data or ticker not in self.baseline_metrics:
            return signals
        
        # Get baseline metrics
        baseline = self.baseline_metrics[ticker]
        
        # Aggregate recent data
        total_volume = sum(trade['volume'] for trade in recent_data)
        block_trades = [t for t in recent_data if t.get('block_trade', False)]
        block_count = len(block_trades)
        block_volume = sum(trade['volume'] for trade in block_trades)
        
        # Calculate volume-weighted average price
        vwap = sum(t['price'] * t['volume'] for t in recent_data) / total_volume if total_volume > 0 else 0
        
        # Calculate premium/discount
        premium_discounts = [t.get('premium_discount', 0) for t in recent_data]
        avg_premium_discount = np.mean(premium_discounts) if premium_discounts else 0
        
        # Check for unusual volume
        unusual_volume = False
        volume_z_score = 0
        
        if baseline['avg_daily_volume'] > 0 and baseline['std_daily_volume'] > 0:
            volume_z_score = (total_volume - baseline['avg_daily_volume']) / baseline['std_daily_volume']
            unusual_volume = volume_z_score > self.unusual_volume_z_score
        
        # Check for unusual block activity
        unusual_blocks = False
        block_z_score = 0
        
        if baseline['avg_block_count'] > 0 and baseline['std_block_count'] > 0:
            block_z_score = (block_count - baseline['avg_block_count']) / baseline['std_block_count']
            unusual_blocks = block_z_score > self.unusual_volume_z_score
        
        # Determine signal type
        signal_type = 'neutral'
        strength = 0.5
        confidence = 0.5
        
        # Block trades at premium often bullish
        if block_count > 0 and avg_premium_discount > 0.001:
            signal_type = 'bullish'
            strength = min(0.5 + abs(avg_premium_discount) * 100, 1.0)
            confidence = min(0.5 + block_z_score * 0.1, 0.9)
        
        # Block trades at discount often bearish
        elif block_count > 0 and avg_premium_discount < -0.001:
            signal_type = 'bearish'
            strength = min(0.5 + abs(avg_premium_discount) * 100, 1.0)
            confidence = min(0.5 + block_z_score * 0.1, 0.9)
        
        # Unusual volume can be a signal
        elif unusual_volume:
            # Look at price trend to determine direction
            if len(recent_data) > 1:
                first_price = recent_data[0]['price']
                last_price = recent_data[-1]['price']
                price_change = (last_price - first_price) / first_price
                
                if price_change > 0.005:  # 0.5% up
                    signal_type = 'bullish'
                    strength = min(0.5 + price_change * 50, 1.0)
                    confidence = min(0.5 + volume_z_score * 0.1, 0.9)
                elif price_change < -0.005:  # 0.5% down
                    signal_type = 'bearish'
                    strength = min(0.5 + abs(price_change) * 50, 1.0)
                    confidence = min(0.5 + volume_z_score * 0.1, 0.9)
        
        # Create signal if not neutral or if unusual activity
        if signal_type != 'neutral' or unusual_volume or unusual_blocks:
            signals.append(DarkPoolSignal(
                ticker=ticker,
                timestamp=datetime.now(),
                signal_type=signal_type,
                strength=strength,
                confidence=confidence,
                volume=total_volume,
                price=vwap,
                premium_discount=avg_premium_discount,
                block_count=block_count,
                unusual_activity=unusual_volume or unusual_blocks,
                metadata={
                    'volume_z_score': volume_z_score,
                    'block_z_score': block_z_score,
                    'block_volume': block_volume,
                    'block_volume_pct': block_volume / total_volume if total_volume > 0 else 0,
                    'venues': list(set(t.get('venue', 'unknown') for t in recent_data))
                }
            ))
        
        return signals
    
    def get_historical_analysis(self, ticker: str) -> Dict[str, Any]:
        """Get historical dark pool analysis for a ticker"""
        if ticker not in self.historical_data:
            return {'error': 'No historical data available'}
        
        data = self.historical_data[ticker]
        
        # Group by day
        daily_data = defaultdict(list)
        for trade in data:
            day = trade['timestamp'].date()
            daily_data[day].append(trade)
        
        # Calculate daily metrics
        daily_metrics = []
        
        for day, trades in sorted(daily_data.items()):
            volume = sum(trade['volume'] for trade in trades)
            block_trades = [t for t in trades if t.get('block_trade', False)]
            block_count = len(block_trades)
            block_volume = sum(trade['volume'] for trade in block_trades)
            
            # Calculate VWAP
            vwap = sum(t['price'] * t['volume'] for t in trades) / volume if volume > 0 else 0
            
            daily_metrics.append({
                'date': day.isoformat(),
                'volume': volume,
                'block_count': block_count,
                'block_volume': block_volume,
                'block_volume_pct': block_volume / volume if volume > 0 else 0,
                'vwap': vwap
            })
        
        return {
            'ticker': ticker,
            'days_analyzed': len(daily_metrics),
            'baseline_metrics': self.baseline_metrics.get(ticker, {}),
            'daily_metrics': daily_metrics
        }
    
    def plot_dark_pool_activity(self, ticker: str, save_path: Optional[str] = None):
        """Plot dark pool activity for a ticker"""
        if ticker not in self.historical_data:
            logger.warning(f"No historical data available for {ticker}")
            return
        
        data = self.historical_data[ticker]
        
        # Group by day
        daily_data = defaultdict(list)
        for trade in data:
            day = trade['timestamp'].date()
            daily_data[day].append(trade)
        
        # Calculate daily metrics
        dates = []
        volumes = []
        block_counts = []
        
        for day, trades in sorted(daily_data.items()):
            dates.append(day)
            volumes.append(sum(trade['volume'] for trade in trades))
            block_counts.append(sum(1 for trade in trades if trade.get('block_trade', False)))
        
        # Create plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # Plot volume
        ax1.bar(dates, volumes, color='blue', alpha=0.7)
        ax1.set_ylabel('Dark Pool Volume')
        ax1.set_title(f'Dark Pool Activity for {ticker}')
        ax1.grid(True, alpha=0.3)
        
        # Plot block count
        ax2.bar(dates, block_counts, color='red', alpha=0.7)
        ax2.set_ylabel('Block Trade Count')
        ax2.set_xlabel('Date')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Saved dark pool activity plot to {save_path}")
        else:
            plt.show()
        
        plt.close(fig)
