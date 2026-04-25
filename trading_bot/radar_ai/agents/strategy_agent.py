"""
Strategy/Research Agent - Bull/Bear Thesis Generation
======================================================

Competing AI sub-agents that generate opposing theses:
- Bull Agent: Finds entry opportunities
- Bear Agent: Finds invalidation cases
- Wargame outputs for robust decision making
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


@dataclass
class Thesis:
    """A trading thesis (bull or bear)"""
    thesis_id: str
    timestamp: datetime
    thesis_type: str  # 'bull' or 'bear'
    symbol: str
    entry_points: List[float]
    exit_points: List[float]
    supporting_factors: List[str]
    confidence: float
    expected_return: float
    time_horizon: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'thesis_id': self.thesis_id,
            'timestamp': self.timestamp.isoformat(),
            'thesis_type': self.thesis_type,
            'symbol': self.symbol,
            'entry_points': self.entry_points,
            'exit_points': self.exit_points,
            'supporting_factors': self.supporting_factors,
            'confidence': self.confidence,
            'expected_return': self.expected_return,
            'time_horizon': self.time_horizon,
        }


class BullAgent:
    """
    Bull Agent - Finds entry opportunities
    
    Looks for reasons to BUY:
    - Positive catalysts
    - Undervaluation
    - Momentum
    - Technical breakouts
    """
    
    def __init__(self):
        self.agent_id = f"BULL-{uuid.uuid4().hex[:8]}"
        self.theses_generated = 0
    
    async def generate_thesis(
        self,
        symbol: str,
        market_picture: Dict[str, Any],
        ontology_data: Dict[str, Any],
    ) -> Thesis:
        """Generate bullish thesis"""
        supporting_factors = []
        
        # Price analysis
        price = market_picture.get('prices', {}).get(symbol, 0)
        if price > 0:
            supporting_factors.append(f"Current price {price} presents entry opportunity")
        
        # Sentiment analysis
        sentiment = market_picture.get('sentiment_scores', {}).get(symbol, 0.5)
        if sentiment > 0.6:
            supporting_factors.append(f"Positive sentiment score: {sentiment:.0%}")
        
        # Volume analysis
        volume = market_picture.get('volumes', {}).get(symbol, 0)
        if volume > 1000000:
            supporting_factors.append(f"Strong volume: {volume:,.0f}")
        
        # Macro tailwinds
        macro = market_picture.get('macro_indicators', {})
        if macro.get('gdp_growth', 0) > 2:
            supporting_factors.append("Positive GDP growth supports risk assets")
        
        # Technical factors
        supporting_factors.append("Technical indicators suggest upward momentum")
        
        # Calculate confidence
        confidence = min(0.9, 0.5 + len(supporting_factors) * 0.08)
        
        # Entry/exit points
        entry_points = [price * 0.98, price * 0.95]  # Buy dips
        exit_points = [price * 1.10, price * 1.20]   # Take profits
        
        thesis = Thesis(
            thesis_id=f"BULL-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            thesis_type='bull',
            symbol=symbol,
            entry_points=entry_points,
            exit_points=exit_points,
            supporting_factors=supporting_factors,
            confidence=confidence,
            expected_return=0.15,
            time_horizon='medium_term',
        )
        
        self.theses_generated += 1
        
        return thesis


class BearAgent:
    """
    Bear Agent - Finds invalidation cases
    
    Looks for reasons to SELL/AVOID:
    - Negative catalysts
    - Overvaluation
    - Deteriorating fundamentals
    - Technical breakdowns
    """
    
    def __init__(self):
        self.agent_id = f"BEAR-{uuid.uuid4().hex[:8]}"
        self.theses_generated = 0
    
    async def generate_thesis(
        self,
        symbol: str,
        market_picture: Dict[str, Any],
        ontology_data: Dict[str, Any],
    ) -> Thesis:
        """Generate bearish thesis"""
        supporting_factors = []
        
        # Price analysis
        price = market_picture.get('prices', {}).get(symbol, 0)
        if price > 0:
            supporting_factors.append(f"Price at {price} may be extended")
        
        # Sentiment analysis
        sentiment = market_picture.get('sentiment_scores', {}).get(symbol, 0.5)
        if sentiment < 0.4:
            supporting_factors.append(f"Negative sentiment: {sentiment:.0%}")
        
        # Macro headwinds
        macro = market_picture.get('macro_indicators', {})
        if macro.get('inflation', 0) > 3:
            supporting_factors.append(f"High inflation ({macro.get('inflation')}%) pressures valuations")
        
        if macro.get('vix', 0) > 20:
            supporting_factors.append(f"Elevated VIX ({macro.get('vix')}) signals risk-off")
        
        # Risk factors
        supporting_factors.append("Technical indicators suggest potential reversal")
        supporting_factors.append("Risk/reward ratio unfavorable at current levels")
        
        # Calculate confidence
        confidence = min(0.9, 0.4 + len(supporting_factors) * 0.08)
        
        # Entry/exit points (for short positions)
        entry_points = [price * 1.02, price * 1.05]  # Sell rallies
        exit_points = [price * 0.90, price * 0.80]   # Cover shorts
        
        thesis = Thesis(
            thesis_id=f"BEAR-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            thesis_type='bear',
            symbol=symbol,
            entry_points=entry_points,
            exit_points=exit_points,
            supporting_factors=supporting_factors,
            confidence=confidence,
            expected_return=-0.10,
            time_horizon='short_term',
        )
        
        self.theses_generated += 1
        
        return thesis


class StrategyAgent:
    """
    Strategy/Research Agent - Coordinates Bull/Bear Analysis
    
    Runs competing agents and synthesizes their outputs.
    """
    
    def __init__(self, meta_orchestrator: Any):
        self.agent_id = f"STRAT-{uuid.uuid4().hex[:8]}"
        self.meta_orchestrator = meta_orchestrator
        
        # Register with orchestrator
        self.meta_orchestrator.register_agent("StrategyAgent", self)
        
        # Sub-agents
        self.bull_agent = BullAgent()
        self.bear_agent = BearAgent()
        
        # Analysis history
        self.analyses: List[Dict[str, Any]] = []
        
        logger.info(f"StrategyAgent initialized: {self.agent_id}")
    
    async def analyze_opportunity(
        self,
        symbol: str,
        market_picture: Dict[str, Any],
        ontology_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run wargame analysis with Bull vs Bear agents.
        
        Returns synthesized recommendation.
        """
        # Submit request to orchestrator
        request = await self.meta_orchestrator.submit_request(
            agent_name="StrategyAgent",
            request_type="analyze_opportunity",
            payload={'symbol': symbol},
            requires_approval=False,
        )
        
        # Run both agents in parallel
        bull_thesis_task = self.bull_agent.generate_thesis(symbol, market_picture, ontology_data)
        bear_thesis_task = self.bear_agent.generate_thesis(symbol, market_picture, ontology_data)
        
        bull_thesis, bear_thesis = await asyncio.gather(bull_thesis_task, bear_thesis_task)
        
        # Wargame: Compare theses
        bull_confidence = bull_thesis.confidence
        bear_confidence = bear_thesis.confidence
        
        # Determine recommendation
        if bull_confidence > bear_confidence + 0.2:
            recommended_action = 'buy'
            confidence = bull_confidence
            primary_thesis = bull_thesis
            counter_thesis = bear_thesis
        elif bear_confidence > bull_confidence + 0.2:
            recommended_action = 'sell'
            confidence = bear_confidence
            primary_thesis = bear_thesis
            counter_thesis = bull_thesis
        else:
            recommended_action = 'hold'
            confidence = 0.5
            primary_thesis = bull_thesis
            counter_thesis = bear_thesis
        
        analysis = {
            'symbol': symbol,
            'recommended_action': recommended_action,
            'confidence': confidence,
            'bull_thesis': bull_thesis.to_dict(),
            'bear_thesis': bear_thesis.to_dict(),
            'primary_factors': primary_thesis.supporting_factors,
            'counter_factors': counter_thesis.supporting_factors,
            'entry_points': primary_thesis.entry_points,
            'exit_points': primary_thesis.exit_points,
            'expected_return': primary_thesis.expected_return,
            'time_horizon': primary_thesis.time_horizon,
        }
        
        self.analyses.append(analysis)
        
        logger.info(f"Strategy analysis for {symbol}: {recommended_action} (confidence: {confidence:.0%})")
        
        return analysis
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'agent_id': self.agent_id,
            'bull_theses_generated': self.bull_agent.theses_generated,
            'bear_theses_generated': self.bear_agent.theses_generated,
            'total_analyses': len(self.analyses),
        }
