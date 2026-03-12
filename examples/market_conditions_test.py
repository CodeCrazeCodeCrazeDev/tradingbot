#!/usr/bin/env python
"""
Market Conditions Test

This script tests the trading system's ability to handle various market conditions:
- High volatility
- Low liquidity
- Market gaps
- News events
- System stress
"""

import asyncio
import logging
import yaml
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pathlib import Path

from trading_bot.core.survival_core import SurvivalCore
import numpy
import pandas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("market_conditions_test.log")
    ]
)
logger = logging.getLogger("market_conditions_test")


async def test_high_volatility(system: SurvivalCore):
    """Test system response to high volatility"""
    logger.info("\n=== High Volatility Test ===")
    
    # Simulate increasing volatility
    volatility_levels = [0.1, 0.2, 0.3, 0.4, 0.5]  # 10% to 50% volatility
    
    for vol in volatility_levels:
        logger.info(f"\nTesting {vol:.0%} volatility:")
        
        # Calculate position size with high volatility
        position = system.execution.calculate_position_size(
            symbol="EURUSD",
            entry_price=1.1000,
            stop_loss=1.1000 * (1 - vol/10),  # Wider stop for higher volatility
            win_rate=0.5,
            reward_risk_ratio=1.5
        )
        
        # Log position details
        logger.info(f"Position Size: {position['recommended_size']:.2f}")
        logger.info(f"Risk Amount: ${position['risk_amount']:.2f}")
        
        # Check if position would be allowed
        risk_check = system.execution.check_portfolio_risk(position)
        logger.info(f"Position Allowed: {risk_check['approved']}")
        logger.info(f"Risk Level: {risk_check['risk_level']}")
        if not risk_check['approved']:
            logger.info(f"Rejection Reason: {risk_check['reason']}")


async def test_low_liquidity(system: SurvivalCore):
    """Test system response to low liquidity"""
    logger.info("\n=== Low Liquidity Test ===")
    
    # Simulate different liquidity conditions
    scenarios = [
        {
            'name': 'Normal Hours',
            'spread': 0.0002,  # 2 pips
            'slippage': 0.0001,  # 1 pip
            'execution_time': 0.1  # 100ms
        },
        {
            'name': 'Asian Session',
            'spread': 0.0004,  # 4 pips
            'slippage': 0.0002,  # 2 pips
            'execution_time': 0.2  # 200ms
        },
        {
            'name': 'Pre-Market',
            'spread': 0.0008,  # 8 pips
            'slippage': 0.0004,  # 4 pips
            'execution_time': 0.5  # 500ms
        },
        {
            'name': 'Market Close',
            'spread': 0.0010,  # 10 pips
            'slippage': 0.0005,  # 5 pips
            'execution_time': 0.8  # 800ms
        }
    ]
    
    for scenario in scenarios:
        logger.info(f"\nTesting {scenario['name']}:")
        logger.info(f"Spread: {scenario['spread']*10000:.1f} pips")
        logger.info(f"Expected Slippage: {scenario['slippage']*10000:.1f} pips")
        logger.info(f"Execution Time: {scenario['execution_time']*1000:.0f}ms")
        
        # Check if trading should be allowed
        if scenario['spread'] > system.config.get('max_spread', 0.0005):
            logger.info("Trading paused due to high spread")
            await system.pause()
        else:
            # Calculate adjusted position size
            position = system.execution.calculate_position_size(
                symbol="EURUSD",
                entry_price=1.1000,
                stop_loss=1.0990,
                win_rate=0.5,
                reward_risk_ratio=1.5
            )
            
            # Adjust size for liquidity
            position['recommended_size'] *= max(0.2, 1 - scenario['spread']*1000)
            
            logger.info(f"Adjusted Position Size: {position['recommended_size']:.2f}")


async def test_market_gaps(system: SurvivalCore):
    """Test system response to market gaps"""
    logger.info("\n=== Market Gap Test ===")
    
    # Simulate different gap scenarios
    scenarios = [
        {
            'name': 'Small Gap',
            'gap_size': 0.0020,  # 20 pips
            'direction': 1  # Up
        },
        {
            'name': 'Medium Gap',
            'gap_size': 0.0050,  # 50 pips
            'direction': -1  # Down
        },
        {
            'name': 'Large Gap',
            'gap_size': 0.0100,  # 100 pips
            'direction': 1  # Up
        }
    ]
    
    # Open test position
    base_price = 1.1000
    position = system.execution.calculate_position_size(
        symbol="EURUSD",
        entry_price=base_price,
        stop_loss=base_price - 0.0020,
        win_rate=0.5,
        reward_risk_ratio=1.5
    )
    
    system.execution.add_position(position)
    
    for scenario in scenarios:
        logger.info(f"\nTesting {scenario['name']}:")
        gap_size = scenario['gap_size']
        direction = scenario['direction']
        
        # Calculate new price after gap
        new_price = base_price + (gap_size * direction)
        logger.info(f"Price Gap: {gap_size*10000:.0f} pips {direction>0 and 'up' or 'down'}")
        logger.info(f"New Price: {new_price:.4f}")
        
        # Update market price
        await system.execution.update_market_price("EURUSD", new_price)
        
        # Get position status
        positions = system.execution.get_active_positions()
        if positions:
            pos = positions[0]
            pnl = (new_price - pos.entry_price) * pos.quantity * (1 if direction > 0 else -1)
            logger.info(f"Position P&L: ${pnl:.2f}")
            
            # Check if stop loss would be triggered
            if abs(new_price - pos.entry_price) > gap_size:
                logger.info("Stop loss would be triggered")
                await system.execution.close_position("EURUSD", new_price)


