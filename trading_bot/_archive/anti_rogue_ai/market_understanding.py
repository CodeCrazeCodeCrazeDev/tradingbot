"""
Market Understanding System
============================

Forces AI to UNDERSTAND markets, not just predict them.

PHILOSOPHY:
- Prediction without understanding is gambling
- AI must explain WHY markets move, not just WHERE
- Context matters more than patterns
- Understanding prevents rogue behavior

UNDERSTANDING vs PREDICTION:
❌ Prediction: "Price will go up 80% confidence"
✅ Understanding: "Price likely up because: institutional accumulation detected,
   volume profile shows support, macro environment favorable, similar to 2019 pattern"
"""

import logging
import threading
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)

try:
    import numpy as np
    import pandas as pd
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class MarketPhase(Enum):
    """Market phases requiring different understanding"""
    ACCUMULATION = "accumulation"           # Smart money buying
    MARKUP = "markup"                       # Trending up
    DISTRIBUTION = "distribution"           # Smart money selling
    MARKDOWN = "markdown"                   # Trending down
    RANGING = "ranging"                     # Sideways consolidation
    VOLATILE = "volatile"                   # High uncertainty
    CRISIS = "crisis"                       # Market stress
    RECOVERY = "recovery"                   # Post-crisis recovery


class UnderstandingLevel(Enum):
    """How well AI understands current market"""
    NONE = 0              # No understanding - DO NOT TRADE
    MINIMAL = 1           # Basic pattern recognition only
    PARTIAL = 2           # Some context understood
    GOOD = 3              # Solid understanding of dynamics
    EXCELLENT = 4         # Deep multi-factor understanding
    EXPERT = 5            # Comprehensive market mastery


class ContextType(Enum):
    """Types of market context"""
    TECHNICAL = "technical"               # Price action, patterns
    FUNDAMENTAL = "fundamental"           # Economic data, earnings
    SENTIMENT = "sentiment"               # Market psychology
    MICROSTRUCTURE = "microstructure"     # Order flow, liquidity
    MACRO = "macro"                       # Global economics, policy
    INTERMARKET = "intermarket"           # Cross-asset relationships
    SEASONAL = "seasonal"                 # Time-based patterns
    REGIME = "regime"                     # Market regime


@dataclass
class MarketContext:
    """Complete market context understanding"""
    symbol: str
    timestamp: datetime
    phase: MarketPhase
    understanding_level: UnderstandingLevel
    
    # Context components
    technical_context: Dict[str, Any] = field(default_factory=dict)
    fundamental_context: Dict[str, Any] = field(default_factory=dict)
    sentiment_context: Dict[str, Any] = field(default_factory=dict)
    microstructure_context: Dict[str, Any] = field(default_factory=dict)
    macro_context: Dict[str, Any] = field(default_factory=dict)
    
    # Understanding quality
    confidence: float = 0.0
    reasoning: str = ""
    key_factors: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    similar_historical_periods: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'phase': self.phase.value,
            'understanding_level': self.understanding_level.value,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'key_factors': self.key_factors,
            'risks': self.risks,
            'technical': self.technical_context,
            'fundamental': self.fundamental_context,
            'sentiment': self.sentiment_context
        }


