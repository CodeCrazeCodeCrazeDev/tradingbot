import logging
logger = logging.getLogger(__name__)
"""Market Microstructure Analysis for Adaptive Trading Bot.

This module analyzes market microstructure elements including:
- Order book dynamics and depth analysis
- Bid-ask spread patterns and liquidity
- Volume profile and market impact
- Trade flow analysis and institutional footprints
- Market making vs taking behavior
"""

# Standard library imports
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

# Third-party imports
import numpy as np
import pandas as pd
try:
    import talib  # Not directly used; optional dependency
    TALIB_AVAILABLE = True
except Exception:
    TALIB_AVAILABLE = False
    talib = None
from loguru import logger
import numpy
import pandas


class OrderType(Enum):
    """Order types for microstructure analysis."""
    MARKET_BUY = "market_buy"
    MARKET_SELL = "market_sell"
    LIMIT_BUY = "limit_buy"
    LIMIT_SELL = "limit_sell"
    AGGRESSIVE_BUY = "aggressive_buy"
    AGGRESSIVE_SELL = "aggressive_sell"


@dataclass
class MicrostructureSignal:
    """Market microstructure signal."""
    signal_type: str
    strength: float
    confidence: float
    timeframe: str
    timestamp: pd.Timestamp
    supporting_data: Dict[str, Any]
    market_impact: float
    liquidity_score: float


