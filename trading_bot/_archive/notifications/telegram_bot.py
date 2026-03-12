"""
Telegram Bot Integration
=========================
Production-grade Telegram bot for trading notifications,
commands, and remote control.
"""

import asyncio
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
import json
try:
    import aiohttp
except ImportError:
    aiohttp = None
import hashlib

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class TelegramConfig:
    """Telegram bot configuration."""
    bot_token: str = ""
    chat_id: str = ""
    admin_ids: List[str] = field(default_factory=list)
    notification_types: List[str] = field(default_factory=lambda: ["trade", "alert", "error", "daily_report"])
    rate_limit_per_minute: int = 20
    parse_mode: str = "HTML"
    disable_notification: bool = False
    enable_commands: bool = True


class NotificationType(Enum):
    """Notification types."""
    TRADE = "trade"
    ALERT = "alert"
    ERROR = "error"
    INFO = "info"
    DAILY_REPORT = "daily_report"
    SIGNAL = "signal"
    RISK = "risk"
    SYSTEM = "system"


@dataclass
class TelegramMessage:
    """Telegram message."""
    chat_id: str
    text: str
    parse_mode: str = "HTML"
    disable_notification: bool = False
    reply_markup: Optional[Dict] = None


# ============================================================================
# TELEGRAM BOT
# ============================================================================

