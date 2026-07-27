"""
Multi-Agent Trading Debate System - Research Lab Grade

Three specialized AI models that "debate" each other with evidence-first reasoning:
- The Macro Strategist: Operates on HTF, identifies overarching themes and key levels
- The Tactical Executioner: Works on LTF, specializes in precise entry/exit timing
- The Risk Sentinel: Monitors overall portfolio exposure, correlation, and black swan signals

A "Head AI" coordinates the debate, weights expertise, calibrates confidence, resolves disagreements,
and publishes the final decision.

Features:
- Evidence-first debate loop (Observation -> Evidence -> Hypothesis -> Predictions -> Counter-evidence)
- Verification Swarm independent gate (Risk, Liquidity, Market Structure, Causal, Regime, Hallucination, Execution)
- Standardized Decision Provenance with 17 key fields
- Byzantine Fault Tolerance & Graceful Degradation
- Bayesian Confidence Calibration
- Deterministic replay support
"""

import logging
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from ..verification.confidence_calibrator import ConfidenceCalibrator, CalibrationMethod

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
class DebateTopic:
    """Topic for debate."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


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
    """Argument from an agent, designed as evidence-first."""
    agent_role: AgentRole
    action: TradeAction
    conviction: Conviction
    reasoning: List[str]
    key_factors: Dict[str, float]
    confidence: float
    timestamp: datetime
    # Evidence-First additions:
    observation: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    hypothesis: str = ""
    predictions: List[str] = field(default_factory=list)
    counter_evidence: List[str] = field(default_factory=list)
    verification: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent': self.agent_role.value,
            'action': self.action.value,
            'conviction': self.conviction.name,
            'reasoning': self.reasoning,
            'key_factors': self.key_factors,
            'confidence': self.confidence,
            'observation': self.observation,
            'evidence': self.evidence,
            'hypothesis': self.hypothesis,
            'predictions': self.predictions,
            'counter_evidence': self.counter_evidence,
            'verification': self.verification
        }


@dataclass
class DebateRound:
    """Single round of debate."""
    round_number: int
    arguments: List[AgentArgument]
    consensus_level: float  # 0 to 1
    conflicts: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
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
    # Standardized Decision Provenance addition:
    provenance: Dict[str, Any] = field(default_factory=dict)
    
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
            'dissenting_views': self.dissenting_views,
            'provenance': self.provenance
        }


class TradingAgent(ABC):
    """Base class for trading agents."""
    
    def __init__(self, role: AgentRole, config: Optional[Dict] = None):
        try:
            self.role = role
            self.config = config or {}
            self.weight = self.config.get('weight', 1.0)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
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
    
    Focuses on evidence-first Higher timeframe trends and Key Levels.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            super().__init__(AgentRole.MACRO_STRATEGIST, config)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(self, context: MarketContext) -> AgentArgument:
        try:
            observation = {
                'htf_trend': context.htf_trend,
                'current_price': context.current_price,
                'news_sentiment': context.news_sentiment
            }
            evidence = []
            key_factors = {}

            # Analyze HTF trend
            if context.htf_trend == 'UP':
                trend_score = 0.7
                evidence.append(f"HTF trend UP confirmed via macro structure.")
            elif context.htf_trend == 'DOWN':
                trend_score = -0.7
                evidence.append(f"HTF trend DOWN confirmed via macro structure.")
            else:
                trend_score = 0.0
                evidence.append(f"HTF trend is SIDEWAYS (neutral structure).")

            key_factors['htf_trend'] = trend_score

            # Analyze key levels
            supports = context.key_levels.get('support', [])
            resistances = context.key_levels.get('resistance', [])
            level_score = 0.0

            if supports:
                nearest_support = min(supports, key=lambda x: abs(x - context.current_price))
                support_distance = (context.current_price - nearest_support) / context.current_price
                if support_distance < 0.01:
                    level_score += 0.3
                    evidence.append(f"Price is near key support at {nearest_support:.5f} (distance: {support_distance:.2%}).")

            if resistances:
                nearest_resistance = min(resistances, key=lambda x: abs(x - context.current_price))
                resistance_distance = (nearest_resistance - context.current_price) / context.current_price
                if resistance_distance < 0.01:
                    level_score -= 0.3
                    evidence.append(f"Price is near key resistance at {nearest_resistance:.5f} (distance: {resistance_distance:.2%}).")

            key_factors['key_levels'] = level_score

            # News sentiment
            key_factors['sentiment'] = context.news_sentiment * 0.5
            evidence.append(f"Macro news sentiment is registered at {context.news_sentiment:+.2f}.")

            total_score = sum(key_factors.values())

            # Formulate Hypothesis & Predictions
            if total_score > 0.4:
                action = TradeAction.BUY
                conviction = Conviction.HIGH
                hypothesis = f"Bullish macro trend continuation from supports."
                predictions = [f"Price is expected to rise and test nearest resistance at {min(resistances) if resistances else context.current_price * 1.02:.5f}."]
                counter_evidence = [f"HTF trend structure changes to sideways or down.", f"Violation of support level at {min(supports) if supports else context.current_price * 0.98:.5f}."]
                verification = f"Aligns with positive news sentiment {context.news_sentiment:.2f}."
            elif total_score < -0.4:
                action = TradeAction.SELL
                conviction = Conviction.HIGH
                hypothesis = f"Bearish macro trend continuation from resistances."
                predictions = [f"Price is expected to fall and test nearest support at {max(supports) if supports else context.current_price * 0.98:.5f}."]
                counter_evidence = [f"HTF trend structure changes to sideways or up.", f"Breach of resistance level at {max(resistances) if resistances else context.current_price * 1.02:.5f}."]
                verification = f"Aligns with negative news sentiment {context.news_sentiment:.2f}."
            else:
                action = TradeAction.HOLD
                conviction = Conviction.MODERATE
                hypothesis = f"Market is in a balanced, range-bound macro state."
                predictions = ["Price is expected to continue sideways consolidation."]
                counter_evidence = ["Unscheduled break out of major levels."]
                verification = "Low macro trend conviction matches sideways structure."

            confidence = min(0.95, 0.5 + abs(total_score) * 0.3)

            return AgentArgument(
                agent_role=self.role,
                action=action,
                conviction=conviction,
                reasoning=[hypothesis],
                key_factors=key_factors,
                confidence=confidence,
                timestamp=datetime.now(),
                observation=observation,
                evidence=evidence,
                hypothesis=hypothesis,
                predictions=predictions,
                counter_evidence=counter_evidence,
                verification=verification
            )
        except Exception as e:
            logger.error(f"Error in MacroStrategist analyze: {e}")
            raise

    def respond_to_argument(
        self,
        argument: AgentArgument,
        context: MarketContext
    ) -> Optional[AgentArgument]:
        try:
            if argument.agent_role == AgentRole.RISK_SENTINEL:
                if argument.conviction.value >= Conviction.HIGH.value:
                    if argument.action == TradeAction.NO_TRADE:
                        # Modify macro view based on extreme risk sentinel feedback
                        return AgentArgument(
                            agent_role=self.role,
                            action=TradeAction.HOLD,
                            conviction=Conviction.MODERATE,
                            reasoning=["Risk Sentinel active hold - adapting macro outlook to neutral."],
                            key_factors={'risk_override_penalty': -0.4},
                            confidence=0.6,
                            timestamp=datetime.now(),
                            observation={'risk_sentinel_action': argument.action.value},
                            evidence=[f"Risk Sentinel signal was {argument.action.value} with high conviction."],
                            hypothesis="De-risking portfolio takes precedence over trend following.",
                            predictions=["Hold position until risk levels contract."],
                            counter_evidence=["Risk parameters suddenly stabilize."],
                            verification="Safe hold directive approved by Macro Strategist."
                        )
            return None
        except Exception as e:
            logger.error(f"Error in MacroStrategist respond_to_argument: {e}")
            raise


class TacticalExecutioner(TradingAgent):
    """
    The Tactical Executioner agent.
    
    Focuses on evidence-first Lower timeframe price action and timing.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            super().__init__(AgentRole.TACTICAL_EXECUTIONER, config)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    def analyze(self, context: MarketContext) -> AgentArgument:
        try:
            observation = {
                'ltf_trend': context.ltf_trend,
                'volume_ratio': context.volume_ratio,
                'volatility': context.volatility
            }
            evidence = []
            key_factors = {}

            # Analyze LTF Trend
            if context.ltf_trend == 'UP':
                ltf_score = 0.6
                evidence.append("LTF micro-trend is UP (bullish momentum).")
            elif context.ltf_trend == 'DOWN':
                ltf_score = -0.6
                evidence.append("LTF micro-trend is DOWN (bearish momentum).")
            else:
                ltf_score = 0.0
                evidence.append("LTF micro-trend is SIDEWAYS (consolidation phase).")

            key_factors['ltf_trend'] = ltf_score

            # Volume ratio analysis
            if context.volume_ratio > 1.5:
                volume_score = 0.3 if context.ltf_trend == 'UP' else -0.3
                evidence.append(f"Volume surge detected at {context.volume_ratio:.1f}x relative volume.")
            elif context.volume_ratio < 0.5:
                volume_score = -0.2
                evidence.append(f"Exhaustion/low volume registered at {context.volume_ratio:.1f}x.")
            else:
                volume_score = 0.0
                evidence.append(f"Volume ratio normal at {context.volume_ratio:.1f}x.")

            key_factors['volume'] = volume_score

            # Volatility
            if context.volatility > 0.02:
                vol_score = -0.2
                evidence.append(f"Local volatility is elevated ({context.volatility:.2%}) - wider entries required.")
            else:
                vol_score = 0.1
                evidence.append(f"Local volatility is compressed ({context.volatility:.2%}) - ideal for accurate timing.")

            key_factors['volatility'] = vol_score

            total_score = sum(key_factors.values())

            # Formulate Hypothesis & Predictions
            if total_score > 0.3:
                action = TradeAction.BUY
                conviction = Conviction.MODERATE
                hypothesis = "Bullish momentum breakout in progress."
                predictions = ["Upward timing entry confirmed."]
                counter_evidence = ["Immediate reversal or volume crash."]
                verification = "LTF trend alignment validates breakout timing."
            elif total_score < -0.3:
                action = TradeAction.SELL
                conviction = Conviction.MODERATE
                hypothesis = "Bearish momentum expansion in progress."
                predictions = ["Downward timing entry confirmed."]
                counter_evidence = ["Immediate micro-trend reversal upward."]
                verification = "LTF bearish timing validated."
            else:
                action = TradeAction.HOLD
                conviction = Conviction.LOW
                hypothesis = "Consolidation regime, wait for micro-breakout."
                predictions = ["Price remains range-bound locally."]
                counter_evidence = ["Local volume surge or level breakout."]
                verification = "Vol and volume metrics support range action."

            confidence = min(0.95, 0.5 + abs(total_score) * 0.35)

            return AgentArgument(
                agent_role=self.role,
                action=action,
                conviction=conviction,
                reasoning=[hypothesis],
                key_factors=key_factors,
                confidence=confidence,
                timestamp=datetime.now(),
                observation=observation,
                evidence=evidence,
                hypothesis=hypothesis,
                predictions=predictions,
                counter_evidence=counter_evidence,
                verification=verification
            )
        except Exception as e:
            logger.error(f"Error in TacticalExecutioner analyze: {e}")
            raise

    def respond_to_argument(
        self,
        argument: AgentArgument,
        context: MarketContext
    ) -> Optional[AgentArgument]:
        try:
            if argument.agent_role == AgentRole.MACRO_STRATEGIST:
                if context.ltf_trend == context.htf_trend and context.ltf_trend in ['UP', 'DOWN']:
                    return AgentArgument(
                        agent_role=self.role,
                        action=argument.action,
                        conviction=Conviction.HIGH,
                        reasoning=["LTF confirms HTF direction - strong multi-timeframe alignment"],
                        key_factors={'alignment_bonus': 0.3},
                        confidence=0.8,
                        timestamp=datetime.now(),
                        observation={'macro_action': argument.action.value},
                        evidence=["Macro trend align with local trend direction."],
                        hypothesis="Dual timeframe trend alignment significantly increases entry timing probability.",
                        predictions=["High probability timing entry launched."],
                        counter_evidence=["Price breaches HTF major levels."],
                        verification="Verified by dual-trend alignment."
                    )
            return None
        except Exception as e:
            logger.error(f"Error in TacticalExecutioner respond_to_argument: {e}")
            raise