class MarketMicrostructureAnalyzer:
    """Advanced market microstructure analysis system."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the microstructure analyzer."""
        self.config = config or {}
        
        # Analysis parameters
        self.depth_levels = self.config.get('depth_levels', 10)
        self.volume_window = self.config.get('volume_window', 20)
        self.spread_threshold = self.config.get('spread_threshold', 0.0001)
        
        # Data buffers
        self.tick_buffer = deque(maxlen=1000)
        self.order_flow_buffer = deque(maxlen=500)
        self.spread_history = deque(maxlen=200)
        
        # Microstructure metrics
        self.current_metrics = {}
        
        logger.info("Market Microstructure Analyzer initialized")
    
    def analyze_microstructure(self, tick_data: pd.DataFrame, order_book: Optional[Dict] = None) -> List[MicrostructureSignal]:
        """Perform comprehensive microstructure analysis."""
        signals = []
        
        if len(tick_data) < 10:
            return signals
        
        # Update internal buffers
        self._update_buffers(tick_data, order_book)
        
        # Analyze different microstructure components
        signals.extend(self._analyze_order_flow(tick_data))
        signals.extend(self._analyze_spread_dynamics(tick_data))
        signals.extend(self._analyze_volume_profile(tick_data))
        signals.extend(self._analyze_market_impact(tick_data))
        signals.extend(self._analyze_liquidity_patterns(tick_data))
        
        if order_book:
            signals.extend(self._analyze_order_book_dynamics(order_book))
        
        # Update current metrics
        self._update_microstructure_metrics(tick_data, order_book)
        
        return signals
    
    def _update_buffers(self, tick_data: pd.DataFrame, order_book: Optional[Dict]):
        """Update internal data buffers."""
        # Add tick data to buffer
        for _, row in tick_data.iterrows():
            self.tick_buffer.append(row.to_dict())
        
        # Update spread history
        if 'bid' in tick_data.columns and 'ask' in tick_data.columns:
            spreads = tick_data['ask'] - tick_data['bid']
            for spread in spreads:
                self.spread_history.append(spread)
    
    def _analyze_order_flow(self, tick_data: pd.DataFrame) -> List[MicrostructureSignal]:
        """Analyze order flow patterns."""
        signals = []
        
        if 'volume' not in tick_data.columns:
            return signals
        
        # Calculate order flow imbalance
        buy_volume = 0
        sell_volume = 0
        
        for _, row in tick_data.iterrows():
            if 'side' in row and row['side'] == 'buy':
                buy_volume += row['volume']
            elif 'side' in row and row['side'] == 'sell':
                sell_volume += row['volume']
            else:
                # Infer from price movement
                if len(self.tick_buffer) > 1:
                    prev_price = self.tick_buffer[-2].get('price', row.get('close', 0))
                    current_price = row.get('price', row.get('close', 0))
                    
                    if current_price > prev_price:
                        buy_volume += row['volume']
                    else:
                        sell_volume += row['volume']
        
        total_volume = buy_volume + sell_volume
        if total_volume > 0:
            order_flow_imbalance = (buy_volume - sell_volume) / total_volume
            
            # Generate signal if imbalance is significant
            if abs(order_flow_imbalance) > 0.3:
                signals.append(MicrostructureSignal(
                    signal_type="order_flow_imbalance",
                    strength=abs(order_flow_imbalance),
                    confidence=0.7,
                    timeframe="tick",
                    timestamp=tick_data.index[-1],
                    supporting_data={
                        'buy_volume': buy_volume,
                        'sell_volume': sell_volume,
                        'imbalance': order_flow_imbalance
                    },
                    market_impact=abs(order_flow_imbalance) * 0.5,
                    liquidity_score=min(total_volume / 10000, 1.0)
                ))
        
        return signals
    
    def _analyze_spread_dynamics(self, tick_data: pd.DataFrame) -> List[MicrostructureSignal]:
        """Analyze bid-ask spread dynamics."""
        signals = []
        
        if 'bid' not in tick_data.columns or 'ask' not in tick_data.columns:
            return signals
        
        spreads = tick_data['ask'] - tick_data['bid']
        
        # Calculate spread statistics
        avg_spread = spreads.mean()
        spread_volatility = spreads.std()
        current_spread = spreads.iloc[-1]
        
        # Detect spread anomalies
        if len(self.spread_history) > 20:
            historical_avg = np.mean(list(self.spread_history)[-20:])
            spread_ratio = current_spread / historical_avg if historical_avg > 0 else 1
            
            # Wide spread signal (low liquidity)
            if spread_ratio > 2.0:
                signals.append(MicrostructureSignal(
                    signal_type="wide_spread",
                    strength=spread_ratio - 1.0,
                    confidence=0.8,
                    timeframe="tick",
                    timestamp=tick_data.index[-1],
                    supporting_data={
                        'current_spread': current_spread,
                        'historical_avg': historical_avg,
                        'spread_ratio': spread_ratio
                    },
                    market_impact=min(spread_ratio * 0.3, 1.0),
                    liquidity_score=max(0.1, 1.0 / spread_ratio)
                ))
            
            # Tight spread signal (high liquidity)
            elif spread_ratio < 0.5:
                signals.append(MicrostructureSignal(
                    signal_type="tight_spread",
                    strength=1.0 - spread_ratio,
                    confidence=0.7,
                    timeframe="tick",
                    timestamp=tick_data.index[-1],
                    supporting_data={
                        'current_spread': current_spread,
                        'historical_avg': historical_avg,
                        'spread_ratio': spread_ratio
                    },
                    market_impact=0.1,
                    liquidity_score=min(1.0, 2.0 / spread_ratio)
                ))
        
        return signals
    
    def _analyze_volume_profile(self, tick_data: pd.DataFrame) -> List[MicrostructureSignal]:
        """Analyze volume profile and distribution."""
        signals = []
        
        if 'volume' not in tick_data.columns:
            return signals
        
        # Calculate volume-weighted average price (VWAP)
        if 'price' in tick_data.columns:
            prices = tick_data['price']
        else:
            prices = (tick_data['high'] + tick_data['low'] + tick_data['close']) / 3
        
        volumes = tick_data['volume']
        vwap = (prices * volumes).sum() / volumes.sum()
        current_price = prices.iloc[-1]
        
        # Price vs VWAP deviation
        vwap_deviation = (current_price - vwap) / vwap
        
        if abs(vwap_deviation) > 0.005:  # 0.5% deviation
            signals.append(MicrostructureSignal(
                signal_type="vwap_deviation",
                strength=abs(vwap_deviation),
                confidence=0.6,
                timeframe="tick",
                timestamp=tick_data.index[-1],
                supporting_data={
                    'vwap': vwap,
                    'current_price': current_price,
                    'deviation': vwap_deviation
                },
                market_impact=abs(vwap_deviation) * 2,
                liquidity_score=0.5
            ))
        
        # Volume surge detection
        avg_volume = volumes.mean()
        max_volume = volumes.max()
        
        if max_volume > avg_volume * 3:  # 3x average volume
            volume_surge_strength = max_volume / avg_volume
            
            signals.append(MicrostructureSignal(
                signal_type="volume_surge",
                strength=min(volume_surge_strength / 10, 1.0),
                confidence=0.8,
                timeframe="tick",
                timestamp=tick_data.index[-1],
                supporting_data={
                    'max_volume': max_volume,
                    'avg_volume': avg_volume,
                    'surge_ratio': volume_surge_strength
                },
                market_impact=min(volume_surge_strength * 0.1, 1.0),
                liquidity_score=min(volume_surge_strength * 0.2, 1.0)
            ))
        
        return signals
    
    def _analyze_market_impact(self, tick_data: pd.DataFrame) -> List[MicrostructureSignal]:
        """Analyze market impact of trades."""
        signals = []
        
        if len(tick_data) < 5:
            return signals
        
        # Calculate price impact per unit volume
        price_changes = tick_data['close'].pct_change().fillna(0)
        volumes = tick_data['volume']
        
        # Market impact coefficient
        impact_coefficients = []
        for i in range(1, len(tick_data)):
            if volumes.iloc[i] > 0:
                impact = abs(price_changes.iloc[i]) / (volumes.iloc[i] / 1000)  # Per 1000 units
                impact_coefficients.append(impact)
        
        if impact_coefficients:
            avg_impact = np.mean(impact_coefficients)
            current_impact = impact_coefficients[-1] if impact_coefficients else 0
            
            # High impact signal
            if current_impact > avg_impact * 2:
                signals.append(MicrostructureSignal(
                    signal_type="high_market_impact",
                    strength=min(current_impact / avg_impact, 5.0) / 5.0,
                    confidence=0.7,
                    timeframe="tick",
                    timestamp=tick_data.index[-1],
                    supporting_data={
                        'current_impact': current_impact,
                        'avg_impact': avg_impact,
                        'impact_ratio': current_impact / avg_impact
                    },
                    market_impact=min(current_impact * 10, 1.0),
                    liquidity_score=max(0.1, 1.0 / (current_impact * 100 + 1))
                ))
        
        return signals
    
    def _analyze_liquidity_patterns(self, tick_data: pd.DataFrame) -> List[MicrostructureSignal]:
        """Analyze liquidity patterns and availability."""
        signals = []
        
        # Liquidity proxy: inverse of price volatility per unit volume
        if 'volume' in tick_data.columns and len(tick_data) > 10:
            price_volatility = tick_data['close'].pct_change().std()
            avg_volume = tick_data['volume'].mean()
            
            if avg_volume > 0 and price_volatility > 0:
                liquidity_score = 1.0 / (price_volatility * 1000 / avg_volume + 1)
                
                # Low liquidity warning
                if liquidity_score < 0.3:
                    signals.append(MicrostructureSignal(
                        signal_type="low_liquidity",
                        strength=1.0 - liquidity_score,
                        confidence=0.6,
                        timeframe="tick",
                        timestamp=tick_data.index[-1],
                        supporting_data={
                            'liquidity_score': liquidity_score,
                            'price_volatility': price_volatility,
                            'avg_volume': avg_volume
                        },
                        market_impact=1.0 - liquidity_score,
                        liquidity_score=liquidity_score
                    ))
                
                # High liquidity opportunity
                elif liquidity_score > 0.8:
                    signals.append(MicrostructureSignal(
                        signal_type="high_liquidity",
                        strength=liquidity_score,
                        confidence=0.7,
                        timeframe="tick",
                        timestamp=tick_data.index[-1],
                        supporting_data={
                            'liquidity_score': liquidity_score,
                            'price_volatility': price_volatility,
                            'avg_volume': avg_volume
                        },
                        market_impact=0.1,
                        liquidity_score=liquidity_score
                    ))
        
        return signals
    
    def _analyze_order_book_dynamics(self, order_book: Dict) -> List[MicrostructureSignal]:
        """Analyze order book dynamics and depth."""
        signals = []
        
        if 'bids' not in order_book or 'asks' not in order_book:
            return signals
        
        bids = order_book['bids'][:self.depth_levels]
        asks = order_book['asks'][:self.depth_levels]
        
        # Calculate order book imbalance
        total_bid_volume = sum(bid[1] for bid in bids)
        total_ask_volume = sum(ask[1] for ask in asks)
        total_volume = total_bid_volume + total_ask_volume
        
        if total_volume > 0:
            book_imbalance = (total_bid_volume - total_ask_volume) / total_volume
            
            if abs(book_imbalance) > 0.2:
                signals.append(MicrostructureSignal(
                    signal_type="order_book_imbalance",
                    strength=abs(book_imbalance),
                    confidence=0.8,
                    timeframe="tick",
                    timestamp=pd.Timestamp.now(),
                    supporting_data={
                        'bid_volume': total_bid_volume,
                        'ask_volume': total_ask_volume,
                        'imbalance': book_imbalance
                    },
                    market_impact=abs(book_imbalance) * 0.7,
                    liquidity_score=min(total_volume / 50000, 1.0)
                ))
        
        # Analyze order book depth
        if len(bids) >= 5 and len(asks) >= 5:
            # Calculate depth at different levels
            depth_levels = [1, 3, 5]
            depth_analysis = {}
            
            for level in depth_levels:
                bid_depth = sum(bid[1] for bid in bids[:level])
                ask_depth = sum(ask[1] for ask in asks[:level])
                depth_analysis[f'level_{level}'] = {
                    'bid_depth': bid_depth,
                    'ask_depth': ask_depth,
                    'total_depth': bid_depth + ask_depth
                }
            
            # Detect thin order book
            top_level_depth = depth_analysis['level_1']['total_depth']
            deep_level_depth = depth_analysis['level_5']['total_depth']
            
            if top_level_depth < deep_level_depth * 0.1:  # Top level has <10% of total depth
                signals.append(MicrostructureSignal(
                    signal_type="thin_order_book",
                    strength=1.0 - (top_level_depth / deep_level_depth),
                    confidence=0.7,
                    timeframe="tick",
                    timestamp=pd.Timestamp.now(),
                    supporting_data=depth_analysis,
                    market_impact=0.8,
                    liquidity_score=top_level_depth / deep_level_depth
                ))
        
        return signals
    
    def _update_microstructure_metrics(self, tick_data: pd.DataFrame, order_book: Optional[Dict]):
        """Update current microstructure metrics."""
        metrics = {}
        
        # Basic metrics
        if len(tick_data) > 0:
            metrics['last_price'] = tick_data['close'].iloc[-1]
            metrics['volume'] = tick_data['volume'].sum()
            metrics['trades_count'] = len(tick_data)
        
        # Spread metrics
        if 'bid' in tick_data.columns and 'ask' in tick_data.columns:
            spreads = tick_data['ask'] - tick_data['bid']
            metrics['avg_spread'] = spreads.mean()
            metrics['spread_volatility'] = spreads.std()
            metrics['current_spread'] = spreads.iloc[-1]
        
        # Order flow metrics
        if len(self.order_flow_buffer) > 0:
            recent_flows = list(self.order_flow_buffer)[-20:]
            buy_flows = [f for f in recent_flows if f.get('side') == 'buy']
            sell_flows = [f for f in recent_flows if f.get('side') == 'sell']
            
            metrics['buy_flow_ratio'] = len(buy_flows) / len(recent_flows) if recent_flows else 0.5
            metrics['order_flow_imbalance'] = (len(buy_flows) - len(sell_flows)) / len(recent_flows) if recent_flows else 0
        
        # Order book metrics
        if order_book:
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            
            if bids and asks:
                metrics['best_bid'] = bids[0][0]
                metrics['best_ask'] = asks[0][0]
                metrics['bid_ask_spread'] = asks[0][0] - bids[0][0]
                
                # Depth metrics
                metrics['bid_depth_5'] = sum(bid[1] for bid in bids[:5])
                metrics['ask_depth_5'] = sum(ask[1] for ask in asks[:5])
                metrics['total_depth_5'] = metrics['bid_depth_5'] + metrics['ask_depth_5']
        
        self.current_metrics = metrics
    
    def get_microstructure_summary(self) -> Dict[str, Any]:
        """Get current microstructure analysis summary."""
        return {
            'current_metrics': self.current_metrics,
            'buffer_sizes': {
                'tick_buffer': len(self.tick_buffer),
                'order_flow_buffer': len(self.order_flow_buffer),
                'spread_history': len(self.spread_history)
            },
            'analysis_config': {
                'depth_levels': self.depth_levels,
                'volume_window': self.volume_window,
                'spread_threshold': self.spread_threshold
            }
        }
    
    def detect_institutional_activity(self, tick_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect potential institutional trading activity."""
        institutional_signals = []
        
        if 'volume' not in tick_data.columns or len(tick_data) < 10:
            return institutional_signals
        
        # Large block trades
        avg_volume = tick_data['volume'].mean()
        large_trades = tick_data[tick_data['volume'] > avg_volume * 5]
        
        for _, trade in large_trades.iterrows():
            institutional_signals.append({
                'type': 'large_block_trade',
                'timestamp': trade.name,
                'volume': trade['volume'],
                'price': trade.get('close', trade.get('price', 0)),
                'volume_ratio': trade['volume'] / avg_volume,
                'confidence': min(trade['volume'] / avg_volume / 10, 1.0)
            })
        
        # Iceberg order detection (repeated similar-sized trades)
        volume_counts = tick_data['volume'].value_counts()
        repeated_volumes = volume_counts[volume_counts >= 3]
        
        for volume, count in repeated_volumes.items():
            if volume > avg_volume * 2:  # Large repeated volume
                institutional_signals.append({
                    'type': 'iceberg_order',
                    'volume': volume,
                    'repetitions': count,
                    'confidence': min(count / 10, 1.0)
                })
        
        return institutional_signals
