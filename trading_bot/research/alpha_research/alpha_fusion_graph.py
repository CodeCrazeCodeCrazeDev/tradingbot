"""
Alpha Fusion Graph
==================
Combine all signal types into unified alpha signal.

Features:
- Trend signal fusion
- Volume signal integration
- LOB signal processing
- News sentiment fusion
- Volatility signal combination
- Macro indicator integration
- Alternative data fusion
- Graph-based signal propagation

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from collections import deque
import threading

import numpy as np
import pandas as pd

try:
    from scipy import stats
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import dijkstra
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of signals in the fusion graph"""
    TREND = auto()
    MOMENTUM = auto()
    VOLUME = auto()
    LOB = auto()
    SENTIMENT = auto()
    VOLATILITY = auto()
    MACRO = auto()
    ALTERNATIVE = auto()
    TECHNICAL = auto()
    FUNDAMENTAL = auto()
    FLOW = auto()
    CORRELATION = auto()


class SignalQuality(Enum):
    """Signal quality levels"""
    EXCELLENT = auto()
    GOOD = auto()
    MODERATE = auto()
    POOR = auto()
    UNRELIABLE = auto()


@dataclass
class SignalNode:
    """Node in the alpha fusion graph"""
    node_id: str
    signal_type: SignalType
    name: str
    
    # Signal value
    value: float = 0.0
    confidence: float = 0.5
    quality: SignalQuality = SignalQuality.MODERATE
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""
    symbol: str = ""
    timeframe: str = ""
    
    # Graph connections
    incoming_edges: List[str] = field(default_factory=list)
    outgoing_edges: List[str] = field(default_factory=list)
    
    # Historical values
    history: List[float] = field(default_factory=list)
    max_history: int = 100


@dataclass
class SignalEdge:
    """Edge connecting signal nodes"""
    edge_id: str
    source_node: str
    target_node: str
    
    # Edge properties
    weight: float = 1.0
    correlation: float = 0.0
    lag: int = 0  # Time lag in bars
    
    # Relationship type
    relationship: str = "influences"  # influences, confirms, contradicts


@dataclass
class FusedAlpha:
    """Fused alpha signal output"""
    timestamp: datetime
    symbol: str
    
    # Fused signal
    alpha_value: float = 0.0
    confidence: float = 0.0
    direction: str = "neutral"  # long, short, neutral
    
    # Component breakdown
    trend_component: float = 0.0
    momentum_component: float = 0.0
    volume_component: float = 0.0
    sentiment_component: float = 0.0
    volatility_component: float = 0.0
    macro_component: float = 0.0
    
    # Signal quality
    quality: SignalQuality = SignalQuality.MODERATE
    agreement_score: float = 0.0
    
    # Contributing signals
    contributing_signals: Dict[str, float] = field(default_factory=dict)


class TrendSignalGenerator:
    """Generate trend-based signals"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def generate(self, data: pd.DataFrame) -> SignalNode:
        """Generate trend signal"""
        
        close = data['close']
        
        # Multiple timeframe trend
        sma_20 = close.rolling(20).mean()
        sma_50 = close.rolling(50).mean()
        sma_200 = close.rolling(200).mean()
        
        # Trend strength
        short_trend = (close.iloc[-1] - sma_20.iloc[-1]) / sma_20.iloc[-1] if len(close) >= 20 else 0
        medium_trend = (sma_20.iloc[-1] - sma_50.iloc[-1]) / sma_50.iloc[-1] if len(close) >= 50 else 0
        long_trend = (sma_50.iloc[-1] - sma_200.iloc[-1]) / sma_200.iloc[-1] if len(close) >= 200 else 0
        
        # Combined trend signal
        trend_signal = 0.5 * short_trend + 0.3 * medium_trend + 0.2 * long_trend
        trend_signal = np.clip(trend_signal * 10, -1, 1)
        
        # Confidence based on alignment
        alignment = 1 if (short_trend > 0) == (medium_trend > 0) == (long_trend > 0) else 0.5
        
        return SignalNode(
            node_id='trend_main',
            signal_type=SignalType.TREND,
            name='Multi-TF Trend',
            value=trend_signal,
            confidence=alignment,
            quality=SignalQuality.GOOD if alignment > 0.7 else SignalQuality.MODERATE
        )


class MomentumSignalGenerator:
    """Generate momentum-based signals"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def generate(self, data: pd.DataFrame) -> SignalNode:
        """Generate momentum signal"""
        
        close = data['close']
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9).mean()
        macd_hist = macd - macd_signal
        
        # ROC
        roc = close.pct_change(10)
        
        # Combined momentum
        rsi_signal = (rsi.iloc[-1] - 50) / 50 if len(rsi) > 0 else 0
        macd_signal_val = np.sign(macd_hist.iloc[-1]) * min(abs(macd_hist.iloc[-1]) / close.iloc[-1] * 100, 1) if len(macd_hist) > 0 else 0
        roc_signal = np.clip(roc.iloc[-1] * 10, -1, 1) if len(roc) > 0 else 0
        
        momentum_signal = 0.4 * rsi_signal + 0.4 * macd_signal_val + 0.2 * roc_signal
        
        # Confidence
        confidence = 0.7 if abs(momentum_signal) > 0.5 else 0.5
        
        return SignalNode(
            node_id='momentum_main',
            signal_type=SignalType.MOMENTUM,
            name='Combined Momentum',
            value=momentum_signal,
            confidence=confidence
        )


