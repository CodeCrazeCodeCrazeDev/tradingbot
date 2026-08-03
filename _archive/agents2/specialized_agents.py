"""
Phase 2: Specialized Trading Agents
Different agents for different market conditions
"""

import numpy as np
from typing import Dict
import logging
from .base_agent import BaseAgent, AgentType, AgentProposal

# Set up logger
logger = logging.getLogger(__name__)


class TrendFollowingAgent(BaseAgent):
    """Agent specialized in trending markets."""
    
    def __init__(self, agent_id: str = "trend_agent"):
        try:
            super().__init__(agent_id, AgentType.TREND_FOLLOWER)
            self.trend_threshold = 0.02  # 2% move to confirm trend
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def get_strategy_name(self) -> str:
        return "Trend Following"
    
    def analyze_market(self, market_data: Dict) -> AgentProposal:
        """Analyze for trend-following opportunities."""
        
        # Extract indicators
        try:
            sma_20 = market_data.get('sma_20', 0)
            sma_50 = market_data.get('sma_50', 0)
            price = market_data.get('price', 0)
            macd = market_data.get('macd', 0)
        
            # Detect trend
            if sma_20 > sma_50 * 1.01 and price > sma_20 and macd > 0:
                # Strong uptrend
                action = 'BUY'
                signal_strength = min((sma_20 - sma_50) / sma_50 / 0.05, 1.0)
                reasoning = f"Strong uptrend: SMA20 > SMA50, price above SMA20, MACD positive"
                expected_return = 0.015
                risk_score = 0.3
            
            elif sma_20 < sma_50 * 0.99 and price < sma_20 and macd < 0:
                # Strong downtrend
                action = 'SELL'
                signal_strength = min((sma_50 - sma_20) / sma_50 / 0.05, 1.0)
                reasoning = f"Strong downtrend: SMA20 < SMA50, price below SMA20, MACD negative"
                expected_return = 0.015
                risk_score = 0.3
            
            else:
                # No clear trend
                action = 'HOLD'
                signal_strength = 0.0
                reasoning = "No clear trend detected"
                expected_return = 0.0
                risk_score = 0.5
        
            confidence = self.calculate_confidence(signal_strength, market_data)
        
            return AgentProposal(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                action=action,
                confidence=confidence,
                reasoning=reasoning,
                expected_return=expected_return,
                risk_score=risk_score,
                priority=2
            )
        except Exception as e:
            logger.error(f"Error in analyze_market: {e}")
            raise


class MeanReversionAgent(BaseAgent):
    """Agent specialized in mean-reverting markets."""
    
    def __init__(self, agent_id: str = "mean_reversion_agent"):
        try:
            super().__init__(agent_id, AgentType.MEAN_REVERTER)
            self.oversold_threshold = 30
            self.overbought_threshold = 70
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def get_strategy_name(self) -> str:
        return "Mean Reversion"
    
    def analyze_market(self, market_data: Dict) -> AgentProposal:
        """Analyze for mean reversion opportunities."""
        
        try:
            rsi = market_data.get('rsi', 50)
            price = market_data.get('price', 0)
            sma_20 = market_data.get('sma_20', price)
            volatility = market_data.get('volatility', 1.0)
        
            # Calculate deviation from mean
            deviation = abs(price - sma_20) / sma_20 if sma_20 > 0 else 0
        
            if rsi < self.oversold_threshold and deviation > 0.02:
                # Oversold, expect bounce
                action = 'BUY'
                signal_strength = (self.oversold_threshold - rsi) / self.oversold_threshold
                reasoning = f"Oversold (RSI={rsi:.1f}), {deviation:.1%} below mean"
                expected_return = 0.01
                risk_score = 0.4
            
            elif rsi > self.overbought_threshold and deviation > 0.02:
                # Overbought, expect pullback
                action = 'SELL'
                signal_strength = (rsi - self.overbought_threshold) / (100 - self.overbought_threshold)
                reasoning = f"Overbought (RSI={rsi:.1f}), {deviation:.1%} above mean"
                expected_return = 0.01
                risk_score = 0.4
            
            else:
                action = 'HOLD'
                signal_strength = 0.0
                reasoning = "No mean reversion opportunity"
                expected_return = 0.0
                risk_score = 0.5
        
            confidence = self.calculate_confidence(signal_strength, market_data)
        
            return AgentProposal(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                action=action,
                confidence=confidence,
                reasoning=reasoning,
                expected_return=expected_return,
                risk_score=risk_score,
                priority=2
            )
        except Exception as e:
            logger.error(f"Error in analyze_market: {e}")
            raise


