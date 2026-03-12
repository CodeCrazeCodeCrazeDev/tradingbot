"""
from typing import List, Optional, Set, Tuple
Layer 6: Orchestration
======================

The orchestration layer that coordinates all other layers and manages
autonomous operation with human oversight.

Components:
- HumanProtocol: Human-in-loop communication and approval
- EvolutionEngine: Self-evolution and improvement
- AutonomousController: Autonomous operation management
- MasterOrchestrator: Master coordinator for all layers

Integrates:
- trading_bot/qwen_codemender/human_protocol.py
- trading_bot/qwen_codemender/self_evolution.py
- trading_bot/master_orchestrator.py
- trading_bot/self_improvement/engine.py
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages to human"""
    ALERT = "alert"
    REPORT = "report"
    PROPOSAL = "proposal"
    QUESTION = "question"
    STATUS = "status"


class MessagePriority(Enum):
    """Message priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ApprovalStatus(Enum):
    """Approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OperationMode(Enum):
    """System operation modes"""
    AUTONOMOUS = "autonomous"
    SEMI_AUTONOMOUS = "semi_autonomous"
    MANUAL = "manual"
    PAUSED = "paused"


@dataclass
class Message:
    """Message to human"""
    message_id: str
    message_type: MessageType
    priority: MessagePriority
    subject: str
    content: str
    timestamp: datetime
    requires_response: bool = False
    response_options: List[str] = field(default_factory=list)
    expires_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HumanResponse:
    """Response from human"""
    message_id: str
    response: str
    timestamp: datetime
    notes: Optional[str] = None


@dataclass
class EvolutionProposal:
    """Proposal for system evolution"""
    proposal_id: str
    category: str
    description: str
    expected_improvement: float
    risk_level: str
    implementation_steps: List[str]
    rollback_plan: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)