class VolumeSignalGenerator:
    """Generate volume-based signals"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def generate(self, data: pd.DataFrame) -> SignalNode:
        """Generate volume signal"""
        
        if 'volume' not in data.columns:
            return SignalNode(
                node_id='volume_main',
                signal_type=SignalType.VOLUME,
                name='Volume Signal',
                value=0,
                confidence=0.3
            )
        
        close = data['close']
        volume = data['volume']
        
        # Volume ratio
        vol_sma = volume.rolling(20).mean()
        vol_ratio = volume / vol_sma
        
        # OBV trend
        obv = (np.sign(close.diff()) * volume).cumsum()
        obv_sma = obv.rolling(20).mean()
        obv_signal = (obv.iloc[-1] - obv_sma.iloc[-1]) / (obv_sma.iloc[-1] + 1e-10) if len(obv) >= 20 else 0
        
        # Volume-price confirmation
        price_up = close.diff().iloc[-1] > 0 if len(close) > 1 else False
        vol_up = vol_ratio.iloc[-1] > 1 if len(vol_ratio) > 0 else False
        
        confirmation = 1 if price_up == vol_up else -0.5
        
        # Combined signal
        volume_signal = 0.5 * np.clip(obv_signal, -1, 1) + 0.5 * confirmation * min(vol_ratio.iloc[-1] - 1, 1)
        
        return SignalNode(
            node_id='volume_main',
            signal_type=SignalType.VOLUME,
            name='Volume Analysis',
            value=volume_signal,
            confidence=0.6 if abs(volume_signal) > 0.3 else 0.4
        )


class LOBSignalGenerator:
    """Generate LOB (Limit Order Book) signals"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def generate(
        self,
        bid_depth: float,
        ask_depth: float,
        spread: float,
        imbalance: float
    ) -> SignalNode:
        """Generate LOB signal"""
        
        # Depth ratio signal
        total_depth = bid_depth + ask_depth
        if total_depth > 0:
            depth_signal = (bid_depth - ask_depth) / total_depth
        else:
            depth_signal = 0
        
        # Spread signal (narrow spread = more confidence)
        spread_quality = 1 - min(spread / 0.001, 1)  # Normalize to 10 bps
        
        # Imbalance signal
        imbalance_signal = np.clip(imbalance, -1, 1)
        
        # Combined LOB signal
        lob_signal = 0.4 * depth_signal + 0.3 * imbalance_signal + 0.3 * np.sign(depth_signal) * spread_quality
        
        return SignalNode(
            node_id='lob_main',
            signal_type=SignalType.LOB,
            name='LOB Analysis',
            value=lob_signal,
            confidence=spread_quality
        )


