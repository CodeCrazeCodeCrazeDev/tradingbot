"""
AlphaAlgo Adaptive Integration System

This module provides a self-adapting integration approach that automatically
selects the optimal integration method based on current market conditions.

The system can dynamically switch between:
1. Full-Tier Integration (all 9 tiers) - for complex market conditions
2. Fast-Track Integration (selected tiers) - for stable markets
3. Emergency Integration (critical tiers only) - for extreme volatility
"""

import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import time

from trading_bot.brain.tier_structure import (
    # Tier structure
    AlphaBrain, SignalOutput, MarketStateVector, OrderFlowIntelligence,
    MarketGeometryModel, RegimeContextVector, SentimentVector, MacroContext,
    RiskParameters, ExecutionIntelligence, EliteBrainSignal,
)
from trading_bot.brain.tier1_technical import Tier1TechnicalAnalysis
from trading_bot.brain.tier2_orderflow import Tier2OrderFlowIntelligence
from trading_bot.brain.tier3_structure import Tier3MarketStructure
from trading_bot.brain.tier4_regime import Tier4RegimeDetection
from trading_bot.brain.tier5_sentiment import Tier5SentimentAnalysis
from trading_bot.brain.tier6_macro import Tier6MacroAnalysis
from trading_bot.brain.tier7_risk import Tier7RiskManagement
from trading_bot.brain.tier8_execution import Tier8ExecutionIntelligence
from trading_bot.brain.tier9_metalearning import Tier9MetaLearning
from trading_bot.brain.brain_architecture import EliteBrainController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarketCondition(Enum):
    """Market condition classification"""
    NORMAL = "normal"           # Stable, predictable markets
    VOLATILE = "volatile"       # High volatility but structured
    EXTREME = "extreme"         # Extreme volatility, potential crisis
    TRENDING = "trending"       # Strong directional movement
    RANGING = "ranging"         # Sideways, consolidation
    TRANSITIONING = "transitioning"  # Regime change in progress


class IntegrationMode(Enum):
    """Integration mode based on market conditions"""
    FULL_TIER = "full_tier"         # All 9 tiers in sequence
    FAST_TRACK = "fast_track"       # Selected tiers for efficiency
    EMERGENCY = "emergency"         # Critical tiers only for extreme conditions
    TREND_FOCUSED = "trend_focused" # Emphasis on trend following
    MEAN_REVERSION = "mean_reversion"  # Emphasis on mean reversion
    ADAPTIVE = "adaptive"           # Dynamic tier weighting


