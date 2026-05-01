"""
Hivemind Core Types and Base Classes
============================================================

Core data structures and base classes for the Hivemind system.
"""

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of hivemind nodes"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    RISK = "risk"
    EXECUTION = "execution"
    MACRO = "macro"
    MICROSTRUCTURE = "microstructure"
    QUANT = "quant"
    PATTERN = "pattern"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    VOLATILITY = "volatility"
    CORRELATION = "correlation"
    NEWS = "news"
    SOCIAL = "social"
    ORDER_FLOW = "order_flow"


class NodeState(Enum):
    """State of a hivemind node"""
    IDLE = "idle"
    ANALYZING = "analyzing"
    VOTING = "voting"
    LEARNING = "learning"
    DISABLED = "disabled"
    ERROR = "error"


class ConsensusMethod(Enum):
    """Methods for reaching consensus"""
    MAJORITY_VOTE = "majority_vote"           # Simple majority
    WEIGHTED_VOTE = "weighted_vote"           # Weighted by performance
    UNANIMOUS = "unanimous"                    # All must agree
    SUPERMAJORITY = "supermajority"           # 2/3 must agree
    BAYESIAN = "bayesian"                     # Bayesian aggregation
    DELPHI = "delphi"                         # Iterative refinement
    BORDA_COUNT = "borda_count"               # Ranked choice
    CONFIDENCE_WEIGHTED = "confidence_weighted"  # Weight by confidence