class SentimentSignalGenerator:
    """Generate sentiment-based signals"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def generate(
        self,
        news_sentiment: float = 0,
        social_sentiment: float = 0,
        analyst_sentiment: float = 0
    ) -> SignalNode:
        """Generate sentiment signal"""
        
        # Weighted sentiment
        sentiment_signal = (
            0.4 * news_sentiment +
            0.3 * social_sentiment +
            0.3 * analyst_sentiment
        )
        
        # Confidence based on agreement
        sentiments = [news_sentiment, social_sentiment, analyst_sentiment]
        agreement = 1 - np.std(sentiments) if sentiments else 0.5
        
        return SignalNode(
            node_id='sentiment_main',
            signal_type=SignalType.SENTIMENT,
            name='Combined Sentiment',
            value=np.clip(sentiment_signal, -1, 1),
            confidence=agreement
        )


class VolatilitySignalGenerator:
    """Generate volatility-based signals"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def generate(self, data: pd.DataFrame) -> SignalNode:
        """Generate volatility signal"""
        
        close = data['close']
        returns = close.pct_change()
        
        # Current volatility
        current_vol = returns.iloc[-20:].std() * np.sqrt(252) if len(returns) >= 20 else 0.15
        
        # Historical volatility percentile
        if len(returns) >= 100:
            rolling_vol = returns.rolling(20).std() * np.sqrt(252)
            vol_percentile = stats.percentileofscore(rolling_vol.dropna(), current_vol) / 100
        else:
            vol_percentile = 0.5
        
        # Volatility regime signal
        # High vol = negative (reduce exposure), low vol = positive (increase exposure)
        vol_signal = 1 - 2 * vol_percentile
        
        # Volatility trend
        if len(returns) >= 40:
            vol_20 = returns.iloc[-20:].std()
            vol_40 = returns.iloc[-40:-20].std()
            vol_trend = (vol_20 - vol_40) / (vol_40 + 1e-10)
            vol_signal += -0.3 * np.clip(vol_trend * 10, -1, 1)
        
        return SignalNode(
            node_id='volatility_main',
            signal_type=SignalType.VOLATILITY,
            name='Volatility Regime',
            value=np.clip(vol_signal, -1, 1),
            confidence=0.7
        )


class MacroSignalGenerator:
    """Generate macro-based signals"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def generate(
        self,
        yield_curve_slope: float = 0,
        vix_level: float = 20,
        dollar_index: float = 0,
        credit_spread: float = 0
    ) -> SignalNode:
        """Generate macro signal"""
        
        # Yield curve signal (positive slope = bullish)
        yc_signal = np.clip(yield_curve_slope / 2, -1, 1)
        
        # VIX signal (low VIX = bullish)
        vix_signal = 1 - 2 * min(vix_level / 40, 1)
        
        # Dollar signal (strong dollar can be negative for risk assets)
        dollar_signal = -np.clip(dollar_index / 5, -1, 1)
        
        # Credit spread signal (tight spreads = bullish)
        credit_signal = -np.clip(credit_spread / 3, -1, 1)
        
        # Combined macro signal
        macro_signal = (
            0.3 * yc_signal +
            0.3 * vix_signal +
            0.2 * dollar_signal +
            0.2 * credit_signal
        )
        
        return SignalNode(
            node_id='macro_main',
            signal_type=SignalType.MACRO,
            name='Macro Environment',
            value=np.clip(macro_signal, -1, 1),
            confidence=0.6
        )


class AlternativeDataSignalGenerator:
    """Generate alternative data signals"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
    def generate(
        self,
        satellite_signal: float = 0,
        web_traffic_signal: float = 0,
        job_posting_signal: float = 0,
        credit_card_signal: float = 0
    ) -> SignalNode:
        """Generate alternative data signal"""
        
        # Weighted combination
        alt_signal = (
            0.25 * satellite_signal +
            0.25 * web_traffic_signal +
            0.25 * job_posting_signal +
            0.25 * credit_card_signal
        )
        
        # Confidence based on data availability
        signals = [satellite_signal, web_traffic_signal, job_posting_signal, credit_card_signal]
        available = sum(1 for s in signals if s != 0)
        confidence = available / 4
        
        return SignalNode(
            node_id='altdata_main',
            signal_type=SignalType.ALTERNATIVE,
            name='Alternative Data',
            value=np.clip(alt_signal, -1, 1),
            confidence=confidence
        )