class AdaptiveIntegrationSystem:
    """
    Adaptive Integration System that selects the optimal integration
    approach based on current market conditions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the adaptive integration system
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Initialize all tiers
        self.tier1 = Tier1TechnicalAnalysis()
        self.tier2 = Tier2OrderFlowIntelligence()
        self.tier3 = Tier3MarketStructure()
        self.tier4 = Tier4RegimeDetection()
        self.tier5 = Tier5SentimentAnalysis()
        self.tier6 = Tier6MacroAnalysis()
        self.tier7 = Tier7RiskManagement()
        self.tier8 = Tier8ExecutionIntelligence()
        self.tier9 = Tier9MetaLearning()
        
        # Initialize controllers
        self.alpha_brain = AlphaBrain()
        self.elite_controller = EliteBrainController()
        
        # Track current market condition and integration mode
        self.current_condition = MarketCondition.NORMAL
        self.current_mode = IntegrationMode.FULL_TIER
        
        # Performance metrics for each mode
        self.mode_performance = {mode: 0.0 for mode in IntegrationMode}
        
        # Initialize tiers and controllers
        self._initialize_components()
        
        logger.info("Adaptive Integration System initialized")
    
    def _initialize_components(self) -> bool:
        """Initialize all components"""
        # Initialize all tiers
        tiers = [self.tier1, self.tier2, self.tier3, self.tier4, 
                self.tier5, self.tier6, self.tier7, self.tier8, self.tier9]
        
        for tier in tiers:
            if not tier.initialize():
                logger.error(f"Failed to initialize {tier.name}")
                return False
        
        # Initialize controllers
        if not self.alpha_brain.initialize_tiers():
            logger.error("Failed to initialize AlphaBrain")
            return False
        
        if not self.elite_controller.initialize():
            logger.error("Failed to initialize Elite Brain Controller")
            return False
        
        return True
    
    def detect_market_condition(self, market_data: pd.DataFrame) -> MarketCondition:
        """
        Detect current market condition based on market data
        
        Args:
            market_data: OHLCV DataFrame
            
        Returns:
            MarketCondition enum value
        """
        try:
            # Calculate key metrics
            returns = market_data['close'].pct_change().dropna()
            
            # Volatility (annualized)
            volatility = returns.std() * np.sqrt(252)
            
            # Trend strength
            price_sma = market_data['close'].rolling(20).mean()
            trend_strength = abs(market_data['close'].iloc[-1] / price_sma.iloc[-1] - 1)
            
            # Range measurement
            high_low_ratio = market_data['high'].rolling(10).max() / market_data['low'].rolling(10).min()
            range_bound = high_low_ratio.iloc[-1] < 1.02  # Less than 2% range
            
            # Detect conditions
            if volatility > 0.03:  # Extremely high volatility (>3% daily)
                return MarketCondition.EXTREME
            elif volatility > 0.015:  # High volatility (>1.5% daily)
                return MarketCondition.VOLATILE
            elif trend_strength > 0.05:  # Strong trend (>5% from SMA)
                return MarketCondition.TRENDING
            elif range_bound:
                return MarketCondition.RANGING
            
            # Check for regime change
            if self.current_condition != MarketCondition.NORMAL:
                # If previous condition was not normal, check if transitioning
                regime_change = self._detect_regime_change(market_data)
                if regime_change:
                    return MarketCondition.TRANSITIONING
            
            # Default to normal
            return MarketCondition.NORMAL
            
        except Exception as e:
            logger.error(f"Error detecting market condition: {str(e)}")
            return MarketCondition.NORMAL
    
    def _detect_regime_change(self, market_data: pd.DataFrame) -> bool:
        """Detect if market is transitioning between regimes"""
        try:
            # Process through Tier 4 (Regime Detection) to check for regime change
            t1_output = self.tier1.process(market_data)
            t2_output = self.tier2.process(market_data, t1_output)
            t3_output = self.tier3.process(market_data, t2_output)
            t4_output = self.tier4.process(market_data, t3_output)
            
            # Check regime probability
            regime_prob = t4_output.regime_probability
            
            # If regime probability is low, it suggests uncertainty/transition
            return regime_prob < 0.6
            
        except Exception as e:
            logger.error(f"Error in regime change detection: {str(e)}")
            return False
    
    def select_integration_mode(self, condition: MarketCondition) -> IntegrationMode:
        """
        Select optimal integration mode based on market condition
        
        Args:
            condition: Current market condition
            
        Returns:
            IntegrationMode enum value
        """
        # Map conditions to modes
        condition_to_mode = {
            MarketCondition.NORMAL: IntegrationMode.FULL_TIER,
            MarketCondition.VOLATILE: IntegrationMode.FAST_TRACK,
            MarketCondition.EXTREME: IntegrationMode.EMERGENCY,
            MarketCondition.TRENDING: IntegrationMode.TREND_FOCUSED,
            MarketCondition.RANGING: IntegrationMode.MEAN_REVERSION,
            MarketCondition.TRANSITIONING: IntegrationMode.ADAPTIVE
        }
        
        # Get default mode for this condition
        default_mode = condition_to_mode.get(condition, IntegrationMode.FULL_TIER)
        
        # Check if we should override based on performance
        best_mode = max(self.mode_performance.items(), key=lambda x: x[1])[0]
        
        # If best performing mode has significantly better performance, use it
        if self.mode_performance[best_mode] > self.mode_performance[default_mode] * 1.2:
            return best_mode
        
        return default_mode
    
    def process_full_tier(self, market_data: pd.DataFrame, 
                         additional_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process using full 9-tier sequence
        
        Args:
            market_data: OHLCV DataFrame
            additional_inputs: Additional inputs for tiers
            
        Returns:
            Dictionary with processing results
        """
        logger.info("Processing with FULL_TIER mode")
        start_time = time.time()
        
        # Process through all tiers sequentially
        t1_output = self.tier1.process(market_data)
        t2_output = self.tier2.process(market_data, t1_output, additional_inputs)
        t3_output = self.tier3.process(market_data, t2_output, additional_inputs)
        t4_output = self.tier4.process(market_data, t3_output, additional_inputs)
        t5_output = self.tier5.process(market_data, t4_output, additional_inputs)
        t6_output = self.tier6.process(market_data, t5_output, additional_inputs)
        t7_output = self.tier7.process(market_data, t6_output, additional_inputs)
        t8_output = self.tier8.process(market_data, t7_output, additional_inputs)
        
        # Prepare tier outputs for meta-learning
        tier_outputs = {
            'tier1': {'signal_value': t1_output.signal_value, 'confidence': t1_output.confidence},
            'tier2': {'signal_value': t2_output.signal_value, 'confidence': t2_output.confidence},
            'tier3': {'signal_value': t3_output.signal_value, 'confidence': t3_output.confidence},
            'tier4': {'signal_value': t4_output.signal_value, 'confidence': t4_output.confidence},
            'tier5': {'signal_value': t5_output.signal_value, 'confidence': t5_output.confidence},
            'tier6': {'signal_value': t6_output.signal_value, 'confidence': t6_output.confidence},
            'tier7': {'signal_value': t7_output.signal_value, 'confidence': t7_output.confidence},
            'tier8': {'signal_value': t8_output.signal_value, 'confidence': t8_output.confidence}
        }
        
        # Add to additional inputs
        additional_inputs['tier_outputs'] = tier_outputs
        
        # Process final tier
        t9_output = self.tier9.process(market_data, t8_output, additional_inputs)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return {
            'decision': t9_output.final_decision,
            'position_type': t9_output.position_type,
            'signal_value': t9_output.signal_value,
            'confidence': t9_output.confidence,
            'explanation': t9_output.explanation,
            'processing_time': processing_time
        }
    
    def process_fast_track(self, market_data: pd.DataFrame, 
                          additional_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process using fast-track approach (selected tiers)
        
        Args:
            market_data: OHLCV DataFrame
            additional_inputs: Additional inputs for tiers
            
        Returns:
            Dictionary with processing results
        """
        logger.info("Processing with FAST_TRACK mode")
        start_time = time.time()
        
        # Process only essential tiers
        t1_output = self.tier1.process(market_data)
        t4_output = self.tier4.process(market_data, None, additional_inputs)
        t7_output = self.tier7.process(market_data, None, additional_inputs)
        
        # Use AlphaBrain for faster processing
        decision = self.alpha_brain.process_market_data(market_data, additional_inputs)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return {
            'decision': decision.final_decision,
            'position_type': decision.position_type,
            'signal_value': decision.signal_value,
            'confidence': decision.confidence,
            'explanation': decision.explanation,
            'processing_time': processing_time
        }
    
    def process_emergency(self, market_data: pd.DataFrame, 
                         additional_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process using emergency approach (critical tiers only)
        
        Args:
            market_data: OHLCV DataFrame
            additional_inputs: Additional inputs for tiers
            
        Returns:
            Dictionary with processing results
        """
        logger.info("Processing with EMERGENCY mode")
        start_time = time.time()
        
        # Process only critical tiers
        t1_output = self.tier1.process(market_data)
        t7_output = self.tier7.process(market_data, None, additional_inputs)
        
        # In emergency mode, prioritize risk management
        position_size = t7_output.position_size
        stop_loss = t7_output.stop_loss_level
        
        # Use simple signal from technical analysis
        signal_value = t1_output.signal_value * 0.5  # Reduce signal strength in emergency
        
        # Determine decision
        if abs(signal_value) < 0.2:
            decision = "HOLD"
            position_type = "none"
        elif signal_value > 0:
            decision = "BUY"
            position_type = "long"
        else:
            decision = "SELL"
            position_type = "short"
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return {
            'decision': decision,
            'position_type': position_type,
            'signal_value': signal_value,
            'confidence': t1_output.confidence * 0.7,  # Reduce confidence in emergency
            'explanation': {
                'emergency_mode': True,
                'risk_parameters': {
                    'position_size': position_size,
                    'stop_loss': stop_loss
                }
            },
            'processing_time': processing_time
        }
    
    def process_trend_focused(self, market_data: pd.DataFrame, 
                            additional_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process using trend-focused approach
        
        Args:
            market_data: OHLCV DataFrame
            additional_inputs: Additional inputs for tiers
            
        Returns:
            Dictionary with processing results
        """
        logger.info("Processing with TREND_FOCUSED mode")
        start_time = time.time()
        
        # Process trend-relevant tiers with higher weight on trend signals
        t1_output = self.tier1.process(market_data)
        t3_output = self.tier3.process(market_data, None, additional_inputs)
        t4_output = self.tier4.process(market_data, t3_output, additional_inputs)
        t7_output = self.tier7.process(market_data, None, additional_inputs)
        
        # Calculate weighted signal with emphasis on trend
        trend_signal = t1_output.signal_value
        structure_signal = t3_output.signal_value
        regime_signal = t4_output.signal_value
        
        # Emphasize trend components
        signal_value = (
            0.6 * trend_signal +
            0.3 * structure_signal +
            0.1 * regime_signal
        )
        
        # Determine decision
        if abs(signal_value) < 0.2:
            decision = "HOLD"
            position_type = "none"
        elif signal_value > 0:
            decision = "BUY"
            position_type = "long"
        else:
            decision = "SELL"
            position_type = "short"
        
        # Calculate confidence
        confidence = (
            0.6 * t1_output.confidence +
            0.3 * t3_output.confidence +
            0.1 * t4_output.confidence
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return {
            'decision': decision,
            'position_type': position_type,
            'signal_value': signal_value,
            'confidence': confidence,
            'explanation': {
                'trend_focused_mode': True,
                'trend_signal': trend_signal,
                'structure_signal': structure_signal,
                'regime_signal': regime_signal,
                'risk_parameters': {
                    'position_size': t7_output.position_size,
                    'stop_loss': t7_output.stop_loss_level
                }
            },
            'processing_time': processing_time
        }
    
    def process_mean_reversion(self, market_data: pd.DataFrame, 
                             additional_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process using mean-reversion approach
        
        Args:
            market_data: OHLCV DataFrame
            additional_inputs: Additional inputs for tiers
            
        Returns:
            Dictionary with processing results
        """
        logger.info("Processing with MEAN_REVERSION mode")
        start_time = time.time()
        
        # Process mean-reversion-relevant tiers
        t1_output = self.tier1.process(market_data)
        t2_output = self.tier2.process(market_data, t1_output, additional_inputs)
        t3_output = self.tier3.process(market_data, t2_output, additional_inputs)
        t7_output = self.tier7.process(market_data, None, additional_inputs)
        
        # Extract mean reversion probability
        mean_rev_prob = t3_output.mean_reversion_probability
        
        # Calculate signal with emphasis on mean reversion
        # Invert the technical signal if mean reversion probability is high
        if mean_rev_prob > 0.7:
            # Invert signal for mean reversion
            signal_value = -t1_output.signal_value * mean_rev_prob
        else:
            # Use normal signal with reduced strength
            signal_value = t1_output.signal_value * (1 - mean_rev_prob)
        
        # Add order flow component
        signal_value += 0.3 * t2_output.signal_value
        
        # Determine decision
        if abs(signal_value) < 0.2:
            decision = "HOLD"
            position_type = "none"
        elif signal_value > 0:
            decision = "BUY"
            position_type = "long"
        else:
            decision = "SELL"
            position_type = "short"
        
        # Calculate confidence based on mean reversion probability
        confidence = mean_rev_prob * t3_output.confidence
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return {
            'decision': decision,
            'position_type': position_type,
            'signal_value': signal_value,
            'confidence': confidence,
            'explanation': {
                'mean_reversion_mode': True,
                'mean_reversion_probability': mean_rev_prob,
                'technical_signal': t1_output.signal_value,
                'order_flow_signal': t2_output.signal_value,
                'risk_parameters': {
                    'position_size': t7_output.position_size,
                    'stop_loss': t7_output.stop_loss_level
                }
            },
            'processing_time': processing_time
        }
    
    def process_adaptive(self, market_data: pd.DataFrame, 
                        additional_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process using adaptive approach with dynamic tier weighting
        
        Args:
            market_data: OHLCV DataFrame
            additional_inputs: Additional inputs for tiers
            
        Returns:
            Dictionary with processing results
        """
        logger.info("Processing with ADAPTIVE mode")
        start_time = time.time()
        
        # Use Elite Brain Controller for adaptive processing
        decision = self.elite_controller.process_market_data(market_data, additional_inputs)
        
        # Get explanation
        explanation = self.elite_controller.get_explanation()
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return {
            'decision': decision.get('decision', 'HOLD'),
            'position_type': decision.get('position_type', 'none'),
            'signal_value': decision.get('signal_value', 0.0),
            'confidence': decision.get('confidence', 0.0),
            'explanation': explanation,
            'processing_time': processing_time
        }
    
    def process(self, market_data: pd.DataFrame, 
               additional_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process market data using adaptive integration
        
        Args:
            market_data: OHLCV DataFrame
            additional_inputs: Additional inputs for tiers
            
        Returns:
            Dictionary with processing results
        """
        if additional_inputs is None:
            additional_inputs = {}
        
        # Detect market condition
        condition = self.detect_market_condition(market_data)
        logger.info(f"Detected market condition: {condition.value}")
        
        # Select integration mode
        mode = self.select_integration_mode(condition)
        logger.info(f"Selected integration mode: {mode.value}")
        
        # Update current condition and mode
        self.current_condition = condition
        self.current_mode = mode
        
        # Process based on selected mode
        if mode == IntegrationMode.FULL_TIER:
            result = self.process_full_tier(market_data, additional_inputs)
        elif mode == IntegrationMode.FAST_TRACK:
            result = self.process_fast_track(market_data, additional_inputs)
        elif mode == IntegrationMode.EMERGENCY:
            result = self.process_emergency(market_data, additional_inputs)
        elif mode == IntegrationMode.TREND_FOCUSED:
            result = self.process_trend_focused(market_data, additional_inputs)
        elif mode == IntegrationMode.MEAN_REVERSION:
            result = self.process_mean_reversion(market_data, additional_inputs)
        else:  # ADAPTIVE
            result = self.process_adaptive(market_data, additional_inputs)
        
        # Add condition and mode to result
        result['market_condition'] = condition.value
        result['integration_mode'] = mode.value
        
        return result
    
    def update_performance(self, mode: IntegrationMode, 
                          performance_score: float) -> None:
        """
        Update performance metrics for integration modes
        
        Args:
            mode: Integration mode
            performance_score: Performance score (-1 to 1)
        """
        # Update with exponential moving average
        alpha = 0.2
        current = self.mode_performance.get(mode, 0.0)
        self.mode_performance[mode] = alpha * performance_score + (1 - alpha) * current
        
        logger.info(f"Updated performance for {mode.value}: {self.mode_performance[mode]:.4f}")


# Example usage
if __name__ == "__main__":
    # Create adaptive integration system
    adaptive_system = AdaptiveIntegrationSystem()
    
    # Load sample data
    from integration_example import load_sample_data, create_sample_additional_inputs
    
    # Process normal market
    logger.info("\n=== Processing Normal Market ===")
    market_data = load_sample_data()
    additional_inputs = create_sample_additional_inputs()
    result = adaptive_system.process(market_data, additional_inputs)
    logger.info(f"Decision: {result['decision']} ({result['confidence']:.2%})")
    logger.info(f"Market Condition: {result['market_condition']}")
    logger.info(f"Integration Mode: {result['integration_mode']}")
    logger.info(f"Processing Time: {result['processing_time']:.4f}s")
    
    # Process volatile market (add volatility)
    logger.info("\n=== Processing Volatile Market ===")
    volatile_data = market_data.copy()
    volatile_data['close'] = volatile_data['close'] * (1 + np.random.normal(0, 0.02, len(volatile_data)))
    result = adaptive_system.process(volatile_data, additional_inputs)
    logger.info(f"Decision: {result['decision']} ({result['confidence']:.2%})")
    logger.info(f"Market Condition: {result['market_condition']}")
    logger.info(f"Integration Mode: {result['integration_mode']}")
    logger.info(f"Processing Time: {result['processing_time']:.4f}s")
    
    # Process trending market (add trend)
    logger.info("\n=== Processing Trending Market ===")
    trending_data = market_data.copy()
    trend = np.linspace(0, 0.1, len(trending_data))
    trending_data['close'] = trending_data['close'] * (1 + trend)
    result = adaptive_system.process(trending_data, additional_inputs)
    logger.info(f"Decision: {result['decision']} ({result['confidence']:.2%})")
    logger.info(f"Market Condition: {result['market_condition']}")
    logger.info(f"Integration Mode: {result['integration_mode']}")
    logger.info(f"Processing Time: {result['processing_time']:.4f}s")
    
    # Update performance based on outcomes
    adaptive_system.update_performance(IntegrationMode.FULL_TIER, 0.5)
    adaptive_system.update_performance(IntegrationMode.FAST_TRACK, 0.3)
    adaptive_system.update_performance(IntegrationMode.TREND_FOCUSED, 0.8)
    
    logger.info("\n=== Updated Mode Performance ===")
    for mode, score in adaptive_system.mode_performance.items():
        logger.info(f"{mode.value}: {score:.4f}")
