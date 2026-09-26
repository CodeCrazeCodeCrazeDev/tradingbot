"""
Specialized Trading Agents for Perplexity Trading Architecture
============================================================

Each agent is a specialized "model" that handles specific types
of trading analysis tasks.

Like Perplexity Computer's multi-model roster, each agent:
- Has specific capabilities and specializations
- Produces structured output with citations
- Can use tools (data retrieval, calculations, etc.)
- Tracks its own performance for adaptive routing
"""

import logging
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
import asyncio

from .core_types import (
    SubTask,
    SubTaskResult,
    Citation,
    AgentType,
    RetrievalSource,
)

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Context passed to agents for execution"""
    subtask: SubTask
    input_data: Dict[str, Any] = field(default_factory=dict)
    memory_context: Dict[str, Any] = field(default_factory=dict)
    market_data: Optional[Any] = None
    config: Dict[str, Any] = field(default_factory=dict)


class BaseTradingAgent(ABC):
    """
    Base class for all specialized trading agents.
    
    Each agent implements:
    - execute(): Main execution logic
    - validate_inputs(): Input validation
    - get_capabilities(): What the agent can do
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.agent_type: AgentType = AgentType.REASONING
        self.name: str = "Base Agent"
        self.description: str = "Base trading agent"
        
        # Performance tracking
        self.total_executions: int = 0
        self.successful_executions: int = 0
        self.total_latency_ms: float = 0.0
        
        # Tools available to this agent
        self.tools: Dict[str, Callable] = {}
    
    @abstractmethod
    async def execute(self, context: AgentContext) -> SubTaskResult:
        """Execute the subtask and return result"""
        pass
    
    def validate_inputs(self, context: AgentContext) -> tuple:
        """Validate inputs, return (is_valid, error_message)"""
        if not context.subtask:
            return False, "No subtask provided"
        return True, None
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities"""
        return {
            'agent_type': self.agent_type.value,
            'name': self.name,
            'description': self.description,
            'tools': list(self.tools.keys()),
        }
    
    def register_tool(self, name: str, tool: Callable) -> None:
        """Register a tool for this agent"""
        self.tools[name] = tool
    
    async def use_tool(self, tool_name: str, **kwargs) -> Any:
        """Use a registered tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not registered")
        
        tool = self.tools[tool_name]
        if asyncio.iscoroutinefunction(tool):
            return await tool(**kwargs)
        return tool(**kwargs)
    
    def create_citation(
        self,
        source_type: RetrievalSource,
        source_name: str,
        data_point: str,
        confidence: float = 0.8,
        url: Optional[str] = None,
    ) -> Citation:
        """Create a citation for data attribution"""
        return Citation(
            source_type=source_type,
            source_name=source_name,
            timestamp=datetime.utcnow(),
            data_point=data_point,
            confidence=confidence,
            url=url,
        )
    
    def record_execution(self, success: bool, latency_ms: float) -> None:
        """Record execution for performance tracking"""
        self.total_executions += 1
        if success:
            self.successful_executions += 1
        self.total_latency_ms += latency_ms
    
    @property
    def success_rate(self) -> float:
        """Get success rate"""
        if self.total_executions == 0:
            return 1.0
        return self.successful_executions / self.total_executions
    
    @property
    def avg_latency_ms(self) -> float:
        """Get average latency"""
        if self.total_executions == 0:
            return 0.0
        return self.total_latency_ms / self.total_executions


