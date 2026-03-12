#!/usr/bin/env python
"""
Integrated Trading System Example

This script demonstrates a complete trading system that integrates all three pillars:
Analysis, Execution, and Monitoring.
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import yaml
from pathlib import Path

# Import core components
from trading_bot.core.analysis_orchestrator import AnalysisOrchestrator
from trading_bot.core.execution_manager import ExecutionManager, OrderType
from trading_bot.core.monitoring_system import MonitoringSystem
from trading_bot.core.trading_system import TradingSystem

# Import data components
from trading_bot.data.market_data_stream import MarketDataStream
from trading_bot.data.time_series_db import TimeSeriesDB
import numpy
import pandas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("integrated_system.log")
    ]
)
logger = logging.getLogger("integrated_system")

# Configuration
CONFIG = {
    "symbols": ["EURUSD", "GBPUSD", "USDJPY"],
    "timeframes": ["M5", "M15", "H1"],
    "data_update_interval": 1.0,
    "analysis_interval": 5.0,
    "trading_enabled": True,
    "risk_per_trade": 1.0,
    "max_open_trades": 5,
    "trading_hours": {
        "start": "00:00",
        "end": "23:59",
        "timezone": "UTC",
        "weekend_trading": False
    },
    "data_stream": {
        "simulate_data": True,
        "use_redis": False
    },
    "time_series_db": {
        "data_dir": "data/time_series",
        "partition_by": "day",
        "compression": "snappy",
        "cache_enabled": True
    },
    "analysis": {
        "min_confidence": 70.0,
        "signal_weights": {
            "market_structure": 0.15,
            "liquidity": 0.10,
            "order_flow": 0.15,
            "microstructure": 0.05,
            "price_action": 0.10,
            "technical": 0.15,
            "sentiment": 0.10,
            "fundamental": 0.05,
            "predictive": 0.15
        }
    },
    "execution": {
        "max_retries": 3,
        "retry_delay": 1.0,
        "smart_router": {
            "venues": [
                {
                    "id": "primary_broker",
                    "name": "Primary Broker",
                    "type": "broker",
                    "latency_ms": 15.0,
                    "cost_bps": 2.5,
                    "fill_rate": 0.98,
                    "liquidity_score": 0.9
                },
                {
                    "id": "secondary_broker",
                    "name": "Secondary Broker",
                    "type": "broker",
                    "latency_ms": 25.0,
                    "cost_bps": 2.0,
                    "fill_rate": 0.95,
                    "liquidity_score": 0.85
                }
            ]
        }
    },
    "monitoring": {
        "health": {
            "monitor_interval": 5.0,
            "cpu_limit": 80.0,
            "memory_limit": 80.0,
            "disk_limit": 80.0
        },
        "alerts": {
            "channels": ["console"]
        }
    }
}

# Save configuration to file
def save_config():
    """Save configuration to file"""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    with open(config_dir / "integrated_system.yaml", "w") as f:
        yaml.dump(CONFIG, f, default_flow_style=False)
    
    logger.info("Configuration saved to config/integrated_system.yaml")

# Main function
async def main():
    """Main function"""
    logger.info("Starting Integrated Trading System Example")
    
    # Save configuration
    save_config()
    
    # Create trading system
    trading_system = TradingSystem(CONFIG)
    
    try:
        # Start trading system
        await trading_system.start()
        logger.info("Trading system started")
        
        # Run for a while
        logger.info("Running trading system for 60 seconds...")
        await asyncio.sleep(60)
        
        # Get dashboard data
        dashboard_data = await trading_system.get_dashboard_data()
        
        # Print summary
        logger.info("Trading System Summary:")
        logger.info(f"System Status: {dashboard_data['system']['status']}")
        logger.info(f"Components:")
        for component, status in dashboard_data['system']['components'].items():
            logger.info(f"  {component}: {status['status']}")
        
        logger.info("Performance Metrics:")
        metrics = dashboard_data['performance']['metrics']
        for key, value in metrics.items():
            logger.info(f"  {key}: {value}")
        
        logger.info("Positions:")
        for position in dashboard_data['positions']:
            logger.info(f"  {position['symbol']}: {position['quantity']} @ {position['entry_price']}, P&L: {position['unrealized_pnl']}")
        
        logger.info("Recent Alerts:")
        for alert in dashboard_data['alerts']:
            logger.info(f"  [{alert['level']}] {alert['message']}")
        
    except Exception as e:
        logger.exception(f"Error in trading system: {e}")
    finally:
        # Stop trading system
        logger.info("Stopping trading system...")
        await trading_system.stop()
        logger.info("Trading system stopped")
    
    logger.info("Integrated Trading System Example completed")

# Run the example
if __name__ == "__main__":
    asyncio.run(main())
