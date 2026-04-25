"""
Intelligence Agent - LLM Reasoning Layer
=========================================

Provides human-like reasoning and narrative generation:
- Trade narrative generation
- Thesis development
- Risk briefs
- Human-in-loop explanations
- Audit trail generation
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


@dataclass
class TradeNarrative:
    """A narrative explaining a trade decision"""
    narrative_id: str
    timestamp: datetime
    title: str
    thesis: str
    supporting_evidence: List[str]
    risk_factors: List[str]
    expected_outcome: str
    confidence_explanation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'narrative_id': self.narrative_id,
            'timestamp': self.timestamp.isoformat(),
            'title': self.title,
            'thesis': self.thesis,
            'supporting_evidence': self.supporting_evidence,
            'risk_factors': self.risk_factors,
            'expected_outcome': self.expected_outcome,
            'confidence_explanation': self.confidence_explanation,
        }


@dataclass
class RiskBrief:
    """A risk assessment brief"""
    brief_id: str
    timestamp: datetime
    overall_assessment: str
    key_risks: List[str]
    mitigation_strategies: List[str]
    risk_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'brief_id': self.brief_id,
            'timestamp': self.timestamp.isoformat(),
            'overall_assessment': self.overall_assessment,
            'key_risks': self.key_risks,
            'mitigation_strategies': self.mitigation_strategies,
            'risk_score': self.risk_score,
        }


class IntelligenceAgent:
    """
    Intelligence Agent - LLM Reasoning Layer
    
    Provides human-readable explanations and reasoning for:
    - Trade decisions
    - Risk assessments
    - Market conditions
    - Strategy recommendations
    """
    
    def __init__(self, meta_orchestrator: Any):
        self.agent_id = f"INTEL-{uuid.uuid4().hex[:8]}"
        self.meta_orchestrator = meta_orchestrator
        
        # Register with orchestrator
        self.meta_orchestrator.register_agent("IntelligenceAgent", self)
        
        # Narrative history
        self.narratives: List[TradeNarrative] = []
        self.risk_briefs: List[RiskBrief] = []
        
        # Metrics
        self.narratives_generated = 0
        self.briefs_generated = 0
        
        logger.info(f"IntelligenceAgent initialized: {self.agent_id}")
    
    async def generate_trade_narrative(
        self,
        strategy_analysis: Dict[str, Any],
        simulation_results: Dict[str, Any],
        risk_assessment: Dict[str, Any],
    ) -> TradeNarrative:
        """
        Generate a comprehensive trade narrative.
        
        Explains WHY a trade makes sense in human terms.
        """
        # Submit request to orchestrator
        request = await self.meta_orchestrator.submit_request(
            agent_name="IntelligenceAgent",
            request_type="generate_narrative",
            payload={'strategy': strategy_analysis.get('strategy_name')},
            requires_approval=False,
        )
        
        # Extract key information
        bull_thesis = strategy_analysis.get('bull_thesis', [])
        bear_thesis = strategy_analysis.get('bear_thesis', [])
        simulation_outcome = simulation_results.get('expected_outcome', 'neutral')
        risk_level = risk_assessment.get('overall_risk_level', 'moderate')
        
        # Generate title
        action = strategy_analysis.get('recommended_action', 'hold')
        symbol = strategy_analysis.get('symbol', 'MARKET')
        title = f"{action.upper()} {symbol}: {simulation_outcome.title()} Outlook"
        
        # Generate thesis
        if action == 'buy':
            thesis = f"Initiating long position in {symbol} based on {len(bull_thesis)} supporting factors. "
            thesis += f"Simulation analysis indicates {simulation_outcome} outcome with "
            thesis += f"{risk_level} risk profile. "
            thesis += "Key drivers include: " + ", ".join(bull_thesis[:3]) + "."
        elif action == 'sell':
            thesis = f"Reducing/shorting {symbol} exposure based on {len(bear_thesis)} risk factors. "
            thesis += f"Simulation suggests {simulation_outcome} scenario with "
            thesis += f"{risk_level} risk. "
            thesis += "Primary concerns: " + ", ".join(bear_thesis[:3]) + "."
        else:
            thesis = f"Maintaining current {symbol} position. "
            thesis += "No compelling signal for action at this time. "
            thesis += f"Risk remains {risk_level}."
        
        # Supporting evidence
        evidence = []
        evidence.extend(bull_thesis[:3])
        evidence.append(f"Monte Carlo simulation: {simulation_results.get('monte_carlo', {}).get('statistics', {}).get('prob_profit', 0.5):.0%} probability of profit")
        evidence.append(f"Risk assessment: {risk_level} risk level")
        
        # Risk factors
        risks = []
        risks.extend(bear_thesis[:3])
        risks.extend(risk_assessment.get('warnings', [])[:2])
        
        # Expected outcome
        expected = f"Based on {simulation_results.get('monte_carlo', {}).get('statistics', {}).get('mean_return', 0):.1%} expected return "
        expected += f"with {risk_assessment.get('risk_metrics', {}).get('max_drawdown', 0):.1%} max drawdown potential."
        
        # Confidence explanation
        confidence = strategy_analysis.get('confidence', 0.5)
        if confidence > 0.7:
            conf_exp = f"High confidence ({confidence:.0%}) due to strong signal alignment across multiple agents and favorable simulation outcomes."
        elif confidence > 0.5:
            conf_exp = f"Moderate confidence ({confidence:.0%}) with some conflicting signals but overall positive thesis."
        else:
            conf_exp = f"Low confidence ({confidence:.0%}) due to mixed signals and uncertain market conditions."
        
        narrative = TradeNarrative(
            narrative_id=f"NAR-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            title=title,
            thesis=thesis,
            supporting_evidence=evidence,
            risk_factors=risks,
            expected_outcome=expected,
            confidence_explanation=conf_exp,
        )
        
        self.narratives.append(narrative)
        self.narratives_generated += 1
        
        return narrative
    
    async def generate_risk_brief(
        self,
        risk_assessment: Dict[str, Any],
        portfolio: Dict[str, Any],
    ) -> RiskBrief:
        """Generate a risk assessment brief"""
        # Submit request to orchestrator
        request = await self.meta_orchestrator.submit_request(
            agent_name="IntelligenceAgent",
            request_type="generate_risk_brief",
            payload={'portfolio_value': portfolio.get('total_value', 0)},
            requires_approval=False,
        )
        
        # Extract risk information
        risk_level = risk_assessment.get('overall_risk_level', 'moderate')
        risk_score = risk_assessment.get('risk_score', 50)
        warnings = risk_assessment.get('warnings', [])
        mitigations = risk_assessment.get('mitigations', [])
        
        # Generate overall assessment
        if risk_score > 80:
            assessment = f"EXTREME RISK: Portfolio faces significant threats requiring immediate attention. "
        elif risk_score > 60:
            assessment = f"HIGH RISK: Elevated risk levels warrant defensive positioning. "
        elif risk_score > 40:
            assessment = f"MODERATE RISK: Balanced risk profile with manageable exposures. "
        else:
            assessment = f"LOW RISK: Conservative positioning with limited downside. "
        
        assessment += f"Risk score: {risk_score:.0f}/100. "
        
        # Add VaR context
        var_95 = risk_assessment.get('risk_metrics', {}).get('var_95', 0)
        portfolio_value = portfolio.get('total_value', 1)
        var_pct = (var_95 / portfolio_value * 100) if portfolio_value > 0 else 0
        assessment += f"Daily VaR (95%): {var_pct:.2f}% of portfolio."
        
        brief = RiskBrief(
            brief_id=f"BRIEF-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            overall_assessment=assessment,
            key_risks=warnings[:5],
            mitigation_strategies=mitigations[:5],
            risk_score=risk_score,
        )
        
        self.risk_briefs.append(brief)
        self.briefs_generated += 1
        
        return brief
    
    async def explain_decision(
        self,
        decision: Dict[str, Any],
        context: Dict[str, Any],
    ) -> str:
        """Generate human-readable explanation of a decision"""
        action = decision.get('action', 'hold')
        symbol = decision.get('symbol', 'UNKNOWN')
        confidence = decision.get('confidence', 0.5)
        reasons = decision.get('reasons', [])
        
        explanation = f"**Decision: {action.upper()} {symbol}**\n\n"
        explanation += f"Confidence: {confidence:.0%}\n\n"
        explanation += "**Reasoning:**\n"
        
        for i, reason in enumerate(reasons[:5], 1):
            explanation += f"{i}. {reason}\n"
        
        explanation += f"\n**Market Context:**\n"
        regime = context.get('regime', 'unknown')
        explanation += f"- Current regime: {regime}\n"
        explanation += f"- Volatility: {context.get('volatility', 0):.1%}\n"
        
        return explanation
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'agent_id': self.agent_id,
            'narratives_generated': self.narratives_generated,
            'briefs_generated': self.briefs_generated,
        }
