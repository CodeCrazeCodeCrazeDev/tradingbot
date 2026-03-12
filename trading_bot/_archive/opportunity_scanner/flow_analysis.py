import asyncio
"""
Order Flow Analysis Module
Detects institutional flow and smart money movements
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
from collections import deque
import numpy
import pandas

logger = logging.getLogger(__name__)

class FlowType(Enum):
    """Types of order flow"""
    INSTITUTIONAL = "institutional"
    RETAIL = "retail"
    ALGORITHMIC = "algorithmic"
    DARK_POOL = "dark_pool"
    WHALE = "whale"

@dataclass
class FlowOpportunity:
    """Represents an order flow opportunity"""
    opportunity_id: str
    symbol: str
    flow_type: FlowType
    direction: str  # BUY/SELL
    magnitude: float
    confidence: float
    expected_impact: float
    time_horizon: float
    entry_signal: Dict[str, Any]
    metadata: Dict[str, Any]

class OrderFlowImbalanceDetector:
    """
    Detects significant order flow imbalances
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_imbalance = self.config.get('min_imbalance', 0.6)
        self.lookback_window = self.config.get('lookback_window', 100)
        
        # Flow tracking
        self.flow_history = {}
        self.cumulative_delta = {}
        self.aggressor_ratio = {}
        
    async def detect_flow_imbalances(self, market_data: Dict) -> List[FlowOpportunity]:
        """
        Detect order flow imbalances that signal directional moves
        """
        opportunities = []
        
        for symbol, data in market_data.items():
            if 'trades' not in data:
                continue
            
            # Analyze trade flow
            flow_analysis = self._analyze_flow(data['trades'])
            
            # Check for significant imbalance
            if abs(flow_analysis['imbalance']) > self.min_imbalance:
                opportunity = self._create_flow_opportunity(symbol, flow_analysis, data)
                opportunities.append(opportunity)
        
        return opportunities
    
    def _analyze_flow(self, trades: List[Dict]) -> Dict:
        """Analyze order flow from trades"""
        if not trades:
            return {'imbalance': 0}
        
        # Separate buy and sell volume
        buy_volume = sum(t['size'] for t in trades if t.get('aggressor') == 'buy')
        sell_volume = sum(t['size'] for t in trades if t.get('aggressor') == 'sell')
        
        total_volume = buy_volume + sell_volume
        
        if total_volume == 0:
            return {'imbalance': 0}
        
        # Calculate metrics
        imbalance = (buy_volume - sell_volume) / total_volume
        
        # Analyze trade sizes for institutional detection
        trade_sizes = [t['size'] for t in trades]
        avg_size = np.mean(trade_sizes)
        large_trades = [s for s in trade_sizes if s > avg_size * 3]
        
        # Detect clustering (institutional footprint)
        clustering = self._detect_trade_clustering(trades)
        
        return {
            'imbalance': imbalance,
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'total_volume': total_volume,
            'avg_trade_size': avg_size,
            'large_trade_ratio': len(large_trades) / len(trades) if trades else 0,
            'clustering_score': clustering,
            'direction': 'BUY' if imbalance > 0 else 'SELL'
        }
    
    def _detect_trade_clustering(self, trades: List[Dict]) -> float:
        """Detect if trades are clustered (institutional activity)"""
        if len(trades) < 10:
            return 0
        
        # Time clustering
        timestamps = [t['timestamp'] for t in trades if 'timestamp' in t]
        if len(timestamps) < 2:
            return 0
        
        # Calculate time between trades
        time_diffs = []
        for i in range(1, len(timestamps)):
            diff = (timestamps[i] - timestamps[i-1]).total_seconds()
            time_diffs.append(diff)
        
        # Low variance in time differences suggests algorithmic/institutional
        if time_diffs:
            cv = np.std(time_diffs) / np.mean(time_diffs) if np.mean(time_diffs) > 0 else 1
            clustering = 1 - min(1, cv)  # Lower CV = higher clustering
        else:
            clustering = 0
        
        return clustering
    
    def _create_flow_opportunity(self, symbol: str, flow_analysis: Dict, 
                                market_data: Dict) -> FlowOpportunity:
        """Create order flow opportunity"""
        # Determine flow type
        if flow_analysis['large_trade_ratio'] > 0.3:
            flow_type = FlowType.INSTITUTIONAL
        elif flow_analysis['clustering_score'] > 0.7:
            flow_type = FlowType.ALGORITHMIC
        else:
            flow_type = FlowType.RETAIL
        
        # Calculate expected impact
        impact = abs(flow_analysis['imbalance']) * 0.01  # 1% per unit imbalance
        
        return FlowOpportunity(
            opportunity_id=f"FLOW_{symbol}_{datetime.now().timestamp()}",
            symbol=symbol,
            flow_type=flow_type,
            direction=flow_analysis['direction'],
            magnitude=abs(flow_analysis['imbalance']),
            confidence=min(0.9, abs(flow_analysis['imbalance'])),
            expected_impact=impact,
            time_horizon=1.0,  # 1 hour
            entry_signal={
                'trigger': 'immediate',
                'price': market_data['price'],
                'size': flow_analysis['total_volume'] * 0.01
            },
            metadata=flow_analysis
        )