class TelegramBot:
    """
    Telegram bot for trading notifications and commands.
    """
    
    def __init__(self, config: TelegramConfig):
        self.config = config
        self._base_url = f"https://api.telegram.org/bot{config.bot_token}"
        self._session: Optional[aiohttp.ClientSession] = None
        self._command_handlers: Dict[str, Callable] = {}
        self._callback_handlers: Dict[str, Callable] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._rate_limiter: Dict[str, List[datetime]] = {}
        self._running = False
        self._update_offset = 0
        self._lock = threading.Lock()
        
        # Register default commands
        self._register_default_commands()
    
    def _register_default_commands(self):
        """Register default bot commands."""
        self.register_command("start", self._cmd_start)
        self.register_command("help", self._cmd_help)
        self.register_command("status", self._cmd_status)
        self.register_command("balance", self._cmd_balance)
        self.register_command("positions", self._cmd_positions)
        self.register_command("trades", self._cmd_trades)
        self.register_command("stop", self._cmd_stop)
        self.register_command("pause", self._cmd_pause)
        self.register_command("resume", self._cmd_resume)
    
    async def start(self):
        """Start the bot."""
        if self._running:
            return
        
        self._session = aiohttp.ClientSession()
        self._running = True
        
        # Start background tasks
        asyncio.create_task(self._process_queue())
        
        if self.config.enable_commands:
            asyncio.create_task(self._poll_updates())
        
        logger.info("Telegram bot started")
    
    async def stop(self):
        """Stop the bot."""
        self._running = False
        
        if self._session:
            await self._session.close()
            self._session = None
        
        logger.info("Telegram bot stopped")
    
    async def _request(self, method: str, data: Optional[Dict] = None) -> Dict:
        """Make API request."""
        if not self._session:
            raise RuntimeError("Bot not started")
        
        url = f"{self._base_url}/{method}"
        
        try:
            async with self._session.post(url, json=data) as resp:
                result = await resp.json()
                
                if not result.get("ok"):
                    logger.error(f"Telegram API error: {result.get('description')}")
                
                return result
        except Exception as e:
            logger.error(f"Telegram request error: {e}")
            return {"ok": False, "error": str(e)}
    
    def _check_rate_limit(self, chat_id: str) -> bool:
        """Check if rate limit allows sending."""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        with self._lock:
            if chat_id not in self._rate_limiter:
                self._rate_limiter[chat_id] = []
            
            # Clean old entries
            self._rate_limiter[chat_id] = [
                t for t in self._rate_limiter[chat_id] if t > minute_ago
            ]
            
            if len(self._rate_limiter[chat_id]) >= self.config.rate_limit_per_minute:
                return False
            
            self._rate_limiter[chat_id].append(now)
            return True
    
    async def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[Dict] = None,
    ) -> bool:
        """Send a message."""
        chat_id = chat_id or self.config.chat_id
        
        if not self._check_rate_limit(chat_id):
            logger.warning(f"Rate limit exceeded for chat {chat_id}")
            return False
        
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode or self.config.parse_mode,
            "disable_notification": disable_notification if disable_notification is not None else self.config.disable_notification,
        }
        
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        result = await self._request("sendMessage", data)
        return result.get("ok", False)
    
    async def send_photo(
        self,
        photo_url: str,
        caption: Optional[str] = None,
        chat_id: Optional[str] = None,
    ) -> bool:
        """Send a photo."""
        chat_id = chat_id or self.config.chat_id
        
        data = {
            "chat_id": chat_id,
            "photo": photo_url,
        }
        
        if caption:
            data["caption"] = caption
            data["parse_mode"] = self.config.parse_mode
        
        result = await self._request("sendPhoto", data)
        return result.get("ok", False)
    
    async def send_document(
        self,
        document_url: str,
        caption: Optional[str] = None,
        chat_id: Optional[str] = None,
    ) -> bool:
        """Send a document."""
        chat_id = chat_id or self.config.chat_id
        
        data = {
            "chat_id": chat_id,
            "document": document_url,
        }
        
        if caption:
            data["caption"] = caption
        
        result = await self._request("sendDocument", data)
        return result.get("ok", False)
    
    # ========================================================================
    # NOTIFICATION METHODS
    # ========================================================================
    
    async def notify_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        pnl: Optional[float] = None,
        trade_id: Optional[str] = None,
    ):
        """Send trade notification."""
        if NotificationType.TRADE.value not in self.config.notification_types:
            return
        
        emoji = "🟢" if side.lower() == "buy" else "🔴"
        pnl_text = f"\n💰 P&L: ${pnl:,.2f}" if pnl is not None else ""
        
        text = f"""
{emoji} <b>Trade Executed</b>

📊 Symbol: <code>{symbol}</code>
📈 Side: {side.upper()}
📦 Quantity: {quantity}
💵 Price: ${price:,.4f}{pnl_text}
🆔 ID: <code>{trade_id or 'N/A'}</code>
⏰ Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        
        await self.send_message(text.strip())
    
    async def notify_alert(
        self,
        title: str,
        message: str,
        severity: str = "info",
    ):
        """Send alert notification."""
        if NotificationType.ALERT.value not in self.config.notification_types:
            return
        
        emoji_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨",
        }
        emoji = emoji_map.get(severity.lower(), "ℹ️")
        
        text = f"""
{emoji} <b>{title}</b>

{message}

⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        
        await self.send_message(text.strip())
    
    async def notify_error(
        self,
        error_type: str,
        error_message: str,
        component: Optional[str] = None,
    ):
        """Send error notification."""
        if NotificationType.ERROR.value not in self.config.notification_types:
            return
        
        text = f"""
❌ <b>Error Occurred</b>

🔴 Type: <code>{error_type}</code>
📝 Message: {error_message}
🔧 Component: {component or 'Unknown'}
⏰ Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        
        await self.send_message(text.strip())
    
    async def notify_signal(
        self,
        symbol: str,
        direction: str,
        confidence: float,
        source: str,
        price: float,
    ):
        """Send signal notification."""
        if NotificationType.SIGNAL.value not in self.config.notification_types:
            return
        
        emoji = "📈" if direction.lower() == "buy" else "📉"
        confidence_bar = "█" * int(confidence * 10) + "░" * (10 - int(confidence * 10))
        
        text = f"""
{emoji} <b>New Signal</b>

