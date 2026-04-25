"""
Debate Protocol - Structured Multi-Agent Debate
=================================================

Implements structured debate protocols for decision-making:
1. Argumentation framework
2. Evidence-based reasoning
3. Counterargument generation
4. Debate resolution

Based on the Foundation Agents paper (arXiv:2504.01990) multi-agent systems.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


class ArgumentType(Enum):
    """Types of arguments"""
    CLAIM = "claim"                 # Main assertion
    EVIDENCE = "evidence"           # Supporting evidence
    WARRANT = "warrant"             # Reasoning connecting evidence to claim
    BACKING = "backing"             # Support for warrant
    REBUTTAL = "rebuttal"           # Counter-argument
    QUALIFIER = "qualifier"         # Conditions/limitations
    CONCESSION = "concession"       # Acknowledging opponent's point


class ArgumentStrength(Enum):
    """Strength of an argument"""
    VERY_STRONG = 5
    STRONG = 4
    MODERATE = 3
    WEAK = 2
    VERY_WEAK = 1


class DebatePhase(Enum):
    """Phases of a debate"""
    OPENING = "opening"
    ARGUMENTATION = "argumentation"
    REBUTTAL = "rebuttal"
    CLOSING = "closing"
    RESOLUTION = "resolution"


class DebateOutcome(Enum):
    """Possible debate outcomes"""
    PROPOSITION_WINS = "proposition_wins"
    OPPOSITION_WINS = "opposition_wins"
    DRAW = "draw"
    SYNTHESIS = "synthesis"         # New position emerges


@dataclass
class Argument:
    """An argument in a debate"""
    argument_id: str
    argument_type: ArgumentType
    agent_id: str
    
    # Content
    claim: str
    evidence: List[str] = field(default_factory=list)
    reasoning: str = ""
    
    # Strength
    strength: ArgumentStrength = ArgumentStrength.MODERATE
    confidence: float = 0.5
    
    # References
    supports: Optional[str] = None      # Argument ID this supports
    attacks: Optional[str] = None       # Argument ID this attacks
    
    # Evaluation
    votes_for: int = 0
    votes_against: int = 0
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def net_support(self) -> int:
        return self.votes_for - self.votes_against
    
    def to_dict(self) -> Dict:
        return {
            'argument_id': self.argument_id,
            'argument_type': self.argument_type.value,
            'agent_id': self.agent_id,
            'claim': self.claim,
            'evidence': self.evidence,
            'strength': self.strength.value,
            'confidence': self.confidence,
            'net_support': self.net_support()
        }


@dataclass
class DebatePosition:
    """A position in a debate"""
    position_id: str
    name: str
    description: str
    
    # Arguments
    arguments: List[str] = field(default_factory=list)  # Argument IDs
    
    # Supporters
    supporters: List[str] = field(default_factory=list)  # Agent IDs
    
    # Scoring
    total_strength: float = 0.0
    rebuttals_survived: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'position_id': self.position_id,
            'name': self.name,
            'description': self.description,
            'n_arguments': len(self.arguments),
            'n_supporters': len(self.supporters),
            'total_strength': self.total_strength
        }


@dataclass
class Debate:
    """A structured debate"""
    debate_id: str
    topic: str
    description: str
    
    # Positions
    proposition: DebatePosition
    opposition: DebatePosition
    
    # Arguments
    arguments: Dict[str, Argument] = field(default_factory=dict)
    argument_order: List[str] = field(default_factory=list)
    
    # Participants
    moderator_id: Optional[str] = None
    participants: List[str] = field(default_factory=list)
    
    # State
    phase: DebatePhase = DebatePhase.OPENING
    round_number: int = 0
    max_rounds: int = 5
    
    # Outcome
    outcome: Optional[DebateOutcome] = None
    synthesis: Optional[str] = None
    
    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            'debate_id': self.debate_id,
            'topic': self.topic,
            'phase': self.phase.value,
            'round': self.round_number,
            'proposition': self.proposition.to_dict(),
            'opposition': self.opposition.to_dict(),
            'n_arguments': len(self.arguments),
            'outcome': self.outcome.value if self.outcome else None
        }


class ArgumentEvaluator:
    """Evaluates argument strength and validity"""
    
    def evaluate(self, argument: Argument) -> Dict[str, float]:
        """Evaluate an argument"""
        scores = {
            'clarity': self._score_clarity(argument),
            'evidence_quality': self._score_evidence(argument),
            'reasoning': self._score_reasoning(argument),
            'relevance': self._score_relevance(argument)
        }
        
        scores['overall'] = sum(scores.values()) / len(scores)
        
        return scores
    
    def _score_clarity(self, argument: Argument) -> float:
        """Score argument clarity"""
        claim_length = len(argument.claim)
        # Prefer concise but substantive claims
        if 20 <= claim_length <= 200:
            return 0.8
        elif claim_length < 20:
            return 0.5
        else:
            return 0.6
    
    def _score_evidence(self, argument: Argument) -> float:
        """Score evidence quality"""
        n_evidence = len(argument.evidence)
        if n_evidence == 0:
            return 0.3
        elif n_evidence == 1:
            return 0.6
        elif n_evidence <= 3:
            return 0.8
        else:
            return 0.9
    
    def _score_reasoning(self, argument: Argument) -> float:
        """Score reasoning quality"""
        if not argument.reasoning:
            return 0.4
        
        reasoning_length = len(argument.reasoning)
        if reasoning_length > 50:
            return 0.8
        else:
            return 0.6
    
    def _score_relevance(self, argument: Argument) -> float:
        """Score relevance (placeholder)"""
        return argument.confidence


class RebuttalGenerator:
    """Generates rebuttals to arguments"""
    
    def generate_rebuttal(
        self,
        argument: Argument,
        context: Optional[Dict] = None
    ) -> Argument:
        """Generate a rebuttal to an argument"""
        # Identify weak points
        weak_points = self._identify_weak_points(argument)
        
        # Generate counter-claim
        counter_claim = self._generate_counter_claim(argument, weak_points)
        
        # Generate counter-evidence
        counter_evidence = self._generate_counter_evidence(argument)
        
        rebuttal = Argument(
            argument_id=f"reb_{argument.argument_id}_{uuid.uuid4().hex[:6]}",
            argument_type=ArgumentType.REBUTTAL,
            agent_id="rebuttal_generator",
            claim=counter_claim,
            evidence=counter_evidence,
            reasoning=f"Challenges the claim that {argument.claim[:50]}...",
            strength=ArgumentStrength.MODERATE,
            confidence=0.6,
            attacks=argument.argument_id
        )
        
        return rebuttal
    
    def _identify_weak_points(self, argument: Argument) -> List[str]:
        """Identify weak points in an argument"""
        weak_points = []
        
        if not argument.evidence:
            weak_points.append("lack_of_evidence")
        
        if argument.confidence < 0.5:
            weak_points.append("low_confidence")
        
        if argument.strength.value <= 2:
            weak_points.append("weak_claim")
        
        if not argument.reasoning:
            weak_points.append("missing_reasoning")
        
        return weak_points
    
    def _generate_counter_claim(
        self,
        argument: Argument,
        weak_points: List[str]
    ) -> str:
        """Generate a counter-claim"""
        if "lack_of_evidence" in weak_points:
            return f"The claim '{argument.claim[:50]}...' lacks sufficient evidence"
        elif "low_confidence" in weak_points:
            return f"The confidence in '{argument.claim[:50]}...' is not justified"
        else:
            return f"Alternative interpretation challenges: {argument.claim[:50]}..."
    
    def _generate_counter_evidence(self, argument: Argument) -> List[str]:
        """Generate counter-evidence"""
        return [
            "Historical data suggests alternative outcomes",
            "Similar situations have led to different results"
        ]


class DebateProtocol:
    """
    Debate Protocol
    
    Manages structured debates between agents for
    decision-making and knowledge synthesis.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.evaluator = ArgumentEvaluator()
        self.rebuttal_generator = RebuttalGenerator()
        
        # Debates
        self.debates: Dict[str, Debate] = {}
        self.debate_history: List[Debate] = []
        
        # Statistics
        self.stats = {
            'debates_held': 0,
            'arguments_made': 0,
            'rebuttals_generated': 0,
            'syntheses_achieved': 0
        }
        
        logger.info("Debate Protocol initialized")
    
    def create_debate(
        self,
        topic: str,
        proposition_name: str,
        proposition_description: str,
        opposition_name: str,
        opposition_description: str,
        moderator_id: Optional[str] = None,
        max_rounds: int = 5
    ) -> Debate:
        """Create a new debate"""
        debate = Debate(
            debate_id=str(uuid.uuid4())[:8],
            topic=topic,
            description=f"Debate on: {topic}",
            proposition=DebatePosition(
                position_id=f"prop_{uuid.uuid4().hex[:6]}",
                name=proposition_name,
                description=proposition_description
            ),
            opposition=DebatePosition(
                position_id=f"opp_{uuid.uuid4().hex[:6]}",
                name=opposition_name,
                description=opposition_description
            ),
            moderator_id=moderator_id,
            max_rounds=max_rounds
        )
        
        self.debates[debate.debate_id] = debate
        self.stats['debates_held'] += 1
        
        logger.info(f"Created debate: {topic}")
        
        return debate
    
    def add_argument(
        self,
        debate_id: str,
        agent_id: str,
        position: str,  # "proposition" or "opposition"
        claim: str,
        evidence: Optional[List[str]] = None,
        reasoning: str = "",
        strength: ArgumentStrength = ArgumentStrength.MODERATE,
        confidence: float = 0.5,
        supports: Optional[str] = None,
        attacks: Optional[str] = None
    ) -> Optional[Argument]:
        """Add an argument to a debate"""
        if debate_id not in self.debates:
            return None
        
        debate = self.debates[debate_id]
        
        # Determine argument type
        if attacks:
            arg_type = ArgumentType.REBUTTAL
        elif supports:
            arg_type = ArgumentType.EVIDENCE
        else:
            arg_type = ArgumentType.CLAIM
        
        argument = Argument(
            argument_id=f"arg_{uuid.uuid4().hex[:8]}",
            argument_type=arg_type,
            agent_id=agent_id,
            claim=claim,
            evidence=evidence or [],
            reasoning=reasoning,
            strength=strength,
            confidence=confidence,
            supports=supports,
            attacks=attacks
        )
        
        # Add to debate
        debate.arguments[argument.argument_id] = argument
        debate.argument_order.append(argument.argument_id)
        
        # Add to position
        if position == "proposition":
            debate.proposition.arguments.append(argument.argument_id)
            if agent_id not in debate.proposition.supporters:
                debate.proposition.supporters.append(agent_id)
        else:
            debate.opposition.arguments.append(argument.argument_id)
            if agent_id not in debate.opposition.supporters:
                debate.opposition.supporters.append(agent_id)
        
        # Add to participants
        if agent_id not in debate.participants:
            debate.participants.append(agent_id)
        
        self.stats['arguments_made'] += 1
        
        return argument
    
    def generate_rebuttal(
        self,
        debate_id: str,
        argument_id: str,
        agent_id: str
    ) -> Optional[Argument]:
        """Generate a rebuttal to an argument"""
        if debate_id not in self.debates:
            return None
        
        debate = self.debates[debate_id]
        
        if argument_id not in debate.arguments:
            return None
        
        original = debate.arguments[argument_id]
        rebuttal = self.rebuttal_generator.generate_rebuttal(original)
        rebuttal.agent_id = agent_id
        
        # Determine which side the rebuttal supports
        if argument_id in debate.proposition.arguments:
            position = "opposition"
        else:
            position = "proposition"
        
        # Add rebuttal
        debate.arguments[rebuttal.argument_id] = rebuttal
        debate.argument_order.append(rebuttal.argument_id)
        
        if position == "proposition":
            debate.proposition.arguments.append(rebuttal.argument_id)
        else:
            debate.opposition.arguments.append(rebuttal.argument_id)
        
        self.stats['rebuttals_generated'] += 1
        
        return rebuttal
    
    def advance_phase(self, debate_id: str) -> Optional[DebatePhase]:
        """Advance debate to next phase"""
        if debate_id not in self.debates:
            return None
        
        debate = self.debates[debate_id]
        
        phase_order = [
            DebatePhase.OPENING,
            DebatePhase.ARGUMENTATION,
            DebatePhase.REBUTTAL,
            DebatePhase.CLOSING,
            DebatePhase.RESOLUTION
        ]
        
        current_idx = phase_order.index(debate.phase)
        
        if current_idx < len(phase_order) - 1:
            debate.phase = phase_order[current_idx + 1]
            
            if debate.phase == DebatePhase.ARGUMENTATION:
                debate.round_number += 1
        
        return debate.phase
    
    def vote_on_argument(
        self,
        debate_id: str,
        argument_id: str,
        agent_id: str,
        support: bool
    ):
        """Vote on an argument"""
        if debate_id not in self.debates:
            return
        
        debate = self.debates[debate_id]
        
        if argument_id not in debate.arguments:
            return
        
        argument = debate.arguments[argument_id]
        
        if support:
            argument.votes_for += 1
        else:
            argument.votes_against += 1
    
    def evaluate_debate(self, debate_id: str) -> Dict[str, Any]:
        """Evaluate the current state of a debate"""
        if debate_id not in self.debates:
            return {}
        
        debate = self.debates[debate_id]
        
        # Evaluate proposition arguments
        prop_score = 0.0
        for arg_id in debate.proposition.arguments:
            arg = debate.arguments.get(arg_id)
            if arg:
                eval_result = self.evaluator.evaluate(arg)
                prop_score += eval_result['overall'] * arg.strength.value
                prop_score += arg.net_support() * 0.1
        
        # Evaluate opposition arguments
        opp_score = 0.0
        for arg_id in debate.opposition.arguments:
            arg = debate.arguments.get(arg_id)
            if arg:
                eval_result = self.evaluator.evaluate(arg)
                opp_score += eval_result['overall'] * arg.strength.value
                opp_score += arg.net_support() * 0.1
        
        debate.proposition.total_strength = prop_score
        debate.opposition.total_strength = opp_score
        
        return {
            'debate_id': debate_id,
            'proposition_score': prop_score,
            'opposition_score': opp_score,
            'leading': 'proposition' if prop_score > opp_score else 'opposition',
            'margin': abs(prop_score - opp_score),
            'n_arguments': len(debate.arguments),
            'phase': debate.phase.value
        }
    
    def resolve_debate(self, debate_id: str) -> Optional[DebateOutcome]:
        """Resolve a debate and determine outcome"""
        if debate_id not in self.debates:
            return None
        
        debate = self.debates[debate_id]
        evaluation = self.evaluate_debate(debate_id)
        
        prop_score = evaluation['proposition_score']
        opp_score = evaluation['opposition_score']
        margin = evaluation['margin']
        
        # Determine outcome
        if margin < 0.5:
            # Close debate - attempt synthesis
            debate.outcome = DebateOutcome.SYNTHESIS
            debate.synthesis = self._synthesize_positions(debate)
            self.stats['syntheses_achieved'] += 1
        elif prop_score > opp_score:
            debate.outcome = DebateOutcome.PROPOSITION_WINS
        else:
            debate.outcome = DebateOutcome.OPPOSITION_WINS
        
        debate.phase = DebatePhase.RESOLUTION
        debate.ended_at = datetime.utcnow()
        
        self.debate_history.append(debate)
        
        logger.info(f"Debate {debate_id} resolved: {debate.outcome.value}")
        
        return debate.outcome
    
    def _synthesize_positions(self, debate: Debate) -> str:
        """Synthesize a new position from debate"""
        # Extract key points from both sides
        prop_claims = [
            debate.arguments[aid].claim
            for aid in debate.proposition.arguments[:3]
            if aid in debate.arguments
        ]
        
        opp_claims = [
            debate.arguments[aid].claim
            for aid in debate.opposition.arguments[:3]
            if aid in debate.arguments
        ]
        
        synthesis = f"Synthesis of '{debate.topic}':\n"
        synthesis += f"From proposition: {'; '.join(prop_claims[:2])}\n"
        synthesis += f"From opposition: {'; '.join(opp_claims[:2])}\n"
        synthesis += "A balanced view incorporates valid points from both positions."
        
        return synthesis
    
    def get_debate(self, debate_id: str) -> Optional[Debate]:
        """Get debate by ID"""
        return self.debates.get(debate_id)
    
    def get_active_debates(self) -> List[Debate]:
        """Get active debates"""
        return [
            d for d in self.debates.values()
            if d.phase != DebatePhase.RESOLUTION
        ]
    
    def get_debate_transcript(self, debate_id: str) -> List[Dict]:
        """Get transcript of a debate"""
        if debate_id not in self.debates:
            return []
        
        debate = self.debates[debate_id]
        transcript = []
        
        for arg_id in debate.argument_order:
            arg = debate.arguments.get(arg_id)
            if arg:
                # Determine side
                if arg_id in debate.proposition.arguments:
                    side = "proposition"
                else:
                    side = "opposition"
                
                transcript.append({
                    'side': side,
                    'agent_id': arg.agent_id,
                    'type': arg.argument_type.value,
                    'claim': arg.claim,
                    'evidence': arg.evidence,
                    'timestamp': arg.timestamp.isoformat()
                })
        
        return transcript
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get protocol statistics"""
        outcomes = defaultdict(int)
        for debate in self.debate_history:
            if debate.outcome:
                outcomes[debate.outcome.value] += 1
        
        return {
            **self.stats,
            'active_debates': len(self.get_active_debates()),
            'completed_debates': len(self.debate_history),
            'outcomes': dict(outcomes),
            'avg_arguments_per_debate': (
                self.stats['arguments_made'] / max(1, self.stats['debates_held'])
            )
        }
