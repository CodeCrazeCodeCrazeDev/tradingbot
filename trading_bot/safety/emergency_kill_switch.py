"""
Emergency Kill Switch

Monitors critical thresholds and stops all trading if breached.
Prevents catastrophic losses from runaway trading.
"""

import logging
import json
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime
from pathlib import Path

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

logger = logging.getLogger(__name__)


@dataclass
class EmergencyTrigger:
    """Represents an emergency trigger condition."""
    name: str
    threshold: float
    current_value: float
    triggered: bool
    message: str
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class EmergencyKillSwitch:
    """
    Emergency kill switch that monitors critical thresholds and stops trading.
    
    Monitors:
    - Equity drawdown
    - Consecutive losses
    - Daily loss percentage
    - Manual kill switch file
    """
    
    def __init__(
        self,
        max_drawdown: float = 0.15,
        max_consecutive_losses: int = 5,
        max_daily_loss_pct: float = 0.05,
        kill_switch_file: str = "EMERGENCY_STOP.txt"
    ):
        """
        Initialize emergency kill switch.
        
        Args:
            max_drawdown: Maximum allowed drawdown (default 15%)
            max_consecutive_losses: Maximum consecutive losing trades
            max_daily_loss_pct: Maximum daily loss percentage (default 5%)
            kill_switch_file: File to check for manual emergency stop
        """
        self.max_drawdown = max_drawdown
        self.max_consecutive_losses = max_consecutive_losses
        self.max_daily_loss_pct = max_daily_loss_pct
        self.kill_switch_file = Path(kill_switch_file)
        
        # State tracking
        self.consecutive_losses = 0
        self.daily_start_equity: Optional[float] = None
        self.peak_equity: Optional[float] = None
        self.last_reset_date: Optional[str] = None
        self.emergency_triggered = False
        
        logger.info(f"Emergency Kill Switch initialized:")
        logger.info(f"  Max Drawdown: {max_drawdown:.1%}")
        logger.info(f"  Max Consecutive Losses: {max_consecutive_losses}")
        logger.info(f"  Max Daily Loss: {max_daily_loss_pct:.1%}")
    
    def check_triggers(
        self,
        current_equity: float,
        last_trade_pnl: Optional[float] = None
    ) -> List[EmergencyTrigger]:
        """
        Check all emergency triggers.
        
        Args:
            current_equity: Current account equity
            last_trade_pnl: PnL of last trade (None if no recent trade)
        
        Returns:
            List of EmergencyTrigger objects
        """
        triggers = []
        
        # Reset daily tracking at start of new day
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        if self.last_reset_date != current_date:
            self.daily_start_equity = current_equity
            self.last_reset_date = current_date
            logger.info(f"Daily tracking reset. Starting equity: ${current_equity:.2f}")
        
        # Initialize tracking
        if self.daily_start_equity is None:
            self.daily_start_equity = current_equity
        if self.peak_equity is None or current_equity > self.peak_equity:
            self.peak_equity = current_equity
        
        # Track consecutive losses
        if last_trade_pnl is not None:
            if last_trade_pnl < 0:
                self.consecutive_losses += 1
                logger.debug(f"Consecutive losses: {self.consecutive_losses}")
            else:
                self.consecutive_losses = 0
        
        # Check 1: Drawdown
        drawdown = (self.peak_equity - current_equity) / self.peak_equity if self.peak_equity > 0 else 0
        triggers.append(EmergencyTrigger(
            name="Max Drawdown",
            threshold=self.max_drawdown,
            current_value=drawdown,
            triggered=drawdown > self.max_drawdown,
            message=f"Drawdown {drawdown:.1%} exceeds limit {self.max_drawdown:.1%}"
        ))
        
        # Check 2: Consecutive Losses
        triggers.append(EmergencyTrigger(
            name="Consecutive Losses",
            threshold=float(self.max_consecutive_losses),
            current_value=float(self.consecutive_losses),
            triggered=self.consecutive_losses >= self.max_consecutive_losses,
            message=f"{self.consecutive_losses} consecutive losses (limit: {self.max_consecutive_losses})"
        ))
        
        # Check 3: Daily Loss
        daily_loss_pct = (self.daily_start_equity - current_equity) / self.daily_start_equity if self.daily_start_equity > 0 else 0
        triggers.append(EmergencyTrigger(
            name="Daily Loss",
            threshold=self.max_daily_loss_pct,
            current_value=daily_loss_pct,
            triggered=daily_loss_pct > self.max_daily_loss_pct,
            message=f"Daily loss {daily_loss_pct:.1%} exceeds limit {self.max_daily_loss_pct:.1%}"
        ))
        
        # Check 4: Manual Kill Switch File
        manual_trigger = self.kill_switch_file.exists()
        triggers.append(EmergencyTrigger(
            name="Manual Kill Switch",
            threshold=1.0,
            current_value=1.0 if manual_trigger else 0.0,
            triggered=manual_trigger,
            message=f"Manual kill switch file detected: {self.kill_switch_file}"
        ))
        
        return triggers
    
    def execute_emergency_stop(self, triggers: List[EmergencyTrigger]) -> bool:
        """
        Execute emergency stop procedures.
        
        Args:
            triggers: List of trigger conditions
        
        Returns:
            True if emergency stop was executed
        """
        triggered = [t for t in triggers if t.triggered]
        
        if not triggered:
            return False
        
        if self.emergency_triggered:
            logger.warning("Emergency stop already triggered, skipping duplicate execution")
            return False
        
        self.emergency_triggered = True
        
        logger.critical("=" * 80)
        logger.critical("🚨 EMERGENCY STOP TRIGGERED 🚨")
        logger.critical("=" * 80)
        
        for trigger in triggered:
            logger.critical(f"⚠️  {trigger.name}: {trigger.message}")
        
        # Close all positions
        if mt5 is not None:
            try:
                positions = mt5.positions_get()
                if positions:
                    logger.critical(f"Closing {len(positions)} open positions...")
                    for pos in positions:
                        self._close_position(pos.ticket)
                else:
                    logger.info("No open positions to close")
            except Exception as e:
                logger.error(f"Error closing positions: {e}")
        else:
            logger.warning("MT5 not available, cannot close positions")
        
        # Save emergency state
        self._save_emergency_state(triggered)
        
        # Send alerts (implement your notification system)
        self._send_alerts(triggered)
        
        logger.critical("Emergency stop complete. Manual review required.")
        logger.critical("To resume trading, delete EMERGENCY_STOP.txt and restart bot.")
        logger.critical("=" * 80)
        
        return True
    
    def _close_position(self, ticket: int) -> bool:
        """Close a position by ticket number."""
        if mt5 is None:
            return False
        try:
        
            position = mt5.positions_get(ticket=ticket)
            if not position:
                logger.warning(f"Position {ticket} not found")
                return False
            
            position = position[0]
            
            # Prepare close request
            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "price": mt5.symbol_info_tick(position.symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(position.symbol).ask,
                "deviation": 20,
                "magic": position.magic,
                "comment": "EMERGENCY_CLOSE",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(close_request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"✓ Emergency closed position {ticket}")
                return True
            else:
                logger.error(f"✗ Failed to close position {ticket}: {result.comment}")
                return False
                
        except Exception as e:
            logger.error(f"Exception closing position {ticket}: {e}")
            return False
    
    def _save_emergency_state(self, triggers: List[EmergencyTrigger]):
        """Save emergency state to file."""
        try:
            state = {
                'timestamp': datetime.utcnow().isoformat(),
                'triggers': [asdict(t) for t in triggers],
                'consecutive_losses': self.consecutive_losses,
                'peak_equity': self.peak_equity,
                'daily_start_equity': self.daily_start_equity,
            }
            
            state_file = Path('logs/emergency_state.json')
            state_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"Emergency state saved to {state_file}")
            
        except Exception as e:
            logger.error(f"Failed to save emergency state: {e}")
    
    def _send_alerts(self, triggers: List[EmergencyTrigger]):
        """Send alerts via configured channels."""
        # Implement notification system
        alert_message = "🚨 EMERGENCY STOP TRIGGERED\n\n"
        for trigger in triggers:
            alert_message += f"• {trigger.name}: {trigger.message}\n"
        
        logger.info(f"Alert message prepared: {alert_message}")
        
        try:
            # Write to alert file
            alert_file = Path('logs/emergency_alert.txt')
            alert_file.parent.mkdir(parents=True, exist_ok=True)
            with open(alert_file, 'w') as f:
                f.write(alert_message)
                f.write(f"\nTimestamp: {datetime.utcnow().isoformat()}\n")
            logger.info(f"Alert written to {alert_file}")
        except Exception as e:
            logger.error(f"Failed to write alert file: {e}")
        # Send via Telegram if configured
            import os
            telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
            telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            if telegram_token and telegram_chat_id:
                import requests
                url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
                payload = {
                    'chat_id': telegram_chat_id,
                    'text': alert_message,
                    'parse_mode': 'HTML'
                }
                response = requests.post(url, json=payload, timeout=5)
                if response.status_code == 200:
                    logger.info("Telegram alert sent successfully")
                else:
                    logger.warning(f"Telegram alert failed: {response.status_code}")
        except Exception as e:
            logger.debug(f"Telegram notification failed: {e}")
        # Send via Email if configured
            email_to = os.getenv('ALERT_EMAIL')
            email_from = os.getenv('EMAIL_FROM')
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = os.getenv('SMTP_PORT', '587')
            smtp_user = os.getenv('SMTP_USER')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            if all([email_to, email_from, smtp_server, smtp_user, smtp_password]):
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                msg = MIMEMultipart()
                msg['From'] = email_from
                msg['To'] = email_to
                msg['Subject'] = 'EMERGENCY STOP - Trading Bot Alert'
                msg.attach(MIMEText(alert_message, 'plain'))
                
                with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                logger.info("Email alert sent successfully")
        except Exception as e:
            logger.debug(f"Email notification failed: {e}")
        # Send via Discord webhook if configured
            discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
            
            if discord_webhook:
                payload = {
                    'content': alert_message,
                    'username': 'Trading Bot Alert'
                }
                response = requests.post(discord_webhook, json=payload, timeout=5)
                if response.status_code == 204:
                    logger.info("Discord alert sent successfully")
                else:
                    logger.warning(f"Discord alert failed: {response.status_code}")
        except Exception as e:
            logger.debug(f"Discord notification failed: {e}")
    
    def reset(self):
        """Reset kill switch state (use with caution)."""
        logger.warning("Resetting emergency kill switch state")
        self.consecutive_losses = 0
        self.emergency_triggered = False
        
        # Remove manual kill switch file if exists
        if self.kill_switch_file.exists():
            self.kill_switch_file.unlink()
            logger.info(f"Removed manual kill switch file: {self.kill_switch_file}")
    
    def is_triggered(self) -> bool:
        """Check if emergency stop has been triggered."""
        return self.emergency_triggered or self.kill_switch_file.exists()
    
    def can_trade(self, current_equity: float = 100000.0) -> bool:
        """
        Check if trading is allowed based on current state.
        
        Args:
            current_equity: Current account equity (default for paper mode)
            
        Returns:
            True if trading is allowed, False otherwise
        """
        # Check if already triggered
        if self.is_triggered():
            return False
        
        # Check triggers with current equity
        triggers = self.check_triggers(current_equity)
        triggered = [t for t in triggers if t.triggered]
        
        return len(triggered) == 0
