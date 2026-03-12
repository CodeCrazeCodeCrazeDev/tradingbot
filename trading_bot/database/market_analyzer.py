"""
Market Analyzer
Integrates microstructure and order flow analysis with the data pipeline
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
import numpy as np
from .market_microstructure import MarketMicrostructure
from .order_flow_processor import OrderFlowProcessor
from .data_streaming import MarketDataStream
from .real_time_processor import DataProcessor
import numpy

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



logger = logging.getLogger(__name__)

class MarketAnalyzer:
    """
    High-level market analyzer that combines:
    - Market microstructure analysis
    - Order flow processing
    - Real-time data processing
    - Signal generation
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize components
        self.microstructure = MarketMicrostructure(config)
        self.order_flow = OrderFlowProcessor(config)
        self.data_stream = MarketDataStream(config)
        self.data_processor = DataProcessor(config)
        
        # Signal aggregation
        self.aggregated_signals: Dict[str, List[Dict]] = {}
        self.signal_weights = {
            'microstructure': 0.4,
            'order_flow': 0.4,
            'technical': 0.2
        }
        
        logger.info("Market analyzer initialized")
    
    async def initialize(self):
        """Initialize all components"""
        await self.data_stream.initialize()
        
        # Add processors for different analysis types
        self.data_processor.add_processor('market_data', self._process_market_data)
        self.data_processor.add_processor('order_flow', self._process_order_flow)
        
        logger.info("Market analyzer components initialized")
    
    async def start_analysis(self, symbols: List[str]):
        """Start market analysis for given symbols"""
        for symbol in symbols:
            # Create data streams
            await self.data_stream.create_stream(f"{symbol}_market")
            await self.data_stream.create_stream(f"{symbol}_orderflow")
            
            # Initialize signal storage
            self.aggregated_signals[symbol] = []
            
            logger.info(f"Started analysis for {symbol}")
    
    async def process_tick(self, symbol: str, tick: Dict[str, Any]):
        """Process new tick data"""
        try:
            # Push to data streams
            await self.data_stream.push_data(f"{symbol}_market", tick)
            await self.data_stream.push_data(f"{symbol}_orderflow", tick)
            
            # Process through components
            micro_analysis = await self.microstructure.process_trade(symbol, tick)
            flow_signal = await self.order_flow.process_tick(symbol, tick)
            
            # Combine signals
            combined_signal = await self._combine_signals(
                symbol, micro_analysis, flow_signal
            )
            
            if combined_signal:
                self.aggregated_signals[symbol].append(combined_signal)
            
            return combined_signal
            
        except Exception as e:
            logger.error(f"Error processing tick for {symbol}: {e}")
            raise
    
    async def _process_market_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process market data through microstructure analysis"""
        symbol = data.get('symbol')
        if not symbol:
            return data
        
        # Add microstructure metrics
        liquidity_analysis = self.microstructure.get_liquidity_analysis(symbol)
        
        return {
            **data,
            'liquidity_analysis': liquidity_analysis
        }
    
    async def _process_order_flow(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process order flow data"""
        symbol = data.get('symbol')
        if not symbol:
            return data
        
        # Add order flow metrics
        flow_stats = self.order_flow.get_order_flow_stats(symbol)
        signal_prob = self.order_flow.calculate_signal_probability(symbol)
        
        return {
            **data,
            'order_flow_stats': flow_stats,
            'signal_probabilities': signal_prob
        }
    
    async def _combine_signals(self, 
                             symbol: str,
                             micro_analysis: Dict[str, Any],
                             flow_signal: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Combine signals from different analysis components"""
        if not micro_analysis and not flow_signal:
            return None
        
        # Extract key metrics
        micro_strength = self._get_microstructure_strength(micro_analysis)
        flow_strength = self._get_orderflow_strength(flow_signal)
        
        # Determine signal direction
        direction = self._determine_signal_direction(
            micro_analysis, flow_signal
        )
        
        if not direction:
            return None
        
        # Calculate combined strength
        combined_strength = (
            micro_strength * self.signal_weights['microstructure'] +
            flow_strength * self.signal_weights['order_flow']
        )
        
        # Generate combined signal
        return {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'direction': direction,
            'strength': combined_strength,
            'confidence': min(combined_strength * 1.2, 1.0),  # Boost confidence but cap at 1.0
            'components': {
                'microstructure': micro_analysis,
                'order_flow': flow_signal
            }
        }
    
    def _get_microstructure_strength(self, 
                                   analysis: Optional[Dict[str, Any]]) -> float:
        """Extract strength from microstructure analysis"""
        if not analysis:
            return 0.0
        
        # Combine multiple factors
        factors = []
        
        # Liquidity imbalance
        if 'order_flow' in analysis:
            factors.append(abs(analysis['order_flow'].get('imbalance_ratio', 0)))
        
        # Price impact
        if 'liquidity_analysis' in analysis:
            zones = analysis['liquidity_analysis'].get('liquidity_zones', [])
            if zones:
                # Use closest liquidity zone
                closest_zone = min(zones, 
                                 key=lambda x: abs(x['price'] - analysis.get('current_price', 0)))
                factors.append(closest_zone.get('volume', 0) / 
                             analysis['order_flow'].get('avg_trade_size', 1))
        
        return np.mean(factors) if factors else 0.0
    
    def _get_orderflow_strength(self, 
                              signal: Optional[Dict[str, Any]]) -> float:
        """Extract strength from order flow signal"""
        if not signal:
            return 0.0
        
        return signal.get('strength', 0.0)
    
    def _determine_signal_direction(self,
                                  micro_analysis: Optional[Dict[str, Any]],
                                  flow_signal: Optional[Dict[str, Any]]) -> Optional[str]:
        """Determine overall signal direction"""
        directions = []
        
        # Get direction from microstructure
        if micro_analysis and 'order_flow' in micro_analysis:
            pressure = micro_analysis['order_flow'].get('pressure_score', 0)
            if abs(pressure) > 0.3:  # Minimum threshold
                directions.append('buy' if pressure > 0 else 'sell')
        
        # Get direction from order flow
        if flow_signal:
            directions.append(flow_signal.get('direction'))
        
        if not directions:
            return None
        
        # Return most common direction
        return max(set(directions), key=directions.count)
    
    def get_market_state(self, symbol: str) -> Dict[str, Any]:
        """Get current market state analysis"""
        return {
            'microstructure': self.microstructure.get_metrics(symbol),
            'order_flow': self.order_flow.get_order_flow_stats(symbol),
            'recent_signals': self.aggregated_signals.get(symbol, [])[-10:],
            'signal_probabilities': self.order_flow.calculate_signal_probability(symbol),
            'stream_metrics': self.data_stream.get_metrics(),
            'processing_metrics': self.data_processor.get_stats()
        }
    
    async def cleanup(self):
        """Cleanup all components"""
        await self.data_stream.cleanup()
        await self.data_processor.cleanup()
        logger.info("Market analyzer cleaned up")