class SignalGraph:
    """Graph structure for signal fusion"""
    
    def __init__(self):
        self.nodes: Dict[str, SignalNode] = {}
        self.edges: Dict[str, SignalEdge] = {}
        self.adjacency: Dict[str, List[str]] = {}
        
    def add_node(self, node: SignalNode):
        """Add a signal node"""
        self.nodes[node.node_id] = node
        if node.node_id not in self.adjacency:
            self.adjacency[node.node_id] = []
    
    def add_edge(self, edge: SignalEdge):
        """Add an edge between nodes"""
        self.edges[edge.edge_id] = edge
        
        if edge.source_node in self.adjacency:
            self.adjacency[edge.source_node].append(edge.target_node)
        
        # Update node connections
        if edge.source_node in self.nodes:
            self.nodes[edge.source_node].outgoing_edges.append(edge.edge_id)
        if edge.target_node in self.nodes:
            self.nodes[edge.target_node].incoming_edges.append(edge.edge_id)
    
    def propagate_signals(self, iterations: int = 3) -> Dict[str, float]:
        """Propagate signals through graph"""
        
        # Initialize values
        values = {node_id: node.value for node_id, node in self.nodes.items()}
        
        for _ in range(iterations):
            new_values = values.copy()
            
            for node_id, neighbors in self.adjacency.items():
                if not neighbors:
                    continue
                
                # Aggregate incoming signals
                incoming_sum = 0
                incoming_weight = 0
                
                for neighbor_id in neighbors:
                    edge_id = f"{node_id}_{neighbor_id}"
                    if edge_id in self.edges:
                        edge = self.edges[edge_id]
                        incoming_sum += values[neighbor_id] * edge.weight
                        incoming_weight += edge.weight
                
                if incoming_weight > 0:
                    # Blend with current value
                    propagated = incoming_sum / incoming_weight
                    new_values[node_id] = 0.7 * values[node_id] + 0.3 * propagated
            
            values = new_values
        
        return values
    
    def get_signal_path(self, source: str, target: str) -> List[str]:
        """Find path between signals"""
        
        if not SCIPY_AVAILABLE:
            return []
        
        # Build adjacency matrix
        node_ids = list(self.nodes.keys())
        n = len(node_ids)
        node_idx = {nid: i for i, nid in enumerate(node_ids)}
        
        adj_matrix = np.zeros((n, n))
        for edge in self.edges.values():
            if edge.source_node in node_idx and edge.target_node in node_idx:
                i, j = node_idx[edge.source_node], node_idx[edge.target_node]
                adj_matrix[i, j] = 1 / (edge.weight + 0.01)
        
        # Find shortest path
        sparse_adj = csr_matrix(adj_matrix)
        dist, predecessors = dijkstra(sparse_adj, indices=node_idx.get(source, 0), return_predecessors=True)
        
        # Reconstruct path
        path = []
        current = node_idx.get(target, 0)
        while current != node_idx.get(source, 0) and predecessors[current] >= 0:
            path.append(node_ids[current])
            current = predecessors[current]
        path.append(source)
        
        return path[:-1]


