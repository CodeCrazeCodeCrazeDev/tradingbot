"""
from typing import List, Optional, Set
Telegram Operations Commands - Slash commands with RBAC

Provides Telegram bot commands for operational control with role-based access.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import asyncio
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User roles for RBAC"""
    ADMIN = 'admin'
    OPERATOR = 'operator'
    VIEWER = 'viewer'


class TelegramOpsCommands:
    """Telegram operations commands with RBAC"""
    
    def __init__(self, survival_core, config: Optional[Dict[str, Any]] = None):
        self.survival_core = survival_core
        self.config = config or {}
        
        # User permissions
        self.user_roles: Dict[int, UserRole] = {}  # user_id -> role
        self._load_user_roles()
        
        # Command history
        self.command_history: List[Dict[str, Any]] = []
        
        # Telegram application
        self.application = None
        
        logger.info("Telegram ops commands initialized")
    
    def _load_user_roles(self):
        """Load user roles from config"""
        roles_config = self.config.get('user_roles', {})
        for user_id, role in roles_config.items():
            self.user_roles[int(user_id)] = UserRole(role)
    
    def _check_permission(self, user_id: int, required_role: UserRole) -> bool:
        """Check if user has required permission"""
        user_role = self.user_roles.get(user_id)
        if not user_role:
            return False
        
        # Admin can do everything
        if user_role == UserRole.ADMIN:
            return True
        
        # Operator can do operator and viewer actions
        if user_role == UserRole.OPERATOR and required_role in [UserRole.OPERATOR, UserRole.VIEWER]:
            return True
        
        # Viewer can only do viewer actions
        if user_role == UserRole.VIEWER and required_role == UserRole.VIEWER:
            return True
        
        return False
    
    def _log_command(self, user_id: int, command: str, result: str):
        """Log command execution"""
        self.command_history.append({
            'user_id': user_id,
            'command': command,
            'result': result,
            'timestamp': datetime.now()
        })
        
        # Keep last 100 commands
        if len(self.command_history) > 100:
            self.command_history = self.command_history[-100:]
    
    async def cmd_pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/pause - Pause trading"""
        user_id = update.effective_user.id
        
        if not self._check_permission(user_id, UserRole.OPERATOR):
            await update.message.reply_text("❌ Insufficient permissions")
            return
        try:
        
            await self.survival_core.pause()
            result = "✅ Trading paused"
            await update.message.reply_text(result)
            self._log_command(user_id, '/pause', 'success')
        except Exception as e:
            result = f"❌ Error: {e}"
            await update.message.reply_text(result)
            self._log_command(user_id, '/pause', f'error: {e}')
    
    async def cmd_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/resume - Resume trading"""
        user_id = update.effective_user.id
        
        if not self._check_permission(user_id, UserRole.OPERATOR):
            await update.message.reply_text("❌ Insufficient permissions")
            return
        try:
        
            await self.survival_core.resume()
            result = "✅ Trading resumed"
            await update.message.reply_text(result)
            self._log_command(user_id, '/resume', 'success')
        except Exception as e:
            result = f"❌ Error: {e}"
            await update.message.reply_text(result)
            self._log_command(user_id, '/resume', f'error: {e}')
    
    async def cmd_flat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/flat - Flatten all positions"""
        user_id = update.effective_user.id
        
        if not self._check_permission(user_id, UserRole.ADMIN):
            await update.message.reply_text("❌ Admin permission required")
            return
        try:
        
            from trading_bot.ops.emergency_controls import EmergencyControls
            emergency = EmergencyControls(self.survival_core)
            
            result = await emergency.flat_book(
                reason="Telegram command",
                executed_by=f"user_{user_id}"
            )
            
            msg = f"✅ Flattened book\n"
            msg += f"Closed: {result['closed_count']}\n"
            msg += f"Failed: {result['failed_count']}"
            
            await update.message.reply_text(msg)
            self._log_command(user_id, '/flat', 'success')
        except Exception as e:
            result = f"❌ Error: {e}"
            await update.message.reply_text(result)
            self._log_command(user_id, '/flat', f'error: {e}')
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/status - Get system status"""
        user_id = update.effective_user.id
        
        if not self._check_permission(user_id, UserRole.VIEWER):
            await update.message.reply_text("❌ Insufficient permissions")
            return
        try:
        
            status = self.survival_core.get_system_status()
            
            msg = "📊 **System Status**\n\n"
            msg += f"Running: {'✅' if status['system']['running'] else '❌'}\n"
            msg += f"Paused: {'⏸️' if status['system']['paused'] else '▶️'}\n"
            msg += f"Errors: {status['system']['error_count']}\n\n"
            
            # Portfolio
            portfolio = status.get('portfolio', {})
            msg += f"**Portfolio**\n"
            msg += f"Positions: {len(portfolio.get('positions', []))}\n"
            msg += f"Balance: ${portfolio.get('account_balance', 0):,.2f}\n\n"
            
            # Risk
            msg += f"**Risk Limits**\n"
            for key, value in status.get('risk_limits', {}).items():
                msg += f"{key}: {value}\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            self._log_command(user_id, '/status', 'success')
        except Exception as e:
            result = f"❌ Error: {e}"
            await update.message.reply_text(result)
            self._log_command(user_id, '/status', f'error: {e}')
    
    async def cmd_positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/positions - List open positions"""
        user_id = update.effective_user.id
        
        if not self._check_permission(user_id, UserRole.VIEWER):
            await update.message.reply_text("❌ Insufficient permissions")
            return
        try:
        
            positions = self.survival_core.execution.get_active_positions()
            
            if not positions:
                await update.message.reply_text("No open positions")
                return
            
            msg = "📈 **Open Positions**\n\n"
            for pos in positions:
                pnl_emoji = "🟢" if pos.unrealized_pnl >= 0 else "🔴"
                msg += f"{pnl_emoji} {pos.symbol}\n"
                msg += f"  Qty: {pos.quantity:,.2f}\n"
                msg += f"  Entry: {pos.entry_price:.5f}\n"
                msg += f"  Current: {pos.current_price:.5f}\n"
                msg += f"  P&L: ${pos.unrealized_pnl:,.2f}\n\n"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            self._log_command(user_id, '/positions', 'success')
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            self._log_command(user_id, '/positions', f'error: {e}')
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/help - Show available commands"""
        user_id = update.effective_user.id
        user_role = self.user_roles.get(user_id, UserRole.VIEWER)
        
        msg = "🤖 **Available Commands**\n\n"
        msg += "**Viewer Commands:**\n"
        msg += "/status - System status\n"
        msg += "/positions - Open positions\n"
        msg += "/help - This message\n\n"
        
        if user_role in [UserRole.OPERATOR, UserRole.ADMIN]:
            msg += "**Operator Commands:**\n"
            msg += "/pause - Pause trading\n"
            msg += "/resume - Resume trading\n\n"
        
        if user_role == UserRole.ADMIN:
            msg += "**Admin Commands:**\n"
            msg += "/flat - Flatten all positions\n"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def setup(self, token: str):
        """Setup Telegram bot"""
        self.application = Application.builder().token(token).build()
        
        # Register commands
        self.application.add_handler(CommandHandler("pause", self.cmd_pause))
        self.application.add_handler(CommandHandler("resume", self.cmd_resume))
        self.application.add_handler(CommandHandler("flat", self.cmd_flat))
        self.application.add_handler(CommandHandler("status", self.cmd_status))
        self.application.add_handler(CommandHandler("positions", self.cmd_positions))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        
        # Set bot commands
        await self.application.bot.set_my_commands([
            BotCommand("status", "Get system status"),
            BotCommand("positions", "List open positions"),
            BotCommand("pause", "Pause trading"),
            BotCommand("resume", "Resume trading"),
            BotCommand("flat", "Flatten all positions"),
            BotCommand("help", "Show help")
        ])
        
        logger.info("Telegram bot commands registered")
    
    async def start(self):
        """Start Telegram bot"""
        if self.application:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            logger.info("Telegram bot started")
    
    async def stop(self):
        """Stop Telegram bot"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Telegram bot stopped")
