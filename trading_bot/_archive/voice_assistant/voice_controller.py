"""
from typing import Any, Optional, Set
Voice Assistant Controller
Control trading bot with voice commands
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class VoiceCommand(Enum):
    """Voice commands"""
    # Status commands
    STATUS = "status"
    POSITIONS = "positions"
    BALANCE = "balance"
    PERFORMANCE = "performance"
    
    # Trading commands
    START_TRADING = "start trading"
    STOP_TRADING = "stop trading"
    PAUSE_TRADING = "pause trading"
    RESUME_TRADING = "resume trading"
    
    # Position management
    CLOSE_ALL = "close all positions"
    CLOSE_POSITION = "close position"
    
    # Information
    MARKET_STATUS = "market status"
    LAST_TRADE = "last trade"
    WIN_RATE = "win rate"
    
    # Emergency
    EMERGENCY_STOP = "emergency stop"
    KILL_SWITCH = "kill switch"


@dataclass
class VoiceResponse:
    """Voice response structure"""
    text: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class SpeechRecognizer:
    """Speech recognition handler"""
    
    def __init__(self, language: str = "en-US"):
        self.language = language
        self.is_listening = False
    
    async def listen(self) -> Optional[str]:
        """Listen for voice command"""
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            
            with sr.Microphone() as source:
                logger.info("Listening for command...")
                self.is_listening = True
                
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen for audio
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                self.is_listening = False
                
                # Recognize speech
                text = recognizer.recognize_google(audio, language=self.language)
                logger.info(f"Recognized: {text}")
                
                return text.lower()
        
        except Exception as e:
            logger.error(f"Speech recognition failed: {e}")
            self.is_listening = False
            return None
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False


class TextToSpeech:
    """Text-to-speech handler"""
    
    def __init__(self, engine: str = "pyttsx3", voice: Optional[str] = None):
        self.engine_name = engine
        self.voice = voice
        self._init_engine()
    
    def _init_engine(self):
        """Initialize TTS engine"""
        try:
            if self.engine_name == "pyttsx3":
                import pyttsx3
                self.engine = pyttsx3.init()
                
                # Set properties
                self.engine.setProperty('rate', 150)  # Speed
                self.engine.setProperty('volume', 0.9)  # Volume
                
                # Set voice if specified
                if self.voice:
                    voices = self.engine.getProperty('voices')
                    for v in voices:
                        if self.voice.lower() in v.name.lower():
                            self.engine.setProperty('voice', v.id)
                            break
            else:
                self.engine = None
        except Exception as e:
            logger.error(f"TTS initialization failed: {e}")
            self.engine = None
    
    async def speak(self, text: str):
        """Speak text"""
        if not self.engine:
            logger.warning("TTS engine not available")
            return
        try:
        
            logger.info(f"Speaking: {text}")
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS failed: {e}")
    
    def stop(self):
        """Stop speaking"""
        if self.engine:
            try:
                self.engine.stop()
            except Exception:
                pass


class VoiceAssistant:
    """
    Voice Assistant for Trading Bot
    Control bot with voice commands and get audio feedback
    """
    
    def __init__(self, trading_bot: Any, config: Optional[Dict[str, Any]] = None):
        """Initialize voice assistant"""
        self.trading_bot = trading_bot
        self.config = config or {}
        
        # Initialize components
        self.recognizer = SpeechRecognizer(
            language=self.config.get('language', 'en-US')
        )
        self.tts = TextToSpeech(
            engine=self.config.get('tts_engine', 'pyttsx3'),
            voice=self.config.get('voice')
        )
        
        # Command handlers
        self.command_handlers: Dict[VoiceCommand, Callable] = {}
        self._register_handlers()
        
        # State
        self.is_active = False
        self.command_history = []
    
    def _register_handlers(self):
        """Register command handlers"""
        self.command_handlers = {
            VoiceCommand.STATUS: self._handle_status,
            VoiceCommand.POSITIONS: self._handle_positions,
            VoiceCommand.BALANCE: self._handle_balance,
            VoiceCommand.PERFORMANCE: self._handle_performance,
            VoiceCommand.START_TRADING: self._handle_start_trading,
            VoiceCommand.STOP_TRADING: self._handle_stop_trading,
            VoiceCommand.PAUSE_TRADING: self._handle_pause_trading,
            VoiceCommand.RESUME_TRADING: self._handle_resume_trading,
            VoiceCommand.CLOSE_ALL: self._handle_close_all,
            VoiceCommand.CLOSE_POSITION: self._handle_close_position,
            VoiceCommand.MARKET_STATUS: self._handle_market_status,
            VoiceCommand.LAST_TRADE: self._handle_last_trade,
            VoiceCommand.WIN_RATE: self._handle_win_rate,
            VoiceCommand.EMERGENCY_STOP: self._handle_emergency_stop,
        }
    
    async def start(self):
        """Start voice assistant"""
        self.is_active = True
        await self.tts.speak("Voice assistant activated. I'm ready for your commands.")
        
        while self.is_active:
            try:
                # Listen for command
                text = await self.recognizer.listen()
                
                if text:
                    # Process command
                    response = await self.process_command(text)
                    
                    # Speak response
                    await self.tts.speak(response.text)
                    
                    # Store in history
                    self.command_history.append({
                        'command': text,
                        'response': response,
                        'timestamp': datetime.now()
                    })
            
            except Exception as e:
                logger.error(f"Voice assistant error: {e}")
                await asyncio.sleep(1)
    
    def stop(self):
        """Stop voice assistant"""
        self.is_active = False
        self.recognizer.stop_listening()
        self.tts.stop()
    
    async def process_command(self, text: str) -> VoiceResponse:
        """Process voice command"""
        # Match command
        command = self._match_command(text)
        
        if not command:
            return VoiceResponse(
                text="Sorry, I didn't understand that command.",
                success=False
            )
        
        # Execute handler
        if command in self.command_handlers:
            try:
                return await self.command_handlers[command]()
            except Exception as e:
                logger.error(f"Command handler failed: {e}")
                return VoiceResponse(
                    text=f"Error executing command: {str(e)}",
                    success=False
                )
        else:
            return VoiceResponse(
                text="Command not implemented yet.",
                success=False
            )
    
    def _match_command(self, text: str) -> Optional[VoiceCommand]:
        """Match text to command"""
        text = text.lower().strip()
        
        for command in VoiceCommand:
            if command.value in text:
                return command
        
        return None
    
    # Command Handlers
    
    async def _handle_status(self) -> VoiceResponse:
        """Handle status command"""
        try:
            status = getattr(self.trading_bot, 'get_status', lambda: {})()
            
            text = f"Trading bot is {status.get('state', 'unknown')}. "
            text += f"I have {status.get('open_positions', 0)} open positions. "
            text += f"Today's profit is {status.get('daily_pnl', 0):.2f} dollars."
            
            return VoiceResponse(text=text, success=True, data=status)
        except Exception as e:
            return VoiceResponse(text=f"Error getting status: {str(e)}", success=False)
    
    async def _handle_positions(self) -> VoiceResponse:
        """Handle positions command"""
        try:
            positions = getattr(self.trading_bot, 'get_positions', lambda: [])()
            
            if not positions:
                text = "You have no open positions."
            else:
                text = f"You have {len(positions)} open positions. "
                for pos in positions[:3]:  # Limit to 3
                    text += f"{pos.get('symbol')} {pos.get('direction')} at {pos.get('entry_price')}. "
            
            return VoiceResponse(text=text, success=True, data={'positions': positions})
        except Exception as e:
            return VoiceResponse(text=f"Error getting positions: {str(e)}", success=False)
    
    async def _handle_balance(self) -> VoiceResponse:
        """Handle balance command"""
        try:
            balance = getattr(self.trading_bot, 'get_balance', lambda: 0)()
            
            text = f"Your account balance is {balance:.2f} dollars."
            
            return VoiceResponse(text=text, success=True, data={'balance': balance})
        except Exception as e:
            return VoiceResponse(text=f"Error getting balance: {str(e)}", success=False)
    
    async def _handle_performance(self) -> VoiceResponse:
        """Handle performance command"""
        try:
            perf = getattr(self.trading_bot, 'get_performance', lambda: {})()
            
            text = f"Your win rate is {perf.get('win_rate', 0)*100:.1f} percent. "
            text += f"Total profit is {perf.get('total_profit', 0):.2f} dollars. "
            text += f"Sharpe ratio is {perf.get('sharpe_ratio', 0):.2f}."
            
            return VoiceResponse(text=text, success=True, data=perf)
        except Exception as e:
            return VoiceResponse(text=f"Error getting performance: {str(e)}", success=False)
    
    async def _handle_start_trading(self) -> VoiceResponse:
        """Handle start trading command"""
        try:
            if hasattr(self.trading_bot, 'start'):
                self.trading_bot.start()
                text = "Trading started successfully."
            else:
                text = "Start trading function not available."
            
            return VoiceResponse(text=text, success=True)
        except Exception as e:
            return VoiceResponse(text=f"Error starting trading: {str(e)}", success=False)
    
    async def _handle_stop_trading(self) -> VoiceResponse:
        """Handle stop trading command"""
        try:
            if hasattr(self.trading_bot, 'stop'):
                self.trading_bot.stop()
                text = "Trading stopped successfully."
            else:
                text = "Stop trading function not available."
            
            return VoiceResponse(text=text, success=True)
        except Exception as e:
            return VoiceResponse(text=f"Error stopping trading: {str(e)}", success=False)
    
    async def _handle_pause_trading(self) -> VoiceResponse:
        """Handle pause trading command"""
        try:
            if hasattr(self.trading_bot, 'pause'):
                self.trading_bot.pause()
                text = "Trading paused."
            else:
                text = "Pause function not available."
            
            return VoiceResponse(text=text, success=True)
        except Exception as e:
            return VoiceResponse(text=f"Error pausing trading: {str(e)}", success=False)
    
    async def _handle_resume_trading(self) -> VoiceResponse:
        """Handle resume trading command"""
        try:
            if hasattr(self.trading_bot, 'resume'):
                self.trading_bot.resume()
                text = "Trading resumed."
            else:
                text = "Resume function not available."
            
            return VoiceResponse(text=text, success=True)
        except Exception as e:
            return VoiceResponse(text=f"Error resuming trading: {str(e)}", success=False)
    
    async def _handle_close_all(self) -> VoiceResponse:
        """Handle close all positions command"""
        try:
            if hasattr(self.trading_bot, 'close_all_positions'):
                result = self.trading_bot.close_all_positions()
                text = f"Closed {result.get('closed', 0)} positions."
            else:
                text = "Close all function not available."
            
            return VoiceResponse(text=text, success=True)
        except Exception as e:
            return VoiceResponse(text=f"Error closing positions: {str(e)}", success=False)
    
    async def _handle_close_position(self, symbol: Optional[str] = None) -> VoiceResponse:
        """Handle close specific position command"""
        try:
            if hasattr(self.trading_bot, 'close_position'):
                if symbol:
                    result = self.trading_bot.close_position(symbol)
                    if result.get('success', False):
                        text = f"Position for {symbol} closed successfully."
                    else:
                        text = f"Failed to close position for {symbol}."
                else:
                    # Try to get the last mentioned symbol or most recent position
                    positions = getattr(self.trading_bot, 'get_positions', lambda: [])()
                    if positions:
                        last_pos = positions[-1]
                        symbol = last_pos.get('symbol', 'unknown')
                        result = self.trading_bot.close_position(symbol)
                        if result.get('success', False):
                            text = f"Closed position for {symbol}."
                        else:
                            text = f"Failed to close position for {symbol}."
                    else:
                        text = "No positions to close. Please specify a symbol."
            else:
                text = "Close position function not available."
            
            return VoiceResponse(text=text, success=True)
        except Exception as e:
            return VoiceResponse(text=f"Error closing position: {str(e)}", success=False)
    
    async def _handle_market_status(self) -> VoiceResponse:
        """Handle market status command"""
        try:
            status = getattr(self.trading_bot, 'get_market_status', lambda: {})()
            
            text = f"Market is {status.get('state', 'unknown')}. "
            text += f"Volatility is {status.get('volatility', 'normal')}."
            
            return VoiceResponse(text=text, success=True, data=status)
        except Exception as e:
            return VoiceResponse(text=f"Error getting market status: {str(e)}", success=False)
    
    async def _handle_last_trade(self) -> VoiceResponse:
        """Handle last trade command"""
        try:
            trade = getattr(self.trading_bot, 'get_last_trade', lambda: {})()
            
            if not trade:
                text = "No recent trades."
            else:
                profit = trade.get('profit', 0)
                text = f"Last trade was {trade.get('symbol')} {trade.get('direction')}. "
                text += f"Result: {'profit' if profit > 0 else 'loss'} of {abs(profit):.2f} dollars."
            
            return VoiceResponse(text=text, success=True, data=trade)
        except Exception as e:
            return VoiceResponse(text=f"Error getting last trade: {str(e)}", success=False)
    
    async def _handle_win_rate(self) -> VoiceResponse:
        """Handle win rate command"""
        try:
            stats = getattr(self.trading_bot, 'get_statistics', lambda: {})()
            
            win_rate = stats.get('win_rate', 0) * 100
            text = f"Your win rate is {win_rate:.1f} percent over {stats.get('total_trades', 0)} trades."
            
            return VoiceResponse(text=text, success=True, data=stats)
        except Exception as e:
            return VoiceResponse(text=f"Error getting win rate: {str(e)}", success=False)
    
    async def _handle_emergency_stop(self) -> VoiceResponse:
        """Handle emergency stop command"""
        try:
            if hasattr(self.trading_bot, 'emergency_stop'):
                self.trading_bot.emergency_stop()
                text = "Emergency stop activated. All trading halted."
            else:
                text = "Emergency stop function not available."
            
            return VoiceResponse(text=text, success=True)
        except Exception as e:
            return VoiceResponse(text=f"Error activating emergency stop: {str(e)}", success=False)


__all__ = [
    'VoiceAssistant',
    'VoiceCommand',
    'VoiceResponse',
    'SpeechRecognizer',
    'TextToSpeech'
]
