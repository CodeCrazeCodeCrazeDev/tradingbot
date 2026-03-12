"""
Multi-Agent Trading Debate System

Three specialized AI models that "debate" each other:
- The Macro Strategist: Operates on HTF, identifies overarching themes and key levels
- The Tactical Executioner: Works on LTF, specializes in precise entry/exit timing
- The Risk Sentinel: Monitors overall portfolio exposure, correlation, and black swan signals

A "Head AI" weighs the arguments of these three agents to make the final decision,
mimicking a professional trading desk.

Features:
- Multi-agent consensus building
- Argument weighting and scoring
- Conflict resolution
- Final decision synthesis
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import statistics

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent roles in the debate."""
    MACRO_STRATEGIST = "macro_strategist"
    TACTICAL_EXECUTIONER = "tactical_executioner"
    RISK_SENTINEL = "risk_sentinel"
    HEAD_AI = "head_ai"


class Conviction(Enum):
    """Conviction levels."""
    VERY_LOW = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    VERY_HIGH = 5


class TradeAction(Enum):
    """Possible trade actions."""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"
    NO_TRADE = "no_trade"


@dataclass
class MarketContext:
    """Market context for agent analysis."""
    symbol: str
    current_price: float
    htf_trend: str  # 'UP', 'DOWN', 'SIDEWAYS'
    ltf_trend: str
    volatility: float
    volume_ratio: float
    key_levels: Dict[str, List[float]]  # 'support', 'resistance'
    news_sentiment: float  # -1 to +1
    portfolio_exposure: float  # Current exposure %
    correlation_risk: float  # 0 to 1
    vix_level: Optional[float] = None


@dataclass
class AgentArgument:
    """Argument from an agent."""
    agent_role: AgentRole
    action: TradeAction
    conviction: Conviction
    reasoning: List[str]
    key_factors: Dict[str, float]
    confidence: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'agent': self.agent_role.value,
            'action': self.action.value,
            'conviction': self.conviction.name,
            'reasoning': self.reasoning,
            'key_factors': self.key_factors,
            'confidence': self.confidence
        }


@dataclass
class DebateRound:
    """Single round of debate."""
    round_number: int
    arguments: List[AgentArgument]
    consensus_level: float  # 0 to 1
    conflicts: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'round': self.round_number,
            'arguments': [a.to_dict() for a in self.arguments],
            'consensus_level': self.consensus_level,
            'conflicts': self.conflicts
        }


@dataclass
class FinalDecision:
    """Final decision from Head AI."""
    timestamp: datetime
    symbol: str
    action: TradeAction
    confidence: float
    position_size_pct: float
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    reasoning: str
    agent_votes: Dict[str, str]
    debate_rounds: int
    consensus_level: float
    dissenting_views: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'action': self.action.value,
            'confidence': self.confidence,
            'position_size_pct': self.position_size_pct,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'reasoning': self.reasoning,
            'agent_votes': self.agent_votes,
            'consensus_level': self.consensus_level,
            'dissenting_views': self.dissenting_views
        }


class TradingAgent(ABC):
    """Base class for trading agents."""
    
    def __init__(self, role: AgentRole, config: Optional[Dict] = None):
        self.role = role
        self.config = config or {}
        self.weight = self.config.get('weight', 1.0)
    
    @abstractmethod
    def analyze(self, context: MarketContext) -> AgentArgument:
        """Analyze market and produce argument."""
        pass
    
    @abstractmethod
    def respond_to_argument(
        self,
        argument: AgentArgument,
        context: MarketContext
    ) -> Optional[AgentArgument]:
        """Respond to another agent's argument."""
        pass


