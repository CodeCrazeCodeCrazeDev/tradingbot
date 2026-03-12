"""
Elite Trader Brain - Institutional-Grade Trading Intelligence
==============================================================

Trades like an elite institutional trader:
1. Risk-first approach
2. Position sizing mastery
3. Entry/exit optimization
4. Multi-timeframe analysis
5. Psychological discipline
6. Market regime adaptation
"""

import asyncio
import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path
import numpy

logger = logging.getLogger(__name__)


class TradingStyle(Enum):
    """Trading styles"""
    SCALPING = "scalping"
    DAY_TRADING = "day_trading"
    SWING_TRADING = "swing_trading"
    POSITION_TRADING = "position_trading"
    ALGORITHMIC = "algorithmic"


class MarketRegime(Enum):
    """Market regimes"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    QUIET = "quiet"
    CRISIS = "crisis"


class TradeQuality(Enum):
    """Trade quality ratings"""
    A_PLUS = "A+"  # Perfect setup
    A = "A"  # Excellent
    B = "B"  # Good
    C = "C"  # Acceptable
    D = "D"  # Poor - avoid
    F = "F"  # Do not trade


@dataclass
class TradeDecision:
    """Elite trade decision"""
    decision_id: str
    symbol: str
    timestamp: datetime
    
    # Action
    action: str  # BUY, SELL, HOLD
    trade_quality: TradeQuality
    
    # Position details
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    position_size_pct: float
    
    # Risk metrics
    risk_amount: float
    risk_reward_ratio: float
    max_risk_pct: float
    
    # Confidence
    confidence: float
    conviction: str  # high, medium, low
    
    # Analysis
    regime: MarketRegime
    style: TradingStyle
    reasoning: str
    key_factors: List[str]
    
    # Execution
    order_type: str  # market, limit, stop
    time_in_force: str  # GTC, IOC, FOK
    
    def to_dict(self) -> Dict:
        return {
            'decision_id': self.decision_id,
            'symbol': self.symbol,
            'action': self.action,
            'quality': self.trade_quality.value,
            'entry': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'position_size': self.position_size,
            'risk_reward': self.risk_reward_ratio,
            'confidence': self.confidence
        }


@dataclass
class TradingRules:
    """Elite trading rules"""
    # Risk management
    max_risk_per_trade: float = 0.02  # 2%
    max_daily_risk: float = 0.06  # 6%
    max_portfolio_risk: float = 0.20  # 20%
    max_correlation_exposure: float = 0.30  # 30%
    
    # Position sizing
    min_risk_reward: float = 2.0
    max_position_size: float = 0.10  # 10% of portfolio
    scale_in_levels: int = 3
    
    # Entry rules
    min_confidence: float = 0.65
    min_trade_quality: TradeQuality = TradeQuality.B
    require_multi_timeframe: bool = True
    
    # Exit rules
    trailing_stop_activation: float = 0.02  # 2% profit
    trailing_stop_distance: float = 0.01  # 1%
    time_stop_hours: int = 48
    
    # Regime rules
    reduce_size_in_volatile: float = 0.5
    no_trade_in_crisis: bool = True


class EliteTraderBrain:
    """
    Elite Trader Brain
    
    Implements institutional-grade trading logic:
    - Risk-first decision making
    - Optimal position sizing
    - Multi-timeframe analysis
    - Market regime adaptation
    - Psychological discipline
    - Trade quality filtering
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Trading rules
        self.rules = TradingRules(**self.config.get('rules', {}))
        
        # Current state
        self.current_regime = MarketRegime.RANGING
        self.current_style = TradingStyle(
            self.config.get('style', 'swing_trading')
        )
        
        # Portfolio state
        self.portfolio_value = self.config.get('initial_capital', 100000)
        self.open_positions: Dict[str, Dict] = {}
        self.daily_pnl = 0.0
        self.daily_risk_used = 0.0
        
        # Performance tracking
        self.trade_history: List[TradeDecision] = []
        self.performance = {
            'total_trades': 0,
            'winning_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'win_rate': 0.0
        }
        
        # Trade quality stats
        self.quality_stats = {q.value: {'count': 0, 'wins': 0} for q in TradeQuality}
        
        # Storage
        self.storage_path = Path(self.config.get('storage_path', 'elite_brain'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Elite Trader Brain initialized - Style: {self.current_style.value}")
    
    async def make_decision(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        analysis: Dict[str, Any],
        current_price: float
    ) -> TradeDecision:
        """
        Make an elite trading decision
        
        Args:
            symbol: Trading symbol
            market_data: OHLCV data
            analysis: Analysis from other systems
            current_price: Current market price
            
        Returns:
            Elite trade decision
        """
        decision_id = f"elite_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{symbol}"
        
        logger.info(f"Elite brain analyzing {symbol}...")
        
        # Step 1: Detect market regime
        self.current_regime = self._detect_regime(market_data)
        
        # Step 2: Check if trading is allowed
        can_trade, reason = self._can_trade()
        if not can_trade:
            return self._create_hold_decision(decision_id, symbol, current_price, reason)
        
        # Step 3: Analyze trade setup
        setup = self._analyze_setup(market_data, analysis, current_price)
        
        # Step 4: Grade trade quality
        quality = self._grade_trade_quality(setup)
        
        # Step 5: Check minimum quality
        if quality.value > self.rules.min_trade_quality.value:
            return self._create_hold_decision(
                decision_id, symbol, current_price,
                f"Trade quality {quality.value} below minimum {self.rules.min_trade_quality.value}"
            )
        
        # Step 6: Determine action
        action, confidence = self._determine_action(setup, analysis)
        
        if action == 'HOLD' or confidence < self.rules.min_confidence:
            return self._create_hold_decision(
                decision_id, symbol, current_price,
                f"Confidence {confidence:.2%} below minimum {self.rules.min_confidence:.2%}"
            )
        
        # Step 7: Calculate position size
        position_size, risk_amount = self._calculate_position_size(
            current_price, setup['stop_loss'], action
        )
        
        # Step 8: Calculate risk/reward
        risk_reward = self._calculate_risk_reward(
            current_price, setup['stop_loss'], setup['take_profit'], action
        )
        
        if risk_reward < self.rules.min_risk_reward:
            return self._create_hold_decision(
                decision_id, symbol, current_price,
                f"Risk/reward {risk_reward:.2f} below minimum {self.rules.min_risk_reward}"
            )
        
        # Step 9: Create decision
        decision = TradeDecision(
            decision_id=decision_id,
            symbol=symbol,
            timestamp=datetime.now(),
            action=action,
            trade_quality=quality,
            entry_price=current_price,
            stop_loss=setup['stop_loss'],
            take_profit=setup['take_profit'],
            position_size=position_size,
            position_size_pct=position_size * current_price / self.portfolio_value,
            risk_amount=risk_amount,
            risk_reward_ratio=risk_reward,
            max_risk_pct=risk_amount / self.portfolio_value,
            confidence=confidence,
            conviction=self._get_conviction(confidence),
            regime=self.current_regime,
            style=self.current_style,
            reasoning=setup['reasoning'],
            key_factors=setup['key_factors'],
            order_type=self._determine_order_type(setup),
            time_in_force='GTC'
        )
        
        # Store decision
        self.trade_history.append(decision)
        
        logger.info(f"Elite decision: {action} {symbol} @ {current_price}, "
                   f"Quality: {quality.value}, R:R: {risk_reward:.2f}")
        
        return decision
    
    def _detect_regime(self, market_data: Dict) -> MarketRegime:
        """Detect current market regime"""
        prices = market_data.get('close', [])
        
        if len(prices) < 50:
            return MarketRegime.RANGING
        
        prices = np.array(prices)
        
        # Calculate metrics
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns[-20:]) * np.sqrt(252)
        
        # Trend detection
        sma_20 = np.mean(prices[-20:])
        sma_50 = np.mean(prices[-50:])
        trend = (sma_20 - sma_50) / sma_50
        
        # Range detection
        high_20 = np.max(prices[-20:])
        low_20 = np.min(prices[-20:])
        range_pct = (high_20 - low_20) / low_20
        
        # Classify regime
        if volatility > 0.4:
            return MarketRegime.CRISIS
        elif volatility > 0.25:
            return MarketRegime.VOLATILE
        elif trend > 0.02:
            return MarketRegime.TRENDING_UP
        elif trend < -0.02:
            return MarketRegime.TRENDING_DOWN
        elif range_pct < 0.03:
            return MarketRegime.QUIET
        else:
            return MarketRegime.RANGING
    
    def _can_trade(self) -> Tuple[bool, str]:
        """Check if trading is allowed"""
        # Check crisis mode
        if self.current_regime == MarketRegime.CRISIS and self.rules.no_trade_in_crisis:
            return False, "No trading during crisis regime"
        
        # Check daily risk limit
        if self.daily_risk_used >= self.rules.max_daily_risk * self.portfolio_value:
            return False, "Daily risk limit reached"
        
        # Check portfolio risk
        total_risk = sum(
            pos.get('risk', 0) for pos in self.open_positions.values()
        )
        if total_risk >= self.rules.max_portfolio_risk * self.portfolio_value:
            return False, "Portfolio risk limit reached"
        
        return True, "OK"
    
    def _analyze_setup(
        self,
        market_data: Dict,
        analysis: Dict,
        current_price: float
    ) -> Dict[str, Any]:
        """Analyze trade setup"""
        prices = market_data.get('close', [current_price])
        highs = market_data.get('high', prices)
        lows = market_data.get('low', prices)
        
        # Calculate ATR for stops
        if len(prices) > 14:
            true_ranges = []
            for i in range(1, min(15, len(prices))):
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - prices[i-1]),
                    abs(lows[i] - prices[i-1])
                )
                true_ranges.append(tr)
            atr = np.mean(true_ranges)
        else:
            atr = current_price * 0.02
        
        # Determine bias from analysis
        bias = analysis.get('overall_bias', 'neutral')
        confidence = analysis.get('overall_confidence', 0.5)
        
        # Calculate levels
        if bias == 'bullish':
            stop_loss = current_price - atr * 2
            take_profit = current_price + atr * 4
        elif bias == 'bearish':
            stop_loss = current_price + atr * 2
            take_profit = current_price - atr * 4
        else:
            stop_loss = current_price - atr * 1.5
            take_profit = current_price + atr * 1.5
        
        # Key factors
        key_factors = []
        if analysis.get('alignment_score', 0) > 0.7:
            key_factors.append("Strong signal alignment")
        if self.current_regime in [MarketRegime.TRENDING_UP, MarketRegime.TRENDING_DOWN]:
            key_factors.append(f"Trending market: {self.current_regime.value}")
        if confidence > 0.7:
            key_factors.append("High confidence signals")
        
        # Reasoning
        reasoning = f"Regime: {self.current_regime.value}, Bias: {bias}, "
        reasoning += f"Confidence: {confidence:.2%}, ATR: {atr:.4f}"
        
        return {
            'bias': bias,
            'confidence': confidence,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'atr': atr,
            'key_factors': key_factors,
            'reasoning': reasoning
        }
    
    def _grade_trade_quality(self, setup: Dict) -> TradeQuality:
        """Grade trade quality"""
        score = 0
        
        # Confidence score (0-25)
        confidence = setup.get('confidence', 0)
        score += min(25, confidence * 30)
        
        # Key factors score (0-25)
        factors = len(setup.get('key_factors', []))
        score += min(25, factors * 8)
        
        # Regime score (0-25)
        regime_scores = {
            MarketRegime.TRENDING_UP: 25,
            MarketRegime.TRENDING_DOWN: 25,
            MarketRegime.RANGING: 15,
            MarketRegime.QUIET: 10,
            MarketRegime.VOLATILE: 5,
            MarketRegime.CRISIS: 0
        }
        score += regime_scores.get(self.current_regime, 10)
        
        # Risk/reward potential (0-25)
        bias = setup.get('bias', 'neutral')
        if bias != 'neutral':
            score += 20
        
        # Grade
        if score >= 90:
            return TradeQuality.A_PLUS
        elif score >= 80:
            return TradeQuality.A
        elif score >= 65:
            return TradeQuality.B
        elif score >= 50:
            return TradeQuality.C
        elif score >= 35:
            return TradeQuality.D
        else:
            return TradeQuality.F
    
    def _determine_action(
        self,
        setup: Dict,
        analysis: Dict
    ) -> Tuple[str, float]:
        """Determine trading action"""
        bias = setup.get('bias', 'neutral')
        confidence = setup.get('confidence', 0)
        
        # Adjust confidence based on regime
        if self.current_regime == MarketRegime.VOLATILE:
            confidence *= 0.8
        elif self.current_regime == MarketRegime.CRISIS:
            confidence *= 0.5
        elif self.current_regime in [MarketRegime.TRENDING_UP, MarketRegime.TRENDING_DOWN]:
            confidence *= 1.1
        
        confidence = min(0.95, confidence)
        
        if bias == 'bullish' and confidence >= self.rules.min_confidence:
            return 'BUY', confidence
        elif bias == 'bearish' and confidence >= self.rules.min_confidence:
            return 'SELL', confidence
        else:
            return 'HOLD', confidence
    
    def _calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        action: str
    ) -> Tuple[float, float]:
        """Calculate optimal position size using Kelly-inspired sizing"""
        # Risk per trade
        max_risk = self.portfolio_value * self.rules.max_risk_per_trade
        
        # Adjust for regime
        if self.current_regime == MarketRegime.VOLATILE:
            max_risk *= self.rules.reduce_size_in_volatile
        
        # Calculate stop distance
        if action == 'BUY':
            stop_distance = entry_price - stop_loss
        else:
            stop_distance = stop_loss - entry_price
        
        stop_distance = abs(stop_distance)
        
        if stop_distance == 0:
            return 0, 0
        
        # Position size based on risk
        position_size = max_risk / stop_distance
        
        # Apply maximum position size limit
        max_position_value = self.portfolio_value * self.rules.max_position_size
        max_position_size = max_position_value / entry_price
        
        position_size = min(position_size, max_position_size)
        
        # Calculate actual risk
        risk_amount = position_size * stop_distance
        
        return position_size, risk_amount
    
    def _calculate_risk_reward(
        self,
        entry: float,
        stop_loss: float,
        take_profit: float,
        action: str
    ) -> float:
        """Calculate risk/reward ratio"""
        if action == 'BUY':
            risk = entry - stop_loss
            reward = take_profit - entry
        else:
            risk = stop_loss - entry
            reward = entry - take_profit
        
        if risk <= 0:
            return 0
        
        return reward / risk
    
    def _get_conviction(self, confidence: float) -> str:
        """Get conviction level from confidence"""
        if confidence >= 0.85:
            return 'high'
        elif confidence >= 0.70:
            return 'medium'
        else:
            return 'low'
    
    def _determine_order_type(self, setup: Dict) -> str:
        """Determine order type"""
        # Use limit orders for better entries in ranging markets
        if self.current_regime == MarketRegime.RANGING:
            return 'limit'
        
        # Use market orders in trending markets for quick execution
        if self.current_regime in [MarketRegime.TRENDING_UP, MarketRegime.TRENDING_DOWN]:
            return 'market'
        
        return 'limit'
    
    def _create_hold_decision(
        self,
        decision_id: str,
        symbol: str,
        current_price: float,
        reason: str
    ) -> TradeDecision:
        """Create a HOLD decision"""
        return TradeDecision(
            decision_id=decision_id,
            symbol=symbol,
            timestamp=datetime.now(),
            action='HOLD',
            trade_quality=TradeQuality.F,
            entry_price=current_price,
            stop_loss=0,
            take_profit=0,
            position_size=0,
            position_size_pct=0,
            risk_amount=0,
            risk_reward_ratio=0,
            max_risk_pct=0,
            confidence=0,
            conviction='low',
            regime=self.current_regime,
            style=self.current_style,
            reasoning=reason,
            key_factors=[],
            order_type='none',
            time_in_force='none'
        )
    
    def record_trade_result(
        self,
        decision_id: str,
        exit_price: float,
        pnl: float,
        is_win: bool
    ):
        """Record trade result for learning"""
        self.performance['total_trades'] += 1
        if is_win:
            self.performance['winning_trades'] += 1
        self.performance['total_pnl'] += pnl
        
        # Update win rate
        self.performance['win_rate'] = (
            self.performance['winning_trades'] / self.performance['total_trades']
        )
        
        # Update quality stats
        for decision in self.trade_history:
            if decision.decision_id == decision_id:
                quality = decision.trade_quality.value
                self.quality_stats[quality]['count'] += 1
                if is_win:
                    self.quality_stats[quality]['wins'] += 1
                break
        
        # Update daily PnL
        self.daily_pnl += pnl
        self.portfolio_value += pnl
        
        logger.info(f"Trade result recorded: {'WIN' if is_win else 'LOSS'}, PnL: {pnl:.2f}")
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.daily_pnl = 0.0
        self.daily_risk_used = 0.0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get brain statistics"""
        return {
            'performance': self.performance,
            'quality_stats': self.quality_stats,
            'current_regime': self.current_regime.value,
            'current_style': self.current_style.value,
            'portfolio_value': self.portfolio_value,
            'open_positions': len(self.open_positions),
            'daily_pnl': self.daily_pnl,
            'trade_history_size': len(self.trade_history)
        }