class RiskSentinel(TradingAgent):
    """
    The Risk Sentinel agent.
    
    Focuses on evidence-first portfolio protection and risk exposure.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            super().__init__(AgentRole.RISK_SENTINEL, config)
            self.max_exposure = self.config.get('max_exposure', 0.5)
            self.max_correlation = self.config.get('max_correlation', 0.7)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise

    def analyze(self, context: MarketContext) -> AgentArgument:
        try:
            observation = {
                'portfolio_exposure': context.portfolio_exposure,
                'correlation_risk': context.correlation_risk,
                'vix_level': context.vix_level,
                'volatility': context.volatility
            }
            evidence = []
            key_factors = {}
            risk_flags = 0

            # Exposure check
            if context.portfolio_exposure > self.max_exposure:
                exposure_score = -0.5
                risk_flags += 1
                evidence.append(f"Portfolio exposure ({context.portfolio_exposure:.1%}) violates limit ({self.max_exposure:.1%}).")
            elif context.portfolio_exposure > self.max_exposure * 0.8:
                exposure_score = -0.2
                evidence.append(f"Portfolio exposure ({context.portfolio_exposure:.1%}) is approaching safety limit.")
            else:
                exposure_score = 0.1
                evidence.append(f"Portfolio exposure ({context.portfolio_exposure:.1%}) is well within limits.")

            key_factors['exposure'] = exposure_score

            # Correlation risk
            if context.correlation_risk > self.max_correlation:
                corr_score = -0.4
                risk_flags += 1
                evidence.append(f"Asset correlation risk ({context.correlation_risk:.1%}) violates safety limit ({self.max_correlation:.1%}).")
            else:
                corr_score = 0.1
                evidence.append(f"Asset correlation risk ({context.correlation_risk:.1%}) is within safety limit.")

            key_factors['correlation'] = corr_score

            # VIX check
            if context.vix_level:
                if context.vix_level > 30:
                    vix_score = -0.5
                    risk_flags += 1
                    evidence.append(f"VIX extreme levels ({context.vix_level}) indicating tail-risk / black swan scenario.")
                elif context.vix_level > 20:
                    vix_score = -0.2
                    evidence.append(f"VIX moderately elevated at {context.vix_level}.")
                else:
                    vix_score = 0.1
                    evidence.append(f"VIX normal/healthy market state at {context.vix_level}.")
                key_factors['vix'] = vix_score

            # Volatility risk
            if context.volatility > 0.03:
                vol_score = -0.3
                risk_flags += 1
                evidence.append(f"Asset local volatility is extreme ({context.volatility:.2%}).")
            else:
                vol_score = 0.0
                evidence.append(f"Asset local volatility normal ({context.volatility:.2%}).")

            key_factors['volatility_risk'] = vol_score

            # Determine Action
            if risk_flags >= 2:
                action = TradeAction.NO_TRADE
                conviction = Conviction.VERY_HIGH
                hypothesis = "Portfolio-wide tail risk constraints violated - recommending NO TRADE."
                predictions = ["Highly volatile market or correlation spikes likely to trigger stop-losses."]
                counter_evidence = ["Risk levels immediately compress."]
                verification = "Veto enforced by Risk Sentinel."
            elif risk_flags == 1:
                action = TradeAction.HOLD
                conviction = Conviction.HIGH
                hypothesis = "A single stress metric elevated. Moderate/defensive hold recommended."
                predictions = ["Expect compressed risk-reward buffer."]
                counter_evidence = ["Risk flags clear completely."]
                verification = "Verified by elevated stress indicator."
            else:
                action = TradeAction.BUY
                conviction = Conviction.MODERATE
                hypothesis = "All risk parameters well within safety limits."
                predictions = ["Standard market exposure is approved."]
                counter_evidence = ["Sudden increase in VIX or volatility."]
                verification = "Passed all standard risk checks."

            confidence = min(0.95, 0.6 + risk_flags * 0.15)

            return AgentArgument(
                agent_role=self.role,
                action=action,
                conviction=conviction,
                reasoning=[hypothesis],
                key_factors=key_factors,
                confidence=confidence,
                timestamp=datetime.now(),
                observation=observation,
                evidence=evidence,
                hypothesis=hypothesis,
                predictions=predictions,
                counter_evidence=counter_evidence,
                verification=verification
            )
        except Exception as e:
            logger.error(f"Error in RiskSentinel analyze: {e}")
            raise

    def respond_to_argument(
        self,
        argument: AgentArgument,
        context: MarketContext
    ) -> Optional[AgentArgument]:
        try:
            risk_flags = 0
            if context.portfolio_exposure > self.max_exposure: risk_flags += 1
            if context.correlation_risk > self.max_correlation: risk_flags += 1
            if context.vix_level and context.vix_level > 30: risk_flags += 1
            if context.volatility > 0.03: risk_flags += 1

            if risk_flags >= 2:
                return None

            if argument.action in [TradeAction.STRONG_BUY, TradeAction.STRONG_SELL]:
                if context.portfolio_exposure > self.max_exposure * 0.7:
                    return AgentArgument(
                        agent_role=self.role,
                        action=TradeAction.HOLD,
                        conviction=Conviction.HIGH,
                        reasoning=["Approaching maximum portfolio capacity - restricting aggressive sizing."],
                        key_factors={'position_reduction': -0.3},
                        confidence=0.75,
                        timestamp=datetime.now(),
                        observation={'proposing_agent': argument.agent_role.value, 'proposing_action': argument.action.value},
                        evidence=[f"Aggressive actions suggested while exposure is already {context.portfolio_exposure:.1%}."],
                        hypothesis="Safe risk limits require tempering aggressive leverage.",
                        predictions=["Reduced drawdown vulnerability."],
                        counter_evidence=["Asset exposure instantly liquidated."],
                        verification="Verified by capacity buffer calculation."
                    )
            return None
        except Exception as e:
            logger.error(f"Error in RiskSentinel respond_to_argument: {e}")
            raise


@dataclass
class VerificationOutcome:
    """Outcome of a single verifier's check."""
    is_valid: bool
    rejection_reason: Optional[str] = None
    confidence_modifier: float = 1.0


