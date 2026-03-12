"""
Multi-Brain Ensemble Architecture
Multiple specialized AI agents with collective intelligence
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from collections import defaultdict
import numpy
import pandas

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Specialized agent roles"""
    COMMANDER = "commander"  # Master decision maker
    MACRO_ANALYST = "macro_analyst"
    TECHNICAL_ANALYST = "technical_analyst"
    SENTIMENT_ANALYST = "sentiment_analyst"
    RISK_MANAGER = "risk_manager"
    EXECUTION_SPECIALIST = "execution_specialist"
    PATTERN_HUNTER = "pattern_hunter"
    REGIME_DETECTOR = "regime_detector"
    MANIPULATION_DETECTOR = "manipulation_detector"
    NEWS_ANALYST = "news_analyst"
    ORDER_FLOW_ANALYST = "order_flow_analyst"
    VOLATILITY_TRADER = "volatility_trader"


class VoteWeight(Enum):
    """Vote weighting"""
    UNANIMOUS = "unanimous"  # All must agree
    MAJORITY = "majority"  # >50%
    SUPERMAJORITY = "supermajority"  # >66%
    WEIGHTED = "weighted"  # Based on agent confidence
    COMMANDER_VETO = "commander_veto"  # Commander can override


@dataclass
class AgentOpinion:
    """An agent's opinion on a decision"""
    agent_id: str
    agent_role: AgentRole
    
    # Decision
    recommendation: str  # BUY, SELL, HOLD
    conviction: float  # 0-100
    confidence: float  # 0-1
    
    # Reasoning
    reasoning: str
    supporting_evidence: List[str]
    concerns: List[str]
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CollectiveDecision:
    """Result of collective intelligence"""
    decision: str  # Final decision
    consensus_strength: float  # How much agreement
    
    # Voting breakdown
    votes_buy: int
    votes_sell: int
    votes_hold: int
    
    # Agent opinions
    opinions: List[AgentOpinion]
    
    # Reasoning
    majority_reasoning: str
    minority_concerns: List[str]
    
    # Confidence
    collective_confidence: float
    debate_quality: float  # How thorough was the debate
    
    timestamp: datetime = field(default_factory=datetime.now)


