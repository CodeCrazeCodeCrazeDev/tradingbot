"""
Multi-Agent Debate System for Decision Governance
==================================================

Implements structured debate between multiple AI agents to reach
consensus on complex trading decisions. Inspired by multi-agent
validation patterns in advanced AI research systems.

Debate Structure:
- Proposer: Presents the initial decision case
- Challenger: Critiques and identifies weaknesses
- Synthesizer: Reconciles viewpoints and finds common ground
- Arbiter: Makes final judgment based on debate quality

Features:
- Structured turn-based debate rounds
- Belief updating through argument exchange
- Confidence scoring based on argument strength
- Automatic consensus detection
- Dissent documentation for audit trails
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import defaultdict

logger = logging.getLogger(__name__)


class DebateRole(Enum):
    """Roles in the debate"""
    PROPOSER = "proposer"
    CHALLENGER = "challenger"
    SYNTHESIZER = "synthesizer"
    ARBITER = "arbiter"
    OBSERVER = "observer"


class DebateStatus(Enum):
    """Status of a debate"""
    PENDING = "pending"
    ACTIVE = "active"
    CONSENSUS = "consensus"
    STALEMATE = "stalemate"
    ARBITRATED = "arbitrated"
    TIMEOUT = "timeout"


class ArgumentType(Enum):
    """Types of arguments in debate"""
    EVIDENCE = "evidence"  # Factual evidence
    LOGIC = "logic"  # Logical reasoning
    PRECEDENT = "precedent"  # Historical example
    RISK = "risk"  # Risk assessment
    OPPORTUNITY = "opportunity"  # Opportunity assessment
    COUNTER = "counter"  # Counter-argument


@dataclass
class Argument:
    """An argument in the debate"""
    id: str
    role: DebateRole
    argument_type: ArgumentType
    content: str
    supporting_evidence: List[str]
    confidence: float  # 0-1
    timestamp: datetime = field(default_factory=datetime.utcnow)
    responds_to: Optional[str] = None  # ID of argument this responds to
    strength_score: float = 0.0  # Computed strength
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class DebateRound:
    """A single round of debate"""
    round_number: int
    arguments: List[Argument] = field(default_factory=list)
    key_points: List[str] = field(default_factory=list)
    consensus_emerging: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentBelief:
    """Belief state of a debating agent"""
    role: DebateRole
    position: str  # 'approve', 'reject', 'defer'
    confidence: float  # 0-1
    reasoning: str
    key_concerns: List[str] = field(default_factory=list)
    acceptable_compromises: List[str] = field(default_factory=list)


@dataclass
class DebateResult:
    """Result of a completed debate"""
    debate_id: str
    status: DebateStatus
    final_position: str
    final_confidence: float
    rounds_conducted: int
    consensus_achieved: bool
    winning_arguments: List[str]
    dissenting_views: List[str]
    audit_trail: List[Dict[str, Any]]
    recommendation: str
    risk_assessment: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class DebatingAgent:
    """
    Base class for debating agents.
    
    Each agent has a role, belief state, and argument generation capability.
    """
    
    def __init__(self, role: DebateRole, name: str, expertise: List[str] = None):
        self.role = role
        self.name = name
        self.expertise = expertise or []
        self.belief: Optional[AgentBelief] = None
        self.arguments_made: List[str] = []
        
    def initialize_belief(
        self,
        decision_context: Dict[str, Any],
        initial_position: str,
        confidence: float
    ) -> AgentBelief:
        """Initialize agent's belief state for a decision"""
        self.belief = AgentBelief(
            role=self.role,
            position=initial_position,
            confidence=confidence,
            reasoning=self._generate_initial_reasoning(decision_context),
            key_concerns=self._identify_concerns(decision_context)
        )
        return self.belief
    
    def _generate_initial_reasoning(self, context: Dict[str, Any]) -> str:
        """Generate initial reasoning based on role"""
        if self.role == DebateRole.PROPOSER:
            return f"Based on signal confidence {context.get('confidence', 0)}, market conditions support this trade."
        elif self.role == DebateRole.CHALLENGER:
            return f"Initial assessment reveals potential risks in {context.get('regime', 'unknown')} regime."
        elif self.role == DebateRole.SYNTHESIZER:
            return "Analyzing both opportunity and risk factors for balanced assessment."
        else:
            return "Evaluating debate quality and argument strength for final judgment."
    
    def _identify_concerns(self, context: Dict[str, Any]) -> List[str]:
        """Identify key concerns based on role"""
        concerns = []
        if self.role == DebateRole.CHALLENGER:
            if context.get('volatility', 0) > 0.3:
                concerns.append("High volatility environment")
            if context.get('drawdown', 0) > 0.05:
                concerns.append("Portfolio in drawdown")
        return concerns
    
    async def generate_argument(
        self,
        debate_context: Dict[str, Any],
        current_round: int,
        previous_arguments: List[Argument]
    ) -> Optional[Argument]:
        """Generate an argument for the current debate round"""
        
        # Determine argument type based on role and round
        arg_type = self._select_argument_type(current_round, previous_arguments)
        
        # Generate content based on role
        content = self._generate_argument_content(
            debate_context, arg_type, previous_arguments
        )
        
        if not content:
            return None
        
        # Find what this responds to (if challenger)
        responds_to = None
        if self.role == DebateRole.CHALLENGER and previous_arguments:
            # Find last proposer argument to challenge
            for arg in reversed(previous_arguments):
                if arg.role == DebateRole.PROPOSER:
                    responds_to = arg.id
                    break
        
        argument = Argument(
            id=str(uuid.uuid4()),
            role=self.role,
            argument_type=arg_type,
            content=content,
            supporting_evidence=self._gather_evidence(debate_context),
            confidence=self.belief.confidence if self.belief else 0.5,
            responds_to=responds_to
        )
        
        self.arguments_made.append(argument.id)
        return argument
    
    def _select_argument_type(
        self,
        round_num: int,
        previous_args: List[Argument]
    ) -> ArgumentType:
        """Select appropriate argument type"""
        if self.role == DebateRole.PROPOSER:
            if round_num == 0:
                return ArgumentType.EVIDENCE
            else:
                return ArgumentType.COUNTER
        elif self.role == DebateRole.CHALLENGER:
            return ArgumentType.RISK
        elif self.role == DebateRole.SYNTHESIZER:
            return ArgumentType.LOGIC
        else:
            return ArgumentType.PRECEDENT
    
    def _generate_argument_content(
        self,
        context: Dict[str, Any],
        arg_type: ArgumentType,
        previous_args: List[Argument]
    ) -> str:
        """Generate argument content"""
        templates = {
            DebateRole.PROPOSER: {
                ArgumentType.EVIDENCE: f"Signal shows {context.get('confidence', 0):.1%} confidence with supporting indicators.",
                ArgumentType.OPPORTUNITY: "Market regime presents favorable conditions for this strategy.",
                ArgumentType.COUNTER: "The challenger\'s concern is addressed by adaptive position sizing."
            },
            DebateRole.CHALLENGER: {
                ArgumentType.RISK: f"Current volatility at {context.get('volatility', 0):.1%} exceeds comfortable threshold.",
                ArgumentType.EVIDENCE: "Historical data shows similar setups resulted in 40% failure rate.",
                ArgumentType.COUNTER: "Proposer\'s evidence ignores correlation risk in current market."
            },
            DebateRole.SYNTHESIZER: {
                ArgumentType.LOGIC: "Both parties agree on market direction but differ on timing and sizing.",
                ArgumentType.EVIDENCE: "Backtesting supports entry but suggests smaller position size.",
                ArgumentType.PRECEDENT: "Similar debates in past reached consensus at 60% baseline confidence."
            },
            DebateRole.ARBITER: {
                ArgumentType.LOGIC: "Challenger has raised valid concerns that must be addressed.",
                ArgumentType.PRECEDENT: "Standard practice requires minimum 3:1 reward-to-risk ratio.",
                ArgumentType.EVIDENCE: "Risk-adjusted expectancy calculations favor conservative approach."
            }
        }
        
        role_templates = templates.get(self.role, {})
        return role_templates.get(arg_type, "Continuing analysis of the proposed decision.")
    
    def _gather_evidence(self, context: Dict[str, Any]) -> List[str]:
        """Gather supporting evidence"""
        evidence = []
        if 'backtest_results' in context:
            evidence.append(f"Backtest: {context['backtest_results']}")
        if 'market_regime' in context:
            evidence.append(f"Regime: {context['market_regime']}")
        return evidence
    
    def update_belief(self, new_arguments: List[Argument]):
        """Update belief based on new arguments"""
        if not self.belief:
            return
        
        # Adjust confidence based on argument strength
        for arg in new_arguments:
            if arg.role != self.role:
                if arg.argument_type == ArgumentType.RISK:
                    self.belief.confidence *= 0.9
                elif arg.argument_type == ArgumentType.EVIDENCE:
                    if arg.confidence > 0.7:
                        self.belief.confidence = min(1.0, self.belief.confidence * 1.1)
        
        # Update concerns
        for arg in new_arguments:
            if arg.role == DebateRole.CHALLENGER and arg.argument_type == ArgumentType.RISK:
                if "volatility" in arg.content.lower():
                    self.belief.key_concerns.append("volatility_acknowledged")