class MacroStrategist(TradingAgent):
    """
    The Macro Strategist agent.
    
    Focuses on:
    - Higher timeframe trends
    - Key support/resistance levels
    - Market structure
    - Fundamental themes
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(AgentRole.MACRO_STRATEGIST, config)
    
    def analyze(self, context: MarketContext) -> AgentArgument:
        """Analyze from macro perspective."""
        reasoning = []
        key_factors = {}
        
        # Analyze HTF trend
        if context.htf_trend == 'UP':
            trend_score = 0.7
            reasoning.append(f"HTF trend is bullish - favorable for longs")
        elif context.htf_trend == 'DOWN':
            trend_score = -0.7
            reasoning.append(f"HTF trend is bearish - favorable for shorts")
        else:
            trend_score = 0
            reasoning.append(f"HTF trend is sideways - range-bound conditions")
        
        key_factors['htf_trend'] = trend_score
        
        # Analyze key levels
        supports = context.key_levels.get('support', [])
        resistances = context.key_levels.get('resistance', [])
        
        level_score = 0
        if supports:
            nearest_support = min(supports, key=lambda x: abs(x - context.current_price))
            support_distance = (context.current_price - nearest_support) / context.current_price
            if support_distance < 0.01:  # Within 1%
                level_score += 0.3
                reasoning.append(f"Price near support at {nearest_support:.5f}")
        
        if resistances:
            nearest_resistance = min(resistances, key=lambda x: abs(x - context.current_price))
            resistance_distance = (nearest_resistance - context.current_price) / context.current_price
            if resistance_distance < 0.01:
                level_score -= 0.3
                reasoning.append(f"Price near resistance at {nearest_resistance:.5f}")
        
        key_factors['key_levels'] = level_score
        
        # News sentiment
        key_factors['sentiment'] = context.news_sentiment * 0.5
        if context.news_sentiment > 0.3:
            reasoning.append("Positive news sentiment supports bullish bias")
        elif context.news_sentiment < -0.3:
            reasoning.append("Negative news sentiment supports bearish bias")
        
        # Calculate overall score
        total_score = sum(key_factors.values())
        
        # Determine action
        if total_score > 0.8:
            action = TradeAction.STRONG_BUY
            conviction = Conviction.VERY_HIGH
        elif total_score > 0.4:
            action = TradeAction.BUY
            conviction = Conviction.HIGH
        elif total_score < -0.8:
            action = TradeAction.STRONG_SELL
            conviction = Conviction.VERY_HIGH
        elif total_score < -0.4:
            action = TradeAction.SELL
            conviction = Conviction.HIGH
        else:
            action = TradeAction.HOLD
            conviction = Conviction.MODERATE
        
        confidence = min(0.95, 0.5 + abs(total_score) * 0.3)
        
        return AgentArgument(
            agent_role=self.role,
            action=action,
            conviction=conviction,
            reasoning=reasoning,
            key_factors=key_factors,
            confidence=confidence,
            timestamp=datetime.now()
        )
    
    def respond_to_argument(
        self,
        argument: AgentArgument,
        context: MarketContext
    ) -> Optional[AgentArgument]:
        """Respond to tactical or risk arguments."""
        if argument.agent_role == AgentRole.RISK_SENTINEL:
            # If risk agent is very concerned, moderate our view
            if argument.conviction.value >= Conviction.HIGH.value:
                if argument.action == TradeAction.NO_TRADE:
                    return AgentArgument(
                        agent_role=self.role,
                        action=TradeAction.HOLD,
                        conviction=Conviction.MODERATE,
                        reasoning=["Acknowledging risk concerns, moderating position"],
                        key_factors={'risk_adjustment': -0.3},
                        confidence=0.6,
                        timestamp=datetime.now()
                    )
        
        return None


class TacticalExecutioner(TradingAgent):
    """
    The Tactical Executioner agent.
    
    Focuses on:
    - Lower timeframe price action
    - Entry/exit timing
    - Order flow
    - Momentum
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(AgentRole.TACTICAL_EXECUTIONER, config)
    
    def analyze(self, context: MarketContext) -> AgentArgument:
        """Analyze from tactical perspective."""
        reasoning = []
        key_factors = {}
        
        # LTF trend
        if context.ltf_trend == 'UP':
            ltf_score = 0.6
            reasoning.append("LTF momentum is bullish - good entry timing")
        elif context.ltf_trend == 'DOWN':
            ltf_score = -0.6
            reasoning.append("LTF momentum is bearish - wait for reversal")
        else:
            ltf_score = 0
            reasoning.append("LTF is consolidating - await breakout")
        
        key_factors['ltf_trend'] = ltf_score
        
        # Volume analysis
        if context.volume_ratio > 1.5:
            volume_score = 0.3 if context.ltf_trend == 'UP' else -0.3
            reasoning.append(f"Volume surge ({context.volume_ratio:.1f}x) confirms move")
        elif context.volume_ratio < 0.5:
            volume_score = -0.2
            reasoning.append("Low volume - weak conviction in current move")
        else:
            volume_score = 0
        
        key_factors['volume'] = volume_score
        
        # Volatility for timing
        if context.volatility > 0.02:  # High volatility
            vol_score = -0.2
            reasoning.append("High volatility - wider stops needed")
        else:
            vol_score = 0.1
            reasoning.append("Moderate volatility - good for precise entries")
        
        key_factors['volatility'] = vol_score
        
        # Calculate total
        total_score = sum(key_factors.values())
        
        # Determine action
        if total_score > 0.6:
            action = TradeAction.STRONG_BUY
            conviction = Conviction.HIGH
        elif total_score > 0.3:
            action = TradeAction.BUY
            conviction = Conviction.MODERATE
        elif total_score < -0.6:
            action = TradeAction.STRONG_SELL
            conviction = Conviction.HIGH
        elif total_score < -0.3:
            action = TradeAction.SELL
            conviction = Conviction.MODERATE
        else:
            action = TradeAction.HOLD
            conviction = Conviction.LOW
        
        confidence = min(0.95, 0.5 + abs(total_score) * 0.35)
        
        return AgentArgument(
            agent_role=self.role,
            action=action,
            conviction=conviction,
            reasoning=reasoning,
            key_factors=key_factors,
            confidence=confidence,
            timestamp=datetime.now()
        )
    
    def respond_to_argument(
        self,
        argument: AgentArgument,
        context: MarketContext
    ) -> Optional[AgentArgument]:
        """Respond to macro or risk arguments."""
        if argument.agent_role == AgentRole.MACRO_STRATEGIST:
            # Align with macro if LTF confirms
            if context.ltf_trend == context.htf_trend:
                return AgentArgument(
                    agent_role=self.role,
                    action=argument.action,
                    conviction=Conviction.HIGH,
                    reasoning=["LTF confirms HTF direction - strong alignment"],
                    key_factors={'alignment_bonus': 0.3},
                    confidence=0.8,
                    timestamp=datetime.now()
                )
        
        return None