class MarketUnderstanding:
    """
    Enforces market understanding before trading.
    
    CORE PRINCIPLE:
    AI cannot trade unless it demonstrates understanding of:
    1. WHY price is moving
    2. WHAT phase market is in
    3. WHO is driving the move (retail/institutional)
    4. WHEN similar patterns occurred
    5. WHERE key levels are and WHY they matter
    6. HOW current context differs from predictions
    """
    
    # Minimum understanding required to trade
    MIN_UNDERSTANDING_TO_TRADE = UnderstandingLevel.GOOD
    
    # Required context types for trading
    REQUIRED_CONTEXT_TYPES = [
        ContextType.TECHNICAL,
        ContextType.SENTIMENT,
        ContextType.MICROSTRUCTURE
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.lock = threading.RLock()
        
        # Understanding history
        self.understanding_history: deque = deque(maxlen=1000)
        
        # Current market contexts
        self.current_contexts: Dict[str, MarketContext] = {}
        
        logger.info("MarketUnderstanding initialized")
    
    def analyze_market_context(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        additional_data: Optional[Dict] = None
    ) -> MarketContext:
        """
        Analyze and understand market context.
        
        Args:
            symbol: Trading symbol
            market_data: OHLCV and technical data
            additional_data: Sentiment, news, order flow, etc.
            
        Returns:
            MarketContext with understanding
        """
        with self.lock:
            additional_data = additional_data or {}
            
            # Analyze each context type
            technical = self._analyze_technical_context(market_data)
            fundamental = self._analyze_fundamental_context(symbol, additional_data)
            sentiment = self._analyze_sentiment_context(additional_data)
            microstructure = self._analyze_microstructure_context(market_data, additional_data)
            macro = self._analyze_macro_context(additional_data)
            
            # Determine market phase
            phase = self._determine_market_phase(technical, sentiment, microstructure)
            
            # Calculate understanding level
            understanding_level = self._calculate_understanding_level(
                technical, fundamental, sentiment, microstructure, macro
            )
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                phase, technical, fundamental, sentiment, microstructure, macro
            )
            
            # Identify key factors
            key_factors = self._identify_key_factors(
                technical, fundamental, sentiment, microstructure, macro
            )
            
            # Identify risks
            risks = self._identify_risks(
                phase, technical, sentiment, microstructure
            )
            
            # Find similar historical periods
            similar_periods = self._find_similar_periods(
                phase, technical, sentiment
            )
            
            # Create context
            context = MarketContext(
                symbol=symbol,
                timestamp=datetime.now(),
                phase=phase,
                understanding_level=understanding_level,
                technical_context=technical,
                fundamental_context=fundamental,
                sentiment_context=sentiment,
                microstructure_context=microstructure,
                macro_context=macro,
                confidence=self._calculate_confidence(understanding_level),
                reasoning=reasoning,
                key_factors=key_factors,
                risks=risks,
                similar_historical_periods=similar_periods
            )
            
            # Store context
            self.current_contexts[symbol] = context
            self.understanding_history.append(context)
            
            return context
    
    def _analyze_technical_context(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical context."""
        context = {
            'trend': 'unknown',
            'trend_strength': 0.0,
            'support_levels': [],
            'resistance_levels': [],
            'volume_profile': 'unknown',
            'volatility': 'unknown',
            'momentum': 'unknown'
        }
        
        if 'prices' in market_data and NUMPY_AVAILABLE:
            prices = np.array(market_data['prices'])
            
            # Simple trend detection
            if len(prices) >= 20:
                sma_20 = np.mean(prices[-20:])
                current_price = prices[-1]
                
                if current_price > sma_20 * 1.02:
                    context['trend'] = 'uptrend'
                    context['trend_strength'] = min((current_price / sma_20 - 1) * 10, 1.0)
                elif current_price < sma_20 * 0.98:
                    context['trend'] = 'downtrend'
                    context['trend_strength'] = min((1 - current_price / sma_20) * 10, 1.0)
                else:
                    context['trend'] = 'ranging'
                    context['trend_strength'] = 0.3
            
            # Volatility
            if len(prices) >= 20:
                returns = np.diff(prices) / prices[:-1]
                volatility = np.std(returns) * np.sqrt(252)
                
                if volatility > 0.3:
                    context['volatility'] = 'high'
                elif volatility > 0.15:
                    context['volatility'] = 'medium'
                else:
                    context['volatility'] = 'low'
        
        return context
    
    def _analyze_fundamental_context(self, symbol: str, data: Dict) -> Dict[str, Any]:
        """Analyze fundamental context."""
        return {
            'economic_cycle': data.get('economic_cycle', 'unknown'),
            'sector_health': data.get('sector_health', 'unknown'),
            'earnings_trend': data.get('earnings_trend', 'unknown'),
            'valuation': data.get('valuation', 'unknown')
        }
    
    def _analyze_sentiment_context(self, data: Dict) -> Dict[str, Any]:
        """Analyze sentiment context."""
        return {
            'retail_sentiment': data.get('retail_sentiment', 'neutral'),
            'institutional_sentiment': data.get('institutional_sentiment', 'neutral'),
            'fear_greed_index': data.get('fear_greed', 50),
            'social_media_buzz': data.get('social_buzz', 'low'),
            'news_sentiment': data.get('news_sentiment', 'neutral')
        }
    
    def _analyze_microstructure_context(self, market_data: Dict, data: Dict) -> Dict[str, Any]:
        """Analyze microstructure context."""
        return {
            'order_flow': data.get('order_flow', 'balanced'),
            'liquidity': data.get('liquidity', 'normal'),
            'bid_ask_spread': data.get('spread', 'normal'),
            'large_orders': data.get('large_orders', []),
            'institutional_activity': data.get('institutional_activity', 'normal')
        }
    
    def _analyze_macro_context(self, data: Dict) -> Dict[str, Any]:
        """Analyze macro context."""
        return {
            'interest_rates': data.get('interest_rates', 'unknown'),
            'inflation': data.get('inflation', 'unknown'),
            'currency_trends': data.get('currency_trends', 'unknown'),
            'geopolitical_risk': data.get('geopolitical_risk', 'low')
        }
    
    def _determine_market_phase(
        self,
        technical: Dict,
        sentiment: Dict,
        microstructure: Dict
    ) -> MarketPhase:
        """Determine current market phase."""
        
        # Simple phase detection logic
        trend = technical.get('trend', 'unknown')
        volatility = technical.get('volatility', 'unknown')
        order_flow = microstructure.get('order_flow', 'balanced')
        
        if volatility == 'high':
            return MarketPhase.VOLATILE
        
        if trend == 'uptrend' and order_flow == 'buying':
            return MarketPhase.MARKUP
        elif trend == 'downtrend' and order_flow == 'selling':
            return MarketPhase.MARKDOWN
        elif trend == 'ranging' and order_flow == 'buying':
            return MarketPhase.ACCUMULATION
        elif trend == 'ranging' and order_flow == 'selling':
            return MarketPhase.DISTRIBUTION
        else:
            return MarketPhase.RANGING
    
    def _calculate_understanding_level(
        self,
        technical: Dict,
        fundamental: Dict,
        sentiment: Dict,
        microstructure: Dict,
        macro: Dict
    ) -> UnderstandingLevel:
        """Calculate how well we understand the market."""
        
        # Count how many context types have meaningful data
        score = 0
        
        if technical.get('trend') != 'unknown':
            score += 1
        if fundamental.get('economic_cycle') != 'unknown':
            score += 1
        if sentiment.get('retail_sentiment') != 'neutral':
            score += 1
        if microstructure.get('order_flow') != 'balanced':
            score += 1
        if macro.get('interest_rates') != 'unknown':
            score += 1
        
        # Map score to understanding level
        if score >= 5:
            return UnderstandingLevel.EXPERT
        elif score >= 4:
            return UnderstandingLevel.EXCELLENT
        elif score >= 3:
            return UnderstandingLevel.GOOD
        elif score >= 2:
            return UnderstandingLevel.PARTIAL
        elif score >= 1:
            return UnderstandingLevel.MINIMAL
        else:
            return UnderstandingLevel.NONE
    
    def _generate_reasoning(
        self,
        phase: MarketPhase,
        technical: Dict,
        fundamental: Dict,
        sentiment: Dict,
        microstructure: Dict,
        macro: Dict
    ) -> str:
        """Generate human-readable reasoning about market state."""
        
        parts = [f"Market is in {phase.value} phase."]
        
        # Technical reasoning
        if technical.get('trend') != 'unknown':
            parts.append(f"Technical: {technical['trend']} with {technical.get('volatility', 'unknown')} volatility.")
        
        # Sentiment reasoning
        if sentiment.get('retail_sentiment') != 'neutral':
            parts.append(f"Sentiment: Retail {sentiment['retail_sentiment']}, institutional {sentiment.get('institutional_sentiment', 'neutral')}.")
        
        # Microstructure reasoning
        if microstructure.get('order_flow') != 'balanced':
            parts.append(f"Order flow: {microstructure['order_flow']} with {microstructure.get('liquidity', 'normal')} liquidity.")
        
        return " ".join(parts)
    
    def _identify_key_factors(
        self,
        technical: Dict,
        fundamental: Dict,
        sentiment: Dict,
        microstructure: Dict,
        macro: Dict
    ) -> List[str]:
        """Identify key factors driving the market."""
        factors = []
        
        if technical.get('trend_strength', 0) > 0.7:
            factors.append(f"Strong {technical['trend']}")
        
        if sentiment.get('fear_greed_index', 50) > 75:
            factors.append("Extreme greed in market")
        elif sentiment.get('fear_greed_index', 50) < 25:
            factors.append("Extreme fear in market")
        
        if microstructure.get('institutional_activity') == 'high':
            factors.append("High institutional activity")
        
        return factors
    
    def _identify_risks(
        self,
        phase: MarketPhase,
        technical: Dict,
        sentiment: Dict,
        microstructure: Dict
    ) -> List[str]:
        """Identify current market risks."""
        risks = []
        
        if phase == MarketPhase.VOLATILE:
            risks.append("High volatility increases execution risk")
        
        if technical.get('volatility') == 'high':
            risks.append("Elevated volatility may cause stop-outs")
        
        if microstructure.get('liquidity') == 'low':
            risks.append("Low liquidity may cause slippage")
        
        if sentiment.get('fear_greed_index', 50) > 80:
            risks.append("Extreme greed suggests potential reversal")
        
        return risks
    
    def _find_similar_periods(
        self,
        phase: MarketPhase,
        technical: Dict,
        sentiment: Dict
    ) -> List[str]:
        """Find similar historical periods."""
        # Placeholder - would use historical database
        return [
            f"Similar to {phase.value} phase in recent history"
        ]
    
    def _calculate_confidence(self, understanding_level: UnderstandingLevel) -> float:
        """Calculate confidence based on understanding level."""
        confidence_map = {
            UnderstandingLevel.NONE: 0.0,
            UnderstandingLevel.MINIMAL: 0.2,
            UnderstandingLevel.PARTIAL: 0.4,
            UnderstandingLevel.GOOD: 0.6,
            UnderstandingLevel.EXCELLENT: 0.8,
            UnderstandingLevel.EXPERT: 0.95
        }
        return confidence_map.get(understanding_level, 0.0)
    
    def can_trade(self, symbol: str) -> Tuple[bool, str]:
        """
        Check if AI understands market well enough to trade.
        
        Returns:
            (can_trade, reason)
        """
        with self.lock:
            if symbol not in self.current_contexts:
                return False, "No market context available"
            
            context = self.current_contexts[symbol]
            
            # Check understanding level
            if context.understanding_level.value < self.MIN_UNDERSTANDING_TO_TRADE.value:
                return False, f"Understanding level {context.understanding_level.name} below minimum {self.MIN_UNDERSTANDING_TO_TRADE.name}"
            
            # Check if we have reasoning
            if not context.reasoning:
                return False, "No reasoning provided for market state"
            
            # Check if we identified key factors
            if not context.key_factors:
                return False, "No key factors identified"
            
            return True, "Market understanding sufficient for trading"
    
    def get_context(self, symbol: str) -> Optional[MarketContext]:
        """Get current market context for symbol."""
        with self.lock:
            return self.current_contexts.get(symbol)
    
    def get_status(self) -> Dict[str, Any]:
        """Get understanding system status."""
        with self.lock:
            return {
                'tracked_symbols': list(self.current_contexts.keys()),
                'total_contexts': len(self.understanding_history),
                'current_contexts': {
                    symbol: {
                        'phase': ctx.phase.value,
                        'understanding': ctx.understanding_level.name,
                        'confidence': ctx.confidence
                    }
                    for symbol, ctx in self.current_contexts.items()
                }
            }
