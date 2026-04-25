"""
Multi-Agent Validation System

Validates signals through multiple specialized agents.
Tracks ensemble disagreement and requires consensus for approval.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of validation agents"""
    TECHNICAL_ANALYST = "technical_analyst"
    FUNDAMENTAL_ANALYST = "fundamental_analyst"
    RISK_ANALYST = "risk_analyst"
    QUANT_ANALYST = "quant_analyst"
    SENTIMENT_ANALYST = "sentiment_analyst"
    MACRO_ANALYST = "macro_analyst"
    REGIME_SPECIALIST = "regime_specialist"
    EXECUTION_SPECIALIST = "execution_specialist"


@dataclass
class AgentValidation:
    """Validation result from a single agent"""
    agent_type: AgentType
    agent_id: str
    approved: bool
    confidence: float
    concerns: List[str]
    supporting_factors: List[str]
    recommendation: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EnsembleConsensus:
    """Consensus from multi-agent validation"""
    overall_approved: bool
    approval_rate: float
    average_confidence: float
    disagreement_index: float  # 0 = unanimous, 1 = maximum disagreement
    agent_validations: List[AgentValidation]
    consensus_recommendation: str
    dissenting_views: List[str]
    required_followup: List[str]


class MultiAgentValidationSystem:
    """
    Multi-agent validation requiring consensus from multiple perspectives.
    
    Each agent evaluates from its specialized viewpoint.
    High disagreement blocks trades.
    """
    
    def __init__(
        self,
        min_agents_required: int = 3,
        min_approval_rate: float = 0.7,
        max_disagreement: float = 0.5,
        min_average_confidence: float = 0.6
    ):
        self.min_agents = min_agents_required
        self.min_approval = min_approval_rate
        self.max_disagreement = max_disagreement
        self.min_confidence = min_average_confidence
        
        # Agent reliability tracking
        self.agent_performance: Dict[str, List[Dict]] = defaultdict(list)
        
    def validate_signal(
        self,
        signal: Dict[str, Any],
        symbol: str,
        market_data: Dict[str, Any],
        regime: Optional[Any] = None
    ) -> EnsembleConsensus:
        """
        Validate signal through multiple agents.
        
        Returns:
            EnsembleConsensus with multi-agent results
        """
        validations = []
        
        # Agent 1: Technical Analyst
        tech_val = self._technical_validation(signal, symbol, market_data)
        validations.append(tech_val)
        
        # Agent 2: Risk Analyst
        risk_val = self._risk_validation(signal, symbol, market_data)
        validations.append(risk_val)
        
        # Agent 3: Quant Analyst
        quant_val = self._quant_validation(signal, symbol, market_data)
        validations.append(quant_val)
        
        # Agent 4: Sentiment Analyst
        sentiment_val = self._sentiment_validation(signal, symbol, market_data)
        validations.append(sentiment_val)
        
        # Agent 5: Execution Specialist
        exec_val = self._execution_validation(signal, symbol, market_data)
        validations.append(exec_val)
        
        # Calculate consensus metrics
        approval_count = sum(1 for v in validations if v.approved)
        approval_rate = approval_count / len(validations) if validations else 0
        
        avg_confidence = sum(v.confidence for v in validations) / len(validations) if validations else 0
        
        # Calculate disagreement
        disagreement = self._calculate_disagreement(validations)
        
        # Determine if consensus is achieved
        overall_approved = (
            len(validations) >= self.min_agents and
            approval_rate >= self.min_approval and
            disagreement <= self.max_disagreement and
            avg_confidence >= self.min_confidence
        )
        
        # Collect dissenting views
        dissenting = [v for v in validations if not v.approved]
        dissenting_views = [
            f"{v.agent_type.value}: {v.recommendation}"
            for v in dissenting
        ]
        
        # Generate consensus recommendation
        consensus_rec = self._generate_consensus_recommendation(
            validations, overall_approved, approval_rate, disagreement
        )
        
        # Determine required follow-up
        followup = self._determine_followup(validations, overall_approved)
        
        return EnsembleConsensus(
            overall_approved=overall_approved,
            approval_rate=approval_rate,
            average_confidence=avg_confidence,
            disagreement_index=disagreement,
            agent_validations=validations,
            consensus_recommendation=consensus_rec,
            dissenting_views=dissenting_views,
            required_followup=followup
        )
    
    def _technical_validation(
        self,
        signal: Dict,
        symbol: str,
        market_data: Dict
    ) -> AgentValidation:
        """Technical analysis agent validation"""
        
        concerns = []
        supporting = []
        
        # Check trend alignment
        price = market_data.get('price', 0)
        ma_50 = market_data.get('ma_50', price)
        ma_200 = market_data.get('ma_200', price)
        
        signal_dir = signal.get('direction', 'hold')
        
        if signal_dir == 'buy':
            if price > ma_50:
                supporting.append("Price above 50-day MA (bullish)")
            else:
                concerns.append("Price below 50-day MA (caution)")
        elif signal_dir == 'sell':
            if price < ma_50:
                supporting.append("Price below 50-day MA (bearish)")
            else:
                concerns.append("Price above 50-day MA (caution)")
                
        # Check for overbought/oversold
        rsi = market_data.get('rsi', 50)
        if signal_dir == 'buy' and rsi > 70:
            concerns.append(f"RSI {rsi:.0f} indicates overbought")
        elif signal_dir == 'sell' and rsi < 30:
            concerns.append(f"RSI {rsi:.0f} indicates oversold")
            
        # Calculate approval and confidence
        approved = len(concerns) < 2
        confidence = 0.7 if approved else 0.4
        
        recommendation = (
            "APPROVE" if approved else "REVIEW"
        ) + f" - {len(supporting)} supporting, {len(concerns)} concerns"
        
        return AgentValidation(
            agent_type=AgentType.TECHNICAL_ANALYST,
            agent_id=f"tech_{symbol}",
            approved=approved,
            confidence=confidence,
            concerns=concerns,
            supporting_factors=supporting,
            recommendation=recommendation
        )
    
    def _risk_validation(
        self,
        signal: Dict,
        symbol: str,
        market_data: Dict
    ) -> AgentValidation:
        """Risk analyst validation"""
        
        concerns = []
        supporting = []
        
        # Check volatility
        volatility = market_data.get('volatility', 0.2)
        if volatility > 0.4:
            concerns.append(f"High volatility {volatility:.1%} increases risk")
        else:
            supporting.append(f"Normal volatility {volatility:.1%}")
            
        # Check signal confidence
        signal_conf = signal.get('confidence', 0.5)
        if signal_conf < 0.6:
            concerns.append(f"Low signal confidence {signal_conf:.0%}")
        else:
            supporting.append(f"Adequate signal confidence {signal_conf:.0%}")
            
        # Check position sizing
        size = signal.get('size', 1.0)
        if size > 2.0:
            concerns.append(f"Large position size {size}x")
            
        approved = len(concerns) < 2 and signal_conf > 0.5
        confidence = signal_conf if approved else signal_conf * 0.5
        
        return AgentValidation(
            agent_type=AgentType.RISK_ANALYST,
            agent_id=f"risk_{symbol}",
            approved=approved,
            confidence=confidence,
            concerns=concerns,
            supporting_factors=supporting,
            recommendation="APPROVE" if approved else "CAUTION - Review risk factors"
        )
    
    def _quant_validation(
        self,
        signal: Dict,
        symbol: str,
        market_data: Dict
    ) -> AgentValidation:
        """Quantitative analyst validation"""
        
        concerns = []
        supporting = []
        
        # Check statistical edge
        z_score = market_data.get('z_score', 0)
        if abs(z_score) > 2:
            supporting.append(f"Statistical anomaly detected (z={z_score:.2f})")
        else:
            concerns.append("No significant statistical edge")
            
        # Check momentum
        momentum = market_data.get('momentum', 0)
        signal_dir = signal.get('direction', 'hold')
        
        if (signal_dir == 'buy' and momentum > 0) or (signal_dir == 'sell' and momentum < 0):
            supporting.append(f"Momentum aligns with signal ({momentum:.2f})")
        elif momentum != 0:
            concerns.append(f"Momentum contradicts signal ({momentum:.2f})")
            
        approved = len(supporting) > len(concerns)
        confidence = 0.65 if approved else 0.45
        
        return AgentValidation(
            agent_type=AgentType.QUANT_ANALYST,
            agent_id=f"quant_{symbol}",
            approved=approved,
            confidence=confidence,
            concerns=concerns,
            supporting_factors=supporting,
            recommendation="APPROVE" if approved else "QUANT EVIDENCE WEAK"
        )
    
    def _sentiment_validation(
        self,
        signal: Dict,
        symbol: str,
        market_data: Dict
    ) -> AgentValidation:
        """Sentiment analyst validation"""
        
        concerns = []
        supporting = []
        
        sentiment = market_data.get('sentiment', 0)
        signal_dir = signal.get('direction', 'hold')
        
        # Check sentiment alignment
        if signal_dir == 'buy' and sentiment > 0.3:
            supporting.append(f"Positive sentiment {sentiment:.1f} supports buy")
        elif signal_dir == 'sell' and sentiment < -0.3:
            supporting.append(f"Negative sentiment {sentiment:.1f} supports sell")
        elif abs(sentiment) < 0.1:
            concerns.append("Neutral sentiment - no directional bias")
        else:
            concerns.append(f"Sentiment ({sentiment:.1f}) contradicts signal")
            
        # Check for extreme sentiment (contrarian signal)
        if abs(sentiment) > 0.8:
            concerns.append(f"Extreme sentiment {sentiment:.1f} - potential contrarian signal")
            
        approved = len(supporting) > 0
        confidence = 0.6 + abs(sentiment) * 0.2 if approved else 0.4
        
        return AgentValidation(
            agent_type=AgentType.SENTIMENT_ANALYST,
            agent_id=f"sent_{symbol}",
            approved=approved,
            confidence=min(0.9, confidence),
            concerns=concerns,
            supporting_factors=supporting,
            recommendation="APPROVE" if approved else "SENTIMENT MISALIGNMENT"
        )
    
    def _execution_validation(
        self,
        signal: Dict,
        symbol: str,
        market_data: Dict
    ) -> AgentValidation:
        """Execution specialist validation"""
        
        concerns = []
        supporting = []
        
        # Check liquidity
        volume = market_data.get('volume', 0)
        avg_volume = market_data.get('avg_volume', volume)
        
        if volume < avg_volume * 0.5:
            concerns.append(f"Low volume {volume/avg_volume:.0%} of average")
        else:
            supporting.append("Adequate volume for execution")
            
        # Check spread
        spread = market_data.get('spread_bps', 10)
        if spread > 50:
            concerns.append(f"Wide spread {spread:.0f} bps increases costs")
        else:
            supporting.append(f"Normal spread {spread:.0f} bps")
            
        # Check position size vs liquidity
        size = signal.get('size', 1.0)
        if size * 10000 > volume * 0.1:  # Assume $10k per unit
            concerns.append("Position size large relative to volume")
            
        approved = len(concerns) < 2
        confidence = 0.7 if approved else 0.5
        
        return AgentValidation(
            agent_type=AgentType.EXECUTION_SPECIALIST,
            agent_id=f"exec_{symbol}",
            approved=approved,
            confidence=confidence,
            concerns=concerns,
            supporting_factors=supporting,
            recommendation="EXECUTION FEASIBLE" if approved else "EXECUTION RISKY"
        )
    
    def _calculate_disagreement(
        self,
        validations: List[AgentValidation]
    ) -> float:
        """Calculate disagreement index among agents"""
        
        if len(validations) < 2:
            return 0.0
            
        # Count approvals and rejections
        approvals = sum(1 for v in validations if v.approved)
        rejections = len(validations) - approvals
        
        # Disagreement is high when split is even
        total = len(validations)
        approval_pct = approvals / total
        
        # Entropy-based disagreement
        from math import log2
        if approval_pct in [0, 1]:
            return 0.0
        
        entropy = -(approval_pct * log2(approval_pct) + 
                   (1 - approval_pct) * log2(1 - approval_pct))
        
        # Normalize (max entropy for binary is 1)
        return entropy
    
    def _generate_consensus_recommendation(
        self,
        validations: List[AgentValidation],
        overall_approved: bool,
        approval_rate: float,
        disagreement: float
    ) -> str:
        """Generate consensus recommendation text"""
        
        if overall_approved:
            return (
                f"CONSENSUS APPROVE: {approval_rate:.0%} agreement, "
                f"disagreement {disagreement:.2f}"
            )
        elif approval_rate < self.min_approval:
            return (
                f"CONSENSUS REJECT: Only {approval_rate:.0%} approval "
                f"(need {self.min_approval:.0%})"
            )
        elif disagreement > self.max_disagreement:
            return (
                f"CONSENSUS DEFER: High disagreement {disagreement:.2f} "
                f"(max {self.max_disagreement:.2f})"
            )
        else:
            return (
                f"CONSENSUS DEFER: {approval_rate:.0%} approval but "
                f"other constraints not met"
            )
    
    def _determine_followup(
        self,
        validations: List[AgentValidation],
        overall_approved: bool
    ) -> List[str]:
        """Determine required follow-up actions"""
        
        followup = []
        
        if not overall_approved:
            # Collect concerns from all agents
            for v in validations:
                if v.concerns:
                    followup.append(
                        f"{v.agent_type.value}: Address {v.concerns[0]}"
                    )
                    
        return followup
    
    def record_agent_outcome(
        self,
        agent_id: str,
        prediction: Dict,
        actual: Dict
    ) -> None:
        """Record outcome for agent reliability tracking"""
        
        correct = (
            (prediction.get('approved') and actual.get('pnl', 0) > 0) or
            (not prediction.get('approved') and actual.get('pnl', 0) <= 0)
        )
        
        self.agent_performance[agent_id].append({
            'timestamp': datetime.utcnow(),
            'correct': correct,
            'confidence': prediction.get('confidence', 0),
            'pnl': actual.get('pnl', 0)
        })
        
    def get_agent_reliability(
        self,
        agent_id: str,
        min_samples: int = 10
    ) -> Optional[float]:
        """Get reliability score for an agent"""
        
        history = self.agent_performance.get(agent_id, [])
        
        if len(history) < min_samples:
            return None
            
        recent = history[-50:]  # Last 50 predictions
        correct_count = sum(1 for h in recent if h['correct'])
        
        return correct_count / len(recent)