class VolumeProfileAnalyzer:
    """
    Analyzes volume profile to identify key levels
    """
    
    def __init__(self):
        self.profile_bins = 50
        self.value_area_percentage = 0.7
        
    def analyze_volume_profile(self, price_data: List[float], 
                              volume_data: List[float]) -> Dict:
        """
        Analyze volume profile to find high volume nodes
        """
        if not price_data or not volume_data:
            return {}
        
        # Create volume profile
        price_min = min(price_data)
        price_max = max(price_data)
        
        # Create bins
        bins = np.linspace(price_min, price_max, self.profile_bins)
        volume_profile = np.zeros(len(bins) - 1)
        
        # Accumulate volume in bins
        for price, volume in zip(price_data, volume_data):
            bin_idx = np.digitize(price, bins) - 1
            if 0 <= bin_idx < len(volume_profile):
                volume_profile[bin_idx] += volume
        
        # Find Point of Control (POC)
        poc_idx = np.argmax(volume_profile)
        poc_price = (bins[poc_idx] + bins[poc_idx + 1]) / 2
        
        # Calculate Value Area
        value_area = self._calculate_value_area(bins, volume_profile)
        
        # Find High Volume Nodes (HVN) and Low Volume Nodes (LVN)
        hvn_levels = self._find_hvn_levels(bins, volume_profile)
        lvn_levels = self._find_lvn_levels(bins, volume_profile)
        
        return {
            'poc': poc_price,
            'value_area_high': value_area['high'],
            'value_area_low': value_area['low'],
            'hvn_levels': hvn_levels,
            'lvn_levels': lvn_levels,
            'total_volume': np.sum(volume_profile),
            'profile': list(zip(bins[:-1], volume_profile))
        }
    
    def _calculate_value_area(self, bins: np.ndarray, 
                             volume_profile: np.ndarray) -> Dict:
        """Calculate value area (70% of volume)"""
        total_volume = np.sum(volume_profile)
        target_volume = total_volume * self.value_area_percentage
        
        # Start from POC and expand
        poc_idx = np.argmax(volume_profile)
        accumulated_volume = volume_profile[poc_idx]
        
        low_idx = poc_idx
        high_idx = poc_idx
        
        # Expand until we reach target volume
        while accumulated_volume < target_volume:
            # Check which side to expand
            expand_up = expand_down = False
            
            if high_idx < len(volume_profile) - 1:
                expand_up = True
                up_volume = volume_profile[high_idx + 1]
            else:
                up_volume = 0
            
            if low_idx > 0:
                expand_down = True
                down_volume = volume_profile[low_idx - 1]
            else:
                down_volume = 0
            
            # Expand in direction with more volume
            if expand_up and (not expand_down or up_volume > down_volume):
                high_idx += 1
                accumulated_volume += up_volume
            elif expand_down:
                low_idx -= 1
                accumulated_volume += down_volume
            else:
                break
        
        return {
            'high': bins[min(high_idx + 1, len(bins) - 1)],
            'low': bins[low_idx]
        }
    
    def _find_hvn_levels(self, bins: np.ndarray, 
                        volume_profile: np.ndarray) -> List[float]:
        """Find High Volume Node levels"""
        # Find peaks in volume profile
        threshold = np.percentile(volume_profile, 75)
        hvn_indices = np.where(volume_profile > threshold)[0]
        
        hvn_levels = []
        for idx in hvn_indices:
            price = (bins[idx] + bins[idx + 1]) / 2
            hvn_levels.append(price)
        
        return hvn_levels
    
    def _find_lvn_levels(self, bins: np.ndarray, 
                        volume_profile: np.ndarray) -> List[float]:
        """Find Low Volume Node levels (potential breakout areas)"""
        # Find valleys in volume profile
        threshold = np.percentile(volume_profile, 25)
        lvn_indices = np.where(volume_profile < threshold)[0]
        
        lvn_levels = []
        for idx in lvn_indices:
            price = (bins[idx] + bins[idx + 1]) / 2
            lvn_levels.append(price)
        
        return lvn_levels


