"""
AlphaAlgo Brain Integration Example

This example demonstrates how to use all 9 tiers of the AlphaAlgo brain architecture
to process market data and generate trading decisions.
"""

import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

try:
    from trading_bot.brain.tier_structure import (
        AlphaBrain, SignalOutput, MarketStateVector, OrderFlowIntelligence,
        MarketGeometryModel, RegimeContextVector, SentimentVector, MacroContext,
        RiskParameters, ExecutionIntelligence, EliteBrainSignal,
    )
    from trading_bot.brain import (
        # Tier implementations
        Tier1TechnicalAnalysis, Tier2OrderFlowIntelligence, Tier3MarketStructure,
        Tier4RegimeDetection, Tier5SentimentAnalysis, Tier6MacroAnalysis,
        Tier7RiskManagement, Tier8ExecutionIntelligence, Tier9MetaLearning,
        
        # Elite Brain Controller
        EliteBrainController
    )
except ImportError as e:
    logging.getLogger(__name__).warning(f"Brain imports failed: {e}")
    AlphaBrain = SignalOutput = MarketStateVector = OrderFlowIntelligence = None
    MarketGeometryModel = RegimeContextVector = SentimentVector = MacroContext = None
    RiskParameters = ExecutionIntelligence = EliteBrainSignal = None
    Tier1TechnicalAnalysis = Tier2OrderFlowIntelligence = Tier3MarketStructure = None
    Tier4RegimeDetection = Tier5SentimentAnalysis = Tier6MacroAnalysis = None
    Tier7RiskManagement = Tier8ExecutionIntelligence = Tier9MetaLearning = None
    EliteBrainController = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_sample_data(symbol: str = 'EURUSD', 
                   start_date: str = '2024-01-01',
                   periods: int = 500) -> pd.DataFrame:
    """Load sample OHLCV data"""
    logger.info(f"Loading sample data for {symbol}")
    
    # Generate synthetic data
    dates = pd.date_range(start_date, periods=periods, freq='1H')
    np.random.seed(42)
    
    # Create trending market with some volatility
    trend = np.cumsum(np.random.normal(0.0001, 0.0005, periods))
    noise = np.random.normal(0, 0.001, periods)
    price = 1.1 + trend + noise
    
    # Create OHLCV data
    df = pd.DataFrame({
        'open': price + np.random.normal(0, 0.0005, periods),
        'high': price + np.random.uniform(0.0005, 0.002, periods),
        'low': price - np.random.uniform(0.0005, 0.002, periods),
        'close': price,
        'volume': np.random.randint(1000, 10000, periods)
    }, index=dates)
    
    return df


def create_sample_additional_inputs() -> Dict[str, Any]:
    """Create sample additional inputs for all tiers"""
    logger.info("Creating sample additional inputs")
    
    # Create sample order book
    order_book = {
        'bids': [(1.1005, 1000), (1.1000, 2000), (1.0995, 1500)],
        'asks': [(1.1015, 800), (1.1020, 1500), (1.1025, 2000)],
        'spread': 0.001
    }
    
    # Create sample news data
    news_data = [
        {'title': 'ECB Holds Rates', 'sentiment': 0.2, 'importance': 0.8},
        {'title': 'US Inflation Higher', 'sentiment': -0.3, 'importance': 0.7}
    ]
    
    # Create sample social data
    social_data = [
        {'text': 'EUR looking bullish', 'sentiment': 0.7},
        {'text': 'USD weakness continues', 'sentiment': 0.5}
    ]
    
    # Create sample rates data
    rates_data = {
        'EUR': 4.25,
        'USD': 5.50,
        'historical': {'EUR': 4.0, 'USD': 5.25}
    }
    
    # Create sample yield data
    yield_data = {
        '2Y': 4.89,
        '10Y': 4.62
    }
    
    # Create sample venue metrics
    venue_metrics = [
        {
            'name': 'Venue1',
            'fill_rate': 0.95,
            'avg_slippage': 0.0002,
            'avg_latency': 50,
            'cost_score': 0.3,
            'reliability': 0.98
        },
        {
            'name': 'Venue2',
            'fill_rate': 0.90,
            'avg_slippage': 0.0003,
            'avg_latency': 30,
            'cost_score': 0.4,
            'reliability': 0.95
        }
    ]
    
    # Create sample execution data
    execution_data = {
        'venue': 'Venue1',
        'start_time': datetime.now() - timedelta(minutes=5),
        'end_time': datetime.now(),
        'order_size': 1000,
        'filled_size': 950,
        'limit_price': 1.1015,
        'average_price': 1.1013,
        'arrival_price': 1.1010,
        'side': 'buy'
    }
    
    return {
        'order_book': order_book,
        'news_data': news_data,
        'social_data': social_data,
        'rates_data': rates_data,
        'yield_data': yield_data,
        'venue_metrics': venue_metrics,
        'execution_data': execution_data,
        'base_currency': 'EUR',
        'quote_currency': 'USD'
    }