class RiskSentinel(TradingAgent):
    """
    The Risk Sentinel agent.
    
    Focuses on:
    - Portfolio exposure
    - Correlation risk
    - Black swan signals
    - Position sizing
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(AgentRole.RISK_SENTINEL, config)
        self.max_exposure = self.config.get('max_exposure', 0.5)
        self.max_correlation = self.config.get('max_correlation', 0.7)
    
    def analyze(self, context: MarketContext) -> AgentArgument:
        """Analyze from risk perspective."""
        reasoning = []
        key_factors = {}
        risk_flags = 0
        
        # Portfolio exposure
        if context.portfolio_exposure > self.max_exposure:
            exposure_score = -0.5
            risk_flags += 1
            reasoning.append(f"⚠️ Portfolio exposure ({context.portfolio_exposure:.0%}) exceeds limit")
        elif context.portfolio_exposure > self.max_exposure * 0.8:
            exposure_score = -0.2
            reasoning.append(f"Portfolio exposure ({context.portfolio_exposure:.0%}) approaching limit")
        else:
            exposure_score = 0.1
            reasoning.append(f"Portfolio exposure ({context.portfolio_exposure:.0%}) within limits")
        
        key_factors['exposure'] = exposure_score
        
        # Correlation risk
        if context.correlation_risk > self.max_correlation:
            corr_score = -0.4
            risk_flags += 1
            reasoning.append(f"⚠️ High correlation risk ({context.correlation_risk:.0%})")
        else:
            corr_score = 0.1
            reasoning.append(f"Correlation risk acceptable ({context.correlation_risk:.0%})")
        
        key_factors['correlation'] = corr_score
        
        # VIX / Black swan signals
        if context.vix_level:
            if context.vix_level > 30:
                vix_score = -0.5
                risk_flags += 1
                reasoning.append(f"⚠️ VIX elevated ({context.vix_level}) - black swan risk")
            elif context.vix_level > 20:
                vix_score = -0.2
                reasoning.append(f"VIX moderately elevated ({context.vix_level})")
            else:
                vix_score = 0.1
                reasoning.append(f"VIX normal ({context.vix_level})")
            
            key_factors['vix'] = vix_score
        
        # Volatility risk
        if context.volatility > 0.03:
            vol_score = -0.3
            risk_flags += 1
            reasoning.append(f"⚠️ Extreme volatility detected")
        else:
            vol_score = 0
        
        key_factors['volatility_risk'] = vol_score
        
        # Determine action
        total_score = sum(key_factors.values())
        
        if risk_flags >= 2:
            action = TradeAction.NO_TRADE
            conviction = Conviction.VERY_HIGH
            reasoning.append("🛑 Multiple risk flags - recommending NO TRADE")
        elif risk_flags == 1:
            action = TradeAction.HOLD
            conviction = Conviction.HIGH
            reasoning.append("⚠️ Risk flag present - reduce position size")
        elif total_score > 0:
            action = TradeAction.BUY  # Risk allows trading
            conviction = Conviction.MODERATE
            reasoning.append("✅ Risk parameters acceptable")
        else:
            action = TradeAction.HOLD
            conviction = Conviction.MODERATE
        
        confidence = min(0.95, 0.6 + risk_flags * 0.15)
        
        return AgentArgument(
            agent_role=self.role,
            action=action,
            conviction=conviction,
            reasoning=reasoning,
            key_factors=key_factors,
            confidence=confidence,
            timestamp=datetime.now()
        )
    
    def respond_to_argument(
        self,
        argument: AgentArgument,
        context: MarketContext
    ) -> Optional[AgentArgument]:
        """Respond to aggressive positions."""
        if argument.action in [TradeAction.STRONG_BUY, TradeAction.STRONG_SELL]:
            if context.portfolio_exposure > self.max_exposure * 0.7:
                return AgentArgument(
                    agent_role=self.role,
                    action=TradeAction.HOLD,
                    conviction=Conviction.HIGH,
                    reasoning=["Reducing position size due to exposure limits"],
                    key_factors={'position_reduction': -0.3},
                    confidence=0.75,
                    timestamp=datetime.now()
                )
        
        return None


class HeadAI:
    """
    The Head AI that synthesizes all agent arguments.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Agent weights
        self.weights = {
            AgentRole.MACRO_STRATEGIST: self.config.get('macro_weight', 0.35),
            AgentRole.TACTICAL_EXECUTIONER: self.config.get('tactical_weight', 0.35),
            AgentRole.RISK_SENTINEL: self.config.get('risk_weight', 0.30),
        }
    
    def synthesize_decision(
        self,
        arguments: List[AgentArgument],
        context: MarketContext,
        debate_rounds: List[DebateRound]
    ) -> FinalDecision:
        """
        Synthesize final decision from all arguments.
        
        Args:
            arguments: All agent arguments
            context: Market context
            debate_rounds: History of debate rounds
            
        Returns:
            FinalDecision
        """
        # Score each action
        action_scores: Dict[TradeAction, float] = {}
        
        for arg in arguments:
            weight = self.weights.get(arg.agent_role, 0.33)
            conviction_mult = arg.conviction.value / 5.0
            
            score = weight * conviction_mult * arg.confidence
            
            if arg.action not in action_scores:
                action_scores[arg.action] = 0
            action_scores[arg.action] += score
        
        # Find winning action
        if action_scores:
            winning_action = max(action_scores.keys(), key=lambda a: action_scores[a])
            winning_score = action_scores[winning_action]
        else:
            winning_action = TradeAction.HOLD
            winning_score = 0.5
        
        # Check for risk veto
        risk_args = [a for a in arguments if a.agent_role == AgentRole.RISK_SENTINEL]
        if risk_args:
            risk_arg = risk_args[-1]
            if risk_arg.action == TradeAction.NO_TRADE and risk_arg.conviction.value >= Conviction.HIGH.value:
                winning_action = TradeAction.NO_TRADE
                winning_score = risk_arg.confidence
        
        # Calculate consensus
        unique_actions = set(a.action for a in arguments)
        consensus_level = 1.0 - (len(unique_actions) - 1) * 0.25
        
        # Collect votes
        agent_votes = {a.agent_role.value: a.action.value for a in arguments}
        
        # Collect dissenting views
        dissenting = [
            f"{a.agent_role.value}: {a.reasoning[0]}"
            for a in arguments
            if a.action != winning_action and a.reasoning
        ]
        
        # Calculate position size
        position_size = self._calculate_position_size(
            winning_action, winning_score, consensus_level, context
        )
        
        # Calculate levels
        entry, stop, target = self._calculate_levels(
            winning_action, context
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            winning_action, arguments, consensus_level
        )
        
        return FinalDecision(
            timestamp=datetime.now(),
            symbol=context.symbol,
            action=winning_action,
            confidence=winning_score,
            position_size_pct=position_size,
            entry_price=entry,
            stop_loss=stop,
            take_profit=target,
            reasoning=reasoning,
            agent_votes=agent_votes,
            debate_rounds=len(debate_rounds),
            consensus_level=consensus_level,
            dissenting_views=dissenting
        )
    
    def _calculate_position_size(
        self,
        action: TradeAction,
        score: float,
        consensus: float,
        context: MarketContext
    ) -> float:
        """Calculate position size based on conviction and consensus."""
        if action in [TradeAction.HOLD, TradeAction.NO_TRADE]:
            return 0.0
        
        base_size = 0.02  # 2% base
        
        # Adjust for score
        size = base_size * (1 + score)
        
        # Adjust for consensus
        size *= consensus
        
        # Adjust for volatility
        if context.volatility > 0.02:
            size *= 0.5
        
        # Cap at max
        max_size = 0.05  # 5% max
        remaining_capacity = 1.0 - context.portfolio_exposure
        
        return min(size, max_size, remaining_capacity)
    
    def _calculate_levels(
        self,
        action: TradeAction,
        context: MarketContext
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate entry, stop, and target levels."""
        if action in [TradeAction.HOLD, TradeAction.NO_TRADE]:
            return None, None, None
        
        entry = context.current_price
        atr = context.volatility * context.current_price  # Approximate ATR
        
        if action in [TradeAction.BUY, TradeAction.STRONG_BUY]:
            stop = entry - atr * 1.5
            target = entry + atr * 2.5
        else:
            stop = entry + atr * 1.5
            target = entry - atr * 2.5
        
        return entry, stop, target
    
    def _generate_reasoning(
        self,
        action: TradeAction,
        arguments: List[AgentArgument],
        consensus: float
    ) -> str:
        """Generate reasoning summary."""
        parts = []
        
        parts.append(f"Decision: {action.value.upper()}")
        parts.append(f"Consensus: {consensus:.0%}")
        
        # Key points from each agent
        for arg in arguments:
            if arg.reasoning:
                parts.append(f"{arg.agent_role.value}: {arg.reasoning[0]}")
        
        return " | ".join(parts)


class MultiAgentDebateSystem:
    """
    Main multi-agent debate system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize agents
        self.macro_strategist = MacroStrategist(config)
        self.tactical_executioner = TacticalExecutioner(config)
        self.risk_sentinel = RiskSentinel(config)
        self.head_ai = HeadAI(config)
        
        self.agents = [
            self.macro_strategist,
            self.tactical_executioner,
            self.risk_sentinel
        ]
        
        # Debate settings
        self.max_rounds = self.config.get('max_rounds', 3)
        self.consensus_threshold = self.config.get('consensus_threshold', 0.7)
        
        # History
        self.decisions: List[FinalDecision] = []
        
        logger.info("MultiAgentDebateSystem initialized")
    
    def debate(self, context: MarketContext) -> FinalDecision:
        """
        Run debate and produce final decision.
        
        Args:
            context: Market context
            
        Returns:
            FinalDecision from Head AI
        """
        debate_rounds = []
        all_arguments = []
        
        # Initial arguments
        round_args = []
        for agent in self.agents:
            arg = agent.analyze(context)
            round_args.append(arg)
            all_arguments.append(arg)
        
        # Calculate initial consensus
        consensus = self._calculate_consensus(round_args)
        conflicts = self._identify_conflicts(round_args)
        
        debate_rounds.append(DebateRound(
            round_number=1,
            arguments=round_args,
            consensus_level=consensus,
            conflicts=conflicts
        ))
        
        # Additional rounds if needed
        round_num = 2
        while consensus < self.consensus_threshold and round_num <= self.max_rounds:
            round_args = []
            
            # Each agent responds to others
            for agent in self.agents:
                for other_arg in all_arguments[-3:]:  # Last round's arguments
                    if other_arg.agent_role != agent.role:
                        response = agent.respond_to_argument(other_arg, context)
                        if response:
                            round_args.append(response)
                            all_arguments.append(response)
            
            if not round_args:
                break
            
            consensus = self._calculate_consensus(round_args)
            conflicts = self._identify_conflicts(round_args)
            
            debate_rounds.append(DebateRound(
                round_number=round_num,
                arguments=round_args,
                consensus_level=consensus,
                conflicts=conflicts
            ))
            
            round_num += 1
        
        # Head AI synthesizes decision
        decision = self.head_ai.synthesize_decision(
            all_arguments, context, debate_rounds
        )
        
        self.decisions.append(decision)
        
        return decision
    
    def _calculate_consensus(self, arguments: List[AgentArgument]) -> float:
        """Calculate consensus level among arguments."""
        if not arguments:
            return 0.0
        
        # Group by action direction
        bullish = sum(1 for a in arguments if a.action in [TradeAction.BUY, TradeAction.STRONG_BUY])
        bearish = sum(1 for a in arguments if a.action in [TradeAction.SELL, TradeAction.STRONG_SELL])
        neutral = sum(1 for a in arguments if a.action in [TradeAction.HOLD, TradeAction.NO_TRADE])
        
        total = len(arguments)
        max_agreement = max(bullish, bearish, neutral)
        
        return max_agreement / total
    
    def _identify_conflicts(self, arguments: List[AgentArgument]) -> List[str]:
        """Identify conflicts between arguments."""
        conflicts = []
        
        actions = [a.action for a in arguments]
        
        # Check for opposing views
        has_buy = any(a in [TradeAction.BUY, TradeAction.STRONG_BUY] for a in actions)
        has_sell = any(a in [TradeAction.SELL, TradeAction.STRONG_SELL] for a in actions)
        
        if has_buy and has_sell:
            conflicts.append("Conflicting directional views between agents")
        
        # Check for risk veto vs aggressive position
        has_no_trade = TradeAction.NO_TRADE in actions
        has_strong = any(a in [TradeAction.STRONG_BUY, TradeAction.STRONG_SELL] for a in actions)
        
        if has_no_trade and has_strong:
            conflicts.append("Risk sentinel vetoing aggressive position")
        
        return conflicts
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        return {
            'total_decisions': len(self.decisions),
            'max_rounds': self.max_rounds,
            'consensus_threshold': self.consensus_threshold,
            'last_decision': self.decisions[-1].to_dict() if self.decisions else None,
            'timestamp': datetime.now().isoformat()
        }


# Factory function
def create_debate_system(config: Optional[Dict] = None) -> MultiAgentDebateSystem:
    """Create MultiAgentDebateSystem instance."""
    return MultiAgentDebateSystem(config)


# Example usage
if __name__ == "__main__":
    system = create_debate_system()
    
    print("=" * 60)
    print("MULTI-AGENT TRADING DEBATE SYSTEM")
    print("=" * 60)
    
    # Create market context
    context = MarketContext(
        symbol="EURUSD",
        current_price=1.1000,
        htf_trend='UP',
        ltf_trend='UP',
        volatility=0.015,
        volume_ratio=1.3,
        key_levels={
            'support': [1.0950, 1.0900],
            'resistance': [1.1050, 1.1100]
        },
        news_sentiment=0.4,
        portfolio_exposure=0.25,
        correlation_risk=0.3,
        vix_level=18.0
    )
    
    print(f"\nMarket Context:")
    print(f"  Symbol: {context.symbol}")
    print(f"  Price: {context.current_price}")
    print(f"  HTF Trend: {context.htf_trend}")
    print(f"  LTF Trend: {context.ltf_trend}")
    print(f"  Portfolio Exposure: {context.portfolio_exposure:.0%}")
    
    # Run debate
    print("\n" + "=" * 60)
    print("DEBATE IN PROGRESS...")
    print("=" * 60)
    
    decision = system.debate(context)
    
    print("\n" + "=" * 60)
    print("FINAL DECISION")
    print("=" * 60)
    
    print(f"\nAction: {decision.action.value.upper()}")
    print(f"Confidence: {decision.confidence:.0%}")
    print(f"Position Size: {decision.position_size_pct:.1%}")
    print(f"Consensus Level: {decision.consensus_level:.0%}")
    print(f"Debate Rounds: {decision.debate_rounds}")
    
    if decision.entry_price:
        print(f"\nLevels:")
        print(f"  Entry: {decision.entry_price:.5f}")
        print(f"  Stop Loss: {decision.stop_loss:.5f}")
        print(f"  Take Profit: {decision.take_profit:.5f}")
    
    print(f"\nAgent Votes:")
    for agent, vote in decision.agent_votes.items():
        print(f"  {agent}: {vote}")
    
    if decision.dissenting_views:
        print(f"\nDissenting Views:")
        for view in decision.dissenting_views:
            print(f"  - {view}")
    
    print(f"\nReasoning: {decision.reasoning}")