async def test_news_events(system: SurvivalCore):
    """Test system response to news events"""
    logger.info("\n=== News Event Test ===")
    
    # Simulate different news events
    events = [
        {
            'name': 'Interest Rate Decision',
            'impact': 'high',
            'volatility_increase': 0.3,
            'spread_increase': 0.0010
        },
        {
            'name': 'NFP Release',
            'impact': 'high',
            'volatility_increase': 0.5,
            'spread_increase': 0.0020
        },
        {
            'name': 'GDP Data',
            'impact': 'medium',
            'volatility_increase': 0.2,
            'spread_increase': 0.0005
        }
    ]
    
    for event in events:
        logger.info(f"\nTesting {event['name']}:")
        logger.info(f"Impact: {event['impact']}")
        logger.info(f"Expected Volatility Increase: {event['volatility_increase']*100:.0f}%")
        logger.info(f"Expected Spread Increase: {event['spread_increase']*10000:.1f} pips")
        
        # Check if trading should be paused
        if event['impact'] == 'high':
            logger.info("Pausing trading for high-impact news")
            await system.pause()
            
            # Wait for event
            await asyncio.sleep(2)
            
            # Resume trading
            await system.resume()
        else:
            # Adjust position sizing
            position = system.execution.calculate_position_size(
                symbol="EURUSD",
                entry_price=1.1000,
                stop_loss=1.0980,
                win_rate=0.45,  # Lower win rate during news
                reward_risk_ratio=1.5
            )
            
            # Reduce size for news volatility
            position['recommended_size'] *= max(0.2, 1 - event['volatility_increase'])
            
            logger.info(f"Adjusted Position Size: {position['recommended_size']:.2f}")


async def test_system_stress(system: SurvivalCore):
    """Test system under stress conditions"""
    logger.info("\n=== System Stress Test ===")
    
    # Simulate multiple simultaneous conditions
    logger.info("\nSimulating multiple stress conditions:")
    logger.info("- High volatility")
    logger.info("- Multiple rapid price updates")
    logger.info("- Multiple order requests")
    logger.info("- System resource pressure")
    
    # Start with normal conditions
    base_price = 1.1000
    
    try:
        # Simulate rapid price changes
        for i in range(100):
            # Generate random price movement
            price_change = np.random.normal(0, 0.0002)
            new_price = base_price + price_change
            
            # Update price
            await system.execution.update_market_price("EURUSD", new_price)
            
            # Occasionally try to place orders
            if i % 10 == 0:
                position = system.execution.calculate_position_size(
                    symbol="EURUSD",
                    entry_price=new_price,
                    stop_loss=new_price - 0.0020,
                    win_rate=0.5,
                    reward_risk_ratio=1.5
                )
                
                await system.execution.place_order(
                    symbol="EURUSD",
                    order_type="market",
                    side="buy" if price_change > 0 else "sell",
                    quantity=position['recommended_size']
                )
            
            # Simulate system load
            if i % 20 == 0:
                system.monitoring.update_component_status('system', 'warning', {
                    'cpu_usage': 85,
                    'memory_usage': 80,
                    'last_update': datetime.now().isoformat()
                })
            
            await asyncio.sleep(0.1)
        
        # Get final system status
        status = system.get_system_status()
        logger.info("\nFinal System Status:")
        logger.info(f"Running: {status['system']['running']}")
        logger.info(f"Error Count: {status['system']['error_count']}")
        logger.info(f"Active Positions: {len(status['portfolio']['positions'])}")
        
    except Exception as e:
        logger.error(f"Error during stress test: {e}")
        await system.emergency_stop()


async def main():
    """Main function"""
    logger.info("Starting Market Conditions Test")
    
    try:
        # Load configuration
        config_path = Path("config/survival_config.yaml")
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Create survival system
        system = SurvivalCore(config)
        
        # Start system
        await system.start()
        logger.info("Trading system started")
        
        try:
            # Run tests
            await test_high_volatility(system)
            await test_low_liquidity(system)
            await test_market_gaps(system)
            await test_news_events(system)
            await test_system_stress(system)
            
        finally:
            # Stop system
            await system.stop()
            logger.info("Trading system stopped")
        
    except Exception as e:
        logger.exception(f"Error in test: {e}")
    
    logger.info("Market Conditions Test completed")


if __name__ == "__main__":
    asyncio.run(main())