class DarkPoolMonitor:
    """
    Monitors dark pool activity and block trades
    """
    
    def __init__(self):
        self.min_block_size = 10000
        self.dark_pool_sources = ['ATS', 'DARK', 'HIDDEN']
        
    async def scan_dark_pools(self, market_data: Dict) -> List[FlowOpportunity]:
        """
        Scan for dark pool prints and large blocks
        """
        opportunities = []
        
        for symbol, data in market_data.items():
            if 'dark_pool_trades' not in data:
                continue
            
            # Analyze dark pool activity
            dark_analysis = self._analyze_dark_activity(data['dark_pool_trades'])
            
            if dark_analysis['significant']:
                opportunity = self._create_dark_pool_opportunity(symbol, dark_analysis)
                opportunities.append(opportunity)
        
        return opportunities
    
    def _analyze_dark_activity(self, dark_trades: List[Dict]) -> Dict:
        """Analyze dark pool trades"""
        if not dark_trades:
            return {'significant': False}
        
        # Filter for large blocks
        blocks = [t for t in dark_trades if t.get('size', 0) > self.min_block_size]
        
        if not blocks:
            return {'significant': False}
        
        # Analyze direction
        buy_blocks = sum(b['size'] for b in blocks if b.get('side') == 'buy')
        sell_blocks = sum(b['size'] for b in blocks if b.get('side') == 'sell')
        
        total_block_volume = buy_blocks + sell_blocks
        
        # Check for significance
        if total_block_volume < self.min_block_size * 5:
            return {'significant': False}
        
        imbalance = (buy_blocks - sell_blocks) / total_block_volume if total_block_volume > 0 else 0
        
        return {
            'significant': True,
            'total_volume': total_block_volume,
            'buy_volume': buy_blocks,
            'sell_volume': sell_blocks,
            'imbalance': imbalance,
            'block_count': len(blocks),
            'avg_block_size': total_block_volume / len(blocks),
            'direction': 'BUY' if imbalance > 0 else 'SELL'
        }
    
    def _create_dark_pool_opportunity(self, symbol: str, 
                                     analysis: Dict) -> FlowOpportunity:
        """Create dark pool opportunity"""
        return FlowOpportunity(
            opportunity_id=f"DARK_{symbol}_{datetime.now().timestamp()}",
            symbol=symbol,
            flow_type=FlowType.DARK_POOL,
            direction=analysis['direction'],
            magnitude=abs(analysis['imbalance']),
            confidence=0.8,  # Dark pools are typically informed
            expected_impact=abs(analysis['imbalance']) * 0.02,  # 2% per unit
            time_horizon=24.0,  # Dark pool impact is slower
            entry_signal={
                'trigger': 'confirmed',
                'wait_for_confirmation': True
            },
            metadata=analysis
        )


