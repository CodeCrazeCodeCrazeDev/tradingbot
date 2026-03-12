"""
Elite Trading Bot - Minimal Viable Product (MVP)

A secure, reliable trading bot with core features only.
Designed for MetaQuotes demo accounts (MT5).

Core Features:
1. Secure credential management
2. Market data feed integration
3. Simple trade execution (buy/sell at market)
4. Basic stop-loss and take-profit
5. Email notifications
6. Comprehensive logging
7. Safe shutdown procedures

Author: Elite Trading Systems
Email: peterkiragu68@outlook.com
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import os

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f"mvp_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class SecureCredentials:
    """Secure credential management - NEVER hardcode credentials!"""
    
    def __init__(self):
        self._load_from_env()
    
    def _load_from_env(self):
        """Load credentials from environment variables"""
        # Try to load from .env file
        try:
            from dotenv import load_dotenv
            env_file = Path('.env')
            if env_file.exists():
                load_dotenv(env_file)
                logger.info("Loaded credentials from .env file")
            else:
                logger.warning(".env file not found - using system environment")
        except ImportError:
            logger.warning("python-dotenv not installed - using system environment")
        
        # Load MT5 credentials
        self.mt5_login = os.getenv('MT5_LOGIN')
        self.mt5_password = os.getenv('MT5_PASSWORD')
        self.mt5_server = os.getenv('MT5_SERVER')
        
        # Load email credentials
        self.email_address = os.getenv('EMAIL_ADDRESS', 'peterkiragu68@outlook.com')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp-mail.outlook.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', self.email_address)
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
        # Validate required credentials
        if not all([self.mt5_login, self.mt5_password, self.mt5_server]):
            raise ValueError(
                "Missing MT5 credentials! Please set MT5_LOGIN, MT5_PASSWORD, and MT5_SERVER "
                "in .env file or environment variables."
            )
        
        logger.info(f"Credentials loaded for account: {self.mt5_login}")


class EmailNotifier:
    """Email notification system"""
    
    def __init__(self, credentials: SecureCredentials):
        self.credentials = credentials
        self.enabled = bool(credentials.smtp_password)
        
        if not self.enabled:
            logger.warning("Email notifications disabled - SMTP_PASSWORD not set")
    
    async def send_notification(self, subject: str, message: str):
        """Send email notification"""
        if not self.enabled:
            logger.info(f"[EMAIL] {subject}: {message}")
            return
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = self.credentials.smtp_username
            msg['To'] = self.credentials.email_address
            msg['Subject'] = f"[Trading Bot] {subject}"
            
            body = f"""
Elite Trading Bot Notification

Time: {datetime.now().isoformat()}

{message}