class SignalDirection(Enum):
    """Direction of a trading signal"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    WEAK_BUY = "weak_buy"
    NEUTRAL = "neutral"
    WEAK_SELL = "weak_sell"
    SELL = "sell"
    STRONG_SELL = "strong_sell"
    
    def to_numeric(self) -> float:
        """Convert to numeric value (-1 to 1)"""
        mapping = {
            SignalDirection.STRONG_BUY: 1.0,
            SignalDirection.BUY: 0.66,
            SignalDirection.WEAK_BUY: 0.33,
            SignalDirection.NEUTRAL: 0.0,
            SignalDirection.WEAK_SELL: -0.33,
            SignalDirection.SELL: -0.66,
            SignalDirection.STRONG_SELL: -1.0,
        }
        return mapping.get(self, 0.0)
    
    @classmethod
    def from_numeric(cls, value: float) -> 'SignalDirection':
        """Convert from numeric value"""
        if value >= 0.83:
            return cls.STRONG_BUY
        elif value >= 0.5:
            return cls.BUY
        elif value >= 0.17:
            return cls.WEAK_BUY
        elif value >= -0.17:
            return cls.NEUTRAL
        elif value >= -0.5:
            return cls.WEAK_SELL
        elif value >= -0.83:
            return cls.SELL
        else:
            return cls.STRONG_SELL


@dataclass
class NodeVote:
    """A vote from a single node"""
    node_id: str
    node_type: NodeType
    direction: SignalDirection
    confidence: float  # 0-1
    weight: float  # Node's current weight
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def weighted_score(self) -> float:
        """Calculate weighted score"""
        return self.direction.to_numeric() * self.confidence * self.weight
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'node_id': self.node_id,
            'node_type': self.node_type.value,
            'direction': self.direction.value,
            'confidence': self.confidence,
            'weight': self.weight,
            'reasoning': self.reasoning,
            'weighted_score': self.weighted_score,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class SwarmSignal:
    """Emergent signal from swarm interaction"""
    signal_type: str
    direction: SignalDirection
    strength: float  # 0-1
    source_nodes: List[str]
    description: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_type': self.signal_type,
            'direction': self.direction.value,
            'strength': self.strength,
            'source_nodes': self.source_nodes,
            'description': self.description,
        }


@dataclass
class CollectiveDecision:
    """Final decision from the hivemind"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    symbol: str = ""
    action: str = "HOLD"  # BUY, SELL, HOLD
    direction: SignalDirection = SignalDirection.NEUTRAL
    
    # Consensus metrics
    consensus_score: float = 0.0  # 0-1, how much nodes agree
    confidence: float = 0.0       # 0-1, overall confidence
    
    # Voting details
    node_votes: List[NodeVote] = field(default_factory=list)
    total_nodes: int = 0
    agreeing_nodes: int = 0
    dissenting_nodes: int = 0
    
    # Emergent signals
    emergent_signals: List[SwarmSignal] = field(default_factory=list)
    
    # Trade parameters (if action is BUY/SELL)
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0.0
    consensus_method: ConsensusMethod = ConsensusMethod.WEIGHTED_VOTE
    governance_report: Dict[str, Any] = field(default_factory=dict)
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        lines = [
            "=" * 50,
            "HIVEMIND COLLECTIVE DECISION",
            "=" * 50,
            f"Symbol: {self.symbol}",
            f"Action: {self.action}",
            f"Direction: {self.direction.value}",
            f"Consensus: {self.consensus_score:.1%}",
            f"Confidence: {self.confidence:.1%}",
            "",
            f"Nodes: {self.agreeing_nodes}/{self.total_nodes} agree ({self.dissenting_nodes} dissent)",
            "",
        ]
        
        if self.entry_price:
            lines.append(f"Entry: {self.entry_price}")
        if self.stop_loss:
            lines.append(f"Stop Loss: {self.stop_loss}")
        if self.take_profit:
            lines.append(f"Take Profit: {self.take_profit}")
        if self.position_size:
            lines.append(f"Position Size: {self.position_size}")
        
        if self.emergent_signals:
            lines.append("")
            lines.append("Emergent Signals:")
            for signal in self.emergent_signals[:3]:
                lines.append(f"  - {signal.signal_type}: {signal.direction.value} ({signal.strength:.0%})")
        
        lines.append("")
        lines.append(f"Processing Time: {self.processing_time_ms:.0f}ms")
        lines.append("=" * 50)
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'symbol': self.symbol,
            'action': self.action,
            'direction': self.direction.value,
            'consensus_score': self.consensus_score,
            'confidence': self.confidence,
            'node_votes': [v.to_dict() for v in self.node_votes],
            'total_nodes': self.total_nodes,
            'agreeing_nodes': self.agreeing_nodes,
            'dissenting_nodes': self.dissenting_nodes,
            'emergent_signals': [s.to_dict() for s in self.emergent_signals],
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'position_size': self.position_size,
            'timestamp': self.timestamp.isoformat(),
            'processing_time_ms': self.processing_time_ms,
            'governance_report': self.governance_report,
        }


@dataclass
class NodePerformance:
    """Performance tracking for a node"""
    total_votes: int = 0
    correct_votes: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    avg_confidence_when_correct: float = 0.0
    avg_confidence_when_wrong: float = 0.0
    
    @property
    def accuracy(self) -> float:
        if self.total_votes == 0:
            return 0.5
        return self.correct_votes / self.total_votes
    
    @property
    def profit_factor(self) -> float:
        if self.total_loss == 0:
            return float('inf') if self.total_profit > 0 else 1.0
        return self.total_profit / abs(self.total_loss)


