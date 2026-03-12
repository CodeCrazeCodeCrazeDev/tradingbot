"""
Multi-Agent Reinforcement Learning (MARL) Trading System

Implements multiple specialized AI models that "debate" each other:
- The Macro Strategist: Operates on HTF, identifies themes and key levels
- The Tactical Executioner: Works on LTF, precise entry/exit timing
- The Risk Sentinel: Monitors portfolio exposure and black swan signals

A "Head AI" weighs the arguments to make final decisions.

Features:
- Multi-agent debate architecture
- Specialized trading personas
- Consensus decision making
- Federated learning across agents
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent roles in the trading system"""
    MACRO_STRATEGIST = "macro_strategist"
    TACTICAL_EXECUTIONER = "tactical_executioner"
    RISK_SENTINEL = "risk_sentinel"
    HEAD_AI = "head_ai"


class TradeAction(Enum):
    """Possible trading actions"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"
    REDUCE_EXPOSURE = "reduce_exposure"
    HEDGE = "hedge"
    EXIT_ALL = "exit_all"


class Confidence(Enum):
    """Confidence levels"""
    VERY_HIGH = 0.9
    HIGH = 0.75
    MEDIUM = 0.5
    LOW = 0.25
    VERY_LOW = 0.1


@dataclass
class AgentArgument:
    """Argument from an agent"""
    agent: AgentRole
    action: TradeAction
    confidence: float
    reasoning: str
    supporting_evidence: List[str]
    risk_assessment: float  # 0-1
    timeframe: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'agent': self.agent.value,
            'action': self.action.value,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'supporting_evidence': self.supporting_evidence,
            'risk_assessment': self.risk_assessment,
            'timeframe': self.timeframe,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ConsensusDecision:
    """Final consensus decision from Head AI"""
    action: TradeAction
    confidence: float
    position_size_pct: float
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    arguments: List[AgentArgument]
    dissenting_views: List[AgentArgument]
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'action': self.action.value,
            'confidence': self.confidence,
            'position_size_pct': self.position_size_pct,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'arguments': [a.to_dict() for a in self.arguments],
            'dissenting_views': [d.to_dict() for d in self.dissenting_views],
            'reasoning': self.reasoning,
            'timestamp': self.timestamp.isoformat()
        }


class TradingAgent:
    """Base class for trading agents"""
    
    def __init__(self, role: AgentRole, config: Optional[Dict[str, Any]] = None):
        try:
            self.role = role
            self.config = config or {}
            self.memory: deque = deque(maxlen=1000)
            self.performance_history: deque = deque(maxlen=100)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def analyze(self, market_data: Dict[str, Any]) -> AgentArgument:
        """Analyze market and produce argument - to be overridden"""
    
    def learn_from_outcome(self, decision: ConsensusDecision, outcome: Dict[str, Any]):
        """Learn from trade outcome"""
        try:
            self.performance_history.append({
                'decision': decision.to_dict(),
                'outcome': outcome,
                'timestamp': datetime.now()
            })
        except Exception as e:
            logger.error(f"Error in learn_from_outcome: {e}")
            raise


class MacroStrategist(TradingAgent):
    """
    The Macro Strategist
    
    Operates on higher timeframes, identifies overarching themes
    and key levels. Focuses on:
    - Market regime identification
    - Key support/resistance levels
    - Macro trends and themes
    - Intermarket correlations
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            super().__init__(AgentRole.MACRO_STRATEGIST, config)
            self.timeframe = "H4/D1"
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(self, market_data: Dict[str, Any]) -> AgentArgument:
        """Analyze macro conditions"""
        # Extract relevant data
        try:
            prices = market_data.get('prices_htf', np.array([]))
            regime = market_data.get('regime', 'unknown')
            trend = market_data.get('trend', 'neutral')
            key_levels = market_data.get('key_levels', {})
        
            evidence = []
        
            # Analyze trend
            if len(prices) > 20:
                sma20 = np.mean(prices[-20:])
                sma50 = np.mean(prices[-50:]) if len(prices) > 50 else sma20
            
                if prices[-1] > sma20 > sma50:
                    trend_signal = "bullish"
                    evidence.append(f"Price above SMA20 ({sma20:.2f}) and SMA50 ({sma50:.2f})")
                elif prices[-1] < sma20 < sma50:
                    trend_signal = "bearish"
                    evidence.append(f"Price below SMA20 ({sma20:.2f}) and SMA50 ({sma50:.2f})")
                else:
                    trend_signal = "neutral"
                    evidence.append("Mixed moving average signals")
            else:
                trend_signal = "neutral"
        
            # Analyze regime
            if regime == 'trending':
                evidence.append(f"Market in trending regime - favor trend following")
            elif regime == 'ranging':
                evidence.append(f"Market in ranging regime - favor mean reversion")
        
            # Key levels
            if key_levels:
                current_price = prices[-1] if len(prices) > 0 else 0
                nearest_support = key_levels.get('support', current_price * 0.95)
                nearest_resistance = key_levels.get('resistance', current_price * 1.05)
            
                if current_price < nearest_support * 1.02:
                    evidence.append(f"Near support at {nearest_support:.2f}")
                if current_price > nearest_resistance * 0.98:
                    evidence.append(f"Near resistance at {nearest_resistance:.2f}")
        
            # Determine action
            if trend_signal == "bullish" and regime != 'ranging':
                action = TradeAction.BUY
                confidence = 0.7
                reasoning = "Macro trend is bullish with favorable regime"
            elif trend_signal == "bearish" and regime != 'ranging':
                action = TradeAction.SELL
                confidence = 0.7
                reasoning = "Macro trend is bearish with favorable regime"
            else:
                action = TradeAction.HOLD
                confidence = 0.5
                reasoning = "No clear macro direction"
        
            return AgentArgument(
                agent=self.role,
                action=action,
                confidence=confidence,
                reasoning=reasoning,
                supporting_evidence=evidence,
                risk_assessment=0.3 if action == TradeAction.HOLD else 0.5,
                timeframe=self.timeframe
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class TacticalExecutioner(TradingAgent):
    """
    The Tactical Executioner
    
    Works on lower timeframes, specializes in:
    - Precise entry/exit timing
    - Liquidity grab identification
    - Order flow analysis
    - Micro-structure patterns
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            super().__init__(AgentRole.TACTICAL_EXECUTIONER, config)
            self.timeframe = "M5/M15"
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(self, market_data: Dict[str, Any]) -> AgentArgument:
        """Analyze tactical conditions"""
        try:
            prices = market_data.get('prices_ltf', np.array([]))
            order_flow = market_data.get('order_flow', {})
            liquidity = market_data.get('liquidity', {})
        
            evidence = []
        
            # Order flow analysis
            delta = order_flow.get('delta', 0)
            absorption = order_flow.get('absorption', 0)
        
            if delta > 0.3:
                evidence.append(f"Strong buying pressure (delta: {delta:.2f})")
                flow_signal = "bullish"
            elif delta < -0.3:
                evidence.append(f"Strong selling pressure (delta: {delta:.2f})")
                flow_signal = "bearish"
            else:
                flow_signal = "neutral"
        
            # Liquidity analysis
            liquidity_above = liquidity.get('above', 0)
            liquidity_below = liquidity.get('below', 0)
        
            if liquidity_above > liquidity_below * 1.5:
                evidence.append("Significant liquidity above - potential target")
            elif liquidity_below > liquidity_above * 1.5:
                evidence.append("Significant liquidity below - potential target")
        
            # Price action
            if len(prices) > 10:
                recent_high = np.max(prices[-10:])
                recent_low = np.min(prices[-10:])
                current = prices[-1]
            
                range_position = (current - recent_low) / (recent_high - recent_low + 1e-10)
            
                if range_position > 0.8:
                    evidence.append("Price at top of recent range")
                elif range_position < 0.2:
                    evidence.append("Price at bottom of recent range")
        
            # Determine action
            if flow_signal == "bullish" and absorption > 0.5:
                action = TradeAction.BUY
                confidence = 0.75
                reasoning = "Strong buying flow with absorption - optimal entry"
            elif flow_signal == "bearish" and absorption > 0.5:
                action = TradeAction.SELL
                confidence = 0.75
                reasoning = "Strong selling flow with absorption - optimal entry"
            elif flow_signal == "bullish":
                action = TradeAction.BUY
                confidence = 0.6
                reasoning = "Buying flow detected"
            elif flow_signal == "bearish":
                action = TradeAction.SELL
                confidence = 0.6
                reasoning = "Selling flow detected"
            else:
                action = TradeAction.HOLD
                confidence = 0.4
                reasoning = "No clear tactical signal"
        
            return AgentArgument(
                agent=self.role,
                action=action,
                confidence=confidence,
                reasoning=reasoning,
                supporting_evidence=evidence,
                risk_assessment=0.4,
                timeframe=self.timeframe
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class RiskSentinel(TradingAgent):
    """
    The Risk Sentinel
    
    Monitors overall portfolio exposure and risk:
    - Portfolio correlation
    - Black swan signals
    - Drawdown monitoring
    - Position sizing recommendations
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            super().__init__(AgentRole.RISK_SENTINEL, config)
            self.timeframe = "ALL"
            self.max_drawdown = config.get('max_drawdown', 0.1) if config else 0.1
            self.max_correlation = config.get('max_correlation', 0.7) if config else 0.7
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(self, market_data: Dict[str, Any]) -> AgentArgument:
        """Analyze risk conditions"""
        try:
            portfolio = market_data.get('portfolio', {})
            volatility = market_data.get('volatility', {})
            correlations = market_data.get('correlations', {})
        
            evidence = []
            risk_score = 0
        
            # Drawdown check
            current_drawdown = portfolio.get('drawdown', 0)
            if current_drawdown > self.max_drawdown:
                evidence.append(f"CRITICAL: Drawdown {current_drawdown:.1%} exceeds limit")
                risk_score += 0.4
            elif current_drawdown > self.max_drawdown * 0.7:
                evidence.append(f"WARNING: Drawdown {current_drawdown:.1%} approaching limit")
                risk_score += 0.2
        
            # Volatility check
            current_vol = volatility.get('current', 0)
            avg_vol = volatility.get('average', current_vol)
        
            if avg_vol > 0:
                vol_ratio = current_vol / avg_vol
                if vol_ratio > 2:
                    evidence.append(f"ELEVATED: Volatility {vol_ratio:.1f}x normal")
                    risk_score += 0.3
                elif vol_ratio > 1.5:
                    evidence.append(f"Volatility elevated at {vol_ratio:.1f}x normal")
                    risk_score += 0.15
        
            # Correlation check
            max_corr = correlations.get('max_correlation', 0)
            if max_corr > self.max_correlation:
                evidence.append(f"HIGH CORRELATION: {max_corr:.2f} between positions")
                risk_score += 0.2
        
            # Black swan indicators
            vix = market_data.get('vix', 20)
            if vix > 30:
                evidence.append(f"VIX elevated at {vix}")
                risk_score += 0.2
        
            # Determine action
            if risk_score > 0.6:
                action = TradeAction.EXIT_ALL
                confidence = 0.9
                reasoning = "CRITICAL RISK - Recommend exiting all positions"
            elif risk_score > 0.4:
                action = TradeAction.REDUCE_EXPOSURE
                confidence = 0.8
                reasoning = "Elevated risk - Recommend reducing exposure"
            elif risk_score > 0.2:
                action = TradeAction.HEDGE
                confidence = 0.6
                reasoning = "Moderate risk - Consider hedging"
            else:
                action = TradeAction.HOLD
                confidence = 0.7
                reasoning = "Risk levels acceptable"
                evidence.append("All risk metrics within normal range")
        
            return AgentArgument(
                agent=self.role,
                action=action,
                confidence=confidence,
                reasoning=reasoning,
                supporting_evidence=evidence,
                risk_assessment=risk_score,
                timeframe=self.timeframe
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class HeadAI:
    """
    The Head AI
    
    Weighs arguments from all agents and makes final decision.
    Implements consensus mechanism and conflict resolution.
    """
    
    # Agent weights
    AGENT_WEIGHTS = {
        AgentRole.MACRO_STRATEGIST: 0.35,
        AgentRole.TACTICAL_EXECUTIONER: 0.35,
        AgentRole.RISK_SENTINEL: 0.30,
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.decision_history: deque = deque(maxlen=500)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def make_decision(
        self,
        arguments: List[AgentArgument],
        current_price: float
    ) -> ConsensusDecision:
        """
        Make final decision based on agent arguments
        """
        # Separate by agent role
        try:
            agent_args = {arg.agent: arg for arg in arguments}
        
            # Check for risk override
            risk_arg = agent_args.get(AgentRole.RISK_SENTINEL)
            if risk_arg and risk_arg.action in [TradeAction.EXIT_ALL, TradeAction.REDUCE_EXPOSURE]:
                if risk_arg.confidence > 0.7:
                    # Risk override - prioritize safety
                    return self._create_risk_override_decision(risk_arg, arguments, current_price)
        
            # Calculate weighted consensus
            action_scores: Dict[TradeAction, float] = {}
        
            for arg in arguments:
                weight = self.AGENT_WEIGHTS.get(arg.agent, 0.33)
                score = weight * arg.confidence
            
                if arg.action not in action_scores:
                    action_scores[arg.action] = 0
                action_scores[arg.action] += score
        
            # Find winning action
            if action_scores:
                best_action = max(action_scores.items(), key=lambda x: x[1])
                final_action = best_action[0]
                confidence = best_action[1]
            else:
                final_action = TradeAction.HOLD
                confidence = 0.5
        
            # Find dissenting views
            dissenting = [
                arg for arg in arguments 
                if arg.action != final_action and arg.confidence > 0.5
            ]
        
            # Calculate position size based on confidence and risk
            avg_risk = np.mean([arg.risk_assessment for arg in arguments])
            position_size = self._calculate_position_size(confidence, avg_risk)
        
            # Calculate entry/exit levels
            entry_price = current_price
            if final_action in [TradeAction.BUY, TradeAction.STRONG_BUY]:
                stop_loss = current_price * 0.98  # 2% stop
                take_profit = current_price * 1.04  # 4% target
            elif final_action in [TradeAction.SELL, TradeAction.STRONG_SELL]:
                stop_loss = current_price * 1.02
                take_profit = current_price * 0.96
            else:
                stop_loss = None
                take_profit = None
        
            # Generate reasoning
            reasoning = self._generate_reasoning(arguments, final_action, confidence, dissenting)
        
            decision = ConsensusDecision(
                action=final_action,
                confidence=confidence,
                position_size_pct=position_size,
                entry_price=entry_price if final_action not in [TradeAction.HOLD] else None,
                stop_loss=stop_loss,
                take_profit=take_profit,
                arguments=arguments,
                dissenting_views=dissenting,
                reasoning=reasoning
            )
        
            self.decision_history.append(decision)
        
            return decision
        except Exception as e:
            logger.error(f"Error in make_decision: {e}")
            raise
    
    def _create_risk_override_decision(
        self,
        risk_arg: AgentArgument,
        all_args: List[AgentArgument],
        current_price: float
    ) -> ConsensusDecision:
        """Create decision when risk sentinel overrides"""
        return ConsensusDecision(
            action=risk_arg.action,
            confidence=risk_arg.confidence,
            position_size_pct=0,
            entry_price=None,
            stop_loss=None,
            take_profit=None,
            arguments=all_args,
            dissenting_views=[a for a in all_args if a.agent != AgentRole.RISK_SENTINEL],
            reasoning=f"RISK OVERRIDE: {risk_arg.reasoning}"
        )
    
    def _calculate_position_size(self, confidence: float, risk: float) -> float:
        """Calculate position size based on confidence and risk"""
        try:
            base_size = 0.02  # 2% base position
        
            # Adjust for confidence
            confidence_multiplier = confidence / 0.5  # 1.0 at 50% confidence
        
            # Adjust for risk (inverse)
            risk_multiplier = 1 - risk
        
            size = base_size * confidence_multiplier * risk_multiplier
        
            # Cap at 5%
            return min(0.05, max(0.005, size))
        except Exception as e:
            logger.error(f"Error in _calculate_position_size: {e}")
            raise
    
    def _generate_reasoning(
        self,
        arguments: List[AgentArgument],
        action: TradeAction,
        confidence: float,
        dissenting: List[AgentArgument]
    ) -> str:
        """Generate human-readable reasoning"""
        try:
            parts = []
        
            parts.append(f"Decision: {action.value.upper()} with {confidence:.0%} confidence")
        
            # Summarize supporting arguments
            supporting = [a for a in arguments if a.action == action]
            if supporting:
                parts.append("Supporting views:")
                for arg in supporting:
                    parts.append(f"  - {arg.agent.value}: {arg.reasoning}")
        
            # Note dissenting views
            if dissenting:
                parts.append("Dissenting views:")
                for arg in dissenting:
                    parts.append(f"  - {arg.agent.value}: {arg.reasoning}")
        
            return "\n".join(parts)
        except Exception as e:
            logger.error(f"Error in _generate_reasoning: {e}")
            raise


class MultiAgentTradingSystem:
    """
    Multi-Agent Reinforcement Learning Trading System
    
    Coordinates multiple specialized agents for trading decisions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Initialize agents
            self.macro_strategist = MacroStrategist(config)
            self.tactical_executioner = TacticalExecutioner(config)
            self.risk_sentinel = RiskSentinel(config)
            self.head_ai = HeadAI(config)
        
            # Decision history
            self.decisions: deque = deque(maxlen=1000)
        
            logger.info("MultiAgentTradingSystem initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze_and_decide(
        self,
        market_data: Dict[str, Any],
        current_price: float
    ) -> ConsensusDecision:
        """
        Run full multi-agent analysis and return consensus decision
        """
        # Gather arguments from all agents
        try:
            arguments = []
        
            # Macro analysis
            macro_arg = self.macro_strategist.analyze(market_data)
            arguments.append(macro_arg)
            logger.info(f"Macro Strategist: {macro_arg.action.value} ({macro_arg.confidence:.0%})")
        
            # Tactical analysis
            tactical_arg = self.tactical_executioner.analyze(market_data)
            arguments.append(tactical_arg)
            logger.info(f"Tactical Executioner: {tactical_arg.action.value} ({tactical_arg.confidence:.0%})")
        
            # Risk analysis
            risk_arg = self.risk_sentinel.analyze(market_data)
            arguments.append(risk_arg)
            logger.info(f"Risk Sentinel: {risk_arg.action.value} ({risk_arg.confidence:.0%})")
        
            # Head AI makes final decision
            decision = self.head_ai.make_decision(arguments, current_price)
        
            self.decisions.append(decision)
        
            logger.info(f"CONSENSUS: {decision.action.value} ({decision.confidence:.0%})")
        
            return decision
        except Exception as e:
            logger.error(f"Error in analyze_and_decide: {e}")
            raise
    
    def learn_from_trade(
        self,
        decision: ConsensusDecision,
        outcome: Dict[str, Any]
    ):
        """Update agents based on trade outcome"""
        try:
            self.macro_strategist.learn_from_outcome(decision, outcome)
            self.tactical_executioner.learn_from_outcome(decision, outcome)
            self.risk_sentinel.learn_from_outcome(decision, outcome)
        except Exception as e:
            logger.error(f"Error in learn_from_trade: {e}")
            raise
    
    def get_agent_performance(self) -> Dict[str, Any]:
        """Get performance metrics for each agent"""
        return {
            'macro_strategist': self._calculate_agent_performance(self.macro_strategist),
            'tactical_executioner': self._calculate_agent_performance(self.tactical_executioner),
            'risk_sentinel': self._calculate_agent_performance(self.risk_sentinel)
        }
    
    def _calculate_agent_performance(self, agent: TradingAgent) -> Dict[str, Any]:
        """Calculate performance metrics for an agent"""
        try:
            history = list(agent.performance_history)
        
            if not history:
                return {'trades': 0}
        
            wins = sum(1 for h in history if h['outcome'].get('pnl', 0) > 0)
        
            return {
                'trades': len(history),
                'win_rate': wins / len(history) if history else 0,
                'avg_confidence': np.mean([h['decision']['confidence'] for h in history])
            }
        except Exception as e:
            logger.error(f"Error in _calculate_agent_performance: {e}")
            raise


# Factory function
def create_multi_agent_system(config: Optional[Dict[str, Any]] = None) -> MultiAgentTradingSystem:
    """Create multi-agent trading system"""
    return MultiAgentTradingSystem(config)
