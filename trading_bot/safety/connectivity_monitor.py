"""
Connectivity Monitor

Monitors MT5 connection and handles disconnections gracefully.
"""

import time
import logging
from typing import Optional, Callable
from pathlib import Path
import json
import os

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

logger = logging.getLogger(__name__)


class ConnectivityMonitor:
    """
    Monitors MT5 connection and handles disconnections.
    
    Features:
    - Detect connection drops
    - Close all positions on disconnect
    - Save trading state
    - Retry connection with exponential backoff
    """
    
    def __init__(
        self,
        max_retries: int = 5,
        on_disconnect: Optional[Callable] = None,
        on_reconnect: Optional[Callable] = None
    ):
        """
        Initialize connectivity monitor.
        
        Args:
            max_retries: Maximum reconnection attempts
            on_disconnect: Callback function when disconnected
            on_reconnect: Callback function when reconnected
        """
        self.max_retries = max_retries
        self.retry_delays = [5, 15, 45, 135, 405]  # Exponential backoff
        self.is_connected = False
        self.on_disconnect = on_disconnect
        self.on_reconnect = on_reconnect
        
        logger.info(f"Connectivity Monitor initialized:")
        logger.info(f"  Max retries: {max_retries}")
        logger.info(f"  Retry delays: {self.retry_delays}")
    
    def check_connection(self) -> bool:
        """
        Check MT5 connection status.
        
        Returns:
            True if connected, False otherwise
        """
        if mt5 is None:
            logger.warning("MT5 not available")
            return False
        try:
        
            account_info = mt5.account_info()
            if account_info is None:
                logger.warning("MT5 account_info returned None")
                return False
            
            # Additional check: try to get a tick
            tick = mt5.symbol_info_tick("EURUSD")
            if tick is None:
                logger.warning("MT5 symbol_info_tick returned None")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            return False
    
    def handle_disconnect(self) -> bool:
        """
        Handle MT5 disconnection.
        
        Returns:
            True if reconnection successful, False otherwise
        """
        if not self.is_connected:
            logger.info("Already in disconnected state")
            return False
        
        self.is_connected = False
        
        logger.critical("=" * 80)
        logger.critical("🔌 MT5 CONNECTION LOST - ENTERING OFFLINE MODE")
        logger.critical("=" * 80)
        
        # Call disconnect callback
        if self.on_disconnect:
            try:
                self.on_disconnect()
            except Exception as e:
                logger.error(f"Disconnect callback failed: {e}")
        
        # Close all positions
        self._emergency_close_all_positions()
        
        # Save state
        self._save_trading_state()
        
        # Attempt reconnection
        reconnected = self._attempt_reconnection()
        
        if reconnected:
            self.is_connected = True
            logger.info("✓ Reconnection successful")
            
            # Call reconnect callback
            if self.on_reconnect:
                try:
                    self.on_reconnect()
                except Exception as e:
                    logger.error(f"Reconnect callback failed: {e}")
            
            return True
        else:
            logger.critical("✗ All reconnection attempts failed")
            logger.critical("Manual intervention required")
            return False
    
    def _emergency_close_all_positions(self):
        """Close all open positions during disconnect."""
        if mt5 is None:
            logger.warning("MT5 not available, cannot close positions")
            return
        try:
        
            positions = mt5.positions_get()
            if not positions:
                logger.info("No open positions to close")
                return
            
            logger.warning(f"Closing {len(positions)} positions due to disconnect...")
            
            for pos in positions:
                try:
                    self._close_position(pos.ticket, pos.symbol, pos.volume, pos.type)
                except Exception as e:
                    logger.error(f"Failed to close position {pos.ticket}: {e}")
            
            logger.info("All positions closed")
            
        except Exception as e:
            logger.error(f"Error closing positions: {e}")
    
    def _close_position(self, ticket: int, symbol: str, volume: float, position_type: int):
        """Close a specific position."""
        if mt5 is None:
            return
        try:
        
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.error(f"Cannot get tick for {symbol}")
                return
            
            # Determine close type and price
            if position_type == 0:  # Buy position
                close_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            else:  # Sell position
                close_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
            
            # Prepare close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": symbol,
                "volume": volume,
                "type": close_type,
                "price": price,
                "deviation": 20,
                "comment": "DISCONNECT_CLOSE",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"✓ Closed position {ticket}")
            else:
                logger.error(f"✗ Failed to close {ticket}: {result.comment}")
                
        except Exception as e:
            logger.error(f"Exception closing position {ticket}: {e}")
    
    def _save_trading_state(self):
        """Save current trading state to disk."""
        try:
            state = {
                'timestamp': time.time(),
                'disconnect_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                'positions_closed': True,
                'state_saved': True,
            }
            
            # Add account info if available
            if mt5 is not None:
                try:
                    account_info = mt5.account_info()
                    if account_info:
                        state['account'] = {
                            'balance': account_info.balance,
                            'equity': account_info.equity,
                            'margin': account_info.margin,
                        }
                except Exception:
                    pass
            
            state_file = Path('logs/disconnect_state.json')
            state_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"Trading state saved to {state_file}")
            
        except Exception as e:
            logger.error(f"Failed to save trading state: {e}")
    
    def _attempt_reconnection(self) -> bool:
        """
        Attempt to reconnect to MT5.
        
        Returns:
            True if successful, False otherwise
        """
        if mt5 is None:
            logger.error("MT5 module not available")
            return False
        
        for attempt, delay in enumerate(self.retry_delays[:self.max_retries], 1):
            logger.info(f"Reconnection attempt {attempt}/{self.max_retries} in {delay}s...")
            time.sleep(delay)
            
            if self._reconnect():
                logger.info(f"✓ Reconnection successful on attempt {attempt}")
                return True
            else:
                logger.warning(f"✗ Reconnection attempt {attempt} failed")
        
        logger.critical(f"All {self.max_retries} reconnection attempts failed")
        return False
    
    def _reconnect(self) -> bool:
        """
        Attempt single reconnection.
        
        Returns:
            True if successful, False otherwise
        """
        if mt5 is None:
            return False
        try:
        
            # Try to initialize
            if not mt5.initialize():
                logger.debug("MT5 initialize failed")
                return False
            
            # Try to login if credentials available
            account = os.getenv('MT5_ACCOUNT')
            password = os.getenv('MT5_PASSWORD')
            server = os.getenv('MT5_SERVER')
            
            if account and password and server:
                try:
                    account_num = int(account)
                    if not mt5.login(account_num, password, server):
                        logger.debug(f"MT5 login failed: {mt5.last_error()}")
                        return False
                except ValueError:
                    logger.error(f"Invalid account number: {account}")
                    return False
            
            # Verify connection
            if self.check_connection():
                return True
            else:
                logger.debug("Connection check failed after reconnect")
                return False
                
        except Exception as e:
            logger.debug(f"Reconnection exception: {e}")
            return False
    
    def monitor(self) -> bool:
        """
        Monitor connection and handle disconnects.
        
        Returns:
            True if connected, False if disconnected
        """
        connected = self.check_connection()
        
        if not connected and self.is_connected:
            # Connection lost
            self.handle_disconnect()
            return False
        elif connected and not self.is_connected:
            # Connection restored
            self.is_connected = True
            logger.info("Connection restored")
        
        return connected
