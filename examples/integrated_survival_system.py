#!/usr/bin/env python
"""
Integrated Survival System Example

This script demonstrates the full integration of all survival system components:
1. Market Data & Analysis (Brain)
2. Execution (Hands)
3. Risk & Money Management (Shield)
4. Monitoring & Control (Eyes)
5. Security & Reliability (Foundation)

It simulates a complete trading session with various market conditions
and demonstrates how the system responds to different scenarios.
"""

import asyncio
import logging
import yaml
import os
import signal
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

from trading_bot.core.survival_core import SurvivalCore
from typing import Set
import numpy
import pandas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("integrated_survival_system.log")
    ]
)
logger = logging.getLogger("integrated_survival_system")


class MarketSimulator:
    """Simulates market data for testing"""
    
    def __init__(self, symbols, starting_prices=None):
        """Initialize market simulator"""
        self.symbols = symbols
        self.prices = {}
        self.volatility = {}
        self.trend = {}
        
        # Initialize prices
        for symbol in symbols:
            if starting_prices and symbol in starting_prices:
                self.prices[symbol] = starting_prices[symbol]
            else:
                # Default starting prices
                if 'JPY' in symbol:
                    self.prices[symbol] = 100.0 + random.uniform(-5, 5)
                else:
                    self.prices[symbol] = 1.0 + random.uniform(-0.1, 0.1)
            
            # Initialize volatility (annualized)
            self.volatility[symbol] = 0.10  # 10% base volatility
            
            # Initialize trend (annualized)
            self.trend[symbol] = random.uniform(-0.05, 0.05)  # -5% to +5% trend
    
    def update_prices(self, time_delta_seconds):
        """Update prices based on random walk with drift"""
        for symbol in self.symbols:
            # Convert annualized volatility to the time period
            period_volatility = self.volatility[symbol] * np.sqrt(time_delta_seconds / (365 * 24 * 3600))
            
            # Convert annualized trend to the time period
            period_trend = self.trend[symbol] * (time_delta_seconds / (365 * 24 * 3600))
            
            # Generate random price movement
            price_change = np.random.normal(period_trend, period_volatility) * self.prices[symbol]
            
            # Update price
            self.prices[symbol] += price_change
            
            # Ensure price is positive
            self.prices[symbol] = max(0.001, self.prices[symbol])
    
    def get_price(self, symbol):
        """Get current price for a symbol"""
        return self.prices.get(symbol, 0.0)
    
    def set_volatility(self, symbol, volatility):
        """Set volatility for a symbol"""
        self.volatility[symbol] = volatility
    
    def set_trend(self, symbol, trend):
        """Set trend for a symbol"""
        self.trend[symbol] = trend


