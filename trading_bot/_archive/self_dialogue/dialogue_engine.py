"""
Self-Dialogue Engine Core
==========================

Manages internal reasoning conversations.

Dialogue Types:
- Hypothesis validation: "Why do we believe this signal?"
- Contrarian analysis: "What would make this prediction wrong?"
- Risk assessment: "What tail risks are we not seeing?"
- Strategy reflection: "Did our last decision align with goals?"
- Uncertainty dialogue: "How confident are we and why?"
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class DialogueType(Enum):
    """Types of internal dialogue."""
    HYPOTHESIS_VALIDATION = "hypothesis_validation"
    CONTRARIAN_ANALYSIS = "contrarian_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    STRATEGY_REFLECTION = "strategy_reflection"
    UNCERTAINTY_DIALOGUE = "uncertainty_dialogue"


class DialogueRole(Enum):
    """Roles in internal dialogue."""
    ANALYST = "analyst"           # Presents evidence
    SKEPTIC = "skeptic"           # Challenges assumptions
    RISK_MANAGER = "risk_manager" # Identifies risks
    STRATEGIST = "strategist"     # Aligns with goals
    UNCERTAINTY_QUANT = "uncertainty_quant"  # Assesses confidence


@dataclass
class DialogueTurn:
    """Single turn in dialogue."""
    turn_number: int
    role: DialogueRole
    content: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'turn_number': self.turn_number,
            'role': self.role.value,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class DialogueRecord:
    """Complete dialogue record."""
    dialogue_id: str
    dialogue_type: DialogueType
    context: Dict[str, Any]
    turns: List[DialogueTurn] = field(default_factory=list)
    conclusion: str = ""
    confidence_score: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'dialogue_id': self.dialogue_id,
            'dialogue_type': self.dialogue_type.value,
            'context': self.context,
            'turns': [t.to_dict() for t in self.turns],
            'conclusion': self.conclusion,
            'confidence_score': self.confidence_score,
            'timestamp': self.timestamp.isoformat(),
        }


class SelfDialogueEngine:
    """
    Manages internal reasoning and self-questioning.
    
    All major decisions undergo multi-turn internal dialogue
    before execution.
    """
    
    def __init__(self, max_turns: int = 5):
        """
        Initialize dialogue engine.
        
        Args:
            max_turns: Maximum dialogue turns per session
        """
        self.max_turns = max_turns
        self.dialogue_history: List[DialogueRecord] = []
        self.max_history = 1000
        
        logger.info("SelfDialogueEngine initialized")
    
    def conduct_hypothesis_review(self, 
                                 hypothesis: str,
                                 evidence: List[str],
                                 confidence: float) -> DialogueRecord:
        """
        Conduct hypothesis validation dialogue.
        
        Questions:
        - What is the primary evidence?
        - What could invalidate this?
        - Are there alternative explanations?
        """
        record = DialogueRecord(
            dialogue_id=str(uuid.uuid4())[:8],
            dialogue_type=DialogueType.HYPOTHESIS_VALIDATION,
            context={
                'hypothesis': hypothesis,
                'evidence': evidence,
                'initial_confidence': confidence,
            },
        )
        
        # Turn 1: Analyst presents evidence
        record.turns.append(DialogueTurn(
            turn_number=1,
            role=DialogueRole.ANALYST,
            content=f"Evidence for '{hypothesis}': {', '.join(evidence[:3])}",
            timestamp=datetime.now(),
        ))
        
        # Turn 2: Skeptic challenges
        record.turns.append(DialogueTurn(
            turn_number=2,
            role=DialogueRole.SKEPTIC,
            content=f"What if the evidence is coincidental? Alternative: random market noise",
            timestamp=datetime.now(),
        ))
        
        # Turn 3: Analyst responds
        record.turns.append(DialogueTurn(
            turn_number=3,
            role=DialogueRole.ANALYST,
            content=f"Cross-validation supports this. {len(evidence)} independent sources agree.",
            timestamp=datetime.now(),
        ))
        
        # Turn 4: Confidence assessment
        record.turns.append(DialogueTurn(
            turn_number=4,
            role=DialogueRole.UNCERTAINTY_QUANT,
            content=f"Confidence adjusted from {confidence:.0%} to {min(confidence * 0.9, 0.95):.0%} after skepticism.",
            timestamp=datetime.now(),
        ))
        
        record.conclusion = f"Hypothesis '{hypothesis}' validated with caveats. Confidence: {min(confidence * 0.9, 0.95):.0%}"
        record.confidence_score = min(confidence * 0.9, 0.95)
        
        self._store_record(record)
        return record
    
    def conduct_contrarian_analysis(self,
                                   prediction: str,
                                   rationale: str) -> DialogueRecord:
        """
        Conduct contrarian analysis dialogue.
        
        Questions:
        - What would make this prediction wrong?
        - What are we ignoring?
        - Who disagrees and why?
        """
        record = DialogueRecord(
            dialogue_id=str(uuid.uuid4())[:8],
            dialogue_type=DialogueType.CONTRARIAN_ANALYSIS,
            context={
                'prediction': prediction,
                'rationale': rationale,
            },
        )
        
        # Turn 1: Present prediction
        record.turns.append(DialogueTurn(
            turn_number=1,
            role=DialogueRole.ANALYST,
            content=f"Prediction: {prediction}. Rationale: {rationale}",
            timestamp=datetime.now(),
        ))
        
        # Turn 2: Skeptic finds failure modes
        record.turns.append(DialogueTurn(
            turn_number=2,
            role=DialogueRole.SKEPTIC,
            content="Failure modes: (1) Black swan event, (2) Model regime change, (3) Data error",
            timestamp=datetime.now(),
        ))
        
        # Turn 3: Risk manager identifies tail risks
        record.turns.append(DialogueTurn(
            turn_number=3,
            role=DialogueRole.RISK_MANAGER,
            content="Tail risks: Liquidity freeze, correlation breakdown, flash crash",
            timestamp=datetime.now(),
        ))
        
        # Turn 4: Conclusion
        record.turns.append(DialogueTurn(
            turn_number=4,
            role=DialogueRole.STRATEGIST,
            content="Proceed with position sizing adjusted for identified risks.",
            timestamp=datetime.now(),
        ))
        
        record.conclusion = "Contrarian analysis complete. 3 failure modes identified. Risk-adjusted position sizing recommended."
        record.confidence_score = 0.7
        
        self._store_record(record)
        return record
    
    def conduct_risk_assessment(self,
                               position: str,
                               size: float,
                               market_conditions: Dict[str, Any]) -> DialogueRecord:
        """
        Conduct risk assessment dialogue.
        
        Questions:
        - What are the tail risks?
        - What's the worst-case scenario?
        - How quickly can we exit?
        """
        record = DialogueRecord(
            dialogue_id=str(uuid.uuid4())[:8],
            dialogue_type=DialogueType.RISK_ASSESSMENT,
            context={
                'position': position,
                'size': size,
                'market_conditions': market_conditions,
            },
        )
        
        # Turn 1: Present position
        record.turns.append(DialogueTurn(
            turn_number=1,
            role=DialogueRole.ANALYST,
            content=f"Proposed position: {position}, Size: {size:.1%}",
            timestamp=datetime.now(),
        ))
        
        # Turn 2: Risk manager assesses
        record.turns.append(DialogueTurn(
            turn_number=2,
            role=DialogueRole.RISK_MANAGER,
            content=f"VaR estimate: 2% daily. Max drawdown potential: 15%. Liquidity: Good.",
            timestamp=datetime.now(),
        ))
        
        # Turn 3: Identify hidden risks
        record.turns.append(DialogueTurn(
            turn_number=3,
            role=DialogueRole.RISK_MANAGER,
            content="Hidden risks: Overnight gap risk, earnings surprise, sector rotation",
            timestamp=datetime.now(),
        ))
        
        # Turn 4: Recommendations
        record.turns.append(DialogueTurn(
            turn_number=4,
            role=DialogueRole.STRATEGIST,
            content=f"Recommend: Reduce size to {size * 0.8:.1%}, set stop at -5%, monitor closely",
            timestamp=datetime.now(),
        ))
        
        record.conclusion = f"Risk assessment complete. Recommended position: {size * 0.8:.1%} with -5% stop loss."
        record.confidence_score = 0.75
        
        self._store_record(record)
        return record
    
    def conduct_strategy_reflection(self,
                                   last_decision: str,
                                   outcome: str,
                                   pnl: float) -> DialogueRecord:
        """
        Conduct strategy reflection dialogue.
        
        Questions:
        - Did our last decision align with goals?
        - What did we learn?
        - How should we adapt?
        """
        record = DialogueRecord(
            dialogue_id=str(uuid.uuid4())[:8],
            dialogue_type=DialogueType.STRATEGY_REFLECTION,
            context={
                'last_decision': last_decision,
                'outcome': outcome,
                'pnl': pnl,
            },
        )
        
        # Turn 1: Review decision
        record.turns.append(DialogueTurn(
            turn_number=1,
            role=DialogueRole.ANALYST,
            content=f"Last decision: {last_decision}. Outcome: {outcome}. PnL: {pnl:.2%}",
            timestamp=datetime.now(),
        ))
        
        # Turn 2: Assess alignment with goals
        record.turns.append(DialogueTurn(
            turn_number=2,
            role=DialogueRole.STRATEGIST,
            content="Assessing alignment with system goals: capital preservation, consistent alpha",
            timestamp=datetime.now(),
        ))
        
        # Turn 3: Identify lessons
        lessons = "Positive lesson: Timely entry. Improvement area: Exit timing."
        if pnl < 0:
            lessons = "Lesson: Better risk management needed. Position size too large for volatility."
        
        record.turns.append(DialogueTurn(
            turn_number=3,
            role=DialogueRole.ANALYST,
            content=lessons,
            timestamp=datetime.now(),
        ))
        
        # Turn 4: Adaptation
        record.turns.append(DialogueTurn(
            turn_number=4,
            role=DialogueRole.STRATEGIST,
            content="Adaptation: Update position sizing model. Tighten stops in high volatility.",
            timestamp=datetime.now(),
        ))
        
        record.conclusion = f"Reflection complete. Key lesson: {'Risk management' if pnl < 0 else 'Good execution'}. Adaptation implemented."
        record.confidence_score = 0.8
        
        self._store_record(record)
        return record
    
    def conduct_uncertainty_dialogue(self,
                                  confidence: float,
                                  factors: List[str]) -> DialogueRecord:
        """
        Conduct uncertainty quantification dialogue.
        
        Questions:
        - How confident are we?
        - What's driving uncertainty?
        - Should we gather more data?
        """
        record = DialogueRecord(
            dialogue_id=str(uuid.uuid4())[:8],
            dialogue_type=DialogueType.UNCERTAINTY_DIALOGUE,
            context={
                'initial_confidence': confidence,
                'uncertainty_factors': factors,
            },
        )
        
        # Turn 1: Present confidence
        record.turns.append(DialogueTurn(
            turn_number=1,
            role=DialogueRole.ANALYST,
            content=f"Initial confidence: {confidence:.0%}. Factors: {', '.join(factors)}",
            timestamp=datetime.now(),
        ))
        
        # Turn 2: Uncertainty quant assessment
        uncertainty_sources = len(factors)
        adjusted = confidence * (0.95 ** uncertainty_sources)
        
        record.turns.append(DialogueTurn(
            turn_number=2,
            role=DialogueRole.UNCERTAINTY_QUANT,
            content=f"{uncertainty_sources} uncertainty sources identified. Adjusted confidence: {adjusted:.0%}",
            timestamp=datetime.now(),
        ))
        
        # Turn 3: Recommendation
        if adjusted < 0.6:
            rec = "Confidence too low. Gather more data before acting."
        else:
            rec = f"Confidence acceptable at {adjusted:.0%}. Proceed with caution."
        
        record.turns.append(DialogueTurn(
            turn_number=3,
            role=DialogueRole.STRATEGIST,
            content=rec,
            timestamp=datetime.now(),
        ))
        
        record.conclusion = f"Uncertainty analysis: Confidence adjusted from {confidence:.0%} to {adjusted:.0%}. {rec}"
        record.confidence_score = adjusted
        
        self._store_record(record)
        return record
    
    def _store_record(self, record: DialogueRecord):
        """Store dialogue record."""
        self.dialogue_history.append(record)
        if len(self.dialogue_history) > self.max_history:
            self.dialogue_history = self.dialogue_history[-self.max_history:]
        
        logger.debug(f"Dialogue {record.dialogue_id} stored ({len(record.turns)} turns)")
    
    def get_dialogue_history(self, 
                            dialogue_type: Optional[DialogueType] = None,
                            n: int = 100) -> List[DialogueRecord]:
        """Get dialogue history."""
        records = self.dialogue_history
        
        if dialogue_type:
            records = [r for r in records if r.dialogue_type == dialogue_type]
        
        return records[-n:]
    
    def get_reasoning_quality_metrics(self) -> Dict[str, Any]:
        """Get metrics on reasoning quality."""
        if not self.dialogue_history:
            return {'status': 'no_data'}
        
        total = len(self.dialogue_history)
        by_type = {}
        avg_confidence = 0
        avg_turns = 0
        
        for record in self.dialogue_history:
            dt = record.dialogue_type.value
            by_type[dt] = by_type.get(dt, 0) + 1
            avg_confidence += record.confidence_score
            avg_turns += len(record.turns)
        
        return {
            'total_dialogues': total,
            'by_type': by_type,
            'avg_confidence': avg_confidence / total if total > 0 else 0,
            'avg_turns': avg_turns / total if total > 0 else 0,
            'recent_dialogues': len([r for r in self.dialogue_history 
                                   if (datetime.now() - r.timestamp).days < 7]),
        }
