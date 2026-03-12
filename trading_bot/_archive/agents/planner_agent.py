"""
Planner Agent - Analyzes market and proposes trades

Part of AgentFlow multi-agent architecture.
Responsibilities:
- Analyze market data, news, sentiment, forecasts
- Propose trade ideas with reasoning
- Calculate expected returns and risks
- Provide confidence scores
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import numpy

logger = logging.getLogger(__name__)


@dataclass
class TradeProposal:
    """Trade proposal from planner agent"""
    proposal_id: str
    timestamp: datetime
    symbol: str
    action: str  # 'long', 'short', 'hold'
    lots: float
    reasoning: str
    confidence: float  # 0-1
    expected_return: float  # Expected profit in USD
    expected_risk: float  # Expected loss in USD
    stop_loss_pips: float
    take_profit_pips: float
    
    # Supporting evidence
    technical_score: float  # 0-1
    fundamental_score: float  # 0-1
    sentiment_score: float  # 0-1
    forecast_score: float  # 0-1
    
    # Market context
    market_regime: str
    volatility_regime: str
    trend_strength: float
    
    # Risk metrics
    risk_reward_ratio: float
    win_probability: float
    kelly_fraction: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @property
    def expected_value(self) -> float:
        """Expected value of trade"""
        return self.win_probability * self.expected_return - (1 - self.win_probability) * self.expected_risk


class PlannerAgent:
    """
    Planner Agent - Proposes trades based on comprehensive analysis
    
    Inputs:
    - Market data (price, volume, indicators)
    - TFT forecasts (probabilistic predictions)
    - News sentiment
    - Market regime
    
    Outputs:
    - Trade proposals with detailed reasoning
    """
    
    def __init__(
        self,
        min_confidence: float = 0.6,
        min_risk_reward: float = 2.0,
        min_win_probability: float = 0.55,
        max_proposals_per_hour: int = 5
    ):
        """
        Args:
            min_confidence: Minimum confidence to propose trade
            min_risk_reward: Minimum risk:reward ratio
            min_win_probability: Minimum win probability
            max_proposals_per_hour: Rate limit on proposals
        """
        self.min_confidence = min_confidence
        self.min_risk_reward = min_risk_reward
        self.min_win_probability = min_win_probability
        self.max_proposals_per_hour = max_proposals_per_hour
        
        self.proposal_history: List[TradeProposal] = []
        self.proposal_count_last_hour = 0
        self.last_hour_reset = datetime.now()
    
    def analyze_market(self, market_data: Dict) -> Dict[str, float]:
        """
        Analyze market conditions
        
        Args:
            market_data: Dictionary with price, volume, indicators
            
        Returns:
            Analysis scores
        """
        # Technical analysis score
        technical_score = self._analyze_technical(market_data)
        
        # Fundamental analysis score (if available)
        fundamental_score = self._analyze_fundamental(market_data)
        
        # Sentiment analysis score
        sentiment_score = self._analyze_sentiment(market_data)
        
        # Forecast analysis score
        forecast_score = self._analyze_forecast(market_data)
        
        # Market regime
        market_regime = self._detect_market_regime(market_data)
        volatility_regime = self._detect_volatility_regime(market_data)
        
        # Trend strength
        trend_strength = self._calculate_trend_strength(market_data)
        
        return {
            'technical_score': technical_score,
            'fundamental_score': fundamental_score,
            'sentiment_score': sentiment_score,
            'forecast_score': forecast_score,
            'market_regime': market_regime,
            'volatility_regime': volatility_regime,
            'trend_strength': trend_strength,
        }
    
    def _analyze_technical(self, data: Dict) -> float:
        """Analyze technical indicators"""
        score = 0.5  # Neutral
        
        # RSI
        rsi = data.get('rsi', 50)
        if rsi < 30:
            score += 0.2  # Oversold → bullish
        elif rsi > 70:
            score -= 0.2  # Overbought → bearish
        
        # MACD
        macd = data.get('macd', 0)
        macd_signal = data.get('macd_signal', 0)
        if macd > macd_signal:
            score += 0.15  # Bullish crossover
        else:
            score -= 0.15  # Bearish crossover
        
        # Moving average alignment
        price = data.get('price', 0)
        ma_20 = data.get('ma_20', price)
        ma_50 = data.get('ma_50', price)
        
        if price > ma_20 > ma_50:
            score += 0.15  # Bullish alignment
        elif price < ma_20 < ma_50:
            score -= 0.15  # Bearish alignment
        
        return np.clip(score, 0, 1)
    
    def _analyze_fundamental(self, data: Dict) -> float:
        """Analyze fundamental factors"""
        # Placeholder - in production, analyze economic data
        return data.get('fundamental_score', 0.5)
    
    def _analyze_sentiment(self, data: Dict) -> float:
        """Analyze news and social sentiment"""
        sentiment = data.get('news_sentiment', 0.5)
        return np.clip(sentiment, 0, 1)
    
    def _analyze_forecast(self, data: Dict) -> float:
        """Analyze TFT forecast"""
        forecast = data.get('forecast', {})
        
        if not forecast:
            return 0.5
        
        median_pred = forecast.get('median_prediction', 0)
        confidence = forecast.get('confidence', 0.5)
        
        # Score based on prediction magnitude and confidence
        magnitude_score = min(abs(median_pred) * 100, 1.0)  # Normalize
        
        score = 0.5 + (np.sign(median_pred) * magnitude_score * confidence) / 2
        
        return np.clip(score, 0, 1)
    
    def _detect_market_regime(self, data: Dict) -> str:
        """Detect market regime"""
        trend_strength = self._calculate_trend_strength(data)
        volatility = data.get('volatility', 0.01)
        
        if trend_strength > 0.7:
            return 'trending_bullish' if data.get('price', 0) > data.get('ma_50', 0) else 'trending_bearish'
        elif volatility > 0.02:
            return 'volatile_ranging'
        else:
            return 'calm_ranging'
    
    def _detect_volatility_regime(self, data: Dict) -> str:
        """Detect volatility regime"""
        volatility = data.get('volatility', 0.01)
        atr = data.get('atr', 0.001)
        
        if atr > 0.002:
            return 'high'
        elif atr < 0.0005:
            return 'low'
        else:
            return 'normal'
    
    def _calculate_trend_strength(self, data: Dict) -> float:
        """Calculate trend strength (0-1)"""
        price = data.get('price', 0)
        ma_20 = data.get('ma_20', price)
        ma_50 = data.get('ma_50', price)
        
        # Distance from moving averages
        dist_20 = abs(price - ma_20) / price if price > 0 else 0
        dist_50 = abs(price - ma_50) / price if price > 0 else 0
        
        # Alignment score
        if (price > ma_20 > ma_50) or (price < ma_20 < ma_50):
            alignment = 1.0
        else:
            alignment = 0.0
        
        strength = (dist_20 + dist_50) * 50 * alignment  # Normalize
        
        return np.clip(strength, 0, 1)
    
    def propose_trade(
        self,
        symbol: str,
        market_data: Dict,
        current_equity: float = 10000.0
    ) -> Optional[TradeProposal]:
        """
        Propose a trade based on analysis
        
        Args:
            symbol: Trading symbol
            market_data: Market data and indicators
            current_equity: Current account equity
            
        Returns:
            TradeProposal or None if no trade warranted
        """
        # Rate limiting
        self._check_rate_limit()
        
        # Analyze market
        analysis = self.analyze_market(market_data)
        
        # Calculate overall confidence
        confidence = np.mean([
            analysis['technical_score'],
            analysis['fundamental_score'],
            analysis['sentiment_score'],
            analysis['forecast_score']
        ])
        
        # Determine action
        if confidence > 0.6:
            action = 'long'
        elif confidence < 0.4:
            action = 'short'
        else:
            action = 'hold'
        
        # Don't propose if holding
        if action == 'hold':
            logger.debug(f"{symbol}: No trade - confidence {confidence:.2f} is neutral")
            return None
        
        # Don't propose if confidence too low
        if confidence < self.min_confidence and confidence > (1 - self.min_confidence):
            logger.debug(f"{symbol}: No trade - confidence {confidence:.2f} below threshold")
            return None
        
        # Calculate position size (basic Kelly criterion)
        win_prob = confidence if action == 'long' else (1 - confidence)
        kelly_fraction = self._calculate_kelly(win_prob, self.min_risk_reward)
        
        if kelly_fraction <= 0:
            logger.debug(f"{symbol}: No trade - negative Kelly fraction")
            return None
        
        # Position size (fractional Kelly for safety)
        lots = (current_equity * kelly_fraction * 0.25) / 10000  # 25% Kelly, $10k per lot
        lots = np.clip(lots, 0.01, 1.0)
        
        # Calculate stop loss and take profit
        atr = market_data.get('atr', 0.001)
        stop_loss_pips = atr * 10000 * 2.0  # 2x ATR
        take_profit_pips = stop_loss_pips * self.min_risk_reward
        
        # Expected return and risk
        expected_risk = lots * stop_loss_pips * 10  # $10 per pip per lot
        expected_return = lots * take_profit_pips * 10
        
        # Build reasoning
        reasoning = self._build_reasoning(analysis, market_data, action)
        
        # Create proposal
        proposal = TradeProposal(
            proposal_id=f"{symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            timestamp=datetime.now(),
            symbol=symbol,
            action=action,
            lots=lots,
            reasoning=reasoning,
            confidence=confidence,
            expected_return=expected_return,
            expected_risk=expected_risk,
            stop_loss_pips=stop_loss_pips,
            take_profit_pips=take_profit_pips,
            technical_score=analysis['technical_score'],
            fundamental_score=analysis['fundamental_score'],
            sentiment_score=analysis['sentiment_score'],
            forecast_score=analysis['forecast_score'],
            market_regime=analysis['market_regime'],
            volatility_regime=analysis['volatility_regime'],
            trend_strength=analysis['trend_strength'],
            risk_reward_ratio=self.min_risk_reward,
            win_probability=win_prob,
            kelly_fraction=kelly_fraction
        )
        
        # Store proposal
        self.proposal_history.append(proposal)
        self.proposal_count_last_hour += 1
        
        logger.info(
            f"Proposed {action} {symbol}: {lots:.2f} lots, "
            f"confidence {confidence:.2f}, EV ${proposal.expected_value:.2f}"
        )
        
        return proposal
    
    def _calculate_kelly(self, win_prob: float, risk_reward: float) -> float:
        """Calculate Kelly criterion fraction"""
        if win_prob <= 0 or win_prob >= 1:
            return 0.0
        
        # Kelly formula: f = (p*b - q) / b
        # where p = win prob, q = 1-p, b = win/loss ratio
        b = risk_reward
        p = win_prob
        q = 1 - p
        
        kelly = (p * b - q) / b
        
        return max(0, kelly)
    
    def _build_reasoning(self, analysis: Dict, data: Dict, action: str) -> str:
        """Build human-readable reasoning"""
        reasons = []
        
        # Technical
        if analysis['technical_score'] > 0.6:
            reasons.append(f"Strong technical setup (score: {analysis['technical_score']:.2f})")
        elif analysis['technical_score'] < 0.4:
            reasons.append(f"Weak technical setup (score: {analysis['technical_score']:.2f})")
        
        # Forecast
        if 'forecast' in data:
            forecast = data['forecast']
            median = forecast.get('median_prediction', 0)
            reasons.append(f"TFT forecast: {median*100:+.2f}% (conf: {forecast.get('confidence', 0):.2f})")
        
        # Sentiment
        if analysis['sentiment_score'] > 0.6:
            reasons.append("Positive sentiment")
        elif analysis['sentiment_score'] < 0.4:
            reasons.append("Negative sentiment")
        
        # Market regime
        reasons.append(f"Market: {analysis['market_regime']}, Vol: {analysis['volatility_regime']}")
        
        # Trend
        if analysis['trend_strength'] > 0.7:
            reasons.append(f"Strong trend (strength: {analysis['trend_strength']:.2f})")
        
        return "; ".join(reasons)
    
    def _check_rate_limit(self):
        """Check and reset rate limit"""
        now = datetime.now()
        if (now - self.last_hour_reset).total_seconds() > 3600:
            self.proposal_count_last_hour = 0
            self.last_hour_reset = now
        
        if self.proposal_count_last_hour >= self.max_proposals_per_hour:
            raise ValueError(f"Rate limit exceeded: {self.max_proposals_per_hour} proposals/hour")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create planner
    planner = PlannerAgent(
        min_confidence=0.6,
        min_risk_reward=2.0,
        min_win_probability=0.55
    )
    
    # Example market data
    market_data = {
        'price': 1.0850,
        'rsi': 45,
        'macd': 0.0003,
        'macd_signal': 0.0001,
        'ma_20': 1.0840,
        'ma_50': 1.0820,
        'atr': 0.0008,
        'volatility': 0.012,
        'news_sentiment': 0.65,
        'forecast': {
            'median_prediction': 0.0015,
            'lower_bound': 0.0010,
            'upper_bound': 0.0020,
            'confidence': 0.80
        }
    }
    
    # Propose trade
    proposal = planner.propose_trade('EURUSD', market_data, current_equity=10000)
    
    if proposal:
        print("\n" + "="*60)
        logger.info("TRADE PROPOSAL")
        print("="*60)
        logger.info(f"Symbol: {proposal.symbol}")
        logger.info(f"Action: {proposal.action.upper()}")
        logger.info(f"Size: {proposal.lots:.2f} lots")
        logger.info(f"Confidence: {proposal.confidence:.2%}")
        logger.info(f"Expected Return: ${proposal.expected_return:.2f}")
        logger.info(f"Expected Risk: ${proposal.expected_risk:.2f}")
        logger.info(f"Risk:Reward: 1:{proposal.risk_reward_ratio:.1f}")
        logger.info(f"Win Probability: {proposal.win_probability:.2%}")
        logger.info(f"Expected Value: ${proposal.expected_value:.2f}")
        logger.info(f"\nReasoning: {proposal.reasoning}")
        print("="*60)