def run_manual_integration() -> Dict[str, Any]:
    """
    Run all tiers manually to demonstrate the data flow
    
    This approach gives you full control over each tier's processing
    and allows for custom logic between tiers.
    """
    logger.info("Running manual integration")
    
    # Load sample data
    market_data = load_sample_data()
    additional_inputs = create_sample_additional_inputs()
    
    # Initialize all tiers
    tier1 = Tier1TechnicalAnalysis()
    tier2 = Tier2OrderFlowIntelligence()
    tier3 = Tier3MarketStructure()
    tier4 = Tier4RegimeDetection()
    tier5 = Tier5SentimentAnalysis()
    tier6 = Tier6MacroAnalysis()
    tier7 = Tier7RiskManagement()
    tier8 = Tier8ExecutionIntelligence()
    tier9 = Tier9MetaLearning()
    
    # Initialize all tiers
    for tier in [tier1, tier2, tier3, tier4, tier5, tier6, tier7, tier8, tier9]:
        if not tier.initialize():
            logger.error(f"Failed to initialize {tier.name}")
            return {"error": f"Failed to initialize {tier.name}"}
    
    # Process through each tier sequentially
    logger.info("Processing Tier 1: Technical Analysis")
    t1_output = tier1.process(market_data)
    
    logger.info("Processing Tier 2: Order Flow Intelligence")
    t2_output = tier2.process(market_data, t1_output, additional_inputs)
    
    logger.info("Processing Tier 3: Market Structure")
    t3_output = tier3.process(market_data, t2_output, additional_inputs)
    
    logger.info("Processing Tier 4: Regime Detection")
    t4_output = tier4.process(market_data, t3_output, additional_inputs)
    
    logger.info("Processing Tier 5: Sentiment Analysis")
    t5_output = tier5.process(market_data, t4_output, additional_inputs)
    
    logger.info("Processing Tier 6: Macro Analysis")
    t6_output = tier6.process(market_data, t5_output, additional_inputs)
    
    logger.info("Processing Tier 7: Risk Management")
    t7_output = tier7.process(market_data, t6_output, additional_inputs)
    
    logger.info("Processing Tier 8: Execution Intelligence")
    t8_output = tier8.process(market_data, t7_output, additional_inputs)
    
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
    
    # Create sample timeframe data
    timeframe_data = {
        '1m': {'signal': t1_output.signal_value * 0.9, 'confidence': t1_output.confidence * 0.9},
        '5m': {'signal': t1_output.signal_value * 1.1, 'confidence': t1_output.confidence * 1.1},
        '15m': {'signal': t1_output.signal_value * 1.0, 'confidence': t1_output.confidence * 1.0},
        '1h': {'signal': t1_output.signal_value * 1.2, 'confidence': t1_output.confidence * 1.2},
        '4h': {'signal': t1_output.signal_value * 0.8, 'confidence': t1_output.confidence * 0.8}
    }
    
    # Add to additional inputs
    additional_inputs['tier_outputs'] = tier_outputs
    additional_inputs['timeframe_data'] = timeframe_data
    
    logger.info("Processing Tier 9: Meta-Learning")
    t9_output = tier9.process(market_data, t8_output, additional_inputs)
    
    # Collect all outputs
    all_outputs = {
        'tier1': t1_output,
        'tier2': t2_output,
        'tier3': t3_output,
        'tier4': t4_output,
        'tier5': t5_output,
        'tier6': t6_output,
        'tier7': t7_output,
        'tier8': t8_output,
        'tier9': t9_output
    }
    
    return all_outputs