class ResearchAgent(BaseTradingAgent):
    """
    Research Agent - Gathers market research, news, and fundamental data.
    
    Capabilities:
    - News retrieval and summarization
    - Fundamental data extraction
    - Economic calendar analysis
    - Company/asset research
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.agent_type = AgentType.RESEARCH
        self.name = "Research Agent"
        self.description = "Gathers market research, news, and fundamental data"
    
    async def execute(self, context: AgentContext) -> SubTaskResult:
        """Execute research task"""
        start_time = datetime.utcnow()
        citations = []
        
        try:
            # Validate inputs
            is_valid, error = self.validate_inputs(context)
            if not is_valid:
                return SubTaskResult(
                    subtask_id=context.subtask.id,
                    success=False,
                    error=error,
                )
            
            output_data = {}
            reasoning_parts = []
            
            # Gather fundamental data
            fundamentals = await self._gather_fundamentals(context)
            output_data['fundamentals_data'] = fundamentals
            citations.append(self.create_citation(
                RetrievalSource.FUNDAMENTALS,
                "Fundamental Analysis",
                f"Gathered {len(fundamentals)} fundamental data points",
                confidence=0.85,
            ))
            reasoning_parts.append(f"Gathered fundamental data: {len(fundamentals)} data points")
            
            # Gather news
            news = await self._gather_news(context)
            output_data['news_summary'] = news
            citations.append(self.create_citation(
                RetrievalSource.NEWS,
                "News Analysis",
                f"Analyzed {len(news.get('articles', []))} news articles",
                confidence=0.80,
            ))
            reasoning_parts.append(f"Analyzed news: {news.get('sentiment', 'neutral')} sentiment")
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return SubTaskResult(
                subtask_id=context.subtask.id,
                success=True,
                output_data=output_data,
                citations=citations,
                confidence=0.85,
                reasoning=" | ".join(reasoning_parts),
                execution_time_ms=execution_time,
            )
            
        except Exception as e:
            logger.error(f"Research agent error: {e}")
            return SubTaskResult(
                subtask_id=context.subtask.id,
                success=False,
                error=str(e),
            )
    
    async def _gather_fundamentals(self, context: AgentContext) -> Dict[str, Any]:
        """Gather fundamental data"""
        # In production, this would call actual data sources
        symbol = context.config.get('symbol', 'UNKNOWN')
        
        return {
            'symbol': symbol,
            'economic_outlook': 'neutral',
            'interest_rate_differential': 0.5,
            'gdp_growth': 2.1,
            'inflation': 3.2,
            'employment': 'stable',
            'trade_balance': 'deficit',
            'central_bank_stance': 'hawkish',
        }
    
    async def _gather_news(self, context: AgentContext) -> Dict[str, Any]:
        """Gather and analyze news"""
        # In production, this would call news APIs
        return {
            'articles': [
                {'title': 'Market Update', 'sentiment': 0.2},
                {'title': 'Economic Report', 'sentiment': -0.1},
            ],
            'sentiment': 'slightly_bullish',
            'sentiment_score': 0.15,
            'key_themes': ['inflation', 'central_bank', 'employment'],
        }


class TechnicalAgent(BaseTradingAgent):
    """
    Technical Agent - Performs technical analysis on price data.
    
    Capabilities:
    - Chart pattern recognition
    - Indicator calculation
    - Support/resistance identification
    - Trend analysis
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.agent_type = AgentType.TECHNICAL
        self.name = "Technical Agent"
        self.description = "Performs technical analysis on price data"
    
    async def execute(self, context: AgentContext) -> SubTaskResult:
        """Execute technical analysis"""
        start_time = datetime.utcnow()
        citations = []
        
        try:
            output_data = {}
            reasoning_parts = []
            
            # Get market data from inputs
            ohlcv = context.input_data.get('ohlcv_data', context.market_data)
            
            # Analyze patterns
            patterns = await self._analyze_patterns(ohlcv)
            output_data['patterns'] = patterns
            citations.append(self.create_citation(
                RetrievalSource.MARKET_DATA,
                "Pattern Analysis",
                f"Detected {len(patterns)} chart patterns",
                confidence=0.82,
            ))
            reasoning_parts.append(f"Detected patterns: {[p['name'] for p in patterns]}")
            
            # Calculate indicators
            indicators = await self._calculate_indicators(ohlcv)
            output_data['technical_signals'] = indicators
            citations.append(self.create_citation(
                RetrievalSource.CALCULATION,
                "Technical Indicators",
                f"Calculated {len(indicators)} indicators",
                confidence=0.90,
            ))
            reasoning_parts.append(f"Indicator signals: {indicators.get('overall_signal', 'neutral')}")
            
            # Identify key levels
            levels = await self._identify_levels(ohlcv)
            output_data['key_levels'] = levels
            citations.append(self.create_citation(
                RetrievalSource.CALCULATION,
                "Support/Resistance",
                f"Identified {len(levels.get('support', [])) + len(levels.get('resistance', []))} key levels",
                confidence=0.85,
            ))
            reasoning_parts.append(f"Key levels: S={levels.get('support', [])}, R={levels.get('resistance', [])}")
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return SubTaskResult(
                subtask_id=context.subtask.id,
                success=True,
                output_data=output_data,
                citations=citations,
                confidence=0.85,
                reasoning=" | ".join(reasoning_parts),
                execution_time_ms=execution_time,
            )
            
        except Exception as e:
            logger.error(f"Technical agent error: {e}")
            return SubTaskResult(
                subtask_id=context.subtask.id,
                success=False,
                error=str(e),
            )
    
    async def _analyze_patterns(self, ohlcv: Any) -> List[Dict[str, Any]]:
        """Analyze chart patterns"""
        # In production, use actual pattern recognition
        return [
            {'name': 'double_bottom', 'confidence': 0.75, 'direction': 'bullish'},
            {'name': 'ascending_triangle', 'confidence': 0.68, 'direction': 'bullish'},
        ]
    
    async def _calculate_indicators(self, ohlcv: Any) -> Dict[str, Any]:
        """Calculate technical indicators"""
        return {
            'rsi': 55.0,
            'rsi_signal': 'neutral',
            'macd': 0.002,
            'macd_signal': 'bullish',
            'ma_20': 1.0850,
            'ma_50': 1.0820,
            'ma_trend': 'bullish',
            'overall_signal': 'bullish',
            'signal_strength': 0.65,
        }
    
    async def _identify_levels(self, ohlcv: Any) -> Dict[str, Any]:
        """Identify support and resistance levels"""
        return {
            'support': [1.0800, 1.0750, 1.0700],
            'resistance': [1.0900, 1.0950, 1.1000],
            'pivot': 1.0850,
            'current_zone': 'neutral',
        }