class SpecializedAgent:
    """
    A specialized AI agent with specific expertise
    """
    
    def __init__(self, agent_id: str, role: AgentRole, expertise_level: float = 0.7):
        try:
            self.agent_id = agent_id
            self.role = role
            self.expertise_level = expertise_level
        
            # Performance tracking
            self.correct_predictions = 0
            self.total_predictions = 0
            self.accuracy = 0.0
        
            # Learning
            self.knowledge_base: Dict[str, Any] = {}
            self.recent_performance: List[float] = []
        
            logger.info(f"Initialized {role.value} agent: {agent_id}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(self, market_data: Dict[str, Any]) -> AgentOpinion:
        """
        Analyze market and provide opinion
        Each agent has different analysis logic based on role
        """
        
        try:
            if self.role == AgentRole.MACRO_ANALYST:
                return self._analyze_macro(market_data)
            elif self.role == AgentRole.TECHNICAL_ANALYST:
                return self._analyze_technical(market_data)
            elif self.role == AgentRole.SENTIMENT_ANALYST:
                return self._analyze_sentiment(market_data)
            elif self.role == AgentRole.RISK_MANAGER:
                return self._analyze_risk(market_data)
            elif self.role == AgentRole.PATTERN_HUNTER:
                return self._hunt_patterns(market_data)
            elif self.role == AgentRole.REGIME_DETECTOR:
                return self._detect_regime(market_data)
            elif self.role == AgentRole.MANIPULATION_DETECTOR:
                return self._detect_manipulation(market_data)
            elif self.role == AgentRole.ORDER_FLOW_ANALYST:
                return self._analyze_order_flow(market_data)
            else:
                return self._generic_analysis(market_data)
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
    
    def _analyze_macro(self, data: Dict[str, Any]) -> AgentOpinion:
        """Macro analysis"""
        
        try:
            macro = data.get('macro', {})
        
            # Analyze GDP, inflation, Fed policy
            gdp_growth = macro.get('gdp_growth', 0)
            cpi = macro.get('cpi', 0)
            fed_stance = macro.get('fed_stance', 'neutral')
        
            # Simple logic
            score = 0
            evidence = []
        
            if gdp_growth > 2.5:
                score += 1
                evidence.append(f"Strong GDP growth: {gdp_growth}%")
        
            if cpi < 3.0:
                score += 1
                evidence.append(f"Inflation under control: {cpi}%")
        
            if fed_stance == 'dovish':
                score += 1
                evidence.append("Fed is dovish - supportive")
            elif fed_stance == 'hawkish':
                score -= 1
                evidence.append("Fed is hawkish - headwind")
        
            # Decision
            if score >= 2:
                recommendation = "BUY"
                conviction = min(100, 60 + score * 10)
            elif score <= -1:
                recommendation = "SELL"
                conviction = min(100, 60 + abs(score) * 10)
            else:
                recommendation = "HOLD"
                conviction = 50
        
            return AgentOpinion(
                agent_id=self.agent_id,
                agent_role=self.role,
                recommendation=recommendation,
                conviction=conviction,
                confidence=self.expertise_level,
                reasoning=f"Macro score: {score}/3",
                supporting_evidence=evidence,
                concerns=[]
            )
        except Exception as e:
            logger.error(f"Error in _analyze_macro: {e}")
            raise
    
    def _analyze_technical(self, data: Dict[str, Any]) -> AgentOpinion:
        """Technical analysis"""
        
        try:
            micro = data.get('microstructure', {})
        
            price = micro.get('price', 100)
            vpoc = micro.get('vpoc', 100)
            delta = micro.get('cumulative_delta', 0)
        
            evidence = []
            score = 0
        
            # Price vs VPOC
            if price > vpoc * 1.01:
                score += 1
                evidence.append(f"Price above VPOC: {price} > {vpoc}")
            elif price < vpoc * 0.99:
                score -= 1
                evidence.append(f"Price below VPOC: {price} < {vpoc}")
        
            # Delta
            if delta > 1000:
                score += 1
                evidence.append(f"Positive delta: {delta}")
            elif delta < -1000:
                score -= 1
                evidence.append(f"Negative delta: {delta}")
        
            # Decision
            if score >= 1:
                recommendation = "BUY"
                conviction = 70
            elif score <= -1:
                recommendation = "SELL"
                conviction = 70
            else:
                recommendation = "HOLD"
                conviction = 50
        
            return AgentOpinion(
                agent_id=self.agent_id,
                agent_role=self.role,
                recommendation=recommendation,
                conviction=conviction,
                confidence=self.expertise_level,
                reasoning=f"Technical score: {score}",
                supporting_evidence=evidence,
                concerns=[]
            )
        except Exception as e:
            logger.error(f"Error in _analyze_technical: {e}")
            raise
    
    def _analyze_sentiment(self, data: Dict[str, Any]) -> AgentOpinion:
        """Sentiment analysis"""
        
        try:
            sentiment = data.get('sentiment', {})
        
            vix = sentiment.get('vix', 20)
            put_call = sentiment.get('put_call_ratio', 1.0)
        
            evidence = []
            score = 0
        
            # VIX
            if vix < 15:
                score += 1
                evidence.append(f"Low VIX: {vix} - complacency")
            elif vix > 25:
                score -= 1
                evidence.append(f"High VIX: {vix} - fear")
        
            # Put/Call
            if put_call > 1.2:
                score += 1  # Contrarian - excessive fear
                evidence.append(f"High put/call: {put_call} - contrarian bullish")
            elif put_call < 0.8:
                score -= 1  # Excessive greed
                evidence.append(f"Low put/call: {put_call} - excessive optimism")
        
            # Decision
            if score >= 1:
                recommendation = "BUY"
                conviction = 65
            elif score <= -1:
                recommendation = "SELL"
                conviction = 65
            else:
                recommendation = "HOLD"
                conviction = 50
        
            return AgentOpinion(
                agent_id=self.agent_id,
                agent_role=self.role,
                recommendation=recommendation,
                conviction=conviction,
                confidence=self.expertise_level,
                reasoning=f"Sentiment score: {score}",
                supporting_evidence=evidence,
                concerns=[]
            )
        except Exception as e:
            logger.error(f"Error in _analyze_sentiment: {e}")
            raise
    
    def _analyze_risk(self, data: Dict[str, Any]) -> AgentOpinion:
        """Risk analysis - always cautious"""
        
        try:
            concerns = []
        
            # Check for high risk conditions
            sentiment = data.get('sentiment', {})
            vix = sentiment.get('vix', 20)
        
            if vix > 30:
                concerns.append(f"Extreme volatility: VIX={vix}")
        
            # Risk manager is conservative
            if concerns:
                recommendation = "HOLD"
                conviction = 80
            else:
                recommendation = "HOLD"
                conviction = 50
        
            return AgentOpinion(
                agent_id=self.agent_id,
                agent_role=self.role,
                recommendation=recommendation,
                conviction=conviction,
                confidence=self.expertise_level,
                reasoning="Risk assessment",
                supporting_evidence=[],
                concerns=concerns
            )
        except Exception as e:
            logger.error(f"Error in _analyze_risk: {e}")
            raise
    
    def _hunt_patterns(self, data: Dict[str, Any]) -> AgentOpinion:
        """Hunt for patterns"""
        
        # Simulate pattern detection
        try:
            patterns_found = np.random.choice(['bullish_flag', 'head_shoulders', 'double_bottom', 'none'], p=[0.2, 0.1, 0.15, 0.55])
        
            if patterns_found == 'bullish_flag':
                return AgentOpinion(
                    agent_id=self.agent_id,
                    agent_role=self.role,
                    recommendation="BUY",
                    conviction=75,
                    confidence=self.expertise_level,
                    reasoning="Bullish flag pattern detected",
                    supporting_evidence=["Flag pattern", "Volume confirmation"],
                    concerns=[]
                )
            elif patterns_found == 'head_shoulders':
                return AgentOpinion(
                    agent_id=self.agent_id,
                    agent_role=self.role,
                    recommendation="SELL",
                    conviction=70,
                    confidence=self.expertise_level,
                    reasoning="Head and shoulders pattern",
                    supporting_evidence=["H&S pattern", "Neckline break"],
                    concerns=[]
                )
            else:
                return AgentOpinion(
                    agent_id=self.agent_id,
                    agent_role=self.role,
                    recommendation="HOLD",
                    conviction=50,
                    confidence=self.expertise_level,
                    reasoning="No clear pattern",
                    supporting_evidence=[],
                    concerns=[]
                )
        except Exception as e:
            logger.error(f"Error in _hunt_patterns: {e}")
            raise
    
    def _detect_regime(self, data: Dict[str, Any]) -> AgentOpinion:
        """Detect market regime"""
        
        try:
            state = data.get('current_state', {})
            regime = state.get('regime', 'unknown')
        
            if regime == 'trending':
                return AgentOpinion(
                    agent_id=self.agent_id,
                    agent_role=self.role,
                    recommendation="BUY",
                    conviction=70,
                    confidence=self.expertise_level,
                    reasoning="Trending regime - momentum favorable",
                    supporting_evidence=["Trend detected", "Momentum positive"],
                    concerns=[]
                )
            elif regime == 'ranging':
                return AgentOpinion(
                    agent_id=self.agent_id,
                    agent_role=self.role,
                    recommendation="HOLD",
                    conviction=60,
                    confidence=self.expertise_level,
                    reasoning="Ranging regime - wait for breakout",
                    supporting_evidence=["Range bound"],
                    concerns=["No clear direction"]
                )
            else:
                return AgentOpinion(
                    agent_id=self.agent_id,
                    agent_role=self.role,
                    recommendation="HOLD",
                    conviction=50,
                    confidence=self.expertise_level,
                    reasoning="Regime unclear",
                    supporting_evidence=[],
                    concerns=["Uncertainty"]
                )
        except Exception as e:
            logger.error(f"Error in _detect_regime: {e}")
            raise
    
    def _detect_manipulation(self, data: Dict[str, Any]) -> AgentOpinion:
        """Detect market manipulation"""
        
        # Simulate manipulation detection
        try:
            manipulation_score = np.random.rand() * 100
        
            if manipulation_score > 70:
                return AgentOpinion(
                    agent_id=self.agent_id,
                    agent_role=self.role,
                    recommendation="HOLD",
                    conviction=90,
                    confidence=self.expertise_level,
                    reasoning="High manipulation detected",
                    supporting_evidence=[],
                    concerns=[f"Manipulation score: {manipulation_score:.0f}/100"]
                )
            else:
                return AgentOpinion(
                    agent_id=self.agent_id,
                    agent_role=self.role,
                    recommendation="HOLD",
                    conviction=50,
                    confidence=self.expertise_level,
                    reasoning="Market appears clean",
                    supporting_evidence=["No manipulation detected"],
                    concerns=[]
                )
        except Exception as e:
            logger.error(f"Error in _detect_manipulation: {e}")
            raise
    
    def _analyze_order_flow(self, data: Dict[str, Any]) -> AgentOpinion:
        """Analyze order flow"""
        
        try:
            micro = data.get('microstructure', {})
            delta = micro.get('cumulative_delta', 0)
        
            if delta > 2000:
                return AgentOpinion(
                    agent_id=self.agent_id,
                    agent_role=self.role,
                    recommendation="BUY",
                    conviction=75,
                    confidence=self.expertise_level,
                    reasoning="Strong buying pressure",
                    supporting_evidence=[f"Cumulative delta: {delta}"],
                    concerns=[]
                )
            elif delta < -2000:
                return AgentOpinion(
                    agent_id=self.agent_id,
                    agent_role=self.role,
                    recommendation="SELL",
                    conviction=75,
                    confidence=self.expertise_level,
                    reasoning="Strong selling pressure",
                    supporting_evidence=[f"Cumulative delta: {delta}"],
                    concerns=[]
                )
            else:
                return AgentOpinion(
                    agent_id=self.agent_id,
                    agent_role=self.role,
                    recommendation="HOLD",
                    conviction=50,
                    confidence=self.expertise_level,
                    reasoning="Balanced order flow",
                    supporting_evidence=[],
                    concerns=[]
                )
        except Exception as e:
            logger.error(f"Error in _analyze_order_flow: {e}")
            raise
    
    def _generic_analysis(self, data: Dict[str, Any]) -> AgentOpinion:
        """Generic analysis"""
        
        return AgentOpinion(
            agent_id=self.agent_id,
            agent_role=self.role,
            recommendation="HOLD",
            conviction=50,
            confidence=self.expertise_level,
            reasoning="Generic analysis",
            supporting_evidence=[],
            concerns=[]
        )
    
    def update_performance(self, was_correct: bool):
        """Update agent performance"""
        
        try:
            self.total_predictions += 1
            if was_correct:
                self.correct_predictions += 1
        
            self.accuracy = self.correct_predictions / self.total_predictions if self.total_predictions > 0 else 0.0
        
            # Update expertise level based on recent performance
            self.recent_performance.append(1.0 if was_correct else 0.0)
            if len(self.recent_performance) > 100:
                self.recent_performance.pop(0)
        
            if len(self.recent_performance) >= 10:
                recent_accuracy = sum(self.recent_performance[-10:]) / 10
                self.expertise_level = 0.5 + (recent_accuracy * 0.5)  # 0.5 to 1.0
        except Exception as e:
            logger.error(f"Error in update_performance: {e}")
            raise


class MultiBrainEnsemble:
    """
    Multi-brain ensemble with collective intelligence
    """
    
    def __init__(self):
        # Create specialized agents
        try:
            self.agents: Dict[str, SpecializedAgent] = {}
        
            # Commander (master decision maker)
            self.commander = SpecializedAgent("CMD_001", AgentRole.COMMANDER, expertise_level=0.9)
            self.agents[self.commander.agent_id] = self.commander
        
            # Specialist agents
            specialist_roles = [
                AgentRole.MACRO_ANALYST,
                AgentRole.TECHNICAL_ANALYST,
                AgentRole.SENTIMENT_ANALYST,
                AgentRole.RISK_MANAGER,
                AgentRole.PATTERN_HUNTER,
                AgentRole.REGIME_DETECTOR,
                AgentRole.MANIPULATION_DETECTOR,
                AgentRole.ORDER_FLOW_ANALYST
            ]
        
            for i, role in enumerate(specialist_roles):
                agent = SpecializedAgent(f"AGT_{i+1:03d}", role, expertise_level=0.7 + np.random.rand() * 0.2)
                self.agents[agent.agent_id] = agent
        
            # Debate history
            self.debate_history: List[CollectiveDecision] = []
        
            logger.info(f"Multi-Brain Ensemble initialized with {len(self.agents)} agents")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def collective_decision(self, market_data: Dict[str, Any],
                          vote_method: VoteWeight = VoteWeight.WEIGHTED) -> CollectiveDecision:
        """
        Make collective decision through agent debate
        """
        
        # Gather opinions from all agents
        try:
            opinions = []
        
            for agent in self.agents.values():
                if agent.role != AgentRole.COMMANDER:  # Commander decides last
                    opinion = agent.analyze(market_data)
                    opinions.append(opinion)
        
            # Count votes
            votes = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
            weighted_votes = {'BUY': 0.0, 'SELL': 0.0, 'HOLD': 0.0}
        
            for opinion in opinions:
                votes[opinion.recommendation] += 1
            
                # Weighted by confidence and conviction
                weight = opinion.confidence * (opinion.conviction / 100)
                weighted_votes[opinion.recommendation] += weight
        
            # Determine decision based on vote method
            if vote_method == VoteWeight.WEIGHTED:
                decision = max(weighted_votes, key=weighted_votes.get)
                consensus_strength = weighted_votes[decision] / sum(weighted_votes.values())
            elif vote_method == VoteWeight.MAJORITY:
                decision = max(votes, key=votes.get)
                consensus_strength = votes[decision] / len(opinions)
            elif vote_method == VoteWeight.SUPERMAJORITY:
                decision = max(votes, key=votes.get)
                consensus_strength = votes[decision] / len(opinions)
                if consensus_strength < 0.66:
                    decision = "HOLD"  # No supermajority, default to HOLD
            else:
                decision = max(votes, key=votes.get)
                consensus_strength = votes[decision] / len(opinions)
        
            # Commander review (can veto)
            commander_opinion = self.commander.analyze(market_data)
        
            if vote_method == VoteWeight.COMMANDER_VETO:
                if commander_opinion.conviction > 80:
                    decision = commander_opinion.recommendation
                    consensus_strength = 1.0
        
            opinions.append(commander_opinion)
        
            # Calculate collective confidence
            collective_confidence = np.mean([op.confidence * (op.conviction / 100) for op in opinions])
        
            # Debate quality (how much disagreement = thorough debate)
            debate_quality = 1.0 - consensus_strength  # More disagreement = better debate
        
            # Gather minority concerns
            minority_opinions = [op for op in opinions if op.recommendation != decision]
            minority_concerns = []
            for op in minority_opinions:
                minority_concerns.extend(op.concerns)
        
            # Majority reasoning
            majority_opinions = [op for op in opinions if op.recommendation == decision]
            majority_reasoning = " | ".join([op.reasoning for op in majority_opinions[:3]])
        
            collective = CollectiveDecision(
                decision=decision,
                consensus_strength=consensus_strength,
                votes_buy=votes['BUY'],
                votes_sell=votes['SELL'],
                votes_hold=votes['HOLD'],
                opinions=opinions,
                majority_reasoning=majority_reasoning,
                minority_concerns=minority_concerns,
                collective_confidence=collective_confidence,
                debate_quality=debate_quality
            )
        
            self.debate_history.append(collective)
        
            logger.info(f"Collective decision: {decision} with {consensus_strength:.2%} consensus")
        
            return collective
        except Exception as e:
            logger.error(f"Error in collective_decision: {e}")
            raise
    
    def get_agent_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics for all agents"""
        
        try:
            performance = {}
        
            for agent_id, agent in self.agents.items():
                performance[agent_id] = {
                    'role': agent.role.value,
                    'accuracy': agent.accuracy,
                    'expertise_level': agent.expertise_level,
                    'total_predictions': agent.total_predictions
                }
        
            return performance
        except Exception as e:
            logger.error(f"Error in get_agent_performance: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Initialize ensemble
    ensemble = MultiBrainEnsemble()
    
    print("="*80)
    logger.info("MULTI-BRAIN ENSEMBLE ARCHITECTURE")
    print("="*80)
    
    # Market data
    market_data = {
        'macro': {'gdp_growth': 2.8, 'cpi': 3.2, 'fed_stance': 'hawkish'},
        'microstructure': {'price': 4520, 'vpoc': 4500, 'cumulative_delta': 3000},
        'sentiment': {'vix': 18, 'put_call_ratio': 1.1},
        'current_state': {'regime': 'trending'}
    }
    
    # Make collective decision
    decision = ensemble.collective_decision(market_data, VoteWeight.WEIGHTED)
    
    logger.info(f"\nCOLLECTIVE DECISION: {decision.decision}")
    logger.info(f"Consensus Strength: {decision.consensus_strength:.2%}")
    logger.info(f"Collective Confidence: {decision.collective_confidence:.2f}")
    logger.info(f"Debate Quality: {decision.debate_quality:.2f}")
    
    logger.info(f"\nVOTING BREAKDOWN:")
    logger.info(f"  BUY:  {decision.votes_buy}")
    logger.info(f"  SELL: {decision.votes_sell}")
    logger.info(f"  HOLD: {decision.votes_hold}")
    
    logger.info(f"\nMAJORITY REASONING:")
    logger.info(f"  {decision.majority_reasoning}")
    
    if decision.minority_concerns:
        logger.info(f"\nMINORITY CONCERNS:")
        for concern in decision.minority_concerns[:3]:
            logger.info(f"  ⚠ {concern}")
    
    logger.info(f"\nAGENT OPINIONS:")
    for opinion in decision.opinions:
        print(f"  {opinion.agent_role.value}: {opinion.recommendation} "
              f"(conviction={opinion.conviction:.0f}, confidence={opinion.confidence:.2f})")
    
    print("\n" + "="*80)
