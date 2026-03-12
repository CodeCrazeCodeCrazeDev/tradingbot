"""
Swarm Management for Hivemind
============================================================

Swarms are groups of related nodes that collaborate on specific
aspects of trading analysis. Each swarm has emergent behavior
that arises from node interactions.
"""

import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from enum import Enum

from .core import (
    HiveNode,
    NodeType,
    NodeState,
    NodeVote,
    SwarmSignal,
    SignalDirection,
)
from .nodes import create_node

logger = logging.getLogger(__name__)


class SwarmType(Enum):
    """Types of swarms"""
    TECHNICAL = "technical"      # Technical analysis nodes
    FUNDAMENTAL = "fundamental"  # Fundamental analysis nodes
    SENTIMENT = "sentiment"      # Sentiment analysis nodes
    RISK = "risk"               # Risk management nodes
    EXECUTION = "execution"     # Execution optimization nodes
    MACRO = "macro"             # Macroeconomic nodes
    QUANT = "quant"             # Quantitative nodes


@dataclass
class SwarmConfig:
    """Configuration for a swarm"""
    swarm_type: SwarmType
    node_count: int = 3
    node_types: List[NodeType] = field(default_factory=list)
    min_consensus: float = 0.6  # Minimum agreement for swarm signal
    enable_communication: bool = True
    enable_learning: bool = True


class Swarm:
    """
    A swarm of related nodes that collaborate.
    
    Swarms exhibit emergent behavior:
    - Nodes communicate and share information
    - Collective signals emerge from individual votes
    - Swarm adapts based on performance
    """
    
    def __init__(self, config: SwarmConfig):
        self.config = config
        self.swarm_type = config.swarm_type
        self.swarm_id = f"swarm_{config.swarm_type.value}"
        
        # Initialize nodes
        self.nodes: List[HiveNode] = []
        self._initialize_nodes()
        
        # Swarm state
        self.last_signal: Optional[SwarmSignal] = None
        self.signal_history: List[SwarmSignal] = []
        
        # Performance tracking
        self.total_signals = 0
        self.correct_signals = 0
    
    def _initialize_nodes(self) -> None:
        """Initialize swarm nodes"""
        node_types = self.config.node_types
        
        if not node_types:
            # Default node types based on swarm type
            default_types = {
                SwarmType.TECHNICAL: [NodeType.TECHNICAL, NodeType.PATTERN, NodeType.MOMENTUM],
                SwarmType.FUNDAMENTAL: [NodeType.FUNDAMENTAL, NodeType.MACRO],
                SwarmType.SENTIMENT: [NodeType.SENTIMENT, NodeType.NEWS, NodeType.SOCIAL],
                SwarmType.RISK: [NodeType.RISK, NodeType.VOLATILITY],
                SwarmType.EXECUTION: [NodeType.EXECUTION, NodeType.MICROSTRUCTURE],
                SwarmType.MACRO: [NodeType.MACRO, NodeType.CORRELATION],
                SwarmType.QUANT: [NodeType.QUANT, NodeType.MEAN_REVERSION, NodeType.MOMENTUM],
            }
            node_types = default_types.get(self.swarm_type, [NodeType.TECHNICAL])
        
        # Create nodes
        for i in range(self.config.node_count):
            node_type = node_types[i % len(node_types)]
            node = create_node(
                node_type,
                node_id=f"{self.swarm_id}_node_{i}",
            )
            self.nodes.append(node)
        
        logger.info(f"Initialized swarm {self.swarm_id} with {len(self.nodes)} nodes")
    
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> SwarmSignal:
        """
        Have all nodes analyze and produce a swarm signal.
        """
        logger.debug(f"Swarm {self.swarm_id} analyzing {symbol}")
        
        # Collect votes from all nodes in parallel
        tasks = [node.analyze(symbol, market_data) for node in self.nodes]
        votes = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        valid_votes: List[NodeVote] = []
        for vote in votes:
            if isinstance(vote, NodeVote):
                valid_votes.append(vote)
            elif isinstance(vote, Exception):
                logger.warning(f"Node error in swarm {self.swarm_id}: {vote}")
        
        if not valid_votes:
            return self._neutral_signal("No valid votes from nodes")
        
        # Enable node communication
        if self.config.enable_communication:
            await self._facilitate_communication(valid_votes)
        
        # Aggregate votes into swarm signal
        signal = self._aggregate_votes(valid_votes)
        
        self.last_signal = signal
        self.signal_history.append(signal)
        self.total_signals += 1
        
        # Trim history
        if len(self.signal_history) > 100:
            self.signal_history = self.signal_history[-50:]
        
        return signal
    
    async def _facilitate_communication(self, votes: List[NodeVote]) -> None:
        """Allow nodes to communicate and potentially adjust opinions"""
        # Share votes between nodes
        for node in self.nodes:
            for vote in votes:
                if vote.node_id != node.node_id:
                    node.receive_message({
                        'from': vote.node_id,
                        'type': 'share_vote',
                        'data': vote.to_dict(),
                    })
        
        # Process messages
        for node in self.nodes:
            node.process_messages()
    
    def _aggregate_votes(self, votes: List[NodeVote]) -> SwarmSignal:
        """Aggregate individual votes into a swarm signal"""
        if not votes:
            return self._neutral_signal("No votes to aggregate")
        
        # Calculate weighted average
        total_weight = sum(v.weight * v.confidence for v in votes)
        if total_weight == 0:
            return self._neutral_signal("Zero total weight")
        
        weighted_sum = sum(v.weighted_score for v in votes)
        avg_signal = weighted_sum / total_weight if total_weight > 0 else 0
        
        # Calculate consensus (how much nodes agree)
        directions = [v.direction.to_numeric() for v in votes]
        if len(directions) > 1:
            variance = sum((d - avg_signal) ** 2 for d in directions) / len(directions)
            consensus = max(0, 1 - variance)
        else:
            consensus = 1.0
        
        # Determine signal direction
        direction = SignalDirection.from_numeric(avg_signal)
        
        # Calculate strength
        strength = min(abs(avg_signal) * consensus, 1.0)
        
        # Build description
        bullish_count = sum(1 for v in votes if v.direction.to_numeric() > 0.1)
        bearish_count = sum(1 for v in votes if v.direction.to_numeric() < -0.1)
        neutral_count = len(votes) - bullish_count - bearish_count
        
        description = f"{bullish_count} bullish, {bearish_count} bearish, {neutral_count} neutral"
        
        return SwarmSignal(
            signal_type=f"{self.swarm_type.value}_consensus",
            direction=direction,
            strength=strength,
            source_nodes=[v.node_id for v in votes],
            description=description,
        )
    
    def _neutral_signal(self, reason: str) -> SwarmSignal:
        """Create a neutral signal"""
        return SwarmSignal(
            signal_type=f"{self.swarm_type.value}_neutral",
            direction=SignalDirection.NEUTRAL,
            strength=0.0,
            source_nodes=[],
            description=reason,
        )
    
    def record_outcome(self, was_correct: bool, profit: float) -> None:
        """Record outcome for all nodes"""
        if was_correct:
            self.correct_signals += 1
        
        for node in self.nodes:
            node.record_outcome(was_correct, profit / len(self.nodes))
    
    def get_node_votes(self) -> List[NodeVote]:
        """Get last votes from all nodes"""
        return [node.last_vote for node in self.nodes if node.last_vote]
    
    def get_status(self) -> Dict[str, Any]:
        """Get swarm status"""
        return {
            'swarm_id': self.swarm_id,
            'swarm_type': self.swarm_type.value,
            'node_count': len(self.nodes),
            'total_signals': self.total_signals,
            'accuracy': self.correct_signals / self.total_signals if self.total_signals > 0 else 0,
            'last_signal': self.last_signal.to_dict() if self.last_signal else None,
            'nodes': [node.get_status() for node in self.nodes],
        }


