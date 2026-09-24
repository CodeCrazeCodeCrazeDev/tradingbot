"""
Core Types for Perplexity Trading Architecture
============================================================

Defines all data structures, enums, and types used throughout
the Perplexity-style trading system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union
import uuid


class AgentType(Enum):
    """Types of specialized trading agents"""
    RESEARCH = "research"           # Market research, news, fundamentals
    TECHNICAL = "technical"         # Chart patterns, indicators, price action
    RISK = "risk"                   # Position sizing, drawdown, exposure
    EXECUTION = "execution"         # Order routing, timing, slippage
    REASONING = "reasoning"         # Multi-step analysis, chain-of-thought
    SENTIMENT = "sentiment"         # Social media, news sentiment
    MACRO = "macro"                 # Economic indicators, central bank policy
    MICROSTRUCTURE = "microstructure"  # Order flow, liquidity, market depth
    SUMMARIZER = "summarizer"       # Synthesize results into final output
    VALIDATOR = "validator"         # Cross-reference and verify data


class TaskType(Enum):
    """Types of subtasks in the task graph"""
    RESEARCH = auto()               # Gather information
    ANALYSIS = auto()               # Analyze data
    EXTRACTION = auto()             # Extract specific data points
    CALCULATION = auto()            # Perform calculations
    SYNTHESIS = auto()              # Combine multiple inputs
    VERIFICATION = auto()           # Verify/validate data
    DECISION = auto()               # Make a decision
    EXECUTION = auto()              # Execute an action
    SUMMARY = auto()                # Summarize findings


class MemoryLevel(Enum):
    """Memory persistence levels"""
    SHORT_TERM = "short_term"       # Within session (cleared on restart)
    MEDIUM_TERM = "medium_term"     # 7 days persistence
    LONG_TERM = "long_term"         # Permanent storage


class RetrievalSource(Enum):
    """Data retrieval sources"""
    MARKET_DATA = "market_data"     # Price, volume, OHLCV
    NEWS = "news"                   # Financial news
    SENTIMENT = "sentiment"         # Social media sentiment
    FUNDAMENTALS = "fundamentals"   # Company/economic fundamentals
    ALTERNATIVE = "alternative"     # Alternative data sources
    MEMORY = "memory"               # From persistent memory
    CALCULATION = "calculation"     # Computed/derived data


class ConfidenceLevel(Enum):
    """Confidence levels for decisions"""
    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95


class ApprovalStatus(Enum):
    """Status of human approval requests"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    AUTO_APPROVED = "auto_approved"  # Low-risk actions


@dataclass
class Citation:
    """Citation for data source attribution"""
    source_type: RetrievalSource
    source_name: str
    timestamp: datetime
    data_point: str
    confidence: float
    url: Optional[str] = None
    raw_data: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_type': self.source_type.value,
            'source_name': self.source_name,
            'timestamp': self.timestamp.isoformat(),
            'data_point': self.data_point,
            'confidence': self.confidence,
            'url': self.url,
        }