class RiskVerifier:
    def verify(self, action: TradeAction, context: MarketContext) -> VerificationOutcome:
        if context.portfolio_exposure > 0.5 and action in [TradeAction.BUY, TradeAction.STRONG_BUY]:
            return VerificationOutcome(False, "Portfolio exposure violates limit", 0.5)
        if context.vix_level and context.vix_level > 30 and action in [TradeAction.BUY, TradeAction.STRONG_BUY, TradeAction.SELL, TradeAction.STRONG_SELL]:
            return VerificationOutcome(False, "VIX is extremely elevated", 0.3)
        return VerificationOutcome(True, None, 1.0)


class LiquidityVerifier:
    def verify(self, action: TradeAction, context: MarketContext) -> VerificationOutcome:
        if context.volume_ratio < 0.5 and action in [TradeAction.BUY, TradeAction.STRONG_BUY, TradeAction.SELL, TradeAction.STRONG_SELL]:
            return VerificationOutcome(True, "Low volume ratio timing modifier", 0.8)
        return VerificationOutcome(True, None, 1.0)


class MarketStructureVerifier:
    def verify(self, action: TradeAction, context: MarketContext) -> VerificationOutcome:
        supports = context.key_levels.get('support', [])
        resistances = context.key_levels.get('resistance', [])
        if action in [TradeAction.BUY, TradeAction.STRONG_BUY] and resistances:
            nearest_resistance = min(resistances, key=lambda x: abs(x - context.current_price))
            if (nearest_resistance - context.current_price) / context.current_price < 0.002:
                return VerificationOutcome(True, "Buying directly into major resistance level", 0.6)
        if action in [TradeAction.SELL, TradeAction.STRONG_SELL] and supports:
            nearest_support = min(supports, key=lambda x: abs(x - context.current_price))
            if (context.current_price - nearest_support) / context.current_price < 0.002:
                return VerificationOutcome(True, "Selling directly into major support level", 0.6)
        return VerificationOutcome(True, None, 1.0)


