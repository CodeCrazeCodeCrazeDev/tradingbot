import logging
logger = logging.getLogger(__name__)
"""Microstructure Analysis for Market Intelligence System."""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
from datetime import datetime, timedelta
from collections import deque
import asyncio
import numpy
import pandas


class OrderBookAnalysis:
    """Analyze order book dynamics and microstructure patterns."""
    
    def __init__(self):
        try:
            self.order_book_history = deque(maxlen=1000)
            self.imbalance_threshold = 0.3
            logger.info("Initialized OrderBookAnalysis")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze_order_book_imbalance(self, order_book_data: Dict) -> Dict:
        """Analyze order book imbalance patterns."""
        try:
            if not order_book_data or 'bids' not in order_book_data or 'asks' not in order_book_data:
                return {'imbalance': 0, 'direction': 'neutral', 'strength': 'weak'}
        
            bids = order_book_data['bids']
            asks = order_book_data['asks']
        
            # Calculate volume imbalance
            bid_volume = sum(level['volume'] for level in bids[:5])  # Top 5 levels
            ask_volume = sum(level['volume'] for level in asks[:5])
        
            total_volume = bid_volume + ask_volume
            if total_volume == 0:
                return {'imbalance': 0, 'direction': 'neutral', 'strength': 'weak'}
        
            imbalance = (bid_volume - ask_volume) / total_volume
        
            # Determine direction and strength
            direction = 'bullish' if imbalance > self.imbalance_threshold else 'bearish' if imbalance < -self.imbalance_threshold else 'neutral'
            strength = self._calculate_imbalance_strength(abs(imbalance))
        
            return {
                'imbalance': imbalance,
                'direction': direction,
                'strength': strength,
                'bid_volume': bid_volume,
                'ask_volume': ask_volume,
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error in analyze_order_book_imbalance: {e}")
            raise
    
    def detect_order_book_spoofing(self, order_book_history: List[Dict]) -> List[Dict]:
        """Detect potential order book spoofing patterns."""
        try:
            spoofing_events = []
        
            if len(order_book_history) < 10:
                return spoofing_events
        
            for i in range(1, len(order_book_history)):
                current_book = order_book_history[i]
                previous_book = order_book_history[i-1]
            
                # Check for large order appearance and quick removal
                spoof_pattern = self._detect_spoof_pattern(previous_book, current_book)
            
                if spoof_pattern:
                    spoofing_events.append({
                        'timestamp': current_book.get('timestamp', datetime.now()),
                        'type': 'spoofing',
                        'side': spoof_pattern['side'],
                        'volume': spoof_pattern['volume'],
                        'price_level': spoof_pattern['price'],
                        'confidence': spoof_pattern['confidence']
                    })
        
            return spoofing_events
        except Exception as e:
            logger.error(f"Error in detect_order_book_spoofing: {e}")
            raise
    
    def calculate_market_depth(self, order_book_data: Dict, depth_levels: int = 10) -> Dict:
        """Calculate market depth metrics."""
        try:
            if not order_book_data:
                return {}
        
            bids = order_book_data.get('bids', [])[:depth_levels]
            asks = order_book_data.get('asks', [])[:depth_levels]
        
            bid_depth = sum(level['volume'] for level in bids)
            ask_depth = sum(level['volume'] for level in asks)
        
            # Calculate weighted average prices
            bid_wap = sum(level['price'] * level['volume'] for level in bids) / max(bid_depth, 1)
            ask_wap = sum(level['price'] * level['volume'] for level in asks) / max(ask_depth, 1)
        
            return {
                'bid_depth': bid_depth,
                'ask_depth': ask_depth,
                'total_depth': bid_depth + ask_depth,
                'depth_imbalance': (bid_depth - ask_depth) / max(bid_depth + ask_depth, 1),
                'bid_wap': bid_wap,
                'ask_wap': ask_wap,
                'spread': ask_wap - bid_wap if ask_wap > 0 and bid_wap > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error in calculate_market_depth: {e}")
            raise
    
    def _calculate_imbalance_strength(self, imbalance: float) -> str:
        """Calculate strength of order book imbalance."""
        try:
            if imbalance > 0.6:
                return 'extreme'
            elif imbalance > 0.4:
                return 'strong'
            elif imbalance > 0.2:
                return 'moderate'
            else:
                return 'weak'
        except Exception as e:
            logger.error(f"Error in _calculate_imbalance_strength: {e}")
            raise
    
    def _detect_spoof_pattern(self, previous_book: Dict, current_book: Dict) -> Optional[Dict]:
        """Detect spoofing pattern between two order book snapshots."""
        # Simplified spoofing detection
        try:
            prev_bids = previous_book.get('bids', [])
            curr_bids = current_book.get('bids', [])
        
            # Check for large order that disappeared
            for prev_bid in prev_bids:
                if prev_bid['volume'] > 10000:  # Large order threshold
                    # Check if this order is missing in current book
                    found = any(curr_bid['price'] == prev_bid['price'] and 
                               curr_bid['volume'] >= prev_bid['volume'] * 0.8 
                               for curr_bid in curr_bids)
                
                    if not found:
                        return {
                            'side': 'bid',
                            'volume': prev_bid['volume'],
                            'price': prev_bid['price'],
                            'confidence': 0.7
                        }
        
            return None
        except Exception as e:
            logger.error(f"Error in _detect_spoof_pattern: {e}")
            raise


class LiquidityDynamics:
    """Analyze liquidity dynamics and flow patterns."""
    
    def __init__(self):
        try:
            self.liquidity_history = deque(maxlen=500)
            logger.info("Initialized LiquidityDynamics")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze_liquidity_flow(self, trade_data: List[Dict]) -> Dict:
        """Analyze liquidity flow patterns from trade data."""
        try:
            if not trade_data:
                return {}
        
            # Separate aggressive buys and sells
            aggressive_buys = [trade for trade in trade_data if trade.get('side') == 'buy' and trade.get('aggressive', True)]
            aggressive_sells = [trade for trade in trade_data if trade.get('side') == 'sell' and trade.get('aggressive', True)]
        
            buy_volume = sum(trade['volume'] for trade in aggressive_buys)
            sell_volume = sum(trade['volume'] for trade in aggressive_sells)
        
            total_volume = buy_volume + sell_volume
        
            if total_volume == 0:
                return {'flow_direction': 'neutral', 'flow_strength': 0}
        
            flow_imbalance = (buy_volume - sell_volume) / total_volume
        
            return {
                'flow_direction': 'bullish' if flow_imbalance > 0.1 else 'bearish' if flow_imbalance < -0.1 else 'neutral',
                'flow_strength': abs(flow_imbalance),
                'buy_volume': buy_volume,
                'sell_volume': sell_volume,
                'total_volume': total_volume,
                'flow_imbalance': flow_imbalance,
                'trade_count': len(trade_data)
            }
        except Exception as e:
            logger.error(f"Error in analyze_liquidity_flow: {e}")
            raise
    
    def detect_liquidity_events(self, df: pd.DataFrame) -> List[Dict]:
        """Detect significant liquidity events."""
        try:
            events = []
        
            if 'volume' not in df.columns:
                return events
        
            # Calculate volume moving average and standard deviation
            df_copy = df.copy()
            df_copy['volume_ma'] = df_copy['volume'].rolling(20).mean()
            df_copy['volume_std'] = df_copy['volume'].rolling(20).std()
        
            # Detect volume spikes (liquidity events)
            for i, (timestamp, row) in enumerate(df_copy.iterrows()):
                if pd.isna(row['volume_ma']) or pd.isna(row['volume_std']):
                    continue
            
                # Volume spike threshold
                threshold = row['volume_ma'] + 2 * row['volume_std']
            
                if row['volume'] > threshold:
                    event_type = self._classify_liquidity_event(df_copy, i)
                
                    events.append({
                        'timestamp': timestamp,
                        'type': event_type,
                        'volume': row['volume'],
                        'volume_ratio': row['volume'] / row['volume_ma'],
                        'price_impact': self._calculate_price_impact(df_copy, i),
                        'duration': self._estimate_event_duration(df_copy, i)
                    })
        
            return events
        except Exception as e:
            logger.error(f"Error in detect_liquidity_events: {e}")
            raise
    
    def calculate_liquidity_score(self, order_book_data: Dict, trade_data: List[Dict]) -> float:
        """Calculate overall liquidity score."""
        try:
            if not order_book_data and not trade_data:
                return 0.0
        
            score_components = []
        
            # Order book depth component
            if order_book_data:
                depth_metrics = self.calculate_market_depth(order_book_data)
                depth_score = min(1.0, depth_metrics.get('total_depth', 0) / 100000)  # Normalize
                score_components.append(depth_score * 0.4)
        
            # Trade frequency component
            if trade_data:
                trade_frequency = len(trade_data) / max(1, (trade_data[-1]['timestamp'] - trade_data[0]['timestamp']).total_seconds() / 60)  # trades per minute
                frequency_score = min(1.0, trade_frequency / 10)  # Normalize
                score_components.append(frequency_score * 0.3)
        
            # Spread component (lower spread = higher liquidity)
            if order_book_data:
                bids = order_book_data.get('bids', [])
                asks = order_book_data.get('asks', [])
            
                if bids and asks:
                    spread = asks[0]['price'] - bids[0]['price']
                    mid_price = (asks[0]['price'] + bids[0]['price']) / 2
                    spread_ratio = spread / mid_price
                    spread_score = max(0.0, 1.0 - spread_ratio * 1000)  # Lower spread = higher score
                    score_components.append(spread_score * 0.3)
        
            return sum(score_components) if score_components else 0.0
        except Exception as e:
            logger.error(f"Error in calculate_liquidity_score: {e}")
            raise
    
    def _classify_liquidity_event(self, df: pd.DataFrame, index: int) -> str:
        """Classify the type of liquidity event."""
        try:
            if index < 2 or index >= len(df) - 2:
                return 'unknown'
        
            # Analyze price movement around the event
            before_price = df['close'].iloc[index-2:index].mean()
            after_price = df['close'].iloc[index+1:index+3].mean()
        
            price_change = (after_price - before_price) / before_price
        
            if price_change > 0.001:
                return 'liquidity_absorption_bullish'
            elif price_change < -0.001:
                return 'liquidity_absorption_bearish'
            else:
                return 'liquidity_provision'
        except Exception as e:
            logger.error(f"Error in _classify_liquidity_event: {e}")
            raise
    
    def _calculate_price_impact(self, df: pd.DataFrame, index: int) -> float:
        """Calculate price impact of liquidity event."""
        try:
            if index == 0:
                return 0.0
        
            current_price = df['close'].iloc[index]
            previous_price = df['close'].iloc[index-1]
        
            return abs(current_price - previous_price) / previous_price
        except Exception as e:
            logger.error(f"Error in _calculate_price_impact: {e}")
            raise
    
    def _estimate_event_duration(self, df: pd.DataFrame, index: int) -> int:
        """Estimate duration of liquidity event in periods."""
        # Simple estimation - look for return to normal volume
        try:
            normal_volume = df['volume_ma'].iloc[index]
        
            duration = 1
            for i in range(index + 1, min(len(df), index + 10)):
                if df['volume'].iloc[i] < normal_volume * 1.5:
                    break
                duration += 1
        
            return duration
        except Exception as e:
            logger.error(f"Error in _estimate_event_duration: {e}")
            raise
    
    def calculate_market_depth(self, order_book_data: Dict) -> Dict:
        """Calculate market depth from order book."""
        try:
            if not order_book_data:
                return {'total_depth': 0}
        
            bids = order_book_data.get('bids', [])
            asks = order_book_data.get('asks', [])
        
            bid_depth = sum(level['volume'] for level in bids)
            ask_depth = sum(level['volume'] for level in asks)
        
            return {
                'bid_depth': bid_depth,
                'ask_depth': ask_depth,
                'total_depth': bid_depth + ask_depth
            }
        except Exception as e:
            logger.error(f"Error in calculate_market_depth: {e}")
            raise


class SupplyDemandImbalances:
    """Detect and analyze supply/demand imbalances in market microstructure."""
    
    def __init__(self):
        try:
            self.imbalance_history = deque(maxlen=200)
            logger.info("Initialized SupplyDemandImbalances")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_supply_demand_imbalances(self, df: pd.DataFrame) -> List[Dict]:
        """Detect supply/demand imbalances from price and volume data."""
        try:
            imbalances = []
        
            if len(df) < 20:
                return imbalances
        
            # Calculate volume-weighted metrics
            df_copy = df.copy()
            df_copy['vwap'] = (df_copy['volume'] * df_copy['close']).cumsum() / df_copy['volume'].cumsum()
            df_copy['volume_ma'] = df_copy['volume'].rolling(10).mean()
        
            # Detect imbalance patterns
            for i in range(10, len(df_copy)):
                window = df_copy.iloc[i-10:i+1]
            
                imbalance_signal = self._analyze_imbalance_pattern(window)
            
                if imbalance_signal:
                    imbalances.append({
                        'timestamp': df_copy.index[i],
                        'type': imbalance_signal['type'],
                        'strength': imbalance_signal['strength'],
                        'price_level': df_copy['close'].iloc[i],
                        'volume_confirmation': imbalance_signal['volume_confirmation'],
                        'expected_direction': imbalance_signal['expected_direction']
                    })
        
            return imbalances
        except Exception as e:
            logger.error(f"Error in detect_supply_demand_imbalances: {e}")
            raise
    
    def analyze_order_flow_imbalance(self, trade_data: List[Dict]) -> Dict:
        """Analyze order flow imbalances from trade-by-trade data."""
        try:
            if not trade_data:
                return {}
        
            # Classify trades as buyer or seller initiated
            buyer_initiated = []
            seller_initiated = []
        
            for trade in trade_data:
                if trade.get('side') == 'buy' or trade.get('aggressor') == 'buyer':
                    buyer_initiated.append(trade)
                else:
                    seller_initiated.append(trade)
        
            buyer_volume = sum(trade['volume'] for trade in buyer_initiated)
            seller_volume = sum(trade['volume'] for trade in seller_initiated)
        
            total_volume = buyer_volume + seller_volume
        
            if total_volume == 0:
                return {'imbalance': 0, 'direction': 'neutral'}
        
            imbalance = (buyer_volume - seller_volume) / total_volume
        
            return {
                'imbalance': imbalance,
                'direction': 'demand_excess' if imbalance > 0.2 else 'supply_excess' if imbalance < -0.2 else 'balanced',
                'buyer_volume': buyer_volume,
                'seller_volume': seller_volume,
                'buyer_trades': len(buyer_initiated),
                'seller_trades': len(seller_initiated),
                'avg_buyer_size': buyer_volume / max(len(buyer_initiated), 1),
                'avg_seller_size': seller_volume / max(len(seller_initiated), 1)
            }
        except Exception as e:
            logger.error(f"Error in analyze_order_flow_imbalance: {e}")
            raise
    
    def detect_hidden_liquidity(self, df: pd.DataFrame, order_book_history: List[Dict]) -> List[Dict]:
        """Detect hidden liquidity patterns."""
        try:
            hidden_liquidity_events = []
        
            # Look for price levels where large volume was absorbed without significant price movement
            for i in range(20, len(df)):
                window = df.iloc[i-20:i+1]
            
                # Check for high volume with low price movement
                total_volume = window['volume'].sum()
                price_range = window['high'].max() - window['low'].min()
                avg_price = window['close'].mean()
            
                if total_volume > window['volume'].mean() * 3 and price_range / avg_price < 0.005:
                    hidden_liquidity_events.append({
                        'timestamp': df.index[i],
                        'type': 'hidden_liquidity',
                        'price_level': avg_price,
                        'absorbed_volume': total_volume,
                        'price_stability': 1.0 - (price_range / avg_price),
                        'liquidity_strength': self._calculate_liquidity_strength(window)
                    })
        
            return hidden_liquidity_events
        except Exception as e:
            logger.error(f"Error in detect_hidden_liquidity: {e}")
            raise
    
    def calculate_market_pressure(self, recent_trades: List[Dict], 
                                order_book_data: Dict) -> Dict:
        """Calculate current market pressure metrics."""
        try:
            pressure_metrics = {
                'buy_pressure': 0.0,
                'sell_pressure': 0.0,
                'net_pressure': 0.0,
                'pressure_direction': 'neutral'
            }
        
            if not recent_trades:
                return pressure_metrics
        
            # Calculate trade-based pressure
            buy_volume = sum(trade['volume'] for trade in recent_trades 
                            if trade.get('side') == 'buy')
            sell_volume = sum(trade['volume'] for trade in recent_trades 
                             if trade.get('side') == 'sell')
        
            total_volume = buy_volume + sell_volume
        
            if total_volume > 0:
                pressure_metrics['buy_pressure'] = buy_volume / total_volume
                pressure_metrics['sell_pressure'] = sell_volume / total_volume
                pressure_metrics['net_pressure'] = (buy_volume - sell_volume) / total_volume
        
            # Add order book pressure
            if order_book_data:
                ob_analysis = OrderBookAnalysis()
                ob_imbalance = ob_analysis.analyze_order_book_imbalance(order_book_data)
            
                # Combine trade and order book pressure
                combined_pressure = (pressure_metrics['net_pressure'] + ob_imbalance['imbalance']) / 2
                pressure_metrics['net_pressure'] = combined_pressure
        
            # Determine direction
            if pressure_metrics['net_pressure'] > 0.1:
                pressure_metrics['pressure_direction'] = 'bullish'
            elif pressure_metrics['net_pressure'] < -0.1:
                pressure_metrics['pressure_direction'] = 'bearish'
        
            return pressure_metrics
        except Exception as e:
            logger.error(f"Error in calculate_market_pressure: {e}")
            raise
    
    def _analyze_imbalance_pattern(self, window: pd.DataFrame) -> Optional[Dict]:
        """Analyze window for supply/demand imbalance patterns."""
        # Check for volume surge with price rejection
        try:
            volume_surge = window['volume'].iloc[-1] > window['volume_ma'].iloc[-1] * 2
        
            if not volume_surge:
                return None
        
            # Analyze price action
            open_price = window['open'].iloc[-1]
            high_price = window['high'].iloc[-1]
            low_price = window['low'].iloc[-1]
            close_price = window['close'].iloc[-1]
        
            # Check for rejection patterns
            upper_wick = (high_price - max(open_price, close_price)) / (high_price - low_price) if high_price != low_price else 0
            lower_wick = (min(open_price, close_price) - low_price) / (high_price - low_price) if high_price != low_price else 0
        
            if upper_wick > 0.6:  # Strong upper rejection
                return {
                    'type': 'supply_imbalance',
                    'strength': upper_wick,
                    'volume_confirmation': True,
                    'expected_direction': 'bearish'
                }
            elif lower_wick > 0.6:  # Strong lower rejection
                return {
                    'type': 'demand_imbalance',
                    'strength': lower_wick,
                    'volume_confirmation': True,
                    'expected_direction': 'bullish'
                }
        
            return None
        except Exception as e:
            logger.error(f"Error in _analyze_imbalance_pattern: {e}")
            raise
    
    def _calculate_liquidity_strength(self, window: pd.DataFrame) -> float:
        """Calculate strength of hidden liquidity."""
        try:
            volume_consistency = 1.0 - (window['volume'].std() / window['volume'].mean())
            price_stability = 1.0 - ((window['high'].max() - window['low'].min()) / window['close'].mean())
        
            return (volume_consistency + price_stability) / 2
        except Exception as e:
            logger.error(f"Error in _calculate_liquidity_strength: {e}")
            raise


class MarketMicrostructureAnalyzer:
    """Main analyzer combining all microstructure components."""
    
    def __init__(self):
        try:
            self.order_book_analyzer = OrderBookAnalysis()
            self.liquidity_dynamics = LiquidityDynamics()
            self.supply_demand_analyzer = SupplyDemandImbalances()
            logger.info("Initialized MarketMicrostructureAnalyzer")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def comprehensive_microstructure_analysis(self, 
                                                  df: pd.DataFrame,
                                                  order_book_data: Optional[Dict] = None,
                                                  trade_data: Optional[List[Dict]] = None) -> Dict:
        """Perform comprehensive microstructure analysis."""
        try:
            analysis_results = {
                'timestamp': datetime.now(),
                'order_book_analysis': {},
                'liquidity_analysis': {},
                'supply_demand_analysis': {},
                'overall_assessment': {}
            }
        
            # Order book analysis
            if order_book_data:
                analysis_results['order_book_analysis'] = {
                    'imbalance': self.order_book_analyzer.analyze_order_book_imbalance(order_book_data),
                    'market_depth': self.order_book_analyzer.calculate_market_depth(order_book_data)
                }
        
            # Liquidity analysis
            liquidity_events = self.liquidity_dynamics.detect_liquidity_events(df)
            analysis_results['liquidity_analysis'] = {
                'events': liquidity_events,
                'liquidity_score': self.liquidity_dynamics.calculate_liquidity_score(order_book_data, trade_data or [])
            }
        
            if trade_data:
                analysis_results['liquidity_analysis']['flow'] = self.liquidity_dynamics.analyze_liquidity_flow(trade_data)
        
            # Supply/demand analysis
            imbalances = self.supply_demand_analyzer.detect_supply_demand_imbalances(df)
            analysis_results['supply_demand_analysis'] = {
                'imbalances': imbalances,
                'market_pressure': self.supply_demand_analyzer.calculate_market_pressure(trade_data or [], order_book_data)
            }
        
            if trade_data:
                analysis_results['supply_demand_analysis']['order_flow'] = self.supply_demand_analyzer.analyze_order_flow_imbalance(trade_data)
        
            # Overall assessment
            analysis_results['overall_assessment'] = self._generate_overall_assessment(analysis_results)
        
            return analysis_results
        except Exception as e:
            logger.error(f"Error in comprehensive_microstructure_analysis: {e}")
            raise
    
    def _generate_overall_assessment(self, analysis_results: Dict) -> Dict:
        """Generate overall microstructure assessment."""
        try:
            assessment = {
                'market_quality': 'normal',
                'liquidity_condition': 'adequate',
                'dominant_force': 'balanced',
                'risk_level': 'medium',
                'trading_recommendation': 'neutral'
            }
        
            # Assess liquidity condition
            liquidity_score = analysis_results.get('liquidity_analysis', {}).get('liquidity_score', 0.5)
        
            if liquidity_score > 0.7:
                assessment['liquidity_condition'] = 'high'
            elif liquidity_score < 0.3:
                assessment['liquidity_condition'] = 'low'
                assessment['risk_level'] = 'high'
        
            # Assess dominant market force
            market_pressure = analysis_results.get('supply_demand_analysis', {}).get('market_pressure', {})
            net_pressure = market_pressure.get('net_pressure', 0)
        
            if net_pressure > 0.2:
                assessment['dominant_force'] = 'demand'
                assessment['trading_recommendation'] = 'bullish_bias'
            elif net_pressure < -0.2:
                assessment['dominant_force'] = 'supply'
                assessment['trading_recommendation'] = 'bearish_bias'
        
            return assessment
        except Exception as e:
            logger.error(f"Error in _generate_overall_assessment: {e}")
            raise
