"""
Elite Trading Bot - Brain Trader
Integrates the Brain Architecture with Exchange Connectors for Live Trading
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import json
import os
import time
import pandas as pd
import numpy as np

from trading_bot.brain.brain_architecture import EliteBrain
from trading_bot.connectors.binance_connector import BinanceConnector
from trading_bot.dashboard.strategy_dashboard import StrategyDashboard
from trading_bot.execution.market_impact import MarketImpactModel
from trading_bot.risk.advanced_risk_manager import AdvancedRiskManager

logger = logging.getLogger(__name__)


class BrainTrader:
    """
    Elite Brain Trader - Integrates Brain Architecture with Exchange Connectors
    
    Features:
    - Live trading with Binance
    - Real-time market data processing
    - Advanced risk management
    - Performance tracking
    - Automatic trade execution
    """
    
    def __init__(self, config_path: str = 'config/elite_config.yaml'):
        """Initialize the Brain Trader"""
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.brain = EliteBrain()
        self.dashboard = StrategyDashboard(self.config.get('dashboard_config'))
        self.risk_manager = AdvancedRiskManager(self.config.get('risk_manager_config'))
        self.market_impact = MarketImpactModel(self.config.get('market_impact_config'))
        
        # Initialize exchange connector
        connector_config = self.config.get('connector_config', {})
        self.connector = BinanceConnector(connector_config)
        
        # Trading settings
        self.symbols = self.config.get('symbols', ['BTC/USDT', 'ETH/USDT'])
        self.timeframes = self.config.get('timeframes', ['1m', '5m', '15m', '1h', '4h', '1d'])
        self.primary_timeframe = self.config.get('primary_timeframe', '5m')
        self.account_size = self.config.get('account_size', 10000.0)  # USDT
        self.max_position_size = self.config.get('max_position_size', 0.1)  # 10% of account
        
        # Trading state
        self.positions = {}
        self.orders = {}
        self.market_data = {}
        self.last_decision_time = {}
        self.decision_interval = self.config.get('decision_interval_minutes', 5)  # minutes
        
        # Control flags
        self.running = False
        self.paused = False
        self.emergency_stop = False
        
        logger.info("Brain Trader initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.warning(f"Error loading configuration: {e}")
            return {}
    
    async def start(self):
        """Start the Brain Trader"""
        if self.running:
            logger.warning("Brain Trader is already running")
            return
        
        self.running = True
        self.paused = False
        self.emergency_stop = False
        
        # Start dashboard
        self.dashboard.start()
        
        # Connect to exchange
        await self.connector.connect()
        
        # Subscribe to market data
        await self.connector.subscribe_market_data(self.symbols)
        await self.connector.subscribe_order_book(self.symbols)
        await self.connector.subscribe_trades(self.symbols)
        
        # Register event handlers
        self.connector.register_event_handler('market_data', self._handle_market_data)
        self.connector.register_event_handler('trade', self._handle_trade)
        self.connector.register_event_handler('order_book', self._handle_order_book)
        
        # Get account balance
        await self._update_account_balance()
        
        logger.info("Brain Trader started")
        
        try:
            # Main trading loop
            while self.running:
                if not self.paused and not self.emergency_stop:
                    # Process each symbol
                    for symbol in self.symbols:
                        await self._process_symbol(symbol)
                
                # Wait before next cycle
                await asyncio.sleep(60)  # Check every minute
        
        except KeyboardInterrupt:
            logger.info("Brain Trader stopped by user")
        except Exception as e:
            logger.error(f"Error in Brain Trader: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the Brain Trader"""
        if not self.running:
            return
        
        self.running = False
        
        # Close positions if configured
        if self.config.get('close_positions_on_stop', True):
            await self._close_all_positions()
        
        # Disconnect from exchange
        await self.connector.disconnect()
        
        # Save trading data
        self._save_trading_data()
        
        logger.info("Brain Trader stopped")
    
    async def pause(self):
        """Pause trading"""
        self.paused = True
        logger.info("Trading paused")
    
    async def resume(self):
        """Resume trading"""
        self.paused = False
        logger.info("Trading resumed")
    
    async def emergency_stop_trading(self):
        """Emergency stop all trading"""
        self.emergency_stop = True
        logger.warning("EMERGENCY STOP ACTIVATED")
        
        # Close all positions
        await self._close_all_positions()
    
    async def _process_symbol(self, symbol: str):
        """Process a symbol for trading"""
        # Check if we have market data for this symbol
        if symbol not in self.market_data:
            logger.debug(f"No market data for {symbol} yet")
            return
        
        # Check if it's time to make a new decision
        now = datetime.now()
        if symbol in self.last_decision_time:
            time_since_last = now - self.last_decision_time[symbol]
            if time_since_last.total_seconds() < self.decision_interval * 60:
                return
        
        # Make trading decision
        decision = await self._make_trading_decision(symbol)
        if not decision:
            return
        
        # Execute decision
        await self._execute_decision(decision)
        
        # Update last decision time
        self.last_decision_time[symbol] = now
    
    async def _make_trading_decision(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Make a trading decision using the brain"""
        try:
            # Get market data for all timeframes
            market_data = self._get_market_data_for_timeframes(symbol)
            if not market_data:
                return None
            
            # Make decision with brain
            decision = await self.brain.make_decision(symbol, self.primary_timeframe)
            if not decision:
                return None
            
            # Enhance decision with current market data
            decision['current_price'] = market_data.get(self.primary_timeframe, {}).get('close', 0)
            
            # Calculate position size
            position_size = await self._calculate_position_size(symbol, decision)
            decision['position_size'] = position_size
            
            logger.info(f"Decision for {symbol}: {decision['action']} {position_size} @ {decision['current_price']} (confidence: {decision['confidence']:.2f})")
            
            return decision
        
        except Exception as e:
            logger.error(f"Error making trading decision for {symbol}: {e}")
            return None
    
    async def _execute_decision(self, decision: Dict[str, Any]):
        """Execute a trading decision"""
        symbol = decision['symbol']
        action = decision['action']
        position_size = decision['position_size']
        current_price = decision['current_price']
        
        # Skip if no action or tiny position
        if action == 'neutral' or abs(position_size) < 0.0001:
            return
        
        # Check current position
        current_position = self.positions.get(symbol, 0)
        
        # Determine order type
        if action == 'buy':
            if current_position < 0:  # Currently short
                # Close short position first
                await self._place_order(symbol, 'buy', abs(current_position), current_price)
                # Then open long position
                await self._place_order(symbol, 'buy', position_size, current_price)
            else:
                # Open or increase long position
                await self._place_order(symbol, 'buy', position_size, current_price)
        
        elif action == 'sell':
            if current_position > 0:  # Currently long
                # Close long position first
                await self._place_order(symbol, 'sell', current_position, current_price)
                # Then open short position
                await self._place_order(symbol, 'sell', position_size, current_price)
            else:
                # Open or increase short position
                await self._place_order(symbol, 'sell', position_size, current_price)
    
    async def _place_order(self, symbol: str, side: str, quantity: float, price: float):
        """Place an order on the exchange"""
        try:
            # Check for market impact
            impact = self.market_impact.estimate_market_impact(
                symbol=symbol,
                order_size=quantity,
                side=side,
                market_data={'price': price, 'adv': self.market_data.get(symbol, {}).get('volume', 1000)}
            )
            
            # Use optimal execution if impact is high
            if impact.get('market_impact_bps', 0) > 50:  # More than 50 bps impact
                logger.info(f"Using optimal execution for {symbol} due to high market impact")
                
                execution_plan = self.market_impact.optimize_execution(
                    symbol=symbol,
                    order_size=quantity,
                    side=side,
                    market_data={'price': price}
                )
                
                # Execute each chunk
                for chunk in execution_plan['execution_schedule']:
                    # Place order for chunk
                    order = {
                        'symbol': symbol,
                        'side': side,
                        'type': 'LIMIT',
                        'quantity': chunk['size'],
                        'price': chunk['executed_price'],
                        'time_in_force': 'GTC'
                    }
                    
                    result = await self.connector.place_order(order)
                    
                    # Update positions
                    self._update_position(symbol, side, chunk['size'], chunk['executed_price'])
                    
                    # Wait between chunks
                    await asyncio.sleep(chunk['execution_time'] * 60)  # Convert hours to minutes
            else:
                # Place single order
                order = {
                    'symbol': symbol,
                    'side': side,
                    'type': 'LIMIT',
                    'quantity': quantity,
                    'price': price,
                    'time_in_force': 'GTC'
                }
                
                result = await self.connector.place_order(order)
                
                # Update positions
                self._update_position(symbol, side, quantity, price)
        
        except Exception as e:
            logger.error(f"Error placing order for {symbol}: {e}")
    
    def _update_position(self, symbol: str, side: str, quantity: float, price: float):
        """Update position after order execution"""
        if symbol not in self.positions:
            self.positions[symbol] = 0
        
        # Update position
        if side == 'buy':
            self.positions[symbol] += quantity
        else:  # sell
            self.positions[symbol] -= quantity
        
        # Update dashboard
        self.dashboard.add_trade({
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'timestamp': datetime.now(),
            'value': quantity * price
        })
    
    async def _close_all_positions(self):
        """Close all open positions"""
        for symbol, position in self.positions.items():
            if position != 0:
                side = 'sell' if position > 0 else 'buy'
                quantity = abs(position)
                
                # Get current price
                price = self.market_data.get(symbol, {}).get('close', 0)
                if price == 0:
                    # Fallback to getting ticker
                    ticker = await self.connector.get_ticker(symbol)
                    price = ticker.last
                
                logger.info(f"Closing position: {side} {quantity} {symbol} @ {price}")
                
                # Place order
                await self._place_order(symbol, side, quantity, price)
    
    async def _update_account_balance(self):
        """Update account balance"""
        try:
            balance = await self.connector.get_balance()
            
            # Update account size
            if 'total_btc' in balance:
                # Convert BTC value to USDT
                ticker = await self.connector.get_ticker('BTC/USDT')
                self.account_size = float(balance['total_btc']) * ticker.last
            
            # Update positions
            positions = await self.connector.get_positions()
            for position in positions:
                asset = position['asset']
                for symbol in self.symbols:
                    if asset in symbol:
                        self.positions[symbol] = position['total']
            
            logger.info(f"Account balance updated: {self.account_size:.2f} USDT")
            
        except Exception as e:
            logger.error(f"Error updating account balance: {e}")
    
    async def _handle_market_data(self, data):
        """Handle market data updates"""
        symbol = data.symbol
        timestamp = data.timestamp
        
        # Store market data
        if symbol not in self.market_data:
            self.market_data[symbol] = {}
        
        # Update market data
        self.market_data[symbol] = {
            'timestamp': timestamp,
            'open': data.open,
            'high': data.high,
            'low': data.low,
            'close': data.close,
            'volume': data.volume
        }
        
        # Update dashboard
        self.dashboard.update_metric(f"{symbol}_price", data.close)
    
    async def _handle_trade(self, trade):
        """Handle trade updates"""
        # Process trade data if needed
        pass
    
    async def _handle_order_book(self, order_book):
        """Handle order book updates"""
        # Process order book data if needed
        pass
    
    def _get_market_data_for_timeframes(self, symbol: str) -> Dict[str, Dict[str, float]]:
        """Get market data for all timeframes"""
        if symbol not in self.market_data:
            return {}
        
        # In a real implementation, this would aggregate data for different timeframes
        # For now, we'll just duplicate the data for all timeframes
        result = {}
        for timeframe in self.timeframes:
            result[timeframe] = self.market_data[symbol]
        
        return result
    
    async def _calculate_position_size(self, symbol: str, decision: Dict[str, Any]) -> float:
        """Calculate position size based on risk management"""
        action = decision['action']
        confidence = decision['confidence']
        current_price = decision['current_price']
        
        if action == 'neutral':
            return 0.0
        
        # Get risk level based on market regime
        risk_level = 'normal'
        if 'signals' in decision and 'market_regime' in decision['signals']:
            regime = decision['signals']['market_regime']
            if 'bull' in regime.lower():
                risk_level = 'high'
            elif 'bear' in regime.lower():
                risk_level = 'low'
            elif 'volatile' in regime.lower():
                risk_level = 'low'
        
        # Calculate position size using risk manager
        position = self.risk_manager.calculate_position_size(
            symbol=symbol,
            account_size=self.account_size,
            risk_level=risk_level,
            win_rate=0.55,  # Default win rate
            win_loss_ratio=1.5  # Default win/loss ratio
        )
        
        # Scale by confidence
        position_size = position['position_size'] * confidence
        
        # Cap at max position size
        max_size = self.account_size * self.max_position_size / current_price
        position_size = min(position_size, max_size)
        
        return position_size
    
    def _save_trading_data(self):
        """Save trading data to file"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Save positions
            with open('data/positions.json', 'w') as f:
                json.dump(self.positions, f, indent=2)
            
            # Save market data
            with open('data/market_data.json', 'w') as f:
                # Convert datetime to string
                serializable_data = {}
                for symbol, data in self.market_data.items():
                    serializable_data[symbol] = {
                        k: v.isoformat() if isinstance(v, datetime) else v
                        for k, v in data.items()
                    }
                json.dump(serializable_data, f, indent=2)
            
            logger.info("Trading data saved")
            
        except Exception as e:
            logger.error(f"Error saving trading data: {e}")


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create brain trader
    trader = BrainTrader()
    
    # Run trader
    asyncio.run(trader.start())
