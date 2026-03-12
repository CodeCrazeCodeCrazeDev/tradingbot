"""
Elite Trading Bot - MT5 Brain Trader
Integrates the Brain Architecture with MT5 for Forex and Stock Trading
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

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

try:
    from trading_bot.brain.brain_architecture import EliteBrain
except ImportError:
    EliteBrain = None

try:
    from trading_bot.connectors.mt5_connector import MT5Connector
except ImportError:
    MT5Connector = None

try:
    from trading_bot.dashboard.strategy_dashboard import StrategyDashboard
except ImportError:
    StrategyDashboard = None

try:
    from trading_bot.execution.market_impact import MarketImpactModel
except ImportError:
    MarketImpactModel = None

try:
    from trading_bot.risk.advanced_risk_manager import AdvancedRiskManager
except ImportError:
    AdvancedRiskManager = None

try:
    from trading_bot.advanced_features.quantum_computing import QuantumTradingSystem, QuantumOptimizationEngine
except ImportError:
    QuantumTradingSystem = None
    QuantumOptimizationEngine = None

try:
    from trading_bot.advanced_features.blockchain_validation import TradingPredictionSystem, BlockchainValidationSystem
except ImportError:
    TradingPredictionSystem = None
    BlockchainValidationSystem = None

logger = logging.getLogger(__name__)


class MT5BrainTrader:
    """
    Elite Brain Trader for MT5 - Integrates Brain Architecture with MT5 platform
    
    Features:
    - Forex and stock trading with MT5
    - Real-time market data processing
    - Advanced risk management
    - Performance tracking
    - Automatic trade execution
    - Quantum portfolio optimization
    - Blockchain validation for trade verification
    """
    
    def __init__(self, config_path: str = 'config/elite_mt5_config.yaml'):
        """Initialize the MT5 Brain Trader"""
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.brain = EliteBrain()
        self.dashboard = StrategyDashboard(self.config.get('dashboard_config'))
        self.risk_manager = AdvancedRiskManager(self.config.get('risk_manager_config'))
        self.market_impact = MarketImpactModel(self.config.get('market_impact_config'))
        self.quantum_optimizer = QuantumOptimizationEngine()
        self.blockchain_validator = BlockchainValidationSystem()
        
        # Initialize MT5 connector
        connector_config = self.config.get('connector_config', {})
        self.connector = MT5Connector(connector_config)
        
        # Trading settings
        self.symbols = self.config.get('symbols', ['EUR/USD', 'GBP/USD', 'USD/JPY', 'GOLD'])
        self.timeframes = self.config.get('timeframes', ['M1', 'M5', 'M15', 'H1', 'H4', 'D1'])
        self.primary_timeframe = self.config.get('primary_timeframe', 'M5')
        self.account_size = self.config.get('account_size', 10000.0)
        self.max_position_size = self.config.get('max_position_size', 0.1)  # 10% of account
        
        # Trading state
        self.positions = {}
        self.orders = {}
        self.market_data = {}
        self.last_decision_time = {}
        self.decision_interval = self.config.get('decision_interval_minutes', 5)  # minutes
        
        # Historical data cache
        self.historical_data = {}
        
        # Control flags
        self.running = False
        self.paused = False
        self.emergency_stop = False
        
        # Performance metrics
        self.metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'max_drawdown': 0.0,
            'current_drawdown': 0.0,
            'peak_equity': 0.0
        }
        
        logger.info("MT5 Brain Trader initialized")
    
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
        """Start the MT5 Brain Trader"""
        if self.running:
            logger.warning("MT5 Brain Trader is already running")
            return
        
        self.running = True
        self.paused = False
        self.emergency_stop = False
        
        # Start dashboard
        self.dashboard.start()
        
        # Connect to MT5
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
        
        # Initialize historical data
        await self._initialize_historical_data()
        
        logger.info("MT5 Brain Trader started")
        
        try:
            # Main trading loop
            while self.running:
                if not self.paused and not self.emergency_stop:
                    # Process each symbol
                    for symbol in self.symbols:
                        await self._process_symbol(symbol)
                
                # Update dashboard metrics
                await self._update_dashboard_metrics()
                
                # Wait before next cycle
                await asyncio.sleep(60)  # Check every minute
        
        except KeyboardInterrupt:
            logger.info("MT5 Brain Trader stopped by user")
        except Exception as e:
            logger.error(f"Error in MT5 Brain Trader: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the MT5 Brain Trader"""
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
        
        logger.info("MT5 Brain Trader stopped")
    
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
            market_data = await self._get_market_data_for_timeframes(symbol)
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
            
            # Record prediction with blockchain
            await self.blockchain_validator.record_prediction(
                symbol=symbol,
                prediction={'action': decision['action'], 'confidence': decision['confidence']},
                confidence=decision['confidence']
            )
            
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
        positions = await self.connector.get_positions()
        current_position = 0
        
        for pos in positions:
            if pos['symbol'] == self.connector.normalize_symbol(symbol):
                if pos['type'] == 'buy':
                    current_position += pos['volume']
                else:
                    current_position -= pos['volume']
        
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
        """Place an order on MT5"""
        try:
            # Calculate stop loss and take profit
            sl, tp = await self._calculate_stop_loss_take_profit(symbol, side, price)
            
            # Create order
            order = {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'stop_loss': sl,
                'take_profit': tp,
                'comment': 'Elite Brain Trader'
            }
            
            # Place order
            result = await self.connector.place_order(order)
            
            # Log order
            logger.info(f"Order placed: {side} {quantity} {symbol} @ {price} (SL: {sl}, TP: {tp})")
            
            # Update metrics
            self.metrics['total_trades'] += 1
            
            # Update dashboard
            self.dashboard.add_trade({
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'timestamp': datetime.now(),
                'value': quantity * price,
                'stop_loss': sl,
                'take_profit': tp
            })
            
            return result
        
        except Exception as e:
            logger.error(f"Error placing order for {symbol}: {e}")
            return None
    
    async def _calculate_stop_loss_take_profit(self, symbol: str, side: str, price: float) -> tuple:
        """Calculate stop loss and take profit levels"""
        # Get ATR for dynamic stop loss
        atr = await self._calculate_atr(symbol)
        
        # Default values
        risk_reward_ratio = self.config.get('risk_reward_ratio', 2.0)
        sl_atr_multiplier = self.config.get('sl_atr_multiplier', 2.0)
        
        if side == 'buy':
            stop_loss = price - (atr * sl_atr_multiplier)
            take_profit = price + (atr * sl_atr_multiplier * risk_reward_ratio)
        else:  # sell
            stop_loss = price + (atr * sl_atr_multiplier)
            take_profit = price - (atr * sl_atr_multiplier * risk_reward_ratio)
        
        return stop_loss, take_profit
    
    async def _calculate_atr(self, symbol: str, period: int = 14, timeframe: str = 'H1') -> float:
        """Calculate Average True Range (ATR)"""
        # Get historical data
        if symbol in self.historical_data and timeframe in self.historical_data[symbol]:
            data = self.historical_data[symbol][timeframe]
            
            # Calculate true ranges
            high = data['high'].values
            low = data['low'].values
            close = data['close'].values
            close_prev = np.roll(close, 1)
            close_prev[0] = close[0]
            
            tr1 = high - low
            tr2 = np.abs(high - close_prev)
            tr3 = np.abs(low - close_prev)
            
            tr = np.maximum(tr1, np.maximum(tr2, tr3))
            atr = np.mean(tr[-period:])
            
            return atr
        
        return 0.001  # Default to 0.1% if no data
    
    async def _close_all_positions(self):
        """Close all open positions"""
        positions = await self.connector.get_positions()
        
        for position in positions:
            symbol = position['symbol']
            position_type = position['type']
            volume = position['volume']
            
            # Determine closing side
            side = 'sell' if position_type == 'buy' else 'buy'
            
            # Get current price
            ticker = await self.connector.get_ticker(symbol)
            price = ticker.bid if side == 'sell' else ticker.ask
            
            logger.info(f"Closing position: {side} {volume} {symbol} @ {price}")
            
            # Place closing order
            await self._place_order(symbol, side, volume, price)
    
    async def _update_account_balance(self):
        """Update account balance"""
        try:
            balance = await self.connector.get_balance()
            
            # Update account size
            self.account_size = balance.get('equity', self.account_size)
            
            # Update dashboard
            self.dashboard.update_metric("account_balance", balance.get('balance', 0))
            self.dashboard.update_metric("account_equity", balance.get('equity', 0))
            self.dashboard.update_metric("margin_level", balance.get('margin_level', 0))
            
            # Update peak equity for drawdown calculation
            if balance.get('equity', 0) > self.metrics['peak_equity']:
                self.metrics['peak_equity'] = balance.get('equity', 0)
            
            # Calculate current drawdown
            if self.metrics['peak_equity'] > 0:
                current_drawdown = (self.metrics['peak_equity'] - balance.get('equity', 0)) / self.metrics['peak_equity']
                self.metrics['current_drawdown'] = current_drawdown
                
                # Update max drawdown
                if current_drawdown > self.metrics['max_drawdown']:
                    self.metrics['max_drawdown'] = current_drawdown
            
            logger.info(f"Account balance updated: {balance.get('equity', 0)} {balance.get('currency', 'USD')}")
            
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
    
    async def _initialize_historical_data(self):
        """Initialize historical data for all symbols and timeframes"""
        for symbol in self.symbols:
            self.historical_data[symbol] = {}
            
            for timeframe in self.timeframes:
                # Convert timeframe to MT5 format
                mt5_timeframe = self._convert_timeframe_to_mt5(timeframe)
                
                try:
                    # Get historical data
                    # Use MT5 connector to get historical data
                    mt5_symbol = self.connector.normalize_symbol(symbol)
                    rates = await self._get_historical_rates(mt5_symbol, mt5_timeframe, 1000)
                    
                    if rates is not None:
                        # Convert to pandas DataFrame
                        df = pd.DataFrame(rates)
                        df['time'] = pd.to_datetime(df['time'], unit='s')
                        df.set_index('time', inplace=True)
                        
                        # Store in historical data cache
                        self.historical_data[symbol][timeframe] = df
                        
                        logger.info(f"Loaded historical data for {symbol} {timeframe}: {len(df)} bars")
                    else:
                        logger.warning(f"Failed to load historical data for {symbol} {timeframe}")
                
                except Exception as e:
                    logger.error(f"Error loading historical data for {symbol} {timeframe}: {e}")
    
    async def _get_historical_rates(self, symbol: str, timeframe: int, count: int = 1000):
        """Get historical rates from MT5"""
        
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        return rates
    
    def _convert_timeframe_to_mt5(self, timeframe: str) -> int:
        """Convert timeframe string to MT5 timeframe constant"""
        
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN1': mt5.TIMEFRAME_MN1
        }
        
        return timeframe_map.get(timeframe, mt5.TIMEFRAME_H1)
    
    async def _get_market_data_for_timeframes(self, symbol: str) -> Dict[str, Dict[str, float]]:
        """Get market data for all timeframes"""
        result = {}
        
        if symbol in self.historical_data:
            for timeframe, data in self.historical_data[symbol].items():
                if not data.empty:
                    last_row = data.iloc[-1]
                    result[timeframe] = {
                        'open': last_row['open'],
                        'high': last_row['high'],
                        'low': last_row['low'],
                        'close': last_row['close'],
                        'volume': last_row['tick_volume']
                    }
        
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
        
        # Round to appropriate precision for forex
        if 'USD' in symbol or 'EUR' in symbol or 'GBP' in symbol or 'JPY' in symbol:
            # For forex, round to 2 decimal places (0.01 lot)
            position_size = round(position_size * 100) / 100
        else:
            # For stocks, round to 1 decimal place
            position_size = round(position_size * 10) / 10
        
        return position_size
    
    async def _update_dashboard_metrics(self):
        """Update dashboard metrics"""
        # Update account balance
        await self._update_account_balance()
        
        # Update performance metrics
        self.dashboard.update_metric("total_trades", self.metrics['total_trades'])
        self.dashboard.update_metric("winning_trades", self.metrics['winning_trades'])
        self.dashboard.update_metric("losing_trades", self.metrics['losing_trades'])
        
        if self.metrics['total_trades'] > 0:
            win_rate = self.metrics['winning_trades'] / self.metrics['total_trades'] * 100
            self.dashboard.update_metric("win_rate", win_rate)
        
        self.dashboard.update_metric("total_profit", self.metrics['total_profit'])
        self.dashboard.update_metric("total_loss", self.metrics['total_loss'])
        self.dashboard.update_metric("max_drawdown", self.metrics['max_drawdown'] * 100)
        self.dashboard.update_metric("current_drawdown", self.metrics['current_drawdown'] * 100)
        
        # Update strategy metrics
        if self.metrics['total_profit'] > 0 and self.metrics['total_loss'] > 0:
            profit_factor = self.metrics['total_profit'] / max(self.metrics['total_loss'], 0.01)
            self.dashboard.update_metric("profit_factor", profit_factor)
    
    def _save_trading_data(self):
        """Save trading data to file"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Save metrics
            with open('data/mt5_trading_metrics.json', 'w') as f:
                json.dump(self.metrics, f, indent=2)
            
            # Save market data
            with open('data/mt5_market_data.json', 'w') as f:
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
    
    async def optimize_portfolio(self):
        """Optimize portfolio using quantum computing"""
        try:
            logger.info("Starting portfolio optimization with quantum computing")
            
            # Get current positions
            positions = await self.connector.get_positions()
            symbols = [pos['symbol'] for pos in positions]
            
            # Add symbols from configuration if not enough positions
            if len(symbols) < 5:
                symbols.extend([s for s in self.symbols if s not in symbols])
                symbols = symbols[:10]  # Limit to 10 symbols
            
            # Run quantum optimization
            portfolio = await self.quantum_optimizer.optimize_portfolio(
                symbols=symbols,
                constraints={'risk_level': 'moderate'}
            )
            
            logger.info("Portfolio optimization completed")
            logger.info("Recommended allocations:")
            
            for symbol, allocation in portfolio.items():
                logger.info(f"  {symbol}: {allocation:.2%}")
                self.dashboard.update_metric(f"{symbol}_allocation", allocation * 100)
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Error in portfolio optimization: {e}")
            return {}


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create MT5 brain trader
    trader = MT5BrainTrader()
    
    # Run trader
    asyncio.run(trader.start())