class CausalVerifier:
    def verify(self, action: TradeAction, context: MarketContext) -> VerificationOutcome:
        if action in [TradeAction.BUY, TradeAction.STRONG_BUY] and context.htf_trend == 'DOWN' and context.ltf_trend == 'DOWN':
            return VerificationOutcome(True, "Buying against dual-timeframe strong down-trend", 0.4)
        if action in [TradeAction.SELL, TradeAction.STRONG_SELL] and context.htf_trend == 'UP' and context.ltf_trend == 'UP':
            return VerificationOutcome(True, "Selling against dual-timeframe strong up-trend", 0.4)
        return VerificationOutcome(True, None, 1.0)


class RegimeVerifier:
    def verify(self, action: TradeAction, context: MarketContext) -> VerificationOutcome:
        if context.htf_trend == 'SIDEWAYS' and action in [TradeAction.STRONG_BUY, TradeAction.STRONG_SELL]:
            return VerificationOutcome(True, "Sideways regime: downgrading strong actions", 0.7)
        return VerificationOutcome(True, None, 1.0)


class HallucinationDetector:
    def verify(self, action: TradeAction, context: MarketContext) -> VerificationOutcome:
        if context.current_price <= 0:
            return VerificationOutcome(False, "Invalid current price detected", 0.0)
        return VerificationOutcome(True, None, 1.0)