---
This is an automated message from your Elite Trading Bot.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.credentials.smtp_server, self.credentials.smtp_port) as server:
                server.starttls()
                server.login(self.credentials.smtp_username, self.credentials.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")


class MT5Connection:
    """Secure MT5 connection management"""
    
    def __init__(self, credentials: SecureCredentials):
        self.credentials = credentials
        self.connected = False
        self.mt5 = None
        
        # Check if MT5 is available
        try:
            import MetaTrader5 as mt5
            self.mt5 = mt5
        except ImportError:
            raise ImportError(
                "MetaTrader5 package not installed! "
                "Install with: pip install MetaTrader5"
            )
    
    def connect(self) -> bool:
        """Connect to MT5 terminal"""
        try:
            # Initialize MT5
            if not self.mt5.initialize():
                error = self.mt5.last_error()
                logger.error(f"MT5 initialization failed: {error}")
                return False
            
            logger.info("MT5 initialized successfully")
            
            # Login to account
            authorized = self.mt5.login(
                int(self.credentials.mt5_login),
                password=self.credentials.mt5_password,
                server=self.credentials.mt5_server
            )
            
            if not authorized:
                error = self.mt5.last_error()
                logger.error(f"MT5 login failed: {error}")
                return False
            
            self.connected = True
            
            # Get account info
            account = self.mt5.account_info()
            if account:
                logger.info(f"Connected to MT5 account: {account.login}")
                logger.info(f"Balance: ${account.balance:.2f}")
                logger.info(f"Equity: ${account.equity:.2f}")
                logger.info(f"Server: {account.server}")
            
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Safely disconnect from MT5"""
        if self.connected and self.mt5:
            self.mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT5")
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information"""
        if not self.connected:
            return None
        
        account = self.mt5.account_info()
        if not account:
            return None
        
        return {
            'login': account.login,
            'balance': account.balance,
            'equity': account.equity,
            'profit': account.profit,
            'margin': account.margin,
            'margin_free': account.margin_free,
            'margin_level': account.margin_level
        }
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information"""
        if not self.connected:
            return None
        
        info = self.mt5.symbol_info(symbol)
        if not info:
            return None
        
        return {
            'symbol': info.name,
            'bid': info.bid,
            'ask': info.ask,
            'spread': info.spread,
            'digits': info.digits
        }


class SimpleTrader:
    """Simple trade execution with basic risk management"""
    
    def __init__(self, connection: MT5Connection, notifier: EmailNotifier):
        self.connection = connection
        self.notifier = notifier
        self.mt5 = connection.mt5
        
        # Risk management limits
        self.max_position_size = float(os.getenv('MAX_POSITION_SIZE', '0.01'))
        self.max_positions = int(os.getenv('MAX_POSITIONS', '3'))
        self.max_daily_loss = float(os.getenv('MAX_DAILY_LOSS', '100'))
        
        # Tracking
        self.daily_pnl = 0.0
        self.trades_today = 0
    
    async def place_trade(
        self,
        symbol: str,
        action: str,  # 'buy' or 'sell'
        volume: float,
        stop_loss_pips: Optional[float] = None,
        take_profit_pips: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Place a trade with basic risk management
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            action: 'buy' or 'sell'
            volume: Position size in lots
            stop_loss_pips: Stop loss in pips
            take_profit_pips: Take profit in pips
        
        Returns:
            Trade result or None if failed
        """
        try:
            # Pre-trade checks
            if not self._pre_trade_checks(volume):
                return None
            
            # Get symbol info
            symbol_info = self.mt5.symbol_info(symbol)
            if not symbol_info:
                logger.error(f"Symbol {symbol} not found")
                return None
            
            # Get current price
            tick = self.mt5.symbol_info_tick(symbol)
            if not tick:
                logger.error(f"Failed to get tick for {symbol}")
                return None
            
            # Determine order type and price
            if action.lower() == 'buy':
                order_type = self.mt5.ORDER_TYPE_BUY
                price = tick.ask
                sl_price = price - (stop_loss_pips * symbol_info.point * 10) if stop_loss_pips else 0
                tp_price = price + (take_profit_pips * symbol_info.point * 10) if take_profit_pips else 0
            elif action.lower() == 'sell':
                order_type = self.mt5.ORDER_TYPE_SELL
                price = tick.bid
                sl_price = price + (stop_loss_pips * symbol_info.point * 10) if stop_loss_pips else 0
                tp_price = price - (take_profit_pips * symbol_info.point * 10) if take_profit_pips else 0
            else:
                logger.error(f"Invalid action: {action}")
                return None
            
            # Prepare order request
            request = {
                "action": self.mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": sl_price,
                "tp": tp_price,
                "deviation": 20,
                "magic": 234000,
                "comment": "MVP Bot",
                "type_time": self.mt5.ORDER_TIME_GTC,
                "type_filling": self.mt5.ORDER_FILLING_RETURN,
            }
            
            # Send order
            logger.info(f"Placing {action} order: {symbol} {volume} lots @ {price:.5f}")
            result = self.mt5.order_send(request)
            
            if result is None:
                error = self.mt5.last_error()
                logger.error(f"Order failed: {error}")
                await self.notifier.send_notification(
                    "Trade Failed",
                    f"Failed to place {action} order for {symbol}\nError: {error}"
                )
                return None
            
            if result.retcode != self.mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order rejected: {result.comment} (code: {result.retcode})")
                await self.notifier.send_notification(
                    "Trade Rejected",
                    f"Order rejected for {symbol}\nReason: {result.comment}"
                )
                return None
            
            # Success
            self.trades_today += 1
            
            trade_info = {
                'order_id': result.order,
                'symbol': symbol,
                'action': action,
                'volume': result.volume,
                'price': result.price,
                'sl': sl_price,
                'tp': tp_price,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Trade executed successfully: Order #{result.order}")
            
            await self.notifier.send_notification(
                "Trade Executed",
                f"Successfully placed {action} order\n"
                f"Symbol: {symbol}\n"
                f"Volume: {volume} lots\n"
                f"Price: {result.price:.5f}\n"
                f"Order ID: {result.order}"
            )
            
            return trade_info
            
        except Exception as e:
            logger.error(f"Trade execution error: {e}", exc_info=True)
            await self.notifier.send_notification(
                "Trade Error",
                f"Error executing trade: {str(e)}"
            )
            return None
    
    def _pre_trade_checks(self, volume: float) -> bool:
        """Pre-trade risk checks"""
        # Check position size
        if volume > self.max_position_size:
            logger.warning(f"Position size {volume} exceeds limit {self.max_position_size}")
            return False
        
        # Check max positions
        positions = self.mt5.positions_total()
        if positions >= self.max_positions:
            logger.warning(f"Max positions ({self.max_positions}) reached")
            return False
        
        # Check daily loss limit
        if abs(self.daily_pnl) >= self.max_daily_loss:
            logger.warning(f"Daily loss limit (${self.max_daily_loss}) reached")
            return False
        
        return True
    
    async def close_position(self, ticket: int) -> bool:
        """Close a specific position"""
        try:
            positions = self.mt5.positions_get(ticket=ticket)
            if not positions:
                logger.error(f"Position {ticket} not found")
                return False
            
            position = positions[0]
            
            # Prepare close request
            tick = self.mt5.symbol_info_tick(position.symbol)
            
            close_request = {
                "action": self.mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": self.mt5.ORDER_TYPE_SELL if position.type == 0 else self.mt5.ORDER_TYPE_BUY,
                "position": ticket,
                "price": tick.bid if position.type == 0 else tick.ask,
                "deviation": 20,
                "magic": 234000,
                "comment": "Close by MVP Bot",
                "type_time": self.mt5.ORDER_TIME_GTC,
                "type_filling": self.mt5.ORDER_FILLING_RETURN,
            }
            
            result = self.mt5.order_send(close_request)
            
            if result and result.retcode == self.mt5.TRADE_RETCODE_DONE:
                logger.info(f"Position {ticket} closed successfully")
                
                await self.notifier.send_notification(
                    "Position Closed",
                    f"Closed position #{ticket}\n"
                    f"Symbol: {position.symbol}\n"
                    f"Profit: ${position.profit:.2f}"
                )
                
                return True
            else:
                logger.error(f"Failed to close position {ticket}")
                return False
                
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False
    
    async def close_all_positions(self):
        """Emergency: Close all open positions"""
        positions = self.mt5.positions_get()
        if not positions:
            logger.info("No positions to close")
            return
        
        logger.warning(f"Closing all {len(positions)} positions")
        
        for position in positions:
            await self.close_position(position.ticket)
        
        await self.notifier.send_notification(
            "Emergency Close",
            f"Closed all {len(positions)} positions"
        )


class MVPBot:
    """Minimal Viable Product Trading Bot"""
    
    def __init__(self):
        self.running = False
        self.credentials = None
        self.connection = None
        self.notifier = None
        self.trader = None
        
        # Setup signal handlers for safe shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Shutdown signal received")
        asyncio.create_task(self.stop())
    
    async def start(self):
        """Start the bot"""
        logger.info("=" * 60)
        logger.info("ELITE TRADING BOT - MVP")
        logger.info("=" * 60)
        logger.info(f"Start Time: {datetime.now().isoformat()}")
        logger.info("=" * 60)
        
        try:
            # Load credentials
            logger.info("Loading credentials...")
            self.credentials = SecureCredentials()
            
            # Setup email notifications
            logger.info("Setting up notifications...")
            self.notifier = EmailNotifier(self.credentials)
            
            # Connect to MT5
            logger.info("Connecting to MT5...")
            self.connection = MT5Connection(self.credentials)
            
            if not self.connection.connect():
                raise ConnectionError("Failed to connect to MT5")
            
            # Initialize trader
            logger.info("Initializing trader...")
            self.trader = SimpleTrader(self.connection, self.notifier)
            
            # Send startup notification
            account_info = self.connection.get_account_info()
            await self.notifier.send_notification(
                "Bot Started",
                f"Elite Trading Bot started successfully\n"
                f"Account: {account_info['login']}\n"
                f"Balance: ${account_info['balance']:.2f}\n"
                f"Server: {self.credentials.mt5_server}"
            )
            
            self.running = True
            logger.info("Bot started successfully!")
            logger.info("=" * 60)
            
            # Main loop
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"Startup error: {e}", exc_info=True)
            if self.notifier:
                await self.notifier.send_notification(
                    "Bot Startup Failed",
                    f"Error: {str(e)}"
                )
            raise
    
    async def _main_loop(self):
        """Main trading loop with simple trading strategy"""
        logger.info("Entering main loop...")
        
        # Initialize strategy variables
        self.last_prices = {}
        self.moving_averages = {}
        self.positions = {}
        self.check_interval = 60  # seconds
        self.trading_symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        self.history_length = 20
        
        logger.info(f"Trading strategy activated for: {', '.join(self.trading_symbols)}")
        await self.notifier.send_notification(
            "Strategy Activated",
            f"Simple moving average strategy activated\n"
            f"Trading symbols: {', '.join(self.trading_symbols)}\n"
            f"Check interval: {self.check_interval} seconds"
        )
        
        while self.running:
            try:
                # Get account status
                account = self.connection.get_account_info()
                if account:
                    logger.info(
                        f"Status: Balance=${account['balance']:.2f}, "
                        f"Equity=${account['equity']:.2f}, "
                        f"Profit=${account['profit']:.2f}"
                    )
                
                # Execute trading strategy for each symbol
                for symbol in self.trading_symbols:
                    await self._execute_strategy(symbol)
                
                # Sleep for check interval
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await asyncio.sleep(10)
    
    async def _execute_strategy(self, symbol):
        """Execute simple moving average strategy for a symbol"""
        try:
            # Get current price
            info = self.connection.get_symbol_info(symbol)
            if not info:
                logger.warning(f"Could not get price for {symbol}")
                return
            
            current_price = info['bid']
            
            # Initialize price history if needed
            if symbol not in self.last_prices:
                self.last_prices[symbol] = []
            
            # Add current price to history
            self.last_prices[symbol].append(current_price)
            
            # Keep only the last N prices
            if len(self.last_prices[symbol]) > self.history_length:
                self.last_prices[symbol] = self.last_prices[symbol][-self.history_length:]
            
            # Need at least 10 prices for moving average
            if len(self.last_prices[symbol]) < 10:
                return
            
            # Calculate simple moving average
            short_ma = sum(self.last_prices[symbol][-5:]) / 5
            long_ma = sum(self.last_prices[symbol]) / len(self.last_prices[symbol])
            
            # Log strategy data
            logger.info(f"{symbol} - Price: {current_price:.5f}, Short MA: {short_ma:.5f}, Long MA: {long_ma:.5f}")
            
            # Check for crossover (short MA crosses above long MA)
            if len(self.last_prices[symbol]) >= 11:
                prev_short_ma = sum(self.last_prices[symbol][-6:-1]) / 5
                prev_long_ma = sum(self.last_prices[symbol][:-1]) / (len(self.last_prices[symbol])-1)
                
                # Buy signal: Short MA crosses above Long MA
                if prev_short_ma <= prev_long_ma and short_ma > long_ma:
                    logger.info(f"BUY SIGNAL for {symbol}: Short MA crossed above Long MA")
                    
                    # Check if we already have a position
                    positions = self.connection.mt5.positions_get(symbol=symbol)
                    if not positions:
                        # Place buy order
                        result = await self.trader.place_trade(
                            symbol=symbol,
                            action='buy',
                            volume=0.01,
                            stop_loss_pips=50,
                            take_profit_pips=100
                        )
                        
                        if result:
                            logger.info(f"Buy order placed for {symbol} at {current_price:.5f}")
                    else:
                        logger.info(f"Already have position for {symbol}, skipping buy signal")
                
                # Sell signal: Short MA crosses below Long MA
                elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
                    logger.info(f"SELL SIGNAL for {symbol}: Short MA crossed below Long MA")
                    
                    # Check if we already have a position
                    positions = self.connection.mt5.positions_get(symbol=symbol)
                    if not positions:
                        # Place sell order
                        result = await self.trader.place_trade(
                            symbol=symbol,
                            action='sell',
                            volume=0.01,
                            stop_loss_pips=50,
                            take_profit_pips=100
                        )
                        
                        if result:
                            logger.info(f"Sell order placed for {symbol} at {current_price:.5f}")
                    else:
                        logger.info(f"Already have position for {symbol}, skipping sell signal")
            
        except Exception as e:
            logger.error(f"Strategy error for {symbol}: {e}")
            # Don't let one symbol's error affect others
    
    async def stop(self):
        """Safe shutdown"""
        if not self.running:
            return
        
        logger.info("Stopping bot...")
        self.running = False
        
        try:
            # Close all positions (optional - comment out if you want to keep positions)
            # if self.trader:
            #     await self.trader.close_all_positions()
            
            # Disconnect from MT5
            if self.connection:
                self.connection.disconnect()
            
            # Send shutdown notification
            if self.notifier:
                await self.notifier.send_notification(
                    "Bot Stopped",
                    "Elite Trading Bot stopped safely"
                )
            
            logger.info("Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")


async def main():
    """Main entry point"""
    bot = MVPBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