class ScenarioManager:
    """Manages test scenarios for the trading system"""
    
    def __init__(self, system, market_simulator):
        """Initialize scenario manager"""
        self.system = system
        self.market = market_simulator
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def run_normal_trading(self, duration_seconds=60):
        """Run normal trading scenario"""
        self.logger.info("\n=== Normal Trading Scenario ===")
        self.logger.info(f"Duration: {duration_seconds} seconds")
        
        # Set normal market conditions
        for symbol in self.market.symbols:
            self.market.set_volatility(symbol, 0.10)  # 10% annualized volatility
            self.market.set_trend(symbol, 0.0)  # No trend
        
        # Run for specified duration
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration_seconds)
        
        while datetime.now() < end_time and self.system.running:
            # Update market prices
            self.market.update_prices(1.0)  # 1 second update
            
            # Update market data in the system
            for symbol in self.market.symbols:
                price = self.market.get_price(symbol)
                await self.system.market_data.update_price(symbol, price)
            
            # Generate trading signals
            signals = await self.system.analysis.generate_signals()
            
            # Process signals
            if signals and not self.system.paused:
                for signal in signals:
                    if signal.confidence > 70:
                        # Calculate position size
                        position = self.system.execution.calculate_position_size(
                            symbol=signal.symbol,
                            entry_price=signal.price,
                            stop_loss=signal.stop_loss,
                            win_rate=0.55,
                            reward_risk_ratio=signal.reward_risk
                        )
                        
                        # Place order
                        await self.system.execution.place_order(
                            symbol=signal.symbol,
                            order_type="market",
                            side=signal.direction,
                            quantity=position['recommended_size']
                        )
            
            # Wait for next update
            await asyncio.sleep(1.0)
        
        self.logger.info("Normal trading scenario completed")
    
    async def run_high_volatility(self, duration_seconds=60):
        """Run high volatility scenario"""
        self.logger.info("\n=== High Volatility Scenario ===")
        self.logger.info(f"Duration: {duration_seconds} seconds")
        
        # Set high volatility market conditions
        for symbol in self.market.symbols:
            self.market.set_volatility(symbol, 0.30)  # 30% annualized volatility
            self.market.set_trend(symbol, 0.0)  # No trend
        
        # Run for specified duration
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration_seconds)
        
        while datetime.now() < end_time and self.system.running:
            # Update market prices
            self.market.update_prices(1.0)  # 1 second update
            
            # Update market data in the system
            for symbol in self.market.symbols:
                price = self.market.get_price(symbol)
                await self.system.market_data.update_price(symbol, price)
            
            # Generate trading signals
            signals = await self.system.analysis.generate_signals()
            
            # Process signals
            if signals and not self.system.paused:
                for signal in signals:
                    if signal.confidence > 80:  # Higher confidence threshold in high volatility
                        # Calculate position size with reduced risk
                        position = self.system.execution.calculate_position_size(
                            symbol=signal.symbol,
                            entry_price=signal.price,
                            stop_loss=signal.stop_loss,
                            win_rate=0.50,  # Lower win rate in high volatility
                            reward_risk_ratio=signal.reward_risk
                        )
                        
                        # Reduce position size for high volatility
                        position['recommended_size'] *= 0.5
                        
                        # Place order
                        await self.system.execution.place_order(
                            symbol=signal.symbol,
                            order_type="market",
                            side=signal.direction,
                            quantity=position['recommended_size']
                        )
            
            # Wait for next update
            await asyncio.sleep(1.0)
        
        self.logger.info("High volatility scenario completed")
    
    async def run_market_crash(self, duration_seconds=60):
        """Run market crash scenario"""
        self.logger.info("\n=== Market Crash Scenario ===")
        self.logger.info(f"Duration: {duration_seconds} seconds")
        
        # Set market crash conditions
        for symbol in self.market.symbols:
            self.market.set_volatility(symbol, 0.50)  # 50% annualized volatility
            self.market.set_trend(symbol, -0.50)  # -50% annualized trend (crash)
        
        # Run for specified duration
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration_seconds)
        
        while datetime.now() < end_time and self.system.running:
            # Update market prices
            self.market.update_prices(1.0)  # 1 second update
            
            # Update market data in the system
            for symbol in self.market.symbols:
                price = self.market.get_price(symbol)
                await self.system.market_data.update_price(symbol, price)
            
            # Wait for next update
            await asyncio.sleep(1.0)
        
        self.logger.info("Market crash scenario completed")
    
    async def run_system_error(self):
        """Run system error scenario"""
        self.logger.info("\n=== System Error Scenario ===")
        
        # Simulate component errors
        components = ['market_data', 'analysis', 'execution', 'risk']
        
        for component in components:
            # Simulate error
            self.logger.info(f"Simulating error in {component} component")
            
            # Update component status
            self.system.monitoring.update_component_status(component, 'error', {
                'error': f"Simulated error in {component}",
                'timestamp': datetime.now().isoformat()
            })
            
            # Wait for recovery attempt
            await asyncio.sleep(5)
        
        self.logger.info("System error scenario completed")
    
    async def run_emergency_shutdown(self):
        """Run emergency shutdown scenario"""
        self.logger.info("\n=== Emergency Shutdown Scenario ===")
        
        # Open some test positions
        symbols = self.market.symbols[:3]  # Use first 3 symbols
        
        for symbol in symbols:
            price = self.market.get_price(symbol)
            
            # Calculate position size
            position = self.system.execution.calculate_position_size(
                symbol=symbol,
                entry_price=price,
                stop_loss=price * 0.99,  # 1% stop loss
                win_rate=0.55,
                reward_risk_ratio=1.5
            )
            
            # Add position
            self.system.execution.add_position(position)
        
        # Show positions
        positions = self.system.execution.get_active_positions()
        self.logger.info(f"Opened {len(positions)} positions")
        
        # Trigger emergency shutdown
        self.logger.info("Triggering emergency shutdown")
        await self.system.emergency_stop()
        
        self.logger.info("Emergency shutdown scenario completed")


async def main():
    """Main function"""
    logger.info("Starting Integrated Survival System Example")
    
    try:
        # Load configuration
        config_path = Path("config/survival_config.yaml")
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Override configuration for testing
        config["data_stream"]["simulate_data"] = True
        config["trading_enabled"] = True
        
        # Create survival system
        system = SurvivalCore(config)
        
        # Create market simulator
        symbols = config.get("symbols", ["EURUSD", "GBPUSD", "USDJPY"])
        market_simulator = MarketSimulator(symbols)
        
        # Create scenario manager
        scenario_manager = ScenarioManager(system, market_simulator)
        
        # Start system
        await system.start()
        logger.info("Trading system started")
        
        try:
            # Run scenarios
            await scenario_manager.run_normal_trading(duration_seconds=30)
            await scenario_manager.run_high_volatility(duration_seconds=30)
            await scenario_manager.run_market_crash(duration_seconds=30)
            await scenario_manager.run_system_error()
            await scenario_manager.run_emergency_shutdown()
            
            logger.info("All scenarios completed")
            
        finally:
            # Stop system if not already stopped by emergency shutdown
            if system.running:
                await system.stop()
                logger.info("Trading system stopped")
        
    except Exception as e:
        logger.exception(f"Error in example: {e}")
    
    logger.info("Integrated Survival System Example completed")


if __name__ == "__main__":
    # Handle keyboard interrupt
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Example interrupted by user")