class HiveNode(ABC):
    """
    Base class for all hivemind nodes.
    
    Each node is a specialized AI agent that:
    - Analyzes market data from its perspective
    - Casts votes on trading decisions
    - Learns from outcomes to improve
    - Communicates with other nodes
    """
    
    def __init__(
        self,
        node_id: Optional[str] = None,
        node_type: NodeType = NodeType.TECHNICAL,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.node_id = node_id or f"{node_type.value}_{uuid.uuid4().hex[:6]}"
        self.node_type = node_type
        self.config = config or {}
        
        # State
        self.state = NodeState.IDLE
        self.last_vote: Optional[NodeVote] = None
        self.last_analysis_time: Optional[datetime] = None
        
        # Performance tracking
        self.performance = NodePerformance()
        
        # Weight (adjusted based on performance)
        self.base_weight = 1.0
        self.current_weight = 1.0
        
        # Communication
        self.inbox: List[Dict[str, Any]] = []
        self.outbox: List[Dict[str, Any]] = []
        
        # Knowledge
        self.learned_patterns: List[Dict[str, Any]] = []
    
    @abstractmethod
    async def analyze(self, symbol: str, market_data: Dict[str, Any]) -> NodeVote:
        """
        Analyze market data and return a vote.
        
        Args:
            symbol: Trading symbol
            market_data: Market data dictionary
            
        Returns:
            NodeVote with direction, confidence, and reasoning
        """
        pass
    
    def update_weight(self) -> None:
        """Update node weight based on performance"""
        # Base weight adjustment
        accuracy_factor = self.performance.accuracy
        profit_factor = min(self.performance.profit_factor, 3.0) / 3.0
        
        # Combine factors
        self.current_weight = self.base_weight * (0.5 + 0.3 * accuracy_factor + 0.2 * profit_factor)
        
        # Clamp to reasonable range
        self.current_weight = max(0.1, min(2.0, self.current_weight))
    
    def record_outcome(self, was_correct: bool, profit: float) -> None:
        """Record the outcome of a vote"""
        self.performance.total_votes += 1
        
        if was_correct:
            self.performance.correct_votes += 1
            if profit > 0:
                self.performance.total_profit += profit
        else:
            if profit < 0:
                self.performance.total_loss += abs(profit)
        
        # Update weight
        self.update_weight()
    
    def send_message(self, to_node: str, message_type: str, data: Any) -> None:
        """Send a message to another node"""
        self.outbox.append({
            'from': self.node_id,
            'to': to_node,
            'type': message_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
        })
    
    def receive_message(self, message: Dict[str, Any]) -> None:
        """Receive a message from another node"""
        self.inbox.append(message)
    
    def process_messages(self) -> List[Dict[str, Any]]:
        """Process inbox messages and return responses"""
        responses = []
        for message in self.inbox:
            response = self._handle_message(message)
            if response:
                responses.append(response)
        self.inbox.clear()
        return responses
    
    def _handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle a single message"""
        msg_type = message.get('type')
        
        if msg_type == 'request_opinion':
            # Another node is asking for our opinion
            return {
                'type': 'opinion_response',
                'data': {
                    'last_vote': self.last_vote.to_dict() if self.last_vote else None,
                    'confidence': self.last_vote.confidence if self.last_vote else 0,
                }
            }
        
        elif msg_type == 'share_pattern':
            # Another node is sharing a learned pattern
            pattern = message.get('data')
            if pattern:
                self.learned_patterns.append(pattern)
            return None
        
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get node status"""
        return {
            'node_id': self.node_id,
            'node_type': self.node_type.value,
            'state': self.state.value,
            'weight': self.current_weight,
            'accuracy': self.performance.accuracy,
            'total_votes': self.performance.total_votes,
            'profit_factor': self.performance.profit_factor,
        }


@dataclass
class MarketContext:
    """Market context shared across nodes"""
    symbol: str
    timeframe: str = "H1"
    current_price: float = 0.0
    
    # OHLCV data
    ohlcv: Optional[List[Dict[str, Any]]] = None
    
    # Derived data
    trend: str = "neutral"  # bullish, bearish, neutral
    volatility: str = "normal"  # low, normal, high, extreme
    regime: str = "unknown"  # trending, ranging, breakout, reversal
    
    # Additional context
    news: List[Dict[str, Any]] = field(default_factory=list)
    sentiment: Dict[str, float] = field(default_factory=dict)
    fundamentals: Dict[str, Any] = field(default_factory=dict)
    
    # Technical levels
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'current_price': self.current_price,
            'trend': self.trend,
            'volatility': self.volatility,
            'regime': self.regime,
            'support_levels': self.support_levels,
            'resistance_levels': self.resistance_levels,
        }