class AlphaFusionGraph:
    """
    Complete Alpha Fusion Graph.
    
    Combines:
    - Trend signals
    - Momentum signals
    - Volume signals
    - LOB signals
    - Sentiment signals
    - Volatility signals
    - Macro indicators
    - Alternative data
    
    Uses graph-based signal propagation for fusion.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Signal generators
        self.trend_generator = TrendSignalGenerator(config)
        self.momentum_generator = MomentumSignalGenerator(config)
        self.volume_generator = VolumeSignalGenerator(config)
        self.lob_generator = LOBSignalGenerator(config)
        self.sentiment_generator = SentimentSignalGenerator(config)
        self.volatility_generator = VolatilitySignalGenerator(config)
        self.macro_generator = MacroSignalGenerator(config)
        self.altdata_generator = AlternativeDataSignalGenerator(config)
        
        # Signal graph
        self.graph = SignalGraph()
        
        # Fusion weights
        self.fusion_weights = {
            SignalType.TREND: self.config.get('trend_weight', 0.20),
            SignalType.MOMENTUM: self.config.get('momentum_weight', 0.15),
            SignalType.VOLUME: self.config.get('volume_weight', 0.10),
            SignalType.LOB: self.config.get('lob_weight', 0.15),
            SignalType.SENTIMENT: self.config.get('sentiment_weight', 0.10),
            SignalType.VOLATILITY: self.config.get('volatility_weight', 0.10),
            SignalType.MACRO: self.config.get('macro_weight', 0.10),
            SignalType.ALTERNATIVE: self.config.get('altdata_weight', 0.10),
        }
        
        # History
        self.fusion_history: List[FusedAlpha] = []
        
        # Initialize graph structure
        self._initialize_graph()
        
        logger.info("AlphaFusionGraph initialized")
    
    def _initialize_graph(self):
        """Initialize graph structure with default edges"""
        
        # Define signal relationships
        relationships = [
            ('trend_main', 'momentum_main', 0.7, 'confirms'),
            ('momentum_main', 'volume_main', 0.6, 'confirms'),
            ('volume_main', 'lob_main', 0.8, 'confirms'),
            ('sentiment_main', 'trend_main', 0.5, 'influences'),
            ('volatility_main', 'trend_main', 0.4, 'influences'),
            ('macro_main', 'sentiment_main', 0.5, 'influences'),
            ('altdata_main', 'sentiment_main', 0.4, 'influences'),
        ]
        
        for source, target, weight, rel in relationships:
            edge = SignalEdge(
                edge_id=f"{source}_{target}",
                source_node=source,
                target_node=target,
                weight=weight,
                relationship=rel
            )
            self.graph.add_edge(edge)
    
    def generate_all_signals(
        self,
        market_data: pd.DataFrame,
        lob_data: Optional[Dict] = None,
        sentiment_data: Optional[Dict] = None,
        macro_data: Optional[Dict] = None,
        altdata: Optional[Dict] = None
    ) -> Dict[str, SignalNode]:
        """Generate all signal types"""
        
        signals = {}
        
        # Trend signal
        trend_signal = self.trend_generator.generate(market_data)
        signals['trend'] = trend_signal
        self.graph.add_node(trend_signal)
        
        # Momentum signal
        momentum_signal = self.momentum_generator.generate(market_data)
        signals['momentum'] = momentum_signal
        self.graph.add_node(momentum_signal)
        
        # Volume signal
        volume_signal = self.volume_generator.generate(market_data)
        signals['volume'] = volume_signal
        self.graph.add_node(volume_signal)
        
        # LOB signal
        if lob_data:
            lob_signal = self.lob_generator.generate(
                lob_data.get('bid_depth', 0),
                lob_data.get('ask_depth', 0),
                lob_data.get('spread', 0.0001),
                lob_data.get('imbalance', 0)
            )
        else:
            lob_signal = SignalNode(
                node_id='lob_main',
                signal_type=SignalType.LOB,
                name='LOB Signal',
                value=0,
                confidence=0.3
            )
        signals['lob'] = lob_signal
        self.graph.add_node(lob_signal)
        
        # Sentiment signal
        if sentiment_data:
            sentiment_signal = self.sentiment_generator.generate(
                sentiment_data.get('news', 0),
                sentiment_data.get('social', 0),
                sentiment_data.get('analyst', 0)
            )
        else:
            sentiment_signal = SignalNode(
                node_id='sentiment_main',
                signal_type=SignalType.SENTIMENT,
                name='Sentiment Signal',
                value=0,
                confidence=0.3
            )
        signals['sentiment'] = sentiment_signal
        self.graph.add_node(sentiment_signal)
        
        # Volatility signal
        volatility_signal = self.volatility_generator.generate(market_data)
        signals['volatility'] = volatility_signal
        self.graph.add_node(volatility_signal)
        
        # Macro signal
        if macro_data:
            macro_signal = self.macro_generator.generate(
                macro_data.get('yield_curve', 0),
                macro_data.get('vix', 20),
                macro_data.get('dollar_index', 0),
                macro_data.get('credit_spread', 0)
            )
        else:
            macro_signal = SignalNode(
                node_id='macro_main',
                signal_type=SignalType.MACRO,
                name='Macro Signal',
                value=0,
                confidence=0.3
            )
        signals['macro'] = macro_signal
        self.graph.add_node(macro_signal)
        
        # Alternative data signal
        if altdata:
            altdata_signal = self.altdata_generator.generate(
                altdata.get('satellite', 0),
                altdata.get('web_traffic', 0),
                altdata.get('job_postings', 0),
                altdata.get('credit_card', 0)
            )
        else:
            altdata_signal = SignalNode(
                node_id='altdata_main',
                signal_type=SignalType.ALTERNATIVE,
                name='AltData Signal',
                value=0,
                confidence=0.3
            )
        signals['altdata'] = altdata_signal
        self.graph.add_node(altdata_signal)
        
        return signals
    
    def fuse_signals(
        self,
        signals: Dict[str, SignalNode],
        symbol: str = ""
    ) -> FusedAlpha:
        """Fuse all signals into unified alpha"""
        
        # Propagate signals through graph
        propagated_values = self.graph.propagate_signals(iterations=3)
        
        # Calculate weighted fusion
        weighted_sum = 0
        total_weight = 0
        
        component_values = {}
        
        for signal_name, signal in signals.items():
            signal_type = signal.signal_type
            weight = self.fusion_weights.get(signal_type, 0.1)
            
            # Use propagated value if available
            value = propagated_values.get(signal.node_id, signal.value)
            
            # Confidence-adjusted weight
            adjusted_weight = weight * signal.confidence
            
            weighted_sum += value * adjusted_weight
            total_weight += adjusted_weight
            
            # Store component
            component_values[signal_type.name.lower()] = value
        
        # Final fused alpha
        if total_weight > 0:
            alpha_value = weighted_sum / total_weight
        else:
            alpha_value = 0
        
        # Determine direction
        if alpha_value > 0.2:
            direction = 'long'
        elif alpha_value < -0.2:
            direction = 'short'
        else:
            direction = 'neutral'
        
        # Calculate confidence
        confidences = [s.confidence for s in signals.values()]
        avg_confidence = np.mean(confidences) if confidences else 0.5
        
        # Calculate agreement
        values = [s.value for s in signals.values()]
        if values:
            positive = sum(1 for v in values if v > 0)
            negative = sum(1 for v in values if v < 0)
            agreement = max(positive, negative) / len(values)
        else:
            agreement = 0.5
        
        # Determine quality
        if avg_confidence > 0.7 and agreement > 0.7:
            quality = SignalQuality.EXCELLENT
        elif avg_confidence > 0.5 and agreement > 0.5:
            quality = SignalQuality.GOOD
        elif avg_confidence > 0.3:
            quality = SignalQuality.MODERATE
        else:
            quality = SignalQuality.POOR
        
        fused = FusedAlpha(
            timestamp=datetime.now(),
            symbol=symbol,
            alpha_value=alpha_value,
            confidence=avg_confidence,
            direction=direction,
            trend_component=component_values.get('trend', 0),
            momentum_component=component_values.get('momentum', 0),
            volume_component=component_values.get('volume', 0),
            sentiment_component=component_values.get('sentiment', 0),
            volatility_component=component_values.get('volatility', 0),
            macro_component=component_values.get('macro', 0),
            quality=quality,
            agreement_score=agreement,
            contributing_signals={k: v.value for k, v in signals.items()}
        )
        
        self.fusion_history.append(fused)
        
        return fused
    
    def generate_and_fuse(
        self,
        market_data: pd.DataFrame,
        symbol: str = "",
        lob_data: Optional[Dict] = None,
        sentiment_data: Optional[Dict] = None,
        macro_data: Optional[Dict] = None,
        altdata: Optional[Dict] = None
    ) -> FusedAlpha:
        """Generate all signals and fuse them"""
        
        signals = self.generate_all_signals(
            market_data, lob_data, sentiment_data, macro_data, altdata
        )
        
        return self.fuse_signals(signals, symbol)
    
    def update_weights(self, new_weights: Dict[SignalType, float]):
        """Update fusion weights"""
        self.fusion_weights.update(new_weights)
    
    def get_signal_breakdown(self) -> Dict[str, Any]:
        """Get breakdown of current signals"""
        
        if not self.fusion_history:
            return {}
        
        latest = self.fusion_history[-1]
        
        return {
            'alpha_value': latest.alpha_value,
            'direction': latest.direction,
            'confidence': latest.confidence,
            'quality': latest.quality.name,
            'components': {
                'trend': latest.trend_component,
                'momentum': latest.momentum_component,
                'volume': latest.volume_component,
                'sentiment': latest.sentiment_component,
                'volatility': latest.volatility_component,
                'macro': latest.macro_component
            },
            'agreement': latest.agreement_score,
            'contributing_signals': latest.contributing_signals
        }


# Factory function
def create_fusion_graph(config: Optional[Dict] = None) -> AlphaFusionGraph:
    """Create and return an AlphaFusionGraph instance"""
    return AlphaFusionGraph(config)