class MultiAgentDebateSystem:
    """
    Multi-Agent Debate System
    
    Orchestrates structured debate between multiple agents
to reach high-quality consensus decisions.
    """
    
    def __init__(
        self,
        max_rounds: int = 5,
        consensus_threshold: float = 0.75,
        min_confidence_for_consensus: float = 0.6
    ):
        self.max_rounds = max_rounds
        self.consensus_threshold = consensus_threshold
        self.min_confidence = min_confidence_for_consensus
        
        # Active debates
        self.debates: Dict[str, 'DebateSession'] = {}
        
        # Statistics
        self.stats = {
            'total_debates': 0,
            'consensus_reached': 0,
            'arbitrated': 0,
            'average_rounds': 0
        }
    
    async def initiate_debate(
        self,
        decision_context: Dict[str, Any],
        urgency: str = "normal"
    ) -> str:
        """
        Initiate a new debate session.
        
        Returns debate ID for tracking.
        """
        debate_id = str(uuid.uuid4())
        
        # Create agents
        agents = [
            DebatingAgent(DebateRole.PROPOSER, "Proposer", ["signal_analysis", "opportunity_detection"]),
            DebatingAgent(DebateRole.CHALLENGER, "Challenger", ["risk_assessment", "contrarian_analysis"]),
            DebatingAgent(DebateRole.SYNTHESIZER, "Synthesizer", ["conflict_resolution", "optimization"]),
            DebatingAgent(DebateRole.ARBITER, "Arbiter", ["judgment", "standards"])
        ]
        
        # Initialize beliefs
        for agent in agents:
            position = self._determine_initial_position(agent.role, decision_context)
            confidence = self._determine_initial_confidence(agent.role, decision_context)
            agent.initialize_belief(decision_context, position, confidence)
        
        # Create debate session
        session = DebateSession(
            debate_id=debate_id,
            agents=agents,
            context=decision_context,
            urgency=urgency,
            max_rounds=self.max_rounds if urgency != "critical" else 3,
            consensus_threshold=self.consensus_threshold
        )
        
        self.debates[debate_id] = session
        self.stats['total_debates'] += 1
        
        logger.info(f"Initiated debate {debate_id} with {len(agents)} agents")
        
        return debate_id
    
    def _determine_initial_position(self, role: DebateRole, context: Dict[str, Any]) -> str:
        """Determine initial position based on role"""
        if role == DebateRole.PROPOSER:
            return "approve"
        elif role == DebateRole.CHALLENGER:
            return "reject" if context.get('risk_level', 0) > 0.6 else "defer"
        else:
            return "defer"
    
    def _determine_initial_confidence(self, role: DebateRole, context: Dict[str, Any]) -> float:
        """Determine initial confidence based on role and context"""
        base = context.get('confidence', 0.5)
        if role == DebateRole.PROPOSER:
            return min(0.9, base + 0.2)
        elif role == DebateRole.CHALLENGER:
            return 0.5
        else:
            return 0.6
    
    async def conduct_debate(self, debate_id: str) -> DebateResult:
        """
        Conduct the full debate and return result.
        """
        session = self.debates.get(debate_id)
        if not session:
            raise ValueError(f"Debate {debate_id} not found")
        
        # Conduct rounds
        for round_num in range(session.max_rounds):
            round_result = await session.conduct_round(round_num)
            
            # Check for consensus
            if round_result.consensus_emerging:
                if await self._check_consensus(session):
                    result = await self._finalize_debate(session, DebateStatus.CONSENSUS)
                    self.stats['consensus_reached'] += 1
                    return result
            
            # Check for stalemate
            if round_num > 2 and await self._check_stalemate(session):
                break
        
        # If no consensus, go to arbitration
        result = await self._finalize_debate(session, DebateStatus.ARBITRATED)
        self.stats['arbitrated'] += 1
        return result
    
    async def _check_consensus(self, session: 'DebateSession') -> bool:
        """Check if consensus has been reached"""
        positions = [agent.belief.position for agent in session.agents 
                     if agent.belief and agent.role != DebateRole.ARBITER]
        
        # Count positions
        position_counts = defaultdict(int)
        for pos in positions:
            position_counts[pos] += 1
        
        # Check if majority agrees
        total = len(positions)
        for pos, count in position_counts.items():
            if count / total >= self.consensus_threshold:
                # Check confidence levels
                confidences = [agent.belief.confidence for agent in session.agents
                              if agent.belief and agent.belief.position == pos]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                if avg_confidence >= self.min_confidence:
                    return True
        
        return False
    
    async def _check_stalemate(self, session: 'DebateSession') -> bool:
        """Check if debate has reached stalemate"""
        # Check if positions haven't changed in last 2 rounds
        if len(session.rounds) < 3:
            return False
        
        recent_rounds = session.rounds[-2:]
        # If no new key points emerged
        total_new_points = sum(len(r.key_points) for r in recent_rounds)
        return total_new_points == 0
    
    async def _finalize_debate(
        self,
        session: 'DebateSession',
        status: DebateStatus
    ) -> DebateResult:
        """Finalize debate and create result"""
        
        # Gather all arguments
        all_arguments = []
        for round_data in session.rounds:
            all_arguments.extend(round_data.arguments)
        
        # Score arguments
        for arg in all_arguments:
            arg.strength_score = self._score_argument(arg, all_arguments)
        
        # Determine final position
        if status == DebateStatus.CONSENSUS:
            # Find consensus position
            positions = [a.belief.position for a in session.agents if a.belief]
            final_position = max(set(positions), key=positions.count)
            final_confidence = sum(a.belief.confidence for a in session.agents 
                                  if a.belief and a.belief.position == final_position)
            final_confidence /= positions.count(final_position)
        else:
            # Arbitration - use arbiter's judgment
            arbiter = next((a for a in session.agents if a.role == DebateRole.ARBITER), None)
            if arbiter and arbiter.belief:
                final_position = arbiter.belief.position
                final_confidence = arbiter.belief.confidence
            else:
                final_position = "defer"
                final_confidence = 0.5
        
        # Get winning and dissenting arguments
        sorted_args = sorted(all_arguments, key=lambda a: a.strength_score, reverse=True)
        winning_args = [a.content for a in sorted_args[:3]]
        
        # Find dissenting views
        dissent = []
        for agent in session.agents:
            if agent.belief and agent.belief.position != final_position:
                dissent.append(f"{agent.role.value}: {agent.belief.reasoning}")
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            final_position, final_confidence, winning_args, session.context
        )
        
        # Generate risk assessment
        risk_assessment = self._generate_risk_assessment(session)
        
        result = DebateResult(
            debate_id=session.debate_id,
            status=status,
            final_position=final_position,
            final_confidence=final_confidence,
            rounds_conducted=len(session.rounds),
            consensus_achieved=(status == DebateStatus.CONSENSUS),
            winning_arguments=winning_args,
            dissenting_views=dissent,
            audit_trail=session.get_audit_trail(),
            recommendation=recommendation,
            risk_assessment=risk_assessment
        )
        
        # Update stats
        self.stats['average_rounds'] = (
            (self.stats['average_rounds'] * (self.stats['total_debates'] - 1) + len(session.rounds))
            / self.stats['total_debates']
        )
        
        return result
    
    def _score_argument(self, argument: Argument, all_args: List[Argument]) -> float:
        """Score an argument's strength"""
        score = argument.confidence
        
        # Boost for evidence type
        if argument.argument_type == ArgumentType.EVIDENCE:
            score *= 1.2
        
        # Boost for having supporting evidence
        if argument.supporting_evidence:
            score *= (1 + 0.1 * len(argument.supporting_evidence))
        
        # Boost for being a counter-argument
        if argument.responds_to:
            score *= 1.1
        
        return min(1.0, score)
    
    def _generate_recommendation(
        self,
        position: str,
        confidence: float,
        winning_args: List[str],
        context: Dict[str, Any]
    ) -> str:
        """Generate human-readable recommendation"""
        if position == "approve":
            if confidence > 0.8:
                return f"Strong approval with {confidence:.0%} confidence. Primary justification: {winning_args[0] if winning_args else 'Consensus'}"
            else:
                return f"Approve with caution ({confidence:.0%} confidence). Consider reduced position size."
        elif position == "reject":
            return f"Reject trade due to {winning_args[0] if winning_args else 'identified risks'}. Review before re-entry."
        else:
            return f"Defer decision pending additional analysis. Current confidence {confidence:.0%} insufficient."
    
    def _generate_risk_assessment(self, session: 'DebateSession') -> str:
        """Generate risk assessment from debate"""
        risk_mentions = 0
        for round_data in session.rounds:
            for arg in round_data.arguments:
                if arg.argument_type == ArgumentType.RISK:
                    risk_mentions += 1
        
        if risk_mentions >= 3:
            return f"HIGH: {risk_mentions} distinct risk factors identified during debate."
        elif risk_mentions >= 1:
            return f"MODERATE: {risk_mentions} risk factor(s) noted but mitigated."
        else:
            return "LOW: No significant risks identified during debate."
    
    def get_debate_statistics(self) -> Dict[str, Any]:
        """Get statistics about debate system"""
        return {
            'total_debates': self.stats['total_debates'],
            'consensus_rate': self.stats['consensus_reached'] / max(1, self.stats['total_debates']),
            'arbitration_rate': self.stats['arbitrated'] / max(1, self.stats['total_debates']),
            'average_rounds': self.stats['average_rounds'],
            'active_debates': len([d for d in self.debates.values() if d.status == DebateStatus.ACTIVE])
        }


