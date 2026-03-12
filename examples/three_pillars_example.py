#!/usr/bin/env python
"""
Three Pillars Example

This script demonstrates how to use the three pillars of the Elite Trading System:
Analysis, Execution, and Monitoring.
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Import core components
from trading_bot.core.analysis_orchestrator import AnalysisOrchestrator, Signal, MarketContext
from trading_bot.core.execution_manager import ExecutionManager, Order, OrderType, OrderStatus
from trading_bot.core.monitoring_system import MonitoringSystem
import numpy
import pandas

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("three_pillars_example")

# Sample OHLCV data generator
def generate_sample_data(symbol="EURUSD", periods=100, volatility=0.001):
    """Generate sample OHLCV data"""
    np.random.seed(42)  # For reproducibility
    
    # Start with a base price
    base_price = 1.1000
    
    # Generate random price movements
    returns = np.random.normal(0, volatility, periods)
    prices = base_price * np.exp(np.cumsum(returns))
    
    # Generate OHLCV data
    data = []
    now = datetime.now()
    
    for i in range(periods):
        timestamp = now - timedelta(minutes=periods-i)
        close = prices[i]
        high = close * (1 + np.random.uniform(0, 0.0015))
        low = close * (1 - np.random.uniform(0, 0.0015))
        open_price = prices[i-1] if i > 0 else close * (1 - np.random.uniform(-0.001, 0.001))
        volume = np.random.randint(10, 100)
        
        data.append({
            "time": timestamp,
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume
        })
    
    return pd.DataFrame(data)

# Example trade processor
async def process_trade(execution_manager, monitoring_system, symbol, entry_price, exit_price, 
                       quantity, entry_time, exit_time, side="buy"):
    """Process a completed trade"""
    # Calculate P&L
    if side.lower() == "buy":
        pnl = (exit_price - entry_price) * quantity
    else:
        pnl = (entry_price - exit_price) * quantity
    
    # Create trade record
    trade = {
        "symbol": symbol,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "quantity": quantity,
        "entry_time": entry_time,
        "exit_time": exit_time,
        "side": side,
        "pnl": pnl,
        "commission": 0.0,
        "strategy": "example_strategy"
    }
    
    # Add trade to monitoring system
    monitoring_system.add_trade(trade)
    
    logger.info(f"Processed trade: {symbol} {side} {quantity} @ {entry_price}->{exit_price}, P&L: {pnl:.2f}")

# Main example function
async def run_example():
    """Run the three pillars example"""
    logger.info("Starting Three Pillars Example")
    
    # Initialize components
    analysis = AnalysisOrchestrator()
    execution = ExecutionManager()
    monitoring = MonitoringSystem()
    
    # Update component status in monitoring system
    monitoring.update_component_status("analysis", "ok", {"initialized": True})
    monitoring.update_component_status("execution", "ok", {"initialized": True})
    monitoring.update_component_status("data_feed", "ok", {"initialized": True})
    
    # Generate sample data
    symbol = "EURUSD"
    data = generate_sample_data(symbol, periods=100)
    logger.info(f"Generated sample data for {symbol}: {len(data)} periods")
    
    # Analyze market and generate signals
    context = await analysis.analyze_market(symbol, "M15", data)
    signals = await analysis.generate_signals(symbol, "M15", data)
    
    logger.info(f"Generated {len(signals)} signals for {symbol}")
    
    # Process signals
    for i, signal in enumerate(signals):
        logger.info(f"Signal {i+1}: {signal}")
        
        # Place order based on signal
        side = "buy" if signal.direction > 0 else "sell"
        order = await execution.place_order(
            symbol=symbol,
            order_type=OrderType.MARKET,
            side=side,
            quantity=1.0,
            urgency=signal.urgency,
            market_volatility=context.volatility
        )
        
        logger.info(f"Placed order: {order.id}, Status: {order.status}")
        
        # Simulate order fill
        fill_price = data.iloc[-1]["close"]
        trade = await execution.process_fill(
            order_id=order.id,
            fill_quantity=1.0,
            fill_price=fill_price
        )
        
        logger.info(f"Filled order: {order.id} @ {fill_price}")
        
        # Simulate market movement
        new_price = fill_price * (1 + 0.002) if side == "buy" else fill_price * (1 - 0.002)
        await execution.update_market_price(symbol, new_price)
        
        # Close position
        close_order = await execution.close_position(symbol)
        
        if close_order:
            logger.info(f"Closed position with order: {close_order.id}")
            
            # Process fill for close order
            close_trade = await execution.process_fill(
                order_id=close_order.id,
                fill_quantity=1.0,
                fill_price=new_price
            )
            
            logger.info(f"Filled close order: {close_order.id} @ {new_price}")
            
            # Process completed trade
            await process_trade(
                execution_manager=execution,
                monitoring_system=monitoring,
                symbol=symbol,
                entry_price=fill_price,
                exit_price=new_price,
                quantity=1.0,
                entry_time=datetime.now() - timedelta(minutes=5),
                exit_time=datetime.now(),
                side=side
            )
    
    # Get dashboard data
    dashboard_data = monitoring.get_dashboard_data()
    
    # Print performance metrics
    logger.info("Performance Metrics:")
    for key, value in dashboard_data["performance"]["metrics"].items():
        logger.info(f"  {key}: {value}")
    
    # Print system status
    logger.info(f"System Status: {dashboard_data['system']['status']}")
    
    # Print alerts
    if dashboard_data["alerts"]:
        logger.info("Recent Alerts:")
        for alert in dashboard_data["alerts"]:
            logger.info(f"  [{alert['level']}] {alert['message']}")
    
    logger.info("Three Pillars Example completed")

# Run the example
if __name__ == "__main__":
    asyncio.run(run_example())