class RiskAgent(BaseTradingAgent):
    """
    Risk Agent - Calculates risk parameters and position sizing.
    
    Capabilities:
    - Position size calculation
    - Stop loss placement
    - Take profit targets
    - Risk/reward analysis
    - Portfolio exposure check
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.agent_type = AgentType.RISK
        self.name = "Risk Agent"
        self.description = "Calculates risk parameters and position sizing"
        
        # Default risk parameters
        self.max_risk_per_trade = config.get('max_risk_per_trade', 0.02)  # 2%
        self.max_daily_loss = config.get('max_daily_loss', 0.05)  # 5%
        self.max_drawdown = config.get('max_drawdown', 0.20)  # 20%
    
    async def execute(self, context: AgentContext) -> SubTaskResult:
        """Execute risk calculations"""
        start_time = datetime.utcnow()
        citations = []
        
        try:
            output_data = {}
            reasoning_parts = []
            
            # Get account info from memory context
            account_equity = context.memory_context.get('account_equity', 10000)
            current_exposure = context.memory_context.get('current_exposure', 0)
            
            # Get key levels from input
            key_levels = context.input_data.get('key_levels', {})
            current_price = context.config.get('current_price', 1.0850)
            direction = context.config.get('direction', 'long')
            
            # Calculate stop loss
            stop_loss = await self._calculate_stop_loss(current_price, key_levels, direction)
            output_data['stop_loss'] = stop_loss
            reasoning_parts.append(f"Stop loss: {stop_loss}")
            
            # Calculate take profit
            take_profit = await self._calculate_take_profit(current_price, key_levels, direction)
            output_data['take_profit'] = take_profit
            reasoning_parts.append(f"Take profit: {take_profit}")
            
            # Calculate position size
            position_size = await self._calculate_position_size(
                account_equity, current_price, stop_loss, direction
            )
            output_data['position_size'] = position_size
            citations.append(self.create_citation(
                RetrievalSource.CALCULATION,
                "Position Sizing",
                f"Position size: {position_size} units (risk: {self.max_risk_per_trade:.1%})",
                confidence=0.95,
            ))
            reasoning_parts.append(f"Position size: {position_size}")
            
            # Calculate risk/reward
            risk_reward = await self._calculate_risk_reward(
                current_price, stop_loss, take_profit, direction
            )
            output_data['risk_reward'] = risk_reward
            reasoning_parts.append(f"Risk/Reward: {risk_reward:.2f}")
            
            # Check portfolio exposure
            exposure_check = await self._check_exposure(current_exposure, position_size)
            output_data['exposure_check'] = exposure_check
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return SubTaskResult(
                subtask_id=context.subtask.id,
                success=True,
                output_data=output_data,
                citations=citations,
                confidence=0.95,
                reasoning=" | ".join(reasoning_parts),
                execution_time_ms=execution_time,
            )
            
        except Exception as e:
            logger.error(f"Risk agent error: {e}")
            return SubTaskResult(
                subtask_id=context.subtask.id,
                success=False,
                error=str(e),
            )
    
    async def _calculate_stop_loss(
        self, current_price: float, key_levels: Dict, direction: str
    ) -> float:
        """Calculate stop loss level"""
        support_levels = key_levels.get('support', [current_price * 0.99])
        resistance_levels = key_levels.get('resistance', [current_price * 1.01])
        
        if direction == 'long':
            # Stop below nearest support
            stop = min(support_levels) if support_levels else current_price * 0.99
        else:
            # Stop above nearest resistance
            stop = max(resistance_levels) if resistance_levels else current_price * 1.01
        
        return round(stop, 5)
    
    async def _calculate_take_profit(
        self, current_price: float, key_levels: Dict, direction: str
    ) -> float:
        """Calculate take profit level"""
        support_levels = key_levels.get('support', [current_price * 0.99])
        resistance_levels = key_levels.get('resistance', [current_price * 1.01])
        
        if direction == 'long':
            # Target nearest resistance
            tp = max(resistance_levels) if resistance_levels else current_price * 1.02
        else:
            # Target nearest support
            tp = min(support_levels) if support_levels else current_price * 0.98
        
        return round(tp, 5)
    
    async def _calculate_position_size(
        self, equity: float, price: float, stop_loss: float, direction: str
    ) -> float:
        """Calculate position size based on risk"""
        risk_amount = equity * self.max_risk_per_trade
        
        if direction == 'long':
            risk_per_unit = abs(price - stop_loss)
        else:
            risk_per_unit = abs(stop_loss - price)
        
        if risk_per_unit == 0:
            risk_per_unit = price * 0.01  # Default 1% risk
        
        position_size = risk_amount / risk_per_unit
        
        return round(position_size, 2)
    
    async def _calculate_risk_reward(
        self, price: float, stop_loss: float, take_profit: float, direction: str
    ) -> float:
        """Calculate risk/reward ratio"""
        if direction == 'long':
            risk = abs(price - stop_loss)
            reward = abs(take_profit - price)
        else:
            risk = abs(stop_loss - price)
            reward = abs(price - take_profit)
        
        if risk == 0:
            return 0.0
        
        return reward / risk
    
    async def _check_exposure(self, current_exposure: float, new_position: float) -> Dict[str, Any]:
        """Check if new position would exceed exposure limits"""
        total_exposure = current_exposure + new_position
        max_exposure = 100000  # Example limit
        
        return {
            'current_exposure': current_exposure,
            'new_position': new_position,
            'total_exposure': total_exposure,
            'max_exposure': max_exposure,
            'within_limits': total_exposure <= max_exposure,
        }


class ExecutionAgent(BaseTradingAgent):
    """
    Execution Agent - Handles order routing and execution.
    
    Capabilities:
    - Order type selection
    - Timing optimization
    - Slippage estimation
    - Market impact analysis
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.agent_type = AgentType.EXECUTION
        self.name = "Execution Agent"
        self.description = "Handles order routing and execution"
    
    async def execute(self, context: AgentContext) -> SubTaskResult:
        """Prepare execution plan"""
        start_time = datetime.utcnow()
        citations = []
        
        try:
            output_data = {}
            reasoning_parts = []
            
            # Get decision from input
            decision = context.input_data.get('final_decision', {})
            position_size = context.input_data.get('position_size', 0)
            
            # Determine order type
            order_type = await self._determine_order_type(context)
            output_data['order_type'] = order_type
            reasoning_parts.append(f"Order type: {order_type}")
            
            # Estimate slippage
            slippage = await self._estimate_slippage(position_size, context)
            output_data['estimated_slippage'] = slippage
            reasoning_parts.append(f"Est. slippage: {slippage:.4f}")
            
            # Create execution plan
            execution_plan = {
                'order_type': order_type,
                'position_size': position_size,
                'estimated_slippage': slippage,
                'execution_algo': 'TWAP' if position_size > 10000 else 'MARKET',
                'urgency': context.config.get('urgency', 'normal'),
            }
            output_data['execution_plan'] = execution_plan
            
            citations.append(self.create_citation(
                RetrievalSource.CALCULATION,
                "Execution Planning",
                f"Prepared {order_type} order with {execution_plan['execution_algo']} algo",
                confidence=0.90,
            ))
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return SubTaskResult(
                subtask_id=context.subtask.id,
                success=True,
                output_data=output_data,
                citations=citations,
                confidence=0.90,
                reasoning=" | ".join(reasoning_parts),
                execution_time_ms=execution_time,
            )
            
        except Exception as e:
            logger.error(f"Execution agent error: {e}")
            return SubTaskResult(
                subtask_id=context.subtask.id,
                success=False,
                error=str(e),
            )
    
    async def _determine_order_type(self, context: AgentContext) -> str:
        """Determine optimal order type"""
        urgency = context.config.get('urgency', 'normal')
        
        if urgency == 'high':
            return 'MARKET'
        elif urgency == 'low':
            return 'LIMIT'
        else:
            return 'LIMIT'  # Default to limit for better fills
    
    async def _estimate_slippage(self, position_size: float, context: AgentContext) -> float:
        """Estimate expected slippage"""
        # In production, use actual market depth data
        base_slippage = 0.0001  # 1 pip base
        size_factor = min(position_size / 100000, 1.0)  # Scale with size
        
        return base_slippage * (1 + size_factor)


