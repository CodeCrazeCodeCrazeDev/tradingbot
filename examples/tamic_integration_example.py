"""
TAMIC Integration Example

This script demonstrates how to integrate the Time-Aware Market Intelligence and Control (TAMIC)
system with AlphaAlgo Core's Capital Governance System.
"""

import asyncio
import logging
import sys
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import AlphaAlgo Core components
from trading_bot.alphaalgo_core.capital_governance import CapitalGovernanceSystem
from trading_bot.alphaalgo_core.market_physics_filter import MarketPhysicsFilter

# Import TAMIC components
from trading_bot.tamic import (
    TimeHorizon,
    MarketTimeState,
    TAMICIntegration
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def generate_sample_market_data(symbol: str) -> Dict[str, Any]:
    """
    Generate sample market data for demonstration.
    
    Args:
        symbol: Market symbol
        
    Returns:
        Sample market data
    """
    import numpy as np
    import pandas as pd
    
    # Generate sample OHLCV data
    n_periods = 100
    close = np.random.normal(100, 1, n_periods).cumsum()
    high = close + np.random.uniform(0, 2, n_periods)
    low = close - np.random.uniform(0, 2, n_periods)
    open_prices = close - np.random.uniform(-1, 1, n_periods)
    volume = np.random.uniform(1000, 5000, n_periods)
    
    # Calculate some derived metrics
    volatility = np.std(np.diff(close) / close[:-1]) * np.sqrt(252)
    liquidity = np.mean(volume) / 1000
    
    # Create market data dictionary
    market_data = {
        "symbol": symbol,
        "timestamp": time.time(),
        "open": open_prices.tolist(),
        "high": high.tolist(),
        "low": low.tolist(),
        "close": close.tolist(),
        "volume": volume.tolist(),
        "volatility": volatility,
        "liquidity": liquidity,
        "spread": 0.01,
        "market_regime": "trending",
        "correlation": {
            "spy": 0.7,
            "qqq": 0.8
        }
    }
    
    return market_data


async def generate_sample_strategy_config() -> Dict[str, Any]:
    """
    Generate sample strategy configuration for demonstration.
    
    Returns:
        Sample strategy configuration
    """
    return {
        "strategy_id": "momentum_strategy_001",
        "strategy_type": "momentum",
        "time_horizon": "intraday",
        "risk_limit": 0.02,
        "max_exposure": 0.5,
        "parameters": {
            "lookback_periods": 20,
            "entry_threshold": 0.5,
            "exit_threshold": -0.2
        }
    }


async def run_tamic_standalone_example():
    """Run TAMIC standalone example"""
    logger.info("Running TAMIC standalone example")
    
    # Import TAMIC
    from trading_bot.tamic import TAMIC, create_tamic, quick_start
    
    # Create TAMIC instance with quick start
    tamic = await quick_start()
    
    # Generate sample market data
    symbol = "AAPL"
    market_data = await generate_sample_market_data(symbol)
    
    # Evaluate market with TAMIC
    decision = await tamic.evaluate_market(
        symbol=symbol,
        horizon=TimeHorizon.INTRADAY,
        market_data=market_data
    )
    
    # Print decision
    logger.info(f"TAMIC Decision for {symbol}:")
    logger.info(f"  Trade recommended: {decision.is_trade_recommended}")
    logger.info(f"  Confidence level: {decision.confidence_level:.2f}")
    logger.info(f"  Exposure recommendation: {decision.exposure_recommendation:.2f}")
    logger.info(f"  Market time state: {decision.market_time_state.value}")
    logger.info(f"  Signal half-life: {decision.signal_half_life.value}")
    
    if not decision.is_trade_recommended:
        logger.info(f"  No trade reason: {decision.no_trade_reason}")
    
    return decision


async def run_tamic_integration_example():
    """Run TAMIC integration with AlphaAlgo Core example"""
    logger.info("Running TAMIC integration with AlphaAlgo Core example")
    
    # Create Capital Governance System
    capital_governance = CapitalGovernanceSystem()
    
    # Add Market Physics Filter (Layer 0)
    market_physics = MarketPhysicsFilter()
    capital_governance.add_layer("market_physics_filter", market_physics)
    
    # Integrate TAMIC with Capital Governance System
    tamic_layer = await TAMICIntegration.integrate_with_capital_governance(capital_governance)
    
    # Generate sample market data and strategy config
    symbol = "AAPL"
    market_data = await generate_sample_market_data(symbol)
    strategy_config = await generate_sample_strategy_config()
    strategy_id = strategy_config["strategy_id"]
    
    # Evaluate tradability with Capital Governance System
    result = await capital_governance.evaluate_tradability(
        strategy_id=strategy_id,
        symbol=symbol,
        market_data=market_data,
        strategy_config=strategy_config
    )
    
    # Print result
    logger.info(f"Capital Governance Result for {symbol} with {strategy_id}:")
    logger.info(f"  Is tradable: {result.is_tradable}")
    logger.info(f"  Max exposure: {result.max_exposure:.2f}")
    logger.info(f"  Reason: {result.reason}")
    
    # Access TAMIC-specific metrics if available
    if hasattr(result, "tamic_governance_layer") and result.tamic_governance_layer:
        tamic_result = result.tamic_governance_layer
        logger.info(f"  TAMIC confidence level: {tamic_result.confidence_level:.2f}")
        logger.info(f"  TAMIC market time state: {tamic_result.market_time_state.value}")
    
    return result


async def main():
    """Main function"""
    logger.info("Starting TAMIC integration example")
    
    # Run standalone example
    await run_tamic_standalone_example()
    
    # Run integration example
    await run_tamic_integration_example()
    
    logger.info("TAMIC integration example completed")


if __name__ == "__main__":
    asyncio.run(main())
