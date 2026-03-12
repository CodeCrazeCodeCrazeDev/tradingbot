#!/usr/bin/env python
"""
Survival Trading Example

This script demonstrates the survival-focused trading system that prioritizes
long-term survival and profitability through robust risk management and
comprehensive system monitoring.
"""

import asyncio
import logging
import yaml
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Import core components
from trading_bot.core.survival_core import SurvivalCore
import numpy
import pandas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("survival_trading.log")
    ]
)
logger = logging.getLogger("survival_trading")


async def simulate_market_conditions(system: SurvivalCore):
    """
    Simulate various market conditions to test system resilience
    
    Args:
        system: SurvivalCore instance
    """
    logger.info("Simulating market conditions")
    
    # Normal trading conditions
    await asyncio.sleep(5)
    logger.info("Normal trading conditions...")
    
    # Simulate high volatility
    logger.info("Simulating high volatility...")
    await system._send_notification(
        "High Volatility",
        "Market volatility has increased significantly",
        level="warning"
    )
    await asyncio.sleep(5)
    
    # Simulate API error
    logger.info("Simulating API error...")
    system.monitoring.update_component_status('market_data', 'error', {
        'error': 'API connection lost',
        'last_update': datetime.now().isoformat()
    })
    await asyncio.sleep(5)
    
    # Simulate approaching daily loss limit
    logger.info("Simulating approaching daily loss limit...")
    await system._send_notification(
        "Daily Loss Warning",
        "Approaching daily loss limit (80% of maximum)",
        level="warning"
    )
    await asyncio.sleep(5)
    
    # Simulate high spread
    logger.info("Simulating high spread...")
    await system._send_notification(
        "High Spread",
        "Spread has exceeded normal limits",
        level="warning"
    )
    await asyncio.sleep(5)
    
    # Simulate system recovery
    logger.info("Simulating system recovery...")
    system.monitoring.update_component_status('market_data', 'ok', {
        'last_update': datetime.now().isoformat()
    })
    await asyncio.sleep(5)


async def main():
    """Main function"""
    logger.info("Starting Survival Trading Example")
    
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
            # Simulate various market conditions
            await simulate_market_conditions(system)
            
            # Get system status
            status = system.get_system_status()
            
            # Print summary
            logger.info("\nSystem Status Summary:")
            logger.info(f"Running: {status['system']['running']}")
            logger.info(f"Paused: {status['system']['paused']}")
            logger.info(f"Emergency Shutdown: {status['system']['emergency_shutdown']}")
            logger.info(f"Last Health Check: {status['system']['last_health_check']}")
            logger.info(f"Error Count: {status['system']['error_count']}")
            
            logger.info("\nRisk Limits:")
            for limit, value in status['risk_limits'].items():
                logger.info(f"  {limit}: {value}")
            
            logger.info("\nPortfolio Status:")
            portfolio = status['portfolio']
            logger.info(f"Account Balance: ${portfolio['account_balance']:.2f}")
            logger.info(f"Current Drawdown: {portfolio['current_drawdown']:.2%}")
            logger.info(f"Position Count: {len(portfolio['positions'])}")
            
            # Print monitoring status
            logger.info("\nComponent Status:")
            for component, info in status['monitoring']['components'].items():
                logger.info(f"  {component}: {info['status']}")
            
        finally:
            # Stop system
            await system.stop()
            logger.info("Trading system stopped")
        
    except Exception as e:
        logger.exception(f"Error in trading system: {e}")
    
    logger.info("Survival Trading Example completed")


if __name__ == "__main__":
    asyncio.run(main())