class WhaleTracker:
    """
    Tracks whale wallets and large player activity
    """
    
    def __init__(self):
        self.whale_threshold = 1000000  # $1M
        self.known_whales = {}
        self.whale_patterns = {}
        
    async def track_whale_activity(self, market_data: Dict) -> List[FlowOpportunity]:
        """
        Track whale movements and positions
        """
        opportunities = []
        
        for symbol, data in market_data.items():
            # Check on-chain data for crypto
            if 'on_chain' in data:
                whale_activity = self._analyze_on_chain(data['on_chain'])
                
                if whale_activity['active']:
                    opportunity = self._create_whale_opportunity(symbol, whale_activity)
                    opportunities.append(opportunity)
            
            # Check large trades
            if 'trades' in data:
                whale_trades = self._identify_whale_trades(data['trades'], data['price'])
                
                if whale_trades:
                    opportunity = self._create_whale_trade_opportunity(symbol, whale_trades, data)
                    opportunities.append(opportunity)
        
        return opportunities
    
    def _analyze_on_chain(self, on_chain_data: Dict) -> Dict:
        """Analyze on-chain data for whale activity"""
        # Exchange inflows/outflows
        exchange_flow = on_chain_data.get('exchange_netflow', 0)
        
        # Large wallet movements
        large_transfers = on_chain_data.get('large_transfers', [])
        
        # Accumulation/distribution
        if exchange_flow < -self.whale_threshold:
            # Large outflows (accumulation)
            return {
                'active': True,
                'type': 'accumulation',
                'magnitude': abs(exchange_flow),
                'confidence': 0.85
            }
        elif exchange_flow > self.whale_threshold:
            # Large inflows (distribution)
            return {
                'active': True,
                'type': 'distribution',
                'magnitude': abs(exchange_flow),
                'confidence': 0.85
            }
        
        return {'active': False}
    
    def _identify_whale_trades(self, trades: List[Dict], price: float) -> List[Dict]:
        """Identify whale-sized trades"""
        whale_trades = []
        
        for trade in trades:
            trade_value = trade.get('size', 0) * price
            
            if trade_value > self.whale_threshold:
                whale_trades.append({
                    'size': trade['size'],
                    'value': trade_value,
                    'side': trade.get('side', 'unknown'),
                    'timestamp': trade.get('timestamp')
                })
        
        return whale_trades
    
    def _create_whale_opportunity(self, symbol: str, 
                                 whale_activity: Dict) -> FlowOpportunity:
        """Create whale activity opportunity"""
        direction = 'BUY' if whale_activity['type'] == 'accumulation' else 'SELL'
        
        return FlowOpportunity(
            opportunity_id=f"WHALE_{symbol}_{datetime.now().timestamp()}",
            symbol=symbol,
            flow_type=FlowType.WHALE,
            direction=direction,
            magnitude=whale_activity['magnitude'] / self.whale_threshold,
            confidence=whale_activity['confidence'],
            expected_impact=0.05,  # 5% impact for whale moves
            time_horizon=72.0,  # 3 days for whale impact
            entry_signal={
                'trigger': 'follow_whale',
                'position_size': 'scaled'
            },
            metadata=whale_activity
        )
    
    def _create_whale_trade_opportunity(self, symbol: str, whale_trades: List[Dict], 
                                       market_data: Dict) -> FlowOpportunity:
        """Create opportunity from whale trades"""
        # Aggregate whale activity
        buy_value = sum(t['value'] for t in whale_trades if t['side'] == 'buy')
        sell_value = sum(t['value'] for t in whale_trades if t['side'] == 'sell')
        
        total_value = buy_value + sell_value
        
        if total_value == 0:
            return None
        
        imbalance = (buy_value - sell_value) / total_value
        
        return FlowOpportunity(
            opportunity_id=f"WHALE_TRADE_{symbol}_{datetime.now().timestamp()}",
            symbol=symbol,
            flow_type=FlowType.WHALE,
            direction='BUY' if imbalance > 0 else 'SELL',
            magnitude=abs(imbalance),
            confidence=0.75,
            expected_impact=abs(imbalance) * 0.03,
            time_horizon=48.0,
            entry_signal={
                'trigger': 'whale_trade',
                'follow_size': total_value * 0.001  # Follow with 0.1% of whale size
            },
            metadata={
                'whale_trades': whale_trades,
                'total_whale_value': total_value,
                'imbalance': imbalance
            }
        )