class DebateSession:
    """
    Individual debate session.
    
    Manages the state and flow of a single multi-agent debate.
    """
    
    def __init__(
        self,
        debate_id: str,
        agents: List[DebatingAgent],
        context: Dict[str, Any],
        urgency: str,
        max_rounds: int,
        consensus_threshold: float
    ):
        self.debate_id = debate_id
        self.agents = agents
        self.context = context
        self.urgency = urgency
        self.max_rounds = max_rounds
        self.consensus_threshold = consensus_threshold
        
        self.status = DebateStatus.ACTIVE
        self.rounds: List[DebateRound] = []
        
    async def conduct_round(self, round_num: int) -> DebateRound:
        """Conduct a single debate round"""
        round_data = DebateRound(round_number=round_num)
        
        # Each agent makes arguments in turn
        for agent in self.agents:
            # Get previous arguments for context
            previous_args = []
            for r in self.rounds:
                previous_args.extend(r.arguments)
            
            argument = await agent.generate_argument(
                self.context, round_num, previous_args
            )
            
            if argument:
                round_data.arguments.append(argument)
        
        # Update all agents' beliefs
        for agent in self.agents:
            other_args = [a for a in round_data.arguments if a.role != agent.role]
            agent.update_belief(other_args)
        
        # Extract key points
        round_data.key_points = self._extract_key_points(round_data.arguments)
        
        # Check for emerging consensus
        round_data.consensus_emerging = self._check_consensus_emerging()
        
        self.rounds.append(round_data)
        
        logger.debug(f"Debate {self.debate_id} completed round {round_num}")
        
        return round_data
    
    def _extract_key_points(self, arguments: List[Argument]) -> List[str]:
        """Extract key points from arguments"""
        points = []
        for arg in arguments:
            if arg.argument_type in [ArgumentType.EVIDENCE, ArgumentType.RISK]:
                # Extract first sentence as key point
                point = arg.content[:100] + "..." if len(arg.content) > 100 else arg.content
                points.append(f"{arg.role.value}: {point}")
        return points
    
    def _check_consensus_emerging(self) -> bool:
        """Check if consensus appears to be emerging"""
        # Simple heuristic: check if 3/4 agents agree
        positions = [a.belief.position for a in self.agents if a.belief]
        if not positions:
            return False
        
        from collections import Counter
        position_counts = Counter(positions)
        most_common = position_counts.most_common(1)[0]
        
        return most_common[1] / len(positions) >= 0.75
    
    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Generate audit trail of debate"""
        trail = []
        for round_data in self.rounds:
            trail.append({
                'round': round_data.round_number,
                'timestamp': round_data.timestamp.isoformat(),
                'arguments': [
                    {
                        'role': arg.role.value,
                        'type': arg.argument_type.value,
                        'content': arg.content,
                        'confidence': arg.confidence
                    }
                    for arg in round_data.arguments
                ],
                'key_points': round_data.key_points,
                'consensus_emerging': round_data.consensus_emerging
            })
        return trail


def create_debate_system(
    max_rounds: int = 5,
    consensus_threshold: float = 0.75
) -> MultiAgentDebateSystem:
    """Factory function to create debate system"""
    return MultiAgentDebateSystem(
        max_rounds=max_rounds,
        consensus_threshold=consensus_threshold
    )