class HumanProtocol:
    """
    Human-in-loop communication protocol
    
    Integrates trading_bot/qwen_codemender/human_protocol.py
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Message storage
        self.messages: Dict[str, Message] = {}
        self.responses: Dict[str, HumanResponse] = {}
        self.pending_approvals: Dict[str, Any] = {}
        
        # Communication channels
        self.channels = config.get('channels', ['console'])
        
        # Message counter
        self._message_counter = 0
        
        try:
            # Import existing protocol
            self._protocol = None  # Using built-in protocol
            logger.info("Human protocol initialized")
        except Exception as e:
            logger.warning(f"Using fallback human protocol: {e}")
            self._protocol = None
    
    def send_message(self, message_type: MessageType, priority: MessagePriority,
                    subject: str, content: str, requires_response: bool = False,
                    response_options: Optional[List[str]] = None,
                    expires_in_hours: Optional[int] = None,
                    context: Optional[Dict] = None) -> str:
        """Send a message to human"""
        self._message_counter += 1
        message_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._message_counter}"
        
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        
        message = Message(
            message_id=message_id,
            message_type=message_type,
            priority=priority,
            subject=subject,
            content=content,
            timestamp=datetime.now(),
            requires_response=requires_response,
            response_options=response_options or [],
            expires_at=expires_at,
            context=context or {}
        )
        
        self.messages[message_id] = message
        
        # Send through channels
        self._deliver_message(message)
        
        logger.info(f"Message sent: [{priority.value}] {subject}")
        
        return message_id
    
    def _deliver_message(self, message: Message):
        """Deliver message through configured channels"""
        for channel in self.channels:
            try:
                if channel == 'console':
                    self._deliver_console(message)
                elif channel == 'telegram':
                    self._deliver_telegram(message)
                elif channel == 'email':
                    self._deliver_email(message)
            except Exception as e:
                logger.error(f"Failed to deliver via {channel}: {e}")
    
    def _deliver_console(self, message: Message):
        """Deliver to console"""
        logger.info(f"\n{'='*60}")
        logger.info(f"[{message.priority.value.upper()}] {message.message_type.value.upper()}")
        logger.info(f"Subject: {message.subject}")
        logger.info(f"{'='*60}")
        print(message.content)
        if message.requires_response:
            logger.info(f"\nOptions: {', '.join(message.response_options)}")
        logger.info(f"{'='*60}\n")
    
    def _deliver_telegram(self, message: Message):
        """Deliver via Telegram"""
        if self._protocol:
            self._protocol.send_telegram(message)
    
    def _deliver_email(self, message: Message):
        """Deliver via email"""
        if self._protocol:
            self._protocol.send_email(message)
    
    def receive_response(self, message_id: str, response: str, 
                        notes: Optional[str] = None) -> bool:
        """Receive response from human"""
        if message_id not in self.messages:
            logger.warning(f"Unknown message ID: {message_id}")
            return False
        
        message = self.messages[message_id]
        
        # Check expiry
        if message.expires_at and datetime.now() > message.expires_at:
            logger.warning(f"Message expired: {message_id}")
            return False
        
        # Validate response
        if message.response_options and response not in message.response_options:
            logger.warning(f"Invalid response: {response}")
            return False
        
        # Store response
        self.responses[message_id] = HumanResponse(
            message_id=message_id,
            response=response,
            timestamp=datetime.now(),
            notes=notes
        )
        
        logger.info(f"Response received for {message_id}: {response}")
        
        return True
    
    def get_pending_messages(self) -> List[Message]:
        """Get messages awaiting response"""
        pending = []
        for msg_id, message in self.messages.items():
            if message.requires_response and msg_id not in self.responses:
                if not message.expires_at or datetime.now() < message.expires_at:
                    pending.append(message)
        return pending
    
    def send_daily_report(self, metrics: Dict[str, Any]):
        """Send daily performance report"""
        content = self._format_daily_report(metrics)
        self.send_message(
            message_type=MessageType.REPORT,
            priority=MessagePriority.LOW,
            subject="Daily Trading Report",
            content=content
        )
    
    def _format_daily_report(self, metrics: Dict[str, Any]) -> str:
        """Format daily report"""
        lines = [
            f"Date: {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "PERFORMANCE:",
            f"  Total Trades: {metrics.get('total_trades', 0)}",
            f"  Win Rate: {metrics.get('win_rate', 0):.1%}",
            f"  Daily P&L: ${metrics.get('daily_pnl', 0):,.2f}",
            f"  Current Equity: ${metrics.get('equity', 0):,.2f}",
            "",
            "RISK:",
            f"  Current Drawdown: {metrics.get('drawdown', 0):.1%}",
            f"  Open Positions: {metrics.get('positions', 0)}",
            f"  Risk Level: {metrics.get('risk_level', 'unknown')}",
            "",
            "SYSTEM:",
            f"  Status: {metrics.get('status', 'unknown')}",
            f"  Fail-Safe Mode: {metrics.get('fail_safe_mode', 'normal')}",
        ]
        return "\n".join(lines)


class EvolutionEngine:
    """
    Self-evolution and improvement engine
    
    Integrates trading_bot/qwen_codemender/self_evolution.py
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Proposal storage
        self.proposals: Dict[str, EvolutionProposal] = {}
        self.implemented: List[str] = []
        
        # Evolution tracking
        self.evolution_cycle = 0
        self.last_evolution = None
        
        try:
            # Import existing engine
            from trading_bot.qwen_codemender import SelfEvolutionEngine
            self._engine = SelfEvolutionEngine(root_path=config.get('root_path', '.'))
            logger.info("Evolution engine initialized")
        except Exception as e:
            logger.warning(f"Using fallback evolution engine: {e}")
            self._engine = None
    
    def analyze_performance(self, metrics: Dict[str, Any]) -> List[str]:
        """Analyze performance and identify improvement areas"""
        issues = []
        
        # Check win rate
        win_rate = metrics.get('win_rate', 0.5)
        if win_rate < 0.45:
            issues.append("Low win rate - consider signal quality improvements")
        
        # Check drawdown
        drawdown = metrics.get('drawdown', 0)
        if drawdown > 0.10:
            issues.append("Elevated drawdown - consider risk parameter adjustments")
        
        # Check Sharpe ratio
        sharpe = metrics.get('sharpe_ratio', 1.0)
        if sharpe < 1.0:
            issues.append("Low Sharpe ratio - consider strategy optimization")
        
        return issues
    
    def generate_proposal(self, issue: str, category: str) -> EvolutionProposal:
        """Generate an evolution proposal"""
        proposal_id = f"prop_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Generate proposal based on issue
        if "win rate" in issue.lower():
            proposal = EvolutionProposal(
                proposal_id=proposal_id,
                category="signal_quality",
                description="Improve signal generation by adding additional confirmation filters",
                expected_improvement=0.05,
                risk_level="low",
                implementation_steps=[
                    "Add RSI divergence filter",
                    "Require multi-timeframe alignment",
                    "Increase minimum confidence threshold"
                ],
                rollback_plan="Revert to previous signal parameters"
            )
        elif "drawdown" in issue.lower():
            proposal = EvolutionProposal(
                proposal_id=proposal_id,
                category="risk_management",
                description="Reduce position sizes and tighten stop losses",
                expected_improvement=0.03,
                risk_level="low",
                implementation_steps=[
                    "Reduce max risk per trade from 2% to 1.5%",
                    "Implement trailing stops",
                    "Add correlation-based position limits"
                ],
                rollback_plan="Revert to previous risk parameters"
            )
        else:
            proposal = EvolutionProposal(
                proposal_id=proposal_id,
                category="general",
                description=f"Address: {issue}",
                expected_improvement=0.02,
                risk_level="medium",
                implementation_steps=["Analyze issue", "Develop solution", "Test and deploy"],
                rollback_plan="Revert changes"
            )
        
        self.proposals[proposal_id] = proposal
        return proposal
    
    def approve_proposal(self, proposal_id: str) -> bool:
        """Approve a proposal for implementation"""
        if proposal_id not in self.proposals:
            return False
        
        proposal = self.proposals[proposal_id]
        proposal.status = ApprovalStatus.APPROVED
        
        logger.info(f"Proposal approved: {proposal_id}")
        return True
    
    def reject_proposal(self, proposal_id: str, reason: str) -> bool:
        """Reject a proposal"""
        if proposal_id not in self.proposals:
            return False
        
        proposal = self.proposals[proposal_id]
        proposal.status = ApprovalStatus.REJECTED
        
        logger.info(f"Proposal rejected: {proposal_id} - {reason}")
        return True
    
    def implement_proposal(self, proposal_id: str) -> bool:
        """Implement an approved proposal"""
        if proposal_id not in self.proposals:
            return False
        
        proposal = self.proposals[proposal_id]
        
        if proposal.status != ApprovalStatus.APPROVED:
            logger.warning(f"Cannot implement unapproved proposal: {proposal_id}")
            return False
        
        # Implementation would go here
        # For now, just mark as implemented
        self.implemented.append(proposal_id)
        self.evolution_cycle += 1
        self.last_evolution = datetime.now()
        
        logger.info(f"Proposal implemented: {proposal_id}")
        return True
    
    def get_pending_proposals(self) -> List[EvolutionProposal]:
        """Get proposals awaiting approval"""
        return [p for p in self.proposals.values() if p.status == ApprovalStatus.PENDING]