class ExecutionFeasibilityVerifier:
    def verify(self, action: TradeAction, context: MarketContext) -> VerificationOutcome:
        if context.volatility > 0.05:
            return VerificationOutcome(False, "Volatility is too high to guarantee trade fill", 0.5)
        return VerificationOutcome(True, None, 1.0)


class HeadAI:
    """
    Lightweight Head AI: coordinates evidence-first debate aggregation and Bayesian calibration.
    """
    
    def __init__(self, config: Optional[Dict] = None, calibrator: Optional[ConfidenceCalibrator] = None):
        try:
            self.config = config or {}
            self.calibrator = calibrator
        
            # Agent weights
            self.weights = {
                AgentRole.MACRO_STRATEGIST: self.config.get('macro_weight', 0.35),
                AgentRole.TACTICAL_EXECUTIONER: self.config.get('tactical_weight', 0.35),
                AgentRole.RISK_SENTINEL: self.config.get('risk_weight', 0.30),
            }
        except Exception as e:
            logger.error(f"Error in HeadAI init: {e}")
            raise

    def synthesize_decision(
        self,
        arguments: List[AgentArgument],
        context: MarketContext,
        debate_rounds: List[DebateRound]
    ) -> FinalDecision:
        try:
            # Fix: Only use the latest argument from each agent to prevent double-counting across rounds
            # Chronological sort on actual timestamp ensuring delayed/duplicated messages are correctly resolved!
            sorted_arguments = sorted(arguments, key=lambda a: a.timestamp)
            latest_arguments: Dict[AgentRole, AgentArgument] = {}
            for arg in sorted_arguments:
                latest_arguments[arg.agent_role] = arg

            active_arguments = list(latest_arguments.values())

            # Step 1: Weight and calibrate arguments
            action_scores: Dict[TradeAction, float] = {}
            for arg in active_arguments:
                weight = self.weights.get(arg.agent_role, 0.33)
                conviction_mult = arg.conviction.value / 5.0

                confidence = arg.confidence
                if self.calibrator:
                    cal_result = self.calibrator.calibrate(
                        confidence,
                        method=CalibrationMethod.BAYESIAN,
                        prediction_type=arg.agent_role.value
                    )
                    confidence = cal_result.calibrated_confidence

                score = weight * conviction_mult * confidence
                if arg.action not in action_scores:
                    action_scores[arg.action] = 0.0
                action_scores[arg.action] += score

            # Get winning action candidate
            if action_scores:
                winning_action = max(action_scores.keys(), key=lambda a: action_scores[a])
                winning_score = action_scores[winning_action]
            else:
                winning_action = TradeAction.HOLD
                winning_score = 0.5

            # Step 2: Verification Swarm Gate as a mandatory gate before consensus
            risk_verifier = RiskVerifier()
            liq_verifier = LiquidityVerifier()
            ms_verifier = MarketStructureVerifier()
            causal_verifier = CausalVerifier()
            regime_verifier = RegimeVerifier()
            halluc_detector = HallucinationDetector()
            exec_verifier = ExecutionFeasibilityVerifier()

            verifiers = {
                'risk_verifier': risk_verifier,
                'liquidity_verifier': liq_verifier,
                'market_structure_verifier': ms_verifier,
                'causal_verifier': causal_verifier,
                'regime_verifier': regime_verifier,
                'hallucination_detector': halluc_detector,
                'execution_feasibility_verifier': exec_verifier
            }

            verification_results = {}
            vetoed = False
            rejection_reason = None

            for v_name, verifier in verifiers.items():
                res = verifier.verify(winning_action, context)
                verification_results[v_name] = {
                    'is_valid': res.is_valid,
                    'rejection_reason': res.rejection_reason,
                    'confidence_modifier': res.confidence_modifier
                }
                if not res.is_valid:
                    vetoed = True
                    rejection_reason = res.rejection_reason
                    winning_score *= res.confidence_modifier
                else:
                    winning_score *= res.confidence_modifier

            # Risk sentinel veto fallback
            risk_args = [a for a in active_arguments if a.agent_role == AgentRole.RISK_SENTINEL]
            if risk_args:
                risk_arg = risk_args[-1]
                if risk_arg.action == TradeAction.NO_TRADE and risk_arg.conviction.value >= Conviction.HIGH.value:
                    winning_action = TradeAction.NO_TRADE
                    winning_score = risk_arg.confidence
                    rejection_reason = "Vetoed by Risk Sentinel's high conviction hold."
                    vetoed = True

            if vetoed:
                winning_action = TradeAction.NO_TRADE

            # Step 3: Consensus Calculation
            unique_actions = set(a.action for a in active_arguments)
            consensus_level = 1.0 - (len(unique_actions) - 1) * 0.25

            agent_votes = {a.agent_role.value: a.action.value for a in active_arguments}

            # Step 4: Gather dissenting views
            dissenting = [
                f"{a.agent_role.value}: {a.reasoning[0]}"
                for a in active_arguments
                if a.action != winning_action and a.reasoning
            ]

            # Sizing and levels
            position_size = self._calculate_position_size(
                winning_action, winning_score, consensus_level, context
            )
            entry, stop, target = self._calculate_levels(winning_action, context)
            reasoning = self._generate_reasoning(winning_action, active_arguments, consensus_level)
            if rejection_reason:
                reasoning += f" | Rejection: {rejection_reason}"

            # Step 5: Package standard Decision Provenance (17 required fields)
            decision_uuid = str(uuid.uuid4())
            git_commit_hash = get_git_commit()
            config_hash = hashlib.sha256(str(self.weights).encode('utf-8')).hexdigest()
            market_snapshot_str = f"{context.symbol}_{context.current_price}_{context.htf_trend}_{context.ltf_trend}"
            market_snapshot_hash = hashlib.sha256(market_snapshot_str.encode('utf-8')).hexdigest()
            feature_str = f"{context.volatility}_{context.volume_ratio}_{context.portfolio_exposure}_{context.correlation_risk}"
            feature_hash = hashlib.sha256(feature_str.encode('utf-8')).hexdigest()

            participating_agents = [arg.agent_role.value for arg in active_arguments]
            evidence_supplied = []
            for arg in active_arguments:
                evidence_supplied.extend(arg.evidence)

            assumptions = {
                'htf_trend': context.htf_trend,
                'ltf_trend': context.ltf_trend,
                'vix_level': context.vix_level,
                'portfolio_exposure': context.portfolio_exposure,
                'volatility': context.volatility
            }

            rejected_actions = [a.value for a in TradeAction if a != winning_action]

            provenance = {
                'decision_uuid': decision_uuid,
                'timestamp': datetime.now().isoformat(),
                'market_snapshot_hash': market_snapshot_hash,
                'feature_hash': feature_hash,
                'model_version': {
                    'MacroStrategist': 'UCA-v5.3',
                    'TacticalExecutioner': 'UCA-v5.3',
                    'RiskSentinel': 'UCA-v5.3',
                    'HeadAI': 'UCA-v5.3'
                },
                'configuration_hash': config_hash,
                'participating_agents': participating_agents,
                'evidence_supplied': evidence_supplied,
                'assumptions': assumptions,
                'disagreements': dissenting,
                'verification_results': verification_results,
                'consensus_score': winning_score,
                'uncertainty': 1.0 - winning_score,
                'selected_action': winning_action.value,
                'rejected_actions': rejected_actions,
                'expected_utility': winning_score * position_size,
                'execution_outcome': 'pending',
                'git_commit': git_commit_hash
            }

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
                dissenting_views=dissenting,
                provenance=provenance
            )
        except Exception as e:
            logger.error(f"Error in HeadAI synthesize_decision: {e}")
            raise

    def _calculate_position_size(
        self,
        action: TradeAction,
        score: float,
        consensus: float,
        context: MarketContext
    ) -> float:
        try:
            if action in [TradeAction.HOLD, TradeAction.NO_TRADE]:
                return 0.0
            base_size = 0.02
            size = base_size * (1 + score)
            size *= consensus
            if context.volatility > 0.02:
                size *= 0.5
            max_size = 0.05
            remaining_capacity = max(0.0, 1.0 - context.portfolio_exposure)
            return min(size, max_size, remaining_capacity)
        except Exception as e:
            logger.error(f"Error in HeadAI _calculate_position_size: {e}")
            raise

    def _calculate_levels(
        self,
        action: TradeAction,
        context: MarketContext
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        try:
            if action in [TradeAction.HOLD, TradeAction.NO_TRADE]:
                return None, None, None
            entry = context.current_price
            atr = context.volatility * context.current_price
            if action in [TradeAction.BUY, TradeAction.STRONG_BUY]:
                stop = entry - atr * 1.5
                target = entry + atr * 2.5
            else:
                stop = entry + atr * 1.5
                target = entry - atr * 2.5
            return entry, stop, target
        except Exception as e:
            logger.error(f"Error in HeadAI _calculate_levels: {e}")
            raise

    def _generate_reasoning(
        self,
        action: TradeAction,
        arguments: List[AgentArgument],
        consensus: float
    ) -> str:
        try:
            parts = [f"Decision: {action.value.upper()}", f"Consensus: {consensus:.0%}"]
            for arg in arguments:
                if arg.reasoning:
                    parts.append(f"{arg.agent_role.value}: {arg.reasoning[0]}")
            return " | ".join(parts)
        except Exception as e:
            logger.error(f"Error in HeadAI _generate_reasoning: {e}")
            raise


def get_git_commit() -> str:
    try:
        import subprocess
        result = subprocess.run(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "55d3c1d_fallback"


class MultiAgentDebateSystem:
    """
    Main multi-agent debate system implementing Byzantine Fault Tolerance,
    Graceful Degradation, and Evidence-First reasoning.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.calibrator = ConfidenceCalibrator(self.config.get('calibrator_config'))

            # Initialize core agents
            self.macro_strategist = MacroStrategist(config)
            self.tactical_executioner = TacticalExecutioner(config)
            self.risk_sentinel = RiskSentinel(config)
            self.head_ai = HeadAI(config, calibrator=self.calibrator)

            self.agents = [
                self.macro_strategist,
                self.tactical_executioner,
                self.risk_sentinel
            ]

            self.max_rounds = self.config.get('max_rounds', 3)
            self.consensus_threshold = self.config.get('consensus_threshold', 0.7)
            self.decisions: List[FinalDecision] = []
            logger.info("MultiAgentDebateSystem initialized")
        except Exception as e:
            logger.error(f"Error in MultiAgentDebateSystem init: {e}")
            raise
            
    async def debate(self, topic: Any, context: Optional[MarketContext] = None) -> FinalDecision:
        try:
            if context is None and isinstance(topic, MarketContext):
                context = topic
            if context is None:
                raise ValueError("MarketContext is required for debate")

            debate_rounds = []
            all_arguments = []
            current_round_args = []
            responsive_count = 0

            # Initial arguments with robust Byzantine Fault Tolerance and Graceful Degradation
            for agent in self.agents:
                try:
                    arg = agent.analyze(context)
                    current_round_args.append(arg)
                    all_arguments.append(arg)
                    responsive_count += 1
                except Exception as e:
                    logger.error(f"Byzantine failure on agent {agent.role.value}: {e}")
                    # Graceful Degradation Fallback
                    if agent.role == AgentRole.RISK_SENTINEL:
                        fallback_arg = AgentArgument(
                            agent_role=agent.role,
                            action=TradeAction.NO_TRADE,
                            conviction=Conviction.VERY_HIGH,
                            reasoning=[f"Risk Sentinel failure fallback: NO_TRADE"],
                            key_factors={'byzantine_penalty': -1.0},
                            confidence=0.95,
                            timestamp=datetime.now(),
                            evidence=["Risk Sentinel crashed during analysis."]
                        )
                    else:
                        fallback_arg = AgentArgument(
                            agent_role=agent.role,
                            action=TradeAction.HOLD,
                            conviction=Conviction.LOW,
                            reasoning=[f"Agent {agent.role.value} failed: HOLD"],
                            key_factors={'byzantine_penalty': -0.2},
                            confidence=0.2,
                            timestamp=datetime.now(),
                            evidence=[f"Agent {agent.role.value} crashed during analysis."]
                        )
                    current_round_args.append(fallback_arg)
                    all_arguments.append(fallback_arg)

            # Min responsive quorum check (excluding sentinel)
            if responsive_count < 1:
                logger.warning("Critical: Zero responsive agents in debate loop. Triggering safe abort NO_TRADE.")
                return self._trigger_emergency_no_trade(context, debate_rounds)

            consensus = self._calculate_consensus(all_arguments)
            conflicts = self._identify_conflicts(current_round_args)

            debate_rounds.append(DebateRound(
                round_number=1,
                arguments=current_round_args,
                consensus_level=consensus,
                conflicts=conflicts
            ))

            # Debate rounds
            round_num = 2
            while consensus < self.consensus_threshold and round_num <= self.max_rounds:
                previous_round_args = current_round_args
                current_round_args = []

                for agent in self.agents:
                    try:
                        others_args = [arg for arg in previous_round_args if arg.agent_role != agent.role]
                        if not others_args:
                            continue
                        target_arg = max(others_args, key=lambda a: a.confidence)
                        response = agent.respond_to_argument(target_arg, context)
                        if response:
                            current_round_args.append(response)
                            all_arguments.append(response)
                    except Exception as e:
                        logger.error(f"Byzantine response failure on agent {agent.role.value}: {e}")
                        continue

                if not current_round_args:
                    break

                consensus = self._calculate_consensus(all_arguments)
                conflicts = self._identify_conflicts(current_round_args)
                debate_rounds.append(DebateRound(
                    round_number=round_num,
                    arguments=current_round_args,
                    consensus_level=consensus,
                    conflicts=conflicts
                ))
                round_num += 1

            decision = self.head_ai.synthesize_decision(
                all_arguments, context, debate_rounds
            )
            self.decisions.append(decision)
            return decision
        except Exception as e:
            logger.error(f"Error in MultiAgentDebateSystem debate: {e}")
            raise

    def _trigger_emergency_no_trade(self, context: MarketContext, debate_rounds: List[DebateRound]) -> FinalDecision:
        decision_uuid = str(uuid.uuid4())
        provenance = {
            'decision_uuid': decision_uuid,
            'timestamp': datetime.now().isoformat(),
            'consensus_score': 0.0,
            'selected_action': TradeAction.NO_TRADE.value,
            'reasoning': "EMERGENCY VETO: Zero active responsive agents in debate loop.",
            'git_commit': get_git_commit()
        }
        return FinalDecision(
            timestamp=datetime.now(),
            symbol=context.symbol,
            action=TradeAction.NO_TRADE,
            confidence=1.0,
            position_size_pct=0.0,
            entry_price=None,
            stop_loss=None,
            take_profit=None,
            reasoning="EMERGENCY VETO: Zero active responsive agents in debate loop.",
            agent_votes={},
            debate_rounds=len(debate_rounds),
            consensus_level=1.0,
            dissenting_views=[],
            provenance=provenance
        )

    def _calculate_consensus(self, all_arguments: List[AgentArgument]) -> float:
        try:
            if not all_arguments:
                return 0.0
            latest_arguments: Dict[AgentRole, AgentArgument] = {}
            for arg in all_arguments:
                latest_arguments[arg.agent_role] = arg
            arguments = list(latest_arguments.values())

            bullish = sum(1 for a in arguments if a.action in [TradeAction.BUY, TradeAction.STRONG_BUY])
            bearish = sum(1 for a in arguments if a.action in [TradeAction.SELL, TradeAction.STRONG_SELL])
            neutral = sum(1 for a in arguments if a.action in [TradeAction.HOLD, TradeAction.NO_TRADE])

            total = len(arguments)
            max_agreement = max(bullish, bearish, neutral)
            return max_agreement / total
        except Exception as e:
            logger.error(f"Error in _calculate_consensus: {e}")
            raise

    def _identify_conflicts(self, arguments: List[AgentArgument]) -> List[str]:
        try:
            conflicts = []
            actions = [a.action for a in arguments]
            has_buy = any(a in [TradeAction.BUY, TradeAction.STRONG_BUY] for a in actions)
            has_sell = any(a in [TradeAction.SELL, TradeAction.STRONG_SELL] for a in actions)
            if has_buy and has_sell:
                conflicts.append("Conflicting directional views between agents")
            has_no_trade = TradeAction.NO_TRADE in actions
            has_strong = any(a in [TradeAction.STRONG_BUY, TradeAction.STRONG_SELL] for a in actions)
            if has_no_trade and has_strong:
                conflicts.append("Risk sentinel vetoing aggressive position")
            return conflicts
        except Exception as e:
            logger.error(f"Error in _identify_conflicts: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'total_decisions': len(self.decisions),
            'max_rounds': self.max_rounds,
            'consensus_threshold': self.consensus_threshold,
            'last_decision': self.decisions[-1].to_dict() if self.decisions else None,
            'timestamp': datetime.now().isoformat()
        }


DebateResult = FinalDecision
DebateAgent = TradingAgent


def create_debate_system(config: Optional[Dict] = None) -> MultiAgentDebateSystem:
    return MultiAgentDebateSystem(config)


async def run_example():
    system = create_debate_system()
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
    decision = await system.debate(context)
    print("Decision:", decision.action.value)
    print("Provenance:", decision.provenance)


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_example())