class SwarmManager:
    """
    Manages multiple swarms and their interactions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.swarms: Dict[SwarmType, Swarm] = {}
        
        # Initialize default swarms
        self._initialize_default_swarms()
    
    def _initialize_default_swarms(self) -> None:
        """Initialize default swarm configuration"""
        default_configs = [
            SwarmConfig(SwarmType.TECHNICAL, node_count=3),
            SwarmConfig(SwarmType.FUNDAMENTAL, node_count=2),
            SwarmConfig(SwarmType.SENTIMENT, node_count=2),
            SwarmConfig(SwarmType.RISK, node_count=2),
            SwarmConfig(SwarmType.EXECUTION, node_count=2),
            SwarmConfig(SwarmType.MACRO, node_count=2),
            SwarmConfig(SwarmType.QUANT, node_count=2),
        ]
        
        for config in default_configs:
            self.swarms[config.swarm_type] = Swarm(config)
    
    async def analyze_all(self, symbol: str, market_data: Dict[str, Any]) -> Dict[SwarmType, SwarmSignal]:
        """Have all swarms analyze in parallel"""
        tasks = {
            swarm_type: swarm.analyze(symbol, market_data)
            for swarm_type, swarm in self.swarms.items()
        }
        
        results = {}
        for swarm_type, task in tasks.items():
            try:
                results[swarm_type] = await task
            except Exception as e:
                logger.error(f"Swarm {swarm_type.value} error: {e}")
                results[swarm_type] = SwarmSignal(
                    signal_type=f"{swarm_type.value}_error",
                    direction=SignalDirection.NEUTRAL,
                    strength=0.0,
                    source_nodes=[],
                    description=f"Error: {str(e)}",
                )
        
        return results
    
    def get_all_votes(self) -> List[NodeVote]:
        """Get all node votes across all swarms"""
        votes = []
        for swarm in self.swarms.values():
            votes.extend(swarm.get_node_votes())
        return votes
    
    def record_outcome(self, was_correct: bool, profit: float) -> None:
        """Record outcome for all swarms"""
        for swarm in self.swarms.values():
            swarm.record_outcome(was_correct, profit)
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all swarms"""
        return {
            'swarm_count': len(self.swarms),
            'total_nodes': sum(len(s.nodes) for s in self.swarms.values()),
            'swarms': {st.value: s.get_status() for st, s in self.swarms.items()},
        }