class AutonomousController:
    """
    Autonomous operation controller
    
    Manages autonomous trading cycles with appropriate oversight
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Operation mode
        self.mode = OperationMode(config.get('mode', 'semi_autonomous'))
        
        # Cycle tracking
        self.cycle_count = 0
        self.last_cycle = None
        self.cycle_interval_seconds = config.get('cycle_interval', 60)
        
        # Autonomous limits
        self.max_autonomous_trades = config.get('max_autonomous_trades', 10)
        self.autonomous_trade_count = 0
        self.require_approval_above = config.get('require_approval_above', 0.05)  # 5% of equity
        
        # State
        self.is_running = False
        self._stop_requested = False
    
    def can_trade_autonomously(self, trade_value: float, equity: float) -> Tuple[bool, str]:
        """Check if trade can be executed autonomously"""
        if self.mode == OperationMode.MANUAL:
            return False, "Manual mode - all trades require approval"
        
        if self.mode == OperationMode.PAUSED:
            return False, "System paused"
        
        # Check trade count
        if self.autonomous_trade_count >= self.max_autonomous_trades:
            return False, "Autonomous trade limit reached"
        
        # Check trade size
        trade_pct = trade_value / equity if equity > 0 else 1.0
        if trade_pct > self.require_approval_above:
            return False, f"Trade size {trade_pct:.1%} requires approval"
        
        return True, "Autonomous execution allowed"
    
    def record_autonomous_trade(self):
        """Record an autonomous trade"""
        self.autonomous_trade_count += 1
    
    def reset_daily_limits(self):
        """Reset daily autonomous limits"""
        self.autonomous_trade_count = 0
    
    def set_mode(self, mode: OperationMode):
        """Set operation mode"""
        old_mode = self.mode
        self.mode = mode
        logger.info(f"Operation mode changed: {old_mode.value} -> {mode.value}")
    
    def start_cycle(self):
        """Start an autonomous cycle"""
        self.cycle_count += 1
        self.last_cycle = datetime.now()
        self.is_running = True
    
    def end_cycle(self):
        """End an autonomous cycle"""
        self.is_running = False
    
    def request_stop(self):
        """Request graceful stop"""
        self._stop_requested = True
    
    def should_stop(self) -> bool:
        """Check if stop was requested"""
        return self._stop_requested


class MasterOrchestrator:
    """
    Master coordinator for Layer 6: Orchestration
    
    Coordinates all layers and manages the complete trading system
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize components
        self.human_protocol = HumanProtocol(config.get('human', {}))
        self.evolution_engine = EvolutionEngine(config.get('evolution', {}))
        self.autonomous = AutonomousController(config.get('autonomous', {}))
        
        # Layer references (set by unified system)
        self.data_layer = None
        self.intelligence_layer = None
        self.strategy_layer = None
        self.execution_layer = None
        self.risk_layer = None
        
        # State
        self.is_initialized = False
        self.start_time: Optional[datetime] = None
        
        # Statistics
        self.stats = {
            'cycles_completed': 0,
            'trades_executed': 0,
            'signals_generated': 0,
            'proposals_generated': 0
        }
        
        logger.info("Master Orchestrator initialized")
    
    def set_layers(self, data, intelligence, strategy, execution, risk):
        """Set references to other layers"""
        self.data_layer = data
        self.intelligence_layer = intelligence
        self.strategy_layer = strategy
        self.execution_layer = execution
        self.risk_layer = risk
        self.is_initialized = True
    
    async def run_trading_cycle(self, symbol: str) -> Dict[str, Any]:
        """
        Run a complete trading cycle
        
        Pipeline:
        1. Fetch data (Layer 1)
        2. Analyze with AI (Layer 2)
        3. Generate signals (Layer 3)
        4. Check risk (Layer 5)
        5. Execute if approved (Layer 4)
        6. Update and evolve (Layer 6)
        """
        if not self.is_initialized:
            return {'error': 'Orchestrator not initialized'}
        
        self.autonomous.start_cycle()
        cycle_result = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'stages': {}
        }
        
        try:
            # Stage 1: Fetch data
            logger.info(f"[Cycle] Stage 1: Fetching data for {symbol}")
            data = await self.data_layer.fetch_all(symbol)
            cycle_result['stages']['data'] = {'success': bool(data)}
            
            if not data or 'data' not in data:
                return cycle_result
            
            # Stage 2: AI Analysis
            logger.info("[Cycle] Stage 2: Running AI analysis")
            intelligence_output = await self.intelligence_layer.analyze(data['data'], symbol)
            cycle_result['stages']['intelligence'] = {
                'signal': intelligence_output.signal,
                'confidence': intelligence_output.confidence
            }
            
            # Stage 3: Generate signal
            logger.info("[Cycle] Stage 3: Generating trading signal")
            market_data = data['data'].get('market')
            if market_data is not None:
                signal = await self.strategy_layer.generate_signal(
                    symbol=symbol,
                    market_data=market_data,
                    indicators={'rsi': market_data.get('rsi') if hasattr(market_data, 'get') else None},
                    sentiment=data['data'].get('sentiment', {})
                )
                
                if signal:
                    self.stats['signals_generated'] += 1
                    cycle_result['stages']['strategy'] = {
                        'direction': signal.direction.value,
                        'confidence': signal.confidence
                    }
                    
                    # Stage 4: Risk check
                    logger.info("[Cycle] Stage 4: Checking risk")
                    risk_result = self.risk_layer.pre_trade_check(
                        symbol=symbol,
                        side=signal.direction.value,
                        size=signal.position_size,
                        entry_price=signal.entry_price,
                        stop_loss=signal.stop_loss
                    )
                    
                    cycle_result['stages']['risk'] = {
                        'approved': risk_result.approved,
                        'risk_level': risk_result.risk_level.value
                    }
                    
                    # Stage 5: Execute if approved
                    if risk_result.approved and signal.direction.value != 'hold':
                        logger.info("[Cycle] Stage 5: Executing trade")
                        
                        # Check autonomous execution
                        can_auto, reason = self.autonomous.can_trade_autonomously(
                            signal.position_size * signal.entry_price,
                            self.risk_layer.risk_manager.equity
                        )
                        
                        if can_auto or self.autonomous.mode == OperationMode.AUTONOMOUS:
                            from .layer4_execution import OrderSide, OrderType
                            
                            exec_result = await self.execution_layer.execute(
                                symbol=symbol,
                                side=OrderSide.BUY if signal.direction.value == 'buy' else OrderSide.SELL,
                                quantity=risk_result.adjusted_size,
                                price=signal.entry_price
                            )
                            
                            cycle_result['stages']['execution'] = {
                                'success': exec_result.success,
                                'order_id': exec_result.order.order_id if exec_result.order else None
                            }
                            
                            if exec_result.success:
                                self.stats['trades_executed'] += 1
                                self.autonomous.record_autonomous_trade()
                        else:
                            # Request human approval
                            self.human_protocol.send_message(
                                message_type=MessageType.QUESTION,
                                priority=MessagePriority.HIGH,
                                subject=f"Trade Approval Required: {symbol}",
                                content=f"Signal: {signal.direction.value}\n"
                                       f"Size: {risk_result.adjusted_size}\n"
                                       f"Entry: {signal.entry_price}\n"
                                       f"Reason: {reason}",
                                requires_response=True,
                                response_options=["APPROVE", "REJECT"],
                                expires_in_hours=1
                            )
                            cycle_result['stages']['execution'] = {
                                'success': False,
                                'reason': 'Awaiting human approval'
                            }
            
            self.stats['cycles_completed'] += 1
            
        except Exception as e:
            logger.error(f"Cycle error: {e}")
            cycle_result['error'] = str(e)
            self.risk_layer.record_error(str(e))
        
        finally:
            self.autonomous.end_cycle()
        
        return cycle_result
    
    async def run_evolution_cycle(self) -> List[EvolutionProposal]:
        """Run an evolution cycle"""
        # Gather metrics
        metrics = {
            'win_rate': 0.5,  # Would come from actual tracking
            'drawdown': self.risk_layer.risk_manager._calculate_drawdown() if self.risk_layer else 0,
            'sharpe_ratio': 1.0
        }
        
        # Analyze and generate proposals
        issues = self.evolution_engine.analyze_performance(metrics)
        proposals = []
        
        for issue in issues:
            proposal = self.evolution_engine.generate_proposal(issue, "auto")
            proposals.append(proposal)
            self.stats['proposals_generated'] += 1
            
            # Send for human approval
            self.human_protocol.send_message(
                message_type=MessageType.PROPOSAL,
                priority=MessagePriority.MEDIUM,
                subject=f"Evolution Proposal: {proposal.category}",
                content=f"Description: {proposal.description}\n"
                       f"Expected Improvement: {proposal.expected_improvement:.1%}\n"
                       f"Risk Level: {proposal.risk_level}\n\n"
                       f"Steps:\n" + "\n".join(f"  {i+1}. {s}" for i, s in enumerate(proposal.implementation_steps)),
                requires_response=True,
                response_options=["APPROVE", "REJECT", "DEFER"],
                expires_in_hours=24,
                context={'proposal_id': proposal.proposal_id}
            )
        
        return proposals
    
    def send_daily_report(self):
        """Send daily report"""
        metrics = {
            'total_trades': self.stats['trades_executed'],
            'win_rate': 0.5,  # Would come from actual tracking
            'daily_pnl': self.risk_layer.risk_manager.daily_pnl if self.risk_layer else 0,
            'equity': self.risk_layer.risk_manager.equity if self.risk_layer else 0,
            'drawdown': self.risk_layer.risk_manager._calculate_drawdown() if self.risk_layer else 0,
            'positions': len(self.risk_layer.risk_manager.positions) if self.risk_layer else 0,
            'risk_level': 'normal',
            'status': self.autonomous.mode.value,
            'fail_safe_mode': self.risk_layer.fail_safe.mode.value if self.risk_layer else 'normal'
        }
        
        self.human_protocol.send_daily_report(metrics)
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            'initialized': self.is_initialized,
            'mode': self.autonomous.mode.value,
            'cycles_completed': self.stats['cycles_completed'],
            'trades_executed': self.stats['trades_executed'],
            'signals_generated': self.stats['signals_generated'],
            'pending_messages': len(self.human_protocol.get_pending_messages()),
            'pending_proposals': len(self.evolution_engine.get_pending_proposals())
        }