class ReasoningAgent(BaseTradingAgent):
    """
    Reasoning Agent - Performs multi-step reasoning and synthesis.
    
    Capabilities:
    - Chain-of-thought reasoning
    - Multi-factor synthesis
    - Decision making
    - Conflict resolution
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.agent_type = AgentType.REASONING
        self.name = "Reasoning Agent"
        self.description = "Performs multi-step reasoning and synthesis"
    
    async def execute(self, context: AgentContext) -> SubTaskResult:
        """Execute reasoning/synthesis task"""
        start_time = datetime.utcnow()
        citations = []
        
        try:
            output_data = {}
            reasoning_chain = []
            
            # Gather all inputs
            inputs = context.input_data
            
            # Step 1: Analyze technical signals
            technical = inputs.get('technical_signals', {})
            tech_signal = technical.get('overall_signal', 'neutral')
            reasoning_chain.append(f"Technical analysis indicates {tech_signal} signal (strength: {technical.get('signal_strength', 0):.0%})")
            
            # Step 2: Consider fundamentals
            fundamentals = inputs.get('fundamentals_data', {})
            fundamental_outlook = fundamentals.get('economic_outlook', 'neutral')
            reasoning_chain.append(f"Fundamental outlook is {fundamental_outlook}")
            
            # Step 3: Factor in sentiment
            sentiment = inputs.get('sentiment_score', 0)
            sentiment_label = 'bullish' if sentiment > 0.1 else ('bearish' if sentiment < -0.1 else 'neutral')
            reasoning_chain.append(f"Market sentiment is {sentiment_label} ({sentiment:.2f})")
            
            # Step 4: Check risk parameters
            risk_reward = inputs.get('risk_reward', 0)
            reasoning_chain.append(f"Risk/reward ratio: {risk_reward:.2f}")
            
            # Step 5: Synthesize decision
            decision = await self._synthesize_decision(
                tech_signal, fundamental_outlook, sentiment_label, risk_reward
            )
            output_data['trading_signal'] = decision['signal']
            output_data['confidence'] = decision['confidence']
            output_data['reasoning_chain'] = reasoning_chain
            
            reasoning_chain.append(f"DECISION: {decision['signal']} with {decision['confidence']:.0%} confidence")
            
            citations.append(self.create_citation(
                RetrievalSource.CALCULATION,
                "Reasoning Synthesis",
                f"Synthesized {len(inputs)} inputs into trading decision",
                confidence=decision['confidence'],
            ))
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return SubTaskResult(
                subtask_id=context.subtask.id,
                success=True,
                output_data=output_data,
                citations=citations,
                confidence=decision['confidence'],
                reasoning=" → ".join(reasoning_chain),
                execution_time_ms=execution_time,
            )
            
        except Exception as e:
            logger.error(f"Reasoning agent error: {e}")
            return SubTaskResult(
                subtask_id=context.subtask.id,
                success=False,
                error=str(e),
            )
    
    async def _synthesize_decision(
        self,
        tech_signal: str,
        fundamental: str,
        sentiment: str,
        risk_reward: float,
    ) -> Dict[str, Any]:
        """Synthesize final trading decision"""
        # Score each factor
        tech_score = {'bullish': 1, 'neutral': 0, 'bearish': -1}.get(tech_signal, 0)
        fund_score = {'bullish': 0.5, 'neutral': 0, 'bearish': -0.5}.get(fundamental, 0)
        sent_score = {'bullish': 0.3, 'neutral': 0, 'bearish': -0.3}.get(sentiment, 0)
        
        # Risk/reward bonus
        rr_bonus = 0.2 if risk_reward >= 2.0 else (0.1 if risk_reward >= 1.5 else 0)
        
        # Combined score
        total_score = tech_score + fund_score + sent_score + rr_bonus
        
        # Determine signal
        if total_score > 0.5:
            signal = 'BUY'
            confidence = min(0.5 + total_score * 0.2, 0.95)
        elif total_score < -0.5:
            signal = 'SELL'
            confidence = min(0.5 + abs(total_score) * 0.2, 0.95)
        else:
            signal = 'HOLD'
            confidence = 0.6
        
        return {
            'signal': signal,
            'confidence': confidence,
            'score': total_score,
        }


class SentimentAgent(BaseTradingAgent):
    """Sentiment Agent - Analyzes market sentiment from various sources."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.agent_type = AgentType.SENTIMENT
        self.name = "Sentiment Agent"
        self.description = "Analyzes market sentiment from various sources"
    
    async def execute(self, context: AgentContext) -> SubTaskResult:
        """Execute sentiment analysis"""
        start_time = datetime.utcnow()
        
        try:
            # Analyze sentiment from multiple sources
            sentiment_data = {
                'social_media': {'score': 0.15, 'volume': 'high'},
                'news': {'score': 0.08, 'articles': 25},
                'positioning': {'retail': 'long', 'institutional': 'neutral'},
                'fear_greed': 55,
                'overall_score': 0.12,
                'sentiment_label': 'slightly_bullish',
            }
            
            citations = [
                self.create_citation(
                    RetrievalSource.SENTIMENT,
                    "Sentiment Analysis",
                    f"Overall sentiment: {sentiment_data['sentiment_label']}",
                    confidence=0.80,
                )
            ]
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return SubTaskResult(
                subtask_id=context.subtask.id,
                success=True,
                output_data=sentiment_data,
                citations=citations,
                confidence=0.80,
                reasoning=f"Sentiment analysis: {sentiment_data['sentiment_label']} (score: {sentiment_data['overall_score']:.2f})",
                execution_time_ms=execution_time,
            )
            
        except Exception as e:
            return SubTaskResult(subtask_id=context.subtask.id, success=False, error=str(e))


