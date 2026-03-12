"""
Decision Layer Integration Bridge

Connects the 100-concept Decision Layer with the main trading system,
providing real-time data integration, persistence, and execution.

Author: AlphaAlgo Integration Team
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from .core_types import DecisionContext, DecisionAction, AggregatedDecision
from .innovative_decision_engine import InnovativeDecisionEngine

logger = logging.getLogger(__name__)


@dataclass
class TradingSignal:
    """Unified trading signal from decision layer"""
    symbol: str
    action: DecisionAction
    confidence: float
    position_size: float
    reasoning: str
    timestamp: datetime
    metadata: Dict[str, Any]


class DecisionLayerBridge:
    """
    Bridge between Decision Layer and Trading System.
    
    Responsibilities:
    - Convert market data to DecisionContext
    - Execute decision engine
    - Convert decisions to trading signals
    - Track performance
    - Persist decisions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize decision engine
        self.engine = InnovativeDecisionEngine(config)
        
        # Performance tracking
        self.decisions_made = 0
        self.successful_trades = 0
        self.failed_trades = 0
        
        # Configuration
        self.min_confidence = self.config.get('min_confidence', 0.6)
        self.min_consensus = self.config.get('min_consensus', 0.5)
        self.max_position_size = self.config.get('max_position_size', 1.0)
        
        logger.info("DecisionLayerBridge initialized")
    
    async def analyze_and_decide(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        portfolio_state: Dict[str, Any]
    ) -> Optional[TradingSignal]:
        """
        Main entry point: Analyze market and make decision.
        
        Args:
            symbol: Trading symbol
            market_data: Current market data
            portfolio_state: Current portfolio state
            
        Returns:
            TradingSignal if decision confidence high enough, else None
        """
        try:
            # Create decision context
            context = self._create_context(symbol, market_data, portfolio_state)
            
            # Get decision from engine
            decision = self.engine.decide(context)
            
            self.decisions_made += 1
            
            # Check if decision meets thresholds
            if not self._should_execute_decision(decision):
                logger.info(f"Decision for {symbol} below thresholds: "
                          f"conf={decision.final_confidence:.2f}, "
                          f"consensus={decision.consensus_level:.2f}")
                return None
            
            # Convert to trading signal
            signal = self._decision_to_signal(symbol, decision)
            
            logger.info(f"Generated signal for {symbol}: {signal.action.value} "
                       f"(conf={signal.confidence:.2f}, size={signal.position_size:.2f})")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in analyze_and_decide for {symbol}: {e}")
            return None
    
    def _create_context(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        portfolio_state: Dict[str, Any]
    ) -> DecisionContext:
        """Create DecisionContext from market data and portfolio state"""
        
        # Extract market data
        price = market_data.get('price', 0.0)
        volume = market_data.get('volume', 0.0)
        
        # Calculate technical indicators
        volatility = self._calculate_volatility(market_data)
        trend = self._calculate_trend(market_data)
        momentum = self._calculate_momentum(market_data)
        sentiment = self._calculate_sentiment(market_data)
        regime = self._detect_regime(market_data)
        
        # Extract portfolio state
        portfolio_value = portfolio_state.get('value', 100000.0)
        current_position = portfolio_state.get('position', 0.0)
        drawdown = portfolio_state.get('drawdown', 0.0)
        win_rate = portfolio_state.get('win_rate', 0.5)
        recent_trades = portfolio_state.get('recent_trades', [])
        
        # Create context
        context = DecisionContext(
            symbol=symbol,
            price=price,
            volume=volume,
            volatility=volatility,
            trend=trend,
            momentum=momentum,
            sentiment=sentiment,
            regime=regime,
            timeframe=market_data.get('timeframe', '1h'),
            portfolio_value=portfolio_value,
            current_position=current_position,
            drawdown=drawdown,
            win_rate=win_rate,
            recent_trades=recent_trades,
            market_data=market_data,
            timestamp=datetime.utcnow()
        )
        
        return context
    
    def _calculate_volatility(self, market_data: Dict[str, Any]) -> float:
        """Calculate volatility from market data"""
        # Try to get from market data
        if 'volatility' in market_data:
            return market_data['volatility']
        
        # Calculate from price history if available
        if 'price_history' in market_data:
            prices = market_data['price_history']
            if len(prices) > 1:
                import statistics
                returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                return statistics.stdev(returns) if len(returns) > 1 else 0.1
        
        # Default
        return 0.15
    
    def _calculate_trend(self, market_data: Dict[str, Any]) -> float:
        """Calculate trend (-1 to 1) from market data"""
        if 'trend' in market_data:
            return market_data['trend']
        
        # Calculate from price history
        if 'price_history' in market_data:
            prices = market_data['price_history']
            if len(prices) >= 20:
                sma_short = sum(prices[-10:]) / 10
                sma_long = sum(prices[-20:]) / 20
                return min(max((sma_short - sma_long) / sma_long, -1.0), 1.0)
        
        return 0.0
    
    def _calculate_momentum(self, market_data: Dict[str, Any]) -> float:
        """Calculate momentum (-1 to 1) from market data"""
        if 'momentum' in market_data:
            return market_data['momentum']
        
        # Calculate from price history
        if 'price_history' in market_data:
            prices = market_data['price_history']
            if len(prices) >= 10:
                momentum = (prices[-1] - prices[-10]) / prices[-10]
                return min(max(momentum * 10, -1.0), 1.0)
        
        return 0.0
    
    def _calculate_sentiment(self, market_data: Dict[str, Any]) -> float:
        """Calculate sentiment (-1 to 1) from market data"""
        if 'sentiment' in market_data:
            return market_data['sentiment']
        
        # Default neutral
        return 0.0
    
    def _detect_regime(self, market_data: Dict[str, Any]) -> str:
        """Detect market regime"""
        if 'regime' in market_data:
            return market_data['regime']
        
        # Simple regime detection
        volatility = self._calculate_volatility(market_data)
        trend = self._calculate_trend(market_data)
        
        if volatility > 0.3:
            return 'volatile'
        elif abs(trend) > 0.5:
            return 'trending'
        else:
            return 'ranging'
    
    def _should_execute_decision(self, decision: AggregatedDecision) -> bool:
        """Check if decision meets execution thresholds"""
        
        # Check confidence threshold
        if decision.final_confidence < self.min_confidence:
            return False
        
        # Check consensus threshold
        if decision.consensus_level < self.min_consensus:
            return False
        
        # Don't execute HOLD, ABSTAIN, or DEFER
        if decision.final_action in [DecisionAction.HOLD, DecisionAction.ABSTAIN, DecisionAction.DEFER]:
            return False
        
        return True
    
    def _decision_to_signal(self, symbol: str, decision: AggregatedDecision) -> TradingSignal:
        """Convert AggregatedDecision to TradingSignal"""
        
        # Calculate position size
        base_size = decision.position_size_multiplier
        confidence_adjusted = base_size * decision.final_confidence
        consensus_adjusted = confidence_adjusted * decision.consensus_level
        final_size = min(consensus_adjusted, self.max_position_size)
        
        # Create reasoning string
        reasoning = f"Decision from {len(decision.contributing_concepts)} concepts. "
        reasoning += f"Consensus: {decision.consensus_level:.0%}. "
        reasoning += f"Top reasons: {', '.join(decision.reasoning_chain[:3])}"
        
        # Create signal
        signal = TradingSignal(
            symbol=symbol,
            action=decision.risk_adjusted_action,
            confidence=decision.final_confidence,
            position_size=final_size,
            reasoning=reasoning,
            timestamp=decision.timestamp,
            metadata={
                'consensus_level': decision.consensus_level,
                'contributing_concepts': len(decision.contributing_concepts),
                'dissenting_concepts': len(decision.dissenting_concepts),
                'full_reasoning': decision.reasoning_chain,
                'original_action': decision.final_action.value,
                'risk_adjusted_action': decision.risk_adjusted_action.value,
            }
        )
        
        return signal
    
    def update_concept_performance(self, decision: AggregatedDecision, trade_successful: bool):
        """Update concept performance after trade outcome"""
        
        if trade_successful:
            self.successful_trades += 1
        else:
            self.failed_trades += 1
        
        # Update accuracy for contributing concepts
        for concept_result in decision.contributing_concepts:
            concept_id = concept_result.concept_id
            self.engine.concept_accuracy[concept_id].append(trade_successful)
        
        # Update accuracy for dissenting concepts (inverse)
        for concept_result in decision.dissenting_concepts:
            concept_id = concept_result.concept_id
            self.engine.concept_accuracy[concept_id].append(not trade_successful)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        
        total_trades = self.successful_trades + self.failed_trades
        win_rate = self.successful_trades / total_trades if total_trades > 0 else 0.0
        
        # Get concept performance
        concept_accuracies = {}
        for concept in self.engine.concepts:
            history = self.engine.concept_accuracy.get(concept.concept_id, [])
            if len(history) >= 5:
                accuracy = sum(history) / len(history)
                concept_accuracies[concept.name] = accuracy
        
        # Get top concepts
        top_concepts = sorted(
            concept_accuracies.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'decisions_made': self.decisions_made,
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'win_rate': win_rate,
            'top_concepts': dict(top_concepts),
            'total_concepts': len(self.engine.concepts),
            'enabled_concepts': sum(1 for c in self.engine.concepts if c.enabled),
        }
    
    def get_decision_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent decision history"""
        
        history = self.engine.decision_history[-limit:]
        
        return [
            {
                'timestamp': d.timestamp.isoformat(),
                'action': d.final_action.value,
                'confidence': d.final_confidence,
                'consensus': d.consensus_level,
                'contributing': len(d.contributing_concepts),
                'dissenting': len(d.dissenting_concepts),
            }
            for d in history
        ]


class ParallelDecisionBridge(DecisionLayerBridge):
    """
    Parallel execution version of DecisionLayerBridge.
    
    Runs all 100 concepts in parallel for faster execution.
    """
    
    async def analyze_and_decide(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        portfolio_state: Dict[str, Any]
    ) -> Optional[TradingSignal]:
        """Parallel version of analyze_and_decide"""
        
        try:
            # Create decision context
            context = self._create_context(symbol, market_data, portfolio_state)
            
            # Run concepts in parallel
            decision = await self._decide_parallel(context)
            
            self.decisions_made += 1
            
            # Check thresholds and convert to signal
            if not self._should_execute_decision(decision):
                return None
            
            signal = self._decision_to_signal(symbol, decision)
            
            logger.info(f"[PARALLEL] Generated signal for {symbol}: {signal.action.value}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error in parallel analyze_and_decide for {symbol}: {e}")
            return None
    
    async def _decide_parallel(self, context: DecisionContext) -> AggregatedDecision:
        """Run all concepts in parallel"""
        
        # Create tasks for all enabled concepts
        tasks = [
            self._run_concept_async(concept, context)
            for concept in self.engine.concepts
            if concept.enabled
        ]
        
        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and None results
        from .core_types import DecisionResult
        valid_results = [r for r in results if isinstance(r, DecisionResult)]
        
        # Aggregate using engine's method
        return self.engine._aggregate_decisions(valid_results, context)
    
    async def _run_concept_async(self, concept, context):
        """Run single concept asynchronously"""
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, concept.decide, context)
            return result
        except Exception as e:
            logger.debug(f"Concept {concept.name} failed: {e}")
            return None


def create_decision_bridge(
    config: Optional[Dict[str, Any]] = None,
    parallel: bool = True
) -> DecisionLayerBridge:
    """
    Factory function to create decision bridge.
    
    Args:
        config: Configuration dictionary
        parallel: Use parallel execution (recommended)
        
    Returns:
        DecisionLayerBridge instance
    """
    if parallel:
        return ParallelDecisionBridge(config)
    else:
        return DecisionLayerBridge(config)


async def quick_analyze(
    symbol: str,
    price: float,
    trend: float = 0.0,
    momentum: float = 0.0,
    volatility: float = 0.15,
    **kwargs
) -> Optional[TradingSignal]:
    """
    Quick analysis with minimal inputs.
    
    Args:
        symbol: Trading symbol
        price: Current price
        trend: Trend indicator (-1 to 1)
        momentum: Momentum indicator (-1 to 1)
        volatility: Volatility measure
        **kwargs: Additional market data
        
    Returns:
        TradingSignal or None
    """
    bridge = create_decision_bridge()
    
    market_data = {
        'price': price,
        'trend': trend,
        'momentum': momentum,
        'volatility': volatility,
        **kwargs
    }
    
    portfolio_state = {
        'value': 100000.0,
        'position': 0.0,
        'drawdown': 0.0,
        'win_rate': 0.5,
        'recent_trades': []
    }
    
    return await bridge.analyze_and_decide(symbol, market_data, portfolio_state)