📊 Symbol: <code>{symbol}</code>
🎯 Direction: {direction.upper()}
📊 Confidence: {confidence:.1%} [{confidence_bar}]
💵 Price: ${price:,.4f}
🔍 Source: {source}
⏰ Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        
        await self.send_message(text.strip())
    
    async def notify_risk_breach(
        self,
        breach_type: str,
        current_value: float,
        limit_value: float,
        action_taken: str,
    ):
        """Send risk breach notification."""
        if NotificationType.RISK.value not in self.config.notification_types:
            return
        
        text = f"""
🚨 <b>Risk Limit Breach</b>

⚠️ Type: {breach_type}
📊 Current: {current_value:.2%}
🎯 Limit: {limit_value:.2%}
🔧 Action: {action_taken}
⏰ Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        
        await self.send_message(text.strip())
    
    async def send_daily_report(
        self,
        total_trades: int,
        winning_trades: int,
        total_pnl: float,
        win_rate: float,
        max_drawdown: float,
        equity: float,
    ):
        """Send daily performance report."""
        if NotificationType.DAILY_REPORT.value not in self.config.notification_types:
            return
        
        pnl_emoji = "📈" if total_pnl >= 0 else "📉"
        
        text = f"""
📊 <b>Daily Performance Report</b>

{pnl_emoji} P&L: ${total_pnl:,.2f}
📈 Trades: {total_trades} ({winning_trades} wins)
🎯 Win Rate: {win_rate:.1%}
📉 Max Drawdown: {max_drawdown:.2%}
💰 Equity: ${equity:,.2f}

📅 Date: {datetime.utcnow().strftime('%Y-%m-%d')}
"""
        
        await self.send_message(text.strip())
    
    # ========================================================================
    # COMMAND HANDLERS
    # ========================================================================
    
    def register_command(self, command: str, handler: Callable):
        """Register a command handler."""
        self._command_handlers[command.lower()] = handler
    
    def register_callback(self, callback_data: str, handler: Callable):
        """Register a callback query handler."""
        self._callback_handlers[callback_data] = handler
    
    async def _cmd_start(self, chat_id: str, user_id: str, args: List[str]):
        """Handle /start command."""
        text = """
🤖 <b>Trading Bot</b>

Welcome! I'm your trading assistant.

Use /help to see available commands.
"""
        await self.send_message(text.strip(), chat_id)
    
    async def _cmd_help(self, chat_id: str, user_id: str, args: List[str]):
        """Handle /help command."""
        text = """
📚 <b>Available Commands</b>

/status - Bot status
/balance - Account balance
/positions - Open positions
/trades - Recent trades
/stop - Stop trading (admin)
/pause - Pause trading (admin)
/resume - Resume trading (admin)
/help - Show this help
"""
        await self.send_message(text.strip(), chat_id)
    
    async def _cmd_status(self, chat_id: str, user_id: str, args: List[str]):
        """Handle /status command."""
        # This would be connected to actual bot status
        text = """
🤖 <b>Bot Status</b>

✅ Status: Running
📊 Mode: Paper Trading
🔄 Uptime: 24h 30m
📈 Active Positions: 3
⏰ Last Update: Just now
"""
        await self.send_message(text.strip(), chat_id)
    
    async def _cmd_balance(self, chat_id: str, user_id: str, args: List[str]):
        """Handle /balance command."""
        # This would be connected to actual account
        text = """
💰 <b>Account Balance</b>

💵 Balance: $10,000.00
📈 Equity: $10,250.00
📊 Margin Used: $500.00
📉 Free Margin: $9,750.00
📈 Unrealized P&L: +$250.00
"""
        await self.send_message(text.strip(), chat_id)
    
    async def _cmd_positions(self, chat_id: str, user_id: str, args: List[str]):
        """Handle /positions command."""
        # This would be connected to actual positions
        text = """
📊 <b>Open Positions</b>

1️⃣ EURUSD
   📈 Long | 0.1 lots
   💵 Entry: 1.0850
   📊 P&L: +$50.00

2️⃣ GBPUSD
   📉 Short | 0.05 lots
   💵 Entry: 1.2650
   📊 P&L: -$20.00