class VolatilityAgent(BaseAgent):
    """Agent specialized in volatility trading."""
    
    def __init__(self, agent_id: str = "volatility_agent"):
        try:
            super().__init__(agent_id, AgentType.VOLATILITY_TRADER)
            self.high_vol_threshold = 2.5
            self.low_vol_threshold = 0.5
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def get_strategy_name(self) -> str:
        return "Volatility Trading"
    
    def analyze_market(self, market_data: Dict) -> AgentProposal:
        """Analyze volatility conditions."""
        
        try:
            volatility = market_data.get('volatility', 1.0)
            rsi = market_data.get('rsi', 50)
            macd = market_data.get('macd', 0)
        
            if volatility > self.high_vol_threshold:
                # High volatility - trade breakouts
                if rsi > 60 and macd > 0:
                    action = 'BUY'
                    reasoning = f"High volatility ({volatility:.2f}), bullish breakout"
                    expected_return = 0.02
                    risk_score = 0.7
                elif rsi < 40 and macd < 0:
                    action = 'SELL'
                    reasoning = f"High volatility ({volatility:.2f}), bearish breakout"
                    expected_return = 0.02
                    risk_score = 0.7
                else:
                    action = 'HOLD'
                    reasoning = f"High volatility ({volatility:.2f}), waiting for clear direction"
                    expected_return = 0.0
                    risk_score = 0.8
            
                signal_strength = min(volatility / 5.0, 1.0)
            
            elif volatility < self.low_vol_threshold:
                # Low volatility - expect expansion
                action = 'HOLD'
                signal_strength = 0.0
                reasoning = f"Low volatility ({volatility:.2f}), waiting for expansion"
                expected_return = 0.0
                risk_score = 0.3
            
            else:
                # Normal volatility
                action = 'HOLD'
                signal_strength = 0.0
                reasoning = f"Normal volatility ({volatility:.2f})"
                expected_return = 0.0
                risk_score = 0.5
        
            confidence = self.calculate_confidence(signal_strength, market_data)
        
            return AgentProposal(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                action=action,
                confidence=confidence,
                reasoning=reasoning,
                expected_return=expected_return,
                risk_score=risk_score,
                priority=1
            )
        except Exception as e:
            logger.error(f"Error in analyze_market: {e}")
            raise


class RiskManagerAgent(BaseAgent):
    """Agent focused on risk management and position sizing."""
    
    def __init__(self, agent_id: str = "risk_manager"):
        try:
            super().__init__(agent_id, AgentType.RISK_MANAGER)
            self.max_risk_score = 0.7
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def get_strategy_name(self) -> str:
        return "Risk Management"
    
    def analyze_market(self, market_data: Dict) -> AgentProposal:
        """Assess risk and provide risk management recommendations."""
        
        try:
            volatility = market_data.get('volatility', 1.0)
            open_positions = market_data.get('open_positions', 0)
            total_pnl = market_data.get('total_pnl', 0)
        
            # Calculate risk score
            risk_score = 0.0
        
            # Volatility risk
            if volatility > 3.0:
                risk_score += 0.4
            elif volatility > 2.0:
                risk_score += 0.2
        
            # Position concentration risk
            if open_positions >= 3:
                risk_score += 0.3
            elif open_positions >= 2:
                risk_score += 0.15
        
            # Drawdown risk
            if total_pnl < -5000:
                risk_score += 0.3
            elif total_pnl < -2000:
                risk_score += 0.15
        
            # Risk assessment
            if risk_score > self.max_risk_score:
                action = 'HOLD'
                reasoning = f"High risk detected (score={risk_score:.2f}), recommend no new positions"
                confidence = 0.9
                expected_return = 0.0
            elif risk_score > 0.5:
                action = 'HOLD'
                reasoning = f"Moderate risk (score={risk_score:.2f}), recommend caution"
                confidence = 0.7
                expected_return = 0.0
            else:
                action = 'HOLD'
                reasoning = f"Low risk (score={risk_score:.2f}), conditions acceptable"
                confidence = 0.5
                expected_return = 0.0
        
            return AgentProposal(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                action=action,
                confidence=confidence,
                reasoning=reasoning,
                expected_return=expected_return,
                risk_score=risk_score,
                priority=3  # High priority for risk management
            )
        except Exception as e:
            logger.error(f"Error in analyze_market: {e}")
            raise
    
    def calculate_position_size(self, base_size: float, risk_score: float) -> float:
        """Calculate adjusted position size based on risk."""
        try:
            if risk_score > 0.7:
                return 0.0  # No trading
            elif risk_score > 0.5:
                return base_size * 0.5  # Half size
            elif risk_score > 0.3:
                return base_size * 0.75  # 75% size
            else:
                return base_size  # Full size
        except Exception as e:
            logger.error(f"Error in calculate_position_size: {e}")
            raise


class MarketMakerAgent(BaseAgent):
    """Agent for market making strategies."""
    
    def __init__(self, agent_id: str = "market_maker"):
        try:
            super().__init__(agent_id, AgentType.MARKET_MAKER)
            self.spread_threshold = 0.001  # 0.1%
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def get_strategy_name(self) -> str:
        return "Market Making"
    
    def analyze_market(self, market_data: Dict) -> AgentProposal:
        """Analyze for market making opportunities."""
        
        try:
            volatility = market_data.get('volatility', 1.0)
            spread = market_data.get('spread', 0.002)
        
            # Market making works best in low volatility, high spread
            if volatility < 1.0 and spread > self.spread_threshold:
                action = 'HOLD'  # Market maker provides liquidity
                signal_strength = min(spread / 0.005, 1.0)
                reasoning = f"Good market making conditions: low vol ({volatility:.2f}), spread {spread:.4f}"
                expected_return = 0.005
                risk_score = 0.2
            else:
                action = 'HOLD'
                signal_strength = 0.0
                reasoning = "Poor market making conditions"
                expected_return = 0.0
                risk_score = 0.5
        
            confidence = self.calculate_confidence(signal_strength, market_data)
        
            return AgentProposal(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                action=action,
                confidence=confidence,
                reasoning=reasoning,
                expected_return=expected_return,
                risk_score=risk_score,
                priority=1
            )
        except Exception as e:
            logger.error(f"Error in analyze_market: {e}")
            raise