def run_alpha_brain_integration() -> Dict[str, Any]:
    """
    Run integration using the AlphaBrain class
    
    This approach uses the built-in AlphaBrain class to handle
    the tier initialization and processing flow.
    """
    logger.info("Running AlphaBrain integration")
    
    # Load sample data
    market_data = load_sample_data()
    additional_inputs = create_sample_additional_inputs()
    
    # Initialize AlphaBrain
    brain = AlphaBrain()
    if not brain.initialize_tiers():
        logger.error("Failed to initialize AlphaBrain tiers")
        return {"error": "Failed to initialize AlphaBrain tiers"}
    
    # Process market data
    decision = brain.process_market_data(market_data, additional_inputs)
    
    # Get explanation
    explanation = brain.get_explanation()
    
    return {
        'decision': decision,
        'explanation': explanation
    }


def run_elite_brain_controller() -> Dict[str, Any]:
    """
    Run integration using the EliteBrainController
    
    This approach uses the high-level EliteBrainController which provides
    additional features like visualization and state management.
    """
    logger.info("Running EliteBrainController integration")
    
    # Load sample data
    market_data = load_sample_data()
    additional_inputs = create_sample_additional_inputs()
    
    # Initialize Elite Brain Controller
    controller = EliteBrainController()
    if not controller.initialize():
        logger.error("Failed to initialize Elite Brain Controller")
        return {"error": "Failed to initialize Elite Brain Controller"}
    
    # Process market data
    decision = controller.process_market_data(market_data, additional_inputs)
    
    # Get explanation
    explanation = controller.get_explanation()
    
    # Visualize decision (save to file)
    controller.visualize_decision(market_data, save_path="elite_brain_decision.png")
    
    return {
        'decision': decision,
        'explanation': explanation
    }


def print_decision_summary(decision: Dict[str, Any]) -> None:
    """Print a summary of the trading decision"""
    logger.info("\n=== AlphaAlgo Elite Brain Decision ===")
    logger.info(f"Decision: {decision['decision']}")
    logger.info(f"Confidence: {decision['confidence']:.2%}")
    
    if 'explanation' in decision:
        logger.info("\n=== Decision Explanation ===")
        logger.info("Top factors:")
        for factor, value in sorted(
            decision['explanation'].get('shap_values', {}).items(), 
            key=lambda x: abs(x[1]), 
            reverse=True
        )[:5]:
            logger.info(f"- {factor}: {value:.4f}")


if __name__ == "__main__":
    logger.info("=== AlphaAlgo Brain Integration Example ===")
    
    # Choose integration method
    integration_method = "elite_controller"  # Options: manual, alpha_brain, elite_controller
    
    if integration_method == "manual":
        outputs = run_manual_integration()
        final_decision = outputs.get('tier9')
        if final_decision:
            print_decision_summary({
                'decision': final_decision.final_decision,
                'confidence': final_decision.confidence,
                'explanation': final_decision.explanation
            })
    
    elif integration_method == "alpha_brain":
        result = run_alpha_brain_integration()
        if 'decision' in result:
            print_decision_summary(result['explanation'])
    
    else:  # elite_controller
        result = run_elite_brain_controller()
        if 'decision' in result:
            print_decision_summary(result['decision'])
    
    logger.info("\n=== Integration Complete ===")