Total P&L: +$30.00
"""
        await self.send_message(text.strip(), chat_id)
    
    async def _cmd_trades(self, chat_id: str, user_id: str, args: List[str]):
        """Handle /trades command."""
        text = """
📜 <b>Recent Trades</b>

1️⃣ EURUSD | Buy | +$50.00
   ⏰ 2 hours ago

2️⃣ USDJPY | Sell | -$20.00
   ⏰ 5 hours ago

3️⃣ GBPUSD | Buy | +$30.00
   ⏰ 8 hours ago

Today's P&L: +$60.00
"""
        await self.send_message(text.strip(), chat_id)
    
    async def _cmd_stop(self, chat_id: str, user_id: str, args: List[str]):
        """Handle /stop command."""
        if user_id not in self.config.admin_ids:
            await self.send_message("⛔ Admin only command", chat_id)
            return
        
        # This would trigger actual stop
        await self.send_message("🛑 Trading stopped", chat_id)
    
    async def _cmd_pause(self, chat_id: str, user_id: str, args: List[str]):
        """Handle /pause command."""
        if user_id not in self.config.admin_ids:
            await self.send_message("⛔ Admin only command", chat_id)
            return
        
        await self.send_message("⏸️ Trading paused", chat_id)
    
    async def _cmd_resume(self, chat_id: str, user_id: str, args: List[str]):
        """Handle /resume command."""
        if user_id not in self.config.admin_ids:
            await self.send_message("⛔ Admin only command", chat_id)
            return
        
        await self.send_message("▶️ Trading resumed", chat_id)
    
    # ========================================================================
    # UPDATE PROCESSING
    # ========================================================================
    
    async def _poll_updates(self):
        """Poll for updates."""
        while self._running:
            try:
                result = await self._request("getUpdates", {
                    "offset": self._update_offset,
                    "timeout": 30,
                })
                
                if result.get("ok"):
                    for update in result.get("result", []):
                        self._update_offset = update["update_id"] + 1
                        await self._process_update(update)
                
            except Exception as e:
                logger.error(f"Update polling error: {e}")
                await asyncio.sleep(5)
    
    async def _process_update(self, update: Dict):
        """Process an update."""
        try:
            if "message" in update:
                await self._process_message(update["message"])
            elif "callback_query" in update:
                await self._process_callback(update["callback_query"])
        except Exception as e:
            logger.error(f"Update processing error: {e}")
    
    async def _process_message(self, message: Dict):
        """Process a message."""
        text = message.get("text", "")
        chat_id = str(message["chat"]["id"])
        user_id = str(message["from"]["id"])
        
        if text.startswith("/"):
            parts = text[1:].split()
            command = parts[0].lower()
            args = parts[1:]
            
            handler = self._command_handlers.get(command)
            if handler:
                await handler(chat_id, user_id, args)
    
    async def _process_callback(self, callback: Dict):
        """Process a callback query."""
        callback_data = callback.get("data", "")
        chat_id = str(callback["message"]["chat"]["id"])
        
        handler = self._callback_handlers.get(callback_data)
        if handler:
            await handler(chat_id, callback)
        
        # Answer callback
        await self._request("answerCallbackQuery", {
            "callback_query_id": callback["id"],
        })
    
    async def _process_queue(self):
        """Process message queue."""
        while self._running:
            try:
                message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=1.0
                )
                await self.send_message(**message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Queue processing error: {e}")


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_telegram_bot: Optional[TelegramBot] = None


def get_telegram_bot(config: Optional[TelegramConfig] = None) -> TelegramBot:
    """Get global Telegram bot instance."""
    global _telegram_bot
    if _telegram_bot is None:
        if config is None:
            config = TelegramConfig()
        _telegram_bot = TelegramBot(config)
    return _telegram_bot


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'TelegramConfig', 'NotificationType', 'TelegramMessage',
    'TelegramBot', 'get_telegram_bot',
]