@dataclass
class SubTask:
    """A discrete subtask in the task graph"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    task_type: TaskType = TaskType.ANALYSIS
    agent_type: AgentType = AgentType.REASONING
    description: str = ""
    action: str = ""
    inputs: List[str] = field(default_factory=list)  # IDs of dependent subtasks
    outputs: List[str] = field(default_factory=list)  # Output keys
    tool: Optional[str] = None  # Tool to use (e.g., "web_browse", "calculate")
    priority: int = 1  # Higher = more important
    timeout_seconds: float = 30.0
    retry_on_failure: bool = True
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'task_type': self.task_type.name,
            'agent_type': self.agent_type.value,
            'description': self.description,
            'action': self.action,
            'inputs': self.inputs,
            'outputs': self.outputs,
            'tool': self.tool,
            'priority': self.priority,
        }


@dataclass
class SubTaskResult:
    """Result from executing a subtask"""
    subtask_id: str
    success: bool
    output_data: Dict[str, Any] = field(default_factory=dict)
    citations: List[Citation] = field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'subtask_id': self.subtask_id,
            'success': self.success,
            'output_data': self.output_data,
            'citations': [c.to_dict() for c in self.citations],
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'error': self.error,
            'execution_time_ms': self.execution_time_ms,
        }


@dataclass
class QACheckResult:
    """Result of quality assurance verification"""
    passed: bool
    method: str  # e.g., "cross_reference", "consistency_check"
    issues: List[str] = field(default_factory=list)
    corrections: Dict[str, Any] = field(default_factory=dict)
    confidence_adjustment: float = 0.0  # Adjustment to overall confidence
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'passed': self.passed,
            'method': self.method,
            'issues': self.issues,
            'corrections': self.corrections,
            'confidence_adjustment': self.confidence_adjustment,
        }


@dataclass
class TradingQuery:
    """Input query for trading analysis"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"  # low, normal, high, urgent
    require_approval: bool = True  # For execution actions
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'query': self.query,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'context': self.context,
            'constraints': self.constraints,
            'priority': self.priority,
            'require_approval': self.require_approval,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class TradingDecision:
    """Final trading decision output"""
    query_id: str
    action: str  # BUY, SELL, HOLD, WAIT, NO_TRADE
    symbol: Optional[str] = None
    confidence: float = 0.0
    
    # Position details (if applicable)
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None
    order_type: Optional[str] = None  # MARKET, LIMIT, STOP
    
    # Reasoning and provenance
    reasoning_chain: List[str] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    subtask_results: Dict[str, SubTaskResult] = field(default_factory=dict)
    
    # Quality metrics
    qa_results: List[QACheckResult] = field(default_factory=list)
    data_freshness_seconds: float = 0.0
    
    # Approval status
    requires_approval: bool = True
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    approval_reason: Optional[str] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0.0
    model_versions: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'query_id': self.query_id,
            'action': self.action,
            'symbol': self.symbol,
            'confidence': self.confidence,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'position_size': self.position_size,
            'order_type': self.order_type,
            'reasoning_chain': self.reasoning_chain,
            'citations': [c.to_dict() for c in self.citations],
            'qa_results': [q.to_dict() for q in self.qa_results],
            'requires_approval': self.requires_approval,
            'approval_status': self.approval_status.value,
            'timestamp': self.timestamp.isoformat(),
            'processing_time_ms': self.processing_time_ms,
        }
    
    def get_summary(self) -> str:
        """Get human-readable summary of the decision"""
        lines = [
            f"=== Trading Decision ===",
            f"Action: {self.action}",
            f"Symbol: {self.symbol or 'N/A'}",
            f"Confidence: {self.confidence:.1%}",
        ]
        
        if self.entry_price:
            lines.append(f"Entry: {self.entry_price}")
        if self.stop_loss:
            lines.append(f"Stop Loss: {self.stop_loss}")
        if self.take_profit:
            lines.append(f"Take Profit: {self.take_profit}")
        if self.position_size:
            lines.append(f"Position Size: {self.position_size}")
        
        lines.append(f"\n=== Reasoning ===")
        for i, step in enumerate(self.reasoning_chain, 1):
            lines.append(f"{i}. {step}")
        
        lines.append(f"\n=== Citations ({len(self.citations)}) ===")
        for citation in self.citations[:5]:  # Show first 5
            lines.append(f"- [{citation.source_type.value}] {citation.data_point}")
        
        return "\n".join(lines)


@dataclass
class MemoryEntry:
    """Entry in persistent memory"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    level: MemoryLevel = MemoryLevel.SHORT_TERM
    category: str = ""  # e.g., "user_preference", "market_context", "trade_history"
    key: str = ""
    value: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'level': self.level.value,
            'category': self.category,
            'key': self.key,
            'value': self.value,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'access_count': self.access_count,
        }


@dataclass
class MemoryQuery:
    """Query for retrieving from persistent memory"""
    categories: List[str] = field(default_factory=list)
    keys: List[str] = field(default_factory=list)
    levels: List[MemoryLevel] = field(default_factory=list)
    text_search: Optional[str] = None
    limit: int = 10
    include_expired: bool = False


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    decision: 'TradingDecision' = None
    risk_level: str = "medium"  # low, medium, high, critical
    reason: str = ""
    timeout_seconds: float = 300.0  # 5 minutes default
    auto_approve_if_timeout: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'decision': self.decision.to_dict() if self.decision else None,
            'risk_level': self.risk_level,
            'reason': self.reason,
            'timeout_seconds': self.timeout_seconds,
            'auto_approve_if_timeout': self.auto_approve_if_timeout,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class ApprovalDecision:
    """Human's approval decision"""
    request_id: str
    approved: bool
    reason: Optional[str] = None
    modifications: Dict[str, Any] = field(default_factory=dict)
    decided_by: str = "human"
    decided_at: datetime = field(default_factory=datetime.utcnow)