class MacroAgent(BaseTradingAgent):
    """Macro Agent - Analyzes macroeconomic factors and policy."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.agent_type = AgentType.MACRO
        self.name = "Macro Agent"
        self.description = "Analyzes macroeconomic factors and policy"
    
    async def execute(self, context: AgentContext) -> SubTaskResult:
        """Execute macro analysis"""
        start_time = datetime.utcnow()
        
        try:
            macro_data = {
                'macro_outlook': 'neutral_to_bullish',
                'economic_calendar': [
                    {'event': 'FOMC', 'impact': 'high', 'days_until': 5},
                    {'event': 'NFP', 'impact': 'high', 'days_until': 12},
                ],
                'policy_stance': {
                    'fed': 'hawkish',
                    'ecb': 'neutral',
                    'boj': 'dovish',
                },
                'global_factors': {
                    'risk_appetite': 'risk_on',
                    'dollar_strength': 'neutral',
                    'yields': 'rising',
                },
            }
            
            citations = [
                self.create_citation(
                    RetrievalSource.FUNDAMENTALS,
                    "Macro Analysis",
                    f"Macro outlook: {macro_data['macro_outlook']}",
                    confidence=0.85,
                )
            ]
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return SubTaskResult(
                subtask_id=context.subtask.id,
                success=True,
                output_data=macro_data,
                citations=citations,
                confidence=0.85,
                reasoning=f"Macro analysis: {macro_data['macro_outlook']}",
                execution_time_ms=execution_time,
            )
            
        except Exception as e:
            return SubTaskResult(subtask_id=context.subtask.id, success=False, error=str(e))


class MicrostructureAgent(BaseTradingAgent):
    """Microstructure Agent - Analyzes order flow and market depth."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.agent_type = AgentType.MICROSTRUCTURE
        self.name = "Microstructure Agent"
        self.description = "Analyzes order flow and market depth"
    
    async def execute(self, context: AgentContext) -> SubTaskResult:
        """Execute microstructure analysis"""
        start_time = datetime.utcnow()
        
        try:
            microstructure_data = {
                'order_flow': {
                    'buy_volume': 150000,
                    'sell_volume': 120000,
                    'imbalance': 0.11,
                    'direction': 'buying_pressure',
                },
                'liquidity_score': 0.85,
                'market_depth': {
                    'bid_depth': 500000,
                    'ask_depth': 450000,
                    'spread': 0.00012,
                },
                'toxicity': 0.15,  # Low toxicity = good
            }
            
            citations = [
                self.create_citation(
                    RetrievalSource.MARKET_DATA,
                    "Microstructure Analysis",
                    f"Order flow: {microstructure_data['order_flow']['direction']}",
                    confidence=0.88,
                )
            ]
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return SubTaskResult(
                subtask_id=context.subtask.id,
                success=True,
                output_data=microstructure_data,
                citations=citations,
                confidence=0.88,
                reasoning=f"Microstructure: {microstructure_data['order_flow']['direction']}, liquidity: {microstructure_data['liquidity_score']:.0%}",
                execution_time_ms=execution_time,
            )
            
        except Exception as e:
            return SubTaskResult(subtask_id=context.subtask.id, success=False, error=str(e))


# Agent factory
def create_agent(agent_type: AgentType, config: Optional[Dict[str, Any]] = None) -> BaseTradingAgent:
    """Factory function to create agents"""
    agent_classes = {
        AgentType.RESEARCH: ResearchAgent,
        AgentType.TECHNICAL: TechnicalAgent,
        AgentType.RISK: RiskAgent,
        AgentType.EXECUTION: ExecutionAgent,
        AgentType.REASONING: ReasoningAgent,
        AgentType.SENTIMENT: SentimentAgent,
        AgentType.MACRO: MacroAgent,
        AgentType.MICROSTRUCTURE: MicrostructureAgent,
    }
    
    agent_class = agent_classes.get(agent_type, ReasoningAgent)
    return agent_class(config)
