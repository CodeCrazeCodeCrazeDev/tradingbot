"""
Profit Maximizer Brain Integration
===================================

Integrates the Profit Maximizer System with the existing Elite Brain architecture.
This allows the bot to use all 6 profit-maximizing components automatically.
"""

import logging
from typing import Any, Dict, Optional
import pandas as pd

from trading_bot.profit_maximizer.profit_maximizer_core import (
    ProfitMaximizerSystem,
    TradeDecision,
)

logger = logging.getLogger(__name__)


class ProfitMaximizerBrainWrapper:
    """
    Wraps the Profit Maximizer around the existing brain system.
    
    This acts as a filter/enhancer for trading decisions:
    1. Receives signal from Elite Brain
    2. Evaluates through Profit Maximizer
    3. Returns enhanced decision with better entry, targets, and sizing
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the brain wrapper
        
        Args:
            config: Configuration for Profit Maximizer
        """
        try:
            self.config = config or {}
            self.profit_maximizer = ProfitMaximizerSystem(self.config)
            self.enabled = True
        
            logger.info("Profit Maximizer Brain Wrapper initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def enhance_decision(self,
                        brain_decision: Dict,
                        market_data: pd.DataFrame,
                        additional_data: Optional[Dict] = None) -> Dict:
        """
        Enhance a brain decision with Profit Maximizer analysis
        
        Args:
            brain_decision: Decision from Elite Brain with keys:
                - direction: BUY/SELL
                - entry_price: Proposed entry
                - stop_loss: Proposed SL
                - take_profit: Proposed TP
                - confidence: Signal confidence
            market_data: OHLCV DataFrame
            additional_data: Extra data (HTF, order flow, etc.)
        
        Returns:
            Enhanced decision dict
        """
        try:
            if not self.enabled:
                return brain_decision
        
            # Extract brain decision components
            direction = brain_decision.get('direction', brain_decision.get('position_type', 'HOLD'))
        
            if direction == 'HOLD' or direction not in ['BUY', 'SELL']:
                return brain_decision
        
            entry_price = brain_decision.get('entry_price', market_data['close'].iloc[-1])
            stop_loss = brain_decision.get('stop_loss', entry_price * (0.99 if direction == 'BUY' else 1.01))
            confidence = brain_decision.get('confidence', 0.5)
        
            # Run through Profit Maximizer
            pm_decision = self.profit_maximizer.evaluate_signal(
                direction=direction,
                entry_price=entry_price,
                stop_loss=stop_loss,
                base_confidence=confidence,
                market_data=market_data,
                additional_data=additional_data
            )
        
            # Build enhanced decision
            enhanced = {
                **brain_decision,
                'profit_maximizer': {
                    'should_trade': pm_decision.should_trade,
                    'confluence_score': pm_decision.confluence_score,
                    'entry_quality': pm_decision.entry_quality.name,
                    'session_quality': pm_decision.session_quality.name,
                    'recovery_mode': pm_decision.recovery_mode.name,
                    'streak_mode': pm_decision.streak_mode.name,
                    'reasons_to_trade': pm_decision.reasons_to_trade,
                    'reasons_not_to_trade': pm_decision.reasons_not_to_trade,
                }
            }
        
            # Override with PM values if PM says trade
            if pm_decision.should_trade:
                enhanced['entry_price'] = pm_decision.entry_price
                enhanced['stop_loss'] = pm_decision.stop_loss
                enhanced['take_profit'] = pm_decision.take_profit
                enhanced['confidence'] = pm_decision.confidence
                enhanced['position_size_multiplier'] = pm_decision.position_size_multiplier
            
                if pm_decision.profit_targets:
                    enhanced['profit_targets'] = {
                        'tp1': pm_decision.profit_targets.take_profit_1,
                        'tp2': pm_decision.profit_targets.take_profit_2,
                        'tp3': pm_decision.profit_targets.take_profit_3,
                        'trailing_start': pm_decision.profit_targets.trailing_start,
                        'trailing_distance': pm_decision.profit_targets.trailing_distance,
                        'risk_reward': pm_decision.profit_targets.risk_reward_ratio,
                    }
            else:
                # PM says don't trade - override to HOLD
                enhanced['direction'] = 'HOLD'
                enhanced['position_type'] = 'HOLD'
                enhanced['confidence'] = 0.0
                enhanced['position_size_multiplier'] = 0.0
        
            return enhanced
        except Exception as e:
            logger.error(f"Error in enhance_decision: {e}")
            raise
    
    def record_result(self, trade_result: Dict):
        """Record trade result for learning"""
        try:
            self.profit_maximizer.record_trade_result(trade_result)
        except Exception as e:
            logger.error(f"Error in record_result: {e}")
            raise
    
    def get_stats(self) -> Dict:
        """Get Profit Maximizer statistics"""
        return self.profit_maximizer.get_statistics()
    
    def enable(self):
        """Enable Profit Maximizer"""
        try:
            self.enabled = True
            logger.info("Profit Maximizer enabled")
        except Exception as e:
            logger.error(f"Error in enable: {e}")
            raise
    
    def disable(self):
        """Disable Profit Maximizer"""
        try:
            self.enabled = False
            logger.info("Profit Maximizer disabled")
        except Exception as e:
            logger.error(f"Error in disable: {e}")
            raise


def integrate_with_brain(brain_controller, config: Optional[Dict] = None) -> ProfitMaximizerBrainWrapper:
    """
    Integrate Profit Maximizer with an existing brain controller
    
    Args:
        brain_controller: Existing EliteBrainController or similar
        config: Profit Maximizer config
    
    Returns:
        ProfitMaximizerBrainWrapper instance
    """
    wrapper = ProfitMaximizerBrainWrapper(config)
    
    # Store original process method
    original_process = brain_controller.process_market_data
    
    def enhanced_process(market_data: pd.DataFrame, additional_inputs: Optional[Dict] = None) -> Dict:
        # Get original decision
        try:
            decision = original_process(market_data, additional_inputs)
        
            # Enhance with Profit Maximizer
            enhanced = wrapper.enhance_decision(decision, market_data, additional_inputs)
        
            return enhanced
        except Exception as e:
            logger.error(f"Error in enhanced_process: {e}")
            raise
    
    # Replace with enhanced version
    brain_controller.process_market_data = enhanced_process
    brain_controller.profit_maximizer = wrapper
    
    logger.info("Profit Maximizer integrated with brain controller")
    
    return wrapper
